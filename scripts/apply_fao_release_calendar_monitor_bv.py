from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/monitor/FAO_RELEASE_CALENDAR_BV_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
LIVE_RUNNER_PATH = ROOT / "scripts/run_live_monitor.py"
SMOKE_RUNNER_PATH = ROOT / "scripts/run_adapter_smoke.py"
ADAPTER_INIT_PATH = ROOT / "src/world_signals/adapters/__init__.py"

APPLY_ENV = "WORLD_SIGNALS_APPLY_MONITOR_BV"
BASE_SHA = "525d44f0e83c58efd6308900740c5677d962a9f4"
SOURCE_ID = "WSSRC-COM-010"
ADAPTER_ID = "FAO_RELEASE_CALENDAR"
TIMEZONE = "Europe/Rome"
REGION = "Cross-regional / Global"

ALLOWED_SOURCE_MUTATION_KEYS = {
    "automated_monitoring_use",
    "automated_retrieval_permission",
    "monitoring_readiness_status",
    "monitoring_activation_status",
    "verification_mode",
    "runtime_health_state",
    "monitoring_readiness_assessed_at",
    "last_successful_research_verification_at",
    "automation_evidence_url",
    "automation_summary",
    "automation_reviewed_at",
    "rights_evidence_url",
    "rights_summary",
    "rights_review_scope",
    "live_adapter_id",
    "live_validation_evidence",
    "monitor_endpoints",
    "source_role_contract",
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


def _changed_keys(before: dict, after: dict) -> set[str]:
    return {key for key in set(before) | set(after) if before.get(key) != after.get(key)}


def preflight(canonical: dict, sources: dict, expectations: dict, plan: dict) -> dict:
    p = plan["preconditions"]
    if plan.get("exact_base_main_sha") != BASE_SHA:
        raise RuntimeError("BV plan is not frozen to exact post-BU main")
    if (canonical.get("version"), len(canonical.get("records", []))) != (
        p["canonical_registry_version"], p["canonical_record_count"]
    ):
        raise RuntimeError("BV requires exact Canonical v0.41 / 689")
    if (sources.get("version"), len(sources.get("sources", []))) != (
        p["source_registry_version"], p["source_count"]
    ):
        raise RuntimeError("BV requires exact Sources v1.94 / 252")
    if (expectations.get("version"), len(expectations.get("adapters", []))) != (
        p["monitor_expectations_version"], p["configured_monitor_adapter_count"]
    ):
        raise RuntimeError("BV requires exact Monitor v0.19 / 17")
    if expectations.get("automatic_canonical_commit") is not False:
        raise RuntimeError("automatic Canonical commit gate must remain closed")
    if expectations.get("google_calendar_write") is not False:
        raise RuntimeError("Google Calendar write gate must remain closed")
    if any(row.get("adapter_id") == ADAPTER_ID for row in expectations.get("adapters", [])):
        raise RuntimeError("BV FAO monitor route already exists")

    source = deepcopy(source_by_id(sources, SOURCE_ID))
    source_checks = {
        "institution": "Food and Agriculture Organization of the United Nations",
        "jurisdiction": "Global",
        "domain": "agriculture_food",
        "source_type": "official_data_release_calendar",
        "authoritative_url": plan["selection"]["calendar_url"],
        "source_timezone": TIMEZONE,
        "canonical_dependency_count": p["source_canonical_dependency_count"],
        "canonical_provenance_use": "MANUAL_INFORMATIONAL_REFERENCE_ONLY",
        "licence_review_status": "CLEARED_FOR_FACTUAL_METADATA",
        "ingestion_permission": "PUBLIC_FACTS_ALLOWED",
        "redistribution_permission": "PUBLIC_FACTUAL_METADATA_ONLY",
        "automated_monitoring_use": p["source_automated_monitoring_use"],
        "automated_retrieval_permission": p["source_automated_retrieval_permission"],
        "monitoring_readiness_status": p["source_monitoring_readiness_status"],
    }
    for key, expected in source_checks.items():
        if source.get(key) != expected:
            raise RuntimeError(f"BV FAO source pre-state drift for {key}: {source.get(key)!r}")

    all_fao = [r for r in canonical.get("records", []) if r.get("source_id") == SOURCE_ID]
    if len(all_fao) != 9:
        raise RuntimeError(f"BV expected exactly nine Canonical dependencies on {SOURCE_ID}, found {len(all_fao)}")
    expected_source_ids = {f"WSO-COM-A-{n:04d}" for n in range(40, 49)}
    if {r.get("occurrence_id") for r in all_fao} != expected_source_ids:
        raise RuntimeError("BV FAO Canonical dependency identity set drift")

    ids = list(plan["canonical_occurrence_ids"])
    if len(ids) != 6 or len(set(ids)) != 6:
        raise RuntimeError("BV requires exact six-occurrence FAO allow-list")
    by_id = {r.get("occurrence_id"): r for r in canonical.get("records", []) if r.get("occurrence_id") in set(ids)}
    if set(by_id) != set(ids):
        raise RuntimeError("BV FAO allow-list no longer matches Canonical")
    expected_rows = {row["occurrence_id"]: row for row in plan["canonical_occurrences"]}
    for occurrence_id in ids:
        row = by_id[occurrence_id]
        expected = expected_rows[occurrence_id]
        checks = {
            "series_id": expected["series_id"],
            "source_id": SOURCE_ID,
            "region": REGION,
            "source_timezone": TIMEZONE,
            "time_precision": "DAY",
            "timing_type": "CIVIL_DATE",
            "start_local": expected["canonical_release_date"],
            "certainty_status": "CONFIRMED",
        }
        for key, value in checks.items():
            if row.get(key) != value:
                raise RuntimeError(f"BV FAO Canonical drift for {occurrence_id} {key}: {row.get(key)!r}")
        if row.get("start_utc") is not None or row.get("all_day_semantics") is not True:
            raise RuntimeError(f"BV must preserve FAO date-only/no-UTC semantics for {occurrence_id}")
    if {"WSO-COM-A-0040", "WSO-COM-A-0041", "WSO-COM-A-0048"} & set(ids):
        raise RuntimeError("BV configured scope must exclude past September pair and month-window Food Outlook")
    return source


def updated_source(source_before: dict, plan: dict) -> dict:
    out = deepcopy(source_before)
    update = deepcopy(plan["source_governance_update"])
    out.update(update)
    out.update({
        "automation_summary": (
            "WORLD SIGNALS automation is bounded to one valid FAO robots-policy request followed, only when allowed, "
            "by one exact first-party 2026 data-release calendar request. No linked FAO, AMIS, FAOSTAT, PDF, news or search endpoint is followed."
        ),
        "automation_reviewed_at": plan["reference_date"],
        "rights_summary": (
            "FAO general website terms permit attributed non-commercial research/informational reuse subject to stated conditions; "
            "the separate statistical-database licence is not projected onto the HTML release-calendar surface."
        ),
        "live_validation_evidence": {
            "run_id": plan["read_only_diagnostic"]["run_id"],
            "job_id": plan["read_only_diagnostic"]["job_id"],
            "request_count": 2,
            "configured_match_count": 6,
            "clock_exposed": False,
            "automatic_commit_allowed": False,
        },
        "monitor_endpoints": [
            {
                "endpoint_role": "robots_policy",
                "url": plan["selection"]["robots_url"],
                "transport": "TEXT_PLAIN",
                "preferred_for_monitoring": True,
                "completeness_scope": "AUTOMATION_POLICY_GATE",
            },
            {
                "endpoint_role": "official_release_calendar",
                "url": plan["selection"]["calendar_url"],
                "transport": "HTML_GET",
                "preferred_for_monitoring": True,
                "completeness_scope": "EXACT_CONFIGURED_FFPI_AND_AMIS_OCT_DEC_2026_SLOTS_ONLY",
            },
        ],
        "source_role_contract": deepcopy(plan["source_role_contract"]),
    })
    changed = _changed_keys(source_before, out)
    if not changed or not changed <= ALLOWED_SOURCE_MUTATION_KEYS:
        raise RuntimeError(f"BV FAO source mutation escaped allowed automation/readiness boundary: {sorted(changed)}")
    for key in (
        "source_id", "institution", "jurisdiction", "domain", "endpoint_role", "authoritative_url",
        "source_type", "information_supplied", "source_timezone", "canonical_dependency_count",
        "canonical_provenance_use", "licence_constraints", "ingestion_permission", "licence_review_status",
        "redistribution_permission", "governance_backfill_basis", "governance_backfill_reviewed_at",
    ):
        if out.get(key) != source_before.get(key):
            raise RuntimeError(f"BV improperly changed FAO identity/rights/provenance field {key}")
    return out


def monitor_expectation(plan: dict) -> dict:
    identity = {
        row["occurrence_id"]: {
            "series_id": row["series_id"],
            "product_key": row["product_key"],
            "slot_month": row["slot_month"],
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
        "configured_month_sections": list(plan["configured_month_sections"]),
        "monitor_role": "OFFICIAL_FAO_FFPI_AMIS_RELEASE_DATE_CHANGE_SENTINEL",
        "cadence": "DAILY",
        "request_budget_per_run": 2,
        "robots_requests_per_run": 1,
        "calendar_requests_per_run": 1,
        "followup_requests_per_run": 0,
        "classification_contract": deepcopy(plan["classification_contract"]),
        "source_role_contract": deepcopy(plan["source_role_contract"]),
        "source_failure_policy": "SOURCE_HEALTH_ONLY_NO_EVENT_MUTATION",
        "positive_change_policy": "GENERATE_REVIEW_CANDIDATE_FOR_SAME_STABLE_OCCURRENCE_ID_ONLY",
        "absence_policy": "MISSING_CONFIGURED_ROW_IS_REVIEW_EVIDENCE_ONLY_NO_EVENT_STATE_INFERENCE",
        "schedule_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "canonical_clock_mutation_allowed": False,
        "automatic_amis_followup_allowed": False,
        "automatic_faostat_followup_allowed": False,
        "automatic_pdf_fetch_allowed": False,
        "automatic_news_followup_allowed": False,
        "automatic_search_route_discovery_allowed": False,
        "live_intelligence_policy": "NO_AUTOMATIC_PROMOTION_TO_LIVE_INTELLIGENCE_OR_ANALYSIS",
        "automatic_commit_allowed": False,
    }


def transform_sources(sources: dict, plan: dict, source_before: dict) -> dict:
    out = deepcopy(sources)
    index = [i for i, row in enumerate(out["sources"]) if row.get("source_id") == SOURCE_ID]
    if len(index) != 1:
        raise RuntimeError("BV FAO source identity count drift")
    before_other = [deepcopy(row) for row in out["sources"] if row.get("source_id") != SOURCE_ID]
    out["sources"][index[0]] = updated_source(source_before, plan)
    after_other = [row for row in out["sources"] if row.get("source_id") != SOURCE_ID]
    if after_other != before_other:
        raise RuntimeError("BV modified a non-FAO source")
    if len(out["sources"]) != len(sources["sources"]):
        raise RuntimeError("BV must not add or remove a source identity")
    out["version"] = plan["postconditions"]["source_registry_version"]
    out["reference_date"] = plan["reference_date"]
    return out


def transform_expectations(expectations: dict, plan: dict) -> dict:
    out = deepcopy(expectations)
    before = deepcopy(out.get("adapters", []))
    out["adapters"].append(monitor_expectation(plan))
    if out["adapters"][:-1] != before:
        raise RuntimeError("BV changed an existing monitor route")
    out["version"] = plan["postconditions"]["monitor_expectations_version"]
    if out.get("automatic_canonical_commit") is not False or out.get("google_calendar_write") is not False:
        raise RuntimeError("BV changed global write gates")
    return out


def patch_adapter_init(text: str) -> str:
    if "FAO_CALENDAR_URL" in text:
        raise RuntimeError("FAO release-calendar adapter already exported")
    import_anchor = "from .fed_monetary_rss import (\n"
    import_block = '''from .fao_release_calendar import (\n    FAO_ACCEPT,\n    FAO_CALENDAR_URL,\n    FAO_PRODUCT_LABELS,\n    FAO_ROBOTS_URL,\n    FAO_TIMEZONE,\n    FAOReleaseSlot,\n    fao_calendar_allowed,\n    fetch_fao_release_calendar,\n    fetch_fao_robots_policy,\n    parse_fao_release_calendar,\n)\n'''
    if import_anchor not in text:
        raise RuntimeError("BV adapter import anchor missing")
    text = text.replace(import_anchor, import_block + import_anchor, 1)
    all_anchor = '    "FED_MONETARY_POLICY_RSS",\n'
    all_block = '''    "FAO_ACCEPT",\n    "FAO_CALENDAR_URL",\n    "FAO_PRODUCT_LABELS",\n    "FAO_ROBOTS_URL",\n    "FAO_TIMEZONE",\n    "FAOReleaseSlot",\n'''
    if all_anchor not in text:
        raise RuntimeError("BV adapter __all__ anchor missing")
    text = text.replace(all_anchor, all_block + all_anchor, 1)
    fn_anchor = '    "fetch_fed_monetary_policy_rss",\n'
    fn_block = '''    "fao_calendar_allowed",\n    "fetch_fao_release_calendar",\n    "fetch_fao_robots_policy",\n    "parse_fao_release_calendar",\n'''
    if fn_anchor not in text:
        raise RuntimeError("BV adapter function export anchor missing")
    return text.replace(fn_anchor, fn_block + fn_anchor, 1)


def patch_live_runner(text: str) -> str:
    if 'if "FAO_RELEASE_CALENDAR" in configs:' in text:
        raise RuntimeError("FAO release live route already wired")
    import_anchor = "    fetch_fed_monetary_policy_rss,\n"
    if import_anchor not in text:
        raise RuntimeError("BV live adapter import anchor missing")
    text = text.replace(
        import_anchor,
        "    fetch_fao_release_calendar,\n    fetch_fao_robots_policy,\n" + import_anchor,
        1,
    )
    monitor_anchor = "from world_signals.fed_monetary_monitor import fed_monetary_rss_review_candidates\n"
    if monitor_anchor not in text:
        raise RuntimeError("BV live monitor import anchor missing")
    text = text.replace(
        monitor_anchor,
        "from world_signals.fao_release_monitor import fao_release_calendar_review_candidates\n" + monitor_anchor,
        1,
    )
    route_anchor = '    if "INDEC_CPI_CALENDAR" in configs:\n'
    block = '''    if "FAO_RELEASE_CALENDAR" in configs:\n        fao_config=configs["FAO_RELEASE_CALENDAR"]\n        try:\n            fao_allowed,fao_robots_snap=fetch_fao_robots_policy()\n            if not fao_allowed:\n                report["source_health"].append({\n                    "adapter_id":"FAO_RELEASE_CALENDAR",\n                    "source_id":fao_config["source_id"],\n                    "state":"DEGRADED",\n                    "robots_snapshot":fao_robots_snap.as_dict(),\n                    "failure_stage":"ROBOTS_POLICY_NOW_DISALLOWS_FAO_RELEASE_CALENDAR",\n                    "calendar_request_skipped":True,\n                    "canonical_action":"NONE",\n                    "automatic_commit_allowed":False,\n                })\n            else:\n                fao_items,fao_calendar_snap=fetch_fao_release_calendar(\n                    list(fao_config["configured_month_sections"])\n                )\n                report["source_health"].append({\n                    "adapter_id":"FAO_RELEASE_CALENDAR",\n                    "source_id":fao_config["source_id"],\n                    "state":"HEALTHY",\n                    "robots_snapshot":fao_robots_snap.as_dict(),\n                    "calendar_snapshot":fao_calendar_snap.as_dict(),\n                    "item_count":len(fao_items),\n                    "request_budget_per_run":2,\n                    "robots_request_count":1,\n                    "calendar_request_count":1,\n                    "followup_request_count":0,\n                    "amis_followup_request_count":0,\n                    "faostat_followup_request_count":0,\n                    "pdf_followup_request_count":0,\n                    "news_followup_request_count":0,\n                    "search_route_request_count":0,\n                    "schedule_authority":False,\n                    "lifecycle_authority":False,\n                    "certainty_authority":False,\n                    "canonical_clock_mutation_allowed":False,\n                    "automatic_commit_allowed":False,\n                })\n                candidates,observations=fao_release_calendar_review_candidates(\n                    registry.get("records",[]),fao_items,fao_config\n                )\n                report["review_candidates"].extend(candidates)\n                report["observations"].extend(observations)\n        except (AdapterError,ValueError) as exc:\n            report["source_health"].append({\n                "adapter_id":"FAO_RELEASE_CALENDAR",\n                "source_id":fao_config["source_id"],\n                "state":"DEGRADED",\n                "error":str(exc),\n                "canonical_action":"NONE",\n                "absence_is_not_event_state":True,\n                "schedule_authority":False,\n                "lifecycle_authority":False,\n                "certainty_authority":False,\n                "canonical_clock_mutation_allowed":False,\n                "automatic_commit_allowed":False,\n            })\n\n'''
    if route_anchor not in text:
        raise RuntimeError("BV live route insertion anchor missing")
    return text.replace(route_anchor, block + route_anchor, 1)


def patch_smoke_runner(text: str) -> str:
    if '"adapter":"FAO_RELEASE_CALENDAR"' in text:
        raise RuntimeError("FAO release smoke route already wired")
    import_anchor = "    fetch_fed_monetary_policy_rss,\n"
    if import_anchor not in text:
        raise RuntimeError("BV smoke adapter import anchor missing")
    text = text.replace(
        import_anchor,
        "    fetch_fao_release_calendar,\n    fetch_fao_robots_policy,\n" + import_anchor,
        1,
    )
    route_anchor = "    try:\n        indec_slugs=[\"Septiembre-2026\",\"Octubre-2026\",\"Noviembre-2026\",\"Diciembre-2026\"]\n"
    block = '''    try:\n        fao_months=["October 2026","November 2026","December 2026"]\n        fao_allowed,fao_robots_snap=fetch_fao_robots_policy()\n        if not fao_allowed:\n            raise AdapterError("FAO robots policy disallows the release-calendar path")\n        fao_items,fao_calendar_snap=fetch_fao_release_calendar(fao_months)\n        report["results"].append({\n            "adapter":"FAO_RELEASE_CALENDAR",\n            "status":"PASS",\n            "source_id":"WSSRC-COM-010",\n            "robots_snapshot":fao_robots_snap.as_dict(),\n            "calendar_snapshot":fao_calendar_snap.as_dict(),\n            "item_count":len(fao_items),\n            "request_budget_per_run":2,\n            "robots_request_count":1,\n            "calendar_request_count":1,\n            "followup_request_count":0,\n            "schedule_authority":False,\n            "lifecycle_authority":False,\n            "canonical_clock_mutation_allowed":False,\n            "automatic_commit_allowed":False,\n        })\n    except (AdapterError,ValueError) as exc:\n        failures.append({"adapter":"FAO_RELEASE_CALENDAR","error":str(exc)})\n\n'''
    if route_anchor not in text:
        raise RuntimeError("BV smoke route insertion anchor missing")
    return text.replace(route_anchor, block + route_anchor, 1)


def build_post_state(
    canonical: dict,
    sources: dict,
    expectations: dict,
    plan: dict,
) -> tuple[dict, dict, str, str, str, dict]:
    source_before = preflight(canonical, sources, expectations, plan)
    post_sources = transform_sources(sources, plan, source_before)
    post_expectations = transform_expectations(expectations, plan)
    live = patch_live_runner(LIVE_RUNNER_PATH.read_text(encoding="utf-8"))
    smoke = patch_smoke_runner(SMOKE_RUNNER_PATH.read_text(encoding="utf-8"))
    adapter_init = patch_adapter_init(ADAPTER_INIT_PATH.read_text(encoding="utf-8"))

    post_source = deepcopy(source_by_id(post_sources, SOURCE_ID))
    changed = _changed_keys(source_before, post_source)
    if not changed <= ALLOWED_SOURCE_MUTATION_KEYS:
        raise RuntimeError("BV final source mutation boundary drift")
    if (post_sources.get("version"), len(post_sources.get("sources", []))) != ("1.95", 252):
        raise RuntimeError("BV source post-state mismatch")
    if (post_expectations.get("version"), len(post_expectations.get("adapters", []))) != ("0.20", 18):
        raise RuntimeError("BV monitor post-state mismatch")
    return post_sources, post_expectations, live, smoke, adapter_init, source_before


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    plan = load_json(PLAN_PATH)
    canonical = load_json(CANONICAL_PATH)
    sources = load_json(SOURCES_PATH)
    expectations = load_json(EXPECTATIONS_PATH)
    post_sources, post_expectations, live, smoke, adapter_init, _ = build_post_state(
        canonical, sources, expectations, plan
    )
    if not args.apply:
        print("BV CHECK-ONLY PASS: FAO release-calendar transaction is valid; no files written.")
        return 0
    if os.getenv(APPLY_ENV) != "1":
        raise RuntimeError(f"--apply requires {APPLY_ENV}=1")
    dump_json(SOURCES_PATH, post_sources)
    dump_json(EXPECTATIONS_PATH, post_expectations)
    LIVE_RUNNER_PATH.write_text(live, encoding="utf-8")
    SMOKE_RUNNER_PATH.write_text(smoke, encoding="utf-8")
    ADAPTER_INIT_PATH.write_text(adapter_init, encoding="utf-8")
    print("BV APPLY PASS: bounded FAO FFPI/AMIS release-calendar route materialised; Canonical and source identity count unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
