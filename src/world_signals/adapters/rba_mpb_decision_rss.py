"""Candidate-only RBA Monetary Policy decision publication parser.

This module has no production route registration and performs no writes. The
caller must supply captured feed/page bytes and their transport hashes; this
keeps source retrieval, endpoint governance and candidate construction distinct.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from hashlib import sha256
import json
import re
from html.parser import HTMLParser
from urllib.parse import urlparse
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener
from xml.etree import ElementTree as ET

from .base import AdapterError, FetchSnapshot, USER_AGENT

RBA_MPB_DECISION_RSS_URL = "https://www.rba.gov.au/rss/rss-cb-media-releases.xml"
RBA_MPB_DECISION_ADAPTER_CANDIDATE = "RBA_MPB_DECISION_PUBLICATION_RSS"
RBA_MPB_DECISION_SOURCE_CANDIDATE = "WSSRC-CANDIDATE-CB-RBA-MEDIA-RELEASES-RSS-001"
RBA_DECISION_SERIES = "WS.CB.RBA.MONETARY_POLICY_DECISION"
RBA_DECISION_TITLE = "Statement by the Monetary Policy Board: Monetary Policy Decision"
PARSER_VERSION = "rba-mpb-decision-rss-v1"
RBA_ROBOTS_URL = "https://www.rba.gov.au/robots.txt"


class _RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_exact_url(url: str, *, accept: str, timeout: int = 15) -> tuple[bytes, FetchSnapshot]:
    """Fetch one exact RBA URL; redirects are rejected, never followed."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "www.rba.gov.au":
        raise AdapterError("candidate fetch is restricted to https://www.rba.gov.au")
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    opener = build_opener(_RejectRedirects())
    try:
        with opener.open(request, timeout=timeout) as response:
            body = response.read(2_000_001)
            if len(body) > 2_000_000:
                raise AdapterError("candidate response exceeds the 2 MB bounded response limit")
            status = int(response.status)
            content_type = response.headers.get("Content-Type", "")
            resolved = response.geturl()
    except HTTPError as exc:
        raise AdapterError(f"RBA candidate endpoint HTTP {exc.code}; source-health-only") from exc
    except (URLError, TimeoutError) as exc:
        raise AdapterError(f"RBA candidate endpoint unavailable; source-health-only: {exc}") from exc
    if status != 200 or resolved != url or not body:
        raise AdapterError("RBA candidate endpoint response failed exact status/URL/body checks")
    snapshot = FetchSnapshot(
        url=url,
        resolved_url=resolved,
        status=status,
        content_type=content_type,
        body_sha256=sha256(body).hexdigest(),
        body_bytes=len(body),
    )
    return body, snapshot


def feed_path_allowed_by_robots(body: bytes | str) -> bool:
    from urllib.robotparser import RobotFileParser

    text = body.decode("utf-8", "strict") if isinstance(body, bytes) else body
    if not re.search(r"(?im)^\s*user-agent\s*:", text):
        raise AdapterError("RBA robots response lacks policy syntax")
    parser = RobotFileParser()
    parser.parse(text.splitlines())
    return parser.can_fetch(USER_AGENT, RBA_MPB_DECISION_RSS_URL)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _clean(value: str | None) -> str:
    return " ".join((value or "").replace("\xa0", " ").split())


def _hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _parse_timestamp(value: str) -> datetime:
    raw = _clean(value)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(raw)
        except (TypeError, ValueError, OverflowError) as exc:
            raise AdapterError(f"invalid RBA RSS publication timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise AdapterError("RBA RSS publication timestamp must include an offset")
    return parsed


def _child_text(node: ET.Element, names: set[str]) -> str | None:
    for child in list(node):
        if _local_name(child.tag) in names:
            value = child.attrib.get("resource") or child.attrib.get("href") or child.text
            if value and value.strip():
                return value.strip()
    return None


@dataclass(frozen=True)
class DecisionRSSItem:
    title: str
    link: str
    guid: str | None
    published_raw: str
    published_at: str
    description: str | None
    semantic_item_sha256: str

    def as_dict(self) -> dict:
        return asdict(self)


def parse_decision_rss(body: bytes | str) -> list[DecisionRSSItem]:
    raw = body if isinstance(body, bytes) else body.encode("utf-8")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise AdapterError(f"RBA media-release RSS XML invalid: {exc}") from exc
    nodes = [node for node in root.iter() if _local_name(node.tag) in {"item", "entry"}]
    if not nodes:
        raise AdapterError("RBA media-release feed contained no item/entry records")
    items: list[DecisionRSSItem] = []
    seen: set[tuple[str, str]] = set()
    for node in nodes:
        title = _clean(_child_text(node, {"title"}))
        link = _clean(_child_text(node, {"link"}))
        guid = _clean(_child_text(node, {"guid", "id"})) or None
        published = _child_text(node, {"date", "pubDate", "published", "updated"})
        description = _clean(_child_text(node, {"description", "summary"})) or None
        if not title or not link or not published:
            raise AdapterError("RBA media-release item missing title, link or publication timestamp")
        parsed = _parse_timestamp(published)
        identity = (guid or link, parsed.isoformat())
        if identity in seen:
            continue
        seen.add(identity)
        semantic = {
            "title": title,
            "link": link,
            "guid": guid,
            "published_at": parsed.isoformat(),
            "description": description,
        }
        items.append(DecisionRSSItem(
            title=title,
            link=link,
            guid=guid,
            published_raw=published,
            published_at=parsed.isoformat(),
            description=description,
            semantic_item_sha256=_hash(semantic),
        ))
    return items


def classify_decision_item(item: DecisionRSSItem) -> str:
    if item.title == RBA_DECISION_TITLE:
        return "EXACT_TITLE"
    if "monetary policy" in item.title.lower() or "decision" in item.title.lower():
        return "REVIEW_UNCLASSIFIED"
    return "NOT_A_MONETARY_POLICY_DECISION"


def validate_decision_page_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "www.rba.gov.au":
        raise AdapterError("decision page must use the exact official RBA host over HTTPS")
    if parsed.query or parsed.fragment or parsed.params:
        raise AdapterError("decision page URL must not contain query, fragment or parameters")
    if not re.fullmatch(r"/media-releases/20\d{2}/mr-\d{2}-\d{2}\.html", parsed.path):
        raise AdapterError("decision page is outside the bounded RBA media-release path")
    return f"https://www.rba.gov.au{parsed.path}"


class _VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() in {"script", "style", "noscript"}:
            self.hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"} and self.hidden_depth:
            self.hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden_depth:
            cleaned = _clean(data)
            if cleaned:
                self.parts.append(cleaned)


def _html_text(body: bytes | str) -> str:
    parser = _VisibleText()
    parser.feed(body.decode("utf-8", "replace") if isinstance(body, bytes) else body)
    return " ".join(parser.parts)


def parse_decision_page(
    body: bytes | str,
    *,
    item: DecisionRSSItem,
    resolved_url: str,
) -> dict:
    expected_url = validate_decision_page_url(item.link)
    if resolved_url != expected_url:
        raise AdapterError("decision page redirected; candidate rejected")
    text = _html_text(body)
    if RBA_DECISION_TITLE not in text:
        raise AdapterError("linked RBA page title does not match the controlled decision title")
    number = re.search(r"\bNumber\s+(\d{4})-(\d{2})\b", text)
    expected_year = _parse_timestamp(item.published_at).year
    release_path_id = re.search(r"/mr-(\d{2})-(\d{2})\.html$", expected_url)
    expected_number = f"20{release_path_id.group(1)}-{release_path_id.group(2)}" if release_path_id else None
    if (
        not number
        or int(number.group(1)) != expected_year
        or f"{number.group(1)}-{number.group(2)}" != expected_number
    ):
        raise AdapterError("linked RBA page release identity does not match publication year")
    date_match = re.search(r"\bDate\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})\b", text)
    if not date_match:
        raise AdapterError("linked RBA decision page lacks a source-native release date")
    try:
        release_date = date(int(date_match.group(3)), datetime.strptime(date_match.group(2), "%B").month, int(date_match.group(1)))
    except ValueError as exc:
        raise AdapterError("linked RBA release date is malformed") from exc
    if release_date != _parse_timestamp(item.published_at).date():
        raise AdapterError("linked RBA release date differs from RSS publication date")

    outcome = re.search(
        r"Board decided to (?:(increase|raise|decrease|lower) the cash rate target by\s*([0-9]+(?:\.[0-9]+)?)\s*basis points to\s*([0-9]+(?:\.[0-9]+)?)\s*per cent|leave the cash rate target unchanged at\s*([0-9]+(?:\.[0-9]+)?)\s*per cent)",
        text,
        re.I,
    )
    if not outcome:
        raise AdapterError("controlled cash-rate decision statement not found")
    if outcome.group(4):
        direction, change_bps, target = "UNCHANGED", 0, float(outcome.group(4))
    else:
        verb = outcome.group(1).lower()
        direction = "INCREASE" if verb in {"increase", "raise"} else "DECREASE"
        change_bps = float(outcome.group(2)) * (1 if direction == "INCREASE" else -1)
        target = float(outcome.group(3))
    if not float(target).is_integer() and len(str(outcome.group(3) or outcome.group(4)).split(".")[-1]) > 2:
        raise AdapterError("cash-rate target precision exceeds source contract")
    if change_bps is not None and float(change_bps).is_integer():
        change_bps = int(change_bps)
    if re.search(r"Today.s policy decision was unanimous\.", text, re.I):
        unanimous: bool | str = True
    elif re.search(r"Today.s policy decision was made by majority", text, re.I):
        unanimous = False
    else:
        unanimous = "NOT_STATED"
    return {
        "decision_date": release_date.isoformat(),
        "cash_rate_target_percent": target,
        "decision_direction": direction,
        "change_basis_points": change_bps,
        "decision_unanimous": unanimous,
        "rationale_classification": "ISSUER_STATED_RATIONALE",
    }


def match_canonical_occurrence(
    item: DecisionRSSItem,
    occurrences: list[dict],
) -> tuple[str, dict | None]:
    publication_date = _parse_timestamp(item.published_at).date()
    plausible = []
    for occurrence in occurrences:
        if occurrence.get("series_id") != RBA_DECISION_SERIES:
            continue
        start_utc = occurrence.get("start_utc")
        if not start_utc:
            continue
        try:
            scheduled_date = datetime.fromisoformat(start_utc.replace("Z", "+00:00")).date()
        except ValueError:
            continue
        if scheduled_date == publication_date:
            plausible.append(occurrence)
    if len(plausible) == 1:
        return "MATCHED", plausible[0]
    return ("NO_MATCH", None) if not plausible else ("AMBIGUOUS", None)


def build_result_candidate(
    *,
    item: DecisionRSSItem,
    outcome: dict,
    occurrence: dict,
    feed_transport_sha256: str,
    page_transport_sha256: str,
    detected_at_utc: str,
) -> dict:
    if classify_decision_item(item) != "EXACT_TITLE":
        raise AdapterError("only the exact controlled decision title can produce a candidate")
    page_url = validate_decision_page_url(item.link)
    if not re.fullmatch(r"[0-9a-f]{64}", feed_transport_sha256) or not re.fullmatch(r"[0-9a-f]{64}", page_transport_sha256):
        raise AdapterError("candidate requires captured feed and linked-page transport hashes")
    if occurrence.get("series_id") != RBA_DECISION_SERIES or not occurrence.get("occurrence_id"):
        raise AdapterError("candidate requires an exact existing Canonical decision occurrence")
    detected = _parse_timestamp(detected_at_utc)
    published = _parse_timestamp(item.published_at)
    if detected < published:
        raise AdapterError("detected-at cannot precede source publication time")
    semantic = {
        "canonical_occurrence_id": occurrence["occurrence_id"],
        "canonical_series_id": RBA_DECISION_SERIES,
        "publication_identity": item.guid or item.link,
        "publication_url": page_url,
        "published_at": published.isoformat(),
        "outcome": outcome,
        "rss_item_semantic_sha256": item.semantic_item_sha256,
        "parser_version": PARSER_VERSION,
    }
    decision_day = _parse_timestamp(item.published_at).strftime("%Y%m%d")
    candidate_id = f"WSOUTCAND-AU-RBA-MPB-{decision_day}-001"
    return {
        "candidate_id": candidate_id,
        "candidate_type": "OFFICIAL_EVENT_OUTCOME_REVIEW_CANDIDATE",
        "status": "REVIEW_PENDING",
        "semantic_fingerprint": _hash(semantic),
        "semantic_content": semantic,
        "source_transport_hashes": {
            "rss_transport_sha256": feed_transport_sha256,
            "page_transport_sha256": page_transport_sha256,
        },
        "detected_at_utc": detected.isoformat().replace("+00:00", "Z"),
        "known_at_utc": detected.isoformat().replace("+00:00", "Z"),
        "institution": "Reserve Bank of Australia",
        "jurisdiction": "Australia",
        "source_candidate_id": RBA_MPB_DECISION_SOURCE_CANDIDATE,
        "limitations": [
            "Candidate only; not a production Outcome, Live observation or Canonical lifecycle change.",
            "Issuer rationale is attributed and is not an independently established causal conclusion.",
            "Human review and separately authorised admission are required.",
        ],
        "recommended_governed_actions": ["CANONICAL_COMPLETION_REVIEW", "OPTIONAL_BOUNDED_LIVE_FACT_REVIEW"],
        "automatic_actions": [],
    }
