from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/monitor/JGB_RSS_MONITOR_BR_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
LIVE_RUNNER_PATH = ROOT / "scripts/run_live_monitor.py"
SMOKE_RUNNER_PATH = ROOT / "scripts/run_adapter_smoke.py"
ADAPTER_INIT_PATH = ROOT / "src/world_signals/adapters/__init__.py"

APPLY_ENV = "WORLD_SIGNALS_APPLY_MONITOR_BR"
BASE_SHA = "1b021a5edb6b80dfab672f38047377d39dcae497"
CANONICAL_SOURCE_ID = "WSSRC-FIS-007"
MACHINE_SOURCE_ID = "WSSRC-FIS-029"
ADAPTER_ID = "JAPAN_MOF_JGB_RSS"


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
        raise RuntimeError("BR plan is not frozen to the exact post-BQ main SHA")
    if (canonical.get("version"), len(canonical.get("records", []))) != (
        p["canonical_registry_version"], p["canonical_record_count"]
    ):
        raise RuntimeError("BR requires exact Canonical v0.41 / 689")
    if (sources.get("version"), len(sources.get("sources", []))) != (
        p["source_registry_version"], p["source_count"]
    ):
        raise RuntimeError("BR requires exact Sources v1.90 / 248")
    if (expectations.get("version"), len(expectations.get("adapters", []))) != (
        p["monitor_expectations_version"], p["configured_monitor_adapter_count"]
    ):
        raise RuntimeError("BR requires exact Monitor v0.15 / 13")
    if expectations.get("automatic_canonical_commit") is not False:
        raise RuntimeError("automatic Canonical commit gate must remain closed")
    if expectations.get("google_calendar_write") is not False:
        raise RuntimeError("Google Calendar write gate must remain closed")
    if any(row.get("source_id") == MACHINE_SOURCE_ID for row in sources.get("sources", [])):
        raise RuntimeError("BR MOF RSS machine source already exists")
    if any(row.get("adapter_id") == ADAPTER_ID for row in expectations.get("adapters", [])):
        raise RuntimeError("BR MOF JGB RSS route already exists")

    schedule = source_by_id(sources, CANONICAL_SOURCE_ID)
    expected_schedule = {
        "canonical_dependency_count": 10,
        "canonical_provenance_use": "CLEARED_CURATED_FACTUAL_METADATA",
        "automated_monitoring_use": "ENDPOINT_REVIEW_REQUIRED",
        "automated_retrieval_permission": "PENDING_ENDPOINT_OPERATIONAL_REVIEW",
        "verification_mode": "AUTOMATED_PILOT",
        "source_timezone": "Asia/Tokyo",
    }
    for key, expected in expected_schedule.items():
        if schedule.get(key) != expected:
            raise RuntimeError(f"BR JGB schedule source pre-state drift for {key}: {schedule.get(key)!r}")

    ids = list(plan["canonical_occurrence_ids"])
    if len(ids) != 10 or len(set(ids)) != 10:
        raise RuntimeError("BR requires exact ten-occurrence JGB allow-list")
    by_id = {r.get("occurrence_id"): r for r in canonical.get("records", []) if r.get("occurrence_id") in set(ids)}
    if set(by_id) != set(ids):
        raise RuntimeError("BR JGB allow-list no longer matches Canonical")
    for occurrence_id in ids:
        row = by_id[occurrence_id]
        checks = {
            "series_id": "WSER-FIS-JP-JGB",
            "source_id": CANONICAL_SOURCE_ID,
            "region": "East Asia",
            "source_timezone": "Asia/Tokyo",
            "time_precision": "DAY",
        }
        for key, expected in checks.items():
            if row.get(key) != expected:
                raise RuntimeError(f"BR Canonical JGB drift for {occurrence_id} {key}: {row.get(key)!r}")
        if row.get("start_utc") is not None:
            raise RuntimeError(f"BR must preserve date-only/no-UTC semantics for {occurrence_id}")


def new_machine_source(plan: dict) -> dict:
    d = plan["read_only_diagnostic"]
    s = plan["selection"]
    return {
        "source_id": MACHINE_SOURCE_ID,
        "institution": "Japan Ministry of Finance",
        "jurisdiction": "Japan",
        "domain": "fiscal_sovereign",
        "endpoint_role": "Official MOF RSS publication/change sentinel for JGB monitoring",
        "authoritative_url": s["rss_url"],
        "source_type": "official_rss_feed",
        "information_supplied": (
            "Official MOF English news-feed publication items including JGB auction announcements, auction results and possible calendar-change notices. "
            "This source is not forward auction-schedule authority."
        ),
        "future_schedule_horizon": "not a schedule source; finite rolling publication feed",
        "typical_advance_notice": "event/publication driven",
        "machine_readable_available": "RSS 2.0 XML",
        "source_timezone": "Asia/Tokyo",
        "recommended_verification_cadence": "daily; one official RSS request per run",
        "activation_status": "ACTIVE_GUARDED",
        "parser_type": "JAPAN_MOF_JGB_RSS_PUBLICATION_CHANGE_SENTINEL",
        "parser_version": "jp-mof-jgb-rss-0.1",
        "known_limitations": [
            "The RSS feed is finite and rolling; absence cannot imply no calendar change, cancellation, delay, completion or certainty change.",
            "RSS pubDate is publication time and is not the auction event time.",
            "Standard auction-result items are positive publication evidence only and require reviewed Canonical lifecycle handling.",
            "Special-participant result items are corroboration only to avoid duplicate lifecycle propositions.",
            "Issuance-announcement titles identify tenor and reference month but do not establish the Canonical auction date.",
            "Calendar-change notices require manual recheck of WSSRC-FIS-007; BR does not automatically fetch the held auction-calendar HTML.",
            "WSSRC-FIS-007 remains Canonical forward-schedule authority with its separate HTML automated-retrieval hold unchanged."
        ],
        "backup_source": None,
        "notes": "Separate machine-interface identity preserves the distinction between Canonical schedule authority and RSS publication/change monitoring.",
        "timezone_scope": "RSS_PUBLICATION_TIMESTAMP_OFFSET_PRESERVED_AND_NORMALIZED_TO_UTC; CANONICAL_AUCTION_TIME_UNCHANGED",
        "licence_constraints": "PUBLIC_DATA_LICENSE_V1_WITH_STATED_EXCEPTIONS",
        "ingestion_permission": "OFFICIAL_RSS_MACHINE_PUBLICATION_METADATA_ALLOWED",
        "licence_review_status": "CLEARED_PUBLIC_DATA_LICENCE_AND_EXPLICIT_RSS_SOFTWARE_INTERFACE",
        "automated_retrieval_permission": "OFFICIAL_RSS_SUBSCRIPTION_INTERFACE_EXPLICIT_READER_AGGREGATOR_USE",
        "redistribution_permission": "PUBLIC_DATA_LICENCE_V1_WITH_ATTRIBUTION_AND_STATED_EXCEPTIONS",
        "rights_evidence_url": s["rights_url"],
        "rights_summary": "MOF applies Japan Public Data License v1.0 to general website content subject to stated exceptions.",
        "automation_summary": (
            "Automation is limited to one daily request to MOF's documented English RSS subscription interface. "
            "The conventional /robots.txt path returned HTTP 404 and the JGB calendar HTML remains outside this automated route."
        ),
        "rights_reviewed_at": plan["reference_date"],
        "rights_review_scope": "BR_OFFICIAL_RSS_MACHINE_INTERFACE_WITH_HTML_SCHEDULE_HOLD_PRESERVED",
        "rights_review_note": "Operational governance classification for WORLD SIGNALS; not a legal opinion.",
        "monitoring_readiness_status": "LIVE_VALIDATED_NO_AUTO_COMMIT",
        "monitoring_priority_score": 360,
        "canonical_dependency_count": 0,
        "monitoring_readiness_assessed_at": plan["reference_date"],
        "monitoring_activation_status": "LIVE_READ_ONLY_PUBLICATION_CHANGE_SENTINEL_NO_AUTO_COMMIT",
        "last_successful_research_verification_at": plan["reference_date"],
        "canonical_provenance_use": "MONITOR_ONLY_PUBLICATION_CHANGE_SENTINEL_NO_CANONICAL_SCHEDULE_AUTHORITY",
        "automated_monitoring_use": "CLEARED",
        "verification_mode": "AUTOMATED_PILOT",
        "runtime_health_state": "LIVE_GITHUB_ACTIONS_RSS_FETCH_PARSE_PASS_2026_09_08",
        "governance_backfill_reviewed_at": plan["reference_date"],
        "governance_backfill_basis": (
            "Separate official RSS machine-interface identity created because WSSRC-FIS-007 remains the Canonical JGB schedule source with HTML endpoint automation held."
        ),
        "live_adapter_id": ADAPTER_ID,
        "live_validation_evidence": {
            "failed_html_probe_run_id": d["failed_html_probe_run_id"],
            "failed_html_probe_job_id": d["failed_html_probe_job_id"],
            "successful_rss_probe_run_id": d["successful_rss_probe_run_id"],
            "successful_rss_probe_job_id": d["successful_rss_probe_job_id"],
            "observed_at": d["observed_at"],
            "rss_http_status": d["rss_http_status"],
            "rss_content_type": d["rss_content_type"],
            "rss_item_count": d["rss_item_count"],
            "jgb_related_item_count": d["jgb_related_item_count"],
            "rss_sha256": d["rss_sha256"],
            "rss_documentation_http_status": d["rss_documentation_http_status"],
            "rights_http_status": d["rights_http_status"],
            "html_robots_status": 404,
            "html_calendar_hold_preserved": True,
            "automatic_commit_allowed": False,
        },
        "related_source_ids": [CANONICAL_SOURCE_ID],
        "source_role_contract": deepcopy(plan["source_role_contract"]),
        "monitor_endpoints": [
            {
                "endpoint_role": "mof_english_news_rss",
                "url": s["rss_url"],
                "transport": "RSS_2_0_XML",
                "preferred_for_monitoring": True,
                "completeness_scope": "FINITE_ROLLING_MOF_ENGLISH_NEWS_PUBLICATIONS",
                "notes": "One request per daily run; no follow-up calendar HTML fetch."
            },
            {
                "endpoint_role": "rss_machine_interface_documentation",
                "url": s["rss_documentation_url"],
                "transport": "HTML_MANUAL_GOVERNANCE_REFERENCE",
                "preferred_for_monitoring": False,
                "completeness_scope": "RSS_SUBSCRIPTION_INTERFACE_DOCUMENTATION"
            }
        ]
    }


def monitor_expectation(plan: dict) -> dict:
    s = plan["selection"]
    return {
        "adapter_id": ADAPTER_ID,
        "source_id": MACHINE_SOURCE_ID,
        "canonical_occurrence_ids": list(plan["canonical_occurrence_ids"]),
        "monitor_role": "OFFICIAL_JAPAN_MOF_JGB_PUBLICATION_AND_CHANGE_RSS_SENTINEL",
        "cadence": "DAILY",
        "request_budget_per_run": 1,
        "feed": {
            "url": s["rss_url"],
            "transport": "RSS_2_0_XML",
            "request_policy": "ONE_OFFICIAL_RSS_REQUEST_PER_DAILY_MONITOR_RUN"
        },
        "classification_contract": deepcopy(plan["classification_contract"]),
        "source_role_contract": deepcopy(plan["source_role_contract"]),
        "source_failure_policy": "SOURCE_HEALTH_ONLY_NO_EVENT_MUTATION",
        "absence_policy": "FINITE_ROLLING_FEED_ABSENCE_HAS_NO_SCHEDULE_LIFECYCLE_OR_CERTAINTY_SEMANTICS",
        "positive_result_policy": "GENERATE_REVIEW_CANDIDATE_FOR_STANDARD_RESULT_MATCH_TO_NONCOMPLETED_TRACKED_AUCTION",
        "special_participant_result_policy": "CORROBORATION_OBSERVATION_ONLY",
        "issuance_announcement_policy": "OBSERVATION_ONLY_NO_AUCTION_DATE_INFERENCE",
        "calendar_change_notice_policy": "GENERATE_MANUAL_WSSRC_FIS_007_SCHEDULE_RECHECK_CANDIDATE",
        "schedule_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "rss_publication_time_is_auction_time": False,
        "automatic_calendar_html_fetch_allowed": False,
        "canonical_schedule_source_id": CANONICAL_SOURCE_ID,
        "live_intelligence_policy": "NO_AUTOMATIC_PROMOTION_TO_LIVE_INTELLIGENCE_OR_ANALYSIS",
        "automatic_commit_allowed": False
    }


def transform_sources(sources: dict, plan: dict) -> dict:
    out = deepcopy(sources)
    schedule_before = deepcopy(source_by_id(out, CANONICAL_SOURCE_ID))
    out["sources"].append(new_machine_source(plan))
    if source_by_id(out, CANONICAL_SOURCE_ID) != schedule_before:
        raise RuntimeError("BR changed the held JGB Canonical schedule source")
    out["version"] = plan["postconditions"]["source_registry_version"]
    out["reference_date"] = plan["reference_date"]
    return out


def transform_expectations(expectations: dict, plan: dict) -> dict:
    out = deepcopy(expectations)
    before = deepcopy(out.get("adapters", []))
    out["adapters"].append(monitor_expectation(plan))
    if out["adapters"][:-1] != before:
        raise RuntimeError("BR changed an existing monitor route")
    out["version"] = plan["postconditions"]["monitor_expectations_version"]
    if out.get("automatic_canonical_commit") is not False or out.get("google_calendar_write") is not False:
        raise RuntimeError("BR changed global write gates")
    return out


def patch_adapter_init(text: str) -> str:
    if "JAPAN_MOF_NEWS_RSS" in text:
        raise RuntimeError("Japan MOF RSS adapter already exported")
    import_anchor = "from .japan_mof_jgb import (\n"
    block = '''from .japan_mof_rss import (\n    JAPAN_MOF_NEWS_RSS,\n    JAPAN_MOF_RSS_ACCEPT,\n    JAPAN_MOF_RSS_DOCS,\n    JapanMOFRSSItem,\n    fetch_japan_mof_news_rss,\n    parse_japan_mof_news_rss,\n)\n'''
    if import_anchor not in text:
        raise RuntimeError("BR Japan MOF adapter import anchor missing")
    text = text.replace(import_anchor, block + import_anchor, 1)
    all_anchor = '    "JAPAN_MOF_JGB_CALENDAR_INDEX",\n'
    all_block = '''    "JAPAN_MOF_NEWS_RSS",\n    "JAPAN_MOF_RSS_ACCEPT",\n    "JAPAN_MOF_RSS_DOCS",\n    "JapanMOFRSSItem",\n'''
    if all_anchor not in text:
        raise RuntimeError("BR Japan MOF __all__ anchor missing")
    text = text.replace(all_anchor, all_block + all_anchor, 1)
    fn_anchor = '    "fetch_jgb_monthly_auction_calendar",\n'
    fn_block = '''    "fetch_japan_mof_news_rss",\n    "parse_japan_mof_news_rss",\n'''
    if fn_anchor not in text:
        raise RuntimeError("BR Japan MOF __all__ function anchor missing")
    return text.replace(fn_anchor, fn_block + fn_anchor, 1)


def patch_live_runner(text: str) -> str:
    if 'if "JAPAN_MOF_JGB_RSS" in configs:' in text:
        raise RuntimeError("BR live route already wired")
    import_anchor = "    fetch_japan_household_spending_data,\n"
    if import_anchor not in text:
        raise RuntimeError("BR live adapter import anchor missing")
    text = text.replace(import_anchor, import_anchor + "    fetch_japan_mof_news_rss,\n", 1)
    monitor_anchor = "from world_signals.japan_household_spending_monitor import japan_household_spending_review_candidates\n"
    monitor_import = "from world_signals.japan_mof_jgb_monitor import japan_mof_jgb_rss_review_candidates\n"
    if monitor_anchor not in text:
        raise RuntimeError("BR JGB monitor import anchor missing")
    text = text.replace(monitor_anchor, monitor_import + monitor_anchor, 1)
    route_anchor = '    if "JAPAN_HHSPEND_STATISTICS_DASHBOARD_API" in configs:\n'
    block = '''    if "JAPAN_MOF_JGB_RSS" in configs:\n        jgb_config=configs["JAPAN_MOF_JGB_RSS"]\n        try:\n            jgb_items,jgb_snap=fetch_japan_mof_news_rss()\n            report["source_health"].append({\n                "adapter_id":"JAPAN_MOF_JGB_RSS",\n                "source_id":jgb_config["source_id"],\n                "state":"HEALTHY",\n                "snapshot":jgb_snap.as_dict(),\n                "item_count":len(jgb_items),\n                "request_policy":"ONE_OFFICIAL_RSS_REQUEST_PER_DAILY_MONITOR_RUN",\n                "schedule_authority":False,\n                "lifecycle_authority":False,\n                "automatic_calendar_html_fetch_allowed":False,\n                "automatic_commit_allowed":False,\n            })\n            candidates,observations=japan_mof_jgb_rss_review_candidates(\n                registry.get("records",[]),jgb_items,jgb_config\n            )\n            report["review_candidates"].extend(candidates)\n            report["observations"].extend(observations)\n        except (AdapterError,ValueError) as exc:\n            report["source_health"].append({\n                "adapter_id":"JAPAN_MOF_JGB_RSS",\n                "source_id":jgb_config["source_id"],\n                "state":"DEGRADED",\n                "error":str(exc),\n                "canonical_action":"NONE",\n                "absence_is_not_event_state":True,\n                "schedule_authority":False,\n                "lifecycle_authority":False,\n                "automatic_calendar_html_fetch_allowed":False,\n            })\n\n'''
    if route_anchor not in text:
        raise RuntimeError("BR live route insertion anchor missing")
    return text.replace(route_anchor, block + route_anchor, 1)


def patch_smoke_runner(text: str) -> str:
    if '"adapter":"JAPAN_MOF_JGB_RSS"' in text:
        raise RuntimeError("BR smoke route already wired")
    import_anchor = "    fetch_japan_household_spending_data,\n"
    if import_anchor not in text:
        raise RuntimeError("BR smoke adapter import anchor missing")
    text = text.replace(import_anchor, import_anchor + "    fetch_japan_mof_news_rss,\n", 1)
    route_anchor = "    try:\n        jp_values,jp_snap=fetch_japan_household_spending_data(\n"
    block = '''    try:\n        jgb_items,jgb_snap=fetch_japan_mof_news_rss()\n        report["results"].append({\n            "adapter":"JAPAN_MOF_JGB_RSS",\n            "status":"PASS",\n            "source_id":"WSSRC-FIS-029",\n            "snapshot":jgb_snap.as_dict(),\n            "item_count":len(jgb_items),\n            "request_policy":"ONE_OFFICIAL_RSS_REQUEST_PER_DAILY_MONITOR_RUN",\n            "schedule_authority":False,\n            "automatic_calendar_html_fetch_allowed":False,\n            "automatic_commit_allowed":False,\n        })\n    except AdapterError as exc:\n        failures.append(str(exc))\n        report["results"].append({\n            "adapter":"JAPAN_MOF_JGB_RSS",\n            "status":"FAIL",\n            "source_id":"WSSRC-FIS-029",\n            "error":str(exc),\n            "canonical_action":"NONE",\n        })\n\n'''
    if route_anchor not in text:
        raise RuntimeError("BR smoke route insertion anchor missing")
    return text.replace(route_anchor, block + route_anchor, 1)


def build_post_state(canonical: dict, sources: dict, expectations: dict, plan: dict) -> tuple[dict, dict, str, str, str]:
    preflight(canonical, sources, expectations, plan)
    post_sources = transform_sources(sources, plan)
    post_expectations = transform_expectations(expectations, plan)
    live = patch_live_runner(LIVE_RUNNER_PATH.read_text(encoding="utf-8"))
    smoke = patch_smoke_runner(SMOKE_RUNNER_PATH.read_text(encoding="utf-8"))
    adapter_init = patch_adapter_init(ADAPTER_INIT_PATH.read_text(encoding="utf-8"))
    return post_sources, post_expectations, live, smoke, adapter_init


def validate_post_state(canonical: dict, sources: dict, expectations: dict, plan: dict) -> None:
    post = plan["postconditions"]
    if (canonical.get("version"), len(canonical.get("records", []))) != (
        post["canonical_registry_version"], post["canonical_record_count"]
    ):
        raise RuntimeError("BR changed Canonical")
    if (sources.get("version"), len(sources.get("sources", []))) != (
        post["source_registry_version"], post["source_count"]
    ):
        raise RuntimeError("BR source post-state mismatch")
    if (expectations.get("version"), len(expectations.get("adapters", []))) != (
        post["monitor_expectations_version"], post["configured_monitor_adapter_count"]
    ):
        raise RuntimeError("BR monitor post-state mismatch")
    schedule = source_by_id(sources, CANONICAL_SOURCE_ID)
    if schedule.get("automated_monitoring_use") != "ENDPOINT_REVIEW_REQUIRED":
        raise RuntimeError("BR improperly cleared JGB schedule HTML automation")
    if schedule.get("automated_retrieval_permission") != "PENDING_ENDPOINT_OPERATIONAL_REVIEW":
        raise RuntimeError("BR changed JGB schedule HTML endpoint hold")
    machine = source_by_id(sources, MACHINE_SOURCE_ID)
    if machine.get("canonical_dependency_count") != 0:
        raise RuntimeError("BR RSS source acquired Canonical dependencies")
    if machine.get("automated_monitoring_use") != "CLEARED":
        raise RuntimeError("BR RSS source automation state mismatch")
    route = [r for r in expectations.get("adapters", []) if r.get("adapter_id") == ADAPTER_ID]
    if len(route) != 1:
        raise RuntimeError("BR RSS route missing or duplicated")
    route = route[0]
    if route.get("request_budget_per_run") != 1:
        raise RuntimeError("BR RSS route request budget drift")
    for key in ("schedule_authority", "lifecycle_authority", "certainty_authority", "automatic_calendar_html_fetch_allowed", "automatic_commit_allowed"):
        if route.get(key) is not False:
            raise RuntimeError(f"BR route safety gate drift for {key}")
    if expectations.get("automatic_canonical_commit") is not False or expectations.get("google_calendar_write") is not False:
        raise RuntimeError("BR opened global write gate")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    plan = load_json(PLAN_PATH)
    canonical = load_json(CANONICAL_PATH)
    sources = load_json(SOURCES_PATH)
    expectations = load_json(EXPECTATIONS_PATH)
    post_sources, post_expectations, live, smoke, adapter_init = build_post_state(canonical, sources, expectations, plan)
    validate_post_state(canonical, post_sources, post_expectations, plan)
    if not args.apply:
        print("BR CHECK-ONLY PASS: Japan MOF JGB RSS transaction is valid; no files written.")
        return 0
    if os.getenv(APPLY_ENV) != "1":
        raise RuntimeError(f"APPLY BLOCKED: set {APPLY_ENV}=1 for controlled BR transaction")
    dump_json(SOURCES_PATH, post_sources)
    dump_json(EXPECTATIONS_PATH, post_expectations)
    LIVE_RUNNER_PATH.write_text(live, encoding="utf-8")
    SMOKE_RUNNER_PATH.write_text(smoke, encoding="utf-8")
    ADAPTER_INIT_PATH.write_text(adapter_init, encoding="utf-8")
    print("BR APPLY PASS: bounded Japan MOF JGB RSS source/route materialised.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
