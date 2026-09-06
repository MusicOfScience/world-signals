#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
from datetime import datetime
import json
import os
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.world_signals.analytical_overlays import validate_biosecurity_overlay
from src.world_signals.analysis import analysis_population_readiness, validate_analysis
from src.world_signals.live_analysis_bridge import production_live_input_count
from src.world_signals.live_intelligence import validate_live_intelligence
from src.world_signals.validation import validate_registry

CANONICAL_PATH = ROOT / "data/canonical/registry.json"
CANONICAL_SCHEMA_PATH = ROOT / "data/canonical/schema.json"
SOURCE_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
OPERATIONS_PATH = ROOT / "data/monitor/operations_policy.json"
REVIEW_CONTRACT_PATH = ROOT / "data/monitor/review_candidate_state_contract.json"
REVIEW_DECISIONS_PATH = ROOT / "data/monitor/review_decisions.json"
LIVE_SCHEMA_PATH = ROOT / "data/live_intelligence/schema.json"
LIVE_OBSERVATIONS_PATH = ROOT / "data/live_intelligence/observations.json"
LIVE_EVIDENCE_PATH = ROOT / "data/live_intelligence/evidence_registry.json"
ANALYSIS_SCHEMA_PATH = ROOT / "data/analysis/schema.json"
ANALYSIS_REVIEWS_PATH = ROOT / "data/analysis/event_reviews.json"
ANALYSIS_EVIDENCE_PATH = ROOT / "data/analysis/evidence_registry.json"
STATUS_PATH = ROOT / "PROJECT_STATUS.md"
ROADMAP_PATH = ROOT / "ROADMAP.md"
PLAN_PATH = ROOT / "data/coverage/OPEC_OFFICIAL_CONFIRMATION_BG_PLAN_v0.1.json"

APPLY_ENV = "WORLD_SIGNALS_APPLY_OPEC_OFFICIAL_CONFIRMATION_BG"
APPLY_VALUE = "YES"
TARGET_ID = "WSO-COM-A-0001"
SPA_SOURCE_ID = "WSSRC-COM-016"
REUTERS_SOURCE_ID = "WSSRC-COM-015"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def now_melbourne() -> str:
    return datetime.now(ZoneInfo("Australia/Melbourne")).isoformat(timespec="seconds")


def by_occurrence(registry: dict) -> dict[str, dict]:
    return {row.get("occurrence_id"): row for row in registry.get("records", [])}


def by_source(sources: dict) -> dict[str, dict]:
    return {row.get("source_id"): row for row in sources.get("sources", [])}


def overlay_semantics(value: dict) -> dict:
    return {k: copy.deepcopy(v) for k, v in value.items() if k not in {"version", "canonical_checkpoint"}}


def analysis_revision_count(reviews: dict) -> int:
    return sum(1 for row in reviews.get("reviews", []) if row.get("revision_of_analysis_id"))


def exact_series_count(reviews: dict) -> int:
    return sum(
        1
        for review in reviews.get("reviews", [])
        for moved in (review.get("what_moved") or [])
        if moved.get("measurement_precision") == "EXACT_TIMESTAMP_SERIES"
    )


def load_all() -> dict[str, dict]:
    return {
        "canonical": load(CANONICAL_PATH),
        "canonical_schema": load(CANONICAL_SCHEMA_PATH),
        "sources": load(SOURCE_PATH),
        "ledger": load(LEDGER_PATH),
        "overlay": load(OVERLAY_PATH),
        "expectations": load(EXPECTATIONS_PATH),
        "operations": load(OPERATIONS_PATH),
        "review_contract": load(REVIEW_CONTRACT_PATH),
        "review_decisions": load(REVIEW_DECISIONS_PATH),
        "live_schema": load(LIVE_SCHEMA_PATH),
        "live_observations": load(LIVE_OBSERVATIONS_PATH),
        "live_evidence": load(LIVE_EVIDENCE_PATH),
        "analysis_schema": load(ANALYSIS_SCHEMA_PATH),
        "analysis_reviews": load(ANALYSIS_REVIEWS_PATH),
        "analysis_evidence": load(ANALYSIS_EVIDENCE_PATH),
    }


def validate_layers(state: dict[str, dict]) -> None:
    registry = validate_registry(state["canonical"], state["sources"])
    require(registry.ok, "Canonical validation failed: " + "; ".join(registry.errors))
    overlay = validate_biosecurity_overlay(state["canonical"], state["overlay"])
    require(overlay.ok, "Biosecurity validation failed: " + "; ".join(overlay.errors))
    live = validate_live_intelligence(
        state["live_schema"], state["live_evidence"], state["live_observations"], state["canonical"]
    )
    require(live.ok, "Live Intelligence validation failed: " + "; ".join(live.errors))
    analysis = validate_analysis(
        state["analysis_schema"], state["analysis_evidence"], state["analysis_reviews"], state["canonical"]
    )
    require(analysis.ok, "Analysis validation failed: " + "; ".join(analysis.errors))


def exact_subset(row: dict, expected: dict, label: str) -> None:
    for key, value in expected.items():
        require(row.get(key) == value, f"{label} {key}: expected {value!r}, found {row.get(key)!r}")


def fallback_document(row: dict) -> dict | None:
    for doc in row.get("related_documents", []):
        if doc.get("source_id") == REUTERS_SOURCE_ID:
            return doc
    return None


def spa_document(row: dict) -> dict | None:
    for doc in row.get("related_documents", []):
        if doc.get("source_id") == SPA_SOURCE_ID:
            return doc
    return None


def materialised(state: dict[str, dict], plan: dict) -> bool:
    target = by_occurrence(state["canonical"]).get(TARGET_ID)
    spa = by_source(state["sources"]).get(SPA_SOURCE_ID)
    if target is None:
        return False
    evidence_present = spa is not None or spa_document(target) is not None
    if not evidence_present:
        return False
    require(spa is not None and spa_document(target) is not None, "BG partial materialisation detected")
    require(
        target.get("last_successful_assertion_id") == plan["provenance_basis"]["assertion_id"],
        "BG partial materialisation: target assertion does not match SPA",
    )
    return True


def assert_preconditions(state: dict[str, dict], plan: dict) -> None:
    p = plan["preconditions"]
    canonical = state["canonical"]
    sources = state["sources"]
    ledger = state["ledger"]
    overlay = state["overlay"]
    checks = [
        (str(state["canonical_schema"].get("version")) == p["canonical_schema_version"], "canonical schema drift"),
        (str(canonical.get("version")) == p["canonical_registry_version"], "canonical version drift"),
        (canonical.get("record_count") == p["canonical_record_count"] == len(canonical.get("records", [])), "canonical population drift"),
        (str(sources.get("version")) == p["source_registry_version"], "source version drift"),
        (len(sources.get("sources", [])) == p["source_record_count"], "source population drift"),
        (str(ledger.get("version")) == p["change_ledger_version"], "ledger version drift"),
        (len(ledger.get("changes", [])) == p["change_ledger_count"], "ledger population drift"),
        (str(overlay.get("version")) == p["biosecurity_overlay_version"], "overlay version drift"),
        (overlay.get("canonical_checkpoint") == p["biosecurity_overlay_checkpoint"], "overlay checkpoint drift"),
        (str(state["expectations"].get("version")) == p["monitor_expectations_version"], "monitor expectations drift"),
        (len(state["expectations"].get("adapters", [])) == p["monitor_adapter_count"], "monitor adapter count drift"),
        (str(state["live_schema"].get("version")) == p["live_schema_version"], "Live schema drift"),
        (len(state["live_observations"].get("observations", [])) == p["live_observation_count"], "Live observation drift"),
        (len(state["live_evidence"].get("evidence", [])) == p["live_evidence_count"], "Live evidence drift"),
        (str(state["analysis_schema"].get("version")) == p["analysis_schema_version"], "Analysis schema drift"),
        (str(state["analysis_reviews"].get("version")) == p["analysis_reviews_version"], "Analysis reviews version drift"),
        (len(state["analysis_reviews"].get("reviews", [])) == p["analysis_review_count"], "Analysis review drift"),
        (str(state["analysis_evidence"].get("version")) == p["analysis_evidence_version"], "Analysis evidence version drift"),
        (len(state["analysis_evidence"].get("evidence", [])) == p["analysis_evidence_count"], "Analysis evidence drift"),
        (production_live_input_count(state["analysis_reviews"]) == p["production_live_input_count"], "production live_inputs drift"),
        (analysis_revision_count(state["analysis_reviews"]) == p["production_analysis_revision_count"], "Analysis revision drift"),
        (exact_series_count(state["analysis_reviews"]) == p["production_exact_timestamp_series_count"], "exact timestamp series drift"),
    ]
    for ok, message in checks:
        require(ok, f"BG PRECONDITION FAILED: {message}")

    target = by_occurrence(canonical).get(TARGET_ID)
    require(target is not None, f"BG PRECONDITION FAILED: missing {TARGET_ID}")
    exact_subset(target, p["target"], f"BG target {TARGET_ID}")
    require(
        fallback_document(target) is not None,
        "BG PRECONDITION FAILED: BE Reuters fallback related document missing",
    )
    require(
        fallback_document(target).get("role") == p["required_fallback_related_document_role"],
        "BG PRECONDITION FAILED: BE fallback role drift",
    )
    sources_by_id = by_source(sources)
    for sid in p["required_present_source_ids"]:
        require(sid in sources_by_id, f"BG PRECONDITION FAILED: missing source {sid}")
    for sid in p["required_absent_source_ids"]:
        require(sid not in sources_by_id, f"BG PRECONDITION FAILED: source already present {sid}")
    change_id = plan["provenance_basis"]["change_id"]
    require(
        change_id not in {row.get("change_id") for row in ledger.get("changes", [])},
        "BG PRECONDITION FAILED: change identity already present",
    )
    readiness = analysis_population_readiness(state["analysis_schema"], state["analysis_reviews"], canonical)
    require(readiness["eligible_completed_occurrence_count"] == 22, "BG PRECONDITION FAILED: eligible Analysis population drift")
    require(readiness["reviewed_occurrence_count"] == 21, "BG PRECONDITION FAILED: reviewed Analysis population drift")
    validate_layers(state)


def build_ledger_entry(before: dict, after: dict, plan: dict, committed_at: str) -> dict:
    basis = plan["provenance_basis"]
    selection = plan["selection"]
    return {
        "change_id": basis["change_id"],
        "occurrence_id": TARGET_ID,
        "change_type": basis["change_type"],
        "old_values": {
            "lifecycle_status": before.get("lifecycle_status"),
            "last_successful_assertion_id": before.get("last_successful_assertion_id"),
            "completion_provenance_source_id": REUTERS_SOURCE_ID,
            "primary_opec_provenance_state": "REQUIRED_WHEN_RETRIEVABLE",
        },
        "new_values": {
            "lifecycle_status": after.get("lifecycle_status"),
            "last_successful_assertion_id": after.get("last_successful_assertion_id"),
            "official_confirmation_source_id": SPA_SOURCE_ID,
            "official_confirmation_source_url": selection["official_confirmation_url"],
            "official_confirmation_source_class": selection["official_confirmation_class"],
            "reuters_fallback_preserved": True,
            "primary_opec_provenance_state": basis["primary_opec_provenance_state"],
        },
        "source_assertion_id": basis["assertion_id"],
        "review_state": "APPROVED_FOR_CANONICAL_COMMIT",
        "reviewed_at": committed_at,
        "review_basis": [
            selection["official_confirmation_url"],
            selection["official_schedule_notice_url"],
            selection["official_primary_index_url"],
            basis["review_reason"],
            "SPA is official participating-government confirmation and outranks a reputable newswire for this supporting factual proposition, but it is not promoted to competent OPEC issuing authority.",
            "The Reuters fallback remains preserved because it was the evidence used for the BE lifecycle completion.",
            "SPA publication time is publication metadata only and does not become canonical event time.",
            "No future occurrence is created from SPA and all automatic-write gates remain closed.",
        ],
        "commit_mode": "REVIEWED_OFFICIAL_CONFIRMATION_PROVENANCE_STRENGTHENING_BG",
        "committed_at": committed_at,
        "registry_version_before": plan["preconditions"]["canonical_registry_version"],
        "registry_version_after": plan["postconditions"]["canonical_registry_version"],
        "canonical_mutation_committed": True,
        "automatic_canonical_commit": False,
        "google_calendar_write": False,
    }


def build_post_state(state: dict[str, dict], plan: dict, committed_at: str) -> dict[str, dict]:
    assert_preconditions(state, plan)
    out = copy.deepcopy(state)
    post = plan["postconditions"]
    target_before = by_occurrence(state["canonical"])[TARGET_ID]
    target_after = by_occurrence(out["canonical"])[TARGET_ID]
    target_after["last_successful_assertion_id"] = plan["provenance_basis"]["assertion_id"]
    target_after.setdefault("related_documents", []).append({
        "source_id": SPA_SOURCE_ID,
        "role": plan["provenance_basis"]["related_document_role"],
        "source_locator": plan["selection"]["official_confirmation_url"],
        "primary_opec_provenance_state": plan["provenance_basis"]["primary_opec_provenance_state"],
    })

    out["canonical"]["version"] = post["canonical_registry_version"]
    out["canonical"]["reference_date"] = plan["reference_date"]
    out["canonical"]["record_count"] = len(out["canonical"]["records"])

    out["sources"]["sources"].append(copy.deepcopy(plan["official_confirmation_source"]))
    out["sources"]["version"] = post["source_registry_version"]
    out["sources"]["reference_date"] = plan["reference_date"]

    out["ledger"]["changes"].append(build_ledger_entry(target_before, target_after, plan, committed_at))
    out["ledger"]["version"] = post["change_ledger_version"]
    out["ledger"]["reference_date"] = plan["reference_date"]

    out["overlay"]["version"] = post["biosecurity_overlay_version"]
    out["overlay"]["canonical_checkpoint"] = copy.deepcopy(post["biosecurity_overlay_checkpoint"])

    validate_post_state(state, out, plan)
    return out


def validate_post_state(before: dict[str, dict], after: dict[str, dict], plan: dict) -> None:
    post = plan["postconditions"]
    require(
        (str(after["canonical"].get("version")), after["canonical"].get("record_count"), len(after["canonical"].get("records", [])))
        == (post["canonical_registry_version"], post["canonical_record_count"], post["canonical_record_count"]),
        "BG canonical post-state mismatch",
    )
    require(
        (str(after["sources"].get("version")), len(after["sources"].get("sources", [])))
        == (post["source_registry_version"], post["source_record_count"]),
        "BG source post-state mismatch",
    )
    require(
        (str(after["ledger"].get("version")), len(after["ledger"].get("changes", [])))
        == (post["change_ledger_version"], post["change_ledger_count"]),
        "BG ledger post-state mismatch",
    )
    require(
        str(after["overlay"].get("version")) == post["biosecurity_overlay_version"]
        and after["overlay"].get("canonical_checkpoint") == post["biosecurity_overlay_checkpoint"],
        "BG overlay checkpoint mismatch",
    )
    require(overlay_semantics(before["overlay"]) == overlay_semantics(after["overlay"]), "BG changed biosecurity semantics")

    c0, c1 = by_occurrence(before["canonical"]), by_occurrence(after["canonical"])
    require(list(c0) == list(c1), "BG changed Canonical occurrence identity/order")
    changed = [oid for oid in c0 if c0[oid] != c1[oid]]
    require(changed == [TARGET_ID], f"BG unexpected Canonical row mutations: {changed}")
    t0, t1 = c0[TARGET_ID], c1[TARGET_ID]
    changed_fields = {k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
    require(
        changed_fields.issubset({"last_successful_assertion_id", "related_documents"}),
        f"BG changed protected target fields: {sorted(changed_fields)}",
    )
    for key in (
        "occurrence_id", "series_id", "source_id", "canonical_name", "category", "event_type",
        "certainty_status", "lifecycle_status", "start_local", "end_local", "start_utc", "end_utc",
        "source_timezone", "timing_type", "time_precision", "time_status", "time_basis",
        "primary_source_assertion_id", "intrinsic_importance", "expected_market_sensitivity",
        "geopolitical_sensitivity", "status_history", "last_verified_at"
    ):
        require(t0.get(key) == t1.get(key), f"BG protected target field changed: {key}")
    require(t1.get("lifecycle_status") == "COMPLETED", "BG regressed OPEC lifecycle")
    require(t1.get("start_utc") is None, "BG fabricated OPEC event timestamp")
    require(fallback_document(t1) == fallback_document(t0), "BG rewrote Reuters fallback history")
    spa = spa_document(t1)
    require(spa is not None, "BG SPA related document missing")
    require(spa.get("primary_opec_provenance_state") == "REQUIRED_WHEN_RETRIEVABLE", "BG falsely closed OPEC primary gap")
    require(t1.get("last_successful_assertion_id") == plan["provenance_basis"]["assertion_id"], "BG SPA assertion not selected")

    s0, s1 = by_source(before["sources"]), by_source(after["sources"])
    for sid, row in s0.items():
        require(s1.get(sid) == row, f"BG changed pre-existing source {sid}")
    require(s1.get(SPA_SOURCE_ID) == plan["official_confirmation_source"], "BG SPA source row mismatch")
    require(s1[SPA_SOURCE_ID].get("canonical_dependency_count") == 0, "BG SPA source gained Canonical schedule dependency")
    require(s1[SPA_SOURCE_ID].get("automated_monitoring_use") == "PROHIBITED_OR_RIGHTS_HOLD", "BG opened SPA monitoring gate")

    old_changes = before["ledger"].get("changes", [])
    new_changes = after["ledger"].get("changes", [])
    require(new_changes[:len(old_changes)] == old_changes, "BG rewrote Change Ledger history")
    added = new_changes[len(old_changes):]
    require(len(added) == 1 and added[0].get("change_id") == plan["provenance_basis"]["change_id"], "BG Change Ledger scope mismatch")
    require(added[0].get("change_type") == "SOURCE_PROVENANCE_STRENGTHENING", "BG Change Ledger type drift")
    require(added[0].get("new_values", {}).get("primary_opec_provenance_state") == "REQUIRED_WHEN_RETRIEVABLE", "BG ledger falsely closes OPEC primary gap")

    for key in (
        "canonical_schema", "expectations", "operations", "review_contract", "review_decisions",
        "live_schema", "live_observations", "live_evidence", "analysis_schema", "analysis_reviews", "analysis_evidence"
    ):
        require(before[key] == after[key], f"BG mutated protected logical layer {key}")

    readiness = analysis_population_readiness(after["analysis_schema"], after["analysis_reviews"], after["canonical"])
    require(readiness["eligible_completed_occurrence_count"] == 22, "BG changed eligible Analysis population")
    require(readiness["reviewed_occurrence_count"] == 21, "BG changed reviewed Analysis population")
    require(22 - 21 == post["completed_unreviewed_analysis_anchor_count"], "BG completed/unreviewed arithmetic mismatch")
    require(production_live_input_count(after["analysis_reviews"]) == post["production_live_input_count"], "BG changed production live_inputs")
    require(analysis_revision_count(after["analysis_reviews"]) == post["production_analysis_revision_count"], "BG changed Analysis revisions")
    require(exact_series_count(after["analysis_reviews"]) == post["production_exact_timestamp_series_count"], "BG changed exact timestamp series")

    for row in after["canonical"].get("records", []):
        if row.get("series_id") == plan["selection"]["series_id"] and str(row.get("start_local", "")).startswith("2026-10-04"):
            raise SystemExit("BG created prohibited 4 October voluntary-adjustment occurrence")

    validate_layers(after)


def validate_materialised_current(state: dict[str, dict], plan: dict) -> None:
    post = plan["postconditions"]
    require(str(state["canonical"].get("version")) >= post["canonical_registry_version"], "BG materialised Canonical version regressed")
    require(len(state["canonical"].get("records", [])) >= post["canonical_record_count"], "BG materialised Canonical count regressed")
    require(str(state["sources"].get("version")) >= post["source_registry_version"], "BG materialised Source version regressed")
    require(len(state["sources"].get("sources", [])) >= post["source_record_count"], "BG materialised Source count regressed")
    target = by_occurrence(state["canonical"])[TARGET_ID]
    require(target.get("lifecycle_status") == "COMPLETED", "BG materialised lifecycle regressed")
    require(target.get("start_local") == "2026-09-06" and target.get("start_utc") is None, "BG materialised event time drift")
    require(fallback_document(target) is not None, "BG materialised Reuters history missing")
    require(spa_document(target) is not None, "BG materialised SPA evidence missing")
    require(spa_document(target).get("primary_opec_provenance_state") == "REQUIRED_WHEN_RETRIEVABLE", "BG materialised primary gap falsely closed")
    require(by_source(state["sources"]).get(SPA_SOURCE_ID) == plan["official_confirmation_source"], "BG materialised SPA source drift")
    require(plan["provenance_basis"]["change_id"] in {x.get("change_id") for x in state["ledger"].get("changes", [])}, "BG materialised ledger entry missing")
    validate_layers(state)


def target_status(current: str, plan: dict) -> str:
    marker = "\n---\n\n# WORLD SIGNALS — project status / branch-recovery checkpoint"
    require(marker in current, "BG status historical-body marker missing")
    historical = current.split(marker, 1)[1]
    p = plan["postconditions"]
    override = f'''# CURRENT RECOVERY OVERRIDE — POST-BF / BG OPEC OFFICIAL-CONFIRMATION PROVENANCE STRENGTHENING

**Effective checkpoint:** 2026-09-07
**Exact post-BF main base:** `{plan['exact_base_main_sha']}`

This override supersedes stale "current" counts in the historical body below while preserving that body as an audit/recovery record. `WORLD_SIGNALS_PROJECT_CHARTER.md` remains authoritative; governed registry/contract files remain operational truth.

## Current governed state

- Canonical Registry: **v{p['canonical_registry_version']} / {p['canonical_record_count']} occurrences**
- Canonical schema: **v0.52**
- Source Registry: **v{p['source_registry_version']} / {p['source_record_count']} sources**
- reviewed Change Ledger: **v{p['change_ledger_version']} / {p['change_ledger_count']} entries**
- biosecurity overlay: **v{p['biosecurity_overlay_version']} @ canonical v{p['canonical_registry_version']} / {p['canonical_record_count']}**
- Source/Change Monitor expectations: **v0.10 / 8 configured adapters**
- Monitor operations policy: **v0.1**
- Live Intelligence: **v0.6 / 6 reviewed internal observations / 9 primary-official evidence rows / public observation projection CLOSED**
- Analysis schema: **v0.7**
- Analysis: **v0.17 / 21 reviews / 95 evidence / 18 reviewed event types**
- completed Analysis-eligible occurrences: **22**
- completed/unreviewed Analysis-eligible occurrences: **1** (`WSO-COM-A-0001`; not a population target)
- production `live_inputs`: **1 / public projection CLOSED**
- production Analysis revisions: **0 / gate CLOSED / public revision metadata projection CLOSED**
- production `EXACT_TIMESTAMP_SERIES`: **0**
- automatic canonical commit: **OFF / gate closed**
- Google Calendar writes: **OFF**

## Current architecture decision

BG strengthens the completion provenance of the already-completed **6 September 2026 OPEC+ voluntary-adjustment review** (`WSO-COM-A-0001`) with official Saudi Press Agency confirmation that the seven participating countries met and maintained September production requirements for October. SPA is retained as official participating-government confirmation, not promoted to the competent OPEC issuing authority.

BE's Reuters fallback `WSSRC-COM-015` remains preserved in history because it supported the reviewed lifecycle completion. `WSSRC-COM-001` remains the OPEC schedule/decision authority, and the competent OPEC outcome-provenance requirement remains `REQUIRED_WHEN_RETRIEVABLE`. BG changes no event date, lifecycle, certainty or event time and creates no October occurrence.

BF remains the sixth Live specimen. AZ remains the only production `live_input`; BA's Analysis revision grammar remains production-closed. Public Live projection, automatic ingestion, automatic Canonical commit and Google Calendar writes remain closed.

## Current configured monitor cohort

Eight configured adapters: RBA FSR; Colombia SUIN/Socrata; EU CRA/Cellar; three EU CBAM legal-rule routes; ONS release-calendar RSS; EIA WPSR schedule. Route presence does not imply blanket source automation permission, and all routes remain review-only with automatic canonical commit disabled.

## Recovery order

1. `WORLD_SIGNALS_PROJECT_CHARTER.md`
2. this current override
3. `data/canonical/registry.json`, `data/sources/registry.json`, `data/monitor/*`, `data/live_intelligence/*`, `data/analysis/*`
4. latest pressure/transaction audits
5. current `main` SHA and Actions runs
---

# WORLD SIGNALS — project status / branch-recovery checkpoint'''
    return override + historical.split("# WORLD SIGNALS — project status / branch-recovery checkpoint", 1)[1]


def target_roadmap(current: str) -> str:
    heading = "### BG — OPEC official participating-government provenance strengthening — DONE / OPEC PRIMARY STILL PENDING"
    if heading in current:
        return current
    needle = "Public observation projection, automatic ingestion, automatic story clustering, automatic Canonical commit and Google Calendar writes remain closed. A seventh Live observation requires another pressure audit.\n## Stage 8 — prospective Live Intelligence → Analysis linkage"
    require(needle in current, "BG roadmap insertion point missing")
    section = '''Public observation projection, automatic ingestion, automatic story clustering, automatic Canonical commit and Google Calendar writes remain closed. A seventh Live observation requires another pressure audit.\n\n### BG — OPEC official participating-government provenance strengthening — DONE / OPEC PRIMARY STILL PENDING\n\nBG strengthens BE's completion provenance for `WSO-COM-A-0001` with Saudi Press Agency official confirmation that the seven participating OPEC+ countries met on 6 September and maintained September production requirements for October. SPA outranks the Reuters fallback for supporting official confirmation but is not the competent OPEC issuing institution.\n\nReuters `WSSRC-COM-015` remains preserved as the evidence used for BE completion; `WSSRC-COM-001` remains OPEC schedule/decision authority; the competent OPEC outcome source remains `REQUIRED_WHEN_RETRIEVABLE`. BG changes no lifecycle, event date/time, Live observation, Analysis packet, bridge relationship or automation gate and creates no October occurrence from SPA.\n\n## Stage 8 — prospective Live Intelligence → Analysis linkage'''
    return current.replace(needle, section, 1)


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check-only", action="store_true")
    group.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    plan = load(PLAN_PATH)
    state = load_all()
    if materialised(state, plan):
        validate_materialised_current(state, plan)
        target_status(STATUS_PATH.read_text(encoding="utf-8"), plan)
        target_roadmap(ROADMAP_PATH.read_text(encoding="utf-8"))
        print("BG official-confirmation provenance target already materialised and valid")
        return

    committed_at = now_melbourne()
    target = build_post_state(state, plan, committed_at)
    target_status_text = target_status(STATUS_PATH.read_text(encoding="utf-8"), plan)
    target_roadmap_text = target_roadmap(ROADMAP_PATH.read_text(encoding="utf-8"))

    if args.check_only:
        print(
            "BG check-only PASS: would strengthen WSO-COM-A-0001 provenance with SPA; "
            "Canonical v0.41/689, Sources v1.83/246, Ledger v0.27/62; OPEC primary still pending"
        )
        return

    require(os.environ.get(APPLY_ENV) == APPLY_VALUE, f"BG write gate closed: set {APPLY_ENV}={APPLY_VALUE}")
    dump(CANONICAL_PATH, target["canonical"])
    dump(SOURCE_PATH, target["sources"])
    dump(LEDGER_PATH, target["ledger"])
    dump(OVERLAY_PATH, target["overlay"])
    STATUS_PATH.write_text(target_status_text, encoding="utf-8")
    ROADMAP_PATH.write_text(target_roadmap_text, encoding="utf-8")
    print("BG controlled materialisation complete")


if __name__ == "__main__":
    main()
