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
    CRA_CELEX,
    cellar_representation_diagnostics,
    fetch_cellar_celex_document,
    fetch_eli_current_document,
    fetch_rba_fsr,
    fetch_suin_rows,
    parse_cra_article_71,
    parse_eli_current_state,
)
from world_signals.io import load_json
from world_signals.live_monitor import (
    colombia_legal_input_review_candidate,
    cra_legal_rule_review_candidate,
    eli_legal_state_review_candidate,
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

    # RBA FSR: positive publication evidence only. Feed absence never implies cancellation.
    try:
        items,snap=fetch_rba_fsr()
        report["source_health"].append({
            "adapter_id":"RBA_FSR_RSS",
            "source_id":"WSSRC-FIN-001",
            "state":"HEALTHY",
            "snapshot":snap.as_dict(),
            "item_count":len(items),
        })
        candidates,observations=rba_fsr_review_candidates(
            registry.get("records",[]),items,configs["RBA_FSR_RSS"]
        )
        report["review_candidates"].extend(candidates)
        report["observations"].extend(observations)
    except AdapterError as exc:
        message=str(exc)
        print(f"::warning::RBA FSR source degraded: {message}")
        report["source_health"].append({
            "adapter_id":"RBA_FSR_RSS",
            "source_id":"WSSRC-FIN-001",
            "state":"DEGRADED",
            "error":message,
            "canonical_action":"NONE",
        })

    # Colombia SUIN: typed legal-instrument presence/version sentinel only.
    # Any change is routed to clause-level manual verification, never directly to the event date.
    try:
        rows,snap=fetch_suin_rows(
            where="tipo='DECRETO' AND n_mero='111' AND a_o='1996'",
            select="tipo,n_mero,a_o,sector,subtipo,vigencia,entidad,materia,art_culos",
            limit=10,
        )
        report["source_health"].append({
            "adapter_id":"COLOMBIA_SUIN_DECREE_111_1996",
            "source_id":"WSSRC-REG4-001",
            "state":"HEALTHY",
            "snapshot":snap.as_dict(),
            "row_count":len(rows),
        })
        candidate,observation=colombia_legal_input_review_candidate(
            rows,configs["COLOMBIA_SUIN_DECREE_111_1996"]
        )
        report["observations"].append(observation)
        if candidate:
            report["review_candidates"].append(candidate)
    except AdapterError as exc:
        message=str(exc)
        print(f"::warning::Colombia SUIN source degraded: {message}")
        report["source_health"].append({
            "adapter_id":"COLOMBIA_SUIN_DECREE_111_1996",
            "source_id":"WSSRC-REG4-001",
            "state":"DEGRADED",
            "error":message,
            "canonical_action":"NONE",
        })

    # EU CRA uses two deliberately distinct evidence layers:
    #   1) immutable CELEX enactment -> Article 71 semantic baseline;
    #   2) unversioned ELI -> current consolidation/modifier topology.
    # Neither layer is permitted to mutate canonical events.
    cra_config=configs["EU_CELLAR_CRA_ARTICLE_71"]
    cra_health={
        "adapter_id":"EU_CELLAR_CRA_ARTICLE_71",
        "source_id":"WSSRC-TECH-001",
        "state":"HEALTHY",
        "layers":{},
    }
    cra_degraded=False

    try:
        baseline_body,baseline_snap=fetch_cellar_celex_document(CRA_CELEX,language="eng")
        baseline_diag=cellar_representation_diagnostics(baseline_body)
        try:
            baseline_rule=parse_cra_article_71(baseline_body)
        except AdapterError as exc:
            cra_degraded=True
            cra_health["layers"]["immutable_baseline"]={
                "state":"DEGRADED",
                "failure_stage":"BASELINE_PARSE",
                "snapshot":baseline_snap.as_dict(),
                "representation_diagnostics":baseline_diag,
                "error":str(exc),
                "canonical_action":"NONE",
            }
        else:
            cra_health["layers"]["immutable_baseline"]={
                "state":"HEALTHY",
                "snapshot":baseline_snap.as_dict(),
                "representation_diagnostics":baseline_diag,
                "rule":baseline_rule.as_dict(),
            }
            candidate,observation=cra_legal_rule_review_candidate(baseline_rule,cra_config)
            report["observations"].append(observation)
            if candidate:
                report["review_candidates"].append(candidate)
    except AdapterError as exc:
        cra_degraded=True
        cra_health["layers"]["immutable_baseline"]={
            "state":"DEGRADED",
            "failure_stage":"BASELINE_FETCH",
            "error":str(exc),
            "canonical_action":"NONE",
        }

    try:
        current_body,current_snap=fetch_eli_current_document("reg",2024,2847,language="en")
        try:
            current_state=parse_eli_current_state(current_body,base_celex=CRA_CELEX)
        except AdapterError as exc:
            cra_degraded=True
            cra_health["layers"]["current_eli_state"]={
                "state":"DEGRADED",
                "failure_stage":"CURRENT_ELI_PARSE",
                "snapshot":current_snap.as_dict(),
                "error":str(exc),
                "canonical_action":"NONE",
            }
        else:
            cra_health["layers"]["current_eli_state"]={
                "state":"HEALTHY",
                "snapshot":current_snap.as_dict(),
                "eli_identifier":(cra_config.get("current_state_identity") or {}).get("eli_identifier"),
                "legal_state":current_state.as_dict(),
            }
            candidate,observation=eli_legal_state_review_candidate(current_state,cra_config)
            report["observations"].append(observation)
            if candidate:
                report["review_candidates"].append(candidate)
    except AdapterError as exc:
        cra_degraded=True
        cra_health["layers"]["current_eli_state"]={
            "state":"DEGRADED",
            "failure_stage":"CURRENT_ELI_FETCH",
            "error":str(exc),
            "canonical_action":"NONE",
        }

    if cra_degraded:
        cra_health["state"]="DEGRADED"
    report["source_health"].append(cra_health)

    # Candidate artefacts are outputs for review. They are not commits.
    candidate_files=[]
    for candidate in report["review_candidates"]:
        cid=candidate["candidate_id"]
        path=REVIEW_DIR/f"{cid}.json"
        path.write_text(json.dumps(candidate,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        candidate_files.append(str(path.relative_to(ROOT)))
    MANIFEST.write_text(json.dumps({
        "generated_at":now,
        "candidate_count":len(candidate_files),
        "files":candidate_files,
        "automatic_canonical_commit":False,
    },indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

    after=file_hash(CANONICAL)
    report["canonical_sha256_after"]=after
    report["canonical_unchanged"]=before==after
    report["source_health_summary"]={
        "healthy":sum(1 for x in report["source_health"] if x["state"]=="HEALTHY"),
        "degraded":sum(1 for x in report["source_health"] if x["state"]!="HEALTHY"),
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
