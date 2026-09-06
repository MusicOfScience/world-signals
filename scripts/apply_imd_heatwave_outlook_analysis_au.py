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
PLAN_PATH = ROOT / "data/analysis/IMD_HEATWAVE_OUTLOOK_ANALYSIS_AU_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/analysis/IMD_HEATWAVE_OUTLOOK_ANALYSIS_AU_PAYLOAD_v0.1.json"
AUDIT_PATH = ROOT / "data/analysis/IMD_HEATWAVE_OUTLOOK_ANALYSIS_AU_TRANSACTION_AUDIT_v0.1.md"

APPLY_ENV = "WORLD_SIGNALS_APPLY_ANALYSIS_AU"

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
    require((canonical.get("version"), len(canonical.get("records", []))) == (pre["canonical_registry_version"], pre["canonical_record_count"]), "AU canonical pre-state mismatch")
    require((sources.get("version"), len(sources.get("sources", []))) == (pre["source_registry_version"], pre["source_record_count"]), "AU source pre-state mismatch")
    require((ledger.get("version"), len(ledger.get("changes", []))) == (pre["change_ledger_version"], pre["change_ledger_count"]), "AU ledger pre-state mismatch")
    require((overlay.get("version"), overlay.get("canonical_checkpoint")) == (pre["biosecurity_overlay_version"], pre["biosecurity_overlay_checkpoint"]), "AU overlay pre-state mismatch")
    require(expectations.get("version") == pre["monitor_expectations_version"], "AU monitor expectations pre-state mismatch")
    require(schema.get("version") == pre["analysis_schema_version"], "AU Analysis schema pre-state mismatch")
    require((reviews.get("version"), len(reviews.get("reviews", []))) == (pre["analysis_reviews_version"], pre["analysis_review_count"]), "AU reviews pre-state mismatch")
    require(reviews.get("canonical_checkpoint") == pre["analysis_reviews_canonical_checkpoint"], "AU reviews canonical checkpoint pre-state mismatch")
    require((evidence.get("version"), len(evidence.get("evidence", []))) == (pre["analysis_evidence_version"], pre["analysis_evidence_count"]), "AU evidence pre-state mismatch")

    readiness = analysis_population_readiness(schema, reviews, canonical)
    require(readiness["eligible_completed_occurrence_count"] == pre["eligible_completed_occurrence_count"], f"AU eligible completed count drifted: {readiness['eligible_completed_occurrence_count']}")
    require(readiness["reviewed_occurrence_count"] == pre["reviewed_occurrence_count"], "AU reviewed count drifted")
    require(readiness["reviewed_event_type_diversity"] == pre["reviewed_event_type_diversity"], "AU reviewed event-type diversity drifted")
    require(exact_timestamp_series_rows(reviews) == pre["required_pre_analysis_exact_timestamp_series_rows"], "AU exact-series pre-state drifted")

    target = next((row for row in canonical.get("records", []) if row.get("occurrence_id") == pre["required_target_occurrence_id"]), None)
    require(target is not None, "AU target canonical occurrence missing")
    checks = {
        "series_id": pre["required_target_series_id"],
        "source_id": pre["required_target_source_id"],
        "category": pre["required_target_category"],
        "event_type": pre["required_target_event_type"],
        "signal_object_class": pre["required_target_signal_object_class"],
        "lifecycle_status": pre["required_target_lifecycle"],
        "timing_type": pre["required_target_timing_type"],
        "start_local": pre["required_target_start_local"],
        "source_timezone": pre["required_target_source_timezone"],
        "start_utc": pre["required_target_start_utc"],
        "end_utc": pre["required_target_end_utc"],
        "time_precision": pre["required_target_time_precision"],
        "publication_time_semantics": pre["required_target_publication_time_semantics"],
        "physical_shock_routing": pre["required_target_physical_shock_routing"],
    }
    for field, expected in checks.items():
        require(target.get(field) == expected, f"AU target {field} mismatch: {target.get(field)!r} != {expected!r}")
    require(target.get("all_day_semantics") is True, "AU target must retain date-only all-day semantics")
    require(target.get("end_local") is None, "AU target must not turn forecast scope into occurrence window")
    require("April–June 2026" in str(target.get("reference_period")), "AU target forecast reference period lost")

    existing = {row.get("analysis_id") for row in reviews.get("reviews", [])}
    for analysis_id in pre["required_absent_analysis_ids"]:
        require(analysis_id not in existing, f"AU analysis already exists: {analysis_id}")


def assert_payload(
    plan: dict[str, Any],
    payload: dict[str, Any],
    canonical: dict[str, Any],
    reviews: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    require(payload.get("tranche") == "IMD_HEATWAVE_OUTLOOK_ANALYSIS_AU", "wrong AU payload")
    require(len(payload.get("reviews", [])) == 1, "AU must contain exactly one review")
    review = payload["reviews"][0]
    require(review.get("analysis_id") == plan["new_analysis_id"], "AU analysis ID differs from plan")
    require(review.get("canonical_occurrence_id") == plan["selection"]["selected_occurrence_id"], "AU target differs from plan")
    require(review.get("canonical_release_utc") is None, "AU may not invent a UTC publication timestamp")
    require((review.get("what_surprised") or {}).get("status") == "NOT_ESTABLISHED", "AU surprise must remain NOT_ESTABLISHED")
    require((review.get("what_surprised") or {}).get("comparisons") == [], "AU must not fabricate forecast-surprise comparisons")
    require(review.get("what_moved") == [], "AU must not manufacture market response")

    benchmarks = (review.get("what_was_expected") or {}).get("benchmarks") or []
    require(len(benchmarks) == 1, "AU must preserve exactly one prior official-guidance benchmark")
    require(benchmarks[0].get("benchmark_type") == "OFFICIAL_PRIOR_GUIDANCE", "AU benchmark type drifted")
    require(benchmarks[0].get("metric") == "prior_official_seasonal_heatwave_guidance", "AU benchmark metric drifted")

    connection = review.get("what_appears_connected") or {}
    require(connection.get("interaction_type") == "OBSERVATION_CONTEXT", "AU interaction type mismatch")
    require(connection.get("causal_status") == "NOT_A_CAUSAL_CLAIM", "AU causal boundary drifted")
    require(connection.get("confidence") == "HIGH", "AU connection confidence mismatch")
    require((review.get("second_order_effects") or {}).get("status") == "PLAUSIBLE_WATCH_ITEM", "AU second-order status must remain prospective")
    require(len(review.get("what_may_be_noise") or []) >= 10, "AU must retain forecast/observation noise checks")
    require(len(review.get("alternative_explanations") or []) >= 4, "AU must retain alternatives")
    require(len(review.get("falsifiers") or []) >= 10, "AU must retain falsifiers")

    evidence_rows = payload.get("evidence", [])
    new_ids = {row.get("evidence_id") for row in evidence_rows}
    require(new_ids == set(plan["new_evidence_ids"]), "AU evidence IDs differ from plan")
    require(len(evidence_rows) == 6, "AU evidence packet must contain exactly six rows")
    require(all(row.get("evidence_class") == "PRIMARY_OFFICIAL" for row in evidence_rows), "AU evidence must be primary official")
    require(all(row.get("canonical_provenance_effect") == "NONE" for row in evidence_rows), "AU evidence may not mutate canonical provenance")
    require(new_ids.isdisjoint({row.get("evidence_id") for row in evidence.get("evidence", [])}), "AU would duplicate evidence IDs")
    require(review["analysis_id"] not in {row.get("analysis_id") for row in reviews.get("reviews", [])}, "AU would duplicate review ID")

    roles = {role for row in evidence_rows for role in row.get("roles", [])}
    require("OFFICIAL_OUTCOME" in roles, "AU requires official-outcome evidence")
    require("EXPECTATION_BENCHMARK" in roles, "AU requires expectation evidence")
    require("CONTEXT_OR_ALTERNATIVE" in roles, "AU requires forecast/observation context evidence")

    target = next(row for row in canonical["records"] if row.get("occurrence_id") == review["canonical_occurrence_id"])
    require(review.get("canonical_series_id") == target.get("series_id"), "AU review series mismatch")
    require(review.get("canonical_event_type") == target.get("event_type"), "AU review event type mismatch")
    require(review.get("canonical_institution") == target.get("institution"), "AU review institution mismatch")
    require(review.get("canonical_release_utc") == target.get("start_utc"), "AU review UTC mismatch")

    required_false = (
        "forecast_period_equals_occurrence_timing",
        "hazard_equals_publication_event",
        "prior_mam_guidance_equals_matched_amj_benchmark",
        "forecast_evolution_equals_surprise",
        "later_monthly_forecast_equals_verifying_observation",
        "spatial_overlap_equals_skill_score",
        "later_heatwave_equals_forecast_success",
        "later_abatement_equals_forecast_failure",
        "publication_causes_heatwave",
        "publication_causes_preparedness_or_impacts",
        "same_period_market_move_is_publication_response",
        "analytical_evidence_resolves_missing_canonical_utc",
        "future_recurrence_inferred_from_cadence",
        "empty_market_response_is_missing_work",
        "queue_completion_is_population_objective",
        "japan_revision_requires_canonical_retiming",
        "prior_aq_live_count_is_permanent_ceiling",
        "auto_merge",
    )
    for key in required_false:
        require(plan["guardrails"].get(key) is False, f"AU guardrail must remain false: {key}")


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
    require(report.ok, "AU post-state failed Analysis validation: " + "; ".join(report.errors))
    readiness = analysis_population_readiness(schema, new_reviews, canonical)
    require((new_reviews["version"], len(new_reviews["reviews"])) == (post["analysis_reviews_version"], post["analysis_review_count"]), "AU review post-state mismatch")
    require(new_reviews.get("canonical_checkpoint") == post["analysis_reviews_canonical_checkpoint"], "AU review checkpoint post-state mismatch")
    require((new_evidence["version"], len(new_evidence["evidence"])) == (post["analysis_evidence_version"], post["analysis_evidence_count"]), "AU evidence post-state mismatch")
    require(readiness["eligible_completed_occurrence_count"] == post["eligible_completed_occurrence_count"], "AU eligible count mismatch")
    require(readiness["reviewed_occurrence_count"] == post["reviewed_occurrence_count"], "AU reviewed count mismatch")
    require(readiness["reviewed_event_type_diversity"] == post["reviewed_event_type_diversity"], "AU diversity mismatch")
    require(readiness["reviewed_by_event_type"].get("PHYSICAL_RISK_OUTLOOK_RELEASE", 0) == post["reviewed_physical_risk_outlook_release_occurrence_count"], "AU physical-risk outlook reviewed count mismatch")
    require(readiness["broad_population_state"] == post["broad_population_state"], "AU readiness state mismatch")
    require(exact_timestamp_series_rows(new_reviews) == post["post_analysis_exact_timestamp_series_rows"], "AU must not fabricate exact market series")

    reviewed_ids = set(readiness["reviewed_occurrence_ids"])
    remaining = sorted(
        row["occurrence_id"]
        for row in canonical["records"]
        if row.get("lifecycle_status") == "COMPLETED" and row["occurrence_id"] not in reviewed_ids
    )
    require(remaining == sorted(post["remaining_eligible_unreviewed_occurrence_ids"]), f"AU remaining frontier mismatch: {remaining}")
    return new_reviews, new_evidence


def audit_markdown(plan: dict[str, Any], protected_before: dict[str, str]) -> str:
    post = plan["postconditions"]
    return "\n".join([
        "# WORLD SIGNALS — IMD heatwave outlook Analysis AU transaction audit v0.1",
        "",
        f"- committed_at_utc: `{datetime.now(timezone.utc).isoformat()}`",
        f"- exact_base_main: `{plan['base_main_sha']}`",
        f"- occurrence: `{plan['selection']['selected_occurrence_id']}`",
        f"- new_analysis_id: `{plan['new_analysis_id']}`",
        f"- Analysis reviews: `0.15 / 19 -> {post['analysis_reviews_version']} / {post['analysis_review_count']}`",
        f"- Analysis evidence: `0.15 / 85 -> {post['analysis_evidence_version']} / {post['analysis_evidence_count']}`",
        f"- Analysis Canonical checkpoint: `v0.37/687 -> v{post['analysis_reviews_canonical_checkpoint']['registry_version']}/{post['analysis_reviews_canonical_checkpoint']['record_count']}`",
        f"- reviewed event-type diversity: `17 -> {post['reviewed_event_type_diversity']}`",
        "- new reviewed event type: `PHYSICAL_RISK_OUTLOOK_RELEASE`",
        "- remaining completed/unreviewed: `WSO-MAC-B-0041`",
        "- production `EXACT_TIMESTAMP_SERIES`: `0`",
        "",
        "## Analytical boundary",
        "",
        "AU treats the 31 March IMD object as a seasonal risk-information publication. It does not convert April-June into occurrence timing, does not score February MAM versus March AMJ guidance as a matched forecast error, and does not promote later monthly/operational products into proof of seasonal forecast skill.",
        "",
        "Later May/June products are retained as forecast-evolution and operational-weather context under `OBSERVATION_CONTEXT / NOT_A_CAUSAL_CLAIM`. IMD-named health, water, power, infrastructure and agriculture channels remain `PLAUSIBLE_WATCH_ITEM`, not observed effects.",
        "",
        "## Protected-state audit",
        "",
        "All Canonical, Source, Change Ledger, overlay, monitor and Analysis-schema hashes remained unchanged during the controlled Analysis write.",
        "",
        "```json",
        json.dumps(protected_before, indent=2),
        "```",
        "",
        "## Deliberate non-actions",
        "",
        "- no Canonical or Source Registry mutation",
        "- no Change Ledger mutation",
        "- no biosecurity overlay mutation",
        "- no monitor configuration mutation",
        "- no Analysis schema mutation",
        "- no market-response fabrication",
        "- no forecast-skill score",
        "- no future IMD recurrence",
        "- no Google Calendar write",
        "- no auto-merge",
        "",
    ])


def run_check() -> dict[str, Any]:
    plan = load(PLAN_PATH)
    payload = load(PAYLOAD_PATH)
    canonical = load(CANONICAL_PATH)
    sources = load(SOURCES_PATH)
    ledger = load(LEDGER_PATH)
    overlay = load(OVERLAY_PATH)
    expectations = load(EXPECTATIONS_PATH)
    schema = load(ANALYSIS_SCHEMA_PATH)
    reviews = load(REVIEWS_PATH)
    evidence = load(EVIDENCE_PATH)
    before = protected_hashes()
    new_reviews, new_evidence = transform(plan, payload, canonical, sources, ledger, overlay, expectations, schema, reviews, evidence)
    require(protected_hashes() == before, "AU read-only simulation mutated protected repository state")
    readiness = analysis_population_readiness(schema, new_reviews, canonical)
    return {
        "status": "PASS",
        "mode": "READ_ONLY_CHECK",
        "reviews_post": [new_reviews["version"], len(new_reviews["reviews"])],
        "evidence_post": [new_evidence["version"], len(new_evidence["evidence"])],
        "analysis_checkpoint_post": new_reviews["canonical_checkpoint"],
        "eligible_completed": readiness["eligible_completed_occurrence_count"],
        "reviewed": readiness["reviewed_occurrence_count"],
        "event_type_diversity": readiness["reviewed_event_type_diversity"],
        "exact_timestamp_series": exact_timestamp_series_rows(new_reviews),
        "automatic_canonical_commit": False,
        "google_calendar_write": False,
    }


def run_write() -> dict[str, Any]:
    require(os.environ.get(APPLY_ENV) == "1", f"AU write requires {APPLY_ENV}=1")
    plan = load(PLAN_PATH)
    payload = load(PAYLOAD_PATH)
    canonical = load(CANONICAL_PATH)
    sources = load(SOURCES_PATH)
    ledger = load(LEDGER_PATH)
    overlay = load(OVERLAY_PATH)
    expectations = load(EXPECTATIONS_PATH)
    schema = load(ANALYSIS_SCHEMA_PATH)
    reviews = load(REVIEWS_PATH)
    evidence = load(EVIDENCE_PATH)
    protected_before = protected_hashes()
    new_reviews, new_evidence = transform(plan, payload, canonical, sources, ledger, overlay, expectations, schema, reviews, evidence)

    write(REVIEWS_PATH, new_reviews)
    write(EVIDENCE_PATH, new_evidence)
    require(protected_hashes() == protected_before, "AU controlled write mutated protected datasets")

    report = validate_analysis(schema, load(EVIDENCE_PATH), load(REVIEWS_PATH), canonical)
    require(report.ok, "AU written state failed Analysis validation: " + "; ".join(report.errors))
    AUDIT_PATH.write_text(audit_markdown(plan, protected_before), encoding="utf-8")
    return {
        "status": "WROTE_CONTROLLED_AU_STATE",
        "reviews_post": [new_reviews["version"], len(new_reviews["reviews"])],
        "evidence_post": [new_evidence["version"], len(new_evidence["evidence"])],
        "analysis_checkpoint_post": new_reviews["canonical_checkpoint"],
        "protected_unchanged": True,
        "automatic_canonical_commit": False,
        "google_calendar_write": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    require(args.check ^ args.write, "choose exactly one of --check or --write")
    result = run_write() if args.write else run_check()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
