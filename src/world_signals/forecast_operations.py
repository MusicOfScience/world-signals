"""Read-only operational watch for governed production Forecast issuances.

This module derives operational state from immutable Forecast and Outcome data.
It never writes Forecasts, creates issuances, creates Outcomes, resolves
targets, or calculates scores.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from .outcomes import forecast_resolution_due_state


UTC = timezone.utc
TERMINAL_OPERATIONAL_STATES = {"RESOLVED", "VOID", "UNRESOLVABLE", "DISPUTED"}


def _utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        return None
    return parsed.astimezone(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def validate_operations_policy(policy: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    if not isinstance(policy, dict):
        return ("Forecast operations policy must be an object",)
    if policy.get("version") != "0.1":
        errors.append("unsupported Forecast operations policy version")
    lead = policy.get("review_lead_time_days")
    if not isinstance(lead, int) or isinstance(lead, bool) or not 0 <= lead <= 30:
        errors.append("review_lead_time_days must be an integer from 0 to 30")
    for field in ("writes_allowed", "automatic_forecast_update_allowed", "automatic_outcome_creation_allowed", "automatic_resolution_allowed", "public_projection_allowed"):
        if policy.get(field) is not False:
            errors.append(f"Forecast operations policy must keep {field}=false")
    return tuple(errors)


def operational_state(
    forecast: dict[str, Any],
    as_of_utc: str,
    outcome: dict[str, Any] | None = None,
    *,
    authoritative_evidence_available: bool = False,
    review_lead_time_days: int = 7,
) -> str:
    """Derive one operational state without changing governed records."""
    if outcome and outcome.get("resolution_status") in TERMINAL_OPERATIONAL_STATES:
        return outcome["resolution_status"]
    as_of = _utc(as_of_utc)
    resolution = forecast.get("resolution") if isinstance(forecast, dict) else None
    start = _utc(resolution.get("window_start_at_utc")) if isinstance(resolution, dict) else None
    end = _utc(resolution.get("window_end_at_utc")) if isinstance(resolution, dict) else None
    if as_of is None or start is None or end is None or start > end:
        return "INVALID_RESOLUTION_TIMING"
    if as_of < start - timedelta(days=review_lead_time_days):
        return "OPEN_NOT_DUE"
    if as_of < start:
        return "OPEN_REVIEW_WINDOW"
    due_state = forecast_resolution_due_state(
        forecast,
        as_of_utc,
        outcome,
        authoritative_evidence_available=authoritative_evidence_available,
    )
    if due_state == "DUE_AWAITING_REVIEW":
        return "AWAITING_RESOLUTION"
    if due_state == "DUE_AWAITING_AUTHORITATIVE_EVIDENCE":
        return "RESOLUTION_DUE"
    if due_state == "OVERDUE_FOR_RESOLUTION_REVIEW":
        return "OVERDUE_REVIEW"
    return "INVALID_RESOLUTION_TIMING"


def next_review_trigger(
    forecast: dict[str, Any],
    state: str,
    *,
    review_lead_time_days: int = 7,
) -> str | None:
    resolution = forecast.get("resolution") if isinstance(forecast, dict) else None
    start = _utc(resolution.get("window_start_at_utc")) if isinstance(resolution, dict) else None
    if start is None:
        return None
    if state == "OPEN_NOT_DUE":
        return _iso(start - timedelta(days=review_lead_time_days))
    if state == "OPEN_REVIEW_WINDOW":
        return _iso(start)
    if state == "RESOLUTION_DUE":
        return "authoritative evidence availability"
    if state == "AWAITING_RESOLUTION":
        return "human Outcome review"
    if state == "OVERDUE_REVIEW":
        return "immediate resolution review"
    return None


def build_watch_manifest(
    forecasts: dict[str, Any],
    outcomes: dict[str, Any],
    as_of_utc: str,
    *,
    authoritative_source_ids: set[str] | None = None,
    review_lead_time_days: int = 7,
) -> dict[str, Any]:
    """Build a deterministic machine-readable watch from governed datasets."""
    as_of = _utc(as_of_utc)
    if as_of is None:
        raise ValueError("as_of_utc must be exact UTC")
    if not isinstance(forecasts, dict) or not isinstance(forecasts.get("forecasts"), list):
        raise ValueError("Forecast dataset must contain a forecasts list")
    if not isinstance(outcomes, dict) or not isinstance(outcomes.get("outcomes"), list):
        raise ValueError("Outcome dataset must contain an outcomes list")
    rows = forecasts["forecasts"]
    outcome_rows = outcomes["outcomes"]
    by_series: dict[str, list[dict[str, Any]]] = {}
    for outcome in outcome_rows:
        reviewed_at = _utc(outcome.get("world_signals_reviewed_at_utc")) if isinstance(outcome, dict) else None
        if isinstance(outcome, dict) and reviewed_at is not None and reviewed_at <= as_of:
            by_series.setdefault(outcome.get("forecast_id"), []).append(outcome)
    latest_outcomes = {
        forecast_id: max(items, key=lambda item: item.get("revision_number", 0))
        for forecast_id, items in by_series.items()
    }
    latest_by_series: dict[str, dict[str, Any]] = {}
    for row in rows:
        if isinstance(row, dict):
            current = latest_by_series.get(row.get("forecast_id"))
            if current is None or row.get("issuance_number", 0) > current.get("issuance_number", 0):
                latest_by_series[row.get("forecast_id")] = row
    source_ids_with_available_evidence = authoritative_source_ids or set()
    items: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda item: (item.get("resolution", {}).get("window_start_at_utc", ""), item.get("issuance_id", ""))):
        forecast_id = row["forecast_id"]
        resolution = row["resolution"]
        source_ids = resolution.get("resolution_source_ids", [])
        evidence_available = bool(source_ids_with_available_evidence.intersection(source_ids))
        outcome = latest_outcomes.get(forecast_id)
        state = operational_state(
            row,
            as_of_utc,
            outcome,
            authoritative_evidence_available=evidence_available,
            review_lead_time_days=review_lead_time_days,
        )
        series_rows = [candidate for candidate in rows if candidate.get("forecast_id") == forecast_id]
        later = sorted(
            candidate["issuance_id"] for candidate in series_rows
            if candidate.get("issuance_number", 0) > row.get("issuance_number", 0)
        )
        items.append({
            "forecast_id": forecast_id,
            "issuance_id": row["issuance_id"],
            "issuance_number": row["issuance_number"],
            "is_latest_issuance": row["issuance_id"] == latest_by_series[forecast_id]["issuance_id"],
            "later_issuance_ids": later,
            "forecast_type": row["forecast_type"],
            "question": row["question"],
            "forecast_value": row["forecast_value"],
            "issued_at_utc": row["issued_at_utc"],
            "information_cutoff_at_utc": row["information_cutoff_at_utc"],
            "resolution_window_start_at_utc": resolution["window_start_at_utc"],
            "resolution_window_end_at_utc": resolution["window_end_at_utc"],
            "resolution_source_ids": source_ids,
            "fallback_source_ids": resolution.get("fallback_source_ids", []),
            "operational_state": state,
            "next_review_trigger": next_review_trigger(row, state, review_lead_time_days=review_lead_time_days),
            "outcome_id": outcome.get("outcome_id") if outcome else None,
            "outcome_status": outcome.get("resolution_status") if outcome else None,
            "authoritative_evidence_available": evidence_available,
        })
    return {
        "projection_type": "FORECAST_OPERATIONS_READ_ONLY_WATCH",
        "as_of_utc": as_of_utc,
        "review_lead_time_days": review_lead_time_days,
        "forecast_count": len(items),
        "outcome_count": len(outcome_rows),
        "evaluation_allowed": False,
        "writes_allowed": False,
        "items": items,
    }
