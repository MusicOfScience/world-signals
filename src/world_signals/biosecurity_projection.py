from __future__ import annotations

from collections import Counter

from .analytical_overlays import biosecurity_overlay_summary, validate_biosecurity_overlay


def public_biosecurity_projection(registry: dict, overlay: dict) -> dict:
    """Build a browser-safe projection of the noncanonical biosecurity overlay.

    This projection exposes analytical coverage shape only. It does not add
    canonical identities to research candidates and it cannot authorise event
    population or canonical mutation.
    """
    errors = validate_biosecurity_overlay(registry, overlay)
    if errors:
        raise ValueError("; ".join(errors))

    summary = biosecurity_overlay_summary(registry, overlay)
    records_by_series: dict[str, list[dict]] = {}
    for record in registry.get("records", []):
        series_id = record.get("series_id")
        if series_id:
            records_by_series.setdefault(str(series_id), []).append(record)

    series_by_system = Counter()
    occurrences_by_system = Counter()
    membership_rows = []
    for membership in overlay.get("canonical_series_memberships") or []:
        series_id = membership["series_id"]
        occurrence_count = len(records_by_series.get(series_id, []))
        for system_id in membership.get("system_ids") or []:
            series_by_system[system_id] += 1
            occurrences_by_system[system_id] += occurrence_count
        membership_rows.append({
            "series_id": series_id,
            "system_ids": list(membership.get("system_ids") or []),
            "canonical_primary_category": membership.get("canonical_primary_category"),
            "canonical_institution": membership.get("canonical_institution"),
            "occurrence_count": occurrence_count,
            "basis": membership.get("basis"),
        })

    candidate_by_system = Counter()
    candidate_rows = []
    for node in overlay.get("candidate_nodes") or []:
        for system_id in node.get("system_ids") or []:
            candidate_by_system[system_id] += 1
        candidate_rows.append({
            "candidate_node_id": node.get("candidate_node_id"),
            "institution": node.get("institution"),
            "system_ids": list(node.get("system_ids") or []),
            "relationship_ids": list(node.get("relationship_ids") or []),
            "canonical_status": node.get("canonical_status"),
            "authority_basis": node.get("authority_basis"),
            "authority_url": node.get("authority_url"),
            "next_gate": node.get("next_gate"),
        })

    system_rows = []
    for system in overlay.get("systems") or []:
        system_id = system.get("system_id")
        system_rows.append({
            "system_id": system_id,
            "label": system.get("label"),
            "description": system.get("description"),
            "canonical_series_count": series_by_system.get(system_id, 0),
            "canonical_occurrence_count": occurrences_by_system.get(system_id, 0),
            "candidate_node_count": candidate_by_system.get(system_id, 0),
        })

    relationship_rows = []
    for relationship in overlay.get("relationships") or []:
        relationship_rows.append({
            "relationship_id": relationship.get("relationship_id"),
            "label": relationship.get("label"),
            "relationship_type": relationship.get("relationship_type"),
            "connects_system_ids": list(relationship.get("connects_system_ids") or []),
            "note": relationship.get("note"),
        })

    return {
        "project": "WORLD SIGNALS",
        "dataset": "BIOSECURITY_CROSS_DOMAIN_OVERLAY_PUBLIC",
        "version": overlay.get("version"),
        "layer": overlay.get("layer"),
        "metadata": {
            "canonical_registry_version": registry.get("version"),
            "canonical_record_count": len(registry.get("records", [])),
            "mapped_canonical_series_count": summary["mapped_canonical_series_count"],
            "mapped_canonical_occurrence_count": summary["mapped_canonical_occurrence_count"],
            "candidate_node_count": summary["candidate_node_count"],
            "canonical_primary_categories_unchanged": True,
            "canonical_mutation_authorized": False,
            "event_population_authorized": False,
            "candidate_nodes_are_canonical": False,
        },
        "systems": system_rows,
        "relationships": relationship_rows,
        "canonical_series_memberships": membership_rows,
        "candidate_nodes": candidate_rows,
        "boundary_note": "Analytical/coverage overlay only. Candidate nodes are not canonical events or series; primary canonical categories, timing and lifecycle remain unchanged.",
    }
