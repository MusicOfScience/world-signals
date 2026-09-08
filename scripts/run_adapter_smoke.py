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
    CBAM_CERTIFICATE_SALE_AMENDING_CELEX,
    CBAM_PARENT_CELEX,
    CBAM_VERIFICATION_CELEX,
    CRA_CELEX,
    cellar_representation_diagnostics,
    fetch_cbam_certificate_sale_rule,
    fetch_cbam_verification_report_rule,
    fetch_cellar_celex_document,
    fetch_cellar_identifier_notice,
    fetch_cellar_rdf_notice,
    fetch_ons_upcoming_releases,
    fetch_eurostat_release_calendar,
    fetch_japan_household_spending_data,
    fetch_rba_fsr,
    fetch_rba_monetary_policy_calendar,
    fetch_rba_board_schedule,
    validate_rba_calendar_alignment,
    fetch_suin_metadata,
    fetch_suin_rows,
    normalize_cellar_legal_topology,
    parse_cra_article_71,
    parse_cellar_identifier_notice,
    parse_cellar_legal_relation_diagnostics,
)

from world_signals.rba_mpb_monitor import fetch_rba_robots_policy, rba_schedule_path_disallowed

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
        "google_calendar_write":False,
        "scope":"LIVE_ROUTES_ONLY_PLUS_ENDPOINT_CANDIDATE_PROBES",
        "held_routes_excluded":[
            "KENYA_PFM_BPS_RULE",
            "EU_CRA_CURRENT_ELI_HTML_HTTP_202_ROUTE",
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
        robots_rules,robots_snap=fetch_rba_robots_policy()
        if rba_schedule_path_disallowed(robots_rules):
            raise AdapterError("RBA robots policy disallows /schedules-events/")
        rba_calendar,rba_calendar_snap=fetch_rba_monetary_policy_calendar()
        rba_board,rba_board_snap=fetch_rba_board_schedule()
        validate_rba_calendar_alignment(rba_calendar,rba_board)
        report["results"].append({
            "adapter":"RBA_MPB_CALENDAR",
            "status":"PASS",
            "source_id":"WSSRC-CB-002",
            "robots_snapshot":robots_snap.as_dict(),
            "calendar_snapshot":rba_calendar_snap.as_dict(),
            "board_snapshot":rba_board_snap.as_dict(),
            "calendar_event_count":len(rba_calendar.events),
            "board_window_count":len(rba_board),
            "schedule_sha256":rba_calendar.schedule_sha256,
            "request_budget_per_run":3,
            "automatic_commit_allowed":False,
        })
    except AdapterError as exc:
        failures.append(str(exc))
        report["results"].append({
            "adapter":"RBA_MPB_CALENDAR",
            "status":"FAIL",
            "source_id":"WSSRC-CB-002",
            "error":str(exc),
            "canonical_action":"NONE",
        })

    try:
        eurostat_items,eurostat_snap=fetch_eurostat_release_calendar()
        report["results"].append({
            "adapter":"EUROSTAT_RELEASE_CALENDAR_ICS",
            "status":"PASS",
            "source_id":"WSSRC-MAC-005",
            "snapshot":eurostat_snap.as_dict(),
            "item_count":len(eurostat_items),
            "feed_time_precision":"DAY",
            "uid_is_stable_identity":False,
            "automatic_commit_allowed":False,
        })
    except AdapterError as exc:
        failures.append(str(exc))
        report["results"].append({
            "adapter":"EUROSTAT_RELEASE_CALENDAR_ICS",
            "status":"FAIL",
            "source_id":"WSSRC-MAC-005",
            "error":str(exc),
            "canonical_action":"NONE",
        })

    try:
        jp_values,jp_snap=fetch_japan_household_spending_data(
            time_from="20260700",time_to="20270200"
        )
        report["results"].append({
            "adapter":"JAPAN_HHSPEND_STATISTICS_DASHBOARD_API",
            "status":"PASS",
            "source_id":"WSSRC-MAC-030",
            "snapshot":jp_snap.as_dict(),
            "value_count":len(jp_values),
            "reference_period_codes":[row.reference_period_code for row in jp_values],
            "request_policy":"ONE_BOUNDED_REQUEST_PER_MONITOR_RUN",
            "schedule_authority":False,
            "automatic_commit_allowed":False,
        })
    except AdapterError as exc:
        failures.append(str(exc))
        report["results"].append({
            "adapter":"JAPAN_HHSPEND_STATISTICS_DASHBOARD_API",
            "status":"FAIL",
            "source_id":"WSSRC-MAC-030",
            "error":str(exc),
            "canonical_action":"NONE",
        })

    try:
        ons_items,ons_snaps=fetch_ons_upcoming_releases()
        report["results"].append({
            "adapter":"ONS_RELEASE_CALENDAR_RSS",
            "status":"PASS",
            "source_id":"WSSRC-MAC-006",
            "snapshots":[snap.as_dict() for snap in ons_snaps],
            "page_count":len(ons_snaps),
            "item_count":len(ons_items),
            "rss_carries_certainty_status":False,
            "automatic_commit_allowed":False,
        })
    except AdapterError as exc:
        failures.append(str(exc))
        report["results"].append({
            "adapter":"ONS_RELEASE_CALENDAR_RSS",
            "status":"FAIL",
            "source_id":"WSSRC-MAC-006",
            "error":str(exc),
            "canonical_action":"NONE",
        })

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
        topology=normalize_cellar_legal_topology(relations,base_celex=CRA_CELEX)

        incoming_amendment_targets=list(topology.amendment_target_uris)
        consolidation_targets=list(topology.consolidation_target_uris)
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
            "route_state":"PILOT_VALIDATED_NO_AUTO_COMMIT",
            "snapshot":snap.as_dict(),
            "relation_count":len(relations),
            "normalized_topology":topology.as_dict(),
            "resolved_targets":resolved,
        }
    except AdapterError as exc:
        cra_failed=True
        failures.append("CRA Cellar RDF relation probe: "+str(exc))
        cra_result["layers"]["cellar_rdf_relation_probe"]={
            "status":"FAIL",
            "route_state":"PILOT_VALIDATED_NO_AUTO_COMMIT",
            "error":str(exc),
            "canonical_action":"NONE",
        }

    if cra_failed:
        cra_result["status"]="FAIL"
    report["results"].append(cra_result)

    cbam_verification={
        "adapter":"EU_CBAM_VERIFICATION_RULE",
        "status":"PASS",
        "source_id":"WSSRC-TRD-005",
        "canonical_occurrence_ids":["WSO-TRD-A-0006"],
        "automatic_commit_allowed":False,
        "layers":{},
    }
    cbam_verification_failed=False
    try:
        rule,snap=fetch_cbam_verification_report_rule()
        cbam_verification["layers"]["immutable_semantic_baseline"]={
            "status":"PASS",
            "snapshot":snap.as_dict(),
            "rule":rule.as_dict(),
        }
    except AdapterError as exc:
        cbam_verification_failed=True
        failures.append("CBAM verification semantic baseline: "+str(exc))
        cbam_verification["layers"]["immutable_semantic_baseline"]={
            "status":"FAIL","error":str(exc),"canonical_action":"NONE",
        }
    try:
        rdf,snap=fetch_cellar_rdf_notice(CBAM_VERIFICATION_CELEX,inferred=True)
        relations=parse_cellar_legal_relation_diagnostics(
            rdf,base_celex=CBAM_VERIFICATION_CELEX
        )
        topology=normalize_cellar_legal_topology(
            relations,base_celex=CBAM_VERIFICATION_CELEX
        )
        cbam_verification["layers"]["cellar_rdf_legal_topology"]={
            "status":"PASS",
            "route_state":"ENDPOINT_CANDIDATE_NOT_YET_PROMOTED",
            "snapshot":snap.as_dict(),
            "relation_count":len(relations),
            "topology":topology.as_dict(),
        }
    except AdapterError as exc:
        cbam_verification_failed=True
        failures.append("CBAM verification Cellar topology: "+str(exc))
        cbam_verification["layers"]["cellar_rdf_legal_topology"]={
            "status":"FAIL","error":str(exc),"canonical_action":"NONE",
        }
    if cbam_verification_failed:
        cbam_verification["status"]="FAIL"
    report["results"].append(cbam_verification)

    cbam_sale={
        "adapter":"EU_CBAM_CERTIFICATE_SALE_RULE",
        "status":"PASS",
        "source_id":"WSSRC-TRD-005",
        "canonical_occurrence_ids":["WSO-TRD-A-0007"],
        "automatic_commit_allowed":False,
        "layers":{},
    }
    cbam_sale_failed=False
    try:
        rule,snap=fetch_cbam_certificate_sale_rule()
        cbam_sale["layers"]["immutable_semantic_baseline"]={
            "status":"PASS",
            "snapshot":snap.as_dict(),
            "rule":rule.as_dict(),
        }
    except AdapterError as exc:
        cbam_sale_failed=True
        failures.append("CBAM certificate-sale semantic baseline: "+str(exc))
        cbam_sale["layers"]["immutable_semantic_baseline"]={
            "status":"FAIL","error":str(exc),"canonical_action":"NONE",
        }
    try:
        rdf,snap=fetch_cellar_rdf_notice(CBAM_PARENT_CELEX,inferred=True)
        relations=parse_cellar_legal_relation_diagnostics(rdf,base_celex=CBAM_PARENT_CELEX)
        topology=normalize_cellar_legal_topology(relations,base_celex=CBAM_PARENT_CELEX)
        cbam_sale["layers"]["parent_cellar_rdf_legal_topology"]={
            "status":"PASS",
            "route_state":"ENDPOINT_CANDIDATE_NOT_YET_PROMOTED",
            "snapshot":snap.as_dict(),
            "relation_count":len(relations),
            "topology":topology.as_dict(),
            "semantic_baseline_celex":CBAM_CERTIFICATE_SALE_AMENDING_CELEX,
        }
    except AdapterError as exc:
        cbam_sale_failed=True
        failures.append("CBAM parent Cellar topology: "+str(exc))
        cbam_sale["layers"]["parent_cellar_rdf_legal_topology"]={
            "status":"FAIL","error":str(exc),"canonical_action":"NONE",
        }
    if cbam_sale_failed:
        cbam_sale["status"]="FAIL"
    report["results"].append(cbam_sale)

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
