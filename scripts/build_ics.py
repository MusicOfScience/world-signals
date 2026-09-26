#!/usr/bin/env python3
"""Build the governed WORLD SIGNALS subscription calendar projection."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.io import load_json
from world_signals.icalendar import write_icalendar
from world_signals.validation import validate_registry


def main() -> int:
    registry = load_json(ROOT / "data/canonical/registry.json")
    sources = load_json(ROOT / "data/sources/registry.json")
    changes = load_json(ROOT / "data/changes/ledger.json")
    report = validate_registry(registry, sources)
    if not report.ok:
        raise SystemExit("Registry validation failed: " + "; ".join(report.errors))
    output = ROOT / "docs/world-signals.ics"
    build = write_icalendar(output, registry, sources, changes)
    print(
        f"Built {output} with {len(build.included_occurrence_ids)} events; "
        f"omitted {len(build.omitted)} non-dated or non-publishable records."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
