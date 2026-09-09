from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from world_signals.adapters import (
    AdapterError,
    CBAM_PARENT_CELEX,
    CBAM_VERIFICATION_CELEX,
    CRA_CELEX,
    fetch_cbam_annual_declaration_surrender_rule,
    fetch_bsp_media_releases_rss,
    fetch_cbsl_mpr_rss,
    fetch_cbn_mpc_calendar,
    fetch_cbam_certificate_sale_rule,
    fetch_cbam_verification_report_rule,
    fetch_cellar_celex_document,
    fetch_cellar_rdf_notice,
    fetch_eia_wpsr_schedule,
    fetch_european_council_meetings_rss,
    fetch_eurostat_release_calendar,
    fetch_fao_release_calendar,
    fetch_fao_robots_policy,
    fetch_fed_monetary_policy_rss,
    fetch_nbs_native_latest_releases_rss,
    fetch_nz_election_robots_policy,
    fetch_nz_election_rss,
    fetch_ons_upcoming_releases,
    fetch_indec_cpi_months,
    fetch_indec_robots_policy,
    fetch_japan_cpi_robots_policy,
    fetch_japan_cpi_schedule,
    fetch_japan_household_spending_data,
    fetch_japan_mof_news_rss,
    fetch_rba_fsr,
    fetch_rba_monetary_policy_calendar,
    fetch_rba_board_schedule,
    validate_rba_calendar_alignment,
    fetch_suin_rows,
    normalize_cellar_legal_topology,
    parse_cra_article_71,
    parse_cellar_legal_relation_diagnostics,
)
from world_signals.io import load_json
from world_signals.bsp_monetary_monitor import bsp_monetary_rss_review_candidates
from world_signals.cbsl_monetary_monitor import cbsl_mpr_rss_review_candidates
from world_signals.cbn_mpc_monitor import fetch_cbn_robots_policy, cbn_mpc_schedule_review_candidates
from world_signals.eurostat_monitor import eurostat_release_calendar_review_candidates
from world_signals.european_council_monitor import european_council_rss_review_candidates
from world_signals.fao_release_monitor import fao_release_calendar_review_candidates
from world_signals.fed_monetary_monitor import fed_monetary_rss_review_candidates
from world_signals.indec_cpi_monitor import indec_cpi_calendar_review_candidates
from world_signals.japan_mof_jgb_monitor import japan_mof_jgb_rss_review_candidates
from world_signals.japan_cpi_monitor import japan_cpi_schedule_review_candidates
from world_signals.japan_household_spending_monitor import japan_household_spending_review_candidates
from world_signals.nbs_release_monitor import nbs_native_rss_review_candidates
from world_signals.nz_election_monitor import nz_election_timetable_change_review_candidates
from world_signals.ons_monitor import ons_release_calendar_review_candidates
from world_signals.rba_mpb_monitor import (
    fetch_rba_robots_policy,
    rba_mpb_schedule_review_candidates,
    rba_schedule_path_disallowed,
)
from world_signals.legal_monitor import (
    cbam_annual_deadline_review_candidate,
    cbam_legal_milestone_review_candidate,
    cellar_legal_topology_review_candidate,
)
from world_signals.live_monitor import (
    colombia_legal_input_review_candidate,
    cra_legal_rule_review_candidate,
    eia_wpsr_schedule_review_candidate,
    rba_fsr_review_candidates,
)

CANONICAL=ROOT/"data/canonical/registry.json"
SOURCE_REGISTRY=ROOT/"data/sources/registry.json"
EXPECTATIONS=ROOT/"data/monitor/expectations.json"
OPERATIONS_POLICY=ROOT/"data/monitor/operations_policy.json"
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


def workflow_context() -> dict:
    return {
        "github_run_id":os.getenv("GITHUB_RUN_ID"),
        "github_run_number":os.getenv("GITHUB_RUN_NUMBER"),
        "github_sha":os.getenv("GITHUB_SHA"),
        "github_event_name":os.getenv("GITHUB_EVENT_NAME"),
        "github_ref":os.getenv("GITHUB_REF"),
        "github_workflow":os.getenv("GITHUB_WORKFLOW"),
        "github_repository":os.getenv("GITHUB_REPOSITORY"),
    }


def _append_candidate(report: dict, candidate: dict | None, observation: dict) -> None:
    report["observations"].append(observation)
    if candidate:
        report["review_candidates"].append(candidate)


def _run_cbam_monitor(
    report: dict,
    *,
    config: dict,
    fetch_rule,
    compare_rule,
    topology_celex: str,
    topology_layer_name: str,
) -> None:
    adapter_id=config["adapter_id"]
    source_id=config["source_id"]
    health={
        "adapter_id":adapter_id,
        "source_id":source_id,
        "state":"HEALTHY",
        "layers":{},
    }
    degraded=False

    try:
        rule,snap=fetch_rule()
        health["layers"]["immutable_semantic_baseline"]={
            "state":"HEALTHY",
            "snapshot":snap.as_dict(),
            "rule":rule.as_dict(),
        }
        candidate,observation=compare_rule(rule,config)
        _append_candidate(report,candidate,observation)
    except AdapterError as exc:
        degraded=True
        health["layers"]["immutable_semantic_baseline"]={
            "state":"DEGRADED",
            "failure_stage":"SEMANTIC_BASELINE_FETCH_OR_PARSE",
            "error":str(exc),
            "canonical_action":"NONE",
        }

    try:
        rdf,snap=fetch_cellar_rdf_notice(topology_celex,inferred=True)
        relations=parse_cellar_legal_relation_diagnostics(rdf,base_celex=topology_celex)
        topology=normalize_cellar_legal_topology(relations,base_celex=topology_celex)
        health["layers"][topology_layer_name]={
            "state":"HEALTHY",
            "snapshot":snap.as_dict(),
            "topology":topology.as_dict(),
        }
        candidate,observation=cellar_legal_topology_review_candidate(topology,config)
        _append_candidate(report,candidate,observation)
    except AdapterError as exc:
        degraded=True
        health["layers"][topology_layer_name]={
            "state":"DEGRADED",
            "failure_stage":"RDF_FETCH_PARSE_OR_NORMALIZE",
            "error":str(exc),
            "canonical_action":"NONE",
        }

    if degraded:
        health["state"]="DEGRADED"
    report["source_health"].append(health)


def main() -> int:
    canonical_sha=file_hash(CANONICAL)
    source_registry_sha=file_hash(SOURCE_REGISTRY)
    expectations_sha=file_hash(EXPECTATIONS)
    operations_policy_sha=file_hash(OPERATIONS_POLICY)
    registry=load_json(CANONICAL)
    source_registry=load_json(SOURCE_REGISTRY)
    expectations=load_json(EXPECTATIONS)
    operations_policy=load_json(OPERATIONS_POLICY)
    configs=config_by_id(expectations)
    expected_adapter_ids=sorted(configs)
    now=datetime.now(timezone.utc).isoformat()
    configuration_fingerprint=sha256(
        (
            canonical_sha+"|"+source_registry_sha+"|"+expectations_sha+"|"+operations_policy_sha
        ).encode("utf-8")
    ).hexdigest()

    report={
        "project":"WORLD SIGNALS",
        "report_schema_version":"0.3",
        "run_type":"LIVE_READ_ONLY_MONITOR",
        "run_at":now,
        "workflow_context":workflow_context(),
        "canonical_registry_version":registry.get("version"),
        "source_registry_version":source_registry.get("version"),
        "monitor_expectations_version":expectations.get("version"),
        "monitor_operations_policy_version":operations_policy.get("version"),
        "configuration_fingerprint_sha256":configuration_fingerprint,
        "canonical_sha256_before":canonical_sha,
        "source_registry_sha256":source_registry_sha,
        "monitor_expectations_sha256":expectations_sha,
        "monitor_operations_policy_sha256":operations_policy_sha,
        "expected_adapter_ids":expected_adapter_ids,
        "automatic_canonical_commit":False,
        "google_calendar_write":False,
        "source_health":[],
        "observations":[],
        "review_candidates":[],
    }

    try:
        items,snap=fetch_rba_fsr()
        report["source_health"].append({
            "adapter_id":"RBA_FSR_RSS","source_id":"WSSRC-FIN-001",
            "state":"HEALTHY","snapshot":snap.as_dict(),"item_count":len(items),
        })
        candidates,observations=rba_fsr_review_candidates(
            registry.get("records",[]),items,configs["RBA_FSR_RSS"]
        )
        report["review_candidates"].extend(candidates)
        report["observations"].extend(observations)
    except AdapterError as exc:
        report["source_health"].append({
            "adapter_id":"RBA_FSR_RSS","source_id":"WSSRC-FIN-001",
            "state":"DEGRADED","error":str(exc),"canonical_action":"NONE",
        })

    if "BSP_MONETARY_POLICY_RSS" in configs:
        bsp_config=configs["BSP_MONETARY_POLICY_RSS"]
        try:
            bsp_items,bsp_snap=fetch_bsp_media_releases_rss()
            report["source_health"].append({
                "adapter_id":"BSP_MONETARY_POLICY_RSS",
                "source_id":bsp_config["source_id"],
                "state":"HEALTHY",
                "snapshot":bsp_snap.as_dict(),
                "item_count":len(bsp_items),
                "request_budget_per_run":1,
                "schedule_authority":False,
                "lifecycle_authority":False,
                "certainty_authority":False,
                "rss_publication_time_is_event_time":False,
                "automatic_schedule_html_fetch_allowed":False,
                "automatic_commit_allowed":False,
            })
            candidates,observations=bsp_monetary_rss_review_candidates(
                registry.get("records",[]),bsp_items,bsp_config
            )
            report["review_candidates"].extend(candidates)
            report["observations"].extend(observations)
        except (AdapterError,ValueError) as exc:
            report["source_health"].append({
                "adapter_id":"BSP_MONETARY_POLICY_RSS",
                "source_id":bsp_config["source_id"],
                "state":"DEGRADED",
                "error":str(exc),
                "canonical_action":"NONE",
                "absence_is_not_event_state":True,
                "schedule_authority":False,
                "lifecycle_authority":False,
                "automatic_commit_allowed":False,
            })

    if "CBSL_MONETARY_POLICY_RSS" in configs:
        cbsl_config=configs["CBSL_MONETARY_POLICY_RSS"]
        try:
            cbsl_items,cbsl_snap=fetch_cbsl_mpr_rss()
            report["source_health"].append({
                "adapter_id":"CBSL_MONETARY_POLICY_RSS",
                "source_id":cbsl_config["source_id"],
                "state":"HEALTHY",
                "snapshot":cbsl_snap.as_dict(),
                "item_count":len(cbsl_items),
                "request_budget_per_run":1,
                "item_link_followup_request_count":0,
                "schedule_authority":False,
                "lifecycle_authority":False,
                "certainty_authority":False,
                "rss_has_publication_clock":False,
                "official_link_filename_date_is_clock_time":False,
                "automatic_item_link_fetch_allowed":False,
                "automatic_schedule_html_fetch_allowed":False,
                "automatic_commit_allowed":False,
            })
            candidates,observations=cbsl_mpr_rss_review_candidates(
                registry.get("records",[]),cbsl_items,cbsl_config
            )
            report["review_candidates"].extend(candidates)
            report["observations"].extend(observations)
        except (AdapterError,ValueError) as exc:
            report["source_health"].append({
                "adapter_id":"CBSL_MONETARY_POLICY_RSS",
                "source_id":cbsl_config["source_id"],
                "state":"DEGRADED",
                "error":str(exc),
                "canonical_action":"NONE",
                "absence_is_not_event_state":True,
                "schedule_authority":False,
                "lifecycle_authority":False,
                "rss_has_publication_clock":False,
                "automatic_item_link_fetch_allowed":False,
                "automatic_schedule_html_fetch_allowed":False,
                "automatic_commit_allowed":False,
            })

    if "NZ_ELECTION_TIMETABLE_CHANGE_RSS" in configs:
        nz_config=configs["NZ_ELECTION_TIMETABLE_CHANGE_RSS"]
        try:
            nz_allowed,nz_delay,nz_robots_snap=fetch_nz_election_robots_policy()
            if not nz_allowed:
                report["source_health"].append({
                    "adapter_id":"NZ_ELECTION_TIMETABLE_CHANGE_RSS",
                    "source_id":nz_config["source_id"],
                    "state":"DEGRADED",
                    "robots_snapshot":nz_robots_snap.as_dict(),
                    "failure_stage":"ROBOTS_POLICY_NOW_DISALLOWS_ADVERTISED_RSS",
                    "rss_request_skipped":True,
                    "request_count":1,
                    "canonical_action":"NONE",
                    "schedule_authority":False,
                    "clock_authority":False,
                    "lifecycle_authority":False,
                    "certainty_authority":False,
                    "automatic_timetable_html_fetch_allowed":False,
                    "automatic_item_link_fetch_allowed":False,
                    "automatic_commit_allowed":False,
                })
            else:
                time.sleep(nz_delay)
                nz_items,nz_rss_snap=fetch_nz_election_rss()
                report["source_health"].append({
                    "adapter_id":"NZ_ELECTION_TIMETABLE_CHANGE_RSS",
                    "source_id":nz_config["source_id"],
                    "state":"HEALTHY",
                    "robots_snapshot":nz_robots_snap.as_dict(),
                    "rss_snapshot":nz_rss_snap.as_dict(),
                    "rolling_feed_item_count":len(nz_items),
                    "request_budget_per_run":2,
                    "request_count":2,
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
                    "automatic_live_or_analysis_promotion_allowed":False,
                    "automatic_commit_allowed":False,
                })
                candidates,observations=nz_election_timetable_change_review_candidates(
                    registry.get("records",[]),nz_items,nz_config
                )
                report["review_candidates"].extend(candidates)
                report["observations"].extend(observations)
        except (AdapterError,ValueError) as exc:
            report["source_health"].append({
                "adapter_id":"NZ_ELECTION_TIMETABLE_CHANGE_RSS",
                "source_id":nz_config["source_id"],
                "state":"DEGRADED",
                "error":str(exc),
                "canonical_action":"NONE",
                "absence_is_not_event_state":True,
                "schedule_authority":False,
                "clock_authority":False,
                "lifecycle_authority":False,
                "certainty_authority":False,
                "canonical_date_mutation_allowed":False,
                "automatic_timetable_html_fetch_allowed":False,
                "automatic_item_link_fetch_allowed":False,
                "automatic_live_or_analysis_promotion_allowed":False,
                "automatic_commit_allowed":False,
            })

    if "EUROPEAN_COUNCIL_MEETINGS_RSS" in configs:
        euco_config=configs["EUROPEAN_COUNCIL_MEETINGS_RSS"]
        try:
            euco_items,euco_snap=fetch_european_council_meetings_rss()
            report["source_health"].append({
                "adapter_id":"EUROPEAN_COUNCIL_MEETINGS_RSS",
                "source_id":euco_config["source_id"],
                "state":"HEALTHY",
                "snapshot":euco_snap.as_dict(),
                "item_count":len(euco_items),
                "request_budget_per_run":1,
                "request_count":1,
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
                "automatic_live_or_analysis_promotion_allowed":False,
                "automatic_commit_allowed":False,
            })
            candidates,observations=european_council_rss_review_candidates(
                registry.get("records",[]),euco_items,euco_config
            )
            report["review_candidates"].extend(candidates)
            report["observations"].extend(observations)
        except (AdapterError,ValueError) as exc:
            report["source_health"].append({
                "adapter_id":"EUROPEAN_COUNCIL_MEETINGS_RSS",
                "source_id":euco_config["source_id"],
                "state":"DEGRADED",
                "error":str(exc),
                "canonical_action":"NONE",
                "absence_is_not_event_state":True,
                "schedule_authority":False,
                "clock_authority":False,
                "lifecycle_authority":False,
                "certainty_authority":False,
                "canonical_date_mutation_allowed":False,
                "automatic_calendar_html_fetch_allowed":False,
                "automatic_item_link_fetch_allowed":False,
                "automatic_new_occurrence_creation_allowed":False,
                "automatic_live_or_analysis_promotion_allowed":False,
                "automatic_commit_allowed":False,
            })

    if "CHINA_NBS_LATEST_RELEASES_RSS" in configs:
        nbs_config=configs["CHINA_NBS_LATEST_RELEASES_RSS"]
        try:
            nbs_items,nbs_snap=fetch_nbs_native_latest_releases_rss()
            report["source_health"].append({
                "adapter_id":"CHINA_NBS_LATEST_RELEASES_RSS",
                "source_id":nbs_config["source_id"],
                "state":"HEALTHY",
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
                "rss_publication_metadata_is_schedule_authority":False,
                "canonical_clock_mutation_allowed":False,
                "automatic_item_link_fetch_allowed":False,
                "automatic_schedule_html_fetch_allowed":False,
                "automatic_english_rss_fetch_allowed":False,
                "automatic_commit_allowed":False,
            })
            candidates,observations=nbs_native_rss_review_candidates(
                registry.get("records",[]),nbs_items,nbs_config
            )
            report["review_candidates"].extend(candidates)
            report["observations"].extend(observations)
        except (AdapterError,ValueError) as exc:
            report["source_health"].append({
                "adapter_id":"CHINA_NBS_LATEST_RELEASES_RSS",
                "source_id":nbs_config["source_id"],
                "state":"DEGRADED",
                "error":str(exc),
                "canonical_action":"NONE",
                "absence_is_not_event_state":True,
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

    if "FAO_RELEASE_CALENDAR" in configs:
        fao_config=configs["FAO_RELEASE_CALENDAR"]
        try:
            fao_allowed,fao_robots_snap=fetch_fao_robots_policy()
            if not fao_allowed:
                report["source_health"].append({
                    "adapter_id":"FAO_RELEASE_CALENDAR",
                    "source_id":fao_config["source_id"],
                    "state":"DEGRADED",
                    "robots_snapshot":fao_robots_snap.as_dict(),
                    "failure_stage":"ROBOTS_POLICY_NOW_DISALLOWS_FAO_RELEASE_CALENDAR",
                    "calendar_request_skipped":True,
                    "canonical_action":"NONE",
                    "automatic_commit_allowed":False,
                })
            else:
                fao_items,fao_calendar_snap=fetch_fao_release_calendar(
                    list(fao_config["configured_month_sections"])
                )
                report["source_health"].append({
                    "adapter_id":"FAO_RELEASE_CALENDAR",
                    "source_id":fao_config["source_id"],
                    "state":"HEALTHY",
                    "robots_snapshot":fao_robots_snap.as_dict(),
                    "calendar_snapshot":fao_calendar_snap.as_dict(),
                    "item_count":len(fao_items),
                    "request_budget_per_run":2,
                    "robots_request_count":1,
                    "calendar_request_count":1,
                    "followup_request_count":0,
                    "amis_followup_request_count":0,
                    "faostat_followup_request_count":0,
                    "pdf_followup_request_count":0,
                    "news_followup_request_count":0,
                    "search_route_request_count":0,
                    "schedule_authority":False,
                    "lifecycle_authority":False,
                    "certainty_authority":False,
                    "canonical_clock_mutation_allowed":False,
                    "automatic_commit_allowed":False,
                })
                candidates,observations=fao_release_calendar_review_candidates(
                    registry.get("records",[]),fao_items,fao_config
                )
                report["review_candidates"].extend(candidates)
                report["observations"].extend(observations)
        except (AdapterError,ValueError) as exc:
            report["source_health"].append({
                "adapter_id":"FAO_RELEASE_CALENDAR",
                "source_id":fao_config["source_id"],
                "state":"DEGRADED",
                "error":str(exc),
                "canonical_action":"NONE",
                "absence_is_not_event_state":True,
                "schedule_authority":False,
                "lifecycle_authority":False,
                "certainty_authority":False,
                "canonical_clock_mutation_allowed":False,
                "automatic_commit_allowed":False,
            })

    if "INDEC_CPI_CALENDAR" in configs:
        indec_config=configs["INDEC_CPI_CALENDAR"]
        try:
            indec_slugs=list(indec_config["month_slugs"])
            indec_allowed,indec_robots_snap=fetch_indec_robots_policy(indec_slugs)
            if not indec_allowed:
                report["source_health"].append({
                    "adapter_id":"INDEC_CPI_CALENDAR",
                    "source_id":indec_config["source_id"],
                    "state":"DEGRADED",
                    "robots_snapshot":indec_robots_snap.as_dict(),
                    "failure_stage":"ROBOTS_POLICY_NOW_DISALLOWS_CONFIGURED_INDEC_MONTH_ROUTE",
                    "month_route_requests_skipped":True,
                    "canonical_action":"NONE",
                    "automatic_commit_allowed":False,
                })
            else:
                indec_items,indec_snaps=fetch_indec_cpi_months(indec_slugs)
                report["source_health"].append({
                    "adapter_id":"INDEC_CPI_CALENDAR",
                    "source_id":indec_config["source_id"],
                    "state":"HEALTHY",
                    "robots_snapshot":indec_robots_snap.as_dict(),
                    "month_route_snapshots":[snap.as_dict() for snap in indec_snaps],
                    "item_count":len(indec_items),
                    "request_budget_per_run":5,
                    "robots_request_count":1,
                    "month_route_request_count":len(indec_snaps),
                    "google_followup_request_count":0,
                    "pdf_followup_request_count":0,
                    "completed_release_followup_request_count":0,
                    "search_route_request_count":0,
                    "schedule_authority":False,
                    "lifecycle_authority":False,
                    "certainty_authority":False,
                    "canonical_clock_mutation_allowed":False,
                    "automatic_commit_allowed":False,
                })
                candidates,observations=indec_cpi_calendar_review_candidates(
                    registry.get("records",[]),indec_items,indec_config
                )
                report["review_candidates"].extend(candidates)
                report["observations"].extend(observations)
        except (AdapterError,ValueError) as exc:
            report["source_health"].append({
                "adapter_id":"INDEC_CPI_CALENDAR",
                "source_id":indec_config["source_id"],
                "state":"DEGRADED",
                "error":str(exc),
                "canonical_action":"NONE",
                "absence_is_not_event_state":True,
                "schedule_authority":False,
                "lifecycle_authority":False,
                "certainty_authority":False,
                "canonical_clock_mutation_allowed":False,
                "automatic_commit_allowed":False,
            })

    if "CBN_MPC_CALENDAR" in configs:
        cbn_config=configs["CBN_MPC_CALENDAR"]
        try:
            cbn_allowed,cbn_robots_snap=fetch_cbn_robots_policy()
            if not cbn_allowed:
                report["source_health"].append({
                    "adapter_id":"CBN_MPC_CALENDAR",
                    "source_id":cbn_config["source_id"],
                    "state":"DEGRADED",
                    "robots_snapshot":cbn_robots_snap.as_dict(),
                    "failure_stage":"ROBOTS_POLICY_NOW_DISALLOWS_CBN_MPC_CALENDAR",
                    "calendar_request_skipped":True,
                    "canonical_action":"NONE",
                })
            else:
                cbn_calendar,cbn_calendar_snap=fetch_cbn_mpc_calendar()
                report["source_health"].append({
                    "adapter_id":"CBN_MPC_CALENDAR",
                    "source_id":cbn_config["source_id"],
                    "state":"HEALTHY",
                    "robots_snapshot":cbn_robots_snap.as_dict(),
                    "calendar_snapshot":cbn_calendar_snap.as_dict(),
                    "meeting_count":len(cbn_calendar.meetings),
                    "schedule_sha256":cbn_calendar.schedule_sha256,
                    "request_budget_per_run":2,
                    "decision_publication_time_authority":False,
                    "lifecycle_authority":False,
                    "automatic_commit_allowed":False,
                })
                candidates,observations=cbn_mpc_schedule_review_candidates(
                    registry.get("records",[]),cbn_calendar,cbn_config
                )
                report["review_candidates"].extend(candidates)
                report["observations"].extend(observations)
        except (AdapterError,ValueError) as exc:
            report["source_health"].append({
                "adapter_id":"CBN_MPC_CALENDAR",
                "source_id":cbn_config["source_id"],
                "state":"DEGRADED",
                "error":str(exc),
                "canonical_action":"NONE",
                "absence_is_not_event_state":True,
                "decision_publication_time_inference":"PROHIBITED",
            })

    if "FED_MONETARY_POLICY_RSS" in configs:
        fed_config=configs["FED_MONETARY_POLICY_RSS"]
        try:
            fed_items,fed_snap=fetch_fed_monetary_policy_rss()
            report["source_health"].append({
                "adapter_id":"FED_MONETARY_POLICY_RSS",
                "source_id":fed_config["source_id"],
                "state":"HEALTHY",
                "snapshot":fed_snap.as_dict(),
                "item_count":len(fed_items),
                "request_policy":"ONE_DEDICATED_FEED_REQUEST_PER_DAILY_MONITOR_RUN",
                "schedule_authority":False,
                "lifecycle_authority":False,
                "automatic_commit_allowed":False,
            })
            candidates,observations=fed_monetary_rss_review_candidates(
                registry.get("records",[]),fed_items,fed_config
            )
            report["review_candidates"].extend(candidates)
            report["observations"].extend(observations)
        except (AdapterError,ValueError) as exc:
            report["source_health"].append({
                "adapter_id":"FED_MONETARY_POLICY_RSS",
                "source_id":fed_config["source_id"],
                "state":"DEGRADED",
                "error":str(exc),
                "canonical_action":"NONE",
                "absence_is_not_event_state":True,
                "schedule_authority":False,
                "lifecycle_authority":False,
            })

    if "RBA_MPB_CALENDAR" in configs:
        rba_mpb_config=configs["RBA_MPB_CALENDAR"]
        try:
            robots_rules,robots_snap=fetch_rba_robots_policy()
            if rba_schedule_path_disallowed(robots_rules):
                report["source_health"].append({
                    "adapter_id":"RBA_MPB_CALENDAR",
                    "source_id":rba_mpb_config["source_id"],
                    "state":"DEGRADED",
                    "robots_snapshot":robots_snap.as_dict(),
                    "failure_stage":"ROBOTS_POLICY_NOW_DISALLOWS_SCHEDULE_PATH",
                    "schedule_requests_skipped":True,
                    "canonical_action":"NONE",
                })
            else:
                rba_calendar,rba_calendar_snap=fetch_rba_monetary_policy_calendar()
                rba_board,rba_board_snap=fetch_rba_board_schedule()
                validate_rba_calendar_alignment(rba_calendar,rba_board)
                report["source_health"].append({
                    "adapter_id":"RBA_MPB_CALENDAR",
                    "source_id":rba_mpb_config["source_id"],
                    "state":"HEALTHY",
                    "robots_snapshot":robots_snap.as_dict(),
                    "calendar_snapshot":rba_calendar_snap.as_dict(),
                    "board_snapshot":rba_board_snap.as_dict(),
                    "calendar_event_count":len(rba_calendar.events),
                    "board_window_count":len(rba_board),
                    "schedule_sha256":rba_calendar.schedule_sha256,
                    "request_budget_per_run":3,
                    "automatic_commit_allowed":False,
                })
                candidates,observations=rba_mpb_schedule_review_candidates(
                    registry.get("records",[]),rba_calendar,rba_board,rba_mpb_config
                )
                report["review_candidates"].extend(candidates)
                report["observations"].extend(observations)
        except (AdapterError,ValueError) as exc:
            report["source_health"].append({
                "adapter_id":"RBA_MPB_CALENDAR",
                "source_id":rba_mpb_config["source_id"],
                "state":"DEGRADED",
                "error":str(exc),
                "canonical_action":"NONE",
                "absence_is_not_event_state":True,
            })

    if "EIA_WPSR_SCHEDULE" in configs:
        eia_config=configs["EIA_WPSR_SCHEDULE"]
        try:
            schedule,snap=fetch_eia_wpsr_schedule()
            report["source_health"].append({
                "adapter_id":"EIA_WPSR_SCHEDULE",
                "source_id":eia_config["source_id"],
                "state":"HEALTHY",
                "snapshot":snap.as_dict(),
                "schedule":schedule.as_dict(),
                "completion_inference":"PROHIBITED",
            })
            candidate,observation=eia_wpsr_schedule_review_candidate(schedule,eia_config)
            _append_candidate(report,candidate,observation)
        except AdapterError as exc:
            report["source_health"].append({
                "adapter_id":"EIA_WPSR_SCHEDULE",
                "source_id":eia_config["source_id"],
                "state":"DEGRADED",
                "error":str(exc),
                "canonical_action":"NONE",
                "completion_inference":"PROHIBITED",
            })

    if "EUROSTAT_RELEASE_CALENDAR_ICS" in configs:
        eurostat_config=configs["EUROSTAT_RELEASE_CALENDAR_ICS"]
        try:
            eurostat_items,eurostat_snap=fetch_eurostat_release_calendar()
            report["source_health"].append({
                "adapter_id":"EUROSTAT_RELEASE_CALENDAR_ICS",
                "source_id":eurostat_config["source_id"],
                "state":"HEALTHY",
                "snapshot":eurostat_snap.as_dict(),
                "item_count":len(eurostat_items),
                "feed_time_precision":"DAY",
                "uid_is_stable_identity":False,
            })
            candidates,observations=eurostat_release_calendar_review_candidates(
                registry.get("records",[]),eurostat_items,eurostat_config
            )
            report["review_candidates"].extend(candidates)
            report["observations"].extend(observations)
        except (AdapterError,ValueError) as exc:
            report["source_health"].append({
                "adapter_id":"EUROSTAT_RELEASE_CALENDAR_ICS",
                "source_id":eurostat_config["source_id"],
                "state":"DEGRADED",
                "error":str(exc),
                "canonical_action":"NONE",
                "absence_is_not_event_state":True,
            })

    if "JAPAN_MOF_JGB_RSS" in configs:
        jgb_config=configs["JAPAN_MOF_JGB_RSS"]
        try:
            jgb_items,jgb_snap=fetch_japan_mof_news_rss()
            report["source_health"].append({
                "adapter_id":"JAPAN_MOF_JGB_RSS",
                "source_id":jgb_config["source_id"],
                "state":"HEALTHY",
                "snapshot":jgb_snap.as_dict(),
                "item_count":len(jgb_items),
                "request_policy":"ONE_OFFICIAL_RSS_REQUEST_PER_DAILY_MONITOR_RUN",
                "schedule_authority":False,
                "lifecycle_authority":False,
                "automatic_calendar_html_fetch_allowed":False,
                "automatic_commit_allowed":False,
            })
            candidates,observations=japan_mof_jgb_rss_review_candidates(
                registry.get("records",[]),jgb_items,jgb_config
            )
            report["review_candidates"].extend(candidates)
            report["observations"].extend(observations)
        except (AdapterError,ValueError) as exc:
            report["source_health"].append({
                "adapter_id":"JAPAN_MOF_JGB_RSS",
                "source_id":jgb_config["source_id"],
                "state":"DEGRADED",
                "error":str(exc),
                "canonical_action":"NONE",
                "absence_is_not_event_state":True,
                "schedule_authority":False,
                "lifecycle_authority":False,
                "automatic_calendar_html_fetch_allowed":False,
            })

    if "JAPAN_CPI_RELEASE_SCHEDULE" in configs:
        jp_cpi_config=configs["JAPAN_CPI_RELEASE_SCHEDULE"]
        try:
            jp_cpi_allowed,jp_cpi_robots_snap=fetch_japan_cpi_robots_policy()
            if not jp_cpi_allowed:
                report["source_health"].append({
                    "adapter_id":"JAPAN_CPI_RELEASE_SCHEDULE",
                    "source_id":jp_cpi_config["source_id"],
                    "state":"DEGRADED",
                    "robots_snapshot":jp_cpi_robots_snap.as_dict(),
                    "failure_stage":"ROBOTS_POLICY_NOW_DISALLOWS_REGISTERED_JAPAN_CPI_SCHEDULE",
                    "schedule_request_skipped":True,
                    "canonical_action":"NONE",
                    "clock_authority":False,
                    "lifecycle_authority":False,
                    "certainty_authority":False,
                    "automatic_commit_allowed":False,
                })
            else:
                jp_cpi_items,jp_cpi_schedule_snap=fetch_japan_cpi_schedule()
                report["source_health"].append({
                    "adapter_id":"JAPAN_CPI_RELEASE_SCHEDULE",
                    "source_id":jp_cpi_config["source_id"],
                    "state":"HEALTHY",
                    "robots_snapshot":jp_cpi_robots_snap.as_dict(),
                    "schedule_snapshot":jp_cpi_schedule_snap.as_dict(),
                    "national_schedule_row_count":len(jp_cpi_items),
                    "request_budget_per_run":2,
                    "robots_request_count":1,
                    "schedule_request_count":1,
                    "followup_request_count":0,
                    "tokyo_cpi_followup_request_count":0,
                    "estat_api_followup_request_count":0,
                    "data_release_followup_request_count":0,
                    "pdf_followup_request_count":0,
                    "news_followup_request_count":0,
                    "search_route_request_count":0,
                    "schedule_mutation_authority":False,
                    "clock_authority":False,
                    "lifecycle_authority":False,
                    "certainty_authority":False,
                    "canonical_clock_mutation_allowed":False,
                    "automatic_commit_allowed":False,
                })
                candidates,observations=japan_cpi_schedule_review_candidates(
                    registry.get("records",[]),jp_cpi_items,jp_cpi_config
                )
                report["review_candidates"].extend(candidates)
                report["observations"].extend(observations)
        except (AdapterError,ValueError) as exc:
            report["source_health"].append({
                "adapter_id":"JAPAN_CPI_RELEASE_SCHEDULE",
                "source_id":jp_cpi_config["source_id"],
                "state":"DEGRADED",
                "error":str(exc),
                "canonical_action":"NONE",
                "absence_is_not_event_state":True,
                "schedule_mutation_authority":False,
                "clock_authority":False,
                "lifecycle_authority":False,
                "certainty_authority":False,
                "canonical_clock_mutation_allowed":False,
                "automatic_commit_allowed":False,
            })

    if "JAPAN_HHSPEND_STATISTICS_DASHBOARD_API" in configs:
        jp_config=configs["JAPAN_HHSPEND_STATISTICS_DASHBOARD_API"]
        query=jp_config.get("api_query") or {}
        try:
            jp_values,jp_snap=fetch_japan_household_spending_data(
                time_from=query["time_from"],
                time_to=query["time_to"],
            )
            report["source_health"].append({
                "adapter_id":"JAPAN_HHSPEND_STATISTICS_DASHBOARD_API",
                "source_id":jp_config["source_id"],
                "state":"HEALTHY",
                "snapshot":jp_snap.as_dict(),
                "value_count":len(jp_values),
                "reference_period_codes":[row.reference_period_code for row in jp_values],
                "request_policy":"ONE_BOUNDED_REQUEST_PER_MONITOR_RUN",
                "schedule_authority":False,
            })
            candidates,observations=japan_household_spending_review_candidates(
                registry.get("records",[]),jp_values,jp_config
            )
            report["review_candidates"].extend(candidates)
            report["observations"].extend(observations)
        except (AdapterError,ValueError,KeyError) as exc:
            report["source_health"].append({
                "adapter_id":"JAPAN_HHSPEND_STATISTICS_DASHBOARD_API",
                "source_id":jp_config["source_id"],
                "state":"DEGRADED",
                "error":str(exc),
                "canonical_action":"NONE",
                "absence_is_not_event_state":True,
                "schedule_authority":False,
            })

    try:
        ons_items,ons_snaps=fetch_ons_upcoming_releases(
            limit=int((configs["ONS_RELEASE_CALENDAR_RSS"].get("feed") or {}).get("page_limit",100)),
            max_pages=int((configs["ONS_RELEASE_CALENDAR_RSS"].get("feed") or {}).get("max_pages",10)),
        )
        report["source_health"].append({
            "adapter_id":"ONS_RELEASE_CALENDAR_RSS",
            "source_id":configs["ONS_RELEASE_CALENDAR_RSS"]["source_id"],
            "state":"HEALTHY",
            "snapshots":[snap.as_dict() for snap in ons_snaps],
            "page_count":len(ons_snaps),
            "item_count":len(ons_items),
            "rss_carries_certainty_status":False,
        })
        candidates,observations=ons_release_calendar_review_candidates(
            registry.get("records",[]),ons_items,configs["ONS_RELEASE_CALENDAR_RSS"]
        )
        report["review_candidates"].extend(candidates)
        report["observations"].extend(observations)
    except (AdapterError,ValueError) as exc:
        report["source_health"].append({
            "adapter_id":"ONS_RELEASE_CALENDAR_RSS",
            "source_id":configs["ONS_RELEASE_CALENDAR_RSS"]["source_id"],
            "state":"DEGRADED",
            "error":str(exc),
            "canonical_action":"NONE",
            "absence_is_not_event_state":True,
        })

    try:
        rows,snap=fetch_suin_rows(
            where="tipo='DECRETO' AND n_mero='111' AND a_o='1996'",
            select="tipo,n_mero,a_o,sector,subtipo,vigencia,entidad,materia,art_culos",
            limit=10,
        )
        report["source_health"].append({
            "adapter_id":"COLOMBIA_SUIN_DECREE_111_1996","source_id":configs["COLOMBIA_SUIN_DECREE_111_1996"]["source_id"],
            "state":"HEALTHY","snapshot":snap.as_dict(),"row_count":len(rows),
        })
        candidate,observation=colombia_legal_input_review_candidate(
            rows,configs["COLOMBIA_SUIN_DECREE_111_1996"]
        )
        _append_candidate(report,candidate,observation)
    except AdapterError as exc:
        report["source_health"].append({
            "adapter_id":"COLOMBIA_SUIN_DECREE_111_1996","source_id":configs["COLOMBIA_SUIN_DECREE_111_1996"]["source_id"],
            "state":"DEGRADED","error":str(exc),"canonical_action":"NONE",
        })

    cra_config=configs["EU_CELLAR_CRA_ARTICLE_71"]
    cra_health={
        "adapter_id":"EU_CELLAR_CRA_ARTICLE_71","source_id":"WSSRC-TECH-001",
        "state":"HEALTHY","layers":{},
    }
    cra_degraded=False

    try:
        body,snap=fetch_cellar_celex_document(CRA_CELEX,language="eng")
        rule=parse_cra_article_71(body)
        cra_health["layers"]["immutable_baseline"]={
            "state":"HEALTHY","snapshot":snap.as_dict(),"rule":rule.as_dict(),
        }
        candidate,observation=cra_legal_rule_review_candidate(rule,cra_config)
        _append_candidate(report,candidate,observation)
    except AdapterError as exc:
        cra_degraded=True
        cra_health["layers"]["immutable_baseline"]={
            "state":"DEGRADED","failure_stage":"BASELINE_FETCH_OR_PARSE",
            "error":str(exc),"canonical_action":"NONE",
        }

    try:
        rdf,snap=fetch_cellar_rdf_notice(CRA_CELEX,inferred=True)
        relations=parse_cellar_legal_relation_diagnostics(rdf,base_celex=CRA_CELEX)
        topology=normalize_cellar_legal_topology(relations,base_celex=CRA_CELEX)
        cra_health["layers"]["cellar_rdf_legal_topology"]={
            "state":"HEALTHY","snapshot":snap.as_dict(),"topology":topology.as_dict(),
        }
        candidate,observation=cellar_legal_topology_review_candidate(topology,cra_config)
        _append_candidate(report,candidate,observation)
    except AdapterError as exc:
        cra_degraded=True
        cra_health["layers"]["cellar_rdf_legal_topology"]={
            "state":"DEGRADED","failure_stage":"RDF_FETCH_PARSE_OR_NORMALIZE",
            "error":str(exc),"canonical_action":"NONE",
        }

    if cra_degraded:
        cra_health["state"]="DEGRADED"
    report["source_health"].append(cra_health)

    _run_cbam_monitor(
        report,
        config=configs["EU_CBAM_VERIFICATION_RULE"],
        fetch_rule=fetch_cbam_verification_report_rule,
        compare_rule=cbam_legal_milestone_review_candidate,
        topology_celex=CBAM_VERIFICATION_CELEX,
        topology_layer_name="cellar_rdf_legal_topology",
    )

    _run_cbam_monitor(
        report,
        config=configs["EU_CBAM_CERTIFICATE_SALE_RULE"],
        fetch_rule=fetch_cbam_certificate_sale_rule,
        compare_rule=cbam_legal_milestone_review_candidate,
        topology_celex=CBAM_PARENT_CELEX,
        topology_layer_name="parent_cellar_rdf_legal_topology",
    )

    _run_cbam_monitor(
        report,
        config=configs["EU_CBAM_ANNUAL_DEADLINE_RULE"],
        fetch_rule=fetch_cbam_annual_declaration_surrender_rule,
        compare_rule=cbam_annual_deadline_review_candidate,
        topology_celex=CBAM_PARENT_CELEX,
        topology_layer_name="parent_cellar_rdf_legal_topology",
    )

    candidate_files=[]
    for candidate in report["review_candidates"]:
        cid=candidate["candidate_id"]
        path=REVIEW_DIR/f"{cid}.json"
        path.write_text(json.dumps(candidate,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        candidate_files.append(str(path.relative_to(ROOT)))

    observed_adapter_ids=sorted(x["adapter_id"] for x in report["source_health"])
    missing_expected=sorted(set(expected_adapter_ids)-set(observed_adapter_ids))
    unexpected_observed=sorted(set(observed_adapter_ids)-set(expected_adapter_ids))

    after=file_hash(CANONICAL)
    report["canonical_sha256_after"]=after
    report["canonical_unchanged"]=canonical_sha==after
    report["candidate_count"]=len(candidate_files)
    report["source_health_summary"]={
        "healthy":sum(1 for x in report["source_health"] if x["state"]=="HEALTHY"),
        "degraded":sum(1 for x in report["source_health"] if x["state"]!="HEALTHY"),
        "adapter_entries":len(report["source_health"]),
        "expected_adapter_entries":len(expected_adapter_ids),
        "unique_source_ids":len({x["source_id"] for x in report["source_health"]}),
        "observed_adapter_ids":observed_adapter_ids,
        "missing_expected_adapters":missing_expected,
        "unexpected_observed_adapters":unexpected_observed,
        "all_expected_adapters_observed":not missing_expected and not unexpected_observed,
    }

    manifest={
        "project":"WORLD SIGNALS",
        "generated_at":now,
        "workflow_context":report["workflow_context"],
        "canonical_registry_version":report["canonical_registry_version"],
        "source_registry_version":report["source_registry_version"],
        "monitor_expectations_version":report["monitor_expectations_version"],
        "monitor_operations_policy_version":report["monitor_operations_policy_version"],
        "configuration_fingerprint_sha256":configuration_fingerprint,
        "candidate_count":len(candidate_files),
        "files":candidate_files,
        "automatic_canonical_commit":False,
    }
    MANIFEST.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

    if canonical_sha != after:
        report["status"]="FAIL_CANONICAL_GUARD"
        OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        print(json.dumps(report,indent=2,ensure_ascii=False))
        return 2

    report["status"]=(
        "REVIEW_REQUIRED" if report["review_candidates"]
        else "DEGRADED" if report["source_health_summary"]["degraded"] or missing_expected or unexpected_observed
        else "NO_CHANGE"
    )
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())