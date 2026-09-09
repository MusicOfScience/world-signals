from __future__ import annotations

from datetime import date
from hashlib import sha256
import json

from .adapters.european_council_rss import EuropeanCouncilRSSItem

CANONICAL_SOURCE_ID = "WSSRC-INT-003"
MONITOR_SOURCE_ID = "WSSRC-INT-035"
ADAPTER_ID = "EUROPEAN_COUNCIL_MEETINGS_RSS"
EXPECTED_SERIES_ID = "WSER-INT-EUCO"
EXPECTED_TIMEZONE = "Europe/Brussels"
EXPECTED_CATEGORY = "INTERNATIONAL_INSTITUTIONS"
EXPECTED_REGION = "Europe"
EXPECTED_EVENT_TYPE = "INSTITUTIONAL_MEETING"
EXPECTED_GUID_TO_OCCURRENCE = {
    "147805": "WSO-INT-B-0102",
    "147983": "WSO-INT-B-0103",
    "147844": "WSO-INT-B-0104",
}
EXPECTED_GUID_TITLES = {
    "147805": "European Council",
    "147983": "Informal meeting of heads of state or government",
    "147844": "European Council",
}


def _stable_hash(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def _iso_date(value: object, *, field: str, occurrence_id: str) -> date:
    if not isinstance(value, str):
        raise ValueError(f"European Council Canonical {field} is not an ISO date for {occurrence_id}: {value!r}")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"European Council Canonical {field} is invalid for {occurrence_id}: {value!r}") from exc
    if parsed.isoformat() != value:
        raise ValueError(f"European Council Canonical {field} is not canonical ISO form for {occurrence_id}: {value!r}")
    return parsed


def _configured_scope(records: list[dict], config: dict) -> tuple[dict[str, dict], date]:
    gates = {
        "adapter_id": ADAPTER_ID,
        "source_id": MONITOR_SOURCE_ID,
        "canonical_schedule_source_id": CANONICAL_SOURCE_ID,
        "request_budget_per_run": 1,
        "rss_request_count_per_run": 1,
        "robots_request_count_per_run": 0,
        "direct_calendar_html_request_count_per_run": 0,
        "item_followup_request_count_per_run": 0,
        "search_route_discovery_request_count_per_run": 0,
        "schedule_authority": False,
        "clock_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "canonical_date_mutation_allowed": False,
        "automatic_calendar_html_fetch_allowed": False,
        "automatic_item_link_fetch_allowed": False,
        "automatic_new_occurrence_creation_allowed": False,
        "automatic_search_route_discovery_allowed": False,
        "automatic_live_or_analysis_promotion_allowed": False,
        "automatic_commit_allowed": False,
    }
    for key, expected in gates.items():
        if config.get(key) != expected:
            raise ValueError(f"European Council RSS monitor gate drift for {key}: {config.get(key)!r}")

    if config.get("machine_access_basis") != "OFFICIAL_CONSILIUM_RSS_AUTOMATIC_LOADING_INTERFACE":
        raise ValueError("European Council RSS machine-access basis drift")
    if config.get("absence_semantics") != "NONE":
        raise ValueError("European Council RSS absence acquired event-state semantics")
    if config.get("observed_date_source") != "OFFICIAL_RSS_ITEM_LINK_PATH_ONLY":
        raise ValueError("European Council RSS observed-date source drift")
    if config.get("updated_field_is_event_time") is not False:
        raise ValueError("European Council RSS updated field acquired event-time authority")
    if config.get("description_field_is_event_time") is not False:
        raise ValueError("European Council RSS description field acquired event-time authority")

    guid_map = config.get("configured_guid_to_occurrence")
    if guid_map != EXPECTED_GUID_TO_OCCURRENCE:
        raise ValueError(f"European Council RSS configured GUID mapping drift: {guid_map!r}")
    title_map = config.get("configured_guid_titles")
    if title_map != EXPECTED_GUID_TITLES:
        raise ValueError(f"European Council RSS configured title mapping drift: {title_map!r}")
    ids = list(config.get("canonical_occurrence_ids") or [])
    if len(ids) != 3 or set(ids) != set(EXPECTED_GUID_TO_OCCURRENCE.values()) or len(set(ids)) != 3:
        raise ValueError("European Council RSS route must contain the exact three stable occurrence IDs")

    floor_raw = config.get("unconfigured_item_review_floor_local")
    try:
        floor = date.fromisoformat(floor_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"European Council RSS review-floor drift: {floor_raw!r}") from exc

    expected_ids = set(EXPECTED_GUID_TO_OCCURRENCE.values())
    by_id = {row.get("occurrence_id"): row for row in records if row.get("occurrence_id") in expected_ids}
    if set(by_id) != expected_ids:
        raise ValueError("European Council RSS configured occurrence missing from Canonical")

    for occurrence_id, row in by_id.items():
        checks = {
            "series_id": EXPECTED_SERIES_ID,
            "source_id": CANONICAL_SOURCE_ID,
            "source_timezone": EXPECTED_TIMEZONE,
            "category": EXPECTED_CATEGORY,
            "region": EXPECTED_REGION,
            "event_type": EXPECTED_EVENT_TYPE,
            "time_precision": "DAY",
            "all_day_semantics": True,
        }
        for key, expected in checks.items():
            if row.get(key) != expected:
                raise ValueError(
                    f"European Council Canonical scope drift for {occurrence_id} {key}: {row.get(key)!r}"
                )
        start = _iso_date(row.get("start_local"), field="start_local", occurrence_id=occurrence_id)
        end_raw = row.get("end_local")
        timing_type = row.get("timing_type")
        if end_raw is None:
            if timing_type != "CIVIL_DATE":
                raise ValueError(f"European Council single-day occurrence timing drift: {occurrence_id} {timing_type!r}")
        else:
            end = _iso_date(end_raw, field="end_local", occurrence_id=occurrence_id)
            if end <= start:
                raise ValueError(f"European Council Canonical range is not forward: {occurrence_id}")
            if timing_type != "MULTI_DAY_LOCAL":
                raise ValueError(f"European Council multi-day occurrence timing drift: {occurrence_id} {timing_type!r}")
        if row.get("start_utc") is not None or row.get("end_utc") is not None:
            raise ValueError(f"European Council day-precision occurrence unexpectedly acquired UTC clock: {occurrence_id}")
    return by_id, floor


def _old_value(row: dict) -> dict:
    return {
        "occurrence_id": row["occurrence_id"],
        "start_local": row.get("start_local"),
        "end_local": row.get("end_local"),
        "timing_type": row.get("timing_type"),
        "lifecycle_status": row.get("lifecycle_status"),
        "certainty_status": row.get("certainty_status"),
    }


def _candidate_id(candidate_type: str, payload: dict) -> str:
    return "WSRC-EUCO-" + _stable_hash({"candidate_type": candidate_type, **payload})[:16]


def european_council_rss_review_candidates(
    records: list[dict],
    items: list[EuropeanCouncilRSSItem],
    config: dict,
) -> tuple[list[dict], list[dict]]:
    by_occurrence, review_floor = _configured_scope(records, config)

    by_guid: dict[str, EuropeanCouncilRSSItem] = {}
    for item in items:
        if item.guid in by_guid:
            raise ValueError(f"European Council RSS comparator received duplicate GUID: {item.guid}")
        by_guid[item.guid] = item

    candidates: list[dict] = []
    observations: list[dict] = []

    for guid, occurrence_id in EXPECTED_GUID_TO_OCCURRENCE.items():
        row = by_occurrence[occurrence_id]
        item = by_guid.get(guid)
        if item is None:
            if row.get("lifecycle_status") == "COMPLETED":
                observations.append({
                    "type": "EUROPEAN_COUNCIL_RSS_COMPLETED_GUID_ABSENCE_OBSERVATION",
                    "source_id": MONITOR_SOURCE_ID,
                    "canonical_schedule_source_id": CANONICAL_SOURCE_ID,
                    "occurrence_id": occurrence_id,
                    "guid": guid,
                    "absence_is_not_cancellation_or_certainty_change": True,
                    "event_state_inference": "NONE",
                    "automatic_commit_allowed": False,
                })
                continue
            payload = {
                "occurrence_id": occurrence_id,
                "guid": guid,
                "old_value": _old_value(row),
            }
            candidates.append({
                "candidate_id": _candidate_id("EUROPEAN_COUNCIL_RSS_CONFIGURED_GUID_MISSING_REVIEW", payload),
                "candidate_type": "EUROPEAN_COUNCIL_RSS_CONFIGURED_GUID_MISSING_REVIEW",
                "source_id": MONITOR_SOURCE_ID,
                "canonical_schedule_source_id": CANONICAL_SOURCE_ID,
                "occurrence_id": occurrence_id,
                "old_value": _old_value(row),
                "new_value": {"guid": guid, "rss_item_present": False},
                "review_state": "PENDING_MANUAL_AUTHORITATIVE_SCHEDULE_RECHECK",
                "candidate_origin": "LIVE_READ_ONLY_OFFICIAL_RSS_IDENTITY_SENTINEL",
                "absence_is_not_cancellation": True,
                "absence_is_not_completion": True,
                "absence_is_not_certainty_change": True,
                "event_state_inference": "NONE",
                "canonical_date_mutation_allowed": False,
                "automatic_calendar_html_fetch_allowed": False,
                "automatic_item_link_fetch_allowed": False,
                "automatic_commit_allowed": False,
            })
            observations.append({
                "type": "EUROPEAN_COUNCIL_RSS_CONFIGURED_GUID_MISSING_OBSERVATION",
                "source_id": MONITOR_SOURCE_ID,
                "occurrence_id": occurrence_id,
                "guid": guid,
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
            })
            continue

        expected_title = EXPECTED_GUID_TITLES[guid]
        if item.title != expected_title:
            raise ValueError(
                f"European Council RSS configured GUID title drift for {guid}: {item.title!r} != {expected_title!r}"
            )

        observed = {
            "guid": item.guid,
            "title": item.title,
            "link": item.link,
            "start_local": item.start_local,
            "end_local": item.end_local,
            "updated": item.updated,
            "description": item.description,
            "updated_is_event_time": False,
            "description_is_event_time": False,
            "item_page_fetched": False,
            "calendar_html_fetched": False,
        }
        current = (row.get("start_local"), row.get("end_local"))
        observed_dates = (item.start_local, item.end_local)
        if observed_dates == current:
            observations.append({
                "type": "EUROPEAN_COUNCIL_RSS_DATE_MATCH_OBSERVATION",
                "source_id": MONITOR_SOURCE_ID,
                "canonical_schedule_source_id": CANONICAL_SOURCE_ID,
                "occurrence_id": occurrence_id,
                "guid": guid,
                "current_start_local": current[0],
                "current_end_local": current[1],
                "observed_start_local": item.start_local,
                "observed_end_local": item.end_local,
                "observed_link": item.link,
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
            })
        else:
            payload = {
                "occurrence_id": occurrence_id,
                "old_value": _old_value(row),
                "observed": observed,
            }
            candidates.append({
                "candidate_id": _candidate_id("EUROPEAN_COUNCIL_RSS_DATE_CHANGE_REVIEW", payload),
                "candidate_type": "EUROPEAN_COUNCIL_RSS_DATE_CHANGE_REVIEW",
                "source_id": MONITOR_SOURCE_ID,
                "canonical_schedule_source_id": CANONICAL_SOURCE_ID,
                "occurrence_id": occurrence_id,
                "old_value": _old_value(row),
                "new_value": observed,
                "review_state": "PENDING_MANUAL_AUTHORITATIVE_SCHEDULE_RECHECK",
                "candidate_origin": "LIVE_READ_ONLY_OFFICIAL_RSS_DATE_SENTINEL",
                "date_source": "OFFICIAL_RSS_ITEM_LINK_PATH_ONLY",
                "event_state_inference": "NONE",
                "schedule_authority": False,
                "clock_authority": False,
                "lifecycle_authority": False,
                "certainty_authority": False,
                "canonical_date_mutation_allowed": False,
                "automatic_calendar_html_fetch_allowed": False,
                "automatic_item_link_fetch_allowed": False,
                "automatic_commit_allowed": False,
            })
            observations.append({
                "type": "EUROPEAN_COUNCIL_RSS_DATE_CHANGE_OBSERVED_REVIEW_REQUIRED",
                "source_id": MONITOR_SOURCE_ID,
                "occurrence_id": occurrence_id,
                "guid": guid,
                "current_start_local": current[0],
                "current_end_local": current[1],
                "observed_start_local": item.start_local,
                "observed_end_local": item.end_local,
                "observed_link": item.link,
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
            })

    unconfigured_future = []
    configured_guids = set(EXPECTED_GUID_TO_OCCURRENCE)
    for item in items:
        if item.guid in configured_guids:
            continue
        try:
            observed_start = date.fromisoformat(item.start_local)
        except ValueError as exc:
            raise ValueError(f"European Council RSS comparator received invalid parsed date: {item.start_local!r}") from exc
        if observed_start >= review_floor:
            unconfigured_future.append({
                "guid": item.guid,
                "title": item.title,
                "link": item.link,
                "start_local": item.start_local,
                "end_local": item.end_local,
            })
    observations.append({
        "type": "EUROPEAN_COUNCIL_RSS_UNCONFIGURED_FUTURE_MEETING_OBSERVATION",
        "source_id": MONITOR_SOURCE_ID,
        "review_floor_local": review_floor.isoformat(),
        "unconfigured_future_item_count": len(unconfigured_future),
        "items": sorted(unconfigured_future, key=lambda x: (x["start_local"], x["guid"])),
        "automatic_new_occurrence_creation_allowed": False,
        "event_state_inference": "NONE",
        "automatic_commit_allowed": False,
    })
    observations.append({
        "type": "EUROPEAN_COUNCIL_RSS_HAS_NO_DIRECT_WRITE_CLOCK_LIFECYCLE_CERTAINTY_OR_CREATION_AUTHORITY",
        "source_id": MONITOR_SOURCE_ID,
        "configured_occurrence_count": 3,
        "schedule_authority": False,
        "clock_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "canonical_date_mutation_allowed": False,
        "automatic_calendar_html_fetch_allowed": False,
        "automatic_item_link_fetch_allowed": False,
        "automatic_new_occurrence_creation_allowed": False,
        "automatic_live_or_analysis_promotion_allowed": False,
        "automatic_commit_allowed": False,
    })
    return candidates, observations
