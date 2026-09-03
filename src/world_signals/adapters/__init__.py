"""Read-only official-source adapters for WORLD SIGNALS.

Adapters may fetch and parse authoritative sources. They do not mutate canonical data.
"""

from .base import AdapterError, FetchSnapshot
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
    "FetchSnapshot",
    "KENYA_PFM_BASELINE_2025_11_04",
    "KENYA_PFM_CURRENT",
    "RBA_FSR_RSS",
    "SUIN_DATASET_ID",
    "fetch_kenya_budget_policy_rule_baseline",
    "fetch_kenya_budget_policy_rule_current",
    "fetch_rba_fsr",
    "fetch_suin_metadata",
    "fetch_suin_rows",
    "parse_kenya_budget_policy_rule",
    "parse_rba_fsr_rss",
    "parse_socrata_metadata",
    "parse_socrata_rows",
    "resource_url",
]
