from pathlib import Path
import shutil, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from world_signals.io import load_json, dump_json
from world_signals.validation import validate_registry
from world_signals.projection import public_projection

reg=load_json(ROOT/"data/canonical/registry.json")
src=load_json(ROOT/"data/sources/registry.json")
report=validate_registry(reg,src)
if not report.ok:
    raise SystemExit("Registry validation failed: "+"; ".join(report.errors))

docs=ROOT/"docs"
docs.mkdir(exist_ok=True)
for name in ("index.html","app.js","styles.css"):
    shutil.copy2(ROOT/"web"/name, docs/name)
projection=public_projection(reg,src)
dump_json(docs/"data/events.json", projection)
dump_json(docs/"data/changes.json", load_json(ROOT/"data/changes/ledger.json"))
dump_json(docs/"data/source_summary.json", {
    "source_count": len(src.get("sources",[])),
    "monitoring_tiers": {},
})
(docs/".nojekyll").write_text("",encoding="utf-8")
print(f"Built static site for {projection['metadata']['record_count']} events -> {docs}")
