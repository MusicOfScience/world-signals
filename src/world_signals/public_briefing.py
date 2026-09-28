"""Deterministic public briefing-lead projection.

The Brief is a scan projection over already-public Outlook, Calendar and
Analysis artifacts.  It does not rank importance, create intelligence claims,
or become a new governed layer.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from world_signals.icalendar import TIMED_TYPES, VISIBLE_RENDER_POLICIES, WINDOW_TYPES


PUBLIC_BRIEFING_CONTRACT_VERSION = "0.1"
SELECTION_RULES = {
    "forecast_resolution": "NEXT_FORECAST_RESOLUTION",
    "calendar": "NEXT_EXACT_PUBLIC_CALENDAR_OCCURRENCE",
    "analysis": "LATEST_REVIEWED_PUBLIC_ANALYSIS",
}
_EXACT_CIVIL_TYPES = {"CIVIL_DATE", "JURISDICTIONAL_CIVIL_DATE"}


class PublicBriefingError(ValueError):
    """Raised when the public Brief cannot be constructed safely."""


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


def _exact_event(event: dict[str, Any]) -> bool:
    if event.get("lifecycle") == "CANCELLED":
        return False
    if event.get("render_policy") not in VISIBLE_RENDER_POLICIES:
        return False
    timing_type = event.get("timing_type")
    if timing_type in WINDOW_TYPES:
        return False
    if event.get("start_utc") and timing_type in TIMED_TYPES:
        return _parse_utc(event.get("start_utc")) is not None
    if event.get("start_local") and timing_type in TIMED_TYPES:
        return isinstance(event.get("start_local"), str) and "T" in event["start_local"]
    if timing_type in _EXACT_CIVIL_TYPES:
        earliest = event.get("date_earliest")
        return bool(earliest and earliest == (event.get("date_latest") or earliest))
    return False


def _event_instant(event: dict[str, Any]) -> datetime | None:
    if event.get("start_utc"):
        return _parse_utc(event["start_utc"])
    local = event.get("start_local")
    if not isinstance(local, str):
        return None
    try:
        parsed = datetime.fromisoformat(local)
    except ValueError:
        return None
    timezone_name = event.get("source_timezone")
    if timezone_name:
        try:
            return parsed.replace(tzinfo=ZoneInfo(str(timezone_name))).astimezone(timezone.utc)
        except (ZoneInfoNotFoundError, ValueError):
            return None
    return parsed.replace(tzinfo=timezone.utc)


def _event_sort_key(event: dict[str, Any]) -> tuple[str, str]:
    instant = _event_instant(event)
    if instant is not None:
        return instant.isoformat(), str(event.get("occurrence_id", ""))
    return str(event.get("date_earliest", "")), str(event.get("occurrence_id", ""))


def exact_public_calendar_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return the existing public Calendar's exact-date eligible rows."""

    return sorted((event for event in events if _exact_event(event)), key=_event_sort_key)


def select_next_calendar_occurrence(
    events: list[dict[str, Any]], as_of_utc: str
) -> dict[str, Any] | None:
    """Select the next exact occurrence for an explicit display cutoff."""

    cutoff = _parse_utc(as_of_utc)
    if cutoff is None:
        raise PublicBriefingError("calendar selection requires an explicit aware UTC cutoff")
    cutoff_date = cutoff.date()
    for event in exact_public_calendar_events(events):
        instant = _event_instant(event)
        if instant is not None and instant >= cutoff:
            return event
        if instant is None and str(event.get("date_earliest", "")) >= cutoff_date.isoformat():
            return event
    return None


def _forecast_lead(outlook: dict[str, Any]) -> dict[str, Any]:
    if outlook.get("metadata", {}).get("public_forecast_projection_allowed") is not True:
        raise PublicBriefingError("Brief requires the public Forecast projection to be allowed")
    rows = [
        row
        for row in outlook.get("forecasts", [])
        if row.get("review_state") == "ACCEPTED"
        and row.get("lifecycle_state") == "OPEN"
        and _parse_utc((row.get("resolution") or {}).get("window_start_at_utc")) is not None
    ]
    rows.sort(key=lambda row: (_parse_utc(row["resolution"]["window_start_at_utc"]), str(row.get("forecast_id", ""))))
    if not rows:
        return {
            "status": "NO_OPEN_PUBLIC_FORECAST",
            "resolution_date_utc": None,
            "forecast_ids": [],
            "source_refs": [],
        }
    first_date = _parse_utc(rows[0]["resolution"]["window_start_at_utc"]).date()
    selected = [
        row
        for row in rows
        if _parse_utc(row["resolution"]["window_start_at_utc"]).date() == first_date
    ]
    selected.sort(key=lambda row: (str(row.get("institution", "")), str(row.get("forecast_id", ""))))
    return {
        "status": "SELECTED",
        "resolution_date_utc": rows[0]["resolution"]["window_start_at_utc"],
        "forecast_ids": [row["forecast_id"] for row in selected],
        "source_refs": [
            {
                "source_layer": "PUBLIC_OUTLOOK",
                "source_object_id": row["forecast_id"],
                "source_revision_id": row.get("revision_id"),
                "selection_rule": SELECTION_RULES["forecast_resolution"],
            }
            for row in selected
        ],
    }


def _analysis_lead(analysis: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for row in analysis.get("reviews", []):
        as_of = _parse_utc(row.get("analysis_as_of_utc"))
        if row.get("review_state") == "REVIEWED_SAMPLE" and as_of is not None:
            rows.append((as_of, str(row.get("analysis_id", "")), row))
    if not rows:
        return {"status": "NO_REVIEWED_PUBLIC_ANALYSIS", "analysis_id": None, "source_ref": None}
    _, _, selected = max(rows, key=lambda item: (item[0], item[1]))
    return {
        "status": "SELECTED",
        "analysis_id": selected["analysis_id"],
        "analysis_as_of_utc": selected["analysis_as_of_utc"],
        "source_ref": {
            "source_layer": "PUBLIC_ANALYSIS",
            "source_object_id": selected["analysis_id"],
            "selection_rule": SELECTION_RULES["analysis"],
        },
    }


def build_public_briefing(
    outlook: dict[str, Any], events: dict[str, Any], analysis: dict[str, Any]
) -> dict[str, Any]:
    """Build the deterministic public Brief contract without new claims."""

    event_rows = events.get("events", [])
    if not isinstance(event_rows, list):
        raise PublicBriefingError("public Calendar projection must contain an events list")
    eligible = exact_public_calendar_events(event_rows)
    forecast = _forecast_lead(outlook)
    latest_analysis = _analysis_lead(analysis)
    return {
        "metadata": {
            "projection_type": "PUBLIC_BRIEFING_LEAD",
            "contract_version": PUBLIC_BRIEFING_CONTRACT_VERSION,
            "public_projection": True,
            "selection_rules": SELECTION_RULES,
            "chronology_is_not_importance": True,
            "importance_score": None,
            "world_state_projection": "CLOSED",
            "relationship_projection": "CLOSED",
        },
        "forecast_resolution": forecast,
        "calendar": {
            "status": "RUNTIME_DEVICE_TIME",
            "selection_rule": SELECTION_RULES["calendar"],
            "candidate_occurrence_ids": [row["occurrence_id"] for row in eligible],
            "source_refs": [
                {
                    "source_layer": "PUBLIC_CALENDAR",
                    "source_object_id": row["occurrence_id"],
                    "selection_rule": SELECTION_RULES["calendar"],
                }
                for row in eligible
            ],
        },
        "latest_reviewed_analysis": latest_analysis,
        "limitations": [
            "The three lanes are chronological/recency projections, not an importance ranking.",
            "No global score, political prioritisation or new analytical claim is created.",
            "The Calendar lane advances with explicit device display time; source timing remains in the event detail.",
        ],
    }


def validate_public_briefing(
    briefing: dict[str, Any], outlook: dict[str, Any], events: dict[str, Any], analysis: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    metadata = briefing.get("metadata", {})
    if metadata.get("contract_version") != PUBLIC_BRIEFING_CONTRACT_VERSION:
        errors.append("unsupported public Brief contract version")
    if metadata.get("public_projection") is not True:
        errors.append("public Brief must be explicitly public projection metadata")
    if metadata.get("importance_score") is not None:
        errors.append("public Brief must not contain an importance score")
    if metadata.get("selection_rules") != SELECTION_RULES:
        errors.append("public Brief selection rules are not the controlled v1 rules")
    try:
        expected = build_public_briefing(outlook, events, analysis)
    except PublicBriefingError as exc:
        return [str(exc)]
    if briefing != expected:
        errors.append("public Brief does not match deterministic source projections")
    return errors
