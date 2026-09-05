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
PLAN_PATH = ROOT / "data/analysis/INSTITUTIONAL_ANALYSIS_W_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/analysis/INSTITUTIONAL_ANALYSIS_W_PAYLOAD_v0.1.json"
AUDIT_PATH = ROOT / "data/analysis/INSTITUTIONAL_ANALYSIS_W_TRANSACTION_AUDIT_v0.1.md"
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


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes() -> dict[str, str]:
    return {label: digest(path) for label, path in PROTECTED.items()}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def check_pre(plan, canonical, schema, reviews, evidence) -> None:
    pre = plan["pre_state"]
    require((canonical["version"], len(canonical["records"])) == (pre["canonical_registry_version"], pre["canonical_record_count"]), "canonical pre-state drift")
    require(schema["version"] == pre["analysis_schema_version"], "Analysis schema pre-state drift")
    require((reviews["version"], len(reviews["reviews"])) == (pre["analysis_reviews_version"], pre["analysis_review_count"]), "review pre-state drift")
    require((evidence["version"], len(evidence["evidence"])) == (pre["analysis_evidence_version"], pre["analysis_evidence_count"]), "evidence pre-state drift")
    require(reviews["canonical_checkpoint"] == pre["analysis_canonical_checkpoint"], "Analysis canonical checkpoint drift")
    readiness = analysis_population_readiness(schema, reviews, canonical)
    for key in ("eligible_completed_occurrence_count", "reviewed_occurrence_count", "reviewed_event_type_diversity", "broad_population_state"):
        require(readiness[key] == pre[key], f"pre-state readiness drift: {key}")


def check_payload(plan, payload, canonical, reviews, evidence) -> None:
    require(payload.get("tranche") == "INSTITUTIONAL_ANALYSIS_W", "wrong W payload")
    review_ids = {row["analysis_id"] for row in payload["reviews"]}
    evidence_ids = {row["evidence_id"] for row in payload["evidence"]}
    require(review_ids == set(plan["new_analysis_ids"]), "W analysis IDs differ from plan")
    require(evidence_ids == set(plan["new_evidence_ids"]), "W evidence IDs differ from plan")
    require(len(review_ids) == 2 and len(evidence_ids) == 5, "W payload cardinality changed")
    require(review_ids.isdisjoint({row["analysis_id"] for row in reviews["reviews"]}), "duplicate W analysis ID")
    require(evidence_ids.isdisjoint({row["evidence_id"] for row in evidence["evidence"]}), "duplicate W evidence ID")
    require({row["canonical_occurrence_id"] for row in payload["reviews"]} == set(plan["admit_occurrence_ids"]), "W admitted occurrence set changed")

    by_occ = {row["occurrence_id"]: row for row in canonical["records"]}
    bwc = by_occ["WSO-BWC-WG-2026-S08"]
    require((bwc["series_id"], bwc["event_type"], bwc["category"], bwc["lifecycle_status"]) == ("WSER-INT-BWC-WG-STRENGTHENING", "TREATY_WORKING_GROUP_SESSION", "INTERNATIONAL_INSTITUTIONS", "COMPLETED"), "BWC anchor changed")
    require((bwc.get("start_local"), bwc.get("end_local"), bwc.get("time_precision"), bwc.get("start_utc")) == ("2026-02-09", "2026-02-13", "DAY_RANGE", None), "BWC timing changed")

    woah = by_occ["WSO-WOAH-GS-093"]
    require((woah["series_id"], woah["event_type"], woah["category"], woah["lifecycle_status"]) == ("WSER-AGF-WOAH-GENERAL-SESSION", "GOVERNANCE_ASSEMBLY_SESSION", "AGRICULTURE_FOOD", "COMPLETED"), "WOAH anchor/category changed")
    require((woah.get("start_local"), woah.get("end_local"), woah.get("time_precision"), woah.get("start_utc")) == ("2026-05-18", "2026-05-22", "DAY_RANGE", None), "WOAH timing changed")

    boc = by_occ["WSO-ddb70f8ff05a58fb"]
    require((boc["event_type"], boc["lifecycle_status"]) == ("DECISION", "COMPLETED"), "BoC hold anchor changed")
    require(plan["hold_occurrence_ids"] == [boc["occurrence_id"]], "W hold set changed")

    by_analysis = {row["analysis_id"]: row for row in payload["reviews"]}
    b = by_analysis["WSAN-BWC-WG8-20260213-001"]
    require(b["what_surprised"]["status"] == "NOT_ESTABLISHED", "BWC surprise drift")
    require(b["what_moved"] == [], "BWC market move invented")
    require((b["what_appears_connected"]["interaction_type"], b["what_appears_connected"]["causal_status"], b["what_appears_connected"]["confidence"]) == ("STRUCTURAL_DEPENDENCY", "NOT_A_CAUSAL_CLAIM", "HIGH"), "BWC connection grade drift")
    require(b["second_order_effects"]["status"] == "NOT_ESTABLISHED", "BWC second-order drift")

    w = by_analysis["WSAN-WOAH-GS93-20260522-001"]
    require(w["what_surprised"]["status"] == "NO_CLEAR_SURPRISE", "WOAH surprise drift")
    require(w["what_moved"] == [], "WOAH market move invented")
    require((w["what_appears_connected"]["interaction_type"], w["what_appears_connected"]["causal_status"], w["what_appears_connected"]["confidence"]) == ("STRUCTURAL_DEPENDENCY", "NOT_A_CAUSAL_CLAIM", "HIGH"), "WOAH connection grade drift")
    require(w["second_order_effects"]["status"] == "PLAUSIBLE_WATCH_ITEM", "WOAH implementation status drift")


def transform(plan, payload, canonical, schema, reviews, evidence):
    check_pre(plan, canonical, schema, reviews, evidence)
    check_payload(plan, payload, canonical, reviews, evidence)
    post = plan["post_state"]
    new_reviews = copy.deepcopy(reviews)
    new_evidence = copy.deepcopy(evidence)
    new_reviews["version"] = post["analysis_reviews_version"]
    new_evidence["version"] = post["analysis_evidence_version"]
    new_reviews["reference_date"] = plan["reference_date"]
    new_evidence["reference_date"] = plan["reference_date"]
    new_reviews["canonical_checkpoint"] = copy.deepcopy(post["analysis_canonical_checkpoint"])
    new_reviews["reviews"].extend(copy.deepcopy(payload["reviews"]))
    new_evidence["evidence"].extend(copy.deepcopy(payload["evidence"]))
    report = validate_analysis(schema, new_evidence, new_reviews, canonical)
    require(report.ok, "W Analysis validation failed: " + "; ".join(report.errors))
    readiness = analysis_population_readiness(schema, new_reviews, canonical)
    require((new_reviews["version"], len(new_reviews["reviews"])) == (post["analysis_reviews_version"], post["analysis_review_count"]), "W review post-state mismatch")
    require((new_evidence["version"], len(new_evidence["evidence"])) == (post["analysis_evidence_version"], post["analysis_evidence_count"]), "W evidence post-state mismatch")
    for key in ("eligible_completed_occurrence_count", "reviewed_occurrence_count", "reviewed_event_type_diversity", "broad_population_state"):
        require(readiness[key] == post[key], f"W post-state readiness mismatch: {key}")
    reviewed = set(readiness["reviewed_occurrence_ids"])
    remaining = sorted(row["occurrence_id"] for row in canonical["records"] if row.get("lifecycle_status") == "COMPLETED" and row["occurrence_id"] not in reviewed)
    require(remaining == sorted(post["remaining_eligible_unreviewed_occurrence_ids"]), f"W remaining set mismatch: {remaining}")
    return new_reviews, new_evidence, readiness


def audit(plan, readiness, protected_hashes) -> str:
    lines = [
        "# WORLD SIGNALS — Institutional Analysis W transaction audit v0.1",
        "",
        "**Transaction date:** 2026-09-06  ",
        "**Canonical checkpoint:** v0.30 / 681 — unchanged  ",
        "**Analysis post-state:** schema v0.3; reviews v0.6 / 11; evidence v0.6 / 33; canonical checkpoint v0.30 / 681",
        "",
        "## Added reviewed specimens",
        "",
        "- `WSAN-BWC-WG8-20260213-001` — treaty-governance process; procedural consensus and revised negotiating text remain distinct from final substantive agreement; no market move; downstream effect not established.",
        "- `WSAN-WOAH-GS93-20260522-001` — animal-health standards governance; 35 resolutions and 51 standards are realised facts rather than synthetic directional surprise; primary canonical category remains AGRICULTURE_FOOD; 2027–2031 implementation remains a plausible watch item.",
        "",
        "Both W specimens retain `what_moved: []`. High institutional importance is not conditioned on a clean asset-price response.",
        "",
        "## Deliberate hold",
        "",
        "- `WSO-ddb70f8ff05a58fb` — Bank of Canada 2 September decision remains the sole eligible completed occurrence not reviewed. W optimises analytical contract diversity, not backlog completion.",
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
    lines.extend(f"- {label}: `{value}`" for label, value in protected_hashes.items())
    lines += [
        "",
        "All protected upstream files must remain byte-identical through this Analysis-only transaction.",
        "",
        "## Write gates",
        "",
        "- automatic canonical commit: **OFF**",
        "- Google Calendar write: **OFF**",
        "- canonical/source/monitor/ledger/overlay/schema mutation from W: **PROHIBITED**",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fail-closed Institutional Analysis W transaction")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    plan = load(PLAN_PATH)
    payload = load(PAYLOAD_PATH)
    canonical = load(CANONICAL_PATH)
    schema = load(ANALYSIS_SCHEMA_PATH)
    reviews = load(REVIEWS_PATH)
    evidence = load(EVIDENCE_PATH)
    before = hashes()
    new_reviews, new_evidence, readiness = transform(plan, payload, canonical, schema, reviews, evidence)
    mode = "CHECK_ONLY"
    if args.apply:
        require(os.environ.get(APPLY_ENV) == "YES", f"--apply requires {APPLY_ENV}=YES")
        write(REVIEWS_PATH, new_reviews)
        write(EVIDENCE_PATH, new_evidence)
        require(before == hashes(), "protected upstream file changed during W")
        AUDIT_PATH.write_text(audit(plan, readiness, before), encoding="utf-8")
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
            "analysis_canonical_checkpoint": new_reviews["canonical_checkpoint"],
            "eligible_completed_occurrence_count": readiness["eligible_completed_occurrence_count"],
            "reviewed_occurrence_count": readiness["reviewed_occurrence_count"],
            "reviewed_event_type_diversity": readiness["reviewed_event_type_diversity"],
            "broad_population_state": readiness["broad_population_state"],
        },
        "remaining_eligible_unreviewed": plan["post_state"]["remaining_eligible_unreviewed_occurrence_ids"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
