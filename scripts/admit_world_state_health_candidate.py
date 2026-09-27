#!/usr/bin/env python3
"""Perform the explicit, guarded Step 8B first World State admission."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.world_state_admission import (  # noqa: E402
    ADMISSION_TRANSACTION_ID,
    REVIEW_TRANSACTION_ID,
    WorldStateAdmissionError,
    admit_first_health_candidate,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewed-at-utc", required=True, help="Explicit Step 8B human review time")
    parser.add_argument("--admitted-at-utc", required=True, help="Explicit production admission time")
    parser.add_argument("--confirm-admit", action="store_true", help="Materialise the guarded production admission")
    args = parser.parse_args()
    try:
        bundle = admit_first_health_candidate(ROOT, args.reviewed_at_utc, args.admitted_at_utc, write=args.confirm_admit)
    except (WorldStateAdmissionError, OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    transaction = bundle["admission_transaction"]
    print(f"PASS: corrected candidate fingerprint={bundle['package']['candidate_semantic_fingerprint']}")
    print(f"PASS: review transaction={REVIEW_TRANSACTION_ID}")
    print(f"PASS: admission transaction={ADMISSION_TRANSACTION_ID}")
    print(f"PASS: admission fingerprint={transaction['transaction_fingerprint']}")
    print(f"PASS: component fingerprint={bundle['admitted_component']['object_sha256']}")
    print(f"PASS: snapshot fingerprint={bundle['production_snapshot']['object_sha256']}")
    print(f"PASS: freshness={bundle['freshness']['signal_state_at_admission']} due={bundle['freshness']['stale_review_due_at_utc']}")
    print(f"PASS: materialized={bundle['materialized']}")
    print(f"PASS: upstream_mutation={bundle.get('protected_input_hashes_after') == bundle['protected_input_hashes_before'] if bundle['materialized'] else 'NOT_APPLICABLE'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
