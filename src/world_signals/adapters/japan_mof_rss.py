from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import timezone
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET

from .base import AdapterError, FetchSnapshot, fetch_bytes

JAPAN_MOF_NEWS_RSS = "https://www.mof.go.jp/english/news.rss"
JAPAN_MOF_RSS_DOCS = "https://www.mof.go.jp/english/about_mof/rss/index.html"
JAPAN_MOF_RSS_ACCEPT = "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.1"
JAPAN_MOF_OFFICIAL_PREFIX = "https://www.mof.go.jp/"


@dataclass(frozen=True)
class JapanMOFRSSItem:
    title: str
    link: str
    guid: str
    pub_date_utc: str
    pub_date_original: str
    description: str

    def as_dict(self) -> dict:
        return asdict(self)


def _text(node: ET.Element, tag: str, *, required: bool = False) -> str:
    child = node.find(tag)
    value = " ".join((child.text or "").split()) if child is not None else ""
    if required and not value:
        raise AdapterError(f"Japan MOF RSS item missing {tag}")
    return value


def parse_japan_mof_news_rss(body: bytes | str) -> list[JapanMOFRSSItem]:
    raw = body.encode("utf-8") if isinstance(body, str) else body
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise AdapterError(f"Japan MOF RSS XML parse failed: {exc}") from exc
    if root.tag != "rss":
        raise AdapterError(f"Japan MOF RSS expected root <rss>, found <{root.tag}>")
    channel = root.find("channel")
    if channel is None:
        raise AdapterError("Japan MOF RSS missing channel")

    parsed: list[JapanMOFRSSItem] = []
    seen_identity: dict[str, JapanMOFRSSItem] = {}
    for node in channel.findall("item"):
        title = _text(node, "title", required=True)
        link = _text(node, "link", required=True)
        guid = _text(node, "guid") or link
        pub_date = _text(node, "pubDate", required=True)
        description = _text(node, "description")
        if not link.startswith(JAPAN_MOF_OFFICIAL_PREFIX):
            raise AdapterError(f"Japan MOF RSS item points outside official MOF host: {link!r}")
        if guid.startswith("http") and not guid.startswith(JAPAN_MOF_OFFICIAL_PREFIX):
            raise AdapterError(f"Japan MOF RSS guid points outside official MOF host: {guid!r}")
        try:
            dt = parsedate_to_datetime(pub_date)
        except (TypeError, ValueError) as exc:
            raise AdapterError(f"Japan MOF RSS invalid pubDate for {title!r}: {pub_date!r}") from exc
        if dt is None or dt.tzinfo is None:
            raise AdapterError(f"Japan MOF RSS pubDate lacks timezone for {title!r}: {pub_date!r}")
        pub_date_utc = dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        item = JapanMOFRSSItem(
            title=title,
            link=link,
            guid=guid,
            pub_date_utc=pub_date_utc,
            pub_date_original=pub_date,
            description=description,
        )
        prior = seen_identity.get(guid)
        if prior is not None and prior != item:
            raise AdapterError(f"Japan MOF RSS duplicate identity has conflicting payload: {guid}")
        if prior is None:
            seen_identity[guid] = item
            parsed.append(item)

    if not parsed:
        raise AdapterError("Japan MOF RSS contained no items")
    return parsed


def fetch_japan_mof_news_rss(*, timeout: int = 30) -> tuple[list[JapanMOFRSSItem], FetchSnapshot]:
    body, snapshot = fetch_bytes(
        JAPAN_MOF_NEWS_RSS,
        timeout=timeout,
        accept=JAPAN_MOF_RSS_ACCEPT,
    )
    if snapshot.status != 200:
        raise AdapterError(f"Japan MOF RSS returned HTTP {snapshot.status}")
    return parse_japan_mof_news_rss(body), snapshot
