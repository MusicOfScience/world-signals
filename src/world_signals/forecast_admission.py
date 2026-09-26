"""Governed, one-shot admission checks for the prospective Forecast pilot.

The admission transaction is deliberately separate from Forecast content.  It
records the reviewed decision and the exact pre/post dataset fingerprints; it
does not provide an update or deletion path for an issued Forecast.
"""

from __future__ import annotations

from hashlib import sha256
import json
from datetime import datetime, timezone
from typing import Any


UTC = timezone.utc


def _utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        return None
    return parsed.astimezone(UTC)


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def stable_json_hash(value: Any) -> str:
    """Hash semantic JSON, independent of whitespace or object key order."""
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return sha256(raw.encode("utf-8")).hexdigest()


def forecast_dataset_hash(dataset: dict[str, Any]) -> str:
    return stable_json_hash({
        "version": dataset.get("version"),
        "population_state": dataset.get("population_state"),
        "forecasts": dataset.get("forecasts"),
    })


def validate_admission_transaction(
    schema: dict[str, Any],
    dataset: dict[str, Any],
    transaction: dict[str, Any] | None,
    *,
    now_utc: str | None = None,
) -> tuple[str, ...]:
    """Validate the explicit pilot admission against the current dataset.

    This is intentionally strict and only accepts the initial bounded pilot:
    no backfill, no resolved target, no duplicate issuance, no mutation of an
    existing row, and no missing human decision provenance.
    """
    errors: list[str] = []
    policy = schema.get("population_policy") if isinstance(schema, dict) else {}
    if policy.get("admission_mode") != "REVIEWED_PROSPECTIVE_PILOT_ONLY":
        errors.append("Forecast schema must declare the reviewed prospective pilot admission mode")
    if not isinstance(dataset, dict) or not isinstance(dataset.get("forecasts"), list):
        return tuple(errors + ["Forecast dataset must contain a forecasts list"])
    if not isinstance(transaction, dict):
        return tuple(errors + ["a reviewed Forecast admission transaction is required for production rows"])
    required = {
        "transaction_id", "transaction_type", "decision", "admitted_at_utc", "reviewer",
        "information_cutoff_at_utc", "forecast_revision_ids", "issuance_ids", "forecast_ids",
        "pre_state", "post_state", "validation", "denominator_obligation", "candidate_audit",
    }
    if set(transaction) != required:
        errors.append("admission transaction has an invalid field set")
    if transaction.get("transaction_type") != "INITIAL_PROSPECTIVE_FORECAST_PILOT":
        errors.append("only the initial prospective Forecast pilot transaction is allowed")
    if transaction.get("decision") != "ACCEPTED":
        errors.append("production Forecast admission requires an ACCEPTED transaction")
    admitted = _utc(transaction.get("admitted_at_utc"))
    cutoff = _utc(transaction.get("information_cutoff_at_utc"))
    if admitted is None or cutoff is None:
        errors.append("admission and information cutoff timestamps must be exact UTC")
    if admitted and cutoff and cutoff > admitted:
        errors.append("pilot information cutoff cannot follow admission")
    if now_utc and (_utc(now_utc) is None or admitted and admitted > _utc(now_utc)):
        errors.append("pilot admission cannot be dated in the future")
    reviewer = transaction.get("reviewer")
    if not isinstance(reviewer, dict) or set(reviewer) != {"reviewer_id", "reviewed_at_utc", "decision_basis"}:
        errors.append("pilot admission requires reviewer, timestamp and decision basis")
    elif not _text(reviewer.get("reviewer_id")) or _utc(reviewer.get("reviewed_at_utc")) is None or not _text(reviewer.get("decision_basis")):
        errors.append("pilot admission reviewer provenance is incomplete")
    revision_ids = transaction.get("forecast_revision_ids")
    issuance_ids = transaction.get("issuance_ids")
    forecast_ids = transaction.get("forecast_ids")
    if not isinstance(revision_ids, list) or not revision_ids or len(revision_ids) != len(set(revision_ids)):
        errors.append("forecast_revision_ids must be a non-empty unique list")
        revision_ids = []
    if not isinstance(issuance_ids, list) or not issuance_ids or len(issuance_ids) != len(set(issuance_ids)):
        errors.append("issuance_ids must be a non-empty unique list")
        issuance_ids = []
    if not isinstance(forecast_ids, list) or not forecast_ids or len(forecast_ids) != len(set(forecast_ids)):
        errors.append("forecast_ids must be a non-empty unique list")
        forecast_ids = []
    max_rows = policy.get("pilot_max_forecast_issuances", 0)
    if len(issuance_ids) > max_rows:
        errors.append("pilot admission exceeds the governed maximum issuance count")
    rows = dataset["forecasts"]
    actual_revision_ids = [row.get("revision_id") for row in rows if isinstance(row, dict)]
    actual_issuance_ids = [row.get("issuance_id") for row in rows if isinstance(row, dict) and row.get("revision_number") == 1]
    actual_forecast_ids = sorted({row.get("forecast_id") for row in rows if isinstance(row, dict)})
    if sorted(revision_ids) != sorted(actual_revision_ids):
        errors.append("admission transaction revisions do not exactly match the production dataset")
    if sorted(issuance_ids) != sorted(actual_issuance_ids):
        errors.append("admission transaction issuances do not exactly match the production dataset")
    if sorted(forecast_ids) != actual_forecast_ids:
        errors.append("admission transaction Forecast series do not exactly match the production dataset")
    pre = transaction.get("pre_state")
    post = transaction.get("post_state")
    for label, state in (("pre_state", pre), ("post_state", post)):
        if not isinstance(state, dict) or not isinstance(state.get("sha256"), str) or not _text(state.get("version")):
            errors.append(f"{label} must contain version and sha256")
    if isinstance(pre, dict):
        pre_payload = {key: value for key, value in pre.items() if key != "sha256"}
        if pre.get("sha256") != stable_json_hash(pre_payload):
            errors.append("pre-state hash does not match its recorded snapshot")
        if pre.get("forecast_count") != 0 or pre.get("population_state") != "CLOSED_NO_PRODUCTION_FORECASTS":
            errors.append("pilot must start from the empty closed Forecast state")
    if isinstance(post, dict):
        post_payload = {key: value for key, value in post.items() if key != "sha256"}
        if post.get("sha256") != stable_json_hash(post_payload):
            errors.append("post-state hash does not match its recorded snapshot")
        if post.get("forecast_count") != len(rows) or post.get("population_state") != dataset.get("population_state"):
            errors.append("post-state snapshot does not match the production dataset")
        if post.get("sha256_dataset") != forecast_dataset_hash(dataset):
            errors.append("post-state dataset hash does not match the production dataset")
    validation = transaction.get("validation")
    if not isinstance(validation, dict) or validation.get("status") != "PASS" or not _text(validation.get("validator_version")) or _utc(validation.get("validated_at_utc")) is None:
        errors.append("admission transaction must retain a passing validation result")
    if not _text(transaction.get("denominator_obligation")):
        errors.append("pilot denominator obligation is required")
    audit = transaction.get("candidate_audit")
    if not isinstance(audit, list) or len(audit) != len(forecast_ids):
        errors.append("candidate audit must contain one entry per admitted Forecast series")
    for row in rows:
        if not isinstance(row, dict):
            continue
        issued = _utc(row.get("issued_at_utc"))
        row_cutoff = _utc(row.get("information_cutoff_at_utc"))
        resolution = row.get("resolution") or {}
        end = _utc(resolution.get("window_end_at_utc"))
        if admitted and end and end <= admitted:
            errors.append(f"{row.get('issuance_id')}: target resolution is not prospective")
        if admitted and issued and issued > admitted:
            errors.append(f"{row.get('issuance_id')}: issuance is dated after admission")
        if cutoff and row_cutoff and row_cutoff > cutoff:
            errors.append(f"{row.get('issuance_id')}: row cutoff follows the frozen pilot cutoff")
        if row.get("review_state") != "ACCEPTED" or (row.get("forecast_provenance") or {}).get("human_reviewed") is not True:
            errors.append(f"{row.get('issuance_id')}: admitted Forecast must have completed human review")
        if row.get("lifecycle_state") != "OPEN":
            errors.append(f"{row.get('issuance_id')}: pilot Forecast must be OPEN")
    return tuple(errors)
