from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/monitor/USDA_NASS_ASB_ICAL_CA_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
LIVE_RUNNER_PATH = ROOT / "scripts/run_live_monitor.py"
SMOKE_RUNNER_PATH = ROOT / "scripts/run_adapter_smoke.py"
ADAPTER_INIT_PATH = ROOT / "src/world_signals/adapters/__init__.py"

APPLY_ENV = "WORLD_SIGNALS_APPLY_MONITOR_CA"
BASE_SHA = "07c558c8811795f0aed40e73bd386cc70344191e"
SOURCE_ID = "WSSRC-COM-005"
ADAPTER_ID = "USDA_NASS_ASB_ICAL"
TIMEZONE = "America/New_York"
EXPECTED_COUNT = 5

MUTATION_PATHS = [
    SOURCES_PATH,
    EXPECTATIONS_PATH,
    LIVE_RUNNER_PATH,
    SMOKE_RUNNER_PATH,
    ADAPTER_INIT_PATH,
]

ALLOWED_SOURCE_MUTATION_KEYS = {
    "automated_monitoring_use",
    "automated_retrieval_permission",
    "monitoring_readiness_status",
    "monitoring_activation_status",
    "runtime_health_state",
    "verification_mode",
    "monitoring_readiness_assessed_at",
    "last_successful_research_verification_at",
    "governance_backfill_reviewed_at",
    "governance_backfill_basis",
    "automation_evidence_url",
    "automation_summary",
    "parser_type",
    "parser_version",
    "live_adapter_id",
    "live_validation_evidence",
    "monitor_endpoints",
}


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
        raise RuntimeError("CA plan is not frozen to exact post-BZ main")
    if (canonical.get("version"), len(canonical.get("records", []))) != (
        p["canonical_registry_version"], p["canonical_record_count"]
    ):
        raise RuntimeError("CA requires exact Canonical v0.41 / 689")
    if (sources.get("version"), len(sources.get("sources", []))) != (
        p["source_registry_version"], p["source_count"]
    ):
        raise RuntimeError("CA requires exact Sources v1.99 / 255")
    if (expectations.get("version"), len(expectations.get("adapters", []))) != (
        p["monitor_expectations_version"], p["configured_monitor_adapter_count"]
    ):
        raise RuntimeError("CA requires exact Monitor v0.24 / 22")
    if expectations.get("automatic_canonical_commit") is not False:
        raise RuntimeError("automatic Canonical commit gate must remain closed")
    if expectations.get("google_calendar_write") is not False:
        raise RuntimeError("Google Calendar write gate must remain closed")
    if any(row.get("adapter_id") == ADAPTER_ID for row in expectations.get("adapters", [])):
        raise RuntimeError("CA NASS route already exists")

    src = deepcopy(source_by_id(sources, SOURCE_ID))
    checks = {
        "institution": "USDA NASS",
        "jurisdiction": "United States/Global",
        "domain": "agriculture_food",
        "endpoint_role": "Agricultural Statistics Board calendar",
        "source_type": "official_calendar",
        "source_timezone": TIMEZONE,
        "canonical_dependency_count": p["source_canonical_dependency_count"],
        "automated_monitoring_use": p["source_automated_monitoring_use"],
        "automated_retrieval_permission": p["source_automated_retrieval_permission"],
        "monitoring_readiness_status": p["source_monitoring_readiness_status"],
        "runtime_health_state": p["source_runtime_health_state"],
        "verification_mode": p["source_verification_mode"],
        "licence_review_status": p["source_licence_review_status"],
        "canonical_provenance_use": p["source_canonical_provenance_use"],
        "machine_readable_available": p["machine_readable_available"],
        "ingestion_permission": "CURATED_FACTUAL_METADATA_ALLOWED",
        "redistribution_permission": "PUBLIC_DOMAIN_WITH_USDA_NASS_ACKNOWLEDGEMENT_REQUESTED",
    }
    for key, expected in checks.items():
        if src.get(key) != expected:
            raise RuntimeError(f"CA NASS source pre-state drift for {key}: {src.get(key)!r}")

    ids = list(plan["canonical_occurrence_ids"])
    if len(ids) != EXPECTED_COUNT or len(set(ids)) != EXPECTED_COUNT:
        raise RuntimeError("CA requires exact five-occurrence NASS allow-list")
    identity = plan["configured_feed_identity_by_uid"]
    if len(identity) != EXPECTED_COUNT or {row["occurrence_id"] for row in identity.values()} != set(ids):
        raise RuntimeError("CA NASS UID-to-occurrence identity map drift")

    deps = [r for r in canonical.get("records", []) if r.get("source_id") == SOURCE_ID]
    if len(deps) != EXPECTED_COUNT or {r.get("occurrence_id") for r in deps} != set(ids):
        raise RuntimeError("CA NASS Canonical dependency set drift")
    by_id = {r["occurrence_id"]: r for r in deps}
    for uid, expected in identity.items():
        row = by_id[expected["occurrence_id"]]
        row_checks = {
            "series_id": expected["series_id"],
            "source_id": SOURCE_ID,
            "source_timezone": TIMEZONE,
            "category": "AGRICULTURE_FOOD",
            "event_type": "INFORMATION_RELEASE",
            "timing_type": "LOCAL_DATETIME",
            "time_precision": "MINUTE",
            "all_day_semantics": False,
            "start_local": expected["baseline_start_local"],
            "publication_datetime": expected["baseline_start_local"],
            "publication_time_semantics": "EXACT_LOCAL_TIME",
            "end_local": None,
            "end_utc": None,
            "lifecycle_status": "PLANNED",
            "certainty_status": "CONFIRMED",
        }
        for key, value in row_checks.items():
            if row.get(key) != value:
                raise RuntimeError(
                    f"CA NASS Canonical pre-state drift for {uid}/{expected['occurrence_id']} {key}: "
                    f"expected {value!r}, found {row.get(key)!r}"
                )
        if not isinstance(row.get("start_utc"), str) or not row["start_utc"].endswith("Z"):
            raise RuntimeError(f"CA NASS Canonical UTC clock missing for {expected['occurrence_id']}")
    return src


def updated_source(plan: dict, before: dict) -> dict:
    out = deepcopy(before)
    d = plan["ical_endpoint_diagnostic"]
    s = plan["selection"]
    updates = {
        "automated_monitoring_use": "CLEARED_BOUNDED_OFFICIAL_ICAL",
        "automated_retrieval_permission": "BOUNDED_OFFICIAL_ICAL_NONEXCESSIVE_ROBOT_POLICY_WITH_CONTACT_UA",
        "monitoring_readiness_status": "LIVE_VALIDATED_NO_AUTO_COMMIT",
        "monitoring_activation_status": "LIVE_READ_ONLY_NASS_ASB_ICAL_DATETIME_CHANGE_SENTINEL_NO_AUTO_COMMIT",
        "runtime_health_state": "LIVE_GITHUB_ACTIONS_ICAL_FETCH_PARSE_PASS_2026_09_09",
        "verification_mode": "AUTOMATED_PILOT",
        "monitoring_readiness_assessed_at": plan["reference_date"],
        "last_successful_research_verification_at": plan["reference_date"],
        "governance_backfill_reviewed_at": plan["reference_date"],
        "governance_backfill_basis": (
            "CA reviewed the explicitly advertised NASS Agricultural Statistics Board iCalendar route together with NASS's "
            "non-excessive automated-retrieval policy and public-domain reuse statement, then validated the 2026 ICS endpoint "
            "in one production-shaped request. Floating ICS datetimes are interpreted in America/New_York only under separately "
            "verified first-party ET calendar-page evidence; no HTML is fetched by the production route."
        ),
        "automation_evidence_url": s["security_policy_url"],
        "automation_summary": (
            "NASS explicitly discusses automated retrieval and prohibits excessive robot activity rather than all automation. "
            "WORLD SIGNALS uses one request to the advertised iCalendar endpoint and a User-Agent containing the repository URL; "
            "there are no HTML, report-followup or search requests."
        ),
        "parser_type": "NASS_ASB_ICAL_DATETIME_SENTINEL",
        "parser_version": "nass-asb-ical-0.1",
        "live_adapter_id": ADAPTER_ID,
        "live_validation_evidence": {
            "ical_endpoint_run_id": d["run_id"],
            "ical_endpoint_job_id": d["job_id"],
            "ical_http_status": d["ical_http_status"],
            "ical_content_type": d["ical_content_type"],
            "ical_body_bytes": d["ical_body_bytes"],
            "ical_event_count_observed_not_frozen": d["ical_event_count_observed_not_frozen"],
            "ical_sha256_observed_not_frozen": d["ical_sha256_observed_not_frozen"],
            "configured_uid_count": d["configured_uid_count"],
            "configured_uid_match_count": d["configured_uid_match_count"],
            "request_count": 1,
            "calendar_html_request_count": 0,
            "report_followup_request_count": 0,
            "automatic_commit_allowed": False,
        },
        "monitor_endpoints": [
            {
                "endpoint_role": "nass_asb_2026_ical",
                "url": s["ical_url"],
                "transport": "ICALENDAR",
                "preferred_for_monitoring": True,
                "completeness_scope": "2026_AGRICULTURAL_STATISTICS_BOARD_CALENDAR_EVENT_COUNT_NOT_FROZEN",
                "notes": "One direct iCalendar request per monitor run; no HTML/report follow-up."
            },
            {
                "endpoint_role": "nass_reports_by_date_timezone_corroboration_manual_only",
                "url": s["calendar_page_url"],
                "transport": "HTML_MANUAL_GOVERNANCE_REFERENCE",
                "preferred_for_monitoring": False,
                "completeness_scope": "FIRST_PARTY_ET_TIMEZONE_CONVENTION_CORROBORATION_ONLY"
            }
        ],
    }
    out.update(updates)
    changed = {k for k in set(before) | set(out) if before.get(k) != out.get(k)}
    if not changed <= ALLOWED_SOURCE_MUTATION_KEYS:
        raise RuntimeError(f"CA NASS source mutation escaped allowed keys: {sorted(changed - ALLOWED_SOURCE_MUTATION_KEYS)}")
    return out


def monitor_expectation(plan: dict) -> dict:
    r = plan["request_contract"]
    c = plan["ical_contract"]
    identity = plan["configured_feed_identity_by_uid"]
    return {
        "adapter_id": ADAPTER_ID,
        "source_id": SOURCE_ID,
        "canonical_schedule_source_id": SOURCE_ID,
        "canonical_occurrence_ids": list(plan["canonical_occurrence_ids"]),
        "monitor_role": "OFFICIAL_NASS_ASB_ICAL_DATETIME_CHANGE_SENTINEL",
        "cadence": "daily",
        "cadence_is_monitor_metadata_not_new_scheduler_authority": True,
        "request_budget_per_run": r["request_budget_per_run"],
        "ical_request_count_per_run": r["ical_requests_per_run"],
        "robots_request_count_per_run": r["robots_requests_per_run"],
        "calendar_html_request_count_per_run": r["calendar_html_requests_per_run"],
        "report_followup_request_count_per_run": r["report_followup_requests_per_run"],
        "search_route_discovery_request_count_per_run": r["search_route_discovery_requests_per_run"],
        "machine_access_basis": r["machine_access_basis"],
        "feed": {
            "url": plan["selection"]["ical_url"],
            "transport": "ICALENDAR",
            "request_policy": "ONE_OFFICIAL_NASS_ICAL_REQUEST_NO_FOLLOWUPS",
        },
        "configured_uid_to_occurrence": {uid: row["occurrence_id"] for uid, row in identity.items()},
        "configured_uid_summaries": {uid: row["expected_summary"] for uid, row in identity.items()},
        "floating_datetime_timezone": c["floating_datetime_timezone"],
        "floating_timezone_basis": c["floating_timezone_basis"],
        "dtend_is_event_end": c["dtend_is_event_end"],
        "dtstamp_is_event_time": c["dtstamp_is_event_time"],
        "sequence_is_event_state": c["sequence_is_event_state"],
        "description_is_event_time": c["description_is_event_time"],
        "feed_event_count_is_permanent_invariant": False,
        "absence_semantics": "NONE",
        "unconfigured_item_review_floor_local": plan["monitor_review_window"]["unconfigured_item_review_floor_local"],
        "target_summaries": list(plan["monitor_review_window"]["target_summaries"]),
        "classification_contract": deepcopy(plan["classification_contract"]),
        "source_role_contract": deepcopy(plan["source_role_contract"]),
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
        "live_intelligence_policy": "NO_AUTOMATIC_PROMOTION_TO_LIVE_INTELLIGENCE_OR_ANALYSIS",
        "automatic_commit_allowed": False,
    }


def transform_sources(sources: dict, plan: dict, source_before: dict) -> dict:
    out = deepcopy(sources)
    before_rows = deepcopy(out["sources"])
    found = False
    for i, row in enumerate(out["sources"]):
        if row.get("source_id") == SOURCE_ID:
            if row != source_before:
                raise RuntimeError("CA NASS source changed before transformation")
            out["sources"][i] = updated_source(plan, source_before)
            found = True
            break
    if not found:
        raise RuntimeError("CA NASS source disappeared")
    for before_row, after_row in zip(before_rows, out["sources"], strict=True):
        if before_row.get("source_id") != SOURCE_ID and before_row != after_row:
            raise RuntimeError(f"CA changed unrelated source {before_row.get('source_id')}")
    if len(out["sources"]) != len(before_rows):
        raise RuntimeError("CA changed source population size")
    out["version"] = plan["postconditions"]["source_registry_version"]
    out["reference_date"] = plan["reference_date"]
    return out


def transform_expectations(expectations: dict, plan: dict) -> dict:
    out = deepcopy(expectations)
    before = deepcopy(out.get("adapters", []))
    out["adapters"].append(monitor_expectation(plan))
    if out["adapters"][:-1] != before:
        raise RuntimeError("CA changed an existing monitor route")
    out["version"] = plan["postconditions"]["monitor_expectations_version"]
    if out.get("automatic_canonical_commit") is not False or out.get("google_calendar_write") is not False:
        raise RuntimeError("CA changed global write gates")
    return out


def _replace_once(text: str, anchor: str, replacement: str, label: str) -> str:
    count = text.count(anchor)
    if count != 1:
        raise RuntimeError(f"CA expected exactly one {label} anchor, found {count}")
    return text.replace(anchor, replacement, 1)


def patch_adapter_init(text: str) -> str:
    if "NASS_ASB_ICAL_URL" in text or "fetch_nass_asb_ical" in text:
        raise RuntimeError("CA NASS adapter already exported")
    import_anchor = "from .nbs_native_rss import (\n"
    block = '''from .nass_asb_ical import (\n    NASS_ASB_ICAL_URL,\n    NASS_ICAL_ACCEPT,\n    NASS_PUBLICATIONS_URL,\n    NASS_RIGHTS_URL,\n    NASS_SECURITY_POLICY_URL,\n    NASS_TARGET_SUMMARIES,\n    NASS_TIMEZONE,\n    NASSASBRelease,\n    fetch_nass_asb_ical,\n    parse_nass_asb_ical,\n)\n'''
    text = _replace_once(text, import_anchor, block + import_anchor, "adapter import")
    all_anchor = '    "NBS_NATIVE_LATEST_RELEASES_RSS",\n'
    all_block = '''    "NASS_ASB_ICAL_URL",\n    "NASS_ICAL_ACCEPT",\n    "NASS_PUBLICATIONS_URL",\n    "NASS_RIGHTS_URL",\n    "NASS_SECURITY_POLICY_URL",\n    "NASS_TARGET_SUMMARIES",\n    "NASS_TIMEZONE",\n    "NASSASBRelease",\n    "fetch_nass_asb_ical",\n    "parse_nass_asb_ical",\n'''
    return _replace_once(text, all_anchor, all_block + all_anchor, "adapter __all__")


def patch_live_runner(text: str) -> str:
    if "nass_asb_ical_review_candidates" in text or '"USDA_NASS_ASB_ICAL" in configs' in text:
        raise RuntimeError("CA NASS live wiring already exists")
    text = _replace_once(
        text,
        "    fetch_nbs_native_latest_releases_rss,\n",
        "    fetch_nass_asb_ical,\n    fetch_nbs_native_latest_releases_rss,\n",
        "live fetch import",
    )
    text = _replace_once(
        text,
        "from world_signals.nbs_release_monitor import nbs_native_rss_review_candidates\n",
        "from world_signals.nass_asb_monitor import nass_asb_ical_review_candidates\n"
        "from world_signals.nbs_release_monitor import nbs_native_rss_review_candidates\n",
        "live comparator import",
    )
    route_anchor = '    if "CHINA_NBS_LATEST_RELEASES_RSS" in configs:\n'
    block = '''    if "USDA_NASS_ASB_ICAL" in configs:\n        nass_config=configs["USDA_NASS_ASB_ICAL"]\n        try:\n            nass_items,nass_snap=fetch_nass_asb_ical()\n            report["source_health"].append({\n                "adapter_id":"USDA_NASS_ASB_ICAL",\n                "source_id":nass_config["source_id"],\n                "state":"HEALTHY",\n                "snapshot":nass_snap.as_dict(),\n                "target_item_count":len(nass_items),\n                "request_budget_per_run":1,\n                "request_count":1,\n                "ical_request_count":1,\n                "robots_request_count":0,\n                "calendar_html_request_count":0,\n                "report_followup_request_count":0,\n                "search_route_discovery_request_count":0,\n                "feed_event_count_is_permanent_invariant":False,\n                "floating_datetime_timezone":"America/New_York",\n                "floating_timezone_basis":"FIRST_PARTY_NASS_REPORTS_BY_DATE_PAGES_LABEL_TARGET_RELEASES_ET",\n                "dtend_is_event_end":False,\n                "dtstamp_is_event_time":False,\n                "sequence_is_event_state":False,\n                "description_is_event_time":False,\n                "schedule_authority":False,\n                "clock_authority":False,\n                "lifecycle_authority":False,\n                "certainty_authority":False,\n                "canonical_datetime_mutation_allowed":False,\n                "automatic_calendar_html_fetch_allowed":False,\n                "automatic_report_followup_allowed":False,\n                "automatic_new_occurrence_creation_allowed":False,\n                "automatic_live_or_analysis_promotion_allowed":False,\n                "automatic_commit_allowed":False,\n            })\n            candidates,observations=nass_asb_ical_review_candidates(\n                registry.get("records",[]),nass_items,nass_config\n            )\n            report["review_candidates"].extend(candidates)\n            report["observations"].extend(observations)\n        except (AdapterError,ValueError) as exc:\n            report["source_health"].append({\n                "adapter_id":"USDA_NASS_ASB_ICAL",\n                "source_id":nass_config["source_id"],\n                "state":"DEGRADED",\n                "error":str(exc),\n                "canonical_action":"NONE",\n                "absence_is_not_event_state":True,\n                "schedule_authority":False,\n                "clock_authority":False,\n                "lifecycle_authority":False,\n                "certainty_authority":False,\n                "canonical_datetime_mutation_allowed":False,\n                "automatic_calendar_html_fetch_allowed":False,\n                "automatic_report_followup_allowed":False,\n                "automatic_new_occurrence_creation_allowed":False,\n                "automatic_live_or_analysis_promotion_allowed":False,\n                "automatic_commit_allowed":False,\n            })\n\n'''
    return _replace_once(text, route_anchor, block + route_anchor, "live route")


def patch_smoke_runner(text: str) -> str:
    if '"USDA_NASS_ASB_ICAL"' in text or "fetch_nass_asb_ical" in text:
        raise RuntimeError("CA NASS smoke wiring already exists")
    text = _replace_once(
        text,
        "    fetch_nbs_native_latest_releases_rss,\n",
        "    fetch_nass_asb_ical,\n    fetch_nbs_native_latest_releases_rss,\n",
        "smoke fetch import",
    )
    route_anchor = '    try:\n        nbs_items,nbs_snap=fetch_nbs_native_latest_releases_rss()\n'
    block = '''    try:\n        nass_items,nass_snap=fetch_nass_asb_ical()\n        report["results"].append({\n            "adapter":"USDA_NASS_ASB_ICAL",\n            "status":"PASS",\n            "source_id":"WSSRC-COM-005",\n            "snapshot":nass_snap.as_dict(),\n            "target_item_count":len(nass_items),\n            "request_budget_per_run":1,\n            "ical_request_count":1,\n            "robots_request_count":0,\n            "calendar_html_request_count":0,\n            "report_followup_request_count":0,\n            "search_route_discovery_request_count":0,\n            "floating_datetime_timezone":"America/New_York",\n            "dtend_is_event_end":False,\n            "dtstamp_is_event_time":False,\n            "sequence_is_event_state":False,\n            "schedule_authority":False,\n            "clock_authority":False,\n            "lifecycle_authority":False,\n            "certainty_authority":False,\n            "canonical_datetime_mutation_allowed":False,\n            "automatic_commit_allowed":False,\n        })\n    except (AdapterError,ValueError) as exc:\n        failures.append(str(exc))\n        report["results"].append({\n            "adapter":"USDA_NASS_ASB_ICAL",\n            "status":"FAIL",\n            "source_id":"WSSRC-COM-005",\n            "error":str(exc),\n            "canonical_action":"NONE",\n        })\n\n'''
    return _replace_once(text, route_anchor, block + route_anchor, "smoke route")


def build_post_state(canonical: dict, sources: dict, expectations: dict, plan: dict) -> tuple[dict, dict, str, str, str, dict]:
    source_before = preflight(canonical, sources, expectations, plan)
    sources_post = transform_sources(sources, plan, source_before)
    expectations_post = transform_expectations(expectations, plan)
    live_post = patch_live_runner(LIVE_RUNNER_PATH.read_text(encoding="utf-8"))
    smoke_post = patch_smoke_runner(SMOKE_RUNNER_PATH.read_text(encoding="utf-8"))
    init_post = patch_adapter_init(ADAPTER_INIT_PATH.read_text(encoding="utf-8"))
    report = {
        "status": "PASS",
        "mode": "CHECK_ONLY",
        "base_sha": BASE_SHA,
        "source_id": SOURCE_ID,
        "adapter_id": ADAPTER_ID,
        "canonical": {"version": canonical["version"], "count": len(canonical["records"])},
        "sources_before": {"version": sources["version"], "count": len(sources["sources"])},
        "sources_after": {"version": sources_post["version"], "count": len(sources_post["sources"])},
        "monitor_before": {"version": expectations["version"], "count": len(expectations["adapters"])},
        "monitor_after": {"version": expectations_post["version"], "count": len(expectations_post["adapters"])},
        "mutation_paths": [str(p.relative_to(ROOT)) for p in MUTATION_PATHS],
        "automatic_canonical_commit": expectations_post["automatic_canonical_commit"],
        "google_calendar_write": expectations_post["google_calendar_write"],
    }
    return sources_post, expectations_post, live_post, smoke_post, init_post, report


def validate_post_state(canonical: dict, sources: dict, expectations: dict, source_before: dict, plan: dict) -> None:
    p = plan["postconditions"]
    if (canonical.get("version"), len(canonical.get("records", []))) != (p["canonical_registry_version"], p["canonical_record_count"]):
        raise RuntimeError("CA changed Canonical post-state")
    if (sources.get("version"), len(sources.get("sources", []))) != (p["source_registry_version"], p["source_count"]):
        raise RuntimeError("CA source post-state mismatch")
    if (expectations.get("version"), len(expectations.get("adapters", []))) != (p["monitor_expectations_version"], p["configured_monitor_adapter_count"]):
        raise RuntimeError("CA monitor post-state mismatch")
    after = source_by_id(sources, SOURCE_ID)
    changed = {k for k in set(source_before) | set(after) if source_before.get(k) != after.get(k)}
    if not changed <= ALLOWED_SOURCE_MUTATION_KEYS:
        raise RuntimeError(f"CA source changed outside allow-list: {sorted(changed - ALLOWED_SOURCE_MUTATION_KEYS)}")
    preserved = {
        "source_id", "institution", "jurisdiction", "domain", "endpoint_role", "authoritative_url", "source_type",
        "source_timezone", "canonical_dependency_count", "canonical_provenance_use", "licence_review_status",
        "ingestion_permission", "redistribution_permission", "rights_evidence_url", "rights_summary", "machine_readable_available",
    }
    for key in preserved:
        if after.get(key) != source_before.get(key):
            raise RuntimeError(f"CA NASS preserved source field drifted: {key}")
    route = route_by_id(expectations, ADAPTER_ID)
    if route.get("source_id") != SOURCE_ID or route.get("canonical_schedule_source_id") != SOURCE_ID:
        raise RuntimeError("CA route source identity drift")
    if route.get("canonical_occurrence_ids") != plan["canonical_occurrence_ids"]:
        raise RuntimeError("CA route occurrence allow-list mismatch")
    expected_uid_map = {uid: row["occurrence_id"] for uid, row in plan["configured_feed_identity_by_uid"].items()}
    expected_summary_map = {uid: row["expected_summary"] for uid, row in plan["configured_feed_identity_by_uid"].items()}
    if route.get("configured_uid_to_occurrence") != expected_uid_map or route.get("configured_uid_summaries") != expected_summary_map:
        raise RuntimeError("CA route configured identity mismatch")
    if route.get("request_budget_per_run") != 1 or route.get("ical_request_count_per_run") != 1:
        raise RuntimeError("CA route request budget mismatch")
    for key in (
        "robots_request_count_per_run", "calendar_html_request_count_per_run", "report_followup_request_count_per_run",
        "search_route_discovery_request_count_per_run",
    ):
        if route.get(key) != 0:
            raise RuntimeError(f"CA route unexpected request authority: {key}")
    for key in (
        "schedule_authority", "clock_authority", "lifecycle_authority", "certainty_authority",
        "canonical_datetime_mutation_allowed", "automatic_calendar_html_fetch_allowed", "automatic_report_followup_allowed",
        "automatic_new_occurrence_creation_allowed", "automatic_search_route_discovery_allowed",
        "automatic_live_or_analysis_promotion_allowed", "automatic_commit_allowed",
    ):
        if route.get(key) is not False:
            raise RuntimeError(f"CA route authority gate opened: {key}")
    if expectations.get("automatic_canonical_commit") is not False or expectations.get("google_calendar_write") is not False:
        raise RuntimeError("CA global write gates changed")


def main() -> int:
    parser = argparse.ArgumentParser(description="Guarded CA USDA NASS ASB iCalendar monitor activation")
    parser.add_argument("--apply", action="store_true", help="write the exact governed/runtime patch")
    args = parser.parse_args()

    canonical = load_json(CANONICAL_PATH)
    sources = load_json(SOURCES_PATH)
    expectations = load_json(EXPECTATIONS_PATH)
    plan = load_json(PLAN_PATH)
    source_before = deepcopy(source_by_id(sources, SOURCE_ID))
    sources_post, expectations_post, live_post, smoke_post, init_post, report = build_post_state(
        canonical, sources, expectations, plan
    )
    validate_post_state(canonical, sources_post, expectations_post, source_before, plan)

    if args.apply:
        if os.environ.get(APPLY_ENV) != "1":
            raise SystemExit(f"apply refused: set {APPLY_ENV}=1")
        dump_json(SOURCES_PATH, sources_post)
        dump_json(EXPECTATIONS_PATH, expectations_post)
        LIVE_RUNNER_PATH.write_text(live_post, encoding="utf-8")
        SMOKE_RUNNER_PATH.write_text(smoke_post, encoding="utf-8")
        ADAPTER_INIT_PATH.write_text(init_post, encoding="utf-8")
        report["status"] = "APPLIED_GOVERNED_RUNTIME_PATCH"
        report["mode"] = "APPLY"
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
