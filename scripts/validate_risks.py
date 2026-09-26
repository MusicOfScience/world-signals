#!/usr/bin/env python3
"""Validate the closed production Risk / Regime-State contract."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.io import load_json
from world_signals.risks import validate_risk_states


schema = load_json(ROOT / "data/risks/schema.json")
states = load_json(ROOT / "data/risks/states.json")
signals = load_json(ROOT / "data/signals/signals.json")
relationships = load_json(ROOT / "data/relationships/relationships.json")
observations = load_json(ROOT / "data/live_intelligence/observations.json")
evidence = load_json(ROOT / "data/live_intelligence/evidence_registry.json")
canonical = load_json(ROOT / "data/canonical/registry.json")

report = validate_risk_states(schema, states, signals, relationships, observations, evidence, canonical)
if not report.ok:
    for error in report.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print(
    "Risk/Regime validation PASS: "
    f"schema={schema.get('version')} states={len(states.get('states', []))} "
    f"population={states.get('population_state')}"
)
