#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.world_signals.validation import validate_registry

ROOT=Path(__file__).resolve().parents[1]
REGISTRY_PATH=ROOT/"data/canonical/registry.json"
SOURCE_PATH=ROOT/"data/sources/registry.json"
PLAN_PATH=ROOT/"data/coverage/ENERGY_COMMODITIES_CORRECTION_K_PLAN_v0.1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def dump(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False)+"\n")


def assertion_id(item: dict) -> str:
    material="|".join(str(item.get(k) or "") for k in (
        "occurrence_id","series_id","source_id","canonical_name","start_local","start_utc"
    ))
    return "WSA-"+hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def source_runtime_fields(source_plan: dict) -> dict:
    institution=source_plan["institution"]
    common={
        "domain":"energy_commodities",
        "recommended_verification_cadence":"manual weekly; daily inside 14 days of next occurrence",
        "activation_status":"ACTIVE_MANUAL_PROVENANCE_ONLY",
        "parser_version":None,
        "runtime_health_state":"UNKNOWN_NOT_LIVE_POLLED",
        "backup_source":None,
        "timezone_scope":"SOURCE_SPECIFIC",
        "rights_reviewed_at":"2026-09-03",
        "rights_review_scope":"ENERGY_COMMODITIES_CORRECTION_K_CANONICAL_PROVENANCE_AND_AUTOMATION_SEPARATED",
        "rights_review_note":"Operational governance classification for WORLD SIGNALS; not a legal opinion.",
        "monitoring_readiness_assessed_at":"2026-09-03",
        "last_successful_research_verification_at":"2026-09-03",
        "automated_retrieval_permission":"PRODUCTION_AUTOMATION_HOLD"
    }
    if institution.startswith("Joint Organisations Data Initiative"):
        specific={
            "endpoint_role":"JODI Oil + Gas World Database first monthly update schedule",
            "information_supplied":"First monthly JODI-Oil and JODI-Gas World Database update dates; official combined schedule gives noon London time",
            "future_schedule_horizon":"through December 2026 verified",
            "typical_advance_notice":"annual schedule",
            "machine_readable_available":"HTML/PDF",
            "source_timezone":"Europe/London",
            "parser_type":"MANUAL_HTML_PDF_PROVENANCE",
            "known_limitations":[
                "Calendar identifies the first scheduled update in each month; supplementary updates may occur after additional country submissions.",
                "JODI website terms reserve intellectual-property rights; no production crawler permission is inferred from public availability."
            ],
            "notes":"Canonical occurrence is a SOURCE_BUNDLE containing Oil and Gas data products at the same timestamp.",
            "licence_constraints":"INTELLECTUAL_PROPERTY_RIGHTS_RESERVED",
            "ingestion_permission":"CURATED_FACTUAL_METADATA_MANUAL_ONLY",
            "licence_review_status":"RIGHTS_RESERVED_FACTUAL_METADATA_ONLY",
            "redistribution_permission":"FACTUAL_METADATA_ONLY_NO_CONTENT_REPRODUCTION_INFERRED",
            "rights_summary":"JODI terms reserve intellectual-property rights in the website and published material.",
            "automation_summary":"Manual factual schedule provenance only. Public access and downloadable data do not by themselves establish permission for production automated retrieval.",
            "monitoring_readiness_status":"MANUAL_ONLY_RIGHTS_HOLD",
            "monitoring_priority_score":250,
            "canonical_dependency_count":4
        }
    elif institution=="Gas Exporting Countries Forum":
        specific={
            "endpoint_role":"8th GECF Summit official announcement",
            "information_supplied":"8th GECF Summit of Heads of State and Government hosted in Moscow on 27 October 2026",
            "future_schedule_horizon":"explicit 2026 summit occurrence",
            "typical_advance_notice":"months",
            "machine_readable_available":"HTML",
            "source_timezone":"Europe/Moscow",
            "parser_type":"MANUAL_HTML_PROVENANCE",
            "known_limitations":["No production automated retrieval/reuse permission was established in this pass."],
            "notes":"Manual authoritative factual provenance only; no monitoring promotion in Correction K.",
            "licence_constraints":"RIGHTS_REVIEW_PENDING",
            "ingestion_permission":"CURATED_FACTUAL_METADATA_MANUAL_ONLY_PENDING_RIGHTS_REVIEW",
            "licence_review_status":"RIGHTS_AUDIT_REQUIRED",
            "redistribution_permission":"NOT_ESTABLISHED",
            "rights_summary":"Authoritative public event announcement verified; broader reuse rights were not established in this pass.",
            "automation_summary":"No production automated retrieval permission established; manual provenance only.",
            "monitoring_readiness_status":"RIGHTS_AUDIT_REQUIRED",
            "monitoring_priority_score":420,
            "canonical_dependency_count":1
        }
    elif institution=="International Copper Study Group":
        specific={
            "endpoint_role":"ICSG next meetings schedule",
            "information_supplied":"Next ICSG meetings in Lisbon on 13 October 2026",
            "future_schedule_horizon":"explicit October 2026 meeting occurrence",
            "typical_advance_notice":"months",
            "machine_readable_available":"HTML",
            "source_timezone":"Europe/Lisbon",
            "parser_type":"MANUAL_HTML_PROVENANCE",
            "known_limitations":["No production automated retrieval/reuse permission was established in this pass."],
            "notes":"Manual authoritative factual provenance only; no monitoring promotion in Correction K.",
            "licence_constraints":"RIGHTS_REVIEW_PENDING",
            "ingestion_permission":"CURATED_FACTUAL_METADATA_MANUAL_ONLY_PENDING_RIGHTS_REVIEW",
            "licence_review_status":"RIGHTS_AUDIT_REQUIRED",
            "redistribution_permission":"NOT_ESTABLISHED",
            "rights_summary":"Authoritative public meeting schedule verified; broader reuse rights were not established in this pass.",
            "automation_summary":"No production automated retrieval permission established; manual provenance only.",
            "monitoring_readiness_status":"RIGHTS_AUDIT_REQUIRED",
            "monitoring_priority_score":400,
            "canonical_dependency_count":1
        }
    else:
        raise SystemExit(f"unrecognised Correction K source institution: {institution}")
    return common|specific


def build_source(source_plan: dict) -> dict:
    record={
        "source_id":source_plan["source_id"],
        "institution":source_plan["institution"],
        "jurisdiction":source_plan["jurisdiction"],
        "authoritative_url":source_plan["authoritative_url"],
        "source_type":source_plan["source_type"],
        "rights_evidence_url":source_plan.get("rights_evidence_url") or source_plan["authoritative_url"]
    }
    record.update(source_runtime_fields(source_plan))
    return record


def preflight(registry: dict, sources: dict, plan: dict) -> None:
    p=plan["preconditions"]
    errors=[]
    if str(registry.get("version")) != p["canonical_registry_version"]:
        errors.append(f"canonical version {registry.get('version')} != {p['canonical_registry_version']}")
    if registry.get("record_count") != p["canonical_record_count"] or len(registry.get("records",[])) != p["canonical_record_count"]:
        errors.append("canonical record count precondition failed")
    if str(sources.get("version")) != p["source_registry_version"]:
        errors.append(f"source version {sources.get('version')} != {p['source_registry_version']}")

    existing_oids={r.get("occurrence_id") for r in registry.get("records",[])}
    existing_series={r.get("series_id") for r in registry.get("records",[])}
    existing_source_ids={s.get("source_id") for s in sources.get("sources",[])}
    existing_institutions={str(r.get("institution") or "").casefold() for r in registry.get("records",[])}
    source_institutions={str(s.get("institution") or "").casefold() for s in sources.get("sources",[])}

    for oid in p["required_absent_occurrence_ids"]:
        if oid in existing_oids:
            errors.append(f"planned occurrence id already exists: {oid}")
    for sid in p["required_absent_series_ids"]:
        if sid in existing_series:
            errors.append(f"planned series id already exists: {sid}")
    for sid in p["required_absent_source_ids"]:
        if sid in existing_source_ids:
            errors.append(f"planned source id already exists: {sid}")

    for source_plan in plan["source_plan"]:
        name=source_plan["institution"]
        folded=name.casefold()
        if folded in existing_institutions or folded in source_institutions:
            errors.append(f"institution already present; reconcile identity before migration: {name}")

    planned=plan.get("occurrences",[])
    planned_ids=[x["occurrence_id"] for x in planned]
    if planned_ids != p["required_absent_occurrence_ids"]:
        errors.append("plan occurrence sequence differs from frozen reconciled precondition")
    if [x["source_id"] for x in plan["source_plan"]] != p["required_absent_source_ids"]:
        errors.append("plan source sequence differs from frozen reconciled precondition")
    if len(planned) != plan["postconditions"]["new_occurrence_count"]:
        errors.append("plan occurrence count does not match postcondition")
    if len({x["series_id"] for x in planned}) != plan["postconditions"]["new_series_count"]:
        errors.append("plan series count does not match postcondition")

    series_sources={x["series_id"]:x["source_id"] for x in plan["series"]}
    for item in planned:
        if series_sources.get(item["series_id"]) != item["source_id"]:
            errors.append(f"series/source binding mismatch for {item['occurrence_id']}")

    # Verify every timed JODI assertion round-trips from source-local Europe/London to frozen UTC.
    for item in planned:
        if item["series_id"] != "WSER-COM-JODI-WDB":
            continue
        local=datetime.fromisoformat(item["start_local"]).replace(tzinfo=ZoneInfo("Europe/London"))
        expected=local.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")
        if expected != item["start_utc"]:
            errors.append(f"JODI UTC mismatch for {item['occurrence_id']}: {item['start_utc']} != {expected}")
        if len(item.get("data_products",[])) != 2:
            errors.append(f"JODI SOURCE_BUNDLE must contain exactly two data products: {item['occurrence_id']}")

    if errors:
        raise SystemExit("PRECONDITION FAILED:\n- "+"\n- ".join(errors))


def build_occurrence(item: dict) -> dict:
    jodi=item["series_id"]=="WSER-COM-JODI-WDB"
    gecf=item["series_id"]=="WSER-COM-GECF-SUMMIT"
    timed=jodi
    aid=assertion_id(item)

    if jodi:
        institution="Joint Organisations Data Initiative / International Energy Forum"
        jurisdiction="Global"
        subcategory="energy_data_transparency"
        event_type="INFORMATION_RELEASE"
        intrinsic="HIGH"
        expected="HIGH"
        geopolitical="MEDIUM"
        signal_class="SCHEDULED_INFORMATION_CATALYST"
        commodity_scope=["crude oil","oil products","natural gas","LNG"]
        supply_scope=["production","demand","trade","stocks","LNG flows","pipeline flows"]
        bundle_type="SOURCE_BUNDLE"
        rationale="Global producer/consumer oil and gas data update; directly broadens the category beyond oil-only calendars."
        notes="Official combined JODI schedule states the first JODI-Oil and JODI-Gas World Database updates occur together at noon London time. Supplementary later-month updates are not separate canonical occurrences by this series definition."
    elif gecf:
        institution="Gas Exporting Countries Forum"
        jurisdiction="GECF member countries / Global"
        subcategory="gas_producer_policy"
        event_type="PRODUCER_POLICY_MEETING"
        intrinsic="HIGH"
        expected="HIGH"
        geopolitical="HIGH"
        signal_class="SCHEDULED_PRODUCER_POLICY_MEETING"
        commodity_scope=["natural gas","LNG"]
        supply_scope=["producer cooperation","gas market policy","investment","energy security"]
        bundle_type="SINGLE_RELEASE"
        rationale="Heads-of-state producer-policy summit with potential implications for global gas cooperation, investment and market governance."
        notes="GECF official announcement states the 8th Summit will be hosted in Moscow on 27 October 2026. No clock time is inferred."
    else:
        institution="International Copper Study Group"
        jurisdiction="Global"
        subcategory="industrial_metals_market"
        event_type="INFORMATION_CATALYST_MEETING"
        intrinsic="HIGH"
        expected="MEDIUM_HIGH"
        geopolitical="MEDIUM"
        signal_class="SCHEDULED_INFORMATION_CATALYST"
        commodity_scope=["copper"]
        supply_scope=["mine production","refined production","usage","trade","stocks","market balance"]
        bundle_type="SINGLE_RELEASE"
        rationale="Adds a major industrial/transition-metal market institution to an energy/commodities footprint dominated by oil."
        notes="ICSG official site states the next ICSG meetings will take place in Lisbon on 13 October 2026. No clock time is inferred."

    start_local=item["start_local"]
    return {
        "occurrence_id":item["occurrence_id"],
        "series_id":item["series_id"],
        "external_source_id":None,
        "canonical_name":item["canonical_name"],
        "short_calendar_title":item["canonical_name"],
        "category":"ENERGY_COMMODITIES",
        "subcategory":subcategory,
        "jurisdiction":jurisdiction,
        "region":"Cross-regional / Global",
        "institution":institution,
        "event_type":event_type,
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
        "timing_type":"LOCAL_DATETIME" if timed else "CIVIL_DATE",
        "start_local":start_local,
        "end_local":None,
        "source_timezone":item["source_timezone"],
        "start_utc":item.get("start_utc"),
        "end_utc":None,
        "date_earliest":None,
        "date_latest":None,
        "time_precision":"MINUTE" if timed else "DAY",
        "all_day_semantics":not timed,
        "reference_period":None,
        "publication_datetime":start_local if timed else None,
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
        "intrinsic_importance":intrinsic,
        "expected_market_sensitivity":expected,
        "geopolitical_sensitivity":geopolitical,
        "transmission_channels":["commodities","inflation","trade","currencies","equities","industrial_policy","energy_security","shipping_logistics"],
        "render_policy":"INCLUDE",
        "visibility_tier":"ANALYST" if item["series_id"]=="WSER-COM-ICSG-MTG" else "ESSENTIAL",
        "signal_object_class":signal_class,
        "publication_time_semantics":"EXACT_LOCAL_TIME" if timed else "DATE_ONLY",
        "commodity_scope":commodity_scope,
        "supply_chain_scope":supply_scope,
        "physical_shock_routing":"NO_SHOCK_IN_THIS_RECORD",
        "observed_market_response":None,
        "expected_market_sensitivity_basis":rationale,
        "publication_bundle_type":bundle_type,
        "data_products":item.get("data_products",[]),
        "render_cluster_key":None,
        "calendar_aggregation_policy":"STANDALONE",
        "coverage_program_id":"WSCP-ENERGY-COMMODITIES-CORRECTION-K",
        "coverage_repair_reason":"ENERGY_COMMODITIES_OIL_AND_INSTITUTION_CONCENTRATION",
        "population_horizon_policy":"ALL_REMAINING_CURRENT_YEAR_OCCURRENCES" if jodi else "EXPLICIT_CURRENT_YEAR_OCCURRENCE_ONLY",
        "selection_rationale":rationale,
        "notes":notes
    }


def migrate(registry: dict, sources: dict, plan: dict) -> tuple[dict,dict,dict]:
    preflight(registry,sources,plan)
    new_registry=copy.deepcopy(registry)
    new_sources_registry=copy.deepcopy(sources)

    source_records=[build_source(x) for x in plan["source_plan"]]
    if len(source_records) != plan["postconditions"]["new_source_count"]:
        raise SystemExit("new source builder count does not match plan")
    new_sources_registry["sources"].extend(source_records)
    new_sources_registry["version"]=plan["postconditions"]["source_registry_version"]
    new_sources_registry["reference_date"]="2026-09-03"

    for item in plan["occurrences"]:
        new_registry["records"].append(build_occurrence(item))
    new_registry["version"]=plan["postconditions"]["canonical_registry_version"]
    new_registry["record_count"]=len(new_registry["records"])
    new_registry["reference_date"]="2026-09-03"

    post=plan["postconditions"]
    errors=[]
    if new_registry["record_count"] != post["canonical_record_count"]:
        errors.append(f"post canonical count {new_registry['record_count']} != {post['canonical_record_count']}")
    if str(new_registry["version"]) != post["canonical_registry_version"]:
        errors.append("post canonical version mismatch")
    if str(new_sources_registry["version"]) != post["source_registry_version"]:
        errors.append("post source version mismatch")

    added=[r for r in new_registry["records"] if r.get("occurrence_id") in set(plan["preconditions"]["required_absent_occurrence_ids"])]
    if len(added) != post["new_occurrence_count"]:
        errors.append("post new occurrence count mismatch")
    if len({r["series_id"] for r in added}) != post["new_series_count"]:
        errors.append("post new series count mismatch")
    new_sids=set(plan["preconditions"]["required_absent_source_ids"])
    if len([s for s in new_sources_registry["sources"] if s.get("source_id") in new_sids]) != post["new_source_count"]:
        errors.append("post new source count mismatch")

    source_ids={s.get("source_id") for s in new_sources_registry.get("sources",[])}
    dangling=[r["occurrence_id"] for r in added if r.get("source_id") not in source_ids]
    if dangling:
        errors.append("new occurrences have dangling source references: "+", ".join(dangling))

    if post.get("scheduled_live_monitor_change") is not False:
        errors.append("plan safety postcondition for scheduled_live_monitor_change must be false")
    if any(s.get("automated_retrieval_permission") != "PRODUCTION_AUTOMATION_HOLD" for s in source_records):
        errors.append("all Correction K sources must remain production automation holds")

    report=validate_registry(new_registry,new_sources_registry)
    if not report.ok:
        errors.extend(report.errors)
    if errors:
        raise SystemExit("POSTCONDITION FAILED:\n- "+"\n- ".join(errors))

    summary={
        "status":"PASS",
        "canonical_version_before":registry.get("version"),
        "canonical_version_after":new_registry.get("version"),
        "record_count_before":registry.get("record_count"),
        "record_count_after":new_registry.get("record_count"),
        "source_version_before":sources.get("version"),
        "source_version_after":new_sources_registry.get("version"),
        "planned_occurrence_count":post["new_occurrence_count"],
        "planned_series_count":post["new_series_count"],
        "planned_new_source_count":post["new_source_count"],
        "automatic_canonical_commit":False,
        "google_calendar_write":False,
        "scheduled_live_monitor_change":False,
        "validator_warning_count":len(report.warnings)
    }
    return new_registry,new_sources_registry,summary


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--apply",action="store_true",help="write the reviewed transaction after all fail-closed checks pass")
    args=parser.parse_args()

    registry=load(REGISTRY_PATH)
    sources=load(SOURCE_PATH)
    plan=load(PLAN_PATH)
    new_registry,new_sources_registry,summary=migrate(registry,sources,plan)
    summary["mode"]="APPLY" if args.apply else "CHECK_ONLY"
    print(json.dumps(summary,indent=2))
    if args.apply:
        dump(REGISTRY_PATH,new_registry)
        dump(SOURCE_PATH,new_sources_registry)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
