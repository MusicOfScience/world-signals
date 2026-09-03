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
    fetch_cellar_identifier_notice,
    fetch_cellar_rdf_notice,
    fetch_rba_fsr,
    fetch_suin_metadata,
    fetch_suin_rows,
    parse_cra_article_71,
    parse_cellar_identifier_notice,
    parse_cellar_legal_relation_diagnostics,
)

CANONICAL=ROOT/"data/canonical/registry.json"
ARTIFACT_DIR=ROOT/"artifacts"
ARTIFACT_DIR.mkdir(exist_ok=True)
OUT=ARTIFACT_DIR/"adapter-smoke.json"


def file_hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _unique(values):
    out=[]
    for value in values:
        if value not in out:
            out.append(value)
    return out


def main() -> int:
    before=file_hash(CANONICAL)
    report={
        "project":"WORLD SIGNALS",
        "run_type":"LIVE_OFFICIAL_ADAPTER_SMOKE",
        "run_at":datetime.now(timezone.utc).isoformat(),
        "canonical_sha256_before":before,
        "automatic_canonical_commit":False,
        "google_calendar_write":False,
        "scope":"LIVE_ROUTES_ONLY_PLUS_ENDPOINT_CANDIDATE_PROBES",
        "held_routes_excluded":[
            "KENYA_PFM_BPS_RULE",
            "EU_CRA_CURRENT_ELI_HTML_HTTP_202_ROUTE"
        ],
        "results":[],
    }
    failures=[]

    try:
        items,snap=fetch_rba_fsr()
        report["results"].append({
            "adapter":"RBA_FSR_RSS",
            "status":"PASS",
            "snapshot":snap.as_dict(),
            "item_count":len(items),
            "latest_items":[i.as_dict() for i in items[:3]],
        })
    except AdapterError as exc:
        failures.append(str(exc))
        report["results"].append({"adapter":"RBA_FSR_RSS","status":"FAIL","error":str(exc)})

    try:
        meta,snap=fetch_suin_metadata()
        report["results"].append({
            "adapter":"COLOMBIA_SUIN_SOCRATA_METADATA",
            "status":"PASS",
            "snapshot":snap.as_dict(),
            "metadata":meta.as_dict(),
        })
    except AdapterError as exc:
        failures.append(str(exc))
        report["results"].append({"adapter":"COLOMBIA_SUIN_SOCRATA_METADATA","status":"FAIL","error":str(exc)})

    try:
        rows,snap=fetch_suin_rows(
            where="tipo='DECRETO' AND n_mero='111' AND a_o='1996'",
            select="tipo,n_mero,a_o,sector,subtipo,vigencia,entidad,materia,art_culos",
            limit=10,
        )
        if len(rows) != 1:
            raise AdapterError(f"SUIN expected exactly one DECRETO 111/1996 row, found {len(rows)}")
        report["results"].append({
            "adapter":"COLOMBIA_SUIN_DECREE_111_1996",
            "status":"PASS",
            "snapshot":snap.as_dict(),
            "row_count":len(rows),
            "rows":rows,
            "monitor_role":"LEGAL_INSTRUMENT_PRESENCE_VERSION_SENTINEL_ONLY",
            "clause_level_authority_required":True,
        })
    except AdapterError as exc:
        failures.append(str(exc))
        report["results"].append({"adapter":"COLOMBIA_SUIN_DECREE_111_1996","status":"FAIL","error":str(exc)})

    cra_result={
        "adapter":"EU_CRA_LEGAL_MONITOR",
        "status":"PASS",
        "canonical_occurrence_ids":["WSO-TECH-A-0001","WSO-TECH-A-0007"],
        "automatic_commit_allowed":False,
        "layers":{},
    }
    cra_failed=False

    try:
        body,snap=fetch_cellar_celex_document(CRA_CELEX,language="eng")
        diagnostics=cellar_representation_diagnostics(body)
        rule=parse_cra_article_71(body)
        cra_result["layers"]["immutable_baseline"]={
            "status":"PASS",
            "snapshot":snap.as_dict(),
            "representation_diagnostics":diagnostics,
            "rule":rule.as_dict(),
        }
    except AdapterError as exc:
        cra_failed=True
        failures.append("CRA immutable baseline: "+str(exc))
        cra_result["layers"]["immutable_baseline"]={
            "status":"FAIL","error":str(exc),"canonical_action":"NONE",
        }

    try:
        rdf,snap=fetch_cellar_rdf_notice(CRA_CELEX,inferred=True)
        relations=parse_cellar_legal_relation_diagnostics(rdf,base_celex=CRA_CELEX)
        if not relations:
            raise AdapterError("Cellar inferred RDF exposed no legal relations for CRA")

        incoming_amendment_targets=_unique(
            r["target_uri"] for r in relations
            if r["predicate"] in {"amended_by","resource_legal_amended_by_resource_legal"}
            and (r.get("subject_uri") or "").endswith("/celex/"+CRA_CELEX)
        )
        consolidation_targets=_unique(
            r["target_uri"] for r in relations
            if r["predicate"] in {"consolidated_by","resource_legal_consolidated_by_act_consolidated"}
            and "_" not in r["target_uri"].rsplit("/",1)[-1]
            and (r.get("subject_uri") or "").endswith("/celex/"+CRA_CELEX)
        )
        if not incoming_amendment_targets:
            raise AdapterError("CRA Cellar RDF exposed no incoming amendment relation")
        if not consolidation_targets:
            raise AdapterError("CRA Cellar RDF exposed no root consolidation relation")

        resolved=[]
        for role,targets in (
            ("incoming_amendment",incoming_amendment_targets),
            ("consolidation",consolidation_targets),
        ):
            for target in targets:
                notice,notice_snap=fetch_cellar_identifier_notice(target)
                identifiers=parse_cellar_identifier_notice(notice)
                if not identifiers["celex_ids"]:
                    raise AdapterError(f"Cellar identifier notice exposed no CELEX synonym for {target}")
                resolved.append({
                    "role":role,
                    "target_uri":target,
                    "identifier_snapshot":notice_snap.as_dict(),
                    "identifiers":identifiers,
                })

        cra_result["layers"]["cellar_rdf_relation_probe"]={
            "status":"PASS",
            "route_state":"ENDPOINT_CANDIDATE_NOT_YET_PROMOTED",
            "snapshot":snap.as_dict(),
            "relation_count":len(relations),
            "incoming_amendment_targets":incoming_amendment_targets,
            "consolidation_targets":consolidation_targets,
            "resolved_targets":resolved,
        }
    except AdapterError as exc:
        cra_failed=True
        failures.append("CRA Cellar RDF relation probe: "+str(exc))
        cra_result["layers"]["cellar_rdf_relation_probe"]={
            "status":"FAIL",
            "route_state":"ENDPOINT_CANDIDATE_NOT_YET_PROMOTED",
            "error":str(exc),
            "canonical_action":"NONE",
        }

    if cra_failed:
        cra_result["status"]="FAIL"
    report["results"].append(cra_result)

    after=file_hash(CANONICAL)
    report["canonical_sha256_after"]=after
    report["canonical_unchanged"]=before==after
    if before!=after:
        failures.append("canonical registry hash changed during read-only adapter smoke")
    report["status"]="PASS" if not failures else "FAIL"
    report["failures"]=failures
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return 0 if not failures else 1


if __name__=="__main__":
    raise SystemExit(main())
