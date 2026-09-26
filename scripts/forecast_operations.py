#!/usr/bin/env python3
"""Report the read-only operational watch for production Forecasts."""

import argparse
from datetime import datetime, timezone
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.forecast_operations import build_watch_manifest, validate_operations_policy
from world_signals.forecasts import validate_forecasts
from world_signals.io import load_json
from world_signals.outcomes import validate_outcomes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", dest="as_of", help="exact UTC timestamp; defaults to current UTC")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit the machine-readable manifest")
    args = parser.parse_args()
    policy = load_json(ROOT / "data/forecasts/operations_policy.json")
    policy_errors = validate_operations_policy(policy)
    if policy_errors:
        raise SystemExit("Operations policy validation failed: " + "; ".join(policy_errors))
    as_of = args.as_of or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    forecasts = load_json(ROOT / "data/forecasts/forecasts.json")
    outcomes = load_json(ROOT / "data/outcomes/outcomes.json")
    forecast_report = validate_forecasts(
        load_json(ROOT / "data/forecasts/schema.json"),
        forecasts,
        load_json(ROOT / "data/scenarios/scenarios.json"),
        load_json(ROOT / "data/risks/states.json"),
        load_json(ROOT / "data/signals/signals.json"),
        load_json(ROOT / "data/relationships/relationships.json"),
        load_json(ROOT / "data/live_intelligence/observations.json"),
        load_json(ROOT / "data/live_intelligence/evidence_registry.json"),
        load_json(ROOT / "data/canonical/registry.json"),
        load_json(ROOT / "data/sources/registry.json"),
        load_json(ROOT / "data/forecasts/admission_transaction.json"),
    )
    if not forecast_report.ok:
        raise SystemExit("Forecast validation failed: " + "; ".join(forecast_report.errors))
    outcome_report = validate_outcomes(
        load_json(ROOT / "data/outcomes/schema.json"),
        outcomes,
        forecasts,
        load_json(ROOT / "data/live_intelligence/evidence_registry.json"),
        load_json(ROOT / "data/sources/registry.json"),
    )
    if not outcome_report.ok:
        raise SystemExit("Outcome validation failed: " + "; ".join(outcome_report.errors))
    manifest = build_watch_manifest(
        forecasts,
        outcomes,
        as_of,
        review_lead_time_days=policy["review_lead_time_days"],
    )
    if args.as_json:
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
        return 0
    print(f"Forecast Operations watch: {manifest['forecast_count']} Forecasts as of {manifest['as_of_utc']}")
    for item in manifest["items"]:
        print(f"- {item['issuance_id']}: {item['operational_state']}; next review {item['next_review_trigger'] or 'none'}")
    print("No Forecast or Outcome writes performed; Evaluation remains closed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
