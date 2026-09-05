#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.audit_analysis_sample_y import audit as base_audit

BASE_MAIN_SHA = "b12058d260a8139c893feb52ad864258044e83b2"
REFERENCE_DATE = "2026-09-06"


def main() -> None:
    report = base_audit()
    registry = json.loads((ROOT / "data/canonical/registry.json").read_text(encoding="utf-8"))
    reviews = json.loads((ROOT / "data/analysis/event_reviews.json").read_text(encoding="utf-8"))
    evidence = json.loads((ROOT / "data/analysis/evidence_registry.json").read_text(encoding="utf-8"))
    sources = json.loads((ROOT / "data/sources/registry.json").read_text(encoding="utf-8"))
    ledger = json.loads((ROOT / "data/changes/ledger.json").read_text(encoding="utf-8"))
    overlay = json.loads((ROOT / "data/coverage/biosecurity_overlay.json").read_text(encoding="utf-8"))

    records = registry["records"]
    reviewed_ids = {r.get("canonical_occurrence_id") for r in reviews.get("reviews", [])}
    completed = [r for r in records if r.get("lifecycle_status") == "COMPLETED"]
    eligible_ids = {row["occurrence_id"] for row in report["eligible_completed_population"]}
    eligible_completed = [r for r in completed if r.get("occurrence_id") in eligible_ids]
    unreviewed = [r for r in eligible_completed if r.get("occurrence_id") not in reviewed_ids]

    reviewed_regions = {r.get("canonical_region") for r in reviews.get("reviews", []) if r.get("canonical_region")}
    reviewed_categories = {r.get("canonical_category") for r in reviews.get("reviews", []) if r.get("canonical_category")}
    reviewed_types = {r.get("canonical_event_type") for r in reviews.get("reviews", []) if r.get("canonical_event_type")}
    reviewed_institutions = {r.get("canonical_institution") for r in reviews.get("reviews", []) if r.get("canonical_institution")}

    frontier = []
    for r in unreviewed:
        novelty = {
            "new_region": r.get("region") not in reviewed_regions,
            "new_category": r.get("category") not in reviewed_categories,
            "new_event_type": r.get("event_type") not in reviewed_types,
            "new_institution": r.get("institution") not in reviewed_institutions,
            "exact_canonical_timestamp": bool(r.get("start_utc")) and r.get("time_precision") in {"MINUTE", "SECOND"},
        }
        frontier.append({
            "occurrence_id": r.get("occurrence_id"),
            "canonical_name": r.get("canonical_name"),
            "series_id": r.get("series_id"),
            "region": r.get("region"),
            "jurisdiction": r.get("jurisdiction"),
            "category": r.get("category"),
            "event_type": r.get("event_type"),
            "institution": r.get("institution"),
            "intrinsic_importance": r.get("intrinsic_importance"),
            "expected_market_sensitivity": r.get("expected_market_sensitivity"),
            "start_local": r.get("start_local"),
            "source_timezone": r.get("source_timezone"),
            "start_utc": r.get("start_utc"),
            "time_precision": r.get("time_precision"),
            "source_id": r.get("source_id"),
            "novelty": novelty,
            "novelty_score": sum(bool(v) for v in novelty.values()),
        })
    frontier.sort(key=lambda x: (-x["novelty_score"], x.get("start_local") or "", x["occurrence_id"]))

    market_rows = [r for r in records if r.get("category") == "CORPORATE_FINANCIAL_MARKET_STRUCTURE"]
    market_completed = [r for r in market_rows if r.get("lifecycle_status") == "COMPLETED"]

    gaps = report["upstream_population_gaps"]
    semantics = report["analysis_semantics"]
    checkpoint = {
        "base_main_sha": BASE_MAIN_SHA,
        "canonical": [registry.get("version"), len(records)],
        "sources": [sources.get("version"), len(sources.get("sources", []))],
        "ledger": [ledger.get("version"), len(ledger.get("changes", []))],
        "overlay": [overlay.get("version"), overlay.get("canonical_checkpoint")],
        "analysis_reviews": [reviews.get("version"), len(reviews.get("reviews", []))],
        "analysis_evidence": [evidence.get("version"), len(evidence.get("evidence", []))],
    }

    out = {
        "audit": "POST_AH_PRESSURE_AUDIT_AI",
        "reference_date": REFERENCE_DATE,
        "checkpoint": checkpoint,
        "readiness": report["readiness"],
        "upstream_population_gaps": gaps,
        "analysis_semantics": {
            "total_market_movement_rows": semantics["total_market_movement_rows"],
            "exact_timestamp_series_rows": semantics["exact_timestamp_series_rows"],
            "source_reported_or_session_market_rows": semantics["source_reported_or_session_market_rows"],
        },
        "completed_population": {
            "eligible_completed": len(eligible_completed),
            "reviewed": len(reviewed_ids & eligible_ids),
            "unreviewed": len(unreviewed),
            "category_counts": dict(sorted(Counter(r.get("category") for r in eligible_completed).items())),
            "event_type_counts": dict(sorted(Counter(r.get("event_type") for r in eligible_completed).items())),
            "region_counts": dict(sorted(Counter(r.get("region") for r in eligible_completed).items())),
        },
        "frontier_ranked": frontier,
        "market_structure_gap": {
            "occurrence_count": len(market_rows),
            "series_count": len({r.get("series_id") for r in market_rows}),
            "completed_count": len(market_completed),
            "lifecycle_counts": dict(sorted(Counter(r.get("lifecycle_status") for r in market_rows).items())),
            "event_type_counts": dict(sorted(Counter(r.get("event_type") for r in market_rows).items())),
            "institutions": sorted({r.get("institution") for r in market_rows if r.get("institution")}),
            "rows": [{
                "occurrence_id": r.get("occurrence_id"),
                "canonical_name": r.get("canonical_name"),
                "series_id": r.get("series_id"),
                "institution": r.get("institution"),
                "event_type": r.get("event_type"),
                "lifecycle_status": r.get("lifecycle_status"),
                "start_local": r.get("start_local"),
                "time_precision": r.get("time_precision"),
                "source_id": r.get("source_id"),
            } for r in market_rows],
        },
    }
    print("POST_AH_PRESSURE_AUDIT_OK")
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
