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
PLAN_PATH = ROOT / "data/analysis/CONTROLLED_ANALYSIS_EXPANSION_T_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/analysis/CONTROLLED_ANALYSIS_EXPANSION_T_PAYLOAD_v0.1.json"
AUDIT_PATH = ROOT / "data/analysis/CONTROLLED_ANALYSIS_EXPANSION_T_TRANSACTION_AUDIT_v0.1.md"

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


def assert_exact_pre_state(
    plan: dict[str, Any],
    canonical: dict[str, Any],
    schema: dict[str, Any],
    reviews: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    pre = plan["pre_state"]
    require((canonical.get("version"), len(canonical.get("records", []))) ==
            (pre["canonical_registry_version"], pre["canonical_record_count"]),
            "canonical checkpoint is not the frozen T pre-state")
    require(schema.get("version") == "0.2", "Analysis schema version changed; T must be re-reviewed")
    require((reviews.get("version"), len(reviews.get("reviews", []))) ==
            (pre["analysis_reviews_version"], pre["analysis_review_count"]),
            "Analysis review registry is not the frozen T pre-state")
    require((evidence.get("version"), len(evidence.get("evidence", []))) ==
            (pre["analysis_evidence_version"], pre["analysis_evidence_count"]),
            "Analysis evidence registry is not the frozen T pre-state")
    require(reviews.get("canonical_checkpoint") == {
        "registry_version": pre["canonical_registry_version"],
        "record_count": pre["canonical_record_count"],
    }, "Analysis canonical checkpoint is not aligned to T base")
    readiness = analysis_population_readiness(schema, reviews, canonical)
    require(readiness["eligible_completed_occurrence_count"] == pre["eligible_completed_occurrence_count"],
            "eligible completed count drifted before T")
    require(readiness["reviewed_occurrence_count"] == pre["reviewed_occurrence_count"],
            "reviewed occurrence count drifted before T")
    require(readiness["reviewed_event_type_diversity"] == pre["reviewed_event_type_diversity"],
            "reviewed event-type diversity drifted before T")
    require(readiness["broad_population_state"] == pre["broad_population_state"],
            "broad population state drifted before T")


def assert_payload_contract(
    plan: dict[str, Any], payload: dict[str, Any], canonical: dict[str, Any],
    reviews: dict[str, Any], evidence: dict[str, Any]
) -> None:
    require(payload.get("tranche") == "CONTROLLED_ANALYSIS_EXPANSION_T", "wrong T payload")
    new_analysis_ids = {row.get("analysis_id") for row in payload.get("reviews", [])}
    new_evidence_ids = {row.get("evidence_id") for row in payload.get("evidence", [])}
    require(new_analysis_ids == set(plan["new_analysis_ids"]), "T analysis IDs do not match frozen plan")
    require(new_evidence_ids == set(plan["new_evidence_ids"]), "T evidence IDs do not match frozen plan")
    existing_analysis = {row.get("analysis_id") for row in reviews.get("reviews", [])}
    existing_evidence = {row.get("evidence_id") for row in evidence.get("evidence", [])}
    require(new_analysis_ids.isdisjoint(existing_analysis), "T would duplicate an analysis_id")
    require(new_evidence_ids.isdisjoint(existing_evidence), "T would duplicate an evidence_id")

    canonical_by_id = {row["occurrence_id"]: row for row in canonical["records"]}
    require(set(plan["admit_occurrence_ids"]) == {row["canonical_occurrence_id"] for row in payload["reviews"]},
            "T admitted occurrence set differs from frozen plan")

    eia = canonical_by_id["WSO-COM-A-0013"]
    require((eia.get("series_id"), eia.get("event_type"), eia.get("lifecycle_status")) ==
            ("WSER-COM-EIA-WPSR", "INFORMATION_RELEASE", "COMPLETED"),
            "EIA canonical anchor changed")
    require((eia.get("start_local"), eia.get("start_utc"), eia.get("source_timezone")) ==
            ("2026-09-02T10:30:00", "2026-09-02T14:30:00Z", "America/New_York"),
            "EIA canonical timing changed")

    chips = canonical_by_id["WSO-TECH-A-0002"]
    require((chips.get("series_id"), chips.get("event_type"), chips.get("lifecycle_status")) ==
            ("WSER-TECH-EU-CHIPS", "TECHNOLOGY_POLICY_MILESTONE", "COMPLETED"),
            "EU Chips canonical anchor changed")
    require(chips.get("start_local") == "2026-09-20", "EU Chips legal deadline changed")
    require(chips.get("start_utc") is None, "EU Chips deadline must not gain synthetic UTC time")
    require(chips.get("completion_verified_by_date") == "2026-06-03", "EU Chips completion evidence changed")
    require(chips.get("deadline_completion_relation") == "COMPLETED_BEFORE_DEADLINE",
            "EU Chips deadline/completion relation changed")
    require(chips.get("deadline_is_actual_publication_time") is False,
            "EU Chips legal deadline must remain distinct from publication time")

    by_analysis = {row["analysis_id"]: row for row in payload["reviews"]}
    eia_review = by_analysis["WSAN-EIA-WPSR-20260902-001"]
    require(eia_review["what_surprised"]["status"] == "MIXED", "EIA surprise must remain MIXED")
    for movement in eia_review["what_moved"]:
        require(movement["movement_representation"] == "CHANGE_AND_ENDPOINT", "EIA movement representation drifted")
        require(movement.get("before_value") is None, "EIA source-reported movements must not synthesize pre-values")
        require(movement.get("independently_reconstructed") is False, "EIA movement must remain source-reported")
    require(eia_review["what_appears_connected"]["confidence"] == "LOW", "EIA connection must remain LOW confidence")

    chips_review = by_analysis["WSAN-EU-CHIPS-EVAL-20260603-001"]
    require(chips_review["canonical_release_utc"] is None, "EU Chips review must preserve null canonical UTC")
    require(chips_review["what_surprised"]["status"] == "MIXED", "EU Chips timing comparison must remain MIXED")
    require(chips_review["what_moved"] == [], "EU Chips review must not manufacture a market reaction")
    require(chips_review["what_appears_connected"]["causal_status"] == "NOT_A_CAUSAL_CLAIM",
            "EU Chips documentary link must not become a causal claim")


def transform(
    plan: dict[str, Any], payload: dict[str, Any], canonical: dict[str, Any],
    schema: dict[str, Any], reviews: dict[str, Any], evidence: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    assert_exact_pre_state(plan, canonical, schema, reviews, evidence)
    assert_payload_contract(plan, payload, canonical, reviews, evidence)

    new_reviews = copy.deepcopy(reviews)
    new_evidence = copy.deepcopy(evidence)
    new_reviews["version"] = plan["post_state"]["analysis_reviews_version"]
    new_evidence["version"] = plan["post_state"]["analysis_evidence_version"]
    new_reviews["reference_date"] = plan["reference_date"]
    new_evidence["reference_date"] = plan["reference_date"]
    new_reviews["reviews"].extend(copy.deepcopy(payload["reviews"]))
    new_evidence["evidence"].extend(copy.deepcopy(payload["evidence"]))

    report = validate_analysis(schema, new_evidence, new_reviews, canonical)
    require(report.ok, "T post-state failed Analysis validation: " + "; ".join(report.errors))
    readiness = analysis_population_readiness(schema, new_reviews, canonical)
    post = plan["post_state"]
    require(len(new_reviews["reviews"]) == post["analysis_review_count"], "T review count mismatch")
    require(len(new_evidence["evidence"]) == post["analysis_evidence_count"], "T evidence count mismatch")
    require(readiness["eligible_completed_occurrence_count"] == post["eligible_completed_occurrence_count"],
            "T eligible count mismatch")
    require(readiness["reviewed_occurrence_count"] == post["reviewed_occurrence_count"],
            "T reviewed count mismatch")
    require(readiness["reviewed_event_type_diversity"] == post["reviewed_event_type_diversity"],
            "T event-type diversity mismatch")
    require(readiness["broad_population_state"] == post["broad_population_state"],
            "T readiness state mismatch")
    remaining = sorted(
        row["occurrence_id"] for row in canonical["records"]
        if row.get("lifecycle_status") == "COMPLETED"
        and row["occurrence_id"] not in set(readiness["reviewed_occurrence_ids"])
    )
    require(remaining == sorted(post["remaining_eligible_unreviewed_occurrence_ids"]),
            f"T remaining eligible-unreviewed set mismatch: {remaining}")
    return new_reviews, new_evidence, readiness


def audit_text(plan: dict[str, Any], readiness: dict[str, Any], hashes: dict[str, str]) -> str:
    lines = [
        "# WORLD SIGNALS — Controlled Analysis Expansion T transaction audit v0.1",
        "",
        "**Transaction date:** 2026-09-06  ",
        "**Canonical checkpoint:** v0.29 / 678 — unchanged  ",
        "**Analysis post-state:** reviews v0.4 / 8; evidence v0.4 / 21",
        "",
        "## Added reviewed specimens",
        "",
        "- `WSAN-EIA-WPSR-20260902-001` — energy/commodities information release — MIXED inventory surprise — LOW-confidence oil-price association under severe geopolitical contamination.",
        "- `WSAN-EU-CHIPS-EVAL-20260603-001` — technology/industrial policy — legal deadline and indicative planning window kept distinct — no market move required or promoted.",
        "",
        "## Deliberate hold",
        "",
        "- `WSO-ddb70f8ff05a58fb` — Bank of Canada 2 September decision remains eligible but unreviewed. T optimises contract/domain diversity, not completion percentage.",
        "",
        "## Readiness",
        "",
        f"- eligible completed occurrences: {readiness['eligible_completed_occurrence_count']}",
        f"- reviewed occurrences: {readiness['reviewed_occurrence_count']}",
        f"- reviewed event-type diversity: {readiness['reviewed_event_type_diversity']}",
        f"- broad state: `{readiness['broad_population_state']}`",
        "",
        "## Protected upstream SHA-256",
        "",
    ]
    lines.extend(f"- {label}: `{digest}`" for label, digest in hashes.items())
    lines += [
        "",
        "All protected upstream files were hashed before and after the transaction and must remain byte-identical.",
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
    parser = argparse.ArgumentParser(description="Fail-closed controlled Analysis Expansion T transaction")
    parser.add_argument("--apply", action="store_true", help="write reviewed T Analysis post-state")
    args = parser.parse_args()

    plan = load(PLAN_PATH)
    payload = load(PAYLOAD_PATH)
    canonical = load(CANONICAL_PATH)
    schema = load(ANALYSIS_SCHEMA_PATH)
    reviews = load(REVIEWS_PATH)
    evidence = load(EVIDENCE_PATH)
    before_hashes = protected_hashes()

    new_reviews, new_evidence, readiness = transform(plan, payload, canonical, schema, reviews, evidence)

    mode = "CHECK_ONLY"
    if args.apply:
        require(os.environ.get("WORLD_SIGNALS_APPLY_ANALYSIS_T") == "YES",
                "--apply requires WORLD_SIGNALS_APPLY_ANALYSIS_T=YES")
        write(REVIEWS_PATH, new_reviews)
        write(EVIDENCE_PATH, new_evidence)
        after_hashes = protected_hashes()
        require(before_hashes == after_hashes, "protected upstream file changed during T transaction")
        AUDIT_PATH.write_text(audit_text(plan, readiness, before_hashes), encoding="utf-8")
        mode = "APPLY"

    print(json.dumps({
        "mode": mode,
        "post": {
            "canonical_version": canonical["version"],
            "canonical_count": len(canonical["records"]),
            "analysis_reviews_version": new_reviews["version"],
            "analysis_review_count": len(new_reviews["reviews"]),
            "analysis_evidence_version": new_evidence["version"],
            "analysis_evidence_count": len(new_evidence["evidence"]),
            "eligible_completed_occurrence_count": readiness["eligible_completed_occurrence_count"],
            "reviewed_occurrence_count": readiness["reviewed_occurrence_count"],
            "reviewed_event_type_diversity": readiness["reviewed_event_type_diversity"],
            "broad_population_state": readiness["broad_population_state"],
        },
        "remaining_eligible_unreviewed": plan["post_state"]["remaining_eligible_unreviewed_occurrence_ids"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
