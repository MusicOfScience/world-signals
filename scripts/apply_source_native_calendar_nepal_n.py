#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.world_signals.validation import validate_registry

SCHEMA_PATH=ROOT/"data/canonical/schema.json"
REGISTRY_PATH=ROOT/"data/canonical/registry.json"
SOURCE_PATH=ROOT/"data/sources/registry.json"
PLAN_PATH=ROOT/"data/coverage/SOURCE_NATIVE_CALENDAR_NEPAL_PLAN_v0.1.json"
AUDIT_PATH=ROOT/"data/coverage/SOURCE_NATIVE_CALENDAR_NEPAL_TRANSACTION_AUDIT_v0.1.md"
LEDGER_PATH=ROOT/"data/changes/ledger.json"
EXPECTATIONS_PATH=ROOT/"data/monitor/expectations.json"
APPLY_ENV="WORLD_SIGNALS_APPLY_NATIVE_CALENDAR_N"


def load(path:Path)->dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path:Path,payload:dict)->None:
    path.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")


def file_hash(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assertion_id(item:dict)->str:
    material="|".join(str(item.get(k) or "") for k in (
        "occurrence_id","series_id","source_id","canonical_name","source_native_date_label"
    ))
    return "WSA-"+hashlib.sha256(material.encode()).hexdigest()[:16]


def append_absent(seq:list,value,label:str)->None:
    if value in seq:
        raise SystemExit(f"PRECONDITION FAILED: {label} already contains {value}")
    seq.append(value)


def preflight(schema:dict,registry:dict,sources:dict,plan:dict)->None:
    p=plan["preconditions"]
    errors=[]
    if str(schema.get("version"))!=p["canonical_schema_version"]:
        errors.append("canonical schema version drift")
    if str(registry.get("version"))!=p["canonical_registry_version"]:
        errors.append("canonical registry version drift")
    if registry.get("record_count")!=p["canonical_record_count"] or len(registry.get("records",[]))!=p["canonical_record_count"]:
        errors.append("canonical record-count drift")
    if str(sources.get("version"))!=p["source_registry_version"]:
        errors.append("source registry version drift")
    if len(sources.get("sources",[]))!=p["source_record_count"]:
        errors.append("source record-count drift")

    occurrence_ids={r.get("occurrence_id") for r in registry.get("records",[])}
    series_ids={r.get("series_id") for r in registry.get("records",[])}
    source_ids={s.get("source_id") for s in sources.get("sources",[])}
    for oid in p["required_absent_occurrence_ids"]:
        if oid in occurrence_ids: errors.append(f"occurrence identity collision: {oid}")
    for sid in p["required_absent_series_ids"]:
        if sid in series_ids: errors.append(f"series identity collision: {sid}")
    for sid in p["required_absent_source_ids"]:
        if sid in source_ids: errors.append(f"source identity collision: {sid}")

    occurrence=plan["occurrence"]
    if [occurrence["occurrence_id"]]!=p["required_absent_occurrence_ids"]:
        errors.append("occurrence identity drift from frozen plan")
    if [occurrence["series_id"]]!=p["required_absent_series_ids"]:
        errors.append("series identity drift from frozen plan")
    if [s["source_id"] for s in plan["sources"]]!=p["required_absent_source_ids"]:
        errors.append("source identity sequence drift from frozen plan")
    if occurrence["source_id"]!=occurrence["legal_basis_source_id"]:
        errors.append("Nepal canonical source must remain the legal recurring-rule authority")
    if occurrence.get("timing_type")!="SOURCE_NATIVE_CALENDAR_DATE":
        errors.append("Nepal timing type drift")
    if occurrence.get("gregorian_resolution_status")!="UNRESOLVED_AUTHORITATIVE_CONVERSION":
        errors.append("Nepal Gregorian-resolution state drift")
    if errors:
        raise SystemExit("PRECONDITION FAILED:\n- "+"\n- ".join(errors))


def build_source(item:dict,dependency_count:int)->dict:
    legal=item["source_id"]=="WSSRC-FIS-026"
    known=(
        [
            "The constitutional rule supplies the exact source-native annual date but does not supply a Gregorian conversion for 15 Jestha 2084.",
            "A current landing page may expose the constitutional document through an embedded/downloaded representation; the legal rule is manually verified.",
            "No unrestricted production-crawling licence was established in this review."
        ] if legal else [
            "The archive corroborates the federal budget process and current source-native publication dates but does not create the 2084 Gregorian conversion.",
            "Historical publication timing cannot be promoted into a future Gregorian schedule rule.",
            "No unrestricted production-crawling licence was established in this review."
        ]
    )
    return {
        "source_id":item["source_id"],
        "institution":item["institution"],
        "jurisdiction":item["jurisdiction"],
        "domain":item["domain"],
        "endpoint_role":item["endpoint_role"],
        "authoritative_url":item["authoritative_url"],
        "source_type":item["source_type"],
        "information_supplied":item["information_supplied"],
        "future_schedule_horizon":"standing annual legal rule" if legal else "current budget archive; future Gregorian mapping not asserted",
        "typical_advance_notice":"standing law" if legal else "publication/archive surface",
        "machine_readable_available":"HTML/PDF" if legal else "HTML/PDF",
        "source_timezone":item["source_timezone"],
        "recommended_verification_cadence":"annual legal-text recheck; recheck when competent 2084 dual-calendar mapping appears" if legal else "manual monthly; weekly once 2084 official calendar/schedule material appears",
        "activation_status":"ACTIVE_MANUAL_PROVENANCE_ONLY",
        "parser_type":"MANUAL_OFFICIAL_LEGAL_TEXT_VERIFICATION" if legal else "MANUAL_OFFICIAL_BUDGET_ARCHIVE_VERIFICATION",
        "known_limitations":known,
        "backup_source":item.get("backup_source"),
        "notes":"Canonical legal recurring-rule authority; no third-party calendar conversion permitted." if legal else "Supporting publication/schedule verification source; not legal-date or calendar-conversion authority.",
        "timezone_scope":"FIXED",
        "parser_version":None,
        "runtime_health_state":"UNKNOWN_NOT_LIVE_POLLED",
        "licence_constraints":"NO_UNRESTRICTED_REUSE_OR_PRODUCTION_AUTOMATION_GRANT_IDENTIFIED; MANUAL FACTUAL REFERENCE ONLY",
        "ingestion_permission":"CURATED_LEGAL_FACTUAL_METADATA_MANUAL_ONLY" if legal else "CURATED_PUBLIC_FACTS_MANUAL_REFERENCE_ONLY",
        "licence_review_status":"RIGHTS_AUDIT_REQUIRED_NO_UNRESTRICTED_REUSE_GRANT_IDENTIFIED",
        "automated_retrieval_permission":"PRODUCTION_AUTOMATION_HOLD_PENDING_PERMISSION_OR_ENDPOINT_ROUTE",
        "redistribution_permission":"MINIMAL_FACTUAL_METADATA_ONLY_NO_CONTENT_REPUBLICATION_INFERRED",
        "rights_evidence_url":item["authoritative_url"],
        "rights_summary":"Official first-order provenance retained conservatively; no unrestricted site-wide reuse licence is inferred.",
        "automation_summary":"Official status and public accessibility do not establish production crawler permission.",
        "rights_reviewed_at":"2026-09-05",
        "rights_review_scope":"SOURCE_NATIVE_CALENDAR_NEPAL_N_AUTHORITY_AND_AUTOMATION_SEPARATED",
        "rights_review_note":"Operational WORLD SIGNALS source-governance classification; not a legal opinion.",
        "monitoring_readiness_status":"RIGHTS_AUDIT_REQUIRED",
        "monitoring_priority_score":120 if legal else 160,
        "canonical_dependency_count":dependency_count,
        "monitoring_readiness_assessed_at":"2026-09-05",
        "last_successful_research_verification_at":"2026-09-05",
        "canonical_provenance_use":item["canonical_provenance_use"],
        "automated_monitoring_use":item["automated_monitoring_use"],
        "verification_mode":item["verification_mode"],
    }


def build_occurrence(item:dict)->dict:
    aid=assertion_id(item)
    return {
        "occurrence_id":item["occurrence_id"],
        "series_id":item["series_id"],
        "external_source_id":None,
        "canonical_name":item["canonical_name"],
        "short_calendar_title":item["short_calendar_title"],
        "category":item["category"],
        "subcategory":item["subcategory"],
        "jurisdiction":item["jurisdiction"],
        "region":item["region"],
        "institution":item["institution"],
        "event_type":item["event_type"],
        "record_class":"OCCURRENCE",
        "certainty_status":item["certainty_status"],
        "activation_mode":item["activation_mode"],
        "lifecycle_status":item["lifecycle_status"],
        "condition_state":"NOT_REQUIRED",
        "condition_description":None,
        "trigger_source_id":None,
        "trigger_assertion_id":None,
        "triggered_at":None,
        "trigger_verification_status":"NOT_APPLICABLE",
        "timing_type":item["timing_type"],
        "start_local":None,
        "end_local":None,
        "source_timezone":item["source_timezone"],
        "start_utc":None,
        "end_utc":None,
        "date_earliest":None,
        "date_latest":None,
        "time_precision":item["time_precision"],
        "all_day_semantics":False,
        "reference_period":"FY2084/85 (Bikram Sambat)",
        "publication_datetime":None,
        "time_status":item["time_status"],
        "time_basis":item["time_basis"],
        "publication_time_semantics":item["publication_time_semantics"],
        "native_calendar_system":item["native_calendar_system"],
        "native_calendar_year":item["native_calendar_year"],
        "native_calendar_month":item["native_calendar_month"],
        "native_calendar_day":item["native_calendar_day"],
        "source_native_date_label":item["source_native_date_label"],
        "gregorian_resolution_status":item["gregorian_resolution_status"],
        "source_id":item["source_id"],
        "primary_source_assertion_id":aid,
        "last_successful_assertion_id":aid,
        "status_history":[{
            "as_of":"2026-09-05",
            "certainty_status":"CONFIRMED",
            "lifecycle_status":"PLANNED",
            "condition_state":"NOT_REQUIRED",
            "basis":"Constitution of Nepal Article 119(3) fixes annual presentation on 15 Jestha; Gregorian conversion for 2084 remains unresolved."
        }],
        "first_announced_at":None,
        "first_discovered_at":"2026-09-05",
        "last_verified_at":"2026-09-05",
        "next_verification_due":"SOURCE_SPECIFIC",
        "parent_occurrence_id":None,
        "related_occurrence_ids":[],
        "related_documents":[{"source_id":sid,"role":"SUPPORTING_PUBLICATION_VERIFICATION"} for sid in item.get("supporting_source_ids",[])],
        "intrinsic_importance":item["intrinsic_importance"],
        "expected_market_sensitivity":item["expected_market_sensitivity"],
        "geopolitical_sensitivity":item["geopolitical_sensitivity"],
        "transmission_channels":item["transmission_channels"],
        "render_policy":item["render_policy"],
        "visibility_tier":item["visibility_tier"],
        "deadline_type":None,
        "deadline_semantics":None,
        "temporal_basis":"JURISDICTIONAL_CIVIL_DATE",
        "legal_basis_source_id":item["legal_basis_source_id"],
        "governing_instrument":item["governing_instrument"],
        "must_occur_by_date":None,
        "dependency_occurrence_ids":[],
        "dependency_external_ids":[],
        "condition_expression":None,
        "resolution_evidence_assertion_id":None,
        "contingency_if_missed":None,
        "monitor_escalation_start":None,
        "publication_bundle_type":"SINGLE_RELEASE",
        "render_cluster_key":None,
        "calendar_aggregation_policy":"STANDALONE",
        "fiscal_process_milestone_type":item["fiscal_process_milestone_type"],
        "derivation_sources":[item["legal_basis_source_id"]]+list(item.get("supporting_source_ids",[])),
        "notes":"The competent legal date is 15 Jestha 2084. No Gregorian date is stored or rendered until a competent source supplies an authoritative conversion; third-party calendar conversion is prohibited."
    }


def migrate_schema(schema:dict,plan:dict)->dict:
    out=copy.deepcopy(schema)
    additions=plan["schema_additions"]
    out["version"]="0.52"
    controlled=out.setdefault("controlled_vocabularies",{})
    append_absent(controlled.setdefault("timing_type",[]),additions["timing_type"],"timing_type")
    append_absent(controlled.setdefault("publication_time_semantics",[]),additions["publication_time_semantics"],"publication_time_semantics")
    append_absent(controlled.setdefault("native_calendar_system",[]),additions["native_calendar_system"],"native_calendar_system")
    append_absent(controlled.setdefault("gregorian_resolution_status",[]),additions["gregorian_resolution_status"],"gregorian_resolution_status")
    append_absent(controlled.setdefault("fiscal_process_milestone_type",[]),additions["fiscal_process_milestone_type"],"fiscal_process_milestone_type")
    timing_fields=out.setdefault("event_occurrence_fields",{}).setdefault("timing",[])
    for field_name in additions["timing_fields"]:
        append_absent(timing_fields,field_name,"event_occurrence_fields.timing")
    decisions=out.setdefault("design_decisions",[])
    append_absent(decisions,additions["design_decision"],"design_decisions")
    return out


def build_post_state(schema:dict,registry:dict,sources:dict,plan:dict):
    old_records=copy.deepcopy(registry["records"])
    old_sources=copy.deepcopy(sources["sources"])
    post_schema=migrate_schema(schema,plan)
    post_registry=copy.deepcopy(registry)
    post_sources=copy.deepcopy(sources)
    occurrence=build_occurrence(plan["occurrence"])
    new_sources=[
        build_source(plan["sources"][0],1),
        build_source(plan["sources"][1],0),
    ]
    post_registry.update(version="0.28",reference_date="2026-09-05")
    post_registry["records"].append(occurrence)
    post_registry["record_count"]=len(post_registry["records"])
    post_sources.update(version="1.69",reference_date="2026-09-05")
    post_sources["sources"].extend(new_sources)

    if post_registry["records"][:-1]!=old_records:
        raise SystemExit("POSTCONDITION FAILED: pre-existing canonical objects changed")
    if post_sources["sources"][:-2]!=old_sources:
        raise SystemExit("POSTCONDITION FAILED: pre-existing source objects changed")

    validation=validate_registry(post_registry,post_sources)
    if not validation.ok:
        raise SystemExit("POSTCONDITION FAILED: registry validation: "+"; ".join(validation.errors))

    expected=plan["postconditions"]
    checks={
        "schema_version":post_schema.get("version")==expected["canonical_schema_version"],
        "canonical_version":post_registry.get("version")==expected["canonical_registry_version"],
        "canonical_count":post_registry.get("record_count")==expected["canonical_record_count"],
        "source_version":post_sources.get("version")==expected["source_registry_version"],
        "source_count":len(post_sources.get("sources",[]))==expected["source_record_count"],
        "new_occurrence_count":1==expected["new_occurrence_count"],
        "new_series_count":1==expected["new_series_count"],
        "new_source_count":len(new_sources)==expected["new_source_count"],
        "write_gate_closed":expected["automatic_canonical_commit"] is False,
        "calendar_gate_closed":expected["google_calendar_write"] is False,
        "gregorian_fields_empty":all(occurrence.get(k) is None for k in ("start_local","end_local","start_utc","end_utc","date_earliest","date_latest","publication_datetime")),
    }
    failed=[k for k,v in checks.items() if not v]
    if failed:
        raise SystemExit("POSTCONDITION FAILED: "+", ".join(failed))
    return post_schema,post_registry,post_sources,{"checks":checks,"warnings":validation.warnings,"occurrence":occurrence,"source_ids":[s["source_id"] for s in new_sources]}


def audit_text(report:dict,ledger_hash:str,expectations_hash:str)->str:
    warnings="\n".join(f"- {x}" for x in report["warnings"]) or "- none"
    return f"""# WORLD SIGNALS — Nepal source-native calendar transaction audit v0.1

**Transaction date:** 2026-09-05  
**Base:** schema v0.51; canonical v0.27 / 673; source v1.68 / 231  
**Post-state:** schema **v0.52**; canonical **v0.28 / 674**; source **v1.69 / 233**

## Added canonical occurrence
- `{report['occurrence']['occurrence_id']}` — `{report['occurrence']['canonical_name']}`
- authoritative native date: `{report['occurrence']['source_native_date_label']}`
- Gregorian resolution: `{report['occurrence']['gregorian_resolution_status']}`

## Added sources
"""+"\n".join(f"- `{sid}`" for sid in report["source_ids"])+f"""

## Invariants
- all 673 pre-existing canonical objects unchanged;
- all 231 pre-existing source objects unchanged;
- no Gregorian/local/UTC date field populated for the Nepal occurrence;
- source-native event certainty remains independent from Gregorian conversion readiness;
- North Indian Ocean cyclone-season candidate remains held under first-party definition conflict;
- automatic canonical commit OFF; Google Calendar writes OFF.

## Protected files
Change ledger SHA-256: `{ledger_hash}`  
Monitor expectations SHA-256: `{expectations_hash}`

## Validator warnings
{warnings}

This audit authorises no automatic canonical writes, no third-party calendar conversion dependency and no production crawler promotion.
"""


def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--apply",action="store_true")
    args=parser.parse_args()
    schema,registry,sources,plan=load(SCHEMA_PATH),load(REGISTRY_PATH),load(SOURCE_PATH),load(PLAN_PATH)
    ledger_hash,expectations_hash=file_hash(LEDGER_PATH),file_hash(EXPECTATIONS_PATH)
    preflight(schema,registry,sources,plan)
    post_schema,post_registry,post_sources,report=build_post_state(schema,registry,sources,plan)
    print(json.dumps({
        "mode":"APPLY" if args.apply else "CHECK_ONLY",
        "post":{
            "schema_version":post_schema["version"],
            "canonical_version":post_registry["version"],
            "canonical_count":post_registry["record_count"],
            "source_version":post_sources["version"],
            "source_count":len(post_sources["sources"]),
        },
        "occurrence_id":report["occurrence"]["occurrence_id"],
        "source_native_date_label":report["occurrence"]["source_native_date_label"],
        "gregorian_resolution_status":report["occurrence"]["gregorian_resolution_status"],
        "new_source_ids":report["source_ids"],
        "warnings":report["warnings"],
    },indent=2))
    if not args.apply:
        return
    if os.environ.get(APPLY_ENV)!="YES":
        raise SystemExit(f"APPLY BLOCKED: set {APPLY_ENV}=YES")
    dump(SCHEMA_PATH,post_schema)
    dump(REGISTRY_PATH,post_registry)
    dump(SOURCE_PATH,post_sources)
    AUDIT_PATH.write_text(audit_text(report,ledger_hash,expectations_hash),encoding="utf-8")
    if file_hash(LEDGER_PATH)!=ledger_hash:
        raise SystemExit("PROTECTED FILE CHANGED: change ledger")
    if file_hash(EXPECTATIONS_PATH)!=expectations_hash:
        raise SystemExit("PROTECTED FILE CHANGED: monitor expectations")
    print("APPLIED: Nepal source-native calendar transaction N")


if __name__=="__main__":
    main()
