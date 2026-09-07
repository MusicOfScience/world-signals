#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.world_signals.analytical_overlays import validate_biosecurity_overlay
from src.world_signals.analysis import analysis_population_readiness, validate_analysis
from src.world_signals.live_analysis_bridge import production_live_input_count
from src.world_signals.live_intelligence import validate_live_intelligence
from src.world_signals.validation import validate_registry

PLAN_PATH = ROOT / "data/coverage/OPEC_PRIMARY_PROVENANCE_BH_PLAN_v0.1.json"
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
AUDIT_PATH = ROOT / "data/coverage/OPEC_PRIMARY_PROVENANCE_BH_TRANSACTION_AUDIT_v0.1.md"

APPLY_ENV = "WORLD_SIGNALS_APPLY_OPEC_PRIMARY_PROVENANCE_BH"
TARGET_ID = "WSO-COM-A-0001"
OPEC_ID = "WSSRC-COM-001"
REUTERS_ID = "WSSRC-COM-015"
SPA_ID = "WSSRC-COM-016"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def by_occurrence(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row.get("occurrence_id"): row for row in registry.get("records", [])}


def by_source(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row.get("source_id"): row for row in registry.get("sources", [])}


def related_rows(row: dict[str, Any], source_id: str) -> list[dict[str, Any]]:
    return [doc for doc in row.get("related_documents", []) if doc.get("source_id") == source_id]


def revision_count(reviews: dict[str, Any]) -> int:
    return sum(bool(row.get("revision_of_analysis_id")) for row in reviews.get("reviews", []))


def exact_series_count(reviews: dict[str, Any]) -> int:
    return sum(
        1
        for review in reviews.get("reviews", [])
        for moved in (review.get("what_moved") or [])
        if moved.get("measurement_precision") == "EXACT_TIMESTAMP_SERIES"
    )


def load_state() -> dict[str, dict[str, Any]]:
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


def validate_layers(state: dict[str, dict[str, Any]]) -> None:
    report = validate_registry(state["canonical"], state["sources"])
    require(report.ok, "BH canonical validation failed: " + "; ".join(report.errors))
    overlay_errors = validate_biosecurity_overlay(state["canonical"], state["overlay"])
    require(not overlay_errors, "BH overlay validation failed: " + "; ".join(overlay_errors))
    live = validate_live_intelligence(
        state["live_schema"], state["live_evidence"], state["live_observations"], state["canonical"]
    )
    require(live.ok, "BH Live validation failed: " + "; ".join(live.errors))
    analysis = validate_analysis(
        state["analysis_schema"], state["analysis_evidence"], state["analysis_reviews"], state["canonical"]
    )
    require(analysis.ok, "BH Analysis validation failed: " + "; ".join(analysis.errors))


def assert_common_layers(state: dict[str, dict[str, Any]], plan: dict[str, Any]) -> None:
    post = plan["postconditions"]
    require(str(state["canonical_schema"].get("version")) == "0.52", "BH Canonical schema drift")
    require(str(state["expectations"].get("version")) == post["monitor_expectations_version"], "BH monitor expectations drift")
    require(len(state["expectations"].get("adapters", [])) == post["monitor_adapter_count"], "BH monitor adapter drift")
    require(str(state["operations"].get("version")) == "0.1", "BH monitor operations drift")
    require(str(state["live_schema"].get("version")) == post["live_schema_version"], "BH Live schema drift")
    require(len(state["live_observations"].get("observations", [])) == post["live_observation_count"], "BH Live observation drift")
    require(len(state["live_evidence"].get("evidence", [])) == post["live_evidence_count"], "BH Live evidence drift")
    require(str(state["analysis_schema"].get("version")) == post["analysis_schema_version"], "BH Analysis schema drift")
    require((str(state["analysis_reviews"].get("version")), len(state["analysis_reviews"].get("reviews", []))) == (post["analysis_reviews_version"], post["analysis_review_count"]), "BH Analysis reviews drift")
    require((str(state["analysis_evidence"].get("version")), len(state["analysis_evidence"].get("evidence", []))) == (post["analysis_evidence_version"], post["analysis_evidence_count"]), "BH Analysis evidence drift")
    require(production_live_input_count(state["analysis_reviews"]) == post["production_live_input_count"], "BH live_inputs drift")
    require(revision_count(state["analysis_reviews"]) == post["production_analysis_revision_count"], "BH Analysis revision drift")
    require(exact_series_count(state["analysis_reviews"]) == post["production_exact_timestamp_series_count"], "BH exact-series drift")
    readiness = analysis_population_readiness(state["analysis_schema"], state["analysis_reviews"], state["canonical"])
    require(readiness["eligible_completed_occurrence_count"] == post["eligible_completed_occurrence_count"], "BH eligible Analysis count drift")
    require(readiness["reviewed_occurrence_count"] == post["reviewed_occurrence_count"], "BH reviewed Analysis count drift")
    validate_layers(state)


def source_pending_text(source: dict[str, Any]) -> bool:
    combined = " ".join(
        [str(source.get("information_supplied", "")), str(source.get("recommended_verification_cadence", "")), str(source.get("notes", ""))]
        + [str(item) for item in source.get("known_limitations", [])]
    )
    return "REQUIRED_WHEN_RETRIEVABLE" in combined or "primary outcome provenance remains pending" in combined or "continue seeking competent OPEC primary" in combined


def assert_prestate(state: dict[str, dict[str, Any]], plan: dict[str, Any]) -> None:
    pre = plan["preconditions"]
    require((str(state["canonical"].get("version")), len(state["canonical"].get("records", []))) == (pre["canonical_registry_version"], pre["canonical_record_count"]), "BH canonical pre-state drift")
    require((str(state["sources"].get("version")), len(state["sources"].get("sources", []))) == (pre["source_registry_version"], pre["source_record_count"]), "BH source pre-state drift")
    require((str(state["ledger"].get("version")), len(state["ledger"].get("changes", []))) == (pre["change_ledger_version"], pre["change_ledger_count"]), "BH ledger pre-state drift")
    require((str(state["overlay"].get("version")), state["overlay"].get("canonical_checkpoint")) == (pre["biosecurity_overlay_version"], pre["biosecurity_overlay_checkpoint"]), "BH overlay pre-state drift")

    target = by_occurrence(state["canonical"]).get(TARGET_ID)
    require(target is not None, "BH target occurrence missing")
    for key, expected in pre["target"].items():
        require(target.get(key) == expected, f"BH target precondition drift: {key}")

    reuters = related_rows(target, REUTERS_ID)
    spa = related_rows(target, SPA_ID)
    require(any(doc.get("role") == pre["reuters_related_document_role"] for doc in reuters), "BH Reuters historical related document missing")
    require(any(doc.get("role") == pre["spa_related_document_role"] and doc.get("primary_opec_provenance_state") == pre["spa_related_document_primary_state"] for doc in spa), "BH SPA historical related document missing")
    require(not any(doc.get("role") == plan["provenance_basis"]["related_document_role"] for doc in related_rows(target, OPEC_ID)), "BH competent OPEC outcome already related")

    sources = by_source(state["sources"])
    require(set(pre["required_source_ids"]).issubset(sources), "BH required source identity missing")
    opec = sources[OPEC_ID]
    require(opec.get("institution") == "OPEC", "BH OPEC source institution drift")
    require(opec.get("authoritative_url") == pre["opec_source_authoritative_url"], "BH legacy OPEC route precondition drift")
    require(opec.get("automated_monitoring_use") == "PROHIBITED_OR_RIGHTS_HOLD", "BH OPEC automation-rights guard drift")
    require(sources[SPA_ID].get("automated_monitoring_use") == "PROHIBITED_OR_RIGHTS_HOLD", "BH SPA automation-rights guard drift")
    require(source_pending_text(sources[SPA_ID]), "BH SPA source no longer records pre-BH primary provenance debt")
    require(plan["provenance_basis"]["change_id"] not in {row.get("change_id") for row in state["ledger"].get("changes", [])}, "BH change already present")

    # Common downstream layers remain the post-BG values before BH as well.
    assert_common_layers(state, plan)


def update_opec_source(source: dict[str, Any], plan: dict[str, Any]) -> None:
    selection = plan["selection"]
    source["authoritative_url"] = selection["current_press_release_index_url"]
    source["last_successful_research_verification_at"] = plan["reference_date"]
    limitations = list(source.get("known_limitations", []))
    note = "The legacy registered OPEC press-room URL now redirects to the OPEC home page; BH uses the current official press-release index plus direct reviewed event pages for manual provenance."
    if note not in limitations:
        limitations.append(note)
    source["known_limitations"] = limitations
    source["notes"] = "Official OPEC press releases remain the competent schedule/decision/outcome authority. BH updates the current manual source route after recovering the 6 September issuing-authority outcome page; existing rights and production-automation holds remain unchanged."


def update_spa_source(source: dict[str, Any], plan: dict[str, Any]) -> None:
    source["information_supplied"] = "SPA records that Saudi Arabia, Russia, Iraq, Kuwait, Kazakhstan, Algeria and Oman met virtually on 6 September 2026 and decided to maintain September 2026 required production for October 2026. Retained as official participating-government supporting confirmation; BH subsequently recovered competent OPEC issuing-authority outcome provenance."
    source["recommended_verification_cadence"] = "none; retain as reviewed supporting provenance alongside the BH-recovered competent OPEC outcome source"
    updated: list[str] = []
    for item in source.get("known_limitations", []):
        if item == "The competent OPEC primary provenance requirement remains REQUIRED_WHEN_RETRIEVABLE.":
            updated.append("At BG review the competent OPEC primary provenance requirement remained REQUIRED_WHEN_RETRIEVABLE; BH later recovered the competent OPEC issuing-authority outcome source.")
        elif item.startswith("Current accessible/indexed OPEC surfaces reviewed for BG did not expose the 6 September outcome"):
            updated.append("At BG review the accessible/indexed OPEC surfaces did not expose the 6 September outcome; BH later recovered the competent direct OPEC outcome page. The historical BG retrieval observation remains valid for that checkpoint.")
        else:
            updated.append(item)
    source["known_limitations"] = updated
    source["notes"] = "Official participating-government completion confirmation only. Reuters fallback remains in history. BH subsequently recovered competent OPEC outcome provenance through WSSRC-COM-001; SPA remains supporting evidence and is not the issuing authority."


def ledger_entry(before: dict[str, Any], after: dict[str, Any], plan: dict[str, Any], committed_at: str) -> dict[str, Any]:
    selection = plan["selection"]
    basis = plan["provenance_basis"]
    return {
        "change_id": basis["change_id"],
        "occurrence_id": TARGET_ID,
        "change_type": basis["change_type"],
        "old_values": {
            "lifecycle_status": before.get("lifecycle_status"),
            "last_successful_assertion_id": before.get("last_successful_assertion_id"),
            "primary_opec_provenance_state": selection["primary_provenance_state_before"],
            "competent_opec_outcome_url": None,
        },
        "new_values": {
            "lifecycle_status": after.get("lifecycle_status"),
            "last_successful_assertion_id": after.get("last_successful_assertion_id"),
            "primary_opec_provenance_state": selection["primary_provenance_state_after"],
            "competent_opec_outcome_source_id": OPEC_ID,
            "competent_opec_outcome_url": selection["official_primary_outcome_url"],
            "reuters_fallback_preserved": True,
            "spa_confirmation_preserved": True,
        },
        "source_assertion_id": basis["assertion_id"],
        "review_state": "APPROVED_FOR_CANONICAL_COMMIT",
        "reviewed_at": committed_at,
        "review_basis": [
            selection["official_primary_outcome_url"],
            selection["current_press_release_index_url"],
            selection["legacy_registry_url"],
            basis["review_reason"],
            "The direct OPEC outcome source satisfies the competent issuing-authority provenance requirement without changing event timing or lifecycle.",
            "Reuters WSSRC-COM-015 and SPA WSSRC-COM-016 remain preserved because they document the reviewed evidence path used by BE and BG.",
            "No publication timestamp is promoted to canonical event time.",
            "No future occurrence or automatic-write authority is created by BH.",
        ],
        "commit_mode": "REVIEWED_COMPETENT_OPEC_PRIMARY_PROVENANCE_RECOVERY_BH",
        "committed_at": committed_at,
        "registry_version_before": plan["preconditions"]["canonical_registry_version"],
        "registry_version_after": plan["postconditions"]["canonical_registry_version"],
        "canonical_mutation_committed": True,
        "automatic_canonical_commit": False,
        "google_calendar_write": False,
    }


def simulate(state: dict[str, dict[str, Any]], plan: dict[str, Any], committed_at: str = "2026-09-08T12:00:00+10:00") -> dict[str, dict[str, Any]]:
    assert_prestate(state, plan)
    out = copy.deepcopy(state)
    post = plan["postconditions"]
    before_target = by_occurrence(state["canonical"])[TARGET_ID]
    target = by_occurrence(out["canonical"])[TARGET_ID]
    target["last_successful_assertion_id"] = plan["provenance_basis"]["assertion_id"]
    target["last_verified_at"] = plan["reference_date"]
    target.setdefault("related_documents", []).append({
        "source_id": OPEC_ID,
        "role": plan["provenance_basis"]["related_document_role"],
        "source_locator": plan["selection"]["official_primary_outcome_url"],
        "primary_opec_provenance_state": plan["provenance_basis"]["primary_opec_provenance_state"],
    })
    out["canonical"].update(version=post["canonical_registry_version"], reference_date=plan["reference_date"], record_count=len(out["canonical"]["records"]))

    sources = by_source(out["sources"])
    update_opec_source(sources[OPEC_ID], plan)
    update_spa_source(sources[SPA_ID], plan)
    out["sources"].update(version=post["source_registry_version"], reference_date=plan["reference_date"])

    out["ledger"]["changes"].append(ledger_entry(before_target, target, plan, committed_at))
    out["ledger"].update(version=post["change_ledger_version"], reference_date=plan["reference_date"])
    out["overlay"]["version"] = post["biosecurity_overlay_version"]
    out["overlay"]["canonical_checkpoint"] = copy.deepcopy(post["biosecurity_overlay_checkpoint"])
    assert_poststate(state, out, plan)
    return out


def assert_poststate(before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]], plan: dict[str, Any]) -> None:
    post = plan["postconditions"]
    require((str(after["canonical"].get("version")), len(after["canonical"].get("records", []))) == (post["canonical_registry_version"], post["canonical_record_count"]), "BH canonical target mismatch")
    require((str(after["sources"].get("version")), len(after["sources"].get("sources", []))) == (post["source_registry_version"], post["source_record_count"]), "BH source target mismatch")
    require((str(after["ledger"].get("version")), len(after["ledger"].get("changes", []))) == (post["change_ledger_version"], post["change_ledger_count"]), "BH ledger target mismatch")
    require(str(after["overlay"].get("version")) == post["biosecurity_overlay_version"] and after["overlay"].get("canonical_checkpoint") == post["biosecurity_overlay_checkpoint"], "BH overlay target mismatch")

    before_overlay = {key: value for key, value in before["overlay"].items() if key not in {"version", "canonical_checkpoint"}}
    after_overlay = {key: value for key, value in after["overlay"].items() if key not in {"version", "canonical_checkpoint"}}
    require(before_overlay == after_overlay, "BH changed biosecurity overlay semantics")

    c0, c1 = by_occurrence(before["canonical"]), by_occurrence(after["canonical"])
    require(list(c0) == list(c1), "BH changed Canonical identity/order")
    require([oid for oid in c0 if c0[oid] != c1[oid]] == [TARGET_ID], "BH mutated more than the target Canonical occurrence")
    t0, t1 = c0[TARGET_ID], c1[TARGET_ID]
    changed_fields = {key for key in set(t0) | set(t1) if t0.get(key) != t1.get(key)}
    require(changed_fields == {"last_successful_assertion_id", "last_verified_at", "related_documents"}, f"BH target mutation scope drift: {changed_fields}")
    for key in ["series_id", "source_id", "canonical_name", "category", "event_type", "certainty_status", "lifecycle_status", "start_local", "start_utc", "source_timezone", "timing_type", "time_precision", "time_status", "status_history", "intrinsic_importance", "expected_market_sensitivity"]:
        require(t0.get(key) == t1.get(key), f"BH changed protected target field {key}")
    require(t1.get("lifecycle_status") == "COMPLETED" and t1.get("start_local") == "2026-09-06" and t1.get("start_utc") is None, "BH lifecycle/time regression")
    reuters = related_rows(t1, REUTERS_ID)
    spa = related_rows(t1, SPA_ID)
    opec = related_rows(t1, OPEC_ID)
    require(reuters and spa, "BH lost Reuters/SPA history")
    require(any(doc.get("role") == plan["preconditions"]["spa_related_document_role"] and doc.get("primary_opec_provenance_state") == "REQUIRED_WHEN_RETRIEVABLE" for doc in spa), "BH rewrote historical BG pending marker")
    require(any(doc.get("role") == plan["provenance_basis"]["related_document_role"] and doc.get("primary_opec_provenance_state") == "SATISFIED_COMPETENT_ISSUING_AUTHORITY" for doc in opec), "BH competent OPEC provenance missing")

    s0, s1 = by_source(before["sources"]), by_source(after["sources"])
    require(list(s0) == list(s1), "BH changed source identity/order")
    require({sid for sid in s0 if s0[sid] != s1[sid]} == {OPEC_ID, SPA_ID}, "BH source mutation escaped OPEC/SPA boundary")
    for sid in (OPEC_ID, SPA_ID):
        for field in ["source_id", "institution", "canonical_dependency_count", "canonical_provenance_use", "automated_monitoring_use", "automated_retrieval_permission", "verification_mode", "ingestion_permission", "redistribution_permission", "licence_review_status"]:
            require(s0[sid].get(field) == s1[sid].get(field), f"BH changed protected source-governance field {sid}.{field}")
    require(s1[OPEC_ID].get("authoritative_url") == plan["selection"]["current_press_release_index_url"], "BH OPEC current route not updated")
    require(s1[OPEC_ID].get("automated_monitoring_use") == "PROHIBITED_OR_RIGHTS_HOLD", "BH inferred OPEC automation permission")
    require(not source_pending_text(s1[SPA_ID]), "BH left current SPA source text saying competent OPEC provenance is pending")

    change = [row for row in after["ledger"].get("changes", []) if row.get("change_id") == plan["provenance_basis"]["change_id"]]
    require(len(change) == 1, "BH reviewed Change Ledger entry missing/duplicate")
    require(change[0]["new_values"]["primary_opec_provenance_state"] == "SATISFIED_COMPETENT_ISSUING_AUTHORITY", "BH ledger primary state mismatch")
    require(not change[0]["automatic_canonical_commit"] and not change[0]["google_calendar_write"], "BH opened automatic write gate")

    for row in after["canonical"].get("records", []):
        require(not (row.get("series_id") == plan["selection"]["series_id"] and str(row.get("start_local", "")).startswith("2026-10-04")), "BH created prohibited 4 October voluntary-adjustment occurrence")

    for key in ["canonical_schema", "expectations", "operations", "review_contract", "review_decisions", "live_schema", "live_observations", "live_evidence", "analysis_schema", "analysis_reviews", "analysis_evidence"]:
        require(before[key] == after[key], f"BH changed protected layer {key}")
    assert_common_layers(after, plan)


def is_materialised(state: dict[str, dict[str, Any]], plan: dict[str, Any]) -> bool:
    target = by_occurrence(state["canonical"]).get(TARGET_ID)
    if target is None:
        return False
    role = plan["provenance_basis"]["related_document_role"]
    has_doc = any(doc.get("role") == role for doc in related_rows(target, OPEC_ID))
    has_change = plan["provenance_basis"]["change_id"] in {row.get("change_id") for row in state["ledger"].get("changes", [])}
    if has_doc != has_change:
        raise RuntimeError("BH partial materialisation detected")
    return has_doc and has_change


def assert_materialised(state: dict[str, dict[str, Any]], plan: dict[str, Any]) -> None:
    post = plan["postconditions"]
    require((str(state["canonical"].get("version")), len(state["canonical"].get("records", []))) == (post["canonical_registry_version"], post["canonical_record_count"]), "BH materialised Canonical drift")
    require((str(state["sources"].get("version")), len(state["sources"].get("sources", []))) == (post["source_registry_version"], post["source_record_count"]), "BH materialised Source drift")
    require((str(state["ledger"].get("version")), len(state["ledger"].get("changes", []))) == (post["change_ledger_version"], post["change_ledger_count"]), "BH materialised Ledger drift")
    target = by_occurrence(state["canonical"])[TARGET_ID]
    require(target.get("last_successful_assertion_id") == plan["provenance_basis"]["assertion_id"], "BH materialised assertion drift")
    require(any(doc.get("role") == plan["provenance_basis"]["related_document_role"] for doc in related_rows(target, OPEC_ID)), "BH materialised OPEC provenance missing")
    sources = by_source(state["sources"])
    require(sources[OPEC_ID].get("authoritative_url") == plan["selection"]["current_press_release_index_url"], "BH materialised OPEC route drift")
    require(not source_pending_text(sources[SPA_ID]), "BH materialised SPA state still pending")
    assert_common_layers(state, plan)


def target_status(current: str, plan: dict[str, Any]) -> str:
    marker = "\n---\n\n# WORLD SIGNALS — project status / branch-recovery checkpoint"
    require(marker in current, "BH status history marker missing")
    historical = current.split(marker, 1)[1]
    p = plan["postconditions"]
    head = f'''# CURRENT RECOVERY OVERRIDE — BH OPEC COMPETENT-PRIMARY PROVENANCE RECOVERY

**Effective checkpoint:** 2026-09-08
**Exact post-BG main base:** `{plan['exact_base_main_sha']}`

This override supersedes stale "current" counts in the historical body below while preserving that body as an audit/recovery record. `WORLD_SIGNALS_PROJECT_CHARTER.md` remains authoritative; governed registry/contract files remain operational truth.

## Current governed state

- Canonical Registry: **v{p['canonical_registry_version']} / {p['canonical_record_count']} occurrences**
- Canonical schema: **v0.52**
- Source Registry: **v{p['source_registry_version']} / {p['source_record_count']} sources**
- reviewed Change Ledger: **v{p['change_ledger_version']} / {p['change_ledger_count']} entries**
- biosecurity overlay: **v{p['biosecurity_overlay_version']} @ Canonical v{p['canonical_registry_version']} / {p['canonical_record_count']}**
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
- automatic Canonical commit: **OFF / gate closed**
- Google Calendar writes: **OFF**

## Current architecture decision

BH closes the explicit BE/BG competent-primary provenance debt for the already-completed **6 September 2026 OPEC+ voluntary-adjustment review** (`WSO-COM-A-0001`) using the now-retrievable OPEC issuing-authority outcome page. Reuters `WSSRC-COM-015` and SPA `WSSRC-COM-016` remain preserved as historical/supporting evidence; their earlier roles are not rewritten.

`WSSRC-COM-001` remains the OPEC schedule/decision/outcome authority. Its current manual authoritative route is updated to the OPEC press-release index because the legacy registered press-room URL now redirects to the home page. This route repair grants no automated-retrieval or monitoring permission.

BH changes no lifecycle, certainty, event date/time, Live observation, Analysis review, bridge relationship or revision. The occurrence remains `CIVIL_DATE` 2026-09-06 with no invented UTC timestamp. No 4 October voluntary-adjustment occurrence is created.

BF remains the sixth Live specimen. AZ remains the only production `live_input`; BA's Analysis revision grammar remains production-closed. Public Live projection, automatic ingestion, automatic Canonical commit and Google Calendar writes remain closed.

## Recovery order

1. `WORLD_SIGNALS_PROJECT_CHARTER.md`
2. this current override
3. `data/canonical/registry.json`, `data/sources/registry.json`, `data/monitor/*`, `data/live_intelligence/*`, `data/analysis/*`
4. latest pressure/transaction audits
5. current `main` SHA and Actions runs
'''
    return head + marker + historical


def target_roadmap(current: str) -> str:
    if "### BH — OPEC competent-primary provenance recovery — DONE / POPULATION-NEUTRAL" in current:
        return current
    needle = "\n## Stage 8 — prospective Live Intelligence → Analysis linkage"
    require(needle in current, "BH roadmap insertion marker missing")
    section = '''
### BH — OPEC competent-primary provenance recovery — DONE / POPULATION-NEUTRAL

BH closes the competent issuing-authority provenance debt deliberately preserved by BE and BG for the existing 6 September 2026 OPEC+ voluntary-adjustment review. The direct OPEC outcome page is now retrievable and confirms that the seven participating countries met virtually on 6 September and maintained September required production for October.

The same stable occurrence remains `COMPLETED`, `CONFIRMED` and `CIVIL_DATE` 2026-09-06 with null UTC and no fabricated meeting clock. Reuters `WSSRC-COM-015` remains the historical BE fallback and SPA `WSSRC-COM-016` remains BG's official participating-government confirmation; neither is deleted or retrospectively promoted into the competent issuing authority.

`WSSRC-COM-001` remains the competent OPEC schedule/decision/outcome source. Its current manual route is updated from the obsolete legacy press-room URL, which now redirects to the OPEC home page, to the current OPEC press-release index. Existing OPEC rights and production-automation holds remain unchanged: source retrievability is not automation permission.

BH adds no Canonical occurrence, Live observation, Analysis review, second bridge input, revision or market-response claim and creates no 4 October voluntary-adjustment occurrence. Automatic Canonical commit and Google Calendar writes remain closed.
'''
    return current.replace(needle, "\n" + section + needle, 1)


def audit_text(plan: dict[str, Any], committed_at: str) -> str:
    p = plan["postconditions"]
    return f'''# WORLD SIGNALS — OPEC competent-primary provenance BH transaction audit v0.1

**Tranche:** BH  
**Exact base main:** `{plan['exact_base_main_sha']}`  
**Committed at:** `{committed_at}`  
**Decision:** recover competent OPEC issuing-authority outcome provenance for `WSO-COM-A-0001`; no population growth.

## Provenance recovered

- competent source: `WSSRC-COM-001` / OPEC;
- direct outcome: `{plan['selection']['official_primary_outcome_url']}`;
- current OPEC press-release index: `{plan['selection']['current_press_release_index_url']}`;
- Reuters `WSSRC-COM-015` preserved as BE historical fallback;
- SPA `WSSRC-COM-016` preserved as BG official participating-government confirmation;
- competent-primary state: `SATISFIED_COMPETENT_ISSUING_AUTHORITY`.

## Timing and lifecycle boundary

The occurrence remains `COMPLETED`, `CONFIRMED`, `CIVIL_DATE`, start `2026-09-06`, null `start_utc` and null `source_timezone`. BH does not infer an event clock from any publication timestamp and does not create a 4 October voluntary-adjustment occurrence.

## Materialised target

- Canonical Registry: **v{p['canonical_registry_version']} / {p['canonical_record_count']}**;
- Source Registry: **v{p['source_registry_version']} / {p['source_record_count']}**;
- Change Ledger: **v{p['change_ledger_version']} / {p['change_ledger_count']}**;
- biosecurity overlay: **v{p['biosecurity_overlay_version']} @ Canonical v{p['canonical_registry_version']} / {p['canonical_record_count']}**, semantic payload unchanged;
- monitor: **v0.10 / 8**, unchanged;
- Live Intelligence: **v0.6 / 6 / 9**, unchanged;
- Analysis: **v0.17 / 21 / 95**, unchanged;
- production `live_inputs`: **1**;
- production Analysis revisions: **0**;
- automatic Canonical commit: **OFF**;
- Google Calendar writes: **OFF**.

## Mutation boundary

Governed BH writes are limited to the existing OPEC Canonical target, the existing OPEC/SPA source objects, one reviewed Change Ledger entry, the biosecurity overlay version/checkpoint, recovery status/roadmap, and this transaction audit. Canonical schema, monitor configuration/review state, Live Intelligence and all Analysis datasets remain byte-identical.

## Historical preservation

BE and BG audit/plan/ledger records are not rewritten. Their `REQUIRED_WHEN_RETRIEVABLE` language remains historically correct at those checkpoints. The current BH state records that the requirement has since been satisfied.

Manual merge only. No auto-merge is authorised.
'''


def materialise(candidate: dict[str, dict[str, Any]], plan: dict[str, Any], committed_at: str) -> None:
    dump(CANONICAL_PATH, candidate["canonical"])
    dump(SOURCE_PATH, candidate["sources"])
    dump(LEDGER_PATH, candidate["ledger"])
    dump(OVERLAY_PATH, candidate["overlay"])
    STATUS_PATH.write_text(target_status(STATUS_PATH.read_text(encoding="utf-8"), plan), encoding="utf-8")
    ROADMAP_PATH.write_text(target_roadmap(ROADMAP_PATH.read_text(encoding="utf-8")), encoding="utf-8")
    AUDIT_PATH.write_text(audit_text(plan, committed_at), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    require(args.check_only ^ args.apply, "choose exactly one of --check-only or --apply")

    plan = load(PLAN_PATH)
    state = load_state()
    if is_materialised(state, plan):
        assert_materialised(state, plan)
        require("BH OPEC COMPETENT-PRIMARY PROVENANCE RECOVERY" in target_status(STATUS_PATH.read_text(encoding="utf-8"), plan), "BH status transform invalid")
        require("BH — OPEC competent-primary provenance recovery" in target_roadmap(ROADMAP_PATH.read_text(encoding="utf-8")), "BH roadmap transform invalid")
        print("BH target already materialised and valid")
        return

    committed_at = datetime.now(ZoneInfo("Australia/Melbourne")).isoformat(timespec="seconds")
    candidate = simulate(state, plan, committed_at)
    status = target_status(STATUS_PATH.read_text(encoding="utf-8"), plan)
    roadmap = target_roadmap(ROADMAP_PATH.read_text(encoding="utf-8"))
    require("BH OPEC COMPETENT-PRIMARY PROVENANCE RECOVERY" in status, "BH status target invalid")
    require("BH — OPEC competent-primary provenance recovery" in roadmap, "BH roadmap target invalid")

    if args.check_only:
        print(json.dumps({
            "mode": "CHECK_ONLY",
            "occurrence_id": TARGET_ID,
            "competent_source_id": OPEC_ID,
            "official_primary_outcome_url": plan["selection"]["official_primary_outcome_url"],
            "primary_opec_provenance_state": plan["provenance_basis"]["primary_opec_provenance_state"],
            "target_canonical_version": plan["postconditions"]["canonical_registry_version"],
            "automatic_canonical_commit": False,
            "google_calendar_write": False,
        }, indent=2))
        return

    require(os.environ.get(APPLY_ENV) == "YES", f"BH write gate closed: set {APPLY_ENV}=YES")
    materialise(candidate, plan, committed_at)
    print("BH controlled competent-primary provenance materialisation complete")


if __name__ == "__main__":
    main()
