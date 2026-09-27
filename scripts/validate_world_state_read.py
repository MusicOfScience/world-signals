#!/usr/bin/env python3
"""Exercise the private, read-only World State v1 adapter.

The command requires an explicit UTC cutoff and prints only a summary unless
``--full`` is requested.  It never writes a proposal or any repository state.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.world_state_read import (  # noqa: E402
    WORLD_STATE_DIMENSIONS,
    WorldStateReadError,
    proposal_summary,
    read_world_state,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", required=True, help="explicit exact UTC cutoff, for example 2026-09-27T23:59:59Z")
    parser.add_argument("--jurisdiction", action="append", dest="jurisdictions", default=None, help="repeatable jurisdiction; defaults to explicit wildcard scope")
    parser.add_argument("--dimension", action="append", dest="dimensions", choices=sorted(WORLD_STATE_DIMENSIONS), help="repeatable World State dimension; defaults to all controlled vocabulary dimensions")
    parser.add_argument("--actor-id", action="append", dest="actor_ids", default=None, help="optional repeatable proposal-local actor reference")
    parser.add_argument("--exclude-negative-evidence", action="store_true", help="exclude any future governed negative-evidence selection; absence is never promoted by this adapter")
    parser.add_argument("--full", action="store_true", help="print the complete ephemeral proposal instead of the concise summary")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    request = {
        "contract_version": "0.1",
        "as_of_utc": args.as_of,
        "scope": {
            "jurisdictions": args.jurisdictions or ["*"],
            "dimensions": args.dimensions or sorted(WORLD_STATE_DIMENSIONS),
            "actor_ids": args.actor_ids,
        },
        "include_negative_evidence": not args.exclude_negative_evidence,
        "input_policy": "ACCEPTED_REVIEWED_HEADS_ONLY",
    }
    try:
        proposal = read_world_state(request)
    except (WorldStateReadError, OSError, json.JSONDecodeError) as exc:
        print(f"World State read validation FAILED: {exc}", file=sys.stderr)
        return 1
    output = proposal if args.full else proposal_summary(proposal)
    print(json.dumps(output, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
