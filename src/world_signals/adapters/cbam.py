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


@dataclass(frozen=True)
class CBAMMilestoneRule:
    celex: str
    rule_id: str
    legal_locator: str
    milestone_date: str
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
    """Parse the first CBAM-registry verification-report issuance date.

    The semantic baseline is the immutable text of Commission Delegated
    Regulation (EU) 2025/2551. A later amendment is detected separately through
    Cellar legal-topology monitoring; this parser does not treat transport or
    document hashes as legal change.
    """
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
    """Parse the first date on which Member States shall sell CBAM certificates.

    The immutable semantic baseline is Regulation (EU) 2025/2083, which replaces
    Article 20(1) of Regulation (EU) 2023/956. Current-law amendment discovery
    must therefore monitor the parent act (CELEX 32023R0956) separately.
    """
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
