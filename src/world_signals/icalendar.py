"""Deterministic, read-only iCalendar projection of governed Canonical records.

The feed is deliberately narrower than the Canonical Registry.  It includes
records whose render policy makes them calendar-visible and whose timing can be
represented without inventing a date or clock time.  Unresolved TBC,
source-native-calendar, season-only and monitor-only records are reported as
omitted rather than being turned into synthetic appointments.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import re
from typing import Iterable


CALENDAR_NAME = "WORLD SIGNALS"
PRODID = "-//WORLD SIGNALS//Governed Calendar Projection//EN"

VISIBLE_RENDER_POLICIES = {
    "BACKGROUND_LINKED",
    "INCLUDE",
    "INCLUDE_ANALYST",
    "INCLUDE_TIER1",
    "INCLUDE_WITH_CONDITIONAL_MARKER",
    "INCLUDE_WITH_PROVISIONAL_MARKER",
    "INCLUDE_WITH_TBC_MARKER",
    "THEMATIC_ONLY",
}

TIMED_TYPES = {"LOCAL_DATETIME", "LOCAL_DATETIME_RANGE", "TIMED_EVENT"}
DATE_RANGE_TYPES = {"CIVIL_DATE", "DATE_RANGE", "JURISDICTIONAL_CIVIL_DATE", "MULTI_DAY_LOCAL"}
WINDOW_TYPES = {"EXPECTED_DATE_WINDOW", "EXPECTED_YEAR_WINDOW"}
ALL_DAY_RANGE_TYPE = "ALL_DAY_RANGE"

_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_DATETIME_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2})(?:\.(\d+))?)?$")


@dataclass
class ICalendarBuild:
    """Build result, including explicit omission reasons for auditability."""

    text: str
    included_occurrence_ids: list[str] = field(default_factory=list)
    omitted: dict[str, str] = field(default_factory=dict)


def _escape_text(value: object) -> str:
    text = "" if value is None else str(value)
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
        .replace("\r", "\\n")
    )


def _fold_line(line: str) -> list[str]:
    """Fold one content line at the RFC 5545 75-octet boundary."""

    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return [line]

    chunks: list[str] = []
    while raw:
        limit = 75 if not chunks else 74
        chunk = raw[:limit]
        while True:
            try:
                text = chunk.decode("utf-8")
                break
            except UnicodeDecodeError:
                chunk = chunk[:-1]
        chunks.append(text)
        raw = raw[len(chunk) :]
    return [chunks[0], *[f" {chunk}" for chunk in chunks[1:]]]


def _content_lines(lines: Iterable[str]) -> str:
    folded: list[str] = []
    for line in lines:
        folded.extend(_fold_line(line))
    return "\r\n".join(folded) + "\r\n"


def _parse_date(value: object, field_name: str) -> date:
    match = _DATE_RE.fullmatch(str(value or ""))
    if not match:
        raise ValueError(f"{field_name} must be an ISO date: {value!r}")
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(f"{field_name} is not a valid date: {value!r}") from exc


def _date_value(value: date) -> str:
    return value.strftime("%Y%m%d")


def _parse_datetime(value: object, field_name: str) -> datetime:
    text = str(value or "")
    match = _DATETIME_RE.fullmatch(text)
    if not match:
        raise ValueError(f"{field_name} must be an ISO local datetime: {value!r}")
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} is not a valid datetime: {value!r}") from exc


def _local_datetime_value(value: object, field_name: str) -> str:
    parsed = _parse_datetime(value, field_name)
    if parsed.tzinfo is not None:
        raise ValueError(f"{field_name} must not contain an offset when paired with TZID")
    return parsed.strftime("%Y%m%dT%H%M%S")


def _utc_datetime_value(value: object, field_name: str) -> str:
    text = str(value or "")
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _uid(record: dict) -> str:
    occurrence_id = str(record.get("occurrence_id") or "").strip()
    if not occurrence_id:
        raise ValueError("calendar-visible record is missing occurrence_id")
    return f"{occurrence_id}@world-signals"


def _sequence(record: dict) -> int:
    """Use governed assertion history as a deterministic revision sequence."""

    history = record.get("status_history")
    if isinstance(history, list):
        return max(0, len(history) - 1)
    return 0


def _certainty_marker(record: dict) -> str:
    certainty = record.get("certainty_status")
    timing_type = record.get("timing_type")
    if timing_type in WINDOW_TYPES:
        return " [EXPECTED WINDOW]"
    if certainty == "PROVISIONAL":
        return " [PROVISIONAL]"
    if record.get("round_activation_status") or record.get("condition_state") not in (None, "NOT_REQUIRED"):
        return " [CONDITIONAL]"
    return ""


def _description(record: dict, source: dict, *, timing_note: str | None = None) -> str:
    jurisdiction = record.get("jurisdiction")
    if isinstance(jurisdiction, list):
        jurisdiction_text = ", ".join(str(item) for item in jurisdiction)
    else:
        jurisdiction_text = str(jurisdiction or "")
    lines = [
        "WORLD SIGNALS governed calendar projection.",
        f"Occurrence ID: {record.get('occurrence_id')}",
        f"Series ID: {record.get('series_id')}",
        f"Institution: {record.get('institution')}",
        f"Jurisdiction: {jurisdiction_text}",
        f"Certainty: {record.get('certainty_status')}; lifecycle: {record.get('lifecycle_status')}",
    ]
    if timing_note:
        lines.append(f"Timing: {timing_note}")
    if record.get("location"):
        lines.append(f"Location: {record['location']}")
    if record.get("notes"):
        lines.append(f"Notes: {record['notes']}")
    if source.get("authoritative_url"):
        lines.append(f"Source: {source['authoritative_url']}")
    return "\n".join(lines)


def _source_map(source_registry: dict) -> dict[str, dict]:
    return {
        str(source.get("source_id")): source
        for source in source_registry.get("sources", [])
        if source.get("source_id")
    }


def _event_lines(record: dict, source: dict, *, dtstamp: str) -> list[str] | None:
    timing_type = record.get("timing_type")
    render_policy = record.get("render_policy")
    if render_policy not in VISIBLE_RENDER_POLICIES:
        return None

    common = [
        "BEGIN:VEVENT",
        f"UID:{_escape_text(_uid(record))}",
        f"DTSTAMP:{dtstamp}",
        f"SEQUENCE:{_sequence(record)}",
        f"SUMMARY:{_escape_text((record.get('short_calendar_title') or record.get('canonical_name')) + _certainty_marker(record))}",
    ]

    if timing_type in TIMED_TYPES:
        start_local = record.get("start_local")
        if not start_local or "T" not in str(start_local):
            return None
        timezone_name = record.get("source_timezone")
        if timezone_name:
            common.append(f"DTSTART;TZID={_escape_text(timezone_name)}:{_local_datetime_value(start_local, 'start_local')}")
            if record.get("end_local"):
                common.append(f"DTEND;TZID={_escape_text(timezone_name)}:{_local_datetime_value(record['end_local'], 'end_local')}")
        elif record.get("start_utc"):
            common.append(f"DTSTART:{_utc_datetime_value(record['start_utc'], 'start_utc')}")
            if record.get("end_utc"):
                common.append(f"DTEND:{_utc_datetime_value(record['end_utc'], 'end_utc')}")
        else:
            return None
        timing_note = "source-local timed occurrence"
    elif timing_type in DATE_RANGE_TYPES:
        start = record.get("start_local")
        if not start or "T" in str(start):
            return None
        start_date = _parse_date(start, "start_local")
        common.append(f"DTSTART;VALUE=DATE:{_date_value(start_date)}")
        if record.get("end_local"):
            end_date = _parse_date(record["end_local"], "end_local")
            common.append(f"DTEND;VALUE=DATE:{_date_value(end_date + timedelta(days=1))}")
        timing_note = "civil/date-only occurrence; source timezone is retained in Canonical provenance"
    elif timing_type == ALL_DAY_RANGE_TYPE:
        start = record.get("start_local")
        end = record.get("end_local")
        if not start or not end:
            return None
        start_date = _parse_date(start, "start_local")
        end_date = _parse_date(end, "end_local")
        common.append(f"DTSTART;VALUE=DATE:{_date_value(start_date)}")
        common.append(f"DTEND;VALUE=DATE:{_date_value(end_date + timedelta(days=1))}")
        timing_note = "governed all-day range"
    elif timing_type in WINDOW_TYPES:
        start = record.get("date_earliest")
        end = record.get("date_latest")
        if not start or not end:
            return None
        start_date = _parse_date(start, "date_earliest")
        end_date = _parse_date(end, "date_latest")
        common.append(f"DTSTART;VALUE=DATE:{_date_value(start_date)}")
        common.append(f"DTEND;VALUE=DATE:{_date_value(end_date + timedelta(days=1))}")
        timing_note = f"expected date window {start} to {end}; exact appointment date is not asserted"
    else:
        return None

    common.append(f"DESCRIPTION:{_escape_text(_description(record, source, timing_note=timing_note))}")
    if record.get("location"):
        common.append(f"LOCATION:{_escape_text(record['location'])}")
    common.append("END:VEVENT")
    return common


def build_icalendar(registry: dict, source_registry: dict) -> ICalendarBuild:
    """Build a deterministic feed from governed Canonical and Source records."""

    reference_date = str(registry.get("reference_date") or "1970-01-01")
    dtstamp = f"{reference_date.replace('-', '')}T000000Z"
    source_map = _source_map(source_registry)
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape_text(CALENDAR_NAME)}",
        "X-WR-TIMEZONE:UTC",
    ]
    included: list[str] = []
    omitted: dict[str, str] = {}
    seen_uids: set[str] = set()

    records = sorted(registry.get("records", []), key=lambda record: str(record.get("occurrence_id") or ""))
    for record in records:
        occurrence_id = str(record.get("occurrence_id") or "<missing>")
        render_policy = record.get("render_policy")
        if render_policy not in VISIBLE_RENDER_POLICIES:
            omitted[occurrence_id] = f"render_policy={render_policy or 'MISSING'}"
            continue
        if record.get("timing_type") in {"DEADLINE_BOUND_TBC", "SOURCE_NATIVE_CALENDAR_DATE", "MONTH_BOUNDED_SEASON_WINDOW", "UNSCHEDULED_TBC"}:
            omitted[occurrence_id] = f"timing_type={record.get('timing_type')} is not a dated appointment"
            continue
        try:
            uid = _uid(record)
            if uid in seen_uids:
                raise ValueError(f"duplicate UID {uid}")
            event_lines = _event_lines(record, source_map.get(record.get("source_id"), {}), dtstamp=dtstamp)
        except (TypeError, ValueError) as exc:
            omitted[occurrence_id] = str(exc)
            continue
        if event_lines is None:
            omitted[occurrence_id] = f"timing_type={record.get('timing_type')} lacks representable dated timing"
            continue
        seen_uids.add(uid)
        lines.extend(event_lines)
        included.append(occurrence_id)

    lines.append("END:VCALENDAR")
    return ICalendarBuild(_content_lines(lines), included, omitted)


def validate_icalendar(text: str) -> list[str]:
    """Validate structural invariants needed by the static subscription feed."""

    errors: list[str] = []
    if not text.endswith("\r\n"):
        errors.append("calendar must end with CRLF")
    if "\n" in text.replace("\r\n", ""):
        errors.append("calendar contains a bare LF")
    raw_lines = text.split("\r\n")[:-1] if text.endswith("\r\n") else text.split("\r\n")
    if any(len(line.encode("utf-8")) > 75 for line in raw_lines):
        errors.append("calendar contains a line longer than 75 UTF-8 octets")

    unfolded: list[str] = []
    for line in raw_lines:
        if line.startswith(" "):
            if not unfolded:
                errors.append("calendar begins with a continuation line")
            else:
                unfolded[-1] += line[1:]
        else:
            unfolded.append(line)

    if unfolded[:1] != ["BEGIN:VCALENDAR"] or unfolded[-1:] != ["END:VCALENDAR"]:
        errors.append("calendar must be wrapped in VCALENDAR")
    if "VERSION:2.0" not in unfolded or "PRODID:" + PRODID not in unfolded:
        errors.append("calendar is missing required version or PRODID")

    starts = [index for index, line in enumerate(unfolded) if line == "BEGIN:VEVENT"]
    ends = [index for index, line in enumerate(unfolded) if line == "END:VEVENT"]
    if len(starts) != len(ends):
        errors.append("VEVENT begin/end count mismatch")
    uids: list[str] = []
    for start, end in zip(starts, ends):
        if end < start:
            errors.append("VEVENT closes before it opens")
            continue
        event = unfolded[start : end + 1]
        uid_lines = [line for line in event if line.startswith("UID:")]
        dtstart_lines = [line for line in event if line.startswith("DTSTART")]
        if len(uid_lines) != 1:
            errors.append("each VEVENT must contain exactly one UID")
        else:
            uids.append(uid_lines[0])
        if len(dtstart_lines) != 1:
            errors.append("each VEVENT must contain exactly one DTSTART")
    if len(uids) != len(set(uids)):
        errors.append("duplicate VEVENT UID")
    return errors


def write_icalendar(path: str | Path, registry: dict, source_registry: dict) -> ICalendarBuild:
    build = build_icalendar(registry, source_registry)
    errors = validate_icalendar(build.text)
    if errors:
        raise ValueError("generated iCalendar failed validation: " + "; ".join(errors))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(build.text, encoding="utf-8", newline="")
    return build
