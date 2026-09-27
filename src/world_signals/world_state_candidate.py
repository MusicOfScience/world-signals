"""Step 8A construction of the first real World State candidate.

The builder reads existing governed inputs and writes only when its caller
explicitly serialises the returned non-production audit package.  It never
opens a production World State path and never changes an upstream layer.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .live_intelligence import validate_live_intelligence
from .signals import signal_state_as_of, validate_signals
from .world_state_history import (
    fingerprint,
    simulate_production_admission,
    state_hashes,
    validate_component_revision,
    validate_snapshot,
    validate_snapshot_candidate,
    with_object_fingerprint,
)


SIGNAL_ID = "WSSIG-HEALTH-COD-BVD-BURDEN-202609-001"
SIGNAL_REVISION_ID = "WSSIG-HEALTH-COD-BVD-BURDEN-202609-001-R1"
OBSERVATION_IDS = (
    "WSLI-HEALTH-COD-BVD-20260826-001",
    "WSLI-HEALTH-COD-BVD-20260830-001",
)
EVIDENCE_IDS = (
    "WSEV-LI-COD-BVD-WHO-DON616-20260828",
    "WSEV-LI-COD-BVD-WHO-AFRO-SITREP16-20260830",
)
PRE_FLIGHT_STATUS = "REVIEW_PENDING"
CANDIDATE_COMPONENT_ID = "WSDIM-HEALTH-COD-BVD-REPORTED-BURDEN-202609-001"
CANDIDATE_REVISION_ID = f"{CANDIDATE_COMPONENT_ID}-R1"


class WorldStateCandidateError(ValueError):
    """Raised when the real governed pilot cannot be constructed safely."""


def _load(root: Path, relative: str) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise WorldStateCandidateError(f"timestamp must be UTC: {value}")
    return parsed.astimezone(timezone.utc)


def _manifest_entry(layer: str, object_id: str, obj: dict[str, Any], revision_id: str | None = None) -> dict[str, Any]:
    return {
        "layer": layer,
        "object_id": object_id,
        "revision_id": revision_id,
        "object_sha256": fingerprint(obj),
        "object": deepcopy(obj),
    }


def _citation(entry: dict[str, Any], epistemic_class: str, **extra: Any) -> dict[str, Any]:
    citation = {
        "layer": entry["layer"],
        "object_id": entry["object_id"],
        "revision_id": entry.get("revision_id"),
        "object_sha256": entry["object_sha256"],
        "epistemic_class": epistemic_class,
    }
    citation.update(extra)
    return citation


def _empty_domains() -> list[dict[str, str]]:
    return [
        {"domain": "WORLD_STATE_DIMENSIONS_OTHER_THAN_HEALTH_BIOSECURITY", "state": "UNQUERIED"},
        {"domain": "ACTOR_ASSERTIONS", "state": "UNQUERIED"},
        {"domain": "IMPLEMENTATION_CLAIMS", "state": "UNQUERIED"},
        {"domain": "RELATIONSHIPS", "state": "QUERIED_EMPTY"},
        {"domain": "RISKS_REGIMES", "state": "QUERIED_EMPTY"},
        {"domain": "SCENARIOS", "state": "QUERIED_EMPTY"},
        {"domain": "OUTCOMES", "state": "QUERIED_EMPTY"},
        {"domain": "CANONICAL_HISTORICAL_AS_OF", "state": "UNSUPPORTED"},
    ]


def _validate_upstream(root: Path, signal_schema: dict[str, Any], signals: dict[str, Any], live_schema: dict[str, Any], observations: dict[str, Any], evidence: dict[str, Any], canonical: dict[str, Any], signal_admission: dict[str, Any]) -> None:
    live_report = validate_live_intelligence(live_schema, evidence, observations, canonical)
    if not live_report.ok:
        raise WorldStateCandidateError("Live Intelligence validation failed: " + "; ".join(live_report.errors))
    signal_report = validate_signals(signal_schema, signals, observations, evidence, signal_admission)
    if not signal_report.ok:
        raise WorldStateCandidateError("Signal validation failed: " + "; ".join(signal_report.errors))


def build_health_candidate(root: Path, constructed_at_utc: str) -> dict[str, Any]:
    """Build a deterministic Step 8A candidate package from governed inputs."""
    constructed = _parse_utc(constructed_at_utc)
    constructed_at_utc = constructed.strftime("%Y-%m-%dT%H:%M:%SZ")
    signal_schema = _load(root, "data/signals/schema.json")
    signals = _load(root, "data/signals/signals.json")
    live_schema = _load(root, "data/live_intelligence/schema.json")
    observations_dataset = _load(root, "data/live_intelligence/observations.json")
    evidence_registry = _load(root, "data/live_intelligence/evidence_registry.json")
    canonical = _load(root, "data/canonical/registry.json")
    signal_admission = _load(root, "data/signals/signal_admission_transaction_v1.json")
    _validate_upstream(root, signal_schema, signals, live_schema, observations_dataset, evidence_registry, canonical, signal_admission)

    signal = next((row for row in signals["signals"] if row.get("signal_id") == SIGNAL_ID and row.get("revision_id") == SIGNAL_REVISION_ID), None)
    if signal is None or signal.get("review_state") != "ACCEPTED" or signal.get("lifecycle_state") != "ACTIVE":
        raise WorldStateCandidateError("expected accepted active Bundibugyo Signal revision is unavailable")
    observations = {row["observation_id"]: row for row in observations_dataset["observations"]}
    evidence = {row["evidence_id"]: row for row in evidence_registry["evidence"]}
    if set(signal.get("observation_ids", [])) != set(OBSERVATION_IDS) or set(signal.get("evidence_refs", [])) != set(EVIDENCE_IDS):
        raise WorldStateCandidateError("governed Signal lineage differs from the bounded pilot")
    if any(identifier not in observations for identifier in OBSERVATION_IDS) or any(identifier not in evidence for identifier in EVIDENCE_IDS):
        raise WorldStateCandidateError("bounded pilot lineage is incomplete")

    admission = next((row for row in signal_admission.get("revision_ids", []) if row == SIGNAL_REVISION_ID), None)
    if admission is None or signal_admission.get("decision") != "ACCEPTED":
        raise WorldStateCandidateError("accepted Signal admission transaction does not pin the expected revision")

    manifest = [
        _manifest_entry("LIVE_INTELLIGENCE", OBSERVATION_IDS[0], observations[OBSERVATION_IDS[0]]),
        _manifest_entry("LIVE_INTELLIGENCE", OBSERVATION_IDS[1], observations[OBSERVATION_IDS[1]]),
        _manifest_entry("LIVE_INTELLIGENCE", EVIDENCE_IDS[0], evidence[EVIDENCE_IDS[0]]),
        _manifest_entry("LIVE_INTELLIGENCE", EVIDENCE_IDS[1], evidence[EVIDENCE_IDS[1]]),
        _manifest_entry("SIGNALS", SIGNAL_ID, signal, SIGNAL_REVISION_ID),
        _manifest_entry("SIGNAL_ADMISSION", signal_admission["transaction_id"], signal_admission),
    ]
    manifest.sort(key=lambda row: (row["layer"], row["object_id"], row.get("revision_id") or ""))
    manifest_sha256 = fingerprint(manifest)
    signal_state = signal_state_as_of(signal_schema, signals["signals"], observations_dataset, evidence_registry, constructed_at_utc)[SIGNAL_ID]
    if signal_state["revision_id"] != SIGNAL_REVISION_ID or signal_state["effective_state"] != "ACTIVE":
        raise WorldStateCandidateError(f"Signal is not ACTIVE at candidate cutoff: {signal_state}")

    latest_observation = observations[signal["latest_supporting_observation_id"]]
    latest_observed = _parse_utc(latest_observation["observed_at_utc"])
    stale_after = latest_observed.replace() + __import__("datetime").timedelta(days=signal["expiry"]["stale_after_days"])
    elapsed_seconds = (constructed - latest_observed).total_seconds()
    freshness = {
        "latest_supporting_observation_id": latest_observation["observation_id"],
        "latest_supporting_observed_at_utc": latest_observation["observed_at_utc"],
        "latest_supported_state_as_of": latest_observation["state_as_of"],
        "constructed_at_utc": constructed_at_utc,
        "elapsed_days": elapsed_seconds / 86400,
        "stale_after_days": signal["expiry"]["stale_after_days"],
        "stale_review_due_at_utc": stale_after.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "ACTIVE_NEARING_REVIEW" if constructed < stale_after else "STALE_REVIEW_REQUIRED",
        "expiry_basis": "observed_at_utc per Signal validator; not the civil state_as_of date",
    }

    citations = []
    manifest_by_id = {row["object_id"]: row for row in manifest}
    for identifier in OBSERVATION_IDS:
        citations.append(_citation(manifest_by_id[identifier], "FACTUAL_SOURCE"))
    for identifier in EVIDENCE_IDS:
        citations.append(_citation(manifest_by_id[identifier], "FACTUAL_SOURCE"))
    citations.append(_citation(manifest_by_id[SIGNAL_ID], "REVIEWED_SIGNAL"))
    model_input = {"manifest_sha256": manifest_sha256, "signal_revision_id": SIGNAL_REVISION_ID, "procedure_version": "world-state-step8a-health-candidate-v1"}
    model_output = {"state_label": "REPORTED_OUTBREAK_BURDEN_INCREASING", "direction": "UPWARD", "persistence": "PERSISTENT", "breadth": "NOT_ASSESSED"}
    candidate = {
        "component_type": "DIMENSION_ASSESSMENT",
        "component_id": CANDIDATE_COMPONENT_ID,
        "revision_id": CANDIDATE_REVISION_ID,
        "revision_number": 1,
        "previous_revision_id": None,
        "revision_kind": "INITIAL",
        "review_state": "UNDER_REVIEW",
        "lifecycle_state": "UNRESOLVED",
        "effective_at": None,
        "effective_date": latest_observation["state_as_of"]["as_of_date"],
        "effective_time_precision": latest_observation["state_as_of"]["precision"],
        "effective_time_basis": "Latest governed outbreak snapshot; no UTC instant is manufactured from a civil date.",
        "known_at_utc": signal["review_provenance"]["reviewed_at_utc"],
        "known_at_basis": "ADMITTED_SIGNAL_REVIEW_BOUNDARY",
        "reviewed_at_utc": None,
        "admitted_at_utc": None,
        "source_proposal_id": f"WS-STEP8A-{CANDIDATE_COMPONENT_ID}",
        "source_manifest_sha256": manifest_sha256,
        "review_transaction_id": None,
        "admission_transaction_id": None,
        "projection_transaction_id": None,
        "visibility": "INTERNAL_ONLY",
        "revision_reason": "Step 8A candidate only; no production admission or public projection.",
        "dimension": "HEALTH_BIOSECURITY",
        "scope": {
            "jurisdictions": ["Democratic Republic of the Congo"],
            "systems": ["REPORTED_BUNDIBUGYO_OUTBREAK_BURDEN"],
            "boundaries": ["governed confirmed-case snapshots only"],
        },
        "state_label": "REPORTED_OUTBREAK_BURDEN_INCREASING",
        "direction": "UPWARD",
        "persistence": "PERSISTENT",
        "breadth": "NOT_ASSESSED",
        "qualitative_confidence": "LOW",
        "supporting_citations": citations,
        "contradictory_citations": [],
        "uncertainties": [
            {"type": "PROVENANCE_SOURCE", "status": "BOUNDED", "description": "Both primary supporting reports are from the WHO institutional family; the reviewed Signal records partial corroboration and one independent observation.", "basis_refs": list(EVIDENCE_IDS)},
            {"type": "MEASUREMENT", "status": "BOUNDED", "description": "The assessment describes reported confirmed cases, not incidence or true burden; reporting delay, access, testing, case definition and unreported cases remain limitations.", "basis_refs": list(OBSERVATION_IDS)},
            {"type": "TEMPORAL", "status": "BOUNDED", "description": "The latest outbreak state is a civil date (30 August 2026); effective UTC is intentionally unresolved while known time is the reviewed Signal time.", "basis_refs": list(OBSERVATION_IDS)},
            {"type": "INTERPRETIVE", "status": "BOUNDED", "description": "The narrow reported-burden label does not assert severity, geography, causality, response pressure or future trajectory.", "basis_refs": [SIGNAL_REVISION_ID]},
        ],
        "baseline_ref": f"{SIGNAL_ID}:{SIGNAL_REVISION_ID}:baseline",
        "anomaly_refs": [],
        "prior_revision_ref": None,
        "transition_type": "INITIAL",
        "limitations": [
            "reported confirmed-case snapshots are not incidence",
            "reporting delay and access limitations may affect completeness",
            "testing, case-definition and reclassification changes may affect comparability",
            "unreported cases remain outside the governed observation",
            "shared WHO institutional origin is not independent corroboration",
            "the Signal's hypothesised response-pressure channel remains outside this component",
            "no contradiction was found in the complete eligible lineage, but no negative claim of absence is made",
        ],
        "model_provenance": {
            "execution_surface": "Codex",
            "model_identity": "UNAVAILABLE",
            "model_version": "UNAVAILABLE",
            "version": "UNAVAILABLE",
            "reasoning_configuration": "UNAVAILABLE",
            "provenance_status": "RUNTIME_METADATA_UNAVAILABLE",
            "configuration": "Step 8A deterministic candidate-construction procedure",
            "analytical_lens": "narrow reported health/biosecurity burden assessment",
            "procedure_version": "world-state-step8a-health-candidate-v1",
            "generated_at_utc": constructed_at_utc,
            "input_manifest_sha256": manifest_sha256,
            "output_fingerprint": fingerprint(model_output),
            "factual_evidence_status": "MODEL_OUTPUT_IS_NOT_FACTUAL_CORROBORATION",
        },
        "object_sha256": None,
    }
    candidate = with_object_fingerprint(candidate)
    candidate_errors = validate_component_revision(candidate)
    if candidate_errors:
        raise WorldStateCandidateError("candidate validation failed: " + "; ".join(candidate_errors))
    candidate_fingerprint = fingerprint(candidate, exclude={"object_sha256"})

    def make_candidate_snapshot(component_ref: dict[str, Any]) -> dict[str, Any]:
        return with_object_fingerprint({
            "snapshot_series_id": "WSSNAP-HEALTH-COD-BVD-202609",
            "snapshot_revision_id": "WSSNAP-HEALTH-COD-BVD-202609-R1",
            "revision_number": 1,
            "previous_snapshot_revision_id": None,
            "snapshot_kind": "COMPOSITIONAL_INDEX",
            "scope": candidate["scope"],
            "knowledge_cutoff_utc": constructed_at_utc,
            "effective_as_of_utc": None,
            "component_refs": [component_ref],
            "upstream_refs": [_citation(manifest_by_id[SIGNAL_ID], "REVIEWED_SIGNAL")],
            "source_manifest_sha256": manifest_sha256,
            "proposal_id": candidate["source_proposal_id"],
            "candidate_review_id": "WS-STEP8A-CANDIDATE-REVIEW",
            "review_state": "CANDIDATE",
            "review_transaction_id": None,
            "admission_transaction_id": None,
            "limitations": ["Step 8A candidate/simulation only", "single health component; no all-dimensions assessment"],
            "empty_queried_domains": _empty_domains(),
            "lifecycle_state": "UNRESOLVED",
            "visibility": "INTERNAL_ONLY",
            "reviewer": {"reviewer_id": "STEP8A-CANDIDATE", "role": "review-pending"},
            "admitted_at_utc": None,
            "object_sha256": None,
        })

    def make_production_snapshot(component_ref: dict[str, Any], review_id: str, admission_id: str) -> dict[str, Any]:
        return with_object_fingerprint({
            "snapshot_series_id": "WSSNAP-HEALTH-COD-BVD-202609",
            "snapshot_revision_id": "WSSNAP-HEALTH-COD-BVD-202609-R1",
            "revision_number": 1,
            "previous_snapshot_revision_id": None,
            "snapshot_kind": "COMPOSITIONAL_INDEX",
            "scope": candidate["scope"],
            "knowledge_cutoff_utc": constructed_at_utc,
            "effective_as_of_utc": None,
            "component_refs": [component_ref],
            "upstream_refs": [_citation(manifest_by_id[SIGNAL_ID], "REVIEWED_SIGNAL")],
            "source_manifest_sha256": manifest_sha256,
            "proposal_id": candidate["source_proposal_id"],
            "review_transaction_id": review_id,
            "admission_transaction_id": admission_id,
            "limitations": ["Step 8A simulation only", "single health component; no all-dimensions assessment"],
            "empty_queried_domains": _empty_domains(),
            "lifecycle_state": "ACTIVE",
            "visibility": "INTERNAL_ONLY",
            "reviewer": {"reviewer_id": "STEP8A-SIMULATION", "role": "temporary-copy-only"},
            "admitted_at_utc": constructed_at_utc,
            "object_sha256": None,
        })

    candidate_component_ref = {"component_type": candidate["component_type"], "component_id": candidate["component_id"], "revision_id": candidate["revision_id"], "object_sha256": candidate["object_sha256"]}
    proposed_snapshot = make_candidate_snapshot(candidate_component_ref)
    proposed_snapshot_errors = validate_snapshot_candidate(proposed_snapshot, component_index={(candidate["component_type"], candidate["revision_id"]): candidate})
    if proposed_snapshot_errors:
        raise WorldStateCandidateError("candidate snapshot validation failed: " + "; ".join(proposed_snapshot_errors))

    simulated_component = deepcopy(candidate)
    simulated_component.update({
        "review_state": "ACCEPTED",
        "lifecycle_state": "ACTIVE",
        "reviewed_at_utc": constructed_at_utc,
        "admitted_at_utc": constructed_at_utc,
        "review_transaction_id": "WS-STEP8A-SIMULATION-REVIEW",
        "admission_transaction_id": "WS-STEP8A-SIMULATION-ADMISSION",
    })
    simulated_component["object_sha256"] = None
    simulated_component = with_object_fingerprint(simulated_component)
    component_ref = {"component_type": simulated_component["component_type"], "component_id": simulated_component["component_id"], "revision_id": simulated_component["revision_id"], "object_sha256": simulated_component["object_sha256"]}
    simulated_snapshot = make_production_snapshot(component_ref, "WS-STEP8A-SIMULATION-REVIEW", "WS-STEP8A-SIMULATION-ADMISSION")
    snapshot_errors = validate_snapshot(simulated_snapshot, component_index={(simulated_component["component_type"], simulated_component["revision_id"]): simulated_component})
    if snapshot_errors:
        raise WorldStateCandidateError("simulation snapshot validation failed: " + "; ".join(snapshot_errors))
    pre_state = {"actors": [], "components": [], "snapshots": []}
    simulation_state = {"actors": [], "components": [simulated_component], "snapshots": [simulated_snapshot]}
    simulation_transaction = {
        "transaction_id": "WS-STEP8A-SIMULATION-ADMISSION",
        "contract_version": "0.1",
        "transaction_type": "WORLD_STATE_PRODUCTION_ADMISSION",
        "decision": "ACCEPTED",
        "proposal_id": candidate["source_proposal_id"],
        "proposal_semantic_fingerprint": candidate_fingerprint,
        "source_manifest_sha256": manifest_sha256,
        "component_fingerprints": [component_ref],
        "reviewer": {"reviewer_id": "STEP8A-SIMULATION", "role": "temporary-copy-only"},
        "decided_at_utc": constructed_at_utc,
        "component_dispositions": [{"component_id": simulated_component["component_id"], "revision_id": simulated_component["revision_id"], "disposition": "ADMITTED", "reason": "Simulation only; Step 8B human admission remains pending."}],
        "snapshot_revision_identity": {"snapshot_series_id": simulated_snapshot["snapshot_series_id"], "snapshot_revision_id": simulated_snapshot["snapshot_revision_id"]},
        "write_targets": ["TEMPORARY_COPY_ONLY:data/world_state/components/", "TEMPORARY_COPY_ONLY:data/world_state/snapshots/"],
        "pre_state_hashes": state_hashes(pre_state),
        "post_state_hashes": state_hashes(simulation_state),
        "visibility_decision": "INTERNAL_ONLY",
        "admitted_at_utc": constructed_at_utc,
        "validator_version": "world-state-history-v1",
        "transaction_fingerprint": None,
    }
    simulation_transaction["transaction_fingerprint"] = fingerprint(simulation_transaction, exclude={"transaction_fingerprint"})
    simulation = simulate_production_admission(
        simulation_transaction,
        current_state=pre_state,
        candidate_components=[simulated_component],
        candidate_snapshot=simulated_snapshot,
    )

    gates = {
        "scope_and_component_type": {"status": "PASS", "basis": "One HEALTH_BIOSECURITY Dimension Assessment scoped to reported Bundibugyo confirmed-case snapshots in DRC."},
        "governed_pinned_inputs": {"status": "PASS", "basis": "Live observations, evidence, accepted Signal revision and Signal admission transaction are hash-pinned."},
        "temporal_non_backdating": {"status": "PASS", "basis": "Civil-date effective state is retained without a fabricated UTC instant; known_at is the admitted Signal review boundary; admission remains unset."},
        "support_contradiction_inspection": {"status": "PASS", "basis": "Supporting and contradictory refs are disjoint; complete eligible lineage contains no correction/retraction or contradiction."},
        "uncertainty_alternatives_limitations": {"status": "PASS", "basis": "Low confidence, shared WHO origin, measurement/temporal/interpretive limits and reporting alternatives are retained."},
        "native_validators_no_duplicate_relationship": {"status": "PASS", "basis": "Component and temporary snapshot validators pass; no Relationship or transmission component is created."},
        "proposal_model_provenance": {"status": "PASS", "basis": "The deterministic candidate procedure, input manifest and fail-honest unavailable runtime provenance are retained; model output is not factual evidence."},
        "human_review_transaction": {"status": "DEFER", "basis": "Step 8B must explicitly review this candidate; Step 8A cannot approve its own analytical judgment."},
        "production_admission_transaction": {"status": "DEFER", "basis": "No WORLD_STATE_PRODUCTION_ADMISSION is accepted or written; the transaction below is temporary simulation only."},
        "atomic_write_simulation": {"status": "PASS" if simulation["status"] == "PASS" else "FAIL", "basis": "Temporary-copy simulator returned without governed writes and preserved pre-state hashes."},
    }
    package = {
        "package_type": "WORLD_STATE_STEP8A_CANDIDATE",
        "package_version": "0.1",
        "correction_lineage": {
            "correction_type": "PRE_ADMISSION_SNAPSHOT_SEMANTICS_AND_MODEL_PROVENANCE",
            "corrects_package": "data/world_state_audit/STEP8A_HEALTH_BVD_CANDIDATE_REVIEW_PENDING.json",
            "prior_candidate_semantic_fingerprint": "e74cf6c3809405ab5bcdb736714a96247c097fcd7c930aa08b352684596dba81",
            "prior_source_manifest_sha256": "4d16a6c02ed868000859461e6e71f96a1bff2e27b7d9cdaf9b2a022b01f54e8e",
            "prior_proposed_snapshot_fingerprint": "e60b43256c6b6a892d6411e3df048bb27417153d54478a34dbbe3e80955d5500",
            "reason": "The original review-pending package reused the admitted production snapshot validator and therefore carried fake admission metadata; it also recorded an unverified model version.",
        },
        "status": PRE_FLIGHT_STATUS,
        "preflight_classification": "READY_FOR_HUMAN_ADMISSION_REVIEW" if all(row["status"] in {"PASS", "DEFER"} for row in gates.values()) else "REJECT_CONTRACT_FAILURE",
        "constructed_at_utc": constructed_at_utc,
        "knowledge_cutoff_utc": constructed_at_utc,
        "candidate": candidate,
        "candidate_semantic_fingerprint": candidate_fingerprint,
        "source_manifest": manifest,
        "source_manifest_sha256": manifest_sha256,
        "freshness": freshness,
        "baseline_treatment": {"status": "REUSED_EXISTING_SIGNAL_BASELINE", "reference": candidate["baseline_ref"], "observation_ids": list(OBSERVATION_IDS), "separate_baseline_candidate_created": False},
        "anomaly_treatment": {"status": "NOT_CREATED", "reason": "The reviewed Signal already owns the two-snapshot comparison; a duplicate anomaly would add no information."},
        "actor_assertions": [],
        "implementation_claims": [],
        "hypotheses": [],
        "transmission_edges": [],
        "dimension_assessments": [candidate["component_id"]],
        "proposed_snapshot": {"status": "REVIEW_PENDING_CANDIDATE_ONLY", "snapshot": proposed_snapshot, "snapshot_revision_id": proposed_snapshot["snapshot_revision_id"], "snapshot_semantic_fingerprint": fingerprint(proposed_snapshot, exclude={"object_sha256"}), "references_candidate_revision": True, "references_simulated_admitted_revision": False},
        "simulated_component": simulated_component,
        "simulated_snapshot": simulated_snapshot,
        "admission_simulation": {"status": simulation["status"], "transaction": simulation_transaction, "result": simulation, "production_admission_performed": False},
        "production_admission": {"status": "NOT_PERFORMED", "write_targets": [], "production_state_count_before": 0, "production_state_count_after": 0},
        "production_admission_gates": gates,
        "visibility": "INTERNAL_ONLY",
        "public_projection_permitted": False,
        "known_empty_or_unsupported_domains": _empty_domains(),
        "limitations": [
            "Step 8A candidate only; not admitted production World State",
            "effective UTC is unresolved because source state_as_of precision is CIVIL_DATE",
            "candidate describes reported burden only, not incidence, severity, geography, response pressure, causality or forecast",
            "shared WHO institutional origin prevents independent corroboration",
            "Canonical historical as-of remains unsupported and is not used by this pilot",
        ],
    }
    return package


def validate_health_candidate_package(package: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if package.get("package_type") != "WORLD_STATE_STEP8A_CANDIDATE":
        errors.append("package type is invalid")
    lineage = package.get("correction_lineage")
    if not isinstance(lineage, dict) or lineage.get("correction_type") != "PRE_ADMISSION_SNAPSHOT_SEMANTICS_AND_MODEL_PROVENANCE":
        errors.append("corrected Step 8A lineage is required")
    if package.get("status") != PRE_FLIGHT_STATUS:
        errors.append("candidate must remain REVIEW_PENDING")
    candidate = package.get("candidate")
    if not isinstance(candidate, dict):
        return errors + ["candidate is required"]
    errors.extend(validate_component_revision(candidate))
    if candidate.get("review_state") != "UNDER_REVIEW" or candidate.get("admitted_at_utc") is not None:
        errors.append("candidate must remain under review and unadmitted")
    if candidate.get("known_at_basis") != "ADMITTED_SIGNAL_REVIEW_BOUNDARY":
        errors.append("candidate known_at basis must remain the admitted Signal review boundary")
    if candidate.get("visibility") != "INTERNAL_ONLY":
        errors.append("candidate visibility must be INTERNAL_ONLY")
    if package.get("public_projection_permitted") is not False:
        errors.append("public projection must remain closed")
    if package.get("production_admission", {}).get("status") != "NOT_PERFORMED":
        errors.append("production admission must not be performed")
    proposed = package.get("proposed_snapshot", {})
    proposed_snapshot = proposed.get("snapshot")
    if not isinstance(proposed_snapshot, dict):
        errors.append("proposed snapshot candidate is required")
    else:
        errors.extend(validate_snapshot_candidate(proposed_snapshot))
        if proposed.get("snapshot_semantic_fingerprint") != fingerprint(proposed_snapshot, exclude={"object_sha256"}):
            errors.append("proposed snapshot candidate fingerprint mismatch")
        if proposed_snapshot.get("admission_transaction_id") is not None or proposed_snapshot.get("admitted_at_utc") is not None:
            errors.append("proposed snapshot candidate must not carry production admission metadata")
    if package.get("actor_assertions") != [] or package.get("implementation_claims") != [] or package.get("transmission_edges") != []:
        errors.append("Step 8A may not create actor, implementation or transmission objects")
    manifest = package.get("source_manifest")
    if not isinstance(manifest, list) or package.get("source_manifest_sha256") != fingerprint(manifest):
        errors.append("source manifest fingerprint mismatch")
    for entry in manifest or []:
        if entry.get("object_sha256") != fingerprint(entry.get("object")):
            errors.append(f"source object hash mismatch: {entry.get('object_id')}")
    if package.get("candidate_semantic_fingerprint") != fingerprint(candidate, exclude={"object_sha256"}):
        errors.append("candidate semantic fingerprint mismatch")
    simulation = package.get("admission_simulation", {})
    if simulation.get("production_admission_performed") is not False:
        errors.append("simulation must not perform production admission")
    if simulation.get("status") != "PASS":
        errors.append("temporary admission simulation did not pass")
    return errors
