from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date
from hashlib import sha256
import re

from .base import AdapterError, FetchSnapshot
from .cellar import cellar_document_text, fetch_cellar_celex_document

CBAM_VERIFICATION_CELEX = "32025R2551"
CBAM_CERTIFICATE_SALE_AMENDING_CELEX = "32025R2083"
CBAM_PARENT_CELEX = "32023R0956"

_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}
_DATE_PATTERN = (
    r"(?P<day>\d{1,2})\s+"
    r"(?P<month>January|February|March|April|May|June|July|August|September|October|November|December)\s+"
    r"(?P<year>\d{4})"
)
_RECURRING_DEADLINE_HEAD = (
    r"By\s+(?P<day>\d{1,2})\s+"
    r"(?P<month>January|February|March|April|May|June|July|August|September|October|November|December)\s+"
    r"of\s+each\s+year\s*,?\s*and\s+for\s+the\s+first\s+time\s+in\s+"
    r"(?P<first_due_year>\d{4})\s+for\s+the\s+year\s+(?P<first_reference_year>\d{4})\s*,?\s*"
)


@dataclass(frozen=True)
class CBAMMilestoneRule:
    celex: str
    rule_id: str
    legal_locator: str
    milestone_date: str
    rule_sha256: str

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class CBAMAnnualDeadlineRule:
    celex: str
    rule_id: str
    declaration_legal_locator: str
    surrender_legal_locator: str
    declaration_month_day: str
    surrender_month_day: str
    declaration_first_due_year: int
    surrender_first_due_year: int
    declaration_first_reference_year: int
    surrender_first_reference_year: int
    first_deadline_date: str | None
    shared_deadline_consistent: bool
    rule_sha256: str

    def as_dict(self) -> dict:
        return asdict(self)


def _to_iso(match: re.Match[str]) -> str:
    try:
        value = date(
            int(match.group("year")),
            _MONTHS[match.group("month").lower()],
            int(match.group("day")),
        )
    except (KeyError, ValueError) as exc:
        raise AdapterError(f"invalid CBAM legal milestone date: {match.group(0)!r}") from exc
    return value.isoformat()


def _month_day(match: re.Match[str]) -> str:
    try:
        month=_MONTHS[match.group("month").lower()]
        day=int(match.group("day"))
        date(2000,month,day)
    except (KeyError, ValueError) as exc:
        raise AdapterError(f"invalid CBAM recurring deadline: {match.group(0)!r}") from exc
    return f"{month:02d}-{day:02d}"


def _rule(
    *,
    celex: str,
    rule_id: str,
    legal_locator: str,
    milestone_date: str,
) -> CBAMMilestoneRule:
    semantic = "|".join(
        [
            str(celex).upper(),
            rule_id,
            legal_locator,
            "DATE=" + milestone_date,
        ]
    )
    return CBAMMilestoneRule(
        celex=str(celex).upper(),
        rule_id=rule_id,
        legal_locator=legal_locator,
        milestone_date=milestone_date,
        rule_sha256=sha256(semantic.encode("utf-8")).hexdigest(),
    )


def parse_cbam_verification_report_rule(
    body: bytes | str,
    *,
    celex: str = CBAM_VERIFICATION_CELEX,
) -> CBAMMilestoneRule:
    """Parse the first CBAM-registry verification-report issuance date."""
    text = cellar_document_text(body)
    lower = text.lower()
    if "verification report" not in lower or "cbam registry" not in lower:
        raise AdapterError(
            "CBAM verification legal text did not identify verification reports in the CBAM registry"
        )

    match = re.search(
        rf"From\s+{_DATE_PATTERN}\s*,?\s*the\s+verifier\s+shall\s+issue\s+"
        r"the\s+verification\s+report\s+in\s+the\s+CBAM\s+registry",
        text,
        re.IGNORECASE,
    )
    if match is None:
        raise AdapterError("CBAM verifier-report start-date clause was not parsed")

    return _rule(
        celex=celex,
        rule_id="VERIFICATION_REPORT_REGISTRY_START",
        legal_locator="Section 2.17.3",
        milestone_date=_to_iso(match),
    )


def parse_cbam_certificate_sale_rule(
    body: bytes | str,
    *,
    celex: str = CBAM_CERTIFICATE_SALE_AMENDING_CELEX,
) -> CBAMMilestoneRule:
    """Parse the first date on which Member States shall sell CBAM certificates."""
    text = cellar_document_text(body)
    lower = text.lower()
    if "cbam certificates" not in lower or "article 20" not in lower:
        raise AdapterError(
            "CBAM certificate-sale legal text did not identify Article 20 and CBAM certificates"
        )

    match = re.search(
        rf"From\s+{_DATE_PATTERN}\s*,?\s*a\s+Member\s+State\s+shall\s+sell\s+"
        r"CBAM\s+certificates\s+on\s+a\s+common\s+central\s+platform",
        text,
        re.IGNORECASE,
    )
    if match is None:
        raise AdapterError("CBAM Article 20(1) certificate-sale start-date clause was not parsed")

    return _rule(
        celex=celex,
        rule_id="CERTIFICATE_SALE_START",
        legal_locator="Article 20(1) replacement",
        milestone_date=_to_iso(match),
    )


def parse_cbam_annual_declaration_surrender_rule(
    body: bytes | str,
    *,
    celex: str = CBAM_CERTIFICATE_SALE_AMENDING_CELEX,
) -> CBAMAnnualDeadlineRule:
    """Parse the paired annual declaration and certificate-surrender deadlines.

    Regulation (EU) 2025/2083 replaced both Article 6(1) and Article 22(1) of
    the parent CBAM Regulation. The clauses are parsed independently. Their
    agreement is retained as data rather than assumed: a future divergence is
    legal review evidence and must not silently split or mutate the existing
    canonical occurrence.
    """
    text=cellar_document_text(body)
    lower=text.lower()
    if "article 6" not in lower or "article 22" not in lower:
        raise AdapterError("CBAM annual-deadline legal text did not identify Articles 6 and 22")

    declaration=re.search(
        _RECURRING_DEADLINE_HEAD
        + r"each\s+authorised\s+CBAM\s+declarant\s+shall\s+use\s+the\s+CBAM\s+registry"
        + r".*?to\s+submit\s+a\s+CBAM\s+declaration",
        text,
        re.IGNORECASE,
    )
    if declaration is None:
        raise AdapterError("CBAM Article 6(1) annual declaration deadline was not parsed")

    surrender=re.search(
        _RECURRING_DEADLINE_HEAD
        + r"the\s+authorised\s+CBAM\s+declarant\s+shall\s+surrender\s+via\s+the\s+CBAM\s+registry",
        text,
        re.IGNORECASE,
    )
    if surrender is None:
        raise AdapterError("CBAM Article 22(1) annual certificate-surrender deadline was not parsed")

    declaration_month_day=_month_day(declaration)
    surrender_month_day=_month_day(surrender)
    declaration_due=int(declaration.group("first_due_year"))
    surrender_due=int(surrender.group("first_due_year"))
    declaration_reference=int(declaration.group("first_reference_year"))
    surrender_reference=int(surrender.group("first_reference_year"))

    consistent=(
        declaration_month_day == surrender_month_day
        and declaration_due == surrender_due
        and declaration_reference == surrender_reference
    )
    first_deadline=(
        f"{declaration_due:04d}-{declaration_month_day}" if consistent else None
    )
    semantic="|".join([
        str(celex).upper(),
        "ANNUAL_DECLARATION_AND_SURRENDER_DEADLINE",
        "ARTICLE_6_1="+declaration_month_day,
        "ARTICLE_6_1_FIRST_DUE_YEAR="+str(declaration_due),
        "ARTICLE_6_1_FIRST_REFERENCE_YEAR="+str(declaration_reference),
        "ARTICLE_22_1="+surrender_month_day,
        "ARTICLE_22_1_FIRST_DUE_YEAR="+str(surrender_due),
        "ARTICLE_22_1_FIRST_REFERENCE_YEAR="+str(surrender_reference),
        "CONSISTENT="+str(consistent).lower(),
    ])

    return CBAMAnnualDeadlineRule(
        celex=str(celex).upper(),
        rule_id="ANNUAL_DECLARATION_AND_SURRENDER_DEADLINE",
        declaration_legal_locator="Article 6(1) replacement",
        surrender_legal_locator="Article 22(1) replacement",
        declaration_month_day=declaration_month_day,
        surrender_month_day=surrender_month_day,
        declaration_first_due_year=declaration_due,
        surrender_first_due_year=surrender_due,
        declaration_first_reference_year=declaration_reference,
        surrender_first_reference_year=surrender_reference,
        first_deadline_date=first_deadline,
        shared_deadline_consistent=consistent,
        rule_sha256=sha256(semantic.encode("utf-8")).hexdigest(),
    )


def fetch_cbam_verification_report_rule(
    *, timeout: int = 30
) -> tuple[CBAMMilestoneRule, FetchSnapshot]:
    body, snapshot = fetch_cellar_celex_document(
        CBAM_VERIFICATION_CELEX,
        timeout=timeout,
        language="eng",
    )
    return parse_cbam_verification_report_rule(body), snapshot


def fetch_cbam_certificate_sale_rule(
    *, timeout: int = 30
) -> tuple[CBAMMilestoneRule, FetchSnapshot]:
    body, snapshot = fetch_cellar_celex_document(
        CBAM_CERTIFICATE_SALE_AMENDING_CELEX,
        timeout=timeout,
        language="eng",
    )
    return parse_cbam_certificate_sale_rule(body), snapshot


def fetch_cbam_annual_declaration_surrender_rule(
    *, timeout: int = 30
) -> tuple[CBAMAnnualDeadlineRule, FetchSnapshot]:
    body, snapshot = fetch_cellar_celex_document(
        CBAM_CERTIFICATE_SALE_AMENDING_CELEX,
        timeout=timeout,
        language="eng",
    )
    return parse_cbam_annual_declaration_surrender_rule(body), snapshot
