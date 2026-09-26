#!/usr/bin/env python3
"""Validate the explicit reviewed Signal admission transaction."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.io import load_json
from world_signals.signal_admission import validate_signal_admission_transaction


def main() -> int:
    schema = load_json(ROOT / "data/signals/schema.json")
    signals = load_json(ROOT / "data/signals/signals.json")
    transaction = load_json(ROOT / "data/signals/signal_admission_transaction_v1.json")
    observations = load_json(ROOT / "data/live_intelligence/observations.json")
    evidence = load_json(ROOT / "data/live_intelligence/evidence_registry.json")
    report = validate_signal_admission_transaction(schema, signals, observations, evidence, transaction)
    if not report.ok:
        print("Signal admission validation FAILED")
        for error in report.errors:
            print(f"- {error}")
        return 1
    print(
        "Signal admission validation PASS: "
        f"transaction={transaction.get('transaction_id')} "
        f"signals={len(signals.get('signals', []))} "
        "maximum=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
