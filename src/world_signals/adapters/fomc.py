from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from hashlib import sha256
from html.parser import HTMLParser
import json
import re
from typing import Iterable

from .base import AdapterError, FetchSnapshot, fetch_bytes

FOMC_MEETING_CALENDAR_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
FOMC_OPERATIONAL_CALENDAR_TEMPLATE = "https://www.federalreserve.gov/newsevents/{year}-{month}.htm"
FOMC_TIMEZONE = "America/New_York"
FOMC_ACCEPT = "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1"

FOMC_SERIES_BY_KIND = {
    "MEETING_WINDOW": "WS.CB.FED.FOMC_MEETING_WINDOW",
    "DECISION": "WS.CB.FED.FOMC_POLICY_DECISION",
    "PRESS_CONFERENCE": "WS.CB.FED.FOMC_PRESS_CONFERENCE",
    "MINUTES": "WS.CB.FED.FOMC_MINUTES",
}

_MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Sept": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}
_MONTH_NAME = "January|February|March|April|May|June|July|August|September|October|November|December"
_TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})\s*([ap])\.m\.$", re.I)
_DAY_RE = re.compile(r"^\d{1,2}$")
_YEAR_HEADING_RE = re.compile(r"^(20\d{2})\s+FOMC Meetings$")
_RANGE_RE = re.compile(r"^(\d{1,2})\s*[-–]\s*(\d{1,2})(\*)?$")


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


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tokens: list[str] = []
        self._suppressed_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() in {"script", "style", "noscript"}:
            self._suppressed_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"} and self._suppressed_depth:
            self._suppressed_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._suppressed_depth:
            return
        value = _norm(data)
        if value:
            self.tokens.append(value)


def _tokens(body: bytes | str) -> list[str]:
    text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body
    parser = _VisibleTextParser()
    try:
        parser.feed(text)
    except Exception as exc:
        raise AdapterError(f"unable to parse Federal Reserve HTML: {exc}") from exc
    if not parser.tokens:
        raise AdapterError("Federal Reserve HTML produced no visible text")
    return parser.tokens


def _month_number(label: str) -> int:
    try:
        return _MONTHS[label]
    except KeyError as exc:
        raise AdapterError(f"unrecognised FOMC month label: {label!r}") from exc


def _parse_clock(value: str) -> str:
    clean = _norm(value)
    match = _TIME_RE.fullmatch(clean)
    if not match:
        raise AdapterError(f"unrecognised FOMC local clock: {value!r}")
    hour = int(match.group(1))
    minute = int(match.group(2))
    meridiem = match.group(3).lower()
    if not 1 <= hour <= 12 or not 0 <= minute <= 59:
        raise AdapterError(f"invalid FOMC local clock: {value!r}")
    hour = hour % 12 + (12 if meridiem == "p" else 0)
    return f"{hour:02d}:{minute:02d}:00"


def _nearest_preceding_time(tokens: list[str], index: int, *, max_back: int = 4) -> str:
    for candidate in reversed(tokens[max(0, index - max_back) : index]):
        if _TIME_RE.fullmatch(candidate):
            return _parse_clock(candidate)
    raise AdapterError(f"FOMC event at token {index} lacks an unambiguous preceding time")


def _next_day(tokens: list[str], index: int, *, max_forward: int = 5) -> int:
    values = []
    for candidate in tokens[index + 1 : index + 1 + max_forward]:
        if _DAY_RE.fullmatch(candidate):
            values.append(int(candidate))
            break
    if len(values) != 1:
        raise AdapterError(f"FOMC event at token {index} lacks an unambiguous release day")
    return values[0]


def _iso_day(year: int, month: int, day: int) -> str:
    try:
        return date(year, month, day).isoformat()
    except ValueError as exc:
        raise AdapterError(f"invalid FOMC civil date: {year}-{month:02d}-{day:02d}") from exc


@dataclass(frozen=True)
class FOMCMeetingWindow:
    year: int
    month_label: str
    start_date: str
    end_date: str
    sep_associated: bool
    source_timezone: str = FOMC_TIMEZONE
    time_precision: str = "DATE_RANGE"

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class FOMCMeetingCalendar:
    windows: tuple[FOMCMeetingWindow, ...]
    minutes_release_rule: str | None
    future_dates_tentative_note_present: bool

    def normalized_payload(self) -> dict:
        return {
            "windows": [row.as_dict() for row in self.windows],
            "minutes_release_rule": self.minutes_release_rule,
            "future_dates_tentative_note_present": self.future_dates_tentative_note_present,
        }

    @property
    def schedule_sha256(self) -> str:
        return _stable_hash(self.normalized_payload())

    def as_dict(self) -> dict:
        payload = self.normalized_payload()
        payload["schedule_sha256"] = self.schedule_sha256
        return payload


@dataclass(frozen=True)
class FOMCOperationalEvent:
    event_kind: str
    canonical_series_id: str
    start_local: str
    source_timezone: str
    time_precision: str
    related_meeting_start_date: str | None = None
    related_meeting_end_date: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class FOMCOperationalCalendar:
    year: int
    month: int
    events: tuple[FOMCOperationalEvent, ...]

    def normalized_payload(self) -> dict:
        return {
            "year": self.year,
            "month": self.month,
            "events": [event.as_dict() for event in self.events],
        }

    @property
    def schedule_sha256(self) -> str:
        return _stable_hash(self.normalized_payload())

    def as_dict(self) -> dict:
        payload = self.normalized_payload()
        payload["schedule_sha256"] = self.schedule_sha256
        return payload


def _meeting_dates(year: int, month_label: str, range_token: str) -> tuple[str, str, bool]:
    match = _RANGE_RE.fullmatch(range_token)
    if not match:
        raise AdapterError(f"unrecognised FOMC meeting range: {range_token!r}")
    start_day = int(match.group(1))
    end_day = int(match.group(2))
    sep = bool(match.group(3))
    labels = month_label.split("/")
    if len(labels) == 1:
        month = _month_number(labels[0])
        if end_day < start_day:
            raise AdapterError(f"cross-month FOMC range lacks a two-month label: {month_label} {range_token}")
        return _iso_day(year, month, start_day), _iso_day(year, month, end_day), sep
    if len(labels) != 2:
        raise AdapterError(f"invalid FOMC month range label: {month_label!r}")
    start_month = _month_number(labels[0])
    end_month = _month_number(labels[1])
    end_year = year + (1 if end_month < start_month else 0)
    return _iso_day(year, start_month, start_day), _iso_day(end_year, end_month, end_day), sep


def parse_fomc_meeting_calendar_html(
    body: bytes | str,
    *,
    years: Iterable[int] | None = None,
) -> FOMCMeetingCalendar:
    tokens = _tokens(body)
    requested = set(int(y) for y in years) if years is not None else None
    current_year: int | None = None
    windows: list[FOMCMeetingWindow] = []
    seen: set[tuple[str, str]] = set()
    found_years: set[int] = set()

    for idx, token in enumerate(tokens):
        heading = _YEAR_HEADING_RE.fullmatch(token)
        if heading:
            current_year = int(heading.group(1))
            found_years.add(current_year)
            continue
        if current_year is None or (requested is not None and current_year not in requested):
            continue
        if token not in _MONTHS and "/" not in token:
            continue
        if "/" in token and not all(part in _MONTHS for part in token.split("/")):
            continue
        if idx + 1 >= len(tokens) or not _RANGE_RE.fullmatch(tokens[idx + 1]):
            continue
        start, end, sep = _meeting_dates(current_year, token, tokens[idx + 1])
        identity = (start, end)
        if identity in seen:
            raise AdapterError(f"duplicate FOMC meeting window: {identity}")
        seen.add(identity)
        windows.append(
            FOMCMeetingWindow(
                year=current_year,
                month_label=token,
                start_date=start,
                end_date=end,
                sep_associated=sep,
            )
        )

    if requested is not None:
        missing = requested - found_years
        if missing:
            raise AdapterError(f"requested FOMC calendar year heading(s) absent: {sorted(missing)}")
        for year in requested:
            if not any(row.year == year for row in windows):
                raise AdapterError(f"requested FOMC calendar year has no parsed meeting windows: {year}")
    if not windows:
        raise AdapterError("no FOMC meeting windows found")

    minute_rule = next(
        (token for token in tokens if "minutes of regularly scheduled meetings are released three weeks" in token.lower()),
        None,
    )
    tentative = any(
        "each meeting date is tentative until confirmed" in token.lower() for token in tokens
    )
    windows.sort(key=lambda row: (row.start_date, row.end_date))
    return FOMCMeetingCalendar(tuple(windows), minute_rule, tentative)


def _calendar_heading(tokens: list[str]) -> tuple[int, int]:
    pattern = re.compile(rf"^({_MONTH_NAME})\s+(20\d{{2}})$")
    matches = []
    for token in tokens:
        match = pattern.fullmatch(token)
        if match:
            matches.append((int(match.group(2)), _month_number(match.group(1))))
    unique = list(dict.fromkeys(matches))
    if len(unique) != 1:
        raise AdapterError(f"expected one operational calendar month heading, found {unique}")
    return unique[0]


def _fomc_section(tokens: list[str]) -> list[str]:
    starts = [i for i, token in enumerate(tokens) if token == "FOMC Meetings"]
    if len(starts) != 1:
        raise AdapterError(f"expected one FOMC Meetings section, found {len(starts)}")
    start = starts[0] + 1
    stop_labels = {"Beige Book", "Statistical Releases", "Other"}
    stop = next((i for i in range(start, len(tokens)) if tokens[i] in stop_labels), len(tokens))
    section = tokens[start:stop]
    if not section:
        raise AdapterError("empty FOMC Meetings section")
    return section


def _parse_two_day_description(value: str, year: int) -> tuple[str, str]:
    clean = _norm(value)
    match = re.fullmatch(
        rf"Two-day meeting,\s*({_MONTH_NAME})\s+(\d{{1,2}})\s*-\s*(\d{{1,2}})",
        clean,
        re.I,
    )
    if not match:
        raise AdapterError(f"unrecognised FOMC two-day meeting description: {value!r}")
    month = _month_number(match.group(1).title())
    start_day = int(match.group(2))
    end_day = int(match.group(3))
    if end_day < start_day:
        raise AdapterError("operational FOMC two-day description unexpectedly crosses months")
    return _iso_day(year, month, start_day), _iso_day(year, month, end_day)


def _parse_minutes_meeting_description(value: str, calendar_year: int) -> tuple[str | None, str]:
    clean = _norm(value)
    match = re.fullmatch(
        rf"Meeting of\s+({_MONTH_NAME})\s+(\d{{1,2}})\s*-\s*(\d{{1,2}})",
        clean,
        re.I,
    )
    if not match:
        raise AdapterError(f"unrecognised FOMC minutes meeting description: {value!r}")
    month = _month_number(match.group(1).title())
    start_day = int(match.group(2))
    end_day = int(match.group(3))
    year = calendar_year
    # January minutes may describe a December meeting from the prior year.
    if month == 12 and calendar_year == 1:
        year -= 1
    start = _iso_day(year, month, start_day)
    end = _iso_day(year, month, end_day)
    return start, end


def parse_fomc_operational_calendar_html(body: bytes | str) -> FOMCOperationalCalendar:
    tokens = _tokens(body)
    year, month = _calendar_heading(tokens)
    section = _fomc_section(tokens)
    events: list[FOMCOperationalEvent] = []

    decision_indexes = [i for i, token in enumerate(section) if token == "FOMC Meeting"]
    if len(decision_indexes) > 1:
        raise AdapterError("multiple FOMC Meeting decision rows in one monthly calendar")
    for idx in decision_indexes:
        clock = _nearest_preceding_time(section, idx)
        descriptions = [
            token for token in section[idx + 1 : idx + 4] if token.lower().startswith("two-day meeting,")
        ]
        if len(descriptions) != 1:
            raise AdapterError("FOMC Meeting row lacks one two-day meeting description")
        meeting_start, meeting_end = _parse_two_day_description(descriptions[0], year)
        events.append(
            FOMCOperationalEvent(
                event_kind="DECISION",
                canonical_series_id=FOMC_SERIES_BY_KIND["DECISION"],
                start_local=f"{meeting_end}T{clock}",
                source_timezone=FOMC_TIMEZONE,
                time_precision="MINUTE",
                related_meeting_start_date=meeting_start,
                related_meeting_end_date=meeting_end,
            )
        )

    press_indexes = [i for i, token in enumerate(section) if token == "FOMC Press Conference"]
    if len(press_indexes) > 1:
        raise AdapterError("multiple FOMC Press Conference rows in one monthly calendar")
    for idx in press_indexes:
        clock = _nearest_preceding_time(section, idx)
        day = _next_day(section, idx)
        event_date = _iso_day(year, month, day)
        events.append(
            FOMCOperationalEvent(
                event_kind="PRESS_CONFERENCE",
                canonical_series_id=FOMC_SERIES_BY_KIND["PRESS_CONFERENCE"],
                start_local=f"{event_date}T{clock}",
                source_timezone=FOMC_TIMEZONE,
                time_precision="MINUTE",
                related_meeting_end_date=event_date,
            )
        )

    minute_indexes = [i for i, token in enumerate(section) if token == "FOMC Minutes"]
    if len(minute_indexes) > 1:
        raise AdapterError("multiple FOMC Minutes rows in one monthly calendar")
    for idx in minute_indexes:
        clock = _nearest_preceding_time(section, idx)
        descriptions = [
            token for token in section[idx + 1 : idx + 4] if token.lower().startswith("meeting of ")
        ]
        if len(descriptions) != 1:
            raise AdapterError("FOMC Minutes row lacks one source meeting description")
        related_start, related_end = _parse_minutes_meeting_description(descriptions[0], year)
        day = _next_day(section, idx)
        event_date = _iso_day(year, month, day)
        events.append(
            FOMCOperationalEvent(
                event_kind="MINUTES",
                canonical_series_id=FOMC_SERIES_BY_KIND["MINUTES"],
                start_local=f"{event_date}T{clock}",
                source_timezone=FOMC_TIMEZONE,
                time_precision="MINUTE",
                related_meeting_start_date=related_start,
                related_meeting_end_date=related_end,
            )
        )

    identities = [(row.event_kind, row.start_local) for row in events]
    if len(identities) != len(set(identities)):
        raise AdapterError("duplicate FOMC operational event identity")
    if not events:
        raise AdapterError("FOMC Meetings section contains no governed operational events")
    events.sort(key=lambda row: (row.start_local, row.event_kind))
    return FOMCOperationalCalendar(year, month, tuple(events))


def validate_fomc_schedule_alignment(
    meeting_calendar: FOMCMeetingCalendar,
    operational_calendars: Iterable[FOMCOperationalCalendar],
) -> None:
    windows = {(row.start_date, row.end_date) for row in meeting_calendar.windows}
    end_dates = {row.end_date for row in meeting_calendar.windows}
    for calendar in operational_calendars:
        decisions = [row for row in calendar.events if row.event_kind == "DECISION"]
        presses = [row for row in calendar.events if row.event_kind == "PRESS_CONFERENCE"]
        minutes = [row for row in calendar.events if row.event_kind == "MINUTES"]
        if decisions:
            if len(decisions) != 1 or len(presses) != 1:
                raise AdapterError("FOMC decision month must expose one separate press conference")
            decision = decisions[0]
            press = presses[0]
            relation = (decision.related_meeting_start_date, decision.related_meeting_end_date)
            if relation not in windows:
                raise AdapterError(f"operational FOMC meeting window not found in meeting calendar: {relation}")
            if press.related_meeting_end_date != decision.related_meeting_end_date:
                raise AdapterError("FOMC press conference date does not align with decision meeting end date")
            if press.start_local == decision.start_local:
                raise AdapterError("FOMC decision and press conference were collapsed to one timestamp")
        elif presses:
            raise AdapterError("FOMC press conference appears without its decision row")
        for minute in minutes:
            if minute.related_meeting_end_date not in end_dates:
                raise AdapterError(
                    f"FOMC minutes reference an unknown meeting end date: {minute.related_meeting_end_date}"
                )


def fomc_operational_calendar_url(year: int, month: int) -> str:
    if not 1 <= int(month) <= 12:
        raise AdapterError(f"invalid FOMC calendar month: {month}")
    month_name = datetime(2000, int(month), 1).strftime("%B").lower()
    return FOMC_OPERATIONAL_CALENDAR_TEMPLATE.format(year=int(year), month=month_name)


def fetch_fomc_meeting_calendar(
    *,
    timeout: int = 30,
    years: Iterable[int] | None = None,
) -> tuple[FOMCMeetingCalendar, FetchSnapshot]:
    body, snap = fetch_bytes(FOMC_MEETING_CALENDAR_URL, timeout=timeout, accept=FOMC_ACCEPT)
    if snap.status != 200:
        raise AdapterError(f"unexpected FOMC meeting calendar status: {snap.status}")
    return parse_fomc_meeting_calendar_html(body, years=years), snap


def fetch_fomc_operational_calendar(
    year: int,
    month: int,
    *,
    timeout: int = 30,
) -> tuple[FOMCOperationalCalendar, FetchSnapshot]:
    url = fomc_operational_calendar_url(year, month)
    body, snap = fetch_bytes(url, timeout=timeout, accept=FOMC_ACCEPT)
    if snap.status != 200:
        raise AdapterError(f"unexpected FOMC operational calendar status: {snap.status}")
    calendar = parse_fomc_operational_calendar_html(body)
    if (calendar.year, calendar.month) != (int(year), int(month)):
        raise AdapterError(
            f"FOMC operational calendar identity mismatch: requested {(year, month)} got {(calendar.year, calendar.month)}"
        )
    return calendar, snap
