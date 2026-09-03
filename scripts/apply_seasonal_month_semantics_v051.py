#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "data/canonical/schema.json"
REGISTRY_PATH = ROOT / "data/canonical/registry.json"

DECISION = (
    "Exact civil-day seasonal windows use publication_time_semantics=SEASONAL_DATE_RANGE; "
    "source-native month-bounded seasonal windows use SEASONAL_MONTH_RANGE and must not "
    "manufacture first/last civil-day boundaries."
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def migrate(schema: dict, registry: dict) -> tuple[dict, dict]:
    errors: list[str] = []
    if str(schema.get("version")) != "0.50":
        errors.append(f"schema version {schema.get('version')} != 0.50")
    if str(registry.get("version")) != "0.19" or registry.get("record_count") != 668:
        errors.append(
            f"canonical checkpoint {registry.get('version')}/{registry.get('record_count')} != 0.19/668"
        )
    vocab = schema.get("controlled_vocabularies", {}).get("publication_time_semantics", [])
    if "SEASONAL_MONTH_RANGE" in vocab:
        errors.append("SEASONAL_MONTH_RANGE already exists")
    for required in ("SEASONAL_DATE_RANGE", "DATE_ONLY"):
        if required not in vocab:
            errors.append(f"existing publication semantic missing: {required}")
    if errors:
        raise SystemExit("PRECONDITION FAILED:\n- " + "\n- ".join(errors))

    out = copy.deepcopy(schema)
    out["version"] = "0.51"
    out["reference_date"] = "2026-09-04"
    out.setdefault("design_decisions", []).append(DECISION)
    out["controlled_vocabularies"]["publication_time_semantics"].append("SEASONAL_MONTH_RANGE")

    post_errors: list[str] = []
    values = out["controlled_vocabularies"]["publication_time_semantics"]
    if out.get("version") != "0.51":
        post_errors.append("schema version did not advance to 0.51")
    if values.count("SEASONAL_MONTH_RANGE") != 1:
        post_errors.append("SEASONAL_MONTH_RANGE missing or duplicated")
    if "SEASONAL_DATE_RANGE" not in values:
        post_errors.append("SEASONAL_DATE_RANGE was lost")
    if DECISION not in out.get("design_decisions", []):
        post_errors.append("semantic design decision missing")
    if post_errors:
        raise SystemExit("POSTCONDITION FAILED:\n- " + "\n- ".join(post_errors))

    summary = {
        "status": "PASS",
        "schema_version_before": schema.get("version"),
        "schema_version_after": out.get("version"),
        "canonical_registry_version": registry.get("version"),
        "canonical_record_count": registry.get("record_count"),
        "added_publication_time_semantics": "SEASONAL_MONTH_RANGE",
        "retained_exact_day_semantics": "SEASONAL_DATE_RANGE",
        "canonical_registry_mutation": False,
        "google_calendar_write": False,
        "automatic_canonical_commit": False,
    }
    return out, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    schema = load(SCHEMA_PATH)
    registry = load(REGISTRY_PATH)
    migrated, summary = migrate(schema, registry)
    summary["mode"] = "APPLY" if args.apply else "CHECK_ONLY"
    print(json.dumps(summary, indent=2))
    if args.apply:
        dump(SCHEMA_PATH, migrated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
