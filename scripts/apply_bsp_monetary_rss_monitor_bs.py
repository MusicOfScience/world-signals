from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/monitor/BSP_MONETARY_RSS_BS_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
LIVE_RUNNER_PATH = ROOT / "scripts/run_live_monitor.py"
SMOKE_RUNNER_PATH = ROOT / "scripts/run_adapter_smoke.py"
ADAPTER_INIT_PATH = ROOT / "src/world_signals/adapters/__init__.py"

APPLY_ENV = "WORLD_SIGNALS_APPLY_MONITOR_BS"
BASE_SHA = "22a5c0a922d3a126bf268acb61a68abe1bfe5075"
CANONICAL_SOURCE_ID = "WSSRC-REGJ-003"
MACHINE_SOURCE_ID = "WSSRC-REGJ-006"
ADAPTER_ID = "BSP_MONETARY_POLICY_RSS"


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
        raise RuntimeError("BS plan is not frozen to exact post-BR main")
    if (canonical.get("version"), len(canonical.get("records", []))) != (
        p["canonical_registry_version"], p["canonical_record_count"]
    ):
        raise RuntimeError("BS requires exact Canonical v0.41 / 689")
    if (sources.get("version"), len(sources.get("sources", []))) != (
        p["source_registry_version"], p["source_count"]
    ):
        raise RuntimeError("BS requires exact Sources v1.91 / 249")
    if (expectations.get("version"), len(expectations.get("adapters", []))) != (
        p["monitor_expectations_version"], p["configured_monitor_adapter_count"]
    ):
        raise RuntimeError("BS requires exact Monitor v0.16 / 14")
    if expectations.get("automatic_canonical_commit") is not False:
        raise RuntimeError("automatic Canonical commit gate must remain closed")
    if expectations.get("google_calendar_write") is not False:
        raise RuntimeError("Google Calendar write gate must remain closed")
    if any(row.get("source_id") == MACHINE_SOURCE_ID for row in sources.get("sources", [])):
        raise RuntimeError("BS BSP RSS machine source already exists")
    if any(row.get("adapter_id") == ADAPTER_ID for row in expectations.get("adapters", [])):
        raise RuntimeError("BS BSP RSS route already exists")

    schedule = source_by_id(sources, CANONICAL_SOURCE_ID)
    exact_existing = {
        "institution": "Bangko Sentral ng Pilipinas",
        "jurisdiction": "Philippines",
        "domain": "monetary_policy",
        "source_type": "official_schedule",
        "authoritative_url": plan["selection"]["schedule_url"],
        "canonical_dependency_count": 2,
        "automated_retrieval_permission": "PENDING_ENDPOINT_OPERATIONAL_REVIEW",
        "monitoring_readiness_status": "ENDPOINT_REVIEW_REQUIRED",
        "source_timezone": "Asia/Manila",
        "machine_readable_available": "HTML/PDF",
        "parser_type": "HTML+PDF",
    }
    for key, expected in exact_existing.items():
        if schedule.get(key) != expected:
            raise RuntimeError(f"BS BSP schedule source pre-state drift for {key}: {schedule.get(key)!r}")
    for missing in ("canonical_provenance_use", "automated_monitoring_use", "verification_mode", "monitoring_activation_status"):
        if schedule.get(missing) is not None:
            raise RuntimeError(f"BS expected legacy BSP governance field {missing} to remain absent before backfill")
    if any(row.get("source_id") == CANONICAL_SOURCE_ID for row in expectations.get("adapters", [])):
        raise RuntimeError("BS must not find a production route on held BSP schedule source")

    ids = list(plan["canonical_occurrence_ids"])
    if len(ids) != 2 or len(set(ids)) != 2:
        raise RuntimeError("BS requires exact two-occurrence BSP allow-list")
    by_id = {r.get("occurrence_id"): r for r in canonical.get("records", []) if r.get("occurrence_id") in set(ids)}
    if set(by_id) != set(ids):
        raise RuntimeError("BS BSP allow-list no longer matches Canonical")
    expected_dates = {row["occurrence_id"]: row["start_local"] for row in plan["canonical_occurrences"]}
    for occurrence_id in ids:
        row = by_id[occurrence_id]
        checks = {
            "series_id": plan["selection"]["series_id"],
            "source_id": CANONICAL_SOURCE_ID,
            "region": "Southeast Asia",
            "source_timezone": "Asia/Manila",
            "time_precision": "DAY",
            "timing_type": "CIVIL_DATE",
            "start_local": expected_dates[occurrence_id],
            "lifecycle_status": "PLANNED",
            "certainty_status": "CONFIRMED",
        }
        for key, expected in checks.items():
            if row.get(key) != expected:
                raise RuntimeError(f"BS Canonical BSP drift for {occurrence_id} {key}: {row.get(key)!r}")
        if row.get("start_utc") is not None:
            raise RuntimeError(f"BS must preserve BSP date-only/no-UTC semantics for {occurrence_id}")


def backfill_schedule_source(source: dict, plan: dict) -> None:
    target = plan["legacy_schedule_source_governance_backfill"]
    source.update({
        "canonical_provenance_use": target["canonical_provenance_use"],
        "automated_monitoring_use": target["automated_monitoring_use"],
        "verification_mode": target["verification_mode"],
        "monitoring_activation_status": target["monitoring_activation_status"],
        "governance_backfill_reviewed_at": plan["reference_date"],
        "governance_backfill_basis": (
            "BS modernized missing governance fields without clearing automated retrieval of the BSP HTML/PDF schedule source. "
            "WSSRC-REGJ-006 is the separate explicit RSS machine interface."
        ),
    })
    if source.get("automated_retrieval_permission") != "PENDING_ENDPOINT_OPERATIONAL_REVIEW":
        raise RuntimeError("BS changed BSP schedule-source retrieval hold")
    if source.get("monitoring_readiness_status") != "ENDPOINT_REVIEW_REQUIRED":
        raise RuntimeError("BS changed BSP schedule-source endpoint-review hold")
    if source.get("canonical_dependency_count") != 2:
        raise RuntimeError("BS changed BSP schedule-source dependency count")


def new_machine_source(plan: dict) -> dict:
    s = plan["selection"]
    d = plan["read_only_diagnostic"]
    return {
        "source_id": MACHINE_SOURCE_ID,
        "institution": "Bangko Sentral ng Pilipinas",
        "jurisdiction": "Philippines",
        "domain": "monetary_policy",
        "endpoint_role": "Official BSP Media Releases RSS monetary-policy publication sentinel",
        "authoritative_url": s["rss_url"],
        "source_type": "official_rss_feed",
        "information_supplied": (
            "Official BSP Media Releases RSS publication metadata and content, including Monetary Board monetary-policy stance releases. "
            "This source is not forward monetary-policy schedule authority."
        ),
        "future_schedule_horizon": "not a schedule source; finite rolling publication feed",
        "typical_advance_notice": "publication driven",
        "machine_readable_available": "RSS/XML",
        "source_timezone": "Asia/Manila",
        "recommended_verification_cadence": "daily; one official RSS request per run",
        "activation_status": "ACTIVE_GUARDED",
        "parser_type": "BSP_MEDIA_RELEASES_RSS_MONETARY_POLICY_SENTINEL",
        "parser_version": "bsp-monetary-rss-0.1",
        "known_limitations": [
            "The RSS feed is finite and rolling; absence has no schedule, lifecycle, cancellation or certainty semantics.",
            "RSS pubDate is publication time, not the Canonical monetary-policy event clock.",
            "Only structurally identified Monetary Board stance publications are eligible for review matching; generic monetary-policy mentions are not.",
            "Positive publication evidence requires reviewed Canonical lifecycle handling and cannot automatically set COMPLETED.",
            "WSSRC-REGJ-003 remains Canonical forward-schedule authority with HTML/PDF automated retrieval held."
        ],
        "backup_source": None,
        "notes": "Separate machine-interface identity preserves the distinction between Canonical schedule provenance and publication monitoring.",
        "timezone_scope": "RSS_PUBDATE_OFFSET_PRESERVED_NORMALIZED_TO_UTC; ASIA_MANILA_CIVIL_DATE_DERIVED_ONLY_FOR_IDENTITY_MATCHING",
        "licence_constraints": "ATTRIBUTION_REQUIRED_FOR_REUSE",
        "ingestion_permission": "OFFICIAL_RSS_MACHINE_PUBLICATION_METADATA_ALLOWED_WITH_ATTRIBUTION",
        "licence_review_status": "CLEARED_REUSE_WITH_ATTRIBUTION_AND_EXPLICIT_RSS_MACHINE_INTERFACE",
        "automated_retrieval_permission": "OFFICIAL_RSS_INTERFACE_EXPLICIT_AUTOMATIC_FETCH_AND_APPLICATION_USE",
        "redistribution_permission": "ALLOWED_WITH_ATTRIBUTION",
        "rights_evidence_url": s["rights_url"],
        "rights_summary": "BSP terms permit quotation, copying or reproduction with BSP credited; RSS documentation separately establishes intended automated feed/application use.",
        "automation_evidence_url": s["rss_documentation_url"],
        "automation_summary": "Automation is limited to one daily request to the BSP-published Media Releases RSS feed; no schedule HTML/PDF follow-up is performed.",
        "rights_reviewed_at": plan["reference_date"],
        "rights_review_scope": "BS_CONTENT_REUSE_AND_EXPLICIT_RSS_MACHINE_INTERFACE_SEPARATED_FROM_SCHEDULE_SOURCE_HOLD",
        "rights_review_note": "Operational governance classification for WORLD SIGNALS; not a legal opinion.",
        "monitoring_readiness_status": "LIVE_VALIDATED_NO_AUTO_COMMIT",
        "monitoring_priority_score": 610,
        "canonical_dependency_count": 0,
        "monitoring_readiness_assessed_at": plan["reference_date"],
        "monitoring_activation_status": "LIVE_READ_ONLY_PUBLICATION_SENTINEL_NO_AUTO_COMMIT",
        "last_successful_research_verification_at": plan["reference_date"],
        "canonical_provenance_use": "MONITOR_ONLY_PUBLICATION_SENTINEL_NO_CANONICAL_SCHEDULE_AUTHORITY",
        "automated_monitoring_use": "CLEARED",
        "verification_mode": "AUTOMATED_PILOT",
        "runtime_health_state": "LIVE_GITHUB_ACTIONS_RSS_FETCH_PARSE_PASS_2026_09_08",
        "governance_backfill_reviewed_at": plan["reference_date"],
        "governance_backfill_basis": "Separate first-party RSS source created because the legacy BSP schedule source remains held for automated HTML/PDF retrieval.",
        "live_adapter_id": ADAPTER_ID,
        "live_validation_evidence": {
            "read_only_diagnostic_run_id": d["successful_run_id"],
            "read_only_diagnostic_job_id": d["successful_job_id"],
            "rss_documentation_http_status": d["rss_documentation_http_status"],
            "rss_http_status": d["rss_http_status"],
            "rss_content_type": d["rss_content_type"],
            "rss_item_count": d["rss_item_count"],
            "rss_sha256": d["rss_sha256"],
            "historical_stance_example_title": d["historical_stance_example_title"],
            "historical_stance_example_publication_date": d["historical_stance_example_publication_date"],
            "request_count": 1,
            "automatic_commit_allowed": False
        },
        "related_source_ids": [CANONICAL_SOURCE_ID],
        "source_role_contract": deepcopy(plan["source_role_contract"]),
        "monitor_endpoints": [
            {
                "endpoint_role": "bsp_media_releases_rss",
                "url": s["rss_url"],
                "transport": "RSS_XML",
                "preferred_for_monitoring": True,
                "completeness_scope": "FINITE_ROLLING_BSP_MEDIA_RELEASES",
                "notes": "Exactly one request per daily run; no automatic item-link or schedule-source follow-up."
            },
            {
                "endpoint_role": "rss_machine_interface_documentation",
                "url": s["rss_documentation_url"],
                "transport": "HTML_MANUAL_GOVERNANCE_REFERENCE",
                "preferred_for_monitoring": False,
                "completeness_scope": "RSS_AUTOMATIC_FETCH_AND_APPLICATION_USE_DOCUMENTATION"
            }
        ]
    }


def monitor_expectation(plan: dict) -> dict:
    s = plan["selection"]
    return {
        "adapter_id": ADAPTER_ID,
        "source_id": MACHINE_SOURCE_ID,
        "canonical_occurrence_ids": list(plan["canonical_occurrence_ids"]),
        "monitor_role": "OFFICIAL_BSP_MONETARY_POLICY_STANCE_PUBLICATION_RSS_SENTINEL",
        "cadence": "DAILY",
        "request_budget_per_run": 1,
        "feed": {
            "url": s["rss_url"],
            "transport": "RSS_XML",
            "request_policy": "ONE_OFFICIAL_RSS_REQUEST_PER_DAILY_MONITOR_RUN"
        },
        "classification_contract": deepcopy(plan["classification_contract"]),
        "source_role_contract": deepcopy(plan["source_role_contract"]),
        "source_failure_policy": "SOURCE_HEALTH_ONLY_NO_EVENT_MUTATION",
        "positive_publication_policy": "GENERATE_REVIEW_CANDIDATE_ONLY_FOR_STRUCTURAL_STANCE_PUBLICATION_MATCHED_BY_EXACT_MANILA_CIVIL_DATE",
        "absence_policy": "FINITE_ROLLING_FEED_ABSENCE_HAS_NO_SCHEDULE_LIFECYCLE_CANCELLATION_OR_CERTAINTY_SEMANTICS",
        "schedule_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "rss_publication_time_is_event_time": False,
        "canonical_clock_mutation_allowed": False,
        "automatic_schedule_html_fetch_allowed": False,
        "canonical_schedule_source_id": CANONICAL_SOURCE_ID,
        "live_intelligence_policy": "NO_AUTOMATIC_PROMOTION_TO_LIVE_INTELLIGENCE_OR_ANALYSIS",
        "automatic_commit_allowed": False
    }


def transform_sources(sources: dict, plan: dict) -> dict:
    out = deepcopy(sources)
    schedule = source_by_id(out, CANONICAL_SOURCE_ID)
    protected = {k: deepcopy(schedule.get(k)) for k in (
        "source_id", "institution", "jurisdiction", "domain", "endpoint_role", "authoritative_url", "source_type",
        "information_supplied", "future_schedule_horizon", "typical_advance_notice", "machine_readable_available",
        "source_timezone", "timezone_scope", "canonical_dependency_count", "automated_retrieval_permission",
        "monitoring_readiness_status", "parser_type", "rights_evidence_url", "rights_summary", "redistribution_permission"
    )}
    backfill_schedule_source(schedule, plan)
    for key, expected in protected.items():
        if schedule.get(key) != expected:
            raise RuntimeError(f"BS changed protected BSP schedule-source field {key}")
    out["sources"].append(new_machine_source(plan))
    out["version"] = plan["postconditions"]["source_registry_version"]
    out["reference_date"] = plan["reference_date"]
    return out


def transform_expectations(expectations: dict, plan: dict) -> dict:
    out = deepcopy(expectations)
    before = deepcopy(out.get("adapters", []))
    out["adapters"].append(monitor_expectation(plan))
    if out["adapters"][:-1] != before:
        raise RuntimeError("BS changed an existing monitor route")
    out["version"] = plan["postconditions"]["monitor_expectations_version"]
    if out.get("automatic_canonical_commit") is not False or out.get("google_calendar_write") is not False:
        raise RuntimeError("BS changed global write gates")
    return out


def patch_adapter_init(text: str) -> str:
    if "BSP_MEDIA_RELEASES_RSS" in text:
        raise RuntimeError("BSP RSS adapter already exported")
    import_anchor = "from .cbn_mpc import (\n"
    block = '''from .bsp_rss import (\n    BSP_MEDIA_RELEASES_RSS,\n    BSP_RSS_ACCEPT,\n    BSP_RSS_DOCS,\n    BSPMediaReleaseItem,\n    fetch_bsp_media_releases_rss,\n    parse_bsp_media_releases_rss,\n)\n'''
    if import_anchor not in text:
        raise RuntimeError("BS adapter import anchor missing")
    text = text.replace(import_anchor, block + import_anchor, 1)
    all_anchor = '    "CBN_MPC_ACCEPT",\n'
    all_block = '''    "BSP_MEDIA_RELEASES_RSS",\n    "BSP_RSS_ACCEPT",\n    "BSP_RSS_DOCS",\n    "BSPMediaReleaseItem",\n'''
    if all_anchor not in text:
        raise RuntimeError("BS adapter __all__ anchor missing")
    text = text.replace(all_anchor, all_block + all_anchor, 1)
    fn_anchor = '    "fetch_cbn_mpc_calendar",\n'
    fn_block = '''    "fetch_bsp_media_releases_rss",\n    "parse_bsp_media_releases_rss",\n'''
    if fn_anchor not in text:
        raise RuntimeError("BS adapter function export anchor missing")
    return text.replace(fn_anchor, fn_block + fn_anchor, 1)


def patch_live_runner(text: str) -> str:
    if 'if "BSP_MONETARY_POLICY_RSS" in configs:' in text:
        raise RuntimeError("BSP RSS live route already wired")
    import_anchor = "    fetch_cbam_annual_declaration_surrender_rule,\n"
    if import_anchor not in text:
        raise RuntimeError("BS live adapter import anchor missing")
    text = text.replace(import_anchor, import_anchor + "    fetch_bsp_media_releases_rss,\n", 1)
    monitor_anchor = "from world_signals.cbn_mpc_monitor import fetch_cbn_robots_policy, cbn_mpc_schedule_review_candidates\n"
    if monitor_anchor not in text:
        raise RuntimeError("BS live monitor import anchor missing")
    text = text.replace(monitor_anchor, "from world_signals.bsp_monetary_monitor import bsp_monetary_rss_review_candidates\n" + monitor_anchor, 1)
    route_anchor = '    if "CBN_MPC_CALENDAR" in configs:\n'
    block = '''    if "BSP_MONETARY_POLICY_RSS" in configs:\n        bsp_config=configs["BSP_MONETARY_POLICY_RSS"]\n        try:\n            bsp_items,bsp_snap=fetch_bsp_media_releases_rss()\n            report["source_health"].append({\n                "adapter_id":"BSP_MONETARY_POLICY_RSS",\n                "source_id":bsp_config["source_id"],\n                "state":"HEALTHY",\n                "snapshot":bsp_snap.as_dict(),\n                "item_count":len(bsp_items),\n                "request_budget_per_run":1,\n                "schedule_authority":False,\n                "lifecycle_authority":False,\n                "certainty_authority":False,\n                "rss_publication_time_is_event_time":False,\n                "automatic_schedule_html_fetch_allowed":False,\n                "automatic_commit_allowed":False,\n            })\n            candidates,observations=bsp_monetary_rss_review_candidates(\n                registry.get("records",[]),bsp_items,bsp_config\n            )\n            report["review_candidates"].extend(candidates)\n            report["observations"].extend(observations)\n        except (AdapterError,ValueError) as exc:\n            report["source_health"].append({\n                "adapter_id":"BSP_MONETARY_POLICY_RSS",\n                "source_id":bsp_config["source_id"],\n                "state":"DEGRADED",\n                "error":str(exc),\n                "canonical_action":"NONE",\n                "absence_is_not_event_state":True,\n                "schedule_authority":False,\n                "lifecycle_authority":False,\n                "automatic_commit_allowed":False,\n            })\n\n'''
    if route_anchor not in text:
        raise RuntimeError("BS live route insertion anchor missing")
    return text.replace(route_anchor, block + route_anchor, 1)


def patch_smoke_runner(text: str) -> str:
    if '"adapter":"BSP_MONETARY_POLICY_RSS"' in text:
        raise RuntimeError("BSP RSS smoke route already wired")
    import_anchor = "    fetch_cbam_certificate_sale_rule,\n"
    if import_anchor not in text:
        raise RuntimeError("BS smoke import anchor missing")
    text = text.replace(import_anchor, import_anchor + "    fetch_bsp_media_releases_rss,\n", 1)
    route_anchor = "    try:\n        jgb_items,jgb_snap=fetch_japan_mof_news_rss()\n"
    block = '''    try:\n        bsp_items,bsp_snap=fetch_bsp_media_releases_rss()\n        report["results"].append({\n            "adapter":"BSP_MONETARY_POLICY_RSS",\n            "status":"PASS",\n            "source_id":"WSSRC-REGJ-006",\n            "snapshot":bsp_snap.as_dict(),\n            "item_count":len(bsp_items),\n            "request_policy":"ONE_OFFICIAL_RSS_REQUEST_PER_DAILY_MONITOR_RUN",\n            "schedule_authority":False,\n            "lifecycle_authority":False,\n            "automatic_schedule_html_fetch_allowed":False,\n        })\n    except (AdapterError,ValueError) as exc:\n        failures.append({"adapter":"BSP_MONETARY_POLICY_RSS","error":str(exc)})\n\n'''
    if route_anchor not in text:
        raise RuntimeError("BS smoke route insertion anchor missing")
    return text.replace(route_anchor, block + route_anchor, 1)


def build_post_state(canonical: dict, sources: dict, expectations: dict, plan: dict) -> tuple[dict, dict, str, str, str]:
    preflight(canonical, sources, expectations, plan)
    post_sources = transform_sources(sources, plan)
    post_expectations = transform_expectations(expectations, plan)
    live = patch_live_runner(LIVE_RUNNER_PATH.read_text(encoding="utf-8"))
    smoke = patch_smoke_runner(SMOKE_RUNNER_PATH.read_text(encoding="utf-8"))
    adapter_init = patch_adapter_init(ADAPTER_INIT_PATH.read_text(encoding="utf-8"))
    if (post_sources.get("version"), len(post_sources.get("sources", []))) != ("1.92", 250):
        raise RuntimeError("BS source post-state mismatch")
    if (post_expectations.get("version"), len(post_expectations.get("adapters", []))) != ("0.17", 15):
        raise RuntimeError("BS monitor post-state mismatch")
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
        print("BS CHECK-ONLY PASS: BSP monetary RSS transaction is valid; no files written.")
        return 0
    if os.getenv(APPLY_ENV) != "1":
        raise RuntimeError(f"--apply requires {APPLY_ENV}=1")
    dump_json(SOURCES_PATH, post_sources)
    dump_json(EXPECTATIONS_PATH, post_expectations)
    LIVE_RUNNER_PATH.write_text(live, encoding="utf-8")
    SMOKE_RUNNER_PATH.write_text(smoke, encoding="utf-8")
    ADAPTER_INIT_PATH.write_text(adapter_init, encoding="utf-8")
    print("BS APPLY PASS: bounded BSP RSS source/route and conservative schedule-source governance backfill materialised.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
