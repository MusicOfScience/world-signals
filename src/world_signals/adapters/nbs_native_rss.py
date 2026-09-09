from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

from .base import AdapterError, FetchSnapshot, fetch_bytes

NBS_NATIVE_RSS_DOCS = "https://www.stats.gov.cn/wzgl/rss/202302/t20230217_1912859.html"
NBS_NATIVE_LATEST_RELEASES_RSS = "https://www.stats.gov.cn/sj/zxfb/rss.xml"
NBS_NATIVE_RSS_ACCEPT = "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.1"
NBS_OFFICIAL_HOSTS = {"stats.gov.cn", "www.stats.gov.cn"}
NBS_ITEM_CHILDREN = [
    "title", "channel", "link", "source", "pubTime", "pubDate",
    "description", "content", "docId", "hitCount",
]

_CPI = re.compile(r"^(\d{4})年(\d{1,2})月份居民消费价格")
_PPI = re.compile(r"^(\d{4})年(\d{1,2})月份工业生产者出厂价格")
_PMI = re.compile(r"^(\d{4})年(\d{1,2})月中国采购经理指数运行情况$")
_IP = re.compile(r"^(\d{4})年(?:(?:1[—-])?(\d{1,2})月份|上半年)规模以上工业增加值")
_ENERGY = re.compile(r"^(\d{4})年(?:(?:1[—-])?(\d{1,2})月份|上半年)能源生产情况$")
_FAI = re.compile(r"^(\d{4})年(?:(?:1[—-])?(\d{1,2})月份|上半年|全年)全国固定资产投资")
_REALESTATE = re.compile(r"^(\d{4})年(?:(?:1[—-])?(\d{1,2})月份|上半年|全年)全国房地产市场基本情况$")
_RETAIL = re.compile(r"^(\d{4})年(?:(?:1[—-])?(\d{1,2})月份|上半年|全年)社会消费品零售总额")
_NEP_MONTH = re.compile(r"^(?:(?:1[—-])?(\d{1,2})月份)国民经济")
_NEP_Q1 = re.compile(r"^一季度国民经济")
_NEP_H1 = re.compile(r"^上半年国民经济")
_NEP_Q3 = re.compile(r"^前三季度国民经济")


@dataclass(frozen=True)
class NBSNativeReleaseItem:
    title: str
    channel: str
    link: str
    source_text: str
    publication_time: str
    publication_date: str
    doc_id: str
    series_key: str | None
    reference_year: int | None
    reference_month: int | None

    def as_dict(self) -> dict:
        return asdict(self)


def _text(node: ET.Element, tag: str, *, required: bool = False) -> str:
    child = node.find(tag)
    value = " ".join("".join(child.itertext()).split()) if child is not None else ""
    if required and not value:
        raise AdapterError(f"NBS native Latest Releases RSS item missing {tag}")
    return value


def _parse_publication_timestamp(raw: str, field: str) -> datetime:
    try:
        return datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
    except ValueError as exc:
        raise AdapterError(f"NBS native RSS invalid {field}: {raw!r}") from exc


def _validate_link(link: str) -> None:
    parsed = urlparse(link)
    if parsed.scheme != "https" or parsed.hostname not in NBS_OFFICIAL_HOSTS:
        raise AdapterError(f"NBS native RSS item points outside official HTTPS host: {link!r}")
    if parsed.query or parsed.fragment:
        raise AdapterError(f"NBS native RSS item link unexpectedly has query/fragment: {link!r}")
    if not re.fullmatch(r"/sj/zxfb/\d{6}/t\d{8}_\d+\.html", parsed.path):
        raise AdapterError(f"NBS native RSS item official-link path contract drift: {parsed.path!r}")


def _month_or_special(match: re.Match[str], title: str) -> int:
    month = match.group(2) if match.lastindex and match.lastindex >= 2 else None
    if month is not None:
        value = int(month)
    elif "上半年" in title:
        value = 6
    elif "全年" in title:
        value = 12
    else:
        raise AdapterError(f"NBS native RSS could not derive bounded reference month: {title!r}")
    if not 1 <= value <= 12:
        raise AdapterError(f"NBS native RSS invalid reference month in title: {title!r}")
    return value


def _classify_title(title: str, publication_dt: datetime) -> tuple[str | None, int | None, int | None]:
    matches: list[tuple[str, int, int]] = []

    for key, pattern in (("CPI", _CPI), ("PPI", _PPI), ("PMI", _PMI)):
        m = pattern.search(title)
        if m:
            year, month = int(m.group(1)), int(m.group(2))
            matches.append((key, year, month))

    for key, pattern in (
        ("IP", _IP),
        ("ENERGY", _ENERGY),
        ("FAI", _FAI),
        ("REALESTATE", _REALESTATE),
        ("RETAIL", _RETAIL),
    ):
        m = pattern.search(title)
        if m:
            matches.append((key, int(m.group(1)), _month_or_special(m, title)))

    nep_month = _NEP_MONTH.search(title)
    if nep_month:
        matches.append(("NEP", publication_dt.year, int(nep_month.group(1))))
    if _NEP_Q1.search(title):
        matches.append(("NEP", publication_dt.year, 3))
    if _NEP_H1.search(title):
        matches.append(("NEP", publication_dt.year, 6))
    if _NEP_Q3.search(title):
        matches.append(("NEP", publication_dt.year, 9))

    unique = set(matches)
    if len(unique) > 1:
        raise AdapterError(f"NBS native RSS title maps ambiguously to configured series identity: {title!r} -> {sorted(unique)!r}")
    if not unique:
        return None, None, None
    key, year, month = next(iter(unique))
    if not 1 <= month <= 12:
        raise AdapterError(f"NBS native RSS invalid classified reference month: {title!r}")
    return key, year, month


def parse_nbs_native_latest_releases_rss(body: bytes | str) -> list[NBSNativeReleaseItem]:
    raw = body.encode("utf-8") if isinstance(body, str) else body
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise AdapterError(f"NBS native Latest Releases RSS XML parse failed: {exc}") from exc
    if root.tag.rsplit("}", 1)[-1].lower() != "rss":
        raise AdapterError(f"NBS native Latest Releases RSS expected root <rss>, found <{root.tag}>")
    channels = root.findall("channel")
    if len(channels) != 1:
        raise AdapterError(f"NBS native Latest Releases RSS expected exactly one channel, found {len(channels)}")
    channel = channels[0]

    nodes = channel.findall("item")
    if not nodes:
        raise AdapterError("NBS native Latest Releases RSS contained no items")
    if len(nodes) > 1000:
        raise AdapterError(f"NBS native Latest Releases RSS unexpected item-count expansion: {len(nodes)}")

    parsed_items: list[NBSNativeReleaseItem] = []
    seen_payloads: set[tuple[str, str, str]] = set()
    seen_target_identity: dict[tuple[str, int, int], NBSNativeReleaseItem] = {}
    for node in nodes:
        child_names = [child.tag.rsplit("}", 1)[-1] for child in list(node)]
        if child_names != NBS_ITEM_CHILDREN:
            raise AdapterError(
                "NBS native Latest Releases RSS item field contract drift: "
                f"expected {NBS_ITEM_CHILDREN!r}, found {child_names!r}"
            )
        title = _text(node, "title", required=True)
        channel_text = _text(node, "channel", required=True)
        if channel_text != "数据发布":
            raise AdapterError(f"NBS native Latest Releases RSS unexpected item channel: {channel_text!r}")
        link = _text(node, "link", required=True)
        _validate_link(link)
        source_text = _text(node, "source", required=False)
        pub_time = _text(node, "pubTime", required=True)
        pub_date = _text(node, "pubDate", required=True)
        pub_time_dt = _parse_publication_timestamp(pub_time, "pubTime")
        pub_date_dt = _parse_publication_timestamp(pub_date, "pubDate")
        if pub_time_dt != pub_date_dt:
            raise AdapterError(
                "NBS native Latest Releases RSS pubTime/pubDate divergence: "
                f"{pub_time!r} != {pub_date!r}"
            )
        doc_id = _text(node, "docId", required=True)
        if not re.fullmatch(r"\d+", doc_id):
            raise AdapterError(f"NBS native Latest Releases RSS invalid docId: {doc_id!r}")
        series_key, reference_year, reference_month = _classify_title(title, pub_time_dt)
        item = NBSNativeReleaseItem(
            title=title,
            channel=channel_text,
            link=link,
            source_text=source_text,
            publication_time=pub_time,
            publication_date=pub_date,
            doc_id=doc_id,
            series_key=series_key,
            reference_year=reference_year,
            reference_month=reference_month,
        )
        payload_identity = (title, link, doc_id)
        if payload_identity in seen_payloads:
            raise AdapterError(f"NBS native Latest Releases RSS duplicate item payload: {payload_identity!r}")
        seen_payloads.add(payload_identity)
        if series_key is not None:
            target_identity = (series_key, int(reference_year), int(reference_month))
            prior = seen_target_identity.get(target_identity)
            if prior is not None:
                raise AdapterError(
                    "NBS native Latest Releases RSS multiple items share one configured-series identity: "
                    f"{target_identity!r}: {prior.title!r} / {title!r}"
                )
            seen_target_identity[target_identity] = item
        parsed_items.append(item)

    return parsed_items


def fetch_nbs_native_latest_releases_rss(*, timeout: int = 45) -> tuple[list[NBSNativeReleaseItem], FetchSnapshot]:
    body, snapshot = fetch_bytes(
        NBS_NATIVE_LATEST_RELEASES_RSS,
        timeout=timeout,
        accept=NBS_NATIVE_RSS_ACCEPT,
    )
    if snapshot.status != 200:
        raise AdapterError(f"NBS native Latest Releases RSS returned HTTP {snapshot.status}")
    return parse_nbs_native_latest_releases_rss(body), snapshot
