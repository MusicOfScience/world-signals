"""Read-only official-source adapters for WORLD SIGNALS.

Adapters may fetch and parse authoritative sources. They do not mutate canonical data.
"""

from .base import AdapterError, FetchSnapshot
from .rba_fsr import RBA_FSR_RSS, fetch_rba_fsr, parse_rba_fsr_rss
from .socrata import SUIN_DATASET_ID, fetch_suin_metadata, parse_socrata_metadata

__all__ = [
    "AdapterError",
    "FetchSnapshot",
    "RBA_FSR_RSS",
    "SUIN_DATASET_ID",
    "fetch_rba_fsr",
    "fetch_suin_metadata",
    "parse_rba_fsr_rss",
    "parse_socrata_metadata",
]
