"""Guarded Step 8B admission of the first World State component.

This module materialises exactly one human-approved component and compositional
snapshot.  It is deliberately narrow: the corrected Step 8A package is pinned,
the current Signal freshness is rechecked, the exact transaction is simulated,
and only then are the first production-history files written.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from .signals import signal_state_as_of
from .world_state_candidate import (
    CANDIDATE_COMPONENT_ID,
    CANDIDATE_REVISION_ID,
    SIGNAL_ID,
    SIGNAL_REVISION_ID,
    build_health_candidate,
    validate_health_candidate_package,
    WorldStateCandidateError,
)
from .world_state_history import (
    fingerprint,
    simulate_production_admission,
    state_hashes,
    validate_admission_transaction,
    validate_component_history,
    validate_snapshot,
    validate_snapshot_history,
    with_object_fingerprint,
)


PACKAGE_RELATIVE = Path("data/world_state_audit/STEP8A_HEALTH_BVD_CANDIDATE_REVIEW_PENDING_CORRECTED.json")
AUDIT_REVIEW_RELATIVE = Path("data/world_state_audit/STEP8B_HEALTH_BVD_COMPONENT_REVIEW_ACCEPTED.json")
AUDIT_BRIEF_RELATIVE = Path("data/world_state_audit/STEP8B_HEALTH_BVD_COMPONENT_REVIEW_ACCEPTED.md")
COMPONENTS_RELATIVE = Path("data/world_state/components.json")
SNAPSHOTS_RELATIVE = Path("data/world_state/snapshots.json")
ADMISSIONS_RELATIVE = Path("data/world_state/admission_transactions.json")
EXPECTED_CANDIDATE_FINGERPRINT = "996f625c54e6a9717462b04ab339345504b0b481d6d3a9ef3679de0851210c3c"
EXPECTED_PENDING_SNAPSHOT_FINGERPRINT = "42fbe92c8093a2c25d67debc8a2655f3ff06b6ce14aad464a5c69cd9301742c7"
EXPECTED_SOURCE_MANIFEST = "4d16a6c02ed868000859461e6e71f96a1bff2e27b7d9cdaf9b2a022b01f54e8e"
REVIEW_TRANSACTION_ID = "WS-STEP8B-HEALTH-COD-BVD-REVIEW-20260927-001"
ADMISSION_TRANSACTION_ID = "WS-ADMISSION-HEALTH-COD-BVD-20260927-001"
REVIEWER_ID = "operator-human-review"
POPULATION_STATE = "CONTROLLED_FIRST_COMPONENT_PRODUCTION_HISTORY"


class WorldStateAdmissionError(ValueError):
    """Raised when the first production admission fails closed."""


def _load_json(root: Path, relative: Path) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def _parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or len(value) != 20 or not value.endswith("Z"):
        raise WorldStateAdmissionError(f"timestamp must be exact UTC: {value}")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise WorldStateAdmissionError(f"timestamp is invalid UTC: {value}") from exc
    if parsed.tzinfo != timezone.utc:
        raise WorldStateAdmissionError(f"timestamp must use UTC: {value}")
    return parsed


def _json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _object_ref(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "component_type": row["component_type"],
        "component_id": row["component_id"],
        "revision_id": row["revision_id"],
        "object_sha256": row["object_sha256"],
    }


def _protected_input_hashes(root: Path) -> dict[str, str]:
    directories = ("canonical", "live_intelligence", "analysis", "signals", "relationships", "risks", "scenarios", "forecasts", "outcomes", "evaluation")
    paths: list[Path] = []
    for directory in directories:
        paths.extend((root / "data" / directory).rglob("*"))
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)
        if path.is_file()
    }


def _collection(root: Path, relative: Path, key: str) -> list[dict[str, Any]]:
    path = root / relative
    if not path.exists():
        return []
    document = json.loads(path.read_text(encoding="utf-8"))
    rows = document.get(key)
    if not isinstance(rows, list):
        raise WorldStateAdmissionError(f"{relative} must contain a {key} list")
    return rows


def load_production_state(root: Path) -> dict[str, list[dict[str, Any]]]:
    """Read the compositional production history without selecting latest state."""
    if (root / "data/world_state/state.json").exists():
        raise WorldStateAdmissionError("monolithic data/world_state/state.json is prohibited")
    return {
        "actors": _collection(root, Path("data/world_state/actor_registry.json"), "actors"),
        "components": _collection(root, COMPONENTS_RELATIVE, "components"),
        "snapshots": _collection(root, SNAPSHOTS_RELATIVE, "snapshots"),
        "admissions": _collection(root, ADMISSIONS_RELATIVE, "transactions"),
    }


def _validate_review_transaction(transaction: dict[str, Any], package: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if transaction.get("transaction_type") != "WORLD_STATE_COMPONENT_REVIEW":
        errors.append("review transaction type is invalid")
    if transaction.get("decision") != "ACCEPTED":
        errors.append("Step 8B requires an explicit ACCEPTED human decision")
    if transaction.get("decision_scope") != "FIRST_COMPONENT_PRODUCTION_ADMISSION":
        errors.append("review decision scope is invalid")
    if transaction.get("candidate_semantic_fingerprint") != EXPECTED_CANDIDATE_FINGERPRINT:
        errors.append("review transaction candidate fingerprint is not the corrected candidate")
    if transaction.get("pending_snapshot_fingerprint") != EXPECTED_PENDING_SNAPSHOT_FINGERPRINT:
        errors.append("review transaction pending snapshot fingerprint is not the corrected candidate snapshot")
    if transaction.get("source_manifest_sha256") != EXPECTED_SOURCE_MANIFEST:
        errors.append("review transaction source manifest is not the corrected manifest")
    if transaction.get("component", {}).get("component_id") != CANDIDATE_COMPONENT_ID or transaction.get("component", {}).get("revision_id") != CANDIDATE_REVISION_ID:
        errors.append("review transaction component identity is invalid")
    if transaction.get("component", {}).get("object_sha256") != package.get("candidate", {}).get("object_sha256"):
        errors.append("review transaction component hash does not pin the corrected candidate")
    if transaction.get("visibility") != "INTERNAL_ONLY":
        errors.append("review transaction visibility must remain INTERNAL_ONLY")
    if transaction.get("public_projection_permitted") is not False:
        errors.append("review transaction must prohibit public projection")
    if transaction.get("production_world_state_admitted") is not False:
        errors.append("review transaction cannot itself admit production state")
    if transaction.get("write_targets") != []:
        errors.append("component review transaction cannot have write targets")
    if not isinstance(transaction.get("criterion_results"), dict) or any(value.get("status") != "PASS" for value in transaction.get("criterion_results", {}).values() if isinstance(value, dict)):
        errors.append("review criterion results must all pass")
    try:
        _parse_utc(transaction["reviewed_at_utc"])
    except (KeyError, WorldStateAdmissionError) as exc:
        errors.append(str(exc))
    if transaction.get("review_transaction_fingerprint") != fingerprint(transaction, exclude={"review_transaction_fingerprint"}):
        errors.append("review transaction fingerprint mismatch")
    if package.get("candidate_semantic_fingerprint") != EXPECTED_CANDIDATE_FINGERPRINT:
        errors.append("candidate package fingerprint mismatch")
    return errors


def build_review_transaction(package: dict[str, Any], reviewed_at_utc: str) -> dict[str, Any]:
    """Construct the explicit human decision record; this is not admission."""
    reviewed = _parse_utc(reviewed_at_utc)
    reviewed_at_utc = reviewed.strftime("%Y-%m-%dT%H:%M:%SZ")
    transaction = {
        "transaction_id": REVIEW_TRANSACTION_ID,
        "contract_version": "0.1",
        "transaction_type": "WORLD_STATE_COMPONENT_REVIEW",
        "decision": "ACCEPTED",
        "decision_scope": "FIRST_COMPONENT_PRODUCTION_ADMISSION",
        "candidate_package": str(PACKAGE_RELATIVE),
        "candidate_semantic_fingerprint": package.get("candidate_semantic_fingerprint"),
        "pending_snapshot_fingerprint": package.get("proposed_snapshot", {}).get("snapshot_semantic_fingerprint"),
        "source_manifest_sha256": package.get("source_manifest_sha256"),
        "component": {"component_id": CANDIDATE_COMPONENT_ID, "revision_id": CANDIDATE_REVISION_ID, "component_type": "DIMENSION_ASSESSMENT", "object_sha256": package.get("candidate", {}).get("object_sha256")},
        "reviewer": {"reviewer_id": REVIEWER_ID, "role": "human-review"},
        "reviewed_at_utc": reviewed_at_utc,
        "review_basis": {
            "narrow_reported_burden_proposition_supported": True,
            "low_confidence_retained": True,
            "shared_who_origin_limitation_retained": True,
            "no_contradiction_or_correction_in_eligible_lineage": True,
            "no_broad_or_causal_inference_permitted": True,
            "freshness_gate_open": True,
        },
        "criterion_results": {
            "authority_interpretation": {"status": "PASS", "basis": "No actor assertion or authority claim is admitted."},
            "implementation_state": {"status": "PASS", "basis": "No implementation claim is admitted."},
            "evidence_lineage": {"status": "PASS", "basis": "Corrected candidate pins the reviewed Signal, observations, evidence and manifest."},
            "uncertainty_and_shared_origin": {"status": "PASS", "basis": "Partial corroboration, one independent observation and LOW confidence remain explicit."},
            "scope_and_limitations": {"status": "PASS", "basis": "Only reported Bundibugyo confirmed-case burden is admitted."},
            "freshness": {"status": "PASS", "basis": "The Signal is active and before its 2026-10-06 review deadline at transaction time."},
            "public_boundary": {"status": "PASS", "basis": "INTERNAL_ONLY and public projection prohibited."},
        },
        "visibility": "INTERNAL_ONLY",
        "public_projection_permitted": False,
        "production_world_state_admitted": False,
        "write_targets": [],
        "review_transaction_fingerprint": None,
    }
    transaction["review_transaction_fingerprint"] = fingerprint(transaction, exclude={"review_transaction_fingerprint"})
    errors = _validate_review_transaction(transaction, package)
    if errors:
        raise WorldStateAdmissionError("review transaction failed: " + "; ".join(errors))
    return transaction


def validate_component_review_transaction(transaction: dict[str, Any], package: dict[str, Any]) -> list[str]:
    """Validate a retained Step 8B human decision without performing admission."""
    return _validate_review_transaction(transaction, package)


def _current_signal_state(root: Path, as_of_utc: str) -> dict[str, Any]:
    signal_schema = _load_json(root, Path("data/signals/schema.json"))
    signals = _load_json(root, Path("data/signals/signals.json"))
    observations = _load_json(root, Path("data/live_intelligence/observations.json"))
    evidence = _load_json(root, Path("data/live_intelligence/evidence_registry.json"))
    return signal_state_as_of(signal_schema, signals["signals"], observations, evidence, as_of_utc)[SIGNAL_ID]


def _freshness_at_admission(package: dict[str, Any], signal_state: dict[str, Any], admitted_at_utc: str) -> dict[str, Any]:
    freshness = deepcopy(package["freshness"])
    due = _parse_utc(freshness["stale_review_due_at_utc"])
    admitted = _parse_utc(admitted_at_utc)
    if signal_state.get("revision_id") != SIGNAL_REVISION_ID or signal_state.get("effective_state") != "ACTIVE" or admitted >= due:
        raise WorldStateAdmissionError("freshness gate is closed: Signal is stale, changed or past review deadline")
    freshness.update({
        "reviewed_at_utc": admitted_at_utc,
        "admitted_at_utc": admitted_at_utc,
        "signal_state_at_admission": signal_state["effective_state"],
        "freshness_gate": "OPEN",
    })
    return freshness


def build_first_admission(root: Path, reviewed_at_utc: str, admitted_at_utc: str) -> dict[str, Any]:
    """Build and validate the exact first admission without writing files."""
    reviewed = _parse_utc(reviewed_at_utc)
    admitted = _parse_utc(admitted_at_utc)
    if reviewed > admitted:
        raise WorldStateAdmissionError("reviewed_at_utc must be before admitted_at_utc")
    package = _load_json(root, PACKAGE_RELATIVE)
    package_errors = validate_health_candidate_package(package)
    if package_errors:
        raise WorldStateAdmissionError("corrected candidate failed validation: " + "; ".join(package_errors))
    if package.get("candidate_semantic_fingerprint") != EXPECTED_CANDIDATE_FINGERPRINT or package.get("source_manifest_sha256") != EXPECTED_SOURCE_MANIFEST:
        raise WorldStateAdmissionError("corrected candidate fingerprint or source manifest mismatch")
    if package.get("proposed_snapshot", {}).get("snapshot_semantic_fingerprint") != EXPECTED_PENDING_SNAPSHOT_FINGERPRINT:
        raise WorldStateAdmissionError("corrected pending snapshot fingerprint mismatch")
    try:
        regenerated = build_health_candidate(root, package["constructed_at_utc"])
    except (OSError, ValueError, WorldStateCandidateError) as exc:
        raise WorldStateAdmissionError("current governed candidate inputs failed closed: " + str(exc)) from exc
    if regenerated != package:
        raise WorldStateAdmissionError("retained corrected candidate is not reproducible from current governed inputs")
    production = load_production_state(root)
    if any(production[key] for key in ("actors", "components", "snapshots", "admissions")):
        raise WorldStateAdmissionError("first production admission requires empty World State history")
    signal_state = _current_signal_state(root, admitted_at_utc)
    freshness = _freshness_at_admission(package, signal_state, admitted_at_utc)
    review = build_review_transaction(package, reviewed_at_utc)
    candidate = deepcopy(package["candidate"])
    candidate.update({
        "review_state": "ACCEPTED",
        "lifecycle_state": "ACTIVE",
        "reviewed_at_utc": reviewed.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "admitted_at_utc": admitted.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "review_transaction_id": REVIEW_TRANSACTION_ID,
        "admission_transaction_id": ADMISSION_TRANSACTION_ID,
        "revision_reason": "Step 8B human-admitted narrow reported-burden assessment; no broader inference permitted.",
        "freshness": freshness,
        "object_sha256": None,
    })
    admitted_component = with_object_fingerprint(candidate)
    pending_snapshot = deepcopy(package["proposed_snapshot"]["snapshot"])
    pending_snapshot.pop("candidate_review_id", None)
    pending_snapshot.pop("review_state", None)
    pending_snapshot.update({
        "component_refs": [_object_ref(admitted_component)],
        "review_transaction_id": REVIEW_TRANSACTION_ID,
        "admission_transaction_id": ADMISSION_TRANSACTION_ID,
        "lifecycle_state": "ACTIVE",
        "visibility": "INTERNAL_ONLY",
        "reviewer": {"reviewer_id": REVIEWER_ID, "role": "human-review"},
        "admitted_at_utc": admitted.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "object_sha256": None,
    })
    production_snapshot = with_object_fingerprint(pending_snapshot)
    component_index = {(admitted_component["component_type"], admitted_component["revision_id"]): admitted_component}
    errors = validate_component_history([admitted_component])
    errors.extend(validate_snapshot(production_snapshot, component_index=component_index))
    if errors:
        raise WorldStateAdmissionError("admitted object validation failed: " + "; ".join(errors))
    before_state = {"actors": [], "components": [], "snapshots": []}
    after_state = {"actors": [], "components": [admitted_component], "snapshots": [production_snapshot]}
    transaction = {
        "transaction_id": ADMISSION_TRANSACTION_ID,
        "contract_version": "0.1",
        "transaction_type": "WORLD_STATE_PRODUCTION_ADMISSION",
        "decision": "ACCEPTED",
        "proposal_id": package["candidate"]["source_proposal_id"],
        "proposal_semantic_fingerprint": package["candidate_semantic_fingerprint"],
        "source_manifest_sha256": package["source_manifest_sha256"],
        "component_fingerprints": [_object_ref(admitted_component)],
        "reviewer": {"reviewer_id": REVIEWER_ID, "role": "human-review"},
        "review_transaction_id": REVIEW_TRANSACTION_ID,
        "decided_at_utc": reviewed.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "component_dispositions": [{"component_id": admitted_component["component_id"], "revision_id": admitted_component["revision_id"], "disposition": "ADMITTED", "reason": "Explicit Step 8B human decision for the narrow reported-burden component."}],
        "snapshot_revision_identity": {"snapshot_series_id": production_snapshot["snapshot_series_id"], "snapshot_revision_id": production_snapshot["snapshot_revision_id"]},
        "write_targets": [str(COMPONENTS_RELATIVE), str(SNAPSHOTS_RELATIVE), str(ADMISSIONS_RELATIVE)],
        "pre_state_hashes": state_hashes(before_state),
        "post_state_hashes": state_hashes(after_state),
        "visibility_decision": "INTERNAL_ONLY",
        "public_projection_permitted": False,
        "admitted_at_utc": admitted.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "validator_version": "world-state-history-v1",
        "transaction_fingerprint": None,
    }
    transaction["transaction_fingerprint"] = fingerprint(transaction, exclude={"transaction_fingerprint"})
    transaction_errors = validate_admission_transaction(transaction)
    if transaction_errors:
        raise WorldStateAdmissionError("admission transaction failed: " + "; ".join(transaction_errors))
    simulation = simulate_production_admission(transaction, current_state=before_state, candidate_components=[admitted_component], candidate_snapshot=production_snapshot)
    if simulation["status"] != "PASS" or simulation["post_state_hashes"] != transaction["post_state_hashes"]:
        raise WorldStateAdmissionError("exact admission simulation failed: " + "; ".join(simulation["errors"]))
    return {
        "package": package,
        "review_transaction": review,
        "admitted_component": admitted_component,
        "production_snapshot": production_snapshot,
        "admission_transaction": transaction,
        "simulation": simulation,
        "before_state": before_state,
        "after_state": after_state,
        "freshness": freshness,
        "protected_input_hashes_before": _protected_input_hashes(root),
    }


def validate_production_state(root: Path, *, enforce_first_population: bool = True) -> list[str]:
    """Validate materialised history and exact references.

    The default keeps the Step 8B first-admission gate strict.  Read-only
    history consumers may validate an append-only descendant without imposing
    that initial population ceiling.
    """
    state = load_production_state(root)
    errors = validate_component_history(state["components"])
    component_index = {(row["component_type"], row["revision_id"]): row for row in state["components"]}
    errors.extend(validate_snapshot_history(state["snapshots"], component_index=component_index))
    errors.extend(validate_admission_transaction(row) for row in state["admissions"])
    flattened = [error for group in errors for error in (group if isinstance(group, list) else [group])]
    if enforce_first_population and (len(state["components"]) != 1 or len(state["snapshots"]) != 1 or len(state["admissions"]) != 1 or state["actors"]):
        flattened.append("production population does not match the first-admission boundary")
    return flattened


def _review_brief(bundle: dict[str, Any]) -> str:
    component = bundle["admitted_component"]
    transaction = bundle["admission_transaction"]
    return f"""# Step 8B — first World State component review and admission

Decision: `ACCEPTED`
Decision scope: `FIRST_COMPONENT_PRODUCTION_ADMISSION`
Review transaction: `{REVIEW_TRANSACTION_ID}`
Admission transaction: `{ADMISSION_TRANSACTION_ID}`

The human decision admits exactly one internal `DIMENSION_ASSESSMENT`:
`{component['component_id']}` revision `{component['revision_id']}`.
It records reported Bundibugyo confirmed-case burden increasing across the
26–30 August 2026 governed snapshots. The effective state remains the civil
date `2026-08-30`; no UTC instant is manufactured. Known-at is
`{component['known_at_utc']}`. Confidence remains `LOW`.

The shared WHO institutional origin, partial corroboration, one-independent-
observation limitation, measurement limits, contradiction inspection and all
candidate limitations are retained. This does not assert incidence, severity,
geographic expansion, general DRC health deterioration, causal transmission,
forecast, or a health-risk score. No actors, implementation claims,
Relationships, Risks, Scenarios or Forecasts are admitted.

Freshness at admission: `{bundle['freshness']['signal_state_at_admission']}`;
review due `{bundle['freshness']['stale_review_due_at_utc']}` based on the
latest supporting system-observed time `{bundle['freshness']['latest_supporting_observed_at_utc']}`.

Production writes are limited to:

- `{COMPONENTS_RELATIVE}`
- `{SNAPSHOTS_RELATIVE}`
- `{ADMISSIONS_RELATIVE}`

Visibility is `INTERNAL_ONLY`; public projection is prohibited. The admission
transaction pre-state and post-state hashes are retained in the transaction.
The corrected Step 8A package and original superseded audit artifact remain
unchanged.
"""


def _atomic_materialize(files: dict[Path, str]) -> None:
    temporary: dict[Path, Path] = {}
    backups: dict[Path, Path] = {}
    installed: list[Path] = []
    try:
        for target, content in files.items():
            target.parent.mkdir(parents=True, exist_ok=True)
            handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=target.parent, prefix=".world-state-admission-", delete=False)
            with handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            temporary[target] = Path(handle.name)
        for target in files:
            if target.exists():
                backup = target.with_name(f".{target.name}.admission-backup")
                os.replace(target, backup)
                backups[target] = backup
        for target, staged in temporary.items():
            os.replace(staged, target)
            installed.append(target)
        for backup in backups.values():
            backup.unlink(missing_ok=True)
    except Exception:
        for target in installed:
            target.unlink(missing_ok=True)
        for target, backup in backups.items():
            if backup.exists():
                os.replace(backup, target)
        raise
    finally:
        for staged in temporary.values():
            staged.unlink(missing_ok=True)
        for backup in backups.values():
            backup.unlink(missing_ok=True)


def admit_first_health_candidate(root: Path, reviewed_at_utc: str, admitted_at_utc: str, *, write: bool = False) -> dict[str, Any]:
    """Preflight or materialise the explicit first production admission."""
    bundle = build_first_admission(root, reviewed_at_utc, admitted_at_utc)
    if not write:
        bundle["materialized"] = False
        return bundle
    files = {
        root / AUDIT_REVIEW_RELATIVE: _json(bundle["review_transaction"]),
        root / AUDIT_BRIEF_RELATIVE: _review_brief(bundle),
        root / COMPONENTS_RELATIVE: _json({"project": "WORLD SIGNALS", "dataset": "WORLD_STATE_COMPONENT_HISTORY", "version": "0.1", "population_state": POPULATION_STATE, "public_projection_permitted": False, "components": [bundle["admitted_component"]]}),
        root / SNAPSHOTS_RELATIVE: _json({"project": "WORLD SIGNALS", "dataset": "WORLD_STATE_SNAPSHOT_HISTORY", "version": "0.1", "population_state": POPULATION_STATE, "public_projection_permitted": False, "snapshots": [bundle["production_snapshot"]]}),
        root / ADMISSIONS_RELATIVE: _json({"project": "WORLD SIGNALS", "dataset": "WORLD_STATE_PRODUCTION_ADMISSION_HISTORY", "version": "0.1", "population_state": POPULATION_STATE, "public_projection_permitted": False, "transactions": [bundle["admission_transaction"]]}),
    }
    _atomic_materialize(files)
    errors = validate_production_state(root)
    if errors:
        raise WorldStateAdmissionError("materialized production state failed validation: " + "; ".join(errors))
    bundle["protected_input_hashes_after"] = _protected_input_hashes(root)
    if bundle["protected_input_hashes_after"] != bundle["protected_input_hashes_before"]:
        raise WorldStateAdmissionError("protected upstream inputs changed during admission")
    bundle["materialized"] = True
    return bundle
