from __future__ import annotations
from collections import Counter

def _source_map(source_registry: dict) -> dict[str, dict]:
    return {s.get("source_id"): s for s in source_registry.get("sources", [])}

def public_projection(registry: dict, source_registry: dict) -> dict:
    smap = _source_map(source_registry)
    rows=[]
    for r in registry.get("records", []):
        s=smap.get(r.get("source_id"), {})
        rows.append({
            "occurrence_id": r.get("occurrence_id"),
            "series_id": r.get("series_id"),
            "title": r.get("short_calendar_title") or r.get("canonical_name"),
            "canonical_name": r.get("canonical_name"),
            "category": r.get("category"),
            "subcategory": r.get("subcategory"),
            "region": r.get("region"),
            "jurisdiction": r.get("jurisdiction"),
            "institution": r.get("institution"),
            "certainty": r.get("certainty_status"),
            "lifecycle": r.get("lifecycle_status"),
            "timing_type": r.get("timing_type"),
            "start_local": r.get("start_local"),
            "end_local": r.get("end_local"),
            "start_utc": r.get("start_utc"),
            "end_utc": r.get("end_utc"),
            "date_earliest": r.get("date_earliest"),
            "date_latest": r.get("date_latest"),
            "season_window_model": r.get("season_window_model"),
            "source_native_window_label": r.get("source_native_window_label"),
            "season_phases": r.get("season_phases", []),
            "native_calendar_system": r.get("native_calendar_system"),
            "native_calendar_year": r.get("native_calendar_year"),
            "native_calendar_month": r.get("native_calendar_month"),
            "native_calendar_day": r.get("native_calendar_day"),
            "source_native_date_label": r.get("source_native_date_label"),
            "gregorian_resolution_status": r.get("gregorian_resolution_status"),
            "source_timezone": r.get("source_timezone"),
            "visibility_tier": r.get("visibility_tier"),
            "render_policy": r.get("render_policy"),
            "intrinsic_importance": r.get("intrinsic_importance"),
            "expected_market_sensitivity": r.get("expected_market_sensitivity"),
            "source_id": r.get("source_id"),
            "source_url": s.get("authoritative_url"),
            "source_institution": s.get("institution"),
            "monitoring_readiness": s.get("monitoring_readiness_status"),
            "automated_monitoring_use": s.get("automated_monitoring_use"),
            "notes": r.get("notes"),
        })
    cats=Counter(x["category"] for x in rows)
    regions=Counter(x["region"] for x in rows)
    return {
        "metadata": {
            "registry_version": registry.get("version"),
            "reference_date": registry.get("reference_date"),
            "record_count": len(rows),
            "automatic_commit": False,
            "google_calendar_write": False,
            "category_counts": dict(cats),
            "region_counts": dict(regions),
        },
        "events": rows,
    }
