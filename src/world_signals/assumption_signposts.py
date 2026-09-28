"""Governed internal assumption-signpost definitions and immutable snapshots.

This subordinate Analysis contract stores analyst review rules and dated
assessments. It does not fetch sources, evaluate observations automatically,
or promote results into another analytical layer.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from .world_state_history import fingerprint


ANALYSIS_ID = "WSAN-AU-IGR-20260921-001"
CANDIDATE_PATH = "data/analysis/STEP14G_AU_IGR_ASSUMPTION_SIGNPOSTS_REVIEW_PENDING.json"
REVIEW_PATH = "data/analysis/STEP14H_AU_IGR_ASSUMPTION_SIGNPOST_HUMAN_REVIEW_ACCEPTED.json"
TRANSACTION_PATH = "data/analysis/STEP14H_AU_IGR_ASSUMPTION_SIGNPOST_ADMISSION_TRANSACTION.json"
SCHEMA_PATH = "data/analysis/assumption_signposts_schema.json"
DEFINITIONS_PATH = "data/analysis/assumption_signpost_definitions.json"
GAPS_PATH = "data/analysis/assumption_signpost_coverage_gaps.json"
SNAPSHOTS_PATH = "data/analysis/assumption_signpost_assessment_snapshots.json"
REVIEW_ID = "WS-STEP14H-AU-IGR-SIGNPOST-REVIEW-20260929-001"
ADMISSION_ID = "WS-ASSUMPTION-SIGNPOST-ADMISSION-AU-IGR-20260929-001"
SNAPSHOT_ID = "WSASMSNAP-AU-IGR-20260928-001"
DEFINITION_SET_ID = "WSASMDSET-AU-IGR-20260929-001"
EVIDENCE_CUTOFF = "2026-09-28T20:32:40Z"
ANALYSIS_CUTOFF = "2026-09-28T16:25:00Z"
EXPECTED_CANDIDATE = "0d6fc09c1dd84dd8f009a39d01795a26efa9b580d9716160f47370a3db4f2f5b"
EXPECTED_MANIFEST = "2d5b7a6962cbfc4dfc404c7a37ebc002c714d4cf0d4a062f25d49ceb2a855186"
EXPECTED_ANALYSIS = "9e108606a6354ef8862f186db3418207155ff85f65e828079aeec616b8ee3ed0"
EXPECTED_EXTENSION = "96a00e77f7f9d43a59dafb4988c89cac933ce5cacd703f37399782f0be238668"
ASSUMPTION_SUFFIXES = {
    "AI_DIFFUSION", "ENERGY_TRANSITION", "FERTILITY", "HEALTH_COST",
    "MIGRATION", "PARTICIPATION", "PRODUCTIVITY", "TAX_CEILING",
}
OMITTED_SUFFIXES = {
    "MORTALITY", "INFLATION", "COMMODITY_PRICES", "DEBT_YIELDS",
    "AGED_CARE_COST", "NDIS_REFORMS", "RETIREMENT",
}
OBSERVATION_TYPES = {
    "LEVEL", "RATE", "TREND", "COMPOSITION", "POLICY_STATE",
    "IMPLEMENTATION_STATE", "MODEL_REVISION", "STRUCTURAL_BREAK_INDICATOR",
}
DIRECTIONS = {"CONSISTENT_WITH_ASSUMPTION", "IN_TENSION_WITH_ASSUMPTION", "AMBIGUOUS", "NOT_COMPARABLE"}
PRESENT_STATES = DIRECTIONS | {"NOT_ENOUGH_EVIDENCE"}
WORKFLOW_STATES = {"OBSERVE", "REVIEW_DUE", "STRUCTURAL_REASSESSMENT_REQUIRED"}
DEFINITION_FIELDS = {
    "signpost_id", "assumption_id", "metric_or_observation", "source_family",
    "observation_type", "comparison_basis", "observation_frequency",
    "minimum_persistence", "structural_break_condition", "review_trigger",
    "false_positive_risks", "source_refs", "limitations",
}


class SignpostError(ValueError):
    """A governed signpost contract or transaction failed closed."""


def _read(root: Path, relative: str) -> Any:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def _encoded(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or len(value) != 20 or not value.endswith("Z"):
        raise SignpostError(f"{label} must be second-precision UTC ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise SignpostError(f"{label} is invalid UTC") from exc
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise SignpostError(f"{label} must be UTC")
    return parsed


def _seal(value: dict[str, Any], field: str) -> dict[str, Any]:
    result = deepcopy(value)
    result[field] = fingerprint({key: item for key, item in result.items() if key != field})
    return result


def _dataset_hashes(root: Path) -> dict[str, str]:
    """Compact directory fingerprints for protected governed data."""
    groups = {
        "analysis_preexisting": (root / "data/analysis", {Path(REVIEW_PATH).name, Path(TRANSACTION_PATH).name,
            Path(SCHEMA_PATH).name, Path(DEFINITIONS_PATH).name, Path(GAPS_PATH).name, Path(SNAPSHOTS_PATH).name}),
        "canonical": (root / "data/canonical", set()),
        "sources": (root / "data/sources", set()),
        "live_intelligence": (root / "data/live_intelligence", set()),
        "signals": (root / "data/signals", set()),
        "world_state": (root / "data/world_state", set()),
        "relationships": (root / "data/relationships", set()),
        "forecasts": (root / "data/forecasts", set()),
        "scenarios": (root / "data/scenarios", set()),
        "risks": (root / "data/risks", set()),
        "outcomes": (root / "data/outcomes", set()),
        "monitor": (root / "data/monitor", set()),
    }
    result = {}
    for name, (directory, excluded_names) in groups.items():
        entries = {}
        if directory.exists():
            for path in sorted(directory.rglob("*")):
                if path.is_file() and path.name not in excluded_names:
                    entries[str(path.relative_to(root))] = _file_hash(path)
        result[name] = fingerprint(entries)
    # Public build inputs are protected; this tranche cannot change the site.
    web_entries = {}
    for path in sorted((root / "web").rglob("*")):
        if path.is_file():
            web_entries[str(path.relative_to(root))] = _file_hash(path)
    result["web"] = fingerprint(web_entries)
    return result


def human_dispositions() -> dict[str, Any]:
    return {
        "signpost_contract": "ACCEPT_INTERNAL",
        "operationalised_scope": "ACCEPT_OPERATIONALISED_SCOPE",
        "definition_set": "ACCEPT_INTERNAL",
        "minimum_persistence": "ACCEPT",
        "source_coverage_gaps": "ACCEPT_AS_GAPS_ONLY",
        "assessment_snapshot": "ACCEPT_AS_OF",
        "workflow_states": {suffix: "OBSERVE" for suffix in sorted(ASSUMPTION_SUFFIXES)},
        "historical_backtest": "DEFERRED",
        "monitoring": "NOT_AUTHORISED",
        "automated_retrieval": "NOT_AUTHORISED",
        "analysis_revision": "NOT_AUTHORISED",
        "world_state": "NOT_AUTHORISED",
        "relationship": "NOT_AUTHORISED",
        "forecast": "NOT_AUTHORISED",
        "scenario": "NOT_AUTHORISED",
        "risk": "NOT_AUTHORISED",
        "public_projection": "NOT_AUTHORISED",
    }


def _candidate(root: Path) -> dict[str, Any]:
    candidate = _read(root, CANDIDATE_PATH)
    actual = candidate.get("semantic_fingerprint")
    expected = fingerprint({key: value for key, value in candidate.items() if key != "semantic_fingerprint"})
    if actual != EXPECTED_CANDIDATE or actual != expected:
        raise SignpostError("Step 14G candidate semantic fingerprint mismatch")
    if candidate.get("source_manifest_sha256") != EXPECTED_MANIFEST or fingerprint(candidate.get("source_manifest")) != EXPECTED_MANIFEST:
        raise SignpostError("Step 14G source-manifest fingerprint mismatch")
    if candidate.get("candidate_as_of_utc") != EVIDENCE_CUTOFF or candidate.get("analysis_content_as_of_utc") != ANALYSIS_CUTOFF:
        raise SignpostError("Step 14G cutoffs differ from reviewed values")
    return candidate


def _analysis_anchor(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    reviews = _read(root, "data/analysis/event_reviews.json")
    review = next((row for row in reviews.get("reviews", []) if row.get("analysis_id") == ANALYSIS_ID), None)
    if review is None or review.get("review_state") != "REVIEWED" or review.get("analysis_as_of_utc") != ANALYSIS_CUTOFF:
        raise SignpostError("admitted IGR Analysis anchor missing or changed")
    if fingerprint(review) != EXPECTED_ANALYSIS:
        raise SignpostError("admitted IGR Analysis fingerprint mismatch")
    extension = review.get("official_projection_review")
    if not isinstance(extension, dict) or extension.get("visibility") != "INTERNAL_ONLY" or fingerprint(extension) != EXPECTED_EXTENSION:
        raise SignpostError("admitted IGR official-projection extension mismatch")
    assumptions = extension.get("model_assumptions")
    if not isinstance(assumptions, list):
        raise SignpostError("IGR model assumptions unavailable")
    ids = [row.get("assumption_id") for row in assumptions]
    if len(ids) != len(set(ids)):
        raise SignpostError("IGR assumption IDs are not unique")
    return review, extension


def validate_schema(schema: dict[str, Any]) -> list[str]:
    errors = []
    if schema.get("contract") != "WORLD_SIGNALS_ASSUMPTION_SIGNPOST" or schema.get("version") != "0.1":
        errors.append("generic production contract identity/version mismatch")
    if (schema.get("classification") != "INTERNAL_ONLY"
            or schema.get("definition_is_not_observation_or_promotion") is not True
            or any(schema.get(field) is not False for field in (
                "automatic_evaluation", "automatic_analysis_revision",
                "automatic_world_state_mutation", "automated_retrieval",
                "public_projection_permitted"))):
        errors.append("internal-only/no-automatic-promotion policy required")
    if schema.get("observation_types") != sorted(OBSERVATION_TYPES) or schema.get("evidence_directions") != sorted(DIRECTIONS):
        errors.append("controlled vocabulary mismatch")
    if schema.get("workflow_states") != sorted(WORKFLOW_STATES):
        errors.append("workflow vocabulary mismatch")
    if schema.get("prohibited_fields") != ["score", "grade", "rating", "probability", "pass_fail"]:
        errors.append("score/probability prohibition missing")
    return errors


def _validate_no_scoring(value: Any, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in {"score", "grade", "rating", "probability", "probabilities", "pass_fail"}:
                errors.append(f"prohibited assessment field: {key}")
            _validate_no_scoring(child, errors)
    elif isinstance(value, list):
        for child in value:
            _validate_no_scoring(child, errors)


def validate_stores(schema: dict[str, Any], definitions: dict[str, Any], gaps: dict[str, Any], snapshots: dict[str, Any]) -> list[str]:
    errors = validate_schema(schema)
    if definitions.get("contract") != schema.get("contract") or definitions.get("visibility") != "INTERNAL_ONLY":
        errors.append("definition store contract/visibility mismatch")
    defs = definitions.get("definitions")
    if not isinstance(defs, list) or not defs:
        errors.append("definitions must be a nonempty list")
        defs = []
    ids = [row.get("signpost_id") for row in defs if isinstance(row, dict)]
    assumptions = {row.get("assumption_id") for row in defs if isinstance(row, dict)}
    if len(ids) != len(defs) or len(ids) != len(set(ids)):
        errors.append("signpost IDs must be unique and all rows objects")
    for index, row in enumerate(defs):
        if set(row) != DEFINITION_FIELDS:
            errors.append(f"definition[{index}] does not match immutable definition fields")
        if row.get("observation_type") not in OBSERVATION_TYPES:
            errors.append(f"definition[{index}] observation type invalid")
        for field in ("metric_or_observation", "source_family", "comparison_basis", "observation_frequency", "minimum_persistence", "structural_break_condition", "review_trigger", "false_positive_risks"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append(f"definition[{index}].{field} required")
        if not isinstance(row.get("source_refs"), list) or not row["source_refs"] or not isinstance(row.get("limitations"), list) or not row["limitations"]:
            errors.append(f"definition[{index}] source_refs and limitations required")
    gap_rows = gaps.get("gaps")
    if gaps.get("classification") != "INTERNAL_ONLY" or not isinstance(gap_rows, list) or len(gap_rows) != 8:
        errors.append("exact eight internal source gaps required")
    if any(not isinstance(row, dict) or row.get("gap_code") != "SOURCE_COVERAGE_GAP" or row.get("route_created") is not False for row in (gap_rows or [])):
        errors.append("source coverage gaps must remain non-route gaps")
    if {row.get("assumption_id") for row in gap_rows or []} != assumptions:
        errors.append("source gap assumption refs differ from operationalised assumptions")
    snaps = snapshots.get("snapshots")
    if snapshots.get("classification") != "INTERNAL_ONLY" or not isinstance(snaps, list) or not snaps:
        errors.append("internal immutable assessment snapshots required")
        snaps = []
    snap_ids = [row.get("snapshot_id") for row in snaps if isinstance(row, dict)]
    if len(snap_ids) != len(snaps) or len(snap_ids) != len(set(snap_ids)):
        errors.append("snapshot IDs must be unique")
    definition_ids = set(ids)
    for snapshot in snaps:
        if snapshot.get("assessment_count") != 8 or len(snapshot.get("assessments", [])) != 8:
            errors.append("snapshot must contain exactly eight assumption assessments")
        if len(snapshot.get("signpost_assessments", [])) != len(defs):
            errors.append("snapshot must preserve each signpost evidence relationship")
        if {row.get("signpost_id") for row in snapshot.get("signpost_assessments", [])} != definition_ids:
            errors.append("snapshot signpost references do not resolve exactly")
        rows = snapshot.get("assessments", [])
        if {row.get("assumption_id") for row in rows} != assumptions:
            errors.append("snapshot assumptions do not resolve exactly")
        for row in rows:
            if row.get("present_evidence_state") not in PRESENT_STATES or row.get("workflow_state") not in WORKFLOW_STATES:
                errors.append("snapshot assessment vocabulary invalid")
        for row in snapshot.get("signpost_assessments", []):
            if row.get("evidence_relationship") not in DIRECTIONS:
                errors.append("snapshot signpost evidence relationship invalid")
        if snapshot.get("workflow_state_counts") != {"OBSERVE": 8, "REVIEW_DUE": 0, "STRUCTURAL_REASSESSMENT_REQUIRED": 0}:
            errors.append("snapshot workflow counts differ from accepted disposition")
        if snapshot.get("visibility") != "INTERNAL_ONLY" or snapshot.get("public_projection_permitted") is not False:
            errors.append("snapshot publication boundary invalid")
        try:
            evidence_at = _timestamp(snapshot.get("evidence_as_of_utc"), "evidence_as_of_utc")
            analysis_at = _timestamp(snapshot.get("analysis_content_as_of_utc"), "analysis_content_as_of_utc")
            reviewed_at = _timestamp(snapshot.get("reviewed_at_utc"), "reviewed_at_utc")
            admitted_at = _timestamp(snapshot.get("admitted_at_utc"), "admitted_at_utc")
            if not analysis_at <= evidence_at <= reviewed_at <= admitted_at:
                errors.append("snapshot cutoff/review/admission chronology invalid")
        except SignpostError as exc:
            errors.append(str(exc))
    _validate_no_scoring({"definitions": defs, "gaps": gap_rows, "snapshots": snaps}, errors)
    return list(dict.fromkeys(errors))


def _build_targets(root: Path, reviewed_at_utc: str, admitted_at_utc: str, decision: dict[str, Any] | None) -> dict[str, Any]:
    if decision != human_dispositions():
        raise SignpostError("exact explicit human disposition is required")
    reviewed = _timestamp(reviewed_at_utc, "reviewed_at_utc")
    admitted = _timestamp(admitted_at_utc, "admitted_at_utc")
    cutoff = _timestamp(EVIDENCE_CUTOFF, "evidence cutoff")
    analysis_cutoff = _timestamp(ANALYSIS_CUTOFF, "Analysis cutoff")
    if not analysis_cutoff <= cutoff <= reviewed <= admitted:
        raise SignpostError("content cutoff <= evidence cutoff <= review <= admission required")
    for relative in (REVIEW_PATH, TRANSACTION_PATH, SCHEMA_PATH, DEFINITIONS_PATH, GAPS_PATH, SNAPSHOTS_PATH):
        if (root / relative).exists():
            raise SignpostError(f"Step 14H target already exists: {relative}")
    candidate = _candidate(root)
    _, extension = _analysis_anchor(root)
    assumptions = {row["assumption_id"] for row in extension["model_assumptions"]}
    selected_ids = {row["assumption_id"] for row in candidate["selected_assumptions"]}
    expected_suffixes = {"WSASM-AU-IGR-2026-" + suffix for suffix in ASSUMPTION_SUFFIXES}
    omitted_ids = {row["assumption_id"] for row in candidate["omitted_assumptions"]}
    if selected_ids != expected_suffixes or not selected_ids <= assumptions or not omitted_ids == {"WSASM-AU-IGR-2026-" + suffix for suffix in OMITTED_SUFFIXES}:
        raise SignpostError("selected/omitted assumption scope drift")
    if len(candidate["signposts"]) != 15 or len(candidate["source_coverage_gaps"]) != 8:
        raise SignpostError("Step 14G population counts differ from accepted scope")
    if any(row["review_workflow_state"] != "OBSERVE" for row in candidate["selected_assumptions"]):
        raise SignpostError("all eight accepted workflow states must remain OBSERVE")

    schema = {
        "contract": "WORLD_SIGNALS_ASSUMPTION_SIGNPOST", "version": "0.1",
        "classification": "INTERNAL_ONLY", "definition_is_not_observation_or_promotion": True,
        "automatic_evaluation": False, "automatic_analysis_revision": False,
        "automatic_world_state_mutation": False, "automated_retrieval": False,
        "observation_types": sorted(OBSERVATION_TYPES), "evidence_directions": sorted(DIRECTIONS),
        "assessment_present_states": sorted(PRESENT_STATES), "workflow_states": sorted(WORKFLOW_STATES),
        "prohibited_fields": ["score", "grade", "rating", "probability", "pass_fail"],
        "snapshot_immutability": "APPEND_ONLY; future evidence creates a new snapshot",
        "knowledge_visibility": "snapshot visible only when admitted_at_utc <= knowledge_cutoff_utc",
        "public_projection_permitted": False,
    }
    definitions = []
    signpost_assessments = []
    for row in candidate["signposts"]:
        definitions.append({key: deepcopy(value) for key, value in row.items() if key in DEFINITION_FIELDS})
        signpost_assessments.append({
            "signpost_id": row["signpost_id"],
            "evidence_relationship": row["direction_of_evidence"],
            "evidence_refs": deepcopy(next(item["current_signpost_evidence"] for item in candidate["selected_assumptions"] if item["assumption_id"] == row["assumption_id"])),
            "evidence_as_of_utc": EVIDENCE_CUTOFF,
            "limitations": deepcopy(row["limitations"]),
        })
    definition_set = {
        "contract": "WORLD_SIGNALS_ASSUMPTION_SIGNPOST", "contract_version": "0.1",
        "definition_set_id": DEFINITION_SET_ID, "analysis_id": ANALYSIS_ID,
        "analysis_extension_sha256": EXPECTED_EXTENSION, "status": "ADMITTED",
        "source_manifest_sha256": EXPECTED_MANIFEST,
        "visibility": "INTERNAL_ONLY", "definitions": definitions,
        "definition_count": len(definitions), "revision_policy": "IMMUTABLE; explicit future revision/supersession transaction required",
    }
    gaps = {
        "contract": "WORLD_SIGNALS_ASSUMPTION_SIGNPOST_COVERAGE_GAP", "version": "0.1",
        "definition_set_id": DEFINITION_SET_ID, "classification": "INTERNAL_ONLY",
        "gaps": deepcopy(candidate["source_coverage_gaps"]), "gap_count": len(candidate["source_coverage_gaps"]),
        "route_created": False, "monitoring_authorised": False, "automated_retrieval_authorised": False,
    }
    assessments = []
    for row in candidate["selected_assumptions"]:
        assessments.append({
            "assumption_id": row["assumption_id"],
            "present_evidence_state": row["present_evidence_state"],
            "workflow_state": row["review_workflow_state"],
            "evidence_refs": deepcopy(row["current_signpost_evidence"]),
            "why": row["why"],
            "minimum_evidence_to_change_state": row["minimum_evidence_to_change_state"],
            "next_useful_observation": row["next_useful_observation"],
            "limitations": [row["limitation"]],
        })
    counts = {state: sum(row["workflow_state"] == state for row in assessments) for state in sorted(WORKFLOW_STATES)}
    snapshot = {
        "snapshot_id": SNAPSHOT_ID, "snapshot_revision": 1,
        "contract": "WORLD_SIGNALS_ASSUMPTION_SIGNPOST_ASSESSMENT_SNAPSHOT", "contract_version": "0.1",
        "definition_set_id": DEFINITION_SET_ID, "analysis_id": ANALYSIS_ID,
        "candidate_semantic_fingerprint": EXPECTED_CANDIDATE,
        "source_manifest_sha256": EXPECTED_MANIFEST,
        "analysis_sha256": EXPECTED_ANALYSIS,
        "analysis_extension_sha256": EXPECTED_EXTENSION,
        "evidence_as_of_utc": EVIDENCE_CUTOFF, "analysis_content_as_of_utc": ANALYSIS_CUTOFF,
        "review_id": REVIEW_ID, "admission_transaction_id": ADMISSION_ID,
        "reviewed_at_utc": reviewed_at_utc, "admitted_at_utc": admitted_at_utc,
        "assessment_count": len(assessments), "assessments": assessments,
        "signpost_assessments": signpost_assessments, "workflow_state_counts": counts,
        "historical_backtest_disposition": "DEFERRED",
        "visibility": "INTERNAL_ONLY", "public_projection_permitted": False,
        "immutable": True,
        "limitations": [
            "Assessment is strictly as of the evidence cutoff; later evidence requires a new immutable snapshot and human review.",
            "Workflow states direct analyst attention only and are not probability, confidence, severity, risk or truth labels.",
            "Coverage gaps do not create source routes, monitoring, polling or automated retrieval.",
            "No Analysis revision or downstream analytical promotion is authorised.",
        ],
    }
    snapshot["snapshot_sha256"] = fingerprint(snapshot)
    definition_set["definition_set_sha256"] = fingerprint(definition_set)
    targets = {SCHEMA_PATH: schema, DEFINITIONS_PATH: definition_set, GAPS_PATH: gaps,
               SNAPSHOTS_PATH: {"version": "0.1", "classification": "INTERNAL_ONLY", "snapshots": [snapshot]}}
    errors = validate_stores(schema, targets[DEFINITIONS_PATH], gaps, targets[SNAPSHOTS_PATH])
    if errors:
        raise SignpostError("constructed stores invalid: " + "; ".join(errors))

    review = _seal({
        "review_id": REVIEW_ID, "record_type": "ASSUMPTION_SIGNPOST_HUMAN_REVIEW",
        "reviewer_role": "PROJECT_OWNER_EXPLICIT_HUMAN_DECISION", "reviewed_at_utc": reviewed_at_utc,
        "decision_basis": "Accept the exact Step 14G signpost contract, selected scope and as-of assessment for internal governed production; no downstream or public authority.",
        "step14g_semantic_fingerprint": EXPECTED_CANDIDATE,
        "source_manifest_fingerprint": EXPECTED_MANIFEST,
        "analysis_id": ANALYSIS_ID, "analysis_sha256": EXPECTED_ANALYSIS,
        "official_projection_extension_sha256": EXPECTED_EXTENSION,
        "dispositions": human_dispositions(),
        "omitted_assumptions": deepcopy(candidate["omitted_assumptions"]),
        "visibility": "INTERNAL_ONLY", "public_projection_permitted": False,
        "write_targets": [DEFINITIONS_PATH, GAPS_PATH, SNAPSHOTS_PATH],
    }, "review_fingerprint")
    review_hash = review["review_fingerprint"]
    # The snapshot pins the human review fingerprint, not a mutable assessment.
    snapshot["human_review_fingerprint"] = review_hash
    snapshot["snapshot_sha256"] = fingerprint({key: value for key, value in snapshot.items() if key != "snapshot_sha256"})
    targets[SNAPSHOTS_PATH]["snapshots"] = [snapshot]
    definition_hash = definition_set["definition_set_sha256"]
    gap_hash = fingerprint(gaps["gaps"])
    pre_groups = _dataset_hashes(root)
    pre_targets = {relative: None for relative in (*targets.keys(), REVIEW_PATH, TRANSACTION_PATH)}
    post_hashes = {relative: hashlib.sha256(_encoded(value).encode("utf-8")).hexdigest() for relative, value in targets.items()}
    post_hashes[REVIEW_PATH] = hashlib.sha256(_encoded(review).encode("utf-8")).hexdigest()
    transaction = {
        "transaction_id": ADMISSION_ID, "transaction_type": "ASSUMPTION_SIGNPOST_PRODUCTION_ADMISSION",
        "contract_version": "0.1", "review_id": REVIEW_ID, "review_fingerprint": review_hash,
        "step14g_semantic_fingerprint": EXPECTED_CANDIDATE, "source_manifest_fingerprint": EXPECTED_MANIFEST,
        "analysis_id": ANALYSIS_ID, "analysis_sha256": EXPECTED_ANALYSIS,
        "official_projection_extension_sha256": EXPECTED_EXTENSION,
        "definition_set_id": DEFINITION_SET_ID, "definition_set_sha256": definition_hash,
        "signpost_count": len(definitions), "coverage_gap_set_sha256": gap_hash,
        "assessment_snapshot_id": SNAPSHOT_ID, "assessment_snapshot_sha256": snapshot["snapshot_sha256"],
        "reviewed_at_utc": reviewed_at_utc, "admitted_at_utc": admitted_at_utc,
        "pre_state_hashes": {"governed_data_groups": pre_groups, "new_targets_absent": pre_targets},
        "post_state_hashes": post_hashes,
        "write_targets": [SCHEMA_PATH, DEFINITIONS_PATH, GAPS_PATH, SNAPSHOTS_PATH, REVIEW_PATH, TRANSACTION_PATH],
        "visibility": "INTERNAL_ONLY", "public_projection_permitted": False,
        "monitoring_routes_created": 0, "automated_retrieval_authorised": False,
        "analysis_revision_created": False,
        "downstream_write_targets": [],
    }
    transaction["transaction_fingerprint"] = fingerprint(transaction)
    targets[REVIEW_PATH] = review
    targets[TRANSACTION_PATH] = transaction
    return targets


def _validate_materialized(root: Path, *, exact_post_state: bool = True) -> None:
    schema, definitions = _read(root, SCHEMA_PATH), _read(root, DEFINITIONS_PATH)
    gaps, snapshots = _read(root, GAPS_PATH), _read(root, SNAPSHOTS_PATH)
    review, tx = _read(root, REVIEW_PATH), _read(root, TRANSACTION_PATH)
    if not isinstance(snapshots.get("snapshots"), list) or len(snapshots["snapshots"]) != 1:
        raise SignpostError("v0.1 reader accepts only its singly admitted snapshot; a successor needs a separate admission contract")
    errors = validate_stores(schema, definitions, gaps, snapshots)
    if errors:
        raise SignpostError("production validation failed: " + "; ".join(errors))
    if tx.get("transaction_fingerprint") != fingerprint({key: value for key, value in tx.items() if key != "transaction_fingerprint"}):
        raise SignpostError("admission transaction fingerprint mismatch")
    if review.get("review_fingerprint") != fingerprint({key: value for key, value in review.items() if key != "review_fingerprint"}):
        raise SignpostError("human review fingerprint mismatch")
    if review.get("review_id") != REVIEW_ID or review.get("record_type") != "ASSUMPTION_SIGNPOST_HUMAN_REVIEW" or review.get("dispositions") != human_dispositions():
        raise SignpostError("human review identity or decision differs from explicit authority")
    if review.get("visibility") != "INTERNAL_ONLY" or review.get("public_projection_permitted") is not False:
        raise SignpostError("human review publication boundary invalid")
    if tx.get("review_fingerprint") != review.get("review_fingerprint") or tx.get("review_id") != REVIEW_ID:
        raise SignpostError("admission transaction does not pin human review")
    if tx.get("transaction_id") != ADMISSION_ID or tx.get("public_projection_permitted") is not False or tx.get("write_targets") != [SCHEMA_PATH, DEFINITIONS_PATH, GAPS_PATH, SNAPSHOTS_PATH, REVIEW_PATH, TRANSACTION_PATH]:
        raise SignpostError("admission transaction scope mismatch")
    if tx.get("visibility") != "INTERNAL_ONLY" or tx.get("monitoring_routes_created") != 0 or tx.get("automated_retrieval_authorised") is not False or tx.get("analysis_revision_created") is not False or tx.get("downstream_write_targets") != []:
        raise SignpostError("admission transaction exceeds authorised scope")
    candidate = _candidate(root)
    _analysis_anchor(root)
    if _dataset_hashes(root) != tx.get("pre_state_hashes", {}).get("governed_data_groups"):
        raise SignpostError("protected governed input hashes changed")
    if snapshots["snapshots"][0].get("snapshot_sha256") != tx.get("assessment_snapshot_sha256"):
        raise SignpostError("snapshot fingerprint does not resolve")
    snapshot = snapshots["snapshots"][0]
    if snapshot.get("snapshot_sha256") != fingerprint({key: value for key, value in snapshot.items() if key != "snapshot_sha256"}):
        raise SignpostError("snapshot semantic fingerprint mismatch")
    if definitions.get("definition_set_sha256") != tx.get("definition_set_sha256"):
        raise SignpostError("definition-set fingerprint does not resolve")
    if definitions.get("definition_set_sha256") != fingerprint({key: value for key, value in definitions.items() if key != "definition_set_sha256"}):
        raise SignpostError("definition-set semantic fingerprint mismatch")
    if fingerprint(gaps.get("gaps")) != tx.get("coverage_gap_set_sha256"):
        raise SignpostError("coverage-gap set fingerprint mismatch")
    if snapshot.get("snapshot_id") != tx.get("assessment_snapshot_id") or snapshot.get("reviewed_at_utc") != tx.get("reviewed_at_utc") or snapshot.get("admitted_at_utc") != tx.get("admitted_at_utc"):
        raise SignpostError("snapshot identity or transaction times mismatch")
    if (definitions.get("definition_set_id") != DEFINITION_SET_ID
            or definitions.get("analysis_id") != ANALYSIS_ID
            or definitions.get("source_manifest_sha256") != EXPECTED_MANIFEST
            or definitions.get("definitions") != [
                {key: deepcopy(value) for key, value in row.items() if key in DEFINITION_FIELDS}
                for row in candidate["signposts"]]):
        raise SignpostError("production definitions differ from the accepted Step 14G contract")
    if gaps.get("gaps") != candidate.get("source_coverage_gaps"):
        raise SignpostError("production source gaps differ from the accepted Step 14G package")
    if (review.get("step14g_semantic_fingerprint") != EXPECTED_CANDIDATE
            or review.get("source_manifest_fingerprint") != EXPECTED_MANIFEST
            or review.get("analysis_sha256") != EXPECTED_ANALYSIS
            or review.get("official_projection_extension_sha256") != EXPECTED_EXTENSION
            or review.get("omitted_assumptions") != candidate.get("omitted_assumptions")
            or review.get("write_targets") != [DEFINITIONS_PATH, GAPS_PATH, SNAPSHOTS_PATH]):
        raise SignpostError("human review lineage, omissions or scope mismatch")
    if (tx.get("step14g_semantic_fingerprint") != EXPECTED_CANDIDATE
            or tx.get("source_manifest_fingerprint") != EXPECTED_MANIFEST
            or tx.get("analysis_sha256") != EXPECTED_ANALYSIS
            or tx.get("official_projection_extension_sha256") != EXPECTED_EXTENSION
            or tx.get("definition_set_id") != DEFINITION_SET_ID
            or tx.get("signpost_count") != 15):
        raise SignpostError("admission transaction source pins mismatch")
    review_time = _timestamp(review.get("reviewed_at_utc"), "human review time")
    admitted_time = _timestamp(tx.get("admitted_at_utc"), "admission time")
    if (review.get("reviewed_at_utc") != tx.get("reviewed_at_utc")
            or review_time > admitted_time):
        raise SignpostError("human review and admission chronology mismatch")
    expected_assessments = [{
        "assumption_id": row["assumption_id"],
        "present_evidence_state": row["present_evidence_state"],
        "workflow_state": row["review_workflow_state"],
        "evidence_refs": deepcopy(row["current_signpost_evidence"]),
        "why": row["why"],
        "minimum_evidence_to_change_state": row["minimum_evidence_to_change_state"],
        "next_useful_observation": row["next_useful_observation"],
        "limitations": [row["limitation"]],
    } for row in candidate["selected_assumptions"]]
    by_assumption = {row["assumption_id"]: row for row in candidate["selected_assumptions"]}
    expected_signpost_assessments = [{
        "signpost_id": row["signpost_id"],
        "evidence_relationship": row["direction_of_evidence"],
        "evidence_refs": deepcopy(by_assumption[row["assumption_id"]]["current_signpost_evidence"]),
        "evidence_as_of_utc": EVIDENCE_CUTOFF,
        "limitations": deepcopy(row["limitations"]),
    } for row in candidate["signposts"]]
    if (snapshot.get("assessments") != expected_assessments
            or snapshot.get("signpost_assessments") != expected_signpost_assessments
            or snapshot.get("candidate_semantic_fingerprint") != EXPECTED_CANDIDATE
            or snapshot.get("source_manifest_sha256") != EXPECTED_MANIFEST
            or snapshot.get("analysis_sha256") != EXPECTED_ANALYSIS
            or snapshot.get("analysis_extension_sha256") != EXPECTED_EXTENSION):
        raise SignpostError("assessment snapshot differs from the accepted as-of candidate")
    for relative in (SCHEMA_PATH, DEFINITIONS_PATH, GAPS_PATH, REVIEW_PATH):
        expected_hash = tx.get("post_state_hashes", {}).get(relative)
        if not expected_hash or _file_hash(root / relative) != expected_hash:
            raise SignpostError(f"immutable admitted file hash mismatch: {relative}")
    source_ids = {row["source_id"] for row in candidate["source_manifest"]}
    for definition in definitions["definitions"]:
        if any(ref.get("source_id") not in source_ids for ref in definition["source_refs"]):
            raise SignpostError("definition source reference is outside the pinned manifest")
    for assessment in snapshots["snapshots"][0]["signpost_assessments"]:
        if any(ref not in source_ids for ref in assessment["evidence_refs"]):
            raise SignpostError("snapshot evidence reference is outside the pinned manifest")
    if exact_post_state:
        for relative, expected in tx["post_state_hashes"].items():
            if _file_hash(root / relative) != expected:
                raise SignpostError(f"post-state file hash mismatch: {relative}")


def get_signpost(root: Path, signpost_id: str) -> dict[str, Any]:
    _validate_materialized(root, exact_post_state=False)
    definitions = _read(root, DEFINITIONS_PATH)["definitions"]
    found = [row for row in definitions if row.get("signpost_id") == signpost_id]
    if len(found) != 1:
        raise SignpostError("signpost ID missing or non-unique")
    return deepcopy(found[0])


def list_signposts_for_assumption(root: Path, assumption_id: str) -> list[dict[str, Any]]:
    _validate_materialized(root, exact_post_state=False)
    return [deepcopy(row) for row in _read(root, DEFINITIONS_PATH)["definitions"] if row.get("assumption_id") == assumption_id]


def get_snapshot_by_id(root: Path, snapshot_id: str) -> dict[str, Any]:
    _validate_materialized(root, exact_post_state=False)
    rows = [row for row in _read(root, SNAPSHOTS_PATH)["snapshots"] if row.get("snapshot_id") == snapshot_id]
    if len(rows) != 1:
        raise SignpostError("snapshot ID missing or non-unique")
    return deepcopy(rows[0])


def latest_snapshot_as_of(root: Path, knowledge_cutoff_utc: str) -> dict[str, Any] | None:
    _validate_materialized(root, exact_post_state=False)
    cutoff = _timestamp(knowledge_cutoff_utc, "knowledge_cutoff_utc")
    rows = _read(root, SNAPSHOTS_PATH)["snapshots"]
    eligible = [row for row in rows if _timestamp(row.get("admitted_at_utc"), "admitted_at_utc") <= cutoff]
    if not eligible:
        return None
    eligible.sort(key=lambda row: (row["admitted_at_utc"], row["snapshot_id"]))
    return deepcopy(eligible[-1])


def build_human_review_brief(root: Path) -> str:
    """Render a concise internal audit summary from the immutable admitted set."""
    _validate_materialized(root, exact_post_state=False)
    definitions = _read(root, DEFINITIONS_PATH)
    gaps = _read(root, GAPS_PATH)
    snapshot = _read(root, SNAPSHOTS_PATH)["snapshots"][0]
    lines = [
        "# Step 14H — IGR assumption signposts (internal, admitted)", "",
        f"- Definition set: `{definitions['definition_set_id']}` ({definitions['definition_count']} definitions)",
        f"- Assessment snapshot: `{snapshot['snapshot_id']}`",
        f"- Evidence cutoff: `{snapshot['evidence_as_of_utc']}`",
        f"- Analysis content cutoff: `{snapshot['analysis_content_as_of_utc']}`",
        f"- Workflow states: `{snapshot['workflow_state_counts']}`",
        f"- Source coverage gaps: {len(gaps['gaps'])}; routes created: `false`",
        "- Historical backtest: `DEFERRED`", "- Visibility: `INTERNAL_ONLY`",
        "- Public projection, monitoring, automated retrieval and downstream promotion: not authorised.",
        "", "| Assumption | Evidence relationship | Workflow |", "|---|---|---|",
    ]
    for row in snapshot["assessments"]:
        lines.append(f"| `{row['assumption_id'].rsplit('-', 1)[-1]}` | {row['present_evidence_state']} | {row['workflow_state']} |")
    lines.extend(["", "This records analyst attention as of the pinned cutoff; it is not an observation, Forecast, Scenario, Risk, Relationship, Signal, World State assessment, or automatic Analysis revision.", ""])
    return "\n".join(lines)


def build_transaction(root: Path, reviewed_at_utc: str, admitted_at_utc: str, *, decision: dict[str, Any] | None) -> dict[str, Any]:
    """Construct proposed exact write payloads without writing."""
    return _build_targets(root, reviewed_at_utc, admitted_at_utc, decision)


def materialize(root: Path, targets: dict[str, Any]) -> None:
    """Simulate then bounded-materialise the six explicitly authorised files."""
    expected = {SCHEMA_PATH, DEFINITIONS_PATH, GAPS_PATH, SNAPSHOTS_PATH, REVIEW_PATH, TRANSACTION_PATH}
    if set(targets) != expected:
        raise SignpostError("exact Step 14H write target set required")
    if any((root / item).exists() for item in expected):
        raise SignpostError("Step 14H production target collision")
    tx = targets[TRANSACTION_PATH]
    if _dataset_hashes(root) != tx["pre_state_hashes"]["governed_data_groups"]:
        raise SignpostError("protected pre-state changed after construction")
    import shutil
    from .world_state_admission import _atomic_materialize
    with __import__("tempfile").TemporaryDirectory(prefix="ws14h-simulation-") as directory:
        staged = Path(directory)
        shutil.copytree(root / "data", staged / "data")
        if (root / "web").exists():
            shutil.copytree(root / "web", staged / "web")
        _atomic_materialize({staged / relative: _encoded(value) for relative, value in targets.items()})
        _validate_materialized(staged, exact_post_state=True)
    _atomic_materialize({root / relative: _encoded(value) for relative, value in targets.items()})
    try:
        _validate_materialized(root, exact_post_state=True)
    except Exception:
        # No partially admitted production population survives a failed check.
        for relative in expected:
            (root / relative).unlink(missing_ok=True)
        raise
