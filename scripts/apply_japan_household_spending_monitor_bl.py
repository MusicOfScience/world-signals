from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

PLAN_PATH = ROOT / "data/monitor/JAPAN_HHSPEND_API_MONITOR_BL_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
LIVE_RUNNER_PATH = ROOT / "scripts/run_live_monitor.py"
SMOKE_RUNNER_PATH = ROOT / "scripts/run_adapter_smoke.py"
ADAPTER_INIT_PATH = ROOT / "src/world_signals/adapters/__init__.py"

APPLY_ENV = "WORLD_SIGNALS_APPLY_MONITOR_BL"
NEW_SOURCE_ID = "WSSRC-MAC-030"
CANONICAL_SCHEDULE_SOURCE_ID = "WSSRC-MAC-024"
MANUAL_RESULT_SOURCE_ID = "WSSRC-MAC-029"
ADAPTER_ID = "JAPAN_HHSPEND_STATISTICS_DASHBOARD_API"
SERIES_ID = "WSER-MAC-JP-HHSPEND"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def source_by_id(data: dict, source_id: str) -> dict:
    rows = [row for row in data.get("sources", []) if row.get("source_id") == source_id]
    if len(rows) != 1:
        raise RuntimeError(f"expected exactly one source {source_id}, found {len(rows)}")
    return rows[0]


def tracked_from_plan(plan: dict) -> list[dict]:
    return deepcopy(plan["tracked_releases"])


def _civil_date(record: dict) -> str | None:
    value = record.get("start_local")
    return value[:10] if isinstance(value, str) and len(value) >= 10 else None


def preflight(canonical: dict, sources: dict, expectations: dict, plan: dict) -> None:
    p = plan["preconditions"]
    if plan.get("exact_base_main_sha") != "3952ec1f5a6022fec43210103f7a7244442e3201":
        raise RuntimeError("BL plan is not frozen to the exact post-BK main SHA")
    if (canonical.get("version"), len(canonical.get("records", []))) != (
        p["canonical_registry_version"], p["canonical_record_count"]
    ):
        raise RuntimeError("BL requires exact post-BK canonical v0.41 / 689")
    if (sources.get("version"), len(sources.get("sources", []))) != (
        p["source_registry_version"], p["source_count"]
    ):
        raise RuntimeError("BL requires exact post-BK Sources v1.84 / 246")
    if (expectations.get("version"), len(expectations.get("adapters", []))) != (
        p["monitor_expectations_version"], p["configured_monitor_adapter_count"]
    ):
        raise RuntimeError("BL requires exact post-BK Monitor v0.11 / 9")
    if expectations.get("automatic_canonical_commit") is not False:
        raise RuntimeError("automatic Canonical commit gate is not closed")
    if expectations.get("google_calendar_write") is not False:
        raise RuntimeError("Google Calendar write gate is not closed")

    source_ids = {row.get("source_id") for row in sources.get("sources", [])}
    for source_id in p["required_source_ids"]:
        if source_id not in source_ids:
            raise RuntimeError(f"required BL source missing: {source_id}")
    for source_id in p["required_absent_source_ids"]:
        if source_id in source_ids:
            raise RuntimeError(f"BL machine source already exists: {source_id}")
    if any(row.get("adapter_id") == ADAPTER_ID for row in expectations.get("adapters", [])):
        raise RuntimeError("BL monitor route already exists")

    schedule_source = source_by_id(sources, CANONICAL_SCHEDULE_SOURCE_ID)
    if schedule_source.get("canonical_dependency_count") != 8:
        raise RuntimeError("Japan household-spending canonical source dependency count drifted")
    if schedule_source.get("automated_monitoring_use") != "ENDPOINT_REVIEW_REQUIRED":
        raise RuntimeError("BL must not silently change WSSRC-MAC-024 automation governance")
    result_source = source_by_id(sources, MANUAL_RESULT_SOURCE_ID)
    if result_source.get("canonical_dependency_count") != 0:
        raise RuntimeError("Japan result-verification source dependency count drifted")

    expected = tracked_from_plan(plan)
    expected_ids = [row["occurrence_id"] for row in expected]
    actual = [row for row in canonical.get("records", []) if row.get("series_id") == SERIES_ID]
    actual_by_id = {row.get("occurrence_id"): row for row in actual}
    if set(actual_by_id) != set(expected_ids) or len(actual) != p["household_spending_occurrence_count"]:
        raise RuntimeError("Japan household-spending Canonical occurrence scope drifted")
    for tracked in expected:
        record = actual_by_id[tracked["occurrence_id"]]
        if _civil_date(record) != tracked["canonical_release_date"]:
            raise RuntimeError(f"Japan household-spending release date drifted for {tracked['occurrence_id']}")
        if record.get("source_id") != CANONICAL_SCHEDULE_SOURCE_ID:
            raise RuntimeError(f"Japan household-spending Canonical source drifted for {tracked['occurrence_id']}")
        if record.get("source_timezone") != p["household_spending_source_timezone"]:
            raise RuntimeError(f"Japan household-spending timezone drifted for {tracked['occurrence_id']}")
        if record.get("time_precision") != p["household_spending_time_precision"]:
            raise RuntimeError(f"Japan household-spending precision drifted for {tracked['occurrence_id']}")
        if record.get("start_utc") is not None:
            raise RuntimeError(f"BL refuses a household-spending occurrence with invented UTC clock: {tracked['occurrence_id']}")


def new_machine_source(plan: dict) -> dict:
    api = plan["api_identity"]
    return {
        "source_id": NEW_SOURCE_ID,
        "institution": "Statistics Bureau of Japan / Ministry of Internal Affairs and Communications",
        "jurisdiction": "Japan",
        "domain": "macro_releases",
        "endpoint_role": "Family Income and Expenditure Survey household-spending machine data availability sentinel",
        "authoritative_url": api["documentation_url"],
        "source_type": "official_statistical_webapi",
        "information_supplied": (
            "Official machine-readable household-spending reference-period data availability, value and provisional-status metadata. "
            "This source is not release-calendar authority and has zero Canonical schedule dependencies."
        ),
        "future_schedule_horizon": "not a schedule source; data availability follows published statistical releases",
        "typical_advance_notice": "not applicable; current data-state sentinel",
        "machine_readable_available": "REST JSON WebAPI",
        "source_timezone": "Asia/Tokyo",
        "recommended_verification_cadence": "daily; one bounded household-spending request per monitor run",
        "activation_status": "ACTIVE_GUARDED",
        "parser_type": "STATISTICS_DASHBOARD_JSON_REFERENCE_PERIOD_SENTINEL",
        "parser_version": "japan-hhspend-dashboard-0.1",
        "known_limitations": [
            "The WebAPI is a result/data interface, not authority for the pre-announced release schedule.",
            "A requested Time value is echoed even when no DATA_OBJ.VALUE row exists; only validated VALUE rows establish data availability.",
            "Data presence before the Canonical release date is review evidence only and does not move the release date.",
            "Data presence on or after the Canonical release date requires manual WSSRC-MAC-029 completion verification before lifecycle changes.",
            "The API provides no Canonical release clock for this series; all tracked occurrences remain DAY precision in Asia/Tokyo.",
            "BL does not automatically promote returned statistical values into Live Intelligence or Analysis."
        ],
        "timezone_scope": "SOURCE_NATIVE_JAPAN_CIVIL_DATE",
        "licence_constraints": "Use the official public WebAPI without abusive short-period mass access; one bounded request is used per monitor run.",
        "ingestion_permission": "OFFICIAL_MACHINE_DATA_SENTINEL_ALLOWED",
        "licence_review_status": "CLEARED_EXPLICIT_PUBLIC_WEBAPI_USE",
        "automated_retrieval_permission": "OFFICIAL_REST_WEBAPI_NO_REGISTRATION_BOUNDED_REQUESTS",
        "redistribution_permission": "NO_BROAD_REDISTRIBUTION_ASSERTED_BEYOND_CURATED_INTERNAL_MONITOR_METADATA",
        "rights_evidence_url": api["documentation_url"],
        "rights_summary": (
            "Statistics Dashboard documentation explicitly publishes a REST WebAPI, states that no registration is required and that anyone may use it, "
            "subject to Site Policy. Official Japanese API guidance prohibits abusive short-period mass access that interferes with the service."
        ),
        "automation_summary": "Automation is limited to one small bounded getData request per run for one reviewed indicator and explicit monthly reference periods.",
        "rights_reviewed_at": "2026-09-08",
        "rights_review_scope": "BL_EXPLICIT_MACHINE_INTERFACE_AND_ANTI_ABUSE_DISCIPLINE",
        "rights_review_note": "Operational governance classification for WORLD SIGNALS; not a legal opinion.",
        "canonical_provenance_use": "MONITOR_ONLY_MACHINE_SENTINEL_NO_CANONICAL_SCHEDULE_AUTHORITY",
        "automated_monitoring_use": "CLEARED",
        "verification_mode": "AUTOMATED_PILOT",
        "runtime_health_state": "LIVE_GITHUB_ACTIONS_FETCH_PARSE_PASS_2026_09_08",
        "monitoring_readiness_status": "LIVE_VALIDATED_NO_AUTO_COMMIT",
        "monitoring_activation_status": "LIVE_READ_ONLY_DATA_AVAILABILITY_SENTINEL_NO_AUTO_COMMIT",
        "canonical_dependency_count": 0,
        "monitoring_readiness_assessed_at": "2026-09-08",
        "governance_backfill_reviewed_at": "2026-09-08",
        "governance_backfill_basis": (
            "Separate official machine-interface identity created because WSSRC-MAC-024 remains Canonical schedule authority with endpoint review still required. "
            "The Statistics Dashboard WebAPI has explicit public machine-use terms and deterministic household-spending identity."
        ),
        "live_adapter_id": ADAPTER_ID,
        "live_validation_evidence": {
            "metadata_and_policy_probe_run_id": 34168995455,
            "data_availability_probe_run_id": 34169141999,
            "observed_at": "2026-09-08",
            "http_status": 200,
            "indicator_code": api["indicator_code"],
            "july_reference_period_present": True,
            "august_reference_period_absent_at_probe": True,
            "one_bounded_request_per_run": True,
            "automatic_commit_allowed": False
        },
        "required_authoritative_verification_source_ids": [MANUAL_RESULT_SOURCE_ID],
        "related_source_ids": [CANONICAL_SCHEDULE_SOURCE_ID, MANUAL_RESULT_SOURCE_ID],
        "source_role_contract": {
            "canonical_schedule_source_id": CANONICAL_SCHEDULE_SOURCE_ID,
            "machine_data_availability_source_id": NEW_SOURCE_ID,
            "manual_completion_verification_source_id": MANUAL_RESULT_SOURCE_ID
        },
        "monitor_endpoints": [
            {
                "endpoint_role": "statistics_dashboard_household_spending_getData",
                "url": api["data_endpoint_base"],
                "transport": "REST_JSON",
                "preferred_for_monitoring": True,
                "completeness_scope": "ONE_REVIEWED_INDICATOR_BOUNDED_REFERENCE_PERIOD_RANGE",
                "notes": "Query exactly one reviewed indicator and a bounded TimeFrom/TimeTo range; do not enumerate the wider API."
            },
            {
                "endpoint_role": "statistics_dashboard_api_documentation",
                "url": api["documentation_url"],
                "transport": "HTML_MANUAL_GOVERNANCE_REFERENCE",
                "preferred_for_monitoring": False,
                "completeness_scope": "API_USE_AND_PARAMETER_DOCUMENTATION"
            }
        ]
    }


def monitor_expectation(plan: dict) -> dict:
    tracked = tracked_from_plan(plan)
    api = plan["api_identity"]
    route = plan["monitor_route"]
    return {
        "adapter_id": ADAPTER_ID,
        "source_id": NEW_SOURCE_ID,
        "canonical_occurrence_ids": [row["occurrence_id"] for row in tracked],
        "monitor_role": "REFERENCE_PERIOD_DATA_AVAILABILITY_SENTINEL",
        "cadence": "DAILY",
        "api_query": {
            "documentation_url": api["documentation_url"],
            "transport": "REST_JSON",
            "indicator_code": api["indicator_code"],
            "stat_code": api["stat_code"],
            "cycle": api["cycle"],
            "regional_rank": api["regional_rank"],
            "region_code": api["region_code"],
            "original_series_code": api["original_series_code"],
            "time_from": route["query_time_from"],
            "time_to": route["query_time_to"],
            "request_policy": "ONE_BOUNDED_REQUEST_PER_MONITOR_RUN"
        },
        "tracked_releases": [
            {
                "occurrence_id": row["occurrence_id"],
                "reference_period_code": row["reference_period_code"]
            }
            for row in tracked
        ],
        "source_role_contract": {
            "canonical_schedule_source_id": CANONICAL_SCHEDULE_SOURCE_ID,
            "machine_data_availability_source_id": NEW_SOURCE_ID,
            "manual_completion_verification_source_id": MANUAL_RESULT_SOURCE_ID
        },
        "required_manual_verification_source_ids": [MANUAL_RESULT_SOURCE_ID],
        "source_failure_policy": "SOURCE_HEALTH_ONLY_NO_EVENT_MUTATION",
        "absence_policy": "NO_CANCELLATION_DELAY_DATE_OR_COMPLETION_INFERENCE",
        "early_presence_policy": "GENERATE_REVIEW_CANDIDATE_NO_SCHEDULE_CHANGE_INFERENCE",
        "on_or_after_date_presence_policy": "GENERATE_COMPLETION_REVIEW_REQUIRE_MANUAL_RESULT_VERIFICATION",
        "precision_policy": "API_DOES_NOT_SUPPLY_OR_CHANGE_CANONICAL_RELEASE_CLOCK",
        "certainty_policy": "API_DOES_NOT_CHANGE_CANONICAL_CERTAINTY",
        "live_intelligence_policy": "NO_AUTOMATIC_PROMOTION_OF_API_VALUES_TO_LIVE_INTELLIGENCE",
        "automatic_commit_allowed": False
    }


def transform_sources(sources: dict, plan: dict) -> dict:
    out = deepcopy(sources)
    if any(row.get("source_id") == NEW_SOURCE_ID for row in out.get("sources", [])):
        raise RuntimeError("BL machine source already exists")
    out["sources"].append(new_machine_source(plan))
    out["version"] = plan["postconditions"]["source_registry_version"]
    out["reference_date"] = plan["review_date"]
    return out


def transform_expectations(expectations: dict, plan: dict) -> dict:
    out = deepcopy(expectations)
    out["adapters"].append(monitor_expectation(plan))
    out["version"] = plan["postconditions"]["monitor_expectations_version"]
    if out.get("automatic_canonical_commit") is not False or out.get("google_calendar_write") is not False:
        raise RuntimeError("BL changed global write gates")
    return out


def patch_adapter_init(text: str) -> str:
    if "JAPAN_STATISTICS_DASHBOARD_DATA_API" in text:
        raise RuntimeError("Japan Statistics Dashboard adapter already exported")
    anchor = "from .japan_mof_jgb import (\n"
    if anchor not in text:
        raise RuntimeError("adapter __init__ Japan insertion anchor missing")
    block = '''from .japan_statistics_dashboard import (\n    JAPAN_HHSPEND_CYCLE,\n    JAPAN_HHSPEND_INDICATOR_CODE,\n    JAPAN_HHSPEND_ORIGINAL_SERIES,\n    JAPAN_HHSPEND_REGION_CODE,\n    JAPAN_HHSPEND_REGIONAL_RANK,\n    JAPAN_HHSPEND_STAT_CODE,\n    JAPAN_HHSPEND_TIMEZONE,\n    JAPAN_STATISTICS_DASHBOARD_API_DOCS,\n    JAPAN_STATISTICS_DASHBOARD_DATA_API,\n    JapanHouseholdSpendingValue,\n    fetch_japan_household_spending_data,\n    japan_household_spending_data_url,\n    parse_japan_household_spending_data_json,\n)\n'''
    text = text.replace(anchor, block + anchor, 1)
    export_anchor = '    "JGBAuctionEntry",\n'
    if export_anchor not in text:
        raise RuntimeError("adapter __all__ Japan export anchor missing")
    export_block = '''    "JAPAN_HHSPEND_CYCLE",\n    "JAPAN_HHSPEND_INDICATOR_CODE",\n    "JAPAN_HHSPEND_ORIGINAL_SERIES",\n    "JAPAN_HHSPEND_REGION_CODE",\n    "JAPAN_HHSPEND_REGIONAL_RANK",\n    "JAPAN_HHSPEND_STAT_CODE",\n    "JAPAN_HHSPEND_TIMEZONE",\n    "JAPAN_STATISTICS_DASHBOARD_API_DOCS",\n    "JAPAN_STATISTICS_DASHBOARD_DATA_API",\n    "JapanHouseholdSpendingValue",\n'''
    text = text.replace(export_anchor, export_block + export_anchor, 1)
    fn_anchor = '    "fetch_jgb_monthly_auction_calendar",\n'
    text = text.replace(fn_anchor, fn_anchor + '    "fetch_japan_household_spending_data",\n', 1)
    helper_anchor = '    "jgb_monthly_calendar_url",\n'
    text = text.replace(helper_anchor, helper_anchor + '    "japan_household_spending_data_url",\n', 1)
    parse_anchor = '    "parse_jgb_monthly_auction_calendar_html",\n'
    text = text.replace(parse_anchor, parse_anchor + '    "parse_japan_household_spending_data_json",\n', 1)
    return text


def patch_live_runner(text: str) -> str:
    if ADAPTER_ID in text:
        raise RuntimeError("live runner already contains BL route")
    import_anchor = "    fetch_jgb_monthly_auction_calendar,\n" if "    fetch_jgb_monthly_auction_calendar,\n" in text else "    fetch_ons_upcoming_releases,\n"
    if import_anchor not in text:
        raise RuntimeError("live runner adapter import anchor missing")
    text = text.replace(import_anchor, import_anchor + "    fetch_japan_household_spending_data,\n", 1)
    module_anchor = "from world_signals.eurostat_monitor import eurostat_release_calendar_review_candidates\n"
    if module_anchor not in text:
        raise RuntimeError("live runner Eurostat module import anchor missing")
    text = text.replace(
        module_anchor,
        module_anchor + "from world_signals.japan_household_spending_monitor import japan_household_spending_review_candidates\n",
        1,
    )
    insertion_anchor = '    try:\n        ons_items,ons_snaps=fetch_ons_upcoming_releases(\n'
    if insertion_anchor not in text:
        raise RuntimeError("live runner BL insertion anchor missing")
    block = '''    if "JAPAN_HHSPEND_STATISTICS_DASHBOARD_API" in configs:\n        jp_config=configs["JAPAN_HHSPEND_STATISTICS_DASHBOARD_API"]\n        query=jp_config.get("api_query") or {}\n        try:\n            jp_values,jp_snap=fetch_japan_household_spending_data(\n                time_from=query["time_from"],\n                time_to=query["time_to"],\n            )\n            report["source_health"].append({\n                "adapter_id":"JAPAN_HHSPEND_STATISTICS_DASHBOARD_API",\n                "source_id":jp_config["source_id"],\n                "state":"HEALTHY",\n                "snapshot":jp_snap.as_dict(),\n                "value_count":len(jp_values),\n                "reference_period_codes":[row.reference_period_code for row in jp_values],\n                "request_policy":"ONE_BOUNDED_REQUEST_PER_MONITOR_RUN",\n                "schedule_authority":False,\n            })\n            candidates,observations=japan_household_spending_review_candidates(\n                registry.get("records",[]),jp_values,jp_config\n            )\n            report["review_candidates"].extend(candidates)\n            report["observations"].extend(observations)\n        except (AdapterError,ValueError,KeyError) as exc:\n            report["source_health"].append({\n                "adapter_id":"JAPAN_HHSPEND_STATISTICS_DASHBOARD_API",\n                "source_id":jp_config["source_id"],\n                "state":"DEGRADED",\n                "error":str(exc),\n                "canonical_action":"NONE",\n                "absence_is_not_event_state":True,\n                "schedule_authority":False,\n            })\n\n'''
    return text.replace(insertion_anchor, block + insertion_anchor, 1)


def patch_smoke_runner(text: str) -> str:
    if ADAPTER_ID in text:
        raise RuntimeError("smoke runner already contains BL route")
    import_anchor = "    fetch_eurostat_release_calendar,\n"
    if import_anchor not in text:
        raise RuntimeError("smoke runner BL import anchor missing")
    text = text.replace(import_anchor, import_anchor + "    fetch_japan_household_spending_data,\n", 1)
    insertion_anchor = "    try:\n        ons_items,ons_snaps=fetch_ons_upcoming_releases()\n"
    if insertion_anchor not in text:
        raise RuntimeError("smoke runner BL insertion anchor missing")
    block = '''    try:\n        jp_values,jp_snap=fetch_japan_household_spending_data(\n            time_from="20260700",time_to="20270200"\n        )\n        report["results"].append({\n            "adapter":"JAPAN_HHSPEND_STATISTICS_DASHBOARD_API",\n            "status":"PASS",\n            "source_id":"WSSRC-MAC-030",\n            "snapshot":jp_snap.as_dict(),\n            "value_count":len(jp_values),\n            "reference_period_codes":[row.reference_period_code for row in jp_values],\n            "request_policy":"ONE_BOUNDED_REQUEST_PER_MONITOR_RUN",\n            "schedule_authority":False,\n            "automatic_commit_allowed":False,\n        })\n    except AdapterError as exc:\n        failures.append(str(exc))\n        report["results"].append({\n            "adapter":"JAPAN_HHSPEND_STATISTICS_DASHBOARD_API",\n            "status":"FAIL",\n            "source_id":"WSSRC-MAC-030",\n            "error":str(exc),\n            "canonical_action":"NONE",\n        })\n\n'''
    return text.replace(insertion_anchor, block + insertion_anchor, 1)


def build_post_state() -> tuple[dict, dict, str, str, str]:
    plan = load_json(PLAN_PATH)
    canonical = load_json(CANONICAL_PATH)
    sources = load_json(SOURCES_PATH)
    expectations = load_json(EXPECTATIONS_PATH)
    live = LIVE_RUNNER_PATH.read_text(encoding="utf-8")
    smoke = SMOKE_RUNNER_PATH.read_text(encoding="utf-8")
    adapter_init = ADAPTER_INIT_PATH.read_text(encoding="utf-8")
    preflight(canonical, sources, expectations, plan)
    post_sources = transform_sources(sources, plan)
    post_expectations = transform_expectations(expectations, plan)
    post_live = patch_live_runner(live)
    post_smoke = patch_smoke_runner(smoke)
    post_init = patch_adapter_init(adapter_init)
    validate_post_state(canonical, sources, expectations, post_sources, post_expectations, post_live, post_smoke, post_init, plan)
    return post_sources, post_expectations, post_live, post_smoke, post_init


def validate_post_state(
    canonical: dict,
    pre_sources: dict,
    pre_expectations: dict,
    post_sources: dict,
    post_expectations: dict,
    post_live: str,
    post_smoke: str,
    post_init: str,
    plan: dict,
) -> None:
    post = plan["postconditions"]
    if (canonical.get("version"), len(canonical.get("records", []))) != (
        post["canonical_registry_version"], post["canonical_record_count"]
    ):
        raise RuntimeError("BL changed or misread Canonical")
    if (post_sources.get("version"), len(post_sources.get("sources", []))) != (
        post["source_registry_version"], post["source_count"]
    ):
        raise RuntimeError("BL Sources post-state mismatch")
    if (post_expectations.get("version"), len(post_expectations.get("adapters", []))) != (
        post["monitor_expectations_version"], post["configured_monitor_adapter_count"]
    ):
        raise RuntimeError("BL Monitor post-state mismatch")
    if post_expectations.get("automatic_canonical_commit") is not False or post_expectations.get("google_calendar_write") is not False:
        raise RuntimeError("BL opened a global write gate")

    pre_by_id = {row["source_id"]: row for row in pre_sources["sources"]}
    post_by_id = {row["source_id"]: row for row in post_sources["sources"]}
    if set(post_by_id) != set(pre_by_id) | {NEW_SOURCE_ID}:
        raise RuntimeError("BL source identity mutation boundary exceeded")
    for source_id, record in pre_by_id.items():
        if post_by_id[source_id] != record:
            raise RuntimeError(f"BL changed pre-existing source record {source_id}")
    machine = post_by_id[NEW_SOURCE_ID]
    if machine.get("canonical_dependency_count") != 0:
        raise RuntimeError("BL machine source gained Canonical dependencies")
    if machine.get("automated_monitoring_use") != "CLEARED":
        raise RuntimeError("BL machine source automation is not explicitly CLEARED")
    if machine.get("source_role_contract", {}).get("canonical_schedule_source_id") != CANONICAL_SCHEDULE_SOURCE_ID:
        raise RuntimeError("BL source-role separation is not explicit")

    if post_expectations["adapters"][: len(pre_expectations["adapters"])] != pre_expectations["adapters"]:
        raise RuntimeError("BL changed a pre-existing monitor route")
    route = post_expectations["adapters"][-1]
    if route.get("adapter_id") != ADAPTER_ID or route.get("source_id") != NEW_SOURCE_ID:
        raise RuntimeError("BL route identity mismatch")
    if route.get("automatic_commit_allowed") is not False:
        raise RuntimeError("BL route unexpectedly permits automatic commit")
    if route.get("source_role_contract", {}).get("canonical_schedule_source_id") != CANONICAL_SCHEDULE_SOURCE_ID:
        raise RuntimeError("BL monitor route collapsed schedule and machine source identity")

    for text, token, label in (
        (post_live, ADAPTER_ID, "live runner"),
        (post_smoke, ADAPTER_ID, "smoke runner"),
        (post_init, "JAPAN_STATISTICS_DASHBOARD_DATA_API", "adapter exports"),
    ):
        if token not in text:
            raise RuntimeError(f"BL {label} patch missing")


def apply() -> None:
    if os.getenv(APPLY_ENV) != "1":
        raise SystemExit(f"refusing BL write: set {APPLY_ENV}=1")
    post_sources, post_expectations, post_live, post_smoke, post_init = build_post_state()
    dump_json(SOURCES_PATH, post_sources)
    dump_json(EXPECTATIONS_PATH, post_expectations)
    LIVE_RUNNER_PATH.write_text(post_live, encoding="utf-8")
    SMOKE_RUNNER_PATH.write_text(post_smoke, encoding="utf-8")
    ADAPTER_INIT_PATH.write_text(post_init, encoding="utf-8")
    print("BL transaction applied")


def check() -> None:
    post_sources, post_expectations, post_live, post_smoke, post_init = build_post_state()
    print(json.dumps({
        "status": "PASS",
        "source_registry_version": post_sources["version"],
        "source_count": len(post_sources["sources"]),
        "monitor_expectations_version": post_expectations["version"],
        "monitor_adapter_count": len(post_expectations["adapters"]),
        "new_source_id": NEW_SOURCE_ID,
        "adapter_id": ADAPTER_ID,
        "runtime_patches": {
            "live": ADAPTER_ID in post_live,
            "smoke": ADAPTER_ID in post_smoke,
            "adapter_exports": "JAPAN_STATISTICS_DASHBOARD_DATA_API" in post_init,
        },
        "automatic_canonical_commit": post_expectations["automatic_canonical_commit"],
        "google_calendar_write": post_expectations["google_calendar_write"],
    }, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="BL Japan household-spending API monitor transaction")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.apply:
        apply()
    else:
        check()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
