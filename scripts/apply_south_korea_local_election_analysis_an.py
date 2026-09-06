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
PLAN_PATH = ROOT / "data/analysis/SOUTH_KOREA_LOCAL_ELECTION_ANALYSIS_AN_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/analysis/SOUTH_KOREA_LOCAL_ELECTION_ANALYSIS_AN_PAYLOAD_v0.1.json"
AUDIT_PATH = ROOT / "data/analysis/SOUTH_KOREA_LOCAL_ELECTION_ANALYSIS_AN_TRANSACTION_AUDIT_v0.1.md"

APPLY_ENV = "WORLD_SIGNALS_APPLY_ANALYSIS_AN"

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


def version_tuple(raw: Any) -> tuple[int, ...]:
    return tuple(int(part) for part in str(raw).split("."))


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
    require(
        (canonical.get("version"), len(canonical.get("records", []))) ==
        (pre["canonical_registry_version"], pre["canonical_record_count"]),
        "AN canonical pre-state mismatch",
    )
    require(
        (sources.get("version"), len(sources.get("sources", []))) ==
        (pre["source_registry_version"], pre["source_record_count"]),
        "AN source pre-state mismatch",
    )
    require(
        (ledger.get("version"), len(ledger.get("changes", []))) ==
        (pre["change_ledger_version"], pre["change_ledger_count"]),
        "AN ledger pre-state mismatch",
    )
    require(
        (overlay.get("version"), overlay.get("canonical_checkpoint")) ==
        (pre["biosecurity_overlay_version"], pre["biosecurity_overlay_checkpoint"]),
        "AN overlay pre-state mismatch",
    )
    require(expectations.get("version") == pre["monitor_expectations_version"], "AN monitor expectations pre-state mismatch")
    require(schema.get("version") == pre["analysis_schema_version"], "AN Analysis schema pre-state mismatch")
    require(
        (reviews.get("version"), len(reviews.get("reviews", []))) ==
        (pre["analysis_reviews_version"], pre["analysis_review_count"]),
        "AN reviews pre-state mismatch",
    )
    require(
        reviews.get("canonical_checkpoint") == pre["analysis_reviews_canonical_checkpoint"],
        "AN reviews canonical checkpoint mismatch",
    )
    require(
        (evidence.get("version"), len(evidence.get("evidence", []))) ==
        (pre["analysis_evidence_version"], pre["analysis_evidence_count"]),
        "AN evidence pre-state mismatch",
    )

    readiness = analysis_population_readiness(schema, reviews, canonical)
    require(
        readiness["eligible_completed_occurrence_count"] == pre["eligible_completed_occurrence_count"],
        "AN eligible completed count drifted",
    )
    require(readiness["reviewed_occurrence_count"] == pre["reviewed_occurrence_count"], "AN reviewed count drifted")
    require(
        readiness["reviewed_event_type_diversity"] == pre["reviewed_event_type_diversity"],
        "AN event-type diversity drifted",
    )
    require(
        exact_timestamp_series_rows(reviews) == pre["required_pre_analysis_exact_timestamp_series_rows"],
        "AN exact-timestamp market-measurement pre-state drifted",
    )

    target = next(
        (row for row in canonical["records"] if row.get("occurrence_id") == pre["required_target_occurrence_id"]),
        None,
    )
    require(target is not None, "AN target canonical occurrence missing")
    require(target.get("series_id") == pre["required_target_series_id"], "AN target series mismatch")
    require(target.get("category") == pre["required_target_category"], "AN target category mismatch")
    require(target.get("event_type") == pre["required_target_event_type"], "AN target event type mismatch")
    require(target.get("lifecycle_status") == pre["required_target_lifecycle"], "AN target lifecycle mismatch")
    require(target.get("start_local") == pre["required_target_start_local"], "AN target local date mismatch")
    require(target.get("source_timezone") == pre["required_target_source_timezone"], "AN target timezone mismatch")
    require(target.get("start_utc") == pre["required_target_start_utc"], "AN target UTC mismatch")
    require(target.get("time_precision") == pre["required_target_time_precision"], "AN target precision mismatch")
    require(target.get("timing_type") == "CIVIL_DATE", "AN target must remain a civil-date election milestone")
    require(target.get("all_day_semantics") is True, "AN target must retain all-day civil-date semantics")

    existing = {row.get("analysis_id") for row in reviews.get("reviews", [])}
    for analysis_id in pre["required_absent_analysis_ids"]:
        require(analysis_id not in existing, f"AN analysis already exists: {analysis_id}")


def assert_payload(
    plan: dict[str, Any],
    payload: dict[str, Any],
    canonical: dict[str, Any],
    reviews: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    require(payload.get("tranche") == "SOUTH_KOREA_LOCAL_ELECTION_ANALYSIS_AN", "wrong AN payload")
    require(len(payload.get("reviews", [])) == 1, "AN must contain exactly one review")
    review = payload["reviews"][0]
    require(review.get("analysis_id") == plan["new_analysis_id"], "AN analysis ID differs from plan")
    require(
        review.get("canonical_occurrence_id") == plan["selection"]["selected_occurrence_id"],
        "AN target differs from plan",
    )
    require(review.get("canonical_release_utc") is None, "AN may not invent UTC for a civil-date election")
    require(review.get("what_surprised", {}).get("status") == "NOT_ESTABLISHED", "AN surprise must remain NOT_ESTABLISHED")
    require((review.get("what_surprised") or {}).get("comparisons") == [], "AN must not fabricate aggregate forecast-error comparisons")
    require(review.get("what_moved") == [], "AN must not manufacture an election-specific market response")

    benchmarks = (review.get("what_was_expected") or {}).get("benchmarks") or []
    require(len(benchmarks) == 1, "AN must preserve exactly one directional expectation benchmark")
    require(
        benchmarks[0].get("benchmark_type") == "OTHER_DEFENSIBLE_EXPECTATION",
        "AN directional political environment must not be promoted to a market/seat consensus",
    )

    actuals = {row.get("metric"): row.get("value") for row in (review.get("what_happened") or {}).get("actuals", [])}
    require(actuals.get("major_mayoral_provincial_contests_won_by_democratic_party") == 12, "AN DP major-result count drifted")
    require(actuals.get("major_mayoral_provincial_contests_won_by_people_power_party") == 4, "AN PPP major-result count drifted")
    require(actuals.get("polling_stations_receiving_supplemental_ballots") == 140, "AN supplemental dispatch count drifted")
    require(actuals.get("polling_stations_using_supplemental_ballots") == 91, "AN supplemental use count drifted")
    require(actuals.get("polling_stations_with_temporary_voting_interruption_and_resumption") == 26, "AN interruption count drifted")

    connection = review.get("what_appears_connected") or {}
    require(connection.get("interaction_type") == "POLICY_RESPONSE_CONTEXT", "AN interaction type mismatch")
    require(connection.get("causal_status") == "OBSERVED_ASSOCIATION", "AN causal boundary drifted")
    require(connection.get("confidence") == "MEDIUM", "AN connection confidence mismatch")
    require(
        (review.get("second_order_effects") or {}).get("status") == "OBSERVED",
        "AN second-order election-administration consequences must remain observed",
    )
    require(len(review.get("alternative_explanations") or []) >= 4, "AN must retain alternative explanations")
    require(len(review.get("falsifiers") or []) >= 7, "AN must retain explicit falsifiers")

    new_evidence_ids = {row.get("evidence_id") for row in payload.get("evidence", [])}
    require(new_evidence_ids == set(plan["new_evidence_ids"]), "AN evidence IDs differ from plan")
    require(len(new_evidence_ids) == 8, "AN evidence packet must contain exactly eight reviewed rows")
    require(
        new_evidence_ids.isdisjoint({row.get("evidence_id") for row in evidence.get("evidence", [])}),
        "AN would duplicate analytical evidence",
    )
    require(
        review["analysis_id"] not in {row.get("analysis_id") for row in reviews.get("reviews", [])},
        "AN would duplicate analytical review",
    )

    target = next(row for row in canonical["records"] if row.get("occurrence_id") == review["canonical_occurrence_id"])
    require(review.get("canonical_series_id") == target.get("series_id"), "AN review series does not match canonical")
    require(review.get("canonical_event_type") == target.get("event_type"), "AN review event type does not match canonical")
    require(review.get("canonical_institution") == target.get("institution"), "AN review institution does not match canonical")
    require(review.get("canonical_release_utc") == target.get("start_utc"), "AN review UTC does not match canonical")

    required_false = (
        "nationwide_simultaneous_election_is_single_national_result",
        "major_mayoral_provincial_12_of_16_is_complete_election_result",
        "party_polling_is_exact_seat_forecast",
        "post_vote_exit_poll_is_pre_event_expectation",
        "ballot_shortage_establishes_fraud",
        "ballot_shortage_automatically_invalidates_reported_winners",
        "ballot_shortage_is_proven_cause_of_partisan_result",
        "protests_and_reform_are_caused_by_dp_12_of_16_result",
        "polling_hours_resolve_canonical_utc",
        "early_voting_redefines_canonical_election_day",
        "empty_market_response_is_missing_work",
        "queue_completion_is_population_objective",
        "market_structure_gap_must_be_filled_next",
        "auto_merge",
    )
    for key in required_false:
        require(plan["guardrails"].get(key) is False, f"AN guardrail must remain false: {key}")


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
    require(report.ok, "AN post-state failed Analysis validation: " + "; ".join(report.errors))
    readiness = analysis_population_readiness(schema, new_reviews, canonical)
    require(
        (new_reviews["version"], len(new_reviews["reviews"])) ==
        (post["analysis_reviews_version"], post["analysis_review_count"]),
        "AN review post-state mismatch",
    )
    require(
        (new_evidence["version"], len(new_evidence["evidence"])) ==
        (post["analysis_evidence_version"], post["analysis_evidence_count"]),
        "AN evidence post-state mismatch",
    )
    require(readiness["eligible_completed_occurrence_count"] == post["eligible_completed_occurrence_count"], "AN eligible count mismatch")
    require(readiness["reviewed_occurrence_count"] == post["reviewed_occurrence_count"], "AN reviewed count mismatch")
    require(readiness["reviewed_event_type_diversity"] == post["reviewed_event_type_diversity"], "AN diversity mismatch")
    require(
        readiness["reviewed_by_event_type"].get("ELECTION_MILESTONE", 0) == post["reviewed_election_milestone_occurrence_count"],
        "AN election milestone reviewed count mismatch",
    )
    require(readiness["broad_population_state"] == post["broad_population_state"], "AN readiness state mismatch")
    require(
        exact_timestamp_series_rows(new_reviews) == post["post_analysis_exact_timestamp_series_rows"],
        "AN must not fabricate EXACT_TIMESTAMP_SERIES precision",
    )

    remaining = sorted(
        row["occurrence_id"]
        for row in canonical["records"]
        if row.get("lifecycle_status") == "COMPLETED"
        and row["occurrence_id"] not in set(readiness["reviewed_occurrence_ids"])
    )
    require(
        remaining == sorted(post["remaining_eligible_unreviewed_occurrence_ids"]),
        f"AN remaining eligible-unreviewed mismatch: {remaining}",
    )

    projection = public_analysis_projection(schema, new_evidence, new_reviews, canonical)
    projected = next(row for row in projection["reviews"] if row["analysis_id"] == plan["new_analysis_id"])
    require(projected.get("what_surprised", {}).get("status") == "NOT_ESTABLISHED", "AN projection changed surprise status")
    require(projected.get("what_moved") == [], "AN projection invented market movement")
    require(projected.get("what_appears_connected", {}).get("causal_status") == "OBSERVED_ASSOCIATION", "AN projection changed causal boundary")
    require(projected.get("second_order_effects", {}).get("status") == "OBSERVED", "AN projection lost observed second-order state")
    require(projected.get("canonical", {}).get("event_type") == "ELECTION_MILESTONE", "AN projection lost event type")
    require(projected.get("canonical", {}).get("start_local") == "2026-06-03", "AN projection lost canonical civil date")
    require(projected.get("canonical", {}).get("start_utc") is None, "AN projection invented canonical UTC")
    require(projected.get("canonical", {}).get("source_timezone") == "Asia/Seoul", "AN projection lost canonical timezone")

    return new_reviews, new_evidence


def audit_text(before: dict[str, str], after: dict[str, str], plan: dict[str, Any]) -> str:
    same = before == after
    return "\n".join([
        "# WORLD SIGNALS — South Korea local-election Analysis AN transaction audit v0.1",
        "",
        f"**Reference date:** {plan['reference_date']}",
        f"**Exact base main:** `{plan['base_main_sha']}`",
        "**Architecture layer:** Analysis only",
        "",
        "## Mutation",
        "",
        "- Analysis reviews: **v0.11 / 15 → v0.12 / 16**",
        "- Analysis evidence: **v0.11 / 59 → v0.12 / 67**",
        "- added `WSAN-KR-LGE-20260603-001` for canonical `WSO-EL-KR-LGE-20260603`",
        "- Analysis schema remains **v0.4**",
        "- production `EXACT_TIMESTAMP_SERIES` remains **0**",
        "",
        "## Analytical boundary",
        "",
        "- the nationwide simultaneous election remains a distributed electoral process, not a synthetic single national result or mandate",
        "- pre-election party/political context remains directional, not an exact 12-of-16 forecast",
        "- the post-vote exit poll remains observation context, not an ex-ante expectation benchmark",
        "- surprise remains `NOT_ESTABLISHED` rather than manufacturing an aggregate forecast error",
        "- `what_moved` remains empty; no election-specific market response is invented",
        "- ballot-supply failure is separated from partisan-result causality and from fraud/legal-invalidity claims",
        "- observed second-order effects attach to election administration: protests, NEC consequences, investigation and reform pressure",
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
    new_reviews, new_evidence = transform(
        plan,
        payload,
        canonical,
        sources,
        ledger,
        overlay,
        expectations,
        schema,
        reviews,
        evidence,
    )

    if args.check:
        require(protected_hashes() == before, "AN --check mutated protected state")
        print("AN_CHECK_OK")
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
    require(after == before, "AN write mutated protected upstream/configuration state")
    AUDIT_PATH.write_text(audit_text(before, after, plan), encoding="utf-8")
    print("AN_WRITE_OK")


if __name__ == "__main__":
    main()
