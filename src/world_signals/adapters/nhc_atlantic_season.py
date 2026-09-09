from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from html.parser import HTMLParser
import json
import re
from xml.etree import ElementTree

from .base import AdapterError, FetchSnapshot, fetch_bytes


NHC_CLIMATOLOGY_URL = "https://www.nhc.noaa.gov/climo/"
NHC_RSS_DIRECTORY_URL = "https://www.nhc.noaa.gov/mobile/rss.html"
NHC_ATLANTIC_OUTLOOK_RSS_URL = "https://www.nhc.noaa.gov/xml/TWOAT.xml"
NHC_ATLANTIC_BASIN_RSS_URL = "https://www.nhc.noaa.gov/index-at.xml"
NHC_ROBOTS_URL = "https://www.nhc.noaa.gov/robots.txt"
NHC_RIGHTS_URL = "https://www.weather.gov/disclaimer/"


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        value = " ".join(data.replace("\xa0", " ").split())
        if value:
            self.parts.append(value)


def _text(body: bytes | str) -> str:
    raw = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body
    parser = _TextParser()
    try:
        parser.feed(raw)
    except Exception as exc:
        raise AdapterError(f"unable to parse NHC climatology HTML: {exc}") from exc
    return " ".join(" ".join(parser.parts).split())


def _semantic_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(raw.encode("utf-8")).hexdigest()


def _month_day(value: str) -> str:
    match = re.fullmatch(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})", value, re.I)
    if not match:
        raise AdapterError(f"unrecognised NHC month/day: {value!r}")
    months = {
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    }
    month = months[match.group(1).lower()]
    day = int(match.group(2))
    if not 1 <= day <= 31:
        raise AdapterError(f"invalid NHC day: {value!r}")
    return f"{month:02d}-{day:02d}"


@dataclass(frozen=True)
class NHCAtlanticSeasonDefinition:
    start_month_day: str
    end_month_day: str
    semantic_sha256: str
    authority_surface: str = "NHC_TROPICAL_CYCLONE_CLIMATOLOGY"

    def as_dict(self) -> dict:
        return asdict(self)


def parse_nhc_atlantic_climatology_html(body: bytes | str) -> NHCAtlanticSeasonDefinition:
    text = _text(body)
    month = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    patterns = [
        rf"Atlantic hurricane season runs from ({month}\s+\d{{1,2}}) to ({month}\s+\d{{1,2}})",
        rf"official hurricane season for the Atlantic basin is from ({month}\s+\d{{1,2}}) to ({month}\s+\d{{1,2}})",
    ]
    definitions: set[tuple[str, str]] = set()
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.I):
            definitions.add((_month_day(match.group(1)), _month_day(match.group(2))))
    if not definitions:
        raise AdapterError("NHC climatology did not expose an explicit Atlantic hurricane season boundary")
    if len(definitions) != 1:
        raise AdapterError(f"NHC climatology exposed conflicting Atlantic season definitions: {sorted(definitions)}")
    start, end = next(iter(definitions))
    payload = {"start_month_day": start, "end_month_day": end, "authority_surface": "NHC_TROPICAL_CYCLONE_CLIMATOLOGY"}
    return NHCAtlanticSeasonDefinition(start, end, _semantic_hash(payload))


def validate_nhc_rss_xml(body: bytes | str) -> None:
    raw = body if isinstance(body, bytes) else body.encode("utf-8")
    try:
        root = ElementTree.fromstring(raw)
    except ElementTree.ParseError as exc:
        raise AdapterError(f"invalid NHC RSS/XML payload: {exc}") from exc
    if root.tag.lower().split("}")[-1] not in {"rss", "feed"}:
        raise AdapterError(f"unexpected NHC feed root element: {root.tag}")


def fetch_nhc_atlantic_climatology(*, timeout: int = 30) -> tuple[NHCAtlanticSeasonDefinition, FetchSnapshot]:
    body, snapshot = fetch_bytes(
        NHC_CLIMATOLOGY_URL,
        timeout=timeout,
        accept="text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
    )
    return parse_nhc_atlantic_climatology_html(body), snapshot


def fetch_nhc_atlantic_outlook_health(*, timeout: int = 30) -> FetchSnapshot:
    body, snapshot = fetch_bytes(
        NHC_ATLANTIC_OUTLOOK_RSS_URL,
        timeout=timeout,
        accept="application/rss+xml,application/xml,text/xml;q=0.9,*/*;q=0.1",
    )
    validate_nhc_rss_xml(body)
    return snapshot
