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
    "PHYSICAL_CLIMATE_RISK",
]
REFERENCE_DATE = "2026-09-06"
TERMINAL = {"COMPLETED", "CANCELLED"}
records = REGISTRY["records"]
sources = SOURCES.get("sources", [])
by_source = {row.get("source_id"): row for row in sources}
reviewed_ids = {row.get("occurrence_id") for row in REVIEWS.get("reviews", []) if row.get("occurrence_id")}

print("POST_AE_CHECKPOINT", json.dumps({
    "canonical_version": REGISTRY.get("version"),
    "canonical_count": len(records),
    "source_version": SOURCES.get("version"),
    "source_count": len(sources),
    "analysis_reviews_version": REVIEWS.get("version"),
    "analysis_reviews_count": len(REVIEWS.get("reviews", [])),
    "analysis_evidence_version": EVIDENCE.get("version"),
    "analysis_evidence_count": len(EVIDENCE.get("evidence", [])),
}, sort_keys=True))

for category in TARGET_CATEGORIES:
    subset = [row for row in records if row.get("category") == category]
    completed = [row for row in subset if row.get("lifecycle_status") == "COMPLETED"]
    print("CATEGORY", json.dumps({
        "category": category,
        "occurrences": len(subset),
        "series_count": len({row.get("series_id") for row in subset if row.get("series_id")}),
        "event_types": sorted({row.get("event_type") for row in subset if row.get("event_type")}),
        "regions": sorted({row.get("region") for row in subset if row.get("region")}),
        "institutions": sorted({row.get("institution") for row in subset if row.get("institution")}),
        "lifecycle": dict(sorted(Counter(row.get("lifecycle_status") for row in subset).items())),
        "completed_count": len(completed),
        "reviewed_completed_count": sum(1 for row in completed if row.get("occurrence_id") in reviewed_ids),
    }, sort_keys=True, ensure_ascii=False))

    for row in sorted(subset, key=lambda x: ((x.get("start_local") or "9999"), x.get("occurrence_id") or "")):
        print("ROW", json.dumps({
            "category": category,
            "occurrence_id": row.get("occurrence_id"),
            "series_id": row.get("series_id"),
            "canonical_name": row.get("canonical_name"),
            "institution": row.get("institution"),
            "jurisdiction": row.get("jurisdiction"),
            "region": row.get("region"),
            "event_type": row.get("event_type"),
            "certainty_status": row.get("certainty_status"),
            "lifecycle_status": row.get("lifecycle_status"),
            "timing_type": row.get("timing_type"),
            "start_local": row.get("start_local"),
            "end_local": row.get("end_local"),
            "source_timezone": row.get("source_timezone"),
            "time_precision": row.get("time_precision"),
            "source_id": row.get("source_id"),
            "intrinsic_importance": row.get("intrinsic_importance"),
            "expected_market_sensitivity": row.get("expected_market_sensitivity"),
        }, sort_keys=True, ensure_ascii=False))

for row in records:
    if row.get("category") not in TARGET_CATEGORIES:
        continue
    start = row.get("start_local")
    if not isinstance(start, str) or start[:10] > REFERENCE_DATE:
        continue
    if row.get("lifecycle_status") in TERMINAL:
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

source_deps = defaultdict(list)
for row in records:
    if row.get("category") in TARGET_CATEGORIES and row.get("source_id"):
        source_deps[row["source_id"]].append(row.get("occurrence_id"))

for source_id in sorted(source_deps):
    src = by_source.get(source_id, {})
    print("SOURCE", json.dumps({
        "source_id": source_id,
        "source_name": src.get("source_name") or src.get("name"),
        "institution": src.get("institution"),
        "primary_url": src.get("primary_url") or src.get("url"),
        "source_type": src.get("source_type"),
        "canonical_dependency_count_helper": src.get("canonical_dependency_count"),
        "actual_target_dependencies": len(source_deps[source_id]),
        "target_occurrence_ids": sorted(source_deps[source_id]),
        "monitoring_mode": src.get("monitoring_mode"),
        "automation_permission": src.get("automation_permission"),
    }, sort_keys=True, ensure_ascii=False))

eligible = [
    row for row in records
    if row.get("lifecycle_status") == "COMPLETED"
    and row.get("record_class") == "OCCURRENCE"
    and row.get("render_policy") != "EXCLUDE"
]
print("COMPLETED_FRONTIER_SUMMARY", json.dumps({
    "eligible_completed_occurrence_count": len(eligible),
    "reviewed_completed_occurrence_count": sum(1 for row in eligible if row.get("occurrence_id") in reviewed_ids),
    "unreviewed_completed_ids": sorted(row.get("occurrence_id") for row in eligible if row.get("occurrence_id") not in reviewed_ids),
}, sort_keys=True, ensure_ascii=False))
