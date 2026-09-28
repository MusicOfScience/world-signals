"""Read-only coverage and chronology integrity helpers.

These helpers compare already-governed projections.  They do not admit
Canonical occurrences, alter Forecasts, or infer analytical significance.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


EARLIER_SCHEDULED_OCCURRENCE = "EARLIER_SCHEDULED_OCCURRENCE_OUTSIDE_FORECAST_TARGET"
NO_EARLIER_SCHEDULED_OCCURRENCE = "NO_EARLIER_SCHEDULED_OCCURRENCE"


class CoverageIntegrityError(ValueError):
    """Raised when an integrity comparison cannot be made safely."""


def _parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _records(registry: dict[str, Any]) -> list[dict[str, Any]]:
    rows = registry.get("records") if isinstance(registry, dict) else None
    if not isinstance(rows, list):
        raise CoverageIntegrityError("Canonical registry must contain records")
    return [row for row in rows if isinstance(row, dict)]


def detect_earlier_scheduled_occurrences(
    forecast: dict[str, Any],
    canonical_registry: dict[str, Any],
    *,
    target_occurrence_id: str,
) -> dict[str, Any]:
    """Compare a Forecast target with earlier same-series occurrences.

    The comparison uses the Forecast information cutoff as the knowledge
    boundary and the exact linked Canonical occurrence as the target.  It is
    deliberately generic: a result is informational chronology context, not
    a Forecast validation failure and not a new Calendar assertion.
    """

    cutoff = _parse_utc(forecast.get("information_cutoff_at_utc"))
    if cutoff is None:
        raise CoverageIntegrityError("Forecast requires an aware UTC information cutoff")
    rows = _records(canonical_registry)
    by_id = {row.get("occurrence_id"): row for row in rows}
    target = by_id.get(target_occurrence_id)
    if target is None:
        raise CoverageIntegrityError(f"Forecast target occurrence is not in Canonical: {target_occurrence_id}")
    target_start = _parse_utc(target.get("start_utc"))
    series_id = target.get("series_id")
    if target_start is None or not series_id:
        raise CoverageIntegrityError("Forecast target must have a series and exact UTC start")

    earlier = []
    for row in rows:
        if row.get("series_id") != series_id or row.get("occurrence_id") == target_occurrence_id:
            continue
        if row.get("lifecycle_status") == "CANCELLED":
            continue
        start = _parse_utc(row.get("start_utc"))
        if start is None or not (cutoff < start < target_start):
            continue
        earlier.append(
            {
                "occurrence_id": row.get("occurrence_id"),
                "series_id": series_id,
                "canonical_name": row.get("canonical_name"),
                "start_utc": row.get("start_utc"),
                "start_local": row.get("start_local"),
                "source_timezone": row.get("source_timezone"),
                "source_id": row.get("source_id"),
                "lifecycle_status": row.get("lifecycle_status"),
                "certainty_status": row.get("certainty_status"),
            }
        )
    earlier.sort(key=lambda row: (row["start_utc"], row["occurrence_id"]))
    return {
        "classification": EARLIER_SCHEDULED_OCCURRENCE if earlier else NO_EARLIER_SCHEDULED_OCCURRENCE,
        "forecast_id": forecast.get("forecast_id"),
        "information_cutoff_at_utc": forecast.get("information_cutoff_at_utc"),
        "target_occurrence_id": target_occurrence_id,
        "target_series_id": series_id,
        "target_start_utc": target.get("start_utc"),
        "earlier_occurrences": earlier,
        "next_scheduled_event_is_not_necessarily_forecast_target": bool(earlier),
        "automatic_forecast_backfill": False,
    }


def validate_igr_recovery_candidate(candidate: dict[str, Any]) -> list[str]:
    """Validate the non-governed IGR recovery candidate boundary."""

    errors: list[str] = []
    if candidate.get("review_state") != "CANDIDATE_REVIEW_REQUIRED":
        errors.append("IGR candidate must remain review-gated")
    if candidate.get("canonical_write_permitted") is not False:
        errors.append("IGR candidate must prohibit Canonical writes")
    intake = candidate.get("analytical_intake") if isinstance(candidate.get("analytical_intake"), dict) else candidate
    if intake.get("world_state_intake") != "OFFICIAL_PROJECTION_ONLY_NO_INTAKE":
        errors.append("IGR projection boundary is missing")
    publication = candidate.get("publication") if isinstance(candidate.get("publication"), dict) else {}
    if publication.get("date") != "2026-09-21" or publication.get("timing_precision") != "CIVIL_DATE":
        errors.append("IGR publication date must remain a civil date")
    if publication.get("first_discovered_at_utc") in (None, "2026-09-09T00:00:00Z"):
        errors.append("IGR first discovery must be the actual Step 14B time, not backdated")
    if candidate.get("event_type") == "NEW_EVENT_TYPE":
        errors.append("IGR candidate must reuse an existing event type")
    return errors


def classify_strategic_publication_discovery(
    *,
    publication_name: str,
    announcement_date: str | None,
    release_date: str | None,
    source_role: str,
) -> str:
    """Classify a first-party strategic-publication discovery candidate."""

    if not publication_name.strip() or source_role != "FIRST_PARTY_AUTHORITATIVE":
        return "NO_CANDIDATE"
    if release_date:
        return "AUTHORITATIVE_FUTURE_PUBLICATION_ANNOUNCEMENT"
    if announcement_date:
        return "DISCOVERY_WATCH_CANDIDATE"
    return "NO_CANDIDATE"
