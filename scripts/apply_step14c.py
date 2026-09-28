#!/usr/bin/env python3
"""Explicit Step 14C admission command.

Both timestamps are required. Without ``--apply`` this command only builds
and validates the selected transaction in memory. There is no wall-clock
default and no automatic polling or retry path.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.world_state_step14c import (  # noqa: E402
    Step14CError,
    build_climate_transaction,
    build_source_canonical_transaction,
    materialize_step14c,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight or explicitly apply the separate Step 14C admissions.")
    parser.add_argument("--reviewed-at-utc", required=True)
    parser.add_argument("--admitted-at-utc", required=True)
    parser.add_argument("--transaction", choices=("climate", "sources-canonical", "both"), default="both")
    parser.add_argument("--apply", action="store_true", help="materialise the explicitly selected transaction(s)")
    args = parser.parse_args()
    climate = args.transaction in {"climate", "both"}
    sources_and_canonical = args.transaction in {"sources-canonical", "both"}
    try:
        if args.apply:
            result = materialize_step14c(
                ROOT,
                reviewed_at_utc=args.reviewed_at_utc,
                admitted_at_utc=args.admitted_at_utc,
                climate=climate,
                sources_and_canonical=sources_and_canonical,
            )
        else:
            result = {}
            if climate:
                result["climate"] = build_climate_transaction(ROOT, reviewed_at_utc=args.reviewed_at_utc, admitted_at_utc=args.admitted_at_utc)["transaction"]
            if sources_and_canonical:
                result["sources_and_canonical"] = build_source_canonical_transaction(ROOT, reviewed_at_utc=args.reviewed_at_utc, admitted_at_utc=args.admitted_at_utc)["transaction"]
        print(json.dumps({"mode": "APPLY" if args.apply else "PREFLIGHT_ONLY", "transactions": result}, indent=2, sort_keys=True))
        return 0
    except Step14CError as exc:
        print(f"STEP14C FAILED CLOSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
