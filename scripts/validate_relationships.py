#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.io import load_json
from world_signals.relationships import validate_relationships


schema = load_json(ROOT / "data/relationships/schema.json")
relationships = load_json(ROOT / "data/relationships/relationships.json")
signals = load_json(ROOT / "data/signals/signals.json")
observations = load_json(ROOT / "data/live_intelligence/observations.json")
evidence = load_json(ROOT / "data/live_intelligence/evidence_registry.json")
canonical = load_json(ROOT / "data/canonical/registry.json")

report = validate_relationships(schema, relationships, signals, observations, evidence, canonical)
if not report.ok:
    for error in report.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print(
    "Relationship validation PASS: "
    f"schema={schema.get('version')} relationships={len(relationships.get('relationships', []))} "
    f"population={relationships.get('population_state')}"
)
