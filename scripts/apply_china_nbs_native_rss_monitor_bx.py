from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/monitor/CHINA_NBS_NATIVE_RSS_BX_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
LIVE_RUNNER_PATH = ROOT / "scripts/run_live_monitor.py"
SMOKE_RUNNER_PATH = ROOT / "scripts/run_adapter_smoke.py"
ADAPTER_INIT_PATH = ROOT / "src/world_signals/adapters/__init__.py"

APPLY_ENV = "WORLD_SIGNALS_APPLY_MONITOR_BX"
BASE_SHA = "29b71bea42610992ad073b1583be64ced7e5de81"
CANONICAL_SOURCE_ID = "WSSRC-MAC-007"
MACHINE_SOURCE_ID = "WSSRC-MAC-031"
ADAPTER_ID = "CHINA_NBS_LATEST_RELEASES_RSS"
TIMEZONE = "Asia/Shanghai"
EXPECTED_COUNT = 36

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
        raise RuntimeError("BX plan is not frozen to exact post-BW main")
    if (canonical.get("version"), len(canonical.get("records", []))) != (
        p["canonical_registry_version"], p["canonical_record_count"]
    ):
        raise RuntimeError("BX requires exact Canonical v0.41 / 689")
    if (sources.get("version"), len(sources.get("sources", []))) != (
        p["source_registry_version"], p["source_count"]
    ):
        raise RuntimeError("BX requires exact Sources v1.96 / 252")
    if (expectations.get("version"), len(expectations.get("adapters", []))) != (
        p["monitor_expectations_version"], p["configured_monitor_adapter_count"]
    ):
        raise RuntimeError("BX requires exact Monitor v0.21 / 19")
    if expectations.get("automatic_canonical_commit") is not False:
        raise RuntimeError("automatic Canonical commit gate must remain closed")
    if expectations.get("google_calendar_write") is not False:
        raise RuntimeError("Google Calendar write gate must remain closed")
    if any(row.get("source_id") == MACHINE_SOURCE_ID for row in sources.get("sources", [])):
        raise RuntimeError("BX NBS RSS machine source already exists")
    if any(row.get("adapter_id") == ADAPTER_ID for row in expectations.get("adapters", [])):
        raise RuntimeError("BX NBS RSS route already exists")

    schedule = deepcopy(source_by_id(sources, CANONICAL_SOURCE_ID))
    source_checks = {
        "institution": "National Bureau of Statistics of China",
        "jurisdiction": "China",
        "domain": "macroeconomic_releases",
        "endpoint_role": "Annual regular press-release calendar",
        "authoritative_url": plan["selection"]["schedule_url"],
        "source_type": "official_calendar",
        "source_timezone": TIMEZONE,
        "canonical_dependency_count": p["canonical_schedule_dependency_count"],
        "automated_monitoring_use": p["canonical_schedule_automated_monitoring_use"],
        "automated_retrieval_permission": p["canonical_schedule_automated_retrieval_permission"],
        "monitoring_readiness_status": p["canonical_schedule_monitoring_readiness_status"],
        "canonical_provenance_use": p["canonical_schedule_canonical_provenance_use"],
        "verification_mode": "MANUAL_AUTHORITATIVE_RECHECK",
    }
    for key, expected in source_checks.items():
        if schedule.get(key) != expected:
            raise RuntimeError(f"BX NBS schedule-source pre-state drift for {key}: {schedule.get(key)!r}")

    ids = list(plan["canonical_occurrence_ids"])
    identity = deepcopy(plan["canonical_identity_by_occurrence_id"])
    if len(ids) != EXPECTED_COUNT or len(set(ids)) != EXPECTED_COUNT or set(identity) != set(ids):
        raise RuntimeError("BX requires exact 36-occurrence NBS allow-list and identity map")
    by_id = {r.get("occurrence_id"): r for r in canonical.get("records", []) if r.get("occurrence_id") in set(ids)}
    if set(by_id) != set(ids):
        raise RuntimeError("BX NBS allow-list no longer matches Canonical")
    all_deps = [r for r in canonical.get("records", []) if r.get("source_id") == CANONICAL_SOURCE_ID]
    if len(all_deps) != EXPECTED_COUNT or {r.get("occurrence_id") for r in all_deps} != set(ids):
        raise RuntimeError("BX NBS Canonical dependency set drift")

    for occurrence_id in ids:
        row = by_id[occurrence_id]
        expected = identity[occurrence_id]
        checks = {
            "series_id": expected["series_id"],
            "source_id": CANONICAL_SOURCE_ID,
            "region": "East Asia",
            "source_timezone": TIMEZONE,
            "time_precision": "MINUTE",
            "timing_type": "LOCAL_DATETIME",
            "event_type": "DATA_RELEASE",
            "start_local": expected["start_local"],
            "start_utc": expected["start_utc"],
        }
        for key, value in checks.items():
            if row.get(key) != value:
                raise RuntimeError(
                    f"BX NBS Canonical pre-state drift for {occurrence_id} {key}: "
                    f"expected {value!r}, found {row.get(key)!r}"
                )
    return schedule


def new_machine_source(plan: dict) -> dict:
    s = plan["selection"]
    return {
        "source_id": MACHINE_SOURCE_ID,
        "institution": "National Bureau of Statistics of China",
        "jurisdiction": "China",
        "domain": "macroeconomic_releases",
        "endpoint_role": "Official NBS native Latest Releases RSS publication sentinel",
        "authoritative_url": s["native_rss_url"],
        "source_type": "official_rss_feed",
        "information_supplied": (
            "Native NBS Latest Releases RSS title, official link, source label, publication metadata and document identity. "
            "The feed is publication corroboration only and is not forward schedule or Canonical clock authority."
        ),
        "future_schedule_horizon": "not a schedule source; finite rolling publication feed",
        "typical_advance_notice": "publication driven",
        "machine_readable_available": "RSS/XML",
        "source_timezone": TIMEZONE,
        "recommended_verification_cadence": "daily; one native RSS request per run",
        "activation_status": "ACTIVE_GUARDED",
        "parser_type": "NBS_NATIVE_LATEST_RELEASES_RSS_PUBLICATION_SENTINEL",
        "parser_version": "nbs-native-rss-0.1",
        "known_limitations": [
            "The native RSS feed is finite and rolling; absence has no schedule, lifecycle, delay, cancellation or certainty semantics.",
            "RSS pubTime/pubDate are publication metadata only and are not Canonical event-time authority even when historically aligned with scheduled release clocks.",
            "National Economic Performance titles use variable prose; only bounded period-prefix forms are classified and ambiguous identities fail closed.",
            "The monitor never automatically fetches the annual release calendar, English RSS, linked article pages, NBS data APIs, PDFs, news or search routes.",
            "Positive publication evidence creates review candidates only and cannot automatically alter Canonical schedule, clock, lifecycle or certainty.",
            "WSSRC-MAC-007 remains the Canonical annual forward release-calendar authority with its existing endpoint-review hold unchanged."
        ],
        "backup_source": None,
        "notes": "Separate machine-interface identity preserves the distinction between held Canonical calendar retrieval and expressly offered RSS subscription access.",
        "timezone_scope": "ASIA_SHANGHAI_PUBLICATION_METADATA_IDENTITY_ONLY_NO_CANONICAL_CLOCK_AUTHORITY",
        "licence_constraints": "NBS_TERMS_ATTRIBUTION_AND_STATED_REUSE_CONDITIONS_APPLY_NO_UNRESTRICTED_REDISTRIBUTION_ASSUMED",
        "ingestion_permission": "OFFICIAL_DEDICATED_RSS_MINIMAL_FACTUAL_METADATA_INTERNAL_MONITORING_WITH_ATTRIBUTION",
        "licence_review_status": "CURATED_DATA_USE_ALLOWED_REUSE_CONDITIONAL_RSS_MACHINE_INTERFACE_SEPARATELY_IDENTIFIED",
        "automated_retrieval_permission": "OFFICIAL_DEDICATED_RSS_INTERFACE_BOUNDED_METADATA_MONITORING",
        "redistribution_permission": "CONDITIONAL_ATTRIBUTION_MINIMAL_FACTUAL_METADATA_ONLY_NO_ARTICLE_BODY_REPUBLICATION",
        "rights_evidence_url": s["rights_evidence_url"],
        "rights_summary": (
            "NBS terms permit statistical-data use and reasonable good-faith attributed reuse subject to stated conditions; "
            "BX does not infer an unrestricted downstream redistribution licence."
        ),
        "automation_evidence_url": s["native_rss_documentation_url"],
        "automation_summary": (
            "NBS publishes the native RSS subscription interface for immediate automatic acquisition. WORLD SIGNALS is bounded "
            "to one daily request to that native feed with zero automatic calendar, English-feed, article, API, PDF, news or search follow-ups."
        ),
        "rights_reviewed_at": plan["reference_date"],
        "rights_review_scope": "BX_CONTENT_REUSE_AND_DEDICATED_RSS_MACHINE_ACCESS_SEPARATED_FROM_CALENDAR_ENDPOINT_REVIEW",
        "rights_review_note": "Operational governance classification for WORLD SIGNALS; not a legal opinion.",
        "monitoring_readiness_status": "LIVE_VALIDATED_NO_AUTO_COMMIT",
        "monitoring_priority_score": 570,
        "canonical_dependency_count": 0,
        "monitoring_readiness_assessed_at": plan["reference_date"],
        "monitoring_activation_status": "LIVE_READ_ONLY_PUBLICATION_SENTINEL_NO_AUTO_COMMIT",
        "last_successful_research_verification_at": plan["reference_date"],
        "canonical_provenance_use": "MONITOR_ONLY_PUBLICATION_SENTINEL_NO_CANONICAL_SCHEDULE_AUTHORITY",
        "automated_monitoring_use": "CLEARED",
        "verification_mode": "AUTOMATED_PILOT",
        "runtime_health_state": "LIVE_GITHUB_ACTIONS_NATIVE_RSS_FETCH_PARSE_PASS_2026_09_09",
        "governance_backfill_reviewed_at": plan["reference_date"],
        "governance_backfill_basis": (
            "Separate first-party native RSS source created because NBS explicitly offers RSS for automatic acquisition; "
            "the pre-existing annual release-calendar source remains unchanged and under endpoint review."
        ),
        "live_adapter_id": ADAPTER_ID,
        "live_validation_evidence": {
            "native_rss_diagnostic_run_id": 34254908666,
            "native_rss_diagnostic_job_id": 102158115941,
            "rss_http_status": 200,
            "rss_content_type": "text/xml",
            "rss_item_count": 500,
            "rss_sha256": "b15a457fffcba22c65104d35e1c2dfa9021c6c8ec1b47034c153a152c3db12e7",
            "strict_document_xml_parse_succeeded": True,
            "item_fragment_failure_count": 0,
            "request_count": 1,
            "followup_request_count": 0,
            "automatic_commit_allowed": False,
        },
        "related_source_ids": [CANONICAL_SOURCE_ID],
        "source_role_contract": deepcopy(plan["source_role_contract"]),
        "monitor_endpoints": [
            {
                "endpoint_role": "nbs_native_latest_releases_rss",
                "url": s["native_rss_url"],
                "transport": "RSS_XML",
                "preferred_for_monitoring": True,
                "completeness_scope": "FINITE_ROLLING_NATIVE_NBS_LATEST_RELEASES",
                "notes": "Exactly one request per daily run; no automatic item-link or schedule-source follow-up."
            },
            {
                "endpoint_role": "rss_machine_interface_documentation",
                "url": s["native_rss_documentation_url"],
                "transport": "HTML_MANUAL_GOVERNANCE_REFERENCE",
                "preferred_for_monitoring": False,
                "completeness_scope": "NBS_PUBLISHED_RSS_SUBSCRIPTION_DOCUMENTATION"
            },
            {
                "endpoint_role": "english_rss_rejected_diagnostic_only",
                "url": s["english_rss_url"],
                "transport": "RSS_XML_DIAGNOSTIC_ONLY_NOT_PRODUCTION",
                "preferred_for_monitoring": False,
                "completeness_scope": "ENGLISH_TRANSLATION_SURFACE_EXCLUDED_FROM_BX_PRODUCTION_ROUTE"
            }
        ]
    }


def monitor_expectation(plan: dict) -> dict:
    s = plan["selection"]
    r = plan["request_contract"]
    return {
        "adapter_id": ADAPTER_ID,
        "source_id": MACHINE_SOURCE_ID,
        "canonical_schedule_source_id": CANONICAL_SOURCE_ID,
        "canonical_occurrence_ids": list(plan["canonical_occurrence_ids"]),
        "identity_by_occurrence_id": deepcopy(plan["canonical_identity_by_occurrence_id"]),
        "monitor_role": "OFFICIAL_NBS_NATIVE_LATEST_RELEASES_RSS_PUBLICATION_SENTINEL",
        "cadence": "DAILY",
        "request_budget_per_run": r["request_budget_per_run"],
        "native_rss_request_count_per_run": r["native_rss_requests_per_run"],
        "schedule_request_count_per_run": r["schedule_requests_per_run"],
        "english_rss_request_count_per_run": r["english_rss_requests_per_run"],
        "article_followup_request_count_per_run": r["article_followup_requests_per_run"],
        "data_api_followup_request_count_per_run": r["data_api_followup_requests_per_run"],
        "search_route_discovery_request_count_per_run": r["search_route_discovery_requests_per_run"],
        "feed": {
            "url": s["native_rss_url"],
            "transport": "RSS_XML",
            "request_policy": "ONE_OFFICIAL_NATIVE_RSS_REQUEST_PER_DAILY_MONITOR_RUN"
        },
        "classification_contract": deepcopy(plan["classification_contract"]),
        "source_role_contract": deepcopy(plan["source_role_contract"]),
        "source_failure_policy": "SOURCE_HEALTH_ONLY_NO_EVENT_MUTATION",
        "positive_publication_policy": "GENERATE_REVIEW_CANDIDATE_ONLY_FOR_EXACT_SERIES_REFERENCE_YEAR_MONTH_IDENTITY_MATCH",
        "absence_policy": "FINITE_ROLLING_FEED_ABSENCE_HAS_NO_SCHEDULE_LIFECYCLE_DELAY_CANCELLATION_OR_CERTAINTY_SEMANTICS",
        "outside_scope_policy": "OBSERVE_RELEVANT_HISTORICAL_OR_UNTRACKED_PUBLICATIONS_ONLY",
        "schedule_authority": False,
        "clock_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "rss_publication_metadata_is_event_clock_authority": False,
        "rss_publication_metadata_is_schedule_authority": False,
        "canonical_clock_mutation_allowed": False,
        "automatic_item_link_fetch_allowed": False,
        "automatic_schedule_html_fetch_allowed": False,
        "automatic_english_rss_fetch_allowed": False,
        "automatic_data_api_fetch_allowed": False,
        "automatic_search_route_discovery_allowed": False,
        "live_intelligence_policy": "NO_AUTOMATIC_PROMOTION_TO_LIVE_INTELLIGENCE_OR_ANALYSIS",
        "automatic_commit_allowed": False,
    }


def transform_sources(sources: dict, plan: dict, schedule_before: dict) -> dict:
    out = deepcopy(sources)
    if source_by_id(out, CANONICAL_SOURCE_ID) != schedule_before:
        raise RuntimeError("BX NBS schedule source changed before transformation")
    before = deepcopy(out["sources"])
    out["sources"].append(new_machine_source(plan))
    if out["sources"][:-1] != before:
        raise RuntimeError("BX modified an existing source while appending NBS RSS identity")
    if source_by_id(out, CANONICAL_SOURCE_ID) != schedule_before:
        raise RuntimeError("BX changed NBS Canonical schedule source")
    out["version"] = plan["postconditions"]["source_registry_version"]
    out["reference_date"] = plan["reference_date"]
    return out


def transform_expectations(expectations: dict, plan: dict) -> dict:
    out = deepcopy(expectations)
    before = deepcopy(out.get("adapters", []))
    out["adapters"].append(monitor_expectation(plan))
    if out["adapters"][:-1] != before:
        raise RuntimeError("BX changed an existing monitor route")
    out["version"] = plan["postconditions"]["monitor_expectations_version"]
    if out.get("automatic_canonical_commit") is not False or out.get("google_calendar_write") is not False:
        raise RuntimeError("BX changed global write gates")
    return out


def _replace_once(text: str, anchor: str, replacement: str, label: str) -> str:
    if text.count(anchor) != 1:
        raise RuntimeError(f"BX expected exactly one {label} anchor, found {text.count(anchor)}")
    return text.replace(anchor, replacement, 1)


def patch_adapter_init(text: str) -> str:
    if "NBS_NATIVE_LATEST_RELEASES_RSS" in text or "fetch_nbs_native_latest_releases_rss" in text:
        raise RuntimeError("BX NBS native RSS adapter already exported")
    import_anchor = "from .ons_release_calendar import (\n"
    block = '''from .nbs_native_rss import (\n    NBS_NATIVE_LATEST_RELEASES_RSS,\n    NBS_NATIVE_RSS_ACCEPT,\n    NBS_NATIVE_RSS_DOCS,\n    NBSNativeReleaseItem,\n    fetch_nbs_native_latest_releases_rss,\n    parse_nbs_native_latest_releases_rss,\n)\n'''
    text = _replace_once(text, import_anchor, block + import_anchor, "adapter import")
    all_anchor = '    "ONS_RELEASE_CALENDAR",\n'
    all_block = '''    "NBS_NATIVE_LATEST_RELEASES_RSS",\n    "NBS_NATIVE_RSS_ACCEPT",\n    "NBS_NATIVE_RSS_DOCS",\n    "NBSNativeReleaseItem",\n    "fetch_nbs_native_latest_releases_rss",\n    "parse_nbs_native_latest_releases_rss",\n'''
    return _replace_once(text, all_anchor, all_block + all_anchor, "adapter __all__")


def patch_live_runner(text: str) -> str:
    if "nbs_native_rss_review_candidates" in text or '"CHINA_NBS_LATEST_RELEASES_RSS" in configs' in text:
        raise RuntimeError("BX NBS native RSS live wiring already exists")
    fetch_anchor = "    fetch_ons_upcoming_releases,\n"
    text = _replace_once(
        text, fetch_anchor,
        "    fetch_nbs_native_latest_releases_rss,\n" + fetch_anchor,
        "live fetch import",
    )
    monitor_anchor = "from world_signals.ons_monitor import ons_release_calendar_review_candidates\n"
    text = _replace_once(
        text, monitor_anchor,
        "from world_signals.nbs_release_monitor import nbs_native_rss_review_candidates\n" + monitor_anchor,
        "live monitor import",
    )
    route_anchor = '    if "FAO_RELEASE_CALENDAR" in configs:\n'
    block = '''    if "CHINA_NBS_LATEST_RELEASES_RSS" in configs:\n        nbs_config=configs["CHINA_NBS_LATEST_RELEASES_RSS"]\n        try:\n            nbs_items,nbs_snap=fetch_nbs_native_latest_releases_rss()\n            report["source_health"].append({\n                "adapter_id":"CHINA_NBS_LATEST_RELEASES_RSS",\n                "source_id":nbs_config["source_id"],\n                "state":"HEALTHY",\n                "snapshot":nbs_snap.as_dict(),\n                "item_count":len(nbs_items),\n                "request_budget_per_run":1,\n                "native_rss_request_count":1,\n                "schedule_request_count":0,\n                "english_rss_request_count":0,\n                "article_followup_request_count":0,\n                "data_api_followup_request_count":0,\n                "search_route_discovery_request_count":0,\n                "schedule_authority":False,\n                "clock_authority":False,\n                "lifecycle_authority":False,\n                "certainty_authority":False,\n                "rss_publication_metadata_is_event_clock_authority":False,\n                "rss_publication_metadata_is_schedule_authority":False,\n                "canonical_clock_mutation_allowed":False,\n                "automatic_item_link_fetch_allowed":False,\n                "automatic_schedule_html_fetch_allowed":False,\n                "automatic_english_rss_fetch_allowed":False,\n                "automatic_commit_allowed":False,\n            })\n            candidates,observations=nbs_native_rss_review_candidates(\n                registry.get("records",[]),nbs_items,nbs_config\n            )\n            report["review_candidates"].extend(candidates)\n            report["observations"].extend(observations)\n        except (AdapterError,ValueError) as exc:\n            report["source_health"].append({\n                "adapter_id":"CHINA_NBS_LATEST_RELEASES_RSS",\n                "source_id":nbs_config["source_id"],\n                "state":"DEGRADED",\n                "error":str(exc),\n                "canonical_action":"NONE",\n                "absence_is_not_event_state":True,\n                "schedule_authority":False,\n                "clock_authority":False,\n                "lifecycle_authority":False,\n                "certainty_authority":False,\n                "rss_publication_metadata_is_event_clock_authority":False,\n                "canonical_clock_mutation_allowed":False,\n                "automatic_item_link_fetch_allowed":False,\n                "automatic_schedule_html_fetch_allowed":False,\n                "automatic_english_rss_fetch_allowed":False,\n                "automatic_commit_allowed":False,\n            })\n\n'''
    return _replace_once(text, route_anchor, block + route_anchor, "live route")


def patch_smoke_runner(text: str) -> str:
    if '"CHINA_NBS_LATEST_RELEASES_RSS"' in text or "fetch_nbs_native_latest_releases_rss" in text:
        raise RuntimeError("BX NBS native RSS smoke wiring already exists")
    fetch_anchor = "    fetch_ons_upcoming_releases,\n"
    text = _replace_once(
        text, fetch_anchor,
        "    fetch_nbs_native_latest_releases_rss,\n" + fetch_anchor,
        "smoke fetch import",
    )
    route_anchor = '    try:\n        fao_months=["October 2026","November 2026","December 2026"]\n'
    block = '''    try:\n        nbs_items,nbs_snap=fetch_nbs_native_latest_releases_rss()\n        report["results"].append({\n            "adapter":"CHINA_NBS_LATEST_RELEASES_RSS",\n            "status":"PASS",\n            "source_id":"WSSRC-MAC-031",\n            "snapshot":nbs_snap.as_dict(),\n            "item_count":len(nbs_items),\n            "request_budget_per_run":1,\n            "native_rss_request_count":1,\n            "schedule_request_count":0,\n            "english_rss_request_count":0,\n            "article_followup_request_count":0,\n            "data_api_followup_request_count":0,\n            "search_route_discovery_request_count":0,\n            "schedule_authority":False,\n            "clock_authority":False,\n            "lifecycle_authority":False,\n            "certainty_authority":False,\n            "rss_publication_metadata_is_event_clock_authority":False,\n            "canonical_clock_mutation_allowed":False,\n            "automatic_item_link_fetch_allowed":False,\n            "automatic_schedule_html_fetch_allowed":False,\n            "automatic_english_rss_fetch_allowed":False,\n            "automatic_commit_allowed":False,\n        })\n    except (AdapterError,ValueError) as exc:\n        failures.append({"adapter":"CHINA_NBS_LATEST_RELEASES_RSS","error":str(exc)})\n        report["results"].append({\n            "adapter":"CHINA_NBS_LATEST_RELEASES_RSS",\n            "status":"FAIL",\n            "source_id":"WSSRC-MAC-031",\n            "error":str(exc),\n            "canonical_action":"NONE",\n        })\n\n'''
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
        raise RuntimeError("BX changed Canonical post-state")
    if (sources.get("version"), len(sources.get("sources", []))) != (
        p["source_registry_version"], p["source_count"]
    ):
        raise RuntimeError("BX source post-state mismatch")
    if (expectations.get("version"), len(expectations.get("adapters", []))) != (
        p["monitor_expectations_version"], p["configured_monitor_adapter_count"]
    ):
        raise RuntimeError("BX monitor post-state mismatch")
    if source_by_id(sources, CANONICAL_SOURCE_ID) != schedule_before:
        raise RuntimeError("BX changed WSSRC-MAC-007")
    machine = source_by_id(sources, MACHINE_SOURCE_ID)
    if machine.get("canonical_dependency_count") != 0:
        raise RuntimeError("BX machine source must have zero Canonical dependencies")
    if machine.get("canonical_provenance_use") != "MONITOR_ONLY_PUBLICATION_SENTINEL_NO_CANONICAL_SCHEDULE_AUTHORITY":
        raise RuntimeError("BX machine source acquired Canonical schedule authority")
    if machine.get("automated_monitoring_use") != "CLEARED":
        raise RuntimeError("BX machine source monitoring clearance mismatch")
    route = route_by_id(expectations, ADAPTER_ID)
    if route.get("source_id") != MACHINE_SOURCE_ID or route.get("canonical_schedule_source_id") != CANONICAL_SOURCE_ID:
        raise RuntimeError("BX route source-role decomposition mismatch")
    if len(route.get("canonical_occurrence_ids", [])) != EXPECTED_COUNT:
        raise RuntimeError("BX route must configure exactly 36 occurrences")
    false_gates = [
        "schedule_authority", "clock_authority", "lifecycle_authority", "certainty_authority",
        "rss_publication_metadata_is_event_clock_authority", "rss_publication_metadata_is_schedule_authority",
        "canonical_clock_mutation_allowed", "automatic_item_link_fetch_allowed",
        "automatic_schedule_html_fetch_allowed", "automatic_english_rss_fetch_allowed",
        "automatic_data_api_fetch_allowed", "automatic_search_route_discovery_allowed", "automatic_commit_allowed",
    ]
    for key in false_gates:
        if route.get(key) is not False:
            raise RuntimeError(f"BX route gate must remain false: {key}")
    if route.get("request_budget_per_run") != 1 or route.get("native_rss_request_count_per_run") != 1:
        raise RuntimeError("BX route request budget mismatch")
    for key in (
        "schedule_request_count_per_run", "english_rss_request_count_per_run",
        "article_followup_request_count_per_run", "data_api_followup_request_count_per_run",
        "search_route_discovery_request_count_per_run",
    ):
        if route.get(key) != 0:
            raise RuntimeError(f"BX route follow-up request count must remain zero: {key}")
    if expectations.get("automatic_canonical_commit") is not False or expectations.get("google_calendar_write") is not False:
        raise RuntimeError("BX changed global write gates")


def simulate() -> tuple[dict, dict, dict, dict, str, str, str]:
    plan = load_json(PLAN_PATH)
    canonical = load_json(CANONICAL_PATH)
    sources = load_json(SOURCES_PATH)
    expectations = load_json(EXPECTATIONS_PATH)
    schedule_before = preflight(canonical, sources, expectations, plan)
    new_sources = transform_sources(sources, plan, schedule_before)
    new_expectations = transform_expectations(expectations, plan)
    new_live = patch_live_runner(LIVE_RUNNER_PATH.read_text(encoding="utf-8"))
    new_smoke = patch_smoke_runner(SMOKE_RUNNER_PATH.read_text(encoding="utf-8"))
    new_init = patch_adapter_init(ADAPTER_INIT_PATH.read_text(encoding="utf-8"))
    validate_post_state(canonical, new_sources, new_expectations, schedule_before, plan)
    return canonical, new_sources, new_expectations, schedule_before, new_live, new_smoke, new_init


def apply() -> None:
    canonical, new_sources, new_expectations, schedule_before, new_live, new_smoke, new_init = simulate()
    if os.getenv(APPLY_ENV) != "1":
        raise RuntimeError(f"BX apply requires {APPLY_ENV}=1")
    dump_json(SOURCES_PATH, new_sources)
    dump_json(EXPECTATIONS_PATH, new_expectations)
    LIVE_RUNNER_PATH.write_text(new_live, encoding="utf-8")
    SMOKE_RUNNER_PATH.write_text(new_smoke, encoding="utf-8")
    ADAPTER_INIT_PATH.write_text(new_init, encoding="utf-8")
    plan = load_json(PLAN_PATH)
    validate_post_state(canonical, load_json(SOURCES_PATH), load_json(EXPECTATIONS_PATH), schedule_before, plan)


def main() -> int:
    parser = argparse.ArgumentParser(description="Governed BX NBS native RSS monitor activation helper")
    parser.add_argument("--apply", action="store_true", help="write exactly the five governed/runtime files")
    args = parser.parse_args()
    if args.apply:
        apply()
        mode = "APPLIED"
    else:
        simulate()
        mode = "CHECK_ONLY"
    print(f"BX_NBS_NATIVE_RSS_HELPER {mode}")
    print("MUTATION_PATHS")
    for path in MUTATION_PATHS:
        print(path.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
