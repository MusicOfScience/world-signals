from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import re
import xml.etree.ElementTree as ET

from .base import AdapterError, FetchSnapshot, fetch_bytes

SARB_RSS_DOCS = "https://www.resbank.co.za/en/home/quick-links/rss-feeds"
SARB_PUBLICATIONS_RSS = "https://www.resbank.co.za/bin/sarb/solr/publications/rss"
SARB_RSS_ACCEPT = "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.1"
SARB_MPC_CATEGORY = "Statements > Monetary Policy Statements"
TITLE_RE = re.compile(r"^Statement of the Monetary Policy Committee (January|February|March|April|May|June|July|August|September|October|November|December) (\d{4})$")
MONTHS = {name: i for i, name in enumerate(("January","February","March","April","May","June","July","August","September","October","November","December"), 1)}
ITEM_FIELDS = ("title", "link", "description", "pubDate", "category", "guid")

@dataclass(frozen=True)
class SARBPublicationItem:
    title: str
    link: str
    description: str
    pub_date: str
    category: str
    guid: str
    mpc_year: int | None = None
    mpc_month: int | None = None
    mpc_month_name: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


def _text(node: ET.Element, tag: str, *, required: bool = False) -> str:
    child=node.find(tag)
    value=" ".join("".join(child.itertext()).split()) if child is not None else ""
    if required and not value:
        raise AdapterError(f"SARB RSS item missing {tag}")
    return value


def _parse_pub_date(value: str) -> datetime:
    try:
        parsed=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as exc:
        raise AdapterError(f"SARB RSS invalid ISO pubDate: {value!r}") from exc
    if parsed.tzinfo is None:
        raise AdapterError(f"SARB RSS pubDate lacks timezone: {value!r}")
    return parsed


def _mpc_identity(title: str, link: str, category: str) -> tuple[int|None,int|None,str|None]:
    marker="monetary policy committee"
    match=TITLE_RE.fullmatch(title)
    if match is None:
        if marker in title.lower() or "monetary-policy-statements" in link.lower():
            raise AdapterError(f"SARB MPC statement identity drift: title={title!r} link={link!r}")
        return None,None,None
    month_name,year_raw=match.groups()
    year=int(year_raw); month=MONTHS[month_name]
    expected=f"/en/home/publications/publication-detail-pages/statements/monetary-policy-statements/{year}/{month_name.lower()}"
    if link != expected:
        raise AdapterError(f"SARB MPC statement path drift: expected {expected!r}, found {link!r}")
    if SARB_MPC_CATEGORY not in category:
        raise AdapterError(f"SARB MPC statement category drift: {category!r}")
    return year,month,month_name


def parse_sarb_publications_rss(body: bytes | str) -> list[SARBPublicationItem]:
    raw=body.encode("utf-8") if isinstance(body,str) else body
    try:
        root=ET.fromstring(raw)
    except ET.ParseError as exc:
        raise AdapterError(f"SARB RSS XML parse failed: {exc}") from exc
    if root.tag.lower()!="rss":
        raise AdapterError(f"SARB RSS expected root <rss>, found <{root.tag}>")
    channel=root.find("channel")
    if channel is None:
        raise AdapterError("SARB RSS missing channel")
    out=[]; seen=set()
    for node in channel.findall("item"):
        child_names=tuple(child.tag.rsplit("}",1)[-1] for child in list(node))
        if child_names != ITEM_FIELDS:
            raise AdapterError(f"SARB RSS item field contract drift: expected {ITEM_FIELDS!r}, found {child_names!r}")
        title=_text(node,"title",required=True)
        link=_text(node,"link",required=True)
        description=_text(node,"description")
        pub_date=_text(node,"pubDate",required=True)
        category=_text(node,"category",required=True)
        guid=_text(node,"guid",required=True)
        _parse_pub_date(pub_date)
        if not link.startswith("/en/home/publications/publication-detail-pages/") or "?" in link or "#" in link:
            raise AdapterError(f"SARB RSS item link contract drift: {link!r}")
        if not guid.startswith("/content/sarb-project/en/home/publications/publication-detail-pages/"):
            raise AdapterError(f"SARB RSS guid contract drift: {guid!r}")
        identity=_mpc_identity(title,link,category)
        key=(guid,pub_date)
        if key in seen:
            raise AdapterError(f"SARB RSS duplicate item identity: {key!r}")
        seen.add(key)
        out.append(SARBPublicationItem(title,link,description,pub_date,category,guid,*identity))
    if not out:
        raise AdapterError("SARB RSS contained no items")
    return out


def fetch_sarb_publications_rss(*, timeout: int = 30) -> tuple[list[SARBPublicationItem], FetchSnapshot]:
    body,snapshot=fetch_bytes(SARB_PUBLICATIONS_RSS,timeout=timeout,accept=SARB_RSS_ACCEPT)
    if snapshot.status != 200:
        raise AdapterError(f"SARB RSS returned HTTP {snapshot.status}")
    return parse_sarb_publications_rss(body),snapshot
