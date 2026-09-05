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
PLAN_PATH = ROOT / "data/analysis/CROSS_DOMAIN_ANALYSIS_V_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/analysis/CROSS_DOMAIN_ANALYSIS_V_PAYLOAD_v0.1.json"
AUDIT_PATH = ROOT / "data/analysis/CROSS_DOMAIN_ANALYSIS_V_TRANSACTION_AUDIT_v0.1.md"
APPLY_ENV = "WORLD_SIGNALS_APPLY_ANALYSIS_V"

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
    require(
        (canonical.get("version"), len(canonical.get("records", [])))
        == (pre["canonical_registry_version"], pre["canonical_record_count"]),
        "canonical checkpoint is not the frozen V pre-state",
    )
    require(schema.get("version") == pre["analysis_schema_version"], "Analysis schema changed; V must be re-reviewed")
    require(
        (reviews.get("version"), len(reviews.get("reviews", [])))
        == (pre["analysis_reviews_version"], pre["analysis_review_count"]),
        "Analysis review registry is not the frozen V pre-state",
    )
    require(
        (evidence.get("version"), len(evidence.get("evidence", [])))
        == (pre["analysis_evidence_version"], pre["analysis_evidence_count"]),
        "Analysis evidence registry is not the frozen V pre-state",
    )
    require(
        reviews.get("canonical_checkpoint") == pre["analysis_canonical_checkpoint"],
        "Analysis canonical checkpoint is not the frozen V pre-state",
    )
    readiness = analysis_population_readiness(schema, reviews, canonical)
    require(
        readiness["eligible_completed_occurrence_count"] == pre["eligible_completed_occurrence_count"],
        "eligible completed count drifted before V",
    )
    require(
        readiness["reviewed_occurrence_count"] == pre["reviewed_occurrence_count"],
        "reviewed occurrence count drifted before V",
    )
    require(
        readiness["reviewed_event_type_diversity"] == pre["reviewed_event_type_diversity"],
        "reviewed event-type diversity drifted before V",
    )
    require(readiness["broad_population_state"] == pre["broad_population_state"], "broad population state drifted before V")


def assert_payload_contract(
    plan: dict[str, Any],
    payload: dict[str, Any],
    canonical: dict[str, Any],
    reviews: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    require(payload.get("tranche") == "CROSS_DOMAIN_ANALYSIS_V", "wrong V payload")
    new_analysis_ids = {row.get("analysis_id") for row in payload.get("reviews", [])}
    new_evidence_ids = {row.get("evidence_id") for row in payload.get("evidence", [])}
    require(new_analysis_ids == set(plan["new_analysis_ids"]), "V analysis IDs do not match frozen plan")
    require(new_evidence_ids == set(plan["new_evidence_ids"]), "V evidence IDs do not match frozen plan")
    require(len(new_analysis_ids) == 3, "V must contain exactly three new reviews")
    require(len(new_evidence_ids) == 8, "V must contain exactly eight new evidence records")

    existing_analysis = {row.get("analysis_id") for row in reviews.get("reviews", [])}
    existing_evidence = {row.get("evidence_id") for row in evidence.get("evidence", [])}
    require(new_analysis_ids.isdisjoint(existing_analysis), "V would duplicate an analysis_id")
    require(new_evidence_ids.isdisjoint(existing_evidence), "V would duplicate an evidence_id")
    require(
        set(plan["admit_occurrence_ids"])
        == {row["canonical_occurrence_id"] for row in payload["reviews"]},
        "V admitted occurrence set differs from frozen plan",
    )

    canonical_by_id = {row["occurrence_id"]: row for row in canonical["records"]}

    bwc = canonical_by_id["WSO-BWC-WG-2026-S08"]
    require(
        (bwc.get("series_id"), bwc.get("event_type"), bwc.get("category"), bwc.get("lifecycle_status"))
        == ("WSER-INT-BWC-WG-STRENGTHENING", "TREATY_WORKING_GROUP_SESSION", "INTERNATIONAL_INSTITUTIONS", "COMPLETED"),
        "BWC canonical anchor changed",
    )
    require(
        (bwc.get("start_local"), bwc.get("end_local"), bwc.get("start_utc"), bwc.get("time_precision"))
        == ("2026-02-09", "2026-02-13", None, "DAY_RANGE"),
        "BWC day-range timing changed",
    )

    woah = canonical_by_id["WSO-WOAH-GS-093"]
    require(
        (woah.get("series_id"), woah.get("event_type"), woah.get("category"), woah.get("lifecycle_status"))
        == ("WSER-AGF-WOAH-GENERAL-SESSION", "GOVERNANCE_ASSEMBLY_SESSION", "AGRICULTURE_FOOD", "COMPLETED"),
        "WOAH canonical anchor or primary category changed",
    )
    require(
        (woah.get("start_local"), woah.get("end_local"), woah.get("start_utc"), woah.get("time_precision"))
        == ("2026-05-18", "2026-05-22", None, "DAY_RANGE"),
        "WOAH day-range timing changed",
    )

    nepal = canonical_by_id["WSO-FIS-NP-BUDGET-2083"]
    require(
        (nepal.get("series_id"), nepal.get("event_type"), nepal.get("lifecycle_status"))
        == ("WSER-FIS-NP-FEDERAL-BUDGET", "FISCAL_POLICY_PROCESS", "COMPLETED"),
        "Nepal budget canonical anchor changed",
    )
    require(nepal.get("timing_type") == "SOURCE_NATIVE_CALENDAR_DATE", "Nepal must remain source-native dated")
    require(
        (
            nepal.get("source_native_date_label"),
            nepal.get("native_calendar_system"),
            nepal.get("native_calendar_year"),
            nepal.get("native_calendar_month"),
            nepal.get("native_calendar_day"),
        )
        == ("15 Jestha 2083", "BIKRAM_SAMBAT_NEPAL", 2083, "JESTHA", 15),
        "Nepal source-native date changed",
    )
    require(nepal.get("gregorian_resolution_status") == "UNRESOLVED_AUTHORITATIVE_CONVERSION", "Nepal Gregorian resolution status changed")
    require(nepal.get("start_local") is None and nepal.get("start_utc") is None, "Nepal must not gain synthetic Gregorian/local timing")
    require(nepal.get("publication_time_semantics") == "SOURCE_NATIVE_DATE_ONLY", "Nepal publication-time semantics changed")

    boc = canonical_by_id["WSO-ddb70f8ff05a58fb"]
    require((boc.get("event_type"), boc.get("lifecycle_status")) == ("DECISION", "COMPLETED"), "BoC hold anchor changed")
    require(plan["hold_occurrence_ids"] == [boc["occurrence_id"]], "V hold set changed")

    by_analysis = {row["analysis_id"]: row for row in payload["reviews"]}
    bwc_review = by_analysis["WSAN-BWC-WG8-20260213-001"]
    require(bwc_review["what_surprised"]["status"] == "NOT_ESTABLISHED", "BWC surprise must remain NOT_ESTABLISHED")
    require(bwc_review["what_moved"] == [], "BWC must not manufacture a market reaction")
    require(bwc_review["what_appears_connected"]["causal_status"] == "NOT_A_CAUSAL_CLAIM", "BWC must not become a causal claim")
    require(bwc_review["second_order_effects"]["status"] == "NOT_ESTABLISHED", "BWC second-order status drifted")

    woah_review = by_analysis["WSAN-WOAH-GS93-20260522-001"]
    require(woah_review["what_surprised"]["status"] == "NO_CLEAR_SURPRISE", "WOAH surprise must remain NO_CLEAR_SURPRISE")
    require(woah_review["what_moved"] == [], "WOAH must not manufacture a market reaction")
    require(woah_review["second_order_effects"]["status"] == "PLAUSIBLE_WATCH_ITEM", "WOAH implementation must remain prospective")

    nepal_review = by_analysis["WSAN-NP-BUDGET-2083-001"]
    require(nepal_review["canonical_release_utc"] is None, "Nepal review must preserve null canonical UTC")
    require(nepal_review["what_surprised"]["status"] == "NO_CLEAR_SURPRISE", "Nepal timing must remain NO_CLEAR_SURPRISE")
    require(nepal_review["what_moved"] == [], "Nepal must not manufacture a market reaction")
    require(nepal_review["what_appears_connected"]["interaction_type"] == "LEGAL_OR_OPERATIONAL_DEPENDENCY", "Nepal legal dependency classification drifted")
    require(nepal_review["second_order_effects"]["status"] == "OBSERVED", "Nepal later fiscal-cycle observation must remain OBSERVED")

    for review in payload["reviews"]:
        require(review["what_moved"] == [], "all V specimens must preserve null market-movement results")
        require(review["canonical_mutation_prohibited"] is True, "V review must explicitly prohibit canonical mutation")
        require(review["google_calendar_write"] is False, "V review must keep Google Calendar write false")


def transform(
    plan: dict[str, Any],
    payload: dict[str, Any],
    canonical: dict[str, Any],
    schema: dict[str, Any],
    reviews: dict[str, Any],
    evidence: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    assert_exact_pre_state(plan, canonical, schema, reviews, evidence)
    assert_payload_contract(plan, payload, canonical, reviews, evidence)

    new_reviews = copy.deepcopy(reviews)
    new_evidence = copy.deepcopy(evidence)
    post = plan["post_state"]
    new_reviews["version"] = post["analysis_reviews_version"]
    new_evidence["version"] = post["analysis_evidence_version"]
    new_reviews["reference_date"] = plan["reference_date"]
    new_evidence["reference_date"] = plan["reference_date"]
    new_reviews["canonical_checkpoint"] = copy.deepcopy(post["analysis_canonical_checkpoint"])
    new_reviews["reviews"].extend(copy.deepcopy(payload["reviews"]))
    new_evidence["evidence"].extend(copy.deepcopy(payload["evidence"]))

    report = validate_analysis(schema, new_evidence, new_reviews, canonical)
    require(report.ok, "V post-state failed Analysis validation: " + "; ".join(report.errors))
    readiness = analysis_population_readiness(schema, new_reviews, canonical)
    require(len(new_reviews["reviews"]) == post["analysis_review_count"], "V review count mismatch")
    require(len(new_evidence["evidence"]) == post["analysis_evidence_count"], "V evidence count mismatch")
    require(new_reviews["canonical_checkpoint"] == post["analysis_canonical_checkpoint"], "V Analysis canonical checkpoint mismatch")
    require(readiness["eligible_completed_occurrence_count"] == post["eligible_completed_occurrence_count"], "V eligible count mismatch")
    require(readiness["reviewed_occurrence_count"] == post["reviewed_occurrence_count"], "V reviewed count mismatch")
    require(readiness["reviewed_event_type_diversity"] == post["reviewed_event_type_diversity"], "V event-type diversity mismatch")
    require(readiness["broad_population_state"] == post["broad_population_state"], "V readiness state mismatch")
    reviewed_ids = set(readiness["reviewed_occurrence_ids"])
    remaining = sorted(
        row["occurrence_id"]
        for row in canonical["records"]
        if row.get("lifecycle_status") == "COMPLETED" and row["occurrence_id"] not in reviewed_ids
    )
    require(remaining == sorted(post["remaining_eligible_unreviewed_occurrence_ids"]), f"V remaining eligible-unreviewed set mismatch: {remaining}")
    return new_reviews, new_evidence, readiness


def audit_text(plan: dict[str, Any], readiness: dict[str, Any], hashes: dict[str, str]) -> str:
    lines = [
        "# WORLD SIGNALS — Cross-domain Analysis V transaction audit v0.1",
        "",
        "**Transaction date:** 2026-09-06  ",
        "**Canonical checkpoint:** v0.30 / 681 — unchanged  ",
        "**Analysis post-state:** reviews v0.5 / 11; evidence v0.5 / 29; canonical checkpoint v0.30 / 681",
        "",
        "## Added reviewed specimens",
        "",
        "- `WSAN-BWC-WG8-20260213-001` — treaty-governance process; revised negotiating text is not promoted into final substantive consensus; no market move; second-order outcome not established.",
        "- `WSAN-WOAH-GS93-20260522-001` — animal-health standards governance; primary canonical category remains AGRICULTURE_FOOD; implementation from 2027 remains a plausible watch item rather than an observed effect.",
        "- `WSAN-NP-BUDGET-2083-001` — source-native fiscal process; `15 Jestha 2083` remains unconverted; no CMS clock becomes event time; later Appropriation Act listing is an observed fiscal-cycle development without causal shortcut.",
        "",
        "All three V specimens retain `what_moved: []`. Institutional importance is not conditioned on a clean asset-price response.",
        "",
        "## Deliberate hold",
        "",
        "- `WSO-ddb70f8ff05a58fb` — Bank of Canada 2 September decision remains the sole eligible completed occurrence not reviewed. V optimises contract pressure, not backlog completion.",
        "",
        "## Readiness",
        "",
        f"- eligible completed occurrences: {readiness['eligible_completed_occurrence_count']}",
        f"- reviewed occurrences: {readiness['reviewed_occurrence_count']}",
        f"- reviewed event-type diversity: {readiness['reviewed_event_type_diversity']}",
        f"- broad state: `{readiness['broad_population_state']}`",
        "",
        "## Projection boundary",
        "",
        "The public Analysis projection is permitted to expose canonical temporal semantics already present upstream, including source-native calendar labels and multi-day ranges. It must not derive, convert or mutate canonical timing. Nepal therefore remains source-native with unresolved authoritative Gregorian conversion.",
        "",
        "## Protected upstream SHA-256",
        "",
    ]
    lines.extend(f"- {label}: `{digest}`" for label, digest in hashes.items())
    lines += [
        "",
        "All protected upstream files were hashed before and after the Analysis transaction and must remain byte-identical.",
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
    parser = argparse.ArgumentParser(description="Fail-closed Cross-domain Analysis V transaction")
    parser.add_argument("--apply", action="store_true", help="write reviewed V Analysis post-state")
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
        require(os.environ.get(APPLY_ENV) == "YES", f"--apply requires {APPLY_ENV}=YES")
        write(REVIEWS_PATH, new_reviews)
        write(EVIDENCE_PATH, new_evidence)
        after_hashes = protected_hashes()
        require(before_hashes == after_hashes, "protected upstream file changed during V transaction")
        AUDIT_PATH.write_text(audit_text(plan, readiness, before_hashes), encoding="utf-8")
        mode = "APPLY"

    print(
        json.dumps(
            {
                "mode": mode,
                "post": {
                    "canonical_version": canonical["version"],
                    "canonical_count": len(canonical["records"]),
                    "analysis_reviews_version": new_reviews["version"],
                    "analysis_review_count": len(new_reviews["reviews"]),
                    "analysis_evidence_version": new_evidence["version"],
                    "analysis_evidence_count": len(new_evidence["evidence"]),
                    "analysis_canonical_checkpoint": new_reviews["canonical_checkpoint"],
                    "eligible_completed_occurrence_count": readiness["eligible_completed_occurrence_count"],
                    "reviewed_occurrence_count": readiness["reviewed_occurrence_count"],
                    "reviewed_event_type_diversity": readiness["reviewed_event_type_diversity"],
                    "broad_population_state": readiness["broad_population_state"],
                },
                "remaining_eligible_unreviewed": plan["post_state"]["remaining_eligible_unreviewed_occurrence_ids"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
