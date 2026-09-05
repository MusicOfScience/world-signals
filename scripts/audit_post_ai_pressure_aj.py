#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.analysis import analysis_population_readiness, validate_analysis

BASE_MAIN_SHA = "c85db2ec3a675a749acb8201705fb6f1f85de27d"


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def exact_timestamp_series_rows(reviews):
    return sum(
        1
        for review in reviews.get("reviews", [])
        for movement in (review.get("what_moved") or [])
        if movement.get("measurement_precision") == "EXACT_TIMESTAMP_SERIES"
    )


def main() -> None:
    canonical = load("data/canonical/registry.json")
    sources = load("data/sources/registry.json")
    ledger = load("data/changes/ledger.json")
    overlay = load("data/coverage/biosecurity_overlay.json")
    schema = load("data/analysis/schema.json")
    reviews = load("data/analysis/event_reviews.json")
    evidence = load("data/analysis/evidence_registry.json")

    assert (canonical["version"], len(canonical["records"])) == ("0.37", 687)
    assert (sources["version"], len(sources["sources"])) == ("1.78", 242)
    assert (ledger["version"], len(ledger["changes"])) == ("0.24", 59)
    assert (overlay["version"], overlay["canonical_checkpoint"]) == (
        "0.12", {"registry_version": "0.37", "record_count": 687}
    )
    assert schema["version"] == "0.3"
    assert (reviews["version"], len(reviews["reviews"])) == ("0.9", 13)
    assert reviews["canonical_checkpoint"] == {"registry_version": "0.37", "record_count": 687}
    assert (evidence["version"], len(evidence["evidence"])) == ("0.9", 50)

    report = validate_analysis(schema, evidence, reviews, canonical)
    assert report.ok, report.errors
    readiness = analysis_population_readiness(schema, reviews, canonical)
    assert readiness["eligible_completed_occurrence_count"] == 20
    assert readiness["reviewed_occurrence_count"] == 13
    assert readiness["reviewed_event_type_diversity"] == 11
    assert exact_timestamp_series_rows(reviews) == 0

    reviewed = set(readiness["reviewed_occurrence_ids"])
    target_id = "WSO-RISK-AU-TC-2025-26"
    assert target_id not in reviewed
    target = next(row for row in canonical["records"] if row.get("occurrence_id") == target_id)
    assert target["lifecycle_status"] == "COMPLETED"
    assert target["category"] == "PHYSICAL_CLIMATE_RISK"
    assert target["event_type"] == "PHYSICAL_RISK_WINDOW"
    assert target["start_local"] == "2025-11-01"
    assert target["end_local"] == "2026-04-30"
    assert target["source_timezone"] is None
    assert target["start_utc"] is None

    frontier = sorted(
        row["occurrence_id"] for row in canonical["records"]
        if row.get("lifecycle_status") == "COMPLETED"
        and row["occurrence_id"] not in reviewed
    )
    expected_frontier = sorted([
        "WSO-CLIM-UNFCCC-SB64-202606",
        "WSO-EL-KR-LGE-20260603",
        "WSO-FIN-B-0004",
        "WSO-HEALTH-WHA-079",
        "WSO-MAC-B-0041",
        "WSO-RISK-AU-TC-2025-26",
        "WSO-TRD-EU-RU-SANC-20260625",
    ])
    assert frontier == expected_frontier, frontier

    completed = [row for row in canonical["records"] if row.get("lifecycle_status") == "COMPLETED"]
    reviewed_categories = {
        next(row for row in canonical["records"] if row["occurrence_id"] == oid)["category"]
        for oid in reviewed
    }
    reviewed_event_types = {
        next(row for row in canonical["records"] if row["occurrence_id"] == oid)["event_type"]
        for oid in reviewed
    }
    assert target["category"] not in reviewed_categories
    assert target["event_type"] not in reviewed_event_types

    market_rows = [row for row in canonical["records"] if row.get("category") == "CORPORATE_FINANCIAL_MARKET_STRUCTURE"]
    assert len(market_rows) == 17
    assert all(row.get("lifecycle_status") == "PLANNED" for row in market_rows)
    assert not any(row.get("lifecycle_status") == "COMPLETED" for row in market_rows)

    result = {
        "audit": "POST_AI_PRESSURE_AUDIT_AJ",
        "base_main_sha": BASE_MAIN_SHA,
        "checkpoint": {
            "canonical": [canonical["version"], len(canonical["records"])],
            "sources": [sources["version"], len(sources["sources"])],
            "ledger": [ledger["version"], len(ledger["changes"])],
            "overlay": [overlay["version"], overlay["canonical_checkpoint"]],
            "analysis_reviews": [reviews["version"], len(reviews["reviews"])],
            "analysis_evidence": [evidence["version"], len(evidence["evidence"])],
        },
        "readiness": {
            "eligible_completed_occurrence_count": readiness["eligible_completed_occurrence_count"],
            "reviewed_occurrence_count": readiness["reviewed_occurrence_count"],
            "reviewed_event_type_diversity": readiness["reviewed_event_type_diversity"],
            "exact_timestamp_series_rows": exact_timestamp_series_rows(reviews),
        },
        "selected_candidate": {
            "occurrence_id": target_id,
            "category": target["category"],
            "event_type": target["event_type"],
            "new_reviewed_category": target["category"] not in reviewed_categories,
            "new_reviewed_event_type": target["event_type"] not in reviewed_event_types,
            "seasonal_window_without_synthetic_utc": target["start_utc"] is None and target["source_timezone"] is None,
        },
        "frontier": frontier,
        "market_structure_gap": {
            "occurrence_count": len(market_rows),
            "completed_count": sum(1 for row in market_rows if row.get("lifecycle_status") == "COMPLETED"),
            "selection_is_automatic": False,
        },
        "selection_discipline": {
            "queue_completion_is_objective": False,
            "market_structure_gap_must_be_filled_next": False,
            "climatology_may_be_promoted_to_season_specific_forecast": False,
        },
    }
    print("POST_AI_PRESSURE_AUDIT_OK")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
