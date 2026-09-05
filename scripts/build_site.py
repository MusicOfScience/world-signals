from pathlib import Path
import shutil, sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from world_signals.io import load_json, dump_json
from world_signals.validation import validate_registry
from world_signals.projection import public_projection
from world_signals.operations import operations_projection
from world_signals.runtime_projection import unavailable_runtime_projection
from world_signals.biosecurity_projection import public_biosecurity_projection

reg=load_json(ROOT/"data/canonical/registry.json")
src=load_json(ROOT/"data/sources/registry.json")
changes=load_json(ROOT/"data/changes/ledger.json")
expectations=load_json(ROOT/"data/monitor/expectations.json")
operations_policy=load_json(ROOT/"data/monitor/operations_policy.json")
review_contract=load_json(ROOT/"data/monitor/review_candidate_state_contract.json")
biosecurity_overlay=load_json(ROOT/"data/coverage/biosecurity_overlay.json")

report=validate_registry(reg,src)
if not report.ok:
    raise SystemExit("Registry validation failed: "+"; ".join(report.errors))

docs=ROOT/"docs"
docs.mkdir(exist_ok=True)
for name in ("index.html","app.js","styles.css","horizon.js","horizon.css","native-calendar.js","native-calendar.css","history.js","history.css","operations.js","operations.css"):
    shutil.copy2(ROOT/"web"/name, docs/name)

# Keep source modules separate while shipping one Operations browser asset.
# The appended biosecurity module only injects a read-only analytical section.
with (docs/"operations.js").open("a",encoding="utf-8") as bundled:
    bundled.write("\n\n/* bundled source: web/biosecurity.js */\n")
    bundled.write((ROOT/"web/biosecurity.js").read_text(encoding="utf-8"))

projection=public_projection(reg,src)
dump_json(docs/"data/events.json", projection)
dump_json(docs/"data/changes.json", changes)

source_map={s.get("source_id"):s for s in src.get("sources",[])}
monitor_projection={
    "metadata":{
        "projection_type":"CONFIGURED_ROUTES_NOT_RUNTIME_STATUS",
        "automatic_canonical_commit":False,
        "google_calendar_write":False,
        "runtime_status_location":"GitHub Actions artefacts",
    },
    "routes":[],
}
for route in expectations.get("adapters",[]):
    source=source_map.get(route.get("source_id"),{})
    monitor_projection["routes"].append({
        "adapter_id":route.get("adapter_id"),
        "source_id":route.get("source_id"),
        "source_institution":source.get("institution"),
        "jurisdiction":source.get("jurisdiction"),
        "domain":source.get("domain"),
        "monitor_role":route.get("monitor_role"),
        "cadence":route.get("cadence"),
        "canonical_occurrence_ids":route.get("canonical_occurrence_ids",[]),
        "source_failure_policy":route.get("source_failure_policy"),
        "positive_evidence_policy":route.get("positive_evidence_policy"),
        "change_policy":route.get("change_policy"),
        "automatic_commit_allowed":False,
        "registry_monitoring_readiness":source.get("monitoring_readiness_status"),
        "registry_automated_monitoring_use":source.get("automated_monitoring_use"),
    })
dump_json(docs/"data/monitor_routes.json",monitor_projection)

ops_projection=operations_projection(reg,src,expectations,operations_policy,changes)
dump_json(docs/"data/operations.json",ops_projection)

biosecurity_projection=public_biosecurity_projection(reg,biosecurity_overlay)
dump_json(docs/"data/biosecurity.json",biosecurity_projection)

runtime_path=ROOT/"artifacts/latest-monitor-public.json"
if runtime_path.exists():
    runtime_projection=load_json(runtime_path)
else:
    runtime_projection=unavailable_runtime_projection(
        "NO_RUNTIME_ARTIFACT_FETCH_PERFORMED_FOR_THIS_BUILD",
        {
            "canonical_registry_version":reg.get("version"),
            "source_registry_version":src.get("version"),
            "monitor_expectations_version":expectations.get("version"),
            "monitor_operations_policy_version":operations_policy.get("version"),
        },
    )
dump_json(docs/"data/runtime.json",runtime_projection)

review_path=ROOT/"artifacts/retained-review-public.json"
if review_path.exists():
    review_projection=load_json(review_path)
else:
    review_projection={
        "project":"WORLD SIGNALS",
        "dataset":"RETAINED_REVIEW_CANDIDATE_STATE",
        "version":review_contract.get("version"),
        "availability":"UNAVAILABLE_NO_RETAINED_REVIEW_FETCH",
        "scope":"RETAINED_ACTIONS_ARTEFACT_HORIZON_NOT_PERMANENT_QUEUE",
        "activation_after_run_number":(review_contract.get("activation") or {}).get("activation_after_run_number"),
        "retention_days":(review_contract.get("retention_limit") or {}).get("current_monitor_artefact_retention_days"),
        "run_count_considered":0,
        "item_count":0,
        "state_counts":{},
        "items":[],
        "evidence_horizon_complete":False,
        "evidence_gaps":["NO_RETAINED_REVIEW_FETCH_PERFORMED_FOR_THIS_BUILD"],
        "automatic_canonical_commit":False,
        "google_calendar_write":False,
    }
dump_json(docs/"data/review_state.json",review_projection)

dump_json(docs/"data/source_summary.json", {
    "source_count": len(src.get("sources",[])),
    "configured_live_monitor_routes":len(monitor_projection["routes"]),
    "reviewed_change_count":len(changes.get("changes",[])),
    "monitoring_tiers":ops_projection["source_governance_summary"]["monitoring_readiness_status"],
    "runtime_snapshot_availability":runtime_projection.get("availability"),
    "retained_review_state_availability":review_projection.get("availability"),
    "retained_review_item_count":review_projection.get("item_count",0),
    "biosecurity_mapped_series_count":biosecurity_projection["metadata"]["mapped_canonical_series_count"],
    "biosecurity_candidate_node_count":biosecurity_projection["metadata"]["candidate_node_count"],
})

(docs/".nojekyll").write_text("",encoding="utf-8")
print(
    f"Built static site for {projection['metadata']['record_count']} events, "
    f"{len(monitor_projection['routes'])} configured live monitor routes, "
    f"{len(src.get('sources',[]))} governed sources, reviewed change history, "
    f"biosecurity_overlay={biosecurity_projection['metadata']['mapped_canonical_series_count']}series/"
    f"{biosecurity_projection['metadata']['candidate_node_count']}candidates, "
    f"runtime={runtime_projection.get('availability')} and "
    f"retained_review={review_projection.get('availability')}({review_projection.get('item_count',0)}) -> {docs}"
)
