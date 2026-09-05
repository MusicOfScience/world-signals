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
PLAN_PATH = ROOT / "data/analysis/BANK_OF_CANADA_ANALYSIS_AI_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/analysis/BANK_OF_CANADA_ANALYSIS_AI_PAYLOAD_v0.1.json"
AUDIT_PATH = ROOT / "data/analysis/BANK_OF_CANADA_ANALYSIS_AI_TRANSACTION_AUDIT_v0.1.md"

APPLY_ENV = "WORLD_SIGNALS_APPLY_ANALYSIS_AI"

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


def exact_timestamp_series_rows(reviews: dict[str, Any]) -> int:
    return sum(
        1
        for review in reviews.get("reviews", [])
        for movement in (review.get("what_moved") or [])
        if movement.get("measurement_precision") == "EXACT_TIMESTAMP_SERIES"
    )


def assert_pre(
    plan: dict[str, Any], canonical: dict[str, Any], sources: dict[str, Any], ledger: dict[str, Any],
    overlay: dict[str, Any], schema: dict[str, Any], reviews: dict[str, Any], evidence: dict[str, Any],
) -> None:
    pre = plan["preconditions"]
    require((canonical.get("version"), len(canonical.get("records", []))) ==
            (pre["canonical_registry_version"], pre["canonical_record_count"]), "AI canonical pre-state mismatch")
    require((sources.get("version"), len(sources.get("sources", []))) ==
            (pre["source_registry_version"], pre["source_record_count"]), "AI source pre-state mismatch")
    require((ledger.get("version"), len(ledger.get("changes", []))) ==
            (pre["change_ledger_version"], pre["change_ledger_count"]), "AI ledger pre-state mismatch")
    require((overlay.get("version"), overlay.get("canonical_checkpoint")) ==
            (pre["biosecurity_overlay_version"], pre["biosecurity_overlay_checkpoint"]), "AI overlay pre-state mismatch")
    require(schema.get("version") == pre["analysis_schema_version"], "AI Analysis schema pre-state mismatch")
    require((reviews.get("version"), len(reviews.get("reviews", []))) ==
            (pre["analysis_reviews_version"], pre["analysis_review_count"]), "AI reviews pre-state mismatch")
    require(reviews.get("canonical_checkpoint") == pre["analysis_reviews_canonical_checkpoint"],
            "AI reviews canonical checkpoint mismatch")
    require((evidence.get("version"), len(evidence.get("evidence", []))) ==
            (pre["analysis_evidence_version"], pre["analysis_evidence_count"]), "AI evidence pre-state mismatch")

    readiness = analysis_population_readiness(schema, reviews, canonical)
    require(readiness["eligible_completed_occurrence_count"] == pre["eligible_completed_occurrence_count"],
            "AI eligible completed count drifted")
    require(readiness["reviewed_occurrence_count"] == pre["reviewed_occurrence_count"],
            "AI reviewed count drifted")
    require(readiness["reviewed_event_type_diversity"] == pre["reviewed_event_type_diversity"],
            "AI event-type diversity drifted")
    require(exact_timestamp_series_rows(reviews) == pre["required_pre_analysis_exact_timestamp_series_rows"],
            "AI exact-timestamp measurement pre-state drifted")

    target = next((row for row in canonical["records"] if row.get("occurrence_id") == pre["required_target_occurrence_id"]), None)
    require(target is not None, "AI target canonical occurrence missing")
    require(target.get("series_id") == pre["required_target_series_id"], "AI target series mismatch")
    require(target.get("category") == pre["required_target_category"], "AI target category mismatch")
    require(target.get("event_type") == pre["required_target_event_type"], "AI target event type mismatch")
    require(target.get("lifecycle_status") == pre["required_target_lifecycle"], "AI target lifecycle mismatch")
    require(target.get("start_local") == pre["required_target_start_local"], "AI target start_local mismatch")
    require(target.get("source_timezone") == pre["required_target_source_timezone"], "AI target timezone mismatch")
    require(target.get("start_utc") == pre["required_target_start_utc"], "AI target UTC mismatch")
    require(target.get("time_precision") == pre["required_target_time_precision"], "AI target precision mismatch")

    existing = {row.get("analysis_id") for row in reviews.get("reviews", [])}
    for analysis_id in pre["required_absent_analysis_ids"]:
        require(analysis_id not in existing, f"AI analysis already exists: {analysis_id}")


def assert_payload(
    plan: dict[str, Any], payload: dict[str, Any], canonical: dict[str, Any],
    reviews: dict[str, Any], evidence: dict[str, Any],
) -> None:
    require(payload.get("tranche") == "BANK_OF_CANADA_ANALYSIS_AI", "wrong AI payload")
    require(len(payload.get("reviews", [])) == 1, "AI must contain exactly one review")
    review = payload["reviews"][0]
    require(review.get("analysis_id") == plan["new_analysis_id"], "AI analysis ID differs from plan")
    require(review.get("canonical_occurrence_id") == plan["selection"]["selected_occurrence_id"], "AI target differs from plan")
    require(review.get("canonical_release_utc") == "2026-09-02T13:45:00Z", "AI must preserve exact canonical release UTC")
    require(review.get("what_surprised", {}).get("status") == "MIXED", "AI surprise must remain MIXED")

    comparisons = (review.get("what_surprised") or {}).get("comparisons") or []
    require(len(comparisons) == 2, "AI must preserve headline and path comparisons")
    by_metric = {row.get("metric"): row for row in comparisons}
    rate_comparison = by_metric.get("overnight_rate_target") or {}
    require((rate_comparison.get("actual"), rate_comparison.get("expected")) == (2.25, 2.25),
            "AI headline hold comparison mismatch")
    require(rate_comparison.get("difference_percentage_points") == 0.0,
            "AI must preserve zero headline rate surprise")
    path_comparison = by_metric.get("policy_path_and_guidance") or {}
    require(path_comparison.get("comparison_kind") == "QUALITATIVE", "AI path surprise must remain qualitative")
    require(path_comparison.get("direction") == "HAWKISHER_THAN_EXPECTED", "AI path surprise direction drifted")

    movements = review.get("what_moved") or []
    require(len(movements) == 2, "AI must contain exactly two market observations")
    movement_by_type = {row.get("movement_type"): row for row in movements}
    fx = movement_by_type.get("FX_SPOT") or {}
    require(fx.get("movement_representation") == "CHANGE_AND_ENDPOINT", "AI FX representation mismatch")
    require(fx.get("measurement_precision") == "SOURCE_REPORTED_CHANGE_AND_ENDPOINT",
            "AI FX must remain source-reported rather than exact timestamp")
    require(fx.get("independently_reconstructed") is False, "AI FX movement must not be reconstructed")
    require(fx.get("before_value") is None, "AI must not synthesize a pre-decision FX level")
    require(fx.get("after_value") == 1.384 and fx.get("change") == 0.4, "AI source-reported FX move mismatch")
    require("not an independently reconstructed 09:45 event window" in fx.get("measurement_window", ""),
            "AI FX window must preserve precision warning")

    path = movement_by_type.get("POLICY_PROBABILITY_REPRICING") or {}
    require(path.get("movement_representation") == "QUALITATIVE_ONLY", "AI path representation mismatch")
    require(path.get("measurement_precision") == "QUALITATIVE_ONLY", "AI path precision mismatch")
    require(path.get("independently_reconstructed") is False, "AI path repricing must remain source-reported")

    connection = review.get("what_appears_connected") or {}
    require(connection.get("interaction_type") == "OBSERVATION_CONTEXT", "AI interaction type mismatch")
    require(connection.get("causal_status") == "OBSERVED_ASSOCIATION", "AI association status mismatch")
    require(connection.get("confidence") == "MEDIUM", "AI association confidence mismatch")
    require(len(review.get("alternative_explanations") or []) >= 3, "AI observed association requires explicit alternatives")
    require((review.get("second_order_effects") or {}).get("status") == "PLAUSIBLE_WATCH_ITEM",
            "AI second-order status mismatch")

    new_evidence_ids = {row.get("evidence_id") for row in payload.get("evidence", [])}
    require(new_evidence_ids == set(plan["new_evidence_ids"]), "AI evidence IDs differ from plan")
    require(new_evidence_ids.isdisjoint({row.get("evidence_id") for row in evidence.get("evidence", [])}),
            "AI would duplicate analytical evidence")
    require(review["analysis_id"] not in {row.get("analysis_id") for row in reviews.get("reviews", [])},
            "AI would duplicate analytical review")

    target = next(row for row in canonical["records"] if row.get("occurrence_id") == review["canonical_occurrence_id"])
    require(review.get("canonical_series_id") == target.get("series_id"), "AI review series does not match canonical")
    require(review.get("canonical_event_type") == target.get("event_type"), "AI review event type does not match canonical")
    require(review.get("canonical_institution") == target.get("institution"), "AI review institution does not match canonical")
    require(review.get("canonical_release_utc") == target.get("start_utc"), "AI review UTC does not match canonical")
    require(target.get("region") == "North America", "AI target region drifted")

    guardrails = plan["guardrails"]
    for key in (
        "headline_hold_equals_guidance_surprise",
        "exact_canonical_timestamp_implies_exact_market_series",
        "daily_fx_range_is_exact_event_window",
        "same_day_tsx_move_is_clean_boc_reaction",
        "source_reported_market_repricing_is_causal_estimate",
        "global_bond_fx_energy_context_can_be_ignored",
        "queue_completion_is_population_objective",
        "market_structure_gap_must_be_filled_next",
    ):
        require(guardrails.get(key) is False, f"AI guardrail must remain false: {key}")


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
    require(report.ok, "AI post-state failed Analysis validation: " + "; ".join(report.errors))
    readiness = analysis_population_readiness(schema, new_reviews, canonical)
    require((new_reviews["version"], len(new_reviews["reviews"])) ==
            (post["analysis_reviews_version"], post["analysis_review_count"]), "AI review post-state mismatch")
    require((new_evidence["version"], len(new_evidence["evidence"])) ==
            (post["analysis_evidence_version"], post["analysis_evidence_count"]), "AI evidence post-state mismatch")
    require(readiness["eligible_completed_occurrence_count"] == post["eligible_completed_occurrence_count"], "AI eligible count mismatch")
    require(readiness["reviewed_occurrence_count"] == post["reviewed_occurrence_count"], "AI reviewed count mismatch")
    require(readiness["reviewed_event_type_diversity"] == post["reviewed_event_type_diversity"], "AI diversity mismatch")
    require(readiness["reviewed_by_region"].get("North America", 0) == post["reviewed_north_america_occurrence_count"],
            "AI North America reviewed count mismatch")
    require(readiness["broad_population_state"] == post["broad_population_state"], "AI readiness state mismatch")
    require(exact_timestamp_series_rows(new_reviews) == post["post_analysis_exact_timestamp_series_rows"],
            "AI must not fabricate EXACT_TIMESTAMP_SERIES precision")

    remaining = sorted(
        row["occurrence_id"] for row in canonical["records"]
        if row.get("lifecycle_status") == "COMPLETED"
        and row["occurrence_id"] not in set(readiness["reviewed_occurrence_ids"])
    )
    require(remaining == sorted(post["remaining_eligible_unreviewed_occurrence_ids"]),
            f"AI remaining eligible-unreviewed mismatch: {remaining}")

    projection = public_analysis_projection(schema, new_evidence, new_reviews, canonical)
    projected = next(row for row in projection["reviews"] if row["analysis_id"] == plan["new_analysis_id"])
    require(projected.get("what_surprised", {}).get("status") == "MIXED", "AI public projection lost mixed surprise")
    require(len(projected.get("what_moved") or []) == 2, "AI public projection lost market observations")
    require(projected.get("what_appears_connected", {}).get("causal_status") == "OBSERVED_ASSOCIATION",
            "AI public projection changed association status")
    require(projected.get("canonical", {}).get("region") == "North America", "AI public projection lost North America")
    require(projected.get("canonical", {}).get("start_utc") == "2026-09-02T13:45:00Z",
            "AI public projection lost exact canonical UTC")
    require(all(row.get("measurement_precision") != "EXACT_TIMESTAMP_SERIES" for row in projected.get("what_moved", [])),
            "AI public projection invented exact timestamp market series")

    return new_reviews, new_evidence, readiness, projection


def audit_text(plan: dict[str, Any], readiness: dict[str, Any], hashes: dict[str, str]) -> str:
    lines = [
        "# WORLD SIGNALS — Bank of Canada Analysis AI transaction audit v0.1", "",
        "**Transaction date:** 2026-09-06  ",
        "**Canonical checkpoint:** v0.37 / 687 — unchanged  ",
        "**Analysis post-state:** schema v0.3; reviews v0.9 / 13; evidence v0.9 / 50", "",
        "## Added reviewed specimen", "",
        "- `WSAN-CA-BOC-20260902-001` — Bank of Canada 2 September 2026 policy decision — `DECISION`.",
        "- North America becomes represented in the reviewed Analysis sample.",
        "- headline 2.25% hold exactly matches the 35/35 Reuters economist consensus.",
        "- communication/path surprise remains separately classified `MIXED`: no headline surprise, but a more hawkish path signal.",
        "- CAD and policy-path repricing are source-reported market observations, not independently reconstructed event-time series.",
        "- observed association is `OBSERVED_ASSOCIATION` / `MEDIUM`; explicit global-bond, USD, energy, tariff and geopolitical alternatives are retained.",
        "- exact canonical 09:45 ET / 13:45Z timing does not promote market evidence to `EXACT_TIMESTAMP_SERIES`.",
        "", "## Readiness effect", "",
        f"- completed Analysis-eligible occurrences: {readiness['eligible_completed_occurrence_count']}",
        f"- reviewed completed occurrences: {readiness['reviewed_occurrence_count']}",
        f"- reviewed event-type diversity: {readiness['reviewed_event_type_diversity']}",
        f"- reviewed North America occurrences: {readiness['reviewed_by_region'].get('North America', 0)}",
        "- corporate/financial-market-structure remains an upstream completed-anchor gap; AI does not fill it mechanically.",
        "", "## Protected upstream SHA-256", "",
    ]
    for label, digest in hashes.items():
        lines.append(f"- {label}: `{digest}`")
    lines.extend(["", "PR #40 remains untouched.", ""])
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
    before_hashes = protected_hashes()

    new_reviews, new_evidence, readiness, _projection = transform(
        plan, payload, canonical, sources, ledger, overlay, schema, reviews, evidence
    )

    result = {
        "analysis_id": plan["new_analysis_id"],
        "reviews_post": [new_reviews["version"], len(new_reviews["reviews"])],
        "evidence_post": [new_evidence["version"], len(new_evidence["evidence"])],
        "canonical_checkpoint_post": new_reviews["canonical_checkpoint"],
        "eligible_completed": readiness["eligible_completed_occurrence_count"],
        "reviewed_completed": readiness["reviewed_occurrence_count"],
        "reviewed_north_america": readiness["reviewed_by_region"].get("North America", 0),
        "exact_timestamp_series_rows": exact_timestamp_series_rows(new_reviews),
    }

    if not args.apply:
        print("CHECK_ONLY_OK")
        print(json.dumps(result, indent=2))
        return

    if os.environ.get(APPLY_ENV) != "REVIEWED_APPLY":
        raise SystemExit(f"APPLY BLOCKED: set {APPLY_ENV}=REVIEWED_APPLY in the reviewed transaction workflow")

    write(REVIEWS_PATH, new_reviews)
    write(EVIDENCE_PATH, new_evidence)
    after_hashes = protected_hashes()
    require(after_hashes == before_hashes, "AI protected upstream drift detected")
    AUDIT_PATH.write_text(audit_text(plan, readiness, after_hashes), encoding="utf-8")

    print("APPLY_OK")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
