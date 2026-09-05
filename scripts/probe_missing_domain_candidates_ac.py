#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data/canonical/registry.json"
REFERENCE_DATE = "2026-09-06"

MISSING_CATEGORIES = {
    "CLIMATE_ENVIRONMENT",
    "CORPORATE_FINANCIAL_MARKET_STRUCTURE",
    "ELECTIONS_GOVERNANCE",
    "FINANCIAL_STABILITY_REGULATION",
    "HEALTH_BIOSECURITY",
    "PHYSICAL_CLIMATE_RISK",
    "TRADE_SANCTIONS_INDUSTRIAL_POLICY",
}

TERMINAL = {"COMPLETED", "CANCELLED"}
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")


def leading_date(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    match = DATE_RE.match(value)
    return match.group(1) if match else None


def main() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    rows = registry.get("records", [])

    candidates = []
    for row in rows:
        category = row.get("category")
        if category not in MISSING_CATEGORIES:
            continue
        date = leading_date(row.get("start_local"))
        if not date or date > REFERENCE_DATE:
            continue
        lifecycle = str(row.get("lifecycle_status") or "UNSPECIFIED")
        if lifecycle in TERMINAL:
            continue
        candidates.append({
            "occurrence_id": row.get("occurrence_id"),
            "series_id": row.get("series_id"),
            "canonical_name": row.get("canonical_name"),
            "institution": row.get("institution"),
            "country_or_economy": row.get("country_or_economy"),
            "region": row.get("region"),
            "category": category,
            "event_type": row.get("event_type"),
            "start_local": row.get("start_local"),
            "source_timezone": row.get("source_timezone"),
            "time_precision": row.get("time_precision"),
            "time_status": row.get("time_status"),
            "lifecycle_status": lifecycle,
            "certainty_status": row.get("certainty_status"),
            "source_id": row.get("source_id"),
            "primary_source_assertion_id": row.get("primary_source_assertion_id"),
            "last_successful_assertion_id": row.get("last_successful_assertion_id"),
            "intrinsic_importance": row.get("intrinsic_importance"),
            "expected_market_sensitivity": row.get("expected_market_sensitivity"),
            "related_document_count": len(row.get("related_documents") or []),
            "status_history_count": len(row.get("status_history") or []),
        })

    candidates.sort(key=lambda row: (str(row.get("start_local") or ""), str(row.get("occurrence_id") or "")), reverse=True)

    category_counts = Counter(str(row.get("category")) for row in candidates)
    event_type_counts = Counter(str(row.get("event_type")) for row in candidates)
    region_counts = Counter(str(row.get("region")) for row in candidates)

    report = {
        "project": "WORLD SIGNALS",
        "probe": "MISSING_DOMAIN_RECON_AC",
        "reference_date": REFERENCE_DATE,
        "canonical_version": registry.get("version"),
        "canonical_record_count": len(rows),
        "missing_categories": sorted(MISSING_CATEGORIES),
        "past_dated_nonterminal_candidate_count": len(candidates),
        "counts_by_category": dict(sorted(category_counts.items())),
        "counts_by_event_type": dict(sorted(event_type_counts.items())),
        "counts_by_region": dict(sorted(region_counts.items())),
        "candidates": candidates,
        "discipline": {
            "elapsed_time_is_completion_evidence": False,
            "completion_requires_post_event_authoritative_evidence": True,
            "stable_identity_repair_preferred_before_new_history": True,
        },
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
