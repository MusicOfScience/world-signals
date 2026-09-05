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
PLAN_PATH = ROOT / "data/analysis/JAPAN_SOVEREIGN_FINANCING_ANALYSIS_AA_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/analysis/JAPAN_SOVEREIGN_FINANCING_ANALYSIS_AA_PAYLOAD_v0.1.json"
AUDIT_PATH = ROOT / "data/analysis/JAPAN_SOVEREIGN_FINANCING_ANALYSIS_AA_TRANSACTION_AUDIT_v0.1.md"

APPLY_ENV = "WORLD_SIGNALS_APPLY_ANALYSIS_AA"

PROTECTED = {
    "canonical registry": CANONICAL_PATH,
    "canonical schema": CANONICAL_SCHEMA_PATH,
    "source registry": SOURCES_PATH,
    "change ledger": LEDGER_PATH,
    "biosecurity overlay": OVERLAY_PATH,
    "monitor expectations": EXPECTATIONS_PATH,
    "monitor operations policy": OPERATIONS_PATH,
    "Analysis schema": ANALYSIS_SCHEMA_PATH,
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


def assert_pre(
    plan: dict[str, Any], canonical: dict[str, Any], sources: dict[str, Any], ledger: dict[str, Any],
    overlay: dict[str, Any], schema: dict[str, Any], reviews: dict[str, Any], evidence: dict[str, Any],
) -> None:
    pre = plan["preconditions"]
    require((canonical.get("version"), len(canonical.get("records", []))) ==
            (pre["canonical_registry_version"], pre["canonical_record_count"]), "AA canonical pre-state mismatch")
    require((sources.get("version"), len(sources.get("sources", []))) ==
            (pre["source_registry_version"], pre["source_record_count"]), "AA source pre-state mismatch")
    require((ledger.get("version"), len(ledger.get("changes", []))) ==
            (pre["change_ledger_version"], pre["change_ledger_count"]), "AA ledger pre-state mismatch")
    require((overlay.get("version"), overlay.get("canonical_checkpoint")) ==
            (pre["biosecurity_overlay_version"], pre["biosecurity_overlay_checkpoint"]), "AA overlay pre-state mismatch")
    require(schema.get("version") == pre["analysis_schema_version"], "AA Analysis schema pre-state mismatch")
    require((reviews.get("version"), len(reviews.get("reviews", []))) ==
            (pre["analysis_reviews_version"], pre["analysis_review_count"]), "AA reviews pre-state mismatch")
    require(reviews.get("canonical_checkpoint") == pre["analysis_reviews_canonical_checkpoint"],
            "AA reviews canonical checkpoint mismatch")
    require((evidence.get("version"), len(evidence.get("evidence", []))) ==
            (pre["analysis_evidence_version"], pre["analysis_evidence_count"]), "AA evidence pre-state mismatch")

    readiness = analysis_population_readiness(schema, reviews, canonical)
    require(readiness["eligible_completed_occurrence_count"] == pre["eligible_completed_occurrence_count"],
            "AA eligible completed count drifted")
    require(readiness["reviewed_occurrence_count"] == pre["reviewed_occurrence_count"],
            "AA reviewed count drifted")
    require(readiness["reviewed_event_type_diversity"] == pre["reviewed_event_type_diversity"],
            "AA event-type diversity drifted")

    target = next((row for row in canonical["records"] if row.get("occurrence_id") == pre["required_target_occurrence_id"]), None)
    require(target is not None, "AA target canonical occurrence missing")
    require(target.get("series_id") == pre["required_target_series_id"], "AA target series mismatch")
    require(target.get("category") == pre["required_target_category"], "AA target category mismatch")
    require(target.get("event_type") == pre["required_target_event_type"], "AA target event type mismatch")
    require(target.get("lifecycle_status") == pre["required_target_lifecycle"], "AA target lifecycle mismatch")
    require(target.get("start_local") == pre["required_target_start_local"], "AA target start_local mismatch")
    require(target.get("source_timezone") == pre["required_target_source_timezone"], "AA target timezone mismatch")
    require(target.get("start_utc") is pre["required_target_start_utc"], "AA target start_utc mismatch")

    existing = {row.get("analysis_id") for row in reviews.get("reviews", [])}
    for analysis_id in pre["required_absent_analysis_ids"]:
        require(analysis_id not in existing, f"AA analysis already exists: {analysis_id}")


def assert_payload(
    plan: dict[str, Any], payload: dict[str, Any], canonical: dict[str, Any],
    reviews: dict[str, Any], evidence: dict[str, Any],
) -> None:
    require(payload.get("tranche") == "JAPAN_SOVEREIGN_FINANCING_ANALYSIS_AA", "wrong AA payload")
    require(len(payload.get("reviews", [])) == 1, "AA must contain exactly one review")
    review = payload["reviews"][0]
    require(review.get("analysis_id") == plan["new_analysis_id"], "AA analysis ID differs from plan")
    require(review.get("canonical_occurrence_id") == plan["selection"]["selected_occurrence_id"], "AA target differs from plan")
    require(review.get("canonical_release_utc") is None, "AA must preserve unresolved canonical UTC")
    require(review.get("what_surprised", {}).get("status") == "NO_CLEAR_SURPRISE", "AA surprise must remain NO_CLEAR_SURPRISE")

    movements = review.get("what_moved") or []
    require(len(movements) == 1, "AA must contain exactly one matched-tenor movement row")
    movement = movements[0]
    require(movement.get("movement_type") == "SOVEREIGN_YIELD", "AA movement must be sovereign yield")
    require(movement.get("movement_representation") == "CHANGE_AND_ENDPOINT", "AA movement representation mismatch")
    require(movement.get("measurement_precision") == "SOURCE_REPORTED_CHANGE_AND_ENDPOINT", "AA must not fabricate exact timestamp precision")
    require(movement.get("independently_reconstructed") is False, "AA movement must remain source-reported")
    require(movement.get("before_value") is None, "AA must not synthesize a pre-auction yield")
    require(movement.get("after_value") == 4.07 and movement.get("change") == -9.5, "AA source-reported daily yield move mismatch")
    require("unchanged after the auction" in movement.get("measurement_window", ""), "AA movement window must preserve no incremental auction move")

    connection = review.get("what_appears_connected") or {}
    require(connection.get("interaction_type") == "OBSERVATION_CONTEXT", "AA interaction type mismatch")
    require(connection.get("causal_status") == "NOT_A_CAUSAL_CLAIM", "AA must remain non-causal")
    require(connection.get("confidence") == "HIGH", "AA no-incremental-move observation should be high confidence")
    require("unchanged after the auction" in connection.get("summary", ""), "AA connection must preserve the auction/non-auction distinction")
    require((review.get("second_order_effects") or {}).get("status") == "PLAUSIBLE_WATCH_ITEM", "AA second-order status mismatch")

    actuals = {row.get("metric"): row.get("value") for row in (review.get("what_happened") or {}).get("actuals", [])}
    require(actuals.get("competitive_bids") == 1728.1, "AA competitive bid amount mismatch")
    require(actuals.get("accepted_competitive_bids") == 456.2, "AA accepted bid amount mismatch")
    require(actuals.get("weighted_average_yield") == 4.079, "AA weighted average yield mismatch")
    require(actuals.get("bid_to_cover_ratio") == 3.79, "AA bid-to-cover mismatch")
    require(actuals.get("auction_tail") == 0.28, "AA auction tail mismatch")

    new_evidence_ids = {row.get("evidence_id") for row in payload.get("evidence", [])}
    require(new_evidence_ids == set(plan["new_evidence_ids"]), "AA evidence IDs differ from plan")
    require(new_evidence_ids.isdisjoint({row.get("evidence_id") for row in evidence.get("evidence", [])}),
            "AA would duplicate analytical evidence")
    require(review["analysis_id"] not in {row.get("analysis_id") for row in reviews.get("reviews", [])},
            "AA would duplicate analytical review")

    target = next(row for row in canonical["records"] if row.get("occurrence_id") == review["canonical_occurrence_id"])
    require(review.get("canonical_series_id") == target.get("series_id"), "AA review series does not match canonical")
    require(review.get("canonical_event_type") == target.get("event_type"), "AA review event type does not match canonical")
    require(review.get("canonical_institution") == target.get("institution"), "AA review institution does not match canonical")
    require(target.get("category") == "FISCAL_SOVEREIGN_FINANCE", "AA target category drifted")
    require(target.get("start_utc") is None, "AA may not resolve canonical clock time")

    guardrails = plan["guardrails"]
    for key in (
        "auction_clearing_yield_is_secondary_market_move",
        "previous_auction_is_market_consensus",
        "same_session_yield_move_is_auction_causality",
        "exact_timestamp_precision_without_independent_series",
        "one_auction_establishes_capital_repatriation",
        "queue_completion_is_population_objective",
    ):
        require(guardrails.get(key) is False, f"AA guardrail must remain false: {key}")


def transform(
    plan: dict[str, Any], payload: dict[str, Any], canonical: dict[str, Any], sources: dict[str, Any],
    ledger: dict[str, Any], overlay: dict[str, Any], schema: dict[str, Any], reviews: dict[str, Any], evidence: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    assert_pre(plan, canonical, sources, ledger, overlay, schema, reviews, evidence)
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
    require(report.ok, "AA post-state failed Analysis validation: " + "; ".join(report.errors))
    readiness = analysis_population_readiness(schema, new_reviews, canonical)
    require((new_reviews["version"], len(new_reviews["reviews"])) ==
            (post["analysis_reviews_version"], post["analysis_review_count"]), "AA review post-state mismatch")
    require((new_evidence["version"], len(new_evidence["evidence"])) ==
            (post["analysis_evidence_version"], post["analysis_evidence_count"]), "AA evidence post-state mismatch")
    require(readiness["eligible_completed_occurrence_count"] == post["eligible_completed_occurrence_count"], "AA eligible count mismatch")
    require(readiness["reviewed_occurrence_count"] == post["reviewed_occurrence_count"], "AA reviewed count mismatch")
    require(readiness["reviewed_event_type_diversity"] == post["reviewed_event_type_diversity"], "AA diversity mismatch")
    require(readiness["reviewed_by_region"].get("East Asia", 0) == post["reviewed_east_asia_occurrence_count"], "AA East Asia reviewed count mismatch")
    require(readiness["broad_population_state"] == post["broad_population_state"], "AA readiness state mismatch")

    remaining = sorted(
        row["occurrence_id"] for row in canonical["records"]
        if row.get("lifecycle_status") == "COMPLETED"
        and row["occurrence_id"] not in set(readiness["reviewed_occurrence_ids"])
    )
    require(remaining == sorted(post["remaining_eligible_unreviewed_occurrence_ids"]),
            f"AA remaining eligible-unreviewed mismatch: {remaining}")

    projection = public_analysis_projection(schema, new_evidence, new_reviews, canonical)
    projected = next(row for row in projection["reviews"] if row["analysis_id"] == plan["new_analysis_id"])
    require(projected.get("what_surprised", {}).get("status") == "NO_CLEAR_SURPRISE", "AA public projection lost surprise state")
    require(projected.get("what_moved", [])[0].get("movement_type") == "SOVEREIGN_YIELD", "AA public projection lost sovereign-yield move")
    require(projected.get("what_appears_connected", {}).get("causal_status") == "NOT_A_CAUSAL_CLAIM", "AA public projection strengthened causality")
    require(projected.get("canonical", {}).get("event_type") == "FISCAL_FINANCING_EVENT", "AA public projection lost event type")
    require(projected.get("canonical", {}).get("category") == "FISCAL_SOVEREIGN_FINANCE", "AA public projection distorted category")
    require(projected.get("canonical", {}).get("start_utc") is None, "AA public projection inferred canonical UTC")

    return new_reviews, new_evidence, readiness, projection


def audit_text(plan: dict[str, Any], readiness: dict[str, Any], hashes: dict[str, str]) -> str:
    lines = [
        "# WORLD SIGNALS — Japan sovereign financing analysis AA transaction audit v0.1", "",
        "**Transaction date:** 2026-09-06  ",
        "**Canonical checkpoint:** v0.31 / 681 — unchanged  ",
        "**Analysis post-state:** schema v0.3; reviews v0.8 / 12; evidence v0.8 / 44", "",
        "## Added reviewed specimen", "",
        "- `WSAN-JP-JGB30-20260903-001` — Japan 30-year JGB auction — `FISCAL_FINANCING_EVENT`.",
        "- official auction mechanics are preserved separately from secondary-market yields.",
        "- surprise is `NO_CLEAR_SURPRISE`; previous-auction metrics are not promoted into consensus.",
        "- source-reported 30-year yield movement is -9.5bp on the day to 4.070%, while the same source says the yield was unchanged after the auction.",
        "- connection remains `OBSERVATION_CONTEXT` / `NOT_A_CAUSAL_CLAIM`.",
        "- exact timestamp precision is deliberately not fabricated; canonical UTC remains unresolved.",
        "- global capital reallocation remains `PLAUSIBLE_WATCH_ITEM`, not a one-auction effect.", "",
        "## Schema decision", "",
        "- Analysis schema remains v0.3. Existing semantics already support the sovereign-financing case.", "",
        "## Readiness", "",
        f"- eligible completed occurrences: {readiness['eligible_completed_occurrence_count']}",
        f"- reviewed occurrences: {readiness['reviewed_occurrence_count']}",
        f"- reviewed event-type diversity: {readiness['reviewed_event_type_diversity']}",
        f"- reviewed East Asia occurrences: {readiness['reviewed_by_region'].get('East Asia', 0)}",
        f"- broad state: `{readiness['broad_population_state']}`", "",
        "## Remaining eligible unreviewed", "",
    ]
    lines.extend(f"- `{occurrence_id}`" for occurrence_id in plan["postconditions"]["remaining_eligible_unreviewed_occurrence_ids"])
    lines += ["", "## Protected SHA-256", ""]
    lines.extend(f"- {label}: `{digest}`" for label, digest in hashes.items())
    lines += ["", "Canonical/source/ledger/overlay/monitor and Analysis-schema files were hashed before and after AA and must remain byte-identical.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    plan = load(PLAN_PATH)
    payload = load(PAYLOAD_PATH)
    canonical = load(CANONICAL_PATH)
    sources = load(SOURCES_PATH)
    ledger = load(LEDGER_PATH)
    overlay = load(OVERLAY_PATH)
    schema = load(ANALYSIS_SCHEMA_PATH)
    reviews = load(REVIEWS_PATH)
    evidence = load(EVIDENCE_PATH)
    before = protected_hashes()

    new_reviews, new_evidence, readiness, _ = transform(
        plan, payload, canonical, sources, ledger, overlay, schema, reviews, evidence
    )

    if not args.apply:
        print("CHECK_OK")
        print(json.dumps(readiness, indent=2))
        return

    require(os.environ.get(APPLY_ENV) == "REVIEWED_APPLY", f"set {APPLY_ENV}=REVIEWED_APPLY for reviewed write")
    write(REVIEWS_PATH, new_reviews)
    write(EVIDENCE_PATH, new_evidence)
    AUDIT_PATH.write_text(audit_text(plan, readiness, before), encoding="utf-8")
    after = protected_hashes()
    require(before == after, "AA protected upstream/schema files changed during apply")
    print("APPLY_OK")


if __name__ == "__main__":
    main()
