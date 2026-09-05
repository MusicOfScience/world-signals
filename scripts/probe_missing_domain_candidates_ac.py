#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data/canonical/registry.json"
SOURCES = ROOT / "data/sources/registry.json"
LEDGER = ROOT / "data/changes/ledger.json"
OVERLAY = ROOT / "data/coverage/biosecurity_overlay.json"
ANALYSIS_REVIEWS = ROOT / "data/analysis/event_reviews.json"
ANALYSIS_EVIDENCE = ROOT / "data/analysis/evidence_registry.json"
REFERENCE_DATE = "2026-09-06"
TARGET_TEMPLATE_ID = "WSO-FIN-B-0001"
TARGET_SOURCE_ID = "WSSRC-FIN-001"

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


def row_summary(row: dict[str, object]) -> dict[str, object]:
    return {
        "occurrence_id": row.get("occurrence_id"),
        "series_id": row.get("series_id"),
        "canonical_name": row.get("canonical_name"),
        "short_calendar_title": row.get("short_calendar_title"),
        "institution": row.get("institution"),
        "jurisdiction": row.get("jurisdiction"),
        "country_or_economy": row.get("country_or_economy"),
        "region": row.get("region"),
        "category": row.get("category"),
        "event_type": row.get("event_type"),
        "start_local": row.get("start_local"),
        "end_local": row.get("end_local"),
        "source_timezone": row.get("source_timezone"),
        "start_utc": row.get("start_utc"),
        "end_utc": row.get("end_utc"),
        "timing_type": row.get("timing_type"),
        "time_precision": row.get("time_precision"),
        "all_day_semantics": row.get("all_day_semantics"),
        "time_status": row.get("time_status"),
        "time_basis": row.get("time_basis"),
        "lifecycle_status": row.get("lifecycle_status"),
        "certainty_status": row.get("certainty_status"),
        "source_id": row.get("source_id"),
        "primary_source_assertion_id": row.get("primary_source_assertion_id"),
        "last_successful_assertion_id": row.get("last_successful_assertion_id"),
        "intrinsic_importance": row.get("intrinsic_importance"),
        "expected_market_sensitivity": row.get("expected_market_sensitivity"),
        "calendar_rendering_class": row.get("calendar_rendering_class"),
        "related_document_count": len(row.get("related_documents") or []),
        "status_history_count": len(row.get("status_history") or []),
    }


def main() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    sources = json.loads(SOURCES.read_text(encoding="utf-8"))
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    overlay = json.loads(OVERLAY.read_text(encoding="utf-8"))
    reviews = json.loads(ANALYSIS_REVIEWS.read_text(encoding="utf-8"))
    evidence = json.loads(ANALYSIS_EVIDENCE.read_text(encoding="utf-8"))
    rows = registry.get("records", [])
    missing_rows = [row for row in rows if row.get("category") in MISSING_CATEGORIES]

    candidates = []
    for row in missing_rows:
        date = leading_date(row.get("start_local"))
        if not date or date > REFERENCE_DATE:
            continue
        lifecycle = str(row.get("lifecycle_status") or "UNSPECIFIED")
        if lifecycle in TERMINAL:
            continue
        candidates.append(row_summary(row))

    candidates.sort(key=lambda row: (str(row.get("start_local") or ""), str(row.get("occurrence_id") or "")), reverse=True)

    series_rows: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in missing_rows:
        series_rows[str(row.get("series_id") or "NO_SERIES")].append(row)

    series_inventory: dict[str, list[dict[str, object]]] = {category: [] for category in sorted(MISSING_CATEGORIES)}
    for series_id, group in series_rows.items():
        sample = sorted(group, key=lambda row: str(row.get("start_local") or ""))
        category = str(sample[0].get("category"))
        dated = [leading_date(row.get("start_local")) for row in sample]
        dated = [date for date in dated if date]
        inventory_row = {
            "series_id": series_id,
            "institution": sample[0].get("institution"),
            "country_or_economy": sample[0].get("country_or_economy"),
            "region": sample[0].get("region"),
            "event_types": sorted({str(row.get("event_type")) for row in sample}),
            "source_ids": sorted({str(row.get("source_id")) for row in sample}),
            "occurrence_count": len(sample),
            "earliest_date": min(dated) if dated else None,
            "latest_date": max(dated) if dated else None,
            "lifecycle_counts": dict(sorted(Counter(str(row.get("lifecycle_status")) for row in sample).items())),
            "sample_occurrences": [row_summary(row) for row in sample[:2]],
        }
        series_inventory.setdefault(category, []).append(inventory_row)

    for category in series_inventory:
        series_inventory[category].sort(key=lambda row: (str(row.get("institution") or ""), str(row.get("series_id") or "")))

    by_occ = {row.get("occurrence_id"): row for row in rows}
    by_source = {row.get("source_id"): row for row in sources.get("sources", [])}
    category_counts = Counter(str(row.get("category")) for row in candidates)
    event_type_counts = Counter(str(row.get("event_type")) for row in candidates)
    region_counts = Counter(str(row.get("region")) for row in candidates)

    report = {
        "project": "WORLD SIGNALS",
        "probe": "MISSING_DOMAIN_RECON_AC",
        "reference_date": REFERENCE_DATE,
        "checkpoint": {
            "canonical_version": registry.get("version"),
            "canonical_record_count": len(rows),
            "canonical_record_count_field": registry.get("record_count"),
            "source_version": sources.get("version"),
            "source_record_count": len(sources.get("sources", [])),
            "ledger_version": ledger.get("version"),
            "ledger_change_count": len(ledger.get("changes", [])),
            "overlay_version": overlay.get("version"),
            "overlay_checkpoint": overlay.get("canonical_checkpoint"),
            "analysis_reviews_version": reviews.get("version"),
            "analysis_review_count": len(reviews.get("reviews", [])),
            "analysis_evidence_version": evidence.get("version"),
            "analysis_evidence_count": len(evidence.get("evidence", [])),
        },
        "missing_categories": sorted(MISSING_CATEGORIES),
        "canonical_occurrence_count_in_missing_categories": len(missing_rows),
        "canonical_series_count_in_missing_categories": len(series_rows),
        "past_dated_nonterminal_candidate_count": len(candidates),
        "counts_by_category": dict(sorted(category_counts.items())),
        "counts_by_event_type": dict(sorted(event_type_counts.items())),
        "counts_by_region": dict(sorted(region_counts.items())),
        "past_dated_nonterminal_candidates": candidates,
        "series_inventory_by_category": series_inventory,
        "rba_fsr_target_preflight": {
            "template": row_summary(by_occ[TARGET_TEMPLATE_ID]),
            "source": by_source[TARGET_SOURCE_ID],
            "same_series_occurrence_ids": [
                row.get("occurrence_id") for row in rows
                if row.get("series_id") == by_occ[TARGET_TEMPLATE_ID].get("series_id")
            ],
        },
        "discipline": {
            "elapsed_time_is_completion_evidence": False,
            "completion_requires_post_event_authoritative_evidence": True,
            "stable_identity_repair_preferred_before_new_history": True,
            "prefer_existing_series_for_historical_backfill_when_semantically_correct": True,
        },
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
