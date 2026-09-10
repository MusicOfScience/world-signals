from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


CORRECTED_STATES = frozenset({"CORRECTED", "RETRACTED"})
CONFLICT_STATE = "CONFLICTING_REPORTS"


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


def _provider_identity(raw: Any) -> str | None:
    if not isinstance(raw, str):
        return None
    normalised = raw.strip().casefold()
    return normalised or None


def validate_correction_conflict_contract(
    schema: dict[str, Any],
    evidence_by_id: dict[str, dict[str, Any]],
    observations: list[dict[str, Any]],
) -> tuple[str, ...]:
    """Validate reviewed Live correction/retraction/conflict semantics.

    CM intentionally validates structure rather than adjudicating competing claims.
    A conflicting observation must preserve source plurality and describe the
    disagreement; a correction/retraction must preserve its prior Live target,
    correction evidence and temporal ordering.
    """

    errors: list[str] = []
    policy = schema.get("correction_conflict_policy")
    if not isinstance(policy, dict):
        return ("Live Intelligence schema must define correction_conflict_policy",)

    required_policy = {
        "mode": "FOUNDATION_CONTRACT_NO_PRODUCTION_SPECIMEN",
        "conflict_state": CONFLICT_STATE,
        "conflict_description_field": "conflict_description",
        "conflict_description_required": True,
        "conflict_description_prohibited_outside_conflict_state": True,
        "minimum_unique_conflict_evidence_refs": 2,
        "minimum_distinct_conflict_providers": 2,
        "provider_identity_normalisation": "STRIP_CASEFOLD",
        "conflict_requires_winner_selection": False,
        "conflict_requires_synthetic_consensus": False,
        "corrected_or_retracted_requires_revision_reference": True,
        "corrected_or_retracted_requires_correction_evidence": True,
        "corrected_or_retracted_observed_at_must_follow_target": True,
        "external_data_revision_requires_prior_live_observation": False,
    }
    for key, expected in required_policy.items():
        if policy.get(key) != expected:
            errors.append(
                f"Live correction/conflict policy requires {key}={expected!r}"
            )

    policy_states = policy.get("corrected_or_retracted_states")
    if not isinstance(policy_states, list) or set(policy_states) != set(CORRECTED_STATES):
        errors.append(
            "Live correction/conflict policy corrected_or_retracted_states must be exactly CORRECTED and RETRACTED"
        )

    observations_by_id = {
        row.get("observation_id"): row
        for row in observations
        if isinstance(row, dict) and row.get("observation_id")
    }

    for row in observations:
        if not isinstance(row, dict):
            continue
        observation_id = row.get("observation_id") or "<missing-observation-id>"
        verification_state = row.get("verification_state")
        evidence_refs = row.get("evidence_refs")
        refs = evidence_refs if isinstance(evidence_refs, list) else []
        revision_ref = row.get("revision_of_observation_id")

        if verification_state in CORRECTED_STATES:
            if not revision_ref:
                errors.append(
                    f"{observation_id}: corrected/retracted live observation requires revision reference"
                )
            correction_evidence = [
                evidence_by_id[ref]
                for ref in refs
                if ref in evidence_by_id
                and "CORRECTION_OR_REVISION" in (evidence_by_id[ref].get("roles") or [])
            ]
            if not correction_evidence:
                errors.append(
                    f"{observation_id}: corrected/retracted live observation requires evidence with CORRECTION_OR_REVISION role"
                )

            if revision_ref in observations_by_id:
                current_observed_at = _exact_utc(row.get("observed_at_utc"))
                target_observed_at = _exact_utc(
                    observations_by_id[revision_ref].get("observed_at_utc")
                )
                if (
                    current_observed_at is not None
                    and target_observed_at is not None
                    and current_observed_at <= target_observed_at
                ):
                    errors.append(
                        f"{observation_id}: corrected/retracted observation must be observed strictly later than revision target"
                    )

        conflict_description = row.get("conflict_description")
        if verification_state == CONFLICT_STATE:
            if not isinstance(conflict_description, str) or not conflict_description.strip():
                errors.append(
                    f"{observation_id}: CONFLICTING_REPORTS requires non-empty conflict_description"
                )

            unique_refs = {ref for ref in refs if ref in evidence_by_id}
            if len(unique_refs) < 2:
                errors.append(
                    f"{observation_id}: CONFLICTING_REPORTS requires at least two unique evidence records"
                )

            provider_ids = {
                provider_id
                for ref in unique_refs
                for provider_id in [_provider_identity(evidence_by_id[ref].get("provider"))]
                if provider_id is not None
            }
            if len(provider_ids) < 2:
                errors.append(
                    f"{observation_id}: CONFLICTING_REPORTS requires evidence from at least two distinct providers"
                )
        elif "conflict_description" in row:
            errors.append(
                f"{observation_id}: conflict_description is only allowed for CONFLICTING_REPORTS"
            )

    return tuple(errors)
