from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

from .base import AdapterError, FetchSnapshot, fetch_bytes

ONS_RELEASE_CALENDAR = "https://www.ons.gov.uk/releasecalendar"
ONS_RELEASE_CALENDAR_RSS_ACCEPT = "application/rss+xml, application/xml;q=0.9, */*;q=0.8"


@dataclass(frozen=True)
class ONSReleaseItem:
    title: str
    link: str
    guid: str
    pub_date_iso: str
    description: str

    def as_dict(self) -> dict:
        return asdict(self)


def ons_release_calendar_rss_url(*, page: int = 1, limit: int = 100) -> str:
    if page < 1:
        raise ValueError("page must be >= 1")
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")
    params = {
        "highlight": "true",
        "limit": str(limit),
        "page": str(page),
        "release-type": "type-upcoming",
        "rss": "",
        "sort": "date-newest",
    }
    return ONS_RELEASE_CALENDAR + "?" + urlencode(params)


def _required_text(item: ET.Element, tag: str) -> str:
    node = item.find(tag)
    text = " ".join((node.text or "").split()) if node is not None else ""
    if not text:
        raise AdapterError(f"ONS RSS item missing {tag}")
    return text


def parse_ons_release_calendar_rss(body: bytes | str) -> list[ONSReleaseItem]:
    raw = body.encode("utf-8") if isinstance(body, str) else body
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise AdapterError(f"ONS RSS XML parse failed: {exc}") from exc
    if root.tag != "rss":
        raise AdapterError(f"ONS RSS expected root <rss>, found <{root.tag}>")
    channel = root.find("channel")
    if channel is None:
        raise AdapterError("ONS RSS missing channel")

    parsed: list[ONSReleaseItem] = []
    seen_guid: dict[str, ONSReleaseItem] = {}
    for node in channel.findall("item"):
        title = _required_text(node, "title")
        link = _required_text(node, "link")
        guid = _required_text(node, "guid")
        pub_date = _required_text(node, "pubDate")
        description_node = node.find("description")
        description = " ".join((description_node.text or "").split()) if description_node is not None else ""
        try:
            dt = parsedate_to_datetime(pub_date)
        except (TypeError, ValueError) as exc:
            raise AdapterError(f"ONS RSS invalid pubDate for {title!r}: {pub_date!r}") from exc
        if dt is None or dt.tzinfo is None:
            raise AdapterError(f"ONS RSS pubDate lacks timezone for {title!r}: {pub_date!r}")
        pub_date_iso = dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        item = ONSReleaseItem(
            title=title,
            link=link,
            guid=guid,
            pub_date_iso=pub_date_iso,
            description=description,
        )
        prior = seen_guid.get(guid)
        if prior is not None and prior != item:
            raise AdapterError(f"ONS RSS duplicate guid has conflicting payload: {guid}")
        if prior is None:
            seen_guid[guid] = item
            parsed.append(item)
    return parsed


def fetch_ons_release_calendar_page(*, page: int = 1, limit: int = 100) -> tuple[list[ONSReleaseItem], FetchSnapshot]:
    url = ons_release_calendar_rss_url(page=page, limit=limit)
    body, snapshot = fetch_bytes(url, accept=ONS_RELEASE_CALENDAR_RSS_ACCEPT)
    items = parse_ons_release_calendar_rss(body)
    return items, snapshot


def fetch_ons_upcoming_releases(*, limit: int = 100, max_pages: int = 10) -> tuple[list[ONSReleaseItem], list[FetchSnapshot]]:
    if max_pages < 1:
        raise ValueError("max_pages must be >= 1")
    all_items: list[ONSReleaseItem] = []
    snapshots: list[FetchSnapshot] = []
    seen: dict[str, ONSReleaseItem] = {}
    exhausted = False

    for page in range(1, max_pages + 1):
        items, snapshot = fetch_ons_release_calendar_page(page=page, limit=limit)
        snapshots.append(snapshot)
        for item in items:
            prior = seen.get(item.guid)
            if prior is not None and prior != item:
                raise AdapterError(f"ONS RSS guid changed across pages: {item.guid}")
            if prior is None:
                seen[item.guid] = item
                all_items.append(item)
        if len(items) < limit:
            exhausted = True
            break

    if not exhausted:
        raise AdapterError(
            f"ONS upcoming RSS pagination exceeded safe bound of {max_pages} pages; "
            "feed completeness is unknown"
        )
    return all_items, snapshots
