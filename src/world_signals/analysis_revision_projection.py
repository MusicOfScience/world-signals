from __future__ import annotations

from typing import Any

from world_signals.analysis import public_analysis_projection
from world_signals.analysis_revision import (
    public_review_without_revision_metadata,
    validate_analysis_revisions,
)


def public_analysis_projection_with_revision_contract(
    analysis_schema: dict[str, Any],
    evidence_registry: dict[str, Any],
    reviews_dataset: dict[str, Any],
    canonical_registry: dict[str, Any],
) -> dict[str, Any]:
    """Build the public Analysis projection while enforcing revision-lineage gates.

    BA keeps revision metadata and derived-head semantics out of the public surface.
    The core Analysis projection remains reusable; this wrapper is the governed
    browser-publication boundary once the revision contract exists.
    """

    revision_report = validate_analysis_revisions(analysis_schema, reviews_dataset)
    if not revision_report.ok:
        raise ValueError(
            "analysis revision validation failed: " + "; ".join(revision_report.errors)
        )

    projection = public_analysis_projection(
        analysis_schema,
        evidence_registry,
        reviews_dataset,
        canonical_registry,
    )
    projection["reviews"] = [
        public_review_without_revision_metadata(analysis_schema, row)
        for row in projection.get("reviews", [])
    ]
    metadata = projection.setdefault("metadata", {})
    policy = analysis_schema.get("analysis_revision_policy") or {}
    metadata["analysis_revision_contract_present"] = isinstance(
        analysis_schema.get("analysis_revision_policy"), dict
    )
    metadata["public_revision_metadata_projection_allowed"] = bool(
        policy.get("public_revision_metadata_projection_allowed") is True
    )
    metadata["automatic_latest_analysis_selection_allowed"] = bool(
        policy.get("automatic_latest_analysis_selection_allowed") is True
    )
    metadata["derived_revision_head_projection_allowed"] = bool(
        policy.get("public_revision_head_collapse_allowed") is True
    )
    return projection
