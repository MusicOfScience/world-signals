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
    fetch_cbam_annual_declaration_surrender_rule,
    fetch_cellar_rdf_notice,
    normalize_cellar_legal_topology,
    parse_cellar_legal_relation_diagnostics,
)

CANONICAL=ROOT/"data/canonical/registry.json"
ARTIFACT_DIR=ROOT/"artifacts"
ARTIFACT_DIR.mkdir(exist_ok=True)
OUT=ARTIFACT_DIR/"cbam-annual-smoke.json"


def file_hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def main() -> int:
    before=file_hash(CANONICAL)
    report={
        "project":"WORLD SIGNALS",
        "run_type":"CBAM_ANNUAL_DEADLINE_LIVE_OFFICIAL_SMOKE",
        "run_at":datetime.now(timezone.utc).isoformat(),
        "source_id":"WSSRC-TRD-006",
        "canonical_occurrence_ids":["WSO-TRD-A-0008"],
        "canonical_sha256_before":before,
        "automatic_canonical_commit":False,
        "google_calendar_write":False,
        "status":"PASS",
        "layers":{},
        "failures":[],
    }

    try:
        rule,snap=fetch_cbam_annual_declaration_surrender_rule()
        if not rule.shared_deadline_consistent:
            raise AdapterError(
                "Article 6(1) declaration and Article 22(1) surrender rules diverged; legal review required"
            )
        if rule.first_deadline_date != "2027-09-30":
            raise AdapterError(
                f"unexpected first annual CBAM deadline {rule.first_deadline_date!r}; expected reviewed pilot target 2027-09-30"
            )
        report["layers"]["paired_immutable_semantic_rule"]={
            "status":"PASS",
            "snapshot":snap.as_dict(),
            "rule":rule.as_dict(),
        }
    except AdapterError as exc:
        report["status"]="FAIL"
        report["failures"].append("CBAM annual paired semantic rule: "+str(exc))
        report["layers"]["paired_immutable_semantic_rule"]={
            "status":"FAIL","error":str(exc),"canonical_action":"NONE",
        }

    try:
        rdf,snap=fetch_cellar_rdf_notice(CBAM_PARENT_CELEX,inferred=True)
        relations=parse_cellar_legal_relation_diagnostics(rdf,base_celex=CBAM_PARENT_CELEX)
        topology=normalize_cellar_legal_topology(relations,base_celex=CBAM_PARENT_CELEX)
        report["layers"]["parent_cellar_rdf_legal_topology"]={
            "status":"PASS",
            "snapshot":snap.as_dict(),
            "relation_count":len(relations),
            "topology":topology.as_dict(),
        }
    except AdapterError as exc:
        report["status"]="FAIL"
        report["failures"].append("CBAM annual parent Cellar topology: "+str(exc))
        report["layers"]["parent_cellar_rdf_legal_topology"]={
            "status":"FAIL","error":str(exc),"canonical_action":"NONE",
        }

    after=file_hash(CANONICAL)
    report["canonical_sha256_after"]=after
    report["canonical_unchanged"]=before==after
    if before != after:
        report["status"]="FAIL"
        report["failures"].append("canonical registry hash changed during CBAM annual read-only smoke")

    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return 0 if report["status"]=="PASS" else 1


if __name__=="__main__":
    raise SystemExit(main())
