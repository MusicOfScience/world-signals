#!/usr/bin/env python3
"""Build or inspect the deterministic Step 14G review-pending candidate."""
from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.igr_assumption_signposts import (  # noqa: E402
    build_candidate, candidate_json, render_summary,
)


JSON_PATH = ROOT / "data/analysis/STEP14G_AU_IGR_ASSUMPTION_SIGNPOSTS_REVIEW_PENDING.json"
MD_PATH = ROOT / "data/analysis/STEP14G_AU_IGR_ASSUMPTION_SIGNPOSTS_REVIEW_PENDING.md"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="retain the two candidate-only artifacts")
    args = parser.parse_args()
    candidate = build_candidate(ROOT)
    if args.write:
        JSON_PATH.write_text(candidate_json(candidate), encoding="utf-8")
        MD_PATH.write_text(render_summary(candidate), encoding="utf-8")
        print(f"wrote candidate-only files: {JSON_PATH.relative_to(ROOT)}, {MD_PATH.relative_to(ROOT)}")
    print(f"status={candidate['status']} signposts={len(candidate['signposts'])} "
          f"assumptions={len(candidate['selected_assumptions'])} "
          f"fingerprint={candidate['semantic_fingerprint']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
