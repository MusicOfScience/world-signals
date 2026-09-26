#!/usr/bin/env python3
"""Run one bounded local OSINT candidate-generation pass."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.osint_engine import load_json, run_once  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="run one bounded pass; this is the only supported mode")
    parser.add_argument("--runtime-dir", type=Path, default=ROOT / ".world-signals-runtime/osint")
    args = parser.parse_args()
    if not args.once:
        parser.error("OSINT v1 has no implicit daemon; pass --once from a local scheduler")
    run = run_once(load_json(ROOT / "data/sources/registry.json"), load_json(ROOT / "data/osint/source_cohort.json"),
                   runtime_dir=args.runtime_dir)
    successes = sum(item.result_state == "SUCCESS" for item in run.retrievals)
    unchanged = sum(item.result_state == "NO_NEW_INFORMATION" for item in run.retrievals)
    failures = len(run.retrievals) - successes - unchanged
    print(json.dumps({
        "run_id": run.run_id,
        "routes_attempted": len(run.routes_attempted),
        "successful_routes": successes,
        "unchanged_routes": unchanged,
        "retrieval_failures": failures,
        "observation_candidates": len(run.observation_candidates),
        "duplicates": run.duplicate_count,
        "story_clusters": len(run.story_clusters),
        "signal_candidates": len(run.signal_candidates),
        "runtime_output": str(args.runtime_dir / "latest.json"),
        "promotion": "CLOSED",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
