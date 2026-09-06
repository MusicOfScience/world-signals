#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.coverage import build_coverage_audit
from world_signals.validation import validate_registry

PLAN_PATH = ROOT / "data/coverage/IMD_HEATWAVE_OUTLOOK_AT_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SCHEMA_PATH = ROOT / "data/canonical/schema.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
OPERATIONS_PATH = ROOT / "data/monitor/operations_policy.json"
ANALYSIS_SCHEMA_PATH = ROOT / "data/analysis/schema.json"
REVIEWS_PATH = ROOT / "data/analysis/event_reviews.json"
EVIDENCE_PATH = ROOT / "data/analysis/evidence_registry.json"
CORRECTION_L_PLAN_PATH = ROOT / "data/coverage/PHYSICAL_RISK_CORRECTION_L_PLAN_v0.1.json"
AUDIT_PATH = ROOT / "data/coverage/IMD_HEATWAVE_OUTLOOK_AT_TRANSACTION_AUDIT_v0.1.md"

APPLY_ENV = "WORLD_SIGNALS_APPLY_IMD_OUTLOOK_AT"

PROTECTED = {
    "canonical_schema": SCHEMA_PATH,
    "change_ledger": LEDGER_PATH,
    "biosecurity_overlay": OVERLAY_PATH,
    "monitor_expectations": EXPECTATIONS_PATH,
    "monitor_operations_policy": OPERATIONS_PATH,
    "analysis_schema": ANALYSIS_SCHEMA_PATH,
    "analysis_reviews": REVIEWS_PATH,
    "analysis_evidence": EVIDENCE_PATH,
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def protected_hashes() -> dict[str, str]:
    return {name: sha256(path) for name, path in PROTECTED.items()}


def exact_series_rows(reviews: dict[str, Any]) -> int:
    return sum(
        1
        for review in reviews.get("reviews", [])
        for movement in (review.get("what_moved") or [])
        if movement.get("measurement_precision") == "EXACT_TIMESTAMP_SERIES"
    )


def assertion_id(item: dict[str, Any]) -> str:
    material = "|".join(
        str(item.get(key) or "")
        for key in ("occurrence_id", "series_id", "source_id", "canonical_name", "start_local")
    )
    return "WSA-AT-" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def build_occurrence(plan: dict[str, Any]) -> dict[str, Any]:
    item = plan["occurrence"]
    aid = assertion_id(item)
    return {
        "occurrence_id": item["occurrence_id"],
        "series_id": item["series_id"],
        "external_source_id": None,
        "canonical_name": item["canonical_name"],
        "short_calendar_title": item["short_calendar_title"],
        "category": item["category"],
        "subcategory": item["subcategory"],
        "jurisdiction": item["jurisdiction"],
        "region": item["region"],
        "institution": item["institution"],
        "event_type": item["event_type"],
        "record_class": item["record_class"],
        "certainty_status": item["certainty_status"],
        "activation_mode": item["activation_mode"],
        "lifecycle_status": item["lifecycle_status"],
        "condition_state": "NOT_REQUIRED",
        "condition_description": None,
        "trigger_source_id": None,
        "trigger_assertion_id": None,
        "triggered_at": None,
        "trigger_verification_status": "NOT_APPLICABLE",
        "timing_type": item["timing_type"],
        "start_local": item["start_local"],
        "end_local": None,
        "source_timezone": item["source_timezone"],
        "start_utc": None,
        "end_utc": None,
        "date_earliest": None,
        "date_latest": None,
        "publication_datetime": None,
        "time_precision": item["time_precision"],
        "all_day_semantics": item["all_day_semantics"],
        "reference_period": item["reference_period"],
        "time_status": "NOT_APPLICABLE",
        "time_basis": "NOT_APPLICABLE",
        "source_id": item["source_id"],
        "primary_source_assertion_id": aid,
        "last_successful_assertion_id": aid,
        "status_history": [
            {
                "as_of": "2026-09-06",
                "certainty_status": "CONFIRMED",
                "lifecycle_status": "COMPLETED",
                "evidence": "Dated first-party IMD press release published 31 March 2026."
            }
        ],
        "first_announced_at": None,
        "first_discovered_at": "2026-09-06",
        "last_verified_at": "2026-09-06",
        "next_verification_due": "SOURCE_SPECIFIC",
        "parent_occurrence_id": None,
        "related_occurrence_ids": [],
        "related_documents": [
            {
                "document_type": "OFFICIAL_PRESS_RELEASE",
                "source_id": item["source_id"],
                "title": "Updated Seasonal outlook for hot weather season (April to June) 2026 and Monthly Outlook for April 2026 for the Rainfall and Temperature"
            }
        ],
        "intrinsic_importance": "HIGH",
        "expected_market_sensitivity": "LOW",
        "geopolitical_sensitivity": "LOW",
        "transmission_channels": [
            "public_health",
            "water_resources",
            "power_demand",
            "essential_services",
            "critical_infrastructure",
            "agriculture_food",
            "resource_management"
        ],
        "render_policy": "INCLUDE",
        "visibility_tier": "ANALYST",
        "signal_object_class": item["signal_object_class"],
        "publication_time_semantics": item["publication_time_semantics"],
        "physical_shock_routing": item["physical_shock_routing"],
        "observed_market_response": None,
        "expected_market_sensitivity_basis": "The outlook is a system-relevant risk-information catalyst with potential power, agriculture, water and health transmission; no event-specific market response is asserted.",
        "publication_bundle_type": item["publication_bundle_type"],
        "data_products": copy.deepcopy(item["data_products"]),
        "render_cluster_key": None,
        "calendar_aggregation_policy": "STANDALONE_INFORMATION_CATALYST",
        "coverage_program_id": plan["coverage_program_id"],
        "coverage_repair_reason": "DOMAIN_DIVERSIFICATION_CORRECTION",
        "selection_rationale": "Adds a distinct South Asian heat-risk information catalyst from the competent national meteorological authority; does not create a hazard-season window or future recurrence.",
        "future_schedule_deferred": True,
        "notes": "Publication event only. April-June is forecast/reference scope, not occurrence timing. Forecast verification, realized heatwave impacts and market response are outside this canonical record."
    }


def assert_prestate(plan: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    pre = plan["preconditions"]
    canonical = load(CANONICAL_PATH)
    sources = load(SOURCES_PATH)
    schema = load(SCHEMA_PATH)
    ledger = load(LEDGER_PATH)
    expectations = load(EXPECTATIONS_PATH)
    analysis_schema = load(ANALYSIS_SCHEMA_PATH)
    reviews = load(REVIEWS_PATH)
    evidence = load(EVIDENCE_PATH)

    require(plan["base_main_sha"] == "92bf6cba7506483dd861680924879b1ded0f4ddc", "AT base SHA drifted")
    require((canonical.get("version"), canonical.get("record_count"), len(canonical.get("records", []))) == (pre["canonical_registry_version"], pre["canonical_record_count"], pre["canonical_record_count"]), "AT canonical pre-state mismatch")
    require(schema.get("version") == pre["canonical_schema_version"], "AT canonical schema pre-state mismatch")
    require((sources.get("version"), len(sources.get("sources", []))) == (pre["source_registry_version"], pre["source_registry_count"]), "AT source pre-state mismatch")
    require((ledger.get("version"), len(ledger.get("changes", []))) == (pre["change_ledger_version"], pre["change_ledger_count"]), "AT ledger pre-state mismatch")
    require((expectations.get("version"), len(expectations.get("adapters", []))) == (pre["monitor_expectations_version"], pre["monitor_adapter_count"]), "AT monitor pre-state mismatch")
    require(analysis_schema.get("version") == pre["analysis_schema_version"], "AT Analysis schema pre-state mismatch")
    require((reviews.get("version"), len(reviews.get("reviews", []))) == (pre["analysis_reviews_version"], pre["analysis_review_count"]), "AT Analysis reviews pre-state mismatch")
    require((evidence.get("version"), len(evidence.get("evidence", []))) == (pre["analysis_evidence_version"], pre["analysis_evidence_count"]), "AT Analysis evidence pre-state mismatch")
    require(exact_series_rows(reviews) == pre.get("production_exact_timestamp_series_rows", 0), "AT exact-series pre-state mismatch")

    occurrence_ids = {row.get("occurrence_id") for row in canonical.get("records", [])}
    series_ids = {row.get("series_id") for row in canonical.get("records", [])}
    source_ids = {row.get("source_id") for row in sources.get("sources", [])}
    require(not set(pre["required_absent_occurrence_ids"]) & occurrence_ids, "AT occurrence identity already exists")
    require(not set(pre["required_absent_series_ids"]) & series_ids, "AT series identity already exists")
    require(not set(pre["required_absent_source_ids"]) & source_ids, "AT source identity already exists")

    vocab = schema.get("controlled_vocabularies") or {}
    require("SCHEDULED_INFORMATION_CATALYST" in (vocab.get("signal_object_class") or []), "AT information-catalyst ontology missing")
    require("DATE_ONLY" in (vocab.get("publication_time_semantics") or []), "AT DATE_ONLY semantics missing")
    require("CIVIL_DATE" in (vocab.get("timing_type") or []), "AT CIVIL_DATE timing missing")

    correction_l = load(CORRECTION_L_PLAN_PATH)
    deferred = correction_l.get("deferred_candidates") or []
    require(len(deferred) == 1 and deferred[0].get("candidate_id") == "WSFR-RISK-NIO-TC", "AT lost North Indian Ocean deferred identity")
    require(deferred[0].get("state") == "OFFICIAL_SOURCE_DEFINITION_CONFLICT", "AT North Indian Ocean conflict was weakened")
    assertions = {row.get("assertion") for row in deferred[0].get("assertions", [])}
    require(any("April-June" in str(x) for x in assertions), "AT April-June conflict side missing")
    require(any("April-May" in str(x) for x in assertions), "AT April-May conflict side missing")

    return canonical, sources, schema


def build_post_state(plan: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    canonical, sources, _schema = assert_prestate(plan)
    post = plan["postconditions"]
    out_canonical = copy.deepcopy(canonical)
    out_sources = copy.deepcopy(sources)

    out_sources["sources"].append(copy.deepcopy(plan["source_plan"]))
    out_sources["version"] = post["source_registry_version"]
    out_sources["reference_date"] = plan["reference_date"]

    occurrence = build_occurrence(plan)
    out_canonical["records"].append(occurrence)
    out_canonical["version"] = post["canonical_registry_version"]
    out_canonical["record_count"] = len(out_canonical["records"])
    out_canonical["reference_date"] = plan["reference_date"]

    report = validate_registry(out_canonical, out_sources)
    require(report.ok, "AT candidate canonical validation failed: " + "; ".join(report.errors))

    coverage = build_coverage_audit(out_canonical, out_sources)
    totals = coverage["totals"]
    expected_totals = post["coverage_totals"]
    for key, value in expected_totals.items():
        require(totals.get(key) == value, f"AT coverage total {key} mismatch: {totals.get(key)} != {value}")

    region = next(row for row in coverage["by_region"] if row["region"] == "South Asia")
    for key, value in post["south_asia"].items():
        require(region.get(key) == value, f"AT South Asia {key} mismatch: {region.get(key)} != {value}")

    category = next(row for row in coverage["by_category"] if row["category"] == "PHYSICAL_CLIMATE_RISK")
    for key, value in post["physical_climate_risk"].items():
        require(category.get(key) == value, f"AT physical-risk {key} mismatch: {category.get(key)} != {value}")

    require("South Asia" in coverage["diagnostic_flags"]["regions_with_fewer_than_10_unique_series"], "AT unexpectedly cleared South Asia series prompt")
    require("South Asia" in coverage["diagnostic_flags"]["regions_with_fewer_than_8_unique_institutions"], "AT unexpectedly cleared South Asia institution prompt")
    require("PHYSICAL_CLIMATE_RISK" in coverage["diagnostic_flags"]["categories_with_fewer_than_5_unique_series"], "AT unexpectedly cleared physical-risk prompt")

    row = occurrence
    require(row["event_type"] == "PHYSICAL_RISK_OUTLOOK_RELEASE", "AT event type drifted")
    require(row["signal_object_class"] == "SCHEDULED_INFORMATION_CATALYST", "AT signal object class drifted")
    require(row["start_local"] == "2026-03-31" and row["timing_type"] == "CIVIL_DATE", "AT publication civil date drifted")
    require(row["source_timezone"] == "Asia/Kolkata", "AT source timezone drifted")
    require(row["start_utc"] is None and row["end_utc"] is None, "AT invented UTC timestamp")
    require(row["time_precision"] == "DAY" and row["all_day_semantics"] is True, "AT civil-date precision drifted")
    require(row["lifecycle_status"] == "COMPLETED", "AT lifecycle drifted")
    require(row["publication_time_semantics"] == "DATE_ONLY", "AT publication-time semantics drifted")
    require(row["physical_shock_routing"] == "NO_SHOCK_IN_THIS_RECORD", "AT shock routing drifted")
    require("April–June 2026" in row["reference_period"], "AT forecast reference period lost")
    require(row["end_local"] is None and row["date_earliest"] is None and row["date_latest"] is None, "AT converted forecast scope into event window")

    source = plan["source_plan"]
    require(source["canonical_provenance_use"] == "MANUAL_INFORMATIONAL_REFERENCE_ONLY", "AT source provenance gate drifted")
    require(source["automated_monitoring_use"] == "PROHIBITED_OR_RIGHTS_HOLD", "AT source automation gate drifted")
    require(source["verification_mode"] == "RIGHTS_HELD_MANUAL_ONLY", "AT source verification mode drifted")

    return out_canonical, out_sources, coverage


def render_audit(plan: dict[str, Any], coverage: dict[str, Any], protected_before: dict[str, str], protected_after: dict[str, str]) -> str:
    post = plan["postconditions"]
    return f"""# WORLD SIGNALS — IMD heatwave outlook AT transaction audit v0.1

**Executed:** 2026-09-06
**Exact base:** `{plan['base_main_sha']}`

## Controlled mutation

- Canonical Registry: `v{plan['preconditions']['canonical_registry_version']} / {plan['preconditions']['canonical_record_count']}` → `v{post['canonical_registry_version']} / {post['canonical_record_count']}`
- Source Registry: `v{plan['preconditions']['source_registry_version']} / {plan['preconditions']['source_registry_count']}` → `v{post['source_registry_version']} / {post['source_registry_count']}`
- added occurrence: `WSO-RISK-A-0002`
- added series: `WSER-RISK-IN-HEAT-OUTLOOK`
- added source: `WSSRC-RISK-005`

## Object boundary

The new occurrence is the **31 March 2026 IMD publication event**. It is not an April–June heatwave season and not an observed heatwave shock. The April–June period remains forecast/reference scope only. No publication clock time or UTC timestamp was invented.

`WSFR-RISK-NIO-TC` remains deferred under `OFFICIAL_SOURCE_DEFINITION_CONFLICT`; AT does not choose April–May versus April–June.

## Coverage result

```json
{json.dumps({'totals': coverage['totals'], 'south_asia': next(row for row in coverage['by_region'] if row['region']=='South Asia'), 'physical_climate_risk': next(row for row in coverage['by_category'] if row['category']=='PHYSICAL_CLIMATE_RISK'), 'diagnostic_flags': coverage['diagnostic_flags']}, indent=2)}
```

The South Asia and physical-risk mechanical prompts remain open after the correction. This is intentional; AT is not a threshold-clearing transaction.

## Protected-state audit

Protected datasets unchanged: **{protected_before == protected_after}**

```json
{json.dumps({'before': protected_before, 'after': protected_after}, indent=2)}
```

## Deliberate non-actions

- no canonical-schema mutation
- no Change Ledger mutation
- no biosecurity-overlay mutation
- no monitor configuration or operations-policy mutation
- no Analysis schema/review/evidence mutation
- no `EXACT_TIMESTAMP_SERIES` ingestion
- no future 2027 outlook occurrence
- no North Indian Ocean cyclone-season population
- no automatic canonical commit
- no Google Calendar write
"""


def run_check() -> dict[str, Any]:
    plan = load(PLAN_PATH)
    before = protected_hashes()
    candidate_canonical, candidate_sources, coverage = build_post_state(plan)
    require(protected_hashes() == before, "AT read-only check mutated protected repository state")
    return {
        "status": "PASS",
        "mode": "READ_ONLY_CHECK",
        "canonical_post": [candidate_canonical["version"], candidate_canonical["record_count"]],
        "source_post": [candidate_sources["version"], len(candidate_sources["sources"])],
        "occurrence_id": plan["occurrence"]["occurrence_id"],
        "coverage_totals": coverage["totals"],
        "north_indian_ocean_candidate": "DEFERRED_OFFICIAL_SOURCE_DEFINITION_CONFLICT",
        "automatic_canonical_commit": False,
        "google_calendar_write": False,
    }


def run_write() -> dict[str, Any]:
    require(os.environ.get(APPLY_ENV) == "1", f"AT write requires {APPLY_ENV}=1")
    plan = load(PLAN_PATH)
    protected_before = protected_hashes()
    candidate_canonical, candidate_sources, coverage = build_post_state(plan)

    dump(SOURCES_PATH, candidate_sources)
    dump(CANONICAL_PATH, candidate_canonical)

    protected_after = protected_hashes()
    require(protected_after == protected_before, "AT controlled write mutated protected datasets")

    post_report = validate_registry(load(CANONICAL_PATH), load(SOURCES_PATH))
    require(post_report.ok, "AT written state failed canonical validation: " + "; ".join(post_report.errors))
    written_coverage = build_coverage_audit(load(CANONICAL_PATH), load(SOURCES_PATH))
    require(written_coverage["totals"] == coverage["totals"], "AT written coverage differs from simulated coverage")

    AUDIT_PATH.write_text(render_audit(plan, written_coverage, protected_before, protected_after), encoding="utf-8")
    return {
        "status": "WROTE_CONTROLLED_AT_STATE",
        "canonical_post": [candidate_canonical["version"], candidate_canonical["record_count"]],
        "source_post": [candidate_sources["version"], len(candidate_sources["sources"])],
        "occurrence_id": plan["occurrence"]["occurrence_id"],
        "protected_unchanged": True,
        "automatic_canonical_commit": False,
        "google_calendar_write": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    require(args.check ^ args.write, "choose exactly one of --check or --write")
    result = run_write() if args.write else run_check()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
