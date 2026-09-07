from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
from html.parser import HTMLParser
import json
import re

from .base import AdapterError, FetchSnapshot, fetch_bytes

RBA_MPB_CALENDAR_URL = "https://www.rba.gov.au/schedules-events/calendar/?topics=monetary-policy-board"
RBA_BOARD_SCHEDULE_URL = "https://www.rba.gov.au/schedules-events/board-meeting-schedules.html"
RBA_TIMEZONE = "Australia/Sydney"

RBA_SERIES_BY_KIND = {
    "MEETING_WINDOW": "WS.CB.RBA.MPB_MEETING_WINDOW",
    "DECISION_STATEMENT": "WS.CB.RBA.MONETARY_POLICY_DECISION",
    "PRESS_CONFERENCE": "WS.CB.RBA.MPB_PRESS_CONFERENCE",
    "MINUTES": "WS.CB.RBA.MPB_MINUTES",
}

_MONTH = (
    "January|February|March|April|May|June|July|August|September|October|November|December"
)
_DATE_RE = rf"\d{{1,2}}\s+(?:{_MONTH})\s+\d{{4}}"
_TIME_RE = r"\d{1,2}(?:[.:]\d{2})?\s*(?:am|pm)\s*(?:AEST|AEDT)"


def _norm(value: str) -> str:
    return " ".join(
        value.replace("\xa0", " ")
        .replace("\u202f", " ")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .split()
    )


def _stable_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def _parse_date(value: str) -> str:
    clean = _norm(value)
    try:
        return datetime.strptime(clean, "%d %B %Y").date().isoformat()
    except ValueError as exc:
        raise AdapterError(f"unrecognised RBA civil date: {value!r}") from exc


def _parse_time(value: str) -> tuple[str, str]:
    clean = _norm(value).replace(":", ".")
    match = re.fullmatch(r"(\d{1,2})(?:\.(\d{2}))?\s*(am|pm)\s*(AEST|AEDT)", clean, re.I)
    if not match:
        raise AdapterError(f"unrecognised RBA local time: {value!r}")
    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    meridiem = match.group(3).lower()
    if not 1 <= hour <= 12 or not 0 <= minute <= 59:
        raise AdapterError(f"invalid RBA local time: {value!r}")
    hour = hour % 12 + (12 if meridiem == "pm" else 0)
    return f"{hour:02d}:{minute:02d}:00", match.group(4).upper()


def _parse_date_range(value: str) -> tuple[str, str]:
    clean = _norm(value)
    full = re.search(rf"({_DATE_RE})\s*-\s*({_DATE_RE})", clean, re.I)
    if full:
        return _parse_date(full.group(1)), _parse_date(full.group(2))
    compact = re.search(rf"(\d{{1,2}})\s*-\s*(\d{{1,2}})\s+({_MONTH})\s+(\d{{4}})", clean, re.I)
    if compact:
        month = compact.group(3)
        year = compact.group(4)
        return (
            _parse_date(f"{compact.group(1)} {month} {year}"),
            _parse_date(f"{compact.group(2)} {month} {year}"),
        )
    single = re.search(rf"({_DATE_RE})", clean, re.I)
    if single:
        date = _parse_date(single.group(1))
        return date, date
    raise AdapterError(f"RBA meeting date/range not found in {value!r}")


class _HeadingBlockParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[tuple[str, list[str]]] = []
        self._heading_tag: str | None = None
        self._heading_parts: list[str] = []
        self._current_index: int | None = None

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._heading_tag = tag
            self._heading_parts = []

    def handle_endtag(self, tag: str) -> None:
        if self._heading_tag == tag.lower():
            heading = _norm(" ".join(self._heading_parts))
            if heading:
                self.blocks.append((heading, []))
                self._current_index = len(self.blocks) - 1
            self._heading_tag = None
            self._heading_parts = []

    def handle_data(self, data: str) -> None:
        value = _norm(data)
        if not value:
            return
        if self._heading_tag is not None:
            self._heading_parts.append(value)
        elif self._current_index is not None:
            self.blocks[self._current_index][1].append(value)


class _BoardTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[tuple[str, list[list[str]]]] = []
        self._in_table = False
        self._caption_parts: list[str] = []
        self._in_caption = False
        self._rows: list[list[str]] = []
        self._in_row = False
        self._row: list[str] = []
        self._in_cell = False
        self._cell_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag == "table" and not self._in_table:
            self._in_table = True
            self._caption_parts = []
            self._rows = []
        elif self._in_table and tag == "caption":
            self._in_caption = True
        elif self._in_table and tag == "tr":
            self._in_row = True
            self._row = []
        elif self._in_table and self._in_row and tag in {"td", "th"}:
            self._in_cell = True
            self._cell_parts = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._in_table and self._in_cell and tag in {"td", "th"}:
            self._row.append(_norm(" ".join(self._cell_parts)))
            self._in_cell = False
            self._cell_parts = []
        elif self._in_table and self._in_row and tag == "tr":
            if self._row:
                self._rows.append(self._row)
            self._in_row = False
            self._row = []
        elif self._in_table and tag == "caption":
            self._in_caption = False
        elif self._in_table and tag == "table":
            self.tables.append((_norm(" ".join(self._caption_parts)), self._rows))
            self._in_table = False

    def handle_data(self, data: str) -> None:
        value = _norm(data)
        if not value:
            return
        if self._in_caption:
            self._caption_parts.append(value)
        if self._in_cell:
            self._cell_parts.append(value)


@dataclass(frozen=True)
class RBAMonetaryPolicyEvent:
    event_kind: str
    canonical_series_id: str
    start_local: str
    end_local: str | None
    source_timezone: str
    published_timezone_label: str | None
    time_precision: str

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class RBAMonetaryPolicyCalendar:
    events: tuple[RBAMonetaryPolicyEvent, ...]

    def normalized_payload(self) -> dict:
        return {"events": [event.as_dict() for event in self.events]}

    @property
    def schedule_sha256(self) -> str:
        return _stable_hash(self.normalized_payload())

    def as_dict(self) -> dict:
        payload = self.normalized_payload()
        payload["schedule_sha256"] = self.schedule_sha256
        return payload


@dataclass(frozen=True)
class RBAMeetingWindow:
    start_local: str
    end_local: str
    source_timezone: str = RBA_TIMEZONE
    time_precision: str = "CIVIL_DATE"

    def as_dict(self) -> dict:
        return asdict(self)


def _timed_event(kind: str, body: str) -> RBAMonetaryPolicyEvent:
    date_match = re.search(rf"({_DATE_RE})", body, re.I)
    time_match = re.search(rf"({_TIME_RE})", body, re.I)
    if not date_match or not time_match:
        raise AdapterError(f"RBA {kind} block lacks published date/time: {body!r}")
    date = _parse_date(date_match.group(1))
    time_value, label = _parse_time(time_match.group(1))
    return RBAMonetaryPolicyEvent(
        event_kind=kind,
        canonical_series_id=RBA_SERIES_BY_KIND[kind],
        start_local=f"{date}T{time_value}",
        end_local=None,
        source_timezone=RBA_TIMEZONE,
        published_timezone_label=label,
        time_precision="EXACT_LOCAL_TIME",
    )


def parse_rba_monetary_policy_calendar_html(body: bytes | str) -> RBAMonetaryPolicyCalendar:
    text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body
    parser = _HeadingBlockParser()
    try:
        parser.feed(text)
    except Exception as exc:
        raise AdapterError(f"unable to parse RBA monetary-policy calendar HTML: {exc}") from exc

    events: list[RBAMonetaryPolicyEvent] = []
    for heading, parts in parser.blocks:
        body_text = _norm(" ".join(parts))
        if heading == "Monetary Policy Board Meeting":
            start, end = _parse_date_range(body_text)
            events.append(
                RBAMonetaryPolicyEvent(
                    event_kind="MEETING_WINDOW",
                    canonical_series_id=RBA_SERIES_BY_KIND["MEETING_WINDOW"],
                    start_local=start,
                    end_local=end,
                    source_timezone=RBA_TIMEZONE,
                    published_timezone_label=None,
                    time_precision="CIVIL_DATE_RANGE",
                )
            )
        elif heading == "Monetary Policy Decision Statement":
            events.append(_timed_event("DECISION_STATEMENT", body_text))
        elif heading == "Monetary Policy Decision" and re.search(r"\bMedia conference\b", body_text, re.I):
            events.append(_timed_event("PRESS_CONFERENCE", body_text))
        elif re.fullmatch(r"Minutes of the .+ Monetary Policy Board Meeting", heading):
            events.append(_timed_event("MINUTES", body_text))

    if not events:
        raise AdapterError("RBA monetary-policy calendar contained no target event blocks")

    keys = [(event.event_kind, event.start_local, event.end_local) for event in events]
    if len(keys) != len(set(keys)):
        raise AdapterError("RBA monetary-policy calendar contained duplicate semantic events")

    events.sort(key=lambda event: (event.start_local, event.event_kind))
    return RBAMonetaryPolicyCalendar(events=tuple(events))


def parse_rba_board_schedule_html(body: bytes | str) -> tuple[RBAMeetingWindow, ...]:
    text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body
    parser = _BoardTableParser()
    try:
        parser.feed(text)
    except Exception as exc:
        raise AdapterError(f"unable to parse RBA board schedule HTML: {exc}") from exc

    windows: list[RBAMeetingWindow] = []
    for caption, rows in parser.tables:
        year_match = re.search(r"Board meeting schedules\s+(20\d{2})", caption, re.I)
        if not year_match or not rows:
            continue
        year = int(year_match.group(1))
        header = [cell.lower() for cell in rows[0]]
        if "month" not in header or "monetary policy board" not in header:
            continue
        month_index = header.index("month")
        mpb_index = header.index("monetary policy board")
        for row in rows[1:]:
            if len(row) <= max(month_index, mpb_index):
                continue
            month = row[month_index].strip()
            value = row[mpb_index].strip()
            if not month or not value or value in {"-", "—", "---"}:
                continue
            start, end = _parse_date_range(f"{value} {year}" if not re.search(r"20\d{2}", value) else value)
            windows.append(RBAMeetingWindow(start_local=start, end_local=end))

    if not windows:
        raise AdapterError("RBA board schedule contained no Monetary Policy Board meeting windows")
    keys = [(window.start_local, window.end_local) for window in windows]
    if len(keys) != len(set(keys)):
        raise AdapterError("RBA board schedule contained duplicate Monetary Policy Board windows")
    return tuple(sorted(windows, key=lambda window: window.start_local))


def validate_rba_calendar_alignment(
    calendar: RBAMonetaryPolicyCalendar,
    board_windows: tuple[RBAMeetingWindow, ...],
) -> None:
    calendar_windows = {
        (event.start_local, event.end_local)
        for event in calendar.events
        if event.event_kind == "MEETING_WINDOW"
    }
    official_windows = {(window.start_local, window.end_local) for window in board_windows}
    missing = sorted(calendar_windows - official_windows)
    if missing:
        raise AdapterError(f"RBA topic calendar meeting windows absent from board schedule: {missing}")

    decisions = {
        event.start_local[:10]
        for event in calendar.events
        if event.event_kind == "DECISION_STATEMENT"
    }
    conferences = {
        event.start_local[:10]
        for event in calendar.events
        if event.event_kind == "PRESS_CONFERENCE"
    }
    for event in calendar.events:
        if event.event_kind != "MEETING_WINDOW":
            continue
        if event.end_local not in decisions:
            raise AdapterError(f"RBA meeting ending {event.end_local} lacks a separate decision statement")
        if event.end_local not in conferences:
            raise AdapterError(f"RBA meeting ending {event.end_local} lacks a separate media conference")


def fetch_rba_monetary_policy_calendar(*, timeout: int = 30) -> tuple[RBAMonetaryPolicyCalendar, FetchSnapshot]:
    body, snapshot = fetch_bytes(
        RBA_MPB_CALENDAR_URL,
        timeout=timeout,
        accept="text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
    )
    return parse_rba_monetary_policy_calendar_html(body), snapshot


def fetch_rba_board_schedule(*, timeout: int = 30) -> tuple[tuple[RBAMeetingWindow, ...], FetchSnapshot]:
    body, snapshot = fetch_bytes(
        RBA_BOARD_SCHEDULE_URL,
        timeout=timeout,
        accept="text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
    )
    return parse_rba_board_schedule_html(body), snapshot
