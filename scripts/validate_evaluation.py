#!/usr/bin/env python3
"""Validate the closed production Forecast Evaluation projection."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.io import load_json
from world_signals.evaluation import validate_evaluation


schema = load_json(ROOT / "data/evaluation/schema.json")
config = load_json(ROOT / "data/evaluation/config.json")
dataset = load_json(ROOT / "data/evaluation/evaluation.json")
forecasts = load_json(ROOT / "data/forecasts/forecasts.json")
outcomes = load_json(ROOT / "data/outcomes/outcomes.json")
report = validate_evaluation(schema, config, dataset, forecasts, outcomes)
if not report.ok:
    raise SystemExit("Evaluation validation failed: " + "; ".join(report.errors))
print("Evaluation validation PASS: schema=0.1 state=NO_SAMPLE evaluations=0 public_projection=CLOSED")
