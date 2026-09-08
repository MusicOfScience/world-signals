from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from html.parser import HTMLParser
import re
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from .base import AdapterError, FetchSnapshot, USER_AGENT, fetch_bytes

JAPAN_CPI_SCHEDULE_URL = "https://www.stat.go.jp/english/data/cpi/1582.htm"
JAPAN_CPI_ROBOTS_URL = "https://www.stat.go.jp/robots.txt"
JAPAN_CPI_CLOCK_RULE_URL = "https://www.stat.go.jp/english/data/cpi/1585.htm"
JAPAN_CPI_TIMEZONE = "Asia/Tokyo"
JAPAN_CPI_ACCEPT = "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1"
JAPAN_CPI_OFFICIAL_HOST = "www.stat.go.jp"

MONTHS = {
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
}
MONTH_BY_NUMBER = {value: key for key, value in MONTHS.items()}
SURVEY_LABEL_RE = re.compile(
    r"^(January|February|March|April|May|June|July|August|September|October|November|December)(?:,\s*(20\d{2}))?$"
)
RELEASE_LABEL_RE = re.compile(
    r"^(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:,\s*(20\d{2}))?$"
)


@dataclass(frozen=True)
class JapanCPIReleaseRow:
    reference_period: str
    survey_month_label: str
    release_date: str
    source_timezone: str = JAPAN_CPI_TIMEZONE
    time_precision: str = "DAY"
    clock_exposed_by_schedule: bool = False

    def as_dict(self) -> dict:
        return asdict(self)


class _TableRows(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[no-untyped-def]
        tag = tag.lower()
        if tag == "tr":
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"td", "th"} and self._row is not None and self._cell is not None:
            value = " ".join("".join(self._cell).replace("\xa0", " ").split())
            self._row.append(value)
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None
            self._cell = None


def _parse_table_rows(raw_html: str) -> list[list[str]]:
    parser = _TableRows()
    try:
        parser.feed(raw_html)
    except Exception as exc:
        raise AdapterError(f"unable to parse Japan CPI schedule HTML: {exc}") from exc
    return parser.rows


def _reference_period(month_name: str, year: int) -> str:
    return f"{month_name} {year}"


def _parse_release_date(label: str, *, survey_month: int, survey_year: int) -> str:
    match = RELEASE_LABEL_RE.fullmatch(label)
    if match is None:
        raise AdapterError(f"invalid Japan CPI national release-date label: {label!r}")
    month_name, day_raw, explicit_year_raw = match.groups()
    release_month = MONTHS[month_name]
    if explicit_year_raw is not None:
        release_year = int(explicit_year_raw)
        if release_year not in {survey_year, survey_year + 1}:
            raise AdapterError(
                f"Japan CPI release year {release_year} is inconsistent with survey year {survey_year}"
            )
    else:
        release_year = survey_year + (1 if release_month < survey_month else 0)
    try:
        return date(release_year, release_month, int(day_raw)).isoformat()
    except ValueError as exc:
        raise AdapterError(f"invalid Japan CPI release date: {label!r}") from exc


def parse_japan_cpi_schedule(body: bytes | str) -> list[JapanCPIReleaseRow]:
    raw = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body
    lower_head = raw[:5000].lower()
    if "request rejected" in lower_head or "access denied" in lower_head:
        raise AdapterError("Japan CPI schedule returned rejection content")
    if "Schedule of Release" not in raw:
        raise AdapterError("Japan CPI schedule heading not found")

    rows = _parse_table_rows(raw)
    survey_year: int | None = None
    parsed: list[JapanCPIReleaseRow] = []
    seen: set[str] = set()

    for cells in rows:
        if len(cells) < 2:
            continue
        survey_label = cells[0]
        release_label = cells[1]
        survey_match = SURVEY_LABEL_RE.fullmatch(survey_label)
        if survey_match is None:
            continue

        month_name, explicit_year_raw = survey_match.groups()
        if explicit_year_raw is not None:
            survey_year = int(explicit_year_raw)
        elif survey_year is None:
            raise AdapterError(
                f"Japan CPI schedule bare survey month {survey_label!r} appears before a year anchor"
            )

        assert survey_year is not None
        survey_month = MONTHS[month_name]
        reference_period = _reference_period(month_name, survey_year)
        if reference_period in seen:
            raise AdapterError(f"duplicate Japan CPI national survey-period identity: {reference_period}")
        seen.add(reference_period)

        release_date = _parse_release_date(
            release_label,
            survey_month=survey_month,
            survey_year=survey_year,
        )
        parsed.append(
            JapanCPIReleaseRow(
                reference_period=reference_period,
                survey_month_label=survey_label,
                release_date=release_date,
            )
        )

    if not parsed:
        raise AdapterError("Japan CPI schedule contains no national release rows")
    return parsed


def _validate_robots_body(body: bytes | str) -> str:
    text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body
    stripped = text.lstrip()
    if "<html" in stripped[:1000].lower() or "request rejected" in stripped[:2000].lower():
        raise AdapterError("Japan Statistics Bureau robots endpoint returned non-policy content")
    if re.search(r"(?im)^\s*user-agent\s*:", text) is None:
        raise AdapterError("Japan Statistics Bureau robots body lacks User-agent syntax")
    return text


def japan_cpi_schedule_allowed(robots_body: bytes | str) -> bool:
    text = _validate_robots_body(robots_body)
    parser = RobotFileParser()
    try:
        parser.parse(text.splitlines())
    except Exception as exc:
        raise AdapterError(f"unable to parse Japan Statistics Bureau robots policy: {exc}") from exc
    return parser.can_fetch(USER_AGENT, JAPAN_CPI_SCHEDULE_URL)


def fetch_japan_cpi_robots_policy(*, timeout: int = 30) -> tuple[bool, FetchSnapshot]:
    body, snapshot = fetch_bytes(
        JAPAN_CPI_ROBOTS_URL,
        timeout=timeout,
        accept="text/plain,*/*;q=0.1",
    )
    if snapshot.status != 200:
        raise AdapterError(f"Japan Statistics Bureau robots policy returned HTTP {snapshot.status}")
    if "text/plain" not in snapshot.content_type.lower():
        raise AdapterError(
            f"Japan Statistics Bureau robots content-type drift: {snapshot.content_type!r}"
        )
    return japan_cpi_schedule_allowed(body), snapshot


def fetch_japan_cpi_schedule(*, timeout: int = 30) -> tuple[list[JapanCPIReleaseRow], FetchSnapshot]:
    body, snapshot = fetch_bytes(
        JAPAN_CPI_SCHEDULE_URL,
        timeout=timeout,
        accept=JAPAN_CPI_ACCEPT,
        headers={"Accept-Language": "en"},
    )
    if snapshot.status != 200:
        raise AdapterError(f"Japan CPI schedule returned HTTP {snapshot.status}")
    parsed_url = urlparse(snapshot.resolved_url)
    if (
        parsed_url.scheme != "https"
        or parsed_url.hostname != JAPAN_CPI_OFFICIAL_HOST
        or parsed_url.path != "/english/data/cpi/1582.htm"
        or parsed_url.query
        or parsed_url.fragment
    ):
        raise AdapterError(
            f"Japan CPI schedule resolved away from exact registered endpoint: {snapshot.resolved_url!r}"
        )
    if "text/html" not in snapshot.content_type.lower():
        raise AdapterError(f"Japan CPI schedule content-type drift: {snapshot.content_type!r}")
    if snapshot.body_bytes < 10000:
        raise AdapterError(f"Japan CPI schedule body unexpectedly small: {snapshot.body_bytes} bytes")
    return parse_japan_cpi_schedule(body), snapshot
