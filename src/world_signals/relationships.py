"""Closed, reviewed Relationship contract over Signals.

Relationships describe reviewed analytical connections.  They do not mutate
Signals, create transitive graph edges, score risk or forecast outcomes.  The
production population is intentionally empty while this contract is tested
with synthetic, read-only proposal histories.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any


@dataclass(frozen=True)
class RelationshipValidationReport:
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _strings(value: Any) -> bool:
    return isinstance(value, list) and all(_text(item) for item in value)


def _parse_exact_utc(value: Any) -> datetime | None:
    if not _text(value):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        return None
    return parsed.astimezone(timezone.utc)


def _all_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return {str(key) for key in value} | {child for item in value.values() for child in _all_keys(item)}
    if isinstance(value, list):
        return {child for item in value for child in _all_keys(item)}
    return set()


def _preflight(
    schema: Any,
    dataset: Any,
    signals: Any,
    observations: Any,
    evidence: Any,
    canonical: Any,
) -> list[str]:
    errors: list[str] = []
    values = (schema, dataset, signals, observations, evidence, canonical)
    if not all(isinstance(value, dict) for value in values):
        return ["schema and relationship inputs must be objects"]
    try:
        json.dumps(values, allow_nan=False)
    except (TypeError, ValueError):
        return ["relationship inputs must contain finite JSON values"]

    if schema.get("version") != "0.1":
        errors.append("unsupported Relationship schema version")
    for key in ("layer_boundary", "population_policy", "public_projection_policy", "controlled_vocabularies"):
        if not isinstance(schema.get(key), dict):
            errors.append(f"{key} must be an object")
    for key in ("required_relationship_fields",):
        if not _strings(schema.get(key)) or not schema[key]:
            errors.append(f"{key} must be a non-empty string list")
    for key in ("relationships",):
        if not isinstance(dataset.get(key), list):
            errors.append(f"{key} must be a list")
    for data, key, id_key in (
        (signals, "signals", "signal_id"),
        (observations, "observations", "observation_id"),
        (evidence, "evidence", "evidence_id"),
        (canonical, "records", "occurrence_id"),
    ):
        if not isinstance(data.get(key), list):
            errors.append(f"{key} must be a list")
            continue
        for row in data[key]:
            if not isinstance(row, dict) or not _text(row.get(id_key)):
                errors.append(f"{id_key} must be non-empty text")
            elif key == "signals":
                if not _text(row.get("revision_id")):
                    errors.append("Signal revision_id must be non-empty text")
                if type(row.get("revision_number")) is not int or row["revision_number"] < 1:
                    errors.append("Signal revision_number must be positive integer")
                if not _text(row.get("review_state")) or not _text(row.get("lifecycle_state")):
                    errors.append("Signal review/lifecycle state must be non-empty text")

    vocabs = schema.get("controlled_vocabularies")
    if not isinstance(vocabs, dict):
        return errors
    for key in (
        "relationship_class", "directionality", "node_type", "confidence", "review_state",
        "lifecycle_state", "temporal_scope_type", "causal_basis",
    ):
        if not _strings(vocabs.get(key)) or not vocabs[key]:
            errors.append(f"invalid Relationship vocabulary {key}")

    required = set(schema.get("required_relationship_fields") or [])
    rows = dataset.get("relationships")
    if not isinstance(rows, list):
        return errors
    for row in rows:
        if not isinstance(row, dict):
            errors.append("Relationship rows must be objects")
            continue
        if set(row) != required:
            errors.append("missing/unknown Relationship fields; forecast/scenario fields are prohibited")
            continue
        for key in (
            "relationship_id", "revision_id", "title", "relationship_class", "directionality",
            "directionality_rationale", "rationale", "mechanism", "confidence", "review_state",
            "lifecycle_state", "first_asserted_at_utc", "revision_reason",
        ):
            if key == "mechanism":
                valid_text = isinstance(row.get(key), str)
            else:
                valid_text = _text(row.get(key))
            if not valid_text:
                errors.append(f"{key} must be non-empty text")
        if type(row.get("revision_number")) is not int or row["revision_number"] < 1:
            errors.append("revision_number must be a positive integer")
        if row.get("previous_revision_id") is not None and not _text(row["previous_revision_id"]):
            errors.append("previous_revision_id must be null or non-empty text")
        vocab = schema["controlled_vocabularies"]
        if row.get("relationship_class") not in vocab["relationship_class"]:
            errors.append("invalid relationship_class")
        if row.get("directionality") not in vocab["directionality"]:
            errors.append("invalid directionality")
        if row.get("confidence") not in vocab["confidence"]:
            errors.append("invalid relationship confidence")
        if row.get("review_state") not in vocab["review_state"]:
            errors.append("invalid relationship review_state")
        if row.get("lifecycle_state") not in vocab["lifecycle_state"]:
            errors.append("invalid relationship lifecycle_state")

        for key in (
            "supporting_observation_ids", "supporting_evidence_refs", "contradictory_evidence_refs",
            "contextual_canonical_occurrence_ids", "domains", "jurisdictions", "alternative_explanations",
            "confounders", "common_driver_signal_ids", "causal_basis", "falsification_conditions",
        ):
            if not _strings(row.get(key)):
                errors.append(f"{key} must be a list of strings")
        for key in ("source_nodes", "target_nodes"):
            nodes = row.get(key)
            if not isinstance(nodes, list) or not nodes:
                errors.append(f"{key} must be a non-empty list")
                continue
            for node in nodes:
                if not isinstance(node, dict) or set(node) != {"node_id", "node_type"}:
                    errors.append(f"{key} entries must contain only node_id and node_type")
                    continue
                if not _text(node.get("node_id")) or node.get("node_type") not in vocab["node_type"]:
                    errors.append(f"{key} contains an invalid Signal node")
        pins = row.get("supporting_signal_revisions")
        if not isinstance(pins, list) or not pins:
            errors.append("supporting_signal_revisions must be a non-empty list")
        else:
            for pin in pins:
                if not isinstance(pin, dict) or set(pin) != {"signal_id", "revision_id"}:
                    errors.append("supporting_signal_revisions entries must contain signal_id and revision_id")
                    continue
                if not _text(pin.get("signal_id")) or not _text(pin.get("revision_id")):
                    errors.append("supporting_signal_revisions IDs must be non-empty text")
        scope = row.get("temporal_scope")
        scope_fields = {"scope_type", "start_at_utc", "end_at_utc", "notes"}
        if not isinstance(scope, dict) or set(scope) != scope_fields:
            errors.append("temporal_scope has an invalid field set")
        else:
            if scope.get("scope_type") not in vocab["temporal_scope_type"]:
                errors.append("invalid temporal scope type")
            if _parse_exact_utc(scope.get("start_at_utc")) is None:
                errors.append("temporal_scope.start_at_utc must be exact UTC")
            if scope.get("end_at_utc") is not None and _parse_exact_utc(scope.get("end_at_utc")) is None:
                errors.append("temporal_scope.end_at_utc must be exact UTC or null")
            if not _text(scope.get("notes")):
                errors.append("temporal_scope.notes is required")
        provenance = row.get("review_provenance")
        provenance_fields = {"created_by", "created_at_utc", "reviewed_by", "reviewed_at_utc", "decision_basis"}
        if not isinstance(provenance, dict) or set(provenance) != provenance_fields:
            errors.append("review_provenance has an invalid field set")
        else:
            if not _text(provenance.get("created_by")) or _parse_exact_utc(provenance.get("created_at_utc")) is None:
                errors.append("review_provenance requires creator and exact UTC creation time")
            if provenance.get("reviewed_at_utc") is not None and _parse_exact_utc(provenance.get("reviewed_at_utc")) is None:
                errors.append("review_provenance.reviewed_at_utc must be exact UTC or null")
        if row.get("relationship_class") in {"MECHANISTICALLY_SUPPORTED", "CAUSAL_EVIDENCE"} and not row.get("causal_basis"):
            errors.append("strong relationship classes require explicit causal_basis")
        if row.get("relationship_class") == "COMMON_DRIVER" and not row.get("common_driver_signal_ids"):
            errors.append("COMMON_DRIVER requires common_driver_signal_ids")
        if row.get("relationship_class") != "COMMON_DRIVER" and row.get("common_driver_signal_ids"):
            errors.append("common_driver_signal_ids are only valid for COMMON_DRIVER")
    return errors


def _indexes(signals: dict[str, Any], observations: dict[str, Any], evidence: dict[str, Any], canonical: dict[str, Any]):
    signal_by_revision = {}
    signal_revisions_by_id = {}
    observation_by_id = {}
    evidence_by_id = {}
    canonical_by_id = {}
    for row in signals["signals"]:
        signal_by_revision[row["revision_id"]] = row
        signal_revisions_by_id.setdefault(row["signal_id"], []).append(row)
    for row in observations["observations"]:
        observation_by_id[row["observation_id"]] = row
    for row in evidence["evidence"]:
        evidence_by_id[row["evidence_id"]] = row
    for row in canonical["records"]:
        canonical_by_id[row["occurrence_id"]] = row
    signal_heads = {
        signal_id: max(rows, key=lambda row: row["revision_number"])
        for signal_id, rows in signal_revisions_by_id.items()
    }
    return signal_by_revision, signal_heads, observation_by_id, evidence_by_id, canonical_by_id


def _effective_time(row: dict[str, Any]) -> datetime:
    provenance = row["review_provenance"]
    return _parse_exact_utc(provenance.get("reviewed_at_utc") or provenance["created_at_utc"])


def _signal_created_at(row: dict[str, Any]) -> datetime | None:
    provenance = row.get("review_provenance")
    if not isinstance(provenance, dict):
        return None
    return _parse_exact_utc(provenance.get("created_at_utc"))


def _evidence_time(row: dict[str, Any]) -> datetime | None:
    publication = row.get("publication_time")
    if not isinstance(publication, dict):
        return None
    if publication.get("published_at_utc"):
        return _parse_exact_utc(publication.get("published_at_utc"))
    if _text(publication.get("published_date")):
        try:
            return datetime.fromisoformat(publication["published_date"]).replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def _validate_row(row, schema, signal_by_revision, signal_heads, observation_by_id, evidence_by_id, canonical_by_id, errors):
    rid = row["relationship_id"]
    source_ids = [node["node_id"] for node in row["source_nodes"]]
    target_ids = [node["node_id"] for node in row["target_nodes"]]
    if len(source_ids) != len(set(source_ids)) or len(target_ids) != len(set(target_ids)):
        errors.append(f"{rid}: duplicate endpoint Signal references")
    if set(source_ids) & set(target_ids):
        errors.append(f"{rid}: endpoint Signal cannot be both source and target")
    pins = row["supporting_signal_revisions"]
    pin_keys = [(pin["signal_id"], pin["revision_id"]) for pin in pins]
    if len(pin_keys) != len(set(pin_keys)):
        errors.append(f"{rid}: duplicate Signal revision pins cannot increase support")
    referenced_signal_ids = set(source_ids) | set(target_ids) | set(row["common_driver_signal_ids"])
    referenced_signal_ids |= {pin["signal_id"] for pin in pins}
    for signal_id, revision_id in pin_keys:
        signal = signal_by_revision.get(revision_id)
        if signal is None or signal.get("signal_id") != signal_id:
            errors.append(f"{rid}: unknown or mismatched Signal revision {signal_id}/{revision_id}")
    for signal_id in sorted(referenced_signal_ids):
        if signal_id not in signal_heads:
            errors.append(f"{rid}: unknown Signal reference {signal_id}")
    pinned_ids = {pin["signal_id"] for pin in pins}
    if not (set(source_ids) | set(target_ids)) <= pinned_ids:
        errors.append(f"{rid}: every endpoint Signal must have an explicit revision pin")

    for observation_id in row["supporting_observation_ids"]:
        if observation_id not in observation_by_id:
            errors.append(f"{rid}: unknown observation_id {observation_id}")
    for occurrence_id in row["contextual_canonical_occurrence_ids"]:
        if occurrence_id not in canonical_by_id:
            errors.append(f"{rid}: unknown contextual Canonical occurrence {occurrence_id}")
    all_evidence_refs = set(row["supporting_evidence_refs"]) | set(row["contradictory_evidence_refs"])
    if set(row["supporting_evidence_refs"]) & set(row["contradictory_evidence_refs"]):
        errors.append(f"{rid}: evidence cannot be both supporting and contradictory")
    for evidence_id in sorted(all_evidence_refs):
        if evidence_id not in evidence_by_id:
            errors.append(f"{rid}: unknown evidence reference {evidence_id}")
    linked_evidence = {
        evidence_id
        for observation_id in row["supporting_observation_ids"]
        if observation_id in observation_by_id
        for evidence_id in observation_by_id[observation_id].get("evidence_refs", [])
    }
    for pin in pins:
        signal = signal_by_revision.get(pin["revision_id"])
        if isinstance(signal, dict):
            linked_evidence.update(ref for ref in signal.get("evidence_refs", []) if isinstance(ref, str))
    if not all_evidence_refs <= linked_evidence:
        errors.append(f"{rid}: evidence must be traceable through supporting observations or Signals")

    scope = row["temporal_scope"]
    start = _parse_exact_utc(scope["start_at_utc"])
    end = _parse_exact_utc(scope["end_at_utc"]) if scope["end_at_utc"] is not None else None
    if start and end and end <= start:
        errors.append(f"{rid}: temporal scope must move forward")
    if scope["scope_type"] == "ONGOING_UNTIL_REVIEW" and end is not None:
        errors.append(f"{rid}: ongoing scope must not invent an end date")
    if row["directionality"] in {"DIRECTED", "RECIPROCAL"} and not _text(row["directionality_rationale"]):
        errors.append(f"{rid}: directional relationship requires directionality rationale")
    if row["relationship_class"] in {"DEPENDENCY", "HYPOTHESISED_TRANSMISSION"} and row["directionality"] != "DIRECTED":
        errors.append(f"{rid}: {row['relationship_class']} must be explicitly directed")
    if row["relationship_class"] == "CO_OCCURRENCE" and row["directionality"] != "UNDIRECTED":
        errors.append(f"{rid}: CO_OCCURRENCE must remain non-directional")
    if row["relationship_class"] == "FEEDBACK_LOOP" and row["directionality"] != "RECIPROCAL":
        errors.append(f"{rid}: FEEDBACK_LOOP must remain explicitly reciprocal")
    if row["relationship_class"] != "CO_OCCURRENCE" and not row["alternative_explanations"]:
        errors.append(f"{rid}: non-co-occurrence relationship requires alternative explanations")

    strong = row["relationship_class"] in {"MECHANISTICALLY_SUPPORTED", "CAUSAL_EVIDENCE"}
    review = row["review_provenance"]
    created = _parse_exact_utc(review["created_at_utc"])
    reviewed = _parse_exact_utc(review["reviewed_at_utc"]) if review["reviewed_at_utc"] is not None else None
    first_asserted = _parse_exact_utc(row["first_asserted_at_utc"])
    if first_asserted and created and first_asserted > created:
        errors.append(f"{rid}: first_asserted_at_utc cannot be after creation")
    if reviewed and created and reviewed < created:
        errors.append(f"{rid}: review decision cannot predate creation")
    if row["review_state"] in {"ACCEPTED", "REJECTED"}:
        if not _text(review["reviewed_by"]) or reviewed is None or not _text(review["decision_basis"]):
            errors.append(f"{rid}: accepted/rejected decision requires reviewer, timestamp and reason")
    elif any(review[key] is not None for key in ("reviewed_by", "reviewed_at_utc", "decision_basis")):
        errors.append(f"{rid}: unresolved review must not claim a completed decision")
    if row["review_state"] in {"CANDIDATE", "UNDER_REVIEW"} and row["lifecycle_state"] != "UNRESOLVED":
        errors.append(f"{rid}: unaccepted relationship must be UNRESOLVED")
    if row["review_state"] == "REJECTED" and row["lifecycle_state"] != "WITHDRAWN":
        errors.append(f"{rid}: rejected relationship must be WITHDRAWN")
    if row["review_state"] == "ACCEPTED" and row["lifecycle_state"] == "UNRESOLVED":
        errors.append(f"{rid}: accepted relationship requires a resolved lifecycle")
    if row["lifecycle_state"] in {"ACTIVE", "WEAKENING"} and row["review_state"] != "ACCEPTED":
        errors.append(f"{rid}: active relationship requires accepted review")
    if strong:
        if row["review_state"] != "ACCEPTED" or not _text(row["mechanism"]):
            errors.append(f"{rid}: strong relationship class requires accepted review and mechanism")
        if not row["supporting_evidence_refs"]:
            errors.append(f"{rid}: strong relationship class requires supporting evidence")
        if not row["causal_basis"]:
            errors.append(f"{rid}: strong relationship class requires explicit reviewed basis")
    if row["relationship_class"] == "CAUSAL_EVIDENCE" and not row["confounders"]:
        errors.append(f"{rid}: CAUSAL_EVIDENCE requires explicit confounders or a reviewed none-found statement")

    for signal_id, revision_id in pin_keys:
        signal = signal_by_revision.get(revision_id)
        if not isinstance(signal, dict):
            continue
        if created and _signal_created_at(signal) and _signal_created_at(signal) > created:
            errors.append(f"{rid}: later Signal revision cannot support an earlier Relationship assessment")
        if row["lifecycle_state"] in {"ACTIVE", "WEAKENING"}:
            if signal.get("review_state") != "ACCEPTED" or signal.get("lifecycle_state") not in {"ACTIVE", "WEAKENING"}:
                errors.append(f"{rid}: non-active Signal {signal_id} cannot masquerade as an active Relationship node")
            if signal_heads.get(signal_id, {}).get("revision_id") != revision_id:
                errors.append(f"{rid}: active Relationship must pin the current Signal revision")
    for observation_id in row["supporting_observation_ids"]:
        observation = observation_by_id.get(observation_id)
        observed = _parse_exact_utc(observation.get("observed_at_utc")) if observation else None
        if created and observed and observed > created:
            errors.append(f"{rid}: later observation cannot support an earlier Relationship assessment")
        if row["lifecycle_state"] in {"ACTIVE", "WEAKENING"} and observation and observation.get("verification_state") in {"CORRECTED", "RETRACTED"}:
            errors.append(f"{rid}: corrected/retracted observation requires a reviewed replacement before active use")
    for evidence_id in all_evidence_refs:
        published = _evidence_time(evidence_by_id.get(evidence_id, {}))
        if created and published and published > created:
            errors.append(f"{rid}: later evidence cannot support an earlier Relationship assessment")


def _validate_history(schema, rows, signals, observations, evidence, canonical, *, previous_revisions=None):
    errors: list[str] = []
    signal_by_revision, signal_heads, observation_by_id, evidence_by_id, canonical_by_id = _indexes(signals, observations, evidence, canonical)
    relationships_by_id: dict[str, list[dict[str, Any]]] = {}
    revision_ids: set[str] = set()
    for row in rows:
        if row["revision_id"] in revision_ids:
            errors.append(f"duplicate relationship revision_id {row['revision_id']}")
        revision_ids.add(row["revision_id"])
        relationships_by_id.setdefault(row["relationship_id"], []).append(row)
        _validate_row(row, schema, signal_by_revision, signal_heads, observation_by_id, evidence_by_id, canonical_by_id, errors)

    current_by_revision = {row["revision_id"]: row for row in rows}
    if previous_revisions is not None:
        if not isinstance(previous_revisions, list):
            errors.append("previous_revisions must be a retained snapshot list")
        else:
            for old in previous_revisions:
                if not isinstance(old, dict) or not _text(old.get("revision_id")) or current_by_revision.get(old["revision_id"]) != old:
                    errors.append("retained Relationship revision was removed or rewritten")

    transitions = {
        "CANDIDATE": {"CANDIDATE", "UNDER_REVIEW"},
        "UNDER_REVIEW": {"UNDER_REVIEW", "ACCEPTED", "REJECTED"},
        "ACCEPTED": {"ACCEPTED", "UNDER_REVIEW"},
        "REJECTED": {"UNDER_REVIEW"},
    }
    for relationship_id, revisions in relationships_by_id.items():
        ordered = sorted(revisions, key=lambda row: row["revision_number"])
        if [row["revision_number"] for row in ordered] != list(range(1, len(ordered) + 1)):
            errors.append(f"{relationship_id}: revision numbers must be contiguous from 1")
        for index, row in enumerate(ordered):
            previous = ordered[index - 1] if index else None
            if previous is None:
                if row["previous_revision_id"] is not None:
                    errors.append(f"{relationship_id}: first revision cannot have previous_revision_id")
            else:
                if row["previous_revision_id"] != previous["revision_id"]:
                    errors.append(f"{relationship_id}: revision history does not preserve its predecessor")
                if _effective_time(row) <= _effective_time(previous):
                    errors.append(f"{relationship_id}: revision time must strictly advance")
                if row["first_asserted_at_utc"] != previous["first_asserted_at_utc"]:
                    errors.append(f"{relationship_id}: first assertion time must remain stable")
                if row["review_state"] not in transitions[previous["review_state"]]:
                    errors.append(f"{relationship_id}: invalid review transition")
                if previous["lifecycle_state"] in {"EXPIRED", "WITHDRAWN", "SUPERSEDED"} and row["lifecycle_state"] == "ACTIVE":
                    errors.append(f"{relationship_id}: terminal relationship requires reopening review before reactivation")
                changed_path = (
                    row["source_nodes"] != previous["source_nodes"]
                    or row["target_nodes"] != previous["target_nodes"]
                    or row["directionality"] != previous["directionality"]
                )
                if changed_path and not _text(row["revision_reason"]):
                    errors.append(f"{relationship_id}: direction or endpoint change requires revision reason")
    return RelationshipValidationReport(tuple(errors))


def validate_relationship_history(
    schema: dict[str, Any],
    revisions: list[dict[str, Any]],
    signals_dataset: dict[str, Any],
    observations_dataset: dict[str, Any],
    evidence_registry: dict[str, Any],
    canonical_registry: dict[str, Any],
    *,
    previous_revisions: list[dict[str, Any]] | None = None,
) -> RelationshipValidationReport:
    """Validate synthetic/proposed history without production storage authority."""
    dataset = {
        "version": schema.get("version"),
        "population_state": "CLOSED_NO_PRODUCTION_RELATIONSHIPS",
        "relationships": revisions,
    }
    errors = _preflight(schema, dataset, signals_dataset, observations_dataset, evidence_registry, canonical_registry)
    if errors:
        return RelationshipValidationReport(tuple(errors))
    return _validate_history(
        schema, revisions, signals_dataset, observations_dataset, evidence_registry,
        canonical_registry, previous_revisions=previous_revisions,
    )


def validate_relationships(
    schema: dict[str, Any],
    relationships_dataset: dict[str, Any],
    signals_dataset: dict[str, Any],
    observations_dataset: dict[str, Any],
    evidence_registry: dict[str, Any],
    canonical_registry: dict[str, Any],
) -> RelationshipValidationReport:
    """Production admission: the Relationship population gate is closed."""
    errors = _preflight(schema, relationships_dataset, signals_dataset, observations_dataset, evidence_registry, canonical_registry)
    if errors:
        return RelationshipValidationReport(tuple(errors))
    if relationships_dataset.get("version") != schema.get("version"):
        errors.append("Relationship dataset version must match schema version")
    if relationships_dataset.get("population_state") != "CLOSED_NO_PRODUCTION_RELATIONSHIPS":
        errors.append("Relationship dataset must remain in the closed population state")
    policy = schema.get("population_policy") or {}
    for key in (
        "production_population_allowed", "automatic_ingestion_allowed", "candidate_relationship_storage_allowed",
        "synthetic_production_population_allowed", "public_relationship_projection_allowed",
    ):
        if policy.get(key) is not False:
            errors.append(f"Relationship population policy must keep {key}=false")
    boundary = schema.get("layer_boundary") or {}
    for key in (
        "canonical_mutation_allowed", "observation_mutation_allowed", "signal_mutation_allowed",
        "risk_overlay_mutation_allowed", "automatic_relationship_promotion_allowed",
        "transitive_relationship_creation_allowed", "forecast_fields_allowed", "scenario_fields_allowed",
        "public_relationship_projection_allowed",
    ):
        if boundary.get(key) is not False:
            errors.append(f"Relationship boundary must keep {key}=false")
    if relationships_dataset["relationships"]:
        errors.append("closed production population gate prohibits every Relationship revision")
    errors.extend(_validate_history(
        schema, relationships_dataset["relationships"], signals_dataset, observations_dataset,
        evidence_registry, canonical_registry,
    ).errors)
    return RelationshipValidationReport(tuple(errors))


def relationship_state_as_of(
    schema: dict[str, Any],
    revisions: list[dict[str, Any]],
    signals_dataset: dict[str, Any],
    observations_dataset: dict[str, Any],
    evidence_registry: dict[str, Any],
    canonical_registry: dict[str, Any],
    at_utc: str,
) -> dict[str, dict[str, Any]]:
    """Return the reviewed head effective at an explicit time without mutation."""
    report = validate_relationship_history(
        schema, revisions, signals_dataset, observations_dataset, evidence_registry, canonical_registry,
    )
    at = _parse_exact_utc(at_utc)
    if not report.ok or at is None:
        raise ValueError("invalid Relationship history/as-of timestamp: " + "; ".join(report.errors))
    result: dict[str, dict[str, Any]] = {}
    for row in sorted(revisions, key=lambda item: (item["relationship_id"], item["revision_number"])):
        if _effective_time(row) <= at:
            result[row["relationship_id"]] = {
                "revision_id": row["revision_id"],
                "relationship_class": row["relationship_class"],
                "directionality": row["directionality"],
                "lifecycle_state": row["lifecycle_state"],
                "review_state": row["review_state"],
            }
    return result


def relationship_graph_edges_as_of(
    schema: dict[str, Any],
    revisions: list[dict[str, Any]],
    signals_dataset: dict[str, Any],
    observations_dataset: dict[str, Any],
    evidence_registry: dict[str, Any],
    canonical_registry: dict[str, Any],
    at_utc: str,
) -> list[dict[str, Any]]:
    """Expose exact reviewed edges only; never performs transitive closure."""
    validate_relationship_history(schema, revisions, signals_dataset, observations_dataset, evidence_registry, canonical_registry)
    states = relationship_state_as_of(schema, revisions, signals_dataset, observations_dataset, evidence_registry, canonical_registry, at_utc)
    by_revision = {row["revision_id"]: row for row in revisions}
    edges = []
    for state in states.values():
        if state["review_state"] == "ACCEPTED" and state["lifecycle_state"] in {"ACTIVE", "WEAKENING"}:
            row = by_revision[state["revision_id"]]
            edges.append({
                "relationship_id": row["relationship_id"],
                "revision_id": row["revision_id"],
                "source_nodes": row["source_nodes"],
                "target_nodes": row["target_nodes"],
                "directionality": row["directionality"],
                "relationship_class": row["relationship_class"],
            })
    return sorted(edges, key=lambda edge: edge["relationship_id"])


def public_relationship_projection(
    schema: dict[str, Any],
    relationships_dataset: dict[str, Any],
    signals_dataset: dict[str, Any],
    observations_dataset: dict[str, Any],
    evidence_registry: dict[str, Any],
    canonical_registry: dict[str, Any],
) -> dict[str, Any]:
    report = validate_relationships(schema, relationships_dataset, signals_dataset, observations_dataset, evidence_registry, canonical_registry)
    if not report.ok:
        raise ValueError("invalid Relationship state: " + "; ".join(report.errors))
    return {
        "metadata": {
            "projection_type": "RELATIONSHIP_CONTRACT_CLOSED_PROJECTION",
            "schema_version": schema.get("version"),
            "population_state": relationships_dataset.get("population_state"),
            "internal_relationship_count": 0,
            "public_relationship_count": 0,
            "automatic_relationship_promotion": False,
            "public_relationship_projection_allowed": False,
        },
        "relationships": [],
    }
