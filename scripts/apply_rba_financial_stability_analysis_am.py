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

from world_signals.analysis import analysis_population_readiness, public_analysis_projection, validate_analysis

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
PLAN_PATH = ROOT / "data/analysis/RBA_FINANCIAL_STABILITY_ANALYSIS_AM_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/analysis/RBA_FINANCIAL_STABILITY_ANALYSIS_AM_PAYLOAD_v0.1.json"
AUDIT_PATH = ROOT / "data/analysis/RBA_FINANCIAL_STABILITY_ANALYSIS_AM_TRANSACTION_AUDIT_v0.1.md"

APPLY_ENV = "WORLD_SIGNALS_APPLY_ANALYSIS_AM"

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
    return {label: sha256(path) for label, path in PROTECTED.items()}


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


def assert_pre(plan: dict[str, Any], canonical: dict[str, Any], sources: dict[str, Any], ledger: dict[str, Any],
               overlay: dict[str, Any], expectations: dict[str, Any], schema: dict[str, Any],
               reviews: dict[str, Any], evidence: dict[str, Any]) -> None:
    pre = plan["preconditions"]
    require((canonical.get("version"), len(canonical.get("records", []))) ==
            (pre["canonical_registry_version"], pre["canonical_record_count"]), "AM canonical pre-state mismatch")
    require((sources.get("version"), len(sources.get("sources", []))) ==
            (pre["source_registry_version"], pre["source_record_count"]), "AM source pre-state mismatch")
    require((ledger.get("version"), len(ledger.get("changes", []))) ==
            (pre["change_ledger_version"], pre["change_ledger_count"]), "AM ledger pre-state mismatch")
    require((overlay.get("version"), overlay.get("canonical_checkpoint")) ==
            (pre["biosecurity_overlay_version"], pre["biosecurity_overlay_checkpoint"]), "AM overlay pre-state mismatch")
    require(expectations.get("version") == pre["monitor_expectations_version"], "AM monitor expectations pre-state mismatch")
    rba = next((row for row in expectations.get("adapters", []) if row.get("adapter_id") == "RBA_FSR_RSS"), None)
    require(rba is not None, "AM RBA monitor adapter missing")
    require(set(rba.get("canonical_occurrence_ids", [])) == {"WSO-FIN-B-0001", "WSO-FIN-B-0004"},
            "AM requires repaired AL RBA monitor scope")
    require(schema.get("version") == pre["analysis_schema_version"], "AM Analysis schema pre-state mismatch")
    require((reviews.get("version"), len(reviews.get("reviews", []))) ==
            (pre["analysis_reviews_version"], pre["analysis_review_count"]), "AM reviews pre-state mismatch")
    require(reviews.get("canonical_checkpoint") == pre["analysis_reviews_canonical_checkpoint"],
            "AM reviews canonical checkpoint mismatch")
    require((evidence.get("version"), len(evidence.get("evidence", []))) ==
            (pre["analysis_evidence_version"], pre["analysis_evidence_count"]), "AM evidence pre-state mismatch")

    readiness = analysis_population_readiness(schema, reviews, canonical)
    require(readiness["eligible_completed_occurrence_count"] == pre["eligible_completed_occurrence_count"],
            "AM eligible completed count drifted")
    require(readiness["reviewed_occurrence_count"] == pre["reviewed_occurrence_count"], "AM reviewed count drifted")
    require(readiness["reviewed_event_type_diversity"] == pre["reviewed_event_type_diversity"],
            "AM event-type diversity drifted")
    require(exact_timestamp_series_rows(reviews) == pre["required_pre_analysis_exact_timestamp_series_rows"],
            "AM exact-timestamp market-measurement pre-state drifted")

    target = next((row for row in canonical["records"] if row.get("occurrence_id") == pre["required_target_occurrence_id"]), None)
    require(target is not None, "AM target canonical occurrence missing")
    require(target.get("series_id") == pre["required_target_series_id"], "AM target series mismatch")
    require(target.get("category") == pre["required_target_category"], "AM target category mismatch")
    require(target.get("event_type") == pre["required_target_event_type"], "AM target event type mismatch")
    require(target.get("lifecycle_status") == pre["required_target_lifecycle"], "AM target lifecycle mismatch")
    require(target.get("start_local") == pre["required_target_start_local"], "AM target local time mismatch")
    require(target.get("source_timezone") == pre["required_target_source_timezone"], "AM target timezone mismatch")
    require(target.get("start_utc") == pre["required_target_start_utc"], "AM target UTC mismatch")
    require(target.get("time_precision") == pre["required_target_time_precision"], "AM target precision mismatch")

    existing = {row.get("analysis_id") for row in reviews.get("reviews", [])}
    for analysis_id in pre["required_absent_analysis_ids"]:
        require(analysis_id not in existing, f"AM analysis already exists: {analysis_id}")


def assert_payload(plan: dict[str, Any], payload: dict[str, Any], canonical: dict[str, Any],
                   reviews: dict[str, Any], evidence: dict[str, Any]) -> None:
    require(payload.get("tranche") == "RBA_FINANCIAL_STABILITY_ANALYSIS_AM", "wrong AM payload")
    require(len(payload.get("reviews", [])) == 1, "AM must contain exactly one review")
    review = payload["reviews"][0]
    require(review.get("analysis_id") == plan["new_analysis_id"], "AM analysis ID differs from plan")
    require(review.get("canonical_occurrence_id") == plan["selection"]["selected_occurrence_id"], "AM target differs from plan")
    require(review.get("what_surprised", {}).get("status") == "NOT_ESTABLISHED", "AM surprise must remain NOT_ESTABLISHED")
    require((review.get("what_surprised") or {}).get("comparisons") == [], "AM must not fabricate forecast-error comparisons")
    require(review.get("what_moved") == [], "AM must not attribute contaminated same-session moves to the FSR")

    benchmarks = (review.get("what_was_expected") or {}).get("benchmarks") or []
    require(len(benchmarks) == 1, "AM must preserve exactly one prior-guidance benchmark")
    require(benchmarks[0].get("benchmark_type") == "OFFICIAL_PRIOR_GUIDANCE", "AM prior benchmark type drifted")

    connection = review.get("what_appears_connected") or {}
    require(connection.get("interaction_type") == "COMMON_DRIVER_CONTEXT", "AM interaction type mismatch")
    require(connection.get("causal_status") == "NOT_A_CAUSAL_CLAIM", "AM causal boundary drifted")
    require(connection.get("confidence") == "HIGH", "AM context confidence mismatch")
    require((review.get("second_order_effects") or {}).get("status") == "PLAUSIBLE_WATCH_ITEM",
            "AM second-order status must remain prospective")
    require(len(review.get("falsifiers") or []) >= 5, "AM must retain explicit falsifiers")

    new_evidence_ids = {row.get("evidence_id") for row in payload.get("evidence", [])}
    require(new_evidence_ids == set(plan["new_evidence_ids"]), "AM evidence IDs differ from plan")
    require(new_evidence_ids.isdisjoint({row.get("evidence_id") for row in evidence.get("evidence", [])}),
            "AM would duplicate analytical evidence")
    require(review["analysis_id"] not in {row.get("analysis_id") for row in reviews.get("reviews", [])},
            "AM would duplicate analytical review")

    target = next(row for row in canonical["records"] if row.get("occurrence_id") == review["canonical_occurrence_id"])
    require(review.get("canonical_series_id") == target.get("series_id"), "AM review series does not match canonical")
    require(review.get("canonical_event_type") == target.get("event_type"), "AM review event type does not match canonical")
    require(review.get("canonical_institution") == target.get("institution"), "AM review institution does not match canonical")
    require(review.get("canonical_release_utc") == target.get("start_utc"), "AM review UTC does not match canonical")

    for key in (
        "prior_official_assessment_is_pre_event_consensus",
        "changed_risk_assessment_is_directional_surprise",
        "market_volatility_described_by_report_is_caused_by_report",
        "same_day_aud_move_is_fsr_specific_market_response",
        "exact_canonical_timestamp_confers_exact_market_precision",
        "financial_system_resilience_means_no_vulnerability",
        "risk_warning_is_crisis_forecast",
        "empty_market_response_is_missing_work",
        "queue_completion_is_population_objective",
        "market_structure_gap_must_be_filled_next",
    ):
        require(plan["guardrails"].get(key) is False, f"AM guardrail must remain false: {key}")


def transform(plan: dict[str, Any], payload: dict[str, Any], canonical: dict[str, Any], sources: dict[str, Any],
              ledger: dict[str, Any], overlay: dict[str, Any], expectations: dict[str, Any], schema: dict[str, Any],
              reviews: dict[str, Any], evidence: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
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
    require(report.ok, "AM post-state failed Analysis validation: " + "; ".join(report.errors))
    readiness = analysis_population_readiness(schema, new_reviews, canonical)
    require((new_reviews["version"], len(new_reviews["reviews"])) ==
            (post["analysis_reviews_version"], post["analysis_review_count"]), "AM review post-state mismatch")
    require((new_evidence["version"], len(new_evidence["evidence"])) ==
            (post["analysis_evidence_version"], post["analysis_evidence_count"]), "AM evidence post-state mismatch")
    require(readiness["eligible_completed_occurrence_count"] == post["eligible_completed_occurrence_count"], "AM eligible count mismatch")
    require(readiness["reviewed_occurrence_count"] == post["reviewed_occurrence_count"], "AM reviewed count mismatch")
    require(readiness["reviewed_event_type_diversity"] == post["reviewed_event_type_diversity"], "AM diversity mismatch")
    require(readiness["reviewed_by_event_type"].get("FINANCIAL_STABILITY_REPORT", 0) ==
            post["reviewed_financial_stability_report_occurrence_count"], "AM FSR reviewed count mismatch")
    require(readiness["broad_population_state"] == post["broad_population_state"], "AM readiness state mismatch")
    require(exact_timestamp_series_rows(new_reviews) == post["post_analysis_exact_timestamp_series_rows"],
            "AM must not fabricate EXACT_TIMESTAMP_SERIES precision")

    remaining = sorted(
        row["occurrence_id"] for row in canonical["records"]
        if row.get("lifecycle_status") == "COMPLETED" and row["occurrence_id"] not in set(readiness["reviewed_occurrence_ids"])
    )
    require(remaining == sorted(post["remaining_eligible_unreviewed_occurrence_ids"]),
            f"AM remaining eligible-unreviewed mismatch: {remaining}")

    projection = public_analysis_projection(schema, new_evidence, new_reviews, canonical)
    projected = next(row for row in projection["reviews"] if row["analysis_id"] == plan["new_analysis_id"])
    require(projected.get("what_surprised", {}).get("status") == "NOT_ESTABLISHED", "AM projection changed surprise status")
    require(projected.get("what_moved") == [], "AM projection invented market movement")
    require(projected.get("what_appears_connected", {}).get("causal_status") == "NOT_A_CAUSAL_CLAIM",
            "AM projection changed causal boundary")
    require(projected.get("canonical", {}).get("event_type") == "FINANCIAL_STABILITY_REPORT", "AM projection lost event type")
    require(projected.get("canonical", {}).get("start_utc") == "2026-03-19T00:30:00Z", "AM projection lost canonical UTC")

    return new_reviews, new_evidence


def audit_text(before: dict[str, str], after: dict[str, str], plan: dict[str, Any]) -> str:
    same = before == after
    return "\n".join([
        "# WORLD SIGNALS — RBA Financial Stability Analysis AM transaction audit v0.1",
        "",
        f"**Reference date:** {plan['reference_date']}",
        f"**Exact base main:** `{plan['base_main_sha']}`",
        "**Architecture layer:** Analysis only",
        "",
        "## Mutation",
        "",
        "- Analysis reviews: **v0.10 / 14 → v0.11 / 15**",
        "- Analysis evidence: **v0.10 / 54 → v0.11 / 59**",
        "- added `WSAN-AU-RBA-FSR-20260319-001` for canonical `WSO-FIN-B-0004`",
        "- Analysis schema remains **v0.4**",
        "- production `EXACT_TIMESTAMP_SERIES` remains **0**",
        "",
        "## Analytical boundary",
        "",
        "- October 2025 official guidance remains baseline context, not March consensus.",
        "- surprise remains `NOT_ESTABLISHED`.",
        "- `what_moved` remains empty: same-session market moves are not attributed to the FSR.",
        "- connection is `COMMON_DRIVER_CONTEXT` / `NOT_A_CAUSAL_CLAIM`.",
        "- prospective financial-stability transmission channels remain watch items, not publication-caused outcomes.",
        "",
        "## Protected-state hash audit",
        "",
        f"Protected upstream/configuration datasets unchanged: **{same}**",
        "",
        "```json",
        json.dumps({"before": before, "after": after}, indent=2),
        "```",
        "",
        "## Deliberate non-actions",
        "",
        "- no canonical registry/schema mutation",
        "- no source-registry mutation",
        "- no change-ledger mutation",
        "- no biosecurity-overlay mutation",
        "- no monitor configuration/policy mutation",
        "- no Analysis schema mutation",
        "- no exact market-data ingestion",
        "- no Calendar write",
        "- no auto-merge",
        "",
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    require(args.check ^ args.write, "choose exactly one of --check or --write")

    plan, payload = load(PLAN_PATH), load(PAYLOAD_PATH)
    canonical, sources, ledger = load(CANONICAL_PATH), load(SOURCES_PATH), load(LEDGER_PATH)
    overlay, expectations, schema = load(OVERLAY_PATH), load(EXPECTATIONS_PATH), load(ANALYSIS_SCHEMA_PATH)
    reviews, evidence = load(REVIEWS_PATH), load(EVIDENCE_PATH)
    before = protected_hashes()
    new_reviews, new_evidence = transform(plan, payload, canonical, sources, ledger, overlay, expectations, schema, reviews, evidence)

    if args.check:
        require(protected_hashes() == before, "AM --check mutated protected state")
        print("AM_CHECK_OK")
        print(json.dumps({
            "analysis_reviews": [reviews["version"], new_reviews["version"], len(new_reviews["reviews"])],
            "analysis_evidence": [evidence["version"], new_evidence["version"], len(new_evidence["evidence"])],
            "target": plan["selection"]["selected_occurrence_id"],
            "exact_timestamp_series_rows": exact_timestamp_series_rows(new_reviews),
        }, indent=2))
        return

    require(os.environ.get(APPLY_ENV) == "1", f"write requires {APPLY_ENV}=1")
    write(REVIEWS_PATH, new_reviews)
    write(EVIDENCE_PATH, new_evidence)
    after = protected_hashes()
    require(after == before, "AM write mutated protected upstream/configuration state")
    AUDIT_PATH.write_text(audit_text(before, after, plan), encoding="utf-8")
    print("AM_WRITE_OK")


if __name__ == "__main__":
    main()
