from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import timezone
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET

from .base import AdapterError, FetchSnapshot, fetch_bytes

FED_MONETARY_POLICY_RSS = "https://www.federalreserve.gov/feeds/press_monetary.xml"
FED_MONETARY_POLICY_RSS_ACCEPT = "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.1"
FED_RSS_OFFICIAL_PREFIX = "https://www.federalreserve.gov/"


@dataclass(frozen=True)
class FedMonetaryRSSItem:
    title: str
    link: str
    guid: str
    pub_date_utc: str
    description: str

    def as_dict(self) -> dict:
        return asdict(self)


def _required_text(item: ET.Element, tag: str) -> str:
    node = item.find(tag)
    text = " ".join((node.text or "").split()) if node is not None else ""
    if not text:
        raise AdapterError(f"Federal Reserve monetary RSS item missing {tag}")
    return text


def parse_fed_monetary_policy_rss(body: bytes | str) -> list[FedMonetaryRSSItem]:
    raw = body.encode("utf-8") if isinstance(body, str) else body
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise AdapterError(f"Federal Reserve monetary RSS XML parse failed: {exc}") from exc
    if root.tag != "rss":
        raise AdapterError(f"Federal Reserve monetary RSS expected root <rss>, found <{root.tag}>")
    channel = root.find("channel")
    if channel is None:
        raise AdapterError("Federal Reserve monetary RSS missing channel")

    parsed: list[FedMonetaryRSSItem] = []
    seen_guid: dict[str, FedMonetaryRSSItem] = {}
    for node in channel.findall("item"):
        title = _required_text(node, "title")
        link = _required_text(node, "link")
        guid = _required_text(node, "guid")
        pub_date = _required_text(node, "pubDate")
        description_node = node.find("description")
        description = " ".join((description_node.text or "").split()) if description_node is not None else ""
        if not link.startswith(FED_RSS_OFFICIAL_PREFIX) or not guid.startswith(FED_RSS_OFFICIAL_PREFIX):
            raise AdapterError(f"Federal Reserve monetary RSS item points outside official host: {link!r} / {guid!r}")
        try:
            dt = parsedate_to_datetime(pub_date)
        except (TypeError, ValueError) as exc:
            raise AdapterError(f"Federal Reserve monetary RSS invalid pubDate for {title!r}: {pub_date!r}") from exc
        if dt is None or dt.tzinfo is None:
            raise AdapterError(f"Federal Reserve monetary RSS pubDate lacks timezone for {title!r}: {pub_date!r}")
        pub_date_utc = dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        item = FedMonetaryRSSItem(
            title=title,
            link=link,
            guid=guid,
            pub_date_utc=pub_date_utc,
            description=description,
        )
        prior = seen_guid.get(guid)
        if prior is not None and prior != item:
            raise AdapterError(f"Federal Reserve monetary RSS duplicate guid has conflicting payload: {guid}")
        if prior is None:
            seen_guid[guid] = item
            parsed.append(item)

    if not parsed:
        raise AdapterError("Federal Reserve monetary RSS contained no items")
    return parsed


def fetch_fed_monetary_policy_rss(*, timeout: int = 30) -> tuple[list[FedMonetaryRSSItem], FetchSnapshot]:
    body, snapshot = fetch_bytes(
        FED_MONETARY_POLICY_RSS,
        timeout=timeout,
        accept=FED_MONETARY_POLICY_RSS_ACCEPT,
    )
    if snapshot.status != 200:
        raise AdapterError(f"Federal Reserve monetary RSS returned HTTP {snapshot.status}")
    items = parse_fed_monetary_policy_rss(body)
    return items, snapshot
