from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/monitor/CBSL_MPR_RSS_BT_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
LIVE_RUNNER_PATH = ROOT / "scripts/run_live_monitor.py"
SMOKE_RUNNER_PATH = ROOT / "scripts/run_adapter_smoke.py"
ADAPTER_INIT_PATH = ROOT / "src/world_signals/adapters/__init__.py"

APPLY_ENV = "WORLD_SIGNALS_APPLY_MONITOR_BT"
BASE_SHA = "2b74c10905760c98c75b3598df96441f99841b00"
CANONICAL_SOURCE_ID = "WSSRC-REGJ-002"
MACHINE_SOURCE_ID = "WSSRC-REGJ-007"
ADAPTER_ID = "CBSL_MONETARY_POLICY_RSS"
SERIES_ID = "WSER-REGJ-LK-CBSL-MPB"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def source_by_id(data: dict, source_id: str) -> dict:
    rows = [row for row in data.get("sources", []) if row.get("source_id") == source_id]
    if len(rows) != 1:
        raise RuntimeError(f"expected exactly one source {source_id}, found {len(rows)}")
    return rows[0]


def preflight(canonical: dict, sources: dict, expectations: dict, plan: dict) -> dict:
    p = plan["preconditions"]
    if plan.get("exact_base_main_sha") != BASE_SHA:
        raise RuntimeError("BT plan is not frozen to exact post-BS main")
    if (canonical.get("version"), len(canonical.get("records", []))) != (
        p["canonical_registry_version"], p["canonical_record_count"]
    ):
        raise RuntimeError("BT requires exact Canonical v0.41 / 689")
    if (sources.get("version"), len(sources.get("sources", []))) != (
        p["source_registry_version"], p["source_count"]
    ):
        raise RuntimeError("BT requires exact Sources v1.92 / 250")
    if (expectations.get("version"), len(expectations.get("adapters", []))) != (
        p["monitor_expectations_version"], p["configured_monitor_adapter_count"]
    ):
        raise RuntimeError("BT requires exact Monitor v0.17 / 15")
    if expectations.get("automatic_canonical_commit") is not False:
        raise RuntimeError("automatic Canonical commit gate must remain closed")
    if expectations.get("google_calendar_write") is not False:
        raise RuntimeError("Google Calendar write gate must remain closed")
    if any(row.get("source_id") == MACHINE_SOURCE_ID for row in sources.get("sources", [])):
        raise RuntimeError("BT CBSL RSS machine source already exists")
    if any(row.get("adapter_id") == ADAPTER_ID for row in expectations.get("adapters", [])):
        raise RuntimeError("BT CBSL RSS route already exists")
    if any(row.get("source_id") == CANONICAL_SOURCE_ID for row in expectations.get("adapters", [])):
        raise RuntimeError("BT must not find a production route on held CBSL schedule source")

    schedule = source_by_id(sources, CANONICAL_SOURCE_ID)
    checks = {
        "institution": "Central Bank of Sri Lanka",
        "jurisdiction": "Sri Lanka",
        "domain": "monetary_policy",
        "endpoint_role": "Monetary Policy Board advance release calendar",
        "authoritative_url": plan["selection"]["schedule_url"],
        "source_type": "official_schedule",
        "source_timezone": "Asia/Colombo",
        "canonical_dependency_count": 2,
        "automated_retrieval_permission": "PRODUCTION_AUTOMATION_HOLD",
        "monitoring_readiness_status": "RIGHTS_AUDIT_REQUIRED",
        "canonical_provenance_use": "MANUAL_INFORMATIONAL_REFERENCE_ONLY",
        "automated_monitoring_use": "PROHIBITED_OR_RIGHTS_HOLD",
        "verification_mode": "RIGHTS_HELD_MANUAL_ONLY",
    }
    for key, expected in checks.items():
        if schedule.get(key) != expected:
            raise RuntimeError(f"BT CBSL schedule-source pre-state drift for {key}: {schedule.get(key)!r}")

    ids = list(plan["canonical_occurrence_ids"])
    if len(ids) != 2 or len(set(ids)) != 2:
        raise RuntimeError("BT requires exact two-occurrence CBSL allow-list")
    by_id = {r.get("occurrence_id"): r for r in canonical.get("records", []) if r.get("occurrence_id") in set(ids)}
    if set(by_id) != set(ids):
        raise RuntimeError("BT CBSL allow-list no longer matches Canonical")
    expected = {row["occurrence_id"]: row for row in plan["canonical_occurrences"]}
    for occurrence_id in ids:
        row = by_id[occurrence_id]
        mapping = expected[occurrence_id]
        canonical_checks = {
            "series_id": SERIES_ID,
            "source_id": CANONICAL_SOURCE_ID,
            "region": "South Asia",
            "source_timezone": "Asia/Colombo",
            "time_precision": "DAY",
            "timing_type": "CIVIL_DATE",
            "start_local": mapping["announcement_date"],
            "lifecycle_status": "PLANNED",
            "certainty_status": "CONFIRMED",
        }
        for key, expected_value in canonical_checks.items():
            if row.get(key) != expected_value:
                raise RuntimeError(
                    f"BT Canonical CBSL drift for {occurrence_id} {key}: {row.get(key)!r}"
                )
        if row.get("start_utc") is not None:
            raise RuntimeError(f"BT must preserve CBSL date-only/no-UTC semantics for {occurrence_id}")
    return deepcopy(schedule)


def new_machine_source(plan: dict) -> dict:
    s = plan["selection"]
    d = plan["read_only_diagnostics"]["cbsl_feed_contract"]
    return {
        "source_id": MACHINE_SOURCE_ID,
        "institution": "Central Bank of Sri Lanka",
        "jurisdiction": "Sri Lanka",
        "domain": "monetary_policy",
        "endpoint_role": "Official CBSL Monetary Policy Review RSS publication sentinel",
        "authoritative_url": s["rss_url"],
        "source_type": "official_rss_feed",
        "information_supplied": (
            "Official CBSL Monetary Policy Review RSS title and linked-PDF identity metadata. "
            "The feed is not forward monetary-policy schedule authority and supplies no publication clock."
        ),
        "future_schedule_horizon": "not a schedule source; finite rolling publication feed",
        "typical_advance_notice": "publication driven",
        "machine_readable_available": "RSS/XML",
        "source_timezone": "Asia/Colombo",
        "recommended_verification_cadence": "daily; one official RSS request per run",
        "activation_status": "ACTIVE_GUARDED",
        "parser_type": "CBSL_MPR_RSS_PUBLICATION_SENTINEL",
        "parser_version": "cbsl-mpr-rss-0.1",
        "known_limitations": [
            "The RSS feed is finite and rolling; absence has no schedule, lifecycle, delay, cancellation or certainty semantics.",
            "RSS items expose title, link and source only; there is no pubDate or publication clock.",
            "The official linked-PDF filename civil date is used only for exact identity matching and is not a clock-time precision upgrade.",
            "The monitor does not automatically fetch linked PDFs, article pages or the held advance-release-calendar source.",
            "Positive publication evidence creates review candidates only and cannot automatically set COMPLETED.",
            "WSSRC-REGJ-002 remains Canonical forward-schedule authority and retains its rights/automation hold."
        ],
        "backup_source": None,
        "notes": "Separate machine-interface identity preserves the distinction between held Canonical schedule provenance and publication monitoring.",
        "timezone_scope": "ASIA_COLOMBO_CIVIL_DATE_IDENTITY_ONLY_NO_RSS_PUBLICATION_TIMESTAMP",
        "licence_constraints": "ALL_RIGHTS_RESERVED_SITE_CONTENT_NO_BROAD_REUSE_GRANT_ASSERTED",
        "ingestion_permission": "OFFICIAL_DEDICATED_RSS_MINIMAL_FACTUAL_METADATA_INTERNAL_MONITORING",
        "licence_review_status": "NO_BROAD_CONTENT_REUSE_GRANT_RSS_MACHINE_INTERFACE_SEPARATELY_IDENTIFIED",
        "automated_retrieval_permission": "OFFICIAL_DEDICATED_RSS_INTERFACE_BOUNDED_METADATA_MONITORING",
        "redistribution_permission": "MINIMAL_FACTUAL_METADATA_ONLY_NO_PDF_OR_ARTICLE_CONTENT_REPUBLICATION",
        "rights_evidence_url": s["rights_evidence_url"],
        "rights_summary": "CBSL website states All Rights Reserved; BT does not infer a broad content-reuse or redistribution licence.",
        "automation_evidence_url": s["rss_documentation_url"],
        "automation_summary": "Automation is limited to one daily request to the CBSL-published Monetary Policy Review RSS feed; no item-link or schedule-source follow-up is performed.",
        "rights_reviewed_at": plan["reference_date"],
        "rights_review_scope": "BT_CONTENT_REUSE_AND_DEDICATED_RSS_MACHINE_ACCESS_SEPARATED_FROM_SCHEDULE_SOURCE_HOLD",
        "rights_review_note": "Operational governance classification for WORLD SIGNALS; not a legal opinion.",
        "monitoring_readiness_status": "LIVE_VALIDATED_NO_AUTO_COMMIT",
        "monitoring_priority_score": 620,
        "canonical_dependency_count": 0,
        "monitoring_readiness_assessed_at": plan["reference_date"],
        "monitoring_activation_status": "LIVE_READ_ONLY_PUBLICATION_SENTINEL_NO_AUTO_COMMIT",
        "last_successful_research_verification_at": plan["reference_date"],
        "canonical_provenance_use": "MONITOR_ONLY_PUBLICATION_SENTINEL_NO_CANONICAL_SCHEDULE_AUTHORITY",
        "automated_monitoring_use": "CLEARED",
        "verification_mode": "AUTOMATED_PILOT",
        "runtime_health_state": "LIVE_GITHUB_ACTIONS_RSS_FETCH_PARSE_PASS_2026_09_08",
        "governance_backfill_reviewed_at": plan["reference_date"],
        "governance_backfill_basis": "Separate first-party dedicated RSS source created while WSSRC-REGJ-002 remains rights-held manual schedule provenance.",
        "live_adapter_id": ADAPTER_ID,
        "live_validation_evidence": {
            "feed_contract_run_id": d["successful_run_id"],
            "feed_contract_job_id": d["successful_job_id"],
            "metadata_run_id": d["metadata_successful_run_id"],
            "metadata_job_id": d["metadata_successful_job_id"],
            "rss_documentation_http_status": d["docs_http_status"],
            "rss_http_status": d["rss_http_status"],
            "rss_content_type": d["rss_content_type"],
            "rss_item_count": d["rss_item_count"],
            "rss_sha256": d["rss_sha256"],
            "standard_pubdate_present": d["standard_pubdate_present"],
            "followup_item_request_count": d["followup_item_request_count"],
            "automatic_commit_allowed": False,
        },
        "related_source_ids": [CANONICAL_SOURCE_ID],
        "source_role_contract": deepcopy(plan["source_role_contract"]),
        "monitor_endpoints": [
            {
                "endpoint_role": "cbsl_monetary_policy_review_rss",
                "url": s["rss_url"],
                "transport": "RSS_XML",
                "preferred_for_monitoring": True,
                "completeness_scope": "FINITE_ROLLING_CBSL_MONETARY_POLICY_REVIEWS",
                "notes": "Exactly one request per daily run; no automatic linked-PDF or schedule-source follow-up."
            },
            {
                "endpoint_role": "rss_machine_interface_documentation",
                "url": s["rss_documentation_url"],
                "transport": "HTML_MANUAL_GOVERNANCE_REFERENCE",
                "preferred_for_monitoring": False,
                "completeness_scope": "CBSL_PUBLISHED_RSS_FEED_DIRECTORY"
            }
        ]
    }


def monitor_expectation(plan: dict) -> dict:
    s = plan["selection"]
    identity = {
        row["occurrence_id"]: {
            "review_number": row["review_number"],
            "year": row["year"],
            "announcement_date": row["announcement_date"],
        }
        for row in plan["canonical_occurrences"]
    }
    return {
        "adapter_id": ADAPTER_ID,
        "source_id": MACHINE_SOURCE_ID,
        "canonical_occurrence_ids": list(plan["canonical_occurrence_ids"]),
        "review_identity_by_occurrence_id": identity,
        "monitor_role": "OFFICIAL_CBSL_MONETARY_POLICY_REVIEW_PUBLICATION_RSS_SENTINEL",
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
        "positive_publication_policy": "GENERATE_REVIEW_CANDIDATE_ONLY_FOR_EXACT_REVIEW_NUMBER_YEAR_AND_OFFICIAL_LINK_FILENAME_CIVIL_DATE_MATCH",
        "absence_policy": "FINITE_ROLLING_FEED_ABSENCE_HAS_NO_SCHEDULE_LIFECYCLE_DELAY_CANCELLATION_OR_CERTAINTY_SEMANTICS",
        "schedule_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "rss_has_publication_clock": False,
        "official_link_filename_date_is_clock_time": False,
        "canonical_clock_mutation_allowed": False,
        "automatic_item_link_fetch_allowed": False,
        "automatic_schedule_html_fetch_allowed": False,
        "canonical_schedule_source_id": CANONICAL_SOURCE_ID,
        "live_intelligence_policy": "NO_AUTOMATIC_PROMOTION_TO_LIVE_INTELLIGENCE_OR_ANALYSIS",
        "automatic_commit_allowed": False,
    }


def transform_sources(sources: dict, plan: dict, schedule_before: dict) -> dict:
    out = deepcopy(sources)
    schedule = source_by_id(out, CANONICAL_SOURCE_ID)
    if schedule != schedule_before:
        raise RuntimeError("BT CBSL schedule source changed before transformation")
    out["sources"].append(new_machine_source(plan))
    if source_by_id(out, CANONICAL_SOURCE_ID) != schedule_before:
        raise RuntimeError("BT changed held CBSL schedule source")
    out["version"] = plan["postconditions"]["source_registry_version"]
    out["reference_date"] = plan["reference_date"]
    return out


def transform_expectations(expectations: dict, plan: dict) -> dict:
    out = deepcopy(expectations)
    before = deepcopy(out.get("adapters", []))
    out["adapters"].append(monitor_expectation(plan))
    if out["adapters"][:-1] != before:
        raise RuntimeError("BT changed an existing monitor route")
    out["version"] = plan["postconditions"]["monitor_expectations_version"]
    if out.get("automatic_canonical_commit") is not False or out.get("google_calendar_write") is not False:
        raise RuntimeError("BT changed global write gates")
    return out


def patch_adapter_init(text: str) -> str:
    if "CBSL_MPR_RSS" in text:
        raise RuntimeError("CBSL RSS adapter already exported")
    import_anchor = "from .cbn_mpc import (\n"
    block = '''from .cbsl_rss import (\n    CBSL_MPR_RSS,\n    CBSL_RSS_ACCEPT,\n    CBSL_RSS_DOCS,\n    CBSLMonetaryPolicyReviewItem,\n    fetch_cbsl_mpr_rss,\n    parse_cbsl_mpr_rss,\n)\n'''
    if import_anchor not in text:
        raise RuntimeError("BT adapter import anchor missing")
    text = text.replace(import_anchor, block + import_anchor, 1)
    all_anchor = '    "CBN_MPC_ACCEPT",\n'
    all_block = '''    "CBSL_MPR_RSS",\n    "CBSL_RSS_ACCEPT",\n    "CBSL_RSS_DOCS",\n    "CBSLMonetaryPolicyReviewItem",\n'''
    if all_anchor not in text:
        raise RuntimeError("BT adapter __all__ anchor missing")
    text = text.replace(all_anchor, all_block + all_anchor, 1)
    fn_anchor = '    "fetch_cbn_mpc_calendar",\n'
    fn_block = '''    "fetch_cbsl_mpr_rss",\n    "parse_cbsl_mpr_rss",\n'''
    if fn_anchor not in text:
        raise RuntimeError("BT adapter function export anchor missing")
    return text.replace(fn_anchor, fn_block + fn_anchor, 1)


def patch_live_runner(text: str) -> str:
    if 'if "CBSL_MONETARY_POLICY_RSS" in configs:' in text:
        raise RuntimeError("CBSL RSS live route already wired")
    import_anchor = "    fetch_cbn_mpc_calendar,\n"
    if import_anchor not in text:
        raise RuntimeError("BT live adapter import anchor missing")
    text = text.replace(import_anchor, "    fetch_cbsl_mpr_rss,\n" + import_anchor, 1)
    monitor_anchor = "from world_signals.cbn_mpc_monitor import fetch_cbn_robots_policy, cbn_mpc_schedule_review_candidates\n"
    if monitor_anchor not in text:
        raise RuntimeError("BT live monitor import anchor missing")
    text = text.replace(
        monitor_anchor,
        "from world_signals.cbsl_monetary_monitor import cbsl_mpr_rss_review_candidates\n" + monitor_anchor,
        1,
    )
    route_anchor = '    if "CBN_MPC_CALENDAR" in configs:\n'
    block = '''    if "CBSL_MONETARY_POLICY_RSS" in configs:\n        cbsl_config=configs["CBSL_MONETARY_POLICY_RSS"]\n        try:\n            cbsl_items,cbsl_snap=fetch_cbsl_mpr_rss()\n            report["source_health"].append({\n                "adapter_id":"CBSL_MONETARY_POLICY_RSS",\n                "source_id":cbsl_config["source_id"],\n                "state":"HEALTHY",\n                "snapshot":cbsl_snap.as_dict(),\n                "item_count":len(cbsl_items),\n                "request_budget_per_run":1,\n                "item_link_followup_request_count":0,\n                "schedule_authority":False,\n                "lifecycle_authority":False,\n                "certainty_authority":False,\n                "rss_has_publication_clock":False,\n                "official_link_filename_date_is_clock_time":False,\n                "automatic_item_link_fetch_allowed":False,\n                "automatic_schedule_html_fetch_allowed":False,\n                "automatic_commit_allowed":False,\n            })\n            candidates,observations=cbsl_mpr_rss_review_candidates(\n                registry.get("records",[]),cbsl_items,cbsl_config\n            )\n            report["review_candidates"].extend(candidates)\n            report["observations"].extend(observations)\n        except (AdapterError,ValueError) as exc:\n            report["source_health"].append({\n                "adapter_id":"CBSL_MONETARY_POLICY_RSS",\n                "source_id":cbsl_config["source_id"],\n                "state":"DEGRADED",\n                "error":str(exc),\n                "canonical_action":"NONE",\n                "absence_is_not_event_state":True,\n                "schedule_authority":False,\n                "lifecycle_authority":False,\n                "rss_has_publication_clock":False,\n                "automatic_item_link_fetch_allowed":False,\n                "automatic_schedule_html_fetch_allowed":False,\n                "automatic_commit_allowed":False,\n            })\n\n'''
    if route_anchor not in text:
        raise RuntimeError("BT live route insertion anchor missing")
    return text.replace(route_anchor, block + route_anchor, 1)


def patch_smoke_runner(text: str) -> str:
    if '"adapter":"CBSL_MONETARY_POLICY_RSS"' in text:
        raise RuntimeError("CBSL RSS smoke route already wired")
    import_anchor = "    fetch_cbn_mpc_calendar,\n"
    if import_anchor not in text:
        raise RuntimeError("BT smoke import anchor missing")
    text = text.replace(import_anchor, "    fetch_cbsl_mpr_rss,\n" + import_anchor, 1)
    route_anchor = "    try:\n        jgb_items,jgb_snap=fetch_japan_mof_news_rss()\n"
    block = '''    try:\n        cbsl_items,cbsl_snap=fetch_cbsl_mpr_rss()\n        report["results"].append({\n            "adapter":"CBSL_MONETARY_POLICY_RSS",\n            "status":"PASS",\n            "source_id":"WSSRC-REGJ-007",\n            "snapshot":cbsl_snap.as_dict(),\n            "item_count":len(cbsl_items),\n            "request_policy":"ONE_OFFICIAL_RSS_REQUEST_PER_DAILY_MONITOR_RUN",\n            "item_link_followup_request_count":0,\n            "schedule_authority":False,\n            "rss_has_publication_clock":False,\n            "automatic_item_link_fetch_allowed":False,\n            "automatic_schedule_html_fetch_allowed":False,\n            "automatic_commit_allowed":False,\n        })\n    except (AdapterError,ValueError) as exc:\n        failures.append({"adapter":"CBSL_MONETARY_POLICY_RSS","error":str(exc)})\n\n'''
    if route_anchor not in text:
        raise RuntimeError("BT smoke route insertion anchor missing")
    return text.replace(route_anchor, block + route_anchor, 1)


def build_post_state(canonical: dict, sources: dict, expectations: dict, plan: dict) -> tuple[dict, dict, str, str, str]:
    schedule_before = preflight(canonical, sources, expectations, plan)
    post_sources = transform_sources(sources, plan, schedule_before)
    post_expectations = transform_expectations(expectations, plan)
    live = patch_live_runner(LIVE_RUNNER_PATH.read_text(encoding="utf-8"))
    smoke = patch_smoke_runner(SMOKE_RUNNER_PATH.read_text(encoding="utf-8"))
    adapter_init = patch_adapter_init(ADAPTER_INIT_PATH.read_text(encoding="utf-8"))
    if source_by_id(post_sources, CANONICAL_SOURCE_ID) != schedule_before:
        raise RuntimeError("BT post-state mutated held CBSL schedule source")
    if (post_sources.get("version"), len(post_sources.get("sources", []))) != ("1.93", 251):
        raise RuntimeError("BT source post-state mismatch")
    if (post_expectations.get("version"), len(post_expectations.get("adapters", []))) != ("0.18", 16):
        raise RuntimeError("BT monitor post-state mismatch")
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
        print("BT CHECK-ONLY PASS: CBSL monetary-policy RSS transaction is valid; no files written.")
        return 0
    if os.getenv(APPLY_ENV) != "1":
        raise RuntimeError(f"--apply requires {APPLY_ENV}=1")
    dump_json(SOURCES_PATH, post_sources)
    dump_json(EXPECTATIONS_PATH, post_expectations)
    LIVE_RUNNER_PATH.write_text(live, encoding="utf-8")
    SMOKE_RUNNER_PATH.write_text(smoke, encoding="utf-8")
    ADAPTER_INIT_PATH.write_text(adapter_init, encoding="utf-8")
    print("BT APPLY PASS: bounded CBSL RSS source/route materialised; held schedule source preserved unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
