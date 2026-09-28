#!/usr/bin/env python3
"""Validate and optionally retain the Step 11A.1 temporal correction."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.world_state_rbnz_candidate import build_corrected_rbnz_candidate, validate_corrected_rbnz_candidate_package


DEFAULT_OUTPUT = ROOT / "data/world_state_audit/STEP11A1_RBNZ_CANDIDATE_REVIEW_PENDING_CORRECTED.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write the non-governed corrected successor package")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    package = build_corrected_rbnz_candidate(ROOT)
    errors = validate_corrected_rbnz_candidate_package(package)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if args.write:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(package, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Step 11A.1 RBNZ temporal correction: PASS")
    print(f"source manifest: {package['source_manifest_sha256']}")
    print(f"corrected candidate fingerprint: {package['candidate_semantic_fingerprint']}")
    print(f"corrected snapshot fingerprint: {package['proposed_snapshot']['snapshot_semantic_fingerprint']}")
    print("production writes: []")
    if args.write:
        print(f"retained package: {args.output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
