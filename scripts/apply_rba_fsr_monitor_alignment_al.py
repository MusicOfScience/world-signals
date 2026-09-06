#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.live_monitor import rba_fsr_review_candidates

PLAN_PATH = ROOT / "data/monitor/RBA_FSR_MONITOR_ALIGNMENT_AL_PLAN_v0.1.json"
AUDIT_PATH = ROOT / "data/monitor/RBA_FSR_MONITOR_ALIGNMENT_AL_TRANSACTION_AUDIT_v0.1.md"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
CANONICAL_SCHEMA_PATH = ROOT / "data/canonical/schema.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
OPERATIONS_PATH = ROOT / "data/monitor/operations_policy.json"
ANALYSIS_SCHEMA_PATH = ROOT / "data/analysis/schema.json"
REVIEWS_PATH = ROOT / "data/analysis/event_reviews.json"
EVIDENCE_PATH = ROOT / "data/analysis/evidence_registry.json"

APPLY_ENV = "WORLD_SIGNALS_APPLY_RBA_FSR_MONITOR_ALIGNMENT_AL"
RBA_ADAPTER = "RBA_FSR_RSS"
RBA_MARCH = "WSO-FIN-B-0004"
RBA_OCTOBER = "WSO-FIN-B-0001"

PROTECTED = {
    "canonical_registry": CANONICAL_PATH,
    "canonical_schema": CANONICAL_SCHEMA_PATH,
    "source_registry": SOURCES_PATH,
    "change_ledger": LEDGER_PATH,
    "biosecurity_overlay": OVERLAY_PATH,
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


def git_blob_sha(path: Path) -> str:
    return subprocess.check_output(
        ["git", "hash-object", str(path.relative_to(ROOT))], cwd=ROOT, text=True
    ).strip()


def protected_hashes() -> dict[str, str]:
    return {label: sha256(path) for label, path in PROTECTED.items()}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def adapter(expectations: dict[str, Any]) -> dict[str, Any]:
    matches = [
        row for row in expectations.get("adapters", [])
        if row.get("adapter_id") == RBA_ADAPTER
    ]
    require(len(matches) == 1, "AL requires exactly one RBA_FSR_RSS adapter")
    return matches[0]


def records_by_id(canonical: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        row.get("occurrence_id"): row
        for row in canonical.get("records", [])
        if row.get("occurrence_id")
    }


def exact_series_rows(reviews: dict[str, Any]) -> int:
    return sum(
        1
        for review in reviews.get("reviews", [])
        for movement in (review.get("what_moved") or [])
        if movement.get("measurement_precision") == "EXACT_TIMESTAMP_SERIES"
    )


def assert_dataset_state(plan: dict[str, Any], canonical: dict[str, Any], sources: dict[str, Any], ledger: dict[str, Any], overlay: dict[str, Any], expectations: dict[str, Any], analysis_schema: dict[str, Any], reviews: dict[str, Any], evidence: dict[str, Any]) -> None:
    pre = plan["preconditions"]
    checkpoint = overlay.get("canonical_checkpoint") or {}
    require((canonical.get("version"), len(canonical.get("records", []))) == (pre["canonical_registry_version"], pre["canonical_record_count"]), "AL canonical pre-state mismatch")
    require((sources.get("version"), len(sources.get("sources", []))) == (pre["source_registry_version"], pre["source_record_count"]), "AL source pre-state mismatch")
    require((ledger.get("version"), len(ledger.get("changes", []))) == (pre["change_ledger_version"], pre["change_ledger_count"]), "AL ledger pre-state mismatch")
    require(overlay.get("version") == pre["biosecurity_overlay_version"], "AL overlay version mismatch")
    require(checkpoint == pre["biosecurity_overlay_checkpoint"], "AL overlay checkpoint mismatch")
    require(analysis_schema.get("version") == pre["analysis_schema_version"], "AL Analysis schema pre-state mismatch")
    require((reviews.get("version"), len(reviews.get("reviews", []))) == (pre["analysis_reviews_version"], pre["analysis_review_count"]), "AL Analysis reviews pre-state mismatch")
    require((evidence.get("version"), len(evidence.get("evidence", []))) == (pre["analysis_evidence_version"], pre["analysis_evidence_count"]), "AL Analysis evidence pre-state mismatch")
    require(expectations.get("version") == pre["monitor_expectations_version"], "AL monitor expectations version mismatch")
    require(len(expectations.get("adapters", [])) == pre["monitor_adapter_count"], "AL monitor adapter count mismatch")
    require(git_blob_sha(EXPECTATIONS_PATH) == pre["monitor_expectations_blob_sha"], "AL monitor expectations blob drifted")
    require(expectations.get("automatic_canonical_commit") is False, "AL automatic canonical commit must remain false")
    require(expectations.get("google_calendar_write") is False, "AL Google Calendar write must remain false")

    cfg = adapter(expectations)
    require(cfg.get("source_id") == pre["rba_source_id"], "AL RBA source id drifted")
    require(cfg.get("canonical_occurrence_ids") == pre["rba_occurrence_ids"], "AL RBA monitor pre-scope drifted")
    require((cfg.get("matching") or {}) == plan["monitor_change"]["preserve_matching"], "AL RBA matching policy drifted")
    require(cfg.get("monitor_role") == plan["monitor_change"]["preserve_monitor_role"], "AL RBA monitor role drifted")
    require(cfg.get("automatic_commit_allowed") is plan["monitor_change"]["preserve_automatic_commit_allowed"], "AL RBA auto-commit guardrail drifted")

    by_id = records_by_id(canonical)
    for occurrence_id, expected in pre["required_canonical_occurrences"].items():
        row = by_id.get(occurrence_id)
        require(row is not None, f"AL missing canonical occurrence {occurrence_id}")
        require(row.get("series_id") == pre["rba_series_id"], f"AL {occurrence_id} series drifted")
        for key, value in expected.items():
            require(row.get(key) == value, f"AL {occurrence_id} {key} drifted")

    require(exact_series_rows(reviews) == pre.get("production_exact_timestamp_series_rows", 0), "AL production exact-series population drifted")


def current_march_item(plan: dict[str, Any]) -> SimpleNamespace:
    item = plan["preconditions"]["current_official_item"]
    return SimpleNamespace(
        title=item["title"],
        link=item["link"],
        pub_date_iso=item["publication_datetime"],
    )


def october_item() -> SimpleNamespace:
    return SimpleNamespace(
        title="Financial Stability Review - October 2026",
        link="https://www.rba.gov.au/publications/fsr/2026/oct/",
        pub_date_iso="2026-10-01T11:30:00+10:00",
    )


def prove_pre_defect(plan: dict[str, Any], canonical: dict[str, Any], expectations: dict[str, Any]) -> None:
    cfg = adapter(expectations)
    candidates, observations = rba_fsr_review_candidates(
        canonical.get("records", []), [current_march_item(plan)], cfg
    )
    require(candidates == [], "AL pre-state unexpectedly generated an RBA candidate")
    require(len(observations) == 1, "AL pre-state March item must yield one observation")
    require(observations[0].get("type") == plan["preconditions"]["current_official_item"]["expected_pre_observation"], "AL pre-state defect no longer reproduces")


def transform(expectations: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(expectations)
    change = plan["monitor_change"]
    require(out.get("version") == change["from_version"], "AL transform called on wrong monitor version")
    cfg = adapter(out)
    require(cfg.get("canonical_occurrence_ids") == change["preserve_occurrence_ids"], "AL transform monitor scope precondition failed")
    cfg["canonical_occurrence_ids"] = list(change["post_occurrence_ids"])
    out["version"] = change["to_version"]
    return out


def validate_candidate(plan: dict[str, Any], canonical: dict[str, Any], candidate: dict[str, Any]) -> None:
    post = plan["postconditions"]
    require(candidate.get("version") == post["monitor_expectations_version"], "AL monitor post-version mismatch")
    require(len(candidate.get("adapters", [])) == post["monitor_adapter_count"], "AL monitor post adapter count mismatch")
    require(candidate.get("automatic_canonical_commit") is False, "AL automatic canonical commit changed")
    require(candidate.get("google_calendar_write") is False, "AL Google Calendar write changed")
    cfg = adapter(candidate)
    require(cfg.get("canonical_occurrence_ids") == post["rba_occurrence_ids"], "AL RBA post-scope mismatch")
    require((cfg.get("matching") or {}) == plan["monitor_change"]["preserve_matching"], "AL matching policy changed")

    candidates, observations = rba_fsr_review_candidates(
        canonical.get("records", []), [current_march_item(plan)], cfg
    )
    require(candidates == [], "AL aligned March item must not generate review candidate")
    require(len(observations) == 1 and observations[0].get("type") == post["current_official_item_observation"], "AL March item did not resolve as already reflected")
    require(observations[0].get("occurrence_id") == RBA_MARCH, "AL March item resolved to wrong occurrence")

    future_candidates, future_observations = rba_fsr_review_candidates(
        canonical.get("records", []), [october_item()], cfg
    )
    require(future_observations == [], "AL October fixture unexpectedly became observation-only")
    require(len(future_candidates) == 1, "AL October fixture must generate one lifecycle review candidate")
    require(future_candidates[0].get("occurrence_id") == RBA_OCTOBER, "AL October fixture matched wrong occurrence")
    require(future_candidates[0].get("diff_type") == "LIFECYCLE_CHANGED", "AL October fixture should exercise lifecycle review only")
    require(future_candidates[0].get("automatic_commit_allowed") is False, "AL future review candidate must remain non-automatic")


def render_audit(plan: dict[str, Any], protected_before: dict[str, str], protected_after: dict[str, str]) -> str:
    return f'''# WORLD SIGNALS — RBA FSR monitor alignment AL transaction audit v0.1\n\n**Reference date:** {plan['reference_date']}\n**Exact base main:** `{plan['base_main_sha']}`\n**Architecture layer:** Source/Change Monitor only\n\n## Mutation\n\n- monitor expectations: **v{plan['monitor_change']['from_version']} → v{plan['monitor_change']['to_version']}**\n- `RBA_FSR_RSS.canonical_occurrence_ids`: `{plan['monitor_change']['preserve_occurrence_ids']}` → `{plan['monitor_change']['post_occurrence_ids']}`\n- matching window, source identity, monitor role and automatic-commit prohibition: unchanged\n\n## Regression contract\n\nThe official March 2026 RBA FSR item now resolves against `WSO-FIN-B-0004` as `RBA_PUBLICATION_ALREADY_REFLECTED` and generates no review candidate. A synthetic 1 October 2026 publication at the canonical clock time still resolves to `WSO-FIN-B-0001` and generates a non-automatic lifecycle review candidate, proving that adding the historical occurrence does not hijack the forward match.\n\n## Protected-state hash audit\n\nProtected datasets unchanged: **{protected_before == protected_after}**\n\n```json\n{json.dumps({'before': protected_before, 'after': protected_after}, indent=2)}\n```\n\n## Deliberate non-actions\n\n- no canonical registry/schema mutation\n- no source-registry mutation\n- no change-ledger mutation\n- no biosecurity-overlay mutation\n- no monitor-operations-policy mutation\n- no Analysis schema/review/evidence mutation\n- no exact market-data ingestion\n- no Calendar write\n- no dynamic all-series monitor-scope expansion\n- no auto-merge\n'''


def candidate_state() -> tuple[dict[str, Any], dict[str, str], dict[str, Any]]:
    plan = load(PLAN_PATH)
    require(plan.get("base_main_sha") == "72103267f90475b04c80129e03b41b605d4b7f58", "AL plan base SHA drifted")
    canonical = load(CANONICAL_PATH)
    sources = load(SOURCES_PATH)
    ledger = load(LEDGER_PATH)
    overlay = load(OVERLAY_PATH)
    expectations = load(EXPECTATIONS_PATH)
    analysis_schema = load(ANALYSIS_SCHEMA_PATH)
    reviews = load(REVIEWS_PATH)
    evidence = load(EVIDENCE_PATH)

    assert_dataset_state(plan, canonical, sources, ledger, overlay, expectations, analysis_schema, reviews, evidence)
    protected_before = protected_hashes()
    prove_pre_defect(plan, canonical, expectations)
    candidate = transform(expectations, plan)
    validate_candidate(plan, canonical, candidate)
    require(protected_hashes() == protected_before, "AL read-only simulation mutated protected state")
    return candidate, protected_before, plan


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    require(args.check ^ args.write, "choose exactly one of --check or --write")

    candidate, protected_before, plan = candidate_state()
    if args.check:
        print("AL_CHECK_OK")
        print(json.dumps({
            "monitor_expectations": [plan["monitor_change"]["from_version"], plan["monitor_change"]["to_version"]],
            "rba_scope": plan["monitor_change"]["post_occurrence_ids"],
            "march_observation": plan["postconditions"]["current_official_item_observation"],
            "exact_timestamp_series_rows": plan["postconditions"]["production_exact_timestamp_series_rows"],
        }, indent=2))
        return

    require(os.environ.get(APPLY_ENV) == "1", f"AL write requires {APPLY_ENV}=1")
    dump(EXPECTATIONS_PATH, candidate)
    protected_after = protected_hashes()
    require(protected_after == protected_before, "AL write mutated protected datasets")
    validate_candidate(plan, load(CANONICAL_PATH), load(EXPECTATIONS_PATH))
    AUDIT_PATH.write_text(render_audit(plan, protected_before, protected_after), encoding="utf-8")
    print("AL_WRITE_OK")


if __name__ == "__main__":
    main()
