from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"data/sources/registry.json"
SOURCE_ID="WSSRC-TRD-005"


def main() -> int:
    data=json.loads(REGISTRY.read_text(encoding="utf-8"))
    if data.get("version") != "1.46":
        raise SystemExit(f"expected source registry v1.46, found {data.get('version')!r}")

    matches=[s for s in data.get("sources",[]) if s.get("source_id")==SOURCE_ID]
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one {SOURCE_ID}, found {len(matches)}")
    source=matches[0]

    expected={
        "monitoring_readiness_status":"ENDPOINT_TEST_PRIORITY",
        "runtime_health_state":"PILOT_RESEARCH_VERIFIED",
        "parser_type":"EURLEX_CBAM_RULE_PLUS_COMMISSION_IMPLEMENTATION_MONITOR",
        "parser_version":"cbam-rule-monitor-0.1",
        "licence_review_status":"CLEARED_COMMISSION_CC_BY_4_AND_EURLEX_LEGAL_ROUTE",
        "canonical_dependency_count":2,
        "endpoint_route_validation_state":"RUNTIME_EXECUTION_BLOCKED",
        "runtime_environment_health_state":"DNS_NETWORK_BLOCK",
    }
    for key,value in expected.items():
        if source.get(key) != value:
            raise SystemExit(
                f"precondition failed for {SOURCE_ID} {key}: expected {value!r}, found {source.get(key)!r}"
            )

    source["monitoring_readiness_status"]="PILOT_VALIDATED_NO_AUTO_COMMIT"
    source["runtime_health_state"]="PILOT_EXECUTED_HEALTHY"
    source["parser_type"]="CELLAR_CBAM_DUAL_RULE_PLUS_LEGAL_TOPOLOGY_MONITOR"
    source["parser_version"]="cbam-cellar-dual-rule-topology-0.2"
    source["monitoring_activation_status"]="PILOT_WITH_REVIEWED_COMMIT_ONLY"
    source["endpoint_route_validation_state"]="PILOT_VALIDATED_LIVE"
    source["runtime_environment_health_state"]="HEALTHY_GITHUB_ACTIONS"
    source["endpoint_route_validated_at"]="2026-09-03T20:01:45+10:00"
    source["last_successful_research_verification_at"]="2026-09-03T20:01:45+10:00"
    source["monitoring_readiness_assessed_at"]="2026-09-03"
    source["endpoint_route_summary"]=(
        "Live GitHub Actions validation passed for two independent CBAM legal sentinels. "
        "Verifier-report date uses Cellar XHTML CELEX 32025R2551 plus Cellar RDF legal topology on that act. "
        "Certificate-sale date uses Cellar XHTML CELEX 32025R2083 plus Cellar RDF current-law topology on parent Regulation 32023R0956. "
        "European Commission CBAM pages remain official implementation cross-check/fallback surfaces, not the primary legal-date parser."
    )
    source["runtime_execution_note"]=(
        "Credential-free Publications Office Cellar XHTML and inferred RDF transports are live-validated in GitHub Actions. "
        "The earlier local-container DNS/network block is retained as environment-specific historical evidence and no longer defines route readiness."
    )
    source["monitor_endpoints"]=[
        {
            "endpoint_role":"verifier_semantic_rule",
            "url":"https://publications.europa.eu/resource/celex/32025R2551",
            "transport":"CELLAR_XHTML_VIA_CELEX_CONTENT_NEGOTIATION",
            "completeness_scope":"IMMUTABLE_SECTION_2_17_3_SEMANTIC_BASELINE",
            "preferred_for_monitoring":True,
        },
        {
            "endpoint_role":"verifier_current_law_topology",
            "url":"https://publications.europa.eu/resource/celex/32025R2551",
            "transport":"CELLAR_INFERRED_RDF",
            "completeness_scope":"AMENDMENT_CORRIGENDUM_CONSOLIDATION_REPEAL_RELATIONS",
            "preferred_for_monitoring":True,
        },
        {
            "endpoint_role":"certificate_sale_semantic_rule",
            "url":"https://publications.europa.eu/resource/celex/32025R2083",
            "transport":"CELLAR_XHTML_VIA_CELEX_CONTENT_NEGOTIATION",
            "completeness_scope":"IMMUTABLE_ARTICLE_20_1_REPLACEMENT_SEMANTIC_BASELINE",
            "preferred_for_monitoring":True,
        },
        {
            "endpoint_role":"certificate_sale_parent_current_law_topology",
            "url":"https://publications.europa.eu/resource/celex/32023R0956",
            "transport":"CELLAR_INFERRED_RDF",
            "completeness_scope":"PARENT_ACT_AMENDMENT_CORRIGENDUM_CONSOLIDATION_REPEAL_RELATIONS",
            "preferred_for_monitoring":True,
        },
        {
            "endpoint_role":"commission_cbam_implementation_cross_check",
            "url":"https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism/cbam-verification_en",
            "transport":"HTML",
            "completeness_scope":"OFFICIAL_IMPLEMENTATION_GUIDANCE_AND_OPERATIONAL_TIMELINE",
            "preferred_for_monitoring":False,
        },
    ]

    data["version"]="1.47"
    REGISTRY.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "source_id":SOURCE_ID,
        "old_registry_version":"1.46",
        "new_registry_version":"1.47",
        "monitoring_readiness_status":source["monitoring_readiness_status"],
        "runtime_health_state":source["runtime_health_state"],
        "endpoint_route_validation_state":source["endpoint_route_validation_state"],
        "automatic_canonical_commit":False,
        "google_calendar_write":False,
    },indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
