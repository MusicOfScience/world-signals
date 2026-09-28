#!/usr/bin/env python3
"""Build the non-production Step 14A climate candidate package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.world_state_climate_candidate import (  # noqa: E402
    CONSTRUCTION_CUTOFF,
    build_climate_candidate,
    validate_climate_candidate_package,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="Non-production audit output path")
    parser.add_argument("--constructed-at-utc", default=CONSTRUCTION_CUTOFF)
    args = parser.parse_args()
    output = args.output.resolve()
    if "data/world_state/" in str(output) or output.name == "state.json":
        parser.error("output must not be a production World State path")
    package = build_climate_candidate(ROOT, construction_cutoff_utc=args.constructed_at_utc)
    errors = validate_climate_candidate_package(package)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(package, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"PASS: wrote non-production Step 14A candidate package to {output}")
    print(f"baseline_candidate_fingerprint={package['baseline_candidate_fingerprint']}")
    print(f"dimension_candidate_fingerprint={package['dimension_candidate_fingerprint']}")
    print(f"candidate_semantic_fingerprint={package['candidate_semantic_fingerprint']}")
    print(f"source_manifest_sha256={package['source_manifest_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
