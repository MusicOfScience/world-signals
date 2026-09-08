from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import timezone
from email.utils import parsedate_to_datetime
import html
import re
import xml.etree.ElementTree as ET

from .base import AdapterError, FetchSnapshot, fetch_bytes

BSP_RSS_DOCS = "https://www.bsp.gov.ph/SitePages/RSS.aspx"
BSP_MEDIA_RELEASES_RSS = (
    "https://www.bsp.gov.ph/_layouts/15/listfeed.aspx?"
    "List=9b0a2117-49d8-4e96-80ba-8651a0e3e17a&"
    "View=8c968884-887d-4d63-8c00-ba05ea3c2d93"
)
BSP_RSS_ACCEPT = "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.1"
BSP_OFFICIAL_PREFIX = "https://www.bsp.gov.ph/"


@dataclass(frozen=True)
class BSPMediaReleaseItem:
    title: str
    link: str
    guid: str
    pub_date_utc: str
    pub_date_original: str
    description_text: str

    def as_dict(self) -> dict:
        return asdict(self)


def _text(node: ET.Element, tag: str, *, required: bool = False) -> str:
    child = node.find(tag)
    value = " ".join((child.text or "").split()) if child is not None else ""
    if required and not value:
        raise AdapterError(f"BSP Media Releases RSS item missing {tag}")
    return value


def _plain_description(raw: str) -> str:
    value = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", raw)
    value = re.sub(r"(?s)<[^>]+>", " ", value)
    return " ".join(html.unescape(value).replace("\xa0", " ").split())


def parse_bsp_media_releases_rss(body: bytes | str) -> list[BSPMediaReleaseItem]:
    raw = body.encode("utf-8") if isinstance(body, str) else body
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise AdapterError(f"BSP Media Releases RSS XML parse failed: {exc}") from exc
    if root.tag.lower() != "rss":
        raise AdapterError(f"BSP Media Releases RSS expected root <rss>, found <{root.tag}>")
    channel = root.find("channel")
    if channel is None:
        raise AdapterError("BSP Media Releases RSS missing channel")

    parsed: list[BSPMediaReleaseItem] = []
    seen: dict[str, BSPMediaReleaseItem] = {}
    for node in channel.findall("item"):
        title = _text(node, "title", required=True)
        link = _text(node, "link", required=True)
        guid = _text(node, "guid") or link
        pub_date = _text(node, "pubDate", required=True)
        description_raw = _text(node, "description")
        if not link.startswith(BSP_OFFICIAL_PREFIX):
            raise AdapterError(f"BSP Media Releases RSS item points outside official host: {link!r}")
        if guid.startswith("http") and not guid.startswith(BSP_OFFICIAL_PREFIX):
            raise AdapterError(f"BSP Media Releases RSS guid points outside official host: {guid!r}")
        try:
            dt = parsedate_to_datetime(pub_date)
        except (TypeError, ValueError) as exc:
            raise AdapterError(f"BSP Media Releases RSS invalid pubDate for {title!r}: {pub_date!r}") from exc
        if dt is None or dt.tzinfo is None:
            raise AdapterError(f"BSP Media Releases RSS pubDate lacks timezone for {title!r}: {pub_date!r}")
        item = BSPMediaReleaseItem(
            title=title,
            link=link,
            guid=guid,
            pub_date_utc=dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            pub_date_original=pub_date,
            description_text=_plain_description(description_raw),
        )
        prior = seen.get(guid)
        if prior is not None and prior != item:
            raise AdapterError(f"BSP Media Releases RSS duplicate identity has conflicting payload: {guid}")
        if prior is None:
            seen[guid] = item
            parsed.append(item)

    if not parsed:
        raise AdapterError("BSP Media Releases RSS contained no items")
    return parsed


def fetch_bsp_media_releases_rss(*, timeout: int = 30) -> tuple[list[BSPMediaReleaseItem], FetchSnapshot]:
    body, snapshot = fetch_bytes(
        BSP_MEDIA_RELEASES_RSS,
        timeout=timeout,
        accept=BSP_RSS_ACCEPT,
    )
    if snapshot.status != 200:
        raise AdapterError(f"BSP Media Releases RSS returned HTTP {snapshot.status}")
    return parse_bsp_media_releases_rss(body), snapshot
