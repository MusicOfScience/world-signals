#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "data/canonical/registry.json").read_text(encoding="utf-8"))
SOURCES = json.loads((ROOT / "data/sources/registry.json").read_text(encoding="utf-8"))
LEDGER = json.loads((ROOT / "data/changes/ledger.json").read_text(encoding="utf-8"))
OVERLAY = json.loads((ROOT / "data/coverage/biosecurity_overlay.json").read_text(encoding="utf-8"))
REVIEWS = json.loads((ROOT / "data/analysis/event_reviews.json").read_text(encoding="utf-8"))
EVIDENCE = json.loads((ROOT / "data/analysis/evidence_registry.json").read_text(encoding="utf-8"))

TARGETS = {"CLIMATE_ENVIRONMENT", "CORPORATE_FINANCIAL_MARKET_STRUCTURE"}
TERMINAL = {"COMPLETED", "CANCELLED"}
REFERENCE_DATE = "2026-09-06"
records = REGISTRY["records"]
sources = SOURCES["sources"]
by_source = {s["source_id"]: s for s in sources}
reviewed = {r.get("canonical_occurrence_id") or r.get("occurrence_id") for r in REVIEWS.get("reviews", [])}

print("CHECKPOINT", json.dumps({
    "canonical": [REGISTRY.get("version"), len(records)],
    "sources": [SOURCES.get("version"), len(sources)],
    "ledger": [LEDGER.get("version"), len(LEDGER.get("changes", []))],
    "overlay": [OVERLAY.get("version"), OVERLAY.get("canonical_checkpoint")],
    "analysis_reviews": [REVIEWS.get("version"), len(REVIEWS.get("reviews", []))],
    "analysis_evidence": [EVIDENCE.get("version"), len(EVIDENCE.get("evidence", []))],
}, sort_keys=True))

for cat in sorted(TARGETS):
    rows = [r for r in records if r.get("category") == cat]
    print("CATEGORY", json.dumps({
        "category": cat,
        "occurrences": len(rows),
        "series": len({r.get("series_id") for r in rows}),
        "institutions": len({r.get("institution") for r in rows}),
        "sources": len({r.get("source_id") for r in rows}),
        "lifecycle": dict(sorted(Counter(r.get("lifecycle_status") for r in rows).items())),
        "completed": sum(r.get("lifecycle_status") == "COMPLETED" for r in rows),
        "reviewed_completed": sum(r.get("lifecycle_status") == "COMPLETED" and r.get("occurrence_id") in reviewed for r in rows),
    }, sort_keys=True))
    for r in sorted(rows, key=lambda x: (str(x.get("start_local") or x.get("date_earliest") or ""), x.get("occurrence_id", ""))):
        print("ROW", json.dumps({k: r.get(k) for k in (
            "occurrence_id", "series_id", "canonical_name", "category", "subcategory",
            "jurisdiction", "region", "institution", "event_type", "record_class",
            "signal_object_class", "certainty_status", "lifecycle_status", "activation_mode",
            "timing_type", "start_local", "end_local", "date_earliest", "date_latest",
            "source_timezone", "start_utc", "end_utc", "time_precision", "time_status",
            "time_basis", "all_day_semantics", "location", "source_id", "intrinsic_importance",
            "importance_tier", "expected_market_sensitivity", "notes"
        ) if k in r}, sort_keys=True, ensure_ascii=False))

print("PAST_NONTERMINAL")
for r in records:
    if r.get("category") not in TARGETS:
        continue
    start = r.get("start_local") or r.get("date_earliest")
    if not isinstance(start, str) or start[:10] > REFERENCE_DATE or r.get("lifecycle_status") in TERMINAL:
        continue
    print(json.dumps({
        "occurrence_id": r.get("occurrence_id"), "series_id": r.get("series_id"),
        "category": r.get("category"), "canonical_name": r.get("canonical_name"),
        "start_local": r.get("start_local"), "end_local": r.get("end_local"),
        "lifecycle_status": r.get("lifecycle_status"), "source_id": r.get("source_id")
    }, sort_keys=True, ensure_ascii=False))

candidate_source_ids = sorted({r.get("source_id") for r in records if r.get("category") in TARGETS and r.get("source_id")})
for sid in candidate_source_ids:
    actual = [r.get("occurrence_id") for r in records if r.get("source_id") == sid]
    src = by_source.get(sid, {})
    print("SOURCE", json.dumps({
        "source_id": sid,
        "institution": src.get("institution"),
        "authoritative_url": src.get("authoritative_url"),
        "source_timezone": src.get("source_timezone"),
        "parser_type": src.get("parser_type"),
        "canonical_dependency_count": src.get("canonical_dependency_count"),
        "actual_primary_dependency_count": len(actual),
        "occurrence_ids": sorted(actual),
    }, sort_keys=True, ensure_ascii=False))

for cid in ["WSO-CLIM-UNFCCC-SB64-202606", "WSO-MKT-MSCI-20260512", "WSO-MKT-ASX-EXP-202606"]:
    print("ID_COLLISION", cid, any(r.get("occurrence_id") == cid for r in records))
for sid in ["WSER-CLIM-UNFCCC-SB", "WSER-MKT-MSCI-INDEX-REVIEW", "WSER-MKT-ASX-INDEX-DERIVATIVE-EXPIRY"]:
    print("SERIES_COLLISION", sid, any(r.get("series_id") == sid for r in records))
for sid in ["WSSRC-CLIM-004", "WSSRC-MKT-MSCI-001"]:
    print("SOURCE_COLLISION", sid, sid in by_source)

print("FULL_TEMPLATE", json.dumps(next(r for r in records if r.get("occurrence_id") == "WSO-CLIM-A-0001"), sort_keys=True, ensure_ascii=False))
print("FULL_CLIMATE_SOURCE", json.dumps(by_source["WSSRC-CLIM-001"], sort_keys=True, ensure_ascii=False))
