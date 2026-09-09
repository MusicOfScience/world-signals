from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/monitor/EUROPEAN_COUNCIL_MEETINGS_RSS_BZ_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
LIVE_RUNNER_PATH = ROOT / "scripts/run_live_monitor.py"
SMOKE_RUNNER_PATH = ROOT / "scripts/run_adapter_smoke.py"
ADAPTER_INIT_PATH = ROOT / "src/world_signals/adapters/__init__.py"

APPLY_ENV = "WORLD_SIGNALS_APPLY_MONITOR_BZ"
BASE_SHA = "3ccb20539c10d0965de84efa298ba75634c19249"
CANONICAL_SOURCE_ID = "WSSRC-INT-003"
MACHINE_SOURCE_ID = "WSSRC-INT-035"
ADAPTER_ID = "EUROPEAN_COUNCIL_MEETINGS_RSS"
TIMEZONE = "Europe/Brussels"
EXPECTED_COUNT = 3

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
        raise RuntimeError("BZ plan is not frozen to exact post-BY main")
    if (canonical.get("version"), len(canonical.get("records", []))) != (
        p["canonical_registry_version"], p["canonical_record_count"]
    ):
        raise RuntimeError("BZ requires exact Canonical v0.41 / 689")
    if (sources.get("version"), len(sources.get("sources", []))) != (
        p["source_registry_version"], p["source_count"]
    ):
        raise RuntimeError("BZ requires exact Sources v1.98 / 254")
    if (expectations.get("version"), len(expectations.get("adapters", []))) != (
        p["monitor_expectations_version"], p["configured_monitor_adapter_count"]
    ):
        raise RuntimeError("BZ requires exact Monitor v0.23 / 21")
    if expectations.get("automatic_canonical_commit") is not False:
        raise RuntimeError("automatic Canonical commit gate must remain closed")
    if expectations.get("google_calendar_write") is not False:
        raise RuntimeError("Google Calendar write gate must remain closed")
    if any(row.get("source_id") == MACHINE_SOURCE_ID for row in sources.get("sources", [])):
        raise RuntimeError("BZ European Council RSS machine source already exists")
    if any(row.get("adapter_id") == ADAPTER_ID for row in expectations.get("adapters", [])):
        raise RuntimeError("BZ European Council RSS route already exists")

    schedule = deepcopy(source_by_id(sources, CANONICAL_SOURCE_ID))
    checks = {
        "institution": "European Council / Council of the EU",
        "jurisdiction": "European Union",
        "domain": "international_institutions",
        "endpoint_role": "Meetings calendar",
        "authoritative_url": plan["selection"]["canonical_calendar_url"],
        "source_type": "official_calendar",
        "source_timezone": TIMEZONE,
        "canonical_dependency_count": p["canonical_schedule_dependency_count"],
        "automated_retrieval_permission": p["canonical_schedule_automated_retrieval_permission"],
        "monitoring_readiness_status": p["canonical_schedule_monitoring_readiness_status"],
        "runtime_health_state": p["canonical_schedule_runtime_health_state"],
        "licence_review_status": p["canonical_schedule_licence_review_status"],
        "ingestion_permission": "CURATED_FACTUAL_METADATA_ALLOWED",
        "redistribution_permission": "REUSE_ALLOWED_WITH_SOURCE_MEANING_PRESERVED_AND_CHANGES_DISCLOSED",
    }
    for key, expected in checks.items():
        if schedule.get(key) != expected:
            raise RuntimeError(f"BZ European Council schedule-source pre-state drift for {key}: {schedule.get(key)!r}")

    ids = list(plan["canonical_occurrence_ids"])
    if len(ids) != EXPECTED_COUNT or len(set(ids)) != EXPECTED_COUNT:
        raise RuntimeError("BZ requires exact three-occurrence European Council allow-list")
    identity = plan["configured_feed_identity_by_guid"]
    if len(identity) != EXPECTED_COUNT:
        raise RuntimeError("BZ requires exact three GUID identities")
    if {x["occurrence_id"] for x in identity.values()} != set(ids):
        raise RuntimeError("BZ GUID-to-occurrence identity map drift")

    by_id = {r.get("occurrence_id"): r for r in canonical.get("records", []) if r.get("occurrence_id") in set(ids)}
    if set(by_id) != set(ids):
        raise RuntimeError("BZ European Council allow-list no longer matches Canonical")
    all_deps = [r for r in canonical.get("records", []) if r.get("source_id") == CANONICAL_SOURCE_ID]
    if len(all_deps) != EXPECTED_COUNT or {r.get("occurrence_id") for r in all_deps} != set(ids):
        raise RuntimeError("BZ European Council Canonical dependency set drift")

    for guid, expected in identity.items():
        row = by_id[expected["occurrence_id"]]
        row_checks = {
            "series_id": expected["series_id"],
            "source_id": CANONICAL_SOURCE_ID,
            "region": "Europe",
            "source_timezone": TIMEZONE,
            "category": "INTERNATIONAL_INSTITUTIONS",
            "event_type": "INSTITUTIONAL_MEETING",
            "time_precision": "DAY",
            "all_day_semantics": True,
            "start_local": expected["baseline_start_local"],
            "end_local": expected["baseline_end_local"],
            "start_utc": None,
            "end_utc": None,
            "lifecycle_status": "PLANNED",
            "certainty_status": "CONFIRMED",
        }
        expected_timing = "CIVIL_DATE" if expected["baseline_end_local"] is None else "MULTI_DAY_LOCAL"
        row_checks["timing_type"] = expected_timing
        for key, value in row_checks.items():
            if row.get(key) != value:
                raise RuntimeError(
                    f"BZ European Council Canonical pre-state drift for {guid}/{expected['occurrence_id']} {key}: "
                    f"expected {value!r}, found {row.get(key)!r}"
                )
    return schedule


def new_machine_source(plan: dict) -> dict:
    s = plan["selection"]
    diagnostic = plan["rss_endpoint_diagnostic"]
    field_diagnostic = plan["rss_field_contract_diagnostic"]
    return {
        "source_id": MACHINE_SOURCE_ID,
        "institution": "European Council / Council of the EU",
        "jurisdiction": "European Union",
        "domain": "international_institutions",
        "endpoint_role": "Official European Council meetings RSS date-change sentinel",
        "authoritative_url": s["rss_url"],
        "source_type": "official_rss_feed",
        "information_supplied": (
            "Minimal first-party European Council meetings RSS identity and date-bearing link metadata used to compare "
            "three already-modelled forward European Council occurrences and surface unconfigured future meeting items for review."
        ),
        "future_schedule_horizon": "rolling European Council meetings feed; feed item count is bounded but not frozen",
        "typical_advance_notice": "months, as reflected in the official feed",
        "machine_readable_available": "RSS/XML",
        "source_timezone": TIMEZONE,
        "recommended_verification_cadence": "daily",
        "activation_status": "ACTIVE_GUARDED",
        "parser_type": "EUROPEAN_COUNCIL_MEETINGS_RSS_DATE_SENTINEL",
        "parser_version": "euco-rss-0.1",
        "known_limitations": [
            "The RSS feed is a separate machine interface and does not remove the automation hold on the direct meetings-calendar HTML source.",
            "The current feed item count is not treated as a permanent completeness invariant.",
            "Configured meeting identity is the stable numeric GUID; observed civil dates are parsed only from exact first-party European Council meeting URL paths.",
            "RSS description and updated fields are not event-time authority.",
            "Missing configured GUIDs require review but do not imply cancellation, completion or certainty change.",
            "Unconfigured future meeting items are observations only and never create Canonical occurrences automatically.",
            "No RSS item page, direct calendar HTML or search/discovery route is automatically followed."
        ],
        "backup_source": None,
        "notes": "Separate RSS identity preserves the held Canonical HTML source while using Consilium's purpose-built automatic-loading interface.",
        "timezone_scope": "EUROPE_BRUSSELS_CIVIL_DATE_METADATA_ONLY_NO_CLOCK_AUTHORITY",
        "licence_constraints": "REUSE_WITH_ATTRIBUTION_SOURCE_MEANING_PRESERVED_CHANGES_DISCLOSED_MINIMAL_FACTUAL_RSS_METADATA",
        "ingestion_permission": "OFFICIAL_ADVERTISED_RSS_MINIMAL_FACTUAL_METADATA_INTERNAL_CHANGE_SENTINEL",
        "licence_review_status": "CLEARED_COUNCIL_EU_REUSE_WITH_ATTRIBUTION_RSS_INTERFACE_SEPARATELY_REVIEWED",
        "automated_retrieval_permission": "OFFICIAL_CONSILIUM_RSS_AUTOMATIC_LOADING_INTERFACE",
        "redistribution_permission": "FACTUAL_UPDATE_FLAGS_ONLY_WITH_ATTRIBUTION_NO_FEED_OR_ARTICLE_REPUBLICATION",
        "rights_evidence_url": s["copyright_url"],
        "rights_summary": (
            "Consilium permits reuse subject to source acknowledgement, preservation of original meaning and disclosure of changes; "
            "BZ retains only minimal factual feed metadata and does not broaden that permission."
        ),
        "automation_evidence_url": s["rss_documentation_url"],
        "automation_summary": (
            "Consilium's RSS documentation describes RSS as machine-readable and suitable for automatic loading onto computers or websites. "
            "WORLD SIGNALS makes one request to the dedicated European Council meetings feed and performs no HTML or item follow-up."
        ),
        "rights_reviewed_at": plan["reference_date"],
        "rights_review_scope": "BZ_COUNCIL_REUSE_AND_PURPOSE_BUILT_RSS_MACHINE_ACCESS_SEPARATED_FROM_HELD_CALENDAR_HTML",
        "rights_review_note": "Operational WORLD SIGNALS governance classification; not a legal opinion.",
        "monitoring_readiness_status": "LIVE_VALIDATED_NO_AUTO_COMMIT",
        "monitoring_priority_score": 430,
        "canonical_dependency_count": 0,
        "monitoring_readiness_assessed_at": plan["reference_date"],
        "monitoring_activation_status": "LIVE_READ_ONLY_EUROPEAN_COUNCIL_DATE_CHANGE_SENTINEL_NO_AUTO_COMMIT",
        "last_successful_research_verification_at": plan["reference_date"],
        "canonical_provenance_use": "MONITOR_ONLY_EUROPEAN_COUNCIL_RSS_NO_CANONICAL_DATE_AUTHORITY",
        "automated_monitoring_use": "CLEARED",
        "verification_mode": "AUTOMATED_PILOT",
        "runtime_health_state": "LIVE_GITHUB_ACTIONS_RSS_FETCH_PARSE_PASS_2026_09_09",
        "governance_backfill_reviewed_at": plan["reference_date"],
        "governance_backfill_basis": (
            "Separate first-party RSS source created because Consilium explicitly advertises RSS for automatic loading; "
            "the pre-existing direct calendar HTML source remains unchanged and endpoint-held."
        ),
        "live_adapter_id": ADAPTER_ID,
        "live_validation_evidence": {
            "rss_endpoint_run_id": diagnostic["run_id"],
            "rss_endpoint_job_id": diagnostic["job_id"],
            "rss_field_contract_run_id": field_diagnostic["run_id"],
            "rss_field_contract_job_id": field_diagnostic["job_id"],
            "rss_http_status": diagnostic["rss_http_status"],
            "rss_content_type": diagnostic["rss_content_type"],
            "rss_body_bytes": diagnostic["rss_body_bytes"],
            "rss_item_count_observed_not_frozen": diagnostic["rss_item_count"],
            "rss_sha256_observed_not_frozen": diagnostic["rss_sha256"],
            "configured_guid_count": diagnostic["configured_guid_count"],
            "request_count": 1,
            "direct_calendar_html_request_count": 0,
            "item_followup_request_count": 0,
            "automatic_commit_allowed": False,
        },
        "related_source_ids": [CANONICAL_SOURCE_ID],
        "source_role_contract": deepcopy(plan["source_role_contract"]),
        "monitor_endpoints": [
            {
                "endpoint_role": "european_council_meetings_rss",
                "url": s["rss_url"],
                "transport": "RSS_XML",
                "preferred_for_monitoring": True,
                "completeness_scope": "ROLLING_EUROPEAN_COUNCIL_MEETINGS_FEED_ITEM_COUNT_NOT_FROZEN",
                "notes": "One direct RSS request per monitor run; no item-link or calendar-HTML follow-up."
            },
            {
                "endpoint_role": "canonical_calendar_manual_recheck_only",
                "url": s["canonical_calendar_url"],
                "transport": "HTML_MANUAL_GOVERNANCE_REFERENCE",
                "preferred_for_monitoring": False,
                "completeness_scope": "CANONICAL_CALENDAR_AUTHORITY_REMAINS_ENDPOINT_HELD"
            }
        ]
    }


def monitor_expectation(plan: dict) -> dict:
    s = plan["selection"]
    r = plan["request_contract"]
    identity = plan["configured_feed_identity_by_guid"]
    return {
        "adapter_id": ADAPTER_ID,
        "source_id": MACHINE_SOURCE_ID,
        "canonical_schedule_source_id": CANONICAL_SOURCE_ID,
        "canonical_occurrence_ids": list(plan["canonical_occurrence_ids"]),
        "monitor_role": "OFFICIAL_EUROPEAN_COUNCIL_MEETINGS_RSS_DATE_CHANGE_SENTINEL",
        "cadence": "daily",
        "cadence_is_monitor_metadata_not_new_scheduler_authority": True,
        "request_budget_per_run": r["request_budget_per_run"],
        "rss_request_count_per_run": r["rss_requests_per_run"],
        "robots_request_count_per_run": r["robots_requests_per_run"],
        "direct_calendar_html_request_count_per_run": r["direct_calendar_html_requests_per_run"],
        "item_followup_request_count_per_run": r["item_followup_requests_per_run"],
        "search_route_discovery_request_count_per_run": r["search_route_discovery_requests_per_run"],
        "machine_access_basis": "OFFICIAL_CONSILIUM_RSS_AUTOMATIC_LOADING_INTERFACE",
        "feed": {
            "url": s["rss_url"],
            "transport": "RSS_XML",
            "request_policy": "ONE_PURPOSE_BUILT_OFFICIAL_RSS_REQUEST_NO_FOLLOWUPS"
        },
        "configured_guid_to_occurrence": {guid: row["occurrence_id"] for guid, row in identity.items()},
        "configured_guid_titles": {guid: row["expected_title"] for guid, row in identity.items()},
        "observed_date_source": "OFFICIAL_RSS_ITEM_LINK_PATH_ONLY",
        "updated_field_is_event_time": False,
        "description_field_is_event_time": False,
        "feed_item_count_is_permanent_invariant": False,
        "absence_semantics": "NONE",
        "unconfigured_item_review_floor_local": plan["monitor_review_window"]["unconfigured_item_review_floor_local"],
        "classification_contract": deepcopy(plan["classification_contract"]),
        "source_role_contract": deepcopy(plan["source_role_contract"]),
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
        "live_intelligence_policy": "NO_AUTOMATIC_PROMOTION_TO_LIVE_INTELLIGENCE_OR_ANALYSIS",
        "automatic_commit_allowed": False,
    }


def transform_sources(sources: dict, plan: dict, schedule_before: dict) -> dict:
    out = deepcopy(sources)
    if source_by_id(out, CANONICAL_SOURCE_ID) != schedule_before:
        raise RuntimeError("BZ European Council calendar source changed before transformation")
    before = deepcopy(out["sources"])
    out["sources"].append(new_machine_source(plan))
    if out["sources"][:-1] != before:
        raise RuntimeError("BZ modified an existing source while appending European Council RSS identity")
    if source_by_id(out, CANONICAL_SOURCE_ID) != schedule_before:
        raise RuntimeError("BZ changed European Council Canonical calendar source")
    out["version"] = plan["postconditions"]["source_registry_version"]
    out["reference_date"] = plan["reference_date"]
    return out


def transform_expectations(expectations: dict, plan: dict) -> dict:
    out = deepcopy(expectations)
    before = deepcopy(out.get("adapters", []))
    out["adapters"].append(monitor_expectation(plan))
    if out["adapters"][:-1] != before:
        raise RuntimeError("BZ changed an existing monitor route")
    out["version"] = plan["postconditions"]["monitor_expectations_version"]
    if out.get("automatic_canonical_commit") is not False or out.get("google_calendar_write") is not False:
        raise RuntimeError("BZ changed global write gates")
    return out


def _replace_once(text: str, anchor: str, replacement: str, label: str) -> str:
    count = text.count(anchor)
    if count != 1:
        raise RuntimeError(f"BZ expected exactly one {label} anchor, found {count}")
    return text.replace(anchor, replacement, 1)


def patch_adapter_init(text: str) -> str:
    if "EUROPEAN_COUNCIL_MEETINGS_RSS" in text or "fetch_european_council_meetings_rss" in text:
        raise RuntimeError("BZ European Council RSS adapter already exported")
    import_anchor = "from .eurostat_ics import (\n"
    block = '''from .european_council_rss import (\n    EUROPEAN_COUNCIL_CANONICAL_CALENDAR,\n    EUROPEAN_COUNCIL_CHANNEL_DESCRIPTION,\n    EUROPEAN_COUNCIL_CHANNEL_LINK,\n    EUROPEAN_COUNCIL_CHANNEL_TITLE,\n    EUROPEAN_COUNCIL_COPYRIGHT,\n    EUROPEAN_COUNCIL_ITEM_CHILDREN,\n    EUROPEAN_COUNCIL_MAX_ITEMS,\n    EUROPEAN_COUNCIL_MEETINGS_RSS,\n    EUROPEAN_COUNCIL_MIN_ITEMS,\n    EUROPEAN_COUNCIL_RSS_ACCEPT,\n    EUROPEAN_COUNCIL_RSS_DOCS,\n    EuropeanCouncilRSSItem,\n    fetch_european_council_meetings_rss,\n    parse_european_council_meeting_link,\n    parse_european_council_meetings_rss,\n)\n'''
    text = _replace_once(text, import_anchor, block + import_anchor, "adapter import")
    all_anchor = '    "EUROSTAT_ICS_ACCEPT",\n'
    all_block = '''    "EUROPEAN_COUNCIL_CANONICAL_CALENDAR",\n    "EUROPEAN_COUNCIL_CHANNEL_DESCRIPTION",\n    "EUROPEAN_COUNCIL_CHANNEL_LINK",\n    "EUROPEAN_COUNCIL_CHANNEL_TITLE",\n    "EUROPEAN_COUNCIL_COPYRIGHT",\n    "EUROPEAN_COUNCIL_ITEM_CHILDREN",\n    "EUROPEAN_COUNCIL_MAX_ITEMS",\n    "EUROPEAN_COUNCIL_MEETINGS_RSS",\n    "EUROPEAN_COUNCIL_MIN_ITEMS",\n    "EUROPEAN_COUNCIL_RSS_ACCEPT",\n    "EUROPEAN_COUNCIL_RSS_DOCS",\n    "EuropeanCouncilRSSItem",\n    "fetch_european_council_meetings_rss",\n    "parse_european_council_meeting_link",\n    "parse_european_council_meetings_rss",\n'''
    return _replace_once(text, all_anchor, all_block + all_anchor, "adapter __all__")


def patch_live_runner(text: str) -> str:
    if "european_council_rss_review_candidates" in text or '"EUROPEAN_COUNCIL_MEETINGS_RSS" in configs' in text:
        raise RuntimeError("BZ European Council RSS live wiring already exists")
    fetch_anchor = "    fetch_eurostat_release_calendar,\n"
    text = _replace_once(
        text,
        fetch_anchor,
        "    fetch_european_council_meetings_rss,\n" + fetch_anchor,
        "live fetch import",
    )
    monitor_anchor = "from world_signals.eurostat_monitor import eurostat_release_calendar_review_candidates\n"
    text = _replace_once(
        text,
        monitor_anchor,
        monitor_anchor + "from world_signals.european_council_monitor import european_council_rss_review_candidates\n",
        "live comparator import",
    )
    route_anchor = '    if "CHINA_NBS_LATEST_RELEASES_RSS" in configs:\n'
    block = '''    if "EUROPEAN_COUNCIL_MEETINGS_RSS" in configs:\n        euco_config=configs["EUROPEAN_COUNCIL_MEETINGS_RSS"]\n        try:\n            euco_items,euco_snap=fetch_european_council_meetings_rss()\n            report["source_health"].append({\n                "adapter_id":"EUROPEAN_COUNCIL_MEETINGS_RSS",\n                "source_id":euco_config["source_id"],\n                "state":"HEALTHY",\n                "snapshot":euco_snap.as_dict(),\n                "item_count":len(euco_items),\n                "request_budget_per_run":1,\n                "request_count":1,\n                "rss_request_count":1,\n                "robots_request_count":0,\n                "direct_calendar_html_request_count":0,\n                "item_followup_request_count":0,\n                "search_route_discovery_request_count":0,\n                "feed_item_count_is_permanent_invariant":False,\n                "observed_date_source":"OFFICIAL_RSS_ITEM_LINK_PATH_ONLY",\n                "updated_field_is_event_time":False,\n                "description_field_is_event_time":False,\n                "schedule_authority":False,\n                "clock_authority":False,\n                "lifecycle_authority":False,\n                "certainty_authority":False,\n                "canonical_date_mutation_allowed":False,\n                "automatic_calendar_html_fetch_allowed":False,\n                "automatic_item_link_fetch_allowed":False,\n                "automatic_new_occurrence_creation_allowed":False,\n                "automatic_live_or_analysis_promotion_allowed":False,\n                "automatic_commit_allowed":False,\n            })\n            candidates,observations=european_council_rss_review_candidates(\n                registry.get("records",[]),euco_items,euco_config\n            )\n            report["review_candidates"].extend(candidates)\n            report["observations"].extend(observations)\n        except (AdapterError,ValueError) as exc:\n            report["source_health"].append({\n                "adapter_id":"EUROPEAN_COUNCIL_MEETINGS_RSS",\n                "source_id":euco_config["source_id"],\n                "state":"DEGRADED",\n                "error":str(exc),\n                "canonical_action":"NONE",\n                "absence_is_not_event_state":True,\n                "schedule_authority":False,\n                "clock_authority":False,\n                "lifecycle_authority":False,\n                "certainty_authority":False,\n                "canonical_date_mutation_allowed":False,\n                "automatic_calendar_html_fetch_allowed":False,\n                "automatic_item_link_fetch_allowed":False,\n                "automatic_new_occurrence_creation_allowed":False,\n                "automatic_live_or_analysis_promotion_allowed":False,\n                "automatic_commit_allowed":False,\n            })\n\n'''
    return _replace_once(text, route_anchor, block + route_anchor, "live route")


def patch_smoke_runner(text: str) -> str:
    if '"EUROPEAN_COUNCIL_MEETINGS_RSS"' in text or "fetch_european_council_meetings_rss" in text:
        raise RuntimeError("BZ European Council RSS smoke wiring already exists")
    fetch_anchor = "    fetch_eurostat_release_calendar,\n"
    text = _replace_once(
        text,
        fetch_anchor,
        "    fetch_european_council_meetings_rss,\n" + fetch_anchor,
        "smoke fetch import",
    )
    route_anchor = '    try:\n        nbs_items,nbs_snap=fetch_nbs_native_latest_releases_rss()\n'
    block = '''    try:\n        euco_items,euco_snap=fetch_european_council_meetings_rss()\n        report["results"].append({\n            "adapter":"EUROPEAN_COUNCIL_MEETINGS_RSS",\n            "status":"PASS",\n            "source_id":"WSSRC-INT-035",\n            "snapshot":euco_snap.as_dict(),\n            "item_count":len(euco_items),\n            "request_budget_per_run":1,\n            "rss_request_count":1,\n            "robots_request_count":0,\n            "direct_calendar_html_request_count":0,\n            "item_followup_request_count":0,\n            "search_route_discovery_request_count":0,\n            "feed_item_count_is_permanent_invariant":False,\n            "observed_date_source":"OFFICIAL_RSS_ITEM_LINK_PATH_ONLY",\n            "updated_field_is_event_time":False,\n            "description_field_is_event_time":False,\n            "schedule_authority":False,\n            "clock_authority":False,\n            "lifecycle_authority":False,\n            "certainty_authority":False,\n            "canonical_date_mutation_allowed":False,\n            "automatic_calendar_html_fetch_allowed":False,\n            "automatic_item_link_fetch_allowed":False,\n            "automatic_new_occurrence_creation_allowed":False,\n            "automatic_commit_allowed":False,\n        })\n    except (AdapterError,ValueError) as exc:\n        failures.append({"adapter":"EUROPEAN_COUNCIL_MEETINGS_RSS","error":str(exc)})\n        report["results"].append({\n            "adapter":"EUROPEAN_COUNCIL_MEETINGS_RSS",\n            "status":"FAIL",\n            "source_id":"WSSRC-INT-035",\n            "error":str(exc),\n            "canonical_action":"NONE",\n        })\n\n'''
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
        raise RuntimeError("BZ changed Canonical post-state")
    if (sources.get("version"), len(sources.get("sources", []))) != (
        p["source_registry_version"], p["source_count"]
    ):
        raise RuntimeError("BZ source post-state mismatch")
    if (expectations.get("version"), len(expectations.get("adapters", []))) != (
        p["monitor_expectations_version"], p["configured_monitor_adapter_count"]
    ):
        raise RuntimeError("BZ monitor post-state mismatch")
    if source_by_id(sources, CANONICAL_SOURCE_ID) != schedule_before:
        raise RuntimeError("BZ changed WSSRC-INT-003")
    machine = source_by_id(sources, MACHINE_SOURCE_ID)
    if machine.get("canonical_dependency_count") != 0:
        raise RuntimeError("BZ machine source must have zero Canonical dependencies")
    if machine.get("canonical_provenance_use") != "MONITOR_ONLY_EUROPEAN_COUNCIL_RSS_NO_CANONICAL_DATE_AUTHORITY":
        raise RuntimeError("BZ machine source acquired Canonical date authority")
    if machine.get("automated_monitoring_use") != "CLEARED":
        raise RuntimeError("BZ machine source monitoring clearance mismatch")
    if machine.get("automated_retrieval_permission") != "OFFICIAL_CONSILIUM_RSS_AUTOMATIC_LOADING_INTERFACE":
        raise RuntimeError("BZ machine source machine-access classification mismatch")
    route = route_by_id(expectations, ADAPTER_ID)
    if route.get("source_id") != MACHINE_SOURCE_ID or route.get("canonical_schedule_source_id") != CANONICAL_SOURCE_ID:
        raise RuntimeError("BZ route source-role decomposition mismatch")
    if route.get("canonical_occurrence_ids") != plan["canonical_occurrence_ids"]:
        raise RuntimeError("BZ route occurrence allow-list mismatch")
    expected_guid_map = {guid: row["occurrence_id"] for guid, row in plan["configured_feed_identity_by_guid"].items()}
    expected_title_map = {guid: row["expected_title"] for guid, row in plan["configured_feed_identity_by_guid"].items()}
    if route.get("configured_guid_to_occurrence") != expected_guid_map:
        raise RuntimeError("BZ route GUID identity map mismatch")
    if route.get("configured_guid_titles") != expected_title_map:
        raise RuntimeError("BZ route title map mismatch")
    if route.get("request_budget_per_run") != 1 or route.get("rss_request_count_per_run") != 1:
        raise RuntimeError("BZ route request budget mismatch")
    for key in (
        "robots_request_count_per_run",
        "direct_calendar_html_request_count_per_run",
        "item_followup_request_count_per_run",
        "search_route_discovery_request_count_per_run",
    ):
        if route.get(key) != 0:
            raise RuntimeError(f"BZ route follow-up request count must remain zero: {key}")
    for key in (
        "schedule_authority",
        "clock_authority",
        "lifecycle_authority",
        "certainty_authority",
        "canonical_date_mutation_allowed",
        "automatic_calendar_html_fetch_allowed",
        "automatic_item_link_fetch_allowed",
        "automatic_new_occurrence_creation_allowed",
        "automatic_search_route_discovery_allowed",
        "automatic_live_or_analysis_promotion_allowed",
        "automatic_commit_allowed",
    ):
        if route.get(key) is not False:
            raise RuntimeError(f"BZ route gate must remain false: {key}")
    if route.get("machine_access_basis") != "OFFICIAL_CONSILIUM_RSS_AUTOMATIC_LOADING_INTERFACE":
        raise RuntimeError("BZ route machine-access basis mismatch")
    if route.get("observed_date_source") != "OFFICIAL_RSS_ITEM_LINK_PATH_ONLY":
        raise RuntimeError("BZ route observed-date source mismatch")
    if route.get("absence_semantics") != "NONE":
        raise RuntimeError("BZ route absence acquired event-state meaning")
    if route.get("feed_item_count_is_permanent_invariant") is not False:
        raise RuntimeError("BZ route froze current live feed item count")
    if route.get("updated_field_is_event_time") is not False or route.get("description_field_is_event_time") is not False:
        raise RuntimeError("BZ route assigned event-time meaning to non-authoritative RSS fields")
    if expectations.get("automatic_canonical_commit") is not False or expectations.get("google_calendar_write") is not False:
        raise RuntimeError("BZ changed global write gates")


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
        "tranche": "BZ",
        "mode": "READ_ONLY_PREFLIGHT",
        "exact_base_main_sha": BASE_SHA,
        "canonical": {"version": canonical["version"], "count": len(canonical["records"])},
        "sources_before": {"version": sources["version"], "count": len(sources["sources"])},
        "sources_after": {"version": post_sources["version"], "count": len(post_sources["sources"])},
        "monitor_before": {"version": expectations["version"], "count": len(expectations["adapters"])},
        "monitor_after": {"version": post_expectations["version"], "count": len(post_expectations["adapters"])},
        "machine_source_id": MACHINE_SOURCE_ID,
        "canonical_schedule_source_id": CANONICAL_SOURCE_ID,
        "adapter_id": ADAPTER_ID,
        "configured_occurrence_count": EXPECTED_COUNT,
        "configured_guid_count": EXPECTED_COUNT,
        "request_budget_per_run": 1,
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
            raise RuntimeError("BZ check-only path unexpectedly changed Canonical")
        return report
    if os.getenv(APPLY_ENV) != "1":
        raise RuntimeError(f"BZ APPLY REFUSED: set {APPLY_ENV}=1")
    dump_json(SOURCES_PATH, post_sources)
    dump_json(EXPECTATIONS_PATH, post_expectations)
    ADAPTER_INIT_PATH.write_text(post_adapter_init, encoding="utf-8")
    LIVE_RUNNER_PATH.write_text(post_live_runner, encoding="utf-8")
    SMOKE_RUNNER_PATH.write_text(post_smoke_runner, encoding="utf-8")
    if CANONICAL_PATH.read_bytes() != canonical_before:
        raise RuntimeError("BZ apply path changed Canonical")
    report["mode"] = "APPLIED_GOVERNED_RUNTIME_PATCH"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Guarded BZ activation helper for the European Council meetings RSS date-change sentinel. "
            f"Default is read-only; --apply additionally requires {APPLY_ENV}=1."
        )
    )
    parser.add_argument("--apply", action="store_true", help="materialise the exact five-file governed/runtime patch")
    args = parser.parse_args()
    try:
        report = run(apply=args.apply)
    except Exception as exc:
        print(f"BZ EUROPEAN COUNCIL RSS PRECONDITION FAILED: {exc}")
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
