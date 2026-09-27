"""Migration Step 7 validators and temporary World State history simulator.

This module implements contract machinery only.  It does not load, create or
write a production World State dataset.  Callers provide in-memory objects or
test-only copies; production admission is represented by validation and a
temporary-copy simulation.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Iterable


ACTOR_TYPES = {
    "PERSON", "OFFICE", "INSTITUTION", "STATE", "MINISTRY", "REGULATOR",
    "CENTRAL_BANK", "LEGISLATURE", "COURT", "MILITARY_COMMAND", "ALLIANCE",
    "MULTILATERAL_INSTITUTION", "CORPORATION", "NON_STATE_ORGANISATION",
}
ACTOR_RELATIONSHIP_TYPES = {"OCCUPIES", "PART_OF", "JURISDICTION_AUTHORITY"}
COMPONENT_TYPES = {
    "DIMENSION_ASSESSMENT",
    "ACTOR_STATE_ASSERTION",
    "IMPLEMENTATION_CLAIM",
    "BASELINE",
    "NEGATIVE_EVIDENCE",
    "COMPETING_HYPOTHESIS",
    "MODEL_DISAGREEMENT",
}
REVISION_KINDS = {"INITIAL", "UPDATE", "CORRECTION", "SUPERSESSION", "WITHDRAWAL", "EXPIRY"}
REVIEW_STATES = {"CANDIDATE", "UNDER_REVIEW", "ACCEPTED", "REJECTED", "DEFERRED"}
LIFECYCLE_STATES = {"ACTIVE", "SUPERSEDED", "CORRECTED", "WITHDRAWN", "EXPIRED", "UNRESOLVED"}
VISIBILITY_STATES = {"INTERNAL_ONLY", "PUBLIC_ELIGIBLE", "PUBLIC_PROJECTED"}
UNCERTAINTY_TYPES = {
    "PROVENANCE_SOURCE", "MEASUREMENT", "TEMPORAL", "INTERPRETIVE", "MODEL",
    "ACTOR_INTENT", "INSTITUTIONAL_AUTHORITY",
}
IMPLEMENTATION_STATES = {"SAID", "DECIDED", "AUTHORISED", "IMPLEMENTED", "OBSERVED"}
DIMENSIONS = {
    "CONFLICT_MILITARY_ACTIVITY",
    "STRATEGIC_GEOPOLITICAL_TENSION",
    "POLITICAL_INSTITUTIONAL_STABILITY",
    "MACROECONOMIC_FINANCIAL_CONDITIONS",
    "TRADE_CAPITAL_ENERGY_FOOD_FLOWS",
    "DEPENDENCIES_CHOKEPOINTS",
    "MARKETS_AS_SENSORS",
    "CLIMATE_PHYSICAL_RISK",
    "HEALTH_BIOSECURITY",
    "TECHNOLOGY_CRITICAL_INFRASTRUCTURE",
}
QUERY_MODES = {"KNOWLEDGE_AS_OF", "EFFECTIVE_AS_OF"}
EMPTY_DOMAIN_STATES = {"UNQUERIED", "QUERIED_EMPTY", "UNSUPPORTED", "UNKNOWN"}
CITATION_CLASSES = {
    "FACTUAL_SOURCE",
    "REVIEWED_SIGNAL",
    "INFERRED_RELATIONSHIP",
    "HYPOTHESIS",
    "SCENARIO",
    "FORECAST",
    "REVIEWED_RISK_REGIME",
    "OUTCOME",
    "EVALUATION",
}
PRIVATE_FIELDS = {
    "restricted_evidence_locators",
    "actor_sensitive_detail",
    "source_coverage_internals",
    "model_prompts",
    "internal_review_notes",
}
COMMON_FIELDS = {
    "component_type", "component_id", "revision_id", "revision_number",
    "previous_revision_id", "revision_kind", "review_state", "lifecycle_state",
    "effective_at", "known_at_utc", "reviewed_at_utc", "admitted_at_utc",
    "source_proposal_id", "source_manifest_sha256", "review_transaction_id",
    "admission_transaction_id", "visibility", "revision_reason", "object_sha256",
}


class WorldStateHistoryError(ValueError):
    """Raised when an in-memory contract object fails closed."""


def _compact(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def fingerprint(value: Any, *, exclude: Iterable[str] = ()) -> str:
    excluded = set(exclude)
    if isinstance(value, dict):
        value = {key: val for key, val in value.items() if key not in excluded}
    return hashlib.sha256(_compact(value).encode("utf-8")).hexdigest()


def with_object_fingerprint(value: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(value)
    result["object_sha256"] = fingerprint(result, exclude={"object_sha256"})
    return result


def _utc(value: Any, field: str, errors: list[str], *, required: bool = False) -> datetime | None:
    if value is None:
        if required:
            errors.append(f"{field} is required")
        return None
    if not isinstance(value, str) or len(value) != 20 or not value.endswith("Z"):
        errors.append(f"{field} must be exact UTC ending in Z")
        return None
    try:
        result = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        errors.append(f"{field} is not valid UTC")
        return None
    if result.tzinfo != timezone.utc:
        errors.append(f"{field} must use UTC")
        return None
    return result


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _hash(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _list(value: Any) -> bool:
    return isinstance(value, list)


def _validate_uncertainty(ref: Any, errors: list[str], label: str) -> None:
    if not isinstance(ref, dict):
        errors.append(f"{label} must be an object")
        return
    if ref.get("type") not in UNCERTAINTY_TYPES:
        errors.append(f"{label}.type is not a controlled uncertainty type")
    if ref.get("status") not in {"UNRESOLVED", "BOUNDED", "UNKNOWN", "NOT_ASSESSED"}:
        errors.append(f"{label}.status must be UNRESOLVED, BOUNDED, UNKNOWN or NOT_ASSESSED")
    if not _text(ref.get("description")):
        errors.append(f"{label}.description is required")
    if not isinstance(ref.get("basis_refs"), list):
        errors.append(f"{label}.basis_refs must be a list")


def validate_uncertainty_refs(value: Any, errors: list[str], label: str = "uncertainties") -> None:
    if not isinstance(value, list):
        errors.append(f"{label} must be a list")
        return
    for index, ref in enumerate(value):
        _validate_uncertainty(ref, errors, f"{label}[{index}]")


def validate_epistemic_citation(citation: Any, *, label: str = "citation") -> list[str]:
    errors: list[str] = []
    if not isinstance(citation, dict):
        return [f"{label} must be an object"]
    if citation.get("epistemic_class") not in CITATION_CLASSES:
        errors.append(f"{label}.epistemic_class is invalid")
    for field in ("layer", "object_id"):
        if not _text(citation.get(field)):
            errors.append(f"{label}.{field} is required")
    if citation.get("revision_id") is not None and not _text(citation.get("revision_id")):
        errors.append(f"{label}.revision_id must be text or null")
    if not _hash(citation.get("object_sha256")):
        errors.append(f"{label}.object_sha256 must be a SHA-256 hash")
    if citation.get("epistemic_class") == "FORECAST" and citation.get("prospective") is not True:
        errors.append(f"{label}: Forecast citation must remain prospective")
    if citation.get("epistemic_class") == "HYPOTHESIS" and citation.get("factual_claim") is True:
        errors.append(f"{label}: hypothesis citation cannot be labelled factual")
    return errors


def validate_citations(value: Any, errors: list[str], label: str = "citations") -> None:
    if not isinstance(value, list):
        errors.append(f"{label} must be a list")
        return
    for index, citation in enumerate(value):
        errors.extend(validate_epistemic_citation(citation, label=f"{label}[{index}]"))


def validate_visibility_transition(previous: str | None, current: str, *, projection_transaction_id: str | None = None) -> list[str]:
    errors: list[str] = []
    if current not in VISIBILITY_STATES:
        return ["visibility is not controlled"]
    if previous is None:
        if current != "INTERNAL_ONLY":
            errors.append("new components must default to INTERNAL_ONLY")
    elif previous == "INTERNAL_ONLY" and current == "PUBLIC_PROJECTED":
        errors.append("INTERNAL_ONLY cannot skip PUBLIC_ELIGIBLE")
    elif previous == "PUBLIC_ELIGIBLE" and current == "PUBLIC_PROJECTED" and not _text(projection_transaction_id):
        errors.append("PUBLIC_PROJECTED requires a separate projection transaction")
    elif previous == "PUBLIC_PROJECTED" and current != "PUBLIC_PROJECTED":
        errors.append("public projection cannot be silently withdrawn by revision")
    return errors


def validate_public_allowlist(allowlist: Any) -> list[str]:
    if not isinstance(allowlist, list) or not all(_text(value) for value in allowlist):
        return ["public allowlist must be a list of field names"]
    return [f"private field {field} cannot be allowlisted" for field in allowlist if field in PRIVATE_FIELDS]


def public_view(component: dict[str, Any], allowlist: list[str]) -> dict[str, Any]:
    errors = validate_public_allowlist(allowlist)
    if errors:
        raise WorldStateHistoryError("; ".join(errors))
    if component.get("visibility") not in {"PUBLIC_ELIGIBLE", "PUBLIC_PROJECTED"}:
        raise WorldStateHistoryError("component is not public eligible")
    if any(field not in component for field in allowlist):
        raise WorldStateHistoryError("public allowlist references a missing field")
    return {field: deepcopy(component[field]) for field in allowlist}


def _validate_common(row: dict[str, Any], errors: list[str], *, registry: dict[str, Any] | None = None) -> None:
    for field in COMMON_FIELDS:
        if field not in row:
            errors.append(f"{row.get('revision_id', '<row>')}: missing {field}")
    if row.get("component_type") not in COMPONENT_TYPES:
        errors.append("component_type is not a production component family")
    for field in ("component_id", "revision_id", "revision_kind", "source_proposal_id", "revision_reason"):
        if not _text(row.get(field)):
            errors.append(f"{field} is required")
    if type(row.get("revision_number")) is not int or row["revision_number"] < 1:
        errors.append("revision_number must be a positive integer")
    if row.get("revision_kind") not in REVISION_KINDS:
        errors.append("revision_kind is invalid")
    if row.get("review_state") not in REVIEW_STATES:
        errors.append("review_state is invalid")
    if row.get("lifecycle_state") not in LIFECYCLE_STATES:
        errors.append("lifecycle_state is invalid")
    if row.get("visibility") not in VISIBILITY_STATES:
        errors.append("visibility is invalid")
    if row.get("visibility") == "PUBLIC_PROJECTED" and not _text(row.get("projection_transaction_id")):
        errors.append("PUBLIC_PROJECTED requires projection_transaction_id")
    if not _hash(row.get("source_manifest_sha256")):
        errors.append("source_manifest_sha256 must be a SHA-256 hash")
    if row.get("review_transaction_id") is not None and not _text(row.get("review_transaction_id")):
        errors.append("review_transaction_id must be text or null")
    if row.get("admission_transaction_id") is not None and not _text(row.get("admission_transaction_id")):
        errors.append("admission_transaction_id must be text or null")
    effective = _utc(row.get("effective_at"), "effective_at", errors)
    known = _utc(row.get("known_at_utc"), "known_at_utc", errors, required=True)
    reviewed = _utc(row.get("reviewed_at_utc"), "reviewed_at_utc", errors)
    admitted = _utc(row.get("admitted_at_utc"), "admitted_at_utc", errors)
    if known and reviewed and known > reviewed:
        errors.append("known_at_utc cannot be later than reviewed_at_utc")
    if reviewed and admitted and reviewed > admitted:
        errors.append("reviewed_at_utc cannot be later than admitted_at_utc")
    if row.get("review_state") == "ACCEPTED":
        if reviewed is None or admitted is None or not _text(row.get("review_transaction_id")) or not _text(row.get("admission_transaction_id")):
            errors.append("accepted production revision requires review/admission timestamps and transactions")
    if row.get("review_state") in {"REJECTED", "DEFERRED"} and admitted is not None:
        errors.append("rejected/deferred revision cannot have admitted_at_utc")
    if row.get("previous_revision_id") is None and row.get("revision_number") != 1:
        errors.append("initial revision must have revision_number 1")
    if row.get("previous_revision_id") is not None and not _text(row.get("previous_revision_id")):
        errors.append("previous_revision_id must be text or null")
    if not _hash(row.get("object_sha256")):
        errors.append("object_sha256 must be a SHA-256 hash")
    elif row.get("object_sha256") != fingerprint(row, exclude={"object_sha256"}):
        errors.append("object_sha256 does not match the immutable object")
    if "severity" in row or "risk_score" in row or "world_risk_score" in row:
        errors.append("universal severity/risk score is not a World State field")
    for field in ("supporting_citations", "contradictory_citations"):
        if field in row:
            validate_citations(row[field], errors, field)
    if "uncertainties" in row:
        validate_uncertainty_refs(row["uncertainties"], errors)
    if row.get("component_type") == "MODEL_DISAGREEMENT" and "transmission_edges" in row:
        errors.append("World State cannot own production transmission edges")
    if registry is not None and row.get("component_type") == "ACTOR_STATE_ASSERTION":
        actor_ids = {actor.get("actor_id") for actor in registry.get("actors", [])}
        if row.get("actor_id") not in actor_ids:
            errors.append("ActorStateAssertion references an unknown governed actor")
    if effective and admitted and row.get("lifecycle_state") == "ACTIVE" and effective > admitted:
        errors.append("active component cannot be admitted before its effective time")


def _family_errors(row: dict[str, Any], errors: list[str]) -> None:
    component_type = row.get("component_type")
    if component_type == "DIMENSION_ASSESSMENT":
        if row.get("dimension") not in DIMENSIONS:
            errors.append("DimensionAssessment dimension is invalid")
        if not isinstance(row.get("scope"), dict):
            errors.append("DimensionAssessment scope is required")
        if not _text(row.get("state_label")):
            errors.append("DimensionAssessment state_label is required")
        for field in ("direction", "persistence", "breadth"):
            if field in row and row[field] is not None and not _text(row[field]):
                errors.append(f"DimensionAssessment {field} must be text or null")
        for field in ("supporting_citations", "contradictory_citations", "uncertainties"):
            if field not in row:
                errors.append(f"DimensionAssessment {field} is required")
        if row.get("baseline_ref") is not None and not _text(row.get("baseline_ref")):
            errors.append("baseline_ref must be text or null")
    elif component_type == "ACTOR_STATE_ASSERTION":
        if not _text(row.get("actor_id")) or not _text(row.get("claim_type")):
            errors.append("ActorStateAssertion actor_id and claim_type are required")
        if "claim_value" not in row:
            errors.append("ActorStateAssertion claim_value is required and may be UNKNOWN")
        validate_citations(row.get("supporting_citations"), errors, "supporting_citations")
        validate_citations(row.get("contradictory_citations"), errors, "contradictory_citations")
    elif component_type == "IMPLEMENTATION_CLAIM":
        if not _text(row.get("actor_id")) or not _text(row.get("proposition")):
            errors.append("ImplementationClaim actor_id and proposition are required")
        if row.get("state") not in IMPLEMENTATION_STATES:
            errors.append("ImplementationClaim state is invalid")
        validate_citations(row.get("supporting_citations"), errors, "supporting_citations")
        validate_citations(row.get("contradictory_citations"), errors, "contradictory_citations")
    elif component_type == "BASELINE":
        if row.get("basis") not in {"PRIOR_REVIEWED_STATE", "OBSERVATION_WINDOW", "OFFICIAL_REFERENCE", "MARKET_MEASUREMENT", "EXPLICIT_NO_BASELINE"}:
            errors.append("Baseline basis is invalid")
        for field in ("scope", "reference_window", "measurement_definition", "limitations"):
            if field not in row:
                errors.append(f"Baseline {field} is required")
        if row.get("basis") == "EXPLICIT_NO_BASELINE" and row.get("baseline_value_or_label") is not None:
            errors.append("EXPLICIT_NO_BASELINE cannot carry a baseline value")
    elif component_type == "NEGATIVE_EVIDENCE":
        required = ("negative_type", "expected_indicator", "search_scope", "time_window", "source_health", "coverage_assessment", "absence_informative_because", "limitations", "uncertainties")
        for field in required:
            if field not in row:
                errors.append(f"NegativeEvidence {field} is required")
        if row.get("source_health") in {"FAILED", "UNKNOWN"}:
            errors.append("source failure/unknown health cannot support negative evidence")
        if row.get("search_scope") in (None, [], {}):
            errors.append("unqueried source scope cannot support negative evidence")
        if row.get("expected_indicator") in {"", None, "NO_RECORD_FOUND"}:
            errors.append("No record found is not an expected indicator")
    elif component_type == "COMPETING_HYPOTHESIS":
        if not _text(row.get("subject_ref")) or not _text(row.get("proposition")):
            errors.append("CompetingHypothesis subject_ref and proposition are required")
        if not isinstance(row.get("alternatives"), list) or len(row.get("alternatives", [])) < 2:
            errors.append("CompetingHypothesis requires at least two alternatives")
        if row.get("disposition") not in {"UNRESOLVED", "REVIEWED_PREFERRED", "REJECTED"}:
            errors.append("CompetingHypothesis disposition is invalid")
        for field in ("supporting_citations", "contradictory_citations", "assumptions", "falsifiers", "uncertainties"):
            if field not in row:
                errors.append(f"CompetingHypothesis {field} is required")
        validate_citations(row.get("supporting_citations"), errors, "supporting_citations")
        validate_citations(row.get("contradictory_citations"), errors, "contradictory_citations")
    elif component_type == "MODEL_DISAGREEMENT":
        if not _text(row.get("subject_ref")) or not _text(row.get("disagreement")):
            errors.append("ModelDisagreement subject_ref and disagreement are required")
        if not isinstance(row.get("model_outputs"), list) or len(row.get("model_outputs", [])) < 2:
            errors.append("ModelDisagreement requires at least two model outputs")
        provenance = row.get("model_provenance")
        if not isinstance(provenance, dict):
            errors.append("ModelDisagreement model_provenance is required")
        else:
            for field in ("model_identity", "version", "configuration", "analytical_lens", "procedure_version", "generated_at_utc", "input_manifest_sha256", "output_fingerprint"):
                if field not in provenance:
                    errors.append(f"model_provenance.{field} is required")
            if not _hash(provenance.get("input_manifest_sha256")) or not _hash(provenance.get("output_fingerprint")):
                errors.append("model provenance fingerprints must be SHA-256")
        for output in row.get("model_outputs", []):
            if not isinstance(output, dict) or output.get("epistemic_class") == "FACTUAL_SOURCE":
                errors.append("model output cannot be independent factual corroboration")


def validate_component_revision(row: Any, *, registry: dict[str, Any] | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(row, dict):
        return ["component revision must be an object"]
    _validate_common(row, errors, registry=registry)
    _family_errors(row, errors)
    return errors


def validate_component_history(rows: Any, *, previous_revisions: list[dict[str, Any]] | None = None, registry: dict[str, Any] | None = None) -> list[str]:
    if not isinstance(rows, list):
        return ["component history must be a list"]
    errors: list[str] = []
    by_component: dict[str, list[dict[str, Any]]] = {}
    by_revision: dict[str, dict[str, Any]] = {}
    for row in rows:
        errors.extend(validate_component_revision(row, registry=registry))
        if isinstance(row, dict):
            component_id = row.get("component_id")
            revision_id = row.get("revision_id")
            if _text(component_id):
                by_component.setdefault(component_id, []).append(row)
            if _text(revision_id):
                if revision_id in by_revision:
                    errors.append(f"duplicate component revision_id {revision_id}")
                by_revision[revision_id] = row
    if previous_revisions is not None:
        current = {row.get("revision_id"): row for row in rows if isinstance(row, dict)}
        for old in previous_revisions:
            if not isinstance(old, dict) or current.get(old.get("revision_id")) != old:
                errors.append("retained component revision was removed or rewritten")
    for component_id, history in by_component.items():
        ordered = sorted(history, key=lambda row: row.get("revision_number", 0))
        numbers = [row.get("revision_number") for row in ordered]
        if numbers != list(range(1, len(numbers) + 1)):
            errors.append(f"{component_id}: revision numbers must be contiguous")
        for index, row in enumerate(ordered):
            predecessor = row.get("previous_revision_id")
            if index == 0 and predecessor is not None:
                errors.append(f"{component_id}: first revision cannot have predecessor")
            if index > 0 and predecessor != ordered[index - 1].get("revision_id"):
                errors.append(f"{component_id}: predecessor chain is not preserved")
            if index > 0 and row.get("revision_kind") == "INITIAL":
                errors.append(f"{component_id}: later revision cannot be INITIAL")
            previous = ordered[index - 1] if index else None
            if previous and previous.get("lifecycle_state") in {"WITHDRAWN", "EXPIRED"} and row.get("lifecycle_state") == "ACTIVE":
                errors.append(f"{component_id}: terminal history cannot silently reactivate")
    return errors


def validate_actor_registry(dataset: Any) -> list[str]:
    if not isinstance(dataset, dict):
        return ["Actor Registry must be an object"]
    actors = dataset.get("actors")
    relationships = dataset.get("relationships", [])
    if not isinstance(actors, list) or not isinstance(relationships, list):
        return ["Actor Registry actors and relationships must be lists"]
    errors: list[str] = []
    by_actor: dict[str, list[dict[str, Any]]] = {}
    by_revision: set[str] = set()
    forbidden = {"intent", "policy_position", "capability", "constraint", "belief", "commitment", "implementation_state"}
    for actor in actors:
        if not isinstance(actor, dict):
            errors.append("Actor Registry actor must be an object")
            continue
        for field in ("actor_id", "identity_revision_id", "canonical_label", "actor_type", "aliases", "jurisdiction", "effective_from", "effective_to", "identity_provenance", "review_state", "parent_actor_ids", "object_sha256"):
            if field not in actor:
                errors.append(f"Actor Registry actor missing {field}")
        if actor.get("actor_type") not in ACTOR_TYPES:
            errors.append("Actor Registry actor_type is invalid")
        if forbidden & set(actor):
            errors.append(f"Actor Registry identity contains mutable claim fields: {sorted(forbidden & set(actor))}")
        if actor.get("identity_revision_id") in by_revision:
            errors.append("duplicate Actor Registry identity revision")
        by_revision.add(actor.get("identity_revision_id"))
        if not _hash(actor.get("object_sha256")) or actor.get("object_sha256") != fingerprint(actor, exclude={"object_sha256"}):
            errors.append(f"Actor Registry fingerprint mismatch for {actor.get('actor_id')}")
        _utc(actor.get("effective_from"), "actor.effective_from", errors, required=True)
        _utc(actor.get("effective_to"), "actor.effective_to", errors)
        if actor.get("review_state") not in {"CANDIDATE", "UNDER_REVIEW", "ACCEPTED", "REJECTED"}:
            errors.append("Actor Registry review_state is invalid")
        by_actor.setdefault(actor.get("actor_id"), []).append(actor)
    actor_ids = set(by_actor)
    for actor_id, history in by_actor.items():
        if not _text(actor_id):
            errors.append("actor_id is required")
        numbers = sorted(row.get("identity_revision_number", 0) for row in history)
        if numbers != list(range(1, len(numbers) + 1)):
            errors.append(f"{actor_id}: identity revision numbers must be contiguous")
        for row in history:
            if not isinstance(row.get("aliases"), list) or not all(_text(alias) for alias in row["aliases"]):
                errors.append(f"{actor_id}: aliases must be text list")
            if not isinstance(row.get("parent_actor_ids"), list) or any(parent not in actor_ids for parent in row["parent_actor_ids"]):
                errors.append(f"{actor_id}: parent actor references must resolve")
    for relationship in relationships:
        if not isinstance(relationship, dict):
            errors.append("Actor Registry relationship must be an object")
            continue
        if relationship.get("relationship_type") not in ACTOR_RELATIONSHIP_TYPES:
            errors.append("Actor Registry relationship_type is invalid")
        if relationship.get("subject_actor_id") not in actor_ids or relationship.get("object_actor_id") not in actor_ids:
            errors.append("Actor Registry relationship endpoint is unknown")
        if relationship.get("subject_actor_id") == relationship.get("object_actor_id"):
            errors.append("Actor Registry relationship cannot self-link")
        _utc(relationship.get("effective_from"), "relationship.effective_from", errors, required=True)
        _utc(relationship.get("effective_to"), "relationship.effective_to", errors)
    return errors


def validate_history_query(query: Any) -> list[str]:
    if not isinstance(query, dict):
        return ["WorldStateHistoryQuery must be an object"]
    errors: list[str] = []
    if query.get("query_mode") not in QUERY_MODES:
        errors.append("query_mode must be KNOWLEDGE_AS_OF or EFFECTIVE_AS_OF")
    _utc(query.get("knowledge_cutoff_utc"), "knowledge_cutoff_utc", errors, required=True)
    if query.get("query_mode") == "EFFECTIVE_AS_OF":
        _utc(query.get("effective_as_of_utc"), "effective_as_of_utc", errors, required=True)
    elif query.get("effective_as_of_utc") is not None:
        _utc(query.get("effective_as_of_utc"), "effective_as_of_utc", errors)
    if not isinstance(query.get("scope"), dict):
        errors.append("scope is required")
    if not isinstance(query.get("include_withdrawn_history"), bool):
        errors.append("include_withdrawn_history must be boolean")
    return errors


def select_component_revisions(rows: list[dict[str, Any]], query: dict[str, Any]) -> list[dict[str, Any]]:
    errors = validate_history_query(query)
    if errors:
        raise WorldStateHistoryError("; ".join(errors))
    knowledge = datetime.fromisoformat(query["knowledge_cutoff_utc"][:-1] + "+00:00")
    effective = None
    if query["query_mode"] == "EFFECTIVE_AS_OF":
        effective = datetime.fromisoformat(query["effective_as_of_utc"][:-1] + "+00:00")
    eligible: list[dict[str, Any]] = []
    for row in rows:
        if row.get("review_state") != "ACCEPTED" or not row.get("admitted_at_utc"):
            continue
        admitted = datetime.fromisoformat(row["admitted_at_utc"][:-1] + "+00:00")
        known = datetime.fromisoformat(row["known_at_utc"][:-1] + "+00:00")
        if known > knowledge or admitted > knowledge:
            continue
        if row.get("lifecycle_state") in {"WITHDRAWN", "EXPIRED"} and not query["include_withdrawn_history"]:
            continue
        if effective is not None:
            if not row.get("effective_at"):
                continue
            row_effective = datetime.fromisoformat(row["effective_at"][:-1] + "+00:00")
            if row_effective > effective:
                continue
        eligible.append(row)
    selected: dict[str, dict[str, Any]] = {}
    for row in sorted(eligible, key=lambda item: (item["component_id"], item["revision_number"])):
        selected[row["component_id"]] = row
    return [selected[key] for key in sorted(selected)]


def validate_snapshot(snapshot: Any, *, component_index: dict[tuple[str, str], dict[str, Any]] | None = None) -> list[str]:
    if not isinstance(snapshot, dict):
        return ["snapshot must be an object"]
    errors: list[str] = []
    required = ("snapshot_series_id", "snapshot_revision_id", "revision_number", "previous_snapshot_revision_id", "snapshot_kind", "scope", "knowledge_cutoff_utc", "effective_as_of_utc", "component_refs", "upstream_refs", "source_manifest_sha256", "proposal_id", "review_transaction_id", "admission_transaction_id", "limitations", "empty_queried_domains", "lifecycle_state", "visibility", "reviewer", "admitted_at_utc", "object_sha256")
    for field in required:
        if field not in snapshot:
            errors.append(f"snapshot missing {field}")
    for field in ("snapshot_series_id", "snapshot_revision_id", "snapshot_kind", "proposal_id", "review_transaction_id", "admission_transaction_id"):
        if not _text(snapshot.get(field)):
            errors.append(f"snapshot {field} is required")
    if type(snapshot.get("revision_number")) is not int or snapshot["revision_number"] < 1:
        errors.append("snapshot revision_number must be positive")
    _utc(snapshot.get("knowledge_cutoff_utc"), "snapshot.knowledge_cutoff_utc", errors, required=True)
    _utc(snapshot.get("effective_as_of_utc"), "snapshot.effective_as_of_utc", errors)
    _utc(snapshot.get("admitted_at_utc"), "snapshot.admitted_at_utc", errors, required=True)
    if snapshot.get("lifecycle_state") not in {"ACTIVE", "SUPERSEDED", "CORRECTED", "WITHDRAWN", "EXPIRED"}:
        errors.append("snapshot lifecycle_state is invalid")
    if snapshot.get("visibility") not in VISIBILITY_STATES:
        errors.append("snapshot visibility is invalid")
    if not _hash(snapshot.get("source_manifest_sha256")):
        errors.append("snapshot source_manifest_sha256 must be a SHA-256 hash")
    if not _list(snapshot.get("component_refs")) or not _list(snapshot.get("upstream_refs")):
        errors.append("snapshot component_refs and upstream_refs must be lists")
    seen: set[tuple[str, str]] = set()
    for index, ref in enumerate(snapshot.get("component_refs", [])):
        if not isinstance(ref, dict) or set(ref) != {"component_type", "component_id", "revision_id", "object_sha256"}:
            errors.append(f"component_refs[{index}] must be an exact immutable reference")
            continue
        key = (ref["component_type"], ref["revision_id"])
        if key in seen:
            errors.append("snapshot contains duplicate component reference")
        seen.add(key)
        if ref["component_type"] not in COMPONENT_TYPES:
            errors.append("snapshot cannot own a transmission component")
        if not _hash(ref["object_sha256"]):
            errors.append("component reference hash is invalid")
        if component_index is not None:
            row = component_index.get(key)
            if row is None:
                errors.append(f"snapshot component reference unavailable: {key}")
            elif row.get("component_id") != ref.get("component_id") or row.get("object_sha256") != ref.get("object_sha256"):
                errors.append(f"snapshot component reference mismatch: {key}")
    for index, ref in enumerate(snapshot.get("upstream_refs", [])):
        errors.extend(validate_epistemic_citation(ref, label=f"upstream_refs[{index}]"))
        if isinstance(ref, dict) and "content" in ref:
            errors.append("snapshot upstream references cannot copy source content")
    for index, domain in enumerate(snapshot.get("empty_queried_domains", [])):
        if not isinstance(domain, dict) or domain.get("state") not in EMPTY_DOMAIN_STATES or not _text(domain.get("domain")):
            errors.append(f"empty_queried_domains[{index}] must distinguish governed empty states")
    if not _hash(snapshot.get("object_sha256")) or snapshot.get("object_sha256") != fingerprint(snapshot, exclude={"object_sha256"}):
        errors.append("snapshot object_sha256 does not match snapshot content")
    return errors


def validate_snapshot_history(rows: Any, *, previous_revisions: list[dict[str, Any]] | None = None, component_index: dict[tuple[str, str], dict[str, Any]] | None = None) -> list[str]:
    """Validate an append-only snapshot series without selecting a latest head."""
    if not isinstance(rows, list):
        return ["snapshot history must be a list"]
    errors: list[str] = []
    by_series: dict[str, list[dict[str, Any]]] = {}
    seen_revision_ids: set[str] = set()
    for row in rows:
        errors.extend(validate_snapshot(row, component_index=component_index))
        if isinstance(row, dict):
            revision_id = row.get("snapshot_revision_id")
            if revision_id in seen_revision_ids:
                errors.append(f"duplicate snapshot revision_id {revision_id}")
            seen_revision_ids.add(revision_id)
            if _text(row.get("snapshot_series_id")):
                by_series.setdefault(row["snapshot_series_id"], []).append(row)
    if previous_revisions is not None:
        current = {row.get("snapshot_revision_id"): row for row in rows if isinstance(row, dict)}
        for old in previous_revisions:
            if not isinstance(old, dict) or current.get(old.get("snapshot_revision_id")) != old:
                errors.append("retained snapshot revision was removed or rewritten")
    for series_id, history in by_series.items():
        ordered = sorted(history, key=lambda row: row.get("revision_number", 0))
        numbers = [row.get("revision_number") for row in ordered]
        if numbers != list(range(1, len(numbers) + 1)):
            errors.append(f"{series_id}: snapshot revision numbers must be contiguous")
        for index, row in enumerate(ordered):
            predecessor = row.get("previous_snapshot_revision_id")
            if index == 0 and predecessor is not None:
                errors.append(f"{series_id}: first snapshot cannot have predecessor")
            if index > 0 and predecessor != ordered[index - 1].get("snapshot_revision_id"):
                errors.append(f"{series_id}: snapshot predecessor chain is not preserved")
    return errors


def validate_admission_transaction(transaction: Any) -> list[str]:
    if not isinstance(transaction, dict):
        return ["admission transaction must be an object"]
    errors: list[str] = []
    required = ("transaction_id", "contract_version", "transaction_type", "decision", "proposal_id", "proposal_semantic_fingerprint", "source_manifest_sha256", "component_fingerprints", "reviewer", "decided_at_utc", "component_dispositions", "snapshot_revision_identity", "write_targets", "pre_state_hashes", "post_state_hashes", "visibility_decision", "admitted_at_utc", "validator_version", "transaction_fingerprint")
    for field in required:
        if field not in transaction:
            errors.append(f"admission transaction missing {field}")
    if transaction.get("transaction_type") != "WORLD_STATE_PRODUCTION_ADMISSION":
        errors.append("transaction_type must be WORLD_STATE_PRODUCTION_ADMISSION")
    if transaction.get("decision") not in {"ACCEPTED", "REJECTED", "RETURNED_FOR_REVIEW"}:
        errors.append("admission decision is invalid")
    for field in ("transaction_id", "contract_version", "proposal_id", "validator_version"):
        if not _text(transaction.get(field)):
            errors.append(f"admission {field} is required")
    for field in ("proposal_semantic_fingerprint", "source_manifest_sha256"):
        if not _hash(transaction.get(field)):
            errors.append(f"admission {field} must be a SHA-256 hash")
    _utc(transaction.get("decided_at_utc"), "decided_at_utc", errors, required=True)
    _utc(transaction.get("admitted_at_utc"), "admitted_at_utc", errors, required=True)
    if not isinstance(transaction.get("reviewer"), dict) or not _text(transaction.get("reviewer", {}).get("reviewer_id")):
        errors.append("admission reviewer.reviewer_id is required")
    if not isinstance(transaction.get("component_fingerprints"), list):
        errors.append("component_fingerprints must be a list")
    else:
        for ref in transaction["component_fingerprints"]:
            if not isinstance(ref, dict) or set(ref) != {"component_type", "component_id", "revision_id", "object_sha256"}:
                errors.append("component fingerprint must be an exact object reference")
            elif not _hash(ref.get("object_sha256")):
                errors.append("component fingerprint hash is invalid")
    dispositions = transaction.get("component_dispositions")
    if not isinstance(dispositions, list) or not dispositions:
        errors.append("component_dispositions must be non-empty")
    else:
        disposition_ids: set[tuple[str, str]] = set()
        for disposition in dispositions:
            if not isinstance(disposition, dict) or disposition.get("disposition") not in {"ADMITTED", "REJECTED", "DEFERRED"}:
                errors.append("component disposition is invalid")
                continue
            key = (disposition.get("component_id"), disposition.get("revision_id"))
            if key in disposition_ids:
                errors.append("duplicate component disposition")
            disposition_ids.add(key)
            if not _text(disposition.get("reason")):
                errors.append("component disposition reason is required")
    identity = transaction.get("snapshot_revision_identity")
    if not isinstance(identity, dict) or not _text(identity.get("snapshot_series_id")) or not _text(identity.get("snapshot_revision_id")):
        errors.append("snapshot_revision_identity is required")
    if not isinstance(transaction.get("write_targets"), list) or not transaction["write_targets"] or not all(_text(target) for target in transaction["write_targets"]):
        errors.append("accepted admission requires explicit non-empty write_targets")
    for field in ("pre_state_hashes", "post_state_hashes"):
        hashes = transaction.get(field)
        if not isinstance(hashes, dict) or not hashes or any(not _hash(value) for value in hashes.values()):
            errors.append(f"{field} must contain SHA-256 state hashes")
    if transaction.get("visibility_decision") not in VISIBILITY_STATES:
        errors.append("visibility_decision is invalid")
    if transaction.get("transaction_fingerprint") != fingerprint(transaction, exclude={"transaction_fingerprint"}):
        errors.append("transaction_fingerprint does not match transaction content")
    if transaction.get("decision") == "ACCEPTED" and transaction.get("admitted_at_utc") is None:
        errors.append("accepted admission requires admitted_at_utc")
    if transaction.get("transaction_type") == "WORLD_STATE_SYNTHESIS_REVIEW":
        errors.append("Step 5 review transaction cannot be production admission")
    return errors


def state_hashes(state: dict[str, Any]) -> dict[str, str]:
    """Hash temporary state collections; this function performs no I/O."""
    return {
        "actors": fingerprint(state.get("actors", [])),
        "components": fingerprint(sorted(state.get("components", []), key=lambda row: row.get("revision_id", ""))),
        "snapshots": fingerprint(sorted(state.get("snapshots", []), key=lambda row: row.get("snapshot_revision_id", ""))),
    }


def simulate_production_admission(
    transaction: dict[str, Any],
    *,
    current_state: dict[str, Any],
    candidate_components: list[dict[str, Any]],
    candidate_snapshot: dict[str, Any],
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate and compose an admission entirely in memory.

    The returned report is deterministic for identical semantic inputs.  No
    filesystem path is accepted and no repository data is read or written.
    """
    errors = validate_admission_transaction(transaction)
    before = deepcopy(current_state)
    before_hashes = state_hashes(before)
    if transaction.get("pre_state_hashes") != before_hashes:
        errors.append("declared pre-state hashes do not match temporary current state")
    errors.extend(validate_component_history(candidate_components, registry=registry))
    component_by_key = {(row.get("component_type"), row.get("revision_id")): row for row in candidate_components if isinstance(row, dict)}
    dispositions = {(row.get("component_id"), row.get("revision_id")): row.get("disposition") for row in transaction.get("component_dispositions", []) if isinstance(row, dict)}
    admitted_keys = {key for key, disposition in dispositions.items() if disposition == "ADMITTED"}
    rejected_or_deferred = {key for key, disposition in dispositions.items() if disposition in {"REJECTED", "DEFERRED"}}
    if admitted_keys & rejected_or_deferred:
        errors.append("component cannot be both admitted and rejected/deferred")
    for key in admitted_keys:
        if key not in {(row.get("component_id"), row.get("revision_id")) for row in candidate_components}:
            errors.append(f"admitted component is unavailable: {key}")
    snapshot_errors = validate_snapshot(candidate_snapshot, component_index=component_by_key)
    errors.extend(snapshot_errors)
    snapshot_keys = {(ref.get("component_id"), ref.get("revision_id")) for ref in candidate_snapshot.get("component_refs", []) if isinstance(ref, dict)}
    if not snapshot_keys <= admitted_keys:
        errors.append("snapshot includes a component that is not ADMITTED")
    post = deepcopy(before)
    post.setdefault("components", [])
    post.setdefault("snapshots", [])
    post["components"].extend(row for row in candidate_components if (row.get("component_id"), row.get("revision_id")) in admitted_keys)
    post["snapshots"].append(deepcopy(candidate_snapshot))
    after_hashes = state_hashes(post)
    if transaction.get("post_state_hashes") != after_hashes:
        errors.append("declared post-state hashes do not match simulated state")
    semantic = {
        "transaction_id": transaction.get("transaction_id"),
        "admitted": sorted([list(key) for key in admitted_keys]),
        "excluded": sorted([list(key) for key in rejected_or_deferred]),
        "pre_state_hashes": before_hashes,
        "post_state_hashes": after_hashes,
        "snapshot_revision_id": candidate_snapshot.get("snapshot_revision_id"),
        "status": "PASS" if not errors else "FAIL",
    }
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "pre_state_hashes_before": before_hashes,
        "pre_state_hashes_after": state_hashes(before),
        "post_state_hashes": after_hashes,
        "admitted_component_refs": sorted([list(key) for key in admitted_keys]),
        "excluded_component_refs": sorted([list(key) for key in rejected_or_deferred]),
        "governed_files_written": False,
        "simulation_fingerprint": fingerprint(semantic),
    }


def validate_upstream_reference_ownership(ref: dict[str, Any], *, expected_layer: str | None = None) -> list[str]:
    errors = validate_epistemic_citation(ref)
    if expected_layer and ref.get("layer") != expected_layer:
        errors.append(f"reference layer must be {expected_layer}")
    if ref.get("layer") == "RELATIONSHIPS" and ref.get("epistemic_class") != "INFERRED_RELATIONSHIP":
        errors.append("Relationship reference must retain INFERRED_RELATIONSHIP class")
    if ref.get("layer") == "FORECASTS" and ref.get("epistemic_class") != "FORECAST":
        errors.append("Forecast reference must retain FORECAST class")
    return errors


def canonical_historical_dependency_result(*, requires_historical_canonical: bool, canonical_selector_available: bool = False) -> dict[str, Any]:
    if requires_historical_canonical and not canonical_selector_available:
        return {
            "status": "UNSUPPORTED_DEPENDENCY",
            "code": "CANONICAL_HISTORICAL_AS_OF_UNSUPPORTED",
            "admission_permitted": False,
            "detail": "Mixed-precision Canonical history cannot be reconstructed without a dedicated selector.",
        }
    return {"status": "SUPPORTED", "admission_permitted": True}
