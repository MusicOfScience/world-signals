from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from zoneinfo import ZoneInfo

from .adapters.nass_asb_ical import NASSASBRelease

SOURCE_ID = "WSSRC-COM-005"
ADAPTER_ID = "USDA_NASS_ASB_ICAL"
EXPECTED_TIMEZONE = "America/New_York"
EXPECTED_CATEGORY = "AGRICULTURE_FOOD"
EXPECTED_EVENT_TYPE = "INFORMATION_RELEASE"
EXPECTED_UID_TO_OCCURRENCE = {
    "a763c1f5-aef0-435a-a183-2f8191f08d99": "WSO-COM-A-0030",
    "7172110f-8719-4672-9026-f708df320e71": "WSO-COM-A-0032",
    "cf36624c-7ddb-4293-ad32-c52b78d0e299": "WSO-COM-A-0034",
    "49647b19-c690-45dc-a48f-54d12ea99307": "WSO-COM-A-0036",
    "4b58e729-3b3b-4f2a-a86e-2ee17637ad46": "WSO-COM-A-0037",
}
EXPECTED_UID_SUMMARIES = {
    "a763c1f5-aef0-435a-a183-2f8191f08d99": "Crop Production",
    "7172110f-8719-4672-9026-f708df320e71": "Crop Production",
    "cf36624c-7ddb-4293-ad32-c52b78d0e299": "Crop Production",
    "49647b19-c690-45dc-a48f-54d12ea99307": "Crop Production",
    "4b58e729-3b3b-4f2a-a86e-2ee17637ad46": "Grain Stocks",
}
EXPECTED_SERIES = {
    "WSO-COM-A-0030": "WSER-COM-USDA-CROP",
    "WSO-COM-A-0032": "WSER-COM-USDA-CROP",
    "WSO-COM-A-0034": "WSER-COM-USDA-CROP",
    "WSO-COM-A-0036": "WSER-COM-USDA-CROP",
    "WSO-COM-A-0037": "WSER-COM-USDA-GRAIN",
}


def _stable_hash(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def _parse_local(value: object, *, occurrence_id: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"NASS Canonical start_local is not string for {occurrence_id}: {value!r}")
    try:
        dt = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"NASS Canonical start_local invalid for {occurrence_id}: {value!r}") from exc
    if dt.tzinfo is not None or dt.isoformat(timespec="seconds") != value:
        raise ValueError(f"NASS Canonical start_local must be naive second-precision local datetime for {occurrence_id}: {value!r}")
    return dt


def _utc_for_local(value: str) -> str:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is not None:
        raise ValueError(f"NASS local datetime unexpectedly timezone-aware: {value!r}")
    aware = dt.replace(tzinfo=ZoneInfo(EXPECTED_TIMEZONE)).astimezone(timezone.utc)
    return aware.isoformat(timespec="seconds").replace("+00:00", "Z")


def _configured_scope(records: list[dict], config: dict) -> tuple[dict[str, dict], datetime]:
    gates = {
        "adapter_id": ADAPTER_ID,
        "source_id": SOURCE_ID,
        "canonical_schedule_source_id": SOURCE_ID,
        "request_budget_per_run": 1,
        "ical_request_count_per_run": 1,
        "robots_request_count_per_run": 0,
        "calendar_html_request_count_per_run": 0,
        "report_followup_request_count_per_run": 0,
        "search_route_discovery_request_count_per_run": 0,
        "schedule_authority": False,
        "clock_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "canonical_datetime_mutation_allowed": False,
        "automatic_calendar_html_fetch_allowed": False,
        "automatic_report_followup_allowed": False,
        "automatic_new_occurrence_creation_allowed": False,
        "automatic_search_route_discovery_allowed": False,
        "automatic_live_or_analysis_promotion_allowed": False,
        "automatic_commit_allowed": False,
    }
    for key, expected in gates.items():
        if config.get(key) != expected:
            raise ValueError(f"NASS ASB monitor gate drift for {key}: {config.get(key)!r}")
    if config.get("machine_access_basis") != "OFFICIAL_NASS_ICAL_PLUS_EXPLICIT_NONEXCESSIVE_ROBOT_POLICY_WITH_CONTACT_UA":
        raise ValueError("NASS ASB machine-access basis drift")
    if config.get("floating_datetime_timezone") != EXPECTED_TIMEZONE:
        raise ValueError("NASS ASB floating-time timezone contract drift")
    if config.get("floating_timezone_basis") != "FIRST_PARTY_NASS_REPORTS_BY_DATE_PAGES_LABEL_TARGET_RELEASES_ET":
        raise ValueError("NASS ASB floating-time evidence basis drift")
    if config.get("dtend_is_event_end") is not False or config.get("dtstamp_is_event_time") is not False:
        raise ValueError("NASS ASB non-authoritative ICS metadata acquired event-time authority")
    if config.get("sequence_is_event_state") is not False or config.get("description_is_event_time") is not False:
        raise ValueError("NASS ASB non-authoritative ICS metadata acquired event-state authority")
    if config.get("absence_semantics") != "NONE":
        raise ValueError("NASS ASB absence acquired event-state semantics")
    if config.get("configured_uid_to_occurrence") != EXPECTED_UID_TO_OCCURRENCE:
        raise ValueError("NASS ASB configured UID mapping drift")
    if config.get("configured_uid_summaries") != EXPECTED_UID_SUMMARIES:
        raise ValueError("NASS ASB configured UID summary mapping drift")

    ids = list(config.get("canonical_occurrence_ids") or [])
    expected_ids = set(EXPECTED_UID_TO_OCCURRENCE.values())
    if len(ids) != 5 or set(ids) != expected_ids or len(set(ids)) != 5:
        raise ValueError("NASS ASB route must contain the exact five stable occurrence IDs")
    by_id = {r.get("occurrence_id"): r for r in records if r.get("occurrence_id") in expected_ids}
    if set(by_id) != expected_ids:
        raise ValueError("NASS ASB configured occurrence missing from Canonical")

    for occurrence_id, row in by_id.items():
        checks = {
            "series_id": EXPECTED_SERIES[occurrence_id],
            "source_id": SOURCE_ID,
            "source_timezone": EXPECTED_TIMEZONE,
            "category": EXPECTED_CATEGORY,
            "event_type": EXPECTED_EVENT_TYPE,
            "timing_type": "LOCAL_DATETIME",
            "time_precision": "MINUTE",
            "all_day_semantics": False,
        }
        for key, expected in checks.items():
            if row.get(key) != expected:
                raise ValueError(f"NASS Canonical scope drift for {occurrence_id} {key}: {row.get(key)!r}")
        if row.get("end_local") is not None or row.get("end_utc") is not None:
            raise ValueError(f"NASS information release unexpectedly acquired end-time semantics: {occurrence_id}")
        local = _parse_local(row.get("start_local"), occurrence_id=occurrence_id)
        expected_utc = _utc_for_local(local.isoformat(timespec="seconds"))
        if row.get("start_utc") != expected_utc:
            raise ValueError(f"NASS Canonical UTC/local timezone mismatch for {occurrence_id}: {row.get('start_utc')!r} != {expected_utc!r}")
        if row.get("publication_datetime") != row.get("start_local"):
            raise ValueError(f"NASS Canonical publication_datetime/start_local drift for {occurrence_id}")
        if row.get("publication_time_semantics") != "EXACT_LOCAL_TIME":
            raise ValueError(f"NASS Canonical publication-time semantics drift for {occurrence_id}")

    floor_raw = config.get("unconfigured_item_review_floor_local")
    try:
        floor = datetime.fromisoformat(floor_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"NASS ASB review-floor drift: {floor_raw!r}") from exc
    if floor.tzinfo is not None:
        raise ValueError("NASS ASB review floor must be source-local naive datetime")
    return by_id, floor


def _old_value(row: dict) -> dict:
    return {
        "occurrence_id": row["occurrence_id"],
        "start_local": row.get("start_local"),
        "start_utc": row.get("start_utc"),
        "publication_datetime": row.get("publication_datetime"),
        "lifecycle_status": row.get("lifecycle_status"),
        "certainty_status": row.get("certainty_status"),
    }


def _candidate_id(candidate_type: str, payload: dict) -> str:
    return "WSRC-NASS-" + _stable_hash({"candidate_type": candidate_type, **payload})[:16]


def nass_asb_ical_review_candidates(
    records: list[dict],
    items: list[NASSASBRelease],
    config: dict,
) -> tuple[list[dict], list[dict]]:
    by_occurrence, review_floor = _configured_scope(records, config)
    by_uid: dict[str, NASSASBRelease] = {}
    for item in items:
        if item.uid in by_uid:
            raise ValueError(f"NASS ASB comparator received duplicate UID: {item.uid}")
        by_uid[item.uid] = item

    candidates: list[dict] = []
    observations: list[dict] = []
    for uid, occurrence_id in EXPECTED_UID_TO_OCCURRENCE.items():
        row = by_occurrence[occurrence_id]
        item = by_uid.get(uid)
        if item is None:
            if row.get("lifecycle_status") == "COMPLETED":
                observations.append({
                    "type": "NASS_ASB_ICAL_COMPLETED_UID_ABSENCE_OBSERVATION",
                    "source_id": SOURCE_ID,
                    "occurrence_id": occurrence_id,
                    "uid": uid,
                    "event_state_inference": "NONE",
                    "automatic_commit_allowed": False,
                })
                continue
            payload = {"occurrence_id": occurrence_id, "uid": uid, "old_value": _old_value(row)}
            candidates.append({
                "candidate_id": _candidate_id("NASS_ASB_ICAL_CONFIGURED_UID_MISSING_REVIEW", payload),
                "candidate_type": "NASS_ASB_ICAL_CONFIGURED_UID_MISSING_REVIEW",
                "source_id": SOURCE_ID,
                "occurrence_id": occurrence_id,
                "old_value": _old_value(row),
                "new_value": {"uid": uid, "ical_item_present": False},
                "review_state": "PENDING_MANUAL_AUTHORITATIVE_SCHEDULE_RECHECK",
                "candidate_origin": "LIVE_READ_ONLY_OFFICIAL_NASS_ICAL_IDENTITY_SENTINEL",
                "absence_is_not_cancellation": True,
                "absence_is_not_completion": True,
                "absence_is_not_certainty_change": True,
                "event_state_inference": "NONE",
                "canonical_datetime_mutation_allowed": False,
                "automatic_calendar_html_fetch_allowed": False,
                "automatic_report_followup_allowed": False,
                "automatic_commit_allowed": False,
            })
            continue

        expected_summary = EXPECTED_UID_SUMMARIES[uid]
        if item.summary != expected_summary:
            raise ValueError(f"NASS ASB configured UID summary drift for {uid}: {item.summary!r} != {expected_summary!r}")

        observed_utc = _utc_for_local(item.start_local)
        if row.get("lifecycle_status") == "COMPLETED":
            observations.append({
                "type": "NASS_ASB_ICAL_COMPLETED_UID_PRESENCE_OBSERVATION",
                "source_id": SOURCE_ID,
                "occurrence_id": occurrence_id,
                "uid": uid,
                "observed_start_local": item.start_local,
                "observed_start_utc": observed_utc,
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
            })
            continue

        current = (row.get("start_local"), row.get("start_utc"))
        observed = (item.start_local, observed_utc)
        if observed == current:
            observations.append({
                "type": "NASS_ASB_ICAL_DATETIME_MATCH_OBSERVATION",
                "source_id": SOURCE_ID,
                "occurrence_id": occurrence_id,
                "uid": uid,
                "summary": item.summary,
                "current_start_local": current[0],
                "current_start_utc": current[1],
                "observed_start_local": item.start_local,
                "observed_start_utc": observed_utc,
                "floating_datetime_timezone": EXPECTED_TIMEZONE,
                "dtend_is_event_end": False,
                "dtstamp_is_event_time": False,
                "sequence_is_event_state": False,
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
            })
        else:
            new_value = {
                "uid": uid,
                "summary": item.summary,
                "start_local": item.start_local,
                "start_utc": observed_utc,
                "floating_datetime_timezone": EXPECTED_TIMEZONE,
                "dtend_raw": item.dtend_raw,
                "dtend_is_event_end": False,
                "dtstamp_raw": item.dtstamp_raw,
                "dtstamp_is_event_time": False,
                "sequence_raw": item.sequence_raw,
                "sequence_is_event_state": False,
                "description_is_event_time": False,
            }
            payload = {"occurrence_id": occurrence_id, "old_value": _old_value(row), "new_value": new_value}
            candidates.append({
                "candidate_id": _candidate_id("NASS_ASB_ICAL_DATETIME_CHANGE_REVIEW", payload),
                "candidate_type": "NASS_ASB_ICAL_DATETIME_CHANGE_REVIEW",
                "source_id": SOURCE_ID,
                "occurrence_id": occurrence_id,
                "old_value": _old_value(row),
                "new_value": new_value,
                "review_state": "PENDING_MANUAL_AUTHORITATIVE_SCHEDULE_RECHECK",
                "candidate_origin": "LIVE_READ_ONLY_OFFICIAL_NASS_ICAL_DATETIME_SENTINEL",
                "event_state_inference": "NONE",
                "schedule_authority": False,
                "clock_authority": False,
                "lifecycle_authority": False,
                "certainty_authority": False,
                "canonical_datetime_mutation_allowed": False,
                "automatic_calendar_html_fetch_allowed": False,
                "automatic_report_followup_allowed": False,
                "automatic_commit_allowed": False,
            })

    configured = set(EXPECTED_UID_TO_OCCURRENCE)
    unconfigured: list[dict] = []
    for item in items:
        if item.uid in configured:
            continue
        try:
            observed_local = datetime.fromisoformat(item.start_local)
        except ValueError as exc:
            raise ValueError(f"NASS ASB comparator received invalid parsed datetime: {item.start_local!r}") from exc
        if observed_local >= review_floor:
            unconfigured.append({
                "uid": item.uid,
                "summary": item.summary,
                "start_local": item.start_local,
                "start_utc": _utc_for_local(item.start_local),
            })
    observations.append({
        "type": "NASS_ASB_ICAL_UNCONFIGURED_TARGET_RELEASE_OBSERVATION",
        "source_id": SOURCE_ID,
        "review_floor_local": review_floor.isoformat(timespec="seconds"),
        "unconfigured_future_target_count": len(unconfigured),
        "items": sorted(unconfigured, key=lambda x: (x["start_local"], x["uid"])),
        "automatic_new_occurrence_creation_allowed": False,
        "event_state_inference": "NONE",
        "automatic_commit_allowed": False,
    })
    observations.append({
        "type": "NASS_ASB_ICAL_HAS_NO_DIRECT_WRITE_LIFECYCLE_CERTAINTY_OR_CREATION_AUTHORITY",
        "source_id": SOURCE_ID,
        "configured_occurrence_count": 5,
        "schedule_authority": False,
        "clock_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "canonical_datetime_mutation_allowed": False,
        "automatic_calendar_html_fetch_allowed": False,
        "automatic_report_followup_allowed": False,
        "automatic_new_occurrence_creation_allowed": False,
        "automatic_live_or_analysis_promotion_allowed": False,
        "automatic_commit_allowed": False,
    })
    return candidates, observations
