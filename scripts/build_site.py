from pathlib import Path
import shutil, sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from world_signals.io import load_json, dump_json
from world_signals.validation import validate_registry
from world_signals.projection import public_projection
from world_signals.operations import operations_projection
from world_signals.biosecurity_projection import public_biosecurity_projection
from world_signals.risk_projection import public_risk_projection
from world_signals.live_intelligence import public_live_intelligence_projection, validate_live_intelligence
from world_signals.analysis import validate_analysis
from world_signals.analysis_revision import validate_analysis_revisions
from world_signals.analysis_revision_projection import public_analysis_projection_with_revision_contract
from world_signals.live_analysis_bridge import validate_live_analysis_bridge
from world_signals.icalendar import write_icalendar
from world_signals.public_forecast_projection import build_public_forecast_projection

reg=load_json(ROOT/"data/canonical/registry.json")
src=load_json(ROOT/"data/sources/registry.json")
changes=load_json(ROOT/"data/changes/ledger.json")
expectations=load_json(ROOT/"data/monitor/expectations.json")
operations_policy=load_json(ROOT/"data/monitor/operations_policy.json")
biosecurity_overlay=load_json(ROOT/"data/coverage/biosecurity_overlay.json")
live_schema=load_json(ROOT/"data/live_intelligence/schema.json")
live_evidence=load_json(ROOT/"data/live_intelligence/evidence_registry.json")
live_observations=load_json(ROOT/"data/live_intelligence/observations.json")
analysis_schema=load_json(ROOT/"data/analysis/schema.json")
analysis_evidence=load_json(ROOT/"data/analysis/evidence_registry.json")
analysis_reviews=load_json(ROOT/"data/analysis/event_reviews.json")
forecasts=load_json(ROOT/"data/forecasts/forecasts.json")

report=validate_registry(reg,src)
if not report.ok:
    raise SystemExit("Registry validation failed: "+"; ".join(report.errors))
live_report=validate_live_intelligence(live_schema,live_evidence,live_observations,reg)
if not live_report.ok:
    raise SystemExit("Live Intelligence validation failed: "+"; ".join(live_report.errors))
analysis_report=validate_analysis(analysis_schema,analysis_evidence,analysis_reviews,reg)
if not analysis_report.ok:
    raise SystemExit("Analysis validation failed: "+"; ".join(analysis_report.errors))
revision_report=validate_analysis_revisions(analysis_schema,analysis_reviews)
if not revision_report.ok:
    raise SystemExit("Analysis revision validation failed: "+"; ".join(revision_report.errors))
bridge_report=validate_live_analysis_bridge(analysis_schema,analysis_reviews,live_observations)
if not bridge_report.ok:
    raise SystemExit("Live → Analysis bridge validation failed: "+"; ".join(bridge_report.errors))

docs=ROOT/"docs"
# `docs/` is disposable generated output. Clearing this exact directory prevents
# a stale runtime/review artefact from surviving into a later public build.
if docs.exists():
    shutil.rmtree(docs)
docs.mkdir(exist_ok=True)
for name in ("index.html","app.js","styles.css","outlook.css","horizon.js","horizon.css","native-calendar.js","native-calendar.css","history.js","history.css","operations.js","operations.css","analysis.js","analysis.css","risk.css"):
    shutil.copy2(ROOT/"web"/name, docs/name)

# Keep source modules separate in the repository while shipping the existing
# no-bundler static site. Biosecurity extends Operations; Analysis extends the
# main app with a separate read-only view and cannot write canonical data.
# Live Intelligence AV is metadata-only: no UI module or current-feed claim is
# introduced until a later pressure-audited population tranche opens that gate.
with (docs/"operations.js").open("a",encoding="utf-8") as bundled:
    bundled.write("\n\n/* bundled source: web/biosecurity.js */\n")
    bundled.write((ROOT/"web/biosecurity.js").read_text(encoding="utf-8"))
with (docs/"app.js").open("a",encoding="utf-8") as bundled:
    bundled.write("\n\n/* bundled source: web/analysis.js */\n")
    bundled.write((ROOT/"web/analysis.js").read_text(encoding="utf-8"))
    bundled.write("\n\n/* bundled source: web/risk.js */\n")
    bundled.write((ROOT/"web/risk.js").read_text(encoding="utf-8"))

projection=public_projection(reg,src)
dump_json(docs/"data/events.json", projection)
dump_json(docs/"data/changes.json", changes)
ical_build = write_icalendar(docs / "world-signals.ics", reg, src, changes)

source_map={s.get("source_id"):s for s in src.get("sources",[])}
monitor_projection={
    "metadata":{
        "projection_type":"CONFIGURED_ROUTES_NOT_RUNTIME_STATUS",
        "automatic_canonical_commit":False,
        "google_calendar_write":False,
        "runtime_status_location":"sanitized local or GitHub execution projection",
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

# Public source metadata is intentionally narrower than the local operations
# projection. In particular, it does not publish monitor endpoints, rights
# evidence, runtime state or review-candidate material.
# Deliberately excluded public paths: data/runtime.json and
# data/review_state.json. Those names belong only to the local operator build.
dump_json(docs/"data/sources.json", {
    "metadata": {
        "source_count": len(src.get("sources", [])),
        "configured_live_monitor_routes": len(monitor_projection["routes"]),
        "distinction": "governed source records are not the same as actively monitored routes",
    },
    "sources": [
        {
            "source_id": source.get("source_id"),
            "institution": source.get("institution"),
            "jurisdiction": source.get("jurisdiction"),
            "domain": source.get("domain"),
            "source_type": source.get("source_type"),
            "authoritative_url": source.get("authoritative_url"),
            "source_role": source.get("endpoint_role") or source.get("information_supplied"),
            "publication_status": source.get("activation_status"),
        }
        for source in src.get("sources", [])
    ],
})

biosecurity_projection=public_biosecurity_projection(reg,biosecurity_overlay)
dump_json(docs/"data/biosecurity.json",biosecurity_projection)

live_projection=public_live_intelligence_projection(live_schema,live_evidence,live_observations,reg)
dump_json(docs/"data/live_intelligence.json",live_projection)

analysis_projection=public_analysis_projection_with_revision_contract(
    analysis_schema,analysis_evidence,analysis_reviews,reg
)
dump_json(docs/"data/analysis.json",analysis_projection)

# Forecast publication is a separate, narrow allowlist contract. The governed
# Forecast dataset remains private and its own publication policy remains
# closed; only the reviewed monetary-policy pilot is copied into Outlook.
outlook_projection=build_public_forecast_projection(forecasts)
dump_json(docs/"data/outlook.json",outlook_projection)

risk_projection=public_risk_projection(reg)
dump_json(docs/"data/risk_overlay.json",risk_projection)

def layer_status(path, collection_key, state_key="population_state"):
    payload=load_json(ROOT / path)
    policy=payload.get("public_projection_policy") or {}
    public_projection=next(
        (policy[key] for key in (
            "signal_projection_allowed",
            "forecast_projection_allowed",
            "relationship_projection_allowed",
            "risk_projection_allowed",
            "scenario_projection_allowed",
            "observation_projection_allowed",
        ) if key in policy),
        False,
    )
    return {
        "version": payload.get("version"),
        "count": len(payload.get(collection_key, [])),
        "state": payload.get(state_key),
        "public_projection": public_projection,
    }

# Counts and publication gates are safe public metadata; the underlying closed
# Signal, Forecast, Observation and downstream records are never copied.
dump_json(docs/"data/public_status.json", {
    "project": "WORLD SIGNALS",
    "reference_timezone": "Australia/Melbourne",
    "canonical": {"version": reg.get("version"), "count": len(reg.get("records", []))},
    "sources": {"version": src.get("version"), "count": len(src.get("sources", []))},
    "monitor_routes": {"version": expectations.get("version"), "count": len(monitor_projection["routes"])},
    "live_intelligence": {
        "version": live_schema.get("version"),
        "internal_count": len(live_observations.get("observations", [])),
        "public_count": live_projection["metadata"]["public_observation_count"],
        "state": live_projection["metadata"]["population_state"],
        "public_projection": live_schema.get("public_projection_policy", {}).get("observation_projection_allowed", False),
    },
    "signals": layer_status("data/signals/signals.json", "signals"),
    "relationships": layer_status("data/relationships/relationships.json", "relationships"),
    "risks": layer_status("data/risks/states.json", "states"),
    "scenarios": layer_status("data/scenarios/scenarios.json", "scenarios"),
    "forecasts": {
        "version": forecasts.get("version"),
        "internal_count": len(forecasts.get("forecasts", [])),
        "public_count": outlook_projection["metadata"]["public_forecast_count"],
        # Keep the legacy count field as the public count so older consumers
        # cannot mistake private Forecast population for published rows.
        "count": outlook_projection["metadata"]["public_forecast_count"],
        "state": "PILOT_PUBLIC_PROJECTION",
        "public_projection": True,
        "evaluation_state": outlook_projection["metadata"]["evaluation_state"],
    },
    "outcomes": layer_status("data/outcomes/outcomes.json", "outcomes"),
    "evaluation": {
        "version": load_json(ROOT / "data/evaluation/evaluation.json").get("version"),
        "count": len(load_json(ROOT / "data/evaluation/evaluation.json").get("evaluations", [])),
        "state": load_json(ROOT / "data/evaluation/evaluation.json").get("evaluation_state"),
        "public_projection": False,
    },
})

dump_json(docs/"data/source_summary.json", {
    "source_count": len(src.get("sources",[])),
    "configured_live_monitor_routes":len(monitor_projection["routes"]),
    "reviewed_change_count":len(changes.get("changes",[])),
    "live_intelligence_schema_version":live_projection["metadata"]["schema_version"],
    "live_intelligence_population_state":live_projection["metadata"]["population_state"],
    "live_intelligence_internal_observation_count":live_projection["metadata"]["internal_observation_count"],
    "live_intelligence_public_observation_count":live_projection["metadata"]["public_observation_count"],
    "analysis_review_count":analysis_projection["metadata"]["review_count"],
    "risk_overlay_event_count":risk_projection["metadata"]["projected_event_count"],
    "risk_overlay_domain_count":risk_projection["metadata"]["risk_domain_count"],
    "risk_overlay_convergence_window_count":risk_projection["metadata"]["convergence_window_count"],
    "monitoring_tiers":ops_projection["source_governance_summary"]["monitoring_readiness_status"],
    # Runtime and retained review state are intentionally absent from public
    # Pages. The local operator build is the only surface that may include them.
    "public_runtime_projection": "CLOSED",
    "public_review_candidate_projection": "CLOSED",
    "biosecurity_mapped_series_count":biosecurity_projection["metadata"]["mapped_canonical_series_count"],
    "biosecurity_candidate_node_count":biosecurity_projection["metadata"]["candidate_node_count"],
})

(docs/".nojekyll").write_text("",encoding="utf-8")
print(
    f"Built static site for {projection['metadata']['record_count']} events, "
    f"{len(monitor_projection['routes'])} configured live monitor routes, "
    f"{len(src.get('sources',[]))} governed sources, "
    f"Live Intelligence {live_projection['metadata']['schema_version']} "
    f"({live_projection['metadata']['population_state']}; "
    f"{live_projection['metadata']['public_observation_count']} public observations), "
    f"{analysis_projection['metadata']['review_count']} analytical review(s), reviewed change history, "
    f"risk_overlay={risk_projection['metadata']['projected_event_count']}events/"
    f"{risk_projection['metadata']['risk_domain_count']}domains/"
    f"{risk_projection['metadata']['convergence_window_count']}density-windows, "
    f"ics={len(ical_build.included_occurrence_ids)}events/"
    f"{len(ical_build.omitted)}omitted, "
    f"biosecurity_overlay={biosecurity_projection['metadata']['mapped_canonical_series_count']}series/"
    f"{biosecurity_projection['metadata']['candidate_node_count']}candidates, "
    "runtime=CLOSED and review_candidates=CLOSED -> "
    f"{docs}"
)
