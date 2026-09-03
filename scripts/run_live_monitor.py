from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from world_signals.adapters import (
    AdapterError,
    CBAM_PARENT_CELEX,
    CBAM_VERIFICATION_CELEX,
    CRA_CELEX,
    fetch_cbam_annual_declaration_surrender_rule,
    fetch_cbam_certificate_sale_rule,
    fetch_cbam_verification_report_rule,
    fetch_cellar_celex_document,
    fetch_cellar_rdf_notice,
    fetch_rba_fsr,
    fetch_suin_rows,
    normalize_cellar_legal_topology,
    parse_cra_article_71,
    parse_cellar_legal_relation_diagnostics,
)
from world_signals.io import load_json
from world_signals.legal_monitor import (
    cbam_annual_deadline_review_candidate,
    cbam_legal_milestone_review_candidate,
    cellar_legal_topology_review_candidate,
)
from world_signals.live_monitor import (
    colombia_legal_input_review_candidate,
    cra_legal_rule_review_candidate,
    rba_fsr_review_candidates,
)

CANONICAL=ROOT/"data/canonical/registry.json"
SOURCE_REGISTRY=ROOT/"data/sources/registry.json"
EXPECTATIONS=ROOT/"data/monitor/expectations.json"
ARTIFACT_DIR=ROOT/"artifacts"
REVIEW_DIR=ROOT/"review_candidates/live"
ARTIFACT_DIR.mkdir(exist_ok=True)
REVIEW_DIR.mkdir(parents=True,exist_ok=True)
OUT=ARTIFACT_DIR/"live-monitor.json"
MANIFEST=REVIEW_DIR/"manifest.json"


def file_hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def config_by_id(expectations: dict) -> dict[str,dict]:
    return {x["adapter_id"]:x for x in expectations.get("adapters",[])}


def workflow_context() -> dict:
    return {
        "github_run_id":os.getenv("GITHUB_RUN_ID"),
        "github_run_number":os.getenv("GITHUB_RUN_NUMBER"),
        "github_sha":os.getenv("GITHUB_SHA"),
        "github_event_name":os.getenv("GITHUB_EVENT_NAME"),
        "github_ref":os.getenv("GITHUB_REF"),
        "github_workflow":os.getenv("GITHUB_WORKFLOW"),
        "github_repository":os.getenv("GITHUB_REPOSITORY"),
    }


def _append_candidate(report: dict, candidate: dict | None, observation: dict) -> None:
    report["observations"].append(observation)
    if candidate:
        report["review_candidates"].append(candidate)


def _run_cbam_monitor(
    report: dict,
    *,
    config: dict,
    fetch_rule,
    compare_rule,
    topology_celex: str,
    topology_layer_name: str,
) -> None:
    adapter_id=config["adapter_id"]
    source_id=config["source_id"]
    health={
        "adapter_id":adapter_id,
        "source_id":source_id,
        "state":"HEALTHY",
        "layers":{},
    }
    degraded=False

    try:
        rule,snap=fetch_rule()
        health["layers"]["immutable_semantic_baseline"]={
            "state":"HEALTHY",
            "snapshot":snap.as_dict(),
            "rule":rule.as_dict(),
        }
        candidate,observation=compare_rule(rule,config)
        _append_candidate(report,candidate,observation)
    except AdapterError as exc:
        degraded=True
        health["layers"]["immutable_semantic_baseline"]={
            "state":"DEGRADED",
            "failure_stage":"SEMANTIC_BASELINE_FETCH_OR_PARSE",
            "error":str(exc),
            "canonical_action":"NONE",
        }

    try:
        rdf,snap=fetch_cellar_rdf_notice(topology_celex,inferred=True)
        relations=parse_cellar_legal_relation_diagnostics(rdf,base_celex=topology_celex)
        topology=normalize_cellar_legal_topology(relations,base_celex=topology_celex)
        health["layers"][topology_layer_name]={
            "state":"HEALTHY",
            "snapshot":snap.as_dict(),
            "topology":topology.as_dict(),
        }
        candidate,observation=cellar_legal_topology_review_candidate(topology,config)
        _append_candidate(report,candidate,observation)
    except AdapterError as exc:
        degraded=True
        health["layers"][topology_layer_name]={
            "state":"DEGRADED",
            "failure_stage":"RDF_FETCH_PARSE_OR_NORMALIZE",
            "error":str(exc),
            "canonical_action":"NONE",
        }

    if degraded:
        health["state"]="DEGRADED"
    report["source_health"].append(health)


def main() -> int:
    canonical_sha=file_hash(CANONICAL)
    source_registry_sha=file_hash(SOURCE_REGISTRY)
    expectations_sha=file_hash(EXPECTATIONS)
    registry=load_json(CANONICAL)
    source_registry=load_json(SOURCE_REGISTRY)
    expectations=load_json(EXPECTATIONS)
    configs=config_by_id(expectations)
    expected_adapter_ids=sorted(configs)
    now=datetime.now(timezone.utc).isoformat()
    configuration_fingerprint=sha256(
        (canonical_sha+"|"+source_registry_sha+"|"+expectations_sha).encode("utf-8")
    ).hexdigest()

    report={
        "project":"WORLD SIGNALS",
        "report_schema_version":"0.2",
        "run_type":"LIVE_READ_ONLY_MONITOR",
        "run_at":now,
        "workflow_context":workflow_context(),
        "canonical_registry_version":registry.get("version"),
        "source_registry_version":source_registry.get("version"),
        "monitor_expectations_version":expectations.get("version"),
        "configuration_fingerprint_sha256":configuration_fingerprint,
        "canonical_sha256_before":canonical_sha,
        "source_registry_sha256":source_registry_sha,
        "monitor_expectations_sha256":expectations_sha,
        "expected_adapter_ids":expected_adapter_ids,
        "automatic_canonical_commit":False,
        "google_calendar_write":False,
        "source_health":[],
        "observations":[],
        "review_candidates":[],
    }

    try:
        items,snap=fetch_rba_fsr()
        report["source_health"].append({
            "adapter_id":"RBA_FSR_RSS","source_id":"WSSRC-FIN-001",
            "state":"HEALTHY","snapshot":snap.as_dict(),"item_count":len(items),
        })
        candidates,observations=rba_fsr_review_candidates(
            registry.get("records",[]),items,configs["RBA_FSR_RSS"]
        )
        report["review_candidates"].extend(candidates)
        report["observations"].extend(observations)
    except AdapterError as exc:
        report["source_health"].append({
            "adapter_id":"RBA_FSR_RSS","source_id":"WSSRC-FIN-001",
            "state":"DEGRADED","error":str(exc),"canonical_action":"NONE",
        })

    try:
        rows,snap=fetch_suin_rows(
            where="tipo='DECRETO' AND n_mero='111' AND a_o='1996'",
            select="tipo,n_mero,a_o,sector,subtipo,vigencia,entidad,materia,art_culos",
            limit=10,
        )
        report["source_health"].append({
            "adapter_id":"COLOMBIA_SUIN_DECREE_111_1996","source_id":"WSSRC-REG4-001",
            "state":"HEALTHY","snapshot":snap.as_dict(),"row_count":len(rows),
        })
        candidate,observation=colombia_legal_input_review_candidate(
            rows,configs["COLOMBIA_SUIN_DECREE_111_1996"]
        )
        _append_candidate(report,candidate,observation)
    except AdapterError as exc:
        report["source_health"].append({
            "adapter_id":"COLOMBIA_SUIN_DECREE_111_1996","source_id":"WSSRC-REG4-001",
            "state":"DEGRADED","error":str(exc),"canonical_action":"NONE",
        })

    cra_config=configs["EU_CELLAR_CRA_ARTICLE_71"]
    cra_health={
        "adapter_id":"EU_CELLAR_CRA_ARTICLE_71","source_id":"WSSRC-TECH-001",
        "state":"HEALTHY","layers":{},
    }
    cra_degraded=False

    try:
        body,snap=fetch_cellar_celex_document(CRA_CELEX,language="eng")
        rule=parse_cra_article_71(body)
        cra_health["layers"]["immutable_baseline"]={
            "state":"HEALTHY","snapshot":snap.as_dict(),"rule":rule.as_dict(),
        }
        candidate,observation=cra_legal_rule_review_candidate(rule,cra_config)
        _append_candidate(report,candidate,observation)
    except AdapterError as exc:
        cra_degraded=True
        cra_health["layers"]["immutable_baseline"]={
            "state":"DEGRADED","failure_stage":"BASELINE_FETCH_OR_PARSE",
            "error":str(exc),"canonical_action":"NONE",
        }

    try:
        rdf,snap=fetch_cellar_rdf_notice(CRA_CELEX,inferred=True)
        relations=parse_cellar_legal_relation_diagnostics(rdf,base_celex=CRA_CELEX)
        topology=normalize_cellar_legal_topology(relations,base_celex=CRA_CELEX)
        cra_health["layers"]["cellar_rdf_legal_topology"]={
            "state":"HEALTHY","snapshot":snap.as_dict(),"topology":topology.as_dict(),
        }
        candidate,observation=cellar_legal_topology_review_candidate(topology,cra_config)
        _append_candidate(report,candidate,observation)
    except AdapterError as exc:
        cra_degraded=True
        cra_health["layers"]["cellar_rdf_legal_topology"]={
            "state":"DEGRADED","failure_stage":"RDF_FETCH_PARSE_OR_NORMALIZE",
            "error":str(exc),"canonical_action":"NONE",
        }

    if cra_degraded:
        cra_health["state"]="DEGRADED"
    report["source_health"].append(cra_health)

    _run_cbam_monitor(
        report,
        config=configs["EU_CBAM_VERIFICATION_RULE"],
        fetch_rule=fetch_cbam_verification_report_rule,
        compare_rule=cbam_legal_milestone_review_candidate,
        topology_celex=CBAM_VERIFICATION_CELEX,
        topology_layer_name="cellar_rdf_legal_topology",
    )

    _run_cbam_monitor(
        report,
        config=configs["EU_CBAM_CERTIFICATE_SALE_RULE"],
        fetch_rule=fetch_cbam_certificate_sale_rule,
        compare_rule=cbam_legal_milestone_review_candidate,
        topology_celex=CBAM_PARENT_CELEX,
        topology_layer_name="parent_cellar_rdf_legal_topology",
    )

    _run_cbam_monitor(
        report,
        config=configs["EU_CBAM_ANNUAL_DEADLINE_RULE"],
        fetch_rule=fetch_cbam_annual_declaration_surrender_rule,
        compare_rule=cbam_annual_deadline_review_candidate,
        topology_celex=CBAM_PARENT_CELEX,
        topology_layer_name="parent_cellar_rdf_legal_topology",
    )

    candidate_files=[]
    for candidate in report["review_candidates"]:
        cid=candidate["candidate_id"]
        path=REVIEW_DIR/f"{cid}.json"
        path.write_text(json.dumps(candidate,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        candidate_files.append(str(path.relative_to(ROOT)))

    observed_adapter_ids=sorted(x["adapter_id"] for x in report["source_health"])
    missing_expected=sorted(set(expected_adapter_ids)-set(observed_adapter_ids))
    unexpected_observed=sorted(set(observed_adapter_ids)-set(expected_adapter_ids))

    after=file_hash(CANONICAL)
    report["canonical_sha256_after"]=after
    report["canonical_unchanged"]=canonical_sha==after
    report["candidate_count"]=len(candidate_files)
    report["source_health_summary"]={
        "healthy":sum(1 for x in report["source_health"] if x["state"]=="HEALTHY"),
        "degraded":sum(1 for x in report["source_health"] if x["state"]!="HEALTHY"),
        "adapter_entries":len(report["source_health"]),
        "expected_adapter_entries":len(expected_adapter_ids),
        "unique_source_ids":len({x["source_id"] for x in report["source_health"]}),
        "observed_adapter_ids":observed_adapter_ids,
        "missing_expected_adapters":missing_expected,
        "unexpected_observed_adapters":unexpected_observed,
        "all_expected_adapters_observed":not missing_expected and not unexpected_observed,
    }

    manifest={
        "project":"WORLD SIGNALS",
        "generated_at":now,
        "workflow_context":report["workflow_context"],
        "canonical_registry_version":report["canonical_registry_version"],
        "source_registry_version":report["source_registry_version"],
        "monitor_expectations_version":report["monitor_expectations_version"],
        "configuration_fingerprint_sha256":configuration_fingerprint,
        "candidate_count":len(candidate_files),
        "files":candidate_files,
        "automatic_canonical_commit":False,
    }
    MANIFEST.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

    if canonical_sha != after:
        report["status"]="FAIL_CANONICAL_GUARD"
        OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        print(json.dumps(report,indent=2,ensure_ascii=False))
        return 2

    report["status"]=(
        "REVIEW_REQUIRED" if report["review_candidates"]
        else "DEGRADED" if report["source_health_summary"]["degraded"] or missing_expected or unexpected_observed
        else "NO_CHANGE"
    )
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
