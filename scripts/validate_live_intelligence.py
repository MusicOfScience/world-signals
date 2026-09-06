#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.io import load_json
from world_signals.live_intelligence import validate_live_intelligence


def main() -> int:
    schema = load_json(ROOT / "data/live_intelligence/schema.json")
    evidence = load_json(ROOT / "data/live_intelligence/evidence_registry.json")
    observations = load_json(ROOT / "data/live_intelligence/observations.json")
    canonical = load_json(ROOT / "data/canonical/registry.json")

    report = validate_live_intelligence(schema, evidence, observations, canonical)
    if not report.ok:
        print("Live Intelligence validation FAILED")
        for error in report.errors:
            print(f"- {error}")
        return 1

    print(
        "Live Intelligence validation PASS: "
        f"schema={schema.get('version')} "
        f"observations={len(observations.get('observations', []))} "
        f"evidence={len(evidence.get('evidence', []))} "
        f"population={observations.get('population_state')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
