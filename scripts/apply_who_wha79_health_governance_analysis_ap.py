#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.analysis import analysis_population_readiness, validate_analysis

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
PLAN_PATH = ROOT / "data/analysis/WHO_WHA79_HEALTH_GOVERNANCE_ANALYSIS_AP_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/analysis/WHO_WHA79_HEALTH_GOVERNANCE_ANALYSIS_AP_PAYLOAD_v0.1.json"
AUDIT_PATH = ROOT / "data/analysis/WHO_WHA79_HEALTH_GOVERNANCE_ANALYSIS_AP_TRANSACTION_AUDIT_v0.1.md"

APPLY_ENV = "WORLD_SIGNALS_APPLY_ANALYSIS_AP"

PROTECTED = {
    "canonical_registry": CANONICAL_PATH,
    "canonical_schema": CANONICAL_SCHEMA_PATH,
    "source_registry": SOURCES_PATH,
    "change_ledger": LEDGER_PATH,
    "biosecurity_overlay": OVERLAY_PATH,
    "monitor_expectations": EXPECTATIONS_PATH,
    "monitor_operations_policy": OPERATIONS_PATH,
    "analysis_schema": ANALYSIS_SCHEMA_PATH,
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_hashes() -> dict[str, str]:
    return {name: sha256(path) for name, path in PROTECTED.items()}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def exact_timestamp_series_rows(reviews: dict[str, Any]) -> int:
    return sum(
        1
        for review in reviews.get("reviews", [])
        for movement in (review.get("what_moved") or [])
        if movement.get("measurement_precision") == "EXACT_TIMESTAMP_SERIES"
    )


def assert_pre(
    plan: dict[str, Any],
    canonical: dict[str, Any],
    sources: dict[str, Any],
    ledger: dict[str, Any],
    overlay: dict[str, Any],
    expectations: dict[str, Any],
    schema: dict[str, Any],
    reviews: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    pre = plan["preconditions"]
    require((canonical.get("version"), len(canonical.get("records", []))) == (pre["canonical_registry_version"], pre["canonical_record_count"]), "AP canonical pre-state mismatch")
    require((sources.get("version"), len(sources.get("sources", []))) == (pre["source_registry_version"], pre["source_record_count"]), "AP source pre-state mismatch")
    require((ledger.get("version"), len(ledger.get("changes", []))) == (pre["change_ledger_version"], pre["change_ledger_count"]), "AP ledger pre-state mismatch")
    require((overlay.get("version"), overlay.get("canonical_checkpoint")) == (pre["biosecurity_overlay_version"], pre["biosecurity_overlay_checkpoint"]), "AP overlay pre-state mismatch")
    require(expectations.get("version") == pre["monitor_expectations_version"], "AP monitor expectations pre-state mismatch")
    require(schema.get("version") == pre["analysis_schema_version"], "AP Analysis schema pre-state mismatch")
    require((reviews.get("version"), len(reviews.get("reviews", []))) == (pre["analysis_reviews_version"], pre["analysis_review_count"]), "AP reviews pre-state mismatch")
    require(reviews.get("canonical_checkpoint") == pre["analysis_reviews_canonical_checkpoint"], "AP reviews canonical checkpoint mismatch")
    require((evidence.get("version"), len(evidence.get("evidence", []))) == (pre["analysis_evidence_version"], pre["analysis_evidence_count"]), "AP evidence pre-state mismatch")

    readiness = analysis_population_readiness(schema, reviews, canonical)
    require(readiness["eligible_completed_occurrence_count"] == pre["eligible_completed_occurrence_count"], "AP eligible completed count drifted")
    require(readiness["reviewed_occurrence_count"] == pre["reviewed_occurrence_count"], "AP reviewed count drifted")
    require(readiness["reviewed_event_type_diversity"] == pre["reviewed_event_type_diversity"], "AP reviewed diversity drifted")
    require(exact_timestamp_series_rows(reviews) == pre["required_pre_analysis_exact_timestamp_series_rows"], "AP exact-series pre-state drifted")

    target = next((row for row in canonical["records"] if row.get("occurrence_id") == pre["required_target_occurrence_id"]), None)
    require(target is not None, "AP target canonical occurrence missing")
    checks = {
        "series_id": pre["required_target_series_id"],
        "source_id": pre["required_target_source_id"],
        "category": pre["required_target_category"],
        "event_type": pre["required_target_event_type"],
        "lifecycle_status": pre["required_target_lifecycle"],
        "timing_type": pre["required_target_timing_type"],
        "start_local": pre["required_target_start_local"],
        "end_local": pre["required_target_end_local"],
        "source_timezone": pre["required_target_source_timezone"],
        "start_utc": pre["required_target_start_utc"],
        "end_utc": pre["required_target_end_utc"],
        "time_precision": pre["required_target_time_precision"],
    }
    for field, expected in checks.items():
        require(target.get(field) == expected, f"AP target {field} mismatch: {target.get(field)!r} != {expected!r}")
    require(target.get("all_day_semantics") is True, "AP target must retain all-day multi-day semantics")

    existing = {row.get("analysis_id") for row in reviews.get("reviews", [])}
    for analysis_id in pre["required_absent_analysis_ids"]:
        require(analysis_id not in existing, f"AP analysis already exists: {analysis_id}")


def assert_payload(
    plan: dict[str, Any],
    payload: dict[str, Any],
    canonical: dict[str, Any],
    reviews: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    require(payload.get("tranche") == "WHO_WHA79_HEALTH_GOVERNANCE_ANALYSIS_AP", "wrong AP payload")
    require(len(payload.get("reviews", [])) == 1, "AP must contain exactly one review")
    review = payload["reviews"][0]
    require(review.get("analysis_id") == plan["new_analysis_id"], "AP analysis ID differs from plan")
    require(review.get("canonical_occurrence_id") == plan["selection"]["selected_occurrence_id"], "AP target differs from plan")
    require(review.get("canonical_release_utc") is None, "AP may not invent a UTC release for a multi-day local event")
    require((review.get("what_surprised") or {}).get("status") == "NOT_ESTABLISHED", "AP surprise must remain NOT_ESTABLISHED")
    require((review.get("what_surprised") or {}).get("comparisons") == [], "AP must not fabricate surprise comparisons")
    require(review.get("what_moved") == [], "AP must not manufacture a WHA79-specific market response")

    benchmarks = (review.get("what_was_expected") or {}).get("benchmarks") or []
    require(len(benchmarks) == 1, "AP must preserve exactly one official PABS guidance benchmark")
    require(benchmarks[0].get("benchmark_type") == "OFFICIAL_PRIOR_GUIDANCE", "AP PABS guidance benchmark class drifted")

    connection = review.get("what_appears_connected") or {}
    require(connection.get("interaction_type") == "LEGAL_OR_OPERATIONAL_DEPENDENCY", "AP interaction type mismatch")
    require(connection.get("causal_status") == "NOT_A_CAUSAL_CLAIM", "AP causal boundary drifted")
    require(connection.get("confidence") == "HIGH", "AP connection confidence mismatch")
    require((review.get("second_order_effects") or {}).get("status") == "OBSERVED", "AP later IGWG process propagation must remain observed")
    require(len(review.get("what_may_be_noise") or []) >= 6, "AP must retain decision-semantic noise checks")
    require(len(review.get("alternative_explanations") or []) >= 3, "AP must retain alternatives")
    require(len(review.get("falsifiers") or []) >= 8, "AP must retain falsifiers")

    evidence_rows = payload.get("evidence", [])
    new_ids = {row.get("evidence_id") for row in evidence_rows}
    require(new_ids == set(plan["new_evidence_ids"]), "AP evidence IDs differ from plan")
    require(len(evidence_rows) == 7, "AP evidence packet must contain exactly seven rows")
    require(all(row.get("evidence_class") == "PRIMARY_OFFICIAL" for row in evidence_rows), "AP evidence packet must remain first-party official")
    require(all(row.get("canonical_provenance_effect") == "NONE" for row in evidence_rows), "AP evidence may not mutate canonical provenance")
    require(new_ids.isdisjoint({row.get("evidence_id") for row in evidence.get("evidence", [])}), "AP would duplicate evidence IDs")
    require(review["analysis_id"] not in {row.get("analysis_id") for row in reviews.get("reviews", [])}, "AP would duplicate review ID")

    target = next(row for row in canonical["records"] if row.get("occurrence_id") == review["canonical_occurrence_id"])
    require(review.get("canonical_series_id") == target.get("series_id"), "AP review series mismatch")
    require(review.get("canonical_event_type") == target.get("event_type"), "AP review event type mismatch")
    require(review.get("canonical_institution") == target.get("institution"), "AP review institution mismatch")
    require(review.get("canonical_release_utc") == target.get("start_utc"), "AP review UTC mismatch")

    required_false = (
        "assembly_completion_implies_resolution_implementation",
        "decision_count_is_scalar_success_metric",
        "pabs_continuation_equals_pabs_annex_adoption",
        "pabs_continuation_equals_pandemic_agreement_ratification",
        "gha_process_establishment_equals_reform_completion",
        "amr_plan_adoption_equals_health_effect",
        "official_pre_event_process_guidance_is_aggregate_consensus_forecast",
        "same_period_health_emergency_is_caused_by_assembly",
        "later_igwg_meeting_retimes_wha79",
        "analytical_evidence_resolves_missing_canonical_utc",
        "empty_market_response_is_missing_work",
        "queue_completion_is_population_objective",
        "market_structure_gap_must_be_filled_next",
        "prior_ao_live_count_is_permanent_ceiling",
        "auto_merge",
    )
    for key in required_false:
        require(plan["guardrails"].get(key) is False, f"AP guardrail must remain false: {key}")


def transform(
    plan: dict[str, Any],
    payload: dict[str, Any],
    canonical: dict[str, Any],
    sources: dict[str, Any],
    ledger: dict[str, Any],
    overlay: dict[str, Any],
    expectations: dict[str, Any],
    schema: dict[str, Any],
    reviews: dict[str, Any],
    evidence: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    assert_pre(plan, canonical, sources, ledger, overlay, expectations, schema, reviews, evidence)
    assert_payload(plan, payload, canonical, reviews, evidence)
    post = plan["postconditions"]

    new_reviews = copy.deepcopy(reviews)
    new_evidence = copy.deepcopy(evidence)
    new_reviews["version"] = post["analysis_reviews_version"]
    new_reviews["reference_date"] = plan["reference_date"]
    new_reviews["canonical_checkpoint"] = copy.deepcopy(post["analysis_reviews_canonical_checkpoint"])
    new_reviews["reviews"].extend(copy.deepcopy(payload["reviews"]))
    new_evidence["version"] = post["analysis_evidence_version"]
    new_evidence["reference_date"] = plan["reference_date"]
    new_evidence["evidence"].extend(copy.deepcopy(payload["evidence"]))

    report = validate_analysis(schema, new_evidence, new_reviews, canonical)
    require(report.ok, "AP post-state failed Analysis validation: " + "; ".join(report.errors))
    readiness = analysis_population_readiness(schema, new_reviews, canonical)
    require((new_reviews["version"], len(new_reviews["reviews"])) == (post["analysis_reviews_version"], post["analysis_review_count"]), "AP review post-state mismatch")
    require((new_evidence["version"], len(new_evidence["evidence"])) == (post["analysis_evidence_version"], post["analysis_evidence_count"]), "AP evidence post-state mismatch")
    require(readiness["eligible_completed_occurrence_count"] == post["eligible_completed_occurrence_count"], "AP eligible count mismatch")
    require(readiness["reviewed_occurrence_count"] == post["reviewed_occurrence_count"], "AP reviewed count mismatch")
    require(readiness["reviewed_event_type_diversity"] == post["reviewed_event_type_diversity"], "AP diversity mismatch")
    require(readiness["reviewed_by_event_type"].get("HEALTH_GOVERNANCE_EVENT", 0) == post["reviewed_health_governance_event_occurrence_count"], "AP health-governance reviewed count mismatch")
    require(readiness["broad_population_state"] == post["broad_population_state"], "AP readiness state mismatch")
    require(exact_timestamp_series_rows(new_reviews) == post["post_analysis_exact_timestamp_series_rows"], "AP must not fabricate exact market series")

    reviewed_ids = set(readiness["reviewed_occurrence_ids"])
    remaining = sorted(
        row["occurrence_id"]
        for row in canonical["records"]
        if row.get("lifecycle_status") == "COMPLETED" and row["occurrence_id"] not in reviewed_ids
    )
    require(remaining == sorted(post["remaining_eligible_unreviewed_occurrence_ids"]), f"AP remaining frontier mismatch: {remaining}")
    return new_reviews, new_evidence


def audit_markdown(plan: dict[str, Any], protected_before: dict[str, str]) -> str:
    post = plan["postconditions"]
    lines = [
        "# WORLD SIGNALS — WHO WHA79 health-governance Analysis AP transaction audit v0.1",
        "",
        f"- committed_at_utc: `{datetime.now(timezone.utc).isoformat()}`",
        f"- exact_base_main: `{plan['base_main_sha']}`",
        f"- occurrence: `{plan['selection']['selected_occurrence_id']}`",
        f"- new_analysis_id: `{plan['new_analysis_id']}`",
        f"- Analysis reviews: `{plan['preconditions']['analysis_reviews_version']} / {plan['preconditions']['analysis_review_count']} -> {post['analysis_reviews_version']} / {post['analysis_review_count']}`",
        f"- Analysis evidence: `{plan['preconditions']['analysis_evidence_version']} / {plan['preconditions']['analysis_evidence_count']} -> {post['analysis_evidence_version']} / {post['analysis_evidence_count']}`",
        f"- reviewed event-type diversity: `{plan['preconditions']['reviewed_event_type_diversity']} -> {post['reviewed_event_type_diversity']}`",
        "- Analysis schema: `v0.4 unchanged`",
        "- production EXACT_TIMESTAMP_SERIES rows: `0`",
        "- canonical/source/ledger/overlay/monitor/calendar mutation: `none`",
        "- automatic canonical commit: `false`",
        "- auto-merge: `false`",
        "",
        "## Analytical guardrails",
        "",
        "- Assembly completion is not implementation of every resolution or plan.",
        "- Decision/resolution counts are not a scalar impact or success metric.",
        "- PABS continuation is not PABS Annex adoption, ratification or implementation.",
        "- Establishing a global-health-architecture reform process is not completing reform.",
        "- AMR plan adoption is not evidence of realised health effects.",
        "- Later IGWG meetings are process propagation and do not retime WHA79.",
        "- Empty market response is an allowed analytical conclusion.",
        "",
        "## Protected SHA-256 before write",
        "",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in sorted(protected_before.items()))
    lines.append("")
    return "\n".join(lines)


def load_all() -> tuple[dict[str, Any], ...]:
    return (
        load(PLAN_PATH),
        load(PAYLOAD_PATH),
        load(CANONICAL_PATH),
        load(SOURCES_PATH),
        load(LEDGER_PATH),
        load(OVERLAY_PATH),
        load(EXPECTATIONS_PATH),
        load(ANALYSIS_SCHEMA_PATH),
        load(REVIEWS_PATH),
        load(EVIDENCE_PATH),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply WORLD SIGNALS Analysis AP WHA79 specimen")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Validate exact pre-state and simulate without writing")
    mode.add_argument("--write", action="store_true", help="Write the reviewed AP Analysis transaction")
    args = parser.parse_args()

    plan, payload, canonical, sources, ledger, overlay, expectations, schema, reviews, evidence = load_all()
    protected_before = protected_hashes()
    new_reviews, new_evidence = transform(plan, payload, canonical, sources, ledger, overlay, expectations, schema, reviews, evidence)
    require(protected_hashes() == protected_before, "AP simulation mutated protected files")

    if args.check:
        print("AP_CHECK_OK")
        print(json.dumps({
            "analysis_reviews": [reviews["version"], new_reviews["version"], len(new_reviews["reviews"])],
            "analysis_evidence": [evidence["version"], new_evidence["version"], len(new_evidence["evidence"])],
            "target": plan["selection"]["selected_occurrence_id"],
            "exact_timestamp_series_rows": exact_timestamp_series_rows(new_reviews),
        }, indent=2))
        return 0

    require(os.environ.get(APPLY_ENV) == "1", f"AP write requires {APPLY_ENV}=1")
    write(REVIEWS_PATH, new_reviews)
    write(EVIDENCE_PATH, new_evidence)
    AUDIT_PATH.write_text(audit_markdown(plan, protected_before), encoding="utf-8")
    require(protected_hashes() == protected_before, "AP write mutated protected upstream files")
    print("AP_WRITE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
