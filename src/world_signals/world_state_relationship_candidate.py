"""Read-only Step 12A Relationship candidate construction and validation."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from .relationships import (
    RelationshipValidationReport,
    validate_temporal_dependency_dag,
    validate_relationship_history,
)


class WorldStateRelationshipCandidateError(ValueError):
    """Raised when the bounded RBNZ Relationship candidate is not admissible for review."""


RELATIONSHIP_ID = "WSREL-NZ-RBNZ-OCR-MARKET-REPRICING-202609-001"
REVISION_ID = f"{RELATIONSHIP_ID}-R1"
ANALYSIS_ID = "WSAN-NZ-OCR-20260902-001"
MACRO_ID = "WSDIM-MACRO-NZ-RBNZ-OCR-202609-001"
MACRO_REVISION_ID = f"{MACRO_ID}-R1"
MACRO_HASH = "646ceafdba6324c421c2dceb9285d8fa4c0ecdec9df5558e369d05c261699e89"
MARKETS_ID = "WSDIM-MARKETS-NZ-RBNZ-OCR-202609-001"
MARKETS_REVISION_ID = f"{MARKETS_ID}-R1"
MARKETS_HASH = "a209a5958635dc1d95dd45214eec29d6a0ba76d1d8eefa252f16406dad673914"
ADMISSION_ID = "WS-ADMISSION-NZ-RBNZ-OCR-20260928-001"
ANALYSIS_HASH = "26dd13a0b120c18995355705512f6c1fae2cbe65d93b2211a2613fe5cb6780d1"
RBNZ_EVIDENCE_ID = "WSEV-NZ-OCR-RBNZ-20260902"
RBNZ_EVIDENCE_HASH = "60b2a70362a6412cba8be7a91735fa99d5c614da082fa64283baeb84ea1900da"
REUTERS_EVIDENCE_ID = "WSEV-NZ-OCR-REUTERS-20260902"
REUTERS_EVIDENCE_HASH = "a8458f7c845a32c97a2f1e359f3bb413f6a078466210f11154098b30c639fd47"
BT_EVIDENCE_ID = "WSEV-NZ-OCR-BT-20260902"
BT_EVIDENCE_HASH = "0b7614e5e21dae7117969f24c62d2799162dc9bd807e6290523b8f902580648e"
DEFAULT_CREATED_AT = "2026-09-28T07:22:06Z"


def semantic_fingerprint(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def _load(root: Path, relative: str) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def _parse_utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise WorldStateRelationshipCandidateError(f"invalid UTC timestamp: {value}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise WorldStateRelationshipCandidateError(f"timestamp must be UTC: {value}")
    return parsed.astimezone(timezone.utc)


def _find(rows: list[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
    row = next((item for item in rows if item.get(key) == value), None)
    if row is None:
        raise WorldStateRelationshipCandidateError(f"missing governed {key}: {value}")
    return row


def _manifest_entry(layer: str, object_id: str, object_sha256: str, revision_id: str | None = None) -> dict[str, Any]:
    return {
        "layer": layer,
        "object_id": object_id,
        "revision_id": revision_id,
        "object_sha256": object_sha256,
    }


def _node(component: dict[str, Any]) -> dict[str, Any]:
    return {
        "node_id": component["component_id"],
        "node_type": "WORLD_STATE_COMPONENT",
        "revision_id": component["revision_id"],
        "object_sha256": component["object_sha256"],
        "component_type": component["component_type"],
        "dimension": component["dimension"],
        "admitted_at_utc": component["admitted_at_utc"],
        "admission_transaction_id": component["admission_transaction_id"],
    }


def _support_pin(component: dict[str, Any]) -> dict[str, Any]:
    return {
        "node_type": "WORLD_STATE_COMPONENT",
        "node_id": component["component_id"],
        "revision_id": component["revision_id"],
        "object_sha256": component["object_sha256"],
    }


def _candidate_row(macro: dict[str, Any], markets: dict[str, Any], evidence: dict[str, Any], created_at_utc: str) -> dict[str, Any]:
    evidence_pins = [
        {"evidence_id": RBNZ_EVIDENCE_ID, "object_sha256": RBNZ_EVIDENCE_HASH},
        {"evidence_id": REUTERS_EVIDENCE_ID, "object_sha256": REUTERS_EVIDENCE_HASH},
        {"evidence_id": BT_EVIDENCE_ID, "object_sha256": BT_EVIDENCE_HASH},
    ]
    row = {
        "relationship_id": RELATIONSHIP_ID,
        "revision_id": REVISION_ID,
        "revision_number": 1,
        "previous_revision_id": None,
        "title": "RBNZ forward-path information and reported market repricing",
        "source_nodes": [_node(macro)],
        "target_nodes": [_node(markets)],
        "supporting_node_revisions": [_support_pin(macro), _support_pin(markets)],
        "supporting_analysis_refs": [{"analysis_id": ANALYSIS_ID, "object_sha256": ANALYSIS_HASH}],
        "supporting_observation_ids": [],
        "supporting_evidence_refs": [RBNZ_EVIDENCE_ID, REUTERS_EVIDENCE_ID, BT_EVIDENCE_ID],
        "supporting_evidence_pins": evidence_pins,
        "contradictory_evidence_refs": [],
        "contextual_canonical_occurrence_ids": [],
        "relationship_class": "ASSOCIATION",
        "directionality": "DIRECTED",
        "directionality_rationale": "The reviewed policy-path information precedes the source-reported market response window; direction is analytical ordering, not causal proof.",
        "domains": ["MACROECONOMIC_FINANCIAL_CONDITIONS", "MARKETS_AS_SENSORS"],
        "jurisdictions": ["New Zealand"],
        "rationale": "The expected 25 basis-point hike is not the surprise. The reviewed proposition concerns a more gradual forward path than market pricing and source-reported lower two-year swap and NZD pricing in the immediate/same-session window.",
        "mechanism": "NOT_ASSERTED_AT_ASSOCIATION_CLASS",
        "alternative_explanations": [
            "Global oil and geopolitical shocks may have driven or contaminated longer-duration rates independently of the domestic decision.",
            "A global bond-market sell-off may explain part of the market movement.",
            "The NZD had already weakened before the decision, and no high-frequency reconstruction is available.",
        ],
        "confounders": [
            "Simultaneous global rates repricing.",
            "Oil/geopolitical inflation shock.",
            "Pre-existing currency movement and source-reported rather than independently reconstructed event windows.",
        ],
        "common_driver_signal_ids": [],
        "causal_basis": [],
        "confidence": "MEDIUM",
        "temporal_scope": {
            "scope_type": "HISTORICAL_PERIOD",
            "precision": "SOURCE_REPORTED_WINDOW",
            "anchor_at_utc": "2026-09-02T02:00:00Z",
            "start_at_utc": None,
            "end_at_utc": None,
            "start_date": "2026-09-02",
            "end_date": "2026-09-02",
            "notes": "The RBNZ release is the event anchor. Market-response onset and end remain unknown within the source-reported immediate/same-session window; no exact temporal onset is manufactured.",
        },
        "first_asserted_at_utc": created_at_utc,
        "review_state": "UNDER_REVIEW",
        "lifecycle_state": "UNRESOLVED",
        "falsification_conditions": [
            "High-frequency swap or FX data show the reported moves materially preceded the RBNZ release.",
            "Later evidence shows the short-end move was primarily driven by a simultaneous global rates catalyst rather than the RBNZ path.",
            "The market had priced an OCR path at or below the RBNZ projection immediately before the decision.",
        ],
        "review_provenance": {
            "created_by": "world-state-step12a-rbnz-relationship-candidate-v1",
            "created_at_utc": created_at_utc,
            "reviewed_by": None,
            "reviewed_at_utc": None,
            "decision_basis": None,
        },
        "revision_reason": "Initial review-pending association candidate over two independently admitted World State component revisions; no production Relationship admission.",
    }
    return row


def _candidate_without_fingerprint(candidate: dict[str, Any]) -> dict[str, Any]:
    value = deepcopy(candidate)
    value.pop("candidate_semantic_fingerprint", None)
    return value


def build_rbnz_relationship_candidate(root: Path, *, created_at_utc: str = DEFAULT_CREATED_AT) -> dict[str, Any]:
    """Construct the bounded candidate from exact admitted lineage without writing."""
    _parse_utc(created_at_utc)
    schema = _load(root, "data/relationships/schema_v0.2.json")
    components_dataset = _load(root, "data/world_state/components.json")
    admissions_dataset = _load(root, "data/world_state/admission_transactions.json")
    event_reviews = _load(root, "data/analysis/event_reviews.json")
    evidence_dataset = _load(root, "data/analysis/evidence_registry.json")
    components = components_dataset["components"]
    macro = _find(components, "component_id", MACRO_ID)
    markets = _find(components, "component_id", MARKETS_ID)
    for component, expected_hash in ((macro, MACRO_HASH), (markets, MARKETS_HASH)):
        actual_hash = semantic_fingerprint({key: value for key, value in component.items() if key != "object_sha256"})
        if component.get("object_sha256") != actual_hash or component.get("object_sha256") != expected_hash:
            raise WorldStateRelationshipCandidateError(f"World State component hash mismatch: {component.get('component_id')}")
    admission = _find(admissions_dataset["transactions"], "transaction_id", ADMISSION_ID)
    analysis = _find(event_reviews["reviews"], "analysis_id", ANALYSIS_ID)
    evidence = {row["evidence_id"]: row for row in evidence_dataset["evidence"]}
    for identifier in (RBNZ_EVIDENCE_ID, REUTERS_EVIDENCE_ID, BT_EVIDENCE_ID):
        _find(event_reviews["reviews"], "analysis_id", ANALYSIS_ID)
        if identifier not in evidence:
            raise WorldStateRelationshipCandidateError(f"missing Analysis evidence: {identifier}")

    manifest = [
        _manifest_entry("WORLD_STATE", macro["component_id"], MACRO_HASH, macro["revision_id"]),
        _manifest_entry("WORLD_STATE", markets["component_id"], MARKETS_HASH, markets["revision_id"]),
        _manifest_entry("WORLD_STATE_ADMISSION", ADMISSION_ID, semantic_fingerprint(admission)),
        _manifest_entry("ANALYSIS", ANALYSIS_ID, ANALYSIS_HASH),
        _manifest_entry("ANALYSIS_EVIDENCE", RBNZ_EVIDENCE_ID, RBNZ_EVIDENCE_HASH),
        _manifest_entry("ANALYSIS_EVIDENCE", REUTERS_EVIDENCE_ID, REUTERS_EVIDENCE_HASH),
        _manifest_entry("ANALYSIS_EVIDENCE", BT_EVIDENCE_ID, BT_EVIDENCE_HASH),
    ]
    manifest.sort(key=lambda item: (item["layer"], item["object_id"], item.get("revision_id") or ""))
    manifest_sha256 = semantic_fingerprint(manifest)
    row = _candidate_row(macro, markets, evidence, created_at_utc)
    combined_evidence = {
        "evidence": [
            *(_load(root, "data/live_intelligence/evidence_registry.json").get("evidence", [])),
            *evidence_dataset["evidence"],
        ]
    }
    signals = _load(root, "data/signals/signals.json")
    observations = _load(root, "data/live_intelligence/observations.json")
    canonical = _load(root, "data/canonical/registry.json")
    report = validate_relationship_history(
        schema,
        [row],
        signals,
        observations,
        combined_evidence,
        canonical,
        world_state_components=components_dataset,
        world_state_admissions=admissions_dataset,
    )
    if not report.ok:
        raise WorldStateRelationshipCandidateError("Relationship candidate validation failed: " + "; ".join(report.errors))
    dag = validate_temporal_dependency_dag([
        {"source": {"node_type": "WORLD_STATE_COMPONENT", "node_id": MACRO_ID, "revision_id": MACRO_REVISION_ID}, "target": {"node_type": "RELATIONSHIP", "node_id": RELATIONSHIP_ID, "revision_id": REVISION_ID}},
        {"source": {"node_type": "WORLD_STATE_COMPONENT", "node_id": MARKETS_ID, "revision_id": MARKETS_REVISION_ID}, "target": {"node_type": "RELATIONSHIP", "node_id": RELATIONSHIP_ID, "revision_id": REVISION_ID}},
    ])
    if not dag.ok:
        raise WorldStateRelationshipCandidateError("Relationship dependency DAG failed: " + "; ".join(dag.errors))
    candidate = {
        "candidate_type": "RELATIONSHIP_REVIEW_CANDIDATE",
        "contract_version": schema["version"],
        "proposal_id": "WS-STEP12A-RBNZ-RELATIONSHIP-202609",
        "relationship": row,
        "source_manifest": manifest,
        "source_manifest_sha256": manifest_sha256,
        "endpoint_current_use": [
            {"component_id": MACRO_ID, "status": "NO_CURRENTNESS_CLAIM"},
            {"component_id": MARKETS_ID, "status": "NO_CURRENTNESS_CLAIM"},
        ],
        "dependency_dag_check": {"status": "PASS", "production_write_targets": []},
        "review_state": "UNDER_REVIEW",
        "lifecycle_state": "UNRESOLVED",
        "visibility": "INTERNAL_ONLY",
        "candidate_disposition": "READY_FOR_HUMAN_RELATIONSHIP_REVIEW",
        "production_write_targets": [],
        "public_projection_permitted": False,
        "production_relationship_admitted": False,
        "limitations": [
            "Association is not causal evidence or a mechanistically supported transmission claim.",
            "Analysis and evidence remain supporting lineage, never endpoint nodes.",
            "Endpoint current-use status does not make this historical candidate a current transmission channel.",
            "The production Relationship population remains closed pending Step 12B human review.",
        ],
    }
    candidate["candidate_semantic_fingerprint"] = semantic_fingerprint(_candidate_without_fingerprint(candidate))
    return candidate


def _current_manifest(root: Path, candidate: dict[str, Any]) -> list[dict[str, Any]]:
    components = _load(root, "data/world_state/components.json")["components"]
    admissions = _load(root, "data/world_state/admission_transactions.json")["transactions"]
    analyses = _load(root, "data/analysis/event_reviews.json")["reviews"]
    evidence = _load(root, "data/analysis/evidence_registry.json")["evidence"]
    indexes = {
        "WORLD_STATE": {
            row["component_id"]: semantic_fingerprint({key: value for key, value in row.items() if key != "object_sha256"})
            for row in components
        },
        "WORLD_STATE_ADMISSION": {row["transaction_id"]: semantic_fingerprint(row) for row in admissions},
        "ANALYSIS": {row["analysis_id"]: semantic_fingerprint(row) for row in analyses},
        "ANALYSIS_EVIDENCE": {row["evidence_id"]: semantic_fingerprint(row) for row in evidence},
    }
    current = []
    for entry in candidate["source_manifest"]:
        current.append({**entry, "object_sha256": indexes[entry["layer"]].get(entry["object_id"])})
    current.sort(key=lambda item: (item["layer"], item["object_id"], item.get("revision_id") or ""))
    return current


def validate_rbnz_relationship_candidate(candidate: dict[str, Any], root: Path) -> RelationshipValidationReport:
    """Verify the retained candidate against current governed inputs without writing."""
    errors: list[str] = []
    try:
        rebuilt = build_rbnz_relationship_candidate(root, created_at_utc=candidate["relationship"]["review_provenance"]["created_at_utc"])
    except (KeyError, TypeError, WorldStateRelationshipCandidateError) as exc:
        return RelationshipValidationReport((str(exc),))
    expected = candidate.get("candidate_semantic_fingerprint")
    actual = semantic_fingerprint(_candidate_without_fingerprint(candidate))
    if expected != actual:
        errors.append("candidate semantic fingerprint mismatch")
    if candidate.get("source_manifest_sha256") != semantic_fingerprint(candidate.get("source_manifest")):
        errors.append("source manifest fingerprint mismatch")
    if candidate.get("source_manifest") != _current_manifest(root, candidate):
        errors.append("source manifest no longer matches governed inputs")
    if rebuilt.get("candidate_semantic_fingerprint") != expected:
        errors.append("candidate is not reproducible from current governed inputs")
    if candidate.get("review_state") != "UNDER_REVIEW" or candidate.get("lifecycle_state") != "UNRESOLVED":
        errors.append("candidate must remain review-pending and unresolved")
    if candidate.get("production_write_targets") != [] or candidate.get("public_projection_permitted") is not False:
        errors.append("candidate must have no production write targets and no public permission")
    if candidate.get("production_relationship_admitted") is not False:
        errors.append("candidate must not be admitted")
    if candidate.get("candidate_disposition") != "READY_FOR_HUMAN_RELATIONSHIP_REVIEW":
        errors.append("candidate disposition is not ready for human review")
    return RelationshipValidationReport(tuple(errors))
