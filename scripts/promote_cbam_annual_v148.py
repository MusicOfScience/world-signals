from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"data/sources/registry.json"
SOURCE_ID="WSSRC-TRD-006"


def main() -> int:
    data=json.loads(REGISTRY.read_text(encoding="utf-8"))
    if data.get("version") != "1.47":
        raise SystemExit(f"expected source registry v1.47, found {data.get('version')!r}")

    matches=[s for s in data.get("sources",[]) if s.get("source_id")==SOURCE_ID]
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one {SOURCE_ID}, found {len(matches)}")
    source=matches[0]

    expected={
        "monitoring_readiness_status":"ENDPOINT_TEST_PRIORITY",
        "runtime_health_state":"PILOT_RESEARCH_VERIFIED",
        "parser_type":"EURLEX_CBAM_RULE_PLUS_COMMISSION_IMPLEMENTATION_MONITOR",
        "licence_review_status":"CLEARED_COMMISSION_CC_BY_4_AND_EURLEX_LEGAL_ROUTE",
        "canonical_dependency_count":1,
        "automated_retrieval_permission":"PREFER_EURLEX_LEGAL_TEXT_COMMISSION_PAGE_FALLBACK",
    }
    for key,value in expected.items():
        if source.get(key) != value:
            raise SystemExit(
                f"precondition failed for {SOURCE_ID} {key}: expected {value!r}, found {source.get(key)!r}"
            )

    source["monitoring_readiness_status"]="PILOT_VALIDATED_NO_AUTO_COMMIT"
    source["runtime_health_state"]="PILOT_EXECUTED_HEALTHY"
    source["parser_type"]="CELLAR_CBAM_ANNUAL_PAIRED_RULE_PLUS_PARENT_TOPOLOGY_MONITOR"
    source["parser_version"]="cbam-annual-paired-rule-topology-0.2"
    source["monitoring_activation_status"]="PILOT_WITH_REVIEWED_COMMIT_ONLY"
    source["endpoint_route_validation_state"]="PILOT_VALIDATED_LIVE"
    source["runtime_environment_health_state"]="HEALTHY_GITHUB_ACTIONS"
    source["endpoint_route_validated_at"]="2026-09-03T22:08:10+10:00"
    source["last_successful_research_verification_at"]="2026-09-03T22:08:10+10:00"
    source["monitoring_readiness_assessed_at"]="2026-09-03"
    source["endpoint_route_summary"]=(
        "Live GitHub Actions validation passed for the paired annual CBAM deadline sentinel. "
        "Articles 6(1) and 22(1) are parsed independently from Cellar XHTML CELEX 32025R2083; "
        "both currently produce 30 September, first due in 2027 for the 2026 reference/import year. "
        "Current-law change detection uses Cellar inferred RDF topology on parent Regulation 32023R0956. "
        "Clause divergence, semantic date drift or parent-act topology change generate review evidence only."
    )
    source["runtime_execution_note"]=(
        "GitHub live-monitor run 43 completed with six adapters healthy, zero degraded routes, zero review candidates, "
        "canonical SHA unchanged and final status NO_CHANGE. Automatic canonical commit and Google Calendar writes remained disabled."
    )
    source["known_limitations"]=[
        *[x for x in (source.get("known_limitations") or []) if x],
        "The declaration and certificate-surrender obligations presently share one canonical deadline only because Articles 6(1) and 22(1) agree; future divergence requires human legal review before any split or reschedule.",
        "A Cellar topology change is review evidence, not proof that the tracked annual deadline changed."
    ]
    source["monitor_endpoints"]=[
        {
            "endpoint_role":"annual_paired_semantic_rule",
            "url":"https://publications.europa.eu/resource/celex/32025R2083",
            "transport":"CELLAR_XHTML_VIA_CELEX_CONTENT_NEGOTIATION",
            "completeness_scope":"IMMUTABLE_ARTICLE_6_1_AND_ARTICLE_22_1_REPLACEMENT_RULES",
            "preferred_for_monitoring":True,
        },
        {
            "endpoint_role":"annual_parent_current_law_topology",
            "url":"https://publications.europa.eu/resource/celex/32023R0956",
            "transport":"CELLAR_INFERRED_RDF",
            "completeness_scope":"PARENT_ACT_AMENDMENT_CORRIGENDUM_CONSOLIDATION_REPEAL_RELATIONS",
            "preferred_for_monitoring":True,
        },
        {
            "endpoint_role":"commission_cbam_implementation_cross_check",
            "url":"https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism/cbam-communication-and-news_en",
            "transport":"HTML",
            "completeness_scope":"OFFICIAL_IMPLEMENTATION_GUIDANCE_AND_OPERATIONAL_TIMELINE",
            "preferred_for_monitoring":False,
        },
    ]

    data["version"]="1.48"
    REGISTRY.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "source_id":SOURCE_ID,
        "old_registry_version":"1.47",
        "new_registry_version":"1.48",
        "monitoring_readiness_status":source["monitoring_readiness_status"],
        "runtime_health_state":source["runtime_health_state"],
        "endpoint_route_validation_state":source["endpoint_route_validation_state"],
        "automatic_canonical_commit":False,
        "google_calendar_write":False,
    },indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
