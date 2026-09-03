from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
from html.parser import HTMLParser
import re

from .base import AdapterError, FetchSnapshot, fetch_bytes

CELLAR_CELEX_BASE = "https://publications.europa.eu/resource/celex"
CRA_CELEX = "32024R2847"


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
class CRAApplicationRule:
    celex: str
    article: str
    general_application_date: str
    article_14_application_date: str
    chapter_iv_application_date: str
    rule_sha256: str

    def as_dict(self) -> dict:
        return asdict(self)


def cellar_celex_url(celex: str) -> str:
    token=str(celex).strip()
    if not re.fullmatch(r"[0-9A-Z()_-]+",token):
        raise AdapterError(f"invalid CELEX identifier: {celex!r}")
    return f"{CELLAR_CELEX_BASE}/{token}"


def _to_text(body: bytes | str) -> str:
    raw=body.decode("utf-8",errors="replace") if isinstance(body,bytes) else body
    parser=_TextExtractor()
    parser.feed(raw)
    text=" ".join(parser.parts)
    return re.sub(r"\s+"," ",text).strip()


def cellar_representation_diagnostics(body: bytes | str) -> dict:
    text=_to_text(body)
    lower=text.lower()
    return {
        "text_chars":len(text),
        "identifies_cra":(
            "cyber resilience act" in lower
            or "cybersecurity requirements for products with digital elements" in lower
        ),
        "contains_article_71":"article 71" in lower,
        "contains_11_december_2027":"11 december 2027" in lower,
        "contains_11_september_2026":"11 september 2026" in lower,
        "contains_11_june_2026":"11 june 2026" in lower,
        "contains_article_14":"article 14" in lower,
        "contains_chapter_iv":"chapter iv" in lower,
    }


def parse_cra_article_71(body: bytes | str, *, celex: str = CRA_CELEX) -> CRAApplicationRule:
    text=_to_text(body)
    lower=text.lower()
    if "cyber resilience act" not in lower and "cybersecurity requirements for products with digital elements" not in lower:
        raise AdapterError("Cellar response did not identify the Cyber Resilience Act")

    # Match the semantic rule, tolerating punctuation and markup-induced wording
    # between the operative labels and their dates. The dates themselves remain
    # exact legal assertions and are never inferred from recurrence.
    general=re.search(r"shall\s+apply\s+from.{0,80}?11\s+December\s+2027",text,re.IGNORECASE)
    article14=re.search(r"Article\s+14.{0,120}?11\s+September\s+2026",text,re.IGNORECASE)
    chapter4=re.search(r"Chapter\s+IV.{0,180}?11\s+June\s+2026",text,re.IGNORECASE)
    if not all((general,article14,chapter4)):
        raise AdapterError("CRA Article 71 application-date rule was not found intact")

    semantic="|".join([
        str(celex),
        "ARTICLE_71",
        "GENERAL=2027-12-11",
        "ARTICLE_14=2026-09-11",
        "CHAPTER_IV=2026-06-11",
    ])
    return CRAApplicationRule(
        celex=str(celex),
        article="71",
        general_application_date="2027-12-11",
        article_14_application_date="2026-09-11",
        chapter_iv_application_date="2026-06-11",
        rule_sha256=sha256(semantic.encode("utf-8")).hexdigest(),
    )


def fetch_cellar_celex_document(
    celex: str,
    *,
    timeout: int = 30,
    language: str = "eng",
) -> tuple[bytes, FetchSnapshot]:
    return fetch_bytes(
        cellar_celex_url(celex),
        timeout=timeout,
        accept="application/xhtml+xml,text/html;q=0.9,application/xml;q=0.8,*/*;q=0.1",
        headers={"Accept-Language":language},
    )


def fetch_cra_article_71(*, timeout: int = 30) -> tuple[CRAApplicationRule, FetchSnapshot]:
    body,snapshot=fetch_cellar_celex_document(CRA_CELEX,timeout=timeout,language="eng")
    return parse_cra_article_71(body),snapshot
