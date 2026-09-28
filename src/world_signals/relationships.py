"""Closed, reviewed Relationship contract over Signals and World State.

Relationships describe reviewed analytical connections. They do not mutate
Signals, create transitive graph edges, score risk or forecast outcomes. The
hash-pinned v0.1 production checkpoint remains empty; schema 0.2 also supports
one separately validated, human-admitted historical specimen. Schema 0.2 pins
immutable endpoint revisions and keeps temporal dependency cycles separate from
ordinary reviewed graph feedback semantics.
"""

from __future__ import annotations

from copy import deepcopy
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
    world_state_components: Any | None = None,
    world_state_admissions: Any | None = None,
) -> list[str]:
    errors: list[str] = []
    values = (schema, dataset, signals, observations, evidence, canonical)
    if not all(isinstance(value, dict) for value in values):
        return ["schema and relationship inputs must be objects"]
    try:
        json.dumps(values, allow_nan=False)
    except (TypeError, ValueError):
        return ["relationship inputs must contain finite JSON values"]

    if schema.get("version") not in {"0.1", "0.2"}:
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
                node_type = node.get("node_type") if isinstance(node, dict) else None
                expected = {"node_id", "node_type"} if node_type == "SIGNAL" else {
                    "node_id", "node_type", "revision_id", "object_sha256", "component_type",
                    "dimension", "admitted_at_utc", "admission_transaction_id",
                }
                if not isinstance(node, dict) or set(node) != expected:
                    errors.append(f"{key} contains an invalid typed node identity")
                    continue
                if not _text(node.get("node_id")) or node_type not in vocab["node_type"]:
                    errors.append(f"{key} contains an invalid Relationship node")
                if node_type == "WORLD_STATE_COMPONENT":
                    for field in ("revision_id", "object_sha256", "component_type", "dimension", "admission_transaction_id"):
                        if not _text(node.get(field)):
                            errors.append(f"{key} World State node requires {field}")
                    if _parse_exact_utc(node.get("admitted_at_utc")) is None:
                        errors.append(f"{key} World State node requires exact admitted_at_utc")
        node_types = {
            node.get("node_type")
            for key in ("source_nodes", "target_nodes")
            for node in row.get(key, [])
            if isinstance(node, dict)
        }
        if len(node_types) > 1:
            errors.append("mixed node-type Relationships are prohibited in schema 0.2")
        pins = row.get("supporting_node_revisions")
        if not isinstance(pins, list) or not pins:
            errors.append("supporting_node_revisions must be a non-empty list")
        else:
            for pin in pins:
                if not isinstance(pin, dict) or set(pin) != {"node_type", "node_id", "revision_id", "object_sha256"}:
                    errors.append("supporting_node_revisions entries must contain typed exact revision pins")
                    continue
                if any(not _text(pin.get(field)) for field in ("node_type", "node_id", "revision_id", "object_sha256")):
                    errors.append("supporting_node_revisions pin fields must be non-empty text")
                if pin.get("node_type") not in vocab["node_type"]:
                    errors.append("supporting_node_revisions contains an unsupported node type")
        for key, id_key in (("supporting_analysis_refs", "analysis_id"), ("supporting_evidence_pins", "evidence_id")):
            refs = row.get(key)
            if not isinstance(refs, list):
                errors.append(f"{key} must be a list")
                continue
            for ref in refs:
                if not isinstance(ref, dict) or set(ref) != {id_key, "object_sha256"}:
                    errors.append(f"{key} entries must contain {id_key} and object_sha256")
                elif not _text(ref.get(id_key)) or not _text(ref.get("object_sha256")):
                    errors.append(f"{key} pin fields must be non-empty text")
        scope = row.get("temporal_scope")
        scope_fields = {"scope_type", "precision", "anchor_at_utc", "start_at_utc", "end_at_utc", "start_date", "end_date", "notes"}
        if not isinstance(scope, dict) or set(scope) != scope_fields:
            errors.append("temporal_scope has an invalid field set")
        else:
            if scope.get("scope_type") not in vocab["temporal_scope_type"]:
                errors.append("invalid temporal scope type")
            if scope.get("precision") not in vocab["temporal_precision"]:
                errors.append("invalid temporal precision")
            for field in ("anchor_at_utc", "start_at_utc", "end_at_utc"):
                if scope.get(field) is not None and _parse_exact_utc(scope.get(field)) is None:
                    errors.append(f"temporal_scope.{field} must be exact UTC or null")
            for field in ("start_date", "end_date"):
                if scope.get(field) is not None and (not _text(scope.get(field)) or len(scope[field]) != 10):
                    errors.append(f"temporal_scope.{field} must be an ISO civil date or null")
            if scope.get("precision") == "UTC_INSTANT" and _parse_exact_utc(scope.get("start_at_utc")) is None:
                errors.append("UTC_INSTANT temporal scope requires exact start_at_utc")
            if scope.get("precision") == "UTC_RANGE" and (
                _parse_exact_utc(scope.get("start_at_utc")) is None or _parse_exact_utc(scope.get("end_at_utc")) is None
            ):
                errors.append("UTC_RANGE temporal scope requires exact start and end UTC")
            if scope.get("precision") == "CIVIL_DATE" and not _text(scope.get("start_date")):
                errors.append("CIVIL_DATE temporal scope requires start_date")
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


def _indexes(
    signals: dict[str, Any],
    observations: dict[str, Any],
    evidence: dict[str, Any],
    canonical: dict[str, Any],
    world_state_components: dict[str, Any] | None = None,
    world_state_admissions: dict[str, Any] | None = None,
):
    signal_by_revision = {}
    signal_revisions_by_id = {}
    observation_by_id = {}
    evidence_by_id = {}
    canonical_by_id = {}
    world_state_by_revision = {}
    admissions_by_id = {}
    for row in signals["signals"]:
        signal_by_revision[row["revision_id"]] = row
        signal_revisions_by_id.setdefault(row["signal_id"], []).append(row)
    for row in observations["observations"]:
        observation_by_id[row["observation_id"]] = row
    for row in evidence["evidence"]:
        evidence_by_id[row["evidence_id"]] = row
    for row in canonical["records"]:
        canonical_by_id[row["occurrence_id"]] = row
    for row in (world_state_components or {}).get("components", []):
        world_state_by_revision[(row.get("component_id"), row.get("revision_id"))] = row
    for row in (world_state_admissions or {}).get("transactions", []):
        admissions_by_id[row.get("transaction_id")] = row
    signal_heads = {
        signal_id: max(rows, key=lambda row: row["revision_number"])
        for signal_id, rows in signal_revisions_by_id.items()
    }
    return signal_by_revision, signal_heads, observation_by_id, evidence_by_id, canonical_by_id, world_state_by_revision, admissions_by_id


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


def _object_fingerprint(value: Any) -> str:
    import hashlib
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def _validate_row(
    row,
    schema,
    signal_by_revision,
    signal_heads,
    observation_by_id,
    evidence_by_id,
    canonical_by_id,
    world_state_by_revision,
    admissions_by_id,
    errors,
):
    rid = row["relationship_id"]
    source_ids = [node["node_id"] for node in row["source_nodes"]]
    target_ids = [node["node_id"] for node in row["target_nodes"]]
    if len(source_ids) != len(set(source_ids)) or len(target_ids) != len(set(target_ids)):
        errors.append(f"{rid}: duplicate endpoint references")
    if set(source_ids) & set(target_ids):
        errors.append(f"{rid}: endpoint cannot be both source and target")
    endpoint_nodes = row["source_nodes"] + row["target_nodes"]
    endpoint_types = {node["node_type"] for node in endpoint_nodes}
    if len(endpoint_types) > 1:
        errors.append(f"{rid}: mixed node-type Relationships are prohibited in schema 0.2")
    pins = row["supporting_node_revisions"]
    pin_keys = [(pin["node_type"], pin["node_id"], pin["revision_id"]) for pin in pins]
    if len(pin_keys) != len(set(pin_keys)):
        errors.append(f"{rid}: duplicate typed revision pins cannot increase support")
    endpoint_keys = {(node["node_type"], node["node_id"]) for node in endpoint_nodes}
    pinned_keys = {(pin["node_type"], pin["node_id"]) for pin in pins}
    if not endpoint_keys <= pinned_keys:
        errors.append(f"{rid}: every endpoint requires an explicit typed revision pin")
    for pin in pins:
        if pin["node_type"] == "SIGNAL":
            signal = signal_by_revision.get(pin["revision_id"])
            if signal is None or signal.get("signal_id") != pin["node_id"]:
                errors.append(f"{rid}: unknown or mismatched Signal revision {pin['node_id']}/{pin['revision_id']}")
            elif _object_fingerprint(signal) != pin["object_sha256"]:
                errors.append(f"{rid}: Signal revision hash mismatch {pin['node_id']}/{pin['revision_id']}")
        elif pin["node_type"] == "WORLD_STATE_COMPONENT":
            component = world_state_by_revision.get((pin["node_id"], pin["revision_id"]))
            if component is None:
                errors.append(f"{rid}: unknown World State component revision {pin['node_id']}/{pin['revision_id']}")
            elif component.get("object_sha256") != pin["object_sha256"]:
                errors.append(f"{rid}: World State component hash mismatch {pin['node_id']}/{pin['revision_id']}")
    for node in endpoint_nodes:
        if node["node_type"] == "SIGNAL":
            if node["node_id"] not in signal_heads:
                errors.append(f"{rid}: unknown Signal reference {node['node_id']}")
        elif node["node_type"] == "WORLD_STATE_COMPONENT":
            component = world_state_by_revision.get((node["node_id"], node["revision_id"]))
            if component is None:
                errors.append(f"{rid}: endpoint World State component revision is unavailable")
                continue
            for field in ("component_type", "dimension", "admitted_at_utc", "admission_transaction_id"):
                if node.get(field) != component.get(field):
                    errors.append(f"{rid}: endpoint metadata mismatch for World State field {field}")
            if component.get("review_state") != "ACCEPTED" or not component.get("admitted_at_utc"):
                errors.append(f"{rid}: World State endpoint must be an admitted accepted revision")
            if node["admission_transaction_id"] not in admissions_by_id:
                errors.append(f"{rid}: endpoint admission transaction is unavailable")
            created = _parse_exact_utc(row["review_provenance"].get("created_at_utc"))
            admitted = _parse_exact_utc(component.get("admitted_at_utc"))
            if created and admitted and admitted > created:
                errors.append(f"{rid}: World State endpoint was not admitted before Relationship review")
    referenced_signal_ids = {node["node_id"] for node in endpoint_nodes if node["node_type"] == "SIGNAL"}
    referenced_signal_ids |= set(row["common_driver_signal_ids"])

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
    evidence_pins = {pin["evidence_id"]: pin["object_sha256"] for pin in row["supporting_evidence_pins"]}
    if set(evidence_pins) != set(row["supporting_evidence_refs"]):
        errors.append(f"{rid}: supporting evidence references and exact pins must match")
    for evidence_id, object_sha256 in evidence_pins.items():
        if evidence_id in evidence_by_id and _object_fingerprint(evidence_by_id[evidence_id]) != object_sha256:
            errors.append(f"{rid}: supporting evidence hash mismatch for {evidence_id}")
    linked_evidence = {
        evidence_id
        for observation_id in row["supporting_observation_ids"]
        if observation_id in observation_by_id
        for evidence_id in observation_by_id[observation_id].get("evidence_refs", [])
    }
    for pin in pins:
        if pin["node_type"] != "SIGNAL":
            continue
        signal = signal_by_revision.get(pin["revision_id"])
        if isinstance(signal, dict):
            linked_evidence.update(ref for ref in signal.get("evidence_refs", []) if isinstance(ref, str))
    explicitly_pinned_evidence = set(evidence_pins)
    if not all_evidence_refs <= linked_evidence | explicitly_pinned_evidence:
        errors.append(f"{rid}: evidence must be traceable through supporting observations, Signals or exact evidence pins")

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

    for node_type, signal_id, revision_id in pin_keys:
        if node_type != "SIGNAL":
            continue
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


def _validate_history(
    schema,
    rows,
    signals,
    observations,
    evidence,
    canonical,
    *,
    previous_revisions=None,
    world_state_components=None,
    world_state_admissions=None,
):
    errors: list[str] = []
    (
        signal_by_revision,
        signal_heads,
        observation_by_id,
        evidence_by_id,
        canonical_by_id,
        world_state_by_revision,
        admissions_by_id,
    ) = _indexes(signals, observations, evidence, canonical, world_state_components, world_state_admissions)
    relationships_by_id: dict[str, list[dict[str, Any]]] = {}
    revision_ids: set[str] = set()
    for row in rows:
        if row["revision_id"] in revision_ids:
            errors.append(f"duplicate relationship revision_id {row['revision_id']}")
        revision_ids.add(row["revision_id"])
        relationships_by_id.setdefault(row["relationship_id"], []).append(row)
        _validate_row(
            row,
            schema,
            signal_by_revision,
            signal_heads,
            observation_by_id,
            evidence_by_id,
            canonical_by_id,
            world_state_by_revision,
            admissions_by_id,
            errors,
        )

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
    world_state_components: dict[str, Any] | None = None,
    world_state_admissions: dict[str, Any] | None = None,
) -> RelationshipValidationReport:
    """Validate synthetic/proposed history without production storage authority."""
    dataset = {
        "version": schema.get("version"),
        "population_state": "CLOSED_NO_PRODUCTION_RELATIONSHIPS",
        "relationships": revisions,
    }
    errors = _preflight(
        schema, dataset, signals_dataset, observations_dataset, evidence_registry, canonical_registry,
        world_state_components, world_state_admissions,
    )
    if errors:
        return RelationshipValidationReport(tuple(errors))
    return _validate_history(
        schema, revisions, signals_dataset, observations_dataset, evidence_registry,
        canonical_registry,
        previous_revisions=previous_revisions,
        world_state_components=world_state_components,
        world_state_admissions=world_state_admissions,
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


def validate_relationship_production(
    schema: dict[str, Any],
    relationships_dataset: dict[str, Any],
    signals_dataset: dict[str, Any],
    observations_dataset: dict[str, Any],
    evidence_registry: dict[str, Any],
    canonical_registry: dict[str, Any],
    *,
    world_state_components: dict[str, Any] | None = None,
    world_state_admissions: dict[str, Any] | None = None,
) -> RelationshipValidationReport:
    """Validate the narrowly controlled v0.2 production Relationship store.

    The legacy v0.1 checkpoint remains validated by ``validate_relationships``.
    This path is deliberately separate so opening one human-admitted specimen
    cannot silently reopen the general Relationship population.
    """
    errors = _preflight(
        schema, relationships_dataset, signals_dataset, observations_dataset,
        evidence_registry, canonical_registry, world_state_components,
        world_state_admissions,
    )
    if errors:
        return RelationshipValidationReport(tuple(errors))
    if schema.get("version") != "0.2":
        errors.append("controlled production Relationship store requires schema 0.2")
    policy = schema.get("population_policy") or {}
    if policy.get("manual_reviewed_admission_allowed") is not True:
        errors.append("manual_reviewed_admission_allowed must be true")
    if policy.get("automatic_ingestion_allowed") is not False:
        errors.append("automatic_ingestion_allowed must remain false")
    if policy.get("general_population_open") is not False:
        errors.append("general_population_open must remain false")
    if policy.get("maximum_controlled_relationships") != 1:
        errors.append("maximum_controlled_relationships must remain 1")
    if policy.get("public_relationship_projection_allowed") is not False:
        errors.append("public Relationship projection must remain false")
    if relationships_dataset.get("version") != "0.2":
        errors.append("controlled production dataset must be version 0.2")
    if relationships_dataset.get("population_state") != "CONTROLLED_SINGLE_RELATIONSHIP_SPECIMEN":
        errors.append("production population state is not the controlled single specimen")
    if relationships_dataset.get("public_projection_permitted") is not False:
        errors.append("production Relationship public projection must remain false")
    rows = relationships_dataset.get("relationships")
    if not isinstance(rows, list) or len(rows) != 1:
        errors.append("controlled production store must contain exactly one Relationship revision")
    else:
        row = rows[0]
        if row.get("review_state") != "ACCEPTED":
            errors.append("production Relationship must be accepted")
        if row.get("lifecycle_state") != "EXPIRED":
            errors.append("historical production Relationship must be EXPIRED")
        if row.get("relationship_class") != "ASSOCIATION":
            errors.append("first production Relationship must remain ASSOCIATION")
        if row.get("causal_basis") != []:
            errors.append("first production Relationship must have empty causal_basis")
    errors.extend(validate_relationship_history(
        schema,
        rows if isinstance(rows, list) else [],
        signals_dataset,
        observations_dataset,
        evidence_registry,
        canonical_registry,
        world_state_components=world_state_components,
        world_state_admissions=world_state_admissions,
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
    *,
    world_state_components: dict[str, Any] | None = None,
    world_state_admissions: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Return the reviewed head effective at an explicit time without mutation."""
    report = validate_relationship_history(
        schema, revisions, signals_dataset, observations_dataset, evidence_registry, canonical_registry,
        world_state_components=world_state_components,
        world_state_admissions=world_state_admissions,
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
    *,
    world_state_components: dict[str, Any] | None = None,
    world_state_admissions: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Expose exact reviewed edges only; never performs transitive closure."""
    report = validate_relationship_history(
        schema, revisions, signals_dataset, observations_dataset, evidence_registry, canonical_registry,
        world_state_components=world_state_components,
        world_state_admissions=world_state_admissions,
    )
    if not report.ok:
        raise ValueError("invalid Relationship history: " + "; ".join(report.errors))
    states = relationship_state_as_of(
        schema, revisions, signals_dataset, observations_dataset, evidence_registry, canonical_registry, at_utc,
        world_state_components=world_state_components,
        world_state_admissions=world_state_admissions,
    )
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


def relationship_history_as_of(
    schema: dict[str, Any],
    revisions: list[dict[str, Any]],
    signals_dataset: dict[str, Any],
    observations_dataset: dict[str, Any],
    evidence_registry: dict[str, Any],
    canonical_registry: dict[str, Any],
    at_utc: str,
    *,
    world_state_components: dict[str, Any] | None = None,
    world_state_admissions: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return accepted historical revisions available at an explicit UTC time."""
    states = relationship_state_as_of(
        schema, revisions, signals_dataset, observations_dataset, evidence_registry,
        canonical_registry, at_utc, world_state_components=world_state_components,
        world_state_admissions=world_state_admissions,
    )
    by_revision = {row["revision_id"]: row for row in revisions}
    return [
        deepcopy(by_revision[state["revision_id"]])
        for state in sorted(states.values(), key=lambda item: item["revision_id"])
        if state["review_state"] == "ACCEPTED"
    ]


def _transaction_fingerprint(transaction: dict[str, Any]) -> str:
    """Match the guarded v0.2 admission transaction fingerprint rule."""
    core = {
        key: value
        for key, value in transaction.items()
        if key != "transaction_fingerprint"
    }
    return _object_fingerprint(core)


def relationship_production_history_as_of(
    schema: dict[str, Any],
    production_dataset: dict[str, Any],
    admission_dataset: dict[str, Any],
    signals_dataset: dict[str, Any],
    observations_dataset: dict[str, Any],
    evidence_registry: dict[str, Any],
    canonical_registry: dict[str, Any],
    at_utc: str,
    *,
    world_state_components: dict[str, Any] | None = None,
    world_state_admissions: dict[str, Any] | None = None,
    scope: dict[str, list[str]] | None = None,
) -> list[dict[str, Any]]:
    """Return only v0.2 Relationships admitted by an explicit knowledge time.

    ``relationship_history_as_of`` is intentionally an effective/review-time
    helper for the Relationship contract.  World State production reads need a
    stricter boundary: an accepted row is invisible until its separate
    Relationship production admission transaction is itself accepted and
    admitted.  This selector also applies the World State jurisdiction/domain
    scope without inventing graph edges.
    """
    report = validate_relationship_production(
        schema,
        production_dataset,
        signals_dataset,
        observations_dataset,
        evidence_registry,
        canonical_registry,
        world_state_components=world_state_components,
        world_state_admissions=world_state_admissions,
    )
    if not report.ok:
        raise ValueError("invalid production Relationship history: " + "; ".join(report.errors))
    at = _parse_exact_utc(at_utc)
    if at is None:
        raise ValueError("invalid production Relationship knowledge cutoff")
    transactions = admission_dataset.get("transactions")
    if not isinstance(transactions, list):
        raise ValueError("Relationship admission dataset must contain transactions")
    by_revision = {
        (row.get("relationship_id"), row.get("revision_id")): row
        for row in production_dataset.get("relationships", [])
    }
    selected: list[dict[str, Any]] = []
    jurisdictions = set((scope or {}).get("jurisdictions", []))
    dimensions = set((scope or {}).get("dimensions", []))
    for row in production_dataset.get("relationships", []):
        if row.get("review_state") != "ACCEPTED":
            continue
        transaction = next(
            (
                item for item in transactions
                if item.get("relationship_id") == row.get("relationship_id")
                and item.get("revision_id") == row.get("revision_id")
            ),
            None,
        )
        if transaction is None:
            raise ValueError(f"missing Relationship admission for {row.get('revision_id')}")
        if transaction.get("transaction_type") != "RELATIONSHIP_PRODUCTION_ADMISSION":
            raise ValueError(f"invalid Relationship admission type for {row.get('revision_id')}")
        if transaction.get("decision") != "ACCEPTED":
            raise ValueError(f"Relationship admission is not accepted for {row.get('revision_id')}")
        if transaction.get("production_relationship_fingerprint") != _object_fingerprint(row):
            raise ValueError(f"Relationship admission fingerprint mismatch for {row.get('revision_id')}")
        if transaction.get("transaction_fingerprint") != _transaction_fingerprint(transaction):
            raise ValueError(f"Relationship admission transaction fingerprint mismatch for {row.get('revision_id')}")
        admitted = _parse_exact_utc(transaction.get("admitted_at_utc"))
        if admitted is None:
            raise ValueError(f"Relationship admission has invalid admitted_at_utc for {row.get('revision_id')}")
        if admitted > at:
            continue
        if jurisdictions and "*" not in jurisdictions and not (set(row.get("jurisdictions", [])) & jurisdictions):
            continue
        if dimensions and "*" not in dimensions and not (set(row.get("domains", [])) & dimensions):
            continue
        if by_revision.get((row.get("relationship_id"), row.get("revision_id"))) is not row:
            raise ValueError("conflicting production Relationship identity")
        selected.append({
            "relationship": deepcopy(row),
            "admission": deepcopy(transaction),
        })
    return sorted(selected, key=lambda item: (item["relationship"]["relationship_id"], item["relationship"]["revision_id"]))


def active_relationship_graph_edges_as_of(
    schema: dict[str, Any],
    revisions: list[dict[str, Any]],
    signals_dataset: dict[str, Any],
    observations_dataset: dict[str, Any],
    evidence_registry: dict[str, Any],
    canonical_registry: dict[str, Any],
    at_utc: str,
    *,
    world_state_components: dict[str, Any] | None = None,
    world_state_admissions: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return only accepted ACTIVE/WEAKENING edges, never historical EXPIRED ones."""
    return relationship_graph_edges_as_of(
        schema, revisions, signals_dataset, observations_dataset, evidence_registry,
        canonical_registry, at_utc, world_state_components=world_state_components,
        world_state_admissions=world_state_admissions,
    )


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


def validate_temporal_dependency_dag(edges: list[dict[str, Any]]) -> RelationshipValidationReport:
    """Reject explicit revision-dependency cycles without inferring graph edges."""
    errors: list[str] = []
    adjacency: dict[tuple[str, str, str], set[tuple[str, str, str]]] = {}
    for edge in edges:
        if not isinstance(edge, dict) or set(edge) != {"source", "target"}:
            errors.append("dependency edges require source and target typed revision identities")
            continue
        keys = []
        for side in ("source", "target"):
            node = edge[side]
            if not isinstance(node, dict) or set(node) != {"node_type", "node_id", "revision_id"}:
                errors.append("dependency edge identities must contain node_type, node_id and revision_id")
                continue
            if not all(_text(node.get(field)) for field in ("node_type", "node_id", "revision_id")):
                errors.append("dependency edge identity fields must be non-empty")
            keys.append((node["node_type"], node["node_id"], node["revision_id"]))
        if len(keys) == 2:
            adjacency.setdefault(keys[0], set()).add(keys[1])
    visiting: set[tuple[str, str, str]] = set()
    visited: set[tuple[str, str, str]] = set()

    def visit(node: tuple[str, str, str]) -> None:
        if node in visiting:
            errors.append("temporal dependency cycle detected")
            return
        if node in visited:
            return
        visiting.add(node)
        for child in sorted(adjacency.get(node, set())):
            visit(child)
        visiting.remove(node)
        visited.add(node)

    for node in sorted(adjacency):
        visit(node)
    return RelationshipValidationReport(tuple(dict.fromkeys(errors)))
