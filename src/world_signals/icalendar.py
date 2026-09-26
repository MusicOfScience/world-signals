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
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


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


def _parse_governed_timestamp(value: object) -> datetime | None:
    """Parse a governed date/time as a UTC instant without using build time."""

    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0)


def _format_governed_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _approved_changes(record: dict, change_ledger: dict | None) -> list[dict]:
    if not isinstance(change_ledger, dict):
        return []
    occurrence_id = str(record.get("occurrence_id") or "")
    return [
        change
        for change in change_ledger.get("changes", [])
        if isinstance(change, dict)
        and str(change.get("occurrence_id") or "") == occurrence_id
        and str(change.get("review_state") or "").startswith("APPROVED")
    ]


def _revision_metadata(
    record: dict,
    *,
    change_ledger: dict | None,
    fallback_timestamp: object,
) -> tuple[int, str, str]:
    """Return deterministic SEQUENCE, DTSTAMP and LAST-MODIFIED values.

    SEQUENCE is based on governed event history plus approved occurrence-specific
    change-ledger transactions.  The ledger is deliberately occurrence-scoped:
    an unrelated registry edit cannot revise this VEVENT.  Counting both sources
    is conservative when a transaction is represented in both places and avoids
    depending on status-history length for timing-only revisions.
    """

    history = record.get("status_history")
    history = history if isinstance(history, list) else []
    changes = _approved_changes(record, change_ledger)
    sequence = max(0, len(history) - 1) + len(changes)

    created_candidates: list[datetime] = []
    modified_candidates: list[datetime] = []
    for key in ("first_discovered_at", "created_at", "created_timestamp"):
        parsed = _parse_governed_timestamp(record.get(key))
        if parsed:
            created_candidates.append(parsed)
            modified_candidates.append(parsed)
    for item in history:
        if not isinstance(item, dict):
            continue
        parsed = _parse_governed_timestamp(item.get("as_of"))
        if parsed:
            created_candidates.append(parsed)
            modified_candidates.append(parsed)
    for key in ("last_verified_at", "updated_at", "last_modified_at"):
        parsed = _parse_governed_timestamp(record.get(key))
        if parsed:
            modified_candidates.append(parsed)
    for change in changes:
        for key in ("reviewed_at", "committed_at"):
            parsed = _parse_governed_timestamp(change.get(key))
            if parsed:
                modified_candidates.append(parsed)

    fallback = _parse_governed_timestamp(fallback_timestamp) or datetime(1970, 1, 1, tzinfo=timezone.utc)
    created = min(created_candidates or [fallback])
    modified = max(modified_candidates or [created, fallback])
    if modified < created:
        modified = created
    return sequence, _format_governed_timestamp(created), _format_governed_timestamp(modified)


def _sequence(record: dict, change_ledger: dict | None = None) -> int:
    """Return the deterministic governed revision sequence for one occurrence."""

    return _revision_metadata(
        record,
        change_ledger=change_ledger,
        fallback_timestamp="1970-01-01",
    )[0]


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


def _event_lines(
    record: dict,
    source: dict,
    *,
    dtstamp: str,
    last_modified: str,
    sequence: int,
) -> list[str] | None:
    timing_type = record.get("timing_type")
    render_policy = record.get("render_policy")
    if render_policy not in VISIBLE_RENDER_POLICIES:
        return None

    common = [
        "BEGIN:VEVENT",
        f"UID:{_escape_text(_uid(record))}",
        f"DTSTAMP:{dtstamp}",
        f"LAST-MODIFIED:{last_modified}",
        f"SEQUENCE:{sequence}",
        f"SUMMARY:{_escape_text((record.get('short_calendar_title') or record.get('canonical_name')) + _certainty_marker(record))}",
    ]

    if timing_type in TIMED_TYPES:
        start_local = record.get("start_local")
        if not start_local or "T" not in str(start_local):
            return None
        timezone_name = record.get("source_timezone")
        if timezone_name:
            try:
                ZoneInfo(str(timezone_name))
            except ZoneInfoNotFoundError as exc:
                raise ValueError(f"unknown source_timezone={timezone_name}") from exc
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
        # An uncertainty window remains visible but does not claim the whole
        # range as busy time in subscriber free/busy views.
        common.append("TRANSP:TRANSPARENT")
    else:
        return None

    common.append(f"DESCRIPTION:{_escape_text(_description(record, source, timing_note=timing_note))}")
    if record.get("location"):
        common.append(f"LOCATION:{_escape_text(record['location'])}")
    common.append("END:VEVENT")
    return common


def _timezone_bounds(records: list[dict]) -> dict[str, tuple[int, int]]:
    bounds: dict[str, list[int]] = {}
    for record in records:
        if record.get("timing_type") not in TIMED_TYPES or not record.get("source_timezone"):
            continue
        start_local = record.get("start_local")
        if not start_local or "T" not in str(start_local):
            continue
        timezone_name = str(record["source_timezone"])
        years = bounds.setdefault(timezone_name, [])
        years.append(_parse_datetime(start_local, "start_local").year)
        if record.get("end_local"):
            years.append(_parse_datetime(record["end_local"], "end_local").year)
    return {name: (min(years), max(years)) for name, years in bounds.items() if years}


def _offset_value(value: object) -> str:
    seconds = int(value.total_seconds()) if value is not None else 0
    sign = "+" if seconds >= 0 else "-"
    seconds = abs(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    suffix = f"{hours:02d}{minutes:02d}"
    if seconds:
        suffix += f"{seconds:02d}"
    return sign + suffix


def _transition_periods(timezone_name: str, start_year: int, end_year: int) -> list[tuple[datetime, object, object, str, bool]]:
    """Derive concrete observance periods from the system IANA tz database.

    The resulting VTIMEZONE is bounded to the years needed by the included
    events, with one year of padding on each side.  No timezone rules are
    hand-authored: offsets and transitions come from ``zoneinfo``.
    """

    zone = ZoneInfo(timezone_name)
    start_utc = datetime(max(1, start_year - 1), 1, 1, tzinfo=timezone.utc)
    end_utc = datetime(min(9998, end_year + 2), 1, 1, tzinfo=timezone.utc)
    step = timedelta(hours=6)
    previous = start_utc.astimezone(zone)
    previous_offset = previous.utcoffset() or timedelta(0)
    periods: list[tuple[datetime, object, object, str, bool]] = [
        (
            previous.replace(tzinfo=None),
            previous_offset,
            previous_offset,
            previous.tzname() or timezone_name,
            bool(previous.dst()),
        )
    ]
    cursor = start_utc + step
    while cursor < end_utc:
        current = cursor.astimezone(zone)
        current_offset = current.utcoffset() or timedelta(0)
        if current_offset != previous_offset:
            low = cursor - step
            high = cursor
            while (high - low).total_seconds() > 1:
                middle = low + (high - low) / 2
                if (middle.astimezone(zone).utcoffset() or timedelta(0)) == previous_offset:
                    low = middle
                else:
                    high = middle
            transition = high.replace(microsecond=0)
            after = transition.astimezone(zone)
            periods.append(
                (
                    after.replace(tzinfo=None),
                    previous_offset,
                    current_offset,
                    after.tzname() or timezone_name,
                    bool(after.dst()),
                )
            )
            previous_offset = current_offset
        cursor += step
    return periods


def _vtimezone_lines(timezone_name: str, bounds: tuple[int, int]) -> list[str]:
    periods = _transition_periods(timezone_name, *bounds)
    lines = ["BEGIN:VTIMEZONE", f"TZID:{_escape_text(timezone_name)}"]
    for local_start, offset_from, offset_to, tzname, daylight in periods:
        lines.extend(
            [
                "BEGIN:DAYLIGHT" if daylight else "BEGIN:STANDARD",
                f"DTSTART:{local_start.strftime('%Y%m%dT%H%M%S')}",
                f"TZOFFSETFROM:{_offset_value(offset_from)}",
                f"TZOFFSETTO:{_offset_value(offset_to)}",
                f"TZNAME:{_escape_text(tzname)}",
                "END:DAYLIGHT" if daylight else "END:STANDARD",
            ]
        )
    lines.append("END:VTIMEZONE")
    return lines


def build_icalendar(
    registry: dict,
    source_registry: dict,
    change_ledger: dict | None = None,
) -> ICalendarBuild:
    """Build a deterministic feed from governed Canonical and Source records."""

    reference_date = str(registry.get("reference_date") or "1970-01-01")
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
    rendered: list[tuple[dict, list[str]]] = []

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
            sequence, dtstamp, last_modified = _revision_metadata(
                record,
                change_ledger=change_ledger,
                fallback_timestamp=reference_date,
            )
            event_lines = _event_lines(
                record,
                source_map.get(record.get("source_id"), {}),
                dtstamp=dtstamp,
                last_modified=last_modified,
                sequence=sequence,
            )
        except (TypeError, ValueError) as exc:
            omitted[occurrence_id] = str(exc)
            continue
        if event_lines is None:
            omitted[occurrence_id] = f"timing_type={record.get('timing_type')} lacks representable dated timing"
            continue
        seen_uids.add(uid)
        rendered.append((record, event_lines))
        included.append(occurrence_id)

    for timezone_name, bounds in sorted(_timezone_bounds([record for record, _ in rendered]).items()):
        lines.extend(_vtimezone_lines(timezone_name, bounds))
    for _, event_lines in rendered:
        lines.extend(event_lines)

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

    timezone_ids: set[str] = set()
    index = 0
    while index < len(unfolded):
        if unfolded[index] != "BEGIN:VTIMEZONE":
            index += 1
            continue
        try:
            end = unfolded.index("END:VTIMEZONE", index + 1)
        except ValueError:
            errors.append("VTIMEZONE is missing END:VTIMEZONE")
            break
        component = unfolded[index : end + 1]
        ids = [line[5:] for line in component if line.startswith("TZID:")]
        if len(ids) != 1 or not ids[0]:
            errors.append("each VTIMEZONE must contain exactly one TZID")
        else:
            if ids[0] in timezone_ids:
                errors.append("duplicate VTIMEZONE TZID")
            timezone_ids.add(ids[0])
        if not any(line in {"BEGIN:STANDARD", "BEGIN:DAYLIGHT"} for line in component):
            errors.append("each VTIMEZONE must contain STANDARD or DAYLIGHT observances")
        for observance in ("STANDARD", "DAYLIGHT"):
            starts = [i for i, line in enumerate(component) if line == f"BEGIN:{observance}"]
            for start in starts:
                try:
                    observance_end = component.index(f"END:{observance}", start + 1)
                except ValueError:
                    errors.append(f"{observance} observance is missing its end")
                    continue
                body = component[start : observance_end + 1]
                required = ("DTSTART:", "TZOFFSETFROM:", "TZOFFSETTO:", "TZNAME:")
                if any(not any(line.startswith(prefix) for line in body) for prefix in required):
                    errors.append(f"{observance} observance is missing a required property")
        index = end + 1

    referenced_tzids: set[str] = set()
    for line in unfolded:
        if not (line.startswith("DTSTART") or line.startswith("DTEND")):
            continue
        match = re.search(r"(?:^|;)TZID=([^;:]+)(?:;|:)", line)
        if match:
            referenced_tzids.add(match.group(1))
    missing_tzids = sorted(referenced_tzids - timezone_ids)
    if missing_tzids:
        errors.append("TZID references missing VTIMEZONE definitions: " + ", ".join(missing_tzids))

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


def write_icalendar(
    path: str | Path,
    registry: dict,
    source_registry: dict,
    change_ledger: dict | None = None,
) -> ICalendarBuild:
    build = build_icalendar(registry, source_registry, change_ledger)
    errors = validate_icalendar(build.text)
    if errors:
        raise ValueError("generated iCalendar failed validation: " + "; ".join(errors))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(build.text, encoding="utf-8", newline="")
    return build
