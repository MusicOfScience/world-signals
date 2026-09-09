from __future__ import annotations

from collections import Counter
from typing import Any


def _unique_map(rows: list[dict[str, Any]], key: str, label: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        value = row.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"{label} row missing {key}")
        if value in out:
            raise ValueError(f"duplicate {label} {key}: {value}")
        out[value] = row
    return out


def _analysis_live_input_ids(reviews: list[dict[str, Any]]) -> set[str]:
    used: set[str] = set()
    for review in reviews:
        live_inputs = review.get("live_inputs")
        if live_inputs is None:
            continue
        if not isinstance(live_inputs, list):
            raise ValueError("analysis live_inputs must be a list when present")
        for row in live_inputs:
            if not isinstance(row, dict):
                raise ValueError("analysis live input must be an object")
            observation_id = row.get("observation_id")
            if not isinstance(observation_id, str) or not observation_id:
                raise ValueError("analysis live input missing observation_id")
            used.add(observation_id)
    return used


def build_cross_layer_coverage_audit(
    registry: dict[str, Any],
    expectations: dict[str, Any],
    live_observations: dict[str, Any],
    analysis_reviews: dict[str, Any],
) -> dict[str, Any]:
    """Build a read-only cross-layer coverage and pressure diagnostic.

    The diagnostic compares layer shape without converting density into a score or
    granting any write, promotion or population authority. Canonical categories
    and Live domain tags remain separate taxonomies rather than being forced into
    an artificial one-to-one mapping.
    """

    canonical_rows = list(registry.get("records") or [])
    adapter_rows = list(expectations.get("adapters") or [])
    live_rows = list(live_observations.get("observations") or [])
    review_rows = list(analysis_reviews.get("reviews") or [])

    canonical_by_id = _unique_map(canonical_rows, "occurrence_id", "canonical")
    live_by_id = _unique_map(live_rows, "observation_id", "live")
    _unique_map(review_rows, "analysis_id", "analysis")

    monitor_occurrence_ids: set[str] = set()
    for adapter in adapter_rows:
        scope = adapter.get("canonical_occurrence_ids") or []
        if not isinstance(scope, list):
            raise ValueError("monitor canonical_occurrence_ids must be a list")
        for occurrence_id in scope:
            if occurrence_id not in canonical_by_id:
                raise ValueError(f"monitor references unknown canonical occurrence {occurrence_id}")
            monitor_occurrence_ids.add(occurrence_id)

    live_linked_ids: set[str] = set()
    linked_occurrences_by_live: dict[str, list[str]] = {}
    for observation in live_rows:
        observation_id = observation["observation_id"]
        links = observation.get("canonical_links") or []
        if not isinstance(links, list):
            raise ValueError(f"{observation_id}: canonical_links must be a list")
        resolved: list[str] = []
        for link in links:
            if not isinstance(link, dict):
                raise ValueError(f"{observation_id}: canonical link must be an object")
            occurrence_id = link.get("occurrence_id")
            if occurrence_id not in canonical_by_id:
                raise ValueError(f"{observation_id}: unknown canonical occurrence {occurrence_id}")
            resolved.append(occurrence_id)
        if resolved:
            live_linked_ids.add(observation_id)
            linked_occurrences_by_live[observation_id] = resolved

    review_by_occurrence: dict[str, list[dict[str, Any]]] = {}
    for review in review_rows:
        occurrence_id = review.get("canonical_occurrence_id")
        if occurrence_id not in canonical_by_id:
            raise ValueError(f"analysis references unknown canonical occurrence {occurrence_id}")
        review_by_occurrence.setdefault(str(occurrence_id), []).append(review)

    used_live_ids = _analysis_live_input_ids(review_rows)
    unknown_used = sorted(used_live_ids - set(live_by_id))
    if unknown_used:
        raise ValueError(f"analysis references unknown live observations: {unknown_used}")

    canonical_regions = sorted({row.get("region") for row in canonical_rows if row.get("region")})
    live_regions = sorted(
        {
            region
            for row in live_rows
            for region in (row.get("regions") or [])
            if isinstance(region, str) and region
        }
    )
    all_regions = sorted(set(canonical_regions) | set(live_regions))

    by_region: list[dict[str, Any]] = []
    for region in all_regions:
        canonical_region_rows = [row for row in canonical_rows if row.get("region") == region]
        canonical_region_ids = {row["occurrence_id"] for row in canonical_region_rows}
        monitor_region_ids = canonical_region_ids & monitor_occurrence_ids
        live_region_rows = [row for row in live_rows if region in (row.get("regions") or [])]
        linked_live_region_rows = [
            row
            for row in live_region_rows
            if row["observation_id"] in live_linked_ids
        ]
        analysis_region_rows = [
            review
            for review in review_rows
            if canonical_by_id[review["canonical_occurrence_id"]].get("region") == region
        ]
        by_region.append(
            {
                "region": region,
                "canonical_occurrence_count": len(canonical_region_rows),
                "canonical_unique_series_count": len(
                    {row.get("series_id") for row in canonical_region_rows if row.get("series_id")}
                ),
                "configured_monitor_occurrence_count": len(monitor_region_ids),
                "configured_monitor_unique_series_count": len(
                    {
                        canonical_by_id[occurrence_id].get("series_id")
                        for occurrence_id in monitor_region_ids
                        if canonical_by_id[occurrence_id].get("series_id")
                    }
                ),
                "live_observation_count": len(live_region_rows),
                "canonical_linked_live_observation_count": len(linked_live_region_rows),
                "analysis_review_count": len(analysis_region_rows),
                "analysis_with_live_input_count": sum(
                    1 for review in analysis_region_rows if review.get("live_inputs")
                ),
            }
        )

    canonical_categories = sorted({row.get("category") for row in canonical_rows if row.get("category")})
    by_category: list[dict[str, Any]] = []
    for category in canonical_categories:
        canonical_category_rows = [row for row in canonical_rows if row.get("category") == category]
        canonical_category_ids = {row["occurrence_id"] for row in canonical_category_rows}
        monitor_category_ids = canonical_category_ids & monitor_occurrence_ids
        analysis_category_rows = [
            review
            for review in review_rows
            if canonical_by_id[review["canonical_occurrence_id"]].get("category") == category
        ]
        by_category.append(
            {
                "category": category,
                "canonical_occurrence_count": len(canonical_category_rows),
                "canonical_unique_series_count": len(
                    {row.get("series_id") for row in canonical_category_rows if row.get("series_id")}
                ),
                "configured_monitor_occurrence_count": len(monitor_category_ids),
                "configured_monitor_unique_series_count": len(
                    {
                        canonical_by_id[occurrence_id].get("series_id")
                        for occurrence_id in monitor_category_ids
                        if canonical_by_id[occurrence_id].get("series_id")
                    }
                ),
                "analysis_review_count": len(analysis_category_rows),
                "analysis_with_live_input_count": sum(
                    1 for review in analysis_category_rows if review.get("live_inputs")
                ),
            }
        )

    live_domain_counts = Counter(
        tag
        for row in live_rows
        for tag in (row.get("domain_tags") or [])
        if isinstance(tag, str) and tag
    )
    live_by_domain_tag = [
        {"domain_tag": tag, "live_observation_count": count}
        for tag, count in sorted(live_domain_counts.items(), key=lambda item: (-item[1], item[0]))
    ]

    completed_with_analysis_unconsumed: list[dict[str, Any]] = []
    completed_without_analysis: list[dict[str, Any]] = []
    noncompleted_linked: list[dict[str, Any]] = []

    for observation_id, occurrence_ids in sorted(linked_occurrences_by_live.items()):
        if observation_id in used_live_ids:
            continue
        occurrence_rows = [canonical_by_id[occurrence_id] for occurrence_id in occurrence_ids]
        completed_ids = [
            row["occurrence_id"]
            for row in occurrence_rows
            if row.get("lifecycle_status") == "COMPLETED"
        ]
        noncompleted_ids = [
            row["occurrence_id"]
            for row in occurrence_rows
            if row.get("lifecycle_status") != "COMPLETED"
        ]
        if noncompleted_ids:
            noncompleted_linked.append(
                {
                    "observation_id": observation_id,
                    "canonical_occurrence_ids": occurrence_ids,
                    "noncompleted_occurrence_ids": noncompleted_ids,
                    "lifecycle_statuses": {
                        row["occurrence_id"]: row.get("lifecycle_status") for row in occurrence_rows
                    },
                }
            )
        for occurrence_id in completed_ids:
            item = {
                "observation_id": observation_id,
                "canonical_occurrence_id": occurrence_id,
                "relationship_types": sorted(
                    {
                        link.get("relationship")
                        for link in (live_by_id[observation_id].get("canonical_links") or [])
                        if isinstance(link, dict)
                        and link.get("occurrence_id") == occurrence_id
                        and link.get("relationship")
                    }
                ),
            }
            if occurrence_id in review_by_occurrence:
                item["analysis_ids"] = sorted(
                    review["analysis_id"] for review in review_by_occurrence[occurrence_id]
                )
                completed_with_analysis_unconsumed.append(item)
            else:
                completed_without_analysis.append(item)

    unlinked_live_ids = sorted(set(live_by_id) - live_linked_ids)

    region_by_name = {row["region"]: row for row in by_region}
    category_by_name = {row["category"]: row for row in by_category}

    diagnostic_prompts = {
        "regions_with_canonical_series_but_no_configured_monitor_scope": sorted(
            row["region"]
            for row in by_region
            if row["canonical_unique_series_count"] > 0
            and row["configured_monitor_occurrence_count"] == 0
        ),
        "regions_with_canonical_series_but_no_live_observation": sorted(
            row["region"]
            for row in by_region
            if row["canonical_unique_series_count"] > 0 and row["live_observation_count"] == 0
        ),
        "regions_with_live_observation_but_no_analysis_review": sorted(
            row["region"]
            for row in by_region
            if row["live_observation_count"] > 0 and row["analysis_review_count"] == 0
        ),
        "canonical_categories_without_configured_monitor_scope": sorted(
            row["category"]
            for row in by_category
            if row["canonical_unique_series_count"] > 0
            and row["configured_monitor_occurrence_count"] == 0
        ),
        "canonical_categories_without_analysis_review": sorted(
            row["category"]
            for row in by_category
            if row["canonical_unique_series_count"] > 0 and row["analysis_review_count"] == 0
        ),
        "note": (
            "These are qualitative review prompts only. Absence at a downstream layer does not imply "
            "that the layer should be populated, and counts are not quotas."
        ),
    }

    return {
        "project": "WORLD SIGNALS",
        "dataset": "CROSS_LAYER_COVERAGE_PRESSURE_AUDIT",
        "version": "0.1",
        "checkpoints": {
            "canonical_registry_version": registry.get("version"),
            "monitor_expectations_version": expectations.get("version"),
            "live_observations_version": live_observations.get("version"),
            "analysis_reviews_version": analysis_reviews.get("version"),
        },
        "methodology": {
            "read_only": True,
            "count_only_selection_prohibited": True,
            "quota_filling_prohibited": True,
            "canonical_categories_and_live_domain_tags_not_forced_into_one_taxonomy": True,
            "monitor_scope_is_explicit_occurrence_scope_only": True,
            "downstream_absence_is_review_prompt_not_population_authority": True,
            "automatic_canonical_commit": False,
            "automatic_monitor_route_creation": False,
            "automatic_live_population": False,
            "automatic_live_analysis_bridge_population": False,
            "automatic_analysis_population": False,
        },
        "totals": {
            "canonical_occurrence_count": len(canonical_rows),
            "canonical_unique_series_count": len(
                {row.get("series_id") for row in canonical_rows if row.get("series_id")}
            ),
            "configured_monitor_adapter_count": len(adapter_rows),
            "configured_monitor_scoped_occurrence_count": len(monitor_occurrence_ids),
            "configured_monitor_scoped_series_count": len(
                {
                    canonical_by_id[occurrence_id].get("series_id")
                    for occurrence_id in monitor_occurrence_ids
                    if canonical_by_id[occurrence_id].get("series_id")
                }
            ),
            "live_observation_count": len(live_rows),
            "canonical_linked_live_observation_count": len(live_linked_ids),
            "analysis_review_count": len(review_rows),
            "production_live_input_count": sum(
                len(review.get("live_inputs") or [])
                for review in review_rows
                if isinstance(review.get("live_inputs") or [], list)
            ),
            "production_revision_count": sum(
                1 for review in review_rows if review.get("revision_of_analysis_id")
            ),
        },
        "by_region": by_region,
        "by_canonical_category": by_category,
        "live_by_domain_tag": live_by_domain_tag,
        "bridge_frontier": {
            "used_live_observation_ids": sorted(used_live_ids),
            "completed_linked_with_existing_analysis_unconsumed": completed_with_analysis_unconsumed,
            "completed_linked_without_analysis_review": completed_without_analysis,
            "noncompleted_linked_unconsumed": noncompleted_linked,
            "unlinked_live_observation_ids": unlinked_live_ids,
            "factual_same_anchor_candidate_count": len(completed_with_analysis_unconsumed),
            "note": (
                "This frontier is descriptive. A completed same-anchor candidate still requires a fresh "
                "pressure audit and the Analysis live-input policy to permit another production link."
            ),
        },
        "diagnostic_prompts": diagnostic_prompts,
        "lookup": {
            "regions": region_by_name,
            "canonical_categories": category_by_name,
        },
    }
