#!/usr/bin/env python3
"""Validate the retained Step 12A Relationship candidate without writes."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.io import load_json  # noqa: E402
from world_signals.world_state_relationship_candidate import validate_rbnz_relationship_candidate  # noqa: E402


candidate_path = ROOT / "data/relationship_audit/STEP12A_RBNZ_RELATIONSHIP_CANDIDATE_REVIEW_PENDING.json"
candidate = load_json(candidate_path)
report = validate_rbnz_relationship_candidate(candidate, ROOT)
if not report.ok:
    for error in report.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

relationship = candidate["relationship"]
print(
    "Step 12A Relationship candidate: PASS "
    f"id={relationship['relationship_id']} class={relationship['relationship_class']} "
    f"state={candidate['review_state']} disposition={candidate['candidate_disposition']} "
    f"production_writes={candidate['production_write_targets']}"
)
