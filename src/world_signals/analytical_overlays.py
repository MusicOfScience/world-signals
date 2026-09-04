from __future__ import annotations

from collections import Counter, defaultdict


DATASET = "BIOSECURITY_CROSS_DOMAIN_OVERLAY"
LAYER = "ANALYTICAL_COVERAGE_OVERLAY_NONCANONICAL"
CANDIDATE_STATUS = "NOT_CANONICAL_AT_V0.20"
FORBIDDEN_CANDIDATE_ID_FIELDS = {"series_id", "occurrence_id"}


def _records_by_series(registry: dict) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for record in registry.get("records", []):
        if record.get("series_id"):
            grouped[str(record["series_id"])].append(record)
    return grouped


def validate_biosecurity_overlay(registry: dict, overlay: dict) -> list[str]:
    """Validate the noncanonical biosecurity coverage/analytical overlay.

    The function is deliberately read-only. It verifies referential integrity
    against canonical series while preventing candidate research nodes from
    masquerading as canonical identities.
    """
    errors: list[str] = []

    if overlay.get("dataset") != DATASET:
        errors.append(f"dataset must be {DATASET}")
    if overlay.get("layer") != LAYER:
        errors.append(f"layer must be {LAYER}")

    checkpoint = overlay.get("canonical_checkpoint") or {}
    if checkpoint.get("registry_version") != registry.get("version"):
        errors.append("canonical checkpoint registry_version does not match registry")
    if checkpoint.get("record_count") != len(registry.get("records", [])):
        errors.append("canonical checkpoint record_count does not match registry")

    principles = overlay.get("principles") or {}
    required_true = (
        "non_exclusive",
        "canonical_primary_category_unchanged",
        "canonical_timing_unchanged",
        "canonical_lifecycle_unchanged",
        "candidate_nodes_are_not_canonical",
        "candidate_nodes_may_not_carry_canonical_ids",
        "overlay_is_not_population_authority",
        "one_health_is_cross_cutting_relationship_not_primary_bucket",
    )
    for key in required_true:
        if principles.get(key) is not True:
            errors.append(f"principle {key} must be true")

    systems = overlay.get("systems") or []
    system_ids = [x.get("system_id") for x in systems]
    if any(not x for x in system_ids):
        errors.append("every system requires system_id")
    if len(system_ids) != len(set(system_ids)):
        errors.append("system_id values must be unique")
    valid_system_ids = set(system_ids)

    relationships = overlay.get("relationships") or []
    relationship_ids = [x.get("relationship_id") for x in relationships]
    if any(not x for x in relationship_ids):
        errors.append("every relationship requires relationship_id")
    if len(relationship_ids) != len(set(relationship_ids)):
        errors.append("relationship_id values must be unique")
    valid_relationship_ids = set(relationship_ids)
    for relation in relationships:
        unknown = set(relation.get("connects_system_ids") or []) - valid_system_ids
        if unknown:
            errors.append(
                f"relationship {relation.get('relationship_id')} has unknown systems: {sorted(unknown)}"
            )
        if relation.get("relationship_id") == "ONE_HEALTH" and relation.get("relationship_type") != "CROSS_CUTTING":
            errors.append("ONE_HEALTH must remain a CROSS_CUTTING relationship")

    canonical_by_series = _records_by_series(registry)
    membership_series: list[str] = []
    for membership in overlay.get("canonical_series_memberships") or []:
        series_id = membership.get("series_id")
        if not series_id:
            errors.append("canonical membership missing series_id")
            continue
        membership_series.append(series_id)
        records = canonical_by_series.get(series_id)
        if not records:
            errors.append(f"mapped series {series_id} does not exist in canonical registry")
            continue
        unknown_systems = set(membership.get("system_ids") or []) - valid_system_ids
        if unknown_systems:
            errors.append(f"mapped series {series_id} has unknown systems: {sorted(unknown_systems)}")
        actual_categories = {r.get("category") for r in records}
        expected_category = membership.get("canonical_primary_category")
        if actual_categories != {expected_category}:
            errors.append(
                f"mapped series {series_id} primary category mismatch: {sorted(str(x) for x in actual_categories)} != {expected_category}"
            )
        actual_institutions = {r.get("institution") for r in records}
        expected_institution = membership.get("canonical_institution")
        if actual_institutions != {expected_institution}:
            errors.append(
                f"mapped series {series_id} institution mismatch: {sorted(str(x) for x in actual_institutions)} != {expected_institution}"
            )
    if len(membership_series) != len(set(membership_series)):
        errors.append("each canonical series may appear only once; use system_ids for non-exclusive membership")

    canonical_institutions = {r.get("institution") for r in registry.get("records", []) if r.get("institution")}
    candidate_ids: list[str] = []
    for node in overlay.get("candidate_nodes") or []:
        candidate_id = node.get("candidate_node_id")
        if not candidate_id:
            errors.append("candidate node missing candidate_node_id")
        else:
            candidate_ids.append(candidate_id)
        for forbidden in FORBIDDEN_CANDIDATE_ID_FIELDS:
            if node.get(forbidden):
                errors.append(f"candidate node {candidate_id} may not carry {forbidden}")
        if node.get("canonical_status") != CANDIDATE_STATUS:
            errors.append(f"candidate node {candidate_id} must remain {CANDIDATE_STATUS}")
        unknown_systems = set(node.get("system_ids") or []) - valid_system_ids
        if unknown_systems:
            errors.append(f"candidate node {candidate_id} has unknown systems: {sorted(unknown_systems)}")
        unknown_relationships = set(node.get("relationship_ids") or []) - valid_relationship_ids
        if unknown_relationships:
            errors.append(
                f"candidate node {candidate_id} has unknown relationships: {sorted(unknown_relationships)}"
            )
        if node.get("institution") in canonical_institutions:
            errors.append(
                f"candidate node {candidate_id} institution is already canonical; overlay requires review/update"
            )
    if len(candidate_ids) != len(set(candidate_ids)):
        errors.append("candidate_node_id values must be unique")

    return errors


def biosecurity_overlay_summary(registry: dict, overlay: dict) -> dict:
    """Return a small descriptive projection after validation."""
    errors = validate_biosecurity_overlay(registry, overlay)
    if errors:
        raise ValueError("; ".join(errors))

    by_series = _records_by_series(registry)
    system_series = Counter()
    mapped_occurrences = 0
    for membership in overlay.get("canonical_series_memberships") or []:
        series_id = membership["series_id"]
        mapped_occurrences += len(by_series[series_id])
        for system_id in membership.get("system_ids") or []:
            system_series[system_id] += 1

    return {
        "project": "WORLD SIGNALS",
        "dataset": DATASET,
        "version": overlay.get("version"),
        "canonical_registry_version": registry.get("version"),
        "mapped_canonical_series_count": len(overlay.get("canonical_series_memberships") or []),
        "mapped_canonical_occurrence_count": mapped_occurrences,
        "candidate_node_count": len(overlay.get("candidate_nodes") or []),
        "mapped_series_by_system": dict(sorted(system_series.items())),
        "canonical_mutation_authorized": False,
        "event_population_authorized": False,
    }
