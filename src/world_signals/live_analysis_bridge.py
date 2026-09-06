from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class LiveAnalysisBridgeValidationReport:
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


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


def production_live_input_count(reviews_dataset: dict[str, Any]) -> int:
    total = 0
    for review in reviews_dataset.get("reviews", []):
        live_inputs = review.get("live_inputs")
        if isinstance(live_inputs, list):
            total += len(live_inputs)
        elif live_inputs is not None:
            # Invalid non-list values still count as a populated production field
            # so a closed gate fails closed before shape validation can be bypassed.
            total += 1
    return total


def validate_live_analysis_bridge(
    analysis_schema: dict[str, Any],
    reviews_dataset: dict[str, Any],
    live_observations_dataset: dict[str, Any],
) -> LiveAnalysisBridgeValidationReport:
    """Validate the prospective Live Intelligence -> Analysis input boundary.

    AY deliberately supports a schema-level contract before production links are
    opened. When production_live_inputs_allowed is false, any populated
    ``live_inputs`` field fails closed. Tests may copy the schema and explicitly
    open that gate to exercise the prospective referential/time semantics without
    changing production data.
    """

    errors: list[str] = []
    policy = analysis_schema.get("live_input_policy")
    if not isinstance(policy, dict):
        return LiveAnalysisBridgeValidationReport(
            ("Analysis schema must define live_input_policy",)
        )

    required_policy_values = {
        "mode": "FOUNDATION_ONLY_NO_PRODUCTION_LINKS",
        "identity_selector": "observation_id",
        "story_id_selector_allowed": False,
        "latest_selector_allowed": False,
        "automatic_story_expansion_allowed": False,
        "transitive_live_evidence_migration_allowed": False,
        "upstream_live_mutation_allowed": False,
        "one_live_observation_may_support_multiple_analyses": True,
        "multiple_story_snapshots_require_explicit_observation_ids": True,
        "analysis_as_of_must_not_predate_live_observed_at": True,
        "future_production_population_requires_pressure_audit": True,
    }
    for key, expected in required_policy_values.items():
        if policy.get(key) != expected:
            errors.append(
                f"Analysis live-input policy requires {key}={expected!r}"
            )

    if policy.get("public_live_input_projection_allowed") is not False:
        errors.append("AY must keep public Live input projection closed")

    production_allowed = policy.get("production_live_inputs_allowed")
    if production_allowed not in {True, False}:
        errors.append("production_live_inputs_allowed must be explicit boolean")
        production_allowed = False

    required_input_fields = set(policy.get("required_input_fields") or [])
    allowed_input_fields = set(policy.get("allowed_input_fields") or [])
    expected_fields = {"observation_id", "roles", "analysis_sections"}
    if required_input_fields != expected_fields:
        errors.append(
            "AY live-input required fields must be exactly observation_id, roles, analysis_sections"
        )
    if allowed_input_fields != expected_fields:
        errors.append(
            "AY live-input allowed fields must be exactly observation_id, roles, analysis_sections"
        )

    allowed_roles = set(policy.get("allowed_roles") or [])
    expected_roles = {
        "FACTUAL_INPUT",
        "CONTEXT_OR_ALTERNATIVE_INPUT",
        "SECOND_ORDER_INPUT",
        "MARKET_OBSERVATION_INPUT",
    }
    if allowed_roles != expected_roles:
        errors.append("AY live-input role vocabulary does not match reviewed contract")

    allowed_sections = set(analysis_schema.get("required_review_sections") or [])
    observations = live_observations_dataset.get("observations") or []
    observation_by_id = {
        row.get("observation_id"): row
        for row in observations
        if row.get("observation_id")
    }

    populated_count = production_live_input_count(reviews_dataset)
    if production_allowed is False and populated_count:
        errors.append(
            "AY production gate is closed: Analysis reviews may not populate live_inputs"
        )
        return LiveAnalysisBridgeValidationReport(tuple(errors))

    for review in reviews_dataset.get("reviews", []):
        analysis_id = review.get("analysis_id") or "<missing-analysis-id>"
        if "live_inputs" not in review:
            continue
        live_inputs = review.get("live_inputs")
        if not isinstance(live_inputs, list):
            errors.append(f"{analysis_id}: live_inputs must be a list")
            continue

        seen_in_review: set[str] = set()
        analysis_as_of = _exact_utc(review.get("analysis_as_of_utc"))
        if live_inputs and analysis_as_of is None:
            errors.append(
                f"{analysis_id}: live-input use requires exact UTC analysis_as_of_utc"
            )

        for index, live_input in enumerate(live_inputs):
            label = f"{analysis_id}/live_inputs[{index}]"
            if not isinstance(live_input, dict):
                errors.append(f"{label}: live input must be an object")
                continue

            keys = set(live_input)
            missing = sorted(required_input_fields - keys)
            unexpected = sorted(keys - allowed_input_fields)
            if missing:
                errors.append(f"{label}: missing fields {missing}")
            if unexpected:
                errors.append(f"{label}: unexpected fields {unexpected}")

            observation_id = live_input.get("observation_id")
            if not isinstance(observation_id, str) or not observation_id.strip():
                errors.append(f"{label}: observation_id required")
                continue
            if observation_id in seen_in_review:
                errors.append(
                    f"{analysis_id}: duplicate live observation reference {observation_id}"
                )
            seen_in_review.add(observation_id)

            observation = observation_by_id.get(observation_id)
            if observation is None:
                errors.append(f"{label}: unknown Live observation_id {observation_id}")

            roles = live_input.get("roles")
            if (
                not isinstance(roles, list)
                or not roles
                or len(set(roles)) != len(roles)
                or any(role not in allowed_roles for role in roles)
            ):
                errors.append(f"{label}: invalid or empty live-input roles")

            sections = live_input.get("analysis_sections")
            if (
                not isinstance(sections, list)
                or not sections
                or len(set(sections)) != len(sections)
                or any(section not in allowed_sections for section in sections)
            ):
                errors.append(f"{label}: invalid or empty analysis_sections")

            if observation is not None and analysis_as_of is not None:
                observed_at = _exact_utc(observation.get("observed_at_utc"))
                if observed_at is None:
                    errors.append(
                        f"{label}: referenced Live observation has invalid observed_at_utc"
                    )
                elif analysis_as_of < observed_at:
                    errors.append(
                        f"{label}: analysis_as_of_utc predates Live observed_at_utc"
                    )

    return LiveAnalysisBridgeValidationReport(tuple(errors))


def public_review_without_live_inputs(
    analysis_schema: dict[str, Any], review: dict[str, Any]
) -> dict[str, Any]:
    """Return a public-safe review copy under the AY projection gate.

    This helper is intentionally not a production-feed opener. It exists so the
    bridge contract has an executable public-boundary rule before the first real
    production Live input is admitted.
    """

    policy = analysis_schema.get("live_input_policy") or {}
    public_row = deepcopy(review)
    if policy.get("public_live_input_projection_allowed") is not True:
        public_row.pop("live_inputs", None)
    return public_row
