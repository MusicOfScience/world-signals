from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import PurePosixPath
import re
import xml.etree.ElementTree as ET
from urllib.parse import unquote, urlparse

from .base import AdapterError, FetchSnapshot, fetch_bytes

CBSL_RSS_DOCS = "https://www.cbsl.gov.lk/en/rss-feeds"
CBSL_MPR_RSS = "https://www.cbsl.gov.lk/en/press/press-releases/mprrss"
CBSL_RSS_ACCEPT = "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.1"
CBSL_OFFICIAL_HOSTS = {"cbsl.gov.lk", "www.cbsl.gov.lk"}
TITLE_RE = re.compile(r"^Monetary Policy Review\s*-\s*No\.\s*(\d+)\s+of\s+(\d{4})$")
FILENAME_RE = re.compile(
    r"^press_(\d{8})_Monetary_Policy_Review_No_(\d+)_(\d{4})_e_[A-Za-z0-9]+\.pdf$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CBSLMonetaryPolicyReviewItem:
    title: str
    link: str
    source_text: str
    review_number: int
    review_year: int
    link_date: str
    link_filename: str

    def as_dict(self) -> dict:
        return asdict(self)


def _text(node: ET.Element, tag: str, *, required: bool = False) -> str:
    child = node.find(tag)
    value = " ".join("".join(child.itertext()).split()) if child is not None else ""
    if required and not value:
        raise AdapterError(f"CBSL Monetary Policy Review RSS item missing {tag}")
    return value


def _parse_identity(title: str, link: str) -> tuple[int, int, str, str]:
    title_match = TITLE_RE.fullmatch(title)
    if title_match is None:
        raise AdapterError(f"CBSL Monetary Policy Review RSS title identity drift: {title!r}")
    title_number = int(title_match.group(1))
    title_year = int(title_match.group(2))

    parsed = urlparse(link)
    if parsed.scheme != "https" or parsed.hostname not in CBSL_OFFICIAL_HOSTS:
        raise AdapterError(f"CBSL Monetary Policy Review RSS item points outside official HTTPS host: {link!r}")
    if parsed.query or parsed.fragment:
        raise AdapterError(f"CBSL Monetary Policy Review RSS item link unexpectedly has query/fragment: {link!r}")
    filename = PurePosixPath(unquote(parsed.path)).name
    filename_match = FILENAME_RE.fullmatch(filename)
    if filename_match is None:
        raise AdapterError(f"CBSL Monetary Policy Review RSS official PDF filename identity drift: {filename!r}")
    date_compact, filename_number_raw, filename_year_raw = filename_match.groups()
    filename_number = int(filename_number_raw)
    filename_year = int(filename_year_raw)
    if (title_number, title_year) != (filename_number, filename_year):
        raise AdapterError(
            "CBSL Monetary Policy Review RSS title/filename identity mismatch: "
            f"title=({title_number},{title_year}) filename=({filename_number},{filename_year})"
        )
    try:
        link_date = datetime.strptime(date_compact, "%Y%m%d").date().isoformat()
    except ValueError as exc:
        raise AdapterError(f"CBSL Monetary Policy Review RSS invalid official PDF filename date: {date_compact!r}") from exc
    return title_number, title_year, link_date, filename


def parse_cbsl_mpr_rss(body: bytes | str) -> list[CBSLMonetaryPolicyReviewItem]:
    raw = body.encode("utf-8") if isinstance(body, str) else body
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise AdapterError(f"CBSL Monetary Policy Review RSS XML parse failed: {exc}") from exc
    if root.tag.lower() != "rss":
        raise AdapterError(f"CBSL Monetary Policy Review RSS expected root <rss>, found <{root.tag}>")
    channel = root.find("channel")
    if channel is None:
        raise AdapterError("CBSL Monetary Policy Review RSS missing channel")

    parsed_items: list[CBSLMonetaryPolicyReviewItem] = []
    seen: dict[tuple[int, int, str], CBSLMonetaryPolicyReviewItem] = {}
    for node in channel.findall("item"):
        child_names = [child.tag.rsplit("}", 1)[-1] for child in list(node)]
        if child_names != ["title", "link", "source"]:
            raise AdapterError(
                "CBSL Monetary Policy Review RSS item field contract drift: "
                f"expected ['title', 'link', 'source'], found {child_names!r}"
            )
        title = _text(node, "title", required=True)
        link = _text(node, "link", required=True)
        source_text = _text(node, "source", required=True)
        review_number, review_year, link_date, filename = _parse_identity(title, link)
        item = CBSLMonetaryPolicyReviewItem(
            title=title,
            link=link,
            source_text=source_text,
            review_number=review_number,
            review_year=review_year,
            link_date=link_date,
            link_filename=filename,
        )
        identity = (review_year, review_number, link_date)
        prior = seen.get(identity)
        if prior is not None and prior != item:
            raise AdapterError(f"CBSL Monetary Policy Review RSS duplicate identity has conflicting payload: {identity}")
        if prior is None:
            seen[identity] = item
            parsed_items.append(item)

    if not parsed_items:
        raise AdapterError("CBSL Monetary Policy Review RSS contained no items")
    return parsed_items


def fetch_cbsl_mpr_rss(*, timeout: int = 30) -> tuple[list[CBSLMonetaryPolicyReviewItem], FetchSnapshot]:
    body, snapshot = fetch_bytes(CBSL_MPR_RSS, timeout=timeout, accept=CBSL_RSS_ACCEPT)
    if snapshot.status != 200:
        raise AdapterError(f"CBSL Monetary Policy Review RSS returned HTTP {snapshot.status}")
    return parse_cbsl_mpr_rss(body), snapshot
