"""Read-only official-source adapters for WORLD SIGNALS.

Adapters may fetch and parse authoritative sources. They do not mutate canonical data.
"""

from .base import AdapterError, FetchSnapshot
from .cellar import (
    CELLAR_CELEX_BASE,
    ELI_IDENTIFIER_BASE,
    EURLEX_ELI_FETCH_BASE,
    CRA_CELEX,
    CRA_ELI_CURRENT,
    ELILegalState,
    cellar_celex_url,
    eli_current_url,
    eli_current_fetch_url,
    cellar_document_text,
    cellar_representation_diagnostics,
    fetch_cellar_celex_document,
    fetch_eli_current_document,
    fetch_cra_article_71,
    parse_cra_article_71,
    parse_eli_current_state,
)
from .cellar_metadata import (
    fetch_cellar_identifier_notice,
    fetch_cellar_rdf_notice,
    parse_cellar_identifier_notice,
    parse_cellar_legal_relation_diagnostics,
)
from .kenya_law import (
    KENYA_PFM_BASELINE_2025_11_04,
    KENYA_PFM_CURRENT,
    fetch_kenya_budget_policy_rule_baseline,
    fetch_kenya_budget_policy_rule_current,
    parse_kenya_budget_policy_rule,
)
from .rba_fsr import RBA_FSR_RSS, fetch_rba_fsr, parse_rba_fsr_rss
from .socrata import (
    SUIN_DATASET_ID,
    fetch_suin_metadata,
    fetch_suin_rows,
    parse_socrata_metadata,
    parse_socrata_rows,
    resource_url,
)

__all__ = [
    "AdapterError",
    "CELLAR_CELEX_BASE",
    "ELI_IDENTIFIER_BASE",
    "EURLEX_ELI_FETCH_BASE",
    "CRA_CELEX",
    "CRA_ELI_CURRENT",
    "ELILegalState",
    "FetchSnapshot",
    "KENYA_PFM_BASELINE_2025_11_04",
    "KENYA_PFM_CURRENT",
    "RBA_FSR_RSS",
    "SUIN_DATASET_ID",
    "cellar_celex_url",
    "eli_current_url",
    "eli_current_fetch_url",
    "cellar_document_text",
    "cellar_representation_diagnostics",
    "fetch_cellar_celex_document",
    "fetch_cellar_identifier_notice",
    "fetch_cellar_rdf_notice",
    "fetch_eli_current_document",
    "fetch_cra_article_71",
    "fetch_kenya_budget_policy_rule_baseline",
    "fetch_kenya_budget_policy_rule_current",
    "fetch_rba_fsr",
    "fetch_suin_metadata",
    "fetch_suin_rows",
    "parse_cra_article_71",
    "parse_cellar_identifier_notice",
    "parse_cellar_legal_relation_diagnostics",
    "parse_eli_current_state",
    "parse_kenya_budget_policy_rule",
    "parse_rba_fsr_rss",
    "parse_socrata_metadata",
    "parse_socrata_rows",
    "resource_url",
]
