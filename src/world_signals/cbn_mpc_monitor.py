from __future__ import annotations

from datetime import date, datetime, timezone
from hashlib import sha256
import json
from urllib.robotparser import RobotFileParser
from zoneinfo import ZoneInfo

from .adapters.base import AdapterError, FetchSnapshot, fetch_bytes
from .adapters.cbn_mpc import CBN_MPC_CALENDAR_URL, CBN_MPC_TIMEZONE, CBNMPCCalendar

CBN_ROBOTS_URL = "https://www.cbn.gov.ng/robots.txt"
CBN_MONITOR_USER_AGENT = "WORLD-SIGNALS-read-only-monitor/0.1"
CBN_SERIES_ID = "WSER-CB-NG-CBN-MPC"


def _stable_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def _civil(value: str | None) -> date | None:
    if not isinstance(value, str) or len(value) < 10:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def cbn_calendar_path_allowed(robots_body: bytes | str) -> bool:
    text = robots_body.decode("utf-8", errors="replace") if isinstance(robots_body, bytes) else robots_body
    parser = RobotFileParser()
    try:
        parser.parse(text.splitlines())
    except Exception as exc:
        raise AdapterError(f"unable to parse CBN robots policy: {exc}") from exc
    return parser.can_fetch(CBN_MONITOR_USER_AGENT, CBN_MPC_CALENDAR_URL)


def fetch_cbn_robots_policy(*, timeout: int = 30) -> tuple[bool, FetchSnapshot]:
    body, snapshot = fetch_bytes(
        CBN_ROBOTS_URL,
        timeout=timeout,
        accept="text/plain,*/*;q=0.1",
    )
    if snapshot.status != 200:
        raise AdapterError(f"CBN robots policy returned HTTP {snapshot.status}")
    return cbn_calendar_path_allowed(body), snapshot


def _configured_scope(records: list[dict], config: dict) -> tuple[dict[int, dict], dict[str, dict]]:
    configured = list(config.get("canonical_occurrence_ids") or [])
    identity = config.get("meeting_number_by_occurrence_id") or {}
    if len(configured) != 2 or len(set(configured)) != 2:
        raise ValueError("CBN MPC configured scope must contain exactly two unique occurrences")
    if set(identity) != set(configured):
        raise ValueError("CBN MPC meeting-number identity map must exactly match configured scope")

    by_occurrence = {row.get("occurrence_id"): row for row in records if row.get("occurrence_id") in set(configured)}
    if set(by_occurrence) != set(configured):
        raise ValueError("CBN MPC configured occurrence is missing from Canonical")

    by_number: dict[int, dict] = {}
    for occurrence_id in configured:
        row = by_occurrence[occurrence_id]
        number = int(identity[occurrence_id])
        if number in by_number:
            raise ValueError("CBN MPC configured meeting numbers must be unique")
        if row.get("series_id") != CBN_SERIES_ID:
            raise ValueError(f"CBN MPC series drift for {occurrence_id}")
        if row.get("source_id") != config.get("source_id"):
            raise ValueError(f"CBN MPC Canonical source drift for {occurrence_id}")
        if row.get("source_timezone") != CBN_MPC_TIMEZONE:
            raise ValueError(f"CBN MPC timezone drift for {occurrence_id}")
        if row.get("time_precision") != "DAY_RANGE" or row.get("timing_type") != "MULTI_DAY_LOCAL":
            raise ValueError(f"CBN MPC temporal semantics drift for {occurrence_id}")
        by_number[number] = row
    return by_number, by_occurrence


def _candidate(record: dict, meeting: dict | None, *, candidate_type: str, source_id: str) -> dict:
    payload = {
        "candidate_type": candidate_type,
        "occurrence_id": record["occurrence_id"],
        "old_start_local": record.get("start_local"),
        "old_end_local": record.get("end_local"),
        "observed": meeting,
    }
    return {
        "candidate_id": "WSRC-CBN-MPC-" + _stable_hash(payload)[:16],
        "candidate_type": candidate_type,
        "source_id": source_id,
        "occurrence_ids": [record["occurrence_id"]],
        "old_value": {
            "start_local": record.get("start_local"),
            "end_local": record.get("end_local"),
            "time_precision": record.get("time_precision"),
            "source_timezone": record.get("source_timezone"),
        },
        "new_value": meeting,
        "review_state": "PENDING_AUTHORITATIVE_CBN_MPC_SCHEDULE_REVIEW",
        "candidate_origin": "LIVE_READ_ONLY_MONITOR",
        "event_state_inference": "NONE",
        "absence_is_not_cancellation_delay_completion_or_certainty_change": candidate_type.endswith("ABSENT_FROM_CURRENT_CALENDAR"),
        "decision_publication_time_inference": "PROHIBITED",
        "automatic_commit_allowed": False,
    }


def cbn_mpc_schedule_review_candidates(
    records: list[dict],
    calendar: CBNMPCCalendar,
    config: dict,
    *,
    now_utc: datetime | None = None,
) -> tuple[list[dict], list[dict]]:
    by_number, by_occurrence = _configured_scope(records, config)
    source_id = str(config.get("source_id"))
    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    today = now.astimezone(ZoneInfo(CBN_MPC_TIMEZONE)).date()

    candidates: list[dict] = []
    observations: list[dict] = []
    seen: set[str] = set()

    for meeting in calendar.meetings:
        record = by_number.get(meeting.meeting_number)
        if record is None:
            start = _civil(meeting.start_local)
            if start is not None and start >= today:
                observations.append({
                    "type": "CBN_MPC_UNTRACKED_FUTURE_MEETING",
                    "meeting_number": meeting.meeting_number,
                    "source_start_local": meeting.start_local,
                    "source_end_local": meeting.end_local,
                    "scope_extension_requires_review": True,
                    "event_state_inference": "NONE",
                    "automatic_commit_allowed": False,
                })
            continue

        canonical_start = _civil(record.get("start_local"))
        if canonical_start is None:
            raise ValueError(f"CBN MPC Canonical start date invalid for {record['occurrence_id']}")
        if canonical_start < today:
            observations.append({
                "type": "CBN_MPC_ELAPSED_TRACKED_OCCURRENCE_NOT_PRESENCE_CHECKED_FOR_EVENT_STATE",
                "occurrence_id": record["occurrence_id"],
                "meeting_number": meeting.meeting_number,
                "event_state_inference": "NONE",
                "presence_is_not_completion_evidence": True,
                "automatic_commit_allowed": False,
            })
            seen.add(record["occurrence_id"])
            continue

        seen.add(record["occurrence_id"])
        observed = meeting.as_dict()
        if record.get("start_local") == meeting.start_local and record.get("end_local") == meeting.end_local:
            observations.append({
                "type": "CBN_MPC_MEETING_WINDOW_NO_CHANGE",
                "occurrence_id": record["occurrence_id"],
                "meeting_number": meeting.meeting_number,
                "canonical_start_local": record.get("start_local"),
                "canonical_end_local": record.get("end_local"),
                "event_state_inference": "NONE",
                "decision_publication_time_inference": "PROHIBITED",
                "automatic_commit_allowed": False,
            })
        else:
            candidates.append(_candidate(
                record,
                observed,
                candidate_type="CBN_MPC_MEETING_WINDOW_DRIFT",
                source_id=source_id,
            ))

    for occurrence_id, record in by_occurrence.items():
        start = _civil(record.get("start_local"))
        if start is None or start < today or occurrence_id in seen:
            continue
        candidates.append(_candidate(
            record,
            None,
            candidate_type="CBN_MPC_TRACKED_FUTURE_MEETING_ABSENT_FROM_CURRENT_CALENDAR",
            source_id=source_id,
        ))

    return candidates, observations
