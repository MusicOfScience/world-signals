from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
import time
from zoneinfo import ZoneInfo

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
    fetch_bsp_media_releases_rss,
    fetch_cbsl_mpr_rss,
    fetch_cbn_mpc_calendar,
    fetch_cbam_verification_report_rule,
    fetch_cellar_celex_document,
    fetch_cellar_identifier_notice,
    fetch_cellar_rdf_notice,
    fetch_nass_asb_ical,
    fetch_nbs_native_latest_releases_rss,
    fetch_nz_election_robots_policy,
    fetch_nz_election_rss,
    fetch_ons_upcoming_releases,
    fetch_european_council_meetings_rss,
    fetch_eurostat_release_calendar,
    fetch_fao_release_calendar,
    fetch_fao_robots_policy,
    fetch_fed_monetary_policy_rss,
    fetch_indec_cpi_months,
    fetch_indec_robots_policy,
    fetch_japan_cpi_robots_policy,
    fetch_japan_cpi_schedule,
    fetch_japan_household_spending_data,
    fetch_japan_mof_news_rss,
    fetch_rba_fsr,
    fetch_sarb_publications_rss,
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
from world_signals.adapters.indec_calendar import INDEC_TIMEZONE

from world_signals.adapters.hmt_t1_content_api import fetch_hmt_t1_content_api
from world_signals.cbn_mpc_monitor import fetch_cbn_robots_policy
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
        hmt_state,hmt_snap=fetch_hmt_t1_content_api()
        report["results"].append({
            "adapter":"HMT_T1_CONTENT_API",
            "status":"PASS",
            "source_id":"WSSRC-MKT-014",
            "snapshot":hmt_snap.as_dict(),
            "content_id":hmt_state.content_id,
            "public_updated_at":hmt_state.public_updated_at,
            "withdrawn":hmt_state.withdrawn,
            "pending_markers":hmt_state.pending_markers,
            "semantic_sha256":hmt_state.semantic_sha256,
            "request_budget_per_run":1,
            "followup_request_count":0,
            "condition_state_authority":False,
            "automatic_commit_allowed":False,
        })
    except AdapterError as exc:
        failures.append(str(exc))
        report["results"].append({"adapter":"HMT_T1_CONTENT_API","status":"FAIL","source_id":"WSSRC-MKT-014","error":str(exc),"canonical_action":"NONE"})

    try:
        sarb_items,sarb_snap=fetch_sarb_publications_rss()
        report["results"].append({
            "adapter":"SARB_MPC_STATEMENTS_RSS",
            "status":"PASS",
            "source_id":"WSSRC-REG-013",
            "snapshot":sarb_snap.as_dict(),
            "item_count":len(sarb_items),
            "mpc_item_count":sum(1 for x in sarb_items if x.mpc_year is not None),
            "request_budget_per_run":1,
            "schedule_authority":False,
            "clock_authority":False,
            "lifecycle_authority":False,
            "automatic_commit_allowed":False,
        })
    except AdapterError as exc:
        failures.append(str(exc))
        report["results"].append({"adapter":"SARB_MPC_STATEMENTS_RSS","status":"FAIL","source_id":"WSSRC-REG-013","error":str(exc),"canonical_action":"NONE"})

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
        cbn_allowed,cbn_robots_snap=fetch_cbn_robots_policy()
        if not cbn_allowed:
            raise AdapterError("CBN robots policy disallows the MPC calendar path")
        cbn_calendar,cbn_calendar_snap=fetch_cbn_mpc_calendar()
        report["results"].append({
            "adapter":"CBN_MPC_CALENDAR",
            "status":"PASS",
            "source_id":"WSSRC-CB-014",
            "robots_snapshot":cbn_robots_snap.as_dict(),
            "calendar_snapshot":cbn_calendar_snap.as_dict(),
            "meeting_count":len(cbn_calendar.meetings),
            "schedule_sha256":cbn_calendar.schedule_sha256,
            "request_budget_per_run":2,
            "decision_publication_time_authority":False,
            "automatic_commit_allowed":False,
        })
    except AdapterError as exc:
        failures.append(str(exc))
        report["results"].append({
            "adapter":"CBN_MPC_CALENDAR",
            "status":"FAIL",
            "source_id":"WSSRC-CB-014",
            "error":str(exc),
            "canonical_action":"NONE",
        })

    try:
        fed_items,fed_snap=fetch_fed_monetary_policy_rss()
        report["results"].append({
            "adapter":"FED_MONETARY_POLICY_RSS",
            "status":"PASS",
            "source_id":"WSSRC-CB-015",
            "snapshot":fed_snap.as_dict(),
            "item_count":len(fed_items),
            "request_policy":"ONE_DEDICATED_FEED_REQUEST_PER_DAILY_MONITOR_RUN",
            "schedule_authority":False,
            "lifecycle_authority":False,
            "automatic_commit_allowed":False,
        })
    except AdapterError as exc:
        failures.append(str(exc))
        report["results"].append({
            "adapter":"FED_MONETARY_POLICY_RSS",
            "status":"FAIL",
            "source_id":"WSSRC-CB-015",
            "error":str(exc),
            "canonical_action":"NONE",
        })

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
        bsp_items,bsp_snap=fetch_bsp_media_releases_rss()
        report["results"].append({
            "adapter":"BSP_MONETARY_POLICY_RSS",
            "status":"PASS",
            "source_id":"WSSRC-REGJ-006",
            "snapshot":bsp_snap.as_dict(),
            "item_count":len(bsp_items),
            "request_policy":"ONE_OFFICIAL_RSS_REQUEST_PER_DAILY_MONITOR_RUN",
            "schedule_authority":False,
            "lifecycle_authority":False,
            "automatic_schedule_html_fetch_allowed":False,
        })
    except (AdapterError,ValueError) as exc:
        failures.append({"adapter":"BSP_MONETARY_POLICY_RSS","error":str(exc)})

    try:
        cbsl_items,cbsl_snap=fetch_cbsl_mpr_rss()
        report["results"].append({
            "adapter":"CBSL_MONETARY_POLICY_RSS",
            "status":"PASS",
            "source_id":"WSSRC-REGJ-007",
            "snapshot":cbsl_snap.as_dict(),
            "item_count":len(cbsl_items),
            "request_policy":"ONE_OFFICIAL_RSS_REQUEST_PER_DAILY_MONITOR_RUN",
            "item_link_followup_request_count":0,
            "schedule_authority":False,
            "rss_has_publication_clock":False,
            "automatic_item_link_fetch_allowed":False,
            "automatic_schedule_html_fetch_allowed":False,
            "automatic_commit_allowed":False,
        })
    except (AdapterError,ValueError) as exc:
        failures.append({"adapter":"CBSL_MONETARY_POLICY_RSS","error":str(exc)})

    try:
        nz_allowed,nz_delay,nz_robots_snap=fetch_nz_election_robots_policy()
        if not nz_allowed:
            raise AdapterError("Elections NZ robots policy disallows the advertised Media & News RSS path")
        time.sleep(nz_delay)
        nz_items,nz_rss_snap=fetch_nz_election_rss()
        report["results"].append({
            "adapter":"NZ_ELECTION_TIMETABLE_CHANGE_RSS",
            "status":"PASS",
            "source_id":"WSSRC-EL-NZ-002",
            "robots_snapshot":nz_robots_snap.as_dict(),
            "rss_snapshot":nz_rss_snap.as_dict(),
            "rolling_feed_item_count":len(nz_items),
            "request_budget_per_run":2,
            "robots_request_count":1,
            "rss_request_count":1,
            "inter_request_delay_seconds":nz_delay,
            "timetable_html_request_count":0,
            "item_followup_request_count":0,
            "results_data_request_count":0,
            "search_route_discovery_request_count":0,
            "rolling_feed_completeness":"FINITE_ROLLING_WINDOW_NOT_EXHAUSTIVE_CHANGE_LOG",
            "schedule_authority":False,
            "clock_authority":False,
            "lifecycle_authority":False,
            "certainty_authority":False,
            "canonical_date_mutation_allowed":False,
            "automatic_timetable_html_fetch_allowed":False,
            "automatic_item_link_fetch_allowed":False,
            "automatic_commit_allowed":False,
        })
    except (AdapterError,ValueError) as exc:
        failures.append({"adapter":"NZ_ELECTION_TIMETABLE_CHANGE_RSS","error":str(exc)})
        report["results"].append({
            "adapter":"NZ_ELECTION_TIMETABLE_CHANGE_RSS",
            "status":"FAIL",
            "source_id":"WSSRC-EL-NZ-002",
            "error":str(exc),
            "canonical_action":"NONE",
        })

    try:
        euco_items,euco_snap=fetch_european_council_meetings_rss()
        report["results"].append({
            "adapter":"EUROPEAN_COUNCIL_MEETINGS_RSS",
            "status":"PASS",
            "source_id":"WSSRC-INT-035",
            "snapshot":euco_snap.as_dict(),
            "item_count":len(euco_items),
            "request_budget_per_run":1,
            "rss_request_count":1,
            "robots_request_count":0,
            "direct_calendar_html_request_count":0,
            "item_followup_request_count":0,
            "search_route_discovery_request_count":0,
            "feed_item_count_is_permanent_invariant":False,
            "observed_date_source":"OFFICIAL_RSS_ITEM_LINK_PATH_ONLY",
            "updated_field_is_event_time":False,
            "description_field_is_event_time":False,
            "schedule_authority":False,
            "clock_authority":False,
            "lifecycle_authority":False,
            "certainty_authority":False,
            "canonical_date_mutation_allowed":False,
            "automatic_calendar_html_fetch_allowed":False,
            "automatic_item_link_fetch_allowed":False,
            "automatic_new_occurrence_creation_allowed":False,
            "automatic_commit_allowed":False,
        })
    except (AdapterError,ValueError) as exc:
        failures.append({"adapter":"EUROPEAN_COUNCIL_MEETINGS_RSS","error":str(exc)})
        report["results"].append({
            "adapter":"EUROPEAN_COUNCIL_MEETINGS_RSS",
            "status":"FAIL",
            "source_id":"WSSRC-INT-035",
            "error":str(exc),
            "canonical_action":"NONE",
        })

    try:
        nass_items,nass_snap=fetch_nass_asb_ical()
        report["results"].append({
            "adapter":"USDA_NASS_ASB_ICAL",
            "status":"PASS",
            "source_id":"WSSRC-COM-005",
            "snapshot":nass_snap.as_dict(),
            "target_item_count":len(nass_items),
            "request_budget_per_run":1,
            "ical_request_count":1,
            "robots_request_count":0,
            "calendar_html_request_count":0,
            "report_followup_request_count":0,
            "search_route_discovery_request_count":0,
            "floating_datetime_timezone":"America/New_York",
            "dtend_is_event_end":False,
            "dtstamp_is_event_time":False,
            "sequence_is_event_state":False,
            "schedule_authority":False,
            "clock_authority":False,
            "lifecycle_authority":False,
            "certainty_authority":False,
            "canonical_datetime_mutation_allowed":False,
            "automatic_commit_allowed":False,
        })
    except (AdapterError,ValueError) as exc:
        failures.append(str(exc))
        report["results"].append({
            "adapter":"USDA_NASS_ASB_ICAL",
            "status":"FAIL",
            "source_id":"WSSRC-COM-005",
            "error":str(exc),
            "canonical_action":"NONE",
        })

    try:
        nbs_items,nbs_snap=fetch_nbs_native_latest_releases_rss()
        report["results"].append({
            "adapter":"CHINA_NBS_LATEST_RELEASES_RSS",
            "status":"PASS",
            "source_id":"WSSRC-MAC-031",
            "snapshot":nbs_snap.as_dict(),
            "item_count":len(nbs_items),
            "request_budget_per_run":1,
            "native_rss_request_count":1,
            "schedule_request_count":0,
            "english_rss_request_count":0,
            "article_followup_request_count":0,
            "data_api_followup_request_count":0,
            "search_route_discovery_request_count":0,
            "schedule_authority":False,
            "clock_authority":False,
            "lifecycle_authority":False,
            "certainty_authority":False,
            "rss_publication_metadata_is_event_clock_authority":False,
            "canonical_clock_mutation_allowed":False,
            "automatic_item_link_fetch_allowed":False,
            "automatic_schedule_html_fetch_allowed":False,
            "automatic_english_rss_fetch_allowed":False,
            "automatic_commit_allowed":False,
        })
    except (AdapterError,ValueError) as exc:
        failures.append({"adapter":"CHINA_NBS_LATEST_RELEASES_RSS","error":str(exc)})
        report["results"].append({
            "adapter":"CHINA_NBS_LATEST_RELEASES_RSS",
            "status":"FAIL",
            "source_id":"WSSRC-MAC-031",
            "error":str(exc),
            "canonical_action":"NONE",
        })

    try:
        fao_months=["October 2026","November 2026","December 2026"]
        fao_allowed,fao_robots_snap=fetch_fao_robots_policy()
        if not fao_allowed:
            raise AdapterError("FAO robots policy disallows the release-calendar path")
        fao_items,fao_calendar_snap=fetch_fao_release_calendar(fao_months)
        report["results"].append({
            "adapter":"FAO_RELEASE_CALENDAR",
            "status":"PASS",
            "source_id":"WSSRC-COM-010",
            "robots_snapshot":fao_robots_snap.as_dict(),
            "calendar_snapshot":fao_calendar_snap.as_dict(),
            "item_count":len(fao_items),
            "request_budget_per_run":2,
            "robots_request_count":1,
            "calendar_request_count":1,
            "followup_request_count":0,
            "schedule_authority":False,
            "lifecycle_authority":False,
            "canonical_clock_mutation_allowed":False,
            "automatic_commit_allowed":False,
        })
    except (AdapterError,ValueError) as exc:
        failures.append({"adapter":"FAO_RELEASE_CALENDAR","error":str(exc)})

    try:
        indec_slugs=["Septiembre-2026","Octubre-2026","Noviembre-2026","Diciembre-2026"]
        indec_release_dates={
            "Septiembre-2026":"2026-09-10",
            "Octubre-2026":"2026-10-13",
            "Noviembre-2026":"2026-11-12",
            "Diciembre-2026":"2026-12-15",
        }
        indec_today=datetime.now(ZoneInfo(INDEC_TIMEZONE)).date()
        indec_retired_slugs={
            slug for slug,value in indec_release_dates.items()
            if datetime.fromisoformat(value).date() < indec_today
        }
        indec_allowed,indec_robots_snap=fetch_indec_robots_policy(indec_slugs)
        if not indec_allowed:
            raise AdapterError("INDEC robots policy disallows a configured CPI month route")
        indec_items,indec_snaps=fetch_indec_cpi_months(
            indec_slugs,
            allow_absent_month_slugs=indec_retired_slugs,
        )
        report["results"].append({
            "adapter":"INDEC_CPI_CALENDAR",
            "status":"PASS",
            "source_id":"WSSRC-REG2-009",
            "robots_snapshot":indec_robots_snap.as_dict(),
            "month_route_snapshots":[snap.as_dict() for snap in indec_snaps],
            "item_count":len(indec_items),
            "retired_month_slugs":sorted(indec_retired_slugs),
            "past_release_absence_is_not_event_state":True,
            "request_budget_per_run":5,
            "robots_request_count":1,
            "month_route_request_count":len(indec_snaps),
            "google_followup_request_count":0,
            "pdf_followup_request_count":0,
            "completed_release_followup_request_count":0,
            "search_route_request_count":0,
            "schedule_authority":False,
            "canonical_clock_mutation_allowed":False,
            "automatic_commit_allowed":False,
        })
    except (AdapterError,ValueError) as exc:
        failures.append({"adapter":"INDEC_CPI_CALENDAR","error":str(exc)})

    try:
        jgb_items,jgb_snap=fetch_japan_mof_news_rss()
        report["results"].append({
            "adapter":"JAPAN_MOF_JGB_RSS",
            "status":"PASS",
            "source_id":"WSSRC-FIS-029",
            "snapshot":jgb_snap.as_dict(),
            "item_count":len(jgb_items),
            "request_policy":"ONE_OFFICIAL_RSS_REQUEST_PER_DAILY_MONITOR_RUN",
            "schedule_authority":False,
            "automatic_calendar_html_fetch_allowed":False,
            "automatic_commit_allowed":False,
        })
    except AdapterError as exc:
        failures.append(str(exc))
        report["results"].append({
            "adapter":"JAPAN_MOF_JGB_RSS",
            "status":"FAIL",
            "source_id":"WSSRC-FIS-029",
            "error":str(exc),
            "canonical_action":"NONE",
        })

    try:
        jp_cpi_allowed,jp_cpi_robots_snap=fetch_japan_cpi_robots_policy()
        if not jp_cpi_allowed:
            raise AdapterError("Statistics Bureau robots policy disallows the registered CPI schedule path")
        jp_cpi_items,jp_cpi_schedule_snap=fetch_japan_cpi_schedule()
        report["results"].append({
            "adapter":"JAPAN_CPI_RELEASE_SCHEDULE",
            "status":"PASS",
            "source_id":"WSSRC-MAC-014",
            "robots_snapshot":jp_cpi_robots_snap.as_dict(),
            "schedule_snapshot":jp_cpi_schedule_snap.as_dict(),
            "national_schedule_row_count":len(jp_cpi_items),
            "request_budget_per_run":2,
            "robots_request_count":1,
            "schedule_request_count":1,
            "followup_request_count":0,
            "clock_authority":False,
            "lifecycle_authority":False,
            "certainty_authority":False,
            "canonical_clock_mutation_allowed":False,
            "automatic_commit_allowed":False,
        })
    except (AdapterError,ValueError) as exc:
        failures.append({"adapter":"JAPAN_CPI_RELEASE_SCHEDULE","error":str(exc)})

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
