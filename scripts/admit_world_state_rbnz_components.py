#!/usr/bin/env python3
"""Preflight or explicitly materialise the Step 11B RBNZ admission."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.world_state_rbnz_admission import (  # noqa: E402
    ADMISSION_TRANSACTION_ID,
    REVIEW_TRANSACTION_ID,
    WorldStateRbnzAdmissionError,
    materialize_rbnz_admission,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewed-at-utc", required=True, help="explicit Step 11B human review time")
    parser.add_argument("--admitted-at-utc", required=True, help="explicit Step 11B production admission time")
    parser.add_argument("--confirm-admit", action="store_true", help="materialise the guarded production admission")
    args = parser.parse_args()
    try:
        bundle = materialize_rbnz_admission(
            ROOT,
            args.reviewed_at_utc,
            args.admitted_at_utc,
            write=args.confirm_admit,
        )
    except WorldStateRbnzAdmissionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("Step 11B RBNZ production admission: PASS")
    print(f"review transaction: {REVIEW_TRANSACTION_ID}")
    print(f"admission transaction: {ADMISSION_TRANSACTION_ID}")
    for component in bundle["admitted_components"]:
        print(f"component: {component['component_id']} {component['revision_id']} {component['object_sha256']}")
    print(f"snapshot: {bundle['production_snapshot']['snapshot_revision_id']} {bundle['production_snapshot']['object_sha256']}")
    print(f"admission fingerprint: {bundle['admission_transaction']['transaction_fingerprint']}")
    print(f"materialized: {bundle['materialized']}")
    print("actor decision: DEFERRED; production actor writes: []")
    print("public projection permitted: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
