from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from html.parser import HTMLParser
import json
import re

from .base import AdapterError, FetchSnapshot, fetch_bytes

EIA_WPSR_SCHEDULE_URL = "https://www.eia.gov/petroleum/supply/weekly/schedule.php"
EIA_WPSR_TIMEZONE = "America/New_York"


class _ScheduleHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.text_parts: list[str] = []
        self.rows: list[list[str]] = []
        self._in_tr = False
        self._in_cell = False
        self._cell_parts: list[str] = []
        self._row: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() == "tr":
            self._in_tr = True
            self._row = []
        elif self._in_tr and tag.lower() in {"td", "th"}:
            self._in_cell = True
            self._cell_parts = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._in_tr and self._in_cell and tag in {"td", "th"}:
            value = " ".join(" ".join(self._cell_parts).split())
            self._row.append(value)
            self._in_cell = False
            self._cell_parts = []
        elif tag == "tr" and self._in_tr:
            if self._row:
                self.rows.append(self._row)
            self._in_tr = False
            self._row = []

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


def _parse_date(value: str) -> str:
    clean = " ".join(value.replace("Sept.", "Sep.").split())
    for fmt in ("%B %d, %Y", "%b. %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(clean, fmt).date().isoformat()
        except ValueError:
            continue
    raise AdapterError(f"unrecognised EIA WPSR schedule date: {value!r}")


def _parse_time(value: str) -> str:
    clean = " ".join(value.lower().replace(".", "").split())
    for fmt in ("%I:%M %p", "%I %p"):
        try:
            return datetime.strptime(clean, fmt).strftime("%H:%M")
        except ValueError:
            continue
    raise AdapterError(f"unrecognised EIA WPSR schedule time: {value!r}")


@dataclass(frozen=True)
class EIAWPSRSchedule:
    standard_release_day: str
    standard_release_time_local: str
    standard_time_semantics: str
    source_timezone: str
    holiday_exceptions: tuple[dict[str, str], ...]

    def normalized_payload(self) -> dict:
        return {
            "standard_release_day": self.standard_release_day,
            "standard_release_time_local": self.standard_release_time_local,
            "standard_time_semantics": self.standard_time_semantics,
            "source_timezone": self.source_timezone,
            "holiday_exceptions": [dict(row) for row in self.holiday_exceptions],
        }

    @property
    def schedule_sha256(self) -> str:
        return _stable_hash(self.normalized_payload())

    def as_dict(self) -> dict:
        payload = self.normalized_payload()
        payload["schedule_sha256"] = self.schedule_sha256
        return payload


def parse_eia_wpsr_schedule_html(body: bytes) -> EIAWPSRSchedule:
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        text = body.decode("utf-8", errors="replace")

    parser = _ScheduleHTMLParser()
    try:
        parser.feed(text)
    except Exception as exc:  # HTMLParser can surface malformed entity/state errors.
        raise AdapterError(f"unable to parse EIA WPSR schedule HTML: {exc}") from exc

    visible = " ".join(parser.text_parts)
    standard = re.search(
        r"released\s+to\s+the\s+web\s+site\s+after\s+"
        r"(\d{1,2}(?::\d{2})?)\s*([ap]\.?m\.?)\s+eastern\s+time\s+on\s+([A-Za-z]+)",
        visible,
        flags=re.IGNORECASE,
    )
    if not standard:
        raise AdapterError("EIA WPSR standard release rule not found")

    standard_time = _parse_time(f"{standard.group(1)} {standard.group(2)}")
    standard_day = standard.group(3).capitalize()

    exceptions: list[dict[str, str]] = []
    for row in parser.rows:
        if len(row) < 5:
            continue
        try:
            week_ending = _parse_date(row[0])
            alternate_release_date = _parse_date(row[1])
            release_time = _parse_time(row[3])
        except AdapterError:
            continue
        release_day = " ".join(row[2].split()).capitalize()
        holiday = " ".join(row[4].split())
        if not release_day or not holiday:
            continue
        exceptions.append({
            "week_ending": week_ending,
            "alternate_release_date": alternate_release_date,
            "release_day": release_day,
            "release_time_local": release_time,
            "holiday": holiday,
        })

    if not exceptions:
        raise AdapterError("EIA WPSR holiday exception table not found")

    exceptions.sort(key=lambda row: (row["week_ending"], row["alternate_release_date"]))
    return EIAWPSRSchedule(
        standard_release_day=standard_day,
        standard_release_time_local=standard_time,
        standard_time_semantics="AFTER",
        source_timezone=EIA_WPSR_TIMEZONE,
        holiday_exceptions=tuple(exceptions),
    )


def fetch_eia_wpsr_schedule() -> tuple[EIAWPSRSchedule, FetchSnapshot]:
    body, snap = fetch_bytes(EIA_WPSR_SCHEDULE_URL, accept="text/html,application/xhtml+xml")
    return parse_eia_wpsr_schedule_html(body), snap
