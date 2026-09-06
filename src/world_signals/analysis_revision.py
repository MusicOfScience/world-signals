from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class AnalysisRevisionValidationReport:
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


REVISION_FIELDS = (
    "revision_of_analysis_id",
    "analysis_revision_kind",
    "analysis_revision_reason",
)


def _version_tuple(raw: Any) -> tuple[int, ...] | None:
    try:
        return tuple(int(part) for part in str(raw).split("."))
    except (TypeError, ValueError):
        return None


def _exact_utc(raw: Any) -> datetime | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (TypeError, ValueError, AttributeError):
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        return None
    return parsed.astimezone(timezone.utc)


def _has_revision_metadata(review: dict[str, Any]) -> bool:
    return any(
        field in review and review.get(field) not in {None, ""}
        for field in REVISION_FIELDS
    )


def _live_input_ids(review: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for row in review.get("live_inputs") or []:
        if isinstance(row, dict):
            observation_id = row.get("observation_id")
            if isinstance(observation_id, str) and observation_id.strip():
                ids.add(observation_id)
    return ids


def production_analysis_revision_count(reviews_dataset: dict[str, Any]) -> int:
    """Count populated revision rows fail-closed.

    Any row carrying non-empty revision metadata counts as a production revision,
    even when the shape is invalid, so the closed gate cannot be bypassed by
    malformed metadata.
    """

    return sum(
        1
        for review in reviews_dataset.get("reviews", [])
        if isinstance(review, dict) and _has_revision_metadata(review)
    )


def analysis_revision_heads(reviews_dataset: dict[str, Any]) -> tuple[str, ...]:
    """Return derived lineage heads without selecting a public 'latest' view."""

    ids = {
        review.get("analysis_id")
        for review in reviews_dataset.get("reviews", [])
        if isinstance(review, dict) and review.get("analysis_id")
    }
    parents = {
        review.get("revision_of_analysis_id")
        for review in reviews_dataset.get("reviews", [])
        if isinstance(review, dict)
        and isinstance(review.get("revision_of_analysis_id"), str)
        and review.get("revision_of_analysis_id")
    }
    return tuple(sorted(ids.difference(parents)))


def validate_analysis_revisions(
    analysis_schema: dict[str, Any],
    reviews_dataset: dict[str, Any],
) -> AnalysisRevisionValidationReport:
    """Validate prospective Analysis revision lineage.

    BA introduces the grammar with production revisions closed. Historical
    pre-BA schema descendants remain valid without an analysis_revision_policy;
    schema v0.7 and later must carry the contract.
    """

    errors: list[str] = []
    schema_version = _version_tuple(analysis_schema.get("version"))
    policy = analysis_schema.get("analysis_revision_policy")

    if not isinstance(policy, dict):
        if schema_version is not None and schema_version < (0, 7):
            return AnalysisRevisionValidationReport(())
        return AnalysisRevisionValidationReport(
            ("Analysis schema v0.7+ must define analysis_revision_policy",)
        )

    allowed_modes = {
        "FOUNDATION_ONLY_NO_PRODUCTION_REVISIONS",
        "CONTROLLED_REVISION_LINEAGE",
    }
    mode = policy.get("mode")
    if mode not in allowed_modes:
        errors.append(f"Analysis revision policy has unreviewed mode {mode!r}")

    required_flags = {
        "parent_snapshot_must_remain_present": True,
        "same_canonical_occurrence_required": True,
        "analysis_as_of_must_strictly_advance": True,
        "cycles_prohibited": True,
        "branching_prohibited_in_first_controlled_mode": True,
        "new_live_evidence_revision_requires_novel_live_input": True,
        "live_observation_does_not_automatically_create_revision": True,
        "live_revision_and_analysis_revision_are_distinct": True,
        "upstream_canonical_mutation_allowed": False,
        "upstream_live_mutation_allowed": False,
        "upstream_monitor_mutation_allowed": False,
        "google_calendar_write_allowed": False,
        "automatic_latest_analysis_selection_allowed": False,
        "public_revision_head_collapse_allowed": False,
        "future_production_revision_requires_pressure_audit": True,
    }
    for key, expected in required_flags.items():
        if policy.get(key) != expected:
            errors.append(
                f"Analysis revision policy requires {key}={expected!r}"
            )

    if policy.get("public_revision_metadata_projection_allowed") is not False:
        errors.append("Analysis revision metadata public projection must remain closed in BA")

    required_fields = set(policy.get("required_revision_fields") or [])
    allowed_fields = set(policy.get("allowed_revision_fields") or [])
    expected_fields = set(REVISION_FIELDS)
    if required_fields != expected_fields:
        errors.append(
            "Analysis revision required fields must be exactly revision_of_analysis_id, analysis_revision_kind, analysis_revision_reason"
        )
    if allowed_fields != expected_fields:
        errors.append(
            "Analysis revision allowed fields must be exactly revision_of_analysis_id, analysis_revision_kind, analysis_revision_reason"
        )

    allowed_kinds = set(policy.get("allowed_revision_kinds") or [])
    expected_kinds = {
        "FACTUAL_CORRECTION",
        "NEW_EVIDENCE",
        "NEW_LIVE_EVIDENCE",
        "METHODOLOGICAL_REASSESSMENT",
        "CAUSAL_REASSESSMENT",
        "SCOPE_OR_FRAMING_UPDATE",
    }
    if allowed_kinds != expected_kinds:
        errors.append("Analysis revision kind vocabulary does not match reviewed BA contract")

    production_allowed = policy.get("production_analysis_revisions_allowed")
    if production_allowed not in {True, False}:
        errors.append("production_analysis_revisions_allowed must be explicit boolean")
        production_allowed = False

    max_revisions: int | None = None
    max_children_per_parent: int | None = None
    if mode == "FOUNDATION_ONLY_NO_PRODUCTION_REVISIONS":
        if production_allowed is not False:
            errors.append(
                "BA foundation mode requires production_analysis_revisions_allowed=false"
            )
    elif mode == "CONTROLLED_REVISION_LINEAGE":
        if production_allowed is not True:
            errors.append(
                "controlled revision mode requires production_analysis_revisions_allowed=true"
            )
        raw_max = policy.get("maximum_production_analysis_revisions")
        if not isinstance(raw_max, int) or raw_max < 1:
            errors.append(
                "controlled revision mode requires positive maximum_production_analysis_revisions"
            )
        else:
            max_revisions = raw_max
        raw_children = policy.get("maximum_children_per_revision_parent")
        if not isinstance(raw_children, int) or raw_children != 1:
            errors.append(
                "first controlled revision mode requires maximum_children_per_revision_parent=1"
            )
        else:
            max_children_per_parent = raw_children

    populated = production_analysis_revision_count(reviews_dataset)
    if production_allowed is False and populated:
        errors.append(
            "BA production revision gate is closed: Analysis reviews may not populate revision lineage"
        )
        return AnalysisRevisionValidationReport(tuple(errors))
    if max_revisions is not None and populated > max_revisions:
        errors.append(
            f"production Analysis revision population {populated} exceeds reviewed maximum {max_revisions}"
        )

    reviews = [
        row for row in reviews_dataset.get("reviews", [])
        if isinstance(row, dict)
    ]
    by_id = {
        row.get("analysis_id"): row
        for row in reviews
        if isinstance(row.get("analysis_id"), str) and row.get("analysis_id")
    }
    children = Counter()

    for review in reviews:
        analysis_id = review.get("analysis_id") or "<missing-analysis-id>"
        metadata_present = _has_revision_metadata(review)
        parent_id = review.get("revision_of_analysis_id")

        if not metadata_present:
            continue

        if not isinstance(parent_id, str) or not parent_id.strip():
            errors.append(
                f"{analysis_id}: revision metadata requires revision_of_analysis_id"
            )
            continue
        if parent_id == analysis_id:
            errors.append(f"{analysis_id}: Analysis revision cannot reference itself")
            continue
        parent = by_id.get(parent_id)
        if parent is None:
            errors.append(f"{analysis_id}: unknown revision parent {parent_id}")
            continue

        children[parent_id] += 1

        kind = review.get("analysis_revision_kind")
        if kind not in allowed_kinds:
            errors.append(f"{analysis_id}: invalid analysis_revision_kind {kind!r}")
        reason = review.get("analysis_revision_reason")
        if not isinstance(reason, str) or not reason.strip():
            errors.append(f"{analysis_id}: analysis_revision_reason is required")

        if (
            policy.get("same_canonical_occurrence_required") is True
            and review.get("canonical_occurrence_id") != parent.get("canonical_occurrence_id")
        ):
            errors.append(
                f"{analysis_id}: revision must preserve parent canonical_occurrence_id"
            )

        if policy.get("analysis_as_of_must_strictly_advance") is True:
            parent_as_of = _exact_utc(parent.get("analysis_as_of_utc"))
            child_as_of = _exact_utc(review.get("analysis_as_of_utc"))
            if parent_as_of is None or child_as_of is None:
                errors.append(
                    f"{analysis_id}: revision lineage requires exact UTC analysis_as_of_utc on parent and child"
                )
            elif child_as_of <= parent_as_of:
                errors.append(
                    f"{analysis_id}: revision analysis_as_of_utc must strictly advance beyond parent"
                )

        if (
            kind == "NEW_LIVE_EVIDENCE"
            and policy.get("new_live_evidence_revision_requires_novel_live_input") is True
        ):
            novel = _live_input_ids(review).difference(_live_input_ids(parent))
            if not novel:
                errors.append(
                    f"{analysis_id}: NEW_LIVE_EVIDENCE revision requires at least one novel live observation_id"
                )

    if max_children_per_parent is not None:
        for parent_id, count in children.items():
            if count > max_children_per_parent:
                errors.append(
                    f"{parent_id}: revision lineage branches to {count} children; first controlled mode permits one"
                )

    if policy.get("cycles_prohibited") is True:
        for start_id, review in by_id.items():
            seen: set[str] = set()
            current = review
            while True:
                parent_id = current.get("revision_of_analysis_id")
                if not isinstance(parent_id, str) or not parent_id:
                    break
                if parent_id in seen or parent_id == start_id:
                    errors.append(f"{start_id}: Analysis revision lineage cycle detected")
                    break
                seen.add(parent_id)
                parent = by_id.get(parent_id)
                if parent is None:
                    break
                current = parent

    return AnalysisRevisionValidationReport(tuple(errors))


def public_review_without_revision_metadata(
    analysis_schema: dict[str, Any], review: dict[str, Any]
) -> dict[str, Any]:
    """Return a public-safe Analysis review under the BA metadata gate."""

    public_row = deepcopy(review)
    policy = analysis_schema.get("analysis_revision_policy") or {}
    if policy.get("public_revision_metadata_projection_allowed") is not True:
        for field in REVISION_FIELDS:
            public_row.pop(field, None)
    return public_row
