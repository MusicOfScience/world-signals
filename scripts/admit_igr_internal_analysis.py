"""Explicit Step 14F owner-decision preflight; --write is a bounded transaction."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from world_signals.igr_analysis_admission import DISPOSITIONS, construct, materialize, validate_admitted, TRANSACTION_PATH

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--check", action="store_true")
parser.add_argument("--human-decision", choices=["ACCEPT_INTERNAL_PRODUCTION"])
parser.add_argument("--reviewed-at")
parser.add_argument("--admitted-at")
parser.add_argument("--write", action="store_true")
args = parser.parse_args()
if args.check:
    if args.write or args.human_decision:
        parser.error("--check is read-only")
    validate_admitted(ROOT)
    print("STEP14F_INTERNAL_ADMISSION_VALID; public IGR absent")
else:
    if not args.human_decision or not args.reviewed_at or not args.admitted_at:
        parser.error("explicit owner decision and UTC review/admission times required")
    targets = construct(ROOT, args.reviewed_at, args.admitted_at, human_decision=DISPOSITIONS)
    if args.write:
        materialize(ROOT, targets)
    print(json.dumps({"materialized": args.write, "transaction": targets[TRANSACTION_PATH]}, indent=2))
