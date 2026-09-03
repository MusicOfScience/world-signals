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
    fetch_kenya_budget_policy_rule,
    fetch_rba_fsr,
    fetch_suin_metadata,
    fetch_suin_rows,
)

CANONICAL=ROOT/"data/canonical/registry.json"
ARTIFACT_DIR=ROOT/"artifacts"
ARTIFACT_DIR.mkdir(exist_ok=True)
OUT=ARTIFACT_DIR/"adapter-smoke.json"

def file_hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()

def main() -> int:
    before=file_hash(CANONICAL)
    report={
        "project":"WORLD SIGNALS",
        "run_type":"LIVE_OFFICIAL_ADAPTER_SMOKE",
        "run_at":datetime.now(timezone.utc).isoformat(),
        "canonical_sha256_before":before,
        "automatic_canonical_commit":False,
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

    try:
        rule,snap=fetch_kenya_budget_policy_rule()
        report["results"].append({
            "adapter":"KENYA_PFM_BPS_RULE",
            "status":"PASS",
            "snapshot":snap.as_dict(),
            "rule":rule.as_dict(),
            "monitor_role":"SEMANTIC_LEGAL_RULE_SENTINEL",
            "whole_document_hash_is_not_rule_change":True,
        })
    except AdapterError as exc:
        failures.append(str(exc))
        report["results"].append({"adapter":"KENYA_PFM_BPS_RULE","status":"FAIL","error":str(exc)})

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
