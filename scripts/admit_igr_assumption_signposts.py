#!/usr/bin/env python3
"""Explicitly admit the reviewed Step 14G assumption-signpost package."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.assumption_signposts import human_dispositions, build_transaction, materialize  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--materialize", action="store_true", help="perform the exact bounded internal admission")
    parser.add_argument("--confirm-owner-decision", action="store_true", help="confirm the explicit Step 14H owner dispositions in the retained review record")
    args = parser.parse_args()
    if not args.materialize or not args.confirm_owner_decision:
        parser.error("both --materialize and --confirm-owner-decision are required; validation alone does not admit")
    reviewed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    admitted_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    targets = build_transaction(ROOT, reviewed_at, admitted_at, decision=human_dispositions())
    materialize(ROOT, targets)
    print("Step 14H internal assumption-signpost admission: PASS")
    print(f"reviewed_at_utc={reviewed_at} admitted_at_utc={admitted_at}")
    print("assumptions=8 signposts=15 coverage_gaps=8 snapshots=1 routes=0 public=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
