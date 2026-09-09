from __future__ import annotations

from hashlib import sha256
import json

from .adapters.nz_election_rss import (
    NZ_ELECTION_TIMETABLE_URL,
    NZElectionRSSItem,
)

CANONICAL_SOURCE_ID = "WSSRC-EL-NZ-001"
MONITOR_SOURCE_ID = "WSSRC-EL-NZ-002"
ADAPTER_ID = "NZ_ELECTION_TIMETABLE_CHANGE_RSS"
EXPECTED_OCCURRENCE_COUNT = 6
EXPECTED_SERIES_ID = "WSER-EL-NZ-GEN"
EXPECTED_TIMEZONE = "Pacific/Auckland"
EXPECTED_CATEGORY = "ELECTIONS_GOVERNANCE"
EXPECTED_REGION = "Oceania / Pacific"


def _stable_hash(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def _configured_scope(records: list[dict], config: dict) -> list[dict]:
    gates = {
        "adapter_id": ADAPTER_ID,
        "source_id": MONITOR_SOURCE_ID,
        "canonical_schedule_source_id": CANONICAL_SOURCE_ID,
        "request_budget_per_run": 2,
        "robots_request_count_per_run": 1,
        "rss_request_count_per_run": 1,
        "minimum_inter_request_delay_seconds": 2,
        "timetable_html_request_count_per_run": 0,
        "item_followup_request_count_per_run": 0,
        "results_data_request_count_per_run": 0,
        "search_route_discovery_request_count_per_run": 0,
        "schedule_authority": False,
        "clock_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "canonical_date_mutation_allowed": False,
        "automatic_timetable_html_fetch_allowed": False,
        "automatic_item_link_fetch_allowed": False,
        "automatic_results_data_fetch_allowed": False,
        "automatic_search_route_discovery_allowed": False,
        "automatic_commit_allowed": False,
        "automatic_live_or_analysis_promotion_allowed": False,
    }
    for key, expected in gates.items():
        if config.get(key) != expected:
            raise ValueError(f"NZ election RSS monitor gate drift for {key}: {config.get(key)!r}")

    if config.get("canonical_timetable_page_identity") != NZ_ELECTION_TIMETABLE_URL:
        raise ValueError("NZ election RSS timetable-page identity drift")
    if config.get("rolling_feed_completeness") != "FINITE_ROLLING_WINDOW_NOT_EXHAUSTIVE_CHANGE_LOG":
        raise ValueError("NZ election RSS rolling-window completeness contract drift")
    if config.get("absence_semantics") != "NONE":
        raise ValueError("NZ election RSS absence acquired event semantics")

    ids = list(config.get("canonical_occurrence_ids") or [])
    if len(ids) != EXPECTED_OCCURRENCE_COUNT or len(set(ids)) != EXPECTED_OCCURRENCE_COUNT:
        raise ValueError("NZ election RSS route must contain exactly six stable occurrence IDs")
    expected_ids = {f"WSO-EL-A-{number:04d}" for number in range(5, 11)}
    if set(ids) != expected_ids:
        raise ValueError("NZ election RSS configured occurrence identity set drift")

    by_id = {row.get("occurrence_id"): row for row in records if row.get("occurrence_id") in expected_ids}
    if set(by_id) != expected_ids:
        raise ValueError("NZ election RSS configured occurrence missing from Canonical")

    ordered: list[dict] = []
    for occurrence_id in ids:
        row = by_id[occurrence_id]
        checks = {
            "series_id": EXPECTED_SERIES_ID,
            "source_id": CANONICAL_SOURCE_ID,
            "source_timezone": EXPECTED_TIMEZONE,
            "category": EXPECTED_CATEGORY,
            "region": EXPECTED_REGION,
            "event_type": "ELECTION_MILESTONE",
            "timing_type": "CIVIL_DATE",
            "time_precision": "DAY",
            "all_day_semantics": True,
        }
        for key, expected in checks.items():
            if row.get(key) != expected:
                raise ValueError(
                    f"NZ election Canonical scope drift for {occurrence_id} {key}: {row.get(key)!r}"
                )
        start_local = row.get("start_local")
        if not isinstance(start_local, str) or len(start_local) != 10:
            raise ValueError(f"NZ election Canonical date shape drift for {occurrence_id}")
        if row.get("start_utc") is not None:
            raise ValueError(f"NZ election CIVIL_DATE occurrence unexpectedly acquired UTC clock: {occurrence_id}")
        ordered.append(row)
    return ordered


def _bundle_old_value(records: list[dict]) -> list[dict]:
    return [
        {
            "occurrence_id": row["occurrence_id"],
            "start_local": row.get("start_local"),
            "lifecycle_status": row.get("lifecycle_status"),
            "certainty_status": row.get("certainty_status"),
            "election_milestone_type": row.get("election_milestone_type"),
        }
        for row in records
    ]


def nz_election_timetable_change_review_candidates(
    records: list[dict],
    items: list[NZElectionRSSItem],
    config: dict,
) -> tuple[list[dict], list[dict]]:
    scope = _configured_scope(records, config)

    target_items = [
        item for item in items
        if item.link == NZ_ELECTION_TIMETABLE_URL and item.guid == NZ_ELECTION_TIMETABLE_URL
    ]
    if len(target_items) > 1:
        raise ValueError("NZ election RSS contains duplicate exact timetable-page update identity")

    observations: list[dict] = []
    candidates: list[dict] = []
    outside_count = len(items) - len(target_items)

    if not target_items:
        observations.append({
            "type": "NZ_ELECTION_TIMETABLE_SENTINEL_HEALTHY_ROLLING_WINDOW_OBSERVATION",
            "source_id": MONITOR_SOURCE_ID,
            "canonical_schedule_source_id": CANONICAL_SOURCE_ID,
            "canonical_timetable_page_identity": NZ_ELECTION_TIMETABLE_URL,
            "configured_occurrence_count": len(scope),
            "rolling_feed_item_count": len(items),
            "outside_scope_item_count": outside_count,
            "rolling_feed_completeness": "FINITE_ROLLING_WINDOW_NOT_EXHAUSTIVE_CHANGE_LOG",
            "absence_is_not_evidence_page_unchanged": True,
            "absence_is_not_delay_cancellation_completion_or_certainty_change": True,
            "event_state_inference": "NONE",
            "automatic_commit_allowed": False,
        })
    else:
        item = target_items[0]
        evidence = {
            "timetable_page_url": item.guid,
            "rss_pub_date_raw": item.pub_date_raw,
            "rss_pub_date_iso": item.pub_date_iso,
            "rss_title": item.title,
            "rss_pubdate_is_event_time": False,
            "timetable_html_fetched": False,
            "milestone_specific_change_inference": "NONE",
        }
        digest = _stable_hash({
            "candidate_type": "NZ_ELECTION_TIMETABLE_PAGE_UPDATED_REVIEW",
            "occurrence_ids": [row["occurrence_id"] for row in scope],
            "evidence": evidence,
        })
        candidates.append({
            "candidate_id": "WSRC-NZEL-" + digest[:16],
            "candidate_type": "NZ_ELECTION_TIMETABLE_PAGE_UPDATED_REVIEW",
            "source_id": MONITOR_SOURCE_ID,
            "canonical_schedule_source_id": CANONICAL_SOURCE_ID,
            "occurrence_ids": [row["occurrence_id"] for row in scope],
            "old_value": _bundle_old_value(scope),
            "new_value": evidence,
            "review_state": "PENDING_MANUAL_AUTHORITATIVE_TIMETABLE_RECHECK",
            "candidate_origin": "LIVE_READ_ONLY_SOURCE_PAGE_UPDATE_SENTINEL",
            "bundle_review_required": True,
            "proposed_canonical_date_changes": None,
            "event_state_inference": "NONE",
            "schedule_authority": False,
            "clock_authority": False,
            "lifecycle_authority": False,
            "certainty_authority": False,
            "canonical_date_mutation_allowed": False,
            "automatic_timetable_html_fetch_allowed": False,
            "automatic_commit_allowed": False,
        })
        observations.append({
            "type": "NZ_ELECTION_TIMETABLE_PAGE_UPDATE_OBSERVED_REVIEW_REQUIRED",
            "source_id": MONITOR_SOURCE_ID,
            "canonical_timetable_page_identity": NZ_ELECTION_TIMETABLE_URL,
            "occurrence_ids": [row["occurrence_id"] for row in scope],
            **evidence,
            "event_state_inference": "NONE",
            "automatic_commit_allowed": False,
        })

    observations.append({
        "type": "NZ_ELECTION_RSS_OUTSIDE_TIMETABLE_SENTINEL_SCOPE_OBSERVATION",
        "source_id": MONITOR_SOURCE_ID,
        "outside_scope_item_count": outside_count,
        "outside_scope_item_guids": sorted(
            item.guid for item in items if item.guid != NZ_ELECTION_TIMETABLE_URL
        ),
        "outside_items_are_not_milestone_change_evidence": True,
        "automatic_canonical_addition_allowed": False,
        "event_state_inference": "NONE",
        "automatic_commit_allowed": False,
    })
    observations.append({
        "type": "NZ_ELECTION_RSS_HAS_NO_SCHEDULE_CLOCK_LIFECYCLE_CERTAINTY_OR_DIRECT_WRITE_AUTHORITY",
        "configured_occurrence_count": len(scope),
        "schedule_authority": False,
        "clock_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "canonical_date_mutation_allowed": False,
        "automatic_timetable_html_fetch_allowed": False,
        "automatic_item_link_fetch_allowed": False,
        "automatic_live_or_analysis_promotion_allowed": False,
        "automatic_commit_allowed": False,
    })
    return candidates, observations
