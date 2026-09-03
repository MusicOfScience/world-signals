from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
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

def _local_name(tag: str) -> str:
    return tag.rsplit("}",1)[-1] if "}" in tag else tag

def _child(node: ET.Element, *names: str) -> ET.Element | None:
    wanted=set(names)
    for child in list(node):
        if _local_name(child.tag) in wanted:
            return child
    return None

def _text(node: ET.Element, *names: str) -> str | None:
    child=_child(node,*names)
    if child is None:
        return None
    if child.text and child.text.strip():
        return child.text.strip()
    href=child.attrib.get("href")
    return href.strip() if href else None

def _parse_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).isoformat()
    except (TypeError, ValueError, OverflowError):
        pass
    try:
        return datetime.fromisoformat(value.replace("Z","+00:00")).isoformat()
    except ValueError:
        return None

def parse_rba_fsr_rss(body: bytes | str) -> list[RssItem]:
    raw=body.encode("utf-8") if isinstance(body, str) else body
    try:
        root=ET.fromstring(raw)
    except ET.ParseError as exc:
        raise AdapterError(f"RBA RSS parse failed: {exc}") from exc
    entries=[node for node in root.iter() if _local_name(node.tag) in {"item","entry"}]
    items=[]
    for item in entries:
        title=_text(item,"title")
        if not title:
            continue
        pub=_text(item,"pubDate","date","published","updated")
        items.append(RssItem(
            title=title,
            link=_text(item,"link"),
            guid=_text(item,"guid","id"),
            pub_date=pub,
            pub_date_iso=_parse_date(pub),
        ))
    if not items:
        root_names=sorted({_local_name(node.tag) for node in root.iter()})[:20]
        raise AdapterError(f"RBA FSR RSS contained no parseable item/entry elements; XML names={root_names}")
    return items

def fetch_rba_fsr(*, timeout: int = 30) -> tuple[list[RssItem], FetchSnapshot]:
    body,snapshot=fetch_bytes(RBA_FSR_RSS, timeout=timeout, accept="application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.1")
    return parse_rba_fsr_rss(body), snapshot
