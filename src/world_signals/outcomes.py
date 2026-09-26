"""Validation and closed projection for governed Forecast Outcomes.

An Outcome is the downstream record of what happened under one immutable
Forecast question.  ``outcome_id`` is deliberately keyed to the Forecast
series, not an issuance: one real-world result can therefore resolve many
independently scoreable Forecast issuances.  Evaluation and scoring are outside
this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from typing import Any


UTC = timezone.utc
TERMINAL_STATUSES = {"RESOLVED", "VOID", "UNRESOLVABLE"}
ACTIVE_ISSUANCE_LIFECYCLES = {"OPEN", "CLOSED_AWAITING_RESOLUTION", "SUPERSEDED"}
REVISION_KINDS = {"ORIGINAL", "RESOLUTION_UPDATE", "OUTCOME_CORRECTION", "ADMINISTRATIVE_CORRECTION"}
ADMINISTRATIVE_MUTABLE_FIELDS = {
    "revision_id",
    "revision_number",
    "previous_revision_id",
    "revision_kind",
    "world_signals_reviewed_at_utc",
    "review_provenance",
    "revision_reason",
    "resolution_rationale",
    "provenance",
}
LOCKED_OUTCOME_FIELDS = (
    "outcome_id",
    "forecast_id",
    "forecast_type",
    "resolution_rule_reference",
)


@dataclass(frozen=True)
class OutcomeValidationReport:
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


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


def _index_sources(data: Any, errors: list[str]) -> set[str]:
    if not isinstance(data, dict) or not isinstance(data.get("sources"), list):
        errors.append("Source Registry must contain a sources list")
        return set()
    result: set[str] = set()
    for source in data["sources"]:
        if not isinstance(source, dict) or not _text(source.get("source_id")):
            errors.append("Source Registry rows must have a non-empty source_id")
            continue
        source_id = source["source_id"]
        if source_id in result:
            errors.append(f"duplicate source_id {source_id}")
        result.add(source_id)
    return result


def _index_evidence(data: Any, errors: list[str]) -> dict[str, dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("evidence"), list):
        errors.append("evidence must contain a list")
        return {}
    result: dict[str, dict[str, Any]] = {}
    for evidence in data["evidence"]:
        if not isinstance(evidence, dict) or not _text(evidence.get("evidence_id")):
            errors.append("evidence rows must have a non-empty evidence_id")
            continue
        evidence_id = evidence["evidence_id"]
        if evidence_id in result:
            errors.append(f"duplicate evidence_id {evidence_id}")
        result[evidence_id] = evidence
    return result


def _publication_time(row: dict[str, Any]) -> datetime | None:
    publication = row.get("publication_time")
    if not isinstance(publication, dict):
        return None
    precise = _utc(publication.get("published_at_utc"))
    if precise:
        return precise
    date = publication.get("published_date")
    if _text(date):
        try:
            return datetime.fromisoformat(date).replace(tzinfo=UTC)
        except ValueError:
            return None
    return None


def _index_forecasts(data: Any, errors: list[str]) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    if not isinstance(data, dict) or not isinstance(data.get("forecasts"), list):
        errors.append("Forecast dataset must contain a forecasts list")
        return {}, {}
    by_issuance: dict[str, list[dict[str, Any]]] = {}
    for row in data["forecasts"]:
        if not isinstance(row, dict) or not _text(row.get("issuance_id")):
            errors.append("Forecast rows must have a non-empty issuance_id")
            continue
        by_issuance.setdefault(row["issuance_id"], []).append(row)
    latest: dict[str, dict[str, Any]] = {}
    for issuance_id, revisions in by_issuance.items():
        ordered = sorted(revisions, key=lambda row: row.get("revision_number", 0))
        latest[issuance_id] = ordered[-1]
    return latest, by_issuance


def _preflight(
    schema: Any,
    dataset: Any,
    forecasts: Any,
    evidence: Any,
    sources: Any,
) -> tuple[list[str], dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]], set[str]]:
    errors: list[str] = []
    inputs = (schema, dataset, forecasts, evidence, sources)
    if not all(isinstance(value, dict) for value in inputs):
        return ["Outcome inputs must be objects"], {}, {}, {}, set()
    try:
        json.dumps(inputs, allow_nan=False)
    except (TypeError, ValueError):
        return ["Outcome inputs must contain finite JSON values"], {}, {}, {}, set()
    if schema.get("version") != "0.1":
        errors.append("unsupported Outcome schema version")
    if schema.get("architecture_position") != "OUTCOMES_RESOLUTION":
        errors.append("Outcome schema architecture_position must be OUTCOMES_RESOLUTION")
    if dataset.get("version") != schema.get("version"):
        errors.append("Outcome dataset version must match schema version")
    if not isinstance(dataset.get("outcomes"), list):
        errors.append("outcomes must be a list")
    if not isinstance(schema.get("required_outcome_fields"), list) or not schema["required_outcome_fields"]:
        errors.append("required_outcome_fields must be a non-empty list")
    forecast_latest, forecast_history = _index_forecasts(forecasts, errors)
    evidence_index = _index_evidence(evidence, errors)
    source_ids = _index_sources(sources, errors)
    return errors, forecast_latest, forecast_history, evidence_index, source_ids


def _review_provenance(row_id: str, value: Any, errors: list[str]) -> None:
    expected = {"created_by", "created_at_utc", "reviewed_by", "reviewed_at_utc", "decision_basis"}
    if not isinstance(value, dict) or set(value) != expected:
        errors.append(f"{row_id}: review_provenance has an invalid field set")
        return
    if not _text(value.get("created_by")) or _utc(value.get("created_at_utc")) is None:
        errors.append(f"{row_id}: review provenance requires creator and exact UTC creation time")
    if value.get("reviewed_by") is not None and not _text(value.get("reviewed_by")):
        errors.append(f"{row_id}: reviewed_by must be text or null")
    if value.get("reviewed_at_utc") is not None and _utc(value.get("reviewed_at_utc")) is None:
        errors.append(f"{row_id}: reviewed_at_utc must be exact UTC or null")
    if value.get("decision_basis") is not None and not _text(value.get("decision_basis")):
        errors.append(f"{row_id}: decision_basis must be text or null")


def _source_rule_snapshot(forecast: dict[str, Any]) -> dict[str, Any] | None:
    resolution = forecast.get("resolution")
    target = forecast.get("target")
    horizon = forecast.get("horizon")
    if not isinstance(resolution, dict) or not isinstance(target, dict) or not isinstance(horizon, dict):
        return None
    return {
        "forecast_id": forecast.get("forecast_id"),
        "forecast_type": forecast.get("forecast_type"),
        "target": target,
        "horizon": horizon,
        "window_start_at_utc": resolution.get("window_start_at_utc"),
        "window_end_at_utc": resolution.get("window_end_at_utc"),
        "resolution_rule": resolution.get("resolution_rule"),
        "resolution_source_ids": resolution.get("resolution_source_ids"),
        "fallback_source_ids": resolution.get("fallback_source_ids"),
        "resolution_source_basis": resolution.get("resolution_source_basis"),
        "missing_data_policy": resolution.get("missing_data_policy"),
        "cancellation_policy": resolution.get("cancellation_policy"),
        "vintage_policy": resolution.get("vintage_policy"),
        "vintage_definition": resolution.get("vintage_definition"),
        "measurement_time_basis": resolution.get("measurement_time_basis"),
    }


def _latest_forecast_for_series(
    forecast_latest: dict[str, dict[str, Any]],
    forecast_id: str,
) -> list[dict[str, Any]]:
    rows = [row for row in forecast_latest.values() if row.get("forecast_id") == forecast_id]
    return sorted(rows, key=lambda row: row.get("issuance_number", 0))


def _validate_issuance_eligibility(
    row_id: str,
    outcome: dict[str, Any],
    forecast_latest: dict[str, dict[str, Any]],
    errors: list[str],
) -> list[dict[str, Any]]:
    issuance_ids = outcome.get("eligible_issuance_ids")
    if not isinstance(issuance_ids, list) or not issuance_ids or len(issuance_ids) != len(set(issuance_ids)):
        errors.append(f"{row_id}: eligible_issuance_ids must be a non-empty unique list")
        return []
    series_rows: list[dict[str, Any]] = []
    outcome_id = outcome.get("forecast_id")
    outcome_type = outcome.get("forecast_type")
    rule = outcome.get("resolution_rule_reference")
    end = _utc(rule.get("window_start_at_utc")) if isinstance(rule, dict) else None
    for issuance_id in issuance_ids:
        forecast = forecast_latest.get(issuance_id)
        if not forecast:
            errors.append(f"{row_id}: unknown eligible Forecast issuance {issuance_id}")
            continue
        if forecast.get("forecast_id") != outcome_id or forecast.get("forecast_type") != outcome_type:
            errors.append(f"{row_id}: eligible issuance does not match the Outcome series/type")
        elif _source_rule_snapshot(forecast) != rule:
            errors.append(f"{row_id}: eligible issuance uses incompatible resolution semantics")
        lifecycle = forecast.get("lifecycle_state")
        if lifecycle not in ACTIVE_ISSUANCE_LIFECYCLES:
            errors.append(f"{row_id}: void or withdrawn Forecast issuance cannot be eligible")
        issued = _utc(forecast.get("issued_at_utc"))
        if end and (issued is None or issued > end):
            errors.append(f"{row_id}: eligible issuance must precede the resolution window")
        series_rows.append(forecast)
    return series_rows


def _validate_resolution_rule(
    row_id: str,
    outcome: dict[str, Any],
    forecast: dict[str, Any] | None,
    source_ids: set[str],
    errors: list[str],
) -> None:
    rule = outcome.get("resolution_rule_reference")
    if not isinstance(rule, dict) or forecast is None:
        errors.append(f"{row_id}: resolution_rule_reference must match a Forecast issuance")
        return
    expected = _source_rule_snapshot(forecast)
    if expected is None or rule != expected:
        errors.append(f"{row_id}: Outcome resolution rule must equal the pre-declared Forecast rule")
        return
    primary = rule.get("resolution_source_ids")
    fallback = rule.get("fallback_source_ids")
    if not isinstance(primary, list) or not primary or any(source not in source_ids for source in primary):
        errors.append(f"{row_id}: Outcome rule must contain known authoritative sources")
    if not isinstance(fallback, list) or any(source not in source_ids for source in fallback):
        errors.append(f"{row_id}: Outcome rule must contain known fallback sources")


def _validate_observed_outcome(
    row_id: str,
    outcome: dict[str, Any],
    forecast: dict[str, Any] | None,
    errors: list[str],
) -> None:
    status = outcome.get("resolution_status")
    observed = outcome.get("observed_outcome")
    if status in {"PENDING", "VOID", "UNRESOLVABLE", "DISPUTED"}:
        if observed is not None:
            errors.append(f"{row_id}: {status} Outcome cannot carry a resolved observed_outcome")
        return
    if status != "RESOLVED" or forecast is None:
        return
    if not isinstance(observed, dict):
        errors.append(f"{row_id}: RESOLVED Outcome requires an observed_outcome")
        return
    forecast_type = forecast.get("forecast_type")
    if forecast_type == "BINARY_EVENT":
        if set(observed) != {"event_occurred"} or type(observed.get("event_occurred")) is not bool:
            errors.append(f"{row_id}: binary Outcome requires event_occurred boolean")
    elif forecast_type == "CATEGORICAL":
        if set(observed) != {"outcome_id"} or not _text(observed.get("outcome_id")):
            errors.append(f"{row_id}: categorical Outcome requires one original outcome_id")
        else:
            options = (forecast.get("forecast_value") or {}).get("outcomes", [])
            if observed["outcome_id"] not in {item.get("outcome_id") for item in options if isinstance(item, dict)}:
                errors.append(f"{row_id}: categorical Outcome is outside the original category set")
    elif forecast_type == "NUMERIC_POINT":
        if set(observed) != {"value", "unit"} or not _finite(observed.get("value")) or not _text(observed.get("unit")):
            errors.append(f"{row_id}: numeric Outcome requires finite value and unit")
        elif observed.get("unit") != (forecast.get("forecast_value") or {}).get("unit"):
            errors.append(f"{row_id}: numeric Outcome unit must equal the Forecast unit")


def _validate_sources_and_times(
    row_id: str,
    outcome: dict[str, Any],
    forecast: dict[str, Any] | None,
    evidence_index: dict[str, dict[str, Any]],
    source_ids: set[str],
    errors: list[str],
) -> None:
    status = outcome.get("resolution_status")
    source_id = outcome.get("resolution_source_id")
    fallback_used = outcome.get("fallback_source_used")
    if type(fallback_used) is not bool:
        errors.append(f"{row_id}: fallback_source_used must be boolean")
    rule = outcome.get("resolution_rule_reference") or {}
    fallback = set(rule.get("fallback_source_ids") or [])
    # The Forecast contract keeps fallback IDs within the declared source list;
    # Outcome resolution therefore treats the non-fallback subset as primary.
    primary = set(rule.get("resolution_source_ids") or []) - fallback
    if status in {"RESOLVED", "DISPUTED"}:
        if source_id not in source_ids or not _text(source_id):
            errors.append(f"{row_id}: resolved/disputed Outcome requires a known resolution source")
        elif fallback_used and source_id not in fallback:
            errors.append(f"{row_id}: fallback source was not pre-authorised")
        elif not fallback_used and source_id not in primary:
            errors.append(f"{row_id}: primary resolution source was not pre-authorised")
        if fallback_used and not _text(outcome.get("fallback_reason")):
            errors.append(f"{row_id}: fallback use requires a reason")
        if not fallback_used and outcome.get("fallback_reason") is not None:
            errors.append(f"{row_id}: fallback_reason requires fallback_source_used")
    elif source_id is not None or outcome.get("fallback_reason") is not None:
        errors.append(f"{row_id}: non-resolved Outcome cannot carry resolution source metadata")
    evidence_refs = outcome.get("evidence_refs")
    if not isinstance(evidence_refs, list) or len(evidence_refs) != len(set(evidence_refs)):
        errors.append(f"{row_id}: evidence_refs must be a unique list")
    else:
        for evidence_id in evidence_refs:
            if evidence_id not in evidence_index:
                errors.append(f"{row_id}: unknown resolution evidence {evidence_id}")
    event_at = _utc(outcome.get("event_at_utc"))
    published_at = _utc(outcome.get("evidence_publication_at_utc"))
    resolved_at = _utc(outcome.get("resolution_at_utc"))
    reviewed_at = _utc(outcome.get("world_signals_reviewed_at_utc"))
    resolution = (forecast or {}).get("resolution") or {}
    start = _utc(resolution.get("window_start_at_utc"))
    end = _utc(resolution.get("window_end_at_utc"))
    if status == "RESOLVED":
        if resolved_at is None or reviewed_at is None or published_at is None:
            errors.append(f"{row_id}: resolved Outcome requires resolution, review and evidence publication timestamps")
        if event_at is None or (start and event_at < start) or (end and event_at > end):
            errors.append(f"{row_id}: resolved event time must fall within the Forecast resolution window")
        if published_at and reviewed_at and reviewed_at < published_at:
            errors.append(f"{row_id}: review cannot precede evidence publication")
    elif status in {"VOID", "UNRESOLVABLE", "DISPUTED"} and resolved_at is None:
        errors.append(f"{row_id}: terminal or disputed Outcome requires resolution_at_utc")
    elif status == "PENDING" and resolved_at is not None:
        errors.append(f"{row_id}: PENDING Outcome cannot carry resolution_at_utc")
    if status != "RESOLVED" and any(value is not None for value in (event_at, published_at)):
        errors.append(f"{row_id}: non-resolved Outcome cannot carry event/publication timestamps")
    if status in {"RESOLVED", "DISPUTED"} and not _text(outcome.get("source_locator")):
        errors.append(f"{row_id}: resolved/disputed Outcome requires a source locator")


def _validate_status_metadata(row_id: str, row: dict[str, Any], errors: list[str]) -> None:
    status = row.get("resolution_status")
    if status not in {"PENDING", "RESOLVED", "VOID", "UNRESOLVABLE", "DISPUTED"}:
        errors.append(f"{row_id}: invalid resolution_status")
        return
    void_reason = row.get("void_reason")
    dispute_notes = row.get("dispute_notes")
    rationale = row.get("resolution_rationale")
    if status == "VOID" and not _text(void_reason):
        errors.append(f"{row_id}: VOID requires a governed reason")
    if status == "VOID" and _text(void_reason) and any(term in void_reason.casefold() for term in ("poor", "wrong", "failed", "performance", "score")):
        errors.append(f"{row_id}: forecast performance cannot justify VOID")
    if status != "VOID" and void_reason is not None:
        errors.append(f"{row_id}: void_reason is only permitted for VOID")
    if status == "UNRESOLVABLE" and not _text(rationale):
        errors.append(f"{row_id}: UNRESOLVABLE requires a rationale")
    if status == "DISPUTED" and not _text(dispute_notes):
        errors.append(f"{row_id}: DISPUTED requires explicit dispute notes")
    if status != "DISPUTED" and dispute_notes is not None:
        errors.append(f"{row_id}: dispute_notes is only permitted for DISPUTED")


def _validate_row(
    row: Any,
    schema: dict[str, Any],
    forecast_latest: dict[str, dict[str, Any]],
    evidence_index: dict[str, dict[str, Any]],
    source_ids: set[str],
    errors: list[str],
) -> None:
    if not isinstance(row, dict):
        errors.append("Outcome rows must be objects")
        return
    row_id = str(row.get("revision_id") or "<missing-outcome-revision>")
    required = set(schema.get("required_outcome_fields") or [])
    if set(row) != required:
        errors.append(f"{row_id}: missing/unknown Outcome fields; scoring fields are prohibited")
        return
    prohibited = {str(item).casefold() for item in schema.get("prohibited_fields", [])}
    all_keys = {str(key).casefold() for key in row}
    if all_keys & prohibited:
        errors.append(f"{row_id}: prohibited scoring/evaluation field(s) {sorted(all_keys & prohibited)}")
    for field in ("outcome_id", "forecast_id", "revision_id", "resolution_rationale", "revision_reason"):
        if not _text(row.get(field)):
            errors.append(f"{row_id}: {field} is required")
    if row.get("outcome_id") != row.get("forecast_id"):
        errors.append(f"{row_id}: outcome_id must equal the stable Forecast series identity")
    if _utc(row.get("world_signals_reviewed_at_utc")) is None:
        errors.append(f"{row_id}: world_signals_reviewed_at_utc must be exact UTC")
    if type(row.get("revision_number")) is not int or row["revision_number"] < 1:
        errors.append(f"{row_id}: revision_number must be a positive integer")
    for field in ("previous_revision_id", "resolution_source_id", "fallback_reason", "void_reason", "dispute_notes"):
        if row.get(field) is not None and not _text(row[field]):
            errors.append(f"{row_id}: {field} must be null or non-empty text")
    forecast = None
    series = _latest_forecast_for_series(forecast_latest, row.get("forecast_id"))
    if not series:
        errors.append(f"{row_id}: unknown Forecast series {row.get('forecast_id')}")
    else:
        forecast = series[0]
        if row.get("forecast_type") != forecast.get("forecast_type"):
            errors.append(f"{row_id}: Outcome forecast_type must match Forecast series")
    _validate_status_metadata(row_id, row, errors)
    if row.get("revision_kind") not in REVISION_KINDS:
        errors.append(f"{row_id}: invalid revision_kind")
    _validate_issuance_eligibility(row_id, row, forecast_latest, errors)
    _validate_resolution_rule(row_id, row, forecast, source_ids, errors)
    _validate_observed_outcome(row_id, row, forecast, errors)
    _validate_sources_and_times(row_id, row, forecast, evidence_index, source_ids, errors)
    _review_provenance(row_id, row.get("review_provenance"), errors)
    provenance = row.get("provenance")
    if not isinstance(provenance, dict) or set(provenance) != {"outcome_established_by", "method", "reviewed"}:
        errors.append(f"{row_id}: provenance has an invalid field set")
    elif not _text(provenance.get("outcome_established_by")) or not _text(provenance.get("method")) or type(provenance.get("reviewed")) is not bool:
        errors.append(f"{row_id}: provenance requires established_by, method and reviewed")


def _locked_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {field: row.get(field) for field in LOCKED_OUTCOME_FIELDS}


def _administrative_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in ADMINISTRATIVE_MUTABLE_FIELDS}


def _valid_status_transition(previous: str, current: str, revision_kind: str) -> bool:
    if previous == current:
        return True
    if previous in {"VOID", "UNRESOLVABLE"}:
        return False
    if previous == "PENDING":
        return current in {"RESOLVED", "VOID", "UNRESOLVABLE", "DISPUTED"}
    if previous == "DISPUTED":
        return current in {"RESOLVED", "VOID", "UNRESOLVABLE", "DISPUTED"}
    if previous == "RESOLVED":
        return current == "DISPUTED" and revision_kind == "OUTCOME_CORRECTION"
    return False


def validate_outcome_history(
    schema: dict[str, Any],
    rows: list[dict[str, Any]],
    forecasts: dict[str, Any],
    evidence: dict[str, Any],
    sources: dict[str, Any],
    *,
    previous_revisions: list[dict[str, Any]] | None = None,
) -> OutcomeValidationReport:
    """Validate synthetic/proposed Outcome history without granting production authority."""
    dataset = {"version": schema.get("version"), "outcomes": rows}
    errors, forecast_latest, _forecast_history, evidence_index, source_ids = _preflight(schema, dataset, forecasts, evidence, sources)
    if errors:
        return OutcomeValidationReport(tuple(errors))
    revision_ids: set[str] = set()
    rows_by_outcome: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        revision_id = row.get("revision_id") if isinstance(row, dict) else None
        if not _text(revision_id):
            errors.append("Outcome revision_id must be non-empty text")
        elif revision_id in revision_ids:
            errors.append(f"duplicate Outcome revision_id {revision_id}")
        else:
            revision_ids.add(revision_id)
        _validate_row(row, schema, forecast_latest, evidence_index, source_ids, errors)
        if isinstance(row, dict) and _text(row.get("outcome_id")):
            rows_by_outcome.setdefault(row["outcome_id"], []).append(row)
    for outcome_id, history in rows_by_outcome.items():
        ordered = sorted(history, key=lambda row: row.get("revision_number", 0))
        numbers = [row.get("revision_number") for row in ordered]
        if numbers != list(range(1, len(ordered) + 1)):
            errors.append(f"{outcome_id}: revision numbers must be contiguous from 1")
        first = ordered[0]
        if first.get("revision_kind") != "ORIGINAL" or first.get("previous_revision_id") is not None:
            errors.append(f"{outcome_id}: first Outcome revision must be ORIGINAL without predecessor")
        for index, row in enumerate(ordered):
            if index == 0:
                continue
            previous = ordered[index - 1]
            if row.get("previous_revision_id") != previous.get("revision_id"):
                errors.append(f"{outcome_id}: Outcome revision predecessor link is not preserved")
            current_created = _utc(row.get("world_signals_reviewed_at_utc"))
            previous_created = _utc(previous.get("world_signals_reviewed_at_utc"))
            if current_created is None or previous_created is None or current_created <= previous_created:
                errors.append(f"{outcome_id}: Outcome review time must strictly advance")
            if _locked_payload(row) != _locked_payload(previous):
                errors.append(f"{outcome_id}: Outcome identity or resolution rule was rewritten")
            if not _valid_status_transition(previous.get("resolution_status"), row.get("resolution_status"), row.get("revision_kind")):
                errors.append(f"{outcome_id}: invalid resolution status transition")
            if row.get("revision_kind") == "ADMINISTRATIVE_CORRECTION" and _administrative_payload(row) != _administrative_payload(previous):
                errors.append(f"{outcome_id}: administrative correction changed substantive Outcome content")
            if row.get("revision_kind") == "ADMINISTRATIVE_CORRECTION" and row.get("resolution_status") != previous.get("resolution_status"):
                errors.append(f"{outcome_id}: administrative correction cannot change resolution status")
    if previous_revisions is not None:
        current = {row.get("revision_id"): row for row in rows if isinstance(row, dict)}
        for old in previous_revisions:
            if not isinstance(old, dict) or current.get(old.get("revision_id")) != old:
                errors.append("retained Outcome revision was removed or rewritten")
    return OutcomeValidationReport(tuple(errors))


def validate_outcomes(
    schema: dict[str, Any],
    dataset: dict[str, Any],
    forecasts: dict[str, Any],
    evidence: dict[str, Any],
    sources: dict[str, Any],
) -> OutcomeValidationReport:
    """Validate the intentionally empty production Outcome dataset."""
    errors: list[str] = []
    if not isinstance(dataset, dict):
        return OutcomeValidationReport(("Outcome dataset must be an object",))
    if dataset.get("population_state") != "CLOSED_NO_PRODUCTION_OUTCOMES":
        errors.append("Outcome dataset must remain in its closed population state")
    policy = schema.get("population_policy") if isinstance(schema, dict) else {}
    for key in ("production_population_allowed", "automatic_ingestion_allowed", "synthetic_production_population_allowed", "public_outcome_projection_allowed"):
        if not isinstance(policy, dict) or policy.get(key) is not False:
            errors.append(f"Outcome population policy must keep {key}=false")
    boundary = schema.get("layer_boundary") if isinstance(schema, dict) else {}
    for key in ("forecast_mutation_allowed", "resolution_rule_mutation_allowed", "observation_mutation_allowed", "canonical_mutation_allowed", "automatic_outcome_generation_allowed", "forecast_scoring_allowed", "evaluation_allowed", "model_learning_allowed", "public_outcome_projection_allowed"):
        if not isinstance(boundary, dict) or boundary.get(key) is not False:
            errors.append(f"Outcome boundary must keep {key}=false")
    public = schema.get("public_projection_policy") if isinstance(schema, dict) else {}
    if not isinstance(public, dict) or public.get("outcome_projection_allowed") is not False:
        errors.append("Outcome public projection must remain closed")
    rows = dataset.get("outcomes") if isinstance(dataset.get("outcomes"), list) else []
    if rows:
        errors.append("closed production population gate prohibits every Outcome")
    history = validate_outcome_history(schema, rows, forecasts, evidence, sources)
    return OutcomeValidationReport(tuple(errors) + history.errors)


def outcome_state_as_of(
    schema: dict[str, Any],
    rows: list[dict[str, Any]],
    forecasts: dict[str, Any],
    evidence: dict[str, Any],
    sources: dict[str, Any],
    at_utc: str,
) -> dict[str, dict[str, Any]]:
    """Return the latest Outcome revision available at a UTC timestamp."""
    report = validate_outcome_history(schema, rows, forecasts, evidence, sources)
    at = _utc(at_utc)
    if not report.ok or at is None:
        raise ValueError("invalid Outcome history/as-of timestamp: " + "; ".join(report.errors))
    result: dict[str, dict[str, Any]] = {}
    for outcome_id in {row["outcome_id"] for row in rows}:
        available = [row for row in rows if row.get("outcome_id") == outcome_id and (_utc(row.get("world_signals_reviewed_at_utc")) or at) <= at]
        if available:
            result[outcome_id] = max(available, key=lambda row: row["revision_number"])
    return result


def forecast_resolution_due_state(
    forecast: dict[str, Any],
    as_of_utc: str,
    outcome: dict[str, Any] | None = None,
    *,
    authoritative_evidence_available: bool = False,
) -> str:
    """Return deterministic resolution workflow state without resolving or scoring."""
    if outcome:
        status = outcome.get("resolution_status")
        if status in {"RESOLVED", "VOID", "UNRESOLVABLE", "DISPUTED"}:
            return status
    as_of = _utc(as_of_utc)
    resolution = forecast.get("resolution") if isinstance(forecast, dict) else None
    start = _utc(resolution.get("window_start_at_utc")) if isinstance(resolution, dict) else None
    end = _utc(resolution.get("window_end_at_utc")) if isinstance(resolution, dict) else None
    if as_of is None or start is None or end is None:
        return "INVALID_RESOLUTION_TIMING"
    if as_of < start:
        return "NOT_YET_DUE"
    if authoritative_evidence_available:
        return "DUE_AWAITING_REVIEW"
    if as_of <= end:
        return "DUE_AWAITING_AUTHORITATIVE_EVIDENCE"
    return "OVERDUE_FOR_RESOLUTION_REVIEW"


def public_outcome_projection(
    schema: dict[str, Any],
    dataset: dict[str, Any],
    forecasts: dict[str, Any],
    evidence: dict[str, Any],
    sources: dict[str, Any],
) -> dict[str, Any]:
    report = validate_outcomes(schema, dataset, forecasts, evidence, sources)
    if not report.ok:
        raise ValueError("invalid Outcome dataset: " + "; ".join(report.errors))
    return {
        "metadata": {
            "projection_type": "REVIEWED_OUTCOME_CLOSED_PROJECTION",
            "schema_version": schema.get("version"),
            "population_state": dataset.get("population_state"),
            "internal_outcome_count": 0,
            "public_outcome_count": 0,
            "public_outcome_projection_allowed": False,
            "forecast_scoring_allowed": False,
        },
        "outcomes": [],
    }
