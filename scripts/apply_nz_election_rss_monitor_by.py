from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/monitor/NZ_ELECTION_TIMETABLE_CHANGE_RSS_BY_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
LIVE_RUNNER_PATH = ROOT / "scripts/run_live_monitor.py"
SMOKE_RUNNER_PATH = ROOT / "scripts/run_adapter_smoke.py"
ADAPTER_INIT_PATH = ROOT / "src/world_signals/adapters/__init__.py"

APPLY_ENV = "WORLD_SIGNALS_APPLY_MONITOR_BY"
BASE_SHA = "a3bca03f36eb5af9036017aad926f75f6762267f"
CANONICAL_SOURCE_ID = "WSSRC-EL-NZ-001"
MACHINE_SOURCE_ID = "WSSRC-EL-NZ-002"
ADAPTER_ID = "NZ_ELECTION_TIMETABLE_CHANGE_RSS"
TIMEZONE = "Pacific/Auckland"
EXPECTED_COUNT = 6

MUTATION_PATHS = [
    SOURCES_PATH,
    EXPECTATIONS_PATH,
    LIVE_RUNNER_PATH,
    SMOKE_RUNNER_PATH,
    ADAPTER_INIT_PATH,
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def source_by_id(data: dict, source_id: str) -> dict:
    rows = [row for row in data.get("sources", []) if row.get("source_id") == source_id]
    if len(rows) != 1:
        raise RuntimeError(f"expected exactly one source {source_id}, found {len(rows)}")
    return rows[0]


def route_by_id(data: dict, adapter_id: str) -> dict:
    rows = [row for row in data.get("adapters", []) if row.get("adapter_id") == adapter_id]
    if len(rows) != 1:
        raise RuntimeError(f"expected exactly one route {adapter_id}, found {len(rows)}")
    return rows[0]


def preflight(canonical: dict, sources: dict, expectations: dict, plan: dict) -> dict:
    p = plan["preconditions"]
    if plan.get("exact_base_main_sha") != BASE_SHA:
        raise RuntimeError("BY plan is not frozen to exact post-BX main")
    if (canonical.get("version"), len(canonical.get("records", []))) != (
        p["canonical_registry_version"], p["canonical_record_count"]
    ):
        raise RuntimeError("BY requires exact Canonical v0.41 / 689")
    if (sources.get("version"), len(sources.get("sources", []))) != (
        p["source_registry_version"], p["source_count"]
    ):
        raise RuntimeError("BY requires exact Sources v1.97 / 253")
    if (expectations.get("version"), len(expectations.get("adapters", []))) != (
        p["monitor_expectations_version"], p["configured_monitor_adapter_count"]
    ):
        raise RuntimeError("BY requires exact Monitor v0.22 / 20")
    if expectations.get("automatic_canonical_commit") is not False:
        raise RuntimeError("automatic Canonical commit gate must remain closed")
    if expectations.get("google_calendar_write") is not False:
        raise RuntimeError("Google Calendar write gate must remain closed")
    if any(row.get("source_id") == MACHINE_SOURCE_ID for row in sources.get("sources", [])):
        raise RuntimeError("BY NZ election RSS machine source already exists")
    if any(row.get("adapter_id") == ADAPTER_ID for row in expectations.get("adapters", [])):
        raise RuntimeError("BY NZ election RSS route already exists")

    schedule = deepcopy(source_by_id(sources, CANONICAL_SOURCE_ID))
    checks = {
        "institution": "Electoral Commission New Zealand",
        "jurisdiction": "New Zealand",
        "domain": "elections",
        "endpoint_role": "2026 General Election confirmed timetable",
        "authoritative_url": plan["selection"]["canonical_timetable_url"],
        "source_type": "official_electoral_timetable",
        "source_timezone": TIMEZONE,
        "canonical_dependency_count": p["canonical_schedule_dependency_count"],
        "automated_monitoring_use": p["canonical_schedule_automated_monitoring_use"],
        "automated_retrieval_permission": p["canonical_schedule_automated_retrieval_permission"],
        "monitoring_readiness_status": p["canonical_schedule_monitoring_readiness_status"],
        "verification_mode": p["canonical_schedule_verification_mode"],
        "canonical_provenance_use": p["canonical_schedule_canonical_provenance_use"],
        "licence_review_status": "CLEARED_FOR_FACTUAL_METADATA",
        "ingestion_permission": "PUBLIC_FACTS_ALLOWED",
        "redistribution_permission": "PUBLIC_FACTUAL_METADATA_ONLY",
    }
    for key, expected in checks.items():
        if schedule.get(key) != expected:
            raise RuntimeError(f"BY NZ election schedule-source pre-state drift for {key}: {schedule.get(key)!r}")

    ids = list(plan["canonical_occurrence_ids"])
    identity = deepcopy(plan["canonical_identity_by_occurrence_id"])
    if len(ids) != EXPECTED_COUNT or len(set(ids)) != EXPECTED_COUNT or set(identity) != set(ids):
        raise RuntimeError("BY requires exact six-occurrence election allow-list and identity map")
    by_id = {r.get("occurrence_id"): r for r in canonical.get("records", []) if r.get("occurrence_id") in set(ids)}
    if set(by_id) != set(ids):
        raise RuntimeError("BY NZ election allow-list no longer matches Canonical")
    all_deps = [r for r in canonical.get("records", []) if r.get("source_id") == CANONICAL_SOURCE_ID]
    if len(all_deps) != EXPECTED_COUNT or {r.get("occurrence_id") for r in all_deps} != set(ids):
        raise RuntimeError("BY NZ election Canonical dependency set drift")

    for occurrence_id in ids:
        row = by_id[occurrence_id]
        expected = identity[occurrence_id]
        row_checks = {
            "series_id": expected["series_id"],
            "source_id": CANONICAL_SOURCE_ID,
            "region": "Oceania / Pacific",
            "source_timezone": TIMEZONE,
            "category": "ELECTIONS_GOVERNANCE",
            "event_type": "ELECTION_MILESTONE",
            "timing_type": "CIVIL_DATE",
            "time_precision": "DAY",
            "all_day_semantics": True,
            "start_local": expected["start_local"],
            "start_utc": None,
            "election_milestone_type": expected["milestone"],
            "lifecycle_status": "PLANNED",
            "certainty_status": "CONFIRMED",
        }
        for key, value in row_checks.items():
            if row.get(key) != value:
                raise RuntimeError(
                    f"BY NZ election Canonical pre-state drift for {occurrence_id} {key}: "
                    f"expected {value!r}, found {row.get(key)!r}"
                )
    return schedule


def new_machine_source(plan: dict) -> dict:
    s = plan["selection"]
    return {
        "source_id": MACHINE_SOURCE_ID,
        "institution": "Electoral Commission New Zealand",
        "jurisdiction": "New Zealand",
        "domain": "elections",
        "endpoint_role": "Official Media & News RSS timetable-page update sentinel",
        "authoritative_url": s["rss_url"],
        "source_type": "official_rss_feed",
        "information_supplied": (
            "Minimal first-party RSS metadata identifying recently updated Elections NZ Media & News pages. "
            "Used only to detect whether the exact 2026 General Election timetable page has re-entered the rolling update feed."
        ),
        "future_schedule_horizon": "not a schedule source; rolling ten-page update sentinel",
        "typical_advance_notice": "source-page update driven",
        "machine_readable_available": "RSS/XML",
        "source_timezone": TIMEZONE,
        "recommended_verification_cadence": "every 6 hours during the 2026 election period",
        "activation_status": "ACTIVE_GUARDED",
        "parser_type": "NZ_ELECTION_MEDIA_NEWS_RSS_TIMETABLE_PAGE_SENTINEL",
        "parser_version": "nz-election-rss-0.1",
        "known_limitations": [
            "The RSS channel contains only the ten most recently updated pages and is not an exhaustive change log.",
            "Absence of the timetable page from the rolling feed is not evidence that the page did not change.",
            "RSS pubDate is page-publication/update metadata and is not Canonical election-event time.",
            "General election news titles and descriptions are not parsed into milestone changes.",
            "A positive exact timetable-page identity produces one six-occurrence bundle review only; it does not identify which milestone changed.",
            "The monitor never automatically fetches the timetable HTML, RSS item pages, election results data or search/discovery routes.",
            "WSSRC-EL-NZ-001 remains the Canonical timetable authority and retains its existing HTML automation hold unchanged."
        ],
        "backup_source": None,
        "notes": "Separate RSS identity preserves the distinction between an advertised subscription interface and held HTML timetable retrieval.",
        "timezone_scope": "PACIFIC_AUCKLAND_RSS_PUBLICATION_METADATA_ONLY_NO_CANONICAL_EVENT_TIME_AUTHORITY",
        "licence_constraints": "MINIMAL_FACTUAL_RSS_METADATA_ONLY_UNDER_EXISTING_PUBLIC_FACTS_CLASSIFICATION_NO_FEED_CONTENT_REPUBLICATION",
        "ingestion_permission": "OFFICIAL_ADVERTISED_RSS_MINIMAL_METADATA_INTERNAL_CHANGE_SENTINEL",
        "licence_review_status": "FACTUAL_METADATA_ONLY_RSS_SUBSCRIPTION_INTERFACE_SEPARATELY_REVIEWED",
        "automated_retrieval_permission": "OFFICIAL_ADVERTISED_RSS_SUBSCRIPTION_INTERFACE_ROBOTS_COMPATIBLE_WITH_CRAWL_DELAY",
        "redistribution_permission": "FACTUAL_UPDATE_FLAGS_ONLY_NO_RSS_DESCRIPTION_OR_ARTICLE_REPUBLICATION",
        "rights_evidence_url": s["canonical_timetable_url"],
        "rights_summary": (
            "The existing election source is cleared only for public factual milestone metadata. BY retains that narrow scope "
            "and does not create a broader right to reproduce RSS descriptions or Commission page content."
        ),
        "automation_evidence_url": s["media_news_url"],
        "automation_summary": (
            "The Electoral Commission advertises its Media & News RSS subscription route. WORLD SIGNALS requests robots.txt, "
            "respects the declared crawl delay, then makes one RSS request. No item or timetable page is automatically followed."
        ),
        "rights_reviewed_at": plan["reference_date"],
        "rights_review_scope": "BY_FACTUAL_REUSE_AND_ADVERTISED_RSS_MACHINE_ACCESS_SEPARATED_FROM_HELD_TIMETABLE_HTML",
        "rights_review_note": "Operational WORLD SIGNALS governance classification; not a legal opinion.",
        "monitoring_readiness_status": "LIVE_VALIDATED_NO_AUTO_COMMIT",
        "monitoring_priority_score": 420,
        "canonical_dependency_count": 0,
        "monitoring_readiness_assessed_at": plan["reference_date"],
        "monitoring_activation_status": "LIVE_READ_ONLY_TIMETABLE_PAGE_UPDATE_SENTINEL_NO_AUTO_COMMIT",
        "last_successful_research_verification_at": plan["reference_date"],
        "canonical_provenance_use": "MONITOR_ONLY_TIMETABLE_PAGE_UPDATE_SENTINEL_NO_CANONICAL_DATE_AUTHORITY",
        "automated_monitoring_use": "CLEARED",
        "verification_mode": "AUTOMATED_PILOT",
        "runtime_health_state": "LIVE_GITHUB_ACTIONS_RSS_FETCH_PARSE_PASS_2026_09_09",
        "governance_backfill_reviewed_at": plan["reference_date"],
        "governance_backfill_basis": (
            "Separate first-party RSS source created because the Electoral Commission advertises RSS subscription access; "
            "the pre-existing timetable HTML source and its automation hold remain unchanged."
        ),
        "live_adapter_id": ADAPTER_ID,
        "live_validation_evidence": {
            "rss_discovery_run_id": plan["read_only_rss_discovery"]["run_id"],
            "rss_discovery_job_id": plan["read_only_rss_discovery"]["job_id"],
            "rss_endpoint_run_id": plan["read_only_rss_endpoint_diagnostic"]["run_id"],
            "rss_endpoint_job_id": plan["read_only_rss_endpoint_diagnostic"]["job_id"],
            "rss_http_status": 200,
            "rss_content_type": "application/rss+xml; charset=utf-8",
            "rss_item_count": 10,
            "rss_sha256": plan["read_only_rss_endpoint_diagnostic"]["rss_sha256"],
            "robots_http_status": 200,
            "robots_declared_crawl_delay_seconds": 2,
            "request_count": 2,
            "followup_request_count": 0,
            "automatic_commit_allowed": False,
        },
        "related_source_ids": [CANONICAL_SOURCE_ID],
        "source_role_contract": deepcopy(plan["source_role_contract"]),
        "monitor_endpoints": [
            {
                "endpoint_role": "elections_nz_media_news_rss",
                "url": s["rss_url"],
                "transport": "RSS_XML",
                "preferred_for_monitoring": True,
                "completeness_scope": "TEN_MOST_RECENTLY_UPDATED_PAGES_ROLLING_WINDOW",
                "notes": "One RSS request after robots check and crawl delay; no automatic item-link follow-up."
            },
            {
                "endpoint_role": "robots_policy",
                "url": s["robots_url"],
                "transport": "TEXT_PLAIN",
                "preferred_for_monitoring": True,
                "completeness_scope": "AUTOMATION_POLICY_AND_CRAWL_DELAY_GATE"
            },
            {
                "endpoint_role": "canonical_timetable_manual_recheck_only",
                "url": s["canonical_timetable_url"],
                "transport": "HTML_MANUAL_GOVERNANCE_REFERENCE",
                "preferred_for_monitoring": False,
                "completeness_scope": "CANONICAL_TIMETABLE_AUTHORITY_NOT_AUTOMATICALLY_FETCHED_BY_BY"
            }
        ]
    }


def monitor_expectation(plan: dict) -> dict:
    s = plan["selection"]
    r = plan["request_contract"]
    roll = plan["rolling_feed_contract"]
    return {
        "adapter_id": ADAPTER_ID,
        "source_id": MACHINE_SOURCE_ID,
        "canonical_schedule_source_id": CANONICAL_SOURCE_ID,
        "canonical_occurrence_ids": list(plan["canonical_occurrence_ids"]),
        "canonical_timetable_page_identity": s["canonical_timetable_url"],
        "monitor_role": "OFFICIAL_ELECTIONS_NZ_RSS_TIMETABLE_PAGE_UPDATE_SENTINEL",
        "cadence": roll["recommended_cadence"],
        "cadence_is_monitor_metadata_not_new_scheduler_authority": True,
        "request_budget_per_run": r["request_budget_per_run"],
        "robots_request_count_per_run": r["robots_requests_per_run"],
        "rss_request_count_per_run": r["rss_requests_per_run"],
        "minimum_inter_request_delay_seconds": r["minimum_inter_request_delay_seconds"],
        "respect_greater_live_robots_crawl_delay": r["respect_greater_live_robots_crawl_delay"],
        "timetable_html_request_count_per_run": r["timetable_html_requests_per_run"],
        "item_followup_request_count_per_run": r["item_followup_requests_per_run"],
        "results_data_request_count_per_run": r["results_data_requests_per_run"],
        "search_route_discovery_request_count_per_run": r["search_route_discovery_requests_per_run"],
        "feed": {
            "url": s["rss_url"],
            "transport": "RSS_XML",
            "request_policy": "ROBOTS_THEN_CRAWL_DELAY_THEN_ONE_OFFICIAL_RSS_REQUEST"
        },
        "classification_contract": deepcopy(plan["classification_contract"]),
        "source_role_contract": deepcopy(plan["source_role_contract"]),
        "rolling_feed_completeness": roll["completeness"],
        "rolling_feed_expected_item_count": roll["expected_item_count"],
        "rolling_feed_channel_title": roll["channel_title"],
        "rolling_feed_channel_description": roll["channel_description"],
        "absence_semantics": roll["absence_semantics"],
        "source_failure_policy": "SOURCE_HEALTH_ONLY_NO_EVENT_MUTATION",
        "positive_change_policy": "EXACT_TIMETABLE_LINK_AND_GUID_GENERATES_ONE_SIX_OCCURRENCE_BUNDLE_REVIEW_ONLY",
        "absence_policy": "ROLLING_FEED_ABSENCE_HAS_NO_PAGE_UNCHANGED_OR_EVENT_STATE_SEMANTICS",
        "outside_scope_policy": "OBSERVE_ONLY_NO_MILESTONE_CHANGE_INFERENCE",
        "schedule_authority": False,
        "clock_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "canonical_date_mutation_allowed": False,
        "automatic_timetable_html_fetch_allowed": False,
        "automatic_item_link_fetch_allowed": False,
        "automatic_results_data_fetch_allowed": False,
        "automatic_search_route_discovery_allowed": False,
        "automatic_live_or_analysis_promotion_allowed": False,
        "live_intelligence_policy": "NO_AUTOMATIC_PROMOTION_TO_LIVE_INTELLIGENCE_OR_ANALYSIS",
        "automatic_commit_allowed": False,
    }


def transform_sources(sources: dict, plan: dict, schedule_before: dict) -> dict:
    out = deepcopy(sources)
    if source_by_id(out, CANONICAL_SOURCE_ID) != schedule_before:
        raise RuntimeError("BY NZ election timetable source changed before transformation")
    before = deepcopy(out["sources"])
    out["sources"].append(new_machine_source(plan))
    if out["sources"][:-1] != before:
        raise RuntimeError("BY modified an existing source while appending NZ election RSS identity")
    if source_by_id(out, CANONICAL_SOURCE_ID) != schedule_before:
        raise RuntimeError("BY changed NZ election Canonical timetable source")
    out["version"] = plan["postconditions"]["source_registry_version"]
    out["reference_date"] = plan["reference_date"]
    return out


def transform_expectations(expectations: dict, plan: dict) -> dict:
    out = deepcopy(expectations)
    before = deepcopy(out.get("adapters", []))
    out["adapters"].append(monitor_expectation(plan))
    if out["adapters"][:-1] != before:
        raise RuntimeError("BY changed an existing monitor route")
    out["version"] = plan["postconditions"]["monitor_expectations_version"]
    if out.get("automatic_canonical_commit") is not False or out.get("google_calendar_write") is not False:
        raise RuntimeError("BY changed global write gates")
    return out


def _replace_once(text: str, anchor: str, replacement: str, label: str) -> str:
    if text.count(anchor) != 1:
        raise RuntimeError(f"BY expected exactly one {label} anchor, found {text.count(anchor)}")
    return text.replace(anchor, replacement, 1)


def patch_adapter_init(text: str) -> str:
    if "NZ_ELECTION_RSS_URL" in text or "fetch_nz_election_rss" in text:
        raise RuntimeError("BY NZ election RSS adapter already exported")
    import_anchor = "from .ons_release_calendar import (\n"
    block = '''from .nz_election_rss import (\n    NZ_ELECTION_CHANNEL_DESCRIPTION,\n    NZ_ELECTION_CHANNEL_TITLE,\n    NZ_ELECTION_EXPECTED_ITEM_COUNT,\n    NZ_ELECTION_MEDIA_NEWS_URL,\n    NZ_ELECTION_MINIMUM_DELAY_SECONDS,\n    NZ_ELECTION_ROBOTS_URL,\n    NZ_ELECTION_RSS_ACCEPT,\n    NZ_ELECTION_RSS_URL,\n    NZ_ELECTION_TIMETABLE_URL,\n    NZElectionRSSItem,\n    fetch_nz_election_robots_policy,\n    fetch_nz_election_rss,\n    nz_election_rss_access_policy,\n    parse_nz_election_rss,\n)\n'''
    text = _replace_once(text, import_anchor, block + import_anchor, "adapter import")
    all_anchor = '    "ONS_RELEASE_CALENDAR",\n'
    all_block = '''    "NZ_ELECTION_CHANNEL_DESCRIPTION",\n    "NZ_ELECTION_CHANNEL_TITLE",\n    "NZ_ELECTION_EXPECTED_ITEM_COUNT",\n    "NZ_ELECTION_MEDIA_NEWS_URL",\n    "NZ_ELECTION_MINIMUM_DELAY_SECONDS",\n    "NZ_ELECTION_ROBOTS_URL",\n    "NZ_ELECTION_RSS_ACCEPT",\n    "NZ_ELECTION_RSS_URL",\n    "NZ_ELECTION_TIMETABLE_URL",\n    "NZElectionRSSItem",\n    "fetch_nz_election_robots_policy",\n    "fetch_nz_election_rss",\n    "nz_election_rss_access_policy",\n    "parse_nz_election_rss",\n'''
    return _replace_once(text, all_anchor, all_block + all_anchor, "adapter __all__")


def _patch_time_import(text: str, label: str) -> str:
    if "\nimport time\n" in text:
        return text
    anchor = "import sys\n"
    return _replace_once(text, anchor, anchor + "import time\n", f"{label} time import")


def patch_live_runner(text: str) -> str:
    if "nz_election_timetable_change_review_candidates" in text or '"NZ_ELECTION_TIMETABLE_CHANGE_RSS" in configs' in text:
        raise RuntimeError("BY NZ election RSS live wiring already exists")
    text = _patch_time_import(text, "live")
    fetch_anchor = "    fetch_ons_upcoming_releases,\n"
    text = _replace_once(
        text,
        fetch_anchor,
        "    fetch_nz_election_robots_policy,\n    fetch_nz_election_rss,\n" + fetch_anchor,
        "live fetch import",
    )
    monitor_anchor = "from world_signals.nbs_release_monitor import nbs_native_rss_review_candidates\n"
    text = _replace_once(
        text,
        monitor_anchor,
        monitor_anchor + "from world_signals.nz_election_monitor import nz_election_timetable_change_review_candidates\n",
        "live comparator import",
    )
    route_anchor = '    if "CHINA_NBS_LATEST_RELEASES_RSS" in configs:\n'
    block = '''    if "NZ_ELECTION_TIMETABLE_CHANGE_RSS" in configs:\n        nz_config=configs["NZ_ELECTION_TIMETABLE_CHANGE_RSS"]\n        try:\n            nz_allowed,nz_delay,nz_robots_snap=fetch_nz_election_robots_policy()\n            if not nz_allowed:\n                report["source_health"].append({\n                    "adapter_id":"NZ_ELECTION_TIMETABLE_CHANGE_RSS",\n                    "source_id":nz_config["source_id"],\n                    "state":"DEGRADED",\n                    "robots_snapshot":nz_robots_snap.as_dict(),\n                    "failure_stage":"ROBOTS_POLICY_NOW_DISALLOWS_ADVERTISED_RSS",\n                    "rss_request_skipped":True,\n                    "request_count":1,\n                    "canonical_action":"NONE",\n                    "schedule_authority":False,\n                    "clock_authority":False,\n                    "lifecycle_authority":False,\n                    "certainty_authority":False,\n                    "automatic_timetable_html_fetch_allowed":False,\n                    "automatic_item_link_fetch_allowed":False,\n                    "automatic_commit_allowed":False,\n                })\n            else:\n                time.sleep(nz_delay)\n                nz_items,nz_rss_snap=fetch_nz_election_rss()\n                report["source_health"].append({\n                    "adapter_id":"NZ_ELECTION_TIMETABLE_CHANGE_RSS",\n                    "source_id":nz_config["source_id"],\n                    "state":"HEALTHY",\n                    "robots_snapshot":nz_robots_snap.as_dict(),\n                    "rss_snapshot":nz_rss_snap.as_dict(),\n                    "rolling_feed_item_count":len(nz_items),\n                    "request_budget_per_run":2,\n                    "request_count":2,\n                    "robots_request_count":1,\n                    "rss_request_count":1,\n                    "inter_request_delay_seconds":nz_delay,\n                    "timetable_html_request_count":0,\n                    "item_followup_request_count":0,\n                    "results_data_request_count":0,\n                    "search_route_discovery_request_count":0,\n                    "rolling_feed_completeness":"FINITE_ROLLING_WINDOW_NOT_EXHAUSTIVE_CHANGE_LOG",\n                    "schedule_authority":False,\n                    "clock_authority":False,\n                    "lifecycle_authority":False,\n                    "certainty_authority":False,\n                    "canonical_date_mutation_allowed":False,\n                    "automatic_timetable_html_fetch_allowed":False,\n                    "automatic_item_link_fetch_allowed":False,\n                    "automatic_live_or_analysis_promotion_allowed":False,\n                    "automatic_commit_allowed":False,\n                })\n                candidates,observations=nz_election_timetable_change_review_candidates(\n                    registry.get("records",[]),nz_items,nz_config\n                )\n                report["review_candidates"].extend(candidates)\n                report["observations"].extend(observations)\n        except (AdapterError,ValueError) as exc:\n            report["source_health"].append({\n                "adapter_id":"NZ_ELECTION_TIMETABLE_CHANGE_RSS",\n                "source_id":nz_config["source_id"],\n                "state":"DEGRADED",\n                "error":str(exc),\n                "canonical_action":"NONE",\n                "absence_is_not_event_state":True,\n                "schedule_authority":False,\n                "clock_authority":False,\n                "lifecycle_authority":False,\n                "certainty_authority":False,\n                "canonical_date_mutation_allowed":False,\n                "automatic_timetable_html_fetch_allowed":False,\n                "automatic_item_link_fetch_allowed":False,\n                "automatic_live_or_analysis_promotion_allowed":False,\n                "automatic_commit_allowed":False,\n            })\n\n'''
    return _replace_once(text, route_anchor, block + route_anchor, "live route")


def patch_smoke_runner(text: str) -> str:
    if '"NZ_ELECTION_TIMETABLE_CHANGE_RSS"' in text or "fetch_nz_election_robots_policy" in text:
        raise RuntimeError("BY NZ election RSS smoke wiring already exists")
    text = _patch_time_import(text, "smoke")
    fetch_anchor = "    fetch_ons_upcoming_releases,\n"
    text = _replace_once(
        text,
        fetch_anchor,
        "    fetch_nz_election_robots_policy,\n    fetch_nz_election_rss,\n" + fetch_anchor,
        "smoke fetch import",
    )
    route_anchor = '    try:\n        nbs_items,nbs_snap=fetch_nbs_native_latest_releases_rss()\n'
    block = '''    try:\n        nz_allowed,nz_delay,nz_robots_snap=fetch_nz_election_robots_policy()\n        if not nz_allowed:\n            raise AdapterError("Elections NZ robots policy disallows the advertised Media & News RSS path")\n        time.sleep(nz_delay)\n        nz_items,nz_rss_snap=fetch_nz_election_rss()\n        report["results"].append({\n            "adapter":"NZ_ELECTION_TIMETABLE_CHANGE_RSS",\n            "status":"PASS",\n            "source_id":"WSSRC-EL-NZ-002",\n            "robots_snapshot":nz_robots_snap.as_dict(),\n            "rss_snapshot":nz_rss_snap.as_dict(),\n            "rolling_feed_item_count":len(nz_items),\n            "request_budget_per_run":2,\n            "robots_request_count":1,\n            "rss_request_count":1,\n            "inter_request_delay_seconds":nz_delay,\n            "timetable_html_request_count":0,\n            "item_followup_request_count":0,\n            "results_data_request_count":0,\n            "search_route_discovery_request_count":0,\n            "rolling_feed_completeness":"FINITE_ROLLING_WINDOW_NOT_EXHAUSTIVE_CHANGE_LOG",\n            "schedule_authority":False,\n            "clock_authority":False,\n            "lifecycle_authority":False,\n            "certainty_authority":False,\n            "canonical_date_mutation_allowed":False,\n            "automatic_timetable_html_fetch_allowed":False,\n            "automatic_item_link_fetch_allowed":False,\n            "automatic_commit_allowed":False,\n        })\n    except (AdapterError,ValueError) as exc:\n        failures.append({"adapter":"NZ_ELECTION_TIMETABLE_CHANGE_RSS","error":str(exc)})\n        report["results"].append({\n            "adapter":"NZ_ELECTION_TIMETABLE_CHANGE_RSS",\n            "status":"FAIL",\n            "source_id":"WSSRC-EL-NZ-002",\n            "error":str(exc),\n            "canonical_action":"NONE",\n        })\n\n'''
    return _replace_once(text, route_anchor, block + route_anchor, "smoke route")


def validate_post_state(
    canonical: dict,
    sources: dict,
    expectations: dict,
    schedule_before: dict,
    plan: dict,
) -> None:
    p = plan["postconditions"]
    if (canonical.get("version"), len(canonical.get("records", []))) != (
        p["canonical_registry_version"], p["canonical_record_count"]
    ):
        raise RuntimeError("BY changed Canonical post-state")
    if (sources.get("version"), len(sources.get("sources", []))) != (
        p["source_registry_version"], p["source_count"]
    ):
        raise RuntimeError("BY source post-state mismatch")
    if (expectations.get("version"), len(expectations.get("adapters", []))) != (
        p["monitor_expectations_version"], p["configured_monitor_adapter_count"]
    ):
        raise RuntimeError("BY monitor post-state mismatch")
    if source_by_id(sources, CANONICAL_SOURCE_ID) != schedule_before:
        raise RuntimeError("BY changed WSSRC-EL-NZ-001")
    machine = source_by_id(sources, MACHINE_SOURCE_ID)
    if machine.get("canonical_dependency_count") != 0:
        raise RuntimeError("BY machine source must have zero Canonical dependencies")
    if machine.get("canonical_provenance_use") != "MONITOR_ONLY_TIMETABLE_PAGE_UPDATE_SENTINEL_NO_CANONICAL_DATE_AUTHORITY":
        raise RuntimeError("BY machine source acquired Canonical date authority")
    if machine.get("automated_monitoring_use") != "CLEARED":
        raise RuntimeError("BY machine source monitoring clearance mismatch")
    route = route_by_id(expectations, ADAPTER_ID)
    if route.get("source_id") != MACHINE_SOURCE_ID or route.get("canonical_schedule_source_id") != CANONICAL_SOURCE_ID:
        raise RuntimeError("BY route source-role decomposition mismatch")
    if len(route.get("canonical_occurrence_ids", [])) != EXPECTED_COUNT:
        raise RuntimeError("BY route must configure exactly six occurrences")
    if route.get("canonical_timetable_page_identity") != plan["selection"]["canonical_timetable_url"]:
        raise RuntimeError("BY exact timetable-page identity mismatch")
    if route.get("request_budget_per_run") != 2 or route.get("robots_request_count_per_run") != 1 or route.get("rss_request_count_per_run") != 1:
        raise RuntimeError("BY route request budget mismatch")
    if route.get("minimum_inter_request_delay_seconds") != 2:
        raise RuntimeError("BY route minimum crawl-delay mismatch")
    for key in (
        "timetable_html_request_count_per_run",
        "item_followup_request_count_per_run",
        "results_data_request_count_per_run",
        "search_route_discovery_request_count_per_run",
    ):
        if route.get(key) != 0:
            raise RuntimeError(f"BY route follow-up request count must remain zero: {key}")
    for key in (
        "schedule_authority",
        "clock_authority",
        "lifecycle_authority",
        "certainty_authority",
        "canonical_date_mutation_allowed",
        "automatic_timetable_html_fetch_allowed",
        "automatic_item_link_fetch_allowed",
        "automatic_results_data_fetch_allowed",
        "automatic_search_route_discovery_allowed",
        "automatic_live_or_analysis_promotion_allowed",
        "automatic_commit_allowed",
    ):
        if route.get(key) is not False:
            raise RuntimeError(f"BY route gate must remain false: {key}")
    if route.get("rolling_feed_completeness") != "FINITE_ROLLING_WINDOW_NOT_EXHAUSTIVE_CHANGE_LOG":
        raise RuntimeError("BY route lost rolling-window limitation")
    if route.get("absence_semantics") != "NONE":
        raise RuntimeError("BY route absence acquired event-state meaning")
    if expectations.get("automatic_canonical_commit") is not False or expectations.get("google_calendar_write") is not False:
        raise RuntimeError("BY changed global write gates")


def simulate() -> tuple[dict, dict, str, str, str, dict]:
    plan = load_json(PLAN_PATH)
    canonical = load_json(CANONICAL_PATH)
    sources = load_json(SOURCES_PATH)
    expectations = load_json(EXPECTATIONS_PATH)
    schedule_before = preflight(canonical, sources, expectations, plan)
    post_sources = transform_sources(sources, plan, schedule_before)
    post_expectations = transform_expectations(expectations, plan)
    post_adapter_init = patch_adapter_init(ADAPTER_INIT_PATH.read_text(encoding="utf-8"))
    post_live_runner = patch_live_runner(LIVE_RUNNER_PATH.read_text(encoding="utf-8"))
    post_smoke_runner = patch_smoke_runner(SMOKE_RUNNER_PATH.read_text(encoding="utf-8"))
    validate_post_state(canonical, post_sources, post_expectations, schedule_before, plan)
    report = {
        "tranche": "BY",
        "mode": "READ_ONLY_PREFLIGHT",
        "base_sha": BASE_SHA,
        "canonical_source_id": CANONICAL_SOURCE_ID,
        "machine_source_id": MACHINE_SOURCE_ID,
        "adapter_id": ADAPTER_ID,
        "source_count_before": len(sources["sources"]),
        "source_count_after": len(post_sources["sources"]),
        "source_version_before": sources["version"],
        "source_version_after": post_sources["version"],
        "monitor_version_before": expectations["version"],
        "monitor_version_after": post_expectations["version"],
        "monitor_count_before": len(expectations["adapters"]),
        "monitor_count_after": len(post_expectations["adapters"]),
        "configured_occurrence_count": EXPECTED_COUNT,
        "canonical_schedule_source_unchanged": source_by_id(post_sources, CANONICAL_SOURCE_ID) == schedule_before,
        "canonical_changed": False,
        "automatic_canonical_commit": post_expectations["automatic_canonical_commit"],
        "google_calendar_write": post_expectations["google_calendar_write"],
        "mutation_paths": [str(path.relative_to(ROOT)) for path in MUTATION_PATHS],
    }
    return post_sources, post_expectations, post_adapter_init, post_live_runner, post_smoke_runner, report


def run(*, apply: bool) -> dict:
    canonical_before = CANONICAL_PATH.read_bytes()
    post_sources, post_expectations, post_adapter_init, post_live_runner, post_smoke_runner, report = simulate()
    if not apply:
        if CANONICAL_PATH.read_bytes() != canonical_before:
            raise RuntimeError("BY check-only path unexpectedly changed Canonical")
        return report
    if os.getenv(APPLY_ENV) != "1":
        raise RuntimeError(f"BY APPLY REFUSED: set {APPLY_ENV}=1")
    dump_json(SOURCES_PATH, post_sources)
    dump_json(EXPECTATIONS_PATH, post_expectations)
    ADAPTER_INIT_PATH.write_text(post_adapter_init, encoding="utf-8")
    LIVE_RUNNER_PATH.write_text(post_live_runner, encoding="utf-8")
    SMOKE_RUNNER_PATH.write_text(post_smoke_runner, encoding="utf-8")
    if CANONICAL_PATH.read_bytes() != canonical_before:
        raise RuntimeError("BY apply path changed Canonical")
    report["mode"] = "APPLIED_GOVERNED_RUNTIME_PATCH"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Guarded BY activation helper for Elections NZ RSS timetable-page update sentinel. "
            f"Default is read-only; --apply additionally requires {APPLY_ENV}=1."
        )
    )
    parser.add_argument("--apply", action="store_true", help="materialise the exact five-file governed/runtime patch")
    args = parser.parse_args()
    try:
        report = run(apply=args.apply)
    except Exception as exc:
        print(f"BY NZ ELECTION RSS PRECONDITION FAILED: {exc}")
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
