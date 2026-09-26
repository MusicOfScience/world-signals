#!/usr/bin/env python3
"""Validate the closed reviewed Signal contract."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.io import load_json
from world_signals.signals import validate_signals


def main() -> int:
    schema = load_json(ROOT / "data/signals/schema.json")
    signals = load_json(ROOT / "data/signals/signals.json")
    observations = load_json(ROOT / "data/live_intelligence/observations.json")
    evidence = load_json(ROOT / "data/live_intelligence/evidence_registry.json")
    report = validate_signals(schema, signals, observations, evidence)
    if not report.ok:
        print("Signal validation FAILED")
        for error in report.errors:
            print(f"- {error}")
        return 1
    print(
        "Signal validation PASS: "
        f"schema={schema.get('version')} "
        f"signals={len(signals.get('signals', []))} "
        f"population={signals.get('population_state')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
