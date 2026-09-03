from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date
from hashlib import sha256
from html.parser import HTMLParser
import re

from .base import AdapterError, FetchSnapshot, fetch_bytes

CELLAR_CELEX_BASE = "https://publications.europa.eu/resource/celex"
CRA_CELEX = "32024R2847"
MONTHS={
    "january":1,"february":2,"march":3,"april":4,"may":5,"june":6,
    "july":7,"august":8,"september":9,"october":10,"november":11,"december":12,
}
DATE_PATTERN=r"(?P<day>\d{1,2})\s+(?P<month>January|February|March|April|May|June|July|August|September|October|November|December)\s+(?P<year>\d{4})"


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


def _match_to_iso(match: re.Match[str]) -> str:
    try:
        value=date(
            int(match.group("year")),
            MONTHS[match.group("month").lower()],
            int(match.group("day")),
        )
    except (KeyError,ValueError) as exc:
        raise AdapterError(f"invalid legal application date in CRA Article 71: {match.group(0)!r}") from exc
    return value.isoformat()


def _article_71_window(text: str) -> str:
    candidates=[]
    for match in re.finditer(r"\bArticle\s+71\b",text,re.IGNORECASE):
        window=text[match.start():match.start()+5000]
        lower=window.lower()
        if "article 14" in lower and "chapter iv" in lower and "shall apply from" in lower:
            candidates.append(window)
    if not candidates:
        raise AdapterError("CRA operative Article 71 block was not found")
    # A table of contents can contain the same article label; the operative block
    # is normally the final candidate containing all three application clauses.
    return candidates[-1]


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

    block=_article_71_window(text)
    general=re.search(
        rf"(?:It|This\s+Regulation)\s+shall\s+apply\s+from\s+{DATE_PATTERN}",
        block,re.IGNORECASE,
    )
    if general is None:
        # Representation wording can omit the pronoun. Select an unlabeled
        # application clause only when it is not the Article 14 or Chapter IV clause.
        for match in re.finditer(rf"shall\s+apply\s+from\s+{DATE_PATTERN}",block,re.IGNORECASE):
            prefix=block[max(0,match.start()-90):match.start()].lower()
            if "article 14" not in prefix and "chapter iv" not in prefix:
                general=match
                break

    article14=re.search(
        rf"Article\s+14\s+shall\s+apply\s+from\s+{DATE_PATTERN}",
        block,re.IGNORECASE,
    )
    chapter4=re.search(
        rf"Chapter\s+IV(?:\s*\([^)]*\))?\s+shall\s+apply\s+from\s+{DATE_PATTERN}",
        block,re.IGNORECASE,
    )
    if not all((general,article14,chapter4)):
        raise AdapterError("CRA Article 71 application-date clauses were not parsed completely")

    general_iso=_match_to_iso(general)
    article14_iso=_match_to_iso(article14)
    chapter4_iso=_match_to_iso(chapter4)
    semantic="|".join([
        str(celex),
        "ARTICLE_71",
        f"GENERAL={general_iso}",
        f"ARTICLE_14={article14_iso}",
        f"CHAPTER_IV={chapter4_iso}",
    ])
    return CRAApplicationRule(
        celex=str(celex),
        article="71",
        general_application_date=general_iso,
        article_14_application_date=article14_iso,
        chapter_iv_application_date=chapter4_iso,
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
