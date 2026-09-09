from __future__ import annotations

from hashlib import sha256
import json

from .adapters.hmt_t1_content_api import HMTT1ContentState

CANONICAL_SOURCE_ID = "WSSRC-MKT-012"
MONITOR_SOURCE_ID = "WSSRC-MKT-014"
OCCURRENCE_ID = "WSO-MKT-A-0016"
SERIES_ID = "WSER-MKT-UK-T1"
BASELINE_PUBLIC_UPDATED_AT = "2025-11-20T09:30:10+00:00"


def _stable_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def _scope(records: list[dict], config: dict) -> dict:
    ids = list(config.get("canonical_occurrence_ids") or [])
    if ids != [OCCURRENCE_ID]:
        raise ValueError("HMT T+1 monitor requires exact one-occurrence scope")
    matches = [r for r in records if r.get("occurrence_id") == OCCURRENCE_ID]
    if len(matches) != 1:
        raise ValueError("HMT T+1 configured occurrence missing or duplicated in Canonical")
    row = matches[0]
    checks = {
        "series_id": SERIES_ID,
        "source_id": CANONICAL_SOURCE_ID,
        "category": "CORPORATE_FINANCIAL_MARKET_STRUCTURE",
        "activation_mode": "CONDITIONAL",
        "certainty_status": "PROVISIONAL",
        "condition_state": "PENDING_DEPENDENCY",
        "start_local": "2027-10-11",
        "time_status": "PROVISIONAL",
        "timing_type": "JURISDICTIONAL_CIVIL_DATE",
    }
    for key, expected in checks.items():
        if row.get(key) != expected:
            raise ValueError(f"HMT T+1 Canonical scope drift for {key}: {row.get(key)!r}")

    gates = (
        "schedule_authority",
        "clock_authority",
        "lifecycle_authority",
        "certainty_authority",
        "condition_state_authority",
        "canonical_datetime_mutation_allowed",
        "automatic_attachment_fetch_allowed",
        "automatic_parent_page_fetch_allowed",
        "automatic_legislation_followup_allowed",
        "automatic_new_occurrence_creation_allowed",
        "automatic_live_or_analysis_promotion_allowed",
        "automatic_commit_allowed",
    )
    if config.get("source_id") != MONITOR_SOURCE_ID or any(config.get(key) is not False for key in gates):
        raise ValueError("HMT T+1 authority/write gate drift")
    if config.get("baseline_public_updated_at") != BASELINE_PUBLIC_UPDATED_AT:
        raise ValueError("HMT T+1 baseline public_updated_at drift")
    return row


def hmt_t1_dependency_review_candidate(
    records: list[dict], state: HMTT1ContentState, config: dict
) -> tuple[dict | None, dict]:
    row = _scope(records, config)
    marker_values = state.pending_markers
    markers_still_pending = bool(marker_values) and all(marker_values.values())
    public_revision = state.public_updated_at != BASELINE_PUBLIC_UPDATED_AT
    change_detected = public_revision or state.withdrawn or not markers_still_pending

    evidence = {
        "content_id": state.content_id,
        "public_updated_at": state.public_updated_at,
        "baseline_public_updated_at": BASELINE_PUBLIC_UPDATED_AT,
        "public_revision_observed": public_revision,
        "withdrawn": state.withdrawn,
        "pending_markers": marker_values,
        "semantic_sha256": state.semantic_sha256,
        "raw_transport_hash_is_legal_state_evidence": False,
        "legal_completion_inference": "NONE",
        "canonical_source_id": CANONICAL_SOURCE_ID,
    }

    if not change_detected:
        return None, {
            "type": "HMT_T1_DEPENDENCY_BASELINE_STILL_PENDING_NO_CANONICAL_ACTION",
            "occurrence_id": OCCURRENCE_ID,
            "source_id": MONITOR_SOURCE_ID,
            "public_updated_at": state.public_updated_at,
            "semantic_sha256": state.semantic_sha256,
            "event_state_inference": "NONE",
            "condition_state_inference": "NONE",
            "automatic_commit_allowed": False,
        }

    digest = _stable_hash({"occurrence_id": OCCURRENCE_ID, **evidence})
    candidate = {
        "candidate_id": "WSRC-HMT-T1-" + digest[:16],
        "candidate_type": "HMT_T1_LEGISLATIVE_DEPENDENCY_REVIEW",
        "source_id": MONITOR_SOURCE_ID,
        "occurrence_ids": [OCCURRENCE_ID],
        "old_value": {
            "certainty_status": row.get("certainty_status"),
            "condition_state": row.get("condition_state"),
            "start_local": row.get("start_local"),
            "canonical_source_id": CANONICAL_SOURCE_ID,
            "baseline_public_updated_at": BASELINE_PUBLIC_UPDATED_AT,
        },
        "new_value": evidence,
        "review_state": "PENDING_AUTHORITATIVE_UK_LEGISLATION_VERIFICATION",
        "candidate_origin": "LIVE_READ_ONLY_MONITOR",
        "event_state_inference": "NONE",
        "condition_state_inference": "NONE",
        "canonical_datetime_mutation_allowed": False,
        "completion_requires_review": True,
        "automatic_commit_allowed": False,
    }
    observation = {
        "type": "HMT_T1_CONTENT_API_CHANGE_REVIEW_REQUIRED",
        "occurrence_id": OCCURRENCE_ID,
        "source_id": MONITOR_SOURCE_ID,
        "public_revision_observed": public_revision,
        "withdrawn": state.withdrawn,
        "pending_markers_still_all_present": markers_still_pending,
        "legal_completion_inference": "NONE",
        "event_state_inference": "NONE",
        "condition_state_inference": "NONE",
        "automatic_commit_allowed": False,
    }
    return candidate, observation
