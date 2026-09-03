#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from src.world_signals.validation import validate_registry

ROOT=Path(__file__).resolve().parents[1]
REGISTRY_PATH=ROOT/"data/canonical/registry.json"
SOURCE_PATH=ROOT/"data/sources/registry.json"
PLAN_PATH=ROOT/"data/coverage/REGIONAL_CORRECTION_J_PLAN_v0.1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def dump(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False)+"\n")


def assertion_id(item: dict) -> str:
    material="|".join(str(item.get(k) or "") for k in (
        "occurrence_id","series_id","source_id","canonical_name","start_local","end_local","publication_datetime"
    ))
    return "WSA-"+hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def new_sources() -> list[dict]:
    common={
        "domain":"monetary_policy",
        "recommended_verification_cadence":"manual weekly; daily inside 30 days of next occurrence",
        "activation_status":"ACTIVE_MANUAL_PROVENANCE_ONLY",
        "parser_version":None,
        "runtime_health_state":"UNKNOWN_NOT_LIVE_POLLED",
        "backup_source":None,
        "timezone_scope":"FIXED",
        "rights_reviewed_at":"2026-09-03",
        "rights_review_scope":"REGIONAL_CORRECTION_J_CANONICAL_PROVENANCE_AND_AUTOMATION_SEPARATED",
        "rights_review_note":"Operational governance classification for WORLD SIGNALS; not a legal opinion.",
        "monitoring_readiness_assessed_at":"2026-09-03",
    }
    records=[]
    def add(**kwargs):
        r=dict(common)
        r.update(kwargs)
        records.append(r)

    add(
        source_id="WSSRC-REGJ-001", institution="State Bank of Pakistan", jurisdiction="Pakistan",
        endpoint_role="FY27 MPC calendar and monetary-policy communications",
        authoritative_url="https://www.sbp.org.pk/our-operations/monetary-policy",
        source_type="official_schedule",
        information_supplied="MPC meeting dates, same-day Monetary Policy Statement dates, analyst briefings, minutes windows and Monetary Policy Reports",
        future_schedule_horizon="through June 2027 verified; Regional Correction J populates remaining 2026 only",
        typical_advance_notice="fiscal-year advance calendar",
        machine_readable_available="HTML", source_timezone="Asia/Karachi", parser_type="HTML",
        known_limitations=[
            "SBP states that an unforeseen event may cause an announced MPC date to change; update the same stable occurrence.",
            "Main website footer states all rights reserved; production automation is held pending a fuller rights/access review."
        ],
        notes="Manual authoritative factual provenance only in this correction tranche.",
        licence_constraints="ALL_RIGHTS_RESERVED_SURFACE; FULL_RIGHTS_AUDIT_PENDING",
        ingestion_permission="CURATED_FACTUAL_METADATA_MANUAL_ONLY_PENDING_RIGHTS_REVIEW",
        licence_review_status="RIGHTS_AUDIT_REQUIRED",
        automated_retrieval_permission="PRODUCTION_AUTOMATION_HOLD",
        redistribution_permission="NOT_ESTABLISHED",
        rights_evidence_url="https://www.sbp.org.pk/",
        rights_summary="SBP pages carry an all-rights-reserved copyright notice; no broad production reuse licence was established in this pass.",
        automation_summary="No production automated retrieval permission established; manual provenance only.",
        monitoring_readiness_status="RIGHTS_AUDIT_REQUIRED", monitoring_priority_score=650,
        canonical_dependency_count=3,
        last_successful_research_verification_at="2026-09-03"
    )
    add(
        source_id="WSSRC-REGJ-002", institution="Central Bank of Sri Lanka", jurisdiction="Sri Lanka",
        endpoint_role="Monetary Policy Board advance release calendar",
        authoritative_url="https://www.cbsl.gov.lk/en/monetary-policy/monetary-policy-communication/monetary-policy-advance-release-calendar",
        source_type="official_schedule",
        information_supplied="MPB meeting dates and distinct public monetary-policy announcement dates",
        future_schedule_horizon="remaining 2026 exact; 2027 shown as to be announced",
        typical_advance_notice="annual advance release calendar",
        machine_readable_available="HTML", source_timezone="Asia/Colombo", parser_type="HTML",
        known_limitations=[
            "Meeting date and announcement date are distinct; canonical decision occurrence uses the announcement date.",
            "No sufficiently broad website reuse/automation permission was established in this pass."
        ],
        notes="Manual authoritative factual provenance only pending rights/access review.",
        licence_constraints="RIGHTS_REVIEW_PENDING",
        ingestion_permission="CURATED_FACTUAL_METADATA_MANUAL_ONLY_PENDING_RIGHTS_REVIEW",
        licence_review_status="RIGHTS_AUDIT_REQUIRED",
        automated_retrieval_permission="PRODUCTION_AUTOMATION_HOLD",
        redistribution_permission="NOT_ESTABLISHED",
        rights_evidence_url="https://www.cbsl.gov.lk/",
        rights_summary="Authoritative calendar is public; broader production reuse/automation rights were not established in this pass.",
        automation_summary="No production automated retrieval permission established; manual provenance only.",
        monitoring_readiness_status="RIGHTS_AUDIT_REQUIRED", monitoring_priority_score=620,
        canonical_dependency_count=2,
        last_successful_research_verification_at="2026-09-03"
    )
    add(
        source_id="WSSRC-REGJ-003", institution="Bangko Sentral ng Pilipinas", jurisdiction="Philippines",
        endpoint_role="2026 Monetary Board monetary-policy calendar",
        authoritative_url="https://www.bsp.gov.ph/Pages/PriceStability/ScheduleOfMeetingsOfTheAdvisoryCommitteeAndMonetaryBoardOnMonetaryPolicy.aspx",
        source_type="official_schedule",
        information_supplied="Monetary Board policy meeting dates and Monetary Policy Report schedule",
        future_schedule_horizon="remaining 2026 exact",
        typical_advance_notice="annual calendar",
        machine_readable_available="HTML/PDF", source_timezone="Asia/Manila", parser_type="HTML+PDF",
        known_limitations=["No clock time is supplied for future monetary-policy stance releases; preserve date-only precision."],
        notes="BSP terms permit quotation/copying/reproduction provided BSP is credited; automation permission remains a separate endpoint question.",
        licence_constraints=None,
        ingestion_permission="CURATED_FACTUAL_METADATA_ALLOWED_WITH_ATTRIBUTION",
        licence_review_status="CLEARED_REUSE_WITH_ATTRIBUTION",
        automated_retrieval_permission="PENDING_ENDPOINT_OPERATIONAL_REVIEW",
        redistribution_permission="ALLOWED_WITH_ATTRIBUTION",
        rights_evidence_url="https://www.bsp.gov.ph/Pages/AboutTheBank/Terms-of-Use.aspx",
        rights_summary="BSP terms state site contents may be quoted, copied or reproduced in whole or part provided BSP is duly credited.",
        automation_summary="Reuse permission does not itself establish unrestricted automated retrieval; endpoint review remains required.",
        monitoring_readiness_status="ENDPOINT_REVIEW_REQUIRED", monitoring_priority_score=600,
        canonical_dependency_count=2,
        last_successful_research_verification_at="2026-09-03"
    )
    add(
        source_id="WSSRC-REGJ-004", institution="Bank Negara Malaysia", jurisdiction="Malaysia",
        endpoint_role="MPC meeting decision schedule",
        authoritative_url="https://www.bnm.gov.my/monetary-stability/mpc-meetings",
        source_type="official_schedule",
        information_supplied="MPC decision dates and same-day 15:00 Monetary Policy Statement release rule",
        future_schedule_horizon="remaining 2026 exact",
        typical_advance_notice="annual schedule",
        machine_readable_available="HTML", source_timezone="Asia/Kuala_Lumpur", parser_type="HTML",
        known_limitations=["General BNM website terms restrict reuse of ordinary website content; this source is not eligible for production monitoring in the current rights state."],
        notes="Manual factual provenance only; no production endpoint promotion.",
        licence_constraints="GENERAL_WEB_CONTENT_PERSONAL_USE_RESTRICTIONS",
        ingestion_permission="CURATED_FACTUAL_METADATA_MANUAL_ONLY",
        licence_review_status="GENERAL_WEB_CONTENT_RESTRICTED",
        automated_retrieval_permission="PRODUCTION_AUTOMATION_HOLD",
        redistribution_permission="GENERAL_WEB_REUSE_REQUIRES_PERMISSION_EXCEPT_AS_ALLOWED_BY_LAW",
        rights_evidence_url="https://www.bnm.gov.my/terms-of-use",
        rights_summary="BNM general website terms protect website content and limit ordinary downloaded material to personal use absent further permission; separate liberal dataset terms do not govern this schedule page.",
        automation_summary="Production automated retrieval is held; schedule facts are retained as manually curated provenance only.",
        monitoring_readiness_status="MANUAL_ONLY_RIGHTS_HOLD", monitoring_priority_score=120,
        canonical_dependency_count=1,
        last_successful_research_verification_at="2026-09-03"
    )
    add(
        source_id="WSSRC-REGJ-005", institution="Central Bank of Egypt", jurisdiction="Egypt",
        endpoint_role="2026 MPC meetings schedule",
        authoritative_url="https://www.cbe.org.eg/en/monetary-policy/mpc-meetings-schedule?verify=false",
        source_type="official_schedule",
        information_supplied="MPC meeting/decision dates and links to completed decision releases",
        future_schedule_horizon="remaining 2026 exact",
        typical_advance_notice="annual schedule",
        machine_readable_available="HTML", source_timezone="Africa/Cairo", parser_type="HTML",
        known_limitations=["Future schedule supplies dates but no clock time; preserve date-only precision."],
        notes="CBE permits use/distribution/reproduction of directly obtained information with accurate source attribution; automation permission remains separate.",
        licence_constraints=None,
        ingestion_permission="CURATED_FACTUAL_METADATA_ALLOWED_WITH_ATTRIBUTION",
        licence_review_status="CLEARED_REUSE_WITH_ATTRIBUTION_ACCURACY",
        automated_retrieval_permission="PENDING_ENDPOINT_OPERATIONAL_REVIEW",
        redistribution_permission="ALLOWED_WITH_SOURCE_CITATION_AND_ACCURACY",
        rights_evidence_url="https://www.cbe.org.eg/en/disclaimer",
        rights_summary="CBE states users may make use of information obtained directly from the website and requires CBE citation and accurate reproduction when distributed or reproduced.",
        automation_summary="Reuse terms do not by themselves authorise unrestricted automated retrieval; endpoint review remains required.",
        monitoring_readiness_status="ENDPOINT_REVIEW_REQUIRED", monitoring_priority_score=600,
        canonical_dependency_count=3,
        last_successful_research_verification_at="2026-09-03"
    )
    return records


def preflight(registry: dict, sources: dict, plan: dict) -> None:
    p=plan["preconditions"]
    errors=[]
    if str(registry.get("version")) != p["canonical_registry_version"]:
        errors.append(f"canonical version {registry.get('version')} != {p['canonical_registry_version']}")
    if registry.get("record_count") != p["canonical_record_count"] or len(registry.get("records",[])) != p["canonical_record_count"]:
        errors.append("canonical record count precondition failed")
    if str(sources.get("version")) != p["source_registry_version"]:
        errors.append(f"source version {sources.get('version')} != {p['source_registry_version']}")

    source_ids={s.get("source_id") for s in sources.get("sources",[])}
    for sid in p["required_existing_source_ids"]:
        if sid not in source_ids:
            errors.append(f"required source missing: {sid}")
    for sid in p["required_absent_source_ids"]:
        if sid in source_ids:
            errors.append(f"new source id already exists: {sid}")

    existing_oids={r.get("occurrence_id") for r in registry.get("records",[])}
    existing_series={r.get("series_id") for r in registry.get("records",[])}
    if any(x and x.startswith(p["required_absent_occurrence_prefix"]) for x in existing_oids):
        errors.append("Regional Correction J occurrence namespace already exists")
    if any(x and x.startswith(p["required_absent_series_prefix"]) for x in existing_series):
        errors.append("Regional Correction J series namespace already exists")

    planned=plan.get("occurrences",[])
    planned_ids=[x["occurrence_id"] for x in planned]
    if len(planned_ids) != len(set(planned_ids)):
        errors.append("duplicate planned occurrence id")
    if len(planned) != plan["postconditions"]["new_occurrence_count"]:
        errors.append("plan occurrence count does not match postcondition")
    if len({x["series_id"] for x in planned}) != plan["postconditions"]["new_series_count"]:
        errors.append("plan series count does not match postcondition")
    if any(x in existing_oids for x in planned_ids):
        errors.append("planned occurrence collides with existing occurrence")

    rbi=next((s for s in sources.get("sources",[]) if s.get("source_id")=="WSSRC-CB-011"),None)
    if rbi and rbi.get("canonical_dependency_count") not in (0,None):
        errors.append(f"RBI source dependency count unexpectedly {rbi.get('canonical_dependency_count')}; reconcile before migration")

    if errors:
        raise SystemExit("PRECONDITION FAILED:\n- "+"\n- ".join(errors))


def build_occurrence(item: dict, series_meta: dict) -> dict:
    timed=item["timing_type"]=="LOCAL_DATETIME"
    aid=assertion_id(item)
    return {
        "occurrence_id":item["occurrence_id"],
        "series_id":item["series_id"],
        "external_source_id":None,
        "canonical_name":item["canonical_name"],
        "short_calendar_title":item["canonical_name"],
        "category":"MONETARY_FINANCIAL_POLICY",
        "subcategory":"monetary_policy",
        "jurisdiction":item["jurisdiction"],
        "region":item["region"],
        "institution":item["institution"],
        "event_type":item["event_type"],
        "record_class":"OCCURRENCE",
        "certainty_status":"CONFIRMED",
        "activation_mode":"EXPLICITLY_SCHEDULED",
        "lifecycle_status":"PLANNED",
        "condition_state":"NOT_REQUIRED",
        "condition_description":None,
        "trigger_source_id":None,
        "trigger_assertion_id":None,
        "triggered_at":None,
        "trigger_verification_status":"NOT_APPLICABLE",
        "timing_type":item["timing_type"],
        "start_local":item["start_local"],
        "end_local":item.get("end_local"),
        "source_timezone":item["source_timezone"],
        "start_utc":item.get("start_utc"),
        "end_utc":item.get("end_utc"),
        "date_earliest":None,
        "date_latest":None,
        "time_precision":item["time_precision"],
        "all_day_semantics":not timed,
        "reference_period":None,
        "publication_datetime":item.get("publication_datetime"),
        "time_status":"CONFIRMED",
        "time_basis":"EXPLICIT_AUTHORITATIVE_SCHEDULE",
        "source_id":item["source_id"],
        "primary_source_assertion_id":aid,
        "last_successful_assertion_id":aid,
        "status_history":[{"as_of":"2026-09-03","certainty_status":"CONFIRMED","lifecycle_status":"PLANNED"}],
        "first_announced_at":None,
        "first_discovered_at":"2026-09-03",
        "last_verified_at":"2026-09-03",
        "next_verification_due":"SOURCE_SPECIFIC",
        "parent_occurrence_id":None,
        "related_occurrence_ids":[],
        "related_documents":[],
        "intrinsic_importance":"HIGH",
        "expected_market_sensitivity":"HIGH",
        "geopolitical_sensitivity":"MEDIUM",
        "transmission_channels":["monetary_policy","inflation","financial_stability","currencies","sovereign_bonds","equities","trade","investment","households"],
        "render_policy":"INCLUDE",
        "visibility_tier":"ESSENTIAL",
        "deadline_is_actual_event_time":False,
        "derivation_sources":[],
        "coverage_program_id":"WSCP-REGIONAL-CORRECTION-J",
        "coverage_repair_reason":"STRUCTURAL_REGIONAL_MONETARY_POLICY_GAP",
        "population_horizon_policy":"ALL_REMAINING_CURRENT_YEAR_OCCURRENCES",
        "country_system":item["jurisdiction"],
        "selection_rationale":"Coverage Audit v0.2 and qualitative priority matrix v0.1 identified a systemically material missing monetary-policy series; only primary-source exact remaining-2026 occurrences are admitted.",
        "future_schedule_deferred":bool(series_meta.get("future_schedule_deferred")),
        "publication_bundle_type":"SINGLE_RELEASE",
        "render_cluster_key":None,
        "calendar_aggregation_policy":"STANDALONE",
        "notes":item["notes"]
    }


def apply_in_memory(registry: dict, sources: dict, plan: dict) -> tuple[dict,dict]:
    registry=copy.deepcopy(registry)
    sources=copy.deepcopy(sources)
    preflight(registry,sources,plan)

    # Reuse and improve the dormant RBI source identity without altering its existing rights classification.
    rbi=next(s for s in sources["sources"] if s.get("source_id")=="WSSRC-CB-011")
    rbi.update({
        "endpoint_role":"FY2026-27 MPC meeting schedule / resolutions source family",
        "authoritative_url":"https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=62422",
        "information_supplied":"Authoritative FY2026-27 MPC meeting windows plus RBI monetary-policy resolutions/notices",
        "future_schedule_horizon":"through February 2027 verified; Regional Correction J populates remaining 2026 only",
        "recommended_verification_cadence":"manual weekly; daily inside 30 days of next meeting; production automation status unchanged",
        "activation_status":"ACTIVE_MANUAL_PROVENANCE_ONLY",
        "known_limitations":["Schedule establishes multi-day MPC meeting windows; do not infer a separate exact decision publication timestamp from the final day without authoritative timing."],
        "canonical_dependency_count":2,
        "last_successful_research_verification_at":"2026-09-03"
    })

    for source in new_sources():
        sources["sources"].append(source)

    series_meta={x["series_id"]:x for x in plan["series"]}
    new_records=[build_occurrence(item,series_meta[item["series_id"]]) for item in plan["occurrences"]]
    registry["records"].extend(new_records)
    registry["record_count"]=len(registry["records"])
    registry["version"]="0.18"
    registry["reference_date"]="2026-09-03"
    sources["version"]="1.49"
    sources["reference_date"]="2026-09-03"

    post=plan["postconditions"]
    errors=[]
    if registry["record_count"] != post["canonical_record_count"]:
        errors.append(f"post record_count {registry['record_count']} != {post['canonical_record_count']}")
    if str(registry["version"]) != post["canonical_registry_version"]:
        errors.append("post canonical version mismatch")
    if str(sources["version"]) != post["source_registry_version"]:
        errors.append("post source version mismatch")
    if len({r["occurrence_id"] for r in new_records}) != post["new_occurrence_count"]:
        errors.append("post new occurrence uniqueness/count mismatch")
    if len({r["series_id"] for r in new_records}) != post["new_series_count"]:
        errors.append("post new series count mismatch")
    if len([s for s in sources["sources"] if s.get("source_id","").startswith("WSSRC-REGJ-")]) != post["new_source_count"]:
        errors.append("post new source count mismatch")

    report=validate_registry(registry,sources)
    errors.extend(report.errors)
    if errors:
        raise SystemExit("POSTCONDITION FAILED:\n- "+"\n- ".join(errors))
    return registry,sources


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--apply",action="store_true",help="write validated v0.18/v1.49 registries; default is read-only check")
    args=parser.parse_args()

    registry=load(REGISTRY_PATH)
    sources=load(SOURCE_PATH)
    plan=load(PLAN_PATH)
    new_registry,new_sources_registry=apply_in_memory(registry,sources,plan)

    result={
        "status":"PASS",
        "mode":"APPLY" if args.apply else "CHECK_ONLY",
        "canonical_version_before":registry.get("version"),
        "canonical_version_after":new_registry.get("version"),
        "record_count_before":registry.get("record_count"),
        "record_count_after":new_registry.get("record_count"),
        "source_version_before":sources.get("version"),
        "source_version_after":new_sources_registry.get("version"),
        "planned_occurrence_count":len(plan["occurrences"]),
        "planned_series_count":len({x["series_id"] for x in plan["occurrences"]}),
        "planned_new_source_count":len([x for x in plan["source_plan"] if x["operation"]=="ADD_SOURCE"]),
        "existing_source_reused":"WSSRC-CB-011",
        "automatic_canonical_commit":False,
        "google_calendar_write":False
    }
    print(json.dumps(result,indent=2))
    if args.apply:
        dump(REGISTRY_PATH,new_registry)
        dump(SOURCE_PATH,new_sources_registry)


if __name__=="__main__":
    main()
