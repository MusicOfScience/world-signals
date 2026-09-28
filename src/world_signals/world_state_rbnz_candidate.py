"""Step 11A RBNZ candidate construction from the governed Analysis layer.

The builder creates only non-production, review-pending candidates.  It does
not admit an actor, component, snapshot or transaction and it does not create
Relationships from market observations.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .analysis import validate_analysis
from .world_state_actor import (
    build_actor_identity_admission_transaction,
    build_actor_identity_candidate,
    simulate_actor_identity_admission,
    validate_actor_identity_candidate,
)
from .world_state_history import fingerprint, validate_component_revision, validate_snapshot_candidate, with_object_fingerprint


ANALYSIS_ID = "WSAN-NZ-OCR-20260902-001"
OCCURRENCE_ID = "WSO-8df73c7804d45880"
EVIDENCE_IDS = (
    "WSEV-NZ-OCR-RBNZ-20260902",
    "WSEV-NZ-OCR-BT-20260902",
    "WSEV-NZ-OCR-REUTERS-20260902",
)
ACTOR_ID = "WSACT-RBNZ-202609-001"
MACRO_COMPONENT_ID = "WSDIM-MACRO-NZ-RBNZ-OCR-202609-001"
MARKET_COMPONENT_ID = "WSDIM-MARKETS-NZ-RBNZ-OCR-202609-001"
CONSTRUCTION_CUTOFF = "2026-09-28T00:00:00Z"
PROCEDURE_VERSION = "world-state-step11a-rbnz-candidate-v1"


class RbnzCandidateError(ValueError):
    """Raised when Step 11A cannot construct a bounded candidate."""


def _load(root: Path, relative: str) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def _utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise RbnzCandidateError(f"timestamp must be UTC: {value}")
    return parsed.astimezone(timezone.utc)


def _entry(layer: str, object_id: str, obj: dict[str, Any], revision_id: str | None = None) -> dict[str, Any]:
    return {
        "layer": layer,
        "object_id": object_id,
        "revision_id": revision_id,
        "object_sha256": fingerprint(obj),
        "object": deepcopy(obj),
    }


def _citation(entry: dict[str, Any], epistemic_class: str, **extra: Any) -> dict[str, Any]:
    value = {
        "layer": entry["layer"],
        "object_id": entry["object_id"],
        "revision_id": entry.get("revision_id"),
        "object_sha256": entry["object_sha256"],
        "epistemic_class": epistemic_class,
    }
    value.update(extra)
    return value


def _empty_domains() -> list[dict[str, str]]:
    return [
        {"domain": "OTHER_WORLD_STATE_DIMENSIONS", "state": "UNQUERIED"},
        {"domain": "ACTOR_STATE_ASSERTIONS", "state": "UNQUERIED"},
        {"domain": "IMPLEMENTATION_CLAIMS", "state": "UNQUERIED"},
        {"domain": "RELATIONSHIPS", "state": "QUERIED_EMPTY"},
        {"domain": "RISKS_REGIMES", "state": "QUERIED_EMPTY"},
        {"domain": "SCENARIOS", "state": "QUERIED_EMPTY"},
        {"domain": "FORECASTS", "state": "UNQUERIED"},
        {"domain": "OUTCOMES", "state": "QUERIED_EMPTY"},
        {"domain": "CANONICAL_HISTORICAL_AS_OF", "state": "UNSUPPORTED"},
    ]


def _model_provenance(manifest_sha256: str, output: dict[str, Any]) -> dict[str, Any]:
    return {
        "execution_surface": "Codex",
        "model_identity": "UNAVAILABLE",
        "model_version": "UNAVAILABLE",
        "version": "UNAVAILABLE",
        "reasoning_configuration": "UNAVAILABLE",
        "provenance_status": "RUNTIME_METADATA_UNAVAILABLE",
        "configuration": "Step 11A deterministic RBNZ candidate-construction procedure",
        "analytical_lens": "narrow monetary-policy and market-sensor assessment",
        "procedure_version": PROCEDURE_VERSION,
        "generated_at_utc": CONSTRUCTION_CUTOFF,
        "input_manifest_sha256": manifest_sha256,
        "output_fingerprint": fingerprint(output),
        "factual_evidence_status": "MODEL_OUTPUT_IS_NOT_FACTUAL_CORROBORATION",
    }


def _component_common(component_id: str, dimension: str, source_manifest_sha256: str, known_at: str, state_label: str, direction: str, confidence: str, scope: dict[str, Any], citations: list[dict[str, Any]], uncertainties: list[dict[str, Any]], limitations: list[str]) -> dict[str, Any]:
    return {
        "component_type": "DIMENSION_ASSESSMENT",
        "component_id": component_id,
        "revision_id": f"{component_id}-R1",
        "revision_number": 1,
        "previous_revision_id": None,
        "revision_kind": "INITIAL",
        "review_state": "UNDER_REVIEW",
        "lifecycle_state": "UNRESOLVED",
        "effective_at": "2026-09-02T02:00:00Z",
        "effective_date": "2026-09-02",
        "effective_time_precision": "UTC_INSTANT",
        "effective_time_basis": "RBNZ canonical decision release time; market reaction remains source-reported, not independently reconstructed.",
        "known_at_utc": known_at,
        "known_at_basis": "GOVERNED_ANALYSIS_OR_OFFICIAL_RELEASE_BOUNDARY",
        "reviewed_at_utc": None,
        "admitted_at_utc": None,
        "source_proposal_id": f"WS-STEP11A-{component_id}",
        "source_manifest_sha256": source_manifest_sha256,
        "review_transaction_id": None,
        "admission_transaction_id": None,
        "projection_transaction_id": None,
        "visibility": "INTERNAL_ONLY",
        "revision_reason": "Step 11A review-pending specimen; no production admission or public projection.",
        "dimension": dimension,
        "scope": scope,
        "state_label": state_label,
        "direction": direction,
        "persistence": "NOT_ASSESSED",
        "breadth": "NOT_ASSESSED",
        "qualitative_confidence": confidence,
        "supporting_citations": citations,
        "contradictory_citations": [],
        "uncertainties": uncertainties,
        "baseline_ref": None,
        "anomaly_refs": [],
        "prior_revision_ref": None,
        "transition_type": "INITIAL",
        "limitations": limitations,
        "object_sha256": None,
    }


def build_rbnz_candidate(root: Path, *, construction_cutoff_utc: str = CONSTRUCTION_CUTOFF) -> dict[str, Any]:
    cutoff = _utc(construction_cutoff_utc)
    if cutoff != _utc(CONSTRUCTION_CUTOFF):
        raise RbnzCandidateError("Step 11A retained package requires the explicit reproducible construction cutoff")
    schema = _load(root, "data/analysis/schema.json")
    evidence_dataset = _load(root, "data/analysis/evidence_registry.json")
    reviews_dataset = _load(root, "data/analysis/event_reviews.json")
    canonical = _load(root, "data/canonical/registry.json")
    report = validate_analysis(schema, evidence_dataset, reviews_dataset, canonical)
    if not report.ok:
        raise RbnzCandidateError("Analysis validation failed: " + "; ".join(report.errors))
    review = next((row for row in reviews_dataset["reviews"] if row.get("analysis_id") == ANALYSIS_ID), None)
    if review is None or review.get("review_state") != "REVIEWED_SAMPLE" or review.get("review_phase") != "POST_EVENT":
        raise RbnzCandidateError("reviewed RBNZ Analysis sample is unavailable")
    if _utc(review["analysis_as_of_utc"]) > cutoff:
        raise RbnzCandidateError("Analysis review is after the construction cutoff")
    evidence_by_id = {row["evidence_id"]: row for row in evidence_dataset["evidence"]}
    if any(identifier not in evidence_by_id for identifier in EVIDENCE_IDS):
        raise RbnzCandidateError("RBNZ evidence lineage is incomplete")
    occurrence = next((row for row in canonical["records"] if row.get("occurrence_id") == OCCURRENCE_ID), None)
    if occurrence is None:
        raise RbnzCandidateError("RBNZ canonical occurrence is unavailable")
    manifest = [
        _entry("ANALYSIS", ANALYSIS_ID, review),
        *[_entry("ANALYSIS_EVIDENCE", identifier, evidence_by_id[identifier]) for identifier in EVIDENCE_IDS],
        _entry("CANONICAL", OCCURRENCE_ID, occurrence),
    ]
    manifest.sort(key=lambda row: (row["layer"], row["object_id"], row.get("revision_id") or ""))
    manifest_sha256 = fingerprint(manifest)
    by_id = {row["object_id"]: row for row in manifest}
    analysis_ref = _citation(by_id[ANALYSIS_ID], "HYPOTHESIS", factual_claim=False, role="REVIEWED_ANALYSIS_SUBSTRATE")
    official_ref = _citation(by_id[EVIDENCE_IDS[0]], "FACTUAL_SOURCE", role="OFFICIAL_DECISION")
    benchmark_ref = _citation(by_id[EVIDENCE_IDS[1]], "FACTUAL_SOURCE", role="EXPECTATION_BENCHMARK", expectation_not_fact=True)
    reuters_ref = _citation(by_id[EVIDENCE_IDS[2]], "FACTUAL_SOURCE", role="MARKET_OBSERVATION_AND_ALTERNATIVE")
    macro_scope = {"jurisdictions": ["New Zealand"], "systems": ["RBNZ_OFFICIAL_CASH_RATE_DECISION"], "boundaries": ["2 September 2026 decision and stated forward path only"]}
    market_scope = {"jurisdictions": ["New Zealand"], "systems": ["TWO_YEAR_SWAP_RATE", "NZD_USD_SPOT"], "boundaries": ["source-reported immediate/same-session response; no independently reconstructed before values"]}
    macro_uncertainties = [
        {"type": "PROVENANCE_SOURCE", "status": "BOUNDED", "description": "The OCR level and change are supported by the official RBNZ release; benchmark and forward-path interpretation use distinct analytical sources.", "basis_refs": list(EVIDENCE_IDS)},
        {"type": "INSTITUTIONAL_AUTHORITY", "status": "BOUNDED", "description": "The official release supports what the RBNZ Committee decided and communicated; it does not prove later implementation or an actor-intent claim.", "basis_refs": [EVIDENCE_IDS[0]]},
        {"type": "INTERPRETIVE", "status": "BOUNDED", "description": "The headline hike matched consensus; the more-gradual-than-market-pricing classification is a reviewed interpretation, not an independently measured causal fact.", "basis_refs": [ANALYSIS_ID, EVIDENCE_IDS[1], EVIDENCE_IDS[2]]},
    ]
    market_uncertainties = [
        {"type": "MEASUREMENT", "status": "BOUNDED", "description": "Movements are source-reported change-and-endpoint measurements with null before values and no independent reconstruction.", "basis_refs": [ANALYSIS_ID, EVIDENCE_IDS[2]]},
        {"type": "TEMPORAL", "status": "BOUNDED", "description": "The measurement windows are immediate post-decision or same-session, not a high-frequency event study.", "basis_refs": [ANALYSIS_ID, EVIDENCE_IDS[2]]},
        {"type": "INTERPRETIVE", "status": "BOUNDED", "description": "Global oil and bond-market shocks and pre-existing NZD weakness remain alternative explanations; no causal Relationship is created.", "basis_refs": [ANALYSIS_ID, EVIDENCE_IDS[2]]},
    ]
    macro_output = {"state_label": "POLICY_RATE_INCREASED_WITH_MORE_GRADUAL_FORWARD_PATH", "direction": "UPWARD", "confidence": "MEDIUM"}
    macro = _component_common(MACRO_COMPONENT_ID, "MACROECONOMIC_FINANCIAL_CONDITIONS", manifest_sha256, "2026-09-02T02:00:00Z", macro_output["state_label"], "UPWARD", "MEDIUM", macro_scope, [official_ref, benchmark_ref, reuters_ref, analysis_ref], macro_uncertainties, [
        "The 25bp increase to 2.75 percent was expected; the candidate does not present it as a surprise.",
        "The forward-path comparison is bounded to the reviewed RBNZ-versus-market-pricing proposition.",
        "No actor assertion, implementation claim, forecast or global macro assessment is created.",
    ])
    macro["expectation_baselines"] = [
        {"baseline_id": "WS-STEP11A-RBNZ-ECONOMIST-CONSENSUS", "basis": "OFFICIAL_REFERENCE", "label": "27 of 31 economists expected 25bp to 2.75 percent", "reference_ids": [EVIDENCE_IDS[1]], "used_for": "headline decision comparison"},
        {"baseline_id": "WS-STEP11A-RBNZ-MARKET-PATH", "basis": "MARKET_MEASUREMENT", "label": "market pricing of faster tightening and approximately 3.5 percent peak", "reference_ids": [EVIDENCE_IDS[2]], "used_for": "forward-path comparison", "limitations": ["not a reconstructed pre-event curve"]},
    ]
    macro["model_provenance"] = _model_provenance(manifest_sha256, macro_output)
    macro = with_object_fingerprint(macro)
    market_measurements = deepcopy(review["what_moved"])
    market_output = {"state_label": "SHORT_RATE_AND_FX_PRICING_REPRICED_LOWER_AFTER_POLICY_PATH_SURPRISE", "direction": "DOWNWARD", "confidence": "MEDIUM"}
    market = _component_common(MARKET_COMPONENT_ID, "MARKETS_AS_SENSORS", manifest_sha256, review["analysis_as_of_utc"], market_output["state_label"], "DOWNWARD", "MEDIUM", market_scope, [reuters_ref, analysis_ref, official_ref], market_uncertainties, [
        "The market records are sensors of expectations and positioning, not automatic causal proof.",
        "Before values are unavailable; reported endpoints and changes are preserved without reconstruction.",
        "The observed association remains in the Analysis substrate; no production Relationship or transmission edge is created.",
    ])
    market["market_measurements"] = market_measurements
    market["analytical_association"] = {
        "interaction_type": review["what_appears_connected"]["interaction_type"],
        "causal_status": review["what_appears_connected"]["causal_status"],
        "relationship_ownership": "ANALYSIS_SUBSTRATE_NOT_WORLD_STATE_RELATIONSHIP",
        "alternative_explanations": deepcopy(review["alternative_explanations"]),
    }
    market["model_provenance"] = _model_provenance(manifest_sha256, market_output)
    market = with_object_fingerprint(market)
    actor_provenance = [by_id[EVIDENCE_IDS[0]]]
    actor = build_actor_identity_candidate(
        actor_id=ACTOR_ID,
        canonical_label="Reserve Bank of New Zealand",
        actor_type="CENTRAL_BANK",
        aliases=["RBNZ", "Te Pūtea Matua"],
        jurisdiction=["New Zealand"],
        effective_from="2026-09-02T02:00:00Z",
        provenance_refs=actor_provenance,
    )
    actor_errors = validate_actor_identity_candidate(actor)
    if actor_errors:
        raise RbnzCandidateError("actor identity candidate failed validation: " + "; ".join(actor_errors))
    refs = [
        {"component_type": row["component_type"], "component_id": row["component_id"], "revision_id": row["revision_id"], "object_sha256": row["object_sha256"]}
        for row in (macro, market)
    ]
    snapshot = with_object_fingerprint({
        "snapshot_series_id": "WSSNAP-NZ-RBNZ-OCR-202609",
        "snapshot_revision_id": "WSSNAP-NZ-RBNZ-OCR-202609-R1",
        "revision_number": 1,
        "previous_snapshot_revision_id": None,
        "snapshot_kind": "COMPOSITIONAL_INDEX",
        "scope": {"jurisdictions": ["New Zealand"], "systems": ["RBNZ_OFFICIAL_CASH_RATE_DECISION", "TWO_YEAR_SWAP_RATE", "NZD_USD_SPOT"]},
        "knowledge_cutoff_utc": review["analysis_as_of_utc"],
        "effective_as_of_utc": review["canonical_release_utc"],
        "component_refs": refs,
        "upstream_refs": [official_ref, benchmark_ref, reuters_ref, analysis_ref],
        "source_manifest_sha256": manifest_sha256,
        "proposal_id": f"WS-STEP11A-RBNZ-{ANALYSIS_ID}",
        "candidate_review_id": "WS-STEP11A-RBNZ-CANDIDATE-REVIEW",
        "review_state": "CANDIDATE",
        "review_transaction_id": None,
        "admission_transaction_id": None,
        "limitations": [
            "Review-pending candidate only; not a production snapshot.",
            "Independent component candidates remain unadmitted and are not public.",
            "Market observations remain sensors and do not create causal transmission edges.",
            "Actor identity candidate is separate and remains unadmitted.",
        ],
        "empty_queried_domains": _empty_domains(),
        "lifecycle_state": "UNRESOLVED",
        "visibility": "INTERNAL_ONLY",
        "reviewer": {"reviewer_id": "STEP11A-CANDIDATE", "role": "review-pending"},
        "admitted_at_utc": None,
        "object_sha256": None,
    })
    component_index = {(row["component_type"], row["revision_id"]): row for row in (macro, market)}
    errors = validate_snapshot_candidate(snapshot, component_index=component_index)
    if errors:
        raise RbnzCandidateError("snapshot candidate failed validation: " + "; ".join(errors))
    actor_transaction = build_actor_identity_admission_transaction(
        actor,
        reviewer_id="operator-human-review-required",
        decided_at_utc=CONSTRUCTION_CUTOFF,
        admitted_at_utc=CONSTRUCTION_CUTOFF,
        pre_state_hashes={"actors": fingerprint({"actors": [], "relationships": []})},
        post_state_hashes={"actors": fingerprint({"actors": [actor], "relationships": []})},
        write_targets=["SIMULATION_ONLY:data/world_state/actor_registry.json"],
    )
    actor_simulation = simulate_actor_identity_admission(actor, actor_transaction)
    candidates = [macro, market]
    candidate_fingerprint = fingerprint({"actor": actor, "components": candidates, "snapshot": snapshot, "source_manifest_sha256": manifest_sha256}, exclude={"object_sha256"})
    package = {
        "package_type": "WORLD_STATE_STEP11A_RBNZ_CANDIDATE",
        "package_version": "0.1",
        "status": "REVIEW_PENDING",
        "preflight_classification": "READY_FOR_HUMAN_COMPONENT_REVIEW",
        "constructed_at_utc": CONSTRUCTION_CUTOFF,
        "knowledge_cutoff_utc": review["analysis_as_of_utc"],
        "analysis_id": ANALYSIS_ID,
        "analysis_review_as_of_utc": review["analysis_as_of_utc"],
        "source_manifest": manifest,
        "source_manifest_sha256": manifest_sha256,
        "candidate_semantic_fingerprint": candidate_fingerprint,
        "actor_identity_candidate": actor,
        "actor_identity_admission": {"status": "REVIEW_PENDING_UNADMITTED", "transaction": actor_transaction, "simulation": actor_simulation, "production_population_performed": False},
        "dimension_assessment_candidates": candidates,
        "actor_state_assertions": [],
        "implementation_claims": [],
        "relationships": [],
        "transmission_edges": [],
        "forecasts": [],
        "proposed_snapshot": {"status": "REVIEW_PENDING_CANDIDATE_ONLY", "snapshot": snapshot, "snapshot_semantic_fingerprint": fingerprint(snapshot, exclude={"object_sha256"})},
        "baseline_treatment": {"status": "EMBEDDED_ANALYSIS_BENCHMARKS_RETAINED_SEPARATELY", "standalone_baseline_candidates": [], "reason": "The economist consensus and market path are different comparison bases; no standalone baseline is admitted or invented."},
        "market_sensor_treatment": {"status": "PRESERVED_AS_MEASURED_SENSORS", "causal_relationship_created": False, "before_values_invented": False, "alternative_explanations_preserved": True},
        "known_empty_or_unsupported_domains": _empty_domains(),
        "gates": {
            "analysis_reviewed_and_hash_pinned": {"status": "PASS"},
            "narrow_component_scopes": {"status": "PASS"},
            "actor_identity_only_and_unadmitted": {"status": "PASS"},
            "implementation_and_actor_claims": {"status": "DEFER", "basis": "No governed Actor Registry admission; no claims are created."},
            "market_noncausal_boundary": {"status": "PASS"},
            "human_component_review": {"status": "DEFER", "basis": "Step 11A constructs review-pending candidates only."},
            "production_admission": {"status": "DEFER", "basis": "No Step 11B admission is performed."},
        },
        "production_state": {"actors": 0, "components": 1, "snapshots": 1, "admissions": 1, "writes": []},
        "visibility": "INTERNAL_ONLY",
        "public_projection_permitted": False,
        "limitations": [
            "This package is a review-pending second specimen, not production World State.",
            "Actor identity admission is a separate human-reviewed gate and remains unpopulated.",
            "No implementation claim is created because the actor is not admitted and the analysis does not establish implementation state.",
            "The Analysis review's observed association is not a production Relationship or transmission edge.",
            "No global macroeconomic or market assessment is asserted.",
        ],
    }
    return package


def validate_rbnz_candidate_package(package: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if package.get("package_type") not in {"WORLD_STATE_STEP11A_RBNZ_CANDIDATE", "WORLD_STATE_STEP11A1_RBNZ_CANDIDATE"}:
        errors.append("invalid Step 11A package type")
    if package.get("status") != "REVIEW_PENDING" or package.get("preflight_classification") != "READY_FOR_HUMAN_COMPONENT_REVIEW":
        errors.append("package must remain review pending and ready for human component review")
    if package.get("visibility") != "INTERNAL_ONLY" or package.get("public_projection_permitted") is not False:
        errors.append("package must remain internal and non-public")
    actor = package.get("actor_identity_candidate")
    errors.extend(validate_actor_identity_candidate(actor))
    if package.get("actor_identity_admission", {}).get("production_population_performed") is not False:
        errors.append("actor identity production population must remain false")
    candidates = package.get("dimension_assessment_candidates")
    if not isinstance(candidates, list) or len(candidates) != 2:
        errors.append("exactly two narrow dimension candidates are required")
    for candidate in candidates or []:
        errors.extend(validate_component_revision(candidate))
        if candidate.get("review_state") != "UNDER_REVIEW" or candidate.get("admitted_at_utc") is not None:
            errors.append(f"candidate {candidate.get('component_id')} must remain unadmitted")
    snapshot = package.get("proposed_snapshot", {}).get("snapshot")
    if not isinstance(snapshot, dict):
        errors.append("pending snapshot candidate is required")
    else:
        index = {(row.get("component_type"), row.get("revision_id")): row for row in candidates or []}
        errors.extend(validate_snapshot_candidate(snapshot, component_index=index))
        if package["proposed_snapshot"].get("snapshot_semantic_fingerprint") != fingerprint(snapshot, exclude={"object_sha256"}):
            errors.append("pending snapshot fingerprint mismatch")
    manifest = package.get("source_manifest")
    if not isinstance(manifest, list) or package.get("source_manifest_sha256") != fingerprint(manifest):
        errors.append("source manifest fingerprint mismatch")
    for entry in manifest or []:
        if entry.get("object_sha256") != fingerprint(entry.get("object")):
            errors.append(f"source object hash mismatch: {entry.get('object_id')}")
    if package.get("actor_state_assertions") != [] or package.get("implementation_claims") != [] or package.get("relationships") != [] or package.get("transmission_edges") != [] or package.get("forecasts") != []:
        errors.append("Step 11A package must not create actor claims, implementation claims, relationships or forecasts")
    if package.get("production_state", {}).get("writes") != []:
        errors.append("Step 11A package must have no production write targets")
    return errors


def build_corrected_rbnz_candidate(root: Path) -> dict[str, Any]:
    """Build the Step 11A.1 temporal successor without rewriting Step 11A."""
    original = build_rbnz_candidate(root)
    corrected = deepcopy(original)
    corrected["package_type"] = "WORLD_STATE_STEP11A1_RBNZ_CANDIDATE"
    corrected["correction_lineage"] = {
        "corrects_package": "data/world_state_audit/STEP11A_RBNZ_CANDIDATE_REVIEW_PENDING.json",
        "corrected_successor": "data/world_state_audit/STEP11A1_RBNZ_CANDIDATE_REVIEW_PENDING_CORRECTED.json",
        "predecessor_candidate_fingerprint": original["candidate_semantic_fingerprint"],
        "predecessor_source_manifest_sha256": original["source_manifest_sha256"],
        "correction_type": "KNOWN_AT_AND_EFFECTIVE_TIME_PRECISION_AND_ACTOR_IDENTITY_BOUNDARY",
        "human_review_dispositions": {
            "MACROECONOMIC_FINANCIAL_CONDITIONS": "DEFER_TEMPORAL_CORRECTION",
            "MARKETS_AS_SENSORS": "DEFER_TEMPORAL_CORRECTION",
            "ACTOR_IDENTITY": "DEFER_IDENTITY_TEMPORAL_CONTRACT",
        },
        "reason": "The comparative policy-path proposition was not admissibly known at the official release instant; source-reported market windows do not establish an exact movement instant; identity evidence does not establish institutional founding time.",
    }
    candidates = {row["component_id"]: row for row in corrected["dimension_assessment_candidates"]}
    macro = candidates[MACRO_COMPONENT_ID]
    macro["known_at_utc"] = "2026-09-05T14:40:00Z"
    macro["known_at_basis"] = "ANALYSIS_REVIEW_BOUNDARY_FOR_COMPARATIVE_FORWARD_PATH_PROPOSITION"
    macro["proposition_parts"] = [
        {
            "part": "OFFICIAL_DECISION",
            "label": "POLICY_RATE_INCREASED_TO_2_75_PERCENT",
            "known_at_utc": "2026-09-02T02:00:00Z",
            "basis": "PRIMARY_OFFICIAL_RBNZ_RELEASE",
        },
        {
            "part": "COMPARATIVE_FORWARD_PATH",
            "label": "MORE_GRADUAL_THAN_MARKET_PRICING",
            "known_at_utc": "2026-09-05T14:40:00Z",
            "basis": "REVIEWED_ANALYSIS_COMPARISON",
        },
    ]
    macro["object_sha256"] = None
    candidates[MACRO_COMPONENT_ID] = with_object_fingerprint(macro)
    market = candidates[MARKET_COMPONENT_ID]
    market["effective_at"] = None
    market["effective_time_precision"] = "CIVIL_DATE"
    market["effective_time_basis"] = "Source-reported immediate post-decision and same-session windows; civil date is the narrowest executable production-history precision and no movement onset is manufactured."
    market["effective_window"] = {
        "anchor_event_at_utc": "2026-09-02T02:00:00Z",
        "description": "source-reported immediate post-decision / same-session movement",
        "exact_start_at_utc": None,
        "exact_end_at_utc": None,
    }
    market["object_sha256"] = None
    candidates[MARKET_COMPONENT_ID] = with_object_fingerprint(market)
    corrected["dimension_assessment_candidates"] = [candidates[MACRO_COMPONENT_ID], candidates[MARKET_COMPONENT_ID]]
    actor = corrected["actor_identity_candidate"]
    actor["effective_from"] = None
    actor["effective_from_precision"] = "UNKNOWN"
    actor["identity_known_at_utc"] = "2026-09-05T14:40:00Z"
    actor["identity_known_at_basis"] = "ANALYSIS_REVIEW_BOUNDARY_FOR_IDENTITY_PROVENANCE"
    actor["object_sha256"] = None
    actor = with_object_fingerprint(actor)
    corrected["actor_identity_candidate"] = actor
    actor_transaction = build_actor_identity_admission_transaction(
        actor,
        reviewer_id="operator-human-review-required",
        decided_at_utc=CONSTRUCTION_CUTOFF,
        admitted_at_utc=CONSTRUCTION_CUTOFF,
        pre_state_hashes={"actors": fingerprint({"actors": [], "relationships": []})},
        post_state_hashes={"actors": fingerprint({"actors": [actor], "relationships": []})},
        write_targets=["SIMULATION_ONLY:data/world_state/actor_registry.json"],
    )
    corrected["actor_identity_admission"] = {
        "status": "REVIEW_PENDING_UNADMITTED",
        "transaction": actor_transaction,
        "simulation": simulate_actor_identity_admission(actor, actor_transaction),
        "production_population_performed": False,
    }
    snapshot = corrected["proposed_snapshot"]["snapshot"]
    snapshot["component_refs"] = [
        {"component_type": row["component_type"], "component_id": row["component_id"], "revision_id": row["revision_id"], "object_sha256": row["object_sha256"]}
        for row in corrected["dimension_assessment_candidates"]
    ]
    snapshot["effective_as_of_utc"] = None
    snapshot["effective_date"] = "2026-09-02"
    snapshot["effective_time_precision"] = "CIVIL_DATE"
    snapshot["effective_time_basis"] = "The two candidates share a civil-date decision context, but the market movement window has no exact onset; this pending index does not claim a single effective instant."
    snapshot["object_sha256"] = None
    corrected["proposed_snapshot"]["snapshot"] = with_object_fingerprint(snapshot)
    corrected["proposed_snapshot"]["snapshot_semantic_fingerprint"] = fingerprint(corrected["proposed_snapshot"]["snapshot"], exclude={"object_sha256"})
    corrected["correction_review"] = {
        "status": "REVIEW_PENDING",
        "component_readiness": {
            "MACROECONOMIC_FINANCIAL_CONDITIONS": "READY_FOR_HUMAN_COMPONENT_REVIEW",
            "MARKETS_AS_SENSORS": "READY_FOR_HUMAN_COMPONENT_REVIEW",
            "ACTOR_IDENTITY": "DEFER_IDENTITY_TEMPORAL_CONTRACT",
        },
        "production_admission_performed": False,
        "write_targets": [],
        "public_projection_permitted": False,
    }
    corrected["candidate_semantic_fingerprint"] = fingerprint({
        "actor": actor,
        "components": corrected["dimension_assessment_candidates"],
        "snapshot": corrected["proposed_snapshot"]["snapshot"],
        "source_manifest_sha256": corrected["source_manifest_sha256"],
    }, exclude={"object_sha256"})
    return corrected


def validate_corrected_rbnz_candidate_package(package: dict[str, Any]) -> list[str]:
    errors = validate_rbnz_candidate_package(package)
    if package.get("package_type") != "WORLD_STATE_STEP11A1_RBNZ_CANDIDATE":
        errors.append("corrected Step 11A.1 package type is required")
    lineage = package.get("correction_lineage")
    if not isinstance(lineage, dict) or lineage.get("predecessor_candidate_fingerprint") != "455ac3d2402ac7370fe6b4a4b5b69fbc666183dd57a191c3da23525a85b3dc39":
        errors.append("original Step 11A fingerprint must be preserved in correction lineage")
    candidates = {row.get("component_id"): row for row in package.get("dimension_assessment_candidates", [])}
    macro = candidates.get(MACRO_COMPONENT_ID, {})
    if macro.get("known_at_utc") != "2026-09-05T14:40:00Z":
        errors.append("comparative Macro candidate must use the Analysis review boundary")
    market = candidates.get(MARKET_COMPONENT_ID, {})
    if market.get("effective_at") is not None or market.get("effective_time_precision") != "CIVIL_DATE":
        errors.append("market candidate must use executable civil-date precision")
    actor = package.get("actor_identity_candidate", {})
    if actor.get("effective_from") is not None or actor.get("effective_from_precision") != "UNKNOWN":
        errors.append("actor identity must retain unknown effective-from explicitly")
    if actor.get("identity_known_at_utc") != "2026-09-05T14:40:00Z":
        errors.append("actor identity known-at boundary is missing")
    if package.get("source_manifest_sha256") != "b5eecfedcc9b0d6ae6572e52b394e9157116ced7d8d8393c9e8189b6300ba8d4":
        errors.append("governed source manifest unexpectedly changed")
    return errors
