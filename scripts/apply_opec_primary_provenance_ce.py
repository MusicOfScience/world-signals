#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.world_signals.analytical_overlays import validate_biosecurity_overlay
from src.world_signals.analysis import validate_analysis
from src.world_signals.live_analysis_bridge import production_live_input_count
from src.world_signals.live_intelligence import validate_live_intelligence
from src.world_signals.validation import validate_registry

PLAN_PATH = ROOT / "data/coverage/OPEC_PRIMARY_PROVENANCE_CE_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
CANONICAL_SCHEMA_PATH = ROOT / "data/canonical/schema.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
MONITOR_PATH = ROOT / "data/monitor/expectations.json"
LIVE_SCHEMA_PATH = ROOT / "data/live_intelligence/schema.json"
LIVE_OBSERVATIONS_PATH = ROOT / "data/live_intelligence/observations.json"
LIVE_EVIDENCE_PATH = ROOT / "data/live_intelligence/evidence_registry.json"
ANALYSIS_SCHEMA_PATH = ROOT / "data/analysis/schema.json"
ANALYSIS_REVIEWS_PATH = ROOT / "data/analysis/event_reviews.json"
ANALYSIS_EVIDENCE_PATH = ROOT / "data/analysis/evidence_registry.json"

TARGET_ID = "WSO-COM-A-0001"
OCTOBER_JMMC_ID = "WSO-COM-A-0002"
OPEC_SOURCE_ID = "WSSRC-COM-001"
REUTERS_SOURCE_ID = "WSSRC-COM-015"
SPA_SOURCE_ID = "WSSRC-COM-016"
APPLY_ENV = "WORLD_SIGNALS_APPLY_OPEC_PRIMARY_PROVENANCE_CE"
APPLY_VALUE = "YES"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def by_occurrence(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row.get("occurrence_id"): row for row in registry.get("records", [])}


def by_source(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row.get("source_id"): row for row in registry.get("sources", [])}


def revision_count(reviews: dict[str, Any]) -> int:
    return sum(1 for row in reviews.get("reviews", []) if row.get("revision_of_analysis_id"))


def load_state() -> dict[str, dict[str, Any]]:
    return {
        "canonical": load(CANONICAL_PATH),
        "canonical_schema": load(CANONICAL_SCHEMA_PATH),
        "sources": load(SOURCES_PATH),
        "ledger": load(LEDGER_PATH),
        "overlay": load(OVERLAY_PATH),
        "monitor": load(MONITOR_PATH),
        "live_schema": load(LIVE_SCHEMA_PATH),
        "live_observations": load(LIVE_OBSERVATIONS_PATH),
        "live_evidence": load(LIVE_EVIDENCE_PATH),
        "analysis_schema": load(ANALYSIS_SCHEMA_PATH),
        "analysis_reviews": load(ANALYSIS_REVIEWS_PATH),
        "analysis_evidence": load(ANALYSIS_EVIDENCE_PATH),
    }


def validate_layers(state: dict[str, dict[str, Any]]) -> None:
    registry = validate_registry(state["canonical"], state["sources"])
    require(registry.ok, "CE Canonical validation failed: " + "; ".join(registry.errors))
    overlay_errors = validate_biosecurity_overlay(state["canonical"], state["overlay"])
    require(not overlay_errors, "CE overlay validation failed: " + "; ".join(overlay_errors))
    live = validate_live_intelligence(
        state["live_schema"], state["live_evidence"], state["live_observations"], state["canonical"]
    )
    require(live.ok, "CE Live validation failed: " + "; ".join(live.errors))
    analysis = validate_analysis(
        state["analysis_schema"], state["analysis_evidence"], state["analysis_reviews"], state["canonical"]
    )
    require(analysis.ok, "CE Analysis validation failed: " + "; ".join(analysis.errors))


def primary_document(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": OPEC_SOURCE_ID,
        "role": plan["provenance_upgrade"]["related_document_role"],
        "source_locator": plan["selection"]["primary_outcome_url"],
        "primary_opec_provenance_state": plan["provenance_upgrade"]["primary_opec_provenance_state"],
    }


def provenance_status_entry(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "as_of": plan["reference_date"],
        "certainty_status": "CONFIRMED",
        "lifecycle_status": "COMPLETED",
        "condition_state": "NOT_REQUIRED",
        "source_assertion_id": plan["provenance_upgrade"]["assertion_id"],
        "primary_provenance_upgrade_state": plan["provenance_upgrade"]["primary_opec_provenance_state"],
        "basis": "Competent OPEC primary outcome statement now directly retrievable; historical Reuters and SPA provenance remains preserved.",
        "change_reason": plan["provenance_upgrade"]["review_reason"],
    }


def ledger_entry(before: dict[str, Any], after: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "change_id": plan["provenance_upgrade"]["change_id"],
        "occurrence_id": TARGET_ID,
        "change_type": plan["provenance_upgrade"]["change_type"],
        "old_values": {
            "lifecycle_status": before["lifecycle_status"],
            "certainty_status": before["certainty_status"],
            "last_successful_assertion_id": before["last_successful_assertion_id"],
            "last_verified_at": before["last_verified_at"],
            "primary_opec_provenance_state": "REQUIRED_WHEN_RETRIEVABLE",
        },
        "new_values": {
            "lifecycle_status": after["lifecycle_status"],
            "certainty_status": after["certainty_status"],
            "last_successful_assertion_id": after["last_successful_assertion_id"],
            "last_verified_at": after["last_verified_at"],
            "competent_primary_source_id": OPEC_SOURCE_ID,
            "competent_primary_source_url": plan["selection"]["primary_outcome_url"],
            "primary_opec_provenance_state": plan["provenance_upgrade"]["primary_opec_provenance_state"],
            "reuters_fallback_preserved": True,
            "spa_supporting_confirmation_preserved": True,
        },
        "source_assertion_id": plan["provenance_upgrade"]["assertion_id"],
        "review_state": "APPROVED_FOR_CANONICAL_COMMIT",
        "reviewed_at": "2026-09-09T20:00:00+10:00",
        "review_basis": [
            plan["selection"]["primary_outcome_url"],
            plan["rights_boundary"]["rights_source_url"],
            plan["provenance_upgrade"]["review_reason"],
            "WSSRC-COM-001 remains the competent OPEC source identity and its rights/automation hold is unchanged.",
            "Reuters WSSRC-COM-015 and SPA WSSRC-COM-016 remain preserved as historical/supporting provenance.",
            "No event clock time is inferred and the civil-date timing is unchanged.",
            "The 4 October seven-country meeting statement is not used to create, merge, rename or mutate WSO-COM-A-0002.",
        ],
        "commit_mode": "REVIEWED_COMPETENT_PRIMARY_PROVENANCE_REPAIR_CE",
        "committed_at": "2026-09-09T20:00:00+10:00",
        "registry_version_before": plan["pre_state"]["canonical_registry_version"],
        "registry_version_after": plan["target_state"]["canonical_registry_version"],
        "canonical_mutation_committed": True,
        "automatic_canonical_commit": False,
        "google_calendar_write": False,
    }


def assert_common_state(state: dict[str, dict[str, Any]], plan: dict[str, Any], *, target: bool) -> None:
    expected = plan["target_state"] if target else plan["pre_state"]
    require(state["canonical_schema"].get("version") == "0.52", "CE canonical schema drift")
    require((state["sources"].get("version"), len(state["sources"].get("sources", []))) == (
        expected["source_registry_version"], expected["source_count"]
    ), "CE Source Registry state drift")
    require((state["monitor"].get("version"), len(state["monitor"].get("adapters", []))) == (
        expected["monitor_version"], expected["monitor_adapter_count"]
    ), "CE Monitor state drift")
    require(state["live_schema"].get("version") == expected["live_schema_version"], "CE Live schema drift")
    require(len(state["live_observations"].get("observations", [])) == expected["live_observation_count"], "CE Live observation drift")
    require(len(state["live_evidence"].get("evidence", [])) == expected["live_evidence_count"], "CE Live evidence drift")
    require(state["analysis_schema"].get("version") == expected["analysis_schema_version"], "CE Analysis schema drift")
    require(len(state["analysis_reviews"].get("reviews", [])) == expected["analysis_review_count"], "CE Analysis review drift")
    require(len(state["analysis_evidence"].get("evidence", [])) == expected["analysis_evidence_count"], "CE Analysis evidence drift")
    require(production_live_input_count(state["analysis_reviews"]) == expected["production_live_input_count"], "CE production Live input drift")
    require(revision_count(state["analysis_reviews"]) == expected["production_analysis_revision_count"], "CE Analysis revision drift")
    validate_layers(state)


def assert_prestate(state: dict[str, dict[str, Any]], plan: dict[str, Any]) -> None:
    pre = plan["pre_state"]
    require((state["canonical"].get("version"), len(state["canonical"].get("records", []))) == (
        pre["canonical_registry_version"], pre["canonical_record_count"]
    ), "CE Canonical prestate drift")
    require((state["ledger"].get("version"), len(state["ledger"].get("changes", []))) == (
        pre["change_ledger_version"], pre["change_ledger_count"]
    ), "CE ledger prestate drift")
    require((state["overlay"].get("version"), state["overlay"].get("canonical_checkpoint")) == (
        pre["biosecurity_overlay_version"], pre["biosecurity_overlay_checkpoint"]
    ), "CE overlay prestate drift")

    occurrences = by_occurrence(state["canonical"])
    target = occurrences.get(TARGET_ID)
    require(target is not None, "CE target occurrence missing")
    for key, value in pre["target"].items():
        require(target.get(key) == value, f"CE target precondition drift: {key}")
    require(OCTOBER_JMMC_ID in occurrences, "CE October JMMC identity missing")

    related = target.get("related_documents", [])
    require(len(related) == 2, "CE expected exactly BE/BG related documents before repair")
    require(related[0].get("source_id") == REUTERS_SOURCE_ID, "CE Reuters history missing")
    require(related[0].get("role") == "COMPLETION_FALLBACK_VERIFICATION_PRIMARY_PENDING", "CE Reuters historical role drift")
    require(related[1].get("source_id") == SPA_SOURCE_ID, "CE SPA history missing")
    require(related[1].get("role") == "OFFICIAL_PARTICIPATING_GOVERNMENT_COMPLETION_CONFIRMATION_PRIMARY_OPEC_PENDING", "CE SPA historical role drift")
    require(primary_document(plan) not in related, "CE primary OPEC document already present")
    require(plan["provenance_upgrade"]["assertion_id"] not in {x.get("source_assertion_id") for x in target.get("status_history", [])}, "CE primary assertion already in status history")
    require(plan["provenance_upgrade"]["change_id"] not in {x.get("change_id") for x in state["ledger"].get("changes", [])}, "CE change already present")

    sources = by_source(state["sources"])
    require({OPEC_SOURCE_ID, REUTERS_SOURCE_ID, SPA_SOURCE_ID}.issubset(sources), "CE OPEC provenance source set incomplete")
    opec = sources[OPEC_SOURCE_ID]
    require(opec.get("automated_retrieval_permission") == plan["rights_boundary"]["automated_retrieval_permission_must_remain"], "CE OPEC retrieval-rights state drift")
    require(opec.get("monitoring_readiness_status") == plan["rights_boundary"]["monitoring_readiness_status_must_remain"], "CE OPEC monitor-rights state drift")
    assert_common_state(state, plan, target=False)


def simulate(state: dict[str, dict[str, Any]], plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    assert_prestate(state, plan)
    out = copy.deepcopy(state)
    target = by_occurrence(out["canonical"])[TARGET_ID]
    target["last_successful_assertion_id"] = plan["provenance_upgrade"]["assertion_id"]
    target["last_verified_at"] = plan["reference_date"]
    target.setdefault("related_documents", []).append(primary_document(plan))
    target.setdefault("status_history", []).append(provenance_status_entry(plan))

    out["canonical"]["version"] = plan["target_state"]["canonical_registry_version"]
    out["canonical"]["reference_date"] = plan["reference_date"]
    out["canonical"]["record_count"] = len(out["canonical"]["records"])

    out["ledger"]["changes"].append(ledger_entry(by_occurrence(state["canonical"])[TARGET_ID], target, plan))
    out["ledger"]["version"] = plan["target_state"]["change_ledger_version"]
    out["ledger"]["reference_date"] = plan["reference_date"]

    out["overlay"]["version"] = plan["target_state"]["biosecurity_overlay_version"]
    out["overlay"]["canonical_checkpoint"] = copy.deepcopy(plan["target_state"]["biosecurity_overlay_checkpoint"])

    assert_poststate(state, out, plan)
    return out


def assert_poststate(before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]], plan: dict[str, Any]) -> None:
    target_state = plan["target_state"]
    require((after["canonical"].get("version"), len(after["canonical"].get("records", []))) == (
        target_state["canonical_registry_version"], target_state["canonical_record_count"]
    ), "CE Canonical target mismatch")
    require((after["ledger"].get("version"), len(after["ledger"].get("changes", []))) == (
        target_state["change_ledger_version"], target_state["change_ledger_count"]
    ), "CE ledger target mismatch")
    require((after["overlay"].get("version"), after["overlay"].get("canonical_checkpoint")) == (
        target_state["biosecurity_overlay_version"], target_state["biosecurity_overlay_checkpoint"]
    ), "CE overlay checkpoint target mismatch")

    require(before["sources"] == after["sources"], "CE changed Source Registry")
    require(before["monitor"] == after["monitor"], "CE changed Monitor")
    require(before["live_schema"] == after["live_schema"], "CE changed Live schema")
    require(before["live_observations"] == after["live_observations"], "CE changed Live observations")
    require(before["live_evidence"] == after["live_evidence"], "CE changed Live evidence")
    require(before["analysis_schema"] == after["analysis_schema"], "CE changed Analysis schema")
    require(before["analysis_reviews"] == after["analysis_reviews"], "CE changed Analysis reviews")
    require(before["analysis_evidence"] == after["analysis_evidence"], "CE changed Analysis evidence")

    before_overlay = {k: v for k, v in before["overlay"].items() if k not in {"version", "canonical_checkpoint"}}
    after_overlay = {k: v for k, v in after["overlay"].items() if k not in {"version", "canonical_checkpoint"}}
    require(before_overlay == after_overlay, "CE changed overlay semantics")

    c0 = by_occurrence(before["canonical"])
    c1 = by_occurrence(after["canonical"])
    require(list(c0) == list(c1), "CE changed Canonical identity/order")
    changed_ids = [oid for oid in c0 if c0[oid] != c1[oid]]
    require(changed_ids == [TARGET_ID], f"CE changed unexpected Canonical occurrences: {changed_ids}")
    t0, t1 = c0[TARGET_ID], c1[TARGET_ID]
    changed_fields = {k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
    require(changed_fields == {"last_successful_assertion_id", "last_verified_at", "related_documents", "status_history"}, f"CE target mutation scope drift: {changed_fields}")

    for key in [
        "occurrence_id", "series_id", "source_id", "canonical_name", "category", "event_type",
        "lifecycle_status", "certainty_status", "condition_state", "start_local", "start_utc",
        "source_timezone", "timing_type", "time_precision", "time_status", "primary_source_assertion_id",
        "intrinsic_importance", "expected_market_sensitivity", "observed_market_response",
    ]:
        require(t0.get(key) == t1.get(key), f"CE changed protected target field {key}")

    require(t1["last_successful_assertion_id"] == plan["provenance_upgrade"]["assertion_id"], "CE assertion target mismatch")
    require(t1["last_verified_at"] == plan["reference_date"], "CE verification date mismatch")
    require(t1["related_documents"][:-1] == t0["related_documents"], "CE rewrote historical related documents")
    require(t1["related_documents"][-1] == primary_document(plan), "CE primary related document mismatch")
    require(t1["status_history"][:-1] == t0["status_history"], "CE rewrote historical status history")
    require(t1["status_history"][-1] == provenance_status_entry(plan), "CE provenance status entry mismatch")

    require(c0[OCTOBER_JMMC_ID] == c1[OCTOBER_JMMC_ID], "CE mutated October JMMC occurrence")
    require(after["ledger"]["changes"][:-1] == before["ledger"]["changes"], "CE rewrote ledger history")
    require(after["ledger"]["changes"][-1]["change_id"] == plan["provenance_upgrade"]["change_id"], "CE ledger append mismatch")

    assert_common_state(after, plan, target=True)


def apply(plan: dict[str, Any]) -> None:
    require(os.environ.get(APPLY_ENV) == APPLY_VALUE, f"CE apply requires {APPLY_ENV}={APPLY_VALUE}")
    before = load_state()
    after = simulate(before, plan)
    dump(CANONICAL_PATH, after["canonical"])
    dump(LEDGER_PATH, after["ledger"])
    dump(OVERLAY_PATH, after["overlay"])
    reloaded = load_state()
    assert_poststate(before, reloaded, plan)
    print("CE OPEC primary provenance repair materialised")


def check(plan: dict[str, Any]) -> None:
    state = load_state()
    if state["canonical"].get("version") == plan["pre_state"]["canonical_registry_version"]:
        simulate(state, plan)
        print("CE prestate and simulated target PASS")
        return
    require(state["canonical"].get("version") == plan["target_state"]["canonical_registry_version"], "CE neither prestate nor target state")
    target = by_occurrence(state["canonical"])[TARGET_ID]
    require(target.get("last_successful_assertion_id") == plan["provenance_upgrade"]["assertion_id"], "CE materialised assertion missing")
    require(target.get("last_verified_at") == plan["reference_date"], "CE materialised verification date missing")
    require(primary_document(plan) in target.get("related_documents", []), "CE materialised primary document missing")
    require(provenance_status_entry(plan) in target.get("status_history", []), "CE materialised provenance status missing")
    require(plan["provenance_upgrade"]["change_id"] in {x.get("change_id") for x in state["ledger"].get("changes", [])}, "CE materialised ledger entry missing")
    require((state["overlay"].get("version"), state["overlay"].get("canonical_checkpoint")) == (
        plan["target_state"]["biosecurity_overlay_version"], plan["target_state"]["biosecurity_overlay_checkpoint"]
    ), "CE materialised overlay checkpoint mismatch")
    assert_common_state(state, plan, target=True)
    print("CE materialised target PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    require(args.apply ^ args.check, "choose exactly one of --apply or --check")
    plan = load(PLAN_PATH)
    if args.apply:
        apply(plan)
    else:
        check(plan)


if __name__ == "__main__":
    main()
