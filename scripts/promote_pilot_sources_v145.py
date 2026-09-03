from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"data/sources/registry.json"

EXPECTED_VERSION="1.44"
NEW_VERSION="1.45"

PROMOTIONS={
    "WSSRC-FIN-001":{
        "expected_readiness":"ENDPOINT_TEST_PRIORITY",
        "updates":{
            "parser_type":"RDF_RSS_PRIMARY_HTML_FALLBACK",
            "parser_version":"rba-fsr-0.2",
            "runtime_health_state":"LIVE_GITHUB_ACTIONS_FETCH_PARSE_PASS",
            "monitoring_readiness_status":"PILOT_VALIDATED_NO_AUTO_COMMIT",
            "monitoring_activation_status":"PILOT_READ_ONLY_LIVE_MONITOR_NO_AUTO_COMMIT",
            "endpoint_route_validation_state":"PARSER_VALIDATED",
            "runtime_environment_health_state":"HEALTHY",
            "live_adapter_id":"RBA_FSR_RSS",
            "live_validation_evidence":{
                "workflow":"Smoke WORLD SIGNALS live adapters",
                "successful_run_id":33713741562,
                "transport":"official RBA RDF/RSS XML",
                "result":"HTTP 200; RDF namespace-aware parser PASS",
                "canonical_mutation":False
            }
        }
    },
    "WSSRC-REG4-001":{
        "expected_readiness":"ENDPOINT_TEST_PRIORITY",
        "updates":{
            "parser_type":"SOCRATA_METADATA_AND_TYPED_INSTRUMENT_QUERY_PLUS_MANUAL_LEGAL_TEXT_VERIFICATION",
            "parser_version":"colombia-budget-law-0.2",
            "runtime_health_state":"LIVE_GITHUB_ACTIONS_FETCH_PARSE_PASS",
            "monitoring_readiness_status":"PILOT_VALIDATED_NO_AUTO_COMMIT",
            "monitoring_activation_status":"PILOT_READ_ONLY_LEGAL_VERSION_SENTINEL_NO_AUTO_COMMIT",
            "endpoint_route_validation_state":"PARSER_VALIDATED",
            "runtime_environment_health_state":"HEALTHY",
            "live_adapter_id":"COLOMBIA_SUIN_DECREE_111_1996",
            "live_validation_evidence":{
                "workflow":"Smoke WORLD SIGNALS live adapters",
                "successful_run_id":33715476979,
                "transport":"official Datos Abiertos Socrata JSON API",
                "result":"HTTP 200; metadata + typed DECRETO 111/1996 query PASS",
                "canonical_mutation":False
            },
            "legal_identity_note":"Number/year alone is not unique in SUIN inventory; monitor identity must include instrument type. Current sentinel is DECRETO 111/1996."
        }
    }
}

def main() -> int:
    data=json.loads(REGISTRY.read_text(encoding="utf-8"))
    if str(data.get("version")) != EXPECTED_VERSION:
        raise SystemExit(f"Refusing migration: expected source registry {EXPECTED_VERSION}, got {data.get('version')}")
    sources={s.get("source_id"):s for s in data.get("sources",[])}
    for source_id,spec in PROMOTIONS.items():
        if source_id not in sources:
            raise SystemExit(f"Refusing migration: missing source {source_id}")
        record=sources[source_id]
        current=record.get("monitoring_readiness_status")
        if current != spec["expected_readiness"]:
            raise SystemExit(f"Refusing migration: {source_id} readiness expected {spec['expected_readiness']}, got {current}")
        record.update(spec["updates"])
        record["live_validation_reviewed_at"]=datetime.now(timezone.utc).isoformat()
    data["version"]=NEW_VERSION
    REGISTRY.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"Promoted {', '.join(PROMOTIONS)}; source registry {EXPECTED_VERSION} -> {NEW_VERSION}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
