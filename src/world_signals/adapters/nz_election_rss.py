from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
import re
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET

from .base import AdapterError, FetchSnapshot, USER_AGENT, fetch_bytes

NZ_ELECTION_RSS_URL = "https://elections.nz/media-and-news/rss"
NZ_ELECTION_ROBOTS_URL = "https://elections.nz/robots.txt"
NZ_ELECTION_TIMETABLE_URL = (
    "https://elections.nz/media-and-news/2026/key-dates-for-2026-general-election"
)
NZ_ELECTION_MEDIA_NEWS_URL = "https://elections.nz/media-and-news"
NZ_ELECTION_OFFICIAL_HOST = "elections.nz"
NZ_ELECTION_RSS_ACCEPT = "application/rss+xml,application/xml;q=0.9,text/xml;q=0.8,*/*;q=0.1"
NZ_ELECTION_CHANNEL_TITLE = "10 Most Recently Updated Pages"
NZ_ELECTION_CHANNEL_DESCRIPTION = "Shows a list of the 10 most recently updated pages."
NZ_ELECTION_EXPECTED_ITEM_COUNT = 10
NZ_ELECTION_MINIMUM_DELAY_SECONDS = 2.0


@dataclass(frozen=True)
class NZElectionRSSItem:
    title: str
    link: str
    description: str
    pub_date_raw: str
    pub_date_iso: str
    guid: str

    def as_dict(self) -> dict:
        return asdict(self)


def _text(node: ET.Element, tag: str) -> str:
    child = node.find(tag)
    if child is None or child.text is None:
        raise AdapterError(f"NZ election RSS item missing required field {tag}")
    return " ".join(child.text.split())


def _normalise_official_item_url(value: str, *, field: str) -> str:
    parsed = urlparse(value.strip())
    if parsed.scheme != "https" or parsed.hostname != NZ_ELECTION_OFFICIAL_HOST:
        raise AdapterError(f"NZ election RSS {field} is not an official https URL: {value!r}")
    if parsed.query or parsed.fragment or parsed.params:
        raise AdapterError(f"NZ election RSS {field} contains query/fragment/params: {value!r}")
    if not parsed.path.startswith("/media-and-news/"):
        raise AdapterError(f"NZ election RSS {field} is outside Media & News: {value!r}")
    path = parsed.path.rstrip("/")
    if not path or path == "/media-and-news":
        raise AdapterError(f"NZ election RSS {field} lacks item-page identity: {value!r}")
    return f"https://{NZ_ELECTION_OFFICIAL_HOST}{path}"


def _parse_pub_date(value: str) -> str:
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError) as exc:
        raise AdapterError(f"invalid NZ election RSS pubDate: {value!r}") from exc
    if parsed.tzinfo is None:
        raise AdapterError(f"NZ election RSS pubDate lacks timezone: {value!r}")
    return parsed.isoformat()


def parse_nz_election_rss(body: bytes | str) -> list[NZElectionRSSItem]:
    raw = body if isinstance(body, bytes) else body.encode("utf-8")
    head = raw[:3000].decode("utf-8", errors="replace").lower()
    if "request rejected" in head or "access denied" in head or "<html" in head:
        raise AdapterError("NZ election RSS returned non-feed/rejection content")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise AdapterError(f"unable to parse NZ election RSS XML: {exc}") from exc
    if root.tag.lower() != "rss":
        raise AdapterError(f"NZ election RSS root-tag drift: {root.tag!r}")
    channel = root.find("channel")
    if channel is None:
        raise AdapterError("NZ election RSS channel missing")

    title_node = channel.find("title")
    desc_node = channel.find("description")
    link_node = channel.find("link")
    title = "" if title_node is None or title_node.text is None else " ".join(title_node.text.split())
    description = "" if desc_node is None or desc_node.text is None else " ".join(desc_node.text.split())
    channel_link = "" if link_node is None or link_node.text is None else " ".join(link_node.text.split())
    if title != NZ_ELECTION_CHANNEL_TITLE:
        raise AdapterError(f"NZ election RSS channel-title drift: {title!r}")
    if description != NZ_ELECTION_CHANNEL_DESCRIPTION:
        raise AdapterError(f"NZ election RSS channel-description drift: {description!r}")
    if channel_link.rstrip("/") != NZ_ELECTION_RSS_URL:
        raise AdapterError(f"NZ election RSS channel-link drift: {channel_link!r}")

    items = channel.findall("item")
    if len(items) != NZ_ELECTION_EXPECTED_ITEM_COUNT:
        raise AdapterError(
            f"NZ election RSS rolling-window item-count drift: expected "
            f"{NZ_ELECTION_EXPECTED_ITEM_COUNT}, found {len(items)}"
        )

    expected_fields = ("title", "link", "description", "pubDate", "guid")
    parsed_items: list[NZElectionRSSItem] = []
    seen_guids: set[str] = set()
    for item in items:
        fields = tuple(child.tag for child in list(item))
        if fields != expected_fields:
            raise AdapterError(f"NZ election RSS item-field contract drift: {fields!r}")
        item_title = _text(item, "title")
        description_text = _text(item, "description")
        link = _normalise_official_item_url(_text(item, "link"), field="link")
        guid = _normalise_official_item_url(_text(item, "guid"), field="guid")
        if link != guid:
            raise AdapterError(f"NZ election RSS link/guid identity disagreement: {link!r} != {guid!r}")
        if guid in seen_guids:
            raise AdapterError(f"duplicate NZ election RSS item identity: {guid}")
        seen_guids.add(guid)
        pub_raw = _text(item, "pubDate")
        parsed_items.append(
            NZElectionRSSItem(
                title=item_title,
                link=link,
                description=description_text,
                pub_date_raw=pub_raw,
                pub_date_iso=_parse_pub_date(pub_raw),
                guid=guid,
            )
        )

    timetable_count = sum(1 for item in parsed_items if item.guid == NZ_ELECTION_TIMETABLE_URL)
    if timetable_count > 1:
        raise AdapterError("NZ election RSS contains duplicate Canonical timetable-page identity")
    return parsed_items


def _validate_robots_text(body: bytes | str) -> str:
    text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body
    prefix = text.lstrip()[:1500].lower()
    if "<html" in prefix or "request rejected" in prefix or "access denied" in prefix:
        raise AdapterError("Elections NZ robots endpoint returned non-policy content")
    if re.search(r"(?im)^\s*user-agent\s*:", text) is None:
        raise AdapterError("Elections NZ robots body lacks User-agent syntax")
    return text


def nz_election_rss_access_policy(robots_body: bytes | str) -> tuple[bool, float]:
    text = _validate_robots_text(robots_body)
    parser = RobotFileParser()
    try:
        parser.parse(text.splitlines())
    except Exception as exc:
        raise AdapterError(f"unable to parse Elections NZ robots policy: {exc}") from exc
    allowed = parser.can_fetch(USER_AGENT, NZ_ELECTION_RSS_URL)

    delays = re.findall(r"(?im)^\s*crawl-delay\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*$", text)
    unique_delays = {float(value) for value in delays}
    if len(unique_delays) > 1:
        raise AdapterError(f"ambiguous Elections NZ robots crawl-delay values: {sorted(unique_delays)}")
    declared = next(iter(unique_delays), 0.0)
    return allowed, max(NZ_ELECTION_MINIMUM_DELAY_SECONDS, declared)


def fetch_nz_election_robots_policy(*, timeout: int = 30) -> tuple[bool, float, FetchSnapshot]:
    body, snapshot = fetch_bytes(
        NZ_ELECTION_ROBOTS_URL,
        timeout=timeout,
        accept="text/plain,*/*;q=0.1",
    )
    if snapshot.status != 200:
        raise AdapterError(f"Elections NZ robots policy returned HTTP {snapshot.status}")
    if "text/plain" not in snapshot.content_type.lower():
        raise AdapterError(f"Elections NZ robots content-type drift: {snapshot.content_type!r}")
    if urlparse(snapshot.resolved_url).geturl() != NZ_ELECTION_ROBOTS_URL:
        raise AdapterError(f"Elections NZ robots endpoint redirected: {snapshot.resolved_url!r}")
    allowed, delay_seconds = nz_election_rss_access_policy(body)
    return allowed, delay_seconds, snapshot


def fetch_nz_election_rss(*, timeout: int = 30) -> tuple[list[NZElectionRSSItem], FetchSnapshot]:
    body, snapshot = fetch_bytes(
        NZ_ELECTION_RSS_URL,
        timeout=timeout,
        accept=NZ_ELECTION_RSS_ACCEPT,
        headers={"Accept-Language": "en-NZ,en;q=0.9"},
    )
    if snapshot.status != 200:
        raise AdapterError(f"NZ election RSS returned HTTP {snapshot.status}")
    parsed_url = urlparse(snapshot.resolved_url)
    if (
        parsed_url.scheme != "https"
        or parsed_url.hostname != NZ_ELECTION_OFFICIAL_HOST
        or parsed_url.path.rstrip("/") != "/media-and-news/rss"
        or parsed_url.query
        or parsed_url.fragment
    ):
        raise AdapterError(f"NZ election RSS resolved away from exact endpoint: {snapshot.resolved_url!r}")
    ctype = snapshot.content_type.lower()
    if not any(token in ctype for token in ("application/rss+xml", "application/xml", "text/xml")):
        response_head = body[:3000].decode("utf-8", errors="replace").lower()
        if "incapsula" in response_head or "request unsuccessful" in response_head:
            raise AdapterError(
                "NZ election RSS access blocked by perimeter security; non-feed response has no event semantics"
            )
        raise AdapterError(f"NZ election RSS content-type drift: {snapshot.content_type!r}")
    if snapshot.body_bytes < 1000 or snapshot.body_bytes > 100000:
        raise AdapterError(f"NZ election RSS body-size drift: {snapshot.body_bytes} bytes")
    return parse_nz_election_rss(body), snapshot
