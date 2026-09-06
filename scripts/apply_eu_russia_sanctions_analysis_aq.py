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
PLAN_PATH = ROOT / "data/analysis/EU_RUSSIA_SANCTIONS_ANALYSIS_AQ_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/analysis/EU_RUSSIA_SANCTIONS_ANALYSIS_AQ_PAYLOAD_v0.1.json"
AUDIT_PATH = ROOT / "data/analysis/EU_RUSSIA_SANCTIONS_ANALYSIS_AQ_TRANSACTION_AUDIT_v0.1.md"

APPLY_ENV = "WORLD_SIGNALS_APPLY_ANALYSIS_AQ"

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
    require((canonical.get("version"), len(canonical.get("records", []))) == (pre["canonical_registry_version"], pre["canonical_record_count"]), "AQ canonical pre-state mismatch")
    require((sources.get("version"), len(sources.get("sources", []))) == (pre["source_registry_version"], pre["source_record_count"]), "AQ source pre-state mismatch")
    require((ledger.get("version"), len(ledger.get("changes", []))) == (pre["change_ledger_version"], pre["change_ledger_count"]), "AQ ledger pre-state mismatch")
    require((overlay.get("version"), overlay.get("canonical_checkpoint")) == (pre["biosecurity_overlay_version"], pre["biosecurity_overlay_checkpoint"]), "AQ overlay pre-state mismatch")
    require(expectations.get("version") == pre["monitor_expectations_version"], "AQ monitor expectations pre-state mismatch")
    require(schema.get("version") == pre["analysis_schema_version"], "AQ Analysis schema pre-state mismatch")
    require((reviews.get("version"), len(reviews.get("reviews", []))) == (pre["analysis_reviews_version"], pre["analysis_review_count"]), "AQ reviews pre-state mismatch")
    require(reviews.get("canonical_checkpoint") == pre["analysis_reviews_canonical_checkpoint"], "AQ reviews canonical checkpoint mismatch")
    require((evidence.get("version"), len(evidence.get("evidence", []))) == (pre["analysis_evidence_version"], pre["analysis_evidence_count"]), "AQ evidence pre-state mismatch")

    readiness = analysis_population_readiness(schema, reviews, canonical)
    require(readiness["eligible_completed_occurrence_count"] == pre["eligible_completed_occurrence_count"], "AQ eligible completed count drifted")
    require(readiness["reviewed_occurrence_count"] == pre["reviewed_occurrence_count"], "AQ reviewed count drifted")
    require(readiness["reviewed_event_type_diversity"] == pre["reviewed_event_type_diversity"], "AQ reviewed diversity drifted")
    require(exact_timestamp_series_rows(reviews) == pre["required_pre_analysis_exact_timestamp_series_rows"], "AQ exact-series pre-state drifted")

    target = next((row for row in canonical["records"] if row.get("occurrence_id") == pre["required_target_occurrence_id"]), None)
    require(target is not None, "AQ target canonical occurrence missing")
    checks = {
        "series_id": pre["required_target_series_id"],
        "source_id": pre["required_target_source_id"],
        "category": pre["required_target_category"],
        "event_type": pre["required_target_event_type"],
        "lifecycle_status": pre["required_target_lifecycle"],
        "trade_policy_temporal_role": pre["required_target_trade_policy_temporal_role"],
        "trade_measure_state": pre["required_target_trade_measure_state"],
        "timing_type": pre["required_target_timing_type"],
        "start_local": pre["required_target_start_local"],
        "source_timezone": pre["required_target_source_timezone"],
        "start_utc": pre["required_target_start_utc"],
        "end_utc": pre["required_target_end_utc"],
        "time_precision": pre["required_target_time_precision"],
    }
    for field, expected in checks.items():
        require(target.get(field) == expected, f"AQ target {field} mismatch: {target.get(field)!r} != {expected!r}")
    require(target.get("all_day_semantics") is True, "AQ target must retain civil-date all-day semantics")

    existing = {row.get("analysis_id") for row in reviews.get("reviews", [])}
    for analysis_id in pre["required_absent_analysis_ids"]:
        require(analysis_id not in existing, f"AQ analysis already exists: {analysis_id}")


def assert_payload(
    plan: dict[str, Any],
    payload: dict[str, Any],
    canonical: dict[str, Any],
    reviews: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    require(payload.get("tranche") == "EU_RUSSIA_SANCTIONS_ANALYSIS_AQ", "wrong AQ payload")
    require(len(payload.get("reviews", [])) == 1, "AQ must contain exactly one review")
    review = payload["reviews"][0]
    require(review.get("analysis_id") == plan["new_analysis_id"], "AQ analysis ID differs from plan")
    require(review.get("canonical_occurrence_id") == plan["selection"]["selected_occurrence_id"], "AQ target differs from plan")
    require(review.get("canonical_release_utc") is None, "AQ may not invent a UTC decision time for a civil-date legal act")
    require((review.get("what_surprised") or {}).get("status") == "NOT_ESTABLISHED", "AQ surprise must remain NOT_ESTABLISHED")
    require((review.get("what_surprised") or {}).get("comparisons") == [], "AQ must not fabricate surprise comparisons")
    require(review.get("what_moved") == [], "AQ must not manufacture an EU-renewal-specific market response")

    benchmarks = (review.get("what_was_expected") or {}).get("benchmarks") or []
    require(len(benchmarks) == 1, "AQ must preserve exactly one pre-adoption political benchmark")
    require(benchmarks[0].get("benchmark_type") == "OTHER_DEFENSIBLE_EXPECTATION", "AQ pre-adoption benchmark class drifted")
    require(benchmarks[0].get("metric") == "pre_adoption_political_agreement", "AQ benchmark metric drifted")

    connection = review.get("what_appears_connected") or {}
    require(connection.get("interaction_type") == "LEGAL_OR_OPERATIONAL_DEPENDENCY", "AQ interaction type mismatch")
    require(connection.get("causal_status") == "NOT_A_CAUSAL_CLAIM", "AQ causal boundary drifted")
    require(connection.get("confidence") == "HIGH", "AQ connection confidence mismatch")
    require((review.get("second_order_effects") or {}).get("status") == "PLAUSIBLE_WATCH_ITEM", "AQ annual-cadence second order must remain prospective")
    require(len(review.get("what_may_be_noise") or []) >= 7, "AQ must retain legal/market noise checks")
    require(len(review.get("alternative_explanations") or []) >= 3, "AQ must retain alternatives")
    require(len(review.get("falsifiers") or []) >= 9, "AQ must retain falsifiers")

    evidence_rows = payload.get("evidence", [])
    new_ids = {row.get("evidence_id") for row in evidence_rows}
    require(new_ids == set(plan["new_evidence_ids"]), "AQ evidence IDs differ from plan")
    require(len(evidence_rows) == 6, "AQ evidence packet must contain exactly six rows")
    require(all(row.get("evidence_class") in {"PRIMARY_OFFICIAL", "REPUTABLE_NEWSWIRE"} for row in evidence_rows), "AQ evidence classes exceed reviewed packet")
    require(sum(row.get("evidence_class") == "PRIMARY_OFFICIAL" for row in evidence_rows) == 4, "AQ must contain exactly four primary official evidence rows")
    require(sum(row.get("evidence_class") == "REPUTABLE_NEWSWIRE" for row in evidence_rows) == 2, "AQ must contain exactly two Reuters evidence rows")
    require(all(row.get("canonical_provenance_effect") == "NONE" for row in evidence_rows), "AQ evidence may not mutate canonical provenance")
    require(new_ids.isdisjoint({row.get("evidence_id") for row in evidence.get("evidence", [])}), "AQ would duplicate evidence IDs")
    require(review["analysis_id"] not in {row.get("analysis_id") for row in reviews.get("reviews", [])}, "AQ would duplicate review ID")

    roles = {role for row in evidence_rows for role in row.get("roles", [])}
    require("OFFICIAL_OUTCOME" in roles, "AQ requires official-outcome evidence")
    require("EXPECTATION_BENCHMARK" in roles, "AQ requires expectation evidence")
    require("CONTEXT_OR_ALTERNATIVE" in roles, "AQ requires context/alternative evidence")

    target = next(row for row in canonical["records"] if row.get("occurrence_id") == review["canonical_occurrence_id"])
    require(review.get("canonical_series_id") == target.get("series_id"), "AQ review series mismatch")
    require(review.get("canonical_event_type") == target.get("event_type"), "AQ review event type mismatch")
    require(review.get("canonical_institution") == target.get("institution"), "AQ review institution mismatch")
    require(review.get("canonical_release_utc") == target.get("start_utc"), "AQ review UTC mismatch")

    required_false = (
        "political_agreement_equals_binding_legal_adoption",
        "press_release_publication_time_equals_decision_time",
        "annual_cadence_novelty_equals_surprise",
        "legal_adoption_equals_future_expiry_boundary",
        "renewal_freezes_policy_content_until_2027",
        "later_sanctions_package_is_caused_by_renewal",
        "same_period_oil_move_is_renewal_response",
        "expiry_boundary_implies_automatic_termination",
        "analytical_evidence_resolves_missing_canonical_utc",
        "empty_market_response_is_missing_work",
        "queue_completion_is_population_objective",
        "market_structure_gap_must_be_filled_next",
        "prior_ap_live_count_is_permanent_ceiling",
        "auto_merge",
    )
    for key in required_false:
        require(plan["guardrails"].get(key) is False, f"AQ guardrail must remain false: {key}")


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
    require(report.ok, "AQ post-state failed Analysis validation: " + "; ".join(report.errors))
    readiness = analysis_population_readiness(schema, new_reviews, canonical)
    require((new_reviews["version"], len(new_reviews["reviews"])) == (post["analysis_reviews_version"], post["analysis_review_count"]), "AQ review post-state mismatch")
    require((new_evidence["version"], len(new_evidence["evidence"])) == (post["analysis_evidence_version"], post["analysis_evidence_count"]), "AQ evidence post-state mismatch")
    require(readiness["eligible_completed_occurrence_count"] == post["eligible_completed_occurrence_count"], "AQ eligible count mismatch")
    require(readiness["reviewed_occurrence_count"] == post["reviewed_occurrence_count"], "AQ reviewed count mismatch")
    require(readiness["reviewed_event_type_diversity"] == post["reviewed_event_type_diversity"], "AQ diversity mismatch")
    require(readiness["reviewed_by_event_type"].get("SANCTIONS_PROCESS", 0) == post["reviewed_sanctions_process_occurrence_count"], "AQ sanctions-process reviewed count mismatch")
    require(readiness["broad_population_state"] == post["broad_population_state"], "AQ readiness state mismatch")
    require(exact_timestamp_series_rows(new_reviews) == post["post_analysis_exact_timestamp_series_rows"], "AQ must not fabricate exact market series")

    reviewed_ids = set(readiness["reviewed_occurrence_ids"])
    remaining = sorted(
        row["occurrence_id"]
        for row in canonical["records"]
        if row.get("lifecycle_status") == "COMPLETED" and row["occurrence_id"] not in reviewed_ids
    )
    require(remaining == sorted(post["remaining_eligible_unreviewed_occurrence_ids"]), f"AQ remaining frontier mismatch: {remaining}")
    return new_reviews, new_evidence


def audit_markdown(plan: dict[str, Any], protected_before: dict[str, str]) -> str:
    post = plan["postconditions"]
    lines = [
        "# WORLD SIGNALS — EU Russia sanctions Analysis AQ transaction audit v0.1",
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
        "- Political agreement is not binding legal adoption.",
        "- Press-release publication time is not the Council decision clock.",
        "- Annual-cadence novelty is not automatically surprise.",
        "- Legal adoption is not the future renewal/expiry boundary.",
        "- Annual renewal does not freeze sanctions-policy content.",
        "- A later sanctions package is not asserted to be caused by the renewal.",
        "- Same-period oil movement is not promoted to an EU-renewal response.",
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
    parser = argparse.ArgumentParser(description="Apply WORLD SIGNALS Analysis AQ EU Russia sanctions specimen")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Validate exact pre-state and simulate without writing")
    mode.add_argument("--write", action="store_true", help="Write the reviewed AQ Analysis transaction")
    args = parser.parse_args()

    plan, payload, canonical, sources, ledger, overlay, expectations, schema, reviews, evidence = load_all()
    protected_before = protected_hashes()
    new_reviews, new_evidence = transform(plan, payload, canonical, sources, ledger, overlay, expectations, schema, reviews, evidence)
    require(protected_hashes() == protected_before, "AQ simulation mutated protected files")

    if args.check:
        print("AQ_CHECK_OK")
        print(json.dumps({
            "analysis_reviews": [reviews["version"], new_reviews["version"], len(new_reviews["reviews"])],
            "analysis_evidence": [evidence["version"], new_evidence["version"], len(new_evidence["evidence"])],
            "target": plan["selection"]["selected_occurrence_id"],
            "exact_timestamp_series_rows": exact_timestamp_series_rows(new_reviews),
        }, indent=2))
        return 0

    require(os.environ.get(APPLY_ENV) == "1", f"AQ write requires {APPLY_ENV}=1")
    write(REVIEWS_PATH, new_reviews)
    write(EVIDENCE_PATH, new_evidence)
    AUDIT_PATH.write_text(audit_markdown(plan, protected_before), encoding="utf-8")
    require(protected_hashes() == protected_before, "AQ write mutated protected upstream files")
    print("AQ_WRITE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
