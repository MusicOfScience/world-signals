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

PLAN_PATH = ROOT / "data/coverage/OPEC_OFFICIAL_CONFIRMATION_BG_PLAN_v0.1.json"
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

APPLY_ENV = "WORLD_SIGNALS_APPLY_OPEC_OFFICIAL_CONFIRMATION_BG"
TARGET_ID = "WSO-COM-A-0001"
SPA_ID = "WSSRC-COM-016"
REUTERS_ID = "WSSRC-COM-015"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(message)


def by_occurrence(registry: dict) -> dict[str, dict]:
    return {r.get("occurrence_id"): r for r in registry.get("records", [])}


def by_source(registry: dict) -> dict[str, dict]:
    return {r.get("source_id"): r for r in registry.get("sources", [])}


def related(row: dict, source_id: str) -> dict | None:
    rows = [x for x in row.get("related_documents", []) if x.get("source_id") == source_id]
    require(len(rows) <= 1, f"BG duplicate related document {source_id}")
    return rows[0] if rows else None


def revision_count(reviews: dict) -> int:
    return sum(bool(x.get("revision_of_analysis_id")) for x in reviews.get("reviews", []))


def exact_series_count(reviews: dict) -> int:
    return sum(
        1 for review in reviews.get("reviews", []) for moved in (review.get("what_moved") or [])
        if moved.get("measurement_precision") == "EXACT_TIMESTAMP_SERIES"
    )


def load_state() -> dict[str, dict]:
    return {
        "canonical": load(CANONICAL_PATH), "canonical_schema": load(CANONICAL_SCHEMA_PATH),
        "sources": load(SOURCE_PATH), "ledger": load(LEDGER_PATH), "overlay": load(OVERLAY_PATH),
        "expectations": load(EXPECTATIONS_PATH), "operations": load(OPERATIONS_PATH),
        "review_contract": load(REVIEW_CONTRACT_PATH), "review_decisions": load(REVIEW_DECISIONS_PATH),
        "live_schema": load(LIVE_SCHEMA_PATH), "live_observations": load(LIVE_OBSERVATIONS_PATH),
        "live_evidence": load(LIVE_EVIDENCE_PATH), "analysis_schema": load(ANALYSIS_SCHEMA_PATH),
        "analysis_reviews": load(ANALYSIS_REVIEWS_PATH), "analysis_evidence": load(ANALYSIS_EVIDENCE_PATH),
    }


def validate_layers(state: dict[str, dict]) -> None:
    report = validate_registry(state["canonical"], state["sources"])
    require(report.ok, "BG canonical validation: " + "; ".join(report.errors))
    overlay_errors = validate_biosecurity_overlay(state["canonical"], state["overlay"])
    require(not overlay_errors, "BG overlay validation: " + "; ".join(overlay_errors))
    live = validate_live_intelligence(
        state["live_schema"], state["live_evidence"], state["live_observations"], state["canonical"]
    )
    require(live.ok, "BG Live validation: " + "; ".join(live.errors))
    analysis = validate_analysis(
        state["analysis_schema"], state["analysis_evidence"], state["analysis_reviews"], state["canonical"]
    )
    require(analysis.ok, "BG Analysis validation: " + "; ".join(analysis.errors))


def assert_common_layers(state: dict[str, dict], plan: dict, *, target: bool) -> None:
    p = plan["postconditions"] if target else plan["preconditions"]
    expected = {
        "canonical_schema": (state["canonical_schema"].get("version"), "0.52"),
        "monitor": (state["expectations"].get("version"), "0.10"),
        "live_schema": (state["live_schema"].get("version"), "0.6"),
        "analysis_schema": (state["analysis_schema"].get("version"), "0.7"),
    }
    for label, (actual, want) in expected.items():
        require(str(actual) == want, f"BG {label} drift: {actual} != {want}")
    require(len(state["expectations"].get("adapters", [])) == 8, "BG monitor adapter count drift")
    require(len(state["live_observations"].get("observations", [])) == 6, "BG Live observation count drift")
    require(len(state["live_evidence"].get("evidence", [])) == 9, "BG Live evidence count drift")
    require(len(state["analysis_reviews"].get("reviews", [])) == 21, "BG Analysis review count drift")
    require(len(state["analysis_evidence"].get("evidence", [])) == 95, "BG Analysis evidence count drift")
    require(production_live_input_count(state["analysis_reviews"]) == 1, "BG production live_inputs drift")
    require(revision_count(state["analysis_reviews"]) == 0, "BG Analysis revisions drift")
    require(exact_series_count(state["analysis_reviews"]) == 0, "BG exact-series drift")
    readiness = analysis_population_readiness(state["analysis_schema"], state["analysis_reviews"], state["canonical"])
    require(readiness["eligible_completed_occurrence_count"] == 22, "BG eligible Analysis population drift")
    require(readiness["reviewed_occurrence_count"] == 21, "BG reviewed Analysis population drift")
    validate_layers(state)


def assert_prestate(state: dict[str, dict], plan: dict) -> None:
    p = plan["preconditions"]
    require(str(state["canonical"].get("version")) == p["canonical_registry_version"], "BG canonical pre-version drift")
    require(len(state["canonical"].get("records", [])) == p["canonical_record_count"], "BG canonical pre-count drift")
    require(str(state["sources"].get("version")) == p["source_registry_version"], "BG source pre-version drift")
    require(len(state["sources"].get("sources", [])) == p["source_record_count"], "BG source pre-count drift")
    require(str(state["ledger"].get("version")) == p["change_ledger_version"], "BG ledger pre-version drift")
    require(len(state["ledger"].get("changes", [])) == p["change_ledger_count"], "BG ledger pre-count drift")
    require(str(state["overlay"].get("version")) == p["biosecurity_overlay_version"], "BG overlay pre-version drift")
    require(state["overlay"].get("canonical_checkpoint") == p["biosecurity_overlay_checkpoint"], "BG overlay pre-checkpoint drift")
    target = by_occurrence(state["canonical"]).get(TARGET_ID)
    require(target is not None, "BG target occurrence missing")
    for key, value in p["target"].items():
        require(target.get(key) == value, f"BG target precondition {key} drift")
    require(related(target, REUTERS_ID) is not None, "BG BE Reuters fallback history missing")
    require(related(target, REUTERS_ID).get("role") == p["required_fallback_related_document_role"], "BG Reuters fallback role drift")
    sources = by_source(state["sources"])
    require("WSSRC-COM-001" in sources and REUTERS_ID in sources, "BG prerequisite OPEC/Reuters sources missing")
    require(SPA_ID not in sources, "BG SPA source already present")
    require(plan["provenance_basis"]["change_id"] not in {x.get("change_id") for x in state["ledger"].get("changes", [])}, "BG change already present")
    assert_common_layers(state, plan, target=False)


def ledger_entry(before: dict, after: dict, plan: dict, committed_at: str) -> dict:
    b = plan["provenance_basis"]
    s = plan["selection"]
    return {
        "change_id": b["change_id"], "occurrence_id": TARGET_ID, "change_type": b["change_type"],
        "old_values": {
            "lifecycle_status": before.get("lifecycle_status"),
            "last_successful_assertion_id": before.get("last_successful_assertion_id"),
            "completion_provenance_source_id": REUTERS_ID,
            "primary_opec_provenance_state": "REQUIRED_WHEN_RETRIEVABLE",
        },
        "new_values": {
            "lifecycle_status": after.get("lifecycle_status"),
            "last_successful_assertion_id": after.get("last_successful_assertion_id"),
            "official_confirmation_source_id": SPA_ID,
            "official_confirmation_source_url": s["official_confirmation_url"],
            "official_confirmation_source_class": s["official_confirmation_class"],
            "reuters_fallback_preserved": True,
            "primary_opec_provenance_state": b["primary_opec_provenance_state"],
        },
        "source_assertion_id": b["assertion_id"], "review_state": "APPROVED_FOR_CANONICAL_COMMIT",
        "reviewed_at": committed_at,
        "review_basis": [
            s["official_confirmation_url"], s["official_schedule_notice_url"], s["official_primary_index_url"],
            b["review_reason"],
            "SPA is official participating-government confirmation, not the competent OPEC issuing authority.",
            "Reuters WSSRC-COM-015 remains preserved as the evidence used for BE lifecycle completion.",
            "SPA publication time is publication metadata only and does not become canonical event time.",
            "No future occurrence is created from SPA and all automatic-write gates remain closed.",
        ],
        "commit_mode": "REVIEWED_OFFICIAL_CONFIRMATION_PROVENANCE_STRENGTHENING_BG",
        "committed_at": committed_at,
        "registry_version_before": plan["preconditions"]["canonical_registry_version"],
        "registry_version_after": plan["postconditions"]["canonical_registry_version"],
        "canonical_mutation_committed": True, "automatic_canonical_commit": False, "google_calendar_write": False,
    }


def simulate(state: dict[str, dict], plan: dict, committed_at: str = "2026-09-07T04:00:00+10:00") -> dict[str, dict]:
    assert_prestate(state, plan)
    out = copy.deepcopy(state)
    p = plan["postconditions"]
    before = by_occurrence(state["canonical"])[TARGET_ID]
    target = by_occurrence(out["canonical"])[TARGET_ID]
    target["last_successful_assertion_id"] = plan["provenance_basis"]["assertion_id"]
    target.setdefault("related_documents", []).append({
        "source_id": SPA_ID,
        "role": plan["provenance_basis"]["related_document_role"],
        "source_locator": plan["selection"]["official_confirmation_url"],
        "primary_opec_provenance_state": plan["provenance_basis"]["primary_opec_provenance_state"],
    })
    out["canonical"].update(version=p["canonical_registry_version"], reference_date=plan["reference_date"], record_count=len(out["canonical"]["records"]))
    out["sources"]["sources"].append(copy.deepcopy(plan["official_confirmation_source"]))
    out["sources"].update(version=p["source_registry_version"], reference_date=plan["reference_date"])
    out["ledger"]["changes"].append(ledger_entry(before, target, plan, committed_at))
    out["ledger"].update(version=p["change_ledger_version"], reference_date=plan["reference_date"])
    out["overlay"]["version"] = p["biosecurity_overlay_version"]
    out["overlay"]["canonical_checkpoint"] = copy.deepcopy(p["biosecurity_overlay_checkpoint"])
    assert_poststate(state, out, plan)
    return out


def assert_poststate(before: dict[str, dict], after: dict[str, dict], plan: dict) -> None:
    p = plan["postconditions"]
    require((str(after["canonical"].get("version")), len(after["canonical"].get("records", []))) == (p["canonical_registry_version"], 689), "BG canonical target mismatch")
    require((str(after["sources"].get("version")), len(after["sources"].get("sources", []))) == (p["source_registry_version"], 246), "BG source target mismatch")
    require((str(after["ledger"].get("version")), len(after["ledger"].get("changes", []))) == (p["change_ledger_version"], 62), "BG ledger target mismatch")
    require(str(after["overlay"].get("version")) == p["biosecurity_overlay_version"] and after["overlay"].get("canonical_checkpoint") == p["biosecurity_overlay_checkpoint"], "BG overlay target mismatch")
    before_overlay = {k: v for k, v in before["overlay"].items() if k not in {"version", "canonical_checkpoint"}}
    after_overlay = {k: v for k, v in after["overlay"].items() if k not in {"version", "canonical_checkpoint"}}
    require(before_overlay == after_overlay, "BG changed overlay semantics")
    c0, c1 = by_occurrence(before["canonical"]), by_occurrence(after["canonical"])
    require(list(c0) == list(c1), "BG changed Canonical identity/order")
    require([x for x in c0 if c0[x] != c1[x]] == [TARGET_ID], "BG mutated more than target occurrence")
    t0, t1 = c0[TARGET_ID], c1[TARGET_ID]
    changed_fields = {k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
    require(changed_fields == {"last_successful_assertion_id", "related_documents"}, f"BG target mutation scope drift: {changed_fields}")
    for key in ["lifecycle_status", "certainty_status", "start_local", "start_utc", "source_timezone", "timing_type", "time_precision", "primary_source_assertion_id", "status_history", "last_verified_at"]:
        require(t0.get(key) == t1.get(key), f"BG changed protected target field {key}")
    require(t1.get("lifecycle_status") == "COMPLETED" and t1.get("start_utc") is None, "BG lifecycle/time regression")
    require(related(t1, REUTERS_ID) == related(t0, REUTERS_ID), "BG rewrote Reuters fallback history")
    spa_doc = related(t1, SPA_ID)
    require(spa_doc is not None and spa_doc.get("primary_opec_provenance_state") == "REQUIRED_WHEN_RETRIEVABLE", "BG SPA document/primary-gap contract failure")
    s0, s1 = by_source(before["sources"]), by_source(after["sources"])
    require(all(s1.get(k) == v for k, v in s0.items()), "BG changed a pre-existing source")
    require(s1.get(SPA_ID) == plan["official_confirmation_source"], "BG SPA source mismatch")
    require(s1[SPA_ID].get("canonical_dependency_count") == 0 and s1[SPA_ID].get("automated_monitoring_use") == "PROHIBITED_OR_RIGHTS_HOLD", "BG SPA source opened a prohibited gate")
    old_changes = before["ledger"].get("changes", [])
    new_changes = after["ledger"].get("changes", [])
    require(new_changes[:len(old_changes)] == old_changes and len(new_changes) == len(old_changes) + 1, "BG rewrote ledger history")
    require(new_changes[-1].get("change_type") == "SOURCE_PROVENANCE_STRENGTHENING", "BG ledger type mismatch")
    require(new_changes[-1].get("new_values", {}).get("primary_opec_provenance_state") == "REQUIRED_WHEN_RETRIEVABLE", "BG falsely closed OPEC primary gap")
    for key in ["canonical_schema", "expectations", "operations", "review_contract", "review_decisions", "live_schema", "live_observations", "live_evidence", "analysis_schema", "analysis_reviews", "analysis_evidence"]:
        require(before[key] == after[key], f"BG mutated protected logical layer {key}")
    for row in after["canonical"].get("records", []):
        require(not (row.get("series_id") == plan["selection"]["series_id"] and str(row.get("start_local", "")).startswith("2026-10-04")), "BG created prohibited 4 October voluntary-adjustment occurrence")
    assert_common_layers(after, plan, target=True)


def target_status(current: str, plan: dict) -> str:
    marker = "\n---\n\n# WORLD SIGNALS — project status / branch-recovery checkpoint"
    require(marker in current, "BG status history marker missing")
    historical = current.split(marker, 1)[1]
    p = plan["postconditions"]
    head = f'''# CURRENT RECOVERY OVERRIDE — POST-BF / BG OPEC OFFICIAL-CONFIRMATION PROVENANCE STRENGTHENING\n\n**Effective checkpoint:** 2026-09-07\n**Exact post-BF main base:** `{plan['exact_base_main_sha']}`\n\nThis override supersedes stale "current" counts in the historical body below while preserving that body as an audit/recovery record. `WORLD_SIGNALS_PROJECT_CHARTER.md` remains authoritative; governed registry/contract files remain operational truth.\n\n## Current governed state\n\n- Canonical Registry: **v{p['canonical_registry_version']} / 689 occurrences**\n- Canonical schema: **v0.52**\n- Source Registry: **v{p['source_registry_version']} / 246 sources**\n- reviewed Change Ledger: **v{p['change_ledger_version']} / 62 entries**\n- biosecurity overlay: **v{p['biosecurity_overlay_version']} @ canonical v{p['canonical_registry_version']} / 689**\n- Source/Change Monitor expectations: **v0.10 / 8 configured adapters**\n- Monitor operations policy: **v0.1**\n- Live Intelligence: **v0.6 / 6 reviewed internal observations / 9 primary-official evidence rows / public observation projection CLOSED**\n- Analysis schema: **v0.7**\n- Analysis: **v0.17 / 21 reviews / 95 evidence / 18 reviewed event types**\n- completed Analysis-eligible occurrences: **22**\n- completed/unreviewed Analysis-eligible occurrences: **1** (`WSO-COM-A-0001`; not a population target)\n- production `live_inputs`: **1 / public projection CLOSED**\n- production Analysis revisions: **0 / gate CLOSED / public revision metadata projection CLOSED**\n- production `EXACT_TIMESTAMP_SERIES`: **0**\n- automatic canonical commit: **OFF / gate closed**\n- Google Calendar writes: **OFF**\n\n## Current architecture decision\n\nBG strengthens the completion provenance of the already-completed **6 September 2026 OPEC+ voluntary-adjustment review** (`WSO-COM-A-0001`) with official Saudi Press Agency confirmation. SPA is official participating-government confirmation, not the competent OPEC issuing authority.\n\nBE's Reuters fallback `WSSRC-COM-015` remains preserved in history. `WSSRC-COM-001` remains OPEC schedule/decision authority, and competent OPEC outcome provenance remains `REQUIRED_WHEN_RETRIEVABLE`. BG changes no lifecycle, certainty, event date/time, Live record or Analysis record and creates no October occurrence.\n\nBF remains the sixth Live specimen. AZ remains the only production `live_input`; BA's Analysis revision grammar remains production-closed. Public Live projection, automatic ingestion, automatic Canonical commit and Google Calendar writes remain closed.\n\n## Current configured monitor cohort\n\nEight configured adapters: RBA FSR; Colombia SUIN/Socrata; EU CRA/Cellar; three EU CBAM legal-rule routes; ONS release-calendar RSS; EIA WPSR schedule. Route presence does not imply blanket source automation permission, and all routes remain review-only with automatic canonical commit disabled.\n\n## Recovery order\n\n1. `WORLD_SIGNALS_PROJECT_CHARTER.md`\n2. this current override\n3. `data/canonical/registry.json`, `data/sources/registry.json`, `data/monitor/*`, `data/live_intelligence/*`, `data/analysis/*`\n4. latest pressure/transaction audits\n5. current `main` SHA and Actions runs\n---\n\n# WORLD SIGNALS — project status / branch-recovery checkpoint'''
    return head + historical.split("# WORLD SIGNALS — project status / branch-recovery checkpoint", 1)[1]


def target_roadmap(current: str) -> str:
    heading = "### BG — OPEC official participating-government provenance strengthening — DONE / OPEC PRIMARY STILL PENDING"
    if heading in current:
        return current
    needle = "Public observation projection, automatic ingestion, automatic story clustering, automatic Canonical commit and Google Calendar writes remain closed. A seventh Live observation requires another pressure audit.\n## Stage 8 — prospective Live Intelligence → Analysis linkage"
    require(needle in current, "BG roadmap insertion point missing")
    section = '''Public observation projection, automatic ingestion, automatic story clustering, automatic Canonical commit and Google Calendar writes remain closed. A seventh Live observation requires another pressure audit.\n\n### BG — OPEC official participating-government provenance strengthening — DONE / OPEC PRIMARY STILL PENDING\n\nBG strengthens BE's completion provenance for `WSO-COM-A-0001` with Saudi Press Agency official confirmation that the seven participating OPEC+ countries met on 6 September and maintained September production requirements for October. SPA outranks the Reuters fallback for supporting official confirmation but is not the competent OPEC issuing institution.\n\nReuters `WSSRC-COM-015` remains preserved as the evidence used for BE completion; `WSSRC-COM-001` remains OPEC schedule/decision authority; the competent OPEC outcome source remains `REQUIRED_WHEN_RETRIEVABLE`. BG changes no lifecycle, event date/time, Live observation, Analysis packet, bridge relationship or automation gate and creates no October occurrence from SPA.\n\n## Stage 8 — prospective Live Intelligence → Analysis linkage'''
    return current.replace(needle, section, 1)


def is_materialised(state: dict[str, dict], plan: dict) -> bool:
    target = by_occurrence(state["canonical"]).get(TARGET_ID)
    source = by_source(state["sources"]).get(SPA_ID)
    if target is None:
        return False
    any_bg = source is not None or related(target, SPA_ID) is not None
    if not any_bg:
        return False
    require(source is not None and related(target, SPA_ID) is not None, "BG partial materialisation detected")
    require(target.get("last_successful_assertion_id") == plan["provenance_basis"]["assertion_id"], "BG materialised assertion drift")
    return True


def assert_materialised(state: dict[str, dict], plan: dict) -> None:
    p = plan["postconditions"]
    require((str(state["canonical"].get("version")), len(state["canonical"].get("records", []))) == (p["canonical_registry_version"], 689), "BG committed canonical state drift")
    require((str(state["sources"].get("version")), len(state["sources"].get("sources", []))) == (p["source_registry_version"], 246), "BG committed source state drift")
    require((str(state["ledger"].get("version")), len(state["ledger"].get("changes", []))) == (p["change_ledger_version"], 62), "BG committed ledger state drift")
    target = by_occurrence(state["canonical"])[TARGET_ID]
    require(target.get("lifecycle_status") == "COMPLETED" and target.get("start_local") == "2026-09-06" and target.get("start_utc") is None, "BG committed OPEC lifecycle/time drift")
    require(related(target, REUTERS_ID) is not None and related(target, SPA_ID) is not None, "BG committed provenance evidence missing")
    require(related(target, SPA_ID).get("primary_opec_provenance_state") == "REQUIRED_WHEN_RETRIEVABLE", "BG committed primary gap falsely closed")
    require(by_source(state["sources"]).get(SPA_ID) == plan["official_confirmation_source"], "BG committed SPA source drift")
    require(plan["provenance_basis"]["change_id"] in {x.get("change_id") for x in state["ledger"].get("changes", [])}, "BG committed ledger identity missing")
    assert_common_layers(state, plan, target=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-only", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    plan = load(PLAN_PATH)
    state = load_state()
    if is_materialised(state, plan):
        assert_materialised(state, plan)
        target_status(STATUS_PATH.read_text(encoding="utf-8"), plan)
        target_roadmap(ROADMAP_PATH.read_text(encoding="utf-8"))
        print("BG target already materialised and valid")
        return
    candidate = simulate(state, plan, datetime.now(ZoneInfo("Australia/Melbourne")).isoformat(timespec="seconds"))
    status = target_status(STATUS_PATH.read_text(encoding="utf-8"), plan)
    roadmap = target_roadmap(ROADMAP_PATH.read_text(encoding="utf-8"))
    if args.check_only:
        print("BG check-only PASS: SPA official confirmation would strengthen BE provenance; OPEC primary remains pending")
        return
    require(os.environ.get(APPLY_ENV) == "YES", f"BG write gate closed: set {APPLY_ENV}=YES")
    dump(CANONICAL_PATH, candidate["canonical"]); dump(SOURCE_PATH, candidate["sources"])
    dump(LEDGER_PATH, candidate["ledger"]); dump(OVERLAY_PATH, candidate["overlay"])
    STATUS_PATH.write_text(status, encoding="utf-8"); ROADMAP_PATH.write_text(roadmap, encoding="utf-8")
    print("BG controlled materialisation complete")


if __name__ == "__main__":
    main()
