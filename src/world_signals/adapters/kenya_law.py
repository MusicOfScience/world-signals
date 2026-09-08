from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
from html.parser import HTMLParser
import re

from .base import AdapterError, FetchSnapshot, fetch_bytes

KENYA_PFM_CURRENT = "https://new.kenyalaw.org/akn/ke/act/2012/18/eng"
KENYA_PFM_BASELINE_2025_11_04 = "https://new.kenyalaw.org/akn/ke/act/2012/18/eng@2025-11-04"

class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts=[]
        self._skip=0
    def handle_starttag(self,tag,attrs):
        if tag.lower() in {"script","style","noscript"}:
            self._skip+=1
    def handle_endtag(self,tag):
        if tag.lower() in {"script","style","noscript"} and self._skip:
            self._skip-=1
    def handle_data(self,data):
        if not self._skip:
            self.parts.append(data)

@dataclass(frozen=True)
class KenyaBudgetRule:
    section: str
    clause_text: str
    deadline_month: int
    deadline_day: int
    rule_sha256: str

    def as_dict(self) -> dict:
        return asdict(self)

def html_to_text(body: bytes | str) -> str:
    raw=body.decode("utf-8",errors="replace") if isinstance(body,bytes) else body
    parser=_TextExtractor()
    parser.feed(raw)
    return re.sub(r"\s+"," "," ".join(parser.parts)).strip()

def parse_kenya_budget_policy_rule(body: bytes | str) -> KenyaBudgetRule:
    text=html_to_text(body)
    if "public finance management act" not in text.lower():
        raise AdapterError("Kenya Law response did not identify the Public Finance Management Act")
    pattern=re.compile(
        r"The National Treasury shall submit the Budget Policy Statement approved in terms of subsection\s*\(1\)\s*to Parliament,?\s*by the\s*15(?:th|\^\{th\})?\s*February in each year\.?",
        re.IGNORECASE,
    )
    match=pattern.search(text)
    if not match:
        raise AdapterError("Kenya PFM Act section 25(2) Budget Policy Statement deadline clause not found")
    clause=re.sub(r"\s+"," ",match.group(0)).strip()
    normalized=re.sub(r"[^a-z0-9]+"," ",clause.lower()).strip()
    return KenyaBudgetRule(
        section="25(2)",
        clause_text=clause,
        deadline_month=2,
        deadline_day=15,
        rule_sha256=sha256(normalized.encode("utf-8")).hexdigest(),
    )

def _fetch_rule(url: str, *, timeout: int = 30) -> tuple[KenyaBudgetRule, FetchSnapshot]:
    body,snapshot=fetch_bytes(
        url,
        timeout=timeout,
        accept="text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
    )
    return parse_kenya_budget_policy_rule(body),snapshot

def fetch_kenya_budget_policy_rule_baseline(*, timeout: int = 30) -> tuple[KenyaBudgetRule, FetchSnapshot]:
    """Fetch the frozen 4 Nov 2025 version for reproducible provenance tests."""
    return _fetch_rule(KENYA_PFM_BASELINE_2025_11_04,timeout=timeout)

def fetch_kenya_budget_policy_rule_current(*, timeout: int = 30) -> tuple[KenyaBudgetRule, FetchSnapshot]:
    """Probe the unversioned current route without implying production clearance.

    GitHub Actions returned HTTP 403 on 3 Sep 2026, while the bounded BN
    readiness probe on 8 Sep 2026 returned HTTP 200 and the same semantic
    section 25(2) rule as the frozen versioned route. Reachability is runtime
    evidence only: callers must never treat success or failure as automated
    retrieval permission, legal-rule change, or event-state change.
    """
    return _fetch_rule(KENYA_PFM_CURRENT,timeout=timeout)
