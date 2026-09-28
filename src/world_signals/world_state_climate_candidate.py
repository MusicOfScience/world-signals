"""Step 14A climate World State candidates.

This module constructs a retained, review-pending standalone Baseline and a
narrow completed-season CLIMATE_PHYSICAL_RISK assessment from the governed
Australian tropical-cyclone Analysis.  It never writes production World State
history or public projection data.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from .analysis import validate_analysis
from .world_state_history import fingerprint, validate_component_revision, with_object_fingerprint


ANALYSIS_ID = "WSAN-AU-TCSEASON-2025-26-001"
OCCURRENCE_ID = "WSO-RISK-AU-TC-2025-26"
SERIES_ID = "WSER-RISK-AU-TC"
EVIDENCE_IDS = (
    "WSEV-AU-TC-BOM-SEASON-SUMMARY-20260514",
    "WSEV-AU-TC-BOM-SEASON-NEWS-20260514",
    "WSEV-AU-TC-BOM-SEASON-PLANNING-202510",
    "WSEV-AU-TC-BOM-TROPICAL-UPDATE-20251014",
)
BASELINE_ID = "WSBASE-CLIMATE-AU-TC-CLIMATOLOGY-1980-81-001"
BASELINE_REVISION_ID = f"{BASELINE_ID}-R1"
DIMENSION_ID = "WSDIM-CLIMATE-AU-TCSEASON-2025-26-001"
DIMENSION_REVISION_ID = f"{DIMENSION_ID}-R1"
CONSTRUCTION_CUTOFF = "2026-09-28T13:30:00Z"
PROCEDURE_VERSION = "world-state-step14a-climate-candidate-v1"


class ClimateCandidateError(ValueError):
    """Raised when the bounded Step 14A candidate cannot be built safely."""


def _load(root: Path, relative: str) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def _entry(layer: str, object_id: str, obj: dict[str, Any]) -> dict[str, Any]:
    return {
        "layer": layer,
        "object_id": object_id,
        "revision_id": None,
        "object_sha256": fingerprint(obj),
        "object": deepcopy(obj),
    }


def _citation(entry: dict[str, Any], epistemic_class: str, **extra: Any) -> dict[str, Any]:
    result = {
        "layer": entry["layer"],
        "object_id": entry["object_id"],
        "revision_id": entry.get("revision_id"),
        "object_sha256": entry["object_sha256"],
        "epistemic_class": epistemic_class,
    }
    result.update(extra)
    return result


def _model_provenance(manifest_sha256: str, output: dict[str, Any]) -> dict[str, Any]:
    return {
        "execution_surface": "Codex",
        "model_identity": "UNAVAILABLE",
        "model_version": "UNAVAILABLE",
        "version": "UNAVAILABLE",
        "reasoning_configuration": "UNAVAILABLE",
        "provenance_status": "RUNTIME_METADATA_UNAVAILABLE",
        "configuration": "Step 14A deterministic climate candidate-construction procedure",
        "analytical_lens": "narrow completed Australian tropical-cyclone season physical-risk assessment",
        "procedure_version": PROCEDURE_VERSION,
        "generated_at_utc": CONSTRUCTION_CUTOFF,
        "input_manifest_sha256": manifest_sha256,
        "output_fingerprint": fingerprint(output),
        "factual_evidence_status": "MODEL_OUTPUT_IS_NOT_FACTUAL_CORROBORATION",
    }


def _empty_domains() -> list[dict[str, str]]:
    return [
        {"domain": "ACTOR_STATE_ASSERTIONS", "state": "UNQUERIED"},
        {"domain": "IMPLEMENTATION_CLAIMS", "state": "UNQUERIED"},
        {"domain": "RELATIONSHIPS", "state": "QUERIED_EMPTY"},
        {"domain": "RISKS_REGIMES", "state": "QUERIED_EMPTY"},
        {"domain": "SCENARIOS", "state": "QUERIED_EMPTY"},
        {"domain": "FORECASTS", "state": "UNQUERIED"},
        {"domain": "OUTCOMES", "state": "QUERIED_EMPTY"},
        {"domain": "CANONICAL_HISTORICAL_AS_OF", "state": "UNSUPPORTED"},
    ]


def _make_baseline(manifest_sha256: str, citations: list[dict[str, Any]]) -> dict[str, Any]:
    baseline = {
        "component_type": "BASELINE",
        "component_id": BASELINE_ID,
        "revision_id": BASELINE_REVISION_ID,
        "revision_number": 1,
        "previous_revision_id": None,
        "revision_kind": "INITIAL",
        "review_state": "UNDER_REVIEW",
        "lifecycle_state": "UNRESOLVED",
        "effective_at": None,
        "effective_date": None,
        "effective_time_precision": "SOURCE_NATIVE_SEASON_SERIES",
        "effective_time_basis": "Source-native reference window; no exact UTC boundary is manufactured.",
        "known_at_utc": "2026-09-05T23:35:00Z",
        "known_at_basis": "GOVERNED_ANALYSIS_REVIEW_BOUNDARY",
        "reviewed_at_utc": None,
        "admitted_at_utc": None,
        "source_proposal_id": f"WS-STEP14A-{BASELINE_ID}",
        "source_manifest_sha256": manifest_sha256,
        "review_transaction_id": None,
        "admission_transaction_id": None,
        "projection_transaction_id": None,
        "visibility": "INTERNAL_ONLY",
        "revision_reason": "Step 14A standalone Baseline candidate; no production admission or public projection.",
        "basis": "OFFICIAL_REFERENCE",
        "scope": {
            "jurisdictions": ["Australia"],
            "geographic_scope": "Australian tropical cyclone region",
            "measure": "Australian-region tropical cyclone count per season",
        },
        "reference_window": {
            "source_native_label": "since 1980–81",
            "exact_start": None,
            "exact_end": None,
            "precision": "SOURCE_NATIVE_SEASON_SERIES",
        },
        "baseline_value_or_label": "about 10 Australian-region tropical cyclones per season",
        "baseline_value_type": "APPROXIMATE_SOURCE_LABEL",
        "measurement_definition": {
            "measure": "Australian-region tropical cyclone count per season",
            "unit": "cyclones_per_season",
            "aggregation": "SEASONAL_COUNT",
            "precision": "APPROXIMATE",
        },
        "supporting_citations": citations,
        "contradictory_citations": [],
        "uncertainties": [
            {
                "type": "MEASUREMENT",
                "status": "BOUNDED",
                "description": "The source says about 10 and describes a climatological seasonal count; it is not an exact population mean or severe-count measure.",
                "basis_refs": [EVIDENCE_IDS[2]],
            },
            {
                "type": "TEMPORAL",
                "status": "BOUNDED",
                "description": "The reference window is retained as since 1980–81 without invented UTC start or end instants.",
                "basis_refs": [EVIDENCE_IDS[2]],
            },
            {
                "type": "INTERPRETIVE",
                "status": "BOUNDED",
                "description": "The climatology is comparison context, not a 2025–26 forecast or an abnormality threshold.",
                "basis_refs": [ANALYSIS_ID, EVIDENCE_IDS[2]],
            },
        ],
        "limitations": [
            "climatological/reference guidance only",
            "not a 2025–26 season-specific Forecast or probability distribution",
            "not a severe-cyclone-count baseline",
            "not a damage, loss or attribution baseline",
            "does not define a normal-versus-abnormal threshold",
            "typical 3–4 mainland landfalls remain comparison context, not a second Baseline component",
        ],
        "object_sha256": None,
    }
    return with_object_fingerprint(baseline)


def _make_dimension(manifest_sha256: str, citations: list[dict[str, Any]], baseline_ref: str, analysis: dict[str, Any]) -> dict[str, Any]:
    actuals = {row["metric"]: row["value"] for row in analysis["what_happened"]["actuals"]}
    dimension = {
        "component_type": "DIMENSION_ASSESSMENT",
        "component_id": DIMENSION_ID,
        "revision_id": DIMENSION_REVISION_ID,
        "revision_number": 1,
        "previous_revision_id": None,
        "revision_kind": "INITIAL",
        "review_state": "UNDER_REVIEW",
        "lifecycle_state": "UNRESOLVED",
        "effective_at": None,
        "effective_date": None,
        "effective_time_precision": "DAY_RANGE",
        "effective_time_basis": "Canonical completed seasonal window; no UTC instant is manufactured from source-native local dates.",
        "effective_period": {
            "occurrence_id": OCCURRENCE_ID,
            "series_id": SERIES_ID,
            "start_local": "2025-11-01",
            "end_local": "2026-04-30",
            "time_precision": "DAY",
            "all_day_semantics": True,
        },
        "known_at_utc": analysis["analysis_as_of_utc"],
        "known_at_basis": "GOVERNED_ANALYSIS_REVIEW_BOUNDARY",
        "reviewed_at_utc": None,
        "admitted_at_utc": None,
        "source_proposal_id": f"WS-STEP14A-{DIMENSION_ID}",
        "source_manifest_sha256": manifest_sha256,
        "review_transaction_id": None,
        "admission_transaction_id": None,
        "projection_transaction_id": None,
        "visibility": "INTERNAL_ONLY",
        "revision_reason": "Step 14A completed historical climate physical-risk candidate; no production admission or public projection.",
        "dimension": "CLIMATE_PHYSICAL_RISK",
        "scope": {
            "jurisdictions": ["Australia"],
            "systems": ["AUSTRALIAN_TROPICAL_CYCLONE_REGION"],
            "boundaries": ["completed 2025–26 seasonal physical-risk window", "aggregate season context, not named-cyclone shock"],
        },
        "state_label": "COMPLETED_AUSTRALIAN_REGION_CYCLONE_SEASON_REALISATION",
        "direction": "NOT_ASSESSED",
        "persistence": "COMPLETED_HISTORICAL_WINDOW",
        "breadth": "REGIONAL_HAZARD_WINDOW",
        "qualitative_confidence": "NOT_ASSESSED",
        "confidence_by_aspect": [
            {"aspect": "reported_realised_counts", "assessment": "HIGH", "basis": "official post-season measurements"},
            {"aspect": "climatological_comparison", "assessment": "NOT_ASSESSED", "basis": "climatology is not a season-specific forecast"},
            {"aspect": "damage_impact_attribution", "assessment": "NOT_ASSESSED", "basis": "not established by the governed Analysis"},
        ],
        "realised_measurements": [
            {"metric": "australian_region_tropical_cyclone_count", "value": actuals["australian_region_tropical_cyclone_count"], "unit": "cyclones", "evidence_refs": [EVIDENCE_IDS[0]]},
            {"metric": "severe_tropical_cyclone_count", "value": actuals["severe_tropical_cyclone_count"], "unit": "cyclones_category_3_or_greater", "evidence_refs": [EVIDENCE_IDS[0]]},
            {"metric": "category_5_tropical_cyclone_count", "value": 2, "unit": "cyclones", "evidence_refs": [EVIDENCE_IDS[0], EVIDENCE_IDS[1]]},
            {"metric": "mainland_landfall_count_at_tropical_cyclone_strength", "value": actuals["mainland_landfall_count_at_tropical_cyclone_strength"], "unit": "cyclones", "evidence_refs": [EVIDENCE_IDS[0]]},
            {"metric": "mainland_crossing_count_at_tropical_low_strength", "value": actuals["mainland_crossing_count_at_tropical_low_strength"], "unit": "systems", "evidence_refs": [EVIDENCE_IDS[0]]},
        ],
        "baseline_ref": baseline_ref,
        "baseline_comparison": {
            "status": "DESCRIPTIVE_CONTEXT_ONLY",
            "cyclone_count_context": "11 versus about 10 climatological average",
            "landfall_context": "4 versus typically 3–4 mainland landfalls",
            "forecast_surprise": "NOT_ESTABLISHED",
        },
        "supporting_citations": citations,
        "contradictory_citations": [],
        "uncertainties": [
            {
                "type": "PROVENANCE_SOURCE",
                "status": "BOUNDED",
                "description": "The supporting Bureau publications belong to one institutional source family; repeated Bureau rows are not independent corroboration.",
                "basis_refs": list(EVIDENCE_IDS),
            },
            {
                "type": "MEASUREMENT",
                "status": "BOUNDED",
                "description": "Cyclone count, severity and landfall measures do not measure damage, exposure, loss or economic effect.",
                "basis_refs": [EVIDENCE_IDS[0], EVIDENCE_IDS[1]],
            },
            {
                "type": "TEMPORAL",
                "status": "BOUNDED",
                "description": "The assessment concerns the completed source-native seasonal window; Analysis review time is distinct from the season period and publication dates.",
                "basis_refs": [OCCURRENCE_ID, ANALYSIS_ID],
            },
            {
                "type": "INTERPRETIVE",
                "status": "BOUNDED",
                "description": "The completed realised state is not a trend, forecast surprise, abnormality finding or present-tense current-risk claim.",
                "basis_refs": [ANALYSIS_ID],
            },
        ],
        "what_surprised": "NOT_ESTABLISHED",
        "common_driver_context": {
            "interaction_type": "COMMON_DRIVER_CONTEXT",
            "causal_status": "NOT_A_CAUSAL_CLAIM",
            "source_value": "retained from reviewed Analysis only",
        },
        "anomaly_refs": [],
        "prior_revision_ref": None,
        "transition_type": "INITIAL",
        "limitations": [
            "hazard intensity is not damage, exposure, loss, mortality, GDP or supply-chain impact",
            "11 versus about 10 is not a forecast surprise or abnormality threshold",
            "seven severe systems has no governed severe-count benchmark in this specimen",
            "aggregate season is not a named-cyclone or physical-shock object",
            "warm SST and climate context are not attribution to climate change, ENSO or another single driver",
            "no current Australian cyclone-risk claim is made after the completed window",
            "no current freshness policy is invented for this historical completed assessment",
            "no Risk, Scenario, Forecast, Outcome, Actor or Relationship is created",
        ],
        "model_provenance": _model_provenance(manifest_sha256, {"state_label": "COMPLETED_AUSTRALIAN_REGION_CYCLONE_SEASON_REALISATION", "direction": "NOT_ASSESSED"}),
        "object_sha256": None,
    }
    return with_object_fingerprint(dimension)


def build_climate_candidate(root: Path, *, construction_cutoff_utc: str = CONSTRUCTION_CUTOFF) -> dict[str, Any]:
    if construction_cutoff_utc != CONSTRUCTION_CUTOFF:
        raise ClimateCandidateError("Step 14A requires the explicit reproducible construction cutoff")
    schema = _load(root, "data/analysis/schema.json")
    reviews_dataset = _load(root, "data/analysis/event_reviews.json")
    evidence_dataset = _load(root, "data/analysis/evidence_registry.json")
    canonical = _load(root, "data/canonical/registry.json")
    report = validate_analysis(schema, evidence_dataset, reviews_dataset, canonical)
    if not report.ok:
        raise ClimateCandidateError("Analysis validation failed: " + "; ".join(report.errors))
    analysis = next((row for row in reviews_dataset["reviews"] if row.get("analysis_id") == ANALYSIS_ID), None)
    if analysis is None or analysis.get("review_state") != "REVIEWED_SAMPLE":
        raise ClimateCandidateError("expected reviewed Australian tropical-cyclone Analysis is unavailable")
    evidence = {row["evidence_id"]: row for row in evidence_dataset["evidence"]}
    if any(identifier not in evidence for identifier in EVIDENCE_IDS):
        raise ClimateCandidateError("required Bureau evidence lineage is incomplete")
    occurrence = next((row for row in canonical["records"] if row.get("occurrence_id") == OCCURRENCE_ID), None)
    if occurrence is None or occurrence.get("series_id") != SERIES_ID or occurrence.get("lifecycle_status") != "COMPLETED":
        raise ClimateCandidateError("completed canonical seasonal occurrence is unavailable or changed")
    if (occurrence.get("start_local"), occurrence.get("end_local"), occurrence.get("time_precision"), occurrence.get("start_utc"), occurrence.get("end_utc")) != ("2025-11-01", "2026-04-30", "DAY", None, None):
        raise ClimateCandidateError("canonical seasonal window precision differs from the bounded specimen")

    manifest = [
        _entry("ANALYSIS", ANALYSIS_ID, analysis),
        _entry("CANONICAL", OCCURRENCE_ID, occurrence),
        *[_entry("ANALYSIS_EVIDENCE", identifier, evidence[identifier]) for identifier in EVIDENCE_IDS],
    ]
    manifest.sort(key=lambda row: (row["layer"], row["object_id"]))
    manifest_sha256 = fingerprint(manifest)
    by_id = {row["object_id"]: row for row in manifest}
    baseline_citations = [
        _citation(by_id[EVIDENCE_IDS[2]], "FACTUAL_SOURCE", role="OFFICIAL_REFERENCE"),
        _citation(by_id[ANALYSIS_ID], "HYPOTHESIS", factual_claim=False, role="REVIEWED_ANALYSIS_SUBSTRATE"),
    ]
    dimension_citations = [
        _citation(by_id[identifier], "FACTUAL_SOURCE", role="REALISED_MEASUREMENT" if identifier in EVIDENCE_IDS[:2] else "CONTEXT_OR_COMPARISON")
        for identifier in EVIDENCE_IDS
    ] + [_citation(by_id[ANALYSIS_ID], "HYPOTHESIS", factual_claim=False, role="REVIEWED_ANALYSIS_SUBSTRATE")]
    baseline = _make_baseline(manifest_sha256, baseline_citations)
    dimension = _make_dimension(manifest_sha256, dimension_citations, BASELINE_REVISION_ID, analysis)
    for label, candidate in (("Baseline", baseline), ("Dimension", dimension)):
        errors = validate_component_revision(candidate)
        if errors:
            raise ClimateCandidateError(f"{label} candidate validation failed: " + "; ".join(errors))
    production = {
        "actors": len(_load(root, "data/world_state/actor_registry.json").get("actors", [])) if (root / "data/world_state/actor_registry.json").exists() else 0,
        "components": len(_load(root, "data/world_state/components.json").get("components", [])),
        "snapshots": len(_load(root, "data/world_state/snapshots.json").get("snapshots", [])),
        "admissions": len(_load(root, "data/world_state/admission_transactions.json").get("transactions", [])),
        "baseline_components": 0,
        "writes": [],
    }
    package = {
        "package_type": "WORLD_STATE_STEP14A_CLIMATE_CANDIDATE",
        "package_version": "0.1",
        "status": "REVIEW_PENDING",
        "preflight_classification": "READY_FOR_HUMAN_COMPONENT_REVIEW",
        "constructed_at_utc": construction_cutoff_utc,
        "knowledge_cutoff_utc": analysis["analysis_as_of_utc"],
        "analysis_id": ANALYSIS_ID,
        "canonical_occurrence_id": OCCURRENCE_ID,
        "source_manifest": manifest,
        "source_manifest_sha256": manifest_sha256,
        "baseline_candidate": baseline,
        "dimension_assessment_candidate": dimension,
        "baseline_candidate_fingerprint": fingerprint(baseline, exclude={"object_sha256"}),
        "dimension_candidate_fingerprint": fingerprint(dimension, exclude={"object_sha256"}),
        "candidate_semantic_fingerprint": None,
        "candidate_dispositions": [
            {"candidate_id": BASELINE_REVISION_ID, "options": ["ACCEPT", "DEFER", "REJECT"], "decision": None},
            {"candidate_id": DIMENSION_REVISION_ID, "options": ["ACCEPT", "DEFER", "REJECT"], "decision": None},
        ],
        "proposed_snapshot": {"status": "NOT_CONSTRUCTED_STEP14A", "write_targets": [], "reason": "Step 14A retains two independently reviewable component candidates only."},
        "actor_state_assertions": [],
        "implementation_claims": [],
        "relationships": [],
        "risks_regimes": [],
        "scenarios": [],
        "forecasts": [],
        "outcomes": [],
        "negative_evidence": [],
        "competing_hypotheses": [],
        "model_disagreements": [],
        "production_state": production,
        "visibility": "INTERNAL_ONLY",
        "public_projection_permitted": False,
        "write_targets": [],
        "known_empty_or_unsupported_domains": _empty_domains(),
        "gates": {
            "analysis_reviewed_and_hash_pinned": {"status": "PASS"},
            "canonical_window_and_precision_pinned": {"status": "PASS"},
            "baseline_is_official_reference_not_forecast": {"status": "PASS"},
            "realised_hazard_not_impact_or_attribution": {"status": "PASS"},
            "human_component_review": {"status": "DEFER", "basis": "Each candidate requires an explicit ACCEPT, DEFER or REJECT decision."},
            "production_admission": {"status": "DEFER", "basis": "No production admission is performed in Step 14A."},
            "public_projection": {"status": "DEFER", "basis": "World State remains internal and public projection is closed."},
        },
        "limitations": [
            "This package is audit/review evidence, not production World State history.",
            "The Baseline and Dimension candidates are independently reviewable and need not be admitted together.",
            "The completed seasonal window is aggregate context, not a named-cyclone shock.",
            "No anomaly, negative evidence, Relationship, Risk, Scenario, Forecast, Outcome, Actor or Model Disagreement is created.",
        ],
    }
    package["candidate_semantic_fingerprint"] = fingerprint({
        "package_type": package["package_type"],
        "analysis_id": package["analysis_id"],
        "canonical_occurrence_id": package["canonical_occurrence_id"],
        "source_manifest_sha256": package["source_manifest_sha256"],
        "baseline_candidate": baseline,
        "dimension_assessment_candidate": dimension,
        "candidate_dispositions": package["candidate_dispositions"],
        "proposed_snapshot": package["proposed_snapshot"],
    })
    return package


def validate_climate_candidate_package(package: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(package, dict):
        return ["package must be an object"]
    if package.get("package_type") != "WORLD_STATE_STEP14A_CLIMATE_CANDIDATE":
        errors.append("invalid Step 14A package type")
    if package.get("status") != "REVIEW_PENDING" or package.get("preflight_classification") != "READY_FOR_HUMAN_COMPONENT_REVIEW":
        errors.append("package must remain review pending and ready for human component review")
    if package.get("visibility") != "INTERNAL_ONLY" or package.get("public_projection_permitted") is not False:
        errors.append("Step 14A package must remain internal and non-public")
    if package.get("write_targets") != [] or package.get("production_state", {}).get("writes") != []:
        errors.append("Step 14A package must have no write targets")
    baseline = package.get("baseline_candidate")
    dimension = package.get("dimension_assessment_candidate")
    for label, candidate in (("Baseline", baseline), ("Dimension", dimension)):
        if not isinstance(candidate, dict):
            errors.append(f"{label} candidate is missing")
            continue
        errors.extend(f"{label}: {error}" for error in validate_component_revision(candidate))
        if candidate.get("review_state") != "UNDER_REVIEW" or candidate.get("lifecycle_state") != "UNRESOLVED":
            errors.append(f"{label} candidate is not unadmitted")
        if candidate.get("admitted_at_utc") is not None or candidate.get("admission_transaction_id") is not None:
            errors.append(f"{label} candidate contains production admission metadata")
        if candidate.get("visibility") != "INTERNAL_ONLY":
            errors.append(f"{label} candidate is not internal")
    if isinstance(baseline, dict):
        if baseline.get("component_type") != "BASELINE" or baseline.get("basis") != "OFFICIAL_REFERENCE":
            errors.append("Baseline candidate is not an official-reference Baseline")
        if baseline.get("reference_window", {}).get("source_native_label") != "since 1980–81":
            errors.append("Baseline source-native reference window changed")
        if baseline.get("reference_window", {}).get("exact_start") is not None or baseline.get("reference_window", {}).get("exact_end") is not None:
            errors.append("Baseline invented exact reference-window bounds")
    if isinstance(dimension, dict):
        if dimension.get("component_type") != "DIMENSION_ASSESSMENT" or dimension.get("dimension") != "CLIMATE_PHYSICAL_RISK":
            errors.append("Dimension candidate is not CLIMATE_PHYSICAL_RISK")
        if dimension.get("direction") != "NOT_ASSESSED" or dimension.get("what_surprised") != "NOT_ESTABLISHED":
            errors.append("Dimension candidate incorrectly infers direction or surprise")
        if dimension.get("baseline_ref") != BASELINE_REVISION_ID:
            errors.append("Dimension candidate does not pin the Baseline candidate revision")
    manifest = package.get("source_manifest")
    if not isinstance(manifest, list) or package.get("source_manifest_sha256") != fingerprint(manifest):
        errors.append("source manifest fingerprint mismatch")
    else:
        for entry in manifest:
            if entry.get("object_sha256") != fingerprint(entry.get("object")):
                errors.append(f"source manifest object hash mismatch: {entry.get('object_id')}")
    if package.get("baseline_candidate_fingerprint") != fingerprint(baseline, exclude={"object_sha256"}):
        errors.append("Baseline candidate fingerprint mismatch")
    if package.get("dimension_candidate_fingerprint") != fingerprint(dimension, exclude={"object_sha256"}):
        errors.append("Dimension candidate fingerprint mismatch")
    expected_semantic = fingerprint({
        "package_type": package.get("package_type"),
        "analysis_id": package.get("analysis_id"),
        "canonical_occurrence_id": package.get("canonical_occurrence_id"),
        "source_manifest_sha256": package.get("source_manifest_sha256"),
        "baseline_candidate": baseline,
        "dimension_assessment_candidate": dimension,
        "candidate_dispositions": package.get("candidate_dispositions"),
        "proposed_snapshot": package.get("proposed_snapshot"),
    })
    if package.get("candidate_semantic_fingerprint") != expected_semantic:
        errors.append("package semantic fingerprint mismatch")
    for field in ("actor_state_assertions", "implementation_claims", "relationships", "risks_regimes", "scenarios", "forecasts", "outcomes", "negative_evidence", "competing_hypotheses", "model_disagreements"):
        if package.get(field) != []:
            errors.append(f"Step 14A must not populate {field}")
    return errors
