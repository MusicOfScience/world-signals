"""Reviewed, bounded admission for the first governed Signal specimen."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from .signals import SignalValidationReport, observation_digest, validate_signal_history


MAX_SIGNAL_ADMISSIONS = 1
TRANSACTION_TYPE = "REVIEWED_SIGNAL_ADMISSION"
VALID_DISPOSITIONS = {
    "PROMOTED",
    "INSUFFICIENT_GOVERNED_SUPPORT",
    "DUPLICATE_OR_SHARED_ORIGIN",
    "NO_PERSISTENCE",
    "INSUFFICIENT_MATERIALITY",
    "ANALYSIS_NOT_SIGNAL",
    "FORECAST_LEAKAGE",
    "RETAIN_FOR_LATER_REVIEW",
}


def _utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        return None
    return parsed.astimezone(timezone.utc)


def _hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def signal_state_hash(signals_dataset: dict[str, Any]) -> str:
    """Hash only the reproducible Signal state, never the admission transaction."""
    return _hash({
        "version": signals_dataset.get("version"),
        "population_state": signals_dataset.get("population_state"),
        "signals": signals_dataset.get("signals"),
    })


def empty_signal_state_hash(schema_version: str) -> str:
    return signal_state_hash({
        "version": schema_version,
        "population_state": "CLOSED_NO_PRODUCTION_SIGNALS",
        "signals": [],
    })


def _report(errors: list[str]) -> SignalValidationReport:
    return SignalValidationReport(tuple(errors))


def validate_signal_admission_transaction(
    schema: dict[str, Any],
    signals_dataset: dict[str, Any],
    observations_dataset: dict[str, Any],
    evidence_registry: dict[str, Any],
    transaction: dict[str, Any],
) -> SignalValidationReport:
    """Validate an explicit one-time reviewed admission without writing state."""
    errors: list[str] = []
    if not isinstance(transaction, dict):
        return _report(["Signal admission transaction must be an object"])
    if transaction.get("transaction_type") != TRANSACTION_TYPE:
        errors.append("invalid Signal admission transaction type")
    if transaction.get("decision") != "ACCEPTED":
        errors.append("Signal admission decision must be ACCEPTED")
    if not isinstance(transaction.get("transaction_id"), str) or not transaction["transaction_id"].strip():
        errors.append("transaction_id is required")
    decided = _utc(transaction.get("decided_at_utc"))
    if decided is None:
        errors.append("decided_at_utc must be exact UTC")

    reviewer = transaction.get("reviewer")
    if not isinstance(reviewer, dict):
        errors.append("reviewer is required")
    else:
        if not isinstance(reviewer.get("reviewer_id"), str) or not reviewer["reviewer_id"].strip():
            errors.append("reviewer.reviewer_id is required")
        reviewed = _utc(reviewer.get("reviewed_at_utc"))
        if reviewed is None:
            errors.append("reviewer.reviewed_at_utc must be exact UTC")
        elif decided and reviewed != decided:
            errors.append("reviewer timestamp must equal decision timestamp")
        if not isinstance(reviewer.get("decision_basis"), str) or not reviewer["decision_basis"].strip():
            errors.append("reviewer.decision_basis is required")

    signal_rows = signals_dataset.get("signals") if isinstance(signals_dataset, dict) else None
    if not isinstance(signal_rows, list):
        errors.append("signals must be a list")
        signal_rows = []
    signal_ids = [row.get("signal_id") for row in signal_rows if isinstance(row, dict)]
    revision_ids = [row.get("revision_id") for row in signal_rows if isinstance(row, dict)]
    if len(signal_rows) != len(signal_ids) or any(not isinstance(value, str) or not value.strip() for value in signal_ids):
        errors.append("every admitted Signal must have a stable signal_id")
    if transaction.get("signal_ids") != signal_ids:
        errors.append("transaction signal_ids must exactly match the admitted dataset")
    if transaction.get("revision_ids") != revision_ids:
        errors.append("transaction revision_ids must exactly match the admitted dataset")
    if len(signal_rows) > MAX_SIGNAL_ADMISSIONS:
        errors.append("Signal admission tranche limit is one")
    if signals_dataset.get("population_state") != "CONTROLLED_REVIEWED_SIGNAL_SPECIMEN":
        errors.append("admitted dataset must use CONTROLLED_REVIEWED_SIGNAL_SPECIMEN")

    pre = transaction.get("pre_state")
    if not isinstance(pre, dict):
        errors.append("pre_state is required")
    else:
        expected_pre = empty_signal_state_hash(str(schema.get("version")))
        if pre.get("schema_version") != schema.get("version") or pre.get("population_state") != "CLOSED_NO_PRODUCTION_SIGNALS" or pre.get("signal_count") != 0:
            errors.append("pre_state must describe the empty closed Signal state")
        if pre.get("sha256") != expected_pre:
            errors.append("pre_state hash does not match the empty closed Signal state")

    post = transaction.get("post_state")
    if not isinstance(post, dict):
        errors.append("post_state is required")
    else:
        if post.get("schema_version") != schema.get("version") or post.get("population_state") != signals_dataset.get("population_state") or post.get("signal_count") != len(signal_rows):
            errors.append("post_state does not match the admitted Signal dataset")
        if post.get("sha256") != signal_state_hash(signals_dataset):
            errors.append("post_state hash does not match the admitted Signal dataset")

    validation = transaction.get("validation")
    if not isinstance(validation, dict) or validation.get("status") != "PASS" or not isinstance(validation.get("validator_version"), str) or not validation["validator_version"].strip() or _utc(validation.get("validated_at_utc")) is None:
        errors.append("validation must record a PASS and exact validator metadata")

    limit = transaction.get("admission_limit")
    if not isinstance(limit, dict) or limit.get("maximum_new_signals") != MAX_SIGNAL_ADMISSIONS or limit.get("admitted_count") != len(signal_rows):
        errors.append("admission_limit must record the one-Signal tranche")

    boundary = transaction.get("boundary")
    expected_boundary = {
        "automatic_signal_promotion": False,
        "public_signal_projection": "CLOSED",
        "automatic_relationship_promotion": False,
        "automatic_risk_promotion": False,
        "automatic_scenario_promotion": False,
    }
    if boundary != expected_boundary:
        errors.append("admission boundary does not preserve downstream/public closure")

    dispositions = transaction.get("candidate_dispositions")
    if not isinstance(dispositions, list) or not dispositions:
        errors.append("candidate_dispositions must be a non-empty list")
    else:
        seen: set[str] = set()
        for item in dispositions:
            if not isinstance(item, dict):
                errors.append("candidate disposition must be an object")
                continue
            candidate_id = item.get("candidate_id")
            if not isinstance(candidate_id, str) or not candidate_id.strip() or candidate_id in seen:
                errors.append("candidate dispositions require unique candidate_id values")
            seen.add(candidate_id)
            if item.get("disposition") not in VALID_DISPOSITIONS:
                errors.append(f"invalid candidate disposition for {candidate_id}")
            if not isinstance(item.get("rationale"), str) or not item["rationale"].strip():
                errors.append(f"candidate disposition rationale required for {candidate_id}")

    denominator = transaction.get("denominator_note")
    if not isinstance(denominator, str) or not denominator.strip():
        errors.append("denominator_note is required")

    history = validate_signal_history(schema, signals_dataset.get("signals", []), observations_dataset, evidence_registry)
    errors.extend(history.errors)
    if signal_rows and any(row.get("review_state") != "ACCEPTED" or row.get("lifecycle_state") not in {"ACTIVE", "WEAKENING"} for row in signal_rows if isinstance(row, dict)):
        errors.append("every admitted Signal must be accepted and active/weakening")
    if signal_rows:
        for row in signal_rows:
            if not isinstance(row, dict):
                continue
            if any(str(oid).startswith(("WSC-", "WSC-OBS-")) for oid in row.get("observation_ids", [])):
                errors.append("production Signals may reference governed observations only, not OSINT candidates")
            if set(row.get("observation_hashes", {})) != set(row.get("observation_ids", [])):
                errors.append(f"{row.get('signal_id')}: immutable observation hashes are required")
    return _report(errors)
