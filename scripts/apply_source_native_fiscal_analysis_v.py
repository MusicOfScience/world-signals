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

from world_signals.analysis import (
    analysis_population_readiness,
    public_analysis_projection,
    validate_analysis,
)

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
PLAN_PATH = ROOT / "data/analysis/SOURCE_NATIVE_FISCAL_ANALYSIS_V_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/analysis/SOURCE_NATIVE_FISCAL_ANALYSIS_V_PAYLOAD_v0.1.json"
AUDIT_PATH = ROOT / "data/analysis/SOURCE_NATIVE_FISCAL_ANALYSIS_V_TRANSACTION_AUDIT_v0.1.md"

APPLY_ENV = "WORLD_SIGNALS_APPLY_ANALYSIS_V"

PROTECTED_UPSTREAM = {
    "canonical registry": CANONICAL_PATH,
    "canonical schema": CANONICAL_SCHEMA_PATH,
    "source registry": SOURCES_PATH,
    "change ledger": LEDGER_PATH,
    "biosecurity overlay": OVERLAY_PATH,
    "monitor expectations": EXPECTATIONS_PATH,
    "monitor operations policy": OPERATIONS_PATH,
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_hashes() -> dict[str, str]:
    return {label: sha256(path) for label, path in PROTECTED_UPSTREAM.items()}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def assert_exact_pre_state(
    plan: dict[str, Any],
    canonical: dict[str, Any],
    sources: dict[str, Any],
    ledger: dict[str, Any],
    overlay: dict[str, Any],
    schema: dict[str, Any],
    reviews: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    pre = plan["preconditions"]
    require((canonical.get("version"), len(canonical.get("records", []))) ==
            (pre["canonical_registry_version"], pre["canonical_record_count"]),
            "canonical checkpoint is not the frozen V pre-state")
    require((sources.get("version"), len(sources.get("sources", []))) ==
            (pre["source_registry_version"], pre["source_record_count"]),
            "source registry is not the frozen V pre-state")
    require((ledger.get("version"), len(ledger.get("changes", []))) ==
            (pre["change_ledger_version"], pre["change_ledger_count"]),
            "change ledger is not the frozen V pre-state")
    require((overlay.get("version"), overlay.get("canonical_checkpoint")) ==
            (pre["biosecurity_overlay_version"], pre["biosecurity_overlay_checkpoint"]),
            "biosecurity overlay is not aligned to V base")

    # The v0.3 Analysis schema is the reviewed feature-branch contract evolution.
    require(schema.get("version") == plan["analysis_schema_evolution"]["to_version"],
            "Analysis schema is not the reviewed V contract version")
    temporal_policy = schema.get("temporal_context_policy") or {}
    for key, value in plan["analysis_schema_evolution"]["new_policy"].items():
        require(temporal_policy.get(key) is value, f"V temporal policy mismatch: {key}")

    require((reviews.get("version"), len(reviews.get("reviews", []))) ==
            (pre["analysis_reviews_version"], pre["analysis_review_count"]),
            "Analysis reviews are not the frozen V pre-state")
    require(reviews.get("canonical_checkpoint") == pre["analysis_reviews_canonical_checkpoint"],
            "Analysis review checkpoint changed before V")
    require((evidence.get("version"), len(evidence.get("evidence", []))) ==
            (pre["analysis_evidence_version"], pre["analysis_evidence_count"]),
            "Analysis evidence is not the frozen V pre-state")

    readiness = analysis_population_readiness(schema, reviews, canonical)
    require(readiness["eligible_completed_occurrence_count"] == pre["eligible_completed_occurrence_count"],
            "eligible completed count drifted before V")
    require(readiness["reviewed_occurrence_count"] == pre["reviewed_occurrence_count"],
            "reviewed occurrence count drifted before V")
    require(readiness["reviewed_event_type_diversity"] == pre["reviewed_event_type_diversity"],
            "reviewed event-type diversity drifted before V")

    target = next(
        (row for row in canonical["records"] if row.get("occurrence_id") == pre["required_target_occurrence_id"]),
        None,
    )
    require(target is not None, "V target canonical occurrence is missing")
    require(target.get("lifecycle_status") == pre["required_target_lifecycle"], "V target lifecycle changed")
    require(target.get("timing_type") == pre["required_target_timing_type"], "V target timing type changed")
    require(target.get("source_native_date_label") == pre["required_target_native_date_label"],
            "V target native date changed")
    require(target.get("gregorian_resolution_status") == pre["required_target_gregorian_resolution_status"],
            "V target Gregorian resolution state changed")
    require(target.get("start_local") is pre["required_target_start_local"],
            "V target gained synthetic local Gregorian time")
    require(target.get("start_utc") is pre["required_target_start_utc"],
            "V target gained synthetic UTC time")

    existing_analysis = {row.get("analysis_id") for row in reviews.get("reviews", [])}
    for analysis_id in pre["required_absent_analysis_ids"]:
        require(analysis_id not in existing_analysis, f"V analysis already exists: {analysis_id}")


def assert_payload_contract(
    plan: dict[str, Any],
    payload: dict[str, Any],
    canonical: dict[str, Any],
    reviews: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    require(payload.get("tranche") == "SOURCE_NATIVE_FISCAL_ANALYSIS_V", "wrong V payload")
    require(len(payload.get("reviews", [])) == 1, "V must contain exactly one review")
    review = payload["reviews"][0]
    require(review.get("analysis_id") == plan["new_analysis_id"], "V analysis ID differs from frozen plan")
    require(review.get("canonical_occurrence_id") == plan["selection"]["selected_occurrence_id"],
            "V review does not bind to frozen target")
    require(review.get("canonical_release_utc") is None, "V review must preserve null canonical UTC")

    new_evidence_ids = {row.get("evidence_id") for row in payload.get("evidence", [])}
    require(new_evidence_ids == set(plan["new_evidence_ids"]), "V evidence IDs differ from frozen plan")
    existing_evidence = {row.get("evidence_id") for row in evidence.get("evidence", [])}
    existing_analysis = {row.get("analysis_id") for row in reviews.get("reviews", [])}
    require(new_evidence_ids.isdisjoint(existing_evidence), "V would duplicate analytical evidence")
    require(review["analysis_id"] not in existing_analysis, "V would duplicate analytical review")

    canonical_by_id = {row["occurrence_id"]: row for row in canonical["records"]}
    target = canonical_by_id[plan["selection"]["selected_occurrence_id"]]
    require((target.get("series_id"), target.get("event_type"), target.get("lifecycle_status")) ==
            ("WSER-FIS-NP-FEDERAL-BUDGET", "FISCAL_POLICY_PROCESS", "COMPLETED"),
            "V canonical target identity changed")

    require(review["what_surprised"]["status"] == "NO_CLEAR_SURPRISE",
            "V must not manufacture a headline size surprise from the stale early ceiling")
    require("revised" in review["what_was_expected"]["summary"].lower(),
            "V expectation packet must preserve pre-event revision history")
    require(review["what_moved"][0]["movement_representation"] == "CHANGE_AND_ENDPOINT",
            "V market movement must preserve source-reported change+endpoint")
    require(review["what_moved"][0]["before_value"] is None,
            "V market movement must not reconstruct a pre-event baseline")
    require(review["what_appears_connected"]["causal_status"] == "NOT_A_CAUSAL_CLAIM",
            "V first-market observation must not become a causal claim")
    require(review["second_order_effects"]["status"] == "OBSERVED",
            "V must exercise observed second-order semantics")
    require("reconciliation" in review["second_order_effects"]["summary"].lower(),
            "V observed implementation signal must preserve reconciliation caveat")


def transform(
    plan: dict[str, Any],
    payload: dict[str, Any],
    canonical: dict[str, Any],
    sources: dict[str, Any],
    ledger: dict[str, Any],
    overlay: dict[str, Any],
    schema: dict[str, Any],
    reviews: dict[str, Any],
    evidence: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    assert_exact_pre_state(plan, canonical, sources, ledger, overlay, schema, reviews, evidence)
    assert_payload_contract(plan, payload, canonical, reviews, evidence)

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
    require(report.ok, "V post-state failed Analysis validation: " + "; ".join(report.errors))
    readiness = analysis_population_readiness(schema, new_reviews, canonical)
    require((new_reviews["version"], len(new_reviews["reviews"])) ==
            (post["analysis_reviews_version"], post["analysis_review_count"]), "V review post-state mismatch")
    require((new_evidence["version"], len(new_evidence["evidence"])) ==
            (post["analysis_evidence_version"], post["analysis_evidence_count"]), "V evidence post-state mismatch")
    require(readiness["eligible_completed_occurrence_count"] == post["eligible_completed_occurrence_count"],
            "V eligible count mismatch")
    require(readiness["reviewed_occurrence_count"] == post["reviewed_occurrence_count"],
            "V reviewed count mismatch")
    require(readiness["reviewed_event_type_diversity"] == post["reviewed_event_type_diversity"],
            "V event-type diversity mismatch")
    require(readiness["broad_population_state"] == post["broad_population_state"],
            "V readiness state mismatch")

    remaining = sorted(
        row["occurrence_id"] for row in canonical["records"]
        if row.get("lifecycle_status") == "COMPLETED"
        and row["occurrence_id"] not in set(readiness["reviewed_occurrence_ids"])
    )
    require(remaining == sorted(post["remaining_eligible_unreviewed_occurrence_ids"]),
            f"V remaining eligible-unreviewed set mismatch: {remaining}")

    projection = public_analysis_projection(schema, new_evidence, new_reviews, canonical)
    projected = next(row for row in projection["reviews"] if row["analysis_id"] == plan["new_analysis_id"])
    canonical_context = projected["canonical"]
    for field in plan["analysis_schema_evolution"]["required_public_canonical_temporal_fields"]:
        require(field in canonical_context, f"V public canonical context dropped temporal field {field}")
    require(canonical_context["source_native_date_label"] == "15 Jestha 2083",
            "V public projection lost source-native date")
    require(canonical_context["gregorian_resolution_status"] == "UNRESOLVED_AUTHORITATIVE_CONVERSION",
            "V public projection lost Gregorian-resolution state")
    require(canonical_context["start_local"] is None and canonical_context["start_utc"] is None,
            "V public projection inferred missing Gregorian/UTC time")

    return new_reviews, new_evidence, readiness, projection


def audit_text(plan: dict[str, Any], readiness: dict[str, Any], hashes: dict[str, str]) -> str:
    lines = [
        "# WORLD SIGNALS — Source-native fiscal analysis V transaction audit v0.1",
        "",
        "**Transaction date:** 2026-09-06  ",
        "**Canonical checkpoint:** v0.30 / 681 — unchanged  ",
        "**Analysis post-state:** schema v0.3; reviews v0.5 / 9; evidence v0.5 / 28",
        "",
        "## Added reviewed specimen",
        "",
        "- `WSAN-NP-BUDGET-2083-001` — Nepal Federal Budget 2083/84 — `FISCAL_POLICY_PROCESS`.",
        "- canonical date remains `15 Jestha 2083` / `BIKRAM_SAMBAT_NEPAL`.",
        "- canonical Gregorian and UTC timing remain unresolved and null.",
        "- headline budget size is `NO_CLEAR_SURPRISE` against the latest pre-event benchmark set.",
        "- first post-budget NEPSE session is recorded without a causal claim.",
        "- 3 September FCGO expenditure data are an `OBSERVED` second-order signal with reconciliation warning preserved.",
        "",
        "## Analysis temporal contract",
        "",
        "- public canonical context now preserves source-native timing fields and unresolved-conversion state.",
        "- noncanonical analytical reporting dates cannot resolve canonical Gregorian timing.",
        "- browser rendering may display canonical source-native dates but may not convert them.",
        "",
        "## Readiness",
        "",
        f"- eligible completed occurrences: {readiness['eligible_completed_occurrence_count']}",
        f"- reviewed occurrences: {readiness['reviewed_occurrence_count']}",
        f"- reviewed event-type diversity: {readiness['reviewed_event_type_diversity']}",
        f"- broad state: `{readiness['broad_population_state']}`",
        "",
        "## Remaining eligible unreviewed",
        "",
    ]
    lines.extend(f"- `{occurrence_id}`" for occurrence_id in plan["postconditions"]["remaining_eligible_unreviewed_occurrence_ids"])
    lines += [
        "",
        "## Protected upstream SHA-256",
        "",
    ]
    lines.extend(f"- {label}: `{digest}`" for label, digest in hashes.items())
    lines += [
        "",
        "Canonical/source/ledger/overlay/monitor files were hashed before and after the reviewed Analysis transaction and must remain byte-identical.",
        "",
        "## Write gates",
        "",
        "- automatic canonical commit: **OFF**",
        "- Google Calendar write: **OFF**",
        "- canonical/source/monitor/ledger/overlay mutation from Analysis: **PROHIBITED**",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fail-closed source-native fiscal Analysis V transaction")
    parser.add_argument("--apply", action="store_true", help="write reviewed V Analysis post-state")
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

    mode = "CHECK_ONLY"
    if args.apply:
        require(os.environ.get(APPLY_ENV) == "YES", f"--apply requires {APPLY_ENV}=YES")
        write(REVIEWS_PATH, new_reviews)
        write(EVIDENCE_PATH, new_evidence)
        after_hashes = protected_hashes()
        require(before_hashes == after_hashes, "protected upstream file changed during V transaction")
        AUDIT_PATH.write_text(audit_text(plan, readiness, before_hashes), encoding="utf-8")
        mode = "APPLY"

    print(json.dumps({
        "mode": mode,
        "post": {
            "canonical_version": canonical["version"],
            "canonical_count": len(canonical["records"]),
            "analysis_schema_version": schema["version"],
            "analysis_reviews_version": new_reviews["version"],
            "analysis_review_count": len(new_reviews["reviews"]),
            "analysis_evidence_version": new_evidence["version"],
            "analysis_evidence_count": len(new_evidence["evidence"]),
            "eligible_completed_occurrence_count": readiness["eligible_completed_occurrence_count"],
            "reviewed_occurrence_count": readiness["reviewed_occurrence_count"],
            "reviewed_event_type_diversity": readiness["reviewed_event_type_diversity"],
            "broad_population_state": readiness["broad_population_state"],
        },
        "remaining_eligible_unreviewed": plan["postconditions"]["remaining_eligible_unreviewed_occurrence_ids"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
