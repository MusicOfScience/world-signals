#!/usr/bin/env python3
"""Validate the closed production Outcome / Resolution contract."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.io import load_json
from world_signals.outcomes import validate_outcomes


schema = load_json(ROOT / "data/outcomes/schema.json")
outcomes = load_json(ROOT / "data/outcomes/outcomes.json")
forecasts = load_json(ROOT / "data/forecasts/forecasts.json")
evidence = load_json(ROOT / "data/live_intelligence/evidence_registry.json")
sources = load_json(ROOT / "data/sources/registry.json")

report = validate_outcomes(schema, outcomes, forecasts, evidence, sources)
if not report.ok:
    for error in report.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print(
    "Outcome validation PASS: "
    f"schema={schema.get('version')} "
    f"outcomes={len(outcomes.get('outcomes', []))} "
    f"population={outcomes.get('population_state')}"
)
