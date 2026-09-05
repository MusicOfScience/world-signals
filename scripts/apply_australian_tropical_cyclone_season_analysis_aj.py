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
PLAN_PATH = ROOT / "data/analysis/AUSTRALIAN_TROPICAL_CYCLONE_SEASON_ANALYSIS_AJ_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/analysis/AUSTRALIAN_TROPICAL_CYCLONE_SEASON_ANALYSIS_AJ_PAYLOAD_v0.1.json"
AUDIT_PATH = ROOT / "data/analysis/AUSTRALIAN_TROPICAL_CYCLONE_SEASON_ANALYSIS_AJ_TRANSACTION_AUDIT_v0.1.md"

APPLY_ENV = "WORLD_SIGNALS_APPLY_ANALYSIS_AJ"

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
            (pre["canonical_registry_version"], pre["canonical_record_count"]), "AJ canonical pre-state mismatch")
    require((sources.get("version"), len(sources.get("sources", []))) ==
            (pre["source_registry_version"], pre["source_record_count"]), "AJ source pre-state mismatch")
    require((ledger.get("version"), len(ledger.get("changes", []))) ==
            (pre["change_ledger_version"], pre["change_ledger_count"]), "AJ ledger pre-state mismatch")
    require((overlay.get("version"), overlay.get("canonical_checkpoint")) ==
            (pre["biosecurity_overlay_version"], pre["biosecurity_overlay_checkpoint"]), "AJ overlay pre-state mismatch")
    require(schema.get("version") == pre["analysis_schema_version"], "AJ Analysis schema pre-state mismatch")
    require((reviews.get("version"), len(reviews.get("reviews", []))) ==
            (pre["analysis_reviews_version"], pre["analysis_review_count"]), "AJ reviews pre-state mismatch")
    require(reviews.get("canonical_checkpoint") == pre["analysis_reviews_canonical_checkpoint"],
            "AJ reviews canonical checkpoint mismatch")
    require((evidence.get("version"), len(evidence.get("evidence", []))) ==
            (pre["analysis_evidence_version"], pre["analysis_evidence_count"]), "AJ evidence pre-state mismatch")

    readiness = analysis_population_readiness(schema, reviews, canonical)
    require(readiness["eligible_completed_occurrence_count"] == pre["eligible_completed_occurrence_count"],
            "AJ eligible completed count drifted")
    require(readiness["reviewed_occurrence_count"] == pre["reviewed_occurrence_count"],
            "AJ reviewed count drifted")
    require(readiness["reviewed_event_type_diversity"] == pre["reviewed_event_type_diversity"],
            "AJ event-type diversity drifted")
    require(exact_timestamp_series_rows(reviews) == pre["required_pre_analysis_exact_timestamp_series_rows"],
            "AJ exact-timestamp market-measurement pre-state drifted")

    target = next((row for row in canonical["records"] if row.get("occurrence_id") == pre["required_target_occurrence_id"]), None)
    require(target is not None, "AJ target canonical occurrence missing")
    require(target.get("series_id") == pre["required_target_series_id"], "AJ target series mismatch")
    require(target.get("category") == pre["required_target_category"], "AJ target category mismatch")
    require(target.get("event_type") == pre["required_target_event_type"], "AJ target event type mismatch")
    require(target.get("lifecycle_status") == pre["required_target_lifecycle"], "AJ target lifecycle mismatch")
    require(target.get("start_local") == pre["required_target_start_local"], "AJ target start mismatch")
    require(target.get("end_local") == pre["required_target_end_local"], "AJ target end mismatch")
    require(target.get("source_timezone") == pre["required_target_source_timezone"], "AJ target timezone mismatch")
    require(target.get("start_utc") == pre["required_target_start_utc"], "AJ target start UTC mismatch")
    require(target.get("end_utc") == pre["required_target_end_utc"], "AJ target end UTC mismatch")
    require(target.get("time_precision") == pre["required_target_time_precision"], "AJ target precision mismatch")

    existing = {row.get("analysis_id") for row in reviews.get("reviews", [])}
    for analysis_id in pre["required_absent_analysis_ids"]:
        require(analysis_id not in existing, f"AJ analysis already exists: {analysis_id}")


def assert_payload(
    plan: dict[str, Any], payload: dict[str, Any], canonical: dict[str, Any],
    reviews: dict[str, Any], evidence: dict[str, Any],
) -> None:
    require(payload.get("tranche") == "AUSTRALIAN_TROPICAL_CYCLONE_SEASON_ANALYSIS_AJ", "wrong AJ payload")
    require(len(payload.get("reviews", [])) == 1, "AJ must contain exactly one review")
    review = payload["reviews"][0]
    require(review.get("analysis_id") == plan["new_analysis_id"], "AJ analysis ID differs from plan")
    require(review.get("canonical_occurrence_id") == plan["selection"]["selected_occurrence_id"], "AJ target differs from plan")
    require(review.get("canonical_release_utc") is None, "AJ seasonal window must not invent a canonical release UTC")
    require(review.get("what_surprised", {}).get("status") == "NOT_ESTABLISHED",
            "AJ surprise must remain NOT_ESTABLISHED")
    require((review.get("what_surprised") or {}).get("comparisons") == [],
            "AJ must not convert climatology into forecast-error comparisons")
    require(review.get("what_moved") == [], "AJ must not invent an aggregate seasonal market movement")

    benchmarks = (review.get("what_was_expected") or {}).get("benchmarks") or []
    require(len(benchmarks) == 3, "AJ must preserve two climatological benchmarks and one risk-guidance benchmark")
    by_metric = {row.get("metric"): row for row in benchmarks}
    count = by_metric.get("climatological_australian_region_tropical_cyclone_count") or {}
    require(count.get("value") == 10 and count.get("benchmark_type") == "OTHER_DEFENSIBLE_EXPECTATION",
            "AJ cyclone climatology benchmark drifted")
    landfall = by_metric.get("typical_mainland_landfalls") or {}
    require(landfall.get("value") == "3-4" and landfall.get("benchmark_type") == "OTHER_DEFENSIBLE_EXPECTATION",
            "AJ landfall climatology benchmark drifted")

    actuals = {row.get("metric"): row for row in (review.get("what_happened") or {}).get("actuals", [])}
    require(actuals.get("australian_region_tropical_cyclone_count", {}).get("value") == 11,
            "AJ cyclone count drifted")
    require(actuals.get("severe_tropical_cyclone_count", {}).get("value") == 7,
            "AJ severe cyclone count drifted")
    require(actuals.get("mainland_landfall_count_at_tropical_cyclone_strength", {}).get("value") == 4,
            "AJ cyclone-strength landfall count drifted")
    require(actuals.get("mainland_crossing_count_at_tropical_low_strength", {}).get("value") == 2,
            "AJ tropical-low crossing count drifted")

    connection = review.get("what_appears_connected") or {}
    require(connection.get("interaction_type") == "COMMON_DRIVER_CONTEXT", "AJ interaction type mismatch")
    require(connection.get("causal_status") == "NOT_A_CAUSAL_CLAIM", "AJ causal boundary drifted")
    require(connection.get("confidence") == "HIGH", "AJ context confidence mismatch")
    require((review.get("second_order_effects") or {}).get("status") == "NOT_ESTABLISHED",
            "AJ aggregate seasonal second-order effects must remain NOT_ESTABLISHED")
    require(len(review.get("falsifiers") or []) >= 4, "AJ must retain explicit falsifiers")

    new_evidence_ids = {row.get("evidence_id") for row in payload.get("evidence", [])}
    require(new_evidence_ids == set(plan["new_evidence_ids"]), "AJ evidence IDs differ from plan")
    require(new_evidence_ids.isdisjoint({row.get("evidence_id") for row in evidence.get("evidence", [])}),
            "AJ would duplicate analytical evidence")
    require(review["analysis_id"] not in {row.get("analysis_id") for row in reviews.get("reviews", [])},
            "AJ would duplicate analytical review")

    target = next(row for row in canonical["records"] if row.get("occurrence_id") == review["canonical_occurrence_id"])
    require(review.get("canonical_series_id") == target.get("series_id"), "AJ review series does not match canonical")
    require(review.get("canonical_event_type") == target.get("event_type"), "AJ review event type does not match canonical")
    require(review.get("canonical_institution") == target.get("institution"), "AJ review institution does not match canonical")
    require(review.get("canonical_release_utc") == target.get("start_utc"), "AJ review UTC does not match canonical")

    guardrails = plan["guardrails"]
    for key in (
        "climatological_average_is_season_specific_forecast",
        "eleven_vs_ten_is_directional_surprise",
        "season_window_equals_named_cyclone_occurrence",
        "severe_cyclone_count_implies_damage",
        "landfall_count_implies_market_move",
        "warm_sst_context_is_climate_change_attribution",
        "empty_market_response_is_missing_work",
        "queue_completion_is_population_objective",
        "market_structure_gap_must_be_filled_next",
    ):
        require(guardrails.get(key) is False, f"AJ guardrail must remain false: {key}")


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
    require(report.ok, "AJ post-state failed Analysis validation: " + "; ".join(report.errors))
    readiness = analysis_population_readiness(schema, new_reviews, canonical)
    require((new_reviews["version"], len(new_reviews["reviews"])) ==
            (post["analysis_reviews_version"], post["analysis_review_count"]), "AJ review post-state mismatch")
    require((new_evidence["version"], len(new_evidence["evidence"])) ==
            (post["analysis_evidence_version"], post["analysis_evidence_count"]), "AJ evidence post-state mismatch")
    require(readiness["eligible_completed_occurrence_count"] == post["eligible_completed_occurrence_count"],
            "AJ eligible count mismatch")
    require(readiness["reviewed_occurrence_count"] == post["reviewed_occurrence_count"],
            "AJ reviewed count mismatch")
    require(readiness["reviewed_event_type_diversity"] == post["reviewed_event_type_diversity"],
            "AJ diversity mismatch")
    require(readiness["reviewed_by_event_type"].get("PHYSICAL_RISK_WINDOW", 0) ==
            post["reviewed_physical_risk_window_occurrence_count"], "AJ physical-risk reviewed count mismatch")
    require(readiness["broad_population_state"] == post["broad_population_state"], "AJ readiness state mismatch")
    require(exact_timestamp_series_rows(new_reviews) == post["post_analysis_exact_timestamp_series_rows"],
            "AJ must not fabricate EXACT_TIMESTAMP_SERIES precision")

    remaining = sorted(
        row["occurrence_id"] for row in canonical["records"]
        if row.get("lifecycle_status") == "COMPLETED"
        and row["occurrence_id"] not in set(readiness["reviewed_occurrence_ids"])
    )
    require(remaining == sorted(post["remaining_eligible_unreviewed_occurrence_ids"]),
            f"AJ remaining eligible-unreviewed mismatch: {remaining}")

    projection = public_analysis_projection(schema, new_evidence, new_reviews, canonical)
    projected = next(row for row in projection["reviews"] if row["analysis_id"] == plan["new_analysis_id"])
    require(projected.get("what_surprised", {}).get("status") == "NOT_ESTABLISHED",
            "AJ public projection changed surprise status")
    require(projected.get("what_moved") == [], "AJ public projection invented market movement")
    require(projected.get("what_appears_connected", {}).get("causal_status") == "NOT_A_CAUSAL_CLAIM",
            "AJ public projection changed causal boundary")
    require(projected.get("canonical", {}).get("event_type") == "PHYSICAL_RISK_WINDOW",
            "AJ public projection lost physical-risk event type")
    require(projected.get("canonical", {}).get("start_local") == "2025-11-01",
            "AJ public projection lost season start")
    require(projected.get("canonical", {}).get("end_local") == "2026-04-30",
            "AJ public projection lost season end")
    require(projected.get("canonical", {}).get("start_utc") is None,
            "AJ public projection invented seasonal UTC")

    return new_reviews, new_evidence, readiness, projection


def audit_text(readiness: dict[str, Any], hashes: dict[str, str]) -> str:
    lines = [
        "# WORLD SIGNALS — Australian tropical cyclone season Analysis AJ transaction audit v0.1", "",
        "**Transaction date:** 2026-09-06  ",
        "**Canonical checkpoint:** v0.37 / 687 — unchanged  ",
        "**Analysis post-state:** schema v0.3; reviews v0.10 / 14; evidence v0.10 / 54", "",
        "## Added reviewed specimen", "",
        "- `WSAN-AU-TCSEASON-2025-26-001` — Australian tropical cyclone season 2025–26 — `PHYSICAL_RISK_WINDOW`.",
        "- first reviewed `PHYSICAL_CLIMATE_RISK` / `PHYSICAL_RISK_WINDOW` specimen.",
        "- Bureau outcome: 11 Australian-region cyclones; 7 severe; 4 mainland landfalls at cyclone strength; 2 additional tropical-low crossings.",
        "- Bureau climatology: about 10 cyclones and 3–4 landfalls is retained as planning context, not promoted to a 2025–26 point forecast.",
        "- surprise classification remains `NOT_ESTABLISHED`; no synthetic forecast error is created from 11 versus 10.",
        "- `what_moved` is intentionally empty; aggregate seasonal hazard counts are not market observations.",
        "- warm SST and climate conditions remain `COMMON_DRIVER_CONTEXT` / `NOT_A_CAUSAL_CLAIM`; no climate-change attribution is inferred.",
        "- seasonal window remains separate from named cyclones, landfalls, damage and shock-level second-order effects.",
        "", "## Readiness effect", "",
        f"- completed Analysis-eligible occurrences: {readiness['eligible_completed_occurrence_count']}",
        f"- reviewed completed occurrences: {readiness['reviewed_occurrence_count']}",
        f"- reviewed event-type diversity: {readiness['reviewed_event_type_diversity']}",
        f"- reviewed physical-risk windows: {readiness['reviewed_by_event_type'].get('PHYSICAL_RISK_WINDOW', 0)}",
        "- corporate/financial-market-structure remains an upstream completed-anchor gap; AJ does not fill it mechanically.",
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
        "reviewed_physical_risk_window": readiness["reviewed_by_event_type"].get("PHYSICAL_RISK_WINDOW", 0),
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
    require(after_hashes == before_hashes, "AJ protected upstream drift detected")
    AUDIT_PATH.write_text(audit_text(readiness, after_hashes), encoding="utf-8")

    print("APPLY_OK")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
