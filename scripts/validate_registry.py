from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from world_signals.io import load_json
from world_signals.validation import validate_registry

reg=load_json(ROOT/"data/canonical/registry.json")
src=load_json(ROOT/"data/sources/registry.json")
report=validate_registry(reg,src)
for w in report.warnings: print("WARNING:",w)
for e in report.errors: print("ERROR:",e)
print(f"Validated {reg['record_count']} canonical occurrences: {'PASS' if report.ok else 'FAIL'}")
raise SystemExit(0 if report.ok else 1)
