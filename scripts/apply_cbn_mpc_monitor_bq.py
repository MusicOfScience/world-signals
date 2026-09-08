from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/monitor/CBN_MPC_MONITOR_BQ_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
LIVE_RUNNER_PATH = ROOT / "scripts/run_live_monitor.py"
SMOKE_RUNNER_PATH = ROOT / "scripts/run_adapter_smoke.py"
ADAPTER_INIT_PATH = ROOT / "src/world_signals/adapters/__init__.py"

APPLY_ENV = "WORLD_SIGNALS_APPLY_MONITOR_BQ"
SOURCE_ID = "WSSRC-CB-014"
ADAPTER_ID = "CBN_MPC_CALENDAR"
BASE_SHA = "65e9ceb07d0c5175db61f9251a730a9bcf563d04"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def source_by_id(data: dict, source_id: str) -> dict:
    rows = [row for row in data.get("sources", []) if row.get("source_id") == source_id]
    if len(rows) != 1:
        raise RuntimeError(f"expected exactly one source {source_id}, found {len(rows)}")
    return rows[0]


def preflight(canonical: dict, sources: dict, expectations: dict, plan: dict) -> None:
    p = plan["preconditions"]
    if plan.get("exact_base_main_sha") != BASE_SHA:
        raise RuntimeError("BQ plan is not frozen to the exact post-BP main SHA")
    if (canonical.get("version"), len(canonical.get("records", []))) != (
        p["canonical_registry_version"], p["canonical_record_count"]
    ):
        raise RuntimeError("BQ requires exact Canonical v0.41 / 689")
    if (sources.get("version"), len(sources.get("sources", []))) != (
        p["source_registry_version"], p["source_count"]
    ):
        raise RuntimeError("BQ requires exact Sources v1.89 / 248")
    if (expectations.get("version"), len(expectations.get("adapters", []))) != (
        p["monitor_expectations_version"], p["configured_monitor_adapter_count"]
    ):
        raise RuntimeError("BQ requires exact Monitor v0.14 / 12")
    if expectations.get("automatic_canonical_commit") is not False:
        raise RuntimeError("automatic Canonical commit gate must remain closed")
    if expectations.get("google_calendar_write") is not False:
        raise RuntimeError("Google Calendar write gate must remain closed")
    if any(row.get("adapter_id") == ADAPTER_ID for row in expectations.get("adapters", [])):
        raise RuntimeError("BQ CBN MPC route already exists")

    source = source_by_id(sources, SOURCE_ID)
    expected_source = {
        "canonical_dependency_count": 2,
        "canonical_provenance_use": "CLEARED_CURATED_FACTUAL_METADATA",
        "automated_monitoring_use": "ENDPOINT_REVIEW_REQUIRED",
        "automated_retrieval_permission": "PENDING_ENDPOINT_OPERATIONAL_REVIEW",
        "verification_mode": "MANUAL_AUTHORITATIVE_RECHECK",
        "source_timezone": "Africa/Lagos",
        "parser_type": "MANUAL_HTML_PROVENANCE",
    }
    for key, expected in expected_source.items():
        if source.get(key) != expected:
            raise RuntimeError(f"BQ CBN source pre-state drift for {key}: {source.get(key)!r}")

    tracked = list(plan["tracked_occurrences"])
    ids = [row["occurrence_id"] for row in tracked]
    if len(ids) != 2 or len(set(ids)) != 2:
        raise RuntimeError("BQ requires exactly two unique tracked CBN occurrences")
    by_id = {row.get("occurrence_id"): row for row in canonical.get("records", []) if row.get("occurrence_id") in set(ids)}
    if set(by_id) != set(ids):
        raise RuntimeError("BQ tracked CBN occurrence scope no longer matches Canonical")
    for expected in tracked:
        row = by_id[expected["occurrence_id"]]
        checks = {
            "series_id": "WSER-CB-NG-CBN-MPC",
            "source_id": SOURCE_ID,
            "region": "Africa",
            "source_timezone": expected["source_timezone"],
            "time_precision": expected["time_precision"],
            "timing_type": "MULTI_DAY_LOCAL",
            "start_local": expected["start_local"],
            "end_local": expected["end_local"],
            "lifecycle_status": "PLANNED",
        }
        for key, value in checks.items():
            if row.get(key) != value:
                raise RuntimeError(f"BQ Canonical drift for {expected['occurrence_id']} {key}: {row.get(key)!r}")
        if row.get("start_utc") is not None or row.get("end_utc") is not None:
            raise RuntimeError(f"BQ must preserve date-range/no-UTC semantics for {expected['occurrence_id']}")


def transform_sources(sources: dict, plan: dict) -> dict:
    out = deepcopy(sources)
    source = source_by_id(out, SOURCE_ID)
    target = plan["source_governance_target"]
    source.update({
        "activation_status": "ACTIVE_GUARDED",
        "automated_monitoring_use": target["automated_monitoring_use"],
        "automated_retrieval_permission": target["automated_retrieval_permission"],
        "verification_mode": target["verification_mode"],
        "monitoring_readiness_status": target["monitoring_readiness_status"],
        "monitoring_activation_status": target["monitoring_activation_status"],
        "runtime_health_state": target["runtime_health_state"],
        "parser_type": target["parser_type"],
        "parser_version": target["parser_version"],
        "recommended_verification_cadence": "daily while a tracked future 2026 MPC occurrence remains",
        "monitoring_readiness_assessed_at": plan["review_date"],
        "last_successful_research_verification_at": plan["review_date"],
        "rights_reviewed_at": plan["review_date"],
        "live_adapter_id": ADAPTER_ID,
        "automation_summary": (
            "Bounded automated retrieval is cleared only for a robots-first check followed by one official MPC calendar request when allowed. "
            "CBN copy/reuse conditions remain attribution and no distortion; robots is treated separately as an operational access control."
        ),
        "notes": (
            "Curated factual Canonical provenance remains unchanged. BQ activates only a bounded review-only schedule monitor; "
            "meeting windows do not imply a decision publication clock or lifecycle state."
        ),
        "live_validation_evidence": {
            "read_only_diagnostic_run_id": plan["read_only_diagnostic"]["run_id"],
            "read_only_diagnostic_job_id": plan["read_only_diagnostic"]["job_id"],
            "robots_http_status": plan["read_only_diagnostic"]["robots_http_status"],
            "calendar_http_status": plan["read_only_diagnostic"]["calendar_http_status"],
            "legal_http_status": plan["read_only_diagnostic"]["legal_http_status"],
            "robots_allows_calendar": plan["read_only_diagnostic"]["robots_allows_calendar"],
            "calendar_sha256": plan["read_only_diagnostic"]["calendar_sha256"],
            "automatic_commit_allowed": False,
        },
        "monitor_endpoints": [
            {
                "endpoint_role": "robots_operational_policy",
                "url": plan["official_interfaces"]["robots_url"],
                "preferred_for_monitoring": True,
                "request_order": 1,
            },
            {
                "endpoint_role": "2026_mpc_meeting_calendar",
                "url": plan["official_interfaces"]["calendar_url"],
                "preferred_for_monitoring": True,
                "request_order": 2,
                "request_condition": "ONLY_IF_ROBOTS_ALLOWS_CALENDAR_PATH",
            },
        ],
    })
    if source.get("canonical_provenance_use") != "CLEARED_CURATED_FACTUAL_METADATA":
        raise RuntimeError("BQ changed CBN Canonical provenance role")
    if source.get("canonical_dependency_count") != 2:
        raise RuntimeError("BQ changed CBN Canonical dependency count")
    out["version"] = plan["postconditions"]["source_registry_version"]
    out["reference_date"] = plan["review_date"]
    return out


def monitor_expectation(plan: dict) -> dict:
    route = plan["monitor_route"]
    tracked = plan["tracked_occurrences"]
    return {
        "adapter_id": ADAPTER_ID,
        "source_id": SOURCE_ID,
        "canonical_occurrence_ids": [row["occurrence_id"] for row in tracked],
        "meeting_number_by_occurrence_id": {row["occurrence_id"]: row["meeting_number"] for row in tracked},
        "monitor_role": "OFFICIAL_CBN_MPC_MEETING_WINDOW_SCHEDULE_SENTINEL",
        "cadence": route["cadence"],
        "request_budget_per_run": route["request_budget_per_run"],
        "request_order": deepcopy(route["request_order"]),
        "robots_policy": route["robots_policy"],
        "scope_policy": route["scope_policy"],
        "matching": deepcopy(route["matching"]),
        "source_failure_policy": "SOURCE_HEALTH_ONLY_NO_EVENT_MUTATION",
        "date_drift_policy": route["date_drift_policy"],
        "absence_policy": route["absence_policy"],
        "untracked_future_policy": route["untracked_future_policy"],
        "elapsed_policy": route["elapsed_policy"],
        "decision_time_policy": route["decision_time_policy"],
        "schedule_authority": True,
        "decision_publication_time_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "live_intelligence_policy": "NO_AUTOMATIC_PROMOTION_TO_LIVE_INTELLIGENCE_OR_ANALYSIS",
        "automatic_commit_allowed": False,
    }


def transform_expectations(expectations: dict, plan: dict) -> dict:
    out = deepcopy(expectations)
    out["adapters"].append(monitor_expectation(plan))
    out["version"] = plan["postconditions"]["monitor_expectations_version"]
    if out.get("automatic_canonical_commit") is not False or out.get("google_calendar_write") is not False:
        raise RuntimeError("BQ changed global write gates")
    return out


def patch_adapter_init(text: str) -> str:
    if "CBN_MPC_CALENDAR_URL" in text:
        raise RuntimeError("CBN MPC adapter already exported")
    import_anchor = "from .cellar import (\n"
    block = '''from .cbn_mpc import (\n    CBN_MPC_ACCEPT,\n    CBN_MPC_CALENDAR_URL,\n    CBN_MPC_TIMEZONE,\n    CBNMPCCalendar,\n    CBNMPCMeeting,\n    fetch_cbn_mpc_calendar,\n    parse_cbn_mpc_calendar_html,\n)\n'''
    if import_anchor not in text:
        raise RuntimeError("CBN MPC adapter import anchor missing")
    text = text.replace(import_anchor, block + import_anchor, 1)
    all_anchor = '    "CELLAR_CELEX_BASE",\n'
    all_block = '''    "CBN_MPC_ACCEPT",\n    "CBN_MPC_CALENDAR_URL",\n    "CBN_MPC_TIMEZONE",\n    "CBNMPCCalendar",\n    "CBNMPCMeeting",\n'''
    if all_anchor not in text:
        raise RuntimeError("CBN MPC __all__ anchor missing")
    text = text.replace(all_anchor, all_block + all_anchor, 1)
    fetch_anchor = '    "fetch_cbam_annual_declaration_surrender_rule",\n'
    fetch_block = '''    "fetch_cbn_mpc_calendar",\n    "parse_cbn_mpc_calendar_html",\n'''
    if fetch_anchor not in text:
        raise RuntimeError("CBN MPC __all__ function anchor missing")
    return text.replace(fetch_anchor, fetch_block + fetch_anchor, 1)


def patch_live_runner(text: str) -> str:
    if 'if "CBN_MPC_CALENDAR" in configs:' in text:
        raise RuntimeError("CBN MPC live route already wired")
    import_anchor = "    fetch_cbam_annual_declaration_surrender_rule,\n"
    if import_anchor not in text:
        raise RuntimeError("CBN live adapter import anchor missing")
    text = text.replace(import_anchor, import_anchor + "    fetch_cbn_mpc_calendar,\n", 1)
    monitor_anchor = "from world_signals.eurostat_monitor import eurostat_release_calendar_review_candidates\n"
    monitor_import = "from world_signals.cbn_mpc_monitor import fetch_cbn_robots_policy, cbn_mpc_schedule_review_candidates\n"
    if monitor_anchor not in text:
        raise RuntimeError("CBN monitor import anchor missing")
    text = text.replace(monitor_anchor, monitor_import + monitor_anchor, 1)
    route_anchor = '    if "FED_MONETARY_POLICY_RSS" in configs:\n'
    block = '''    if "CBN_MPC_CALENDAR" in configs:\n        cbn_config=configs["CBN_MPC_CALENDAR"]\n        try:\n            cbn_allowed,cbn_robots_snap=fetch_cbn_robots_policy()\n            if not cbn_allowed:\n                report["source_health"].append({\n                    "adapter_id":"CBN_MPC_CALENDAR",\n                    "source_id":cbn_config["source_id"],\n                    "state":"DEGRADED",\n                    "robots_snapshot":cbn_robots_snap.as_dict(),\n                    "failure_stage":"ROBOTS_POLICY_NOW_DISALLOWS_CBN_MPC_CALENDAR",\n                    "calendar_request_skipped":True,\n                    "canonical_action":"NONE",\n                })\n            else:\n                cbn_calendar,cbn_calendar_snap=fetch_cbn_mpc_calendar()\n                report["source_health"].append({\n                    "adapter_id":"CBN_MPC_CALENDAR",\n                    "source_id":cbn_config["source_id"],\n                    "state":"HEALTHY",\n                    "robots_snapshot":cbn_robots_snap.as_dict(),\n                    "calendar_snapshot":cbn_calendar_snap.as_dict(),\n                    "meeting_count":len(cbn_calendar.meetings),\n                    "schedule_sha256":cbn_calendar.schedule_sha256,\n                    "request_budget_per_run":2,\n                    "decision_publication_time_authority":False,\n                    "lifecycle_authority":False,\n                    "automatic_commit_allowed":False,\n                })\n                candidates,observations=cbn_mpc_schedule_review_candidates(\n                    registry.get("records",[]),cbn_calendar,cbn_config\n                )\n                report["review_candidates"].extend(candidates)\n                report["observations"].extend(observations)\n        except (AdapterError,ValueError) as exc:\n            report["source_health"].append({\n                "adapter_id":"CBN_MPC_CALENDAR",\n                "source_id":cbn_config["source_id"],\n                "state":"DEGRADED",\n                "error":str(exc),\n                "canonical_action":"NONE",\n                "absence_is_not_event_state":True,\n                "decision_publication_time_inference":"PROHIBITED",\n            })\n\n'''
    if route_anchor not in text:
        raise RuntimeError("CBN live route insertion anchor missing")
    return text.replace(route_anchor, block + route_anchor, 1)


def patch_smoke_runner(text: str) -> str:
    if '"adapter":"CBN_MPC_CALENDAR"' in text:
        raise RuntimeError("CBN MPC smoke route already wired")
    import_anchor = "    fetch_cbam_certificate_sale_rule,\n"
    if import_anchor not in text:
        raise RuntimeError("CBN smoke import anchor missing")
    text = text.replace(import_anchor, import_anchor + "    fetch_cbn_mpc_calendar,\n", 1)
    monitor_anchor = "from world_signals.rba_mpb_monitor import fetch_rba_robots_policy, rba_schedule_path_disallowed\n"
    monitor_import = "from world_signals.cbn_mpc_monitor import fetch_cbn_robots_policy\n"
    if monitor_anchor not in text:
        raise RuntimeError("CBN smoke monitor anchor missing")
    text = text.replace(monitor_anchor, monitor_import + monitor_anchor, 1)
    route_anchor = "    try:\n        fed_items,fed_snap=fetch_fed_monetary_policy_rss()\n"
    block = '''    try:\n        cbn_allowed,cbn_robots_snap=fetch_cbn_robots_policy()\n        if not cbn_allowed:\n            raise AdapterError("CBN robots policy disallows the MPC calendar path")\n        cbn_calendar,cbn_calendar_snap=fetch_cbn_mpc_calendar()\n        report["results"].append({\n            "adapter":"CBN_MPC_CALENDAR",\n            "status":"PASS",\n            "source_id":"WSSRC-CB-014",\n            "robots_snapshot":cbn_robots_snap.as_dict(),\n            "calendar_snapshot":cbn_calendar_snap.as_dict(),\n            "meeting_count":len(cbn_calendar.meetings),\n            "schedule_sha256":cbn_calendar.schedule_sha256,\n            "request_budget_per_run":2,\n            "decision_publication_time_authority":False,\n            "automatic_commit_allowed":False,\n        })\n    except AdapterError as exc:\n        failures.append(str(exc))\n        report["results"].append({\n            "adapter":"CBN_MPC_CALENDAR",\n            "status":"FAIL",\n            "source_id":"WSSRC-CB-014",\n            "error":str(exc),\n            "canonical_action":"NONE",\n        })\n\n'''
    if route_anchor not in text:
        raise RuntimeError("CBN smoke route insertion anchor missing")
    return text.replace(route_anchor, block + route_anchor, 1)


def build_post_state() -> tuple[dict, dict, str, str, str]:
    canonical = load_json(CANONICAL_PATH)
    sources = load_json(SOURCES_PATH)
    expectations = load_json(EXPECTATIONS_PATH)
    plan = load_json(PLAN_PATH)
    preflight(canonical, sources, expectations, plan)
    return (
        transform_sources(sources, plan),
        transform_expectations(expectations, plan),
        patch_live_runner(LIVE_RUNNER_PATH.read_text(encoding="utf-8")),
        patch_smoke_runner(SMOKE_RUNNER_PATH.read_text(encoding="utf-8")),
        patch_adapter_init(ADAPTER_INIT_PATH.read_text(encoding="utf-8")),
    )


def apply() -> None:
    if os.getenv(APPLY_ENV) != "1":
        raise RuntimeError(f"BQ APPLY REFUSED: set {APPLY_ENV}=1")
    sources, expectations, live, smoke, adapter_init = build_post_state()
    dump_json(SOURCES_PATH, sources)
    dump_json(EXPECTATIONS_PATH, expectations)
    LIVE_RUNNER_PATH.write_text(live, encoding="utf-8")
    SMOKE_RUNNER_PATH.write_text(smoke, encoding="utf-8")
    ADAPTER_INIT_PATH.write_text(adapter_init, encoding="utf-8")
    print("BQ CBN MPC activation transaction applied")


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply/check WORLD SIGNALS BQ CBN MPC monitor activation")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    build_post_state()
    if args.apply:
        apply()
    else:
        print("BQ CBN MPC activation check-only PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
