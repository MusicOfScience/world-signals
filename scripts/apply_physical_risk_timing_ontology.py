#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "data/canonical/schema.json"
REGISTRY_PATH = ROOT / "data/canonical/registry.json"

DESIGN_DECISIONS = [
    "Month-bounded seasonal risk windows preserve source-native month precision in year-qualified YYYY-MM season_phases[]; first/last civil days are never manufactured.",
    "A multi-phase seasonal risk window preserves each authoritative non-contiguous phase independently and in order; gaps are not collapsed into a continuous span.",
    "For month-bounded seasonal windows, start_local/end_local, UTC timestamps and date_earliest/date_latest remain empty because those fields would imply day or clock precision the source did not assert.",
    "Calendar/index rendering may derive an internal month-start sort proxy from season_phases[] but that proxy is never canonical timing and must not be displayed, exported or written back as an event date.",
    "A dynamic annual season outlook is an information assertion about expected timing and remains separate from a stable PHYSICAL_RISK_WINDOW occurrence unless the authority explicitly establishes a canonical bounded window."
]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def migrate(schema: dict, registry: dict) -> tuple[dict, dict]:
    errors: list[str] = []
    if str(schema.get("version")) != "0.49":
        errors.append(f"schema version {schema.get('version')} != 0.49")
    if str(registry.get("version")) != "0.19" or registry.get("record_count") != 668:
        errors.append(
            f"canonical checkpoint {registry.get('version')}/{registry.get('record_count')} != 0.19/668"
        )

    timing_fields = schema.get("event_occurrence_fields", {}).get("timing", [])
    for field in ("season_window_model", "source_native_window_label", "season_phases"):
        if field in timing_fields:
            errors.append(f"timing field already exists: {field}")
    for vocab in ("season_window_model", "season_phase_boundary_precision"):
        if vocab in schema.get("controlled_vocabularies", {}):
            errors.append(f"controlled vocabulary already exists: {vocab}")
    if "season_phase_fields" in schema:
        errors.append("season_phase_fields already exists")

    if errors:
        raise SystemExit("PRECONDITION FAILED:\n- " + "\n- ".join(errors))

    observed_timing_types = sorted(
        {str(r.get("timing_type")) for r in registry.get("records", []) if r.get("timing_type")}
    )

    out = json.loads(json.dumps(schema))
    out["version"] = "0.50"
    out["reference_date"] = "2026-09-04"
    out["design_decisions"].extend(DESIGN_DECISIONS)

    vocab = out["controlled_vocabularies"]
    vocab["timing_type"] = sorted(
        set(observed_timing_types)
        | {"MONTH_BOUNDED_SEASON_WINDOW", "MULTI_PHASE_SEASON_WINDOW"}
    )
    vocab["season_window_model"] = [
        "MONTH_BOUNDED_SINGLE_PHASE",
        "MONTH_BOUNDED_MULTI_PHASE",
    ]
    vocab["season_phase_boundary_precision"] = ["MONTH"]

    out["event_occurrence_fields"]["timing"].extend(
        ["season_window_model", "source_native_window_label", "season_phases"]
    )
    out["event_occurrence_fields"]["physical_risk_window_semantics"] = [
        "signal_object_class",
        "season_window_model",
        "source_native_window_label",
        "season_phases",
        "publication_time_semantics",
        "physical_shock_routing",
    ]
    out["season_phase_fields"] = [
        "phase_id",
        "start_month",
        "end_month",
        "boundary_precision",
        "source_label",
    ]

    post_errors: list[str] = []
    if out.get("version") != "0.50":
        post_errors.append("schema version did not advance to 0.50")
    for field in ("season_window_model", "source_native_window_label", "season_phases"):
        if field not in out["event_occurrence_fields"]["timing"]:
            post_errors.append(f"missing timing field after migration: {field}")
    required_types = {"MONTH_BOUNDED_SEASON_WINDOW", "MULTI_PHASE_SEASON_WINDOW"}
    if not required_types.issubset(set(vocab["timing_type"])):
        post_errors.append("new seasonal timing types absent after migration")
    if len(out["season_phase_fields"]) != 5:
        post_errors.append("season_phase_fields contract incomplete")
    if post_errors:
        raise SystemExit("POSTCONDITION FAILED:\n- " + "\n- ".join(post_errors))

    summary = {
        "status": "PASS",
        "schema_version_before": schema.get("version"),
        "schema_version_after": out.get("version"),
        "canonical_registry_version": registry.get("version"),
        "canonical_record_count": registry.get("record_count"),
        "observed_existing_timing_types": observed_timing_types,
        "new_timing_types": sorted(required_types),
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
