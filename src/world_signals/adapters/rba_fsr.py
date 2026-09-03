from __future__ import annotations

from dataclasses import dataclass, asdict
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

from .base import AdapterError, FetchSnapshot, fetch_bytes

RBA_FSR_RSS = "https://www.rba.gov.au/rss/rss-cb-fsr.xml"

@dataclass(frozen=True)
class RssItem:
    title: str
    link: str | None
    guid: str | None
    pub_date: str | None
    pub_date_iso: str | None

    def as_dict(self) -> dict:
        return asdict(self)

def _text(node: ET.Element, name: str) -> str | None:
    child=node.find(name)
    if child is None or child.text is None:
        return None
    value=child.text.strip()
    return value or None

def parse_rba_fsr_rss(body: bytes | str) -> list[RssItem]:
    raw=body.encode("utf-8") if isinstance(body, str) else body
    try:
        root=ET.fromstring(raw)
    except ET.ParseError as exc:
        raise AdapterError(f"RBA RSS parse failed: {exc}") from exc
    items=[]
    for item in root.findall(".//item"):
        title=_text(item,"title")
        if not title:
            continue
        pub=_text(item,"pubDate")
        pub_iso=None
        if pub:
            try:
                pub_iso=parsedate_to_datetime(pub).isoformat()
            except (TypeError, ValueError, OverflowError):
                pub_iso=None
        items.append(RssItem(
            title=title,
            link=_text(item,"link"),
            guid=_text(item,"guid"),
            pub_date=pub,
            pub_date_iso=pub_iso,
        ))
    if not items:
        raise AdapterError("RBA FSR RSS contained no <item> entries")
    return items

def fetch_rba_fsr(*, timeout: int = 30) -> tuple[list[RssItem], FetchSnapshot]:
    body,snapshot=fetch_bytes(RBA_FSR_RSS, timeout=timeout, accept="application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.1")
    return parse_rba_fsr_rss(body), snapshot
