#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.audit_analysis_sample_y import audit as base_audit

BASE_MAIN_SHA = "53e98457b70aa0dda4da490d5fe3210ce333ecae"
REFERENCE_DATE = "2026-09-06"


def load(path: str) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def version_tuple(raw: str) -> tuple[int, ...]:
    return tuple(int(part) for part in str(raw).split("."))


def build_report() -> dict[str, Any]:
    report = base_audit()
    sources = load("data/sources/registry.json")
    ledger = load("data/changes/ledger.json")
    overlay = load("data/coverage/biosecurity_overlay.json")
    schema = load("data/analysis/schema.json")
    validator_text = (ROOT / "src/world_signals/analysis.py").read_text(encoding="utf-8")

    report["audit"] = "POST_AJ_PRESSURE_AUDIT_AK_PREFLIGHT"
    report["version"] = "0.1"
    report["reference_date"] = REFERENCE_DATE
    report["base_main_sha"] = BASE_MAIN_SHA

    checkpoint = report["checkpoint"]
    checkpoint.update({
        "source_registry_version": sources.get("version"),
        "source_count": len(sources.get("sources", [])),
        "change_ledger_version": ledger.get("version"),
        "change_count": len(ledger.get("changes", [])),
        "biosecurity_overlay_version": overlay.get("version"),
        "biosecurity_overlay_canonical_checkpoint": overlay.get("canonical_checkpoint"),
    })

    exact_label = "EXACT_TIMESTAMP_SERIES"
    exact_vocab_present = exact_label in ((schema.get("controlled_vocabularies") or {}).get("measurement_precision") or [])
    exact_validator_mentions = validator_text.count(exact_label)
    timestamp_field_markers = [
        "before_observation_utc",
        "after_observation_utc",
        "event_anchor_utc",
        "series_timezone",
        "sampling_interval",
        "market_series_id",
        "series_provenance",
    ]
    timestamp_contract_fields_present = [marker for marker in timestamp_field_markers if marker in validator_text]

    exact_contract = {
        "exact_timestamp_series_vocab_present": exact_vocab_present,
        "validator_exact_timestamp_series_literal_count": exact_validator_mentions,
        "dedicated_exact_series_validator_branch_present": exact_validator_mentions > 0,
        "required_exact_series_contract_markers_present": timestamp_contract_fields_present,
        "required_exact_series_contract_marker_count": len(timestamp_contract_fields_present),
        "current_validator_only_requires_generic_movement_fields": True,
        "architectural_gap": (
            exact_vocab_present
            and report["analysis_semantics"]["exact_timestamp_series_rows"] == 0
            and exact_validator_mentions == 0
            and len(timestamp_contract_fields_present) == 0
        ),
    }

    frontier = sorted(
        report["eligible_unreviewed_frontier"],
        key=lambda row: (-row["novel_dimension_count"], row.get("occurrence_id") or ""),
    )

    categories_gap = report["upstream_population_gaps"]["categories_present_in_registry_but_absent_from_completed_anchors"]
    reviewed_category_gap = report["upstream_population_gaps"]["categories_with_completed_anchor_but_no_reviewed_sample"]
    reviewed_type_gap = report["upstream_population_gaps"]["event_types_with_completed_anchor_but_no_reviewed_sample"]

    candidate_scores: list[dict[str, Any]] = []
    for row in frontier:
        novelty = row["novelty_against_reviewed_sample"]
        score = 0
        reasons: list[str] = []
        if novelty["new_category"]:
            score += 3
            reasons.append("new reviewed category")
        if novelty["new_event_type"]:
            score += 3
            reasons.append("new reviewed event type")
        if novelty["new_institution"]:
            score += 1
            reasons.append("new reviewed institution")
        if novelty["new_region"]:
            score += 2
            reasons.append("new reviewed region")
        if row.get("occurrence_id") == "WSO-FIN-B-0004":
            score += 1
            reasons.append("exact canonical release tests event-time versus market-measurement boundary")
        if row.get("occurrence_id") == "WSO-MAC-B-0041":
            score -= 2
            reasons.append("repeats already reviewed macro/data-release contract")
        candidate_scores.append({**row, "heuristic_score": score, "heuristic_reasons": reasons})

    methodology_score = 0
    methodology_reasons: list[str] = []
    if exact_contract["architectural_gap"]:
        methodology_score += 6
        methodology_reasons.append("EXACT_TIMESTAMP_SERIES is selectable without exact-series-specific validation")
    if report["analysis_semantics"]["total_market_movement_rows"] > 0:
        methodology_score += 2
        methodology_reasons.append("market-movement rows already exist, so the weak precision contract is live rather than hypothetical")
    if report["analysis_semantics"]["exact_timestamp_series_rows"] == 0:
        methodology_score += 2
        methodology_reasons.append("zero exact-series rows permits contract repair before first population")
    if len(frontier) >= 5:
        methodology_score += 1
        methodology_reasons.append("remaining Analysis frontier is broad enough that methodology work does not strand a single urgent specimen")

    market_structure_score = 0
    market_structure_reasons: list[str] = []
    if categories_gap == ["CORPORATE_FINANCIAL_MARKET_STRUCTURE"]:
        market_structure_score += 2
        market_structure_reasons.append("sole upstream completed-anchor category gap")
    market_structure_score -= 2
    market_structure_reasons.append("forward coverage is mechanically concentrated and no historical anchor should be added merely to close the histogram")

    top_specimen_score = max((row["heuristic_score"] for row in candidate_scores), default=0)
    decision = "EXACT_MARKET_MEASUREMENT_CONTRACT" if methodology_score > top_specimen_score and methodology_score > market_structure_score else "REASSESS"

    report["post_aj_pressure"] = {
        "remaining_completed_unreviewed": len(frontier),
        "frontier_ranked": candidate_scores,
        "completed_anchor_category_gaps": categories_gap,
        "completed_anchor_review_category_gaps": reviewed_category_gap,
        "completed_anchor_review_event_type_gaps": reviewed_type_gap,
        "market_structure_gap_is_not_quota": True,
        "exact_market_measurement_contract": exact_contract,
        "option_scores": {
            "exact_market_measurement_methodology": {
                "score": methodology_score,
                "reasons": methodology_reasons,
            },
            "best_analysis_specimen": {
                "score": top_specimen_score,
                "candidate": candidate_scores[0]["occurrence_id"] if candidate_scores else None,
            },
            "historical_market_structure_anchor": {
                "score": market_structure_score,
                "reasons": market_structure_reasons,
            },
        },
        "recommended_next_tranche": decision,
        "recommended_scope": (
            "If the exact-market contract remains the leading option after external rights/source research, add an Analysis-schema/validator methodology tranche before any first EXACT_TIMESTAMP_SERIES row. "
            "It should require independently sourced pre/post observations with explicit UTC timestamps, a declared event anchor, ordered measurement window, series identity/provenance and no inference from canonical timing. "
            "Do not populate exact market data unless an independently reviewable data source and use basis are established."
        ),
    }

    # Fail closed if the live checkpoint is not the verified post-AJ state.
    expected = {
        "canonical_registry_version": "0.37",
        "canonical_record_count": 687,
        "analysis_schema_version": "0.3",
        "analysis_reviews_version": "0.10",
        "analysis_review_count": 14,
        "analysis_evidence_version": "0.10",
        "analysis_evidence_count": 54,
        "source_registry_version": "1.78",
        "source_count": 242,
        "change_ledger_version": "0.24",
        "change_count": 59,
        "biosecurity_overlay_version": "0.12",
    }
    failures = {key: {"expected": value, "actual": checkpoint.get(key)} for key, value in expected.items() if checkpoint.get(key) != value}
    if failures:
        raise RuntimeError("post-AJ checkpoint mismatch: " + json.dumps(failures, sort_keys=True))
    if report["readiness"]["eligible_completed_occurrence_count"] != 20:
        raise RuntimeError("expected 20 completed Analysis-eligible occurrences")
    if report["readiness"]["reviewed_occurrence_count"] != 14:
        raise RuntimeError("expected 14 reviewed occurrences")
    if report["readiness"]["reviewed_event_type_diversity"] != 12:
        raise RuntimeError("expected reviewed event-type diversity 12")
    if report["analysis_semantics"]["exact_timestamp_series_rows"] != 0:
        raise RuntimeError("preflight assumes no existing EXACT_TIMESTAMP_SERIES row")
    if version_tuple(str(overlay.get("version"))) < version_tuple("0.12"):
        raise RuntimeError("biosecurity overlay version regressed")

    return report


def main() -> None:
    report = build_report()
    print("POST_AJ_AUDIT_OK")
    print(json.dumps({
        "checkpoint": report["checkpoint"],
        "readiness": report["readiness"],
        "analysis_semantics": report["analysis_semantics"],
        "upstream_population_gaps": report["upstream_population_gaps"],
        "post_aj_pressure": report["post_aj_pressure"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
