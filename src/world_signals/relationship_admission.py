"""Guarded Step 12B admission of the first historical Relationship.

The v0.1 Relationship checkpoint is deliberately never rewritten.  This
module validates the retained candidate and human decision, constructs the
controlled v0.2 production store, and materialises only the exact bounded
targets after an in-memory post-state check.
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

from .relationships import (
    RelationshipValidationReport,
    validate_relationship_history,
    validate_relationship_production,
)
from .world_state_relationship_candidate import validate_rbnz_relationship_candidate


class RelationshipAdmissionError(ValueError):
    """Raised when Step 12B cannot proceed without weakening governance."""


RELATIONSHIP_ID = "WSREL-NZ-RBNZ-OCR-MARKET-REPRICING-202609-001"
REVISION_ID = f"{RELATIONSHIP_ID}-R1"
PROPOSAL_ID = "WS-STEP12A-RBNZ-RELATIONSHIP-202609"
REVIEW_TRANSACTION_ID = "WS-STEP12B-RBNZ-RELATIONSHIP-REVIEW-20260928-001"
ADMISSION_TRANSACTION_ID = "WS-REL-ADMISSION-NZ-RBNZ-20260928-001"
EXPECTED_CANDIDATE_FINGERPRINT = "398efdf39448a9676bdd099a38fc3f66ac47a69cac1001b3895f493601679221"
EXPECTED_SOURCE_MANIFEST = "a4ecd251fa4f6e57020f0fcf6f0e0427e0cdb8a1d392ed34068d2d73b13fabbe"
MACRO_ID = "WSDIM-MACRO-NZ-RBNZ-OCR-202609-001"
MACRO_REVISION_ID = f"{MACRO_ID}-R1"
MACRO_HASH = "646ceafdba6324c421c2dceb9285d8fa4c0ecdec9df5558e369d05c261699e89"
MARKETS_ID = "WSDIM-MARKETS-NZ-RBNZ-OCR-202609-001"
MARKETS_REVISION_ID = f"{MARKETS_ID}-R1"
MARKETS_HASH = "a209a5958635dc1d95dd45214eec29d6a0ba76d1d8eefa252f16406dad673914"
COMPONENT_ADMISSION_ID = "WS-ADMISSION-NZ-RBNZ-OCR-20260928-001"

CANDIDATE_RELATIVE = Path("data/relationship_audit/STEP12A_RBNZ_RELATIONSHIP_CANDIDATE_REVIEW_PENDING.json")
REVIEW_RELATIVE = Path("data/relationship_audit/STEP12B_RBNZ_RELATIONSHIP_REVIEW_ACCEPTED.json")
REVIEW_BRIEF_RELATIVE = Path("data/relationship_audit/STEP12B_RBNZ_RELATIONSHIP_REVIEW_ACCEPTED.md")
SCHEMA_RELATIVE = Path("data/relationships/schema_v0.2.json")
PRODUCTION_RELATIVE = Path("data/relationships/relationships_v0.2.json")
ADMISSIONS_RELATIVE = Path("data/relationships/admission_transactions_v0.2.json")


def fingerprint(value: Any, *, exclude: set[str] | None = None) -> str:
    excluded = exclude or set()
    if isinstance(value, dict):
        value = {key: item for key, item in value.items() if key not in excluded}
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def _load(root: Path, relative: Path | str) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def _parse_utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise RelationshipAdmissionError(f"invalid UTC timestamp: {value}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise RelationshipAdmissionError(f"timestamp must be exact UTC: {value}")
    return parsed.astimezone(timezone.utc)


def _upstream(root: Path) -> tuple[dict[str, Any], ...]:
    signals = _load(root, "data/signals/signals.json")
    observations = _load(root, "data/live_intelligence/observations.json")
    live_evidence = _load(root, "data/live_intelligence/evidence_registry.json")
    analyses = _load(root, "data/analysis/event_reviews.json")
    analysis_evidence = _load(root, "data/analysis/evidence_registry.json")
    evidence = {row["evidence_id"]: row for row in live_evidence.get("evidence", [])}
    evidence.update({row["evidence_id"]: row for row in analysis_evidence.get("evidence", [])})
    return (
        signals,
        observations,
        {"evidence": list(evidence.values())},
        _load(root, "data/canonical/registry.json"),
        analyses,
        analysis_evidence,
    )


def _absent_hash() -> str:
    return hashlib.sha256(b"ABSENT").hexdigest()


def _state_hashes(production: dict[str, Any] | None, admission_ledger: dict[str, Any] | None) -> dict[str, str]:
    normalized_ledger = None
    if admission_ledger is not None:
        normalized_ledger = {
            key: value
            for key, value in admission_ledger.items()
            if key != "transactions"
        }
        normalized_ledger["transactions"] = [
            _transaction_core(transaction)
            for transaction in admission_ledger.get("transactions", [])
        ]
    return {
        "relationships_v0.2": fingerprint(production) if production is not None else _absent_hash(),
        "admission_transactions_v0.2": (
            fingerprint(normalized_ledger) if normalized_ledger is not None else _absent_hash()
        ),
    }


def _transaction_core(transaction: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in transaction.items()
        if key not in {"transaction_fingerprint", "pre_state_hashes", "post_state_hashes"}
    }


def build_review_transaction(candidate: dict[str, Any], reviewed_at_utc: str) -> dict[str, Any]:
    reviewed = _parse_utc(reviewed_at_utc)
    relationship = candidate.get("relationship") or {}
    created = _parse_utc(relationship.get("first_asserted_at_utc"))
    if reviewed < created:
        raise RelationshipAdmissionError("human Relationship review cannot predate candidate assertion")
    transaction = {
        "transaction_type": "RELATIONSHIP_REVIEW",
        "contract_version": "0.2",
        "transaction_id": REVIEW_TRANSACTION_ID,
        "decision": "ACCEPTED",
        "decision_scope": "FIRST_RELATIONSHIP_PRODUCTION_ADMISSION",
        "candidate": {
            "proposal_id": candidate.get("proposal_id"),
            "candidate_semantic_fingerprint": candidate.get("candidate_semantic_fingerprint"),
            "source_manifest_sha256": candidate.get("source_manifest_sha256"),
            "relationship_id": relationship.get("relationship_id"),
            "revision_id": relationship.get("revision_id"),
        },
        "accepted_semantics": {
            "relationship_class": "ASSOCIATION",
            "directionality": "DIRECTED",
            "confidence": "MEDIUM",
            "temporal_scope_type": "HISTORICAL_PERIOD",
            "causal_promotion": "NONE",
            "current_active_transmission_claim": "NONE",
            "lifecycle_state": "EXPIRED",
        },
        "endpoint_refs": [
            {"node_id": MACRO_ID, "revision_id": MACRO_REVISION_ID, "object_sha256": MACRO_HASH},
            {"node_id": MARKETS_ID, "revision_id": MARKETS_REVISION_ID, "object_sha256": MARKETS_HASH},
        ],
        "reviewer": {"reviewer_id": "operator-human-review", "role": "HUMAN_REVIEWER"},
        "reviewed_at_utc": reviewed_at_utc,
        "decision_basis": "Accept the RBNZ association as a bounded historical relationship only; retain MEDIUM confidence, alternatives, confounders and falsifiers, and make no causal or current-active transmission claim.",
        "independence_assessment": {
            "same_world_state_admission_transaction": COMPONENT_ADMISSION_ID,
            "separately_reviewed_components": True,
            "shared_analysis_or_evidence_lineage": True,
            "counts_as_independent_corroboration": False,
            "confidence_uplift_from_endpoint_coadmission": False,
        },
        "visibility": "INTERNAL_ONLY",
        "public_projection_permitted": False,
        "write_targets": [],
        "production_relationship_admitted": False,
    }
    transaction["transaction_fingerprint"] = fingerprint(transaction)
    return transaction


def validate_review_transaction(review: dict[str, Any], candidate: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    relationship = candidate.get("relationship") or {}
    expected = {
        "proposal_id": candidate.get("proposal_id"),
        "candidate_semantic_fingerprint": candidate.get("candidate_semantic_fingerprint"),
        "source_manifest_sha256": candidate.get("source_manifest_sha256"),
        "relationship_id": RELATIONSHIP_ID,
        "revision_id": REVISION_ID,
    }
    if candidate.get("candidate_semantic_fingerprint") != EXPECTED_CANDIDATE_FINGERPRINT:
        errors.append("candidate semantic fingerprint is not the approved Step 12A value")
    if candidate.get("source_manifest_sha256") != EXPECTED_SOURCE_MANIFEST:
        errors.append("candidate source manifest is not the approved Step 12A value")
    if review.get("transaction_type") != "RELATIONSHIP_REVIEW":
        errors.append("Step 12B transaction must be RELATIONSHIP_REVIEW")
    if review.get("decision") != "ACCEPTED":
        errors.append("human Relationship decision must be ACCEPTED")
    if review.get("candidate") != expected:
        errors.append("review transaction does not pin the exact candidate")
    if review.get("accepted_semantics", {}).get("relationship_class") != "ASSOCIATION":
        errors.append("review cannot promote the Relationship class")
    if review.get("accepted_semantics", {}).get("causal_promotion") != "NONE":
        errors.append("review must explicitly prohibit causal promotion")
    if review.get("accepted_semantics", {}).get("lifecycle_state") != "EXPIRED":
        errors.append("historical review must select EXPIRED lifecycle")
    reviewer = review.get("reviewer") or {}
    if reviewer.get("role") != "HUMAN_REVIEWER":
        errors.append("human reviewer role is required")
    try:
        reviewed = _parse_utc(review.get("reviewed_at_utc"))
        created = _parse_utc(relationship.get("first_asserted_at_utc"))
        if reviewed < created:
            errors.append("review cannot predate candidate assertion")
    except RelationshipAdmissionError as exc:
        errors.append(str(exc))
    if review.get("write_targets") != [] or review.get("public_projection_permitted") is not False:
        errors.append("human review must have no write targets and no public permission")
    independence = review.get("independence_assessment") or {}
    if independence.get("counts_as_independent_corroboration") is not False:
        errors.append("same-admission endpoints must not count as independent corroboration")
    if independence.get("confidence_uplift_from_endpoint_coadmission") is not False:
        errors.append("endpoint co-admission must not uplift confidence")
    if review.get("transaction_fingerprint") != fingerprint(review, exclude={"transaction_fingerprint"}):
        errors.append("human review transaction fingerprint mismatch")
    return errors


def build_accepted_relationship(candidate: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    row = deepcopy(candidate["relationship"])
    row["review_state"] = "ACCEPTED"
    row["lifecycle_state"] = "EXPIRED"
    row["review_provenance"] = {
        **row["review_provenance"],
        "reviewed_by": review["reviewer"]["reviewer_id"],
        "reviewed_at_utc": review["reviewed_at_utc"],
        "decision_basis": review["decision_basis"],
    }
    row["revision_reason"] = (
        "First production revision: two separately reviewed World State component revisions were admitted in the same Step 11B transaction; shared lineage is not independent corroboration. Accepted as a historical association only; no causal promotion."
    )
    return row


def build_production_dataset(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "project": "WORLD SIGNALS",
        "dataset": "REVIEWED_RELATIONSHIPS",
        "version": "0.2",
        "population_state": "CONTROLLED_SINGLE_RELATIONSHIP_SPECIMEN",
        "manual_reviewed_admission_allowed": True,
        "automatic_ingestion_allowed": False,
        "general_population_open": False,
        "maximum_controlled_relationships": 1,
        "public_projection_permitted": False,
        "relationships": [row],
    }


def build_admission_transaction(
    candidate: dict[str, Any],
    review: dict[str, Any],
    row: dict[str, Any],
    pre_state_hashes: dict[str, str],
    post_state_hashes: dict[str, str],
    admitted_at_utc: str,
) -> dict[str, Any]:
    admitted = _parse_utc(admitted_at_utc)
    reviewed = _parse_utc(review["reviewed_at_utc"])
    if admitted < reviewed:
        raise RelationshipAdmissionError("production admission cannot predate human review")
    transaction = {
        "transaction_type": "RELATIONSHIP_PRODUCTION_ADMISSION",
        "contract_version": "0.2",
        "transaction_id": ADMISSION_TRANSACTION_ID,
        "decision": "ACCEPTED",
        "candidate_proposal_id": candidate["proposal_id"],
        "candidate_semantic_fingerprint": candidate["candidate_semantic_fingerprint"],
        "source_manifest_sha256": candidate["source_manifest_sha256"],
        "review_transaction_id": review["transaction_id"],
        "relationship_id": row["relationship_id"],
        "revision_id": row["revision_id"],
        "production_relationship_fingerprint": fingerprint(row),
        "endpoint_fingerprints": [
            {"node_id": MACRO_ID, "revision_id": MACRO_REVISION_ID, "object_sha256": MACRO_HASH, "admission_transaction_id": COMPONENT_ADMISSION_ID},
            {"node_id": MARKETS_ID, "revision_id": MARKETS_REVISION_ID, "object_sha256": MARKETS_HASH, "admission_transaction_id": COMPONENT_ADMISSION_ID},
        ],
        "supporting_analysis_refs": row["supporting_analysis_refs"],
        "supporting_evidence_pins": row["supporting_evidence_pins"],
        "component_admission_transaction_id": COMPONENT_ADMISSION_ID,
        "reviewer": review["reviewer"],
        "reviewed_at_utc": review["reviewed_at_utc"],
        "admitted_at_utc": admitted_at_utc,
        "lifecycle_state": "EXPIRED",
        "visibility": "INTERNAL_ONLY",
        "public_projection_permitted": False,
        "write_targets": [str(PRODUCTION_RELATIVE), str(ADMISSIONS_RELATIVE)],
        "pre_state_hashes": pre_state_hashes,
        "post_state_hashes": post_state_hashes,
        "validator_version": "relationship-admission-v0.2",
        "independence_assessment": review["independence_assessment"],
    }
    transaction["transaction_fingerprint"] = fingerprint(transaction)
    return transaction


def _build_transaction_bundle(root: Path, reviewed_at_utc: str, admitted_at_utc: str) -> dict[str, Any]:
    candidate = _load(root, CANDIDATE_RELATIVE)
    candidate_report = validate_rbnz_relationship_candidate(candidate, root)
    if not candidate_report.ok:
        raise RelationshipAdmissionError("candidate validation failed: " + "; ".join(candidate_report.errors))
    if candidate.get("candidate_semantic_fingerprint") != EXPECTED_CANDIDATE_FINGERPRINT:
        raise RelationshipAdmissionError("unexpected candidate semantic fingerprint")
    if candidate.get("source_manifest_sha256") != EXPECTED_SOURCE_MANIFEST:
        raise RelationshipAdmissionError("unexpected candidate source manifest fingerprint")
    review = build_review_transaction(candidate, reviewed_at_utc)
    review_errors = validate_review_transaction(review, candidate)
    if review_errors:
        raise RelationshipAdmissionError("review transaction failed: " + "; ".join(review_errors))
    row = build_accepted_relationship(candidate, review)
    production = build_production_dataset(row)
    if (root / PRODUCTION_RELATIVE).exists() or (root / ADMISSIONS_RELATIVE).exists():
        raise RelationshipAdmissionError("Step 12B production targets already exist")
    pre_state_hashes = _state_hashes(None, None)
    draft = build_admission_transaction(candidate, review, row, pre_state_hashes, {}, admitted_at_utc)
    admission_core = _transaction_core(draft)
    admission_ledger_preimage = {
        "project": "WORLD SIGNALS",
        "dataset": "RELATIONSHIP_ADMISSION_TRANSACTIONS",
        "version": "0.2",
        "transactions": [admission_core],
    }
    post_state_hashes = _state_hashes(production, admission_ledger_preimage)
    admission = build_admission_transaction(
        candidate, review, row, pre_state_hashes, post_state_hashes, admitted_at_utc,
    )
    admissions = {"project": "WORLD SIGNALS", "dataset": "RELATIONSHIP_ADMISSION_TRANSACTIONS", "version": "0.2", "transactions": [admission]}
    schema = _load(root, SCHEMA_RELATIVE)
    signals, observations, evidence, canonical, _, _ = _upstream(root)
    components = _load(root, "data/world_state/components.json")
    component_admissions = _load(root, "data/world_state/admission_transactions.json")
    report = validate_relationship_production(
        schema, production, signals, observations, evidence, canonical,
        world_state_components=components, world_state_admissions=component_admissions,
    )
    if not report.ok:
        raise RelationshipAdmissionError("production Relationship validation failed: " + "; ".join(report.errors))
    if admission["post_state_hashes"] != _state_hashes(
        production,
        {
            "project": "WORLD SIGNALS",
            "dataset": "RELATIONSHIP_ADMISSION_TRANSACTIONS",
            "version": "0.2",
            "transactions": [admission],
        },
    ):
        raise RelationshipAdmissionError("declared post-state hashes do not match simulated production state")
    if admission["transaction_fingerprint"] != fingerprint(admission, exclude={"transaction_fingerprint"}):
        raise RelationshipAdmissionError("admission transaction fingerprint mismatch")
    return {
        "candidate": candidate,
        "review": review,
        "relationship": row,
        "production": production,
        "admission": admissions,
        "pre_state_hashes": pre_state_hashes,
        "post_state_hashes": post_state_hashes,
        "simulation": {"status": "PASS", "governed_files_written": False},
    }


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _review_brief(bundle: dict[str, Any]) -> str:
    row = bundle["relationship"]
    review = bundle["review"]
    return f"""# Step 12B — RBNZ Relationship review accepted

Status: `ACCEPTED` for first production Relationship admission.

This review accepts `{row['relationship_id']}-R1` as a historical `ASSOCIATION`
with `DIRECTED` ordering and `MEDIUM` confidence. It is event-bounded and
stored with lifecycle `EXPIRED`; that means the historical observation period
is complete, not that the evidence is false or withdrawn.

The Macro and Markets endpoints are separately reviewed World State component
revisions admitted in the same Step 11B transaction. Their shared lineage and
co-admission do not count as independent corroboration and do not increase
confidence. Analysis and evidence remain supporting lineage, not endpoints.

No causal promotion, current-active transmission claim, Risk, Regime, Scenario,
Forecast, World State successor, or public projection is authorized.

- Human review transaction: `{review['transaction_id']}`
- Production admission transaction: `{bundle['admission']['transactions'][0]['transaction_id']}`
- Visibility: `INTERNAL_ONLY`
- Public projection permitted: `false`
- Active current graph edges: `0`
"""


def validate_rbnz_relationship_admission(root: Path) -> RelationshipValidationReport:
    """Validate committed Step 12B artifacts without writing."""
    errors: list[str] = []
    try:
        candidate = _load(root, CANDIDATE_RELATIVE)
        review = _load(root, REVIEW_RELATIVE)
        production = _load(root, PRODUCTION_RELATIVE)
        admissions = _load(root, ADMISSIONS_RELATIVE)
        candidate_report = validate_rbnz_relationship_candidate(candidate, root)
        errors.extend(candidate_report.errors)
        errors.extend(validate_review_transaction(review, candidate))
        row = production.get("relationships", [None])[0]
        expected = build_accepted_relationship(candidate, review)
        if row != expected:
            errors.append("production Relationship does not match the accepted candidate semantics")
        schema = _load(root, SCHEMA_RELATIVE)
        signals, observations, evidence, canonical, _, _ = _upstream(root)
        components = _load(root, "data/world_state/components.json")
        component_admissions = _load(root, "data/world_state/admission_transactions.json")
        errors.extend(validate_relationship_production(
            schema, production, signals, observations, evidence, canonical,
            world_state_components=components, world_state_admissions=component_admissions,
        ).errors)
        transaction = admissions.get("transactions", [None])[0]
        if not isinstance(transaction, dict):
            errors.append("production admission transaction is missing")
        else:
            if transaction.get("relationship_id") != RELATIONSHIP_ID or transaction.get("revision_id") != REVISION_ID:
                errors.append("admission transaction does not pin the accepted Relationship")
            if transaction.get("review_transaction_id") != review.get("transaction_id"):
                errors.append("admission transaction does not pin the human review")
            if transaction.get("transaction_fingerprint") != fingerprint(transaction, exclude={"transaction_fingerprint"}):
                errors.append("production admission transaction fingerprint mismatch")
            if transaction.get("pre_state_hashes") != _state_hashes(None, None):
                errors.append("production admission pre-state hashes do not describe the empty v0.2 store")
            expected_post = _state_hashes(
                production,
                {
                    "project": "WORLD SIGNALS",
                    "dataset": "RELATIONSHIP_ADMISSION_TRANSACTIONS",
                    "version": "0.2",
                    "transactions": [transaction],
                },
            )
            if transaction.get("post_state_hashes") != expected_post:
                errors.append("production admission post-state hashes do not match the committed state")
            if transaction.get("lifecycle_state") != "EXPIRED" or transaction.get("public_projection_permitted") is not False:
                errors.append("production admission semantics are too broad")
    except (KeyError, TypeError, json.JSONDecodeError, OSError, RelationshipAdmissionError) as exc:
        errors.append(str(exc))
    return RelationshipValidationReport(tuple(errors))


def materialize_rbnz_relationship_admission(
    root: Path,
    reviewed_at_utc: str,
    admitted_at_utc: str,
    *,
    write: bool = False,
) -> dict[str, Any]:
    """Build or atomically materialise the exact first Relationship admission."""
    bundle = _build_transaction_bundle(root, reviewed_at_utc, admitted_at_utc)
    if not write:
        return bundle
    audit_dir = root / "data/relationship_audit"
    relationship_dir = root / "data/relationships"
    audit_dir.mkdir(parents=True, exist_ok=True)
    relationship_dir.mkdir(parents=True, exist_ok=True)
    targets = {
        audit_dir / REVIEW_RELATIVE.name: _json_bytes(bundle["review"]),
        audit_dir / REVIEW_BRIEF_RELATIVE.name: _review_brief(bundle).encode("utf-8"),
        root / PRODUCTION_RELATIVE: _json_bytes(bundle["production"]),
        root / ADMISSIONS_RELATIVE: _json_bytes(bundle["admission"]),
    }
    existing = [path for path in targets if path.exists()]
    if existing:
        raise RelationshipAdmissionError("admission target already exists: " + ", ".join(str(path) for path in existing))
    stage = Path(tempfile.mkdtemp(prefix=".relationship-admission-", dir=str(relationship_dir)))
    staged: dict[Path, Path] = {}
    written: list[Path] = []
    try:
        for target, content in targets.items():
            stage_path = stage / target.name
            stage_path.write_bytes(content)
            with stage_path.open("rb") as handle:
                os.fsync(handle.fileno())
            staged[target] = stage_path
        for target, stage_path in staged.items():
            os.replace(stage_path, target)
            written.append(target)
        for target, content in targets.items():
            if target.read_bytes() != content:
                raise RelationshipAdmissionError(f"post-write byte verification failed: {target}")
    except Exception:
        for target in written:
            target.unlink(missing_ok=True)
        raise
    finally:
        try:
            stage.rmdir()
        except OSError:
            pass
    bundle["materialized"] = True
    return bundle
