"""One fail-closed top-level Analysis publication contract.

Nested legacy analytical sections keep their established public semantics.
New internal structures must be classified here before publication can build.
"""
from copy import deepcopy

PUBLIC_FIELDS = (
    "analysis_id", "review_state", "review_phase", "analysis_as_of_utc",
    "canonical_occurrence_id", "canonical_series_id", "canonical_event_type",
    "canonical_institution", "canonical_release_utc", "scope", "what_happened",
    "what_was_expected", "what_surprised", "what_moved", "what_appears_connected",
    "what_may_be_noise", "alternative_explanations", "second_order_effects",
    "falsifiers", "analytical_conclusion", "canonical_mutation_prohibited",
    "google_calendar_write",
)
INTERNAL_FIELDS = (
    "official_projection_review", "assumption_audit", "internal_dependency_map",
    "internal_evidence_manifest", "internal_review_notes", "candidate_dispositions",
    "live_inputs", "revision_of_analysis_id", "analysis_revision_kind",
    "analysis_revision_reason",
)
FIELD_CLASSIFICATIONS = {
    **dict.fromkeys(PUBLIC_FIELDS, "PUBLIC"),
    **dict.fromkeys(INTERNAL_FIELDS, "INTERNAL_ONLY"),
}


def publication_errors(review):
    return [
        "UNCLASSIFIED_ANALYSIS_PUBLICATION_FIELD: " + field
        for field in sorted(set(review) - FIELD_CLASSIFICATIONS.keys())
    ]


def public_review_fields(review):
    errors = publication_errors(review)
    if errors:
        raise ValueError("; ".join(errors))
    return {field: deepcopy(review[field]) for field in PUBLIC_FIELDS if field in review}
