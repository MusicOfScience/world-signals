from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
from html.parser import HTMLParser
import json
import re

from .base import AdapterError, FetchSnapshot, fetch_bytes

CBN_MPC_CALENDAR_URL = "https://www.cbn.gov.ng/MonetaryPolicy/calendar.html"
CBN_MPC_TIMEZONE = "Africa/Lagos"
CBN_MPC_ACCEPT = "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1"


def _norm(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").replace("\u202f", " ").split())


def _stable_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def _parse_cbn_date(value: str) -> str:
    clean = _norm(value).replace("Sept.", "Sep.")
    clean = re.sub(r"\b([A-Za-z]{3})\.", r"\1", clean)
    for fmt in ("%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(clean, fmt).date().isoformat()
        except ValueError:
            pass
    raise AdapterError(f"unrecognised CBN MPC civil date: {value!r}")


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._in_row = False
        self._row: list[str] = []
        self._in_cell = False
        self._cell_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag == "tr":
            self._in_row = True
            self._row = []
        elif self._in_row and tag in {"td", "th"}:
            self._in_cell = True
            self._cell_parts = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._in_cell and tag in {"td", "th"}:
            self._row.append(_norm(" ".join(self._cell_parts)))
            self._in_cell = False
            self._cell_parts = []
        elif self._in_row and tag == "tr":
            if self._row:
                self.rows.append(self._row)
            self._in_row = False
            self._row = []

    def handle_data(self, data: str) -> None:
        value = _norm(data)
        if self._in_cell and value:
            self._cell_parts.append(value)


@dataclass(frozen=True)
class CBNMPCMeeting:
    meeting_number: int
    start_local: str
    end_local: str
    source_timezone: str = CBN_MPC_TIMEZONE
    time_precision: str = "DAY_RANGE"

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class CBNMPCCalendar:
    meetings: tuple[CBNMPCMeeting, ...]

    def normalized_payload(self) -> dict:
        return {"meetings": [row.as_dict() for row in self.meetings]}

    @property
    def schedule_sha256(self) -> str:
        return _stable_hash(self.normalized_payload())

    def as_dict(self) -> dict:
        out = self.normalized_payload()
        out["schedule_sha256"] = self.schedule_sha256
        return out


def parse_cbn_mpc_calendar_html(body: bytes | str) -> CBNMPCCalendar:
    text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body
    if not re.search(r"MPC\s+Meeting\s+Calendar\s+for\s+2026", text, re.I):
        raise AdapterError("CBN MPC calendar does not identify the 2026 calendar")

    parser = _TableParser()
    try:
        parser.feed(text)
    except Exception as exc:
        raise AdapterError(f"unable to parse CBN MPC calendar HTML: {exc}") from exc

    meetings: list[CBNMPCMeeting] = []
    for cells in parser.rows:
        if len(cells) < 4:
            continue
        number = cells[1].strip()
        if not re.fullmatch(r"\d{3}", number):
            continue
        try:
            meeting = CBNMPCMeeting(
                meeting_number=int(number),
                start_local=_parse_cbn_date(cells[2]),
                end_local=_parse_cbn_date(cells[3]),
            )
        except AdapterError:
            raise
        if meeting.end_local < meeting.start_local:
            raise AdapterError(f"CBN MPC meeting {number} ends before it starts")
        meetings.append(meeting)

    if not meetings:
        raise AdapterError("CBN MPC calendar contained no numbered meeting rows")
    numbers = [row.meeting_number for row in meetings]
    if len(numbers) != len(set(numbers)):
        raise AdapterError("CBN MPC calendar contained duplicate meeting numbers")
    if numbers != sorted(numbers):
        raise AdapterError("CBN MPC meeting numbers are not monotonically ordered")
    return CBNMPCCalendar(meetings=tuple(meetings))


def fetch_cbn_mpc_calendar(*, timeout: int = 30) -> tuple[CBNMPCCalendar, FetchSnapshot]:
    body, snapshot = fetch_bytes(
        CBN_MPC_CALENDAR_URL,
        timeout=timeout,
        accept=CBN_MPC_ACCEPT,
    )
    if snapshot.status != 200:
        raise AdapterError(f"CBN MPC calendar returned HTTP {snapshot.status}")
    return parse_cbn_mpc_calendar_html(body), snapshot
