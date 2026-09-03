from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date
from hashlib import sha256
from html.parser import HTMLParser
import re

from .base import AdapterError, FetchSnapshot, fetch_bytes

CELLAR_CELEX_BASE = "https://publications.europa.eu/resource/celex"
ELI_IDENTIFIER_BASE = "https://data.europa.eu/eli"
EURLEX_ELI_FETCH_BASE = "https://eur-lex.europa.eu/eli"
CRA_CELEX = "32024R2847"
CRA_ELI_CURRENT = "https://data.europa.eu/eli/reg/2024/2847"
MONTHS={
    "january":1,"february":2,"march":3,"april":4,"may":5,"june":6,
    "july":7,"august":8,"september":9,"october":10,"november":11,"december":12,
}
DATE_PATTERN=r"(?P<day>\d{1,2})\s+(?P<month>January|February|March|April|May|June|July|August|September|October|November|December)\s+(?P<year>\d{4})"
CELEX_PATTERN=r"(?:0\d{4}[A-Z]\d{4}-\d{8}|3\d{4}[A-Z]\d{4})"


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


@dataclass(frozen=True)
class ELILegalState:
    base_celex: str
    mode: str
    consolidation_celex_ids: tuple[str,...]
    modifier_celex_ids: tuple[str,...]
    state_sha256: str

    def as_dict(self) -> dict:
        data=asdict(self)
        data["consolidation_celex_ids"]=list(self.consolidation_celex_ids)
        data["modifier_celex_ids"]=list(self.modifier_celex_ids)
        return data


def cellar_celex_url(celex: str) -> str:
    token=str(celex).strip()
    if not re.fullmatch(r"[0-9A-Z()_-]+",token):
        raise AdapterError(f"invalid CELEX identifier: {celex!r}")
    return f"{CELLAR_CELEX_BASE}/{token}"


def _validate_eli_identity(typedoc: str, year: int | str, number: int | str) -> tuple[str,str,str]:
    doc=str(typedoc).strip().lower()
    if doc not in {"reg","reg_del","reg_impl","dir","dir_del","dir_impl","dec","dec_del","dec_impl"}:
        raise AdapterError(f"unsupported ELI document type: {typedoc!r}")
    year_s=str(year).strip()
    number_s=str(number).strip()
    if not re.fullmatch(r"\d{4}",year_s) or not re.fullmatch(r"\d+",number_s):
        raise AdapterError(f"invalid ELI identity: {typedoc!r}/{year!r}/{number!r}")
    return doc,year_s,number_s


def eli_current_url(typedoc: str, year: int | str, number: int | str) -> str:
    """Canonical unversioned ELI identifier."""
    doc,year_s,number_s=_validate_eli_identity(typedoc,year,number)
    return f"{ELI_IDENTIFIER_BASE}/{doc}/{year_s}/{number_s}"


def eli_current_fetch_url(typedoc: str, year: int | str, number: int | str) -> str:
    """Direct EUR-Lex operational route implementing the unversioned ELI."""
    doc,year_s,number_s=_validate_eli_identity(typedoc,year,number)
    return f"{EURLEX_ELI_FETCH_BASE}/{doc}/{year_s}/{number_s}"


def cellar_document_text(body: bytes | str) -> str:
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
        raise AdapterError(f"invalid legal application date: {match.group(0)!r}") from exc
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
    return candidates[-1]


def cellar_representation_diagnostics(body: bytes | str) -> dict:
    text=cellar_document_text(body)
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
        "looks_like_result_list":"search results" in lower and "search criteria" in lower,
    }


def parse_cra_article_71(body: bytes | str, *, celex: str = CRA_CELEX) -> CRAApplicationRule:
    text=cellar_document_text(body)
    lower=text.lower()
    if "cyber resilience act" not in lower and "cybersecurity requirements for products with digital elements" not in lower:
        raise AdapterError("EU legal-state response did not identify the Cyber Resilience Act")

    block=_article_71_window(text)
    general=re.search(
        rf"(?:It|This\s+Regulation)\s+shall\s+apply\s+from\s+{DATE_PATTERN}",
        block,re.IGNORECASE,
    )
    if general is None:
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


def parse_eli_current_state(body: bytes | str, *, base_celex: str) -> ELILegalState:
    """Parse the current-law topology returned by an unversioned EUR-Lex ELI.

    The ELI can resolve either to a current consolidated document or to a
    search-results page containing the latest consolidation plus amendments
    that have not yet been consolidated. This parser records that topology;
    it does not infer whether a modifier changes a particular canonical date.
    """
    base=str(base_celex).strip().upper()
    if not re.fullmatch(r"3\d{4}[A-Z]\d{4}",base):
        raise AdapterError(f"unsupported base CELEX for ELI topology: {base_celex!r}")
    text=cellar_document_text(body)
    if not text:
        raise AdapterError("EUR-Lex current ELI returned no readable document text")
    lower=text.lower()
    is_results="search results" in lower and "search criteria" in lower

    if is_results:
        ids=re.findall(rf"CELEX\s+number:\s*({CELEX_PATTERN})",text,re.IGNORECASE)
        if not ids:
            ids=re.findall(rf"\b({CELEX_PATTERN})\b",text)
        mode="RESULT_LIST_WITH_UNCONSOLIDATED_MODIFIERS"
    else:
        match=re.search(rf"\bDocument\s+({CELEX_PATTERN})\b",text,re.IGNORECASE)
        ids=[match.group(1)] if match else []
        mode="CURRENT_DOCUMENT"

    seen=[]
    for item in ids:
        token=item.upper()
        if token not in seen:
            seen.append(token)

    core=base[1:]
    consolidations=tuple(x for x in seen if x.startswith("0"+core+"-"))
    if is_results:
        modifiers=tuple(x for x in seen if x.startswith("3") and x != base)
    else:
        modifiers=tuple()

    base_document_present=base in seen
    if not consolidations and not base_document_present:
        raise AdapterError(
            f"EUR-Lex current ELI did not expose the base act or a matching consolidation for {base}"
        )

    semantic="|".join([
        base,
        mode,
        "CONSOLIDATIONS="+",".join(sorted(consolidations)),
        "MODIFIERS="+",".join(sorted(modifiers)),
        f"BASE_PRESENT={str(base_document_present).lower()}",
    ])
    return ELILegalState(
        base_celex=base,
        mode=mode,
        consolidation_celex_ids=tuple(sorted(consolidations)),
        modifier_celex_ids=tuple(sorted(modifiers)),
        state_sha256=sha256(semantic.encode("utf-8")).hexdigest(),
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


def fetch_eli_current_document(
    typedoc: str,
    year: int | str,
    number: int | str,
    *,
    timeout: int = 30,
    language: str = "en",
) -> tuple[bytes, FetchSnapshot]:
    """Fetch the current-law EUR-Lex page implementing an unversioned ELI."""
    body,snapshot=fetch_bytes(
        eli_current_fetch_url(typedoc,year,number),
        timeout=timeout,
        accept="text/html,application/xhtml+xml;q=0.9,application/xml;q=0.8,*/*;q=0.1",
        headers={"Accept-Language":language},
    )
    if snapshot.status == 202:
        raise AdapterError(
            f"EUR-Lex current ELI returned HTTP 202 asynchronous placeholder for {snapshot.url}"
        )
    return body,snapshot


def fetch_cra_article_71(*, timeout: int = 30) -> tuple[CRAApplicationRule, FetchSnapshot]:
    """Fetch immutable CRA enactment text for the Article 71 semantic baseline."""
    body,snapshot=fetch_cellar_celex_document(CRA_CELEX,timeout=timeout,language="eng")
    return parse_cra_article_71(body),snapshot
