from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class AnalysisValidationReport:
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def _refs(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "evidence_refs" and isinstance(child, list):
                found.update(str(item) for item in child)
            else:
                found.update(_refs(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_refs(child))
    return found


def _parse_iso(raw: str) -> bool:
    try:
        datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return True
    except (TypeError, ValueError, AttributeError):
        return False


def validate_analysis(
    schema: dict[str, Any],
    evidence_registry: dict[str, Any],
    reviews_dataset: dict[str, Any],
    canonical_registry: dict[str, Any],
) -> AnalysisValidationReport:
    errors: list[str] = []
    vocab = schema.get("controlled_vocabularies") or {}
    required_sections = schema.get("required_review_sections") or []

    if (schema.get("layer_boundary") or {}).get("canonical_mutation_allowed") is not False:
        errors.append("analysis schema must prohibit canonical mutation")
    if (schema.get("layer_boundary") or {}).get("calendar_mutation_allowed") is not False:
        errors.append("analysis schema must prohibit calendar mutation")

    canonical_by_id = {
        row.get("occurrence_id"): row
        for row in canonical_registry.get("records", [])
        if row.get("occurrence_id")
    }

    evidence_by_id: dict[str, dict[str, Any]] = {}
    for row in evidence_registry.get("evidence", []):
        evidence_id = row.get("evidence_id")
        if not evidence_id:
            errors.append("analytical evidence row missing evidence_id")
            continue
        if evidence_id in evidence_by_id:
            errors.append(f"duplicate analytical evidence_id {evidence_id}")
        evidence_by_id[evidence_id] = row
        if row.get("evidence_class") not in set(vocab.get("evidence_class", [])):
            errors.append(f"{evidence_id}: invalid evidence_class {row.get('evidence_class')}")
        if row.get("canonical_provenance_effect") != "NONE":
            errors.append(f"{evidence_id}: analytical evidence cannot alter canonical provenance")
        roles = row.get("roles") or []
        allowed_roles = set(vocab.get("evidence_role", []))
        if not roles or any(role not in allowed_roles for role in roles):
            errors.append(f"{evidence_id}: invalid or empty evidence roles")
        if not row.get("url"):
            errors.append(f"{evidence_id}: source URL required")

    seen_analysis_ids: set[str] = set()
    allowed_review_states = set(vocab.get("review_state", []))
    allowed_surprise = set(vocab.get("surprise_status", []))
    allowed_interaction = set(vocab.get("interaction_type", []))
    allowed_causal = set(vocab.get("causal_status", []))
    allowed_confidence = set(vocab.get("confidence", []))
    allowed_movement = set(vocab.get("movement_type", []))
    allowed_precision = set(vocab.get("measurement_precision", []))
    allowed_second_order = set(vocab.get("second_order_status", []))

    for review in reviews_dataset.get("reviews", []):
        analysis_id = review.get("analysis_id") or "<missing-analysis-id>"
        if analysis_id in seen_analysis_ids:
            errors.append(f"duplicate analysis_id {analysis_id}")
        seen_analysis_ids.add(analysis_id)

        if review.get("review_state") not in allowed_review_states:
            errors.append(f"{analysis_id}: invalid review_state")
        if not _parse_iso(review.get("analysis_as_of_utc")):
            errors.append(f"{analysis_id}: analysis_as_of_utc must be ISO datetime")
        if review.get("canonical_mutation_prohibited") is not True:
            errors.append(f"{analysis_id}: canonical mutation prohibition must be explicit")
        if review.get("google_calendar_write") is not False:
            errors.append(f"{analysis_id}: Google Calendar write must remain false")

        occurrence_id = review.get("canonical_occurrence_id")
        canonical = canonical_by_id.get(occurrence_id)
        if not canonical:
            errors.append(f"{analysis_id}: unknown canonical occurrence_id {occurrence_id}")
        else:
            expected_pairs = (
                ("canonical_series_id", "series_id"),
                ("canonical_event_type", "event_type"),
                ("canonical_institution", "institution"),
                ("canonical_release_utc", "start_utc"),
            )
            for review_key, canonical_key in expected_pairs:
                if review.get(review_key) != canonical.get(canonical_key):
                    errors.append(
                        f"{analysis_id}: {review_key} does not match canonical {canonical_key}"
                    )

        for section in required_sections:
            if section not in review:
                errors.append(f"{analysis_id}: missing required section {section}")

        surprise = review.get("what_surprised") or {}
        if surprise.get("status") not in allowed_surprise:
            errors.append(f"{analysis_id}: invalid surprise status")
        if surprise.get("status") not in {"NO_CLEAR_SURPRISE", "NOT_ESTABLISHED"}:
            if not surprise.get("comparisons"):
                errors.append(f"{analysis_id}: surprise requires an explicit comparison basis")

        movements = review.get("what_moved") or []
        for movement in movements:
            movement_id = movement.get("movement_id") or "<missing-movement-id>"
            if movement.get("movement_type") not in allowed_movement:
                errors.append(f"{analysis_id}/{movement_id}: invalid movement_type")
            if movement.get("measurement_precision") not in allowed_precision:
                errors.append(f"{analysis_id}/{movement_id}: invalid measurement_precision")
            if not movement.get("measurement_window"):
                errors.append(f"{analysis_id}/{movement_id}: measurement_window required")
            if not movement.get("evidence_refs"):
                errors.append(f"{analysis_id}/{movement_id}: evidence_refs required")
            if movement.get("independently_reconstructed") not in {True, False}:
                errors.append(
                    f"{analysis_id}/{movement_id}: independently_reconstructed must be explicit"
                )

        connection = review.get("what_appears_connected") or {}
        if connection.get("interaction_type") not in allowed_interaction:
            errors.append(f"{analysis_id}: invalid interaction_type")
        causal_status = connection.get("causal_status")
        if causal_status not in allowed_causal:
            errors.append(f"{analysis_id}: invalid causal_status")
        if connection.get("confidence") not in allowed_confidence:
            errors.append(f"{analysis_id}: invalid connection confidence")
        alternatives = review.get("alternative_explanations") or []
        if causal_status != "NOT_A_CAUSAL_CLAIM" and not alternatives:
            errors.append(
                f"{analysis_id}: non-null connection requires alternative explanations"
            )
        if causal_status in {
            "CAUSAL_HYPOTHESIS",
            "CAUSAL_SUPPORT_PARTIAL",
            "CAUSAL_SUPPORT_STRONG",
        } and len(set(connection.get("evidence_refs") or [])) < 2:
            errors.append(
                f"{analysis_id}: stronger causal language requires at least two evidence references"
            )

        second_order = review.get("second_order_effects") or {}
        if second_order.get("status") not in allowed_second_order:
            errors.append(f"{analysis_id}: invalid second_order status")

        all_refs = _refs(review)
        unknown_refs = sorted(all_refs.difference(evidence_by_id))
        if unknown_refs:
            errors.append(f"{analysis_id}: unknown evidence refs {unknown_refs}")

    if not reviews_dataset.get("reviews"):
        errors.append("analytical layer requires at least one sample review")

    return AnalysisValidationReport(tuple(errors))


def public_analysis_projection(
    schema: dict[str, Any],
    evidence_registry: dict[str, Any],
    reviews_dataset: dict[str, Any],
    canonical_registry: dict[str, Any],
) -> dict[str, Any]:
    report = validate_analysis(schema, evidence_registry, reviews_dataset, canonical_registry)
    if not report.ok:
        raise ValueError("analysis validation failed: " + "; ".join(report.errors))

    evidence = {
        row["evidence_id"]: {
            "evidence_id": row["evidence_id"],
            "evidence_class": row.get("evidence_class"),
            "provider": row.get("provider"),
            "host_or_distribution": row.get("host_or_distribution"),
            "title": row.get("title"),
            "url": row.get("url"),
            "published_at": row.get("published_at"),
            "roles": row.get("roles", []),
        }
        for row in evidence_registry.get("evidence", [])
    }

    reviews = []
    for row in reviews_dataset.get("reviews", []):
        refs = sorted(_refs(row))
        public_row = dict(row)
        public_row["evidence"] = [evidence[ref] for ref in refs]
        reviews.append(public_row)

    return {
        "metadata": {
            "projection_type": "READ_ONLY_ANALYTICAL_REVIEW",
            "schema_version": schema.get("version"),
            "review_dataset_version": reviews_dataset.get("version"),
            "evidence_registry_version": evidence_registry.get("version"),
            "review_count": len(reviews),
            "canonical_mutation_allowed": False,
            "google_calendar_write": False,
            "causal_claims_are_explicitly_graded": True,
        },
        "reviews": reviews,
    }
