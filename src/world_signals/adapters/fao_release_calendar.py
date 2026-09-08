from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import html
from html.parser import HTMLParser
import re
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from .base import AdapterError, FetchSnapshot, USER_AGENT, fetch_bytes

FAO_CALENDAR_URL = "https://www.fao.org/statistics/data-releases/upcoming-data-releases/"
FAO_ROBOTS_URL = "https://www.fao.org/robots.txt"
FAO_TIMEZONE = "Europe/Rome"
FAO_ACCEPT = "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1"
FAO_OFFICIAL_HOSTS = {"fao.org", "www.fao.org"}

FAO_PRODUCT_LABELS = {
    "FFPI": "FAO Food Price Index and Commodity Price Indices",
    "AMIS": "AMIS Market Monitor",
}
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
MONTH_HEADING_RE = re.compile(
    r"(?m)(January|February|March|April|May|June|July|August|September|October|November|December)\s+(20\d{2})"
)


@dataclass(frozen=True)
class FAOReleaseSlot:
    product_key: str
    product_label: str
    slot_month: str
    release_date: str
    source_timezone: str = FAO_TIMEZONE
    time_precision: str = "DAY"

    def as_dict(self) -> dict:
        return asdict(self)


class _VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._suppressed = 0

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[no-untyped-def]
        if tag.lower() in {"script", "style", "noscript"}:
            self._suppressed += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"} and self._suppressed:
            self._suppressed -= 1

    def handle_data(self, data: str) -> None:
        if self._suppressed:
            return
        value = re.sub(r"\s+", " ", html.unescape(data).strip())
        if value:
            self.parts.append(value)


def _visible_text(raw_html: str) -> str:
    parser = _VisibleText()
    try:
        parser.feed(raw_html)
    except Exception as exc:
        raise AdapterError(f"unable to parse FAO release-calendar HTML: {exc}") from exc
    return "\n".join(parser.parts)


def _validate_robots_body(body: bytes | str) -> str:
    text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body
    stripped = text.lstrip()
    if "<html" in stripped[:1000].lower() or "request rejected" in stripped[:2000].lower():
        raise AdapterError("FAO robots endpoint returned HTML/rejection content instead of a robots policy")
    if re.search(r"(?im)^\s*user-agent\s*:", text) is None:
        raise AdapterError("FAO robots body lacks User-agent syntax")
    return text


def fao_calendar_allowed(robots_body: bytes | str) -> bool:
    text = _validate_robots_body(robots_body)
    parser = RobotFileParser()
    try:
        parser.parse(text.splitlines())
    except Exception as exc:
        raise AdapterError(f"unable to parse FAO robots policy: {exc}") from exc
    return parser.can_fetch(USER_AGENT, FAO_CALENDAR_URL)


def _section_span(text: str, slot_month: str) -> tuple[int, int]:
    matches = list(MONTH_HEADING_RE.finditer(text))
    target = [m for m in matches if f"{m.group(1)} {m.group(2)}" == slot_month]
    if len(target) != 1:
        raise AdapterError(f"FAO calendar must expose exactly one {slot_month!r} month section; found {len(target)}")
    selected = target[0]
    later = [m.start() for m in matches if m.start() > selected.start()]
    return selected.start(), min(later) if later else len(text)


def parse_fao_release_calendar(
    body: bytes | str,
    *,
    configured_month_sections: list[str],
) -> list[FAOReleaseSlot]:
    if not configured_month_sections or len(configured_month_sections) != len(set(configured_month_sections)):
        raise AdapterError("FAO configured month sections must be non-empty and unique")

    raw = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body
    lower_head = raw[:5000].lower()
    if "request rejected" in lower_head or "access denied" in lower_head:
        raise AdapterError("FAO release calendar returned rejection content")
    text = _visible_text(raw)
    if "2026 Calendar of Data Releases" not in text:
        raise AdapterError("FAO release calendar heading not found")

    releases: list[FAOReleaseSlot] = []
    for slot_month in configured_month_sections:
        month_match = re.fullmatch(
            r"(January|February|March|April|May|June|July|August|September|October|November|December) (20\d{2})",
            slot_month,
        )
        if month_match is None:
            raise AdapterError(f"invalid FAO configured month section: {slot_month!r}")
        slot_month_name, slot_year_raw = month_match.groups()
        start, end = _section_span(text, slot_month)
        section = text[start:end]

        for product_key, label in FAO_PRODUCT_LABELS.items():
            pattern = re.compile(
                re.escape(label)
                + r"\s*\(\s*(\d{1,2})\s+"
                + r"(January|February|March|April|May|June|July|August|September|October|November|December)\s*\)",
                re.IGNORECASE,
            )
            matches = list(pattern.finditer(section))
            if len(matches) > 1:
                raise AdapterError(
                    f"FAO {slot_month} section contains ambiguous duplicate {product_key} rows: {len(matches)}"
                )
            if not matches:
                continue
            day_raw, date_month_raw = matches[0].groups()
            date_month_name = next(name for name in MONTHS if name.lower() == date_month_raw.lower())
            if date_month_name != slot_month_name:
                raise AdapterError(
                    f"FAO {product_key} visible date month {date_month_name} differs from slot month {slot_month_name}; "
                    "cross-month identity requires manual review"
                )
            try:
                observed_date = date(int(slot_year_raw), MONTHS[date_month_name], int(day_raw)).isoformat()
            except ValueError as exc:
                raise AdapterError(f"invalid FAO release date in {slot_month}: {day_raw} {date_month_name}") from exc
            releases.append(
                FAOReleaseSlot(
                    product_key=product_key,
                    product_label=label,
                    slot_month=slot_month,
                    release_date=observed_date,
                )
            )
    return releases


def fetch_fao_robots_policy(*, timeout: int = 30) -> tuple[bool, FetchSnapshot]:
    body, snapshot = fetch_bytes(
        FAO_ROBOTS_URL,
        timeout=timeout,
        accept="text/plain,*/*;q=0.1",
    )
    if snapshot.status != 200:
        raise AdapterError(f"FAO robots policy returned HTTP {snapshot.status}")
    if "text/plain" not in snapshot.content_type.lower():
        raise AdapterError(f"FAO robots endpoint content-type drift: {snapshot.content_type!r}")
    return fao_calendar_allowed(body), snapshot


def fetch_fao_release_calendar(
    configured_month_sections: list[str],
    *,
    timeout: int = 30,
) -> tuple[list[FAOReleaseSlot], FetchSnapshot]:
    body, snapshot = fetch_bytes(
        FAO_CALENDAR_URL,
        timeout=timeout,
        accept=FAO_ACCEPT,
        headers={"Accept-Language": "en"},
    )
    if snapshot.status != 200:
        raise AdapterError(f"FAO release calendar returned HTTP {snapshot.status}")
    parsed = urlparse(snapshot.resolved_url)
    if parsed.scheme != "https" or parsed.hostname not in FAO_OFFICIAL_HOSTS:
        raise AdapterError(f"FAO calendar resolved outside official HTTPS host: {snapshot.resolved_url!r}")
    if "text/html" not in snapshot.content_type.lower():
        raise AdapterError(f"FAO calendar content-type drift: {snapshot.content_type!r}")
    if snapshot.body_bytes < 10000:
        raise AdapterError(f"FAO calendar body unexpectedly small: {snapshot.body_bytes} bytes")
    return parse_fao_release_calendar(body, configured_month_sections=configured_month_sections), snapshot
