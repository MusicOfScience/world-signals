#!/usr/bin/env python3
"""Validate the bounded, candidate-only OSINT cohort and policy."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.osint_engine import load_json, validate_cohort  # noqa: E402


def main() -> int:
    registry = load_json(ROOT / "data/sources/registry.json")
    cohort = load_json(ROOT / "data/osint/source_cohort.json")
    schema = load_json(ROOT / "data/osint/schema.json")
    issues = validate_cohort(registry, cohort)
    if schema.get("governance", {}).get("status") != "NON_GOVERNED_RUNTIME_ONLY":
        issues.append("OSINT schema must remain non-governed runtime-only")
    policy = cohort.get("retrieval_policy", {})
    for key in ("local_only", "read_only", "automatic_canonical_mutation", "automatic_observation_promotion",
                "automatic_signal_promotion", "public_candidate_projection", "raw_payload_publication"):
        expected = key not in {"automatic_canonical_mutation", "automatic_observation_promotion",
                               "automatic_signal_promotion", "public_candidate_projection", "raw_payload_publication"}
        if policy.get(key) is not expected:
            issues.append(f"retrieval policy {key} must be {expected}")
    if len(cohort.get("routes", [])) < 8 or len(cohort.get("routes", [])) > 15:
        issues.append("v1 cohort must remain bounded between 8 and 15 routes")
    if issues:
        print("OSINT cohort validation failed:")
        print("\n".join(f"- {issue}" for issue in issues))
        return 1
    print(json.dumps({
        "dataset": cohort["dataset"],
        "version": cohort["version"],
        "route_count": len(cohort["routes"]),
        "status": "VALID_CANDIDATE_ONLY_LOCAL_RUNTIME",
        "promotion": "CLOSED",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
