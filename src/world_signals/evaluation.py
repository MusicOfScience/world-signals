"""Deterministic evaluation of immutable Forecast issuances against Outcomes.

Evaluation is a derived analytical layer.  Forecasts and Outcomes remain the
only sources of prospective and resolution truth; this module never writes or
mutates either source.  Production evaluation is deliberately closed while
the repository has no governed Forecast or Outcome population.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from typing import Any, Iterable


UTC = timezone.utc
SUPPORTED_METRICS = {
    "BINARY_EVENT": {"BRIER", "LOG_LOSS"},
    "CATEGORICAL": {"MULTICLASS_BRIER", "MULTICLASS_LOG_LOSS"},
    "NUMERIC_POINT": {"SIGNED_ERROR", "ABSOLUTE_ERROR", "SQUARED_ERROR"},
}
TERMINAL_OUTCOME_STATES = {"RESOLVED", "VOID", "UNRESOLVABLE", "DISPUTED"}
EXCLUDED_FORECAST_LIFECYCLES = {"VOID", "WITHDRAWN"}


@dataclass(frozen=True)
class EvaluationValidationReport:
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


def _json_object(value: Any) -> bool:
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError):
        return False
    return True


def _latest_as_of(rows: Iterable[dict[str, Any]], *, id_key: str, time_key: str, at: datetime) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if not isinstance(row, dict) or not _text(row.get(id_key)):
            continue
        created = _utc(row.get(time_key))
        if created is not None and created <= at:
            grouped[row[id_key]].append(row)
    result: dict[str, dict[str, Any]] = {}
    for row_id, candidates in grouped.items():
        result[row_id] = max(candidates, key=lambda row: (row.get("revision_number", 0), row.get(time_key, "")))
    return result


def _latest_forecasts(forecasts: dict[str, Any], at: datetime) -> dict[str, dict[str, Any]]:
    rows = forecasts.get("forecasts") if isinstance(forecasts, dict) else None
    return _latest_as_of(rows or [], id_key="issuance_id", time_key="revision_created_at_utc", at=at)


def _latest_outcomes(outcomes: dict[str, Any], at: datetime) -> dict[str, dict[str, Any]]:
    rows = outcomes.get("outcomes") if isinstance(outcomes, dict) else None
    return _latest_as_of(rows or [], id_key="outcome_id", time_key="world_signals_reviewed_at_utc", at=at)


def _slug(value: str) -> str:
    return "".join(character if character.isalnum() else "-" for character in value).strip("-")


def _metric(value: float) -> dict[str, Any]:
    if math.isinf(value):
        return {"metric_value": None, "metric_status": "INFINITE"}
    if not math.isfinite(value):
        raise ValueError("metric value must be finite or an explicitly represented infinity")
    return {"metric_value": value, "metric_status": "FINITE"}


def _log_loss(probability: float, observed: bool) -> dict[str, Any]:
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be bounded between 0 and 1")
    if (observed and probability == 0.0) or (not observed and probability == 1.0):
        return _metric(math.inf)
    return _metric(-math.log(probability if observed else 1.0 - probability))


def _score_forecast(forecast: dict[str, Any], outcome: dict[str, Any], metric_names: list[str]) -> dict[str, dict[str, Any]]:
    if outcome.get("resolution_status") != "RESOLVED":
        raise ValueError("only RESOLVED Outcomes can be scored")
    forecast_type = forecast.get("forecast_type")
    expected = SUPPORTED_METRICS.get(forecast_type, set())
    if set(metric_names) != expected:
        raise ValueError(f"metric set is incompatible with {forecast_type}")
    value = forecast.get("forecast_value") or {}
    observed = outcome.get("observed_outcome") or {}
    if forecast_type == "BINARY_EVENT":
        probability = value.get("probability")
        if not _finite(probability) or not 0.0 <= probability <= 1.0 or type(observed.get("event_occurred")) is not bool:
            raise ValueError("binary scoring requires a bounded probability and boolean Outcome")
        occurred = observed["event_occurred"]
        return {"BRIER": _metric((probability - int(occurred)) ** 2), "LOG_LOSS": _log_loss(probability, occurred)}
    if forecast_type == "CATEGORICAL":
        options = value.get("outcomes")
        if not isinstance(options, list) or not options or not _text(observed.get("outcome_id")):
            raise ValueError("categorical scoring requires outcomes and an observed category")
        probabilities = {item.get("outcome_id"): item.get("probability") for item in options if isinstance(item, dict)}
        if set(probabilities) != {item.get("outcome_id") for item in options} or any(not _finite(p) for p in probabilities.values()):
            raise ValueError("categorical scoring requires finite category probabilities")
        if abs(sum(probabilities.values()) - 1.0) > 0.000001:
            raise ValueError("categorical probabilities must sum to one")
        actual = observed["outcome_id"]
        if actual not in probabilities:
            raise ValueError("observed category is outside the Forecast category set")
        brier = sum((probability - (1.0 if category == actual else 0.0)) ** 2 for category, probability in probabilities.items())
        return {"MULTICLASS_BRIER": _metric(brier), "MULTICLASS_LOG_LOSS": _log_loss(probabilities[actual], True)}
    if forecast_type == "NUMERIC_POINT":
        estimate = value.get("estimate")
        actual = observed.get("value")
        if not _finite(estimate) or not _finite(actual) or value.get("unit") != observed.get("unit"):
            raise ValueError("numeric scoring requires finite values and matching units")
        signed = estimate - actual
        return {"SIGNED_ERROR": _metric(signed), "ABSOLUTE_ERROR": _metric(abs(signed)), "SQUARED_ERROR": _metric(signed ** 2)}
    raise ValueError(f"unsupported Forecast type {forecast_type}")


def _resolution_end(forecast: dict[str, Any]) -> datetime | None:
    resolution = forecast.get("resolution")
    return _utc(resolution.get("window_end_at_utc")) if isinstance(resolution, dict) else None


def _lead_time_seconds(forecast: dict[str, Any]) -> int | None:
    issued = _utc(forecast.get("issued_at_utc"))
    end = _resolution_end(forecast)
    if issued is None or end is None:
        return None
    return int((end - issued).total_seconds())


def _due_without_outcome(forecast: dict[str, Any], at: datetime) -> str:
    end = _resolution_end(forecast)
    return "PENDING" if end is None or at <= end else "OVERDUE"


def _record(
    forecast: dict[str, Any],
    outcome: dict[str, Any] | None,
    *,
    at: datetime,
    methodology_version: str,
    metric_names: list[str],
) -> dict[str, Any]:
    forecast_id = forecast.get("forecast_id")
    issuance_id = forecast.get("issuance_id")
    outcome_status = outcome.get("resolution_status") if outcome else None
    eligibility = _due_without_outcome(forecast, at) if outcome is None else outcome_status
    exclusion_reason: str | None = None
    metrics: dict[str, dict[str, Any]] = {}
    if forecast.get("lifecycle_state") in EXCLUDED_FORECAST_LIFECYCLES:
        eligibility = "VOID"
        exclusion_reason = "Forecast issuance is void or withdrawn under its governed lifecycle."
    elif outcome is None:
        exclusion_reason = "No Outcome revision is available as of the evaluation timestamp."
    elif outcome_status == "RESOLVED":
        eligible = issuance_id in (outcome.get("eligible_issuance_ids") or [])
        if not eligible:
            eligibility = "INELIGIBLE"
            exclusion_reason = "Outcome does not declare this issuance eligible for the target resolution."
        else:
            try:
                metrics = _score_forecast(forecast, outcome, metric_names)
                eligibility = "SCORED"
            except ValueError as exc:
                eligibility = "INVALID"
                exclusion_reason = str(exc)
    elif outcome_status == "PENDING" and at > (_resolution_end(forecast) or at):
        eligibility = "OVERDUE"
        exclusion_reason = "Outcome remains pending after the declared resolution window."
    else:
        exclusion_reason = f"Outcome status {outcome_status} is not scoreable."
    resolution_time = outcome.get("resolution_at_utc") if outcome and outcome_status in TERMINAL_OUTCOME_STATES else None
    return {
        "evaluation_id": f"EVAL-{_slug(str(issuance_id))}-{_slug(methodology_version)}-{at.strftime('%Y%m%dT%H%M%SZ')}",
        "issuance_id": issuance_id,
        "forecast_id": forecast_id,
        "outcome_id": forecast_id,
        "forecast_type": forecast.get("forecast_type"),
        "eligibility_state": eligibility,
        "exclusion_reason": exclusion_reason,
        "issue_time_utc": forecast.get("issued_at_utc"),
        "information_cutoff_at_utc": forecast.get("information_cutoff_at_utc"),
        "resolution_time_utc": resolution_time,
        "lead_time_seconds": _lead_time_seconds(forecast),
        "outcome_revision_id": outcome.get("revision_id") if outcome else None,
        "target_identifier": (forecast.get("target") or {}).get("target_identifier"),
        "unit": (forecast.get("forecast_value") or {}).get("unit"),
        "forecast_value_snapshot": forecast.get("forecast_value"),
        "metrics": metrics,
        "evaluation_as_of_utc": at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "methodology_version": methodology_version,
    }


def _validate_config(schema: dict[str, Any], config: dict[str, Any], errors: list[str]) -> None:
    if not isinstance(schema, dict) or schema.get("version") != "0.1" or schema.get("architecture_position") != "FORECAST_EVALUATION":
        errors.append("unsupported Evaluation schema")
    if not isinstance(config, dict) or config.get("version") != "0.1":
        errors.append("unsupported Evaluation configuration")
        return
    compatibility = config.get("metric_compatibility")
    expected_compatibility = {key: set(value) for key, value in SUPPORTED_METRICS.items()}
    actual_compatibility = {
        key: set(value) if isinstance(value, list) else value
        for key, value in (compatibility.items() if isinstance(compatibility, dict) else [])
    }
    if actual_compatibility != expected_compatibility:
        errors.append("Evaluation metric compatibility configuration is not the governed version")
    calibration = config.get("calibration")
    if not isinstance(calibration, dict) or calibration.get("bin_edges") != [i / 10 for i in range(11)]:
        errors.append("Evaluation calibration bins must use the governed fixed edges")
    if not isinstance(config.get("methodology"), dict) or config["methodology"].get("version") != "0.1":
        errors.append("Evaluation methodology version is required")


def validate_evaluation(
    schema: dict[str, Any],
    config: dict[str, Any],
    dataset: dict[str, Any],
    forecasts: dict[str, Any],
    outcomes: dict[str, Any],
) -> EvaluationValidationReport:
    """Validate the closed, zero-sample production Evaluation projection."""
    errors: list[str] = []
    _validate_config(schema, config, errors)
    if not isinstance(dataset, dict):
        return EvaluationValidationReport(tuple(errors + ["Evaluation dataset must be an object"]))
    if dataset.get("evaluation_state") != "NO_SAMPLE":
        errors.append("Evaluation dataset must remain in NO_SAMPLE state")
    if dataset.get("version") != schema.get("version"):
        errors.append("Evaluation dataset version must match schema")
    if not isinstance(dataset.get("evaluations"), list):
        errors.append("Evaluation dataset must contain an evaluations list")
    elif dataset["evaluations"]:
        errors.append("closed Evaluation production gate prohibits every evaluation record")
    for key in ("forecast_mutation_allowed", "outcome_mutation_allowed", "canonical_mutation_allowed", "automatic_forecast_generation_allowed", "model_learning_allowed", "public_evaluation_projection_allowed", "leaderboard_allowed", "ranking_allowed"):
        if schema.get("layer_boundary", {}).get(key) is not False:
            errors.append(f"Evaluation boundary must keep {key}=false")
    if schema.get("population_policy", {}).get("production_population_allowed") is not False:
        errors.append("Evaluation production population must remain closed")
    if schema.get("public_projection_policy", {}).get("evaluation_projection_allowed") is not False:
        errors.append("Evaluation public projection must remain closed")
    if not isinstance(forecasts, dict) or forecasts.get("forecasts") != []:
        errors.append("production Forecast population must remain empty for Evaluation")
    if not isinstance(outcomes, dict) or outcomes.get("outcomes") != []:
        errors.append("production Outcome population must remain empty for Evaluation")
    try:
        json.dumps(dataset, allow_nan=False)
    except (TypeError, ValueError):
        errors.append("Evaluation dataset must contain finite JSON values")
    return EvaluationValidationReport(tuple(errors))


def evaluate_forecasts(
    config: dict[str, Any],
    forecasts: dict[str, Any],
    outcomes: dict[str, Any],
    *,
    as_of_utc: str,
) -> dict[str, Any]:
    """Derive deterministic issuance results and transparent aggregates.

    This function accepts synthetic/proposed inputs for tests and future review
    workflows.  It has no production-write path and requires an explicit
    evaluation timestamp so later evidence cannot silently enter an earlier
    result.
    """
    at = _utc(as_of_utc)
    if at is None:
        raise ValueError("evaluation as_of_utc must be exact UTC")
    if not isinstance(config, dict) or not _text(config.get("version")):
        raise ValueError("valid Evaluation configuration is required")
    if not isinstance(forecasts, dict) or not isinstance(forecasts.get("forecasts"), list):
        raise ValueError("Forecast input must contain a forecasts list")
    if not isinstance(outcomes, dict) or not isinstance(outcomes.get("outcomes"), list):
        raise ValueError("Outcome input must contain an outcomes list")
    if not _json_object(forecasts) or not _json_object(outcomes):
        raise ValueError("Forecast and Outcome inputs must contain finite JSON values")
    for row in forecasts["forecasts"]:
        if not isinstance(row, dict) or not _text(row.get("issuance_id")) or _utc(row.get("revision_created_at_utc")) is None:
            raise ValueError("Forecast input contains a malformed issuance revision")
    for row in outcomes["outcomes"]:
        if not isinstance(row, dict) or not _text(row.get("outcome_id")) or _utc(row.get("world_signals_reviewed_at_utc")) is None:
            raise ValueError("Outcome input contains a malformed resolution revision")
    compatibility = config.get("metric_compatibility")
    if not isinstance(compatibility, dict):
        raise ValueError("Evaluation metric compatibility is required")
    latest_forecasts = _latest_forecasts(forecasts, at)
    latest_outcomes = _latest_outcomes(outcomes, at)
    outcomes_by_series = {row.get("forecast_id"): row for row in latest_outcomes.values()}
    records: list[dict[str, Any]] = []
    for forecast in sorted(latest_forecasts.values(), key=lambda row: (row.get("issued_at_utc", ""), row.get("issuance_id", ""))):
        forecast_type = forecast.get("forecast_type")
        metrics = compatibility.get(forecast_type)
        if not isinstance(metrics, list) or set(metrics) != SUPPORTED_METRICS.get(forecast_type, set()):
            raise ValueError(f"incompatible or unsupported metric configuration for {forecast_type}")
        records.append(_record(
            forecast,
            outcomes_by_series.get(forecast.get("forecast_id")),
            at=at,
            methodology_version=str(config["version"]),
            metric_names=metrics,
        ))
    summary = summarize_evaluation(records, config)
    return {
        "evaluation_as_of_utc": at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "methodology_version": config["version"],
        "records": records,
        "summary": summary,
    }


def summarize_evaluation(records: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    """Summarize without collapsing issuances into independent targets."""
    counts = {state.lower(): 0 for state in ("SCORED", "PENDING", "OVERDUE", "VOID", "UNRESOLVABLE", "DISPUTED", "INELIGIBLE", "INVALID")}
    series: set[str] = set()
    resolved_series: set[str] = set()
    pending_series: set[str] = set()
    for record in records:
        state = str(record.get("eligibility_state"))
        counts[state.lower()] = counts.get(state.lower(), 0) + 1
        if _text(record.get("forecast_id")):
            series.add(record["forecast_id"])
        if state == "SCORED" and _text(record.get("forecast_id")):
            resolved_series.add(record["forecast_id"])
        if state == "PENDING" and _text(record.get("forecast_id")):
            pending_series.add(record["forecast_id"])
    issued = len(records)
    due = issued - counts.get("pending", 0)
    resolved = counts.get("scored", 0)
    coverage = resolved / due if due else None
    metric_summaries = aggregate_evaluation(records)
    sample_state = "NO_SAMPLE" if resolved == 0 else "DESCRIPTIVE_ONLY" if resolved < int(config.get("calibration", {}).get("minimum_scored_issuances", 10)) else "EVALUABLE"
    return {
        "sample_state": sample_state,
        "counts": {"issued": issued, "distinct_series": len(series), "scored": resolved, **counts},
        "resolution_coverage": {
            "basis": "issuance_level",
            "due": due,
            "resolved": resolved,
            "coverage": coverage,
            "target_series": {
                "due": len(series) - len(pending_series),
                "resolved": len(resolved_series),
                "coverage": (len(resolved_series) / (len(series) - len(pending_series))) if len(series) - len(pending_series) else None,
            },
        },
        "issuance_level_scoring": True,
        "distinct_scored_series": len(resolved_series),
        "series_updates_are_not_independent_targets": True,
        "metric_summaries": metric_summaries,
        "calibration": calibration_summary(records, config),
        "performance_claims": "WITHHELD_UNTIL_SAMPLE_AND_REVIEW",
    }


def aggregate_evaluation(
    records: list[dict[str, Any]],
    *,
    group_by: tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    """Aggregate compatible metric observations only.

    Safe defaults keep forecast type, target and numeric unit separate.  A
    caller requesting a broader group receives an explicit error instead of a
    misleading cross-type or cross-unit number.
    """
    dimensions = group_by or ("forecast_type", "metric_family", "target_identifier", "unit")
    groups: dict[tuple[Any, ...], list[tuple[dict[str, Any], str, dict[str, Any]]]] = defaultdict(list)
    for record in records:
        if record.get("eligibility_state") != "SCORED":
            continue
        for metric_family, payload in (record.get("metrics") or {}).items():
            if not isinstance(payload, dict):
                continue
            metric_record = {**record, "metric_family": metric_family}
            groups[tuple(metric_record.get(field) for field in dimensions)].append((metric_record, metric_family, payload))
    result: list[dict[str, Any]] = []
    for key, members in groups.items():
        types = {member[0].get("forecast_type") for member in members}
        units = {member[0].get("unit") for member in members if member[0].get("forecast_type") == "NUMERIC_POINT"}
        if len(types) > 1:
            raise ValueError("incompatible Forecast types cannot share an aggregate")
        if len(units) > 1:
            raise ValueError("incompatible numeric units cannot share an aggregate")
        finite = [payload["metric_value"] for _, _, payload in members if payload.get("metric_status") == "FINITE"]
        infinite_count = sum(payload.get("metric_status") == "INFINITE" for _, _, payload in members)
        result.append({
            "group": {field: value for field, value in zip(dimensions, key)},
            "issuance_count": len(members),
            "finite_count": len(finite),
            "infinite_count": infinite_count,
            "mean_metric": sum(finite) / len(finite) if finite else None,
            "metric_status": "INFINITE_PRESENT" if infinite_count else "FINITE",
        })
    return sorted(result, key=lambda row: json.dumps(row["group"], sort_keys=True))


def calibration_summary(records: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    binary = [row for row in records if row.get("eligibility_state") == "SCORED" and row.get("forecast_type") == "BINARY_EVENT"]
    minimum = int(config.get("calibration", {}).get("minimum_scored_issuances", 10))
    distinct_minimum = int(config.get("calibration", {}).get("minimum_distinct_series", 5))
    distinct = {row.get("forecast_id") for row in binary}
    if not binary:
        state = "NO_SAMPLE"
    elif len(binary) < minimum or len(distinct) < distinct_minimum:
        state = "INSUFFICIENT_SAMPLE"
    else:
        state = "EVALUABLE"
    return {
        "state": state,
        "bin_edges": config.get("calibration", {}).get("bin_edges"),
        "scored_issuance_count": len(binary),
        "distinct_series_count": len(distinct),
        "bins": [],
        "claim": "NONE_UNTIL_EVALUABLE_SAMPLE" if state != "EVALUABLE" else "DESCRIPTIVE_ONLY_PENDING_REVIEW",
    }


def public_evaluation_projection(schema: dict[str, Any], config: dict[str, Any], dataset: dict[str, Any], forecasts: dict[str, Any], outcomes: dict[str, Any]) -> dict[str, Any]:
    report = validate_evaluation(schema, config, dataset, forecasts, outcomes)
    if not report.ok:
        raise ValueError("invalid Evaluation dataset: " + "; ".join(report.errors))
    return {
        "metadata": {
            "projection_type": "DERIVED_FORECAST_EVALUATION_CLOSED_PROJECTION",
            "schema_version": schema.get("version"),
            "evaluation_state": "NO_SAMPLE",
            "internal_evaluation_count": 0,
            "public_evaluation_count": 0,
            "public_evaluation_projection_allowed": False,
            "performance_claims": "WITHHELD_NO_PRODUCTION_SAMPLE",
        },
        "evaluations": [],
    }
