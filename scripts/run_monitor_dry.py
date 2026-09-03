from pathlib import Path
import sys, copy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from world_signals.io import load_json, dump_json
from world_signals.monitor import compare_assertion, protected_digest

reg=load_json(ROOT/"data/canonical/registry.json")
record=next(r for r in reg["records"] if r["occurrence_id"]=="WSO-MAC-B-0035")
before=protected_digest(record)
# Default dry-run is the real current ONS assertion: NO_CHANGE.
assertion={
    "start_local":"2026-09-11T07:00:00",
    "certainty_status":"CONFIRMED",
    "lifecycle_status":"PLANNED",
    "source_id":"WSSRC-MAC-006",
    "mode":"DRY_RUN_FIXTURE"
}
candidate=compare_assertion(record,assertion)
after=protected_digest(record)
if before != after:
    raise SystemExit("FAIL: monitor mutated protected canonical identity")
out=ROOT/"review_candidates/dry_run.generated.json"
dump_json(out,{
    "mode":"DRY_RUN",
    "canonical_mutation":False,
    "candidate": candidate.as_dict() if candidate else None,
    "result":"REVIEW_CANDIDATE" if candidate else "NO_CHANGE",
})
print("Monitor dry-run:","REVIEW_CANDIDATE" if candidate else "NO_CHANGE")
print("Canonical mutation: False")
