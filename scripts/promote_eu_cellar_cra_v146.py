from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"data/sources/registry.json"
SOURCE_ID="WSSRC-TECH-001"


def main() -> int:
    data=json.loads(REGISTRY.read_text(encoding="utf-8"))
    if data.get("version") != "1.45":
        raise SystemExit(f"expected source registry v1.45, found {data.get('version')!r}")

    matches=[s for s in data.get("sources",[]) if s.get("source_id")==SOURCE_ID]
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one {SOURCE_ID}, found {len(matches)}")
    source=matches[0]

    expected={
        "monitoring_readiness_status":"ENDPOINT_TEST_PRIORITY",
        "runtime_health_state":"PILOT_RESEARCH_VERIFIED",
        "parser_type":"EURLEX_CELLAR_RSS_LEGAL_RULE_MONITOR",
        "parser_version":"eurlex-tech-0.1",
        "licence_review_status":"CLEARED_EURLEX_REUSE_AND_CC_BY_EU_OWNED_CONTENT",
        "canonical_dependency_count":2,
    }
    for key,value in expected.items():
        if source.get(key) != value:
            raise SystemExit(f"precondition failed for {SOURCE_ID} {key}: expected {value!r}, found {source.get(key)!r}")

    source["monitoring_readiness_status"]="PILOT_VALIDATED_NO_AUTO_COMMIT"
    source["runtime_health_state"]="PILOT_EXECUTED_HEALTHY"
    source["parser_type"]="CELLAR_XHTML_CRA_ARTICLE71_SEMANTIC_RULE_MONITOR"
    source["parser_version"]="cellar-cra-article71-0.2"
    source["automated_retrieval_permission"]="OFFICIAL_CELLAR_REST_CELEX_XHTML_CREDENTIAL_FREE"
    source["last_successful_research_verification_at"]="2026-09-03T16:05:42+10:00"
    data["version"]="1.46"

    REGISTRY.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "source_id":SOURCE_ID,
        "old_registry_version":"1.45",
        "new_registry_version":"1.46",
        "monitoring_readiness_status":source["monitoring_readiness_status"],
        "runtime_health_state":source["runtime_health_state"],
        "automatic_canonical_commit":False,
    },indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
