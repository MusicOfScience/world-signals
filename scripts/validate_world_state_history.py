#!/usr/bin/env python3
"""Validate the controlled World State production history contracts.

This command is read-only.  It validates the admitted component, snapshot and
admission histories and does not select a latest state, write production data,
or treat the synthetic test fixture as governed state.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "data" / "world_state"
sys.path.insert(0, str(ROOT / "src"))

from world_signals.world_state_admission import load_production_state, validate_production_state  # noqa: E402
from world_signals.world_state_history import validate_actor_registry  # noqa: E402


SCHEMAS = {
    "actor_registry_schema.json": "UNPOPULATED_CONTRACT_ONLY",
    "component_schema.json": "CONTROLLED_COMPONENTIZED_PRODUCTION_HISTORY",
    "snapshot_schema.json": "CONTROLLED_COMPONENTIZED_PRODUCTION_HISTORY",
    "admission_schema.json": "CONTROLLED_COMPONENTIZED_PRODUCTION_HISTORY",
}


def main() -> int:
    errors: list[str] = []
    if (SCHEMA_DIR / "state.json").exists():
        errors.append("production data/world_state/state.json must not exist")
    for filename, expected_population_state in SCHEMAS.items():
        path = SCHEMA_DIR / filename
        if not path.exists():
            errors.append(f"missing schema: {path}")
            continue
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid schema {path}: {exc}")
            continue
        if document.get("population_state") != expected_population_state:
            errors.append(f"{filename}: unexpected population_state")
        if document.get("version") != "0.1":
            errors.append(f"{filename}: unexpected version")
    try:
        state = load_production_state(ROOT)
        errors.extend(validate_production_state(ROOT, enforce_first_population=False))
        actor_registry = ROOT / "data/world_state/actor_registry.json"
        if actor_registry.exists():
            errors.extend(validate_actor_registry(json.loads(actor_registry.read_text(encoding="utf-8"))))
        if len(state["actors"]) != 0:
            errors.append("Actor Registry must remain empty for the current componentized tranche")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"production history validation failed: {exc}")
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: World State production-history schemas and admitted history are valid")
    print("PASS: no monolithic production World State dataset is present")
    print("PASS: Actor Registry remains empty and public projection remains closed")
    print("PASS: validator performed no writes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
