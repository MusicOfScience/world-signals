"""Candidate-only official projection / assumption-audit validation.

No retrieval, registry write, admission or public projection API. These retained
Step 14D artifacts remain candidates. Step 14E adopted their native v0.9 shape;
Step 14F separately admitted an immutable-linked production copy internally.
Neither native validation nor this inspector grants publication authority.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from .analysis import validate_analysis
from .world_state_history import fingerprint


AUDIT_AXES = (
    "historical_plausibility", "current_trajectory", "structural_break_risk",
    "implementation_dependency", "circularity_endogeneity", "sensitivity",
    "downside_alternative", "upside_alternative", "signposts", "revision_conditions",
)
EDGE_CLASSES = {
    "MODEL_DEFINED", "ASSUMED_MECHANISM", "SENSITIVITY_SUPPORTED",
    "EXTERNAL_EVIDENCE_SUPPORTED", "HYPOTHESISED",
}
CLASSES = {
    "PUBLICATION_FACT", "OBSERVED_EVIDENCE", "MODEL_ASSUMPTION",
    "OFFICIAL_PROJECTION", "SENSITIVITY_CASE", "POLICY_CLAIM",
    "PRIOR_OFFICIAL_PROJECTION",
}
PREFIX = "STEP14D_AU_IGR_"
FILES = {
    "evidence_manifest": PREFIX + "EVIDENCE_MANIFEST_REVIEW_PENDING.json",
    "projection_inventory": PREFIX + "OFFICIAL_PROJECTION_INVENTORY_REVIEW_PENDING.json",
    "assumption_audit": PREFIX + "ASSUMPTION_AUDIT_REVIEW_PENDING.json",
    "analysis_candidate": PREFIX + "ANALYSIS_CANDIDATE_REVIEW_PENDING.json",
    "extension_candidate": PREFIX + "CONTRACT_EXTENSION_REVIEW_PENDING.json",
}


class ProjectionCandidateError(ValueError):
    """Fail closed on candidate integrity or epistemic-boundary violation."""


def semantic_fingerprint(value: dict[str, Any]) -> str:
    return fingerprint({k: v for k, v in value.items() if k != "semantic_fingerprint"})


def seal(value: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(value)
    result["semantic_fingerprint"] = semantic_fingerprint(result)
    return result


def protected_file_hashes(root: Path) -> dict[str, str]:
    """Existing data and public source files; Step 14D candidates are excluded."""
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for directory in ("data", "web")
        for path in sorted((root / directory).rglob("*"))
        if path.is_file() and not path.name.startswith(PREFIX)
    }


def _require(condition: Any, message: str) -> None:
    if not condition:
        raise ProjectionCandidateError(message)


def _utc(value: Any) -> datetime:
    _require(isinstance(value, str) and value.endswith("Z"), "exact UTC required")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ProjectionCandidateError("invalid UTC") from error


def _no_scores(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _require(key not in {"score", "quality_score", "global_confidence_score", "overall_verdict", "rating"}, "scores/aggregate verdict prohibited")
            _no_scores(item)
    elif isinstance(value, list):
        for item in value:
            _no_scores(item)


def validate_package(package: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Validate retained extraction, not the truth of an analyst's interpretation."""
    _require(set(package) == set(FILES), "exact candidate package parts required")
    for part in package.values():
        _require(part.get("contract_version") == "0.1-candidate", "candidate version required")
        _require(part.get("review_state") == "REVIEW_PENDING", "no accepted production candidate")
        _require(part.get("visibility") == "INTERNAL_ONLY", "candidate remains private")
        _require(part.get("write_targets") == [], "no production write targets")
        _require(part.get("public_projection_permitted") is False, "public gate closed")
        _require(part.get("semantic_fingerprint") == semantic_fingerprint(part), "candidate fingerprint mismatch")
        _no_scores(part)

    manifest = package["evidence_manifest"]
    assets = {row["asset_id"]: row for row in manifest["assets"]}
    _require(bool(assets), "evidence assets required")
    _require(len(assets) == len(manifest["assets"]), "duplicate asset identity")
    for row in assets.values():
        _require(row["url"].startswith("https://"), "source locator required")
        _require(len(row["sha256"]) == 64 and all(c in "0123456789abcdef" for c in row["sha256"]), "asset SHA256 required")
        _require(row.get("content_type") and row.get("source_family"), "source metadata required")
        _utc(row["retrieved_at_utc"])
        _require(row["source_class"] in CLASSES, "invalid source epistemic class")
    _require(manifest["asset_manifest_sha256"] == fingerprint(manifest["assets"]), "asset manifest mismatch")
    _require(manifest["chart_manifest_sha256"] == fingerprint(manifest["chart_members"]), "chart manifest mismatch")
    _utc(manifest["research_as_of_utc"])
    _require(all(_utc(row["retrieved_at_utc"]) <= _utc(manifest["research_as_of_utc"]) for row in assets.values()), "future retrieval")
    _require(manifest["mutation_result"] == "PASS" and manifest["protected_input_fingerprint_before"] == manifest["protected_input_fingerprint_after"] == fingerprint(manifest["protected_input_hashes"]), "historical mutation proof mismatch")
    pins = manifest["governed_object_pins"]
    _require(len({(r["layer"], r["object_id"]) for r in pins}) == len(pins), "duplicate governed pin")
    _require(all(r["layer"] in {"canonical", "sources"} and len(r["object_sha256"]) == 64 for r in pins), "invalid governed pin")

    def refs(rows: list[dict[str, Any]]) -> None:
        _require(bool(rows), "locatable source references required")
        for ref in rows:
            _require(ref.get("asset_id") in assets and bool(ref.get("locator")), "unresolved source/locator")

    inventory = package["projection_inventory"]
    refs(inventory["projection_framework"]["source_refs"])
    _require(inventory["projection_framework"]["publication_fact"]["epistemic_class"] == "PUBLICATION_FACT", "publication fact separate")
    framing = inventory["projection_framework"]["ministerial_framing"]
    _require(framing["epistemic_class"] == "POLICY_CLAIM", "ministerial framing is not factual corroboration")
    refs(framing["source_refs"])
    _require(inventory["comparison_baseline"]["epistemic_class"] == "PRIOR_OFFICIAL_PROJECTION", "prior projection is not truth")
    refs(inventory["comparison_baseline"]["source_refs"])
    assumptions = {row["assumption_id"]: row for row in inventory["model_assumptions"]}
    outputs = {row["projection_id"]: row for row in inventory["projection_outputs"]}
    _require(len(assumptions) == len(inventory["model_assumptions"]), "duplicate assumption")
    _require(len(outputs) == len(inventory["projection_outputs"]), "duplicate projection")
    sensitivities = {row["sensitivity_id"]: row for row in inventory["sensitivity_cases"]}
    _require(bool(assumptions) and bool(outputs), "material inventory required")
    _require(len(sensitivities) == len(inventory["sensitivity_cases"]), "duplicate sensitivity")
    for row in outputs.values():
        _require(row.get("projection_class") == "OFFICIAL_PROJECTION", "future output is not observation/Forecast")
        _require(row.get("horizon") and row.get("reference_year") and row.get("unit"), "output period/units required")
        _require(isinstance(row.get("value"), (int, float, str)) and not isinstance(row.get("value"), bool), "output value required")
        _require(not isinstance(row["value"], (float, int)) or math.isfinite(row["value"]), "finite output value required")
        _require(row.get("assumption_refs") and set(row["assumption_refs"]) <= assumptions.keys(), "output assumptions unresolved")
        _require(set(row.get("sensitivity_refs", [])) <= sensitivities.keys(), "sensitivity unresolved")
        refs(row["source_refs"])
        for ref in row["source_refs"]:
            _require(assets[ref["asset_id"]]["role"] in {"TECHNICAL_REPORT", "CHART_DATA", "TECHNICAL_FACT_SHEET"} and assets[ref["asset_id"]]["vintage"] == inventory["projection_framework"]["report_vintage"], "ministerial/prior source cannot establish technical output")
    for row in assumptions.values():
        _require(row.get("epistemic_class") == "MODEL_ASSUMPTION", "assumption class")
        _require(row.get("basis_kind") in {"EMPIRICAL_EXTRAPOLATION", "MAINTAINED_POLICY_SETTING", "TECHNICAL_CONVENTION", "CONDITIONAL_MODEL_MECHANISM"}, "assumption basis required")
        if row.get("assumption_type") == "FISCAL_POLICY_SETTING":
            _require(row["basis_kind"] == "MAINTAINED_POLICY_SETTING", "policy premise is not empirical validation")
        _require(row.get("assumption_type") and row.get("value_or_rule") is not None and row.get("issuer_rationale") and row.get("unit") and row.get("reference_period") and row.get("projection_horizon"), "assumption substance required")
        _require(set(row["output_dependencies"]) <= outputs.keys(), "output dependency unresolved")
        _require(set(row["output_dependencies"]) == {o["projection_id"] for o in outputs.values() if row["assumption_id"] in o["assumption_refs"]}, "dependency direction mismatch")
        refs(row["source_refs"])
    for row in sensitivities.values():
        _require(row.get("epistemic_class") == "SENSITIVITY_CASE", "sensitivity not central path")
        _require(set(row["assumption_refs"]) <= assumptions.keys(), "sensitivity assumption unresolved")
        _require(row.get("shock") and row.get("results") and row.get("horizon") and row.get("limitations"), "bounded sensitivity required")
        refs(row["source_refs"])
    for row in inventory["observed_evidence"]:
        _require(row.get("epistemic_class") == "OBSERVED_EVIDENCE", "observations separate")
        refs(row["source_refs"])
        _require(all(assets[r["asset_id"]]["role"] == "OBSERVED_AUDIT_EVIDENCE" for r in row["source_refs"]), "projection source cannot establish observed audit values")
        _require(row.get("reference_period") and row.get("limitations"), "observed evidence needs period/limitations")
    for row in inventory["major_transitions"]:
        _require(row["treatment"] in {"CONDITIONAL_QUANTITATIVE_AND_QUALITATIVE", "QUALITATIVE_CONTEXT", "QUANTITATIVE_MODEL_AND_POLICY_CONTEXT", "DESCRIPTIVE_AND_POLICY_CONTEXT"}, "transition modelling class required")
        refs(row["source_refs"])

    audit = package["assumption_audit"]
    _require(audit["inventory_fingerprint"] == inventory["semantic_fingerprint"], "audit inventory mismatch")
    audit_rows = audit["assumption_audit"]
    _require({row["assumption_id"] for row in audit_rows} == set(assumptions) and len(audit_rows) == len(assumptions), "each assumption needs one audit")
    for row in audit_rows:
        for axis in AUDIT_AXES:
            assessment = row.get(axis, {})
            _require(assessment.get("finding") and assessment.get("limitations"), "audit axis needs finding/limitations: " + axis)
            refs(assessment.get("source_refs", []))
    for row in audit["historical_backtest"]:
        _require(row.get("original_vintage") and row.get("observed_vintage") and row.get("reference_period") and row.get("method_basis"), "backtest vintage/method required")
        refs(row["source_refs"])
        _require(any(assets[r["asset_id"]]["role"] == "ORIGINAL_VINTAGE_REPORT" and assets[r["asset_id"]]["vintage"] == row["original_vintage"] for r in row["source_refs"]), "original backtest vintage unresolved")
        _require(row["comparability"] in {"SOURCE_REPORTED_COMPARISON", "NOT_DIRECTLY_COMPARABLE"}, "backtest comparability explicit")
        if row["comparability"] == "NOT_DIRECTLY_COMPARABLE":
            _require(row.get("error") is None, "no noncomparable error")
        else:
            _require(row["error"] == round(row["observed_value"] - row["original_projected_value"], 6), "backtest arithmetic")
    for row in audit["projection_comparison"]:
        refs(row["source_refs"])
        _require(row["comparability"] in {"MATCHED_HORIZON_MODEL_REVISION", "NOT_DIRECTLY_COMPARABLE"}, "comparison method required")
        _require(row.get("method_basis") and row.get("identified_driver"), "comparison basis required")
        if row["comparability"] == "MATCHED_HORIZON_MODEL_REVISION":
            _require(row["prior_horizon"] == row["current_horizon"], "cannot compare unlike horizons")
            _require(row["difference"] == round(row["current_value"] - row["prior_value"], 6), "comparison arithmetic")
        else:
            _require(row.get("difference") is None, "noncomparable difference prohibited")
    for row in audit["dependency_map"]:
        _require(row["epistemic_class"] in EDGE_CLASSES, "edge class required")
        _require(row["from_ref"] in assumptions or row["from_ref"] in outputs, "edge source unresolved")
        _require(row["to_ref"] in assumptions or row["to_ref"] in outputs, "edge target unresolved")
        _require(row["production_relationship"] is False, "no Relationship promotion")
        refs(row["source_refs"])
    _require(audit["corroboration_policy"] == "SAME_ORIGIN_ASSETS_AND_DEPENDENT_OUTPUTS_NOT_INDEPENDENT_CONFIRMATIONS", "no transitive confidence")
    _require(audit["error_interpretation"] == "MODEL_ERROR_IS_NOT_EVIDENCE_OF_BAD_FAITH", "error not dishonesty")
    for row in audit["dimension_mapping_candidates"]:
        _require(row["current_state_claim"] is False, "projection is not World State")
        refs(row["source_refs"])
    _require(set(audit["human_review_questions"]) == {"analysis", "projection_inventory", "assumption_audit", "historical_backtest", "dependency_map"}, "separate human review required")
    for row in audit["human_review_questions"].values():
        _require(row["decision"] is None and row["permitted_decisions"] == ["ACCEPT", "DEFER", "REJECT"], "no automatic review")

    analysis = package["analysis_candidate"]
    review = analysis["review"]
    _require(review["review_state"] == "DRAFT", "Analysis remains draft")
    _require(review["what_happened"]["actuals"] == [], "no future projections in actuals")
    _require(review["what_surprised"]["status"] == "NOT_ESTABLISHED" and review["what_surprised"]["comparisons"] == [], "model revision not surprise")
    _require(review["what_moved"] == [], "no invented market movement")
    _require(review["second_order_effects"]["status"] == "NOT_ESTABLISHED", "no projected effects as observed")
    _require(review["what_appears_connected"]["causal_status"] == "NOT_A_CAUSAL_CLAIM", "no causal promotion")
    for key, part in (("inventory_fingerprint", inventory), ("audit_fingerprint", audit), ("evidence_manifest_fingerprint", manifest), ("extension_fingerprint", package["extension_candidate"])):
        _require(analysis["official_projection_review"][key] == part["semantic_fingerprint"], "linked candidate mismatch")
    extension = package["extension_candidate"]
    _require(extension["production_schema_change"] is False and extension["production_admission_permitted"] is False, "extension is candidate only")
    _require(set(extension["required_sections"]) == {"projection_framework", "projection_outputs", "model_assumptions", "sensitivity_cases", "assumption_audit", "comparison_baseline", "limitations"}, "extension sections")
    _require(set(extension["audit_axes"]) == set(AUDIT_AXES) and set(extension["epistemic_classes"]) == CLASSES, "extension taxonomy mismatch")
    provenance = analysis["model_provenance"]
    _require(provenance["factual_evidence_status"] == "MODEL_OUTPUT_IS_NOT_FACTUAL_CORROBORATION", "model is not evidence")
    _require(all(provenance.get(k) for k in ("execution_surface", "model_identity", "model_version", "reasoning_configuration", "procedure_version")), "fail-honest model provenance required")
    if any(provenance[k] != "UNAVAILABLE" for k in ("model_identity", "model_version", "reasoning_configuration")):
        _require(provenance.get("authoritative_runtime_metadata_ref"), "runtime model provenance cannot be guessed")
    return {"status": "REVIEW_PENDING", "projection_count": len(outputs), "assumption_count": len(assumptions), "asset_manifest_sha256": manifest["asset_manifest_sha256"], "package_fingerprint": fingerprint({key: part["semantic_fingerprint"] for key, part in sorted(package.items())}), "write_targets": [], "public_projection_permitted": False}


def inspect_step14d(root: Path) -> dict[str, Any]:
    """Read-only native-contract and hash check over the current repository."""
    before = protected_file_hashes(root)
    load = lambda relative: json.loads((root / relative).read_text(encoding="utf-8"))
    package = {key: load("data/analysis/" + name) for key, name in FILES.items()}
    result = validate_package(package)
    manifest = package["evidence_manifest"]
    canonical = load("data/canonical/registry.json")
    sources = load("data/sources/registry.json")
    _require({(r["layer"], r["object_id"]) for r in manifest["governed_object_pins"]} == {("canonical", "WSO-FIS-AU-IGR-20260921"), ("sources", "WSSRC-FIS-030"), ("sources", "WSSRC-FIS-031")}, "exact IGR identity/source pins required")
    # Whole-file hashes are historical transaction proof, not permanent limits
    # on legitimate unrelated population. Selected objects remain exact-pinned.
    for pin in manifest["governed_object_pins"]:
        population, key = (canonical["records"], "occurrence_id") if pin["layer"] == "canonical" else (sources["sources"], "source_id")
        selected = next((r for r in population if r[key] == pin["object_id"]), None)
        _require(selected and fingerprint(selected) == pin["object_sha256"], "selected governed object mismatch: " + pin["object_id"])
    occurrence = next((row for row in canonical["records"] if row["occurrence_id"] == "WSO-FIS-AU-IGR-20260921"), None)
    _require(occurrence and occurrence["series_id"] == "WSER-FIS-AU-IGR" and occurrence["lifecycle_status"] == "COMPLETED", "IGR identity/lifecycle unresolved")
    source_ids = {"WSSRC-FIS-030", "WSSRC-FIS-031"}
    for source_id in source_ids:
        source = next((row for row in sources["sources"] if row["source_id"] == source_id), None)
        _require(source and source["automated_monitoring_use"] == "MANUAL_ONLY_RIGHTS_HOLD" and source["monitoring_activation_status"] == "PRODUCTION_AUTOMATION_HOLD" and source["monitor_endpoints"] == [], "manual-only hold required")
    expectations = load("data/monitor/expectations.json")
    _require(not any(source_id in json.dumps(expectations) for source_id in source_ids), "no Treasury monitor route")
    candidate = package["analysis_candidate"]
    report = validate_analysis(load("data/analysis/schema.json"), {"evidence": candidate["candidate_local_evidence"]}, {"reviews": [candidate["review"]]}, canonical)
    _require(report.ok, "native Analysis validation: " + "; ".join(report.errors))
    from world_signals.official_projection_review import step14d_native_extension
    native_review = deepcopy(candidate["review"])
    native_review["official_projection_review"] = step14d_native_extension(package)
    extension_report = validate_analysis(load("data/analysis/schema.json"), {"evidence": candidate["candidate_local_evidence"]}, {"reviews": [native_review]}, canonical)
    _require(extension_report.ok, "native official-projection extension: " + "; ".join(extension_report.errors))
    _require(protected_file_hashes(root) == before, "read mutated protected inputs")
    return {**result, "mutation_check": "PASS", "native_analysis_candidate_check": "PASS", "native_official_projection_extension_check": "PASS", "protected_input_fingerprint": fingerprint(before), "historical_file_drift": sorted(p for p, digest in manifest["protected_input_hashes"].items() if before.get(p) != digest)}
