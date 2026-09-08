from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/monitor/JAPAN_CPI_RELEASE_SCHEDULE_BW_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
LIVE_RUNNER_PATH = ROOT / "scripts/run_live_monitor.py"
SMOKE_RUNNER_PATH = ROOT / "scripts/run_adapter_smoke.py"
ADAPTER_INIT_PATH = ROOT / "src/world_signals/adapters/__init__.py"

APPLY_ENV = "WORLD_SIGNALS_APPLY_MONITOR_BW"
BASE_SHA = "b277939bc6c540d0986f298a832c7d63a29a2d19"
SOURCE_ID = "WSSRC-MAC-014"
ADAPTER_ID = "JAPAN_CPI_RELEASE_SCHEDULE"
SERIES_ID = "WSER-MAC-JP-CPI"
TIMEZONE = "Asia/Tokyo"
REGION = "East Asia"
SCHEDULE_URL = "https://www.stat.go.jp/english/data/cpi/1582.htm"
ROBOTS_URL = "https://www.stat.go.jp/robots.txt"
CLOCK_RULE_URL = "https://www.stat.go.jp/english/data/cpi/1585.htm"
RIGHTS_URL = "https://www.stat.go.jp/english/info/riyou.html"

ALLOWED_SOURCE_MUTATION_KEYS = {
    "automated_monitoring_use",
    "automated_retrieval_permission",
    "automation_summary",
    "automation_reviewed_at",
    "automation_evidence_url",
    "automation_review_scope",
    "monitoring_readiness_status",
    "monitoring_activation_status",
    "verification_mode",
    "runtime_health_state",
    "monitoring_readiness_assessed_at",
    "last_successful_research_verification_at",
    "live_adapter_id",
    "live_validation_evidence",
    "monitor_endpoints",
    "parser_version",
    "source_role_contract",
}

IMMUTABLE_SOURCE_KEYS = {
    "source_id",
    "institution",
    "jurisdiction",
    "domain",
    "endpoint_role",
    "authoritative_url",
    "source_type",
    "information_supplied",
    "source_timezone",
    "timezone_scope",
    "canonical_dependency_count",
    "canonical_provenance_use",
    "licence_constraints",
    "ingestion_permission",
    "licence_review_status",
    "redistribution_permission",
    "rights_evidence_url",
    "rights_summary",
    "rights_review_scope",
    "rights_reviewed_at",
    "rights_review_note",
    "governance_backfill_basis",
    "governance_backfill_reviewed_at",
    "notes",
    "parser_type",
}

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


def _changed_keys(before: dict, after: dict) -> set[str]:
    return {key for key in set(before) | set(after) if before.get(key) != after.get(key)}


def preflight(canonical: dict, sources: dict, expectations: dict, plan: dict) -> dict:
    p = plan["preconditions"]
    if plan.get("exact_base_main_sha") != BASE_SHA:
        raise RuntimeError("BW plan is not frozen to exact post-BV main")
    if (canonical.get("version"), len(canonical.get("records", []))) != (
        p["canonical_registry_version"], p["canonical_record_count"]
    ):
        raise RuntimeError("BW requires exact Canonical v0.41 / 689")
    if (sources.get("version"), len(sources.get("sources", []))) != (
        p["source_registry_version"], p["source_count"]
    ):
        raise RuntimeError("BW requires exact Sources v1.95 / 252")
    if (expectations.get("version"), len(expectations.get("adapters", []))) != (
        p["monitor_expectations_version"], p["configured_monitor_adapter_count"]
    ):
        raise RuntimeError("BW requires exact Monitor v0.20 / 18")
    if expectations.get("automatic_canonical_commit") is not False:
        raise RuntimeError("automatic Canonical commit gate must remain closed")
    if expectations.get("google_calendar_write") is not False:
        raise RuntimeError("Google Calendar write gate must remain closed")
    if any(row.get("adapter_id") == ADAPTER_ID for row in expectations.get("adapters", [])):
        raise RuntimeError("BW Japan CPI monitor route already exists")

    source = deepcopy(source_by_id(sources, SOURCE_ID))
    source_checks = {
        "institution": "Statistics Bureau of Japan",
        "jurisdiction": "Japan",
        "domain": "macroeconomic_releases",
        "source_type": "official_series_schedule",
        "endpoint_role": "Consumer Price Index release schedule",
        "authoritative_url": SCHEDULE_URL,
        "source_timezone": TIMEZONE,
        "canonical_dependency_count": p["source_canonical_dependency_count"],
        "canonical_provenance_use": p["source_canonical_provenance_use"],
        "automated_monitoring_use": p["source_automated_monitoring_use"],
        "automated_retrieval_permission": p["source_automated_retrieval_permission"],
        "monitoring_readiness_status": p["source_monitoring_readiness_status"],
        "monitoring_activation_status": p["source_monitoring_activation_status"],
        "verification_mode": p["source_verification_mode"],
        "runtime_health_state": p["source_runtime_health_state"],
        "parser_type": p["source_parser_type"],
        "parser_version": p["source_parser_version"],
        "rights_evidence_url": RIGHTS_URL,
        "licence_review_status": "CLEARED_GOVERNMENT_OF_JAPAN_OPEN_TERMS",
        "ingestion_permission": "CURATED_FACTUAL_METADATA_ALLOWED",
        "redistribution_permission": "COMMERCIAL_AND_NONCOMMERCIAL_REUSE_WITH_ATTRIBUTION_AND_CHANGE_NOTICE",
    }
    for key, expected in source_checks.items():
        if source.get(key) != expected:
            raise RuntimeError(f"BW Japan CPI source pre-state drift for {key}: {source.get(key)!r}")

    if source.get("notes", {}).get("time_rule_url") != CLOCK_RULE_URL:
        raise RuntimeError("BW requires separate official Japan CPI clock-rule provenance")
    endpoints = source.get("monitor_endpoints")
    if not isinstance(endpoints, list) or len(endpoints) != 1:
        raise RuntimeError("BW expects exactly one pre-existing Japan CPI schedule monitor endpoint")
    endpoint = endpoints[0]
    if endpoint.get("url") != SCHEDULE_URL or endpoint.get("endpoint_role") != "national_and_tokyo_cpi_schedule":
        raise RuntimeError("BW Japan CPI registered endpoint drift")

    all_cpi = [r for r in canonical.get("records", []) if r.get("source_id") == SOURCE_ID]
    if len(all_cpi) != 7:
        raise RuntimeError(f"BW expected exactly seven Canonical dependencies on {SOURCE_ID}, found {len(all_cpi)}")
    expected_ids = {f"WSO-MAC-A-{n:04d}" for n in range(50, 57)}
    if {r.get("occurrence_id") for r in all_cpi} != expected_ids:
        raise RuntimeError("BW Japan CPI Canonical dependency identity set drift")

    ids = list(plan["canonical_occurrence_ids"])
    if len(ids) != 7 or len(set(ids)) != 7 or set(ids) != expected_ids:
        raise RuntimeError("BW requires exact seven-occurrence Japan CPI allow-list")
    by_id = {r.get("occurrence_id"): r for r in canonical.get("records", []) if r.get("occurrence_id") in set(ids)}
    expected_rows = {row["occurrence_id"]: row for row in plan["canonical_occurrences"]}
    if set(by_id) != set(ids) or set(expected_rows) != set(ids):
        raise RuntimeError("BW Japan CPI allow-list no longer matches Canonical or plan")

    for occurrence_id in ids:
        row = by_id[occurrence_id]
        expected = expected_rows[occurrence_id]
        checks = {
            "series_id": SERIES_ID,
            "source_id": SOURCE_ID,
            "region": REGION,
            "source_timezone": TIMEZONE,
            "reference_period": expected["reference_period"],
            "start_local": expected["canonical_start_local"],
            "start_utc": expected["canonical_start_utc"],
            "time_precision": "MINUTE",
            "time_basis": "EXPLICIT_OCCURRENCE_TIME",
            "timing_type": "LOCAL_DATETIME",
            "lifecycle_status": "PLANNED",
            "certainty_status": "CONFIRMED",
            "notes": "Date from official schedule; 08:30 JST from official CPI publication rule.",
        }
        for key, value in checks.items():
            if row.get(key) != value:
                raise RuntimeError(
                    f"BW Japan CPI Canonical pre-state drift for {occurrence_id} {key}: {row.get(key)!r}"
                )
        if row.get("all_day_semantics") is True:
            raise RuntimeError(f"BW Japan CPI occurrence unexpectedly has all-day semantics: {occurrence_id}")
    return source


def updated_source(source_before: dict, plan: dict) -> dict:
    out = deepcopy(source_before)
    out.update(deepcopy(plan["source_governance_update"]))
    out.update({
        "automation_summary": (
            "WORLD SIGNALS automation is bounded to one Statistics Bureau robots-policy request followed, only when allowed, "
            "by one exact registered national/Tokyo CPI schedule request. The parser reads national CPI date cells only for "
            "the configured Canonical scope; Tokyo CPI, e-Stat/API, data releases, PDFs, news and search routes are not followed."
        ),
        "automation_reviewed_at": plan["reference_date"],
        "live_validation_evidence": {
            "endpoint_diagnostic_run_id": plan["read_only_endpoint_diagnostic"]["run_id"],
            "endpoint_diagnostic_job_id": plan["read_only_endpoint_diagnostic"]["job_id"],
            "registered_endpoint_run_id": plan["read_only_registered_endpoint_check"]["run_id"],
            "registered_endpoint_job_id": plan["read_only_registered_endpoint_check"]["job_id"],
            "request_budget_per_run": 2,
            "configured_exact_unique_match_count": 7,
            "clock_exposed_by_schedule": False,
            "automatic_commit_allowed": False,
        },
        "monitor_endpoints": [
            deepcopy(source_before["monitor_endpoints"][0]),
            {
                "endpoint_role": "robots_policy",
                "url": ROBOTS_URL,
                "transport": "TEXT_PLAIN",
                "preferred_for_monitoring": True,
                "completeness_scope": "AUTOMATION_POLICY_GATE_FOR_REGISTERED_CPI_SCHEDULE",
            },
        ],
        "source_role_contract": deepcopy(plan["source_role_contract"]),
    })

    changed = _changed_keys(source_before, out)
    if not changed or not changed <= ALLOWED_SOURCE_MUTATION_KEYS:
        raise RuntimeError(
            f"BW Japan CPI source mutation escaped automation/readiness boundary: {sorted(changed)}"
        )
    for key in IMMUTABLE_SOURCE_KEYS:
        if out.get(key) != source_before.get(key):
            raise RuntimeError(f"BW improperly changed Japan CPI identity/rights/provenance field {key}")
    if out.get("verification_mode") != "AUTOMATED_PILOT":
        raise RuntimeError("BW must not overstate Japan CPI verification mode")
    return out


def monitor_expectation(plan: dict) -> dict:
    identity = {
        row["occurrence_id"]: {
            "series_id": row["series_id"],
            "reference_period": row["reference_period"],
        }
        for row in plan["canonical_occurrences"]
    }
    return {
        "adapter_id": ADAPTER_ID,
        "source_id": SOURCE_ID,
        "canonical_schedule_source_id": SOURCE_ID,
        "same_source_identity_for_canonical_and_monitor": True,
        "canonical_occurrence_ids": list(plan["canonical_occurrence_ids"]),
        "identity_by_occurrence_id": identity,
        "registered_schedule_url": SCHEDULE_URL,
        "robots_url": ROBOTS_URL,
        "separate_clock_rule_url": CLOCK_RULE_URL,
        "monitor_role": "OFFICIAL_JAPAN_NATIONAL_CPI_RELEASE_DATE_DRIFT_SENTINEL",
        "cadence": "WEEKLY; DAILY_INSIDE_7_DAYS_OF_CONFIGURED_RELEASE",
        "request_budget_per_run": 2,
        "robots_requests_per_run": 1,
        "schedule_requests_per_run": 1,
        "followup_requests_per_run": 0,
        "classification_contract": deepcopy(plan["classification_contract"]),
        "source_role_contract": deepcopy(plan["source_role_contract"]),
        "source_failure_policy": "SOURCE_HEALTH_ONLY_NO_EVENT_MUTATION",
        "positive_change_policy": "GENERATE_DATE_REVIEW_CANDIDATE_FOR_SAME_STABLE_OCCURRENCE_ID_ONLY",
        "absence_policy": "MISSING_CONFIGURED_ROW_IS_REVIEW_EVIDENCE_ONLY_NO_EVENT_STATE_INFERENCE",
        "outside_scope_policy": "OBSERVE_ONLY_NO_AUTOMATIC_CANONICAL_ADDITION",
        "schedule_mutation_authority": False,
        "clock_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "canonical_clock_mutation_allowed": False,
        "automatic_tokyo_cpi_followup_allowed": False,
        "automatic_estat_api_followup_allowed": False,
        "automatic_data_release_followup_allowed": False,
        "automatic_pdf_fetch_allowed": False,
        "automatic_news_followup_allowed": False,
        "automatic_search_route_discovery_allowed": False,
        "live_intelligence_policy": "NO_AUTOMATIC_PROMOTION_TO_LIVE_INTELLIGENCE_OR_ANALYSIS",
        "automatic_commit_allowed": False,
    }


def transform_sources(sources: dict, plan: dict, source_before: dict) -> dict:
    out = deepcopy(sources)
    indexes = [i for i, row in enumerate(out["sources"]) if row.get("source_id") == SOURCE_ID]
    if len(indexes) != 1:
        raise RuntimeError("BW Japan CPI source identity count drift")
    other_before = [deepcopy(row) for row in out["sources"] if row.get("source_id") != SOURCE_ID]
    out["sources"][indexes[0]] = updated_source(source_before, plan)
    other_after = [row for row in out["sources"] if row.get("source_id") != SOURCE_ID]
    if other_after != other_before:
        raise RuntimeError("BW modified a non-Japan-CPI source")
    if len(out["sources"]) != len(sources["sources"]):
        raise RuntimeError("BW must not add or remove a source identity")
    out["version"] = plan["postconditions"]["source_registry_version"]
    out["reference_date"] = plan["reference_date"]
    return out


def transform_expectations(expectations: dict, plan: dict) -> dict:
    out = deepcopy(expectations)
    before = deepcopy(out.get("adapters", []))
    out["adapters"].append(monitor_expectation(plan))
    if out["adapters"][:-1] != before:
        raise RuntimeError("BW changed an existing monitor route")
    out["version"] = plan["postconditions"]["monitor_expectations_version"]
    if out.get("automatic_canonical_commit") is not False or out.get("google_calendar_write") is not False:
        raise RuntimeError("BW changed global write gates")
    return out


def patch_adapter_init(text: str) -> str:
    if "JAPAN_CPI_SCHEDULE_URL" in text:
        raise RuntimeError("Japan CPI schedule adapter already exported")
    import_anchor = "from .japan_statistics_dashboard import (\n"
    import_block = '''from .japan_cpi_schedule import (\n    JAPAN_CPI_ACCEPT,\n    JAPAN_CPI_CLOCK_RULE_URL,\n    JAPAN_CPI_ROBOTS_URL,\n    JAPAN_CPI_SCHEDULE_URL,\n    JAPAN_CPI_TIMEZONE,\n    JapanCPIReleaseRow,\n    fetch_japan_cpi_robots_policy,\n    fetch_japan_cpi_schedule,\n    japan_cpi_schedule_allowed,\n    parse_japan_cpi_schedule,\n)\n'''
    if import_anchor not in text:
        raise RuntimeError("BW adapter import anchor missing")
    text = text.replace(import_anchor, import_block + import_anchor, 1)

    all_anchor = '    "JAPAN_HHSPEND_CYCLE",\n'
    all_block = '''    "JAPAN_CPI_ACCEPT",\n    "JAPAN_CPI_CLOCK_RULE_URL",\n    "JAPAN_CPI_ROBOTS_URL",\n    "JAPAN_CPI_SCHEDULE_URL",\n    "JAPAN_CPI_TIMEZONE",\n    "JapanCPIReleaseRow",\n'''
    if all_anchor not in text:
        raise RuntimeError("BW adapter __all__ anchor missing")
    text = text.replace(all_anchor, all_block + all_anchor, 1)

    fn_anchor = '    "fetch_japan_household_spending_data",\n'
    fn_block = '''    "fetch_japan_cpi_robots_policy",\n    "fetch_japan_cpi_schedule",\n    "japan_cpi_schedule_allowed",\n    "parse_japan_cpi_schedule",\n'''
    if fn_anchor not in text:
        raise RuntimeError("BW adapter function export anchor missing")
    return text.replace(fn_anchor, fn_block + fn_anchor, 1)


def patch_live_runner(text: str) -> str:
    if 'if "JAPAN_CPI_RELEASE_SCHEDULE" in configs:' in text:
        raise RuntimeError("Japan CPI live route already wired")
    adapter_import_anchor = "    fetch_japan_household_spending_data,\n"
    if adapter_import_anchor not in text:
        raise RuntimeError("BW live adapter import anchor missing")
    text = text.replace(
        adapter_import_anchor,
        "    fetch_japan_cpi_robots_policy,\n    fetch_japan_cpi_schedule,\n" + adapter_import_anchor,
        1,
    )
    monitor_import_anchor = (
        "from world_signals.japan_household_spending_monitor import japan_household_spending_review_candidates\n"
    )
    monitor_import = "from world_signals.japan_cpi_monitor import japan_cpi_schedule_review_candidates\n"
    if monitor_import_anchor not in text:
        raise RuntimeError("BW live monitor import anchor missing")
    text = text.replace(monitor_import_anchor, monitor_import + monitor_import_anchor, 1)

    route_anchor = '    if "JAPAN_HHSPEND_STATISTICS_DASHBOARD_API" in configs:\n'
    if route_anchor not in text:
        raise RuntimeError("BW live route insertion anchor missing")
    block = '''    if "JAPAN_CPI_RELEASE_SCHEDULE" in configs:\n        jp_cpi_config=configs["JAPAN_CPI_RELEASE_SCHEDULE"]\n        try:\n            jp_cpi_allowed,jp_cpi_robots_snap=fetch_japan_cpi_robots_policy()\n            if not jp_cpi_allowed:\n                report["source_health"].append({\n                    "adapter_id":"JAPAN_CPI_RELEASE_SCHEDULE",\n                    "source_id":jp_cpi_config["source_id"],\n                    "state":"DEGRADED",\n                    "robots_snapshot":jp_cpi_robots_snap.as_dict(),\n                    "failure_stage":"ROBOTS_POLICY_NOW_DISALLOWS_REGISTERED_JAPAN_CPI_SCHEDULE",\n                    "schedule_request_skipped":True,\n                    "canonical_action":"NONE",\n                    "clock_authority":False,\n                    "lifecycle_authority":False,\n                    "certainty_authority":False,\n                    "automatic_commit_allowed":False,\n                })\n            else:\n                jp_cpi_items,jp_cpi_schedule_snap=fetch_japan_cpi_schedule()\n                report["source_health"].append({\n                    "adapter_id":"JAPAN_CPI_RELEASE_SCHEDULE",\n                    "source_id":jp_cpi_config["source_id"],\n                    "state":"HEALTHY",\n                    "robots_snapshot":jp_cpi_robots_snap.as_dict(),\n                    "schedule_snapshot":jp_cpi_schedule_snap.as_dict(),\n                    "national_schedule_row_count":len(jp_cpi_items),\n                    "request_budget_per_run":2,\n                    "robots_request_count":1,\n                    "schedule_request_count":1,\n                    "followup_request_count":0,\n                    "tokyo_cpi_followup_request_count":0,\n                    "estat_api_followup_request_count":0,\n                    "data_release_followup_request_count":0,\n                    "pdf_followup_request_count":0,\n                    "news_followup_request_count":0,\n                    "search_route_request_count":0,\n                    "schedule_mutation_authority":False,\n                    "clock_authority":False,\n                    "lifecycle_authority":False,\n                    "certainty_authority":False,\n                    "canonical_clock_mutation_allowed":False,\n                    "automatic_commit_allowed":False,\n                })\n                candidates,observations=japan_cpi_schedule_review_candidates(\n                    registry.get("records",[]),jp_cpi_items,jp_cpi_config\n                )\n                report["review_candidates"].extend(candidates)\n                report["observations"].extend(observations)\n        except (AdapterError,ValueError) as exc:\n            report["source_health"].append({\n                "adapter_id":"JAPAN_CPI_RELEASE_SCHEDULE",\n                "source_id":jp_cpi_config["source_id"],\n                "state":"DEGRADED",\n                "error":str(exc),\n                "canonical_action":"NONE",\n                "absence_is_not_event_state":True,\n                "schedule_mutation_authority":False,\n                "clock_authority":False,\n                "lifecycle_authority":False,\n                "certainty_authority":False,\n                "canonical_clock_mutation_allowed":False,\n                "automatic_commit_allowed":False,\n            })\n\n'''
    return text.replace(route_anchor, block + route_anchor, 1)


def patch_smoke_runner(text: str) -> str:
    if '"adapter":"JAPAN_CPI_RELEASE_SCHEDULE"' in text:
        raise RuntimeError("Japan CPI smoke route already wired")
    adapter_import_anchor = "    fetch_japan_household_spending_data,\n"
    if adapter_import_anchor not in text:
        raise RuntimeError("BW smoke adapter import anchor missing")
    text = text.replace(
        adapter_import_anchor,
        "    fetch_japan_cpi_robots_policy,\n    fetch_japan_cpi_schedule,\n" + adapter_import_anchor,
        1,
    )
    route_anchor = "    try:\n        jp_values,jp_snap=fetch_japan_household_spending_data(\n"
    if route_anchor not in text:
        raise RuntimeError("BW smoke route insertion anchor missing")
    block = '''    try:\n        jp_cpi_allowed,jp_cpi_robots_snap=fetch_japan_cpi_robots_policy()\n        if not jp_cpi_allowed:\n            raise AdapterError("Statistics Bureau robots policy disallows the registered CPI schedule path")\n        jp_cpi_items,jp_cpi_schedule_snap=fetch_japan_cpi_schedule()\n        report["results"].append({\n            "adapter":"JAPAN_CPI_RELEASE_SCHEDULE",\n            "status":"PASS",\n            "source_id":"WSSRC-MAC-014",\n            "robots_snapshot":jp_cpi_robots_snap.as_dict(),\n            "schedule_snapshot":jp_cpi_schedule_snap.as_dict(),\n            "national_schedule_row_count":len(jp_cpi_items),\n            "request_budget_per_run":2,\n            "robots_request_count":1,\n            "schedule_request_count":1,\n            "followup_request_count":0,\n            "clock_authority":False,\n            "lifecycle_authority":False,\n            "certainty_authority":False,\n            "canonical_clock_mutation_allowed":False,\n            "automatic_commit_allowed":False,\n        })\n    except (AdapterError,ValueError) as exc:\n        failures.append({"adapter":"JAPAN_CPI_RELEASE_SCHEDULE","error":str(exc)})\n\n'''
    return text.replace(route_anchor, block + route_anchor, 1)


def build_post_state(
    canonical: dict,
    sources: dict,
    expectations: dict,
    plan: dict,
    *,
    adapter_init_text: str,
    live_runner_text: str,
    smoke_runner_text: str,
) -> tuple[dict, dict, str, str, str, dict]:
    source_before = preflight(canonical, sources, expectations, plan)
    post_sources = transform_sources(sources, plan, source_before)
    post_expectations = transform_expectations(expectations, plan)
    post_adapter_init = patch_adapter_init(adapter_init_text)
    post_live_runner = patch_live_runner(live_runner_text)
    post_smoke_runner = patch_smoke_runner(smoke_runner_text)

    source_after = source_by_id(post_sources, SOURCE_ID)
    report = {
        "tranche": "BW",
        "mode": "READ_ONLY_PREFLIGHT",
        "base_sha": BASE_SHA,
        "source_id": SOURCE_ID,
        "adapter_id": ADAPTER_ID,
        "source_count_before": len(sources["sources"]),
        "source_count_after": len(post_sources["sources"]),
        "source_version_before": sources["version"],
        "source_version_after": post_sources["version"],
        "monitor_version_before": expectations["version"],
        "monitor_version_after": post_expectations["version"],
        "monitor_count_before": len(expectations["adapters"]),
        "monitor_count_after": len(post_expectations["adapters"]),
        "configured_occurrence_count": 7,
        "changed_source_keys": sorted(_changed_keys(source_before, source_after)),
        "canonical_changed": False,
        "automatic_canonical_commit": post_expectations["automatic_canonical_commit"],
        "google_calendar_write": post_expectations["google_calendar_write"],
        "mutation_paths": [str(path.relative_to(ROOT)) for path in MUTATION_PATHS],
    }
    return (
        post_sources,
        post_expectations,
        post_adapter_init,
        post_live_runner,
        post_smoke_runner,
        report,
    )


def run(*, apply: bool) -> dict:
    plan = load_json(PLAN_PATH)
    canonical_before_bytes = CANONICAL_PATH.read_bytes()
    canonical = load_json(CANONICAL_PATH)
    sources = load_json(SOURCES_PATH)
    expectations = load_json(EXPECTATIONS_PATH)
    adapter_init_text = ADAPTER_INIT_PATH.read_text(encoding="utf-8")
    live_runner_text = LIVE_RUNNER_PATH.read_text(encoding="utf-8")
    smoke_runner_text = SMOKE_RUNNER_PATH.read_text(encoding="utf-8")

    post = build_post_state(
        canonical,
        sources,
        expectations,
        plan,
        adapter_init_text=adapter_init_text,
        live_runner_text=live_runner_text,
        smoke_runner_text=smoke_runner_text,
    )
    post_sources, post_expectations, post_adapter_init, post_live_runner, post_smoke_runner, report = post

    if not apply:
        if CANONICAL_PATH.read_bytes() != canonical_before_bytes:
            raise RuntimeError("BW check-only path unexpectedly changed Canonical")
        return report

    if os.getenv(APPLY_ENV) != "1":
        raise RuntimeError(f"BW APPLY REFUSED: set {APPLY_ENV}=1")

    dump_json(SOURCES_PATH, post_sources)
    dump_json(EXPECTATIONS_PATH, post_expectations)
    ADAPTER_INIT_PATH.write_text(post_adapter_init, encoding="utf-8")
    LIVE_RUNNER_PATH.write_text(post_live_runner, encoding="utf-8")
    SMOKE_RUNNER_PATH.write_text(post_smoke_runner, encoding="utf-8")
    if CANONICAL_PATH.read_bytes() != canonical_before_bytes:
        raise RuntimeError("BW apply path changed Canonical")
    report["mode"] = "APPLIED_GOVERNED_RUNTIME_PATCH"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Guarded BW activation helper for the Statistics Bureau Japan CPI release-date monitor. "
            f"Default is read-only; --apply additionally requires {APPLY_ENV}=1."
        )
    )
    parser.add_argument("--apply", action="store_true", help="materialise the exact five-file governed/runtime patch")
    args = parser.parse_args()
    try:
        report = run(apply=args.apply)
    except Exception as exc:
        print(f"BW JAPAN CPI MONITOR PRECONDITION FAILED: {exc}")
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
