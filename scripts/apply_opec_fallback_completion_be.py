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
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.world_signals.analytical_overlays import validate_biosecurity_overlay
from src.world_signals.analysis import analysis_population_readiness, validate_analysis
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
PLAN_PATH = ROOT / "data/coverage/OPEC_FALLBACK_COMPLETION_BE_PLAN_v0.1.json"

APPLY_ENV = "WORLD_SIGNALS_APPLY_OPEC_FALLBACK_COMPLETION_BE"
APPLY_VALUE = "YES"
TARGET_ID = "WSO-COM-A-0001"
COMPLETION_SOURCE_ID = "WSSRC-COM-015"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now_melbourne() -> str:
    return datetime.now(ZoneInfo("Australia/Melbourne")).isoformat(timespec="seconds")


def overlay_semantics(value: dict) -> dict:
    return {k: copy.deepcopy(v) for k, v in value.items() if k not in {"version", "canonical_checkpoint"}}


def by_occurrence(registry: dict) -> dict[str, dict]:
    return {row.get("occurrence_id"): row for row in registry.get("records", [])}


def by_source(sources: dict) -> dict[str, dict]:
    return {row.get("source_id"): row for row in sources.get("sources", [])}


def exact_subset(row: dict, expected: dict, label: str, errors: list[str]) -> None:
    for key, value in expected.items():
        if row.get(key) != value:
            errors.append(f"{label} {key}: expected {value!r}, found {row.get(key)!r}")


def protected_paths() -> dict[str, Path]:
    return {
        "canonical_schema": CANONICAL_SCHEMA_PATH,
        "monitor_expectations": EXPECTATIONS_PATH,
        "monitor_operations": OPERATIONS_PATH,
        "review_candidate_state_contract": REVIEW_CONTRACT_PATH,
        "review_decisions": REVIEW_DECISIONS_PATH,
        "live_schema": LIVE_SCHEMA_PATH,
        "live_observations": LIVE_OBSERVATIONS_PATH,
        "live_evidence": LIVE_EVIDENCE_PATH,
        "analysis_schema": ANALYSIS_SCHEMA_PATH,
        "analysis_reviews": ANALYSIS_REVIEWS_PATH,
        "analysis_evidence": ANALYSIS_EVIDENCE_PATH,
    }


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


def preflight(state: dict[str, dict], plan: dict) -> None:
    p = plan["preconditions"]
    errors: list[str] = []
    canonical = state["canonical"]
    sources = state["sources"]
    ledger = state["ledger"]
    overlay = state["overlay"]
    expectations = state["expectations"]
    live_schema = state["live_schema"]
    live_observations = state["live_observations"]
    live_evidence = state["live_evidence"]
    analysis_schema = state["analysis_schema"]
    reviews = state["analysis_reviews"]
    evidence = state["analysis_evidence"]

    checks = [
        (str(state["canonical_schema"].get("version")) == p["canonical_schema_version"], "canonical schema version drift"),
        (str(canonical.get("version")) == p["canonical_registry_version"], "canonical registry version drift"),
        (canonical.get("record_count") == p["canonical_record_count"] == len(canonical.get("records", [])), "canonical record count drift"),
        (str(sources.get("version")) == p["source_registry_version"], "source registry version drift"),
        (len(sources.get("sources", [])) == p["source_record_count"], "source record count drift"),
        (str(ledger.get("version")) == p["change_ledger_version"], "change ledger version drift"),
        (len(ledger.get("changes", [])) == p["change_ledger_count"], "change ledger count drift"),
        (str(overlay.get("version")) == p["biosecurity_overlay_version"], "biosecurity overlay version drift"),
        (overlay.get("canonical_checkpoint") == p["biosecurity_overlay_checkpoint"], "biosecurity overlay checkpoint drift"),
        (str(expectations.get("version")) == p["monitor_expectations_version"], "monitor expectations version drift"),
        (len(expectations.get("adapters", [])) == p["monitor_adapter_count"], "monitor adapter count drift"),
        (str(live_schema.get("version")) == p["live_schema_version"], "Live schema version drift"),
        (len(live_observations.get("observations", [])) == p["live_observation_count"], "Live observation count drift"),
        (len(live_evidence.get("evidence", [])) == p["live_evidence_count"], "Live evidence count drift"),
        (str(analysis_schema.get("version")) == p["analysis_schema_version"], "Analysis schema version drift"),
        (str(reviews.get("version")) == p["analysis_reviews_version"] and len(reviews.get("reviews", [])) == p["analysis_review_count"], "Analysis reviews drift"),
        (str(evidence.get("version")) == p["analysis_evidence_version"] and len(evidence.get("evidence", [])) == p["analysis_evidence_count"], "Analysis evidence drift"),
    ]
    errors.extend(label for ok, label in checks if not ok)

    occ = by_occurrence(canonical)
    if TARGET_ID not in occ:
        errors.append(f"missing target occurrence {TARGET_ID}")
    else:
        exact_subset(occ[TARGET_ID], p["target"], f"target {TARGET_ID}", errors)

    src = by_source(sources)
    for sid in p["required_absent_source_ids"]:
        if sid in src:
            errors.append(f"completion source already exists: {sid}")
    if plan["selection"]["schedule_source_id"] not in src:
        errors.append("missing governed OPEC schedule source")
    if plan["completion_basis"]["change_id"] in {row.get("change_id") for row in ledger.get("changes", [])}:
        errors.append("BE change identity already exists")

    readiness = analysis_population_readiness(analysis_schema, reviews, canonical)
    if readiness["eligible_completed_occurrence_count"] != p["eligible_completed_occurrence_count"]:
        errors.append(f"eligible completed pre-count drift: {readiness}")
    if readiness["reviewed_occurrence_count"] != p["reviewed_occurrence_count"]:
        errors.append("reviewed occurrence pre-count drift")

    registry_validation = validate_registry(canonical, sources)
    errors.extend(f"canonical pre-state: {e}" for e in registry_validation.errors)
    errors.extend(f"biosecurity pre-state: {e}" for e in validate_biosecurity_overlay(canonical, overlay))
    analysis_validation = validate_analysis(analysis_schema, evidence, reviews, canonical)
    errors.extend(f"Analysis pre-state: {e}" for e in analysis_validation.errors)

    if errors:
        raise SystemExit("BE PRECONDITION FAILED:\n- " + "\n- ".join(errors))


def patch_target(before: dict, plan: dict) -> dict:
    out = copy.deepcopy(before)
    basis = plan["completion_basis"]
    out["lifecycle_status"] = "COMPLETED"
    out["last_verified_at"] = plan["reference_date"]
    out["last_successful_assertion_id"] = basis["assertion_id"]
    out.setdefault("status_history", []).append({
        "as_of": plan["reference_date"],
        "certainty_status": out.get("certainty_status"),
        "lifecycle_status": "COMPLETED",
        "condition_state": out.get("condition_state", "NOT_REQUIRED"),
        "change_reason": basis["status_history_reason"],
        "source_assertion_id": basis["assertion_id"],
        "basis": (
            "Completion-only reputable-newswire fallback. Primary OPEC outcome provenance was not retrievable on the accessible/indexed primary surface at BE review time and remains pending."
        ),
        "primary_provenance_upgrade_state": basis["primary_provenance_upgrade_state"],
    })
    out.setdefault("related_documents", []).append({
        "source_id": plan["selection"]["completion_source_id"],
        "role": basis["related_document_role"],
        "source_locator": plan["selection"]["fallback_url"],
        "primary_provenance_upgrade_state": basis["primary_provenance_upgrade_state"],
    })
    return out


def build_ledger_entry(before: dict, after: dict, plan: dict, committed_at: str) -> dict:
    p = plan["preconditions"]
    post = plan["postconditions"]
    basis = plan["completion_basis"]
    selection = plan["selection"]
    return {
        "change_id": basis["change_id"],
        "occurrence_id": TARGET_ID,
        "change_type": "LIFECYCLE_AND_CERTAINTY_UPDATE",
        "old_values": {
            "certainty_status": before.get("certainty_status"),
            "lifecycle_status": before.get("lifecycle_status"),
            "last_verified_at": before.get("last_verified_at"),
            "last_successful_assertion_id": before.get("last_successful_assertion_id"),
        },
        "new_values": {
            "certainty_status": after.get("certainty_status"),
            "lifecycle_status": after.get("lifecycle_status"),
            "last_verified_at": after.get("last_verified_at"),
            "last_successful_assertion_id": after.get("last_successful_assertion_id"),
            "completion_source_id": COMPLETION_SOURCE_ID,
            "completion_source_url": selection["fallback_url"],
            "completion_source_class": selection["completion_source_class"],
            "primary_outcome_provenance_state": "PENDING_PRIMARY_UPGRADE",
        },
        "source_assertion_id": basis["assertion_id"],
        "review_state": "APPROVED_FOR_CANONICAL_COMMIT",
        "reviewed_at": committed_at,
        "review_basis": [
            selection["official_schedule_notice_url"],
            selection["fallback_url"],
            basis["status_history_reason"],
            "Charter source hierarchy permits a highly reputable newswire when primary material is unavailable; the fallback is explicitly not promoted to primary authority.",
            "Stable occurrence, series and schedule-source identities are preserved.",
            "Source-native civil-date/day precision and null UTC fields are preserved; no clock time is inferred.",
            "The Reuters-reported 4 October next-meeting date is not admitted by this transaction.",
        ],
        "commit_mode": "REVIEWED_FALLBACK_LIFECYCLE_REPAIR_BE",
        "committed_at": committed_at,
        "registry_version_before": p["canonical_registry_version"],
        "registry_version_after": post["canonical_registry_version"],
        "canonical_mutation_committed": True,
        "automatic_canonical_commit": False,
        "google_calendar_write": False,
    }


def build_post_state(state: dict[str, dict], plan: dict, committed_at: str) -> dict[str, dict]:
    preflight(state, plan)
    out = copy.deepcopy(state)
    post = plan["postconditions"]

    before_target = by_occurrence(state["canonical"])[TARGET_ID]
    target = by_occurrence(out["canonical"])[TARGET_ID]
    target.clear()
    target.update(patch_target(before_target, plan))

    out["canonical"]["version"] = post["canonical_registry_version"]
    out["canonical"]["reference_date"] = plan["reference_date"]
    out["canonical"]["record_count"] = len(out["canonical"]["records"])

    out["sources"]["sources"].append(copy.deepcopy(plan["completion_source"]))
    out["sources"]["version"] = post["source_registry_version"]
    out["sources"]["reference_date"] = plan["reference_date"]

    out["ledger"]["changes"].append(build_ledger_entry(before_target, target, plan, committed_at))
    out["ledger"]["version"] = post["change_ledger_version"]
    out["ledger"]["reference_date"] = plan["reference_date"]

    out["overlay"]["version"] = post["biosecurity_overlay_version"]
    out["overlay"]["canonical_checkpoint"] = copy.deepcopy(post["biosecurity_overlay_checkpoint"])

    validate_post_state(state, out, plan)
    return out


def validate_post_state(before: dict[str, dict], after: dict[str, dict], plan: dict) -> None:
    post = plan["postconditions"]
    errors: list[str] = []
    c0, c1 = before["canonical"], after["canonical"]
    s0, s1 = before["sources"], after["sources"]
    l0, l1 = before["ledger"], after["ledger"]
    o0, o1 = before["overlay"], after["overlay"]

    if (str(c1.get("version")), c1.get("record_count"), len(c1.get("records", []))) != (post["canonical_registry_version"], post["canonical_record_count"], post["canonical_record_count"]):
        errors.append("canonical post-state mismatch")
    if (str(s1.get("version")), len(s1.get("sources", []))) != (post["source_registry_version"], post["source_record_count"]):
        errors.append("source post-state mismatch")
    if (str(l1.get("version")), len(l1.get("changes", []))) != (post["change_ledger_version"], post["change_ledger_count"]):
        errors.append("ledger post-state mismatch")
    if str(o1.get("version")) != post["biosecurity_overlay_version"] or o1.get("canonical_checkpoint") != post["biosecurity_overlay_checkpoint"]:
        errors.append("overlay checkpoint post-state mismatch")
    if overlay_semantics(o0) != overlay_semantics(o1):
        errors.append("biosecurity overlay semantics changed")

    occ0, occ1 = by_occurrence(c0), by_occurrence(c1)
    if list(occ0) != list(occ1):
        errors.append("canonical occurrence identity/order changed")
    changed = [oid for oid in occ0 if occ0[oid] != occ1[oid]]
    if changed != [TARGET_ID]:
        errors.append(f"unexpected canonical row mutation scope: {changed}")

    before_target, after_target = occ0[TARGET_ID], occ1[TARGET_ID]
    allowed_fields = {"lifecycle_status", "last_verified_at", "last_successful_assertion_id", "status_history", "related_documents"}
    changed_fields = {k for k in set(before_target) | set(after_target) if before_target.get(k) != after_target.get(k)}
    if not changed_fields.issubset(allowed_fields):
        errors.append(f"target changed outside allowed fields: {sorted(changed_fields - allowed_fields)}")
    if after_target.get("lifecycle_status") != "COMPLETED" or after_target.get("certainty_status") != "CONFIRMED":
        errors.append("target lifecycle/certainty mismatch")
    for key in (
        "occurrence_id", "series_id", "source_id", "start_local", "end_local", "source_timezone",
        "start_utc", "end_utc", "timing_type", "time_precision", "all_day_semantics", "time_status",
        "time_basis", "primary_source_assertion_id", "event_type", "category", "intrinsic_importance",
        "expected_market_sensitivity", "canonical_name"
    ):
        if before_target.get(key) != after_target.get(key):
            errors.append(f"protected target field changed: {key}")
    if after_target.get("start_utc") is not None:
        errors.append("BE fabricated a canonical UTC timestamp")

    src0, src1 = by_source(s0), by_source(s1)
    for sid, row in src0.items():
        if src1.get(sid) != row:
            errors.append(f"pre-existing source changed: {sid}")
    source = src1.get(COMPLETION_SOURCE_ID)
    if not source:
        errors.append("missing BE fallback completion source")
    else:
        if source.get("canonical_dependency_count") != 0:
            errors.append("fallback source gained canonical schedule dependency")
        if source.get("institution") != "Reuters":
            errors.append("fallback provider mismatch")
        if source.get("automated_monitoring_use") != "PROHIBITED_OR_RIGHTS_HOLD":
            errors.append("fallback monitoring gate opened")
        if "no future occurrence" not in str(source.get("future_schedule_horizon", "")).lower():
            errors.append("fallback forward-schedule prohibition missing")

    if l1.get("changes", [])[:len(l0.get("changes", []))] != l0.get("changes", []):
        errors.append("historical Change Ledger entries changed")
    new_ledger = l1.get("changes", [])[len(l0.get("changes", [])):]
    if len(new_ledger) != 1 or new_ledger[0].get("change_id") != plan["completion_basis"]["change_id"]:
        errors.append("BE Change Ledger scope mismatch")
    elif new_ledger[0].get("new_values", {}).get("primary_outcome_provenance_state") != "PENDING_PRIMARY_UPGRADE":
        errors.append("primary provenance pending state missing from ledger")

    registry_validation = validate_registry(c1, s1)
    errors.extend(f"canonical validation: {e}" for e in registry_validation.errors)
    errors.extend(f"biosecurity validation: {e}" for e in validate_biosecurity_overlay(c1, o1))
    analysis_validation = validate_analysis(after["analysis_schema"], after["analysis_evidence"], after["analysis_reviews"], c1)
    errors.extend(f"Analysis validation: {e}" for e in analysis_validation.errors)

    readiness = analysis_population_readiness(after["analysis_schema"], after["analysis_reviews"], c1)
    if readiness["eligible_completed_occurrence_count"] != post["eligible_completed_occurrence_count"]:
        errors.append(f"eligible completed post-count mismatch: {readiness}")
    if readiness["reviewed_occurrence_count"] != post["reviewed_occurrence_count"]:
        errors.append("reviewed Analysis count changed")
    if post["eligible_completed_occurrence_count"] - post["reviewed_occurrence_count"] != post["completed_unreviewed_analysis_anchor_count"]:
        errors.append("completed/unreviewed arithmetic mismatch")

    for key in (
        "canonical_schema", "expectations", "operations", "review_contract", "review_decisions",
        "live_schema", "live_observations", "live_evidence", "analysis_schema", "analysis_reviews", "analysis_evidence"
    ):
        if before[key] != after[key]:
            errors.append(f"protected logical layer mutated in memory: {key}")

    # No future Oct 4 OPEC occurrence may appear as a side effect.
    for row in c1.get("records", []):
        if row.get("series_id") == plan["selection"]["series_id"] and str(row.get("start_local", "")).startswith("2026-10-04"):
            errors.append("BE created prohibited 4 October OPEC occurrence")

    if errors:
        raise SystemExit("BE POSTCONDITION FAILED:\n- " + "\n- ".join(errors))


def status_override(plan: dict) -> str:
    p = plan["postconditions"]
    return f'''# CURRENT RECOVERY OVERRIDE — POST-BD / BE OPEC FALLBACK LIFECYCLE COMPLETION

**Effective checkpoint:** 2026-09-07
**Exact post-BD main base:** `{plan['exact_base_main_sha']}`

This override supersedes stale "current" counts in the historical body below while preserving that body as an audit/recovery record. `WORLD_SIGNALS_PROJECT_CHARTER.md` remains authoritative; governed registry/contract files remain operational truth.

## Current governed state

- Canonical Registry: **v{p['canonical_registry_version']} / {p['canonical_record_count']} occurrences**
- Canonical schema: **v0.52**
- Source Registry: **v{p['source_registry_version']} / {p['source_record_count']} sources**
- reviewed Change Ledger: **v{p['change_ledger_version']} / {p['change_ledger_count']} entries**
- biosecurity overlay: **v{p['biosecurity_overlay_version']} @ canonical v{p['canonical_registry_version']} / {p['canonical_record_count']}**
- Source/Change Monitor expectations: **v0.10 / 8 configured adapters**
- Monitor operations policy: **v0.1**
- Live Intelligence: **v0.5 / 5 reviewed internal observations / 7 primary-official evidence rows / public observation projection CLOSED**
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

BE repairs one upstream lifecycle state: the already-scheduled **6 September 2026 OPEC+ voluntary-adjustment review** (`WSO-COM-A-0001`) moves `PLANNED → COMPLETED` after reviewed post-event verification. The competent OPEC primary outcome statement was not retrievable on the accessible/indexed primary surface at review time, so BE uses one tightly bounded Reuters completion-only fallback source under the Charter's reputable-newswire tier. The fallback is explicitly secondary and primary OPEC outcome provenance remains a future reviewed upgrade requirement.

BE does **not** create the Reuters-reported 4 October meeting, add a sixth Live observation, populate a second Live→Analysis link, open Analysis revision production, infer any event clock time, or change monitor configuration. `WSSRC-COM-001` remains the OPEC schedule/decision authority; `WSSRC-COM-015` has zero Canonical dependencies and no forward-schedule or automation authority.

BD remains the fifth pressure-audited Live specimen. BC remains the historical-checkpoint / legitimate-descendant contract. BA's Analysis revision-lineage grammar remains production-closed. AZ's inaugural Live-to-Analysis relationship remains the only production `live_input`.

## Current configured monitor cohort

Eight configured adapters: RBA FSR; Colombia SUIN/Socrata; EU CRA/Cellar; three EU CBAM legal-rule routes; ONS release-calendar RSS; EIA WPSR schedule. Route presence does not imply blanket source automation permission, and all routes remain review-only with automatic canonical commit disabled.

## Recovery order

1. `WORLD_SIGNALS_PROJECT_CHARTER.md`
2. this current override
3. `data/canonical/registry.json`, `data/sources/registry.json`, `data/monitor/*`, `data/live_intelligence/*`, `data/analysis/*`
4. latest pressure/transaction audits
5. current `main` SHA and Actions runs
'''


def update_status(plan: dict) -> None:
    text = STATUS_PATH.read_text(encoding="utf-8")
    marker = "\n---\n"
    if marker not in text:
        raise SystemExit("BE STATUS UPDATE FAILED: historical separator missing")
    _, historical = text.split(marker, 1)
    STATUS_PATH.write_text(status_override(plan).rstrip() + marker + historical, encoding="utf-8")


def update_roadmap() -> None:
    text = ROADMAP_PATH.read_text(encoding="utf-8")
    if "### BE — OPEC fallback lifecycle completion" in text:
        return
    marker = "## Stage 8 — prospective Live Intelligence → Analysis linkage"
    if marker not in text:
        raise SystemExit("BE ROADMAP UPDATE FAILED: Stage 8 marker missing")
    block = '''### BE — OPEC fallback lifecycle completion — DONE / PRIMARY PROVENANCE UPGRADE PENDING

BE repairs the existing 6 September 2026 OPEC+ voluntary-adjustment review from `PLANNED` to `COMPLETED` using one reviewed Reuters completion-only fallback because the competent OPEC outcome statement was not retrievable on the accessible/indexed primary surface at review time. The fallback does not displace `WSSRC-COM-001` as OPEC schedule/decision authority and is retained explicitly as secondary provenance pending a later primary-source upgrade.

BE creates no 4 October occurrence from secondary reporting, no sixth Live observation and no Analysis mutation. The repair raises the completed Analysis-eligible pool to 22 and leaves one completed/unreviewed OPEC anchor for a future pressure audit; queue completion is not the objective.

'''
    ROADMAP_PATH.write_text(text.replace(marker, block + marker, 1), encoding="utf-8")


def apply(post: dict[str, dict], plan: dict) -> None:
    before_hashes = {name: sha(path) for name, path in protected_paths().items()}
    dump(CANONICAL_PATH, post["canonical"])
    dump(SOURCE_PATH, post["sources"])
    dump(LEDGER_PATH, post["ledger"])
    dump(OVERLAY_PATH, post["overlay"])
    update_status(plan)
    update_roadmap()
    after_hashes = {name: sha(path) for name, path in protected_paths().items()}
    if before_hashes != after_hashes:
        raise SystemExit("BE MUTATION BOUNDARY FAILED: protected file changed")


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply the bounded WORLD SIGNALS OPEC fallback lifecycle completion BE.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check-only", action="store_true", help="Simulate and validate target state without writes.")
    group.add_argument("--apply", action="store_true", help="Write the guarded BE target state.")
    args = parser.parse_args()

    plan = load(PLAN_PATH)
    state = load_all()
    post = build_post_state(state, plan, now_melbourne())

    if not args.apply:
        readiness = analysis_population_readiness(post["analysis_schema"], post["analysis_reviews"], post["canonical"])
        print(json.dumps({
            "transaction": plan["transaction"],
            "mode": "CHECK_ONLY",
            "target_occurrence_id": TARGET_ID,
            "completion_source_id": COMPLETION_SOURCE_ID,
            "canonical_post_version": post["canonical"].get("version"),
            "source_post_version": post["sources"].get("version"),
            "ledger_post_version": post["ledger"].get("version"),
            "eligible_completed_occurrence_count": readiness["eligible_completed_occurrence_count"],
            "reviewed_occurrence_count": readiness["reviewed_occurrence_count"],
            "primary_provenance_upgrade_state": plan["completion_basis"]["primary_provenance_upgrade_state"],
            "october_4_created": False,
        }, indent=2))
        return

    if os.environ.get(APPLY_ENV) != APPLY_VALUE:
        raise SystemExit(f"APPLY BLOCKED: set {APPLY_ENV}={APPLY_VALUE}")
    apply(post, plan)
    print(f"Applied {plan['transaction']} with protected layers unchanged.")


if __name__ == "__main__":
    main()
