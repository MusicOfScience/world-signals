from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/monitor/INDEC_CPI_CALENDAR_BU_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
LIVE_RUNNER_PATH = ROOT / "scripts/run_live_monitor.py"
SMOKE_RUNNER_PATH = ROOT / "scripts/run_adapter_smoke.py"
ADAPTER_INIT_PATH = ROOT / "src/world_signals/adapters/__init__.py"

APPLY_ENV = "WORLD_SIGNALS_APPLY_MONITOR_BU"
BASE_SHA = "17e6130267c9d7911d12ac6f685c90228fec9e1e"
CANONICAL_SOURCE_ID = "WSSRC-REG2-006"
COMPLETED_SOURCE_ID = "WSSRC-REG2-008"
MACHINE_SOURCE_ID = "WSSRC-REG2-009"
ADAPTER_ID = "INDEC_CPI_CALENDAR"
SERIES_ID = "WSER-REG2-AR-CPI"
TIMEZONE = "America/Argentina/Buenos_Aires"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def source_by_id(data: dict, source_id: str) -> dict:
    rows = [row for row in data.get("sources", []) if row.get("source_id") == source_id]
    if len(rows) != 1:
        raise RuntimeError(f"expected exactly one source {source_id}, found {len(rows)}")
    return rows[0]


def preflight(canonical: dict, sources: dict, expectations: dict, plan: dict) -> tuple[dict, dict]:
    p = plan["preconditions"]
    if plan.get("exact_base_main_sha") != BASE_SHA:
        raise RuntimeError("BU plan is not frozen to exact post-BT main")
    if (canonical.get("version"), len(canonical.get("records", []))) != (
        p["canonical_registry_version"], p["canonical_record_count"]
    ):
        raise RuntimeError("BU requires exact Canonical v0.41 / 689")
    if (sources.get("version"), len(sources.get("sources", []))) != (
        p["source_registry_version"], p["source_count"]
    ):
        raise RuntimeError("BU requires exact Sources v1.93 / 251")
    if (expectations.get("version"), len(expectations.get("adapters", []))) != (
        p["monitor_expectations_version"], p["configured_monitor_adapter_count"]
    ):
        raise RuntimeError("BU requires exact Monitor v0.18 / 16")
    if expectations.get("automatic_canonical_commit") is not False:
        raise RuntimeError("automatic Canonical commit gate must remain closed")
    if expectations.get("google_calendar_write") is not False:
        raise RuntimeError("Google Calendar write gate must remain closed")
    if any(row.get("source_id") == MACHINE_SOURCE_ID for row in sources.get("sources", [])):
        raise RuntimeError("BU INDEC machine source already exists")
    if any(row.get("adapter_id") == ADAPTER_ID for row in expectations.get("adapters", [])):
        raise RuntimeError("BU INDEC monitor route already exists")

    schedule = deepcopy(source_by_id(sources, CANONICAL_SOURCE_ID))
    completed = deepcopy(source_by_id(sources, COMPLETED_SOURCE_ID))
    schedule_checks = {
        "institution": "INDEC",
        "jurisdiction": "Argentina",
        "domain": "macro_official_statistics",
        "source_timezone": TIMEZONE,
        "canonical_dependency_count": 5,
    }
    for key, expected in schedule_checks.items():
        if schedule.get(key) != expected:
            raise RuntimeError(f"BU INDEC schedule-source pre-state drift for {key}: {schedule.get(key)!r}")
    if schedule.get("automated_retrieval_permission") not in {
        "PENDING_ENDPOINT_OPERATIONAL_REVIEW", "PRODUCTION_AUTOMATION_HOLD"
    }:
        raise RuntimeError("BU expected held/review-required automation state on INDEC PDF schedule source")
    if completed.get("institution") != "INDEC" or completed.get("canonical_dependency_count") != 0:
        raise RuntimeError("BU INDEC completed-release source pre-state drift")

    ids = list(plan["canonical_occurrence_ids"])
    if len(ids) != 4 or len(set(ids)) != 4:
        raise RuntimeError("BU requires exact four-occurrence INDEC allow-list")
    by_id = {r.get("occurrence_id"): r for r in canonical.get("records", []) if r.get("occurrence_id") in set(ids)}
    if set(by_id) != set(ids):
        raise RuntimeError("BU INDEC allow-list no longer matches Canonical")
    expected_rows = {row["occurrence_id"]: row for row in plan["canonical_occurrences"]}
    for occurrence_id in ids:
        row = by_id[occurrence_id]
        expected = expected_rows[occurrence_id]
        checks = {
            "series_id": SERIES_ID,
            "source_id": CANONICAL_SOURCE_ID,
            "region": "Latin America",
            "source_timezone": TIMEZONE,
            "time_precision": "DAY",
            "timing_type": "CIVIL_DATE",
            "start_local": expected["canonical_release_date"],
            "reference_period": expected["reference_period"],
            "certainty_status": "CONFIRMED",
        }
        for key, value in checks.items():
            if row.get(key) != value:
                raise RuntimeError(f"BU INDEC Canonical drift for {occurrence_id} {key}: {row.get(key)!r}")
        if row.get("start_utc") is not None or row.get("all_day_semantics") is not True:
            raise RuntimeError(f"BU must preserve INDEC date-only/no-UTC semantics for {occurrence_id}")
    return schedule, completed


def new_machine_source(plan: dict) -> dict:
    s = plan["selection"]
    d = plan["read_only_diagnostics"]
    return {
        "source_id": MACHINE_SOURCE_ID,
        "institution": "INDEC",
        "jurisdiction": "Argentina",
        "domain": "macro_official_statistics",
        "endpoint_role": "Official INDEC interactive dissemination-calendar CPI schedule/change sentinel",
        "authoritative_url": s["calendar_url"],
        "source_type": "official_interactive_release_calendar",
        "information_supplied": (
            "First-party INDEC month-calendar rows for the four remaining 2026 national CPI releases, "
            "including report identity, civil release date and explicit 16:00 America/Argentina/Buenos_Aires clock metadata."
        ),
        "future_schedule_horizon": "through Dec 2026; exact four-occurrence BU allow-list only",
        "typical_advance_notice": "calendar publication and revision driven",
        "machine_readable_available": "bounded first-party HTML fragments invoked by official calendar UI",
        "source_timezone": TIMEZONE,
        "recommended_verification_cadence": "daily; one robots request plus at most four exact month-route requests",
        "activation_status": "ACTIVE_GUARDED",
        "parser_type": "INDEC_CPI_INTERACTIVE_CALENDAR_SENTINEL",
        "parser_version": "indec-cpi-calendar-0.1",
        "known_limitations": [
            "Only four reviewed 2026 month routes are permitted; this source is not a general INDEC crawler.",
            "Embedded Google Calendar URLs are parsed only as metadata already present in the INDEC response; Google is never requested.",
            "The richer 16:00 source clock is review evidence only and cannot automatically upgrade Canonical precision.",
            "Absence of a configured CPI row triggers review only and has no cancellation, delay, completion or certainty semantics.",
            "WSSRC-REG2-006 remains the Canonical forward-schedule provenance source and is preserved unchanged.",
            "WSSRC-REG2-008 remains post-event outcome/completion provenance only and is never automatically fetched by this route."
        ],
        "backup_source": None,
        "notes": "Separate machine identity preserves provenance-layer separation while exposing authoritative schedule and clock-change evidence.",
        "timezone_scope": "FIXED_AMERICA_ARGENTINA_BUENOS_AIRES",
        "licence_constraints": "INDEC_CREATIVE_COMMONS_TERMS_WITH_ATTRIBUTION_AND_MODIFICATION_CONDITIONS",
        "ingestion_permission": "BOUNDED_FIRST_PARTY_CALENDAR_METADATA_INTERNAL_MONITORING",
        "licence_review_status": "CLEARED_CREATIVE_COMMONS_STATISTICAL_CONTENT_MACHINE_ACCESS_SEPARATELY_GOVERNED",
        "automated_retrieval_permission": "BOUNDED_PUBLIC_UI_MONTH_ROUTES_ROBOTS_COMPATIBLE",
        "redistribution_permission": "MINIMAL_FACTUAL_METADATA_WITH_PRIMARY_SOURCE_ATTRIBUTION",
        "rights_evidence_url": s["rights_evidence_url"],
        "rights_summary": "INDEC dissemination policy generally permits copying and redistribution of website material subject to source attribution and modification notice conditions.",
        "automation_evidence_url": s["calendar_url"],
        "automation_summary": "Automation is limited to one robots check and the exact four first-party month routes already used by INDEC's public calendar UI; no search, PDF, result-page or Google follow-up.",
        "rights_reviewed_at": plan["reference_date"],
        "rights_review_scope": "BU_CONTENT_REUSE_ROBOTS_AND_FIRST_PARTY_MACHINE_ACCESS_SEPARATED",
        "rights_review_note": "Operational governance classification for WORLD SIGNALS; not a legal opinion.",
        "monitoring_readiness_status": "LIVE_VALIDATED_NO_AUTO_COMMIT",
        "monitoring_priority_score": 640,
        "canonical_dependency_count": 0,
        "monitoring_readiness_assessed_at": plan["reference_date"],
        "monitoring_activation_status": "LIVE_READ_ONLY_SCHEDULE_AND_CLOCK_SENTINEL_NO_AUTO_COMMIT",
        "last_successful_research_verification_at": plan["reference_date"],
        "canonical_provenance_use": "MONITOR_ONLY_INTERACTIVE_CALENDAR_NO_DIRECT_CANONICAL_WRITE_AUTHORITY",
        "automated_monitoring_use": "CLEARED",
        "verification_mode": "AUTOMATED_PILOT",
        "runtime_health_state": "READ_ONLY_DIAGNOSTICS_PASS_2026_09_08",
        "governance_backfill_reviewed_at": plan["reference_date"],
        "governance_backfill_basis": "Separate first-party interactive-calendar machine source created without mutating the existing PDF schedule or completed-release sources.",
        "live_adapter_id": ADAPTER_ID,
        "live_validation_evidence": {
            "robots_calendar_run_id": d["robots_and_calendar_surface"]["run_id"],
            "robots_calendar_job_id": d["robots_and_calendar_surface"]["job_id"],
            "september_route_run_id": d["september_one_shot"]["run_id"],
            "september_route_job_id": d["september_one_shot"]["job_id"],
            "entity_structure_run_id": d["entity_normalized_structure"]["run_id"],
            "entity_structure_job_id": d["entity_normalized_structure"]["job_id"],
            "google_followup_request_count": 0,
            "automatic_commit_allowed": False,
        },
        "related_source_ids": [CANONICAL_SOURCE_ID, COMPLETED_SOURCE_ID],
        "source_role_contract": deepcopy(plan["source_role_contract"]),
        "monitor_endpoints": [
            {
                "endpoint_role": "robots_policy",
                "url": s["robots_url"],
                "transport": "TEXT_PLAIN",
                "preferred_for_monitoring": True,
                "completeness_scope": "AUTOMATION_POLICY_GATE"
            },
            {
                "endpoint_role": "indec_interactive_calendar_month_routes",
                "url": s["month_route_template"],
                "transport": "HTML_FRAGMENT_GET",
                "preferred_for_monitoring": True,
                "completeness_scope": "EXACT_FOUR_REVIEWED_2026_MONTH_ROUTES_ONLY"
            }
        ]
    }


def monitor_expectation(plan: dict) -> dict:
    identity = {
        row["occurrence_id"]: {
            "reference_period_es": row["reference_period_es"],
            "canonical_release_date": row["canonical_release_date"],
            "authoritative_calendar_time": row["authoritative_calendar_time"],
            "month_slug": row["month_slug"],
        }
        for row in plan["canonical_occurrences"]
    }
    return {
        "adapter_id": ADAPTER_ID,
        "source_id": MACHINE_SOURCE_ID,
        "canonical_schedule_source_id": CANONICAL_SOURCE_ID,
        "completed_release_source_id": COMPLETED_SOURCE_ID,
        "canonical_occurrence_ids": list(plan["canonical_occurrence_ids"]),
        "identity_by_occurrence_id": identity,
        "monitor_role": "OFFICIAL_INDEC_CPI_INTERACTIVE_CALENDAR_SCHEDULE_AND_CLOCK_SENTINEL",
        "cadence": "DAILY",
        "request_budget_per_run": 5,
        "robots_requests_per_run": 1,
        "maximum_month_route_requests_per_run": 4,
        "month_slugs": list(plan["request_contract"]["month_slugs"]),
        "classification_contract": deepcopy(plan["classification_contract"]),
        "source_role_contract": deepcopy(plan["source_role_contract"]),
        "source_failure_policy": "SOURCE_HEALTH_ONLY_NO_EVENT_MUTATION",
        "positive_change_policy": "GENERATE_REVIEW_CANDIDATES_ONLY_FOR_EXACT_CONFIGURED_REFERENCE_PERIOD_IDENTITIES",
        "absence_policy": "MISSING_CONFIGURED_REPORT_IS_REVIEW_EVIDENCE_ONLY_NO_EVENT_STATE_INFERENCE",
        "schedule_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "canonical_clock_mutation_allowed": False,
        "automatic_pdf_fetch_allowed": False,
        "automatic_completed_release_fetch_allowed": False,
        "automatic_google_fetch_allowed": False,
        "automatic_search_route_discovery_allowed": False,
        "live_intelligence_policy": "NO_AUTOMATIC_PROMOTION_TO_LIVE_INTELLIGENCE_OR_ANALYSIS",
        "automatic_commit_allowed": False,
    }


def transform_sources(sources: dict, plan: dict, schedule_before: dict, completed_before: dict) -> dict:
    out = deepcopy(sources)
    if source_by_id(out, CANONICAL_SOURCE_ID) != schedule_before:
        raise RuntimeError("BU INDEC schedule source changed before transformation")
    if source_by_id(out, COMPLETED_SOURCE_ID) != completed_before:
        raise RuntimeError("BU INDEC completed-release source changed before transformation")
    out["sources"].append(new_machine_source(plan))
    if source_by_id(out, CANONICAL_SOURCE_ID) != schedule_before:
        raise RuntimeError("BU changed INDEC Canonical schedule source")
    if source_by_id(out, COMPLETED_SOURCE_ID) != completed_before:
        raise RuntimeError("BU changed INDEC completed-release source")
    out["version"] = plan["postconditions"]["source_registry_version"]
    out["reference_date"] = plan["reference_date"]
    return out


def transform_expectations(expectations: dict, plan: dict) -> dict:
    out = deepcopy(expectations)
    before = deepcopy(out.get("adapters", []))
    out["adapters"].append(monitor_expectation(plan))
    if out["adapters"][:-1] != before:
        raise RuntimeError("BU changed an existing monitor route")
    out["version"] = plan["postconditions"]["monitor_expectations_version"]
    if out.get("automatic_canonical_commit") is not False or out.get("google_calendar_write") is not False:
        raise RuntimeError("BU changed global write gates")
    return out


def patch_adapter_init(text: str) -> str:
    if "INDEC_MONTH_ROUTE_TEMPLATE" in text:
        raise RuntimeError("INDEC calendar adapter already exported")
    import_anchor = "from .japan_statistics_dashboard import (\n"
    block = '''from .indec_calendar import (\n    INDEC_ACCEPT,\n    INDEC_CALENDAR_URL,\n    INDEC_MONTH_ROUTE_TEMPLATE,\n    INDEC_ROBOTS_URL,\n    INDEC_TIMEZONE,\n    INDECCPIRelease,\n    fetch_indec_cpi_month,\n    fetch_indec_cpi_months,\n    fetch_indec_robots_policy,\n    indec_routes_allowed,\n    month_route_url,\n    parse_indec_cpi_month,\n)\n'''
    if import_anchor not in text:
        raise RuntimeError("BU adapter import anchor missing")
    text = text.replace(import_anchor, block + import_anchor, 1)
    all_anchor = '    "JAPAN_MOF_NEWS_RSS",\n'
    all_block = '''    "INDEC_ACCEPT",\n    "INDEC_CALENDAR_URL",\n    "INDEC_MONTH_ROUTE_TEMPLATE",\n    "INDEC_ROBOTS_URL",\n    "INDEC_TIMEZONE",\n    "INDECCPIRelease",\n'''
    if all_anchor not in text:
        raise RuntimeError("BU adapter __all__ anchor missing")
    text = text.replace(all_anchor, all_block + all_anchor, 1)
    fn_anchor = '    "fetch_japan_mof_news_rss",\n'
    fn_block = '''    "fetch_indec_cpi_month",\n    "fetch_indec_cpi_months",\n    "fetch_indec_robots_policy",\n    "indec_routes_allowed",\n    "month_route_url",\n    "parse_indec_cpi_month",\n'''
    if fn_anchor not in text:
        raise RuntimeError("BU adapter function export anchor missing")
    return text.replace(fn_anchor, fn_block + fn_anchor, 1)


def patch_live_runner(text: str) -> str:
    if 'if "INDEC_CPI_CALENDAR" in configs:' in text:
        raise RuntimeError("INDEC CPI live route already wired")
    import_anchor = "    fetch_japan_household_spending_data,\n"
    if import_anchor not in text:
        raise RuntimeError("BU live adapter import anchor missing")
    text = text.replace(
        import_anchor,
        "    fetch_indec_cpi_months,\n    fetch_indec_robots_policy,\n" + import_anchor,
        1,
    )
    monitor_anchor = "from world_signals.japan_mof_jgb_monitor import japan_mof_jgb_rss_review_candidates\n"
    if monitor_anchor not in text:
        raise RuntimeError("BU live monitor import anchor missing")
    text = text.replace(
        monitor_anchor,
        "from world_signals.indec_cpi_monitor import indec_cpi_calendar_review_candidates\n" + monitor_anchor,
        1,
    )
    route_anchor = '    if "CBN_MPC_CALENDAR" in configs:\n'
    block = '''    if "INDEC_CPI_CALENDAR" in configs:\n        indec_config=configs["INDEC_CPI_CALENDAR"]\n        try:\n            indec_slugs=list(indec_config["month_slugs"])\n            indec_allowed,indec_robots_snap=fetch_indec_robots_policy(indec_slugs)\n            if not indec_allowed:\n                report["source_health"].append({\n                    "adapter_id":"INDEC_CPI_CALENDAR",\n                    "source_id":indec_config["source_id"],\n                    "state":"DEGRADED",\n                    "robots_snapshot":indec_robots_snap.as_dict(),\n                    "failure_stage":"ROBOTS_POLICY_NOW_DISALLOWS_CONFIGURED_INDEC_MONTH_ROUTE",\n                    "month_route_requests_skipped":True,\n                    "canonical_action":"NONE",\n                    "automatic_commit_allowed":False,\n                })\n            else:\n                indec_items,indec_snaps=fetch_indec_cpi_months(indec_slugs)\n                report["source_health"].append({\n                    "adapter_id":"INDEC_CPI_CALENDAR",\n                    "source_id":indec_config["source_id"],\n                    "state":"HEALTHY",\n                    "robots_snapshot":indec_robots_snap.as_dict(),\n                    "month_route_snapshots":[snap.as_dict() for snap in indec_snaps],\n                    "item_count":len(indec_items),\n                    "request_budget_per_run":5,\n                    "robots_request_count":1,\n                    "month_route_request_count":len(indec_snaps),\n                    "google_followup_request_count":0,\n                    "pdf_followup_request_count":0,\n                    "completed_release_followup_request_count":0,\n                    "search_route_request_count":0,\n                    "schedule_authority":False,\n                    "lifecycle_authority":False,\n                    "certainty_authority":False,\n                    "canonical_clock_mutation_allowed":False,\n                    "automatic_commit_allowed":False,\n                })\n                candidates,observations=indec_cpi_calendar_review_candidates(\n                    registry.get("records",[]),indec_items,indec_config\n                )\n                report["review_candidates"].extend(candidates)\n                report["observations"].extend(observations)\n        except (AdapterError,ValueError) as exc:\n            report["source_health"].append({\n                "adapter_id":"INDEC_CPI_CALENDAR",\n                "source_id":indec_config["source_id"],\n                "state":"DEGRADED",\n                "error":str(exc),\n                "canonical_action":"NONE",\n                "absence_is_not_event_state":True,\n                "schedule_authority":False,\n                "lifecycle_authority":False,\n                "certainty_authority":False,\n                "canonical_clock_mutation_allowed":False,\n                "automatic_commit_allowed":False,\n            })\n\n'''
    if route_anchor not in text:
        raise RuntimeError("BU live route insertion anchor missing")
    return text.replace(route_anchor, block + route_anchor, 1)


def patch_smoke_runner(text: str) -> str:
    if '"adapter":"INDEC_CPI_CALENDAR"' in text:
        raise RuntimeError("INDEC CPI smoke route already wired")
    import_anchor = "    fetch_japan_household_spending_data,\n"
    if import_anchor not in text:
        raise RuntimeError("BU smoke import anchor missing")
    text = text.replace(
        import_anchor,
        "    fetch_indec_cpi_months,\n    fetch_indec_robots_policy,\n" + import_anchor,
        1,
    )
    route_anchor = "    try:\n        jgb_items,jgb_snap=fetch_japan_mof_news_rss()\n"
    block = '''    try:\n        indec_slugs=["Septiembre-2026","Octubre-2026","Noviembre-2026","Diciembre-2026"]\n        indec_allowed,indec_robots_snap=fetch_indec_robots_policy(indec_slugs)\n        if not indec_allowed:\n            raise AdapterError("INDEC robots policy disallows a configured CPI month route")\n        indec_items,indec_snaps=fetch_indec_cpi_months(indec_slugs)\n        report["results"].append({\n            "adapter":"INDEC_CPI_CALENDAR",\n            "status":"PASS",\n            "source_id":"WSSRC-REG2-009",\n            "robots_snapshot":indec_robots_snap.as_dict(),\n            "month_route_snapshots":[snap.as_dict() for snap in indec_snaps],\n            "item_count":len(indec_items),\n            "request_budget_per_run":5,\n            "robots_request_count":1,\n            "month_route_request_count":len(indec_snaps),\n            "google_followup_request_count":0,\n            "pdf_followup_request_count":0,\n            "completed_release_followup_request_count":0,\n            "search_route_request_count":0,\n            "schedule_authority":False,\n            "canonical_clock_mutation_allowed":False,\n            "automatic_commit_allowed":False,\n        })\n    except (AdapterError,ValueError) as exc:\n        failures.append({"adapter":"INDEC_CPI_CALENDAR","error":str(exc)})\n\n'''
    if route_anchor not in text:
        raise RuntimeError("BU smoke route insertion anchor missing")
    return text.replace(route_anchor, block + route_anchor, 1)


def build_post_state(
    canonical: dict,
    sources: dict,
    expectations: dict,
    plan: dict,
) -> tuple[dict, dict, str, str, str]:
    schedule_before, completed_before = preflight(canonical, sources, expectations, plan)
    post_sources = transform_sources(sources, plan, schedule_before, completed_before)
    post_expectations = transform_expectations(expectations, plan)
    live = patch_live_runner(LIVE_RUNNER_PATH.read_text(encoding="utf-8"))
    smoke = patch_smoke_runner(SMOKE_RUNNER_PATH.read_text(encoding="utf-8"))
    adapter_init = patch_adapter_init(ADAPTER_INIT_PATH.read_text(encoding="utf-8"))
    if source_by_id(post_sources, CANONICAL_SOURCE_ID) != schedule_before:
        raise RuntimeError("BU post-state mutated INDEC schedule source")
    if source_by_id(post_sources, COMPLETED_SOURCE_ID) != completed_before:
        raise RuntimeError("BU post-state mutated INDEC completed-release source")
    if (post_sources.get("version"), len(post_sources.get("sources", []))) != ("1.94", 252):
        raise RuntimeError("BU source post-state mismatch")
    if (post_expectations.get("version"), len(post_expectations.get("adapters", []))) != ("0.19", 17):
        raise RuntimeError("BU monitor post-state mismatch")
    return post_sources, post_expectations, live, smoke, adapter_init


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    plan = load_json(PLAN_PATH)
    canonical = load_json(CANONICAL_PATH)
    sources = load_json(SOURCES_PATH)
    expectations = load_json(EXPECTATIONS_PATH)
    post_sources, post_expectations, live, smoke, adapter_init = build_post_state(
        canonical, sources, expectations, plan
    )
    if not args.apply:
        print("BU CHECK-ONLY PASS: INDEC CPI calendar transaction is valid; no files written.")
        return 0
    if os.getenv(APPLY_ENV) != "1":
        raise RuntimeError(f"--apply requires {APPLY_ENV}=1")
    dump_json(SOURCES_PATH, post_sources)
    dump_json(EXPECTATIONS_PATH, post_expectations)
    LIVE_RUNNER_PATH.write_text(live, encoding="utf-8")
    SMOKE_RUNNER_PATH.write_text(smoke, encoding="utf-8")
    ADAPTER_INIT_PATH.write_text(adapter_init, encoding="utf-8")
    print("BU APPLY PASS: bounded INDEC CPI calendar source/route materialised; prior INDEC provenance sources preserved unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
