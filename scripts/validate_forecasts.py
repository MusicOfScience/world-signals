#!/usr/bin/env python3
"""Validate the governed Forecast contract and prospective pilot admission."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.io import load_json
from world_signals.forecasts import validate_forecasts


schema = load_json(ROOT / "data/forecasts/schema.json")
forecasts = load_json(ROOT / "data/forecasts/forecasts.json")
admission_path = ROOT / "data/forecasts/admission_transaction.json"
admission = load_json(admission_path) if admission_path.exists() else None
scenarios = load_json(ROOT / "data/scenarios/scenarios.json")
risks = load_json(ROOT / "data/risks/states.json")
signals = load_json(ROOT / "data/signals/signals.json")
relationships = load_json(ROOT / "data/relationships/relationships.json")
observations = load_json(ROOT / "data/live_intelligence/observations.json")
evidence = load_json(ROOT / "data/live_intelligence/evidence_registry.json")
canonical = load_json(ROOT / "data/canonical/registry.json")
sources = load_json(ROOT / "data/sources/registry.json")

report = validate_forecasts(
    schema,
    forecasts,
    scenarios,
    risks,
    signals,
    relationships,
    observations,
    evidence,
    canonical,
    sources,
    admission,
)
if not report.ok:
    for error in report.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print(
    "Forecast validation PASS: "
    f"schema={schema.get('version')} "
    f"forecasts={len(forecasts.get('forecasts', []))} "
    f"population={forecasts.get('population_state')} "
    f"admission={'present' if admission else 'none'}"
)
