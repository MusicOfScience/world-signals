#!/usr/bin/env python3
"""Read admitted World State history without writing production state."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.world_state_history import DIMENSIONS  # noqa: E402
from world_signals.world_state_production import (  # noqa: E402
    WorldStateProductionReadError,
    compare_production_world_state,
    read_production_world_state,
    successor_preflight,
)


def _request(args: argparse.Namespace, knowledge_cutoff: str, effective_as_of: str | None) -> dict:
    return {
        "query_mode": "EFFECTIVE_AS_OF" if effective_as_of else "KNOWLEDGE_AS_OF",
        "knowledge_cutoff_utc": knowledge_cutoff,
        "effective_as_of_utc": effective_as_of,
        "scope": {
            "jurisdictions": args.jurisdiction or [],
            "dimensions": args.dimension or [],
            "systems": args.system or [],
            "component_ids": args.component_id or [],
        },
        "include_withdrawn_history": args.include_withdrawn,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--knowledge-cutoff", required=True, help="explicit exact UTC knowledge cutoff")
    parser.add_argument("--effective-as-of", help="explicit exact UTC effective view; selects EFFECTIVE_AS_OF")
    parser.add_argument("--compare-from-knowledge-cutoff", help="optional earlier knowledge cutoff for a deterministic delta")
    parser.add_argument("--compare-from-effective-as-of", help="optional earlier effective cutoff for a deterministic delta")
    parser.add_argument("--jurisdiction", action="append", help="repeatable jurisdiction scope")
    parser.add_argument("--dimension", action="append", choices=sorted(DIMENSIONS), help="repeatable dimension scope")
    parser.add_argument("--system", action="append", help="repeatable system scope")
    parser.add_argument("--component-id", action="append", help="repeatable component identity scope")
    parser.add_argument("--include-withdrawn", action="store_true")
    parser.add_argument("--successor-preflight", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        current = read_production_world_state(_request(args, args.knowledge_cutoff, args.effective_as_of))
        result = {"production_world_state": current}
        if args.compare_from_knowledge_cutoff or args.compare_from_effective_as_of:
            previous = read_production_world_state(_request(args, args.compare_from_knowledge_cutoff or args.knowledge_cutoff, args.compare_from_effective_as_of))
            result["delta"] = compare_production_world_state(previous, current)
        if args.successor_preflight:
            result["successor_preflight"] = successor_preflight(current)
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
        return 0
    except (WorldStateProductionReadError, OSError, json.JSONDecodeError) as exc:
        print(f"World State production read FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
