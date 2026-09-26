"""Guarded promotion of OSINT candidates into reviewed Live observations.

The OSINT engine remains candidate-only.  This module validates an explicit
human-reviewed transaction against the governed Live store; it does not fetch
sources, write production data, or promote candidates automatically.
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any


UTC = timezone.utc
MAX_PROMOTIONS_PER_TRANSACTION = 4


def stable_json_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return sha256(raw.encode("utf-8")).hexdigest()


def live_state_hash(schema: dict[str, Any], evidence: dict[str, Any], observations: dict[str, Any]) -> str:
    """Hash the complete governed Live state, excluding this audit record."""
    return stable_json_hash({"schema": schema, "evidence": evidence, "observations": observations})


def _utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        return None
    return parsed.astimezone(UTC)


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_osint_promotion_transaction(
    schema: dict[str, Any],
    evidence: dict[str, Any],
    observations: dict[str, Any],
    source_registry: dict[str, Any],
    transaction: dict[str, Any] | None,
    *,
    now_utc: str | None = None,
) -> tuple[str, ...]:
    """Validate a reviewed candidate-to-observation promotion transaction."""
    errors: list[str] = []
    required = {
        "transaction_id", "transaction_type", "decision", "decided_at_utc", "reviewer",
        "candidate_audit", "evidence_ids", "observation_ids", "pre_state", "post_state",
        "validation", "promotion_limit", "boundary", "denominator_note",
    }
    if not isinstance(transaction, dict):
        return ("a reviewed OSINT promotion transaction is required",)
    allowed = required | {"project", "dataset", "version"}
    if not required.issubset(transaction) or set(transaction) - allowed:
        errors.append("OSINT promotion transaction has an invalid field set")
    if transaction.get("transaction_type") != "REVIEWED_OSINT_OBSERVATION_PROMOTION":
        errors.append("transaction type must be REVIEWED_OSINT_OBSERVATION_PROMOTION")
    if transaction.get("decision") != "ACCEPTED":
        errors.append("production OSINT promotion requires an ACCEPTED decision")
    decided = _utc(transaction.get("decided_at_utc"))
    if decided is None:
        errors.append("decided_at_utc must be exact UTC")
    if now_utc and (_utc(now_utc) is None or decided and decided > _utc(now_utc)):
        errors.append("promotion decision cannot be dated in the future")

    reviewer = transaction.get("reviewer")
    if not isinstance(reviewer, dict) or set(reviewer) != {"reviewer_id", "reviewed_at_utc", "decision_basis"}:
        errors.append("promotion requires reviewer, timestamp and decision basis")
    elif not _text(reviewer.get("reviewer_id")) or _utc(reviewer.get("reviewed_at_utc")) is None or not _text(reviewer.get("decision_basis")):
        errors.append("promotion reviewer provenance is incomplete")

    evidence_rows = evidence.get("evidence") if isinstance(evidence, dict) else None
    observation_rows = observations.get("observations") if isinstance(observations, dict) else None
    source_rows = source_registry.get("sources") if isinstance(source_registry, dict) else None
    if not isinstance(evidence_rows, list) or not isinstance(observation_rows, list) or not isinstance(source_rows, list):
        return tuple(errors + ["promotion validation requires governed evidence, observations and source lists"])

    evidence_by_id = {row.get("evidence_id"): row for row in evidence_rows if isinstance(row, dict)}
    observation_by_id = {row.get("observation_id"): row for row in observation_rows if isinstance(row, dict)}
    source_by_id = {row.get("source_id"): row for row in source_rows if isinstance(row, dict)}

    evidence_ids = transaction.get("evidence_ids")
    observation_ids = transaction.get("observation_ids")
    if not isinstance(evidence_ids, list) or not evidence_ids or len(evidence_ids) != len(set(evidence_ids)):
        errors.append("evidence_ids must be a non-empty unique list")
        evidence_ids = []
    if not isinstance(observation_ids, list) or not observation_ids or len(observation_ids) != len(set(observation_ids)):
        errors.append("observation_ids must be a non-empty unique list")
        observation_ids = []
    if len(observation_ids) > MAX_PROMOTIONS_PER_TRANSACTION:
        errors.append("OSINT promotion exceeds the four-observation tranche limit")
    for evidence_id in evidence_ids:
        if evidence_id not in evidence_by_id:
            errors.append(f"transaction references unknown evidence {evidence_id}")
    for observation_id in observation_ids:
        if observation_id not in observation_by_id:
            errors.append(f"transaction references unknown observation {observation_id}")

    limit = transaction.get("promotion_limit")
    if not isinstance(limit, dict) or set(limit) != {"maximum_new_observations", "promoted_count"}:
        errors.append("promotion_limit must record the bounded tranche")
    elif limit.get("maximum_new_observations") != MAX_PROMOTIONS_PER_TRANSACTION or limit.get("promoted_count") != len(observation_ids):
        errors.append("promotion_limit does not match the bounded transaction")

    boundary = transaction.get("boundary")
    expected_boundary = {
        "automatic_promotion": False,
        "automatic_signal_promotion": False,
        "automatic_canonical_commit": False,
        "public_observation_projection": "CLOSED",
    }
    if boundary != expected_boundary:
        errors.append("OSINT promotion boundary is not closed and read-only")
    if not _text(transaction.get("denominator_note")):
        errors.append("promotion denominator obligation is required")

    audit = transaction.get("candidate_audit")
    if not isinstance(audit, list) or len(audit) != len(observation_ids):
        errors.append("candidate_audit must contain one reviewed entry per promoted observation")
        audit = []
    seen_candidates: set[str] = set()
    seen_audit_observations: set[str] = set()
    for item in audit:
        if not isinstance(item, dict):
            errors.append("candidate_audit entries must be objects")
            continue
        required_item = {
            "candidate_id", "observation_id", "source_id", "route_id", "retrieval_state",
            "payload_sha256", "parser_version", "adapter_version", "candidate_state", "decision", "rationale",
        }
        if set(item) != required_item:
            errors.append("candidate_audit entry has an invalid field set")
            continue
        candidate_id = item.get("candidate_id")
        observation_id = item.get("observation_id")
        if not _text(candidate_id) or candidate_id in seen_candidates:
            errors.append("candidate IDs must be present and unique")
        seen_candidates.add(candidate_id)
        if observation_id not in observation_ids or observation_id in seen_audit_observations:
            errors.append("candidate_audit observation mapping must be unique and transactional")
        seen_audit_observations.add(observation_id)
        if item.get("retrieval_state") != "SUCCESS":
            errors.append(f"{candidate_id}: only a successful retrieval can be promoted")
        if not _text(item.get("payload_sha256")) or not _text(item.get("parser_version")) or not _text(item.get("adapter_version")):
            errors.append(f"{candidate_id}: retrieval provenance is incomplete")
        if item.get("candidate_state") not in {"NEW", "NEEDS_REVIEW"} or item.get("decision") != "PROMOTE":
            errors.append(f"{candidate_id}: candidate must be explicitly reviewed for promotion")
        if not _text(item.get("source_id")) or item.get("source_id") not in source_by_id:
            errors.append(f"{candidate_id}: source is not in the governed registry")
        else:
            source = source_by_id[item["source_id"]]
            permission = str(source.get("automated_monitoring_use") or "")
            if not permission.startswith("CLEARED"):
                errors.append(f"{candidate_id}: source automation permission is not cleared")
        if not _text(item.get("route_id")) or not _text(item.get("rationale")):
            errors.append(f"{candidate_id}: route and review rationale are required")

    for observation_id in observation_ids:
        row = observation_by_id.get(observation_id)
        if not row:
            continue
        refs = row.get("evidence_refs") or []
        if not set(refs).intersection(evidence_ids):
            errors.append(f"{observation_id}: promoted observation is not linked to the transaction evidence")
        if row.get("automatic_canonical_commit") is not False or row.get("google_calendar_write") is not False:
            errors.append(f"{observation_id}: automatic writes must remain disabled")

    pre = transaction.get("pre_state")
    post = transaction.get("post_state")
    for label, state in (("pre_state", pre), ("post_state", post)):
        if not isinstance(state, dict):
            errors.append(f"{label} must be an object")
            continue
        required_state = {"schema_version", "population_state", "observation_count", "evidence_count", "sha256"}
        if set(state) != required_state:
            errors.append(f"{label} has an invalid field set")
        if not _text(state.get("schema_version")) or not _text(state.get("population_state")) or not isinstance(state.get("sha256"), str):
            errors.append(f"{label} must contain version, population state and sha256")
    if isinstance(pre, dict) and isinstance(post, dict):
        if post.get("observation_count") != pre.get("observation_count", -1) + len(observation_ids):
            errors.append("post-state observation count is not the pre-state plus the promotion")
        if post.get("evidence_count") != pre.get("evidence_count", -1) + len(evidence_ids):
            errors.append("post-state evidence count is not the pre-state plus the promotion")
        if post.get("schema_version") != schema.get("version") or post.get("population_state") != observations.get("population_state"):
            errors.append("post-state does not match the current governed Live state")
        if post.get("observation_count") != len(observation_rows) or post.get("evidence_count") != len(evidence_rows):
            errors.append("post-state counts do not match governed Live data")
        if post.get("sha256") != live_state_hash(schema, evidence, observations):
            errors.append("post-state sha256 does not match governed Live data")

    validation = transaction.get("validation")
    if not isinstance(validation, dict) or validation.get("status") != "PASS" or not _text(validation.get("validator_version")) or _utc(validation.get("validated_at_utc")) is None:
        errors.append("promotion transaction must retain a passing validation result")
    return tuple(errors)
