from __future__ import annotations


def public_coverage_projection(audit: dict) -> dict:
    """Return a deliberately aggregate-only public view of the coverage audit.

    Coverage diagnostics are useful to readers, but the build should not expose the
    audit's focus inventory or operational source-readiness details as if they were
    part of the public event projection. This function keeps that boundary explicit.
    """

    totals = audit.get("totals") or {}
    methodology = audit.get("methodology") or {}
    diagnostic_flags = audit.get("diagnostic_flags") or {}

    region_fields = (
        "region",
        "occurrence_count",
        "unique_series_count",
        "unique_institution_count",
        "unique_source_count",
        "unique_category_count",
        "occurrences_per_series",
    )
    category_fields = (
        "category",
        "occurrence_count",
        "unique_series_count",
        "unique_institution_count",
        "unique_source_count",
        "occurrences_per_series",
    )
    frequency_fields = (
        "series_id",
        "occurrence_count",
        "region",
        "category",
        "institution",
    )

    def select(row: dict, fields: tuple[str, ...]) -> dict:
        return {field: row.get(field) for field in fields}

    return {
        "project": audit.get("project"),
        "dataset": "PUBLIC_COVERAGE_PROJECTION",
        "version": "0.1",
        "metadata": {
            "canonical_registry_version": audit.get("canonical_registry_version"),
            "canonical_reference_date": audit.get("canonical_reference_date"),
            "occurrence_count": totals.get("occurrence_count"),
            "unique_series_count": totals.get("unique_series_count"),
            "unique_institution_count": totals.get("unique_institution_count"),
            "unique_source_count": totals.get("unique_source_count"),
            "occurrences_per_series": totals.get("occurrences_per_series"),
            "monetary_plus_macro_occurrence_count": totals.get("monetary_plus_macro_occurrence_count"),
            "monetary_plus_macro_occurrence_share": totals.get("monetary_plus_macro_occurrence_share"),
            "projection_scope": "AGGREGATE_READ_ONLY_COVERAGE_DIAGNOSTIC",
            "canonical_mutation_authority": False,
            "population_quota_authority": False,
        },
        "methodology": {
            "principle": methodology.get("principle"),
            "quota_filling_prohibited": methodology.get("quota_filling_prohibited"),
            "machine_readability_is_not_importance": methodology.get("machine_readability_is_not_importance"),
            "series_identity_is_primary_unit_for_coverage_shape": methodology.get("series_identity_is_primary_unit_for_coverage_shape"),
            "institution_diversity_is_secondary_unit": methodology.get("institution_diversity_is_secondary_unit"),
        },
        "by_region": [select(row, region_fields) for row in audit.get("by_region", [])],
        "by_category": [select(row, category_fields) for row in audit.get("by_category", [])],
        "diagnostic_flags": {
            "regions_with_fewer_than_10_unique_series": list(diagnostic_flags.get("regions_with_fewer_than_10_unique_series", [])),
            "regions_with_fewer_than_8_unique_institutions": list(diagnostic_flags.get("regions_with_fewer_than_8_unique_institutions", [])),
            "categories_with_fewer_than_5_unique_series": list(diagnostic_flags.get("categories_with_fewer_than_5_unique_series", [])),
            "note": diagnostic_flags.get("note"),
        },
        "high_frequency_series": [
            select(row, frequency_fields) for row in audit.get("high_frequency_series", [])[:12]
        ],
    }
