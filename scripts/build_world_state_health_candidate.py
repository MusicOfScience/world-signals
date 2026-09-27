#!/usr/bin/env python3
"""Build the non-production Step 8A DRC health candidate package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.world_state_candidate import build_health_candidate, validate_health_candidate_package


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--constructed-at-utc", required=True, help="Explicit UTC construction/knowledge cutoff")
    parser.add_argument("--output", required=True, type=Path, help="Non-production audit output path")
    args = parser.parse_args()
    if "data/world_state/" in str(args.output) or args.output.name == "state.json":
        parser.error("output must not be a production World State path")
    package = build_health_candidate(ROOT, args.constructed_at_utc)
    errors = validate_health_candidate_package(package)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(package, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"PASS: wrote non-production Step 8A candidate package to {args.output}")
    print(f"candidate_semantic_fingerprint={package['candidate_semantic_fingerprint']}")
    print(f"source_manifest_sha256={package['source_manifest_sha256']}")
    print(f"preflight_classification={package['preflight_classification']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
