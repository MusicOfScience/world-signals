from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import re
from urllib.parse import parse_qs, urlparse
import xml.etree.ElementTree as ET

from .base import AdapterError, FetchSnapshot, fetch_bytes

EUROPEAN_COUNCIL_RSS_DOCS = "https://www.consilium.europa.eu/en/about-site/rss/"
EUROPEAN_COUNCIL_MEETINGS_RSS = "https://www.consilium.europa.eu/en/rss/meetings.ashx?cat=euco"
EUROPEAN_COUNCIL_CANONICAL_CALENDAR = "https://www.consilium.europa.eu/en/meetings/calendar/"
EUROPEAN_COUNCIL_COPYRIGHT = "https://www.consilium.europa.eu/en/about-site/copyright/"
EUROPEAN_COUNCIL_RSS_ACCEPT = "application/rss+xml,application/xml;q=0.9,text/xml;q=0.8,*/*;q=0.1"
EUROPEAN_COUNCIL_OFFICIAL_HOST = "www.consilium.europa.eu"
EUROPEAN_COUNCIL_CHANNEL_TITLE = "Council of the EU"
EUROPEAN_COUNCIL_CHANNEL_LINK = "https://www.consilium.europa.eu/"
EUROPEAN_COUNCIL_CHANNEL_DESCRIPTION = ""
EUROPEAN_COUNCIL_MIN_ITEMS = 1
EUROPEAN_COUNCIL_MAX_ITEMS = 200
EUROPEAN_COUNCIL_ITEM_CHILDREN = ["guid", "link", "title", "description", "updated"]

_MEETING_PATH = re.compile(
    r"^/en/meetings/european-council/(\d{4})/(\d{2})/(\d{2})(?:-(\d{2}))?/$"
)


@dataclass(frozen=True)
class EuropeanCouncilRSSItem:
    guid: str
    link: str
    title: str
    description: str
    updated: str
    start_local: str
    end_local: str | None

    def as_dict(self) -> dict:
        return asdict(self)


def _text(node: ET.Element, tag: str, *, required: bool) -> str:
    child = node.find(tag)
    value = " ".join("".join(child.itertext()).split()) if child is not None else ""
    if required and not value:
        raise AdapterError(f"European Council RSS item missing required field {tag}")
    return value


def parse_european_council_meeting_link(link: str) -> tuple[str, str | None]:
    parsed = urlparse(link.strip())
    if parsed.scheme != "https" or parsed.hostname != EUROPEAN_COUNCIL_OFFICIAL_HOST:
        raise AdapterError(f"European Council RSS item points outside official HTTPS host: {link!r}")
    if parsed.query or parsed.fragment or parsed.params:
        raise AdapterError(f"European Council RSS item link unexpectedly has query/fragment/params: {link!r}")
    match = _MEETING_PATH.fullmatch(parsed.path)
    if match is None:
        raise AdapterError(f"European Council RSS meeting-link path contract drift: {parsed.path!r}")
    year_s, month_s, start_day_s, end_day_s = match.groups()
    year, month, start_day = int(year_s), int(month_s), int(start_day_s)
    try:
        start = date(year, month, start_day)
    except ValueError as exc:
        raise AdapterError(f"European Council RSS invalid start date in link: {link!r}") from exc
    end: date | None = None
    if end_day_s is not None:
        try:
            end = date(year, month, int(end_day_s))
        except ValueError as exc:
            raise AdapterError(f"European Council RSS invalid end date in link: {link!r}") from exc
        if end < start:
            raise AdapterError(f"European Council RSS meeting range runs backwards within encoded month: {link!r}")
        if end == start:
            raise AdapterError(f"European Council RSS redundant same-day range encoding: {link!r}")
    return start.isoformat(), None if end is None else end.isoformat()


def parse_european_council_meetings_rss(body: bytes | str) -> list[EuropeanCouncilRSSItem]:
    raw = body.encode("utf-8") if isinstance(body, str) else body
    head = raw[:3000].decode("utf-8", errors="replace").lower()
    if "<html" in head or "<!doctype" in head or "request rejected" in head or "access denied" in head:
        raise AdapterError("European Council RSS returned non-feed/rejection content")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise AdapterError(f"European Council RSS XML parse failed: {exc}") from exc
    if root.tag.rsplit("}", 1)[-1].lower() != "rss":
        raise AdapterError(f"European Council RSS expected root <rss>, found <{root.tag}>")
    channels = root.findall("channel")
    if len(channels) != 1:
        raise AdapterError(f"European Council RSS expected exactly one channel, found {len(channels)}")
    channel = channels[0]

    title = " ".join((channel.findtext("title") or "").split())
    channel_link = " ".join((channel.findtext("link") or "").split())
    description = " ".join((channel.findtext("description") or "").split())
    if title != EUROPEAN_COUNCIL_CHANNEL_TITLE:
        raise AdapterError(f"European Council RSS channel-title drift: {title!r}")
    if channel_link != EUROPEAN_COUNCIL_CHANNEL_LINK:
        raise AdapterError(f"European Council RSS channel-link drift: {channel_link!r}")
    if description != EUROPEAN_COUNCIL_CHANNEL_DESCRIPTION:
        raise AdapterError(f"European Council RSS channel-description drift: {description!r}")

    nodes = channel.findall("item")
    if not EUROPEAN_COUNCIL_MIN_ITEMS <= len(nodes) <= EUROPEAN_COUNCIL_MAX_ITEMS:
        raise AdapterError(
            "European Council RSS item-count outside bounded contract: "
            f"{len(nodes)} not in [{EUROPEAN_COUNCIL_MIN_ITEMS}, {EUROPEAN_COUNCIL_MAX_ITEMS}]"
        )

    items: list[EuropeanCouncilRSSItem] = []
    seen_guids: set[str] = set()
    for node in nodes:
        child_names = [child.tag.rsplit("}", 1)[-1] for child in list(node)]
        if child_names != EUROPEAN_COUNCIL_ITEM_CHILDREN:
            raise AdapterError(
                "European Council RSS item-field contract drift: "
                f"expected {EUROPEAN_COUNCIL_ITEM_CHILDREN!r}, found {child_names!r}"
            )
        guid = _text(node, "guid", required=True)
        if re.fullmatch(r"[0-9]+", guid) is None:
            raise AdapterError(f"European Council RSS GUID is not numeric: {guid!r}")
        if guid in seen_guids:
            raise AdapterError(f"European Council RSS duplicate GUID: {guid}")
        seen_guids.add(guid)
        link = _text(node, "link", required=True)
        start_local, end_local = parse_european_council_meeting_link(link)
        title_text = _text(node, "title", required=True)
        description_text = _text(node, "description", required=False)
        updated_text = _text(node, "updated", required=False)
        items.append(
            EuropeanCouncilRSSItem(
                guid=guid,
                link=link,
                title=title_text,
                description=description_text,
                updated=updated_text,
                start_local=start_local,
                end_local=end_local,
            )
        )
    return items


def fetch_european_council_meetings_rss(*, timeout: int = 30) -> tuple[list[EuropeanCouncilRSSItem], FetchSnapshot]:
    body, snapshot = fetch_bytes(
        EUROPEAN_COUNCIL_MEETINGS_RSS,
        timeout=timeout,
        accept=EUROPEAN_COUNCIL_RSS_ACCEPT,
        headers={"Accept-Language": "en,en-GB;q=0.9"},
    )
    if snapshot.status != 200:
        raise AdapterError(f"European Council RSS returned HTTP {snapshot.status}")
    parsed = urlparse(snapshot.resolved_url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != EUROPEAN_COUNCIL_OFFICIAL_HOST
        or parsed.path != "/en/rss/meetings.ashx"
        or parse_qs(parsed.query, keep_blank_values=True) != {"cat": ["euco"]}
        or parsed.fragment
    ):
        raise AdapterError(f"European Council RSS resolved away from exact advertised endpoint: {snapshot.resolved_url!r}")
    if "xml" not in snapshot.content_type.lower():
        raise AdapterError(f"European Council RSS content-type drift: {snapshot.content_type!r}")
    if snapshot.body_bytes < 500 or snapshot.body_bytes > 500000:
        raise AdapterError(f"European Council RSS body-size drift: {snapshot.body_bytes} bytes")
    return parse_european_council_meetings_rss(body), snapshot
