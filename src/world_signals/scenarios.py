"""Validation and closed projection for the reviewed Scenario contract.

A Scenario is a reviewed, conditional possible pathway.  It is deliberately
separate from facts, current Risk/Regime state and later probabilistic
Forecasts.  The production population remains closed while this module
provides deterministic history and as-of validation for synthetic fixtures.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any


UTC = timezone.utc


@dataclass(frozen=True)
class ScenarioValidationReport:
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _strings(value: Any) -> bool:
    return isinstance(value, list) and all(_text(item) for item in value)


def _utc(value: Any) -> datetime | None:
    if not _text(value):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        return None
    return parsed.astimezone(UTC)


def _all_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return {str(key) for key in value} | {
            child for item in value.values() for child in _all_keys(item)
        }
    if isinstance(value, list):
        return {child for item in value for child in _all_keys(item)}
    return set()


def _has_prohibited_key(value: Any, prohibited: set[str]) -> str | None:
    keys = {key.casefold() for key in _all_keys(value)}
    for key in sorted(keys):
        if key in prohibited:
            return key
    return None


def _index_rows(data: Any, key: str, id_key: str, errors: list[str], label: str) -> dict[str, dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get(key), list):
        errors.append(f"{label} must contain a list named {key}")
        return {}
    result: dict[str, dict[str, Any]] = {}
    for row in data[key]:
        if not isinstance(row, dict) or not _text(row.get(id_key)):
            errors.append(f"{label} rows must have a non-empty {id_key}")
            continue
        identifier = row[id_key]
        revision_id = row.get("revision_id")
        if not _text(revision_id):
            errors.append(f"{label} {identifier} must have a revision_id")
            continue
        if revision_id in result:
            errors.append(f"duplicate upstream revision_id {revision_id}")
        else:
            result[revision_id] = row
    return result


def _index_observations(data: Any, errors: list[str]) -> dict[str, dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("observations"), list):
        errors.append("observations must contain a list")
        return {}
    result: dict[str, dict[str, Any]] = {}
    for row in data["observations"]:
        if not isinstance(row, dict) or not _text(row.get("observation_id")):
            errors.append("observation rows must have a non-empty observation_id")
            continue
        if row["observation_id"] in result:
            errors.append(f"duplicate observation_id {row['observation_id']}")
        else:
            result[row["observation_id"]] = row
    return result


def _index_evidence(data: Any, errors: list[str]) -> dict[str, dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("evidence"), list):
        errors.append("evidence must contain a list")
        return {}
    result: dict[str, dict[str, Any]] = {}
    for row in data["evidence"]:
        if not isinstance(row, dict) or not _text(row.get("evidence_id")):
            errors.append("evidence rows must have a non-empty evidence_id")
            continue
        if row["evidence_id"] in result:
            errors.append(f"duplicate evidence_id {row['evidence_id']}")
        else:
            result[row["evidence_id"]] = row
    return result


def _revision_time(row: dict[str, Any]) -> datetime | None:
    return _utc(row.get("effective_at_utc")) or _utc(row.get("latest_reviewed_at_utc"))


def _created_time(row: dict[str, Any]) -> datetime | None:
    return _utc(row.get("first_created_at_utc")) or _utc(row.get("effective_at_utc"))


def _upstream_created(row: dict[str, Any]) -> datetime | None:
    provenance = row.get("review_provenance")
    if isinstance(provenance, dict):
        return _utc(provenance.get("created_at_utc"))
    return _utc(row.get("created_at_utc"))


def _preflight(
    schema: Any,
    dataset: Any,
    risks: Any,
    signals: Any,
    relationships: Any,
    observations: Any,
    evidence: Any,
    canonical: Any,
) -> tuple[list[str], dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    errors: list[str] = []
    inputs = (schema, dataset, risks, signals, relationships, observations, evidence, canonical)
    if not all(isinstance(value, dict) for value in inputs):
        return ["Scenario inputs must be objects"], {}, {}, {}, {}, {}, {}
    try:
        json.dumps(inputs, allow_nan=False)
    except (TypeError, ValueError):
        return ["Scenario inputs must contain finite JSON values"], {}, {}, {}, {}, {}, {}

    if schema.get("version") != "0.1":
        errors.append("unsupported Scenario schema version")
    if schema.get("architecture_position") != "SCENARIOS":
        errors.append("Scenario schema architecture_position must be SCENARIOS")
    if dataset.get("version") != schema.get("version"):
        errors.append("Scenario dataset version must match schema version")
    for key in ("scenario_sets", "scenarios"):
        if not isinstance(dataset.get(key), list):
            errors.append(f"{key} must be a list")
    for key in ("required_scenario_set_fields", "required_scenario_fields"):
        if not _strings(schema.get(key)) or not schema[key]:
            errors.append(f"{key} must be a non-empty string list")
    for key in ("layer_boundary", "population_policy", "public_projection_policy", "controlled_vocabularies"):
        if not isinstance(schema.get(key), dict):
            errors.append(f"{key} must be an object")

    risk_revisions = _index_rows(risks, "states", "state_id", errors, "Risk/Regime")
    signal_revisions = _index_rows(signals, "signals", "signal_id", errors, "Signal")
    relationship_revisions = _index_rows(relationships, "relationships", "relationship_id", errors, "Relationship")
    observation_by_id = _index_observations(observations, errors)
    evidence_by_id = _index_evidence(evidence, errors)
    if not isinstance(canonical.get("records"), list):
        errors.append("Canonical must contain a records list")
    canonical_by_id: dict[str, dict[str, Any]] = {}
    return errors, risk_revisions, signal_revisions, relationship_revisions, observation_by_id, evidence_by_id, canonical_by_id


def _validate_pin_list(
    row_id: str,
    field: str,
    value: Any,
    object_id_key: str,
    index: dict[str, dict[str, Any]],
    errors: list[str],
) -> list[dict[str, str]]:
    if not isinstance(value, list):
        errors.append(f"{row_id}: {field} must be a list")
        return []
    pins: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for pin in value:
        if not isinstance(pin, dict) or set(pin) != {object_id_key, "revision_id"} or not _text(pin.get(object_id_key)) or not _text(pin.get("revision_id")):
            errors.append(f"{row_id}: invalid {field} revision pin")
            continue
        pair = (pin[object_id_key], pin["revision_id"])
        if pair in seen:
            errors.append(f"{row_id}: duplicate {field} revision pin")
        seen.add(pair)
        upstream = index.get(pin["revision_id"])
        if upstream is None:
            errors.append(f"{row_id}: unknown {field} revision {pin['revision_id']}")
        elif upstream.get(object_id_key) != pin[object_id_key]:
            errors.append(f"{row_id}: {field} revision/object mismatch")
        pins.append({object_id_key: pin[object_id_key], "revision_id": pin["revision_id"]})
    return pins


def _validate_date_list(row_id: str, field: str, value: Any, index: dict[str, dict[str, Any]], errors: list[str]) -> list[str]:
    if not _strings(value):
        errors.append(f"{row_id}: {field} must be a list of strings")
        return []
    seen: set[str] = set()
    for identifier in value:
        if identifier in seen:
            errors.append(f"{row_id}: duplicate {field} reference {identifier}")
        seen.add(identifier)
        if identifier not in index:
            errors.append(f"{row_id}: unknown {field} reference {identifier}")
    return list(value)


def _validate_provenance(row_id: str, provenance: Any, errors: list[str]) -> None:
    expected = {"created_by", "created_at_utc", "reviewed_by", "reviewed_at_utc", "decision_basis"}
    if not isinstance(provenance, dict) or set(provenance) != expected:
        errors.append(f"{row_id}: review_provenance has an invalid field set")
        return
    if not _text(provenance.get("created_by")) or _utc(provenance.get("created_at_utc")) is None:
        errors.append(f"{row_id}: review provenance requires creator and exact UTC creation time")
    reviewed_at = _utc(provenance.get("reviewed_at_utc"))
    if provenance.get("reviewed_at_utc") is not None and reviewed_at is None:
        errors.append(f"{row_id}: reviewed_at_utc must be exact UTC or null")
    if provenance.get("reviewed_by") is not None and not _text(provenance.get("reviewed_by")):
        errors.append(f"{row_id}: reviewed_by must be text or null")
    if provenance.get("decision_basis") is not None and not _text(provenance.get("decision_basis")):
        errors.append(f"{row_id}: decision_basis must be text or null")


def _validate_scope(row_id: str, scope: Any, errors: list[str]) -> None:
    if not isinstance(scope, dict) or set(scope) != {"system_domain", "jurisdictions", "description"}:
        errors.append(f"{row_id}: scope has an invalid field set")
        return
    if not _text(scope.get("system_domain")) or not _strings(scope.get("jurisdictions")) or not _text(scope.get("description")):
        errors.append(f"{row_id}: scope requires system_domain, jurisdictions and description")


def _validate_temporal_scope(row_id: str, value: Any, vocab: dict[str, Any], errors: list[str]) -> None:
    if not isinstance(value, dict) or set(value) != {"scope_type", "start_at_utc", "end_at_utc", "description"}:
        errors.append(f"{row_id}: temporal_scope has an invalid field set")
        return
    if value.get("scope_type") not in set(vocab.get("temporal_scope_type") or []):
        errors.append(f"{row_id}: invalid temporal scope type")
    start = _utc(value.get("start_at_utc"))
    end = _utc(value.get("end_at_utc")) if value.get("end_at_utc") is not None else None
    if start is None or not _text(value.get("description")):
        errors.append(f"{row_id}: temporal_scope requires exact UTC start and description")
    if value.get("scope_type") == "BOUNDED" and end is None:
        errors.append(f"{row_id}: BOUNDED temporal_scope requires end_at_utc")
    if value.get("scope_type") == "OPEN_ENDED" and value.get("end_at_utc") is not None:
        errors.append(f"{row_id}: OPEN_ENDED temporal_scope cannot have end_at_utc")
    if start and end and end < start:
        errors.append(f"{row_id}: temporal_scope end cannot precede start")


def _validate_assumptions(
    row_id: str,
    assumptions: Any,
    vocab: dict[str, Any],
    observations: dict[str, dict[str, Any]],
    evidence: dict[str, dict[str, Any]],
    errors: list[str],
) -> set[str]:
    if not isinstance(assumptions, list) or not assumptions:
        errors.append(f"{row_id}: assumptions must be a non-empty list of explicit objects")
        return set()
    ids: set[str] = set()
    expected = {"assumption_id", "category", "statement", "rationale", "provenance", "basis_observation_ids", "basis_evidence_refs"}
    for assumption in assumptions:
        if not isinstance(assumption, dict) or set(assumption) != expected:
            errors.append(f"{row_id}: assumptions must distinguish explicit assumptions from evidence")
            continue
        assumption_id = assumption.get("assumption_id")
        if not _text(assumption_id) or assumption_id in ids:
            errors.append(f"{row_id}: assumption IDs must be unique and non-empty")
        if _text(assumption_id):
            ids.add(assumption_id)
        if assumption.get("category") not in set(vocab.get("assumption_category") or []):
            errors.append(f"{row_id}: invalid assumption category")
        for field in ("statement", "rationale", "provenance"):
            if not _text(assumption.get(field)):
                errors.append(f"{row_id}: assumption {field} is required")
        _validate_date_list(row_id, "assumption basis observations", assumption.get("basis_observation_ids"), observations, errors)
        _validate_date_list(row_id, "assumption basis evidence", assumption.get("basis_evidence_refs"), evidence, errors)
    return ids


def _validate_signposts(row_id: str, field: str, value: Any, vocab: dict[str, Any], errors: list[str], *, disconfirming: bool = False) -> None:
    if not isinstance(value, list):
        errors.append(f"{row_id}: {field} must be a list")
        return
    expected = {"signpost_id", "description", "observable_evidence_class", "compatibility_effect", "assessment_rule", "resolution_notes"}
    ids: set[str] = set()
    for signpost in value:
        if not isinstance(signpost, dict) or set(signpost) != expected:
            errors.append(f"{row_id}: {field} contains an invalid signpost")
            continue
        signpost_id = signpost.get("signpost_id")
        if not _text(signpost_id) or signpost_id in ids:
            errors.append(f"{row_id}: {field} IDs must be unique and non-empty")
        if _text(signpost_id):
            ids.add(signpost_id)
        for key in ("description", "observable_evidence_class", "assessment_rule", "resolution_notes"):
            if not _text(signpost.get(key)):
                errors.append(f"{row_id}: {field}.{key} is required")
        if signpost.get("compatibility_effect") not in set(vocab.get("signpost_effect") or []):
            errors.append(f"{row_id}: invalid signpost compatibility effect")
        if disconfirming and signpost.get("compatibility_effect") != "LESS_COMPATIBLE":
            errors.append(f"{row_id}: disconfirming signposts must be LESS_COMPATIBLE")


def _validate_pathways(row_id: str, value: Any, vocab: dict[str, Any], relationship_revisions: dict[str, dict[str, Any]], relevant_ids: set[str], errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append(f"{row_id}: transmission_pathways must be a list")
        return
    expected = {"pathway_id", "from_node", "to_node", "relationship_revision_ids", "epistemic_status", "rationale"}
    ids: set[str] = set()
    for pathway in value:
        if not isinstance(pathway, dict) or set(pathway) != expected:
            errors.append(f"{row_id}: transmission_pathways contains an invalid pathway")
            continue
        pathway_id = pathway.get("pathway_id")
        if not _text(pathway_id) or pathway_id in ids:
            errors.append(f"{row_id}: pathway IDs must be unique and non-empty")
        ids.add(pathway_id)
        for key in ("from_node", "to_node", "rationale"):
            if not _text(pathway.get(key)):
                errors.append(f"{row_id}: pathway {key} is required")
        if pathway.get("epistemic_status") not in set(vocab.get("transmission_epistemic_status") or []):
            errors.append(f"{row_id}: invalid transmission epistemic status")
        pins = pathway.get("relationship_revision_ids")
        if not _strings(pins):
            errors.append(f"{row_id}: pathway relationship_revision_ids must be a list of strings")
            continue
        if len(pins) != len(set(pins)):
            errors.append(f"{row_id}: duplicate pathway relationship revisions")
        for revision_id in pins:
            if revision_id not in relationship_revisions:
                errors.append(f"{row_id}: unknown pathway Relationship revision {revision_id}")
            if revision_id not in relevant_ids:
                errors.append(f"{row_id}: pathway Relationship must be a relevant Relationship revision")


def _review_and_lifecycle(row_id: str, row: dict[str, Any], vocab: dict[str, Any], errors: list[str], *, lifecycle_allowed: list[str] | None = None) -> None:
    review = row.get("review_state")
    lifecycle = row.get("lifecycle_state")
    if review not in set(vocab.get("review_state") or []):
        errors.append(f"{row_id}: invalid review_state")
    if lifecycle not in set(lifecycle_allowed or vocab.get("lifecycle_state") or []):
        errors.append(f"{row_id}: invalid lifecycle_state")
    provenance = row.get("review_provenance")
    _validate_provenance(row_id, provenance, errors)
    if not isinstance(provenance, dict):
        return
    reviewed = _utc(provenance.get("reviewed_at_utc"))
    if review == "ACCEPTED":
        if not _text(provenance.get("reviewed_by")) or reviewed is None or not _text(provenance.get("decision_basis")):
            errors.append(f"{row_id}: accepted review requires reviewer, timestamp and decision basis")
    elif review in {"DRAFT", "CANDIDATE", "UNDER_REVIEW"}:
        if any(provenance.get(key) is not None for key in ("reviewed_by", "reviewed_at_utc", "decision_basis")):
            errors.append(f"{row_id}: unresolved review cannot claim a completed decision")
    elif review == "REJECTED" and lifecycle != "RETIRED":
        errors.append(f"{row_id}: rejected scenario must be RETIRED")
    if lifecycle in {"ACTIVE", "WEAKENING"} and review != "ACCEPTED":
        errors.append(f"{row_id}: active/weakening scenario requires accepted review")
    if lifecycle in {"FALSIFIED", "SUPERSEDED"} and review != "ACCEPTED":
        errors.append(f"{row_id}: falsified/superseded scenario requires accepted review")


def _validate_upstream_pins(
    row_id: str,
    row: dict[str, Any],
    field: str,
    pins: list[dict[str, str]],
    index: dict[str, dict[str, Any]],
    created: datetime | None,
    errors: list[str],
) -> None:
    active_scenario = row.get("lifecycle_state") in {"ACTIVE", "WEAKENING"}
    for pin in pins:
        upstream = index.get(pin["revision_id"])
        if not upstream:
            continue
        if upstream.get("review_state") != "ACCEPTED":
            errors.append(f"{row_id}: {field} cannot use unaccepted upstream evidence")
        if upstream.get("lifecycle_state") in {"WITHDRAWN", "REJECTED"}:
            errors.append(f"{row_id}: withdrawn upstream evidence cannot be used")
        if active_scenario and upstream.get("lifecycle_state") not in {"ACTIVE", "WEAKENING"}:
            errors.append(f"{row_id}: non-active upstream cannot support an active scenario")
        upstream_created = _upstream_created(upstream)
        if created and upstream_created and upstream_created > created:
            errors.append(f"{row_id}: later upstream revision cannot support an earlier scenario")


def _validate_lineage(
    row_id: str,
    row: dict[str, Any],
    observations: dict[str, dict[str, Any]],
    evidence: dict[str, dict[str, Any]],
    created: datetime | None,
    errors: list[str],
) -> None:
    observation_ids = _validate_date_list(row_id, "supporting observations", row.get("supporting_observation_ids"), observations, errors)
    evidence_ids = _validate_date_list(row_id, "supporting evidence", row.get("supporting_evidence_refs"), evidence, errors)
    linked_evidence: set[str] = set()
    for observation_id in observation_ids:
        observation = observations.get(observation_id, {})
        refs = observation.get("evidence_refs") or []
        linked_evidence.update(ref for ref in refs if isinstance(ref, str))
        observed_at = _utc(observation.get("observed_at_utc"))
        if created and observed_at and observed_at > created:
            errors.append(f"{row_id}: later observation cannot support an earlier scenario")
    for evidence_id in evidence_ids:
        if evidence_id not in linked_evidence:
            errors.append(f"{row_id}: evidence {evidence_id} is not traceable through supporting observations")
        item = evidence.get(evidence_id, {})
        publication = item.get("publication_time") if isinstance(item, dict) else None
        published = None
        if isinstance(publication, dict):
            published = _utc(publication.get("published_at_utc"))
            if published is None and _text(publication.get("published_date")):
                try:
                    published = datetime.fromisoformat(publication["published_date"]).replace(tzinfo=UTC)
                except ValueError:
                    published = None
        if created and published and published > created:
            errors.append(f"{row_id}: later evidence cannot support an earlier scenario")


def _validate_set_row(
    row: dict[str, Any],
    schema: dict[str, Any],
    risk_revisions: dict[str, dict[str, Any]],
    observations: dict[str, dict[str, Any]],
    evidence: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    set_id = str(row.get("scenario_set_id") or "<missing-scenario-set-id>")
    required = set(schema["required_scenario_set_fields"])
    if set(row) != required:
        errors.append(f"{set_id}: missing/unknown Scenario Set fields; forecast fields are prohibited")
        return
    for field in ("scenario_set_id", "revision_id", "title", "revision_reason"):
        if not _text(row.get(field)):
            errors.append(f"{set_id}: {field} is required")
    if type(row.get("revision_number")) is not int or row["revision_number"] < 1:
        errors.append(f"{set_id}: revision_number must be a positive integer")
    if row.get("previous_revision_id") is not None and not _text(row["previous_revision_id"]):
        errors.append(f"{set_id}: previous_revision_id must be null or text")
    _validate_scope(set_id, row.get("scope"), errors)
    _validate_temporal_scope(set_id, row.get("temporal_scope"), schema["controlled_vocabularies"], errors)
    starting_risk_pins = _validate_pin_list(set_id, "starting_risk_state_revisions", row.get("starting_risk_state_revisions"), "state_id", risk_revisions, errors)
    if not starting_risk_pins:
        errors.append(f"{set_id}: Scenario Set requires at least one starting Risk/Regime revision")
    _validate_assumptions(set_id, row.get("shared_assumptions"), schema["controlled_vocabularies"], observations, evidence, errors)
    scenario_ids = row.get("scenario_ids")
    if not _strings(scenario_ids) or len(scenario_ids) < 2 or len(scenario_ids) != len(set(scenario_ids)):
        errors.append(f"{set_id}: Scenario Set requires at least two unique competing scenario IDs")
    divergence_points = row.get("divergence_points")
    if not isinstance(divergence_points, list) or not divergence_points:
        errors.append(f"{set_id}: divergence_points must be a non-empty list")
    else:
        expected = {"divergence_point_id", "description", "observable_trigger", "scenario_ids"}
        divergence_ids: set[str] = set()
        for point in divergence_points:
            if not isinstance(point, dict) or set(point) != expected:
                errors.append(f"{set_id}: invalid divergence point")
                continue
            point_id = point.get("divergence_point_id")
            if not _text(point_id) or point_id in divergence_ids:
                errors.append(f"{set_id}: divergence point IDs must be unique")
            divergence_ids.add(point_id)
            if not _text(point.get("description")) or not _text(point.get("observable_trigger")):
                errors.append(f"{set_id}: divergence point requires description and observable trigger")
            members = point.get("scenario_ids")
            if not _strings(members) or len(members) < 2:
                errors.append(f"{set_id}: divergence point must distinguish at least two scenarios")
            elif scenario_ids and not set(members).issubset(set(scenario_ids)):
                errors.append(f"{set_id}: divergence point references a non-member scenario")
    for field in ("first_created_at_utc", "effective_at_utc"):
        if _utc(row.get(field)) is None:
            errors.append(f"{set_id}: {field} must be exact UTC")
    latest_reviewed = row.get("latest_reviewed_at_utc")
    if latest_reviewed is not None and _utc(latest_reviewed) is None:
        errors.append(f"{set_id}: latest_reviewed_at_utc must be exact UTC or null")
    _review_and_lifecycle(
        set_id,
        row,
        schema["controlled_vocabularies"],
        errors,
        lifecycle_allowed=schema["controlled_vocabularies"].get("set_lifecycle_state"),
    )
    created = _utc(row.get("first_created_at_utc"))
    effective = _utc(row.get("effective_at_utc"))
    if created and effective and effective < created:
        errors.append(f"{set_id}: effective_at_utc cannot precede first creation")
    if latest_reviewed and created and _utc(latest_reviewed) < created:
        errors.append(f"{set_id}: latest review cannot predate creation")


def _validate_scenario_row(
    row: dict[str, Any],
    schema: dict[str, Any],
    set_revisions: dict[str, dict[str, Any]],
    risk_revisions: dict[str, dict[str, Any]],
    signal_revisions: dict[str, dict[str, Any]],
    relationship_revisions: dict[str, dict[str, Any]],
    observations: dict[str, dict[str, Any]],
    evidence: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    scenario_id = str(row.get("scenario_id") or "<missing-scenario-id>")
    required = set(schema["required_scenario_fields"])
    if set(row) != required:
        errors.append(f"{scenario_id}: missing/unknown Scenario fields; forecast fields are prohibited")
        return
    prohibited = {str(item).casefold() for item in schema.get("prohibited_fields", [])}
    prohibited_key = _has_prohibited_key(row, prohibited)
    if prohibited_key:
        errors.append(f"{scenario_id}: prohibited forecast/ranking field {prohibited_key}")
    for field in ("scenario_id", "scenario_set_id", "scenario_set_revision_id", "revision_id", "title", "description", "rationale", "revision_reason", "uncertainty_notes"):
        if not _text(row.get(field)):
            errors.append(f"{scenario_id}: {field} is required")
    if type(row.get("revision_number")) is not int or row["revision_number"] < 1:
        errors.append(f"{scenario_id}: revision_number must be a positive integer")
    if row.get("previous_revision_id") is not None and not _text(row["previous_revision_id"]):
        errors.append(f"{scenario_id}: previous_revision_id must be null or text")
    _validate_scope(scenario_id, row.get("scope"), errors)
    _validate_temporal_scope(scenario_id, row.get("temporal_scope"), schema["controlled_vocabularies"], errors)
    risk_pins = _validate_pin_list(scenario_id, "originating_risk_state_revisions", row.get("originating_risk_state_revisions"), "state_id", risk_revisions, errors)
    signal_pins = _validate_pin_list(scenario_id, "relevant_signal_revisions", row.get("relevant_signal_revisions"), "signal_id", signal_revisions, errors)
    relationship_pins = _validate_pin_list(scenario_id, "relevant_relationship_revisions", row.get("relevant_relationship_revisions"), "relationship_id", relationship_revisions, errors)
    if not risk_pins:
        errors.append(f"{scenario_id}: a Scenario must reference at least one Risk/Regime revision")
    created = _utc(row.get("first_created_at_utc"))
    effective = _utc(row.get("effective_at_utc"))
    latest_reviewed = _utc(row.get("latest_reviewed_at_utc")) if row.get("latest_reviewed_at_utc") is not None else None
    for field, parsed in (("first_created_at_utc", created), ("effective_at_utc", effective)):
        if parsed is None:
            errors.append(f"{scenario_id}: {field} must be exact UTC")
    if row.get("latest_reviewed_at_utc") is not None and latest_reviewed is None:
        errors.append(f"{scenario_id}: latest_reviewed_at_utc must be exact UTC or null")
    if created and effective and effective < created:
        errors.append(f"{scenario_id}: effective_at_utc cannot precede first creation")
    if latest_reviewed and created and latest_reviewed < created:
        errors.append(f"{scenario_id}: latest review cannot predate creation")
    _review_and_lifecycle(scenario_id, row, schema["controlled_vocabularies"], errors)
    _validate_upstream_pins(scenario_id, row, "Risk/Regime", risk_pins, risk_revisions, created, errors)
    _validate_upstream_pins(scenario_id, row, "Signal", signal_pins, signal_revisions, created, errors)
    _validate_upstream_pins(scenario_id, row, "Relationship", relationship_pins, relationship_revisions, created, errors)
    _validate_lineage(scenario_id, row, observations, evidence, created, errors)
    assumption_ids = _validate_assumptions(scenario_id, row.get("assumptions"), schema["controlled_vocabularies"], observations, evidence, errors)
    shared_ids = row.get("shared_assumption_ids")
    if not _strings(shared_ids) or len(shared_ids) != len(set(shared_ids)):
        errors.append(f"{scenario_id}: shared_assumption_ids must be unique strings")
    set_row = set_revisions.get(row.get("scenario_set_revision_id"))
    if set_row is None:
        errors.append(f"{scenario_id}: unknown scenario_set_revision_id")
    else:
        if row.get("scenario_set_id") != set_row.get("scenario_set_id"):
            errors.append(f"{scenario_id}: scenario set/revision mismatch")
        if scenario_id not in (set_row.get("scenario_ids") or []):
            errors.append(f"{scenario_id}: Scenario is not a member of its Scenario Set revision")
        shared_definitions = {item.get("assumption_id") for item in set_row.get("shared_assumptions", []) if isinstance(item, dict)}
        if not set(shared_ids or []).issubset(shared_definitions):
            errors.append(f"{scenario_id}: unknown shared assumption reference")
    competitors = row.get("competing_scenario_ids")
    if not _strings(competitors) or len(competitors) != len(set(competitors)):
        errors.append(f"{scenario_id}: competing_scenario_ids must be unique strings")
    elif scenario_id in competitors:
        errors.append(f"{scenario_id}: a Scenario cannot compete with itself")
    if set_row and competitors and not set(competitors).issubset(set(set_row.get("scenario_ids") or [])):
        errors.append(f"{scenario_id}: competitor is outside its Scenario Set")
    divergence_ids = row.get("divergence_point_ids")
    set_divergence_ids = {item.get("divergence_point_id") for item in (set_row or {}).get("divergence_points", []) if isinstance(item, dict)}
    if not _strings(divergence_ids) or not set(divergence_ids).issubset(set_divergence_ids):
        errors.append(f"{scenario_id}: divergence_point_ids must reference the Scenario Set")
    if not assumption_ids:
        errors.append(f"{scenario_id}: explicit scenario assumptions are required")
    relevant_relationship_ids = {pin["revision_id"] for pin in relationship_pins}
    _validate_pathways(scenario_id, row.get("transmission_pathways"), schema["controlled_vocabularies"], relationship_revisions, relevant_relationship_ids, errors)
    _validate_signposts(scenario_id, "signposts", row.get("signposts"), schema["controlled_vocabularies"], errors)
    _validate_signposts(scenario_id, "disconfirming_signposts", row.get("disconfirming_signposts"), schema["controlled_vocabularies"], errors, disconfirming=True)
    for field in ("enabling_conditions", "inhibiting_conditions", "falsification_conditions"):
        if not _strings(row.get(field)) or not row[field]:
            errors.append(f"{scenario_id}: {field} must be a non-empty list of strings")


def _validate_history(
    schema: dict[str, Any],
    set_rows: list[dict[str, Any]],
    scenario_rows: list[dict[str, Any]],
    risks: dict[str, Any],
    signals: dict[str, Any],
    relationships: dict[str, Any],
    observations: dict[str, Any],
    evidence: dict[str, Any],
    canonical: dict[str, Any],
    *,
    previous_set_revisions: list[dict[str, Any]] | None = None,
    previous_scenario_revisions: list[dict[str, Any]] | None = None,
) -> ScenarioValidationReport:
    errors, risk_index, signal_index, relationship_index, observation_index, evidence_index, _ = _preflight(
        schema,
        {"version": schema.get("version"), "scenario_sets": set_rows, "scenarios": scenario_rows},
        risks,
        signals,
        relationships,
        observations,
        evidence,
        canonical,
    )
    if errors:
        return ScenarioValidationReport(tuple(errors))
    set_revision_index: dict[str, dict[str, Any]] = {}
    scenario_revision_ids: set[str] = set()
    for row in set_rows:
        if not isinstance(row, dict):
            errors.append("Scenario Set rows must be objects")
            continue
        revision_id = row.get("revision_id")
        if not _text(revision_id):
            errors.append("Scenario Set revision_id must be non-empty text")
            continue
        if revision_id in set_revision_index:
            errors.append(f"duplicate Scenario Set revision_id {revision_id}")
        set_revision_index[revision_id] = row
        _validate_set_row(row, schema, risk_index, observation_index, evidence_index, errors)
    for row in scenario_rows:
        if not isinstance(row, dict):
            errors.append("Scenario rows must be objects")
            continue
        revision_id = row.get("revision_id")
        if not _text(revision_id):
            errors.append("Scenario revision_id must be non-empty text")
            continue
        if revision_id in scenario_revision_ids:
            errors.append(f"duplicate Scenario revision_id {revision_id}")
        scenario_revision_ids.add(revision_id)
        _validate_scenario_row(row, schema, set_revision_index, risk_index, signal_index, relationship_index, observation_index, evidence_index, errors)

    set_groups: dict[str, list[dict[str, Any]]] = {}
    scenario_groups: dict[str, list[dict[str, Any]]] = {}
    for row in set_rows:
        if isinstance(row, dict):
            set_groups.setdefault(str(row.get("scenario_set_id")), []).append(row)
    for row in scenario_rows:
        if isinstance(row, dict):
            scenario_groups.setdefault(str(row.get("scenario_id")), []).append(row)

    for row in set_rows:
        if not isinstance(row, dict):
            continue
        for scenario_id in row.get("scenario_ids", []) if isinstance(row.get("scenario_ids"), list) else []:
            if scenario_id not in scenario_groups:
                errors.append(f"{row.get('scenario_set_id', '<missing-scenario-set-id>')}: Scenario Set member has no retained Scenario revision")

    transitions = {
        "DRAFT": {"DRAFT", "CANDIDATE", "UNDER_REVIEW"},
        "CANDIDATE": {"CANDIDATE", "UNDER_REVIEW", "REJECTED"},
        "UNDER_REVIEW": {"UNDER_REVIEW", "ACCEPTED", "REJECTED"},
        "ACCEPTED": {"ACCEPTED", "UNDER_REVIEW"},
        "REJECTED": {"UNDER_REVIEW"},
    }
    for label, groups in (("Scenario Set", set_groups), ("Scenario", scenario_groups)):
        for object_id, revisions in groups.items():
            ordered = sorted(revisions, key=lambda item: item.get("revision_number", 0))
            numbers = [item.get("revision_number") for item in ordered]
            if numbers != list(range(1, len(ordered) + 1)):
                errors.append(f"{object_id}: {label} revision numbers must be contiguous from 1")
            for index, row in enumerate(ordered):
                current_time = _revision_time(row)
                if index == 0:
                    if row.get("previous_revision_id") is not None:
                        errors.append(f"{object_id}: first {label} revision cannot have a predecessor")
                    continue
                previous = ordered[index - 1]
                if row.get("previous_revision_id") != previous.get("revision_id"):
                    errors.append(f"{object_id}: {label} predecessor link is not preserved")
                if current_time is None or _revision_time(previous) is None or current_time <= _revision_time(previous):
                    errors.append(f"{object_id}: {label} revision time must strictly advance")
                if row.get("first_created_at_utc") != previous.get("first_created_at_utc"):
                    errors.append(f"{object_id}: first creation time must remain stable")
                if row.get("review_state") not in transitions.get(previous.get("review_state"), set()):
                    errors.append(f"{object_id}: invalid {label} review transition")
                if _utc(row.get("effective_at_utc")) and _utc(previous.get("effective_at_utc")) and _utc(row["effective_at_utc"]) < _utc(previous["effective_at_utc"]):
                    errors.append(f"{object_id}: effective time cannot move backwards")
    if previous_set_revisions is not None:
        current = {row.get("revision_id"): row for row in set_rows}
        for old in previous_set_revisions:
            if not isinstance(old, dict) or current.get(old.get("revision_id")) != old:
                errors.append("retained Scenario Set revision was removed or rewritten")
    if previous_scenario_revisions is not None:
        current = {row.get("revision_id"): row for row in scenario_rows}
        for old in previous_scenario_revisions:
            if not isinstance(old, dict) or current.get(old.get("revision_id")) != old:
                errors.append("retained Scenario revision was removed or rewritten")
    return ScenarioValidationReport(tuple(errors))


def validate_scenario_history(
    schema: dict[str, Any],
    scenario_sets: list[dict[str, Any]],
    scenarios: list[dict[str, Any]],
    risks: dict[str, Any],
    signals: dict[str, Any],
    relationships: dict[str, Any],
    observations: dict[str, Any],
    evidence: dict[str, Any],
    canonical: dict[str, Any],
    *,
    previous_set_revisions: list[dict[str, Any]] | None = None,
    previous_scenario_revisions: list[dict[str, Any]] | None = None,
) -> ScenarioValidationReport:
    """Validate synthetic/proposed Scenario history without production authority."""
    return _validate_history(
        schema, scenario_sets, scenarios, risks, signals, relationships,
        observations, evidence, canonical,
        previous_set_revisions=previous_set_revisions,
        previous_scenario_revisions=previous_scenario_revisions,
    )


def validate_scenarios(
    schema: dict[str, Any],
    dataset: dict[str, Any],
    risks: dict[str, Any],
    signals: dict[str, Any],
    relationships: dict[str, Any],
    observations: dict[str, Any],
    evidence: dict[str, Any],
    canonical: dict[str, Any],
) -> ScenarioValidationReport:
    """Validate the intentionally empty production Scenario dataset."""
    errors: list[str] = []
    if not isinstance(dataset, dict):
        return ScenarioValidationReport(("Scenario dataset must be an object",))
    if dataset.get("population_state") != "CLOSED_NO_PRODUCTION_SCENARIOS":
        errors.append("Scenario dataset must remain in its closed population state")
    policy = schema.get("population_policy") if isinstance(schema, dict) else {}
    for key in ("production_population_allowed", "automatic_ingestion_allowed", "candidate_scenario_storage_allowed", "synthetic_production_population_allowed", "public_scenario_projection_allowed"):
        if not isinstance(policy, dict) or policy.get(key) is not False:
            errors.append(f"Scenario population policy must keep {key}=false")
    boundary = schema.get("layer_boundary") if isinstance(schema, dict) else {}
    for key in ("canonical_mutation_allowed", "observation_mutation_allowed", "signal_mutation_allowed", "relationship_mutation_allowed", "risk_state_mutation_allowed", "automatic_scenario_promotion_allowed", "forecast_fields_allowed", "probability_fields_allowed", "public_scenario_projection_allowed"):
        if not isinstance(boundary, dict) or boundary.get(key) is not False:
            errors.append(f"Scenario boundary must keep {key}=false")
    public_policy = schema.get("public_projection_policy") if isinstance(schema, dict) else {}
    if not isinstance(public_policy, dict) or public_policy.get("scenario_projection_allowed") is not False:
        errors.append("Scenario public projection must remain closed")
    if isinstance(dataset.get("scenario_sets"), list) and dataset["scenario_sets"]:
        errors.append("closed production population gate prohibits every Scenario Set")
    if isinstance(dataset.get("scenarios"), list) and dataset["scenarios"]:
        errors.append("closed production population gate prohibits every Scenario")
    history = validate_scenario_history(
        schema,
        dataset.get("scenario_sets") if isinstance(dataset.get("scenario_sets"), list) else [],
        dataset.get("scenarios") if isinstance(dataset.get("scenarios"), list) else [],
        risks, signals, relationships, observations, evidence, canonical,
    )
    return ScenarioValidationReport(tuple(errors) + history.errors)


def scenario_state_as_of(
    schema: dict[str, Any],
    scenario_sets: list[dict[str, Any]],
    scenarios: list[dict[str, Any]],
    risks: dict[str, Any],
    signals: dict[str, Any],
    relationships: dict[str, Any],
    observations: dict[str, Any],
    evidence: dict[str, Any],
    canonical: dict[str, Any],
    at_utc: str,
) -> dict[str, dict[str, Any]]:
    """Return the latest Scenario revision available at an explicit UTC time."""
    report = validate_scenario_history(schema, scenario_sets, scenarios, risks, signals, relationships, observations, evidence, canonical)
    at = _utc(at_utc)
    if not report.ok or at is None:
        raise ValueError("invalid Scenario history/as-of timestamp: " + "; ".join(report.errors))
    active_set_revisions = {
        row["revision_id"]
        for row in scenario_sets
        if _revision_time(row) is not None and _revision_time(row) <= at
    }
    result: dict[str, dict[str, Any]] = {}
    for row in sorted(scenarios, key=lambda item: (item["scenario_id"], item["revision_number"])):
        if _revision_time(row) is not None and _revision_time(row) <= at and row["scenario_set_revision_id"] in active_set_revisions:
            result[row["scenario_id"]] = {
                "revision_id": row["revision_id"],
                "scenario_set_id": row["scenario_set_id"],
                "title": row["title"],
                "review_state": row["review_state"],
                "lifecycle_state": row["lifecycle_state"],
                "effective_at_utc": row["effective_at_utc"],
            }
    return result


def public_scenario_projection(
    schema: dict[str, Any],
    dataset: dict[str, Any],
    risks: dict[str, Any],
    signals: dict[str, Any],
    relationships: dict[str, Any],
    observations: dict[str, Any],
    evidence: dict[str, Any],
    canonical: dict[str, Any],
) -> dict[str, Any]:
    report = validate_scenarios(schema, dataset, risks, signals, relationships, observations, evidence, canonical)
    if not report.ok:
        raise ValueError("invalid Scenario dataset: " + "; ".join(report.errors))
    return {
        "metadata": {
            "projection_type": "REVIEWED_SCENARIO_CLOSED_PROJECTION",
            "schema_version": schema.get("version"),
            "population_state": dataset.get("population_state"),
            "internal_scenario_set_count": 0,
            "internal_scenario_count": 0,
            "public_scenario_projection_allowed": False,
        },
        "scenario_sets": [],
        "scenarios": [],
    }
