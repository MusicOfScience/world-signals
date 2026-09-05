from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.analysis import validate_analysis
from world_signals.io import load_json

schema = load_json(ROOT / "data/analysis/schema.json")
evidence = load_json(ROOT / "data/analysis/evidence_registry.json")
reviews = load_json(ROOT / "data/analysis/event_reviews.json")
canonical = load_json(ROOT / "data/canonical/registry.json")

report = validate_analysis(schema, evidence, reviews, canonical)
if not report.ok:
    for error in report.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print(
    f"Validated {len(reviews.get('reviews', []))} analytical review(s), "
    f"{len(evidence.get('evidence', []))} evidence record(s): PASS"
)
