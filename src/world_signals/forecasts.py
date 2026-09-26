"""Validation and closed public projection for the reviewed Forecast contract.

Forecasts are prospective, explicitly resolvable claims.  A stable
``forecast_id`` identifies a question series, while each analytical update has
its own ``issuance_id`` and remains independently scoreable.  Administrative
corrections revise one issuance without changing its substantive content.
Outcome resolution and scoring are deliberately outside this module. Production
population is limited to the explicit reviewed prospective pilot transaction;
automatic ingestion and public Forecast projection remain closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from typing import Any


UTC = timezone.utc
ADMINISTRATIVE_MUTABLE_FIELDS = {
    "revision_id",
    "revision_number",
    "previous_revision_id",
    "revision_kind",
    "revision_created_at_utc",
    "review_provenance",
    "revision_reason",
    "rationale",
}
LOCKED_QUESTION_FIELDS = (
    "forecast_type",
    "question",
    "target",
    "horizon",
    "resolution",
)


@dataclass(frozen=True)
class ForecastValidationReport:
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


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _all_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return {str(key) for key in value} | {
            child for item in value.values() for child in _all_keys(item)
        }
    if isinstance(value, list):
        return {child for item in value for child in _all_keys(item)}
    return set()


def _parse_date_or_utc(publication: Any) -> datetime | None:
    if not isinstance(publication, dict):
        return None
    precise = _utc(publication.get("published_at_utc"))
    if precise:
        return precise
    civil = publication.get("published_date")
    if _text(civil):
        try:
            return datetime.fromisoformat(civil).replace(tzinfo=UTC)
        except ValueError:
            return None
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
        revision_id = row.get("revision_id")
        if not _text(revision_id):
            errors.append(f"{label} {row[id_key]} must have a revision_id")
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


def _index_sources(data: Any, errors: list[str]) -> set[str]:
    if not isinstance(data, dict) or not isinstance(data.get("sources"), list):
        errors.append("Source Registry must contain a sources list")
        return set()
    result: set[str] = set()
    for row in data["sources"]:
        if not isinstance(row, dict) or not _text(row.get("source_id")):
            errors.append("Source Registry rows must have a non-empty source_id")
            continue
        if row["source_id"] in result:
            errors.append(f"duplicate source_id {row['source_id']}")
        result.add(row["source_id"])
    return result


def _upstream_created(row: dict[str, Any]) -> datetime | None:
    provenance = row.get("review_provenance")
    if isinstance(provenance, dict):
        return _utc(provenance.get("created_at_utc"))
    return _utc(row.get("created_at_utc"))


def _preflight(
    schema: Any,
    dataset: Any,
    scenarios: Any,
    risks: Any,
    signals: Any,
    relationships: Any,
    observations: Any,
    evidence: Any,
    canonical: Any,
    sources: Any,
) -> tuple[list[str], dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]], set[str]]:
    errors: list[str] = []
    inputs = (schema, dataset, scenarios, risks, signals, relationships, observations, evidence, canonical, sources)
    if not all(isinstance(value, dict) for value in inputs):
        return ["Forecast inputs must be objects"], {}, {}, {}, {}, {}, {}, set()
    try:
        json.dumps(inputs, allow_nan=False)
    except (TypeError, ValueError):
        return ["Forecast inputs must contain finite JSON values"], {}, {}, {}, {}, {}, {}, set()
    if schema.get("version") != "0.1":
        errors.append("unsupported Forecast schema version")
    if schema.get("architecture_position") != "FORECASTS":
        errors.append("Forecast schema architecture_position must be FORECASTS")
    if dataset.get("version") != schema.get("version"):
        errors.append("Forecast dataset version must match schema version")
    if not isinstance(dataset.get("forecasts"), list):
        errors.append("forecasts must be a list")
    if not _strings(schema.get("required_forecast_fields")) or not schema["required_forecast_fields"]:
        errors.append("required_forecast_fields must be a non-empty string list")
    for key in ("layer_boundary", "population_policy", "public_projection_policy", "controlled_vocabularies"):
        if not isinstance(schema.get(key), dict):
            errors.append(f"{key} must be an object")
    scenario_revisions = _index_rows(scenarios, "scenarios", "scenario_id", errors, "Scenario")
    risk_revisions = _index_rows(risks, "states", "state_id", errors, "Risk/Regime")
    signal_revisions = _index_rows(signals, "signals", "signal_id", errors, "Signal")
    relationship_revisions = _index_rows(relationships, "relationships", "relationship_id", errors, "Relationship")
    observation_by_id = _index_observations(observations, errors)
    evidence_by_id = _index_evidence(evidence, errors)
    if not isinstance(canonical.get("records"), list):
        errors.append("Canonical must contain a records list")
    source_ids = _index_sources(sources, errors)
    return errors, scenario_revisions, risk_revisions, signal_revisions, relationship_revisions, observation_by_id, evidence_by_id, source_ids


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
    result: list[dict[str, str]] = []
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
        result.append({object_id_key: pin[object_id_key], "revision_id": pin["revision_id"]})
    return result


def _validate_provenance(row_id: str, value: Any, errors: list[str]) -> None:
    expected = {"created_by", "created_at_utc", "reviewed_by", "reviewed_at_utc", "decision_basis"}
    if not isinstance(value, dict) or set(value) != expected:
        errors.append(f"{row_id}: review_provenance has an invalid field set")
        return
    if not _text(value.get("created_by")) or _utc(value.get("created_at_utc")) is None:
        errors.append(f"{row_id}: review provenance requires creator and exact UTC creation time")
    if value.get("reviewed_at_utc") is not None and _utc(value.get("reviewed_at_utc")) is None:
        errors.append(f"{row_id}: reviewed_at_utc must be exact UTC or null")
    if value.get("reviewed_by") is not None and not _text(value.get("reviewed_by")):
        errors.append(f"{row_id}: reviewed_by must be text or null")
    if value.get("decision_basis") is not None and not _text(value.get("decision_basis")):
        errors.append(f"{row_id}: decision_basis must be text or null")


def _validate_forecast_provenance(row_id: str, value: Any, vocab: dict[str, Any], errors: list[str]) -> None:
    expected = {"issuer_type", "issuer_id", "method_family", "human_reviewed"}
    if not isinstance(value, dict) or set(value) != expected:
        errors.append(f"{row_id}: forecast_provenance has an invalid field set")
        return
    if value.get("issuer_type") not in set(vocab.get("issuer_type") or []):
        errors.append(f"{row_id}: invalid issuer_type")
    if not _text(value.get("issuer_id")) or not _text(value.get("method_family")):
        errors.append(f"{row_id}: forecast provenance requires issuer_id and method_family")
    if type(value.get("human_reviewed")) is not bool:
        errors.append(f"{row_id}: human_reviewed must be boolean")


def _validate_review_lifecycle(row_id: str, row: dict[str, Any], vocab: dict[str, Any], errors: list[str]) -> None:
    review = row.get("review_state")
    lifecycle = row.get("lifecycle_state")
    if review not in set(vocab.get("review_state") or []):
        errors.append(f"{row_id}: invalid review_state")
    if lifecycle not in set(vocab.get("lifecycle_state") or []):
        errors.append(f"{row_id}: invalid lifecycle_state")
    provenance = row.get("review_provenance")
    _validate_provenance(row_id, provenance, errors)
    forecast_provenance = row.get("forecast_provenance")
    _validate_forecast_provenance(row_id, forecast_provenance, vocab, errors)
    if review == "ACCEPTED":
        if not isinstance(forecast_provenance, dict) or forecast_provenance.get("human_reviewed") is not True:
            errors.append(f"{row_id}: accepted forecast requires human_reviewed provenance")
        if not isinstance(provenance, dict) or not _text(provenance.get("reviewed_by")) or _utc(provenance.get("reviewed_at_utc")) is None or not _text(provenance.get("decision_basis")):
            errors.append(f"{row_id}: accepted forecast requires reviewer, timestamp and decision basis")
    elif review in {"DRAFT", "CANDIDATE", "UNDER_REVIEW"}:
        if isinstance(provenance, dict) and any(provenance.get(key) is not None for key in ("reviewed_by", "reviewed_at_utc", "decision_basis")):
            errors.append(f"{row_id}: unresolved review cannot claim a completed decision")
    elif review == "REJECTED" and lifecycle != "WITHDRAWN":
        errors.append(f"{row_id}: rejected forecast must be WITHDRAWN")
    if lifecycle in {"OPEN", "CLOSED_AWAITING_RESOLUTION"} and review != "ACCEPTED":
        errors.append(f"{row_id}: open forecast requires accepted review")
    if lifecycle == "VOID":
        if not _text(row.get("void_reason")) or _utc(row.get("voided_at_utc")) is None:
            errors.append(f"{row_id}: VOID forecast requires governed reason and timestamp")
    elif row.get("void_reason") is not None or row.get("voided_at_utc") is not None:
        errors.append(f"{row_id}: non-VOID forecast cannot carry void metadata")


def _validate_target_and_horizon(row_id: str, row: dict[str, Any], vocab: dict[str, Any], errors: list[str]) -> None:
    target = row.get("target")
    if not isinstance(target, dict) or set(target) != {"target_kind", "target_identifier", "definition"}:
        errors.append(f"{row_id}: target has an invalid field set")
    elif target.get("target_kind") not in set(vocab.get("target_kind") or []) or not _text(target.get("target_identifier")) or not _text(target.get("definition")):
        errors.append(f"{row_id}: target requires controlled kind, identifier and definition")
    horizon = row.get("horizon")
    if not isinstance(horizon, dict) or set(horizon) != {"horizon_type", "end_at_utc", "description"}:
        errors.append(f"{row_id}: horizon has an invalid field set")
    elif horizon.get("horizon_type") not in set(vocab.get("horizon_type") or []) or _utc(horizon.get("end_at_utc")) is None or not _text(horizon.get("description")):
        errors.append(f"{row_id}: horizon requires type, exact end and description")


def _validate_resolution(row_id: str, row: dict[str, Any], vocab: dict[str, Any], source_ids: set[str], errors: list[str]) -> None:
    resolution = row.get("resolution")
    expected = {
        "window_start_at_utc", "window_end_at_utc", "resolution_rule", "resolution_source_ids",
        "fallback_source_ids", "resolution_source_basis", "missing_data_policy", "cancellation_policy",
        "vintage_policy", "vintage_definition", "measurement_time_basis",
    }
    if not isinstance(resolution, dict) or set(resolution) != expected:
        errors.append(f"{row_id}: resolution has an invalid field set")
        return
    start = _utc(resolution.get("window_start_at_utc"))
    end = _utc(resolution.get("window_end_at_utc"))
    if start is None or end is None or end < start:
        errors.append(f"{row_id}: resolution window must be ordered exact UTC")
    for field in ("resolution_rule", "resolution_source_basis", "vintage_definition", "measurement_time_basis"):
        if not _text(resolution.get(field)):
            errors.append(f"{row_id}: resolution {field} is required")
    if resolution.get("missing_data_policy") not in set(vocab.get("missing_data_policy") or []):
        errors.append(f"{row_id}: invalid missing_data_policy")
    if resolution.get("cancellation_policy") not in set(vocab.get("cancellation_policy") or []):
        errors.append(f"{row_id}: invalid cancellation_policy")
    if resolution.get("vintage_policy") not in set(vocab.get("vintage_policy") or []):
        errors.append(f"{row_id}: invalid vintage_policy")
    primary = resolution.get("resolution_source_ids")
    fallback = resolution.get("fallback_source_ids")
    if not _strings(primary) or not primary:
        errors.append(f"{row_id}: at least one authoritative resolution source is required")
        primary = []
    if not _strings(fallback) or len(fallback) != len(set(fallback)):
        errors.append(f"{row_id}: fallback_source_ids must be unique strings")
        fallback = []
    for source_id in list(primary) + list(fallback):
        if source_id not in source_ids:
            errors.append(f"{row_id}: unknown resolution source {source_id}")
    if set(fallback) - set(primary):
        errors.append(f"{row_id}: fallback sources must be included in resolution_source_ids")
    if row.get("forecast_type") == "NUMERIC_POINT" and resolution.get("vintage_policy") == "NOT_APPLICABLE":
        errors.append(f"{row_id}: numeric forecast requires explicit resolution vintage policy")
    if row.get("forecast_type") != "NUMERIC_POINT" and resolution.get("vintage_policy") != "NOT_APPLICABLE":
        errors.append(f"{row_id}: non-numeric forecast must use NOT_APPLICABLE vintage policy")


def _validate_value(row_id: str, row: dict[str, Any], schema: dict[str, Any], errors: list[str]) -> None:
    forecast_type = row.get("forecast_type")
    vocab = schema["controlled_vocabularies"]
    if forecast_type not in set(vocab.get("forecast_type") or []):
        errors.append(f"{row_id}: invalid forecast_type")
        return
    value = row.get("forecast_value")
    if not isinstance(value, dict):
        errors.append(f"{row_id}: forecast_value must be an object")
        return
    if forecast_type == "BINARY_EVENT":
        if set(value) != {"probability"} or not _finite(value.get("probability")) or not 0 <= value["probability"] <= 1:
            errors.append(f"{row_id}: binary probability must be finite and within [0,1]")
    elif forecast_type == "CATEGORICAL":
        if set(value) != {"outcomes", "mutually_exclusive", "collectively_exhaustive", "coverage_basis"}:
            errors.append(f"{row_id}: categorical forecast_value has an invalid field set")
            return
        outcomes = value.get("outcomes")
        if not isinstance(outcomes, list) or len(outcomes) < 2:
            errors.append(f"{row_id}: categorical forecast requires at least two outcomes")
            return
        if value.get("mutually_exclusive") is not True or value.get("collectively_exhaustive") is not True or not _text(value.get("coverage_basis")):
            errors.append(f"{row_id}: categorical outcomes require exclusivity, exhaustiveness and basis")
        ids: set[str] = set()
        total = 0.0
        for outcome in outcomes:
            if not isinstance(outcome, dict) or set(outcome) != {"outcome_id", "label", "definition", "probability"}:
                errors.append(f"{row_id}: categorical outcome has an invalid field set")
                continue
            outcome_id = outcome.get("outcome_id")
            if not _text(outcome_id) or outcome_id in ids:
                errors.append(f"{row_id}: categorical outcome IDs must be unique")
            if _text(outcome_id):
                ids.add(outcome_id)
            if not _text(outcome.get("label")) or not _text(outcome.get("definition")) or not _finite(outcome.get("probability")) or not 0 <= outcome["probability"] <= 1:
                errors.append(f"{row_id}: categorical outcomes require bounded probabilities and definitions")
            elif _finite(outcome.get("probability")):
                total += outcome["probability"]
        tolerance = float(schema.get("forecast_policy", {}).get("categorical_probability_sum_tolerance", 0.000001))
        if abs(total - 1.0) > tolerance:
            errors.append(f"{row_id}: categorical probabilities must sum to 1 within tolerance")
    elif forecast_type == "NUMERIC_POINT":
        if set(value) != {"estimate", "unit"} or not _finite(value.get("estimate")) or not _text(value.get("unit")):
            errors.append(f"{row_id}: numeric forecast requires finite estimate and unit")


def _validate_assumptions(
    row_id: str,
    value: Any,
    observations: dict[str, dict[str, Any]],
    evidence: dict[str, dict[str, Any]],
    cutoff: datetime | None,
    errors: list[str],
) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{row_id}: assumptions must be explicit and non-empty")
        return
    expected = {"assumption_id", "statement", "rationale", "provenance", "basis_observation_ids", "basis_evidence_refs"}
    ids: set[str] = set()
    for assumption in value:
        if not isinstance(assumption, dict) or set(assumption) != expected:
            errors.append(f"{row_id}: assumptions must remain distinct from evidence")
            continue
        assumption_id = assumption.get("assumption_id")
        if not _text(assumption_id) or assumption_id in ids:
            errors.append(f"{row_id}: assumption IDs must be unique")
        if _text(assumption_id):
            ids.add(assumption_id)
        for field in ("statement", "rationale", "provenance"):
            if not _text(assumption.get(field)):
                errors.append(f"{row_id}: assumption {field} is required")
        for field, index in (("basis_observation_ids", observations), ("basis_evidence_refs", evidence)):
            refs = assumption.get(field)
            if not isinstance(refs, list) or any(not _text(item) or item not in index for item in refs):
                errors.append(f"{row_id}: assumption {field} must reference known lineage")
            elif cutoff:
                for ref in refs:
                    if field == "basis_observation_ids":
                        observed_at = _utc(index[ref].get("observed_at_utc"))
                        if observed_at and observed_at > cutoff:
                            errors.append(f"{row_id}: assumption observation after information cutoff cannot support the forecast")
                    else:
                        published = _parse_date_or_utc(index[ref].get("publication_time"))
                        if published and published > cutoff:
                            errors.append(f"{row_id}: assumption evidence published after information cutoff cannot be attached")


def _validate_lineage(row_id: str, row: dict[str, Any], observations: dict[str, dict[str, Any]], evidence: dict[str, dict[str, Any]], cutoff: datetime | None, errors: list[str]) -> None:
    observation_ids = row.get("supporting_observation_ids")
    evidence_refs = row.get("supporting_evidence_refs")
    if not isinstance(observation_ids, list) or len(observation_ids) != len(set(observation_ids)):
        errors.append(f"{row_id}: supporting_observation_ids must be unique")
        observation_ids = []
    if not isinstance(evidence_refs, list) or len(evidence_refs) != len(set(evidence_refs)):
        errors.append(f"{row_id}: supporting_evidence_refs must be unique")
        evidence_refs = []
    linked_evidence: set[str] = set()
    for observation_id in observation_ids:
        if observation_id not in observations:
            errors.append(f"{row_id}: unknown supporting observation {observation_id}")
            continue
        observation = observations[observation_id]
        linked_evidence.update(ref for ref in observation.get("evidence_refs", []) if isinstance(ref, str))
        observed_at = _utc(observation.get("observed_at_utc"))
        if cutoff and observed_at and observed_at > cutoff:
            errors.append(f"{row_id}: observation after information cutoff cannot support the forecast")
    for evidence_id in evidence_refs:
        if evidence_id not in evidence:
            errors.append(f"{row_id}: unknown supporting evidence {evidence_id}")
            continue
        if evidence_id not in linked_evidence:
            errors.append(f"{row_id}: evidence {evidence_id} is not traceable through supporting observations")
        published = _parse_date_or_utc(evidence[evidence_id].get("publication_time"))
        if cutoff and published and published > cutoff:
            errors.append(f"{row_id}: evidence published after information cutoff cannot be attached")


def _validate_upstream(
    row_id: str,
    row: dict[str, Any],
    field: str,
    pins: list[dict[str, str]],
    index: dict[str, dict[str, Any]],
    issued: datetime | None,
    errors: list[str],
) -> None:
    active_forecast = row.get("lifecycle_state") in {"OPEN", "CLOSED_AWAITING_RESOLUTION"}
    for pin in pins:
        upstream = index.get(pin["revision_id"])
        if not upstream:
            continue
        if upstream.get("review_state") != "ACCEPTED":
            errors.append(f"{row_id}: {field} cannot use unaccepted upstream context")
        if upstream.get("lifecycle_state") in {"WITHDRAWN", "REJECTED"}:
            errors.append(f"{row_id}: withdrawn upstream context cannot be used")
        if active_forecast and upstream.get("lifecycle_state") not in {"ACTIVE", "WEAKENING"}:
            errors.append(f"{row_id}: non-active upstream context cannot support an open forecast")
        created = _upstream_created(upstream)
        if issued and created and created > issued:
            errors.append(f"{row_id}: later upstream revision cannot support an earlier issuance")


def _validate_row(
    row: dict[str, Any],
    schema: dict[str, Any],
    indexes: tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]], set[str]],
    errors: list[str],
) -> None:
    scenario_revisions, risk_revisions, signal_revisions, relationship_revisions, observations, evidence, source_ids = indexes
    row_id = str(row.get("revision_id") or row.get("issuance_id") or "<missing-forecast-revision>")
    required = set(schema["required_forecast_fields"])
    if set(row) != required:
        errors.append(f"{row_id}: missing/unknown Forecast fields; outcome and scoring fields are prohibited")
        return
    prohibited = {str(item).casefold() for item in schema.get("prohibited_fields", [])}
    prohibited_hits = sorted({key.casefold() for key in _all_keys(row)} & prohibited)
    if prohibited_hits:
        errors.append(f"{row_id}: prohibited outcome/scoring field(s) {prohibited_hits}")
    for field in ("forecast_id", "issuance_id", "revision_id", "question", "rationale", "revision_reason"):
        if not _text(row.get(field)):
            errors.append(f"{row_id}: {field} is required")
    if type(row.get("issuance_number")) is not int or row["issuance_number"] < 1:
        errors.append(f"{row_id}: issuance_number must be a positive integer")
    if type(row.get("revision_number")) is not int or row["revision_number"] < 1:
        errors.append(f"{row_id}: revision_number must be a positive integer")
    for field in ("previous_issuance_id", "previous_revision_id"):
        if row.get(field) is not None and not _text(row[field]):
            errors.append(f"{row_id}: {field} must be null or non-empty text")
    vocab = schema["controlled_vocabularies"]
    if row.get("issuance_kind") not in set(vocab.get("issuance_kind") or []):
        errors.append(f"{row_id}: invalid issuance_kind")
    if row.get("revision_kind") not in set(vocab.get("revision_kind") or []):
        errors.append(f"{row_id}: invalid revision_kind")
    if row.get("forecast_type") not in set(vocab.get("forecast_type") or []):
        errors.append(f"{row_id}: invalid forecast_type")
    issued = _utc(row.get("issued_at_utc"))
    cutoff = _utc(row.get("information_cutoff_at_utc"))
    revision_created = _utc(row.get("revision_created_at_utc"))
    if issued is None or cutoff is None or revision_created is None:
        errors.append(f"{row_id}: issued, information cutoff and revision creation times must be exact UTC")
    if issued and cutoff and cutoff > issued:
        errors.append(f"{row_id}: information cutoff cannot follow issue time")
    if issued and revision_created and revision_created < issued:
        errors.append(f"{row_id}: revision creation cannot precede issue time")
    _validate_target_and_horizon(row_id, row, vocab, errors)
    _validate_value(row_id, row, schema, errors)
    _validate_resolution(row_id, row, vocab, source_ids, errors)
    scenario_pins = _validate_pin_list(row_id, "scenario_references", row.get("scenario_references"), "scenario_id", scenario_revisions, errors)
    risk_pins = _validate_pin_list(row_id, "risk_state_references", row.get("risk_state_references"), "state_id", risk_revisions, errors)
    signal_pins = _validate_pin_list(row_id, "signal_references", row.get("signal_references"), "signal_id", signal_revisions, errors)
    relationship_pins = _validate_pin_list(row_id, "relationship_references", row.get("relationship_references"), "relationship_id", relationship_revisions, errors)
    _validate_upstream(row_id, row, "Scenario", scenario_pins, scenario_revisions, issued, errors)
    _validate_upstream(row_id, row, "Risk/Regime", risk_pins, risk_revisions, issued, errors)
    _validate_upstream(row_id, row, "Signal", signal_pins, signal_revisions, issued, errors)
    _validate_upstream(row_id, row, "Relationship", relationship_pins, relationship_revisions, issued, errors)
    _validate_lineage(row_id, row, observations, evidence, cutoff, errors)
    _validate_assumptions(row_id, row.get("assumptions"), observations, evidence, cutoff, errors)
    _validate_review_lifecycle(row_id, row, vocab, errors)
    if row.get("issuance_kind") == "INITIAL" and row.get("issuance_number") != 1:
        errors.append(f"{row_id}: INITIAL issuance must be number 1")
    if row.get("issuance_kind") == "ANALYTICAL_UPDATE" and row.get("issuance_number") == 1:
        errors.append(f"{row_id}: ANALYTICAL_UPDATE must follow an earlier issuance")


def _locked_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {field: row.get(field) for field in LOCKED_QUESTION_FIELDS}


def _administrative_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in ADMINISTRATIVE_MUTABLE_FIELDS}


def _validate_history(
    schema: dict[str, Any],
    rows: list[dict[str, Any]],
    scenarios: dict[str, Any],
    risks: dict[str, Any],
    signals: dict[str, Any],
    relationships: dict[str, Any],
    observations: dict[str, Any],
    evidence: dict[str, Any],
    canonical: dict[str, Any],
    sources: dict[str, Any],
    *,
    previous_revisions: list[dict[str, Any]] | None = None,
) -> ForecastValidationReport:
    preflight = _preflight(schema, {"version": schema.get("version"), "forecasts": rows}, scenarios, risks, signals, relationships, observations, evidence, canonical, sources)
    errors, scenario_index, risk_index, signal_index, relationship_index, observation_index, evidence_index, source_ids = preflight
    indexes = (scenario_index, risk_index, signal_index, relationship_index, observation_index, evidence_index, source_ids)
    if errors:
        return ForecastValidationReport(tuple(errors))
    revision_ids: set[str] = set()
    issuance_ids: set[str] = set()
    rows_by_issuance: dict[str, list[dict[str, Any]]] = {}
    rows_by_series: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if not isinstance(row, dict):
            errors.append("Forecast rows must be objects")
            continue
        revision_id = row.get("revision_id")
        issuance_id = row.get("issuance_id")
        if not _text(revision_id):
            errors.append("Forecast revision_id must be non-empty text")
        elif revision_id in revision_ids:
            errors.append(f"duplicate Forecast revision_id {revision_id}")
        else:
            revision_ids.add(revision_id)
        if not _text(issuance_id):
            errors.append("Forecast issuance_id must be non-empty text")
        elif issuance_id not in issuance_ids:
            issuance_ids.add(issuance_id)
        _validate_row(row, schema, indexes, errors)
        if _text(issuance_id):
            rows_by_issuance.setdefault(issuance_id, []).append(row)
        if _text(row.get("forecast_id")):
            rows_by_series.setdefault(row["forecast_id"], []).append(row)

    for issuance_id, issuance_rows in rows_by_issuance.items():
        ordered = sorted(issuance_rows, key=lambda item: item.get("revision_number", 0))
        numbers = [row.get("revision_number") for row in ordered]
        if numbers != list(range(1, len(ordered) + 1)):
            errors.append(f"{issuance_id}: revision numbers must be contiguous from 1")
        first = ordered[0]
        if first.get("revision_kind") != "ORIGINAL" or first.get("previous_revision_id") is not None:
            errors.append(f"{issuance_id}: first issuance revision must be ORIGINAL without predecessor")
        for index, row in enumerate(ordered):
            if index == 0:
                continue
            previous = ordered[index - 1]
            if row.get("previous_revision_id") != previous.get("revision_id"):
                errors.append(f"{issuance_id}: revision predecessor link is not preserved")
            current_created = _utc(row.get("revision_created_at_utc"))
            previous_created = _utc(previous.get("revision_created_at_utc"))
            if current_created is None or previous_created is None or current_created <= previous_created:
                errors.append(f"{issuance_id}: revision creation time must strictly advance")
            if row.get("revision_kind") != "ADMINISTRATIVE_CORRECTION":
                errors.append(f"{issuance_id}: only administrative corrections may revise an issuance")
            if _administrative_payload(row) != _administrative_payload(previous):
                errors.append(f"{issuance_id}: administrative correction changed substantive forecast content")
            if row.get("issued_at_utc") != previous.get("issued_at_utc") or row.get("information_cutoff_at_utc") != previous.get("information_cutoff_at_utc"):
                errors.append(f"{issuance_id}: administrative correction changed issue or cutoff time")

    latest_by_issuance: dict[str, dict[str, Any]] = {}
    first_by_issuance: dict[str, dict[str, Any]] = {}
    for issuance_id, issuance_rows in rows_by_issuance.items():
        ordered = sorted(issuance_rows, key=lambda item: item.get("revision_number", 0))
        first_by_issuance[issuance_id] = ordered[0]
        latest_by_issuance[issuance_id] = ordered[-1]
    for forecast_id, series_rows in rows_by_series.items():
        first_issuances = {
            row["issuance_id"]: row
            for row in series_rows
            if row.get("revision_number") == 1
        }
        ordered = sorted(first_issuances.values(), key=lambda item: item.get("issuance_number", 0))
        numbers = [row.get("issuance_number") for row in ordered]
        if numbers != list(range(1, len(ordered) + 1)):
            errors.append(f"{forecast_id}: issuance numbers must be contiguous from 1")
        if ordered:
            if ordered[0].get("issuance_kind") != "INITIAL" or ordered[0].get("previous_issuance_id") is not None:
                errors.append(f"{forecast_id}: first issuance must be INITIAL without predecessor")
            baseline_locked = _locked_payload(ordered[0])
            previous = None
            for row in ordered:
                if _locked_payload(row) != baseline_locked:
                    errors.append(f"{forecast_id}: forecast question, target or resolution changed after issuance")
                if previous is not None:
                    if row.get("issuance_kind") != "ANALYTICAL_UPDATE":
                        errors.append(f"{forecast_id}: later issuance must be ANALYTICAL_UPDATE")
                    if row.get("previous_issuance_id") != previous.get("issuance_id"):
                        errors.append(f"{forecast_id}: issuance predecessor link is not preserved")
                    current_issue = _utc(row.get("issued_at_utc"))
                    previous_issue = _utc(previous.get("issued_at_utc"))
                    if current_issue is None or previous_issue is None or current_issue <= previous_issue:
                        errors.append(f"{forecast_id}: analytical issuance time must strictly advance")
                previous = row
    duplicate_keys: dict[tuple[Any, ...], str] = {}
    for row in first_by_issuance.values():
        provenance = row.get("forecast_provenance") or {}
        horizon = row.get("horizon") or {}
        key = (row.get("forecast_id"), row.get("issued_at_utc"), provenance.get("issuer_id"), horizon.get("end_at_utc"))
        prior = duplicate_keys.get(key)
        if prior and prior != row.get("issuance_id"):
            errors.append(f"{row.get('forecast_id')}: duplicate issuance key for {prior} and {row.get('issuance_id')}")
        duplicate_keys[key] = row.get("issuance_id")
    if previous_revisions is not None:
        current = {row.get("revision_id"): row for row in rows}
        for old in previous_revisions:
            if not isinstance(old, dict) or current.get(old.get("revision_id")) != old:
                errors.append("retained Forecast revision was removed or rewritten")
    return ForecastValidationReport(tuple(errors))


def validate_forecast_history(
    schema: dict[str, Any],
    rows: list[dict[str, Any]],
    scenarios: dict[str, Any],
    risks: dict[str, Any],
    signals: dict[str, Any],
    relationships: dict[str, Any],
    observations: dict[str, Any],
    evidence: dict[str, Any],
    canonical: dict[str, Any],
    sources: dict[str, Any],
    *,
    previous_revisions: list[dict[str, Any]] | None = None,
) -> ForecastValidationReport:
    """Validate synthetic/proposed Forecast history without production authority."""
    return _validate_history(
        schema, rows, scenarios, risks, signals, relationships, observations,
        evidence, canonical, sources, previous_revisions=previous_revisions,
    )


def validate_forecasts(
    schema: dict[str, Any],
    dataset: dict[str, Any],
    scenarios: dict[str, Any],
    risks: dict[str, Any],
    signals: dict[str, Any],
    relationships: dict[str, Any],
    observations: dict[str, Any],
    evidence: dict[str, Any],
    canonical: dict[str, Any],
    sources: dict[str, Any],
    admission_transaction: dict[str, Any] | None = None,
) -> ForecastValidationReport:
    """Validate the production Forecast dataset and its admission boundary."""
    errors: list[str] = []
    if not isinstance(dataset, dict):
        return ForecastValidationReport(("Forecast dataset must be an object",))
    rows = dataset.get("forecasts") if isinstance(dataset.get("forecasts"), list) else []
    allowed_population_states = {"CLOSED_NO_PRODUCTION_FORECASTS", "PILOT_PRODUCTION_FORECASTS_REVIEWED"}
    if dataset.get("population_state") not in allowed_population_states:
        errors.append("Forecast dataset has an invalid population state")
    policy = schema.get("population_policy") if isinstance(schema, dict) else {}
    for key in ("automatic_ingestion_allowed", "candidate_forecast_storage_allowed", "synthetic_production_population_allowed", "public_forecast_projection_allowed"):
        if not isinstance(policy, dict) or policy.get(key) is not False:
            errors.append(f"Forecast population policy must keep {key}=false")
    if not isinstance(policy, dict) or policy.get("production_population_allowed") is not True:
        errors.append("Forecast population policy must explicitly allow only the reviewed pilot path")
    if rows and dataset.get("population_state") != "PILOT_PRODUCTION_FORECASTS_REVIEWED":
        errors.append("populated Forecast dataset must declare the reviewed pilot population state")
    if not rows and dataset.get("population_state") != "CLOSED_NO_PRODUCTION_FORECASTS":
        errors.append("empty Forecast dataset must retain the closed population state")
    boundary = schema.get("layer_boundary") if isinstance(schema, dict) else {}
    for key in ("canonical_mutation_allowed", "observation_mutation_allowed", "signal_mutation_allowed", "relationship_mutation_allowed", "risk_state_mutation_allowed", "scenario_mutation_allowed", "automatic_forecast_generation_allowed", "outcome_resolution_allowed", "forecast_scoring_allowed", "model_learning_allowed", "public_forecast_projection_allowed"):
        if not isinstance(boundary, dict) or boundary.get(key) is not False:
            errors.append(f"Forecast boundary must keep {key}=false")
    public_policy = schema.get("public_projection_policy") if isinstance(schema, dict) else {}
    if not isinstance(public_policy, dict) or public_policy.get("forecast_projection_allowed") is not False:
        errors.append("Forecast public projection must remain closed")
    history = validate_forecast_history(schema, rows, scenarios, risks, signals, relationships, observations, evidence, canonical, sources)
    if rows:
        from .forecast_admission import validate_admission_transaction
        errors.extend(validate_admission_transaction(schema, dataset, admission_transaction))
    elif admission_transaction is not None:
        errors.append("an admission transaction cannot accompany an empty Forecast dataset")
    return ForecastValidationReport(tuple(errors) + history.errors)


def forecast_state_as_of(
    schema: dict[str, Any],
    rows: list[dict[str, Any]],
    scenarios: dict[str, Any],
    risks: dict[str, Any],
    signals: dict[str, Any],
    relationships: dict[str, Any],
    observations: dict[str, Any],
    evidence: dict[str, Any],
    canonical: dict[str, Any],
    sources: dict[str, Any],
    at_utc: str,
) -> dict[str, dict[str, Any]]:
    """Return the latest revision of each issued Forecast available at UTC time."""
    report = validate_forecast_history(schema, rows, scenarios, risks, signals, relationships, observations, evidence, canonical, sources)
    at = _utc(at_utc)
    if not report.ok or at is None:
        raise ValueError("invalid Forecast history/as-of timestamp: " + "; ".join(report.errors))
    result: dict[str, dict[str, Any]] = {}
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if _utc(row.get("revision_created_at_utc")) and _utc(row["revision_created_at_utc"]) <= at:
            grouped.setdefault(row["issuance_id"], []).append(row)
    for issuance_id, issuance_rows in grouped.items():
        latest = max(issuance_rows, key=lambda row: row["revision_number"])
        result[issuance_id] = {
            "forecast_id": latest["forecast_id"],
            "issuance_id": issuance_id,
            "issuance_number": latest["issuance_number"],
            "forecast_type": latest["forecast_type"],
            "question": latest["question"],
            "forecast_value": latest["forecast_value"],
            "issued_at_utc": latest["issued_at_utc"],
            "lifecycle_state": latest["lifecycle_state"],
            "revision_id": latest["revision_id"],
        }
    return result


def public_forecast_projection(
    schema: dict[str, Any],
    dataset: dict[str, Any],
    scenarios: dict[str, Any],
    risks: dict[str, Any],
    signals: dict[str, Any],
    relationships: dict[str, Any],
    observations: dict[str, Any],
    evidence: dict[str, Any],
    canonical: dict[str, Any],
    sources: dict[str, Any],
    admission_transaction: dict[str, Any] | None = None,
) -> dict[str, Any]:
    report = validate_forecasts(schema, dataset, scenarios, risks, signals, relationships, observations, evidence, canonical, sources, admission_transaction)
    if not report.ok:
        raise ValueError("invalid Forecast dataset: " + "; ".join(report.errors))
    return {
        "metadata": {
            "projection_type": "REVIEWED_FORECAST_CLOSED_PROJECTION",
            "schema_version": schema.get("version"),
            "population_state": dataset.get("population_state"),
            "internal_forecast_count": 0,
            "public_forecast_count": 0,
            "public_forecast_projection_allowed": False,
            "outcome_resolution_allowed": False,
            "forecast_scoring_allowed": False,
        },
        "forecasts": [],
    }
