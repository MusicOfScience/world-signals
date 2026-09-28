"""Guarded Step 11B admission of the corrected RBNZ specimen.

This module materialises exactly two independently reviewable Dimension
Assessment revisions and one compositional RBNZ snapshot.  The Actor Registry
remains untouched.  The existing Health history is an immutable input, not a
newly composed production snapshot.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from .world_state_admission import _atomic_materialize, load_production_state, validate_production_state
from .world_state_history import (
    fingerprint,
    select_component_revisions,
    simulate_production_admission,
    state_hashes,
    validate_admission_transaction,
    validate_component_history,
    validate_snapshot,
    validate_snapshot_history,
    with_object_fingerprint,
)
from .world_state_rbnz_candidate import (
    MACRO_COMPONENT_ID,
    MARKET_COMPONENT_ID,
    build_corrected_rbnz_candidate,
    validate_corrected_rbnz_candidate_package,
)


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_RELATIVE = Path("data/world_state_audit/STEP11A1_RBNZ_CANDIDATE_REVIEW_PENDING_CORRECTED.json")
ORIGINAL_PACKAGE_RELATIVE = Path("data/world_state_audit/STEP11A_RBNZ_CANDIDATE_REVIEW_PENDING.json")
REVIEW_RELATIVE = Path("data/world_state_audit/STEP11B_RBNZ_COMPONENT_REVIEW_ACCEPTED.json")
REVIEW_BRIEF_RELATIVE = Path("data/world_state_audit/STEP11B_RBNZ_COMPONENT_REVIEW_ACCEPTED.md")
COMPONENTS_RELATIVE = Path("data/world_state/components.json")
SNAPSHOTS_RELATIVE = Path("data/world_state/snapshots.json")
ADMISSIONS_RELATIVE = Path("data/world_state/admission_transactions.json")

EXPECTED_PACKAGE_FINGERPRINT = "447954092a4825dd5a6b4a0253ed9cf8939d97df127632ae43e8121792f74571"
EXPECTED_PENDING_SNAPSHOT_FINGERPRINT = "72e1de6ab61c30d8944c34410cddb62965f8af86701590e9ef2ab1c158164617"
EXPECTED_SOURCE_MANIFEST = "b5eecfedcc9b0d6ae6572e52b394e9157116ced7d8d8393c9e8189b6300ba8d4"
EXPECTED_MACRO_CANDIDATE_HASH = "e041de9aacd6d1bb0692e0895ffae44cd36ea5c50caccf5842229e233d3d064a"
EXPECTED_MARKET_CANDIDATE_HASH = "0f89ae71e23146da67d0b385734ae56368e96cf86e124dc72992041e327d3240"
EXPECTED_ORIGINAL_PACKAGE_SHA256 = "38ac088534f7f61c60be0e528894aec0e0d167a7a7abcada3b40f53de698add3"

REVIEW_TRANSACTION_ID = "WS-STEP11B-RBNZ-COMPONENT-REVIEW-20260928-001"
ADMISSION_TRANSACTION_ID = "WS-ADMISSION-NZ-RBNZ-OCR-20260928-001"
REVIEWER_ID = "operator-human-review"
SNAPSHOT_REVISION_ID = "WSSNAP-NZ-RBNZ-OCR-202609-R1"


class WorldStateRbnzAdmissionError(ValueError):
    """Raised when the narrow Step 11B admission fails closed."""


def _parse_utc(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or len(value) != 20 or not value.endswith("Z"):
        raise WorldStateRbnzAdmissionError(f"{field} must be exact UTC ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise WorldStateRbnzAdmissionError(f"{field} is invalid UTC") from exc
    if parsed.tzinfo != timezone.utc:
        raise WorldStateRbnzAdmissionError(f"{field} must be UTC")
    return parsed


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _load_json(root: Path, relative: Path) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def _collection(root: Path, relative: Path, key: str) -> list[dict[str, Any]]:
    document = _load_json(root, relative)
    rows = document.get(key)
    if not isinstance(rows, list):
        raise WorldStateRbnzAdmissionError(f"{relative} must contain a {key} list")
    return rows


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


def _object_ref(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "component_type": row["component_type"],
        "component_id": row["component_id"],
        "revision_id": row["revision_id"],
        "object_sha256": row["object_sha256"],
    }


def _candidate_rows(package: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row.get("component_id"): row for row in package.get("dimension_assessment_candidates", [])}


def _verify_package(root: Path) -> dict[str, Any]:
    package = _load_json(root, PACKAGE_RELATIVE)
    errors = validate_corrected_rbnz_candidate_package(package)
    if errors:
        raise WorldStateRbnzAdmissionError("corrected candidate failed validation: " + "; ".join(errors))
    if package.get("candidate_semantic_fingerprint") != EXPECTED_PACKAGE_FINGERPRINT:
        raise WorldStateRbnzAdmissionError("corrected package fingerprint does not match the reviewed candidate")
    if package.get("proposed_snapshot", {}).get("snapshot_semantic_fingerprint") != EXPECTED_PENDING_SNAPSHOT_FINGERPRINT:
        raise WorldStateRbnzAdmissionError("corrected pending snapshot fingerprint does not match the reviewed candidate")
    if package.get("source_manifest_sha256") != EXPECTED_SOURCE_MANIFEST:
        raise WorldStateRbnzAdmissionError("source manifest does not match the reviewed candidate")
    rows = _candidate_rows(package)
    expected = {
        MACRO_COMPONENT_ID: EXPECTED_MACRO_CANDIDATE_HASH,
        MARKET_COMPONENT_ID: EXPECTED_MARKET_CANDIDATE_HASH,
    }
    if set(rows) != set(expected):
        raise WorldStateRbnzAdmissionError("the reviewed package must contain exactly Macro and Markets candidates")
    for component_id, object_sha256 in expected.items():
        row = rows[component_id]
        if row.get("object_sha256") != object_sha256:
            raise WorldStateRbnzAdmissionError(f"candidate hash mismatch for {component_id}")
        if row.get("review_state") != "UNDER_REVIEW" or row.get("admitted_at_utc") is not None:
            raise WorldStateRbnzAdmissionError(f"candidate {component_id} is not pending and unadmitted")
        if "actor_id" in row:
            raise WorldStateRbnzAdmissionError(f"candidate {component_id} unexpectedly depends on Actor Registry identity")
    original = root / ORIGINAL_PACKAGE_RELATIVE
    if hashlib.sha256(original.read_bytes()).hexdigest() != EXPECTED_ORIGINAL_PACKAGE_SHA256:
        raise WorldStateRbnzAdmissionError("original Step 11A artifact changed")
    regenerated = build_corrected_rbnz_candidate(root)
    if regenerated != package:
        raise WorldStateRbnzAdmissionError("retained corrected package is not reproducible from current governed inputs")
    return package


def build_component_review_transaction(package: dict[str, Any], reviewed_at_utc: str) -> dict[str, Any]:
    reviewed = _iso(_parse_utc(reviewed_at_utc, "reviewed_at_utc"))
    rows = _candidate_rows(package)
    transaction = {
        "transaction_id": REVIEW_TRANSACTION_ID,
        "contract_version": "0.1",
        "transaction_type": "WORLD_STATE_COMPONENT_REVIEW",
        "decision": "ACCEPTED",
        "decision_scope": "RBNZ_SECOND_SPECIMEN",
        "candidate_package": str(PACKAGE_RELATIVE),
        "candidate_semantic_fingerprint": package["candidate_semantic_fingerprint"],
        "pending_snapshot_fingerprint": package["proposed_snapshot"]["snapshot_semantic_fingerprint"],
        "source_manifest_sha256": package["source_manifest_sha256"],
        "candidate_components": [_object_ref(rows[component_id]) for component_id in (MACRO_COMPONENT_ID, MARKET_COMPONENT_ID)],
        "reviewer": {"reviewer_id": REVIEWER_ID, "role": "human-review"},
        "reviewed_at_utc": reviewed,
        "decision_basis": {
            "macro": "Narrow policy-rate increase and more-gradual-than-market-pricing proposition accepted; no generic dovishness, future path, regime or broad macro claim.",
            "markets": "Narrow source-reported swap and NZD sensor measurements accepted; MEDIUM confidence, null before-values, alternative explanations and OBSERVED_ASSOCIATION retained.",
            "actor": "DEFERRED / NOT_PART_OF_COMPONENT_ADMISSION: actor identity is not required by the accepted Dimension Assessments; identity admission remains separate.",
        },
        "component_decisions": {
            MACRO_COMPONENT_ID: "ACCEPTED",
            MARKET_COMPONENT_ID: "ACCEPTED",
            "WSACT-RBNZ-202609-001": "DEFERRED",
        },
        "visibility": "INTERNAL_ONLY",
        "public_projection_permitted": False,
        "production_world_state_admitted": False,
        "write_targets": [],
        "review_transaction_fingerprint": None,
    }
    transaction["review_transaction_fingerprint"] = fingerprint(transaction, exclude={"review_transaction_fingerprint"})
    return transaction


def validate_component_review_transaction_step11b(transaction: Any, package: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(transaction, dict):
        return ["Step 11B component review transaction must be an object"]
    if transaction.get("transaction_type") != "WORLD_STATE_COMPONENT_REVIEW":
        errors.append("review transaction type is invalid")
    if transaction.get("decision") != "ACCEPTED" or transaction.get("decision_scope") != "RBNZ_SECOND_SPECIMEN":
        errors.append("review transaction must explicitly accept only the RBNZ second specimen")
    if transaction.get("candidate_semantic_fingerprint") != EXPECTED_PACKAGE_FINGERPRINT:
        errors.append("review transaction candidate fingerprint mismatch")
    if transaction.get("pending_snapshot_fingerprint") != EXPECTED_PENDING_SNAPSHOT_FINGERPRINT:
        errors.append("review transaction pending snapshot fingerprint mismatch")
    if transaction.get("source_manifest_sha256") != EXPECTED_SOURCE_MANIFEST:
        errors.append("review transaction source manifest mismatch")
    rows = _candidate_rows(package)
    expected_refs = [_object_ref(rows[component_id]) for component_id in (MACRO_COMPONENT_ID, MARKET_COMPONENT_ID)]
    if transaction.get("candidate_components") != expected_refs:
        errors.append("review transaction candidate component refs mismatch")
    decisions = transaction.get("component_decisions")
    if not isinstance(decisions, dict) or decisions.get(MACRO_COMPONENT_ID) != "ACCEPTED" or decisions.get(MARKET_COMPONENT_ID) != "ACCEPTED" or decisions.get("WSACT-RBNZ-202609-001") != "DEFERRED":
        errors.append("review transaction decisions must accept Macro and Markets and defer actor")
    if transaction.get("visibility") != "INTERNAL_ONLY" or transaction.get("public_projection_permitted") is not False:
        errors.append("review transaction visibility/public boundary is invalid")
    if transaction.get("production_world_state_admitted") is not False or transaction.get("write_targets") != []:
        errors.append("component review transaction must not admit or write production state")
    try:
        _parse_utc(transaction["reviewed_at_utc"], "reviewed_at_utc")
    except (KeyError, WorldStateRbnzAdmissionError) as exc:
        errors.append(str(exc))
    if transaction.get("review_transaction_fingerprint") != fingerprint(transaction, exclude={"review_transaction_fingerprint"}):
        errors.append("review transaction fingerprint mismatch")
    return errors


def _admitted_component(candidate: dict[str, Any], reviewed_at: str, admitted_at: str, admission_id: str) -> dict[str, Any]:
    component = deepcopy(candidate)
    component.update({
        "review_state": "ACCEPTED",
        "lifecycle_state": "ACTIVE",
        "reviewed_at_utc": reviewed_at,
        "admitted_at_utc": admitted_at,
        "review_transaction_id": REVIEW_TRANSACTION_ID,
        "admission_transaction_id": admission_id,
        "revision_reason": "Step 11B human-admitted narrow RBNZ specimen; no actor, relationship, forecast or broader macro/market inference permitted.",
        "object_sha256": None,
    })
    return with_object_fingerprint(component)


def _production_snapshot(package: dict[str, Any], components: list[dict[str, Any]], reviewed_at: str, admitted_at: str, admission_id: str) -> dict[str, Any]:
    snapshot = deepcopy(package["proposed_snapshot"]["snapshot"])
    snapshot.pop("candidate_review_id", None)
    snapshot.pop("review_state", None)
    snapshot.update({
        "component_refs": [_object_ref(row) for row in components],
        "review_transaction_id": REVIEW_TRANSACTION_ID,
        "admission_transaction_id": admission_id,
        "lifecycle_state": "ACTIVE",
        "visibility": "INTERNAL_ONLY",
        "reviewer": {"reviewer_id": REVIEWER_ID, "role": "human-review"},
        "admitted_at_utc": admitted_at,
        "limitations": [
            "Independent RBNZ Macro and Markets assessments; not a global World State snapshot.",
            "Mixed temporal precision is preserved: Macro UTC_INSTANT and Markets CIVIL_DATE.",
            "Market measurements remain sensors with OBSERVED_ASSOCIATION and no production Relationship.",
            "Actor identity was explicitly deferred and is not required by either component.",
        ],
        "reviewed_at_utc": reviewed_at,
        "object_sha256": None,
    })
    return with_object_fingerprint(snapshot)


def _validate_full_state(state: dict[str, list[dict[str, Any]]]) -> list[str]:
    errors = validate_component_history(state["components"])
    component_index = {(row["component_type"], row["revision_id"]): row for row in state["components"]}
    errors.extend(validate_snapshot_history(state["snapshots"], component_index=component_index))
    errors.extend(validate_admission_transaction(row) for row in state["admissions"])
    return [error for group in errors for error in (group if isinstance(group, list) else [group])]


def build_rbnz_admission(root: Path, reviewed_at_utc: str, admitted_at_utc: str) -> dict[str, Any]:
    reviewed = _iso(_parse_utc(reviewed_at_utc, "reviewed_at_utc"))
    admitted = _iso(_parse_utc(admitted_at_utc, "admitted_at_utc"))
    if reviewed > admitted:
        raise WorldStateRbnzAdmissionError("reviewed_at_utc must not follow admitted_at_utc")
    package = _verify_package(root)
    review = build_component_review_transaction(package, reviewed)
    review_errors = validate_component_review_transaction_step11b(review, package)
    if review_errors:
        raise WorldStateRbnzAdmissionError("human component review failed: " + "; ".join(review_errors))
    state = load_production_state(root)
    state_errors = validate_production_state(root, enforce_first_population=False)
    if state_errors:
        raise WorldStateRbnzAdmissionError("existing production history is invalid: " + "; ".join(state_errors))
    if len(state["actors"]) != 0 or len(state["components"]) != 1 or len(state["snapshots"]) != 1 or len(state["admissions"]) != 1:
        raise WorldStateRbnzAdmissionError("Step 11B requires the exact one-component production pre-state")
    health_component = deepcopy(state["components"][0])
    health_snapshot = deepcopy(state["snapshots"][0])
    health_admission = deepcopy(state["admissions"][0])
    rows = _candidate_rows(package)
    components = [
        _admitted_component(rows[MACRO_COMPONENT_ID], reviewed, admitted, ADMISSION_TRANSACTION_ID),
        _admitted_component(rows[MARKET_COMPONENT_ID], reviewed, admitted, ADMISSION_TRANSACTION_ID),
    ]
    for row in components:
        if row.get("qualitative_confidence") != "MEDIUM" or row.get("visibility") != "INTERNAL_ONLY":
            raise WorldStateRbnzAdmissionError(f"admitted component lost reviewed epistemic boundary: {row.get('component_id')}")
        if row.get("actor_id") is not None:
            raise WorldStateRbnzAdmissionError("admitted component cannot depend on deferred actor identity")
    snapshot = _production_snapshot(package, components, reviewed, admitted, ADMISSION_TRANSACTION_ID)
    component_index = {(row["component_type"], row["revision_id"]): row for row in state["components"] + components}
    errors = validate_component_history(state["components"] + components)
    errors.extend(validate_snapshot(snapshot, component_index=component_index))
    if errors:
        raise WorldStateRbnzAdmissionError("admitted object validation failed: " + "; ".join(errors))
    before_state = {"actors": state["actors"], "components": state["components"], "snapshots": state["snapshots"]}
    after_state = {"actors": state["actors"], "components": state["components"] + components, "snapshots": state["snapshots"] + [snapshot]}
    transaction = {
        "transaction_id": ADMISSION_TRANSACTION_ID,
        "contract_version": "0.1",
        "transaction_type": "WORLD_STATE_PRODUCTION_ADMISSION",
        "decision": "ACCEPTED",
        "proposal_id": "WS-STEP11A1-RBNZ-RBNZ-OCR-202609",
        "candidate_package": str(PACKAGE_RELATIVE),
        "proposal_semantic_fingerprint": package["candidate_semantic_fingerprint"],
        "source_manifest_sha256": package["source_manifest_sha256"],
        "candidate_component_fingerprints": [_object_ref(rows[component_id]) for component_id in (MACRO_COMPONENT_ID, MARKET_COMPONENT_ID)],
        "component_fingerprints": [_object_ref(row) for row in components],
        "reviewer": {"reviewer_id": REVIEWER_ID, "role": "human-review"},
        "review_transaction_id": REVIEW_TRANSACTION_ID,
        "decided_at_utc": reviewed,
        "component_dispositions": [
            {"component_id": row["component_id"], "revision_id": row["revision_id"], "disposition": "ADMITTED", "reason": "Explicit Step 11B human decision for the narrow reviewed RBNZ component."}
            for row in components
        ],
        "deferred_dispositions": [{"actor_id": "WSACT-RBNZ-202609-001", "disposition": "DEFERRED", "reason": "Actor identity is not required by the accepted Dimension Assessments."}],
        "snapshot_revision_identity": {"snapshot_series_id": snapshot["snapshot_series_id"], "snapshot_revision_id": snapshot["snapshot_revision_id"]},
        "snapshot_fingerprint": snapshot["object_sha256"],
        "write_targets": [str(COMPONENTS_RELATIVE), str(SNAPSHOTS_RELATIVE), str(ADMISSIONS_RELATIVE), str(REVIEW_RELATIVE), str(REVIEW_BRIEF_RELATIVE)],
        "pre_state_hashes": state_hashes(before_state),
        "post_state_hashes": state_hashes(after_state),
        "visibility_decision": "INTERNAL_ONLY",
        "public_projection_permitted": False,
        "admitted_at_utc": admitted,
        "validator_version": "world-state-rbnz-admission-v1",
        "transaction_fingerprint": None,
    }
    transaction["transaction_fingerprint"] = fingerprint(transaction, exclude={"transaction_fingerprint"})
    transaction_errors = validate_admission_transaction(transaction)
    if transaction_errors:
        raise WorldStateRbnzAdmissionError("production admission transaction failed: " + "; ".join(transaction_errors))
    simulation = simulate_production_admission(
        transaction,
        current_state=before_state,
        candidate_components=components,
        candidate_snapshot=snapshot,
    )
    if simulation["status"] != "PASS" or simulation["post_state_hashes"] != transaction["post_state_hashes"]:
        raise WorldStateRbnzAdmissionError("exact Step 11B simulation failed: " + "; ".join(simulation["errors"]))
    combined_state = {"actors": state["actors"], "components": state["components"] + components, "snapshots": state["snapshots"] + [snapshot], "admissions": state["admissions"] + [transaction]}
    combined_errors = _validate_full_state(combined_state)
    if combined_errors:
        raise WorldStateRbnzAdmissionError("combined production state failed validation: " + "; ".join(combined_errors))
    return {
        "package": package,
        "review_transaction": review,
        "admitted_components": components,
        "production_snapshot": snapshot,
        "admission_transaction": transaction,
        "simulation": simulation,
        "before_state": before_state,
        "after_state": after_state,
        "previous_health_component": health_component,
        "previous_health_snapshot": health_snapshot,
        "previous_health_admission": health_admission,
        "protected_input_hashes_before": _protected_input_hashes(root),
    }


def _review_brief(bundle: dict[str, Any]) -> str:
    components = bundle["admitted_components"]
    return f"""# Step 11B — RBNZ component review and production admission

Decision: `ACCEPTED`
Decision scope: `RBNZ_SECOND_SPECIMEN`
Review transaction: `{REVIEW_TRANSACTION_ID}`
Admission transaction: `{ADMISSION_TRANSACTION_ID}`

The human decision accepts exactly two internal Dimension Assessments:

- `{components[0]['component_id']}` — `{components[0]['state_label']}`
- `{components[1]['component_id']}` — `{components[1]['state_label']}`

The Macro assessment preserves UTC-instant effective time at
`2026-09-02T02:00:00Z`, comparative `known_at_utc` at
`2026-09-05T14:40:00Z`, and MEDIUM confidence. The Markets assessment
preserves civil-date effective precision for 2026-09-02, null exact movement
bounds, source-reported endpoints, MEDIUM confidence and
`OBSERVED_ASSOCIATION` without a production Relationship.

The RBNZ actor identity decision is explicitly `DEFERRED`; no Actor Registry
identity, actor relationship, ActorStateAssertion or ImplementationClaim is
admitted. No standalone baseline, Forecast, Outcome or Evaluation object is
created. The two assessments are independent of the existing Health snapshot
series and remain `INTERNAL_ONLY`.

The snapshot is a compositional index over the two admitted RBNZ components.
It does not claim global macro or market coverage, does not create a combined
Health/RBNZ production snapshot, and preserves mixed temporal precision.
Read-time multi-series composition remains non-admitted and marked
`INDEPENDENT_ADMISSIONS`.

Production writes are limited to the two component history rows, the RBNZ
snapshot revision, the production admission transaction, and these retained
Step 11B audit records. Public projection remains prohibited.
"""


def materialize_rbnz_admission(root: Path, reviewed_at_utc: str, admitted_at_utc: str, *, write: bool = False) -> dict[str, Any]:
    bundle = build_rbnz_admission(root, reviewed_at_utc, admitted_at_utc)
    if not write:
        bundle["materialized"] = False
        return bundle
    current = load_production_state(root)
    if state_hashes(current) != bundle["admission_transaction"]["pre_state_hashes"]:
        raise WorldStateRbnzAdmissionError("production pre-state changed after preflight")
    files = {
        root / REVIEW_RELATIVE: _json(bundle["review_transaction"]),
        root / REVIEW_BRIEF_RELATIVE: _review_brief(bundle),
        root / COMPONENTS_RELATIVE: _json({"project": "WORLD SIGNALS", "dataset": "WORLD_STATE_COMPONENT_HISTORY", "version": "0.1", "population_state": "CONTROLLED_COMPONENTIZED_PRODUCTION_HISTORY", "public_projection_permitted": False, "components": bundle["after_state"]["components"]}),
        root / SNAPSHOTS_RELATIVE: _json({"project": "WORLD SIGNALS", "dataset": "WORLD_STATE_SNAPSHOT_HISTORY", "version": "0.1", "population_state": "CONTROLLED_COMPONENTIZED_PRODUCTION_HISTORY", "public_projection_permitted": False, "snapshots": bundle["after_state"]["snapshots"]}),
        root / ADMISSIONS_RELATIVE: _json({"project": "WORLD SIGNALS", "dataset": "WORLD_STATE_PRODUCTION_ADMISSION_HISTORY", "version": "0.1", "population_state": "CONTROLLED_COMPONENTIZED_PRODUCTION_HISTORY", "public_projection_permitted": False, "transactions": current["admissions"] + [bundle["admission_transaction"]]}),
    }
    _atomic_materialize(files)
    errors = validate_production_state(root, enforce_first_population=False)
    if errors:
        raise WorldStateRbnzAdmissionError("materialized production state failed validation: " + "; ".join(errors))
    after = load_production_state(root)
    if after["components"][0] != bundle["previous_health_component"] or after["snapshots"][0] != bundle["previous_health_snapshot"] or after["admissions"][0] != bundle["previous_health_admission"]:
        raise WorldStateRbnzAdmissionError("existing Health production history was rewritten")
    if _protected_input_hashes(root) != bundle["protected_input_hashes_before"]:
        raise WorldStateRbnzAdmissionError("upstream governed inputs changed during Step 11B admission")
    bundle["materialized"] = True
    bundle["protected_input_hashes_after"] = _protected_input_hashes(root)
    return bundle
