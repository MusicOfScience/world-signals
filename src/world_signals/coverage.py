from __future__ import annotations

from collections import Counter, defaultdict


FOCUS_REGIONS=("Africa","South Asia","Southeast Asia")
FOCUS_CATEGORIES=("PHYSICAL_CLIMATE_RISK","HEALTH_BIOSECURITY","ENERGY_COMMODITIES")


def _clean(value, fallback="UNKNOWN"):
    if value is None or value == "":
        return fallback
    return str(value)


def _summary(records: list[dict], dimension: str) -> list[dict]:
    buckets: dict[str,list[dict]]=defaultdict(list)
    for record in records:
        buckets[_clean(record.get(dimension))].append(record)
    rows=[]
    for key,items in buckets.items():
        series={_clean(x.get("series_id")) for x in items}
        institutions={_clean(x.get("institution")) for x in items}
        sources={_clean(x.get("source_id")) for x in items}
        categories={_clean(x.get("category")) for x in items}
        rows.append({
            dimension:key,
            "occurrence_count":len(items),
            "unique_series_count":len(series),
            "unique_institution_count":len(institutions),
            "unique_source_count":len(sources),
            "unique_category_count":len(categories),
            "occurrences_per_series":round(len(items)/len(series),2) if series else None,
        })
    return sorted(rows,key=lambda x:(-x["occurrence_count"],x[dimension]))


def _series_summary(records: list[dict]) -> list[dict]:
    buckets: dict[str,list[dict]]=defaultdict(list)
    for r in records:
        buckets[_clean(r.get("series_id"))].append(r)
    rows=[]
    for sid,items in buckets.items():
        first=items[0]
        rows.append({
            "series_id":sid,
            "occurrence_count":len(items),
            "category":_clean(first.get("category")),
            "region":_clean(first.get("region")),
            "institution":_clean(first.get("institution")),
            "source_id":_clean(first.get("source_id")),
            "example_name":_clean(first.get("canonical_name")),
        })
    return sorted(rows,key=lambda x:(-x["occurrence_count"],x["series_id"]))


def _region_category_matrix(records: list[dict]) -> list[dict]:
    buckets: dict[tuple[str,str],list[dict]]=defaultdict(list)
    for r in records:
        buckets[(_clean(r.get("region")),_clean(r.get("category")))].append(r)
    rows=[]
    for (region,category),items in buckets.items():
        rows.append({
            "region":region,
            "category":category,
            "occurrence_count":len(items),
            "unique_series_count":len({_clean(x.get("series_id")) for x in items}),
            "unique_institution_count":len({_clean(x.get("institution")) for x in items}),
        })
    return sorted(rows,key=lambda x:(x["region"],-x["occurrence_count"],x["category"]))


def _source_readiness_for_records(records: list[dict], source_registry: dict) -> dict:
    sources={s.get("source_id"):s for s in source_registry.get("sources",[])}
    used_ids={r.get("source_id") for r in records if r.get("source_id")}
    status=Counter()
    missing=[]
    for sid in sorted(used_ids):
        source=sources.get(sid)
        if source is None:
            missing.append(sid)
            continue
        status[_clean(source.get("monitoring_readiness_status"))]+=1
    return {
        "unique_used_source_count":len(used_ids),
        "monitoring_readiness_status_counts":dict(sorted(status.items())),
        "source_ids_missing_from_source_registry":missing,
    }


def _focus_inventory(records: list[dict]) -> dict:
    """Return exact canonical records for bounded qualitative review.

    A record is included once if either its region or category is in the
    declared focus set. This is an audit projection only: it does not infer
    undercoverage and does not mutate or normalize the canonical record.
    """
    focus=[]
    for record in records:
        if record.get("region") in FOCUS_REGIONS or record.get("category") in FOCUS_CATEGORIES:
            focus.append(dict(record))
    return {
        "focus_regions":list(FOCUS_REGIONS),
        "focus_categories":list(FOCUS_CATEGORIES),
        "record_count":len(focus),
        "records":focus,
        "note":"Exact canonical-record projection for qualitative review only; inclusion is not an undercoverage finding or population quota.",
    }


def build_coverage_audit(registry: dict, source_registry: dict) -> dict:
    records=list(registry.get("records",[]))
    series=_series_summary(records)
    region=_summary(records,"region")
    category=_summary(records,"category")
    institution=_summary(records,"institution")
    occurrence_total=len(records)
    unique_series=len(series)
    unique_institutions=len({_clean(r.get("institution")) for r in records})
    unique_sources=len({r.get("source_id") for r in records if r.get("source_id")})

    category_occurrences=Counter(_clean(r.get("category")) for r in records)
    monetary_macro=(
        category_occurrences.get("MONETARY_FINANCIAL_POLICY",0)+
        category_occurrences.get("MACROECONOMIC_RELEASE",0)
    )

    region_series_counts={x["region"]:x["unique_series_count"] for x in region}
    region_institution_counts={x["region"]:x["unique_institution_count"] for x in region}

    return {
        "project":"WORLD SIGNALS",
        "dataset":"COVERAGE_BIAS_AUDIT",
        "version":"0.2",
        "canonical_registry_version":registry.get("version"),
        "canonical_reference_date":registry.get("reference_date"),
        "methodology":{
            "principle":"Occurrence counts are not treated as a proxy for coverage quality. Audit occurrence density together with distinct series, institutions and sources.",
            "quota_filling_prohibited":True,
            "machine_readability_is_not_importance":True,
            "series_identity_is_primary_unit_for_coverage_shape":True,
            "institution_diversity_is_secondary_unit":True,
            "focus_inventory_is_read_only_projection":True,
        },
        "totals":{
            "occurrence_count":occurrence_total,
            "unique_series_count":unique_series,
            "unique_institution_count":unique_institutions,
            "unique_source_count":unique_sources,
            "occurrences_per_series":round(occurrence_total/unique_series,2) if unique_series else None,
            "monetary_plus_macro_occurrence_count":monetary_macro,
            "monetary_plus_macro_occurrence_share":round(monetary_macro/occurrence_total,4) if occurrence_total else None,
        },
        "by_region":region,
        "by_category":category,
        "by_institution":institution,
        "region_category_matrix":_region_category_matrix(records),
        "high_frequency_series":series[:40],
        "source_readiness":_source_readiness_for_records(records,source_registry),
        "focus_inventory":_focus_inventory(records),
        "diagnostic_flags":{
            "regions_with_fewer_than_10_unique_series":sorted([k for k,v in region_series_counts.items() if v<10]),
            "regions_with_fewer_than_8_unique_institutions":sorted([k for k,v in region_institution_counts.items() if v<8]),
            "categories_with_fewer_than_5_unique_series":sorted([x["category"] for x in category if x["unique_series_count"]<5]),
            "note":"Threshold flags are prompts for qualitative review, not automatic undercoverage findings or population quotas."
        }
    }
