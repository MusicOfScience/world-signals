from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from zoneinfo import ZoneInfo

from .adapters.japan_statistics_dashboard import JAPAN_HHSPEND_TIMEZONE


def _stable_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def _civil_date(record: dict) -> str:
    value = record.get("start_local")
    if not isinstance(value, str) or len(value) < 10:
        raise ValueError(f"tracked Japan household-spending occurrence lacks start_local: {record.get('occurrence_id')}")
    return value[:10]


def japan_household_spending_review_candidates(
    records: list[dict],
    values: list[object],
    config: dict,
    *,
    now_utc: datetime | None = None,
) -> tuple[list[dict], list[dict]]:
    tracked = config.get("tracked_releases") or []
    configured_ids = list(config.get("canonical_occurrence_ids") or [])
    tracked_ids = [row.get("occurrence_id") for row in tracked]
    if configured_ids != tracked_ids or len(set(configured_ids)) != len(configured_ids):
        raise ValueError("Japan household-spending tracked scope must exactly equal configured occurrence IDs")

    by_id = {row.get("occurrence_id"): row for row in records if row.get("occurrence_id") in set(configured_ids)}
    if set(by_id) != set(configured_ids):
        raise ValueError("Japan household-spending configured occurrence is missing from Canonical")

    value_by_period: dict[str, object] = {}
    for value in values:
        period = getattr(value, "reference_period_code", None)
        if not isinstance(period, str):
            raise ValueError("Japan household-spending API value lacks reference_period_code")
        if period in value_by_period:
            raise ValueError(f"duplicate Japan household-spending value for {period}")
        value_by_period[period] = value

    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    today_japan = now.astimezone(ZoneInfo(JAPAN_HHSPEND_TIMEZONE)).date().isoformat()
    manual_sources = list(config.get("required_manual_verification_source_ids") or [])

    candidates: list[dict] = []
    observations: list[dict] = []
    for track in tracked:
        occurrence_id = track["occurrence_id"]
        period = track["reference_period_code"]
        record = by_id[occurrence_id]
        if record.get("series_id") != "WSER-MAC-JP-HHSPEND":
            raise ValueError(f"Japan household-spending series drift for {occurrence_id}")
        if record.get("source_id") != "WSSRC-MAC-024":
            raise ValueError(f"Japan household-spending canonical source drift for {occurrence_id}")
        if record.get("source_timezone") != JAPAN_HHSPEND_TIMEZONE:
            raise ValueError(f"Japan household-spending source timezone drift for {occurrence_id}")
        if record.get("time_precision") != "DAY":
            raise ValueError(f"Japan household-spending canonical precision drift for {occurrence_id}")

        planned_date = _civil_date(record)
        value = value_by_period.get(period)
        lifecycle = record.get("lifecycle_status")

        if lifecycle == "COMPLETED":
            observations.append({
                "type": (
                    "JAPAN_HHSPEND_COMPLETED_REFERENCE_PERIOD_DATA_AVAILABLE"
                    if value is not None
                    else "JAPAN_HHSPEND_COMPLETED_REFERENCE_PERIOD_DATA_ABSENT_SOURCE_HEALTH_ONLY"
                ),
                "occurrence_id": occurrence_id,
                "reference_period_code": period,
                "canonical_lifecycle_status": lifecycle,
                "event_state_inference": "NONE",
            })
            continue

        if value is None:
            observations.append({
                "type": "JAPAN_HHSPEND_DATA_NOT_YET_AVAILABLE_NO_EVENT_INFERENCE",
                "occurrence_id": occurrence_id,
                "reference_period_code": period,
                "canonical_planned_date": planned_date,
                "canonical_lifecycle_status": lifecycle,
                "event_state_inference": "NONE",
                "absence_is_not_cancellation_or_date_change": True,
            })
            continue

        value_payload = value.as_dict() if hasattr(value, "as_dict") else dict(value)
        early = today_japan < planned_date
        candidate_payload = {
            "occurrence_id": occurrence_id,
            "reference_period_code": period,
            "api_value": value_payload,
            "canonical_planned_date": planned_date,
            "canonical_lifecycle_status": lifecycle,
            "observed_japan_civil_date": today_japan,
            "early_relative_to_canonical_date": early,
        }
        candidate_hash = _stable_hash(candidate_payload)
        candidate_type = (
            "JAPAN_HHSPEND_DATA_AVAILABLE_BEFORE_PLANNED_RELEASE_REVIEW"
            if early
            else "JAPAN_HHSPEND_DATA_AVAILABLE_COMPLETION_REVIEW"
        )
        review_state = (
            "PENDING_SCHEDULE_AND_RESULT_REVIEW"
            if early
            else "PENDING_MANUAL_STATISTICS_BUREAU_RELEASE_COMPLETION_REVIEW"
        )
        candidates.append({
            "candidate_id": "WSRC-JP-HHSPEND-" + candidate_hash[:16],
            "candidate_type": candidate_type,
            "source_id": config.get("source_id"),
            "occurrence_ids": [occurrence_id],
            "old_value": {
                "canonical_start_local": record.get("start_local"),
                "canonical_start_utc": record.get("start_utc"),
                "canonical_time_precision": record.get("time_precision"),
                "canonical_lifecycle_status": lifecycle,
            },
            "new_value": {
                "reference_period_code": period,
                "official_machine_data_available": True,
                "api_value": value_payload,
                "observation_date_japan": today_japan,
                "canonical_date_preserved": planned_date,
                "canonical_clock_preserved": record.get("start_utc"),
                "no_schedule_change_inferred": True,
            },
            "review_state": review_state,
            "candidate_origin": "LIVE_READ_ONLY_MONITOR",
            "event_state_inference": (
                "NONE" if early else "POTENTIAL_COMPLETION_REQUIRES_MANUAL_VERIFICATION"
            ),
            "required_manual_verification_source_ids": manual_sources,
            "automatic_commit_allowed": False,
        })
        observations.append({
            "type": (
                "JAPAN_HHSPEND_DATA_AVAILABLE_EARLY_REVIEW_REQUIRED"
                if early
                else "JAPAN_HHSPEND_DATA_AVAILABLE_COMPLETION_REVIEW_REQUIRED"
            ),
            "occurrence_id": occurrence_id,
            "reference_period_code": period,
            "canonical_planned_date": planned_date,
            "observed_japan_civil_date": today_japan,
            "event_state_inference": (
                "NONE" if early else "POTENTIAL_COMPLETION_REQUIRES_MANUAL_VERIFICATION"
            ),
        })

    return candidates, observations
