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
from src.world_signals.analysis import validate_analysis
from src.world_signals.checkpoint_contract import version_at_least
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

APPLY_ENV = "WORLD_SIGNALS_APPLY_OPEC_PRIMARY_PROVENANCE_BH"
TARGET_ID = "WSO-COM-A-0001"
OPEC_ID = "WSSRC-COM-001"
REUTERS_ID = "WSSRC-COM-015"
SPA_ID = "WSSRC-COM-016"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(message)


def by_occurrence(registry: dict) -> dict[str, dict]:
    return {row.get("occurrence_id"): row for row in registry.get("records", [])}


def by_source(registry: dict) -> dict[str, dict]:
    return {row.get("source_id"): row for row in registry.get("sources", [])}


def related_rows(row: dict, source_id: str) -> list[dict]:
    return [item for item in row.get("related_documents", []) if item.get("source_id") == source_id]


def overlay_semantics(overlay: dict) -> dict:
    return {k: v for k, v in overlay.items() if k not in {"version", "canonical_checkpoint"}}


def load_state() -> dict[str, dict]:
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
    canonical = validate_registry(state["canonical"], state["sources"])
    require(canonical.ok, "BH canonical validation: " + "; ".join(canonical.errors))
    overlay_errors = validate_biosecurity_overlay(state["canonical"], state["overlay"])
    require(not overlay_errors, "BH overlay validation: " + "; ".join(overlay_errors))
    live = validate_live_intelligence(
        state["live_schema"], state["live_evidence"], state["live_observations"], state["canonical"]
    )
    require(live.ok, "BH Live validation: " + "; ".join(live.errors))
    analysis = validate_analysis(
        state["analysis_schema"], state["analysis_evidence"], state["analysis_reviews"], state["canonical"]
    )
    require(analysis.ok, "BH Analysis validation: " + "; ".join(analysis.errors))


def assert_exact_prestate(state: dict[str, dict], plan: dict) -> None:
    p = plan["preconditions"]
    checks = [
        (str(state["canonical_schema"].get("version")), p["canonical_schema_version"], "canonical schema"),
        (str(state["canonical"].get("version")), p["canonical_registry_version"], "canonical registry"),
        (len(state["canonical"].get("records", [])), p["canonical_record_count"], "canonical count"),
        (str(state["sources"].get("version")), p["source_registry_version"], "source registry"),
        (len(state["sources"].get("sources", [])), p["source_record_count"], "source count"),
        (str(state["ledger"].get("version")), p["change_ledger_version"], "change ledger"),
        (len(state["ledger"].get("changes", [])), p["change_ledger_count"], "change count"),
        (str(state["overlay"].get("version")), p["biosecurity_overlay_version"], "overlay"),
        (str(state["expectations"].get("version")), p["monitor_expectations_version"], "monitor expectations"),
        (len(state["expectations"].get("adapters", [])), p["monitor_adapter_count"], "monitor adapters"),
        (str(state["live_schema"].get("version")), p["live_schema_version"], "Live schema"),
        (len(state["live_observations"].get("observations", [])), p["live_observation_count"], "Live observations"),
        (len(state["live_evidence"].get("evidence", [])), p["live_evidence_count"], "Live evidence"),
        (str(state["analysis_schema"].get("version")), p["analysis_schema_version"], "Analysis schema"),
        (str(state["analysis_reviews"].get("version")), p["analysis_reviews_version"], "Analysis reviews version"),
        (len(state["analysis_reviews"].get("reviews", [])), p["analysis_review_count"], "Analysis reviews"),
        (str(state["analysis_evidence"].get("version")), p["analysis_evidence_version"], "Analysis evidence version"),
        (len(state["analysis_evidence"].get("evidence", [])), p["analysis_evidence_count"], "Analysis evidence"),
    ]
    for actual, expected, label in checks:
        require(actual == expected, f"BH exact prestate drift: {label}: {actual!r} != {expected!r}")
    require(state["overlay"].get("canonical_checkpoint") == p["biosecurity_overlay_checkpoint"], "BH overlay checkpoint drift")

    target = by_occurrence(state["canonical"]).get(TARGET_ID)
    require(target is not None, "BH target occurrence missing")
    for key, value in p["target"].items():
        require(target.get(key) == value, f"BH target precondition drift: {key}")

    sources = by_source(state["sources"])
    for source_id in p["required_source_ids"]:
        require(source_id in sources, f"BH required source missing: {source_id}")

    reuters = related_rows(target, REUTERS_ID)
    spa = related_rows(target, SPA_ID)
    require(len(reuters) == 1 and reuters[0].get("role") == p["required_reuters_role"], "BH Reuters history drift")
    require(len(spa) == 1 and spa[0].get("role") == p["required_spa_role"], "BH SPA history drift")
    require(spa[0].get("primary_opec_provenance_state") == p["required_spa_primary_state"], "BH historical SPA pending marker drift")
    require(not related_rows(target, OPEC_ID), "BH OPEC outcome provenance already present")
    require(plan["provenance_basis"]["change_id"] not in {x.get("change_id") for x in state["ledger"].get("changes", [])}, "BH change already present")
    validate_layers(state)


def ledger_entry(before: dict, after: dict, plan: dict, committed_at: str) -> dict:
    basis = plan["provenance_basis"]
    selection = plan["selection"]
    return {
        "change_id": basis["change_id"],
        "occurrence_id": TARGET_ID,
        "change_type": basis["change_type"],
        "old_values": {
            "lifecycle_status": before.get("lifecycle_status"),
            "last_successful_assertion_id": before.get("last_successful_assertion_id"),
            "competent_opec_primary_outcome_provenance": "REQUIRED_WHEN_RETRIEVABLE",
            "reuters_fallback_source_id": REUTERS_ID,
            "spa_confirmation_source_id": SPA_ID
        },
        "new_values": {
            "lifecycle_status": after.get("lifecycle_status"),
            "last_successful_assertion_id": after.get("last_successful_assertion_id"),
            "competent_source_id": OPEC_ID,
            "competent_source_url": selection["official_outcome_url"],
            "competent_source_class": selection["official_outcome_class"],
            "primary_opec_provenance_state": basis["primary_opec_provenance_state"],
            "reuters_fallback_preserved": True,
            "spa_confirmation_preserved": True
        },
        "source_assertion_id": basis["assertion_id"],
        "review_state": "APPROVED_FOR_CANONICAL_COMMIT",
        "reviewed_at": committed_at,
        "review_basis": [
            selection["official_outcome_url"],
            basis["review_reason"],
            "OPEC is the competent issuing institution for the governed schedule/decision source WSSRC-COM-001.",
            "The OPEC release establishes the meeting civil date and policy outcome but no canonical meeting clock time.",
            "BE Reuters and BG SPA provenance remain preserved as historical evidence.",
            "No 4 October occurrence is created by BH; no Live, Analysis, monitor or calendar write gate is opened."
        ],
        "commit_mode": "REVIEWED_COMPETENT_PRIMARY_PROVENANCE_RECOVERY_BH",
        "committed_at": committed_at,
        "registry_version_before": plan["preconditions"]["canonical_registry_version"],
        "registry_version_after": plan["postconditions"]["canonical_registry_version"],
        "canonical_mutation_committed": True,
        "automatic_canonical_commit": False,
        "google_calendar_write": False
    }


def build_post_state(state: dict[str, dict], plan: dict, committed_at: str) -> dict[str, dict]:
    assert_exact_prestate(state, plan)
    out = copy.deepcopy(state)
    target = by_occurrence(out["canonical"])[TARGET_ID]
    before = by_occurrence(state["canonical"])[TARGET_ID]
    basis = plan["provenance_basis"]
    selection = plan["selection"]
    post = plan["postconditions"]

    target["last_successful_assertion_id"] = basis["assertion_id"]
    target.setdefault("related_documents", []).append({
        "source_id": OPEC_ID,
        "role": basis["related_document_role"],
        "source_locator": selection["official_outcome_url"],
        "primary_opec_provenance_state": basis["primary_opec_provenance_state"]
    })
    out["canonical"].update(
        version=post["canonical_registry_version"],
        reference_date=plan["reference_date"],
        record_count=len(out["canonical"].get("records", []))
    )
    out["ledger"].setdefault("changes", []).append(ledger_entry(before, target, plan, committed_at))
    out["ledger"].update(version=post["change_ledger_version"], reference_date=plan["reference_date"])
    out["overlay"]["version"] = post["biosecurity_overlay_version"]
    out["overlay"]["canonical_checkpoint"] = copy.deepcopy(post["biosecurity_overlay_checkpoint"])
    assert_exact_poststate(state, out, plan)
    return out


def assert_exact_poststate(before: dict[str, dict], after: dict[str, dict], plan: dict) -> None:
    post = plan["postconditions"]
    require((str(after["canonical"].get("version")), len(after["canonical"].get("records", []))) == (post["canonical_registry_version"], post["canonical_record_count"]), "BH canonical target mismatch")
    require((str(after["sources"].get("version")), len(after["sources"].get("sources", []))) == (post["source_registry_version"], post["source_record_count"]), "BH source target mismatch")
    require((str(after["ledger"].get("version")), len(after["ledger"].get("changes", []))) == (post["change_ledger_version"], post["change_ledger_count"]), "BH ledger target mismatch")
    require(str(after["overlay"].get("version")) == post["biosecurity_overlay_version"], "BH overlay version mismatch")
    require(after["overlay"].get("canonical_checkpoint") == post["biosecurity_overlay_checkpoint"], "BH overlay checkpoint mismatch")
    require(overlay_semantics(after["overlay"]) == overlay_semantics(before["overlay"]), "BH changed overlay semantics")

    require(after["sources"] == before["sources"], "BH mutated Source Registry")
    for key in ("canonical_schema", "expectations", "operations", "review_contract", "review_decisions", "live_schema", "live_observations", "live_evidence", "analysis_schema", "analysis_reviews", "analysis_evidence"):
        require(after[key] == before[key], f"BH changed protected layer {key}")

    c0 = by_occurrence(before["canonical"])
    c1 = by_occurrence(after["canonical"])
    require(list(c0) == list(c1), "BH changed Canonical identity/order")
    changed_occurrences = [oid for oid in c0 if c0[oid] != c1[oid]]
    require(changed_occurrences == [TARGET_ID], f"BH changed unexpected occurrences: {changed_occurrences}")
    t0, t1 = c0[TARGET_ID], c1[TARGET_ID]
    changed_fields = {key for key in set(t0) | set(t1) if t0.get(key) != t1.get(key)}
    require(changed_fields == {"last_successful_assertion_id", "related_documents"}, f"BH target field boundary drift: {changed_fields}")
    for key in ("occurrence_id", "series_id", "source_id", "canonical_name", "category", "event_type", "certainty_status", "lifecycle_status", "start_local", "start_utc", "source_timezone", "timing_type", "time_precision", "time_status", "intrinsic_importance", "expected_market_sensitivity", "primary_source_assertion_id", "status_history", "last_verified_at"):
        require(t0.get(key) == t1.get(key), f"BH changed protected target field {key}")
    require(t1.get("lifecycle_status") == "COMPLETED", "BH lifecycle regression")
    require(t1.get("start_local") == "2026-09-06" and t1.get("start_utc") is None and t1.get("source_timezone") is None, "BH time regression")
    require(related_rows(t1, REUTERS_ID) == related_rows(t0, REUTERS_ID), "BH rewrote Reuters history")
    require(related_rows(t1, SPA_ID) == related_rows(t0, SPA_ID), "BH rewrote SPA history")
    primary = related_rows(t1, OPEC_ID)
    require(len(primary) == 1, "BH competent OPEC related document missing/duplicated")
    require(primary[0].get("primary_opec_provenance_state") == plan["provenance_basis"]["primary_opec_provenance_state"], "BH competent OPEC state mismatch")

    matches = [x for x in after["ledger"].get("changes", []) if x.get("change_id") == plan["provenance_basis"]["change_id"]]
    require(len(matches) == 1, "BH change ledger entry missing/duplicated")
    require(matches[0].get("change_type") == "SOURCE_PROVENANCE_PRIMARY_RECOVERY", "BH change type mismatch")
    require(not matches[0].get("automatic_canonical_commit") and not matches[0].get("google_calendar_write"), "BH write gates opened")

    for row in after["canonical"].get("records", []):
        require(not (row.get("series_id") == plan["selection"]["series_id"] and str(row.get("start_local", "")).startswith("2026-10-04")), "BH created prohibited 4 October voluntary-adjustment occurrence")
    validate_layers(after)


def is_materialised(state: dict[str, dict], plan: dict) -> bool:
    target = by_occurrence(state["canonical"]).get(TARGET_ID)
    if target is None:
        return False
    change_present = plan["provenance_basis"]["change_id"] in {x.get("change_id") for x in state["ledger"].get("changes", [])}
    doc_present = any(
        item.get("role") == plan["provenance_basis"]["related_document_role"]
        and item.get("source_locator") == plan["selection"]["official_outcome_url"]
        for item in related_rows(target, OPEC_ID)
    )
    if change_present != doc_present:
        require(False, "BH partial materialisation detected")
    return change_present and doc_present


def assert_materialised_or_descendant(state: dict[str, dict], plan: dict) -> None:
    post = plan["postconditions"]
    require(version_at_least(str(state["canonical"].get("version")), post["canonical_registry_version"]), "BH descendant canonical version regressed")
    require(len(state["canonical"].get("records", [])) >= post["canonical_record_count"], "BH descendant canonical population regressed")
    require(version_at_least(str(state["sources"].get("version")), post["source_registry_version"]), "BH descendant source version regressed")
    require(len(state["sources"].get("sources", [])) >= post["source_record_count"], "BH descendant source population regressed")
    require(version_at_least(str(state["ledger"].get("version")), post["change_ledger_version"]), "BH descendant ledger version regressed")
    require(len(state["ledger"].get("changes", [])) >= post["change_ledger_count"], "BH descendant ledger population regressed")
    target = by_occurrence(state["canonical"]).get(TARGET_ID)
    require(target is not None, "BH descendant target missing")
    require(target.get("lifecycle_status") == "COMPLETED" and target.get("start_local") == "2026-09-06" and target.get("start_utc") is None, "BH descendant lifecycle/time regression")
    require(len(related_rows(target, REUTERS_ID)) == 1, "BH descendant Reuters history missing")
    require(len(related_rows(target, SPA_ID)) == 1, "BH descendant SPA history missing")
    primary = [item for item in related_rows(target, OPEC_ID) if item.get("role") == plan["provenance_basis"]["related_document_role"]]
    require(len(primary) == 1 and primary[0].get("source_locator") == plan["selection"]["official_outcome_url"], "BH descendant competent OPEC evidence missing")
    require(plan["provenance_basis"]["change_id"] in {x.get("change_id") for x in state["ledger"].get("changes", [])}, "BH descendant change ledger identity missing")
    validate_layers(state)


def target_status(current: str, plan: dict) -> str:
    marker = "\n---\n\n# WORLD SIGNALS — project status / branch-recovery checkpoint"
    require(marker in current, "BH status history marker missing")
    historical = current.split(marker, 1)[1]
    p = plan["postconditions"]
    head = f'''# CURRENT RECOVERY OVERRIDE — POST-BG / BH OPEC COMPETENT-PRIMARY PROVENANCE RECOVERY

**Effective checkpoint:** 2026-09-08
**Exact post-BG main base:** `{plan['exact_base_main_sha']}`

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

BH closes the explicit BE/BG competent-OPEC-primary provenance debt for the already-completed **6 September 2026 OPEC+ voluntary-adjustment review** (`WSO-COM-A-0001`). The competent OPEC issuing institution now provides the official outcome release at `{plan['selection']['official_outcome_url']}`.

`WSSRC-COM-001` remains the stable OPEC schedule/decision authority. BE Reuters `WSSRC-COM-015` and BG SPA `WSSRC-COM-016` remain preserved as historical provenance; their earlier pending markers are not rewritten. BH changes no lifecycle, certainty, event date/time, Source population, Live record or Analysis record and creates no 4 October occurrence.

BF remains the sixth Live specimen. AZ remains the only production `live_input`; BA's Analysis revision grammar remains production-closed. Public Live projection, automatic ingestion, automatic Canonical commit and Google Calendar writes remain closed.

## Latest read-only monitor evidence at BH selection

Scheduled run `34111609049` (run 83) observed all eight configured adapters healthy, produced zero review candidates, left Canonical unchanged and retained automatic Canonical commit / Google Calendar write as false. This is evidence against advancing the monitor write gate in BH.

## Recovery order

1. `WORLD_SIGNALS_PROJECT_CHARTER.md`
2. this current override
3. `data/canonical/registry.json`, `data/sources/registry.json`, `data/monitor/*`, `data/live_intelligence/*`, `data/analysis/*`
4. latest pressure/transaction audits
5. current `main` SHA and Actions runs
---

# WORLD SIGNALS — project status / branch-recovery checkpoint'''
    return head + historical


def target_roadmap(current: str) -> str:
    heading = "### BH — OPEC competent-primary provenance recovery — DONE"
    if heading in current:
        return current
    needle = "## Stage 8 — prospective Live Intelligence → Analysis linkage"
    require(needle in current, "BH roadmap insertion point missing")
    section = '''### BH — OPEC competent-primary provenance recovery — DONE

BH closes the provenance condition deliberately left open by BE and BG. The competent OPEC issuing institution now exposes the official 6 September 2026 outcome release confirming that the seven participating countries met and maintained September required production for October.

BH reuses `WSSRC-COM-001`; it creates no new source object or occurrence. Reuters `WSSRC-COM-015` and SPA `WSSRC-COM-016` remain preserved as historical evidence, including the fact that OPEC-primary provenance was still pending at their review checkpoints. The later OPEC related-document assertion and reviewed Change Ledger entry satisfy that requirement without rewriting history.

Event timing remains `CIVIL_DATE` on 6 September 2026 with no invented clock time. Lifecycle remains `COMPLETED`. Monitor, Live Intelligence and Analysis populations are unchanged; no second Live→Analysis link, Analysis revision, automatic Canonical commit or Calendar write is opened.

A standalone OPEC Analysis review remains a separate future pressure decision, not a consequence of queue status or BH provenance repair.

'''
    return current.replace(needle, section + needle, 1)


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-only", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    plan = load(PLAN_PATH)
    state = load_state()
    if is_materialised(state, plan):
        assert_materialised_or_descendant(state, plan)
        print("BH target already materialised and descendant-safe")
        return

    candidate = build_post_state(
        state,
        plan,
        datetime.now(ZoneInfo("Australia/Melbourne")).isoformat(timespec="seconds")
    )
    status = target_status(STATUS_PATH.read_text(encoding="utf-8"), plan)
    roadmap = target_roadmap(ROADMAP_PATH.read_text(encoding="utf-8"))
    if args.check_only:
        print("BH check-only PASS: competent OPEC primary provenance would close BE/BG debt with no population growth")
        return
    require(os.environ.get(APPLY_ENV) == "YES", f"BH write gate closed: set {APPLY_ENV}=YES")
    dump(CANONICAL_PATH, candidate["canonical"])
    dump(LEDGER_PATH, candidate["ledger"])
    dump(OVERLAY_PATH, candidate["overlay"])
    STATUS_PATH.write_text(status, encoding="utf-8")
    ROADMAP_PATH.write_text(roadmap, encoding="utf-8")
    print("BH controlled materialisation complete")


if __name__ == "__main__":
    main()
