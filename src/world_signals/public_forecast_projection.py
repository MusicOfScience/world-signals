"""Allowlisted public projection for the reviewed monetary-policy pilot.

The governed Forecast dataset remains private and its own publication policy
remains closed.  This module is a separate, deliberately narrow publication
contract.  It copies only fields approved for the public Outlook and fails
closed when an allowlisted issuance is not an accepted, open, non-political
Forecast.
"""

from __future__ import annotations

from copy import deepcopy
from math import isfinite
from typing import Any


PUBLIC_FORECAST_ALLOWLIST_VERSION = "world-signals-public-forecast-pilot-v1"
PUBLIC_FORECAST_ALLOWLIST = frozenset(
    {
        "WS-FP-RBA-20261103",
        "WS-FP-BOC-20261028",
        "WS-FP-ECB-20261029",
        "WS-FP-FED-20261028",
    }
)

_SOURCE_LABELS = {
    "WS-FP-RBA-20261103": "Official RBA decision release",
    "WS-FP-BOC-20261028": "Official Bank of Canada decision release",
    "WS-FP-ECB-20261029": "Official ECB decision release",
    "WS-FP-FED-20261028": "Official FOMC statement",
}
_INSTITUTIONS = {
    "WS-FP-RBA-20261103": "Reserve Bank of Australia",
    "WS-FP-BOC-20261028": "Bank of Canada",
    "WS-FP-ECB-20261029": "European Central Bank",
    "WS-FP-FED-20261028": "Federal Reserve",
}
_POLITICAL_TERMS = (
    "election",
    "electoral",
    "politic",
    "president",
    "parliament",
    "legislative",
    "legislature",
    "vote",
    "party",
    "poll",
)


class PublicForecastProjectionError(ValueError):
    """Raised when a public Forecast allowlist cannot be satisfied safely."""


def _text(value: Any) -> str:
    return str(value or "")


def _looks_political(row: dict[str, Any]) -> bool:
    target = row.get("target") if isinstance(row.get("target"), dict) else {}
    searchable = " ".join(
        _text(value).lower()
        for value in (
            row.get("forecast_id"),
            row.get("question"),
            target.get("target_identifier"),
            target.get("target_kind"),
            target.get("definition"),
        )
    )
    return any(term in searchable for term in _POLITICAL_TERMS)


def _required(row: dict[str, Any], field: str) -> Any:
    value = row.get(field)
    if value in (None, ""):
        raise PublicForecastProjectionError(
            f"public Forecast {row.get('forecast_id', '<unknown>')} missing {field}"
        )
    return value


def _numeric_value(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("forecast_value")
    if not isinstance(value, dict):
        raise PublicForecastProjectionError("numeric public Forecast value must be an object")
    estimate = value.get("estimate")
    unit = value.get("unit")
    if not isinstance(estimate, (int, float)) or isinstance(estimate, bool) or not isfinite(estimate):
        raise PublicForecastProjectionError("numeric public Forecast estimate must be finite")
    if not isinstance(unit, str) or not unit.strip():
        raise PublicForecastProjectionError("numeric public Forecast unit is required")
    return {"estimate": estimate, "unit": unit}


def _categorical_value(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("forecast_value")
    if not isinstance(value, dict):
        raise PublicForecastProjectionError("categorical public Forecast value must be an object")
    if value.get("mutually_exclusive") is not True or value.get("collectively_exhaustive") is not True:
        raise PublicForecastProjectionError("categorical public Forecast outcomes must be an exhaustive partition")
    outcomes = value.get("outcomes") if isinstance(value, dict) else None
    if not isinstance(outcomes, list) or len(outcomes) < 2:
        raise PublicForecastProjectionError("categorical public Forecast requires outcomes")
    public_outcomes = []
    total = 0.0
    for outcome in outcomes:
        if not isinstance(outcome, dict):
            raise PublicForecastProjectionError("categorical public Forecast outcome must be an object")
        probability = outcome.get("probability")
        if not isinstance(probability, (int, float)) or isinstance(probability, bool):
            raise PublicForecastProjectionError("categorical public Forecast probability must be numeric")
        if not 0 <= probability <= 1:
            raise PublicForecastProjectionError("categorical public Forecast probability must be bounded")
        label = _required(outcome, "label")
        outcome_id = _required(outcome, "outcome_id")
        total += probability
        public_outcomes.append(
            {
                "outcome_id": outcome_id,
                "label": label,
                "probability": probability,
                "definition": _required(outcome, "definition"),
            }
        )
    if abs(total - 1.0) > 0.000001:
        raise PublicForecastProjectionError("categorical public Forecast probabilities must sum to one")
    return {
        "outcomes": public_outcomes,
        "mutually_exclusive": value.get("mutually_exclusive") is True,
        "collectively_exhaustive": value.get("collectively_exhaustive") is True,
    }


def _validate_public_candidate(row: dict[str, Any]) -> None:
    forecast_id = _required(row, "forecast_id")
    if forecast_id not in PUBLIC_FORECAST_ALLOWLIST:
        raise PublicForecastProjectionError(f"Forecast {forecast_id} is not on the public allowlist")
    if row.get("review_state") != "ACCEPTED":
        raise PublicForecastProjectionError(f"Forecast {forecast_id} is not ACCEPTED")
    if row.get("lifecycle_state") != "OPEN":
        raise PublicForecastProjectionError(f"Forecast {forecast_id} is not in an eligible lifecycle state")
    if _looks_political(row):
        raise PublicForecastProjectionError(
            f"Forecast {forecast_id} is political/electoral and is not authorised for public projection"
        )
    for field in ("issuance_id", "revision_id", "question", "issued_at_utc", "information_cutoff_at_utc"):
        _required(row, field)
    target = row.get("target")
    if not isinstance(target, dict) or not target.get("definition"):
        raise PublicForecastProjectionError(f"Forecast {forecast_id} has no public target definition")
    _required(row, "rationale")
    resolution = row.get("resolution")
    if not isinstance(resolution, dict):
        raise PublicForecastProjectionError(f"Forecast {forecast_id} has no resolution contract")
    for field in ("window_start_at_utc", "window_end_at_utc", "resolution_rule"):
        _required(resolution, field)
    if row.get("forecast_type") == "NUMERIC_POINT":
        _numeric_value(row)
    elif row.get("forecast_type") == "CATEGORICAL":
        _categorical_value(row)
    else:
        raise PublicForecastProjectionError(
            f"Forecast {forecast_id} type {row.get('forecast_type')} is not public-pilot eligible"
        )


def _public_row(row: dict[str, Any]) -> dict[str, Any]:
    forecast_id = row["forecast_id"]
    resolution = row["resolution"]
    value = (
        _numeric_value(row)
        if row["forecast_type"] == "NUMERIC_POINT"
        else _categorical_value(row)
    )
    return {
        "forecast_id": forecast_id,
        "issuance_id": row["issuance_id"],
        "revision_id": row["revision_id"],
        "institution": _INSTITUTIONS[forecast_id],
        "target_label": row["target"]["definition"],
        "question": row["question"],
        "forecast_type": row["forecast_type"],
        "forecast_value": value,
        "issued_at_utc": row["issued_at_utc"],
        "information_cutoff_at_utc": row["information_cutoff_at_utc"],
        "resolution": {
            "window_start_at_utc": resolution["window_start_at_utc"],
            "window_end_at_utc": resolution["window_end_at_utc"],
            "resolution_rule": resolution["resolution_rule"],
            "source_label": _SOURCE_LABELS[forecast_id],
        },
        "lifecycle_state": row["lifecycle_state"],
        "review_state": row["review_state"],
        "resolution_status": "UNRESOLVED",
        "public_rationale": _required(row, "rationale"),
    }


def build_public_forecast_projection(dataset: dict[str, Any]) -> dict[str, Any]:
    """Build the deterministic public Outlook projection from governed rows."""
    rows = dataset.get("forecasts") if isinstance(dataset, dict) else None
    if not isinstance(rows, list):
        raise PublicForecastProjectionError("Forecast dataset must contain a forecasts list")
    allowlisted_rows = [
        row for row in rows
        if isinstance(row, dict) and row.get("forecast_id") in PUBLIC_FORECAST_ALLOWLIST
    ]
    allowlisted_ids = [row["forecast_id"] for row in allowlisted_rows]
    if len(allowlisted_ids) != len(set(allowlisted_ids)):
        raise PublicForecastProjectionError("public Forecast allowlist contains duplicate issuance rows")
    by_id = {row.get("forecast_id"): row for row in rows if isinstance(row, dict)}
    missing = sorted(PUBLIC_FORECAST_ALLOWLIST - set(by_id))
    if missing:
        raise PublicForecastProjectionError("public Forecast allowlist is missing: " + ", ".join(missing))
    projected = []
    for forecast_id in sorted(PUBLIC_FORECAST_ALLOWLIST):
        row = by_id[forecast_id]
        _validate_public_candidate(row)
        projected.append(_public_row(row))
    projected.sort(key=lambda row: (row["resolution"]["window_start_at_utc"], row["forecast_id"]))
    return {
        "metadata": {
            "projection_type": "PUBLIC_FORECAST_PILOT_ALLOWLIST",
            "allowlist_version": PUBLIC_FORECAST_ALLOWLIST_VERSION,
            "population_state": dataset.get("population_state"),
            "internal_forecast_count": len(rows),
            "public_forecast_count": len(projected),
            "public_forecast_projection_allowed": True,
            "evaluation_state": "NO_SAMPLE",
            "outcome_projection": "NONE_AVAILABLE",
            "political_electoral_forecasts": "FAIL_CLOSED_UNAUTHORISED",
        },
        "forecasts": projected,
    }


def validate_public_forecast_projection(projection: dict[str, Any]) -> list[str]:
    """Validate the already-sanitised public contract without governed writes."""
    errors: list[str] = []
    metadata = projection.get("metadata") if isinstance(projection, dict) else None
    rows = projection.get("forecasts") if isinstance(projection, dict) else None
    if not isinstance(metadata, dict) or metadata.get("projection_type") != "PUBLIC_FORECAST_PILOT_ALLOWLIST":
        errors.append("invalid public Forecast projection type")
    if not isinstance(rows, list) or {row.get("forecast_id") for row in rows} != set(PUBLIC_FORECAST_ALLOWLIST):
        errors.append("public Forecast projection does not contain exactly the allowlist")
    for row in rows or []:
        if not isinstance(row, dict):
            errors.append("public Forecast row must be an object")
            continue
        if "forecast_provenance" in row or "review_provenance" in row or "supporting_evidence_refs" in row:
            errors.append(f"{row.get('forecast_id')}: private Forecast metadata leaked")
        if row.get("resolution_status") != "UNRESOLVED":
            errors.append(f"{row.get('forecast_id')}: unresolved pilot must remain unresolved")
    return errors


def public_forecast_projection_copy(projection: dict[str, Any]) -> dict[str, Any]:
    """Return a defensive copy for callers that render the public contract."""
    return deepcopy(projection)
