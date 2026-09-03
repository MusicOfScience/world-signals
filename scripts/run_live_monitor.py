from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from world_signals.adapters import (
    AdapterError,
    CBAM_PARENT_CELEX,
    CBAM_VERIFICATION_CELEX,
    CRA_CELEX,
    cellar_representation_diagnostics,
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
    before=file_hash(CANONICAL)
    registry=load_json(CANONICAL)
    expectations=load_json(EXPECTATIONS)
    configs=config_by_id(expectations)
    now=datetime.now(timezone.utc).isoformat()

    report={
        "project":"WORLD SIGNALS",
        "run_type":"LIVE_READ_ONLY_MONITOR",
        "run_at":now,
        "canonical_sha256_before":before,
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

    # CRA: immutable semantic baseline + machine-readable Cellar RDF legal topology.
    cra_config=configs["EU_CELLAR_CRA_ARTICLE_71"]
    cra_health={
        "adapter_id":"EU_CELLAR_CRA_ARTICLE_71","source_id":"WSSRC-TECH-001",
        "state":"HEALTHY","layers":{},
    }
    cra_degraded=False

    try:
        body,snap=fetch_cellar_celex_document(CRA_CELEX,language="eng")
        diagnostics=cellar_representation_diagnostics(body)
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

    # CBAM verifier milestone: semantic rule and current-law topology both live
    # on Delegated Regulation (EU) 2025/2551.
    _run_cbam_monitor(
        report,
        config=configs["EU_CBAM_VERIFICATION_RULE"],
        fetch_rule=fetch_cbam_verification_report_rule,
        compare_rule=cbam_legal_milestone_review_candidate,
        topology_celex=CBAM_VERIFICATION_CELEX,
        topology_layer_name="cellar_rdf_legal_topology",
    )

    # CBAM certificate sales: semantic baseline is the 2025 amending act, but
    # current-law topology must watch parent Regulation (EU) 2023/956 because a
    # future Article 20 change would normally amend the parent act.
    _run_cbam_monitor(
        report,
        config=configs["EU_CBAM_CERTIFICATE_SALE_RULE"],
        fetch_rule=fetch_cbam_certificate_sale_rule,
        compare_rule=cbam_legal_milestone_review_candidate,
        topology_celex=CBAM_PARENT_CELEX,
        topology_layer_name="parent_cellar_rdf_legal_topology",
    )

    # CBAM annual declaration + certificate surrender: Articles 6(1) and 22(1)
    # are parsed independently and must remain internally consistent. Their
    # current-law topology is the same parent Regulation (EU) 2023/956. Any
    # semantic or topology drift is review evidence only; no split/reschedule
    # or canonical mutation is automatic.
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
    MANIFEST.write_text(json.dumps({
        "generated_at":now,"candidate_count":len(candidate_files),"files":candidate_files,
        "automatic_canonical_commit":False,
    },indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

    after=file_hash(CANONICAL)
    report["canonical_sha256_after"]=after
    report["canonical_unchanged"]=before==after
    report["source_health_summary"]={
        "healthy":sum(1 for x in report["source_health"] if x["state"]=="HEALTHY"),
        "degraded":sum(1 for x in report["source_health"] if x["state"]!="HEALTHY"),
        "unique_source_ids":len({x["source_id"] for x in report["source_health"]}),
    }
    if before != after:
        report["status"]="FAIL_CANONICAL_GUARD"
        OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        print(json.dumps(report,indent=2,ensure_ascii=False))
        return 2

    report["status"]=(
        "REVIEW_REQUIRED" if report["review_candidates"]
        else "DEGRADED" if report["source_health_summary"]["degraded"]
        else "NO_CHANGE"
    )
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
