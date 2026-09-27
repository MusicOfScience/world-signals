#!/usr/bin/env python3
"""Validate the unpopulated Migration Step 7 World State contracts.

This command is deliberately schema-only.  It does not read or write a
production World State dataset and does not treat the synthetic test fixture as
governed state.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "data" / "world_state"
SCHEMAS = (
    "actor_registry_schema.json",
    "component_schema.json",
    "snapshot_schema.json",
    "admission_schema.json",
)


def main() -> int:
    errors: list[str] = []
    if (SCHEMA_DIR / "state.json").exists():
        errors.append("production data/world_state/state.json must not exist in Step 7")
    for filename in SCHEMAS:
        path = SCHEMA_DIR / filename
        if not path.exists():
            errors.append(f"missing schema: {path}")
            continue
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid schema {path}: {exc}")
            continue
        if document.get("population_state") != "UNPOPULATED_CONTRACT_ONLY":
            errors.append(f"{filename}: population_state is not explicitly unpopulated")
        if document.get("version") != "0.1":
            errors.append(f"{filename}: unexpected version")
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: World State production-history schemas are present and unpopulated")
    print("PASS: no production World State dataset is present")
    print("PASS: validator performed no writes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
