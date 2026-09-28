#!/usr/bin/env python3
"""Validate the controlled v0.2 Relationship production specimen."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.relationship_admission import validate_rbnz_relationship_admission  # noqa: E402


report = validate_rbnz_relationship_admission(ROOT)
if not report.ok:
    for error in report.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print(
    "Relationship production validation PASS: "
    "accepted=1 historical=1 active=0 public=0"
)
