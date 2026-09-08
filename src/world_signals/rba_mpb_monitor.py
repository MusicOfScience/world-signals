from __future__ import annotations

from datetime import date, datetime, timezone
from hashlib import sha256
import json
from zoneinfo import ZoneInfo

from .adapters.base import AdapterError, FetchSnapshot, fetch_bytes
from .adapters.rba_mpb import RBA_TIMEZONE, RBAMeetingWindow, RBAMonetaryPolicyCalendar

RBA_ROBOTS_URL = "https://www.rba.gov.au/robots.txt"
RBA_SCHEDULE_PATH_PREFIX = "/schedules-events/"

SERIES_BY_KIND = {
    "MEETING_WINDOW": "WS.CB.RBA.MPB_MEETING_WINDOW",
    "DECISION_STATEMENT": "WS.CB.RBA.MONETARY_POLICY_DECISION",
    "PRESS_CONFERENCE": "WS.CB.RBA.MPB_PRESS_CONFERENCE",
    "MINUTES": "WS.CB.RBA.MPB_MINUTES",
}


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


def _star_disallow_rules(body: str) -> tuple[str, ...]:
    rules: list[str] = []
    active = False
    for raw in body.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        if key.lower() == "user-agent":
            active = value == "*"
        elif active and key.lower() == "disallow":
            rules.append(value)
    return tuple(rules)


def rba_schedule_path_disallowed(rules: tuple[str, ...]) -> bool:
    for rule in rules:
        if not rule:
            continue
        prefix = rule.rstrip("*")
        if RBA_SCHEDULE_PATH_PREFIX == prefix or RBA_SCHEDULE_PATH_PREFIX.startswith(prefix):
            return True
    return False


def fetch_rba_robots_policy(*, timeout: int = 30) -> tuple[tuple[str, ...], FetchSnapshot]:
    body, snapshot = fetch_bytes(
        RBA_ROBOTS_URL,
        timeout=timeout,
        accept="text/plain,*/*;q=0.1",
    )
    if snapshot.status != 200:
        raise AdapterError(f"RBA robots policy returned HTTP {snapshot.status}")
    rules = _star_disallow_rules(body.decode("utf-8", errors="replace"))
    return rules, snapshot


def _configured_scope(records: list[dict], config: dict) -> dict[str, dict]:
    configured = list(config.get("canonical_occurrence_ids") or [])
    if not configured or len(configured) != len(set(configured)):
        raise ValueError("RBA MPB configured occurrence scope must be non-empty and unique")
    by_id = {r.get("occurrence_id"): r for r in records if r.get("occurrence_id") in set(configured)}
    if set(by_id) != set(configured):
        raise ValueError("RBA MPB configured occurrence is missing from Canonical")
    source_contract = config.get("canonical_source_role_contract") or {}
    for occurrence_id in configured:
        record = by_id[occurrence_id]
        series = record.get("series_id")
        if series not in set(SERIES_BY_KIND.values()):
            raise ValueError(f"RBA MPB configured series drift for {occurrence_id}")
        if record.get("source_timezone") != RBA_TIMEZONE:
            raise ValueError(f"RBA MPB source timezone drift for {occurrence_id}")
        expected_source = source_contract.get(series)
        if expected_source and record.get("source_id") != expected_source:
            raise ValueError(f"RBA MPB canonical source-role drift for {occurrence_id}")
    return by_id


def _nearest_record(
    records: list[dict],
    *,
    series_id: str,
    source_start: str,
    max_days: int,
) -> tuple[dict | None, bool]:
    source_date = _civil(source_start)
    if source_date is None:
        return None, False
    matches: list[tuple[int, dict]] = []
    for record in records:
        if record.get("series_id") != series_id:
            continue
        planned = _civil(record.get("start_local"))
        if planned is None:
            continue
        delta = abs((planned - source_date).days)
        if delta <= max_days:
            matches.append((delta, record))
    matches.sort(key=lambda item: (item[0], item[1]["occurrence_id"]))
    if not matches:
        return None, False
    if len(matches) > 1 and matches[0][0] == matches[1][0]:
        return None, True
    return matches[0][1], False


def _drift_candidate(record: dict, observed: dict, *, source_id: str, kind: str) -> dict:
    payload = {
        "occurrence_id": record["occurrence_id"],
        "kind": kind,
        "observed": observed,
        "canonical_start_local": record.get("start_local"),
        "canonical_end_local": record.get("end_local"),
        "canonical_source_id": record.get("source_id"),
    }
    digest = _stable_hash(payload)
    return {
        "candidate_id": "WSRC-RBA-MPB-" + digest[:16],
        "candidate_type": "RBA_MPB_SCHEDULE_DRIFT",
        "source_id": source_id,
        "occurrence_ids": [record["occurrence_id"]],
        "old_value": {
            "start_local": record.get("start_local"),
            "end_local": record.get("end_local"),
            "source_timezone": record.get("source_timezone"),
            "time_precision": record.get("time_precision"),
            "canonical_source_id": record.get("source_id"),
        },
        "new_value": observed,
        "review_state": "PENDING_AUTHORITATIVE_RBA_SCHEDULE_REVIEW",
        "candidate_origin": "LIVE_READ_ONLY_MONITOR",
        "event_state_inference": "NONE",
        "automatic_commit_allowed": False,
    }


def rba_mpb_schedule_review_candidates(
    records: list[dict],
    calendar: RBAMonetaryPolicyCalendar,
    board_windows: tuple[RBAMeetingWindow, ...],
    config: dict,
    *,
    now_utc: datetime | None = None,
) -> tuple[list[dict], list[dict]]:
    by_id = _configured_scope(records, config)
    scoped = list(by_id.values())
    max_days = int((config.get("matching") or {}).get("nearest_occurrence_max_days", 14))
    source_id = str(config.get("source_id"))
    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    today = now.astimezone(ZoneInfo(RBA_TIMEZONE)).date()

    candidates: list[dict] = []
    observations: list[dict] = []
    seen_ids: set[str] = set()

    for window in board_windows:
        source_date = _civil(window.start_local)
        if source_date is None or source_date < today:
            continue
        record, ambiguous = _nearest_record(
            scoped,
            series_id=SERIES_BY_KIND["MEETING_WINDOW"],
            source_start=window.start_local,
            max_days=max_days,
        )
        if ambiguous:
            observations.append({
                "type": "RBA_MPB_MEETING_WINDOW_IDENTITY_AMBIGUOUS",
                "source_start_local": window.start_local,
                "source_end_local": window.end_local,
                "event_state_inference": "NONE",
            })
            continue
        if record is None:
            observations.append({
                "type": "RBA_MPB_UNTRACKED_FUTURE_MEETING_WINDOW",
                "source_start_local": window.start_local,
                "source_end_local": window.end_local,
                "scope_extension_requires_review": True,
                "event_state_inference": "NONE",
            })
            continue
        seen_ids.add(record["occurrence_id"])
        observed = {
            "start_local": window.start_local,
            "end_local": window.end_local,
            "source_timezone": window.source_timezone,
            "time_precision": window.time_precision,
            "monitor_surface": "RBA_BOARD_SCHEDULE",
        }
        if record.get("start_local") == window.start_local and record.get("end_local") == window.end_local:
            observations.append({
                "type": "RBA_MPB_MEETING_WINDOW_NO_CHANGE",
                "occurrence_id": record["occurrence_id"],
                "canonical_source_id": record.get("source_id"),
                "event_state_inference": "NONE",
            })
        else:
            candidates.append(_drift_candidate(record, observed, source_id=source_id, kind="MEETING_WINDOW"))

    for event in calendar.events:
        if event.event_kind == "MEETING_WINDOW":
            continue
        source_date = _civil(event.start_local)
        if source_date is None or source_date < today:
            continue
        series_id = SERIES_BY_KIND[event.event_kind]
        record, ambiguous = _nearest_record(
            scoped,
            series_id=series_id,
            source_start=event.start_local,
            max_days=max_days,
        )
        if ambiguous:
            observations.append({
                "type": "RBA_MPB_EVENT_IDENTITY_AMBIGUOUS",
                "event_kind": event.event_kind,
                "source_start_local": event.start_local,
                "event_state_inference": "NONE",
            })
            continue
        if record is None:
            observations.append({
                "type": "RBA_MPB_UNTRACKED_FUTURE_CALENDAR_EVENT",
                "event_kind": event.event_kind,
                "source_start_local": event.start_local,
                "scope_extension_requires_review": True,
                "event_state_inference": "NONE",
            })
            continue
        seen_ids.add(record["occurrence_id"])
        observed = {
            "start_local": event.start_local,
            "end_local": event.end_local,
            "source_timezone": event.source_timezone,
            "time_precision": event.time_precision,
            "published_timezone_label": event.published_timezone_label,
            "monitor_surface": "RBA_MPB_TOPIC_CALENDAR",
            "canonical_source_id_preserved": record.get("source_id"),
        }
        if record.get("start_local") == event.start_local and record.get("end_local") == event.end_local:
            observations.append({
                "type": "RBA_MPB_CALENDAR_EVENT_NO_CHANGE",
                "occurrence_id": record["occurrence_id"],
                "event_kind": event.event_kind,
                "canonical_source_id": record.get("source_id"),
                "monitor_source_id": source_id,
                "event_state_inference": "NONE",
            })
        else:
            candidates.append(_drift_candidate(record, observed, source_id=source_id, kind=event.event_kind))

    for record in scoped:
        start = _civil(record.get("start_local"))
        if start is None or start < today or record["occurrence_id"] in seen_ids:
            continue
        observations.append({
            "type": "RBA_MPB_TRACKED_OCCURRENCE_NOT_PRESENT_ON_CURRENT_SURFACES_NO_EVENT_INFERENCE",
            "occurrence_id": record["occurrence_id"],
            "series_id": record.get("series_id"),
            "canonical_start_local": record.get("start_local"),
            "canonical_source_id": record.get("source_id"),
            "absence_is_not_cancellation_delay_or_completion": True,
            "event_state_inference": "NONE",
        })

    return candidates, observations
