from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


CANDIDATE_READINESS_STATUSES = {
    "PILOT_RESEARCH_VALIDATED_AUTOMATION_ROUTE_CANDIDATE",
    "ENDPOINT_TEST_PRIORITY",
    "PILOT_VALIDATED_NO_AUTO_COMMIT",
    "PILOT_RESEARCH_VALIDATED_AUTOMATION_RIGHTS_PENDING",
}


def _count(values: list[Any]) -> dict[str, int]:
    counts = Counter(str(value) if value not in (None, "") else "NOT_RECORDED_IN_REGISTRY" for value in values)
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _scope_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "occurrence_count": len(records),
        "unique_series_count": len({row.get("series_id") for row in records if row.get("series_id")}),
        "unique_institution_count": len({row.get("institution") for row in records if row.get("institution")}),
        "unique_region_count": len({row.get("region") for row in records if row.get("region")}),
        "unique_category_count": len({row.get("category") for row in records if row.get("category")}),
    }


def build_monitor_coverage_audit(
    registry: dict[str, Any],
    sources: dict[str, Any],
    expectations: dict[str, Any],
) -> dict[str, Any]:
    """Build a read-only audit of configured Source/Change Monitor scope.

    This is deliberately not a monitor-completeness score. Configured routes are
    compared with canonical breadth to expose concentration and review prompts,
    while source governance remains the authority for whether a future route is
    actually viable.
    """

    records = registry.get("records", [])
    occurrence_map = {row.get("occurrence_id"): row for row in records}
    if len(occurrence_map) != len(records):
        raise ValueError("canonical occurrence ids must be unique")

    source_records = sources.get("sources", [])
    source_map = {row.get("source_id"): row for row in source_records}
    if len(source_map) != len(source_records):
        raise ValueError("source ids must be unique")

    adapters = expectations.get("adapters", [])
    adapter_ids = [row.get("adapter_id") for row in adapters]
    if any(not adapter_id for adapter_id in adapter_ids):
        raise ValueError("configured monitor adapter missing adapter_id")
    if len(set(adapter_ids)) != len(adapter_ids):
        raise ValueError("configured monitor adapter ids must be unique")

    scoped_occurrence_ids: list[str] = []
    adapter_inventory: list[dict[str, Any]] = []
    configured_source_ids: set[str] = set()

    for adapter in adapters:
        adapter_id = adapter["adapter_id"]
        source_id = adapter.get("source_id")
        if not source_id or source_id not in source_map:
            raise ValueError(f"{adapter_id}: configured source id is absent from source registry")
        configured_source_ids.add(source_id)

        scope_ids = adapter.get("canonical_occurrence_ids", [])
        if not isinstance(scope_ids, list):
            raise ValueError(f"{adapter_id}: canonical_occurrence_ids must be a list")
        if len(scope_ids) != len(set(scope_ids)):
            raise ValueError(f"{adapter_id}: canonical occurrence scope contains duplicates")

        resolved: list[dict[str, Any]] = []
        for occurrence_id in scope_ids:
            if occurrence_id not in occurrence_map:
                raise ValueError(f"{adapter_id}: unknown canonical occurrence id {occurrence_id}")
            resolved.append(occurrence_map[occurrence_id])
            scoped_occurrence_ids.append(occurrence_id)

        source = source_map[source_id]
        adapter_inventory.append(
            {
                "adapter_id": adapter_id,
                "source_id": source_id,
                "source_institution": source.get("institution"),
                "monitor_role": adapter.get("monitor_role"),
                "cadence": adapter.get("cadence"),
                "explicit_canonical_occurrence_ids": list(scope_ids),
                "scope": _scope_summary(resolved),
                "regions": sorted({row.get("region") for row in resolved if row.get("region")}),
                "categories": sorted({row.get("category") for row in resolved if row.get("category")}),
                "series_ids": sorted({row.get("series_id") for row in resolved if row.get("series_id")}),
                "monitoring_readiness_status": source.get("monitoring_readiness_status"),
                "automated_monitoring_use": source.get("automated_monitoring_use"),
                "verification_mode": source.get("verification_mode"),
                "automatic_commit_allowed": False,
            }
        )

    unique_scoped_ids = sorted(set(scoped_occurrence_ids))
    scoped_records = [occurrence_map[occurrence_id] for occurrence_id in unique_scoped_ids]

    canonical_regions = sorted({row.get("region") for row in records if row.get("region")})
    canonical_categories = sorted({row.get("category") for row in records if row.get("category")})
    monitored_regions = sorted({row.get("region") for row in scoped_records if row.get("region")})
    monitored_categories = sorted({row.get("category") for row in scoped_records if row.get("category")})

    by_region = []
    for region in canonical_regions:
        canonical_rows = [row for row in records if row.get("region") == region]
        monitored_rows = [row for row in scoped_records if row.get("region") == region]
        by_region.append(
            {
                "region": region,
                "canonical_unique_series_count": len({row.get("series_id") for row in canonical_rows if row.get("series_id")}),
                "configured_monitor_occurrence_count": len(monitored_rows),
                "configured_monitor_unique_series_count": len({row.get("series_id") for row in monitored_rows if row.get("series_id")}),
                "configured_monitor_unique_institution_count": len({row.get("institution") for row in monitored_rows if row.get("institution")}),
            }
        )

    by_category = []
    for category in canonical_categories:
        canonical_rows = [row for row in records if row.get("category") == category]
        monitored_rows = [row for row in scoped_records if row.get("category") == category]
        by_category.append(
            {
                "category": category,
                "canonical_unique_series_count": len({row.get("series_id") for row in canonical_rows if row.get("series_id")}),
                "configured_monitor_occurrence_count": len(monitored_rows),
                "configured_monitor_unique_series_count": len({row.get("series_id") for row in monitored_rows if row.get("series_id")}),
                "configured_monitor_unique_institution_count": len({row.get("institution") for row in monitored_rows if row.get("institution")}),
            }
        )

    canonical_uses_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        source_id = row.get("source_id")
        if source_id:
            canonical_uses_by_source[source_id].append(row)

    candidate_sources = []
    unbound_candidate_sources = []
    for source in source_records:
        status = source.get("monitoring_readiness_status")
        if status not in CANDIDATE_READINESS_STATUSES:
            continue
        source_id = source.get("source_id")
        canonical_uses = canonical_uses_by_source.get(source_id, [])
        candidate = {
            "source_id": source_id,
            "institution": source.get("institution"),
            "jurisdiction": source.get("jurisdiction"),
            "domain": source.get("domain"),
            "monitoring_readiness_status": status,
            "automated_monitoring_use": source.get("automated_monitoring_use"),
            "verification_mode": source.get("verification_mode"),
            "already_configured_monitor_source": source_id in configured_source_ids,
            "canonical_occurrence_count": len(canonical_uses),
            "regions": sorted({row.get("region") for row in canonical_uses if row.get("region")}),
            "categories": sorted({row.get("category") for row in canonical_uses if row.get("category")}),
            "series_ids": sorted({row.get("series_id") for row in canonical_uses if row.get("series_id")}),
        }
        if canonical_uses:
            candidate_sources.append(candidate)
        else:
            candidate["candidate_class"] = "UNBOUND_SOURCE_REGISTRY_HOLDING_NOT_MONITOR_COVERAGE"
            unbound_candidate_sources.append(candidate)

    candidate_sources.sort(key=lambda row: (row["monitoring_readiness_status"], row.get("source_id") or ""))
    unbound_candidate_sources.sort(key=lambda row: (row["monitoring_readiness_status"], row.get("source_id") or ""))

    configured_sources = [source_map[source_id] for source_id in sorted(configured_source_ids)]

    return {
        "project": "WORLD SIGNALS",
        "dataset": "MONITOR_COVERAGE_AUDIT",
        "version": "0.1",
        "canonical_registry_version": registry.get("version"),
        "source_registry_version": sources.get("version"),
        "monitor_expectations_version": expectations.get("version"),
        "methodology": {
            "configured_scope_is_not_monitor_completeness": True,
            "occurrence_density_is_not_route_diversity": True,
            "missing_region_or_category_is_review_prompt_not_quota": True,
            "source_readiness_and_rights_govern_route_viability": True,
            "canonical_source_dependency_is_not_automatic_monitor_permission": True,
            "explicit_occurrence_scope_only_no_series_inference": True,
            "automatic_canonical_commit": False,
            "automatic_adapter_enablement": False,
        },
        "totals": {
            "configured_adapter_count": len(adapters),
            "unique_monitor_source_count": len(configured_source_ids),
            "scoped_occurrence_count": len(unique_scoped_ids),
            "scoped_series_count": len({row.get("series_id") for row in scoped_records if row.get("series_id")}),
            "scoped_institution_count": len({row.get("institution") for row in scoped_records if row.get("institution")}),
            "scoped_region_count": len(monitored_regions),
            "scoped_category_count": len(monitored_categories),
        },
        "configured_source_readiness": {
            "monitoring_readiness_status_counts": _count([row.get("monitoring_readiness_status") for row in configured_sources]),
            "automated_monitoring_use_counts": _count([row.get("automated_monitoring_use") for row in configured_sources]),
            "verification_mode_counts": _count([row.get("verification_mode") for row in configured_sources]),
        },
        "diagnostic_prompts": {
            "canonical_regions_without_configured_monitor_scope": sorted(set(canonical_regions) - set(monitored_regions)),
            "canonical_categories_without_configured_monitor_scope": sorted(set(canonical_categories) - set(monitored_categories)),
            "note": "Absence from configured monitor scope is a qualitative review prompt, not evidence that a route should be added.",
        },
        "by_region": by_region,
        "by_category": by_category,
        "adapter_inventory": sorted(adapter_inventory, key=lambda row: row["adapter_id"]),
        "candidate_sources_with_canonical_dependencies": candidate_sources,
        "candidate_sources_without_canonical_dependencies": unbound_candidate_sources,
    }
