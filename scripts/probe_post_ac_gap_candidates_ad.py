#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "data/canonical/registry.json").read_text(encoding="utf-8"))
SOURCES = json.loads((ROOT / "data/sources/registry.json").read_text(encoding="utf-8"))
REVIEWS = json.loads((ROOT / "data/analysis/event_reviews.json").read_text(encoding="utf-8"))
EVIDENCE = json.loads((ROOT / "data/analysis/evidence_registry.json").read_text(encoding="utf-8"))

TARGET_CATEGORIES = [
    "CLIMATE_ENVIRONMENT",
    "CORPORATE_FINANCIAL_MARKET_STRUCTURE",
    "ELECTIONS_GOVERNANCE",
    "HEALTH_BIOSECURITY",
    "PHYSICAL_CLIMATE_RISK",
    "TRADE_SANCTIONS_INDUSTRIAL_POLICY",
]
REFERENCE_DATE = "2026-09-06"

records = REGISTRY["records"]
by_source = {row.get("source_id"): row for row in SOURCES.get("sources", [])}
reviewed_occurrence_ids = {
    row.get("occurrence_id") for row in REVIEWS.get("reviews", []) if row.get("occurrence_id")
}

print("POST_AC_CHECKPOINT", json.dumps({
    "canonical_version": REGISTRY.get("version"),
    "canonical_count": len(records),
    "source_version": SOURCES.get("version"),
    "source_count": len(SOURCES.get("sources", [])),
    "analysis_reviews_version": REVIEWS.get("version"),
    "analysis_reviews_count": len(REVIEWS.get("reviews", [])),
    "analysis_evidence_version": EVIDENCE.get("version"),
    "analysis_evidence_count": len(EVIDENCE.get("evidence", [])),
}, sort_keys=True))

for category in TARGET_CATEGORIES:
    subset = [row for row in records if row.get("category") == category]
    series = sorted({row.get("series_id") for row in subset if row.get("series_id")})
    institutions = sorted({row.get("institution") for row in subset if row.get("institution")})
    lifecycle = Counter(row.get("lifecycle_status") for row in subset)
    completed = [row for row in subset if row.get("lifecycle_status") == "COMPLETED"]
    print("CATEGORY", json.dumps({
        "category": category,
        "occurrences": len(subset),
        "series_count": len(series),
        "series_ids": series,
        "institution_count": len(institutions),
        "institutions": institutions,
        "lifecycle": dict(sorted(lifecycle.items())),
        "completed_count": len(completed),
        "reviewed_completed_count": sum(1 for row in completed if row.get("occurrence_id") in reviewed_occurrence_ids),
    }, sort_keys=True))

wha = [row for row in records if row.get("series_id") == "WSER-HEALTH-WHA"]
print("WHA_RECORD_COUNT", len(wha))
for row in wha:
    fields = {
        key: row.get(key)
        for key in (
            "occurrence_id", "series_id", "canonical_name", "short_calendar_title",
            "institution", "jurisdiction", "region", "category", "subcategory",
            "event_type", "certainty_status", "lifecycle_status", "timing_type",
            "start_local", "end_local", "source_timezone", "start_utc", "end_utc",
            "time_precision", "all_day_semantics", "time_status", "time_basis",
            "location", "source_id", "primary_source_assertion_id",
            "last_successful_assertion_id", "importance_tier", "expected_market_sensitivity",
            "health_process", "health_security_relevance", "notes",
        )
        if key in row
    }
    print("WHA_RECORD", json.dumps(fields, sort_keys=True, ensure_ascii=False))
    source = by_source.get(row.get("source_id"))
    if source:
        source_fields = {
            key: source.get(key)
            for key in (
                "source_id", "institution", "jurisdiction", "domain", "endpoint_role",
                "authoritative_url", "source_type", "source_timezone", "information_supplied",
                "canonical_dependency_count", "automation_permission_status",
                "monitoring_readiness", "notes",
            )
            if key in source
        }
        print("WHA_SOURCE", json.dumps(source_fields, sort_keys=True, ensure_ascii=False))

# Past-starting records in still-missing categories that are not terminal.
for row in records:
    if row.get("category") not in TARGET_CATEGORIES:
        continue
    start = row.get("start_local")
    if not isinstance(start, str) or start[:10] > REFERENCE_DATE:
        continue
    if row.get("lifecycle_status") in {"COMPLETED", "CANCELLED"}:
        continue
    print("PAST_NONTERMINAL", json.dumps({
        "occurrence_id": row.get("occurrence_id"),
        "series_id": row.get("series_id"),
        "category": row.get("category"),
        "event_type": row.get("event_type"),
        "canonical_name": row.get("canonical_name"),
        "start_local": row.get("start_local"),
        "end_local": row.get("end_local"),
        "lifecycle_status": row.get("lifecycle_status"),
        "source_id": row.get("source_id"),
    }, sort_keys=True, ensure_ascii=False))
