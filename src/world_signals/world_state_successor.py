"""Lineage-aware, read-only World State successor review.

This module starts with an admitted component's exact production lineage and
compares that lineage with the governed repository state at an explicit
knowledge cutoff.  It never treats caller assertions, domain similarity, or
time passing as governed evidence and never writes production state.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from .world_state_admission import load_production_state, validate_production_state
from .world_state_history import (
    fingerprint,
    validate_component_history,
    validate_snapshot_candidate,
    with_object_fingerprint,
)
from .world_state_production import derive_freshness, semantic_fingerprint


ROOT = Path(__file__).resolve().parents[2]
SUCCESSOR_PACKET_VERSION = "0.1"
SUCCESSOR_DISPOSITIONS = {
    "NO_SUCCESSOR_NEEDED",
    "REVIEW_DUE_NO_NEW_EVIDENCE",
    "UPSTREAM_SIGNAL_REVISION_ADVANCED",
    "NEW_ASSOCIATED_GOVERNED_EVIDENCE",
    "CORRECTION_OR_RETRACTION_REQUIRES_REVIEW",
    "CONTRADICTION_REQUIRES_REVIEW",
    "UPSTREAM_LINEAGE_UNRESOLVED",
    "NO_ADMITTED_COMPONENT",
}
SUCCESSOR_REVISION_KINDS = {"UPDATE", "CORRECTION", "SUPERSESSION"}


class WorldStateSuccessorReviewError(ValueError):
    """Raised when a successor review cannot be made safely."""


def _parse_utc(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or len(value) != 20 or not value.endswith("Z"):
        raise WorldStateSuccessorReviewError(f"{field} must be exact UTC ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise WorldStateSuccessorReviewError(f"{field} is invalid UTC") from exc
    if parsed.tzinfo != timezone.utc:
        raise WorldStateSuccessorReviewError(f"{field} must be UTC")
    return parsed


def _load_json(root: Path, relative: str) -> dict[str, Any]:
    try:
        return json.loads((root / relative).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorldStateSuccessorReviewError(f"cannot read {relative}: {exc}") from exc


def _collection(root: Path, relative: str, key: str) -> list[dict[str, Any]]:
    path = root / relative
    if not path.exists():
        return []
    document = _load_json(root, relative)
    rows = document.get(key)
    if not isinstance(rows, list):
        raise WorldStateSuccessorReviewError(f"{relative} must contain a {key} list")
    return rows


def _file_hashes(root: Path, directories: tuple[str, ...]) -> dict[str, str]:
    paths = [path for directory in directories for path in (root / "data" / directory).rglob("*") if path.is_file()]
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(paths)}


def protected_hashes(root: Path = ROOT) -> dict[str, dict[str, str]]:
    """Return hashes for World State and all governed upstream inputs."""
    return {
        "production_world_state": _file_hashes(root, ("world_state",)),
        "upstream": _file_hashes(root, ("canonical", "live_intelligence", "analysis", "signals", "relationships", "risks", "scenarios", "forecasts", "outcomes", "evaluation")),
    }


def _row_hash(row: dict[str, Any]) -> str:
    return fingerprint(row)


def _find(rows: list[dict[str, Any]], field: str, value: str) -> dict[str, Any] | None:
    return next((row for row in rows if row.get(field) == value), None)


def _parse_revision_number(value: Any) -> int:
    return value if type(value) is int and value > 0 else 0


def _read_upstream(root: Path) -> dict[str, list[dict[str, Any]]]:
    return {
        "signals": _collection(root, "data/signals/signals.json", "signals"),
        "observations": _collection(root, "data/live_intelligence/observations.json", "observations"),
        "evidence": _collection(root, "data/live_intelligence/evidence_registry.json", "evidence"),
    }


def _lineage_refs(component: dict[str, Any]) -> list[dict[str, Any]]:
    refs = []
    for citation in component.get("supporting_citations", []):
        if isinstance(citation, dict) and citation.get("layer") in {"SIGNALS", "LIVE_INTELLIGENCE"}:
            refs.append({key: citation.get(key) for key in ("layer", "object_id", "revision_id", "object_sha256", "epistemic_class")})
    return sorted(refs, key=lambda row: (row.get("layer") or "", row.get("object_id") or "", row.get("revision_id") or ""))


def _signal_heads(signals: list[dict[str, Any]], signal_id: str, cutoff: datetime) -> list[dict[str, Any]]:
    heads = []
    for row in signals:
        if row.get("signal_id") != signal_id or row.get("review_state") != "ACCEPTED":
            continue
        review = row.get("review_provenance", {}).get("reviewed_at_utc")
        if not isinstance(review, str):
            continue
        try:
            if _parse_utc(review, "signal.review_provenance.reviewed_at_utc") <= cutoff:
                heads.append(row)
        except WorldStateSuccessorReviewError:
            continue
    return sorted(heads, key=lambda row: (_parse_revision_number(row.get("revision_number")), row.get("revision_id", "")))


def _explicitly_corrected(row: dict[str, Any]) -> bool:
    states = {row.get("verification_state"), row.get("lifecycle_state"), row.get("status"), row.get("state")}
    return bool(states & {"CORRECTED", "RETRACTED", "WITHDRAWN", "INVALIDATED"})


def _descendant_linked(row: dict[str, Any], object_id: str) -> bool:
    return any(row.get(field) == object_id for field in (
        "revision_of_observation_id",
        "state_update_of_observation_id",
        "corrects_object_id",
        "retracts_object_id",
        "contradicts_object_id",
    ))


def _linked_contradiction(component: dict[str, Any], upstream: dict[str, list[dict[str, Any]]]) -> bool:
    if component.get("contradictory_citations"):
        return True
    pinned_ids = {ref.get("object_id") for ref in _lineage_refs(component)}
    for row in upstream["observations"] + upstream["evidence"] + upstream["signals"]:
        if row.get("contradiction_status") == "LINKED" and any(_descendant_linked(row, object_id) for object_id in pinned_ids):
            return True
    return False


def _review_component(root: Path, component_id: str, cutoff: datetime) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    state = load_production_state(root)
    candidates = [
        row for row in state["components"]
        if row.get("component_id") == component_id
        and row.get("review_state") == "ACCEPTED"
        and row.get("admitted_at_utc")
        and _parse_utc(row["admitted_at_utc"], "component.admitted_at_utc") <= cutoff
    ]
    if not candidates:
        return None, state
    component = sorted(candidates, key=lambda row: _parse_revision_number(row.get("revision_number")))[-1]
    return component, state


def review_successor_lineage(
    component_id: str,
    knowledge_cutoff_utc: str,
    *,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Build a deterministic successor-review packet from governed lineage."""
    cutoff = _parse_utc(knowledge_cutoff_utc, "knowledge_cutoff_utc")
    before = protected_hashes(root)
    errors = validate_production_state(root, enforce_first_population=False)
    if errors:
        raise WorldStateSuccessorReviewError("production history validation failed: " + "; ".join(errors))
    component, state = _review_component(root, component_id, cutoff)
    upstream = _read_upstream(root)
    if component is None:
        packet = {
            "contract_version": SUCCESSOR_PACKET_VERSION,
            "packet_type": "WORLD_STATE_SUCCESSOR_REVIEW_PACKET",
            "component_id": component_id,
            "component_revision_id": None,
            "knowledge_cutoff_utc": knowledge_cutoff_utc,
            "disposition": "NO_ADMITTED_COMPONENT",
            "successor_review_warranted": False,
            "write_targets": [],
            "production_write_performed": False,
            "public_projection_permitted": False,
            "limitations": ["No accepted component for this identity was admitted by the requested knowledge cutoff."],
        }
        before_after = protected_hashes(root)
        packet["mutation_check"] = {"status": "PASS" if before_after == before else "FAIL", "before": before, "after": before_after}
        packet["semantic_fingerprint"] = semantic_fingerprint(packet)
        return packet

    refs = _lineage_refs(component)
    signal_refs = [ref for ref in refs if ref.get("layer") == "SIGNALS"]
    observation_refs = [ref for ref in refs if ref.get("layer") == "LIVE_INTELLIGENCE" and str(ref.get("object_id", "")).startswith("WSLI-")]
    evidence_refs = [ref for ref in refs if ref.get("layer") == "LIVE_INTELLIGENCE" and str(ref.get("object_id", "")).startswith("WSEV-")]
    pinned_ids = {ref.get("object_id") for ref in refs}
    current_lineage: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    corrections: list[dict[str, Any]] = []
    associated_new: list[dict[str, Any]] = []
    signal_advanced: list[dict[str, Any]] = []
    accepted_signal_heads: list[dict[str, Any]] = []
    for ref in refs:
        collection = upstream["signals"] if ref["layer"] == "SIGNALS" else upstream["observations"] + upstream["evidence"]
        row = _find(collection, "signal_id" if ref["layer"] == "SIGNALS" else ("observation_id" if ref["object_id"].startswith("WSLI-") else "evidence_id"), ref["object_id"])
        if row is None:
            unresolved.append(ref)
            continue
        current = {"layer": ref["layer"], "object_id": ref["object_id"], "revision_id": row.get("revision_id"), "object_sha256": _row_hash(row), "pinned_object_sha256": ref.get("object_sha256"), "status": row.get("review_state") or row.get("verification_state") or row.get("lifecycle_state")}
        current_lineage.append(current)
        if _explicitly_corrected(row):
            corrections.append(current)
        if ref["layer"] == "SIGNALS":
            heads = _signal_heads(upstream["signals"], ref["object_id"], cutoff)
            accepted_head = heads[-1] if heads else None
            if accepted_head is None:
                unresolved.append(ref)
            elif accepted_head.get("revision_id") != ref.get("revision_id"):
                signal_advanced.append({"signal_id": ref["object_id"], "pinned_revision_id": ref.get("revision_id"), "current_accepted_revision_id": accepted_head.get("revision_id"), "current_object_sha256": _row_hash(accepted_head)})
            accepted_signal_heads.append({"signal_id": ref["object_id"], "accepted_revision_ids": [row.get("revision_id") for row in heads], "head_revision_id": accepted_head.get("revision_id") if accepted_head else None})
        else:
            if current["object_sha256"] != ref.get("object_sha256"):
                corrections.append(current)
            for candidate in collection:
                candidate_id = candidate.get("observation_id") or candidate.get("evidence_id")
                if candidate_id in pinned_ids or not _descendant_linked(candidate, ref["object_id"]):
                    continue
                if _explicitly_corrected(candidate):
                    corrections.append({"layer": ref["layer"], "object_id": candidate_id, "basis_object_id": ref["object_id"], "object_sha256": _row_hash(candidate), "status": candidate.get("verification_state") or candidate.get("lifecycle_state")})
                    continue
                if candidate.get("verification_state") in {"PRIMARY_CONFIRMED", "REVIEWED"}:
                    associated_new.append({"layer": ref["layer"], "object_id": candidate.get("observation_id") or candidate.get("evidence_id"), "basis_object_id": ref["object_id"], "object_sha256": _row_hash(candidate)})
    linked_contradiction = _linked_contradiction(component, upstream)
    freshness = derive_freshness(component, knowledge_cutoff_utc)
    if unresolved:
        disposition = "UPSTREAM_LINEAGE_UNRESOLVED"
    elif corrections:
        disposition = "CORRECTION_OR_RETRACTION_REQUIRES_REVIEW"
    elif linked_contradiction:
        disposition = "CONTRADICTION_REQUIRES_REVIEW"
    elif signal_advanced:
        disposition = "UPSTREAM_SIGNAL_REVISION_ADVANCED"
    elif associated_new:
        disposition = "NEW_ASSOCIATED_GOVERNED_EVIDENCE"
    elif freshness.get("status") in {"REVIEW_DUE", "STALE_REVIEW_REQUIRED"}:
        disposition = "REVIEW_DUE_NO_NEW_EVIDENCE"
    else:
        disposition = "NO_SUCCESSOR_NEEDED"
    packet = {
        "contract_version": SUCCESSOR_PACKET_VERSION,
        "packet_type": "WORLD_STATE_SUCCESSOR_REVIEW_PACKET",
        "component_id": component["component_id"],
        "component_revision_id": component["revision_id"],
        "component_object_sha256": component["object_sha256"],
        "knowledge_cutoff_utc": knowledge_cutoff_utc,
        "predecessor": {"component_id": component["component_id"], "revision_id": component["revision_id"], "object_sha256": component["object_sha256"]},
        "admission": {
            "admission_transaction_id": component.get("admission_transaction_id"),
            "review_transaction_id": component.get("review_transaction_id"),
            "source_manifest_sha256": component.get("source_manifest_sha256"),
            "snapshot_revision_ids": sorted(
                row.get("snapshot_revision_id") for row in state["snapshots"]
                if any(ref.get("component_id") == component.get("component_id") and ref.get("revision_id") == component.get("revision_id") for ref in row.get("component_refs", []))
            ),
        },
        "pinned_lineage": refs,
        "current_lineage": current_lineage,
        "lineage_comparison": {
            "accepted_signal_heads": accepted_signal_heads,
            "signal_revision_advanced": signal_advanced,
            "correction_or_retraction": corrections,
            "associated_new_evidence": associated_new,
            "unresolved": unresolved,
            "linked_contradiction": linked_contradiction,
        },
        "freshness": freshness,
        "disposition": disposition,
        "successor_review_warranted": disposition not in {"NO_SUCCESSOR_NEEDED", "REVIEW_DUE_NO_NEW_EVIDENCE", "NO_ADMITTED_COMPONENT"},
        "review_due_at_utc": freshness.get("stale_review_due_at_utc"),
        "limitations": [
            "Lineage review does not create or admit a successor revision.",
            "Unassociated same-domain evidence is not an automatic trigger.",
            "Model output and time passing are not governed successor evidence.",
        ],
        "write_targets": [],
        "production_write_performed": False,
        "public_projection_permitted": False,
    }
    after = protected_hashes(root)
    packet["mutation_check"] = {"status": "PASS" if before == after else "FAIL", "before": before, "after": after}
    if before != after:
        raise WorldStateSuccessorReviewError("successor review changed governed inputs")
    packet["semantic_fingerprint"] = semantic_fingerprint(packet)
    return packet


def successor_diff(predecessor: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Compare analytical fields, not textual JSON layout."""
    fields = ("state_label", "direction", "persistence", "breadth", "qualitative_confidence", "scope", "limitations", "uncertainties", "supporting_citations", "contradictory_citations", "freshness")
    changed: dict[str, dict[str, Any]] = {}
    unchanged: list[str] = []
    for field in fields:
        old, new = predecessor.get(field), candidate.get(field)
        if old == new:
            unchanged.append(field)
        else:
            changed[field] = {"from": deepcopy(old), "to": deepcopy(new)}
    return {"changed_fields": changed, "unchanged_fields": sorted(unchanged), "freshness_only": set(changed) == {"freshness"}, "semantic_fingerprint": semantic_fingerprint({"changed_fields": changed, "unchanged_fields": sorted(unchanged)})}


def build_successor_candidate(
    predecessor: dict[str, Any],
    *,
    revision_kind: str,
    source_manifest: list[dict[str, Any]],
    changes: dict[str, Any] | None = None,
    candidate_review_id: str = "WS-STEP9B-SYNTHETIC-CANDIDATE-REVIEW",
    test_only: bool = False,
) -> dict[str, Any]:
    """Build an unadmitted successor candidate; intended for tests/audit only."""
    if test_only is not True:
        raise WorldStateSuccessorReviewError("successor candidate construction requires explicit test_only=True")
    if revision_kind not in SUCCESSOR_REVISION_KINDS:
        raise WorldStateSuccessorReviewError("successor candidate revision_kind is invalid")
    if not isinstance(source_manifest, list) or not source_manifest:
        raise WorldStateSuccessorReviewError("successor candidate requires a non-empty source manifest")
    if predecessor.get("review_state") != "ACCEPTED" or predecessor.get("admitted_at_utc") is None:
        raise WorldStateSuccessorReviewError("successor predecessor must be admitted production state")
    candidate = deepcopy(predecessor)
    changes = deepcopy(changes or {})
    next_number = _parse_revision_number(predecessor.get("revision_number")) + 1
    candidate.update(changes)
    candidate.update({
        "revision_id": f"{predecessor['component_id']}-R{next_number}",
        "revision_number": next_number,
        "previous_revision_id": predecessor["revision_id"],
        "prior_revision_ref": predecessor["revision_id"],
        "revision_kind": revision_kind,
        "review_state": "UNDER_REVIEW",
        "lifecycle_state": "UNRESOLVED",
        "reviewed_at_utc": None,
        "admitted_at_utc": None,
        "review_transaction_id": None,
        "admission_transaction_id": None,
        "projection_transaction_id": None,
        "source_proposal_id": f"WS-STEP9B-{predecessor['component_id']}-R{next_number}",
        "source_manifest_sha256": fingerprint(source_manifest),
        "revision_reason": f"Synthetic Step 9B {revision_kind} successor candidate; human review and production admission required.",
        "transition_type": revision_kind,
        "object_sha256": None,
    })
    candidate["candidate_semantic_fingerprint"] = fingerprint(candidate, exclude={"object_sha256", "candidate_semantic_fingerprint"})
    candidate = with_object_fingerprint(candidate)
    errors = validate_component_history([predecessor, candidate])
    if errors:
        raise WorldStateSuccessorReviewError("successor candidate failed validation: " + "; ".join(errors))
    return candidate


def build_snapshot_successor_candidate(
    predecessor_snapshot: dict[str, Any],
    successor_component: dict[str, Any],
    *,
    source_manifest_sha256: str,
    candidate_review_id: str = "WS-STEP9B-SYNTHETIC-SNAPSHOT-REVIEW",
    test_only: bool = False,
) -> dict[str, Any]:
    if test_only is not True:
        raise WorldStateSuccessorReviewError("snapshot candidate construction requires explicit test_only=True")
    candidate = deepcopy(predecessor_snapshot)
    candidate.update({
        "snapshot_revision_id": f"{predecessor_snapshot['snapshot_series_id']}-R{predecessor_snapshot['revision_number'] + 1}",
        "revision_number": predecessor_snapshot["revision_number"] + 1,
        "previous_snapshot_revision_id": predecessor_snapshot["snapshot_revision_id"],
        "component_refs": [{
            "component_type": successor_component["component_type"],
            "component_id": successor_component["component_id"],
            "revision_id": successor_component["revision_id"],
            "object_sha256": successor_component["object_sha256"],
        }],
        "source_manifest_sha256": source_manifest_sha256,
        "proposal_id": f"WS-STEP9B-{successor_component['component_id']}-SNAPSHOT-R2",
        "candidate_review_id": candidate_review_id,
        "review_state": "UNDER_REVIEW",
        "review_transaction_id": None,
        "admission_transaction_id": None,
        "admitted_at_utc": None,
        "lifecycle_state": "UNRESOLVED",
        "visibility": "INTERNAL_ONLY",
        "object_sha256": None,
    })
    candidate["candidate_semantic_fingerprint"] = fingerprint(candidate, exclude={"object_sha256", "candidate_semantic_fingerprint"})
    candidate = with_object_fingerprint(candidate)
    errors = validate_snapshot_candidate(candidate, component_index={(successor_component["component_type"], successor_component["revision_id"]): successor_component})
    if errors:
        raise WorldStateSuccessorReviewError("snapshot successor candidate failed validation: " + "; ".join(errors))
    return candidate
