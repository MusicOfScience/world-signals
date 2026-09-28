"""One-query internal World State and Relationship intelligence read.

This module is a structured read projection over the existing evidence reader,
admitted World State history and admitted Relationship context.  It does not
create a snapshot, synthesize a new assessment, infer a Relationship, or
publish anything.  The request is the single source of truth for both the
knowledge/evidence and production-history reads.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from .world_state_admission import load_production_state
from .world_state_history import DIMENSIONS, QUERY_MODES
from .world_state_read import (
    ROOT,
    read_world_state,
)


CONTRACT_VERSION = "0.1"
CURRENT_USE_STATUSES = {
    "CURRENTLY_USABLE_WITHIN_SCOPE",
    "CURRENT_WITH_REVIEW_DUE_SOON",
}
REVIEW_REQUIRED_STATUS = "CURRENT_USE_REQUIRES_REVIEW"
HISTORICAL_STATUS = "NO_CURRENTNESS_CLAIM"
UNKNOWN_STATUS = "UNKNOWN"
ENDPOINT_SELECTED = "SELECTED_IN_THIS_VIEW"
ENDPOINT_OUTSIDE_SCOPE = "VALID_PRODUCTION_ENDPOINT_OUTSIDE_VIEW_SCOPE"
ENDPOINT_UNAVAILABLE = "UNAVAILABLE"


class WorldStateInternalReadError(ValueError):
    """Raised when an integrated internal read cannot be made coherently."""


def _compact(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def semantic_fingerprint(value: Any) -> str:
    return hashlib.sha256(_compact(value).encode("utf-8")).hexdigest()


def _parse_utc(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or len(value) != 20 or not value.endswith("Z"):
        raise WorldStateInternalReadError(f"{field} must be exact UTC ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise WorldStateInternalReadError(f"{field} is not valid UTC") from exc
    if parsed.tzinfo != timezone.utc:
        raise WorldStateInternalReadError(f"{field} must use UTC")
    return parsed


def _normalize_scope(scope: Any) -> dict[str, list[str]]:
    if not isinstance(scope, dict) or set(scope) != {"jurisdictions", "dimensions"}:
        raise WorldStateInternalReadError("scope must contain only jurisdictions and dimensions")
    normalized: dict[str, list[str]] = {}
    for key in ("jurisdictions", "dimensions"):
        values = scope[key]
        if not isinstance(values, list) or not values or any(not isinstance(value, str) or not value.strip() for value in values):
            raise WorldStateInternalReadError(f"scope.{key} must be a non-empty list of strings")
        if len(set(values)) != len(values):
            raise WorldStateInternalReadError(f"scope.{key} must not contain duplicates")
        if "*" in values and len(values) != 1:
            raise WorldStateInternalReadError(f"scope.{key} wildcard cannot be combined with named values")
        normalized[key] = sorted(values)
    unknown = sorted(set(normalized["dimensions"]) - DIMENSIONS)
    if unknown:
        raise WorldStateInternalReadError(f"unsupported dimension vocabulary: {unknown}")
    return normalized


def validate_internal_read_request(request: Any) -> dict[str, Any]:
    """Validate the single source-of-truth internal intelligence request."""
    if not isinstance(request, dict):
        raise WorldStateInternalReadError("internal intelligence request must be an object")
    required = {
        "contract_version",
        "query_mode",
        "knowledge_cutoff_utc",
        "effective_as_of_utc",
        "scope",
        "include_negative_evidence",
        "include_withdrawn_history",
    }
    if set(request) != required:
        raise WorldStateInternalReadError(
            f"request keys mismatch; missing={sorted(required - set(request))} extra={sorted(set(request) - required)}"
        )
    if request["contract_version"] != CONTRACT_VERSION:
        raise WorldStateInternalReadError("unsupported internal intelligence contract version")
    if request["query_mode"] not in QUERY_MODES:
        raise WorldStateInternalReadError("query_mode must be KNOWLEDGE_AS_OF or EFFECTIVE_AS_OF")
    knowledge = _parse_utc(request["knowledge_cutoff_utc"], "knowledge_cutoff_utc")
    effective_value = request["effective_as_of_utc"]
    effective = None
    if request["query_mode"] == "KNOWLEDGE_AS_OF":
        if effective_value is not None:
            raise WorldStateInternalReadError("KNOWLEDGE_AS_OF requires null effective_as_of_utc")
    else:
        effective = _parse_utc(effective_value, "effective_as_of_utc")
        if effective > knowledge:
            raise WorldStateInternalReadError("effective_as_of_utc cannot exceed knowledge_cutoff_utc")
    if type(request["include_negative_evidence"]) is not bool:
        raise WorldStateInternalReadError("include_negative_evidence must be boolean")
    if type(request["include_withdrawn_history"]) is not bool:
        raise WorldStateInternalReadError("include_withdrawn_history must be boolean")
    scope = _normalize_scope(request["scope"])
    return {
        "contract_version": CONTRACT_VERSION,
        "query_mode": request["query_mode"],
        "knowledge_cutoff_utc": request["knowledge_cutoff_utc"],
        "effective_as_of_utc": request["effective_as_of_utc"],
        "scope": scope,
        "include_negative_evidence": request["include_negative_evidence"],
        "include_withdrawn_history": request["include_withdrawn_history"],
    }


def derive_coherent_requests(request: Any) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Derive evidence and production queries from one normalized request."""
    normalized = validate_internal_read_request(request)
    synthesis_request = {
        "contract_version": "0.1",
        "as_of_utc": normalized["knowledge_cutoff_utc"],
        "scope": {
            "jurisdictions": deepcopy(normalized["scope"]["jurisdictions"]),
            "dimensions": deepcopy(normalized["scope"]["dimensions"]),
            "actor_ids": None,
        },
        "include_negative_evidence": normalized["include_negative_evidence"],
        "input_policy": "ACCEPTED_REVIEWED_HEADS_ONLY",
    }
    production_query = {
        "query_mode": normalized["query_mode"],
        "knowledge_cutoff_utc": normalized["knowledge_cutoff_utc"],
        "effective_as_of_utc": normalized["effective_as_of_utc"],
        "scope": {
            "jurisdictions": deepcopy(normalized["scope"]["jurisdictions"]),
            "dimensions": deepcopy(normalized["scope"]["dimensions"]),
            "systems": [],
            "component_ids": [],
        },
        "include_withdrawn_history": normalized["include_withdrawn_history"],
    }
    return normalized, synthesis_request, production_query


def _component_summary(row: dict[str, Any], freshness: dict[str, Any], current_use: dict[str, Any]) -> dict[str, Any]:
    return {
        "component_id": row.get("component_id"),
        "component_type": row.get("component_type"),
        "revision_id": row.get("revision_id"),
        "object_sha256": row.get("object_sha256"),
        "dimension": row.get("dimension"),
        "scope": deepcopy(row.get("scope", {})),
        "state_label": row.get("state_label"),
        "direction": row.get("direction"),
        "qualitative_confidence": row.get("qualitative_confidence"),
        "effective_at": row.get("effective_at"),
        "effective_date": row.get("effective_date"),
        "effective_time_precision": row.get("effective_time_precision"),
        "known_at_utc": row.get("known_at_utc"),
        "admitted_at_utc": row.get("admitted_at_utc"),
        "lifecycle_state": row.get("lifecycle_state"),
        "visibility": row.get("visibility"),
        "freshness": deepcopy(freshness),
        "current_use": deepcopy(current_use),
        "audit_refs": {
            "review_transaction_id": row.get("review_transaction_id"),
            "admission_transaction_id": row.get("admission_transaction_id"),
            "source_proposal_id": row.get("source_proposal_id"),
            "source_manifest_sha256": row.get("source_manifest_sha256"),
        },
    }


def partition_assessments(
    selected_components: list[dict[str, Any]],
    freshness: list[dict[str, Any]],
    current_use: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Partition admitted components without turning status into new claims."""
    freshness_by_id = {row.get("component_id"): row for row in freshness}
    current_by_id = {row.get("component_id"): row for row in current_use}
    buckets = {
        "CURRENTLY_USABLE": [],
        "REVIEW_REQUIRED": [],
        "HISTORICAL_OR_NO_CURRENTNESS": [],
        "UNKNOWN": [],
    }
    for component in selected_components:
        component_id = component.get("component_id")
        freshness_row = freshness_by_id.get(component_id, {"status": "UNKNOWN"})
        current_row = current_by_id.get(component_id, {"status": UNKNOWN_STATUS})
        summary = _component_summary(component, freshness_row, current_row)
        status = current_row.get("status")
        if status in CURRENT_USE_STATUSES:
            buckets["CURRENTLY_USABLE"].append(summary)
        elif status == REVIEW_REQUIRED_STATUS:
            buckets["REVIEW_REQUIRED"].append(summary)
        elif status == HISTORICAL_STATUS:
            buckets["HISTORICAL_OR_NO_CURRENTNESS"].append(summary)
        else:
            buckets["UNKNOWN"].append(summary)
    for rows in buckets.values():
        rows.sort(key=lambda row: (row.get("dimension", ""), row.get("component_id", ""), row.get("revision_id", "")))
    return buckets


def _relationship_applies_to_effective_time(row: dict[str, Any], effective: datetime) -> bool:
    temporal = row.get("temporal_scope", {})
    if not isinstance(temporal, dict):
        return True
    start = temporal.get("start_at_utc")
    end = temporal.get("end_at_utc")
    if start and effective < _parse_utc(start, "relationship.temporal_scope.start_at_utc"):
        return False
    if end and effective > _parse_utc(end, "relationship.temporal_scope.end_at_utc"):
        return False
    if temporal.get("start_date") and effective.date().isoformat() < temporal["start_date"]:
        return False
    if temporal.get("end_date") and effective.date().isoformat() > temporal["end_date"]:
        return False
    return True


def join_relationship_context(
    relationships: list[dict[str, Any]],
    selected_components: list[dict[str, Any]],
    all_components: list[dict[str, Any]],
    *,
    query_mode: str,
    effective_as_of_utc: str | None,
) -> list[dict[str, Any]]:
    """Join Relationship endpoints only by exact component identity and hash."""
    selected_by_identity = {
        (row.get("component_id"), row.get("revision_id"), row.get("object_sha256")): row
        for row in selected_components
    }
    all_by_id_revision: dict[tuple[str | None, str | None], list[dict[str, Any]]] = {}
    for row in all_components:
        all_by_id_revision.setdefault((row.get("component_id"), row.get("revision_id")), []).append(row)
    effective = _parse_utc(effective_as_of_utc, "effective_as_of_utc") if effective_as_of_utc else None
    joined: list[dict[str, Any]] = []
    for relationship in relationships:
        if query_mode == "EFFECTIVE_AS_OF" and effective is not None and not _relationship_applies_to_effective_time(relationship, effective):
            continue
        endpoint_states = []
        for endpoint_name in ("source_nodes", "target_nodes"):
            endpoint_rows = []
            for node in relationship.get(endpoint_name, []):
                identity = (node.get("node_id"), node.get("revision_id"), node.get("object_sha256"))
                matching_selected = selected_by_identity.get(identity)
                if matching_selected is not None:
                    status = ENDPOINT_SELECTED
                else:
                    same_revision = all_by_id_revision.get((node.get("node_id"), node.get("revision_id")), [])
                    if same_revision and not any(row.get("object_sha256") == node.get("object_sha256") for row in same_revision):
                        raise WorldStateInternalReadError(
                            f"ENDPOINT_HASH_MISMATCH: {node.get('node_id')}:{node.get('revision_id')}"
                        )
                    status = ENDPOINT_OUTSIDE_SCOPE if same_revision else ENDPOINT_UNAVAILABLE
                endpoint_rows.append({
                    "node_id": node.get("node_id"),
                    "node_type": node.get("node_type"),
                    "revision_id": node.get("revision_id"),
                    "object_sha256": node.get("object_sha256"),
                    "status": status,
                })
            endpoint_states.append((endpoint_name, endpoint_rows))
        endpoints = dict(endpoint_states)
        statuses = [node["status"] for rows in endpoints.values() for node in rows]
        if ENDPOINT_UNAVAILABLE in statuses:
            context_status = "ENDPOINT_UNAVAILABLE"
        elif ENDPOINT_OUTSIDE_SCOPE in statuses:
            context_status = "PARTIAL_RELATIONSHIP_CONTEXT"
        else:
            context_status = "RELATIONSHIP_CONTEXT_IN_SCOPE"
        joined.append({
            "relationship_id": relationship.get("relationship_id"),
            "revision_id": relationship.get("revision_id"),
            "relationship_class": relationship.get("relationship_class"),
            "directionality": relationship.get("directionality"),
            "confidence": relationship.get("confidence"),
            "causal_status": "NON_CAUSAL" if not relationship.get("causal_basis") else "CAUSAL_BASIS_RETAINED",
            "historical_status": (
                "HISTORICAL_RELATIONSHIP_KNOWN_LATER"
                if query_mode == "EFFECTIVE_AS_OF"
                else "HISTORICAL_REVIEWED_CONNECTION"
            ),
            "context_status": context_status,
            "source_endpoints": endpoints["source_nodes"],
            "target_endpoints": endpoints["target_nodes"],
            "admitted_at_utc": relationship.get("admitted_at_utc"),
            "admission_transaction_id": relationship.get("admission_transaction_id"),
            "admission_transaction_fingerprint": relationship.get("admission_transaction_fingerprint"),
            "production_relationship_fingerprint": relationship.get("production_relationship_fingerprint"),
            "temporal_scope": deepcopy(relationship.get("temporal_scope", {})),
            "visibility": relationship.get("visibility", "INTERNAL_ONLY"),
            "public_projection_permitted": False,
        })
    return sorted(joined, key=lambda row: (row.get("relationship_id", ""), row.get("revision_id", "")))


def _coverage(partitions: dict[str, list[dict[str, Any]]], dimensions: list[str]) -> dict[str, Any]:
    all_rows = [row for rows in partitions.values() for row in rows]
    by_dimension: dict[str, list[dict[str, Any]]] = {}
    for row in all_rows:
        by_dimension.setdefault(row.get("dimension"), []).append(row)
    scoped = sorted(dimension for dimension in dimensions if by_dimension.get(dimension))
    current = sorted({row.get("dimension") for row in partitions["CURRENTLY_USABLE"] if row.get("dimension") in dimensions})
    historical = sorted({row.get("dimension") for row in partitions["HISTORICAL_OR_NO_CURRENTNESS"] if row.get("dimension") in dimensions})
    return {
        "queried_dimensions": sorted(dimensions),
        "scoped_assessment_available": scoped,
        "current_scoped_assessment_available": current,
        "historical_only_assessment_available": historical,
        "not_assessed": sorted(set(dimensions) - set(scoped)),
    }


def read_internal_intelligence(request: Any) -> dict[str, Any]:
    """Return one deterministic, non-narrative internal intelligence view."""
    normalized, synthesis_request, production_query = derive_coherent_requests(request)
    evidence = read_world_state(synthesis_request, production_query=production_query)
    production = evidence.get("production_world_state")
    if not isinstance(production, dict):
        raise WorldStateInternalReadError("production read was not attached to the coherent evidence read")
    selected_components = production.get("selected_components", [])
    partitions = partition_assessments(
        selected_components,
        production.get("freshness", []),
        production.get("current_use", []),
    )
    all_components = load_production_state(ROOT)["components"]
    relationship_rows = evidence.get("relationship_context", {}).get("historical_accepted_relationships", [])
    relationships = join_relationship_context(
        relationship_rows,
        selected_components,
        all_components,
        query_mode=normalized["query_mode"],
        effective_as_of_utc=normalized["effective_as_of_utc"],
    )
    active_relationships = evidence.get("relationship_context", {}).get("current_active_relationships", [])
    coverage = _coverage(partitions, normalized["scope"]["dimensions"])
    partition_counts = {
        "current_use": len(partitions["CURRENTLY_USABLE"]),
        "historical_or_no_currentness": len(partitions["HISTORICAL_OR_NO_CURRENTNESS"]),
        "review_required": len(partitions["REVIEW_REQUIRED"]),
        "unknown": len(partitions["UNKNOWN"]),
    }
    production_refs = []
    for row in selected_components:
        production_refs.append({
            "component_id": row.get("component_id"),
            "revision_id": row.get("revision_id"),
            "object_sha256": row.get("object_sha256"),
        })
    view = {
        "view_type": "WORLD_STATE_INTERNAL_INTELLIGENCE_VIEW",
        "query": normalized,
        "query_coherence_check": {
            "status": "PASS",
            "knowledge_cutoff_shared": True,
            "jurisdiction_scope_shared": True,
            "dimension_scope_shared": True,
            "systems_filter": [],
            "component_filter": [],
        },
        "derived_requests": {
            "synthesis": deepcopy(synthesis_request),
            "production": deepcopy(production_query),
        },
        "evidence_state": {
            "proposal_id": evidence.get("proposal_id"),
            "contract_version": evidence.get("contract_version"),
            "semantic_fingerprint": evidence.get("semantic_fingerprint"),
            "source_manifest_sha256": evidence.get("source_manifest_sha256"),
            "selected_counts": {key: len(value) for key, value in evidence.get("selected_inputs", {}).items()},
            "limitations": deepcopy(evidence.get("limitations", [])),
        },
        "production_state": {
            "status": production.get("status"),
            "component_count": len(selected_components),
            "selected_snapshot": deepcopy(production.get("selected_snapshot")),
            "admission_refs": deepcopy(production.get("admission_refs", [])),
            "production_counts": deepcopy(production.get("production_counts", {})),
            "semantic_fingerprint": production.get("semantic_fingerprint"),
        },
        "current_state": partitions["CURRENTLY_USABLE"],
        "historical_state": partitions["HISTORICAL_OR_NO_CURRENTNESS"],
        "review_required_state": partitions["REVIEW_REQUIRED"],
        "unknown_currentness_state": partitions["UNKNOWN"],
        "partition_counts": partition_counts,
        "coverage": coverage,
        "relationship_context": relationships,
        "relationship_counts": {
            "historical_accepted_in_scope": len(relationships),
            "current_active_in_scope": len(active_relationships),
        },
        "transmission_edge_count": len(evidence.get("transmission_edges", [])),
        "operator_summary": {
            "as_known_at_utc": normalized["knowledge_cutoff_utc"],
            "current_use_assessments": partition_counts["current_use"],
            "historical_no_currentness_assessments": partition_counts["historical_or_no_currentness"],
            "review_required_assessments": partition_counts["review_required"],
            "unknown_assessments": partition_counts["unknown"],
            "historical_relationships": len(relationships),
            "current_active_relationships": len(active_relationships),
            "transmission_edges": len(evidence.get("transmission_edges", [])),
        },
        "provenance": {
            "production_components": production_refs,
            "admission_refs": deepcopy(production.get("admission_refs", [])),
            "production_semantic_fingerprint": production.get("semantic_fingerprint"),
            "relationship_refs": [
                {
                    "relationship_id": row.get("relationship_id"),
                    "revision_id": row.get("revision_id"),
                    "production_relationship_fingerprint": row.get("production_relationship_fingerprint"),
                    "admission_transaction_id": row.get("admission_transaction_id"),
                    "admission_transaction_fingerprint": row.get("admission_transaction_fingerprint"),
                }
                for row in relationships
            ],
        },
        "review_state": {
            "new_synthesis_performed": False,
            "successor_revision_created": False,
            "production_write_performed": False,
            "public_projection_permitted": False,
        },
        "limitations": [
            "This is a structured read of admitted state and eligible evidence; no new synthesis was performed.",
            "A scoped assessment is not a dimension-wide or global assessment.",
            "Historical Relationship context is ASSOCIATION and NON_CAUSAL; no transmission edge is inferred.",
            "Independent snapshot series remain independently admitted and are not a new atomic snapshot.",
        ],
        "mutation_check": {
            "status": "PASS" if evidence.get("mutation_check", {}).get("status") == "PASS" and production.get("production_file_mutation_check", {}).get("status") == "PASS" else "FAIL",
            "evidence": deepcopy(evidence.get("mutation_check", {})),
            "production": deepcopy(production.get("production_file_mutation_check", {})),
        },
    }
    if view["mutation_check"]["status"] != "PASS":
        raise WorldStateInternalReadError("internal intelligence read detected governed input mutation")
    view["semantic_fingerprint"] = semantic_fingerprint({key: value for key, value in view.items() if key != "semantic_fingerprint"})
    return view


__all__ = [
    "WorldStateInternalReadError",
    "derive_coherent_requests",
    "join_relationship_context",
    "partition_assessments",
    "read_internal_intelligence",
    "semantic_fingerprint",
    "validate_internal_read_request",
]
