from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/monitor/RBA_MPB_MONITOR_ACTIVATION_BO_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
LIVE_RUNNER_PATH = ROOT / "scripts/run_live_monitor.py"
SMOKE_RUNNER_PATH = ROOT / "scripts/run_adapter_smoke.py"

APPLY_ENV = "WORLD_SIGNALS_APPLY_MONITOR_BO"
SOURCE_ID = "WSSRC-CB-002"
MINUTES_SOURCE_ID = "WSSRC-CB-013"
ADAPTER_ID = "RBA_MPB_CALENDAR"


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
    if plan.get("exact_base_main_sha") != "3a6869a054372e5df135067df77fb9bdc772367e":
        raise RuntimeError("BO plan is not frozen to the exact post-BN main SHA")
    if (canonical.get("version"), len(canonical.get("records", []))) != (
        p["canonical_registry_version"], p["canonical_record_count"]
    ):
        raise RuntimeError("BO requires exact Canonical v0.41 / 689")
    if (sources.get("version"), len(sources.get("sources", []))) != (
        p["source_registry_version"], p["source_count"]
    ):
        raise RuntimeError("BO requires exact Sources v1.87 / 247")
    if (expectations.get("version"), len(expectations.get("adapters", []))) != (
        p["monitor_expectations_version"], p["configured_monitor_adapter_count"]
    ):
        raise RuntimeError("BO requires exact Monitor v0.12 / 10")
    if expectations.get("automatic_canonical_commit") is not False:
        raise RuntimeError("automatic Canonical commit gate must remain closed")
    if expectations.get("google_calendar_write") is not False:
        raise RuntimeError("Google Calendar write gate must remain closed")
    if any(row.get("adapter_id") == ADAPTER_ID for row in expectations.get("adapters", [])):
        raise RuntimeError("RBA MPB production monitor route already exists")

    source = source_by_id(sources, SOURCE_ID)
    required = {
        "source_timezone": "Australia/Sydney",
        "parser_version": "rba-calendar-0.1",
        "canonical_provenance_use": "CLEARED_CURATED_FACTUAL_METADATA",
        "automated_monitoring_use": "ENDPOINT_REVIEW_REQUIRED",
        "verification_mode": "AUTOMATED_PILOT",
        "automated_retrieval_permission": "PENDING_ENDPOINT_OPERATIONAL_REVIEW",
        "monitoring_readiness_status": "PILOT_RESEARCH_VALIDATED_AUTOMATION_RIGHTS_PENDING",
        "monitoring_activation_status": "PILOT_ONLY_NO_AUTO_COMMIT",
    }
    for key, expected in required.items():
        if source.get(key) != expected:
            raise RuntimeError(f"unexpected {SOURCE_ID} pre-state {key}: {source.get(key)!r} != {expected!r}")
    if source.get("canonical_dependency_count") != 33:
        raise RuntimeError("RBA schedule source dependency count must remain 33")

    minutes_source = deepcopy(source_by_id(sources, MINUTES_SOURCE_ID))
    ids = list(plan["canonical_occurrence_ids"])
    if len(ids) != 44 or len(set(ids)) != 44:
        raise RuntimeError("BO requires the exact unique 44-occurrence RBA MPB family allow-list")
    rows = [r for r in canonical.get("records", []) if r.get("occurrence_id") in set(ids)]
    if len(rows) != 44 or {r.get("occurrence_id") for r in rows} != set(ids):
        raise RuntimeError("BO RBA MPB allow-list no longer matches Canonical")
    contract = plan["canonical_source_role_contract"]
    counts = {SOURCE_ID: 0, MINUTES_SOURCE_ID: 0}
    series_counts: dict[str, int] = {}
    for row in rows:
        series = row.get("series_id")
        expected_source = contract.get(series)
        if expected_source is None or row.get("source_id") != expected_source:
            raise RuntimeError(f"RBA MPB source-role drift for {row.get('occurrence_id')}")
        if row.get("source_timezone") != "Australia/Sydney":
            raise RuntimeError(f"RBA MPB timezone drift for {row.get('occurrence_id')}")
        counts[row["source_id"]] += 1
        series_counts[series] = series_counts.get(series, 0) + 1
    if counts != {SOURCE_ID: 33, MINUTES_SOURCE_ID: 11}:
        raise RuntimeError(f"RBA MPB source-role counts drifted: {counts}")
    if set(series_counts.values()) != {11} or len(series_counts) != 4:
        raise RuntimeError(f"RBA MPB series counts drifted: {series_counts}")
    if source_by_id(sources, MINUTES_SOURCE_ID) != minutes_source:
        raise RuntimeError("minutes source preflight mutated unexpectedly")


def transform_sources(sources: dict, plan: dict) -> dict:
    out = deepcopy(sources)
    target = source_by_id(out, SOURCE_ID)
    target["automated_retrieval_permission"] = "CLEARED_BOUNDED_ROBOTS_CONFORMANT_LOW_RATE_SCHEDULE_PATHS"
    target["automated_monitoring_use"] = "CLEARED"
    target["runtime_health_state"] = "LIVE_GITHUB_ACTIONS_DUAL_SCHEDULE_AND_ROBOTS_PASS_2026_09_08"
    target["monitoring_readiness_status"] = "LIVE_VALIDATED_ROBOTS_CONFORMANT_NO_AUTO_COMMIT"
    target["monitoring_activation_status"] = "LIVE_READ_ONLY_REVIEW_MONITOR_NO_AUTO_COMMIT"
    target["monitoring_readiness_assessed_at"] = "2026-09-08"
    target["live_adapter_id"] = ADAPTER_ID
    target["automation_summary"] = (
        "Production monitoring is bounded to one daily robots-policy check followed, only when /schedules-events/ remains compatible, "
        "by the reviewed MPB topic calendar and Board schedule. The operational clearance combines RBA's published crawler exclusions "
        "with the existing CC BY 4.0 general-content reuse review; it is not blanket permission to crawl RBA infrastructure. All schedule "
        "differences are review-only and cannot automatically change Canonical."
    )
    target["automated_monitoring_scope"] = {
        "cadence": "DAILY",
        "request_budget_per_run": 3,
        "robots_url": "https://www.rba.gov.au/robots.txt",
        "allowed_schedule_path_prefix": "/schedules-events/",
        "topic_calendar_url": "https://www.rba.gov.au/schedules-events/calendar/?topics=monetary-policy-board",
        "board_schedule_url": "https://www.rba.gov.au/schedules-events/board-meeting-schedules.html",
        "fail_closed_if_schedule_path_disallowed": True,
        "broad_crawling_allowed": False,
    }
    target["live_validation_evidence"] = {
        "read_only_diagnostic_run_id": plan["read_only_diagnostic"]["run_id"],
        "read_only_diagnostic_job_id": plan["read_only_diagnostic"]["job_id"],
        "observed_at": "2026-09-08",
        "calendar_http_status": 200,
        "board_http_status": 200,
        "robots_http_status": 200,
        "schedule_path_disallowed": False,
        "calendar_event_count": 31,
        "board_window_count": 16,
        "calendar_schedule_sha256": plan["read_only_diagnostic"]["calendar_schedule_sha256"],
        "automatic_commit_allowed": False,
    }
    limitations = list(target.get("known_limitations") or [])
    for item in [
        "robots.txt compatibility is operational crawler-policy evidence and not blanket legal permission; every live run rechecks it before schedule retrieval.",
        "The MPB topic calendar is rolling, so absence from the current page cannot imply cancellation, delay, completion or certainty change.",
        "The monitor may observe minutes on the MPB calendar but must preserve WSSRC-CB-013 as the Canonical source identity for the 11 tracked minutes occurrences.",
        "Meeting windows, decision statements, media conferences and minutes remain distinct event series; BO never derives decision timing from the final meeting day when explicit schedule entries exist.",
    ]:
        if item not in limitations:
            limitations.append(item)
    target["known_limitations"] = limitations
    out["version"] = plan["postconditions"]["source_registry_version"]
    out["reference_date"] = plan["review_date"]
    return out


def monitor_expectation(plan: dict) -> dict:
    return {
        "adapter_id": ADAPTER_ID,
        "source_id": SOURCE_ID,
        "canonical_occurrence_ids": list(plan["canonical_occurrence_ids"]),
        "canonical_source_role_contract": deepcopy(plan["canonical_source_role_contract"]),
        "monitor_role": "RBA_MPB_AUTHORITATIVE_SCHEDULE_CHANGE_SENTINEL",
        "cadence": "DAILY",
        "request_budget_per_run": 3,
        "request_sequence": [
            "RBA_ROBOTS_POLICY",
            "RBA_MPB_TOPIC_CALENDAR",
            "RBA_BOARD_SCHEDULE",
        ],
        "robots_policy": "FETCH_FIRST_FAIL_CLOSED_IF_SCHEDULE_PATH_DISALLOWED",
        "matching": {
            "method": "SERIES_KIND_PLUS_NEAREST_CIVIL_DATE_WITH_EXPLICIT_ALLOW_LIST",
            "nearest_occurrence_max_days": 14,
            "tie_policy": "NO_IDENTITY_GUESS",
        },
        "meeting_window_surface": "RBA_BOARD_SCHEDULE",
        "timed_event_surface": "RBA_MPB_TOPIC_CALENDAR",
        "topic_calendar_meeting_windows": "CROSS_VALIDATION_ONLY",
        "source_failure_policy": "SOURCE_HEALTH_ONLY_NO_EVENT_MUTATION",
        "absence_policy": "NO_CANCELLATION_DELAY_COMPLETION_OR_CERTAINTY_INFERENCE",
        "elapsed_time_policy": "NO_COMPLETION_INFERENCE",
        "source_role_policy": "PRESERVE_CANONICAL_SOURCE_ID_INCLUDING_WSSRC_CB_013_MINUTES",
        "precision_policy": "PRESERVE_SOURCE_NATIVE_AUSTRALIA_SYDNEY_AND_EXPLICIT_RBA_PRECISION",
        "event_separation_policy": "MEETING_WINDOW_DECISION_PRESS_CONFERENCE_AND_MINUTES_ARE_DISTINCT",
        "heuristic_policy": "DO_NOT_INFER_DECISION_FROM_LAST_MEETING_DAY_WHEN_EXPLICIT_SCHEDULE_EXISTS",
        "automatic_commit_allowed": False,
    }


def transform_expectations(expectations: dict, plan: dict) -> dict:
    out = deepcopy(expectations)
    out["adapters"].append(monitor_expectation(plan))
    out["version"] = plan["postconditions"]["monitor_expectations_version"]
    if out.get("automatic_canonical_commit") is not False or out.get("google_calendar_write") is not False:
        raise RuntimeError("BO changed global write gates")
    return out


def patch_live_runner(text: str) -> str:
    if 'if "RBA_MPB_CALENDAR" in configs:' in text:
        raise RuntimeError("RBA MPB live runner already wired")
    adapter_anchor = "    fetch_rba_fsr,\n"
    replacement = (
        "    fetch_rba_fsr,\n"
        "    fetch_rba_monetary_policy_calendar,\n"
        "    fetch_rba_board_schedule,\n"
        "    validate_rba_calendar_alignment,\n"
    )
    if adapter_anchor not in text:
        raise RuntimeError("RBA MPB live-runner adapter import anchor missing")
    text = text.replace(adapter_anchor, replacement, 1)
    module_anchor = "from world_signals.ons_monitor import ons_release_calendar_review_candidates\n"
    module_replacement = (
        module_anchor
        + "from world_signals.rba_mpb_monitor import (\n"
        + "    fetch_rba_robots_policy,\n"
        + "    rba_mpb_schedule_review_candidates,\n"
        + "    rba_schedule_path_disallowed,\n"
        + ")\n"
    )
    if module_anchor not in text:
        raise RuntimeError("RBA MPB live-runner monitor import anchor missing")
    text = text.replace(module_anchor, module_replacement, 1)
    insert_anchor = '    if "EIA_WPSR_SCHEDULE" in configs:\n'
    block = '''    if "RBA_MPB_CALENDAR" in configs:\n        rba_mpb_config=configs["RBA_MPB_CALENDAR"]\n        try:\n            robots_rules,robots_snap=fetch_rba_robots_policy()\n            if rba_schedule_path_disallowed(robots_rules):\n                report["source_health"].append({\n                    "adapter_id":"RBA_MPB_CALENDAR",\n                    "source_id":rba_mpb_config["source_id"],\n                    "state":"DEGRADED",\n                    "robots_snapshot":robots_snap.as_dict(),\n                    "failure_stage":"ROBOTS_POLICY_NOW_DISALLOWS_SCHEDULE_PATH",\n                    "schedule_requests_skipped":True,\n                    "canonical_action":"NONE",\n                })\n            else:\n                rba_calendar,rba_calendar_snap=fetch_rba_monetary_policy_calendar()\n                rba_board,rba_board_snap=fetch_rba_board_schedule()\n                validate_rba_calendar_alignment(rba_calendar,rba_board)\n                report["source_health"].append({\n                    "adapter_id":"RBA_MPB_CALENDAR",\n                    "source_id":rba_mpb_config["source_id"],\n                    "state":"HEALTHY",\n                    "robots_snapshot":robots_snap.as_dict(),\n                    "calendar_snapshot":rba_calendar_snap.as_dict(),\n                    "board_snapshot":rba_board_snap.as_dict(),\n                    "calendar_event_count":len(rba_calendar.events),\n                    "board_window_count":len(rba_board),\n                    "schedule_sha256":rba_calendar.schedule_sha256,\n                    "request_budget_per_run":3,\n                    "automatic_commit_allowed":False,\n                })\n                candidates,observations=rba_mpb_schedule_review_candidates(\n                    registry.get("records",[]),rba_calendar,rba_board,rba_mpb_config\n                )\n                report["review_candidates"].extend(candidates)\n                report["observations"].extend(observations)\n        except (AdapterError,ValueError) as exc:\n            report["source_health"].append({\n                "adapter_id":"RBA_MPB_CALENDAR",\n                "source_id":rba_mpb_config["source_id"],\n                "state":"DEGRADED",\n                "error":str(exc),\n                "canonical_action":"NONE",\n                "absence_is_not_event_state":True,\n            })\n\n'''
    if insert_anchor not in text:
        raise RuntimeError("RBA MPB live-runner insertion anchor missing")
    return text.replace(insert_anchor, block + insert_anchor, 1)


def patch_smoke_runner(text: str) -> str:
    if '"RBA_MPB_CALENDAR"' in text:
        raise RuntimeError("RBA MPB smoke runner already wired")
    adapter_anchor = "    fetch_rba_fsr,\n"
    replacement = (
        "    fetch_rba_fsr,\n"
        "    fetch_rba_monetary_policy_calendar,\n"
        "    fetch_rba_board_schedule,\n"
        "    validate_rba_calendar_alignment,\n"
    )
    if adapter_anchor not in text:
        raise RuntimeError("RBA MPB smoke-runner adapter import anchor missing")
    text = text.replace(adapter_anchor, replacement, 1)
    module_anchor = "from world_signals.adapters import (\n"
    # Add monitor helper import after the adapter import block by anchoring the CANONICAL declaration.
    import_end_anchor = "\nCANONICAL=ROOT/\"data/canonical/registry.json\"\n"
    helper_import = (
        "\nfrom world_signals.rba_mpb_monitor import fetch_rba_robots_policy, rba_schedule_path_disallowed\n"
        "\nCANONICAL=ROOT/\"data/canonical/registry.json\"\n"
    )
    if import_end_anchor not in text:
        raise RuntimeError("RBA MPB smoke-runner helper import anchor missing")
    text = text.replace(import_end_anchor, helper_import, 1)
    insert_anchor = "    try:\n        eurostat_items,eurostat_snap=fetch_eurostat_release_calendar()\n"
    block = '''    try:\n        robots_rules,robots_snap=fetch_rba_robots_policy()\n        if rba_schedule_path_disallowed(robots_rules):\n            raise AdapterError("RBA robots policy disallows /schedules-events/")\n        rba_calendar,rba_calendar_snap=fetch_rba_monetary_policy_calendar()\n        rba_board,rba_board_snap=fetch_rba_board_schedule()\n        validate_rba_calendar_alignment(rba_calendar,rba_board)\n        report["results"].append({\n            "adapter":"RBA_MPB_CALENDAR",\n            "status":"PASS",\n            "source_id":"WSSRC-CB-002",\n            "robots_snapshot":robots_snap.as_dict(),\n            "calendar_snapshot":rba_calendar_snap.as_dict(),\n            "board_snapshot":rba_board_snap.as_dict(),\n            "calendar_event_count":len(rba_calendar.events),\n            "board_window_count":len(rba_board),\n            "schedule_sha256":rba_calendar.schedule_sha256,\n            "request_budget_per_run":3,\n            "automatic_commit_allowed":False,\n        })\n    except AdapterError as exc:\n        failures.append(str(exc))\n        report["results"].append({\n            "adapter":"RBA_MPB_CALENDAR",\n            "status":"FAIL",\n            "source_id":"WSSRC-CB-002",\n            "error":str(exc),\n            "canonical_action":"NONE",\n        })\n\n'''
    if insert_anchor not in text:
        raise RuntimeError("RBA MPB smoke-runner insertion anchor missing")
    return text.replace(insert_anchor, block + insert_anchor, 1)


def build_post_state() -> tuple[dict, dict, str, str]:
    plan = load_json(PLAN_PATH)
    canonical = load_json(CANONICAL_PATH)
    sources = load_json(SOURCES_PATH)
    expectations = load_json(EXPECTATIONS_PATH)
    preflight(canonical, sources, expectations, plan)
    new_sources = transform_sources(sources, plan)
    new_expectations = transform_expectations(expectations, plan)
    new_live = patch_live_runner(LIVE_RUNNER_PATH.read_text(encoding="utf-8"))
    new_smoke = patch_smoke_runner(SMOKE_RUNNER_PATH.read_text(encoding="utf-8"))

    before = {row["source_id"]: row for row in sources["sources"]}
    after = {row["source_id"]: row for row in new_sources["sources"]}
    if set(before) != set(after):
        raise RuntimeError("BO must not add/remove source identities")
    changed_sources = [sid for sid in before if before[sid] != after[sid]]
    if changed_sources != [SOURCE_ID]:
        raise RuntimeError(f"BO must change exactly {SOURCE_ID}; changed={changed_sources}")
    if before[MINUTES_SOURCE_ID] != after[MINUTES_SOURCE_ID]:
        raise RuntimeError("BO must preserve the minutes source row byte-semantically")
    if len(new_sources["sources"]) != 247:
        raise RuntimeError("BO must not change source population")
    if len(new_expectations["adapters"]) != 11:
        raise RuntimeError("BO must produce exactly 11 configured monitor routes")
    if new_expectations["adapters"][:10] != expectations["adapters"]:
        raise RuntimeError("BO must preserve the ten existing monitor routes semantically")
    route = new_expectations["adapters"][10]
    if route.get("adapter_id") != ADAPTER_ID or route.get("automatic_commit_allowed") is not False:
        raise RuntimeError("BO appended route contract invalid")
    return new_sources, new_expectations, new_live, new_smoke


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply BO RBA MPB bounded read-only monitor activation")
    parser.add_argument("--apply", action="store_true", help="materialise the bounded post-state")
    args = parser.parse_args()
    new_sources, new_expectations, new_live, new_smoke = build_post_state()
    if not args.apply:
        print("BO RBA MPB activation check-only PASS")
        return 0
    if os.environ.get(APPLY_ENV) != "1":
        raise RuntimeError(f"refusing write without {APPLY_ENV}=1")
    dump_json(SOURCES_PATH, new_sources)
    dump_json(EXPECTATIONS_PATH, new_expectations)
    LIVE_RUNNER_PATH.write_text(new_live, encoding="utf-8")
    SMOKE_RUNNER_PATH.write_text(new_smoke, encoding="utf-8")
    print("BO RBA MPB activation transaction applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
