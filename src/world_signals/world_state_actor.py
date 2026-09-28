"""Read-only actor identity admission boundary for World State candidates.

This module deliberately stops before production Actor Registry population.  It
validates identity-only candidates, detects alias collisions, and can simulate
an explicit human-reviewed identity admission in a temporary in-memory copy.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from .world_state_history import ACTOR_TYPES, fingerprint, validate_actor_registry, with_object_fingerprint


ACTOR_IDENTITY_ADMISSION_TRANSACTION_TYPE = "WORLD_STATE_ACTOR_IDENTITY_ADMISSION"
ACTOR_IDENTITY_REVIEW_STATES = {"CANDIDATE", "UNDER_REVIEW", "ACCEPTED", "REJECTED"}
MUTABLE_ACTOR_FIELDS = {
    "intent", "policy_position", "capability", "constraint", "belief",
    "commitment", "implementation_state",
}


class ActorIdentityAdmissionError(ValueError):
    """Raised when an actor identity admission preflight fails closed."""


def _utc(value: Any, label: str, *, required: bool = False) -> str | None:
    if value is None:
        if required:
            raise ActorIdentityAdmissionError(f"{label} is required")
        return None
    if not isinstance(value, str) or len(value) != 20 or not value.endswith("Z"):
        raise ActorIdentityAdmissionError(f"{label} must be exact UTC")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ActorIdentityAdmissionError(f"{label} is invalid UTC") from exc
    if parsed.tzinfo != timezone.utc:
        raise ActorIdentityAdmissionError(f"{label} must use UTC")
    return value


def _alias_key(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def _normalise_aliases(canonical_label: str, aliases: list[str]) -> list[str]:
    values = [canonical_label, *aliases]
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ActorIdentityAdmissionError("actor aliases must be non-empty text")
        key = _alias_key(value)
        if key not in seen:
            seen.add(key)
            result.append(value.strip())
    return result


def _citation(ref: dict[str, Any]) -> dict[str, Any]:
    return {
        "layer": ref["layer"],
        "object_id": ref["object_id"],
        "revision_id": ref.get("revision_id"),
        "object_sha256": ref["object_sha256"],
    }


def build_actor_identity_candidate(
    *,
    actor_id: str,
    canonical_label: str,
    actor_type: str,
    aliases: list[str],
    jurisdiction: list[str],
    effective_from: str | None,
    provenance_refs: list[dict[str, Any]],
    effective_from_precision: str | None = None,
    identity_known_at_utc: str | None = None,
    identity_known_at_basis: str = "GOVERNED_IDENTITY_REVIEW_BOUNDARY",
) -> dict[str, Any]:
    """Construct identity-only, under-review actor data without admission fields."""
    if actor_type not in ACTOR_TYPES:
        raise ActorIdentityAdmissionError(f"unsupported actor_type: {actor_type}")
    if not actor_id.strip() or not canonical_label.strip():
        raise ActorIdentityAdmissionError("actor_id and canonical_label are required")
    if not isinstance(jurisdiction, list) or not all(isinstance(item, str) and item.strip() for item in jurisdiction):
        raise ActorIdentityAdmissionError("jurisdiction must be a non-empty text list")
    if not provenance_refs:
        raise ActorIdentityAdmissionError("identity provenance is required")
    identity_provenance = [_citation(ref) for ref in provenance_refs]
    if effective_from is None:
        if effective_from_precision != "UNKNOWN":
            raise ActorIdentityAdmissionError("unknown effective_from requires effective_from_precision=UNKNOWN")
    elif effective_from_precision not in {None, "UTC_INSTANT"}:
        raise ActorIdentityAdmissionError("known effective_from must be an exact UTC instant")
    known_at = identity_known_at_utc or effective_from
    if known_at is None:
        raise ActorIdentityAdmissionError("identity_known_at_utc is required")
    _utc(known_at, "identity_known_at_utc", required=True)
    candidate = {
        "actor_id": actor_id,
        "identity_revision_id": f"{actor_id}-R1",
        "identity_revision_number": 1,
        "canonical_label": canonical_label.strip(),
        "actor_type": actor_type,
        "aliases": _normalise_aliases(canonical_label, aliases),
        "jurisdiction": jurisdiction,
        "effective_from": _utc(effective_from, "effective_from"),
        "effective_to": None,
        "identity_provenance": identity_provenance,
        "review_state": "UNDER_REVIEW",
        "parent_actor_ids": [],
        "object_sha256": None,
    }
    # Preserve the pre-Step-11A shape for legacy known-time candidates. New
    # unknown-bound identities must carry the explicit temporal fields.
    if effective_from is None or effective_from_precision is not None or identity_known_at_utc is not None:
        candidate["effective_from_precision"] = effective_from_precision or "UTC_INSTANT"
        candidate["identity_known_at_utc"] = known_at
        candidate["identity_known_at_basis"] = identity_known_at_basis
    return with_object_fingerprint(candidate)


def _registry_aliases(registry: dict[str, Any]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for actor in registry.get("actors", []):
        for alias in [actor.get("canonical_label"), *(actor.get("aliases") or [])]:
            if isinstance(alias, str):
                aliases[_alias_key(alias)] = actor.get("actor_id")
    return aliases


def validate_actor_identity_candidate(candidate: Any, *, existing_registry: dict[str, Any] | None = None) -> list[str]:
    """Validate identity-only semantics and reject collisions or admission claims."""
    errors: list[str] = []
    if not isinstance(candidate, dict):
        return ["actor identity candidate must be an object"]
    errors.extend(validate_actor_registry({"actors": [candidate], "relationships": []}))
    if candidate.get("review_state") not in {"CANDIDATE", "UNDER_REVIEW"}:
        errors.append("actor identity candidate must remain under review")
    if candidate.get("effective_from") is None and candidate.get("effective_from_precision") != "UNKNOWN":
        errors.append("unknown effective_from requires explicit UNKNOWN precision")
    if candidate.get("effective_from") is not None and candidate.get("effective_from_precision") not in {"UTC_INSTANT", None}:
        errors.append("known effective_from must use UTC_INSTANT precision")
    if candidate.get("effective_from") is None or "identity_known_at_utc" in candidate:
        try:
            _utc(candidate.get("identity_known_at_utc"), "identity_known_at_utc", required=True)
        except ActorIdentityAdmissionError as exc:
            errors.append(str(exc))
    if candidate.get("effective_to") is not None and not isinstance(candidate.get("effective_to"), str):
        errors.append("effective_to must be UTC text or null")
    if MUTABLE_ACTOR_FIELDS & set(candidate):
        errors.append(f"mutable actor claim fields are prohibited: {sorted(MUTABLE_ACTOR_FIELDS & set(candidate))}")
    if any(field in candidate for field in ("admission_transaction_id", "admitted_at_utc")):
        errors.append("identity candidate cannot carry production admission metadata")
    aliases = candidate.get("aliases")
    if isinstance(aliases, list):
        keys = [_alias_key(value) for value in aliases if isinstance(value, str)]
        if len(keys) != len(set(keys)):
            errors.append("actor aliases collide within candidate")
    if existing_registry is not None:
        if any(row.get("actor_id") == candidate.get("actor_id") for row in existing_registry.get("actors", [])):
            errors.append("actor_id already exists in Actor Registry")
        occupied = _registry_aliases(existing_registry)
        for alias in [candidate.get("canonical_label"), *(candidate.get("aliases") or [])]:
            owner = occupied.get(_alias_key(alias))
            if owner and owner != candidate.get("actor_id"):
                errors.append(f"actor alias already belongs to {owner}")
    return errors


def build_actor_identity_admission_transaction(
    candidate: dict[str, Any],
    *,
    reviewer_id: str,
    decided_at_utc: str,
    admitted_at_utc: str,
    pre_state_hashes: dict[str, str],
    post_state_hashes: dict[str, str],
    write_targets: list[str],
) -> dict[str, Any]:
    errors = validate_actor_identity_candidate(candidate)
    if errors:
        raise ActorIdentityAdmissionError("candidate failed identity validation: " + "; ".join(errors))
    _utc(decided_at_utc, "decided_at_utc", required=True)
    _utc(admitted_at_utc, "admitted_at_utc", required=True)
    if not reviewer_id.strip():
        raise ActorIdentityAdmissionError("reviewer_id is required")
    transaction = {
        "transaction_id": f"WS-ACTOR-IDENTITY-SIMULATION-{candidate['actor_id']}",
        "contract_version": "0.1",
        "transaction_type": ACTOR_IDENTITY_ADMISSION_TRANSACTION_TYPE,
        "decision": "ACCEPTED",
        "candidate_actor_id": candidate["actor_id"],
        "candidate_identity_revision_id": candidate["identity_revision_id"],
        "candidate_fingerprint": candidate["object_sha256"],
        "reviewer": {"reviewer_id": reviewer_id, "role": "human-review-required"},
        "decided_at_utc": decided_at_utc,
        "admitted_at_utc": admitted_at_utc,
        "pre_state_hashes": deepcopy(pre_state_hashes),
        "post_state_hashes": deepcopy(post_state_hashes),
        "write_targets": list(write_targets),
        "production_write_performed": False,
        "validator_version": "world-state-actor-identity-v1",
        "transaction_fingerprint": None,
    }
    transaction["transaction_fingerprint"] = fingerprint(transaction, exclude={"transaction_fingerprint"})
    return transaction


def simulate_actor_identity_admission(
    candidate: dict[str, Any],
    transaction: dict[str, Any],
    *,
    existing_registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Simulate identity admission in memory; never writes the Actor Registry."""
    registry = deepcopy(existing_registry or {"actors": [], "relationships": []})
    errors = validate_actor_identity_candidate(candidate, existing_registry=registry)
    if errors:
        raise ActorIdentityAdmissionError("simulation failed: " + "; ".join(errors))
    if transaction.get("transaction_type") != ACTOR_IDENTITY_ADMISSION_TRANSACTION_TYPE or transaction.get("decision") != "ACCEPTED":
        raise ActorIdentityAdmissionError("identity simulation requires explicit accepted identity transaction")
    if transaction.get("candidate_fingerprint") != candidate.get("object_sha256"):
        raise ActorIdentityAdmissionError("identity transaction candidate fingerprint mismatch")
    admitted = deepcopy(candidate)
    admitted["review_state"] = "ACCEPTED"
    admitted["identity_admission_transaction_id"] = transaction["transaction_id"]
    admitted["identity_admitted_at_utc"] = transaction["admitted_at_utc"]
    admitted = with_object_fingerprint(admitted)
    registry["actors"].append(admitted)
    validation_errors = validate_actor_registry(registry)
    if validation_errors:
        raise ActorIdentityAdmissionError("simulated admitted registry failed: " + "; ".join(validation_errors))
    return {
        "status": "PASS",
        "production_write_performed": False,
        "candidate": deepcopy(candidate),
        "simulated_admitted_actor": admitted,
        "before": existing_registry or {"actors": [], "relationships": []},
        "after": registry,
        "limitations": [
            "Simulation is temporary and is not a production Actor Registry admission.",
            "Actor identity remains separate from actor state, capability, intent and implementation claims.",
        ],
    }


def actor_reference_admissible(actor_id: str, registry: dict[str, Any]) -> bool:
    return any(row.get("actor_id") == actor_id and row.get("review_state") == "ACCEPTED" for row in registry.get("actors", []))


def actor_identity_known_as_of(actor: dict[str, Any], knowledge_cutoff_utc: str) -> bool:
    """Return whether identity evidence was known by the explicit cutoff."""
    known = _utc(actor.get("identity_known_at_utc"), "identity_known_at_utc", required=True)
    cutoff = _utc(knowledge_cutoff_utc, "knowledge_cutoff_utc", required=True)
    return known <= cutoff


def actor_identity_effective_as_of(actor: dict[str, Any], effective_as_of_utc: str) -> bool:
    """Fail closed when an identity's historical start bound is unknown."""
    if actor.get("effective_from") is None or actor.get("effective_from_precision") == "UNKNOWN":
        return False
    effective = _utc(actor["effective_from"], "effective_from", required=True)
    cutoff = _utc(effective_as_of_utc, "effective_as_of_utc", required=True)
    return effective <= cutoff
