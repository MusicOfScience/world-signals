"""Read-only World State Synthesis Engine v1 boundary.

This module is an orchestrator, not a synthesis engine.  It validates the
existing governed layers, delegates history selection to their as-of helpers,
and returns an ephemeral proposal envelope.  When an explicit production
history query is supplied, it also attaches the separate read-only admitted
World State view.  It has no production write path and no public projection.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .analysis import validate_analysis
from .analysis_revision import validate_analysis_revisions
from .evaluation import validate_evaluation
from .forecasts import forecast_state_as_of, validate_forecasts
from .io import load_json
from .live_analysis_bridge import validate_live_analysis_bridge
from .live_intelligence import validate_live_intelligence
from .outcomes import outcome_state_as_of, validate_outcomes
from .relationships import (
    relationship_graph_edges_as_of,
    relationship_state_as_of,
    validate_relationships,
)
from .risks import risk_state_as_of, validate_risk_states
from .scenarios import scenario_state_as_of, validate_scenarios
from .signal_admission import validate_signal_admission_transaction
from .signals import signal_state_as_of, validate_signals
from .validation import validate_registry


ROOT = Path(__file__).resolve().parents[2]
EXACT_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
CONTRACT_VERSION = "0.1"
INPUT_POLICY = "ACCEPTED_REVIEWED_HEADS_ONLY"
WORLD_STATE_DIMENSIONS = {
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
REVIEWED_LIVE_STATES = {
    "PRIMARY_CONFIRMED",
    "MULTI_SOURCE_CORROBORATED",
    "CONFLICTING_REPORTS",
    "CORRECTED",
    "RETRACTED",
}

DATA_PATHS = {
    "canonical_schema": "data/canonical/schema.json",
    "canonical": "data/canonical/registry.json",
    "sources": "data/sources/registry.json",
    "live_schema": "data/live_intelligence/schema.json",
    "live_evidence": "data/live_intelligence/evidence_registry.json",
    "live_observations": "data/live_intelligence/observations.json",
    "analysis_schema": "data/analysis/schema.json",
    "analysis_evidence": "data/analysis/evidence_registry.json",
    "analysis_reviews": "data/analysis/event_reviews.json",
    "signals_schema": "data/signals/schema.json",
    "signals": "data/signals/signals.json",
    "signal_admission": "data/signals/signal_admission_transaction_v1.json",
    "relationships_schema": "data/relationships/schema.json",
    "relationships": "data/relationships/relationships.json",
    "risks_schema": "data/risks/schema.json",
    "risks": "data/risks/states.json",
    "scenarios_schema": "data/scenarios/schema.json",
    "scenarios": "data/scenarios/scenarios.json",
    "forecasts_schema": "data/forecasts/schema.json",
    "forecasts": "data/forecasts/forecasts.json",
    "forecast_admission": "data/forecasts/admission_transaction.json",
    "outcomes_schema": "data/outcomes/schema.json",
    "outcomes": "data/outcomes/outcomes.json",
    "evaluation_schema": "data/evaluation/schema.json",
    "evaluation_config": "data/evaluation/config.json",
    "evaluation": "data/evaluation/evaluation.json",
}


class WorldStateReadError(ValueError):
    """Raised when a read request or governed input cannot be read safely."""


def _compact_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def object_sha256(value: Any) -> str:
    """Hash the exact deterministic JSON object represented in a manifest."""
    return hashlib.sha256(_compact_json(value).encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_exact_utc(value: Any, field: str = "as_of_utc") -> datetime:
    if not isinstance(value, str) or not EXACT_UTC_RE.fullmatch(value):
        raise WorldStateReadError(f"{field} must be an exact UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise WorldStateReadError(f"{field} is not a valid UTC timestamp") from exc
    if parsed.tzinfo != timezone.utc:
        raise WorldStateReadError(f"{field} must be UTC")
    return parsed


def validate_read_request(request: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize one explicit World State read request."""
    if not isinstance(request, dict):
        raise WorldStateReadError("World State read request must be an object")
    required = {"contract_version", "as_of_utc", "scope", "include_negative_evidence", "input_policy"}
    if set(request) != required:
        missing = sorted(required - set(request))
        extra = sorted(set(request) - required)
        raise WorldStateReadError(f"request keys mismatch; missing={missing} extra={extra}")
    if request["contract_version"] != CONTRACT_VERSION:
        raise WorldStateReadError("unsupported World State read contract version")
    as_of = _parse_exact_utc(request["as_of_utc"])
    if request["input_policy"] != INPUT_POLICY:
        raise WorldStateReadError("input_policy must be ACCEPTED_REVIEWED_HEADS_ONLY")
    if type(request["include_negative_evidence"]) is not bool:
        raise WorldStateReadError("include_negative_evidence must be boolean")

    scope = request["scope"]
    if not isinstance(scope, dict):
        raise WorldStateReadError("scope must be an object")
    allowed_scope_keys = {"jurisdictions", "dimensions", "actor_ids"}
    if set(scope) - allowed_scope_keys:
        raise WorldStateReadError("scope contains unsupported keys")
    jurisdictions = scope.get("jurisdictions")
    dimensions = scope.get("dimensions")
    actor_ids = scope.get("actor_ids")
    if not isinstance(jurisdictions, list) or not jurisdictions or any(not isinstance(x, str) or not x.strip() for x in jurisdictions):
        raise WorldStateReadError("scope.jurisdictions must be a non-empty list of strings")
    if not isinstance(dimensions, list) or not dimensions or any(not isinstance(x, str) or not x.strip() for x in dimensions):
        raise WorldStateReadError("scope.dimensions must be a non-empty list of strings")
    unknown_dimensions = sorted(set(dimensions) - WORLD_STATE_DIMENSIONS)
    if unknown_dimensions:
        raise WorldStateReadError(f"unsupported dimension vocabulary: {unknown_dimensions}")
    if actor_ids is not None and (not isinstance(actor_ids, list) or any(not isinstance(x, str) or not x.strip() for x in actor_ids)):
        raise WorldStateReadError("scope.actor_ids must be a list of strings when supplied")
    if len(set(jurisdictions)) != len(jurisdictions) or len(set(dimensions)) != len(dimensions):
        raise WorldStateReadError("scope lists must not contain duplicates")

    return {
        "contract_version": CONTRACT_VERSION,
        "as_of_utc": request["as_of_utc"],
        "scope": {
            "jurisdictions": list(jurisdictions),
            "dimensions": list(dimensions),
            "actor_ids": list(actor_ids) if actor_ids is not None else None,
        },
        "include_negative_evidence": request["include_negative_evidence"],
        "input_policy": INPUT_POLICY,
        "_as_of": as_of,
    }


def _load_inputs() -> dict[str, Any]:
    return {key: load_json(ROOT / relative) for key, relative in DATA_PATHS.items()}


def _input_file_hashes() -> dict[str, str]:
    return {
        key: _file_sha256(ROOT / relative)
        for key, relative in sorted(DATA_PATHS.items())
    }


def _report_errors(label: str, report: Any) -> list[str]:
    if getattr(report, "ok", False):
        return []
    return [f"{label}: {error}" for error in getattr(report, "errors", ())]


def validate_governed_inputs(inputs: dict[str, Any]) -> None:
    """Run the existing layer validators before selecting any upstream state."""
    errors: list[str] = []
    errors.extend(_report_errors("Canonical", validate_registry(inputs["canonical"], inputs["sources"])))
    errors.extend(_report_errors("Live Intelligence", validate_live_intelligence(
        inputs["live_schema"], inputs["live_evidence"], inputs["live_observations"], inputs["canonical"],
    )))
    errors.extend(_report_errors("Analysis", validate_analysis(
        inputs["analysis_schema"], inputs["analysis_evidence"], inputs["analysis_reviews"], inputs["canonical"],
    )))
    errors.extend(_report_errors("Analysis revisions", validate_analysis_revisions(
        inputs["analysis_schema"], inputs["analysis_reviews"],
    )))
    errors.extend(_report_errors("Live → Analysis bridge", validate_live_analysis_bridge(
        inputs["analysis_schema"], inputs["analysis_reviews"], inputs["live_observations"],
    )))
    errors.extend(_report_errors("Signal admission", validate_signal_admission_transaction(
        inputs["signals_schema"], inputs["signals"], inputs["live_observations"],
        inputs["live_evidence"], inputs["signal_admission"],
    )))
    errors.extend(_report_errors("Signals", validate_signals(
        inputs["signals_schema"], inputs["signals"], inputs["live_observations"],
        inputs["live_evidence"], inputs["signal_admission"],
    )))
    errors.extend(_report_errors("Relationships", validate_relationships(
        inputs["relationships_schema"], inputs["relationships"], inputs["signals"],
        inputs["live_observations"], inputs["live_evidence"], inputs["canonical"],
    )))
    errors.extend(_report_errors("Risks / Regimes", validate_risk_states(
        inputs["risks_schema"], inputs["risks"], inputs["signals"], inputs["relationships"],
        inputs["live_observations"], inputs["live_evidence"], inputs["canonical"],
    )))
    errors.extend(_report_errors("Scenarios", validate_scenarios(
        inputs["scenarios_schema"], inputs["scenarios"], inputs["risks"], inputs["signals"],
        inputs["relationships"], inputs["live_observations"], inputs["live_evidence"], inputs["canonical"],
    )))
    errors.extend(_report_errors("Forecasts", validate_forecasts(
        inputs["forecasts_schema"], inputs["forecasts"], inputs["scenarios"], inputs["risks"],
        inputs["signals"], inputs["relationships"], inputs["live_observations"], inputs["live_evidence"],
        inputs["canonical"], inputs["sources"], inputs["forecast_admission"],
    )))
    errors.extend(_report_errors("Outcomes", validate_outcomes(
        inputs["outcomes_schema"], inputs["outcomes"], inputs["forecasts"], inputs["live_evidence"], inputs["sources"],
    )))
    errors.extend(_report_errors("Evaluation", validate_evaluation(
        inputs["evaluation_schema"], inputs["evaluation_config"], inputs["evaluation"],
        inputs["forecasts"], inputs["outcomes"],
    )))
    if errors:
        raise WorldStateReadError("governed input validation failed: " + "; ".join(errors))


def _in_scope(row: dict[str, Any], jurisdictions: list[str], *, canonical: bool = False) -> bool:
    if "*" in jurisdictions:
        return True
    values = row.get("jurisdiction") if canonical else row.get("jurisdictions")
    if isinstance(values, str):
        values = [values]
    return bool(set(values or ()) & set(jurisdictions))


def _known_at(value: Any, as_of: datetime) -> bool:
    try:
        return _parse_exact_utc(value, "known-at value") <= as_of
    except WorldStateReadError:
        return False


def _manifest_key(layer: str, object_id: str, revision_id: Any = None) -> str:
    return f"{layer}:{object_id}:{revision_id or '-'}"


class _Manifest:
    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}

    def add(self, layer: str, object_id: str, obj: dict[str, Any], revision_id: Any = None) -> str:
        key = _manifest_key(layer, object_id, revision_id)
        entry = {
            "layer": layer,
            "object_id": object_id,
            "revision_id": revision_id,
            "object_sha256": object_sha256(obj),
            "object": deepcopy(obj),
        }
        existing = self.rows.get(key)
        if existing is not None and existing != entry:
            raise WorldStateReadError(f"conflicting source objects for manifest key {key}")
        self.rows[key] = entry
        return key

    def as_list(self) -> list[dict[str, Any]]:
        return [self.rows[key] for key in sorted(self.rows)]


def _refs_in(value: Any) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            if key.endswith("_refs") and isinstance(nested, list):
                refs.update(item for item in nested if isinstance(item, str))
            else:
                refs.update(_refs_in(nested))
    elif isinstance(value, list):
        for nested in value:
            refs.update(_refs_in(nested))
    return refs


def _select_live(inputs: dict[str, Any], request: dict[str, Any], manifest: _Manifest) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    as_of = request["_as_of"]
    jurisdictions = request["scope"]["jurisdictions"]
    observations = [
        row for row in inputs["live_observations"].get("observations", [])
        if row.get("verification_state") in REVIEWED_LIVE_STATES
        and _known_at(row.get("observed_at_utc"), as_of)
        and _in_scope(row, jurisdictions)
    ]
    observations.sort(key=lambda row: row["observation_id"])
    evidence_by_id = {row["evidence_id"]: row for row in inputs["live_evidence"].get("evidence", [])}
    evidence_ids = sorted({ref for row in observations for ref in row.get("evidence_refs", [])})
    missing = [ref for ref in evidence_ids if ref not in evidence_by_id]
    if missing:
        raise WorldStateReadError(f"eligible Live observation references unavailable evidence: {missing}")
    evidence = [evidence_by_id[ref] for ref in evidence_ids]
    for row in observations:
        manifest.add("LIVE_INTELLIGENCE", row["observation_id"], row)
    for row in evidence:
        manifest.add("LIVE_INTELLIGENCE", row["evidence_id"], row)
    return observations, evidence


def _select_analysis(inputs: dict[str, Any], request: dict[str, Any], manifest: _Manifest) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    as_of = request["_as_of"]
    jurisdictions = request["scope"]["jurisdictions"]
    canonical_by_id = {row.get("occurrence_id"): row for row in inputs["canonical"].get("records", [])}
    reviews = []
    for row in inputs["analysis_reviews"].get("reviews", []):
        if row.get("review_state") not in {"REVIEWED_SAMPLE", "REVIEWED"}:
            continue
        if not _known_at(row.get("analysis_as_of_utc"), as_of):
            continue
        canonical = canonical_by_id.get(row.get("canonical_occurrence_id"), {})
        if not _in_scope(canonical, jurisdictions, canonical=True):
            continue
        reviews.append(row)
    reviews.sort(key=lambda row: row["analysis_id"])
    evidence_by_id = {row["evidence_id"]: row for row in inputs["analysis_evidence"].get("evidence", [])}
    evidence_ids = sorted({ref for row in reviews for ref in _refs_in(row)})
    missing = [ref for ref in evidence_ids if ref not in evidence_by_id]
    if missing:
        raise WorldStateReadError(f"eligible Analysis references unavailable evidence: {missing}")
    evidence = [evidence_by_id[ref] for ref in evidence_ids]
    for row in reviews:
        manifest.add("ANALYSIS", row["analysis_id"], row)
    for row in evidence:
        manifest.add("ANALYSIS", row["evidence_id"], row)
    return reviews, evidence


def _select_revisions(inputs: dict[str, Any], request: dict[str, Any], manifest: _Manifest, live_observations: list[dict[str, Any]], live_evidence: list[dict[str, Any]]) -> dict[str, Any]:
    at = request["as_of_utc"]
    signal_states = signal_state_as_of(
        inputs["signals_schema"], inputs["signals"].get("signals", []), inputs["live_observations"], inputs["live_evidence"], at,
    )
    signal_rows = {row["revision_id"]: row for row in inputs["signals"].get("signals", [])}
    selected_signals = []
    for state in sorted(signal_states.values(), key=lambda row: row["revision_id"]):
        row = signal_rows[state["revision_id"]]
        if any(not _known_at(next((obs.get("observed_at_utc") for obs in live_observations if obs.get("observation_id") == oid), None), request["_as_of"]) for oid in row.get("observation_ids", [])):
            raise WorldStateReadError(f"Signal {row['revision_id']} references evidence after the read cutoff")
        selected_signals.append(row)
        manifest.add("SIGNALS", row["signal_id"], row, row["revision_id"])

    relationship_states = relationship_state_as_of(
        inputs["relationships_schema"], inputs["relationships"].get("relationships", []), inputs["signals"],
        inputs["live_observations"], inputs["live_evidence"], inputs["canonical"], at,
    )
    relationship_rows = {row["revision_id"]: row for row in inputs["relationships"].get("relationships", [])}
    selected_relationships = []
    for state in sorted(relationship_states.values(), key=lambda row: row["revision_id"]):
        row = relationship_rows[state["revision_id"]]
        selected_relationships.append(row)
        manifest.add("RELATIONSHIPS", row["relationship_id"], row, row["revision_id"])
    relationship_edges = relationship_graph_edges_as_of(
        inputs["relationships_schema"], inputs["relationships"].get("relationships", []), inputs["signals"],
        inputs["live_observations"], inputs["live_evidence"], inputs["canonical"], at,
    )

    risk_states = risk_state_as_of(
        inputs["risks_schema"], inputs["risks"].get("states", []), inputs["signals"], inputs["relationships"],
        inputs["live_observations"], inputs["live_evidence"], inputs["canonical"], at,
    )
    risk_rows = {row["revision_id"]: row for row in inputs["risks"].get("states", [])}
    selected_risks = []
    for state in sorted(risk_states.values(), key=lambda row: row["revision_id"]):
        row = risk_rows[state["revision_id"]]
        selected_risks.append(row)
        manifest.add("RISKS_REGIMES", row["state_id"], row, row["revision_id"])

    scenario_states = scenario_state_as_of(
        inputs["scenarios_schema"], inputs["scenarios"].get("scenario_sets", []), inputs["scenarios"].get("scenarios", []),
        inputs["risks"], inputs["signals"], inputs["relationships"], inputs["live_observations"], inputs["live_evidence"], inputs["canonical"], at,
    )
    scenario_rows = {row["revision_id"]: row for row in inputs["scenarios"].get("scenarios", [])}
    selected_scenarios = []
    for state in sorted(scenario_states.values(), key=lambda row: row["revision_id"]):
        row = scenario_rows[state["revision_id"]]
        selected_scenarios.append(row)
        manifest.add("SCENARIOS", row["scenario_id"], row, row["revision_id"])

    forecast_states = forecast_state_as_of(
        inputs["forecasts_schema"], inputs["forecasts"].get("forecasts", []), inputs["scenarios"], inputs["risks"],
        inputs["signals"], inputs["relationships"], inputs["live_observations"], inputs["live_evidence"],
        inputs["canonical"], inputs["sources"], at,
    )
    forecast_rows = {row["revision_id"]: row for row in inputs["forecasts"].get("forecasts", [])}
    selected_forecasts = []
    for state in sorted(forecast_states.values(), key=lambda row: row["issuance_id"]):
        row = forecast_rows[state["revision_id"]]
        if _parse_exact_utc(row["issued_at_utc"], "Forecast issued_at_utc") > request["_as_of"]:
            continue
        selected_forecasts.append(row)
        manifest.add("FORECASTS", row["issuance_id"], row, row["revision_id"])

    outcome_states = outcome_state_as_of(
        inputs["outcomes_schema"], inputs["outcomes"].get("outcomes", []), inputs["forecasts"], inputs["live_evidence"], inputs["sources"], at,
    )
    outcome_rows = {row["revision_id"]: row for row in inputs["outcomes"].get("outcomes", [])}
    selected_outcomes = []
    for state in sorted(outcome_states.values(), key=lambda row: row["outcome_id"]):
        row = outcome_rows[state["revision_id"]]
        selected_outcomes.append(row)
        manifest.add("OUTCOMES", row["outcome_id"], row, row["revision_id"])

    return {
        "signals": selected_signals,
        "relationships": selected_relationships,
        "relationship_edges": relationship_edges,
        "risks": selected_risks,
        "scenarios": selected_scenarios,
        "forecasts": selected_forecasts,
        "outcomes": selected_outcomes,
    }


def _semantic_payload(proposal: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in proposal.items()
        if key not in {"generated_at_utc", "proposal_id", "semantic_fingerprint"}
    }


def semantic_fingerprint(proposal: dict[str, Any]) -> str:
    return object_sha256(_semantic_payload(proposal))


def validate_proposal_manifest(proposal: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    manifest = proposal.get("source_manifest")
    if not isinstance(manifest, list):
        return ["source_manifest must be a list"]
    keys: set[str] = set()
    for entry in manifest:
        key = _manifest_key(entry.get("layer", ""), entry.get("object_id", ""), entry.get("revision_id"))
        if key in keys:
            errors.append(f"duplicate source manifest key {key}")
        keys.add(key)
        if entry.get("object_sha256") != object_sha256(entry.get("object")):
            errors.append(f"source manifest hash mismatch for {key}")
    expected = object_sha256(manifest)
    if proposal.get("source_manifest_sha256") != expected:
        errors.append("source manifest aggregate hash mismatch")
    if proposal.get("semantic_fingerprint") != semantic_fingerprint(proposal):
        errors.append("semantic proposal fingerprint mismatch")
    return errors


def read_world_state(
    request: dict[str, Any],
    *,
    generated_at_utc: str | None = None,
    production_query: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one deterministic, ephemeral World State proposal.

    The function reads governed inputs but never writes them.  ``generated_at_utc``
    is optional execution metadata and is excluded from the semantic fingerprint.
    """
    normalized = validate_read_request(request)
    if generated_at_utc is not None:
        _parse_exact_utc(generated_at_utc, "generated_at_utc")
    before = _input_file_hashes()
    inputs = _load_inputs()
    validate_governed_inputs(inputs)
    manifest = _Manifest()
    as_of = normalized["_as_of"]
    jurisdictions = normalized["scope"]["jurisdictions"]

    canonical_context = [
        row for row in inputs["canonical"].get("records", [])
        if _in_scope(row, jurisdictions, canonical=True)
    ]
    canonical_context.sort(key=lambda row: row["occurrence_id"])
    canonical_refs = [
        {"object_id": row["occurrence_id"], "revision_id": None, "manifest_key": manifest.add("CANONICAL", row["occurrence_id"], row)}
        for row in canonical_context
    ]
    live_observations, live_evidence = _select_live(inputs, normalized, manifest)
    analysis_reviews, analysis_evidence = _select_analysis(inputs, normalized, manifest)
    revisions = _select_revisions(inputs, normalized, manifest, live_observations, live_evidence)

    for row in inputs["evaluation"].get("evaluations", []):
        manifest.add("EVALUATION", row.get("evaluation_id", row.get("forecast_id", "evaluation")), row, row.get("evaluation_revision_id"))

    limitations = [
        {
            "code": "CANONICAL_HISTORICAL_AS_OF_UNSUPPORTED",
            "detail": "Canonical records are current context only; no general historical Canonical selector exists.",
        },
        {
            "code": "WORLD_STATE_ASSESSMENT_NOT_SYNTHESISED",
            "detail": "This adapter does not infer dimensions, actors, implementation claims, hypotheses, anomalies, negative evidence, or transmission edges.",
        },
        {
            "code": "ACTOR_REGISTRY_UNAVAILABLE",
            "detail": "No durable actor identity is created; proposal-local actors are emitted only by a future reviewed synthesis operation.",
        },
        {
            "code": "MARKET_FEED_NOT_INTRODUCED",
            "detail": "No live market feed is read; admissible market measurements remain within existing Analysis inputs.",
        },
    ]
    for dimension in normalized["scope"]["dimensions"]:
        limitations.append({
            "code": "DIMENSION_ASSESSMENT_NOT_SUPPORTED",
            "dimension": dimension,
            "detail": "No governed reviewed World State dimension assessment is selected by this read-only adapter.",
        })
    if normalized["include_negative_evidence"]:
        limitations.append({
            "code": "NO_EXPLICIT_GOVERNED_NEGATIVE_EVIDENCE",
            "detail": "Absence in the selected layers is not promoted to negative evidence.",
        })

    known_dimensions = WORLD_STATE_DIMENSIONS
    unqueried_dimensions = sorted(known_dimensions - set(normalized["scope"]["dimensions"]))
    selected_inputs = {
        "canonical_context": canonical_refs,
        "live_observations": [
            {"object_id": row["observation_id"], "revision_id": None, "manifest_key": _manifest_key("LIVE_INTELLIGENCE", row["observation_id"], None)}
            for row in live_observations
        ],
        "live_evidence": [
            {"object_id": row["evidence_id"], "revision_id": None, "manifest_key": _manifest_key("LIVE_INTELLIGENCE", row["evidence_id"], None)}
            for row in live_evidence
        ],
        "analysis_reviews": [
            {"object_id": row["analysis_id"], "revision_id": None, "manifest_key": _manifest_key("ANALYSIS", row["analysis_id"], None)}
            for row in analysis_reviews
        ],
        "analysis_evidence": [
            {"object_id": row["evidence_id"], "revision_id": None, "manifest_key": _manifest_key("ANALYSIS", row["evidence_id"], None)}
            for row in analysis_evidence
        ],
    }
    for layer, rows, id_key in (
        ("SIGNALS", revisions["signals"], "signal_id"),
        ("RELATIONSHIPS", revisions["relationships"], "relationship_id"),
        ("RISKS_REGIMES", revisions["risks"], "state_id"),
        ("SCENARIOS", revisions["scenarios"], "scenario_id"),
        ("FORECASTS", revisions["forecasts"], "issuance_id"),
        ("OUTCOMES", revisions["outcomes"], "outcome_id"),
    ):
        selected_inputs[layer.lower()] = [
            {"object_id": row[id_key], "revision_id": row.get("revision_id"), "manifest_key": _manifest_key(layer, row[id_key], row.get("revision_id"))}
            for row in rows
        ]

    proposal: dict[str, Any] = {
        "contract_version": CONTRACT_VERSION,
        "read_request": {key: value for key, value in normalized.items() if key != "_as_of"},
        "generated_at_utc": generated_at_utc,
        "source_manifest": manifest.as_list(),
        "source_manifest_sha256": object_sha256(manifest.as_list()),
        "selected_inputs": selected_inputs,
        "actors": [],
        "implementation_claims": [],
        "dimension_assessments": [],
        "baselines": [],
        "anomalies": [],
        "negative_evidence": [],
        "uncertainties": [],
        "hypotheses": [],
        "model_disagreement": [],
        "transmission_edges": [],
        "scenario_references": [
            {"scenario_id": row["scenario_id"], "revision_id": row["revision_id"]}
            for row in revisions["scenarios"]
        ],
        "forecast_outcome_references": [
            {
                "forecast_id": row["forecast_id"],
                "issuance_id": row["issuance_id"],
                "revision_id": row["revision_id"],
                "issued_at_utc": row["issued_at_utc"],
                "information_cutoff_at_utc": row["information_cutoff_at_utc"],
                "resolution": row["resolution"],
                "outcome_revision_ids": [
                    outcome["revision_id"] for outcome in revisions["outcomes"] if outcome.get("forecast_id") == row.get("forecast_id")
                ],
            }
            for row in revisions["forecasts"]
        ],
        "relationships": revisions["relationship_edges"],
        "risks_regimes": [{"state_id": row["state_id"], "revision_id": row["revision_id"]} for row in revisions["risks"]],
        "evaluation": {
            "evaluation_state": inputs["evaluation"].get("evaluation_state"),
            "evaluations": deepcopy(inputs["evaluation"].get("evaluations", [])),
        },
        "production_populations": {
            "relationships": len(revisions["relationships"]),
            "risks_regimes": len(revisions["risks"]),
            "scenarios": len(revisions["scenarios"]),
            "outcomes": len(revisions["outcomes"]),
        },
        "scope_coverage": {
            "queried_jurisdictions": list(jurisdictions),
            "queried_dimensions": list(normalized["scope"]["dimensions"]),
            "unqueried_dimensions": unqueried_dimensions,
            "queried_domain_with_no_eligible_evidence": [],
            "negative_evidence_status": (
                "NO_EXPLICIT_GOVERNED_NEGATIVE_EVIDENCE"
                if normalized["include_negative_evidence"]
                else "NOT_REQUESTED"
            ),
        },
        "limitations": limitations,
        "review_transaction": {
            "transaction_type": "WORLD_STATE_SYNTHESIS_REVIEW",
            "decision": "RETURNED_FOR_REVIEW",
            "decision_basis": "Ephemeral read proposal only; no human review or admission was performed.",
            "write_targets": [],
            "public_projection_permitted": False,
        },
        "mutation_check": {
            "status": "PASS" if before == _input_file_hashes() else "FAIL",
            "before": before,
            "after": _input_file_hashes(),
        },
    }
    if production_query is not None:
        from .world_state_production import read_production_world_state

        production_world_state = read_production_world_state(production_query)
        proposal["production_world_state"] = production_world_state
        if production_world_state["status"] == "ADMITTED_ASSESSMENT_AVAILABLE":
            proposal["limitations"] = [
                row for row in proposal["limitations"]
                if row.get("code") != "WORLD_STATE_ASSESSMENT_NOT_SYNTHESISED"
            ]
        else:
            proposal["limitations"].append({
                "code": "NO_ADMITTED_ASSESSMENT",
                "detail": "The explicit production-history query selected no admitted World State assessment.",
            })
    if proposal["mutation_check"]["status"] != "PASS":
        raise WorldStateReadError("governed input file hashes changed during read")
    proposal["semantic_fingerprint"] = semantic_fingerprint(proposal)
    proposal["proposal_id"] = f"WSWP-{proposal['semantic_fingerprint'][:16]}"
    errors = validate_proposal_manifest(proposal)
    if errors:
        raise WorldStateReadError("proposal consistency validation failed: " + "; ".join(errors))
    return proposal


def proposal_summary(proposal: dict[str, Any]) -> dict[str, Any]:
    """Return concise operator output without changing the proposal."""
    selected = proposal.get("selected_inputs", {})
    return {
        "proposal_status": "EPHEMERAL_READ_ONLY",
        "proposal_id": proposal.get("proposal_id"),
        "requested_as_of": proposal.get("read_request", {}).get("as_of_utc"),
        "semantic_fingerprint": proposal.get("semantic_fingerprint"),
        "source_manifest_sha256": proposal.get("source_manifest_sha256"),
        "selected_counts": {key: len(value) for key, value in selected.items()},
        "empty_layers": [key for key, value in proposal.get("production_populations", {}).items() if value == 0],
        "evaluation_state": proposal.get("evaluation", {}).get("evaluation_state"),
        "limitation_codes": [row.get("code") for row in proposal.get("limitations", [])],
        "mutation_check": proposal.get("mutation_check", {}).get("status"),
        "public_projection_permitted": proposal.get("review_transaction", {}).get("public_projection_permitted"),
    }
