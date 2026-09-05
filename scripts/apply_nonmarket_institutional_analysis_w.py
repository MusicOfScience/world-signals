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
PLAN_PATH = ROOT / "data/analysis/NONMARKET_INSTITUTIONAL_ANALYSIS_W_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/analysis/NONMARKET_INSTITUTIONAL_ANALYSIS_W_PAYLOAD_v0.1.json"
AUDIT_PATH = ROOT / "data/analysis/NONMARKET_INSTITUTIONAL_ANALYSIS_W_TRANSACTION_AUDIT_v0.1.md"

APPLY_ENV = "WORLD_SIGNALS_APPLY_ANALYSIS_W"

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
            (pre["canonical_registry_version"], pre["canonical_record_count"]), "W canonical pre-state mismatch")
    require((sources.get("version"), len(sources.get("sources", []))) ==
            (pre["source_registry_version"], pre["source_record_count"]), "W source pre-state mismatch")
    require((ledger.get("version"), len(ledger.get("changes", []))) ==
            (pre["change_ledger_version"], pre["change_ledger_count"]), "W ledger pre-state mismatch")
    require((overlay.get("version"), overlay.get("canonical_checkpoint")) ==
            (pre["biosecurity_overlay_version"], pre["biosecurity_overlay_checkpoint"]), "W overlay pre-state mismatch")
    require(schema.get("version") == pre["analysis_schema_version"], "W Analysis schema pre-state mismatch")
    require((reviews.get("version"), len(reviews.get("reviews", []))) ==
            (pre["analysis_reviews_version"], pre["analysis_review_count"]), "W reviews pre-state mismatch")
    require(reviews.get("canonical_checkpoint") == pre["analysis_reviews_canonical_checkpoint"],
            "W reviews canonical checkpoint mismatch")
    require((evidence.get("version"), len(evidence.get("evidence", []))) ==
            (pre["analysis_evidence_version"], pre["analysis_evidence_count"]), "W evidence pre-state mismatch")

    readiness = analysis_population_readiness(schema, reviews, canonical)
    require(readiness["eligible_completed_occurrence_count"] == pre["eligible_completed_occurrence_count"],
            "W eligible completed count drifted")
    require(readiness["reviewed_occurrence_count"] == pre["reviewed_occurrence_count"],
            "W reviewed count drifted")
    require(readiness["reviewed_event_type_diversity"] == pre["reviewed_event_type_diversity"],
            "W event-type diversity drifted")

    target = next((row for row in canonical["records"] if row.get("occurrence_id") == pre["required_target_occurrence_id"]), None)
    require(target is not None, "W target canonical occurrence missing")
    require(target.get("series_id") == pre["required_target_series_id"], "W target series mismatch")
    require(target.get("event_type") == pre["required_target_event_type"], "W target event type mismatch")
    require(target.get("lifecycle_status") == pre["required_target_lifecycle"], "W target lifecycle mismatch")
    require(target.get("start_local") == pre["required_target_start_local"], "W target start_local mismatch")
    require(target.get("end_local") == pre["required_target_end_local"], "W target end_local mismatch")
    require(target.get("start_utc") is None, "W target must retain null start_utc")

    existing = {row.get("analysis_id") for row in reviews.get("reviews", [])}
    for analysis_id in pre["required_absent_analysis_ids"]:
        require(analysis_id not in existing, f"W analysis already exists: {analysis_id}")


def assert_payload(
    plan: dict[str, Any], payload: dict[str, Any], canonical: dict[str, Any],
    reviews: dict[str, Any], evidence: dict[str, Any],
) -> None:
    require(payload.get("tranche") == "NONMARKET_INSTITUTIONAL_ANALYSIS_W", "wrong W payload")
    require(len(payload.get("reviews", [])) == 1, "W must contain exactly one review")
    review = payload["reviews"][0]
    require(review.get("analysis_id") == plan["new_analysis_id"], "W analysis ID differs from plan")
    require(review.get("canonical_occurrence_id") == plan["selection"]["selected_occurrence_id"], "W target differs from plan")
    require(review.get("canonical_release_utc") is None, "W must preserve null canonical UTC")
    require(review.get("what_surprised", {}).get("status") == "NOT_ESTABLISHED", "W surprise must remain NOT_ESTABLISHED")
    require(review.get("what_surprised", {}).get("comparisons") == [], "W must not manufacture surprise comparisons")
    require(review.get("what_moved") == [], "W must not manufacture a market movement")
    connection = review.get("what_appears_connected") or {}
    require(connection.get("interaction_type") == "LEGAL_OR_OPERATIONAL_DEPENDENCY", "W process linkage mismatch")
    require(connection.get("causal_status") == "NOT_A_CAUSAL_CLAIM", "W must remain non-causal")
    require((review.get("second_order_effects") or {}).get("status") == "PLAUSIBLE_WATCH_ITEM", "W second-order status mismatch")

    new_evidence_ids = {row.get("evidence_id") for row in payload.get("evidence", [])}
    require(new_evidence_ids == set(plan["new_evidence_ids"]), "W evidence IDs differ from plan")
    require(new_evidence_ids.isdisjoint({row.get("evidence_id") for row in evidence.get("evidence", [])}),
            "W would duplicate analytical evidence")
    require(review["analysis_id"] not in {row.get("analysis_id") for row in reviews.get("reviews", [])},
            "W would duplicate analytical review")

    target = next(row for row in canonical["records"] if row.get("occurrence_id") == review["canonical_occurrence_id"])
    require(review.get("canonical_series_id") == target.get("series_id"), "W review series does not match canonical")
    require(review.get("canonical_event_type") == target.get("event_type"), "W review event type does not match canonical")
    require(review.get("canonical_institution") == target.get("institution"), "W review institution does not match canonical")


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
    require(report.ok, "W post-state failed Analysis validation: " + "; ".join(report.errors))
    readiness = analysis_population_readiness(schema, new_reviews, canonical)
    require((new_reviews["version"], len(new_reviews["reviews"])) ==
            (post["analysis_reviews_version"], post["analysis_review_count"]), "W review post-state mismatch")
    require((new_evidence["version"], len(new_evidence["evidence"])) ==
            (post["analysis_evidence_version"], post["analysis_evidence_count"]), "W evidence post-state mismatch")
    require(readiness["eligible_completed_occurrence_count"] == post["eligible_completed_occurrence_count"], "W eligible count mismatch")
    require(readiness["reviewed_occurrence_count"] == post["reviewed_occurrence_count"], "W reviewed count mismatch")
    require(readiness["reviewed_event_type_diversity"] == post["reviewed_event_type_diversity"], "W diversity mismatch")
    require(readiness["broad_population_state"] == post["broad_population_state"], "W readiness state mismatch")

    remaining = sorted(
        row["occurrence_id"] for row in canonical["records"]
        if row.get("lifecycle_status") == "COMPLETED"
        and row["occurrence_id"] not in set(readiness["reviewed_occurrence_ids"])
    )
    require(remaining == sorted(post["remaining_eligible_unreviewed_occurrence_ids"]),
            f"W remaining eligible-unreviewed mismatch: {remaining}")

    projection = public_analysis_projection(schema, new_evidence, new_reviews, canonical)
    projected = next(row for row in projection["reviews"] if row["analysis_id"] == plan["new_analysis_id"])
    require(projected.get("what_moved") == [], "W public projection must preserve empty movement set")
    require(projected.get("what_surprised", {}).get("status") == "NOT_ESTABLISHED", "W public projection lost surprise state")
    require(projected.get("canonical", {}).get("event_type") == "TREATY_WORKING_GROUP_SESSION", "W public projection lost event type")

    return new_reviews, new_evidence, readiness, projection


def audit_text(plan: dict[str, Any], readiness: dict[str, Any], hashes: dict[str, str]) -> str:
    lines = [
        "# WORLD SIGNALS — Non-market institutional analysis W transaction audit v0.1", "",
        "**Transaction date:** 2026-09-06  ",
        "**Canonical checkpoint:** v0.30 / 681 — unchanged  ",
        "**Analysis post-state:** schema v0.3; reviews v0.6 / 10; evidence v0.6 / 32", "",
        "## Added reviewed specimen", "",
        "- `WSAN-BWC-WG8-2026-001` — BWC Working Group eighth session — `TREATY_WORKING_GROUP_SESSION`.",
        "- substantive draft progression is distinguished from adoption of the procedural report.",
        "- surprise is `NOT_ESTABLISHED`; soft completion guidance is not converted into a session-specific forecast.",
        "- `what_moved` is intentionally empty; no market proxy is manufactured.",
        "- connection is `LEGAL_OR_OPERATIONAL_DEPENDENCY` / `NOT_A_CAUSAL_CLAIM`.",
        "- later Working Group continuation is a `PLAUSIBLE_WATCH_ITEM`, not a completed outcome.", "",
        "## Schema decision", "",
        "- Analysis schema remains v0.3. Existing semantics already support this non-market institutional case.", "",
        "## Readiness", "",
        f"- eligible completed occurrences: {readiness['eligible_completed_occurrence_count']}",
        f"- reviewed occurrences: {readiness['reviewed_occurrence_count']}",
        f"- reviewed event-type diversity: {readiness['reviewed_event_type_diversity']}",
        f"- broad state: `{readiness['broad_population_state']}`", "",
        "## Remaining eligible unreviewed", "",
    ]
    lines.extend(f"- `{occurrence_id}`" for occurrence_id in plan["postconditions"]["remaining_eligible_unreviewed_occurrence_ids"])
    lines += ["", "## Protected SHA-256", ""]
    lines.extend(f"- {label}: `{digest}`" for label, digest in hashes.items())
    lines += ["", "Canonical/source/ledger/overlay/monitor and Analysis-schema files were hashed before and after W and must remain byte-identical.", ""]
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
    require(before == after, "W protected upstream/schema files changed during apply")
    print("APPLY_OK")


if __name__ == "__main__":
    main()
