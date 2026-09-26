#!/usr/bin/env python3
"""Validate the closed production Scenario contract."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.io import load_json
from world_signals.scenarios import validate_scenarios


schema = load_json(ROOT / "data/scenarios/schema.json")
scenarios = load_json(ROOT / "data/scenarios/scenarios.json")
risks = load_json(ROOT / "data/risks/states.json")
signals = load_json(ROOT / "data/signals/signals.json")
relationships = load_json(ROOT / "data/relationships/relationships.json")
observations = load_json(ROOT / "data/live_intelligence/observations.json")
evidence = load_json(ROOT / "data/live_intelligence/evidence_registry.json")
canonical = load_json(ROOT / "data/canonical/registry.json")

report = validate_scenarios(schema, scenarios, risks, signals, relationships, observations, evidence, canonical)
if not report.ok:
    for error in report.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print(
    "Scenario validation PASS: "
    f"schema={schema.get('version')} "
    f"scenario_sets={len(scenarios.get('scenario_sets', []))} "
    f"scenarios={len(scenarios.get('scenarios', []))} "
    f"population={scenarios.get('population_state')}"
)
