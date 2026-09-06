from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.analysis import validate_analysis
from world_signals.analysis_revision import validate_analysis_revisions
from world_signals.live_analysis_bridge import validate_live_analysis_bridge
from world_signals.io import load_json

schema = load_json(ROOT / "data/analysis/schema.json")
evidence = load_json(ROOT / "data/analysis/evidence_registry.json")
reviews = load_json(ROOT / "data/analysis/event_reviews.json")
canonical = load_json(ROOT / "data/canonical/registry.json")
live_observations = load_json(ROOT / "data/live_intelligence/observations.json")

report = validate_analysis(schema, evidence, reviews, canonical)
if not report.ok:
    for error in report.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

revision_report = validate_analysis_revisions(schema, reviews)
if not revision_report.ok:
    for error in revision_report.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

bridge_report = validate_live_analysis_bridge(schema, reviews, live_observations)
if not bridge_report.ok:
    for error in bridge_report.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print(
    f"Validated {len(reviews.get('reviews', []))} analytical review(s), "
    f"{len(evidence.get('evidence', []))} evidence record(s), "
    "prospective Live Intelligence input bridge and Analysis revision contract: PASS"
)
