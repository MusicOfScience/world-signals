from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from hashlib import sha256
from html.parser import HTMLParser
import json
import re

from .base import AdapterError, FetchSnapshot, fetch_bytes

JAPAN_MOF_JGB_CALENDAR_INDEX = "https://www.mof.go.jp/english/policy/jgbs/auction/calendar/index.htm"
JAPAN_MOF_TIMEZONE = "Asia/Tokyo"

_MONTHS = {
    name: number
    for number, name in enumerate(
        (
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ),
        start=1,
    )
}


class _CalendarHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.text_parts: list[str] = []
        self.tables: list[list[list[str]]] = []
        self._table_depth = 0
        self._current_table: list[list[str]] | None = None
        self._in_row = False
        self._row: list[str] = []
        self._in_cell = False
        self._cell_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag == "table":
            self._table_depth += 1
            if self._table_depth == 1:
                self._current_table = []
        elif self._table_depth == 1 and tag == "tr":
            self._in_row = True
            self._row = []
        elif self._table_depth == 1 and self._in_row and tag in {"td", "th"}:
            self._in_cell = True
            self._cell_parts = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._table_depth == 1 and self._in_row and self._in_cell and tag in {"td", "th"}:
            value = " ".join(" ".join(self._cell_parts).split())
            self._row.append(value)
            self._in_cell = False
            self._cell_parts = []
        elif self._table_depth == 1 and self._in_row and tag == "tr":
            if self._row and self._current_table is not None:
                self._current_table.append(self._row)
            self._in_row = False
            self._row = []
        elif tag == "table" and self._table_depth:
            if self._table_depth == 1 and self._current_table is not None:
                self.tables.append(self._current_table)
                self._current_table = None
            self._table_depth -= 1

    def handle_data(self, data: str) -> None:
        value = " ".join(data.split())
        if not value:
            return
        self.text_parts.append(value)
        if self._in_cell:
            self._cell_parts.append(value)


def _stable_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def jgb_monthly_calendar_url(year: int, month: int) -> str:
    if year < 2000 or year > 2099:
        raise ValueError("JGB monthly calendar URL only supports 2000-2099")
    if month < 1 or month > 12:
        raise ValueError("month must be in 1..12")
    return f"https://www.mof.go.jp/english/policy/jgbs/auction/calendar/{year % 100:02d}{month:02d}e.htm"


def _parse_heading_month(visible: str) -> tuple[int, int]:
    match = re.search(
        r"Auction\s+Calendar\s+(" + "|".join(_MONTHS) + r")\s+(\d{4})",
        visible,
        flags=re.IGNORECASE,
    )
    if not match:
        raise AdapterError("Japan MOF monthly auction calendar heading not found")
    month_name = match.group(1).capitalize()
    return int(match.group(2)), _MONTHS[month_name]


def _parse_auction_date(value: str) -> str:
    clean = " ".join(value.replace("Sept.", "Sep.").split())
    for fmt in ("%b. %d, %Y", "%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(clean, fmt).date().isoformat()
        except ValueError:
            continue
    raise AdapterError(f"unrecognised Japan MOF auction date: {value!r}")


@dataclass(frozen=True)
class JGBAuctionEntry:
    auction_date: str
    issue: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class JGBMonthlyAuctionCalendar:
    year: int
    month: int
    source_timezone: str
    time_precision: str
    entries: tuple[JGBAuctionEntry, ...]

    def normalized_payload(self) -> dict:
        return {
            "year": self.year,
            "month": self.month,
            "source_timezone": self.source_timezone,
            "time_precision": self.time_precision,
            "entries": [entry.as_dict() for entry in self.entries],
        }

    @property
    def schedule_sha256(self) -> str:
        return _stable_hash(self.normalized_payload())

    def as_dict(self) -> dict:
        payload = self.normalized_payload()
        payload["schedule_sha256"] = self.schedule_sha256
        return payload


def parse_jgb_monthly_auction_calendar_html(body: bytes | str) -> JGBMonthlyAuctionCalendar:
    text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body

    parser = _CalendarHTMLParser()
    try:
        parser.feed(text)
    except Exception as exc:
        raise AdapterError(f"unable to parse Japan MOF auction calendar HTML: {exc}") from exc

    visible = " ".join(parser.text_parts)
    year, month = _parse_heading_month(visible)

    target_table: list[list[str]] | None = None
    for table in parser.tables:
        if not table:
            continue
        header = " | ".join(cell.lower() for cell in table[0])
        if "auction date" in header and "issue" in header and "auction result" in header:
            target_table = table
            break
    if target_table is None:
        raise AdapterError("Japan MOF government-bond auction table not found")

    entries: list[JGBAuctionEntry] = []
    seen: set[tuple[str, str]] = set()
    for row in target_table[1:]:
        if len(row) < 2 or not row[0].strip() or not row[1].strip():
            continue
        try:
            auction_date = _parse_auction_date(row[0])
        except AdapterError:
            continue
        parsed = datetime.fromisoformat(auction_date).date()
        if parsed.year != year or parsed.month != month:
            raise AdapterError(
                f"Japan MOF auction row {auction_date} falls outside heading month {year:04d}-{month:02d}"
            )
        issue = " ".join(row[1].split())
        key = (auction_date, issue)
        if key in seen:
            raise AdapterError(f"duplicate Japan MOF auction row: {auction_date} / {issue}")
        seen.add(key)
        entries.append(JGBAuctionEntry(auction_date=auction_date, issue=issue))

    if not entries:
        raise AdapterError("Japan MOF monthly auction calendar contained no auction rows")
    entries.sort(key=lambda entry: (entry.auction_date, entry.issue))
    return JGBMonthlyAuctionCalendar(
        year=year,
        month=month,
        source_timezone=JAPAN_MOF_TIMEZONE,
        time_precision="CIVIL_DATE",
        entries=tuple(entries),
    )


def fetch_jgb_monthly_auction_calendar(
    year: int,
    month: int,
    *,
    timeout: int = 30,
) -> tuple[JGBMonthlyAuctionCalendar, FetchSnapshot]:
    url = jgb_monthly_calendar_url(year, month)
    body, snapshot = fetch_bytes(
        url,
        timeout=timeout,
        accept="text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
    )
    return parse_jgb_monthly_auction_calendar_html(body), snapshot
