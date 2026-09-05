from __future__ import annotations

from collections import Counter
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


def _region(row: dict[str, Any]) -> str:
    return str(row.get("region") or row.get("broad_region") or "UNSPECIFIED")


def _canonical_context(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "occurrence_id": row.get("occurrence_id"),
        "series_id": row.get("series_id"),
        "canonical_name": row.get("canonical_name") or row.get("title"),
        "institution": row.get("institution"),
        "jurisdiction": row.get("jurisdiction"),
        "region": _region(row),
        "category": row.get("category"),
        "subcategory": row.get("subcategory"),
        "event_type": row.get("event_type"),
        "lifecycle_status": row.get("lifecycle_status"),
        "intrinsic_importance": row.get("intrinsic_importance"),
        "expected_market_sensitivity": row.get("expected_market_sensitivity"),
        "timing_type": row.get("timing_type"),
        "time_precision": row.get("time_precision"),
        "start_utc": row.get("start_utc"),
        "end_utc": row.get("end_utc"),
        "start_local": row.get("start_local"),
        "end_local": row.get("end_local"),
        "source_timezone": row.get("source_timezone"),
        "source_native_date_label": row.get("source_native_date_label"),
        "native_calendar_system": row.get("native_calendar_system"),
        "native_calendar_year": row.get("native_calendar_year"),
        "native_calendar_month": row.get("native_calendar_month"),
        "native_calendar_day": row.get("native_calendar_day"),
        "gregorian_resolution_status": row.get("gregorian_resolution_status"),
        "publication_time_semantics": row.get("publication_time_semantics"),
    }


def analysis_population_readiness(
    schema: dict[str, Any],
    reviews_dataset: dict[str, Any],
    canonical_registry: dict[str, Any],
) -> dict[str, Any]:
    policy = schema.get("population_readiness_policy") or {}
    required_lifecycle = policy.get("post_event_anchor_lifecycle", "COMPLETED")
    priority_regions = list(policy.get("priority_geographic_stress_regions") or [])
    minimum_event_types = int(
        policy.get("minimum_reviewed_event_type_diversity_before_broad_population", 1)
    )

    canonical_by_id = {
        row.get("occurrence_id"): row
        for row in canonical_registry.get("records", [])
        if row.get("occurrence_id")
    }
    completed = [
        row
        for row in canonical_registry.get("records", [])
        if row.get("lifecycle_status") == required_lifecycle
    ]
    reviewed_ids = {
        row.get("canonical_occurrence_id")
        for row in reviews_dataset.get("reviews", [])
        if row.get("review_state") in {"REVIEWED_SAMPLE", "REVIEWED"}
        and row.get("review_phase") == "POST_EVENT"
        and row.get("canonical_occurrence_id") in canonical_by_id
    }
    reviewed_rows = [canonical_by_id[occurrence_id] for occurrence_id in sorted(reviewed_ids)]

    eligible_by_region = Counter(_region(row) for row in completed)
    eligible_by_event_type = Counter(str(row.get("event_type") or "UNSPECIFIED") for row in completed)
    reviewed_by_region = Counter(_region(row) for row in reviewed_rows)
    reviewed_by_event_type = Counter(
        str(row.get("event_type") or "UNSPECIFIED") for row in reviewed_rows
    )

    priority_status = []
    for region in priority_regions:
        eligible_count = eligible_by_region.get(region, 0)
        reviewed_count = reviewed_by_region.get(region, 0)
        if eligible_count == 0:
            state = "NO_COMPLETED_CANONICAL_ANCHOR"
        elif reviewed_count == 0:
            state = "ELIGIBLE_UNREVIEWED"
        else:
            state = "REVIEWED_SAMPLE_PRESENT"
        priority_status.append(
            {
                "region": region,
                "eligible_completed_count": eligible_count,
                "reviewed_count": reviewed_count,
                "state": state,
            }
        )

    reviewed_event_type_diversity = len(reviewed_by_event_type)
    if any(row["state"] == "NO_COMPLETED_CANONICAL_ANCHOR" for row in priority_status):
        broad_state = "BLOCKED_NO_PRIORITY_REGION_COMPLETED_ANCHOR"
    elif any(row["state"] == "ELIGIBLE_UNREVIEWED" for row in priority_status):
        broad_state = "BLOCKED_PRIORITY_REGION_REVIEW_GAP"
    elif reviewed_event_type_diversity < minimum_event_types:
        broad_state = "BLOCKED_EVENT_TYPE_DIVERSITY"
    else:
        broad_state = "READY_FOR_CONTROLLED_EXPANSION"

    return {
        "post_event_anchor_lifecycle": required_lifecycle,
        "eligible_completed_occurrence_count": len(completed),
        "reviewed_occurrence_count": len(reviewed_rows),
        "reviewed_occurrence_ids": sorted(reviewed_ids),
        "eligible_by_region": dict(sorted(eligible_by_region.items())),
        "reviewed_by_region": dict(sorted(reviewed_by_region.items())),
        "eligible_by_event_type": dict(sorted(eligible_by_event_type.items())),
        "reviewed_by_event_type": dict(sorted(reviewed_by_event_type.items())),
        "reviewed_event_type_diversity": reviewed_event_type_diversity,
        "minimum_reviewed_event_type_diversity_before_broad_population": minimum_event_types,
        "priority_geographic_stress_regions": priority_status,
        "broad_population_state": broad_state,
        "elapsed_date_never_implies_completion": bool(
            policy.get("elapsed_date_never_implies_completion")
        ),
        "missing_historical_anchor_never_authorizes_synthetic_occurrence": bool(
            policy.get("missing_historical_anchor_never_authorizes_synthetic_occurrence")
        ),
        "notes": [
            "Readiness counts canonical lifecycle state, not elapsed clock time.",
            "A zero-anchor priority region is an upstream canonical-population constraint, not permission for the Analysis layer to invent historical occurrences.",
            "Review counts measure audited sample coverage only; they are not a claim of analytical completeness.",
        ],
    }


def validate_analysis(
    schema: dict[str, Any],
    evidence_registry: dict[str, Any],
    reviews_dataset: dict[str, Any],
    canonical_registry: dict[str, Any],
) -> AnalysisValidationReport:
    errors: list[str] = []
    vocab = schema.get("controlled_vocabularies") or {}
    required_sections = schema.get("required_review_sections") or []
    population_policy = schema.get("population_readiness_policy") or {}

    if (schema.get("layer_boundary") or {}).get("canonical_mutation_allowed") is not False:
        errors.append("analysis schema must prohibit canonical mutation")
    if (schema.get("layer_boundary") or {}).get("calendar_mutation_allowed") is not False:
        errors.append("analysis schema must prohibit calendar mutation")
    if population_policy.get("elapsed_date_never_implies_completion") is not True:
        errors.append("analysis population policy must prohibit elapsed-date completion inference")
    if population_policy.get("missing_historical_anchor_never_authorizes_synthetic_occurrence") is not True:
        errors.append("analysis population policy must prohibit synthetic historical anchors")

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
    allowed_review_phases = set(vocab.get("review_phase", []))
    allowed_surprise = set(vocab.get("surprise_status", []))
    allowed_benchmark = set(vocab.get("benchmark_type", []))
    allowed_comparison = set(vocab.get("comparison_kind", []))
    allowed_interaction = set(vocab.get("interaction_type", []))
    allowed_causal = set(vocab.get("causal_status", []))
    allowed_confidence = set(vocab.get("confidence", []))
    allowed_movement = set(vocab.get("movement_type", []))
    allowed_representation = set(vocab.get("movement_representation", []))
    allowed_precision = set(vocab.get("measurement_precision", []))
    allowed_second_order = set(vocab.get("second_order_status", []))
    required_post_lifecycle = population_policy.get("post_event_anchor_lifecycle", "COMPLETED")

    for review in reviews_dataset.get("reviews", []):
        analysis_id = review.get("analysis_id") or "<missing-analysis-id>"
        if analysis_id in seen_analysis_ids:
            errors.append(f"duplicate analysis_id {analysis_id}")
        seen_analysis_ids.add(analysis_id)

        review_state = review.get("review_state")
        review_phase = review.get("review_phase")
        if review_state not in allowed_review_states:
            errors.append(f"{analysis_id}: invalid review_state")
        if review_phase not in allowed_review_phases:
            errors.append(f"{analysis_id}: invalid review_phase")
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
            if (
                review_state in {"REVIEWED_SAMPLE", "REVIEWED"}
                and review_phase == "POST_EVENT"
                and canonical.get("lifecycle_status") != required_post_lifecycle
            ):
                errors.append(
                    f"{analysis_id}: reviewed post-event analysis requires canonical lifecycle {required_post_lifecycle}"
                )

        for section in required_sections:
            if section not in review:
                errors.append(f"{analysis_id}: missing required section {section}")

        for benchmark in (review.get("what_was_expected") or {}).get("benchmarks", []):
            if benchmark.get("benchmark_type") not in allowed_benchmark:
                errors.append(
                    f"{analysis_id}: invalid benchmark_type {benchmark.get('benchmark_type')}"
                )

        surprise = review.get("what_surprised") or {}
        surprise_status = surprise.get("status")
        comparisons = surprise.get("comparisons") or []
        if surprise_status not in allowed_surprise:
            errors.append(f"{analysis_id}: invalid surprise status")
        if surprise_status not in {"NO_CLEAR_SURPRISE", "NOT_ESTABLISHED"} and not comparisons:
            errors.append(f"{analysis_id}: surprise requires an explicit comparison basis")
        for comparison in comparisons:
            kind = comparison.get("comparison_kind")
            if kind not in allowed_comparison:
                errors.append(f"{analysis_id}: invalid comparison_kind {kind}")
            if kind == "QUANTITATIVE":
                if not isinstance(comparison.get("actual"), (int, float)) or not isinstance(
                    comparison.get("expected"), (int, float)
                ):
                    errors.append(
                        f"{analysis_id}: quantitative comparison requires numeric actual and expected"
                    )
            if kind == "QUALITATIVE":
                if not str(comparison.get("actual") or "").strip() or not str(
                    comparison.get("expected") or ""
                ).strip():
                    errors.append(
                        f"{analysis_id}: qualitative comparison requires actual and expected descriptions"
                    )

        movements = review.get("what_moved") or []
        for movement in movements:
            movement_id = movement.get("movement_id") or "<missing-movement-id>"
            if movement.get("movement_type") not in allowed_movement:
                errors.append(f"{analysis_id}/{movement_id}: invalid movement_type")
            representation = movement.get("movement_representation")
            if representation not in allowed_representation:
                errors.append(f"{analysis_id}/{movement_id}: invalid movement_representation")
            if movement.get("measurement_precision") not in allowed_precision:
                errors.append(f"{analysis_id}/{movement_id}: invalid measurement_precision")
            if not movement.get("measurement_window"):
                errors.append(f"{analysis_id}/{movement_id}: measurement_window required")
            if not movement.get("evidence_refs"):
                errors.append(f"{analysis_id}/{movement_id}: evidence_refs required")
            independently_reconstructed = movement.get("independently_reconstructed")
            if independently_reconstructed not in {True, False}:
                errors.append(
                    f"{analysis_id}/{movement_id}: independently_reconstructed must be explicit"
                )
            if representation == "PRE_POST_VALUES":
                if movement.get("before_value") is None or movement.get("after_value") is None:
                    errors.append(
                        f"{analysis_id}/{movement_id}: PRE_POST_VALUES requires before_value and after_value"
                    )
            elif representation == "CHANGE_AND_ENDPOINT":
                if movement.get("after_value") is None or movement.get("change") is None:
                    errors.append(
                        f"{analysis_id}/{movement_id}: CHANGE_AND_ENDPOINT requires after_value and change"
                    )
                if movement.get("before_value") is not None and independently_reconstructed is False:
                    errors.append(
                        f"{analysis_id}/{movement_id}: source-reported change+endpoint must not synthesize before_value"
                    )
            elif representation == "QUALITATIVE_ONLY":
                if movement.get("measurement_precision") != "QUALITATIVE_ONLY":
                    errors.append(
                        f"{analysis_id}/{movement_id}: qualitative movement requires QUALITATIVE_ONLY precision"
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

    canonical_by_id = {
        row.get("occurrence_id"): row
        for row in canonical_registry.get("records", [])
        if row.get("occurrence_id")
    }
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
        public_row["canonical"] = _canonical_context(
            canonical_by_id[row["canonical_occurrence_id"]]
        )
        public_row["evidence"] = [evidence[ref] for ref in refs]
        reviews.append(public_row)

    readiness = analysis_population_readiness(schema, reviews_dataset, canonical_registry)

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
            "population_readiness_is_descriptive_not_population_authority": True,
        },
        "readiness": readiness,
        "reviews": reviews,
    }
