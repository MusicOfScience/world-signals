from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from world_signals.monitor_coverage import build_monitor_coverage_audit

CANONICAL=ROOT/"data/canonical/registry.json"
SOURCES=ROOT/"data/sources/registry.json"
EXPECTATIONS=ROOT/"data/monitor/expectations.json"
LEDGER=ROOT/"data/changes/ledger.json"
OPERATIONS=ROOT/"data/monitor/operations_policy.json"
ANALYSIS_REVIEWS=ROOT/"data/analysis/event_reviews.json"
ANALYSIS_EVIDENCE=ROOT/"data/analysis/evidence_registry.json"
AUDIT=ROOT/"data/monitor/EIA_WPSR_MONITOR_AS_TRANSACTION_AUDIT_v0.1.md"

EXPECTED_BASE_SHA="4b25bb452f3def253cf86254e5ad6abdbe8b9f13"
EXPECTED_SCHEDULE_SHA="8f972e877fdd56dd836f6a0cc7bc0abea73c21bfd01dd8bbc3b784ea7eacec87"
TARGET_SOURCE_ID="WSSRC-COM-003"
TARGET_SERIES_ID="WSER-COM-EIA-WPSR"
TARGET_OCCURRENCE_IDS=[f"WSO-COM-A-{n:04d}" for n in range(13,29)]

SCHEDULE={
    "standard_release_day":"Wednesday",
    "standard_release_time_local":"10:30",
    "standard_time_semantics":"AFTER",
    "source_timezone":"America/New_York",
    "holiday_exceptions":[
        {"week_ending":"2024-12-27","alternate_release_date":"2025-01-02","release_day":"Thursday","release_time_local":"11:00","holiday":"New Year's Day"},
        {"week_ending":"2025-01-17","alternate_release_date":"2025-01-23","release_day":"Thursday","release_time_local":"12:00","holiday":"Martin Luther King Jr. Day / Inauguration"},
        {"week_ending":"2025-02-14","alternate_release_date":"2025-02-20","release_day":"Thursday","release_time_local":"12:00","holiday":"President's Day"},
        {"week_ending":"2025-05-23","alternate_release_date":"2025-05-29","release_day":"Thursday","release_time_local":"12:00","holiday":"Memorial Day"},
        {"week_ending":"2025-08-29","alternate_release_date":"2025-09-04","release_day":"Thursday","release_time_local":"12:00","holiday":"Labor Day"},
        {"week_ending":"2025-10-10","alternate_release_date":"2025-10-16","release_day":"Thursday","release_time_local":"12:00","holiday":"Columbus Day"},
        {"week_ending":"2025-11-07","alternate_release_date":"2025-11-13","release_day":"Thursday","release_time_local":"12:00","holiday":"Veterans Day"},
        {"week_ending":"2025-12-19","alternate_release_date":"2025-12-29","release_day":"Monday","release_time_local":"17:00","holiday":"Christmas"},
        {"week_ending":"2026-01-16","alternate_release_date":"2026-01-22","release_day":"Thursday","release_time_local":"12:00","holiday":"Martin Luther King Jr. Day"},
        {"week_ending":"2026-02-13","alternate_release_date":"2026-02-19","release_day":"Thursday","release_time_local":"12:00","holiday":"President's Day"},
        {"week_ending":"2026-05-22","alternate_release_date":"2026-05-28","release_day":"Thursday","release_time_local":"12:00","holiday":"Memorial Day"},
        {"week_ending":"2026-09-04","alternate_release_date":"2026-09-10","release_day":"Thursday","release_time_local":"12:00","holiday":"Labor Day"},
        {"week_ending":"2026-10-09","alternate_release_date":"2026-10-15","release_day":"Thursday","release_time_local":"12:00","holiday":"Columbus Day"},
        {"week_ending":"2026-11-06","alternate_release_date":"2026-11-12","release_day":"Thursday","release_time_local":"12:00","holiday":"Veterans Day"}
    ],
    "schedule_sha256":EXPECTED_SCHEDULE_SHA,
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_hash(value: object) -> str:
    raw=json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",",":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def assert_prestate(canonical: dict, sources: dict, expectations: dict) -> dict:
    errors=[]
    if canonical.get("version")!="0.37" or len(canonical.get("records",[]))!=687:
        errors.append("canonical prestate must be v0.37 / 687")
    if sources.get("version")!="1.78" or len(sources.get("sources",[]))!=242:
        errors.append("source prestate must be v1.78 / 242")
    if expectations.get("version")!="0.9" or len(expectations.get("adapters",[]))!=7:
        errors.append("monitor expectations prestate must be v0.9 / 7 adapters")
    source=next((x for x in sources.get("sources",[]) if x.get("source_id")==TARGET_SOURCE_ID),None)
    if not source:
        errors.append("target EIA source missing")
    else:
        checks={
            "monitoring_readiness_status":"PILOT_VALIDATED_NO_AUTO_COMMIT",
            "monitoring_activation_status":"PILOT_ONLY_NO_CANONICAL_AUTO_COMMIT",
            "automated_monitoring_use":"ENDPOINT_REVIEW_REQUIRED",
            "verification_mode":"AUTOMATED_PILOT",
            "canonical_dependency_count":16,
        }
        for key,value in checks.items():
            if source.get(key)!=value:
                errors.append(f"target source {key} drifted: {source.get(key)!r}")
    ids=[x.get("occurrence_id") for x in canonical.get("records",[]) if x.get("series_id")==TARGET_SERIES_ID]
    if ids!=TARGET_OCCURRENCE_IDS:
        errors.append(f"WPSR occurrence scope drifted: {ids}")
    if any(x.get("adapter_id")=="EIA_WPSR_SCHEDULE" for x in expectations.get("adapters",[])):
        errors.append("EIA_WPSR_SCHEDULE already configured")
    payload={k:v for k,v in SCHEDULE.items() if k!="schedule_sha256"}
    if stable_hash(payload)!=EXPECTED_SCHEDULE_SHA:
        errors.append("embedded reviewed schedule hash does not match normalized payload")
    if errors:
        raise RuntimeError("; ".join(errors))
    return source


def build_poststate(canonical: dict, sources: dict, expectations: dict) -> tuple[dict,dict,dict]:
    new_sources=deepcopy(sources)
    new_expectations=deepcopy(expectations)
    source=next(x for x in new_sources["sources"] if x.get("source_id")==TARGET_SOURCE_ID)

    new_sources["version"]="1.79"
    source.update({
        "automated_monitoring_use":"CLEARED",
        "automated_monitoring_scope":"EIA_WPSR_SCHEDULE_READ_ONLY_SENTINEL_ONLY",
        "monitoring_activation_status":"PILOT_READ_ONLY_SCHEDULE_SENTINEL_NO_AUTO_COMMIT",
        "live_adapter_id":"EIA_WPSR_SCHEDULE",
        "monitor_parser_type":"HTML_RULE_TABLE_SEMANTIC_SCHEDULE_SENTINEL",
        "monitor_parser_version":"eia-wpsr-schedule-0.1",
        "monitor_route_validated_at":"2026-09-06T03:30:54Z",
        "monitor_route_validation_run_id":34009176451,
        "monitor_route_validation_job_id":101421838658,
        "monitor_route_baseline_sha256":EXPECTED_SCHEDULE_SHA,
        "monitor_route_scope_note":"Clearance is limited to read-only polling of the authoritative WPSR schedule rule/holiday-exception page. It does not confer publication-completion authority, generic eia.gov polling permission, or production reliance on test JSON/CSV formats.",
    })

    new_expectations["version"]="0.10"
    new_expectations["adapters"].append({
        "adapter_id":"EIA_WPSR_SCHEDULE",
        "source_id":TARGET_SOURCE_ID,
        "canonical_occurrence_ids":TARGET_OCCURRENCE_IDS,
        "monitor_role":"PUBLICATION_SCHEDULE_RULE_AND_EXCEPTION_SENTINEL",
        "cadence":"DAILY",
        "endpoint":{
            "url":"https://www.eia.gov/petroleum/supply/weekly/schedule.php",
            "transport":"HTML_RULE_TABLE",
            "source_timezone":"America/New_York"
        },
        "baseline":{
            "observed_at":"2026-09-06T03:30:54Z",
            "schedule_sha256":EXPECTED_SCHEDULE_SHA,
            "schedule":SCHEDULE
        },
        "source_failure_policy":"SOURCE_HEALTH_ONLY_NO_EVENT_MUTATION",
        "schedule_change_policy":"GENERATE_REVIEW_CANDIDATE_REQUIRE_AUTHORITATIVE_EIA_REVERIFICATION",
        "completion_policy":"SCHEDULE_PAGE_MUST_NOT_COMPLETE_OCCURRENCES",
        "elapsed_policy":"DO_NOT_INFER_COMPLETION_FROM_ELAPSED_SCHEDULE_TIME",
        "publication_index_policy":"CORROBORATION_ONLY_INDEX_LAG_KNOWN",
        "time_semantics_policy":"PRESERVE_SOURCE_AFTER_SEMANTICS_DO_NOT_UPGRADE_TO_EXACT",
        "test_format_policy":"DO_NOT_DEPEND_ON_PROVISIONAL_WPSR_TEST_JSON_OR_CSV",
        "automatic_commit_allowed":False
    })

    audit=build_monitor_coverage_audit(canonical,new_sources,new_expectations)
    expected={
        "configured_adapter_count":8,
        "unique_monitor_source_count":7,
        "scoped_occurrence_count":43,
        "scoped_series_count":11,
        "scoped_institution_count":6,
        "scoped_region_count":4,
        "scoped_category_count":6,
    }
    if audit["totals"]!=expected:
        raise RuntimeError(f"post-AS monitor coverage mismatch: {audit['totals']}")
    eia=next(x for x in audit["adapter_inventory"] if x["adapter_id"]=="EIA_WPSR_SCHEDULE")
    if eia["regions"]!=["Cross-regional / Global"] or eia["categories"]!=["ENERGY_COMMODITIES"]:
        raise RuntimeError(f"EIA route diversity projection unexpected: {eia}")
    return new_sources,new_expectations,audit


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--check",action="store_true")
    args=parser.parse_args()

    canonical=load(CANONICAL)
    sources=load(SOURCES)
    expectations=load(EXPECTATIONS)
    assert_prestate(canonical,sources,expectations)

    protected={path:file_hash(path) for path in [CANONICAL,LEDGER,OPERATIONS,ANALYSIS_REVIEWS,ANALYSIS_EVIDENCE]}
    new_sources,new_expectations,audit=build_poststate(canonical,sources,expectations)

    result={
        "status":"PASS_CHECK" if args.check else "READY_TO_WRITE",
        "expected_base_sha":EXPECTED_BASE_SHA,
        "source_prestate":[sources.get("version"),len(sources.get("sources",[]))],
        "source_poststate":[new_sources.get("version"),len(new_sources.get("sources",[]))],
        "monitor_prestate":[expectations.get("version"),len(expectations.get("adapters",[]))],
        "monitor_poststate":[new_expectations.get("version"),len(new_expectations.get("adapters",[]))],
        "monitor_coverage_poststate":audit["totals"],
        "schedule_sha256":EXPECTED_SCHEDULE_SHA,
        "canonical_mutation":"NONE",
        "automatic_commit_allowed":False,
    }
    if args.check:
        print(json.dumps(result,indent=2))
        return 0

    if os.getenv("WORLD_SIGNALS_APPLY_MONITOR_AS")!="1":
        raise RuntimeError("write gate closed: set WORLD_SIGNALS_APPLY_MONITOR_AS=1")

    write_json(SOURCES,new_sources)
    write_json(EXPECTATIONS,new_expectations)

    for path,before in protected.items():
        if file_hash(path)!=before:
            raise RuntimeError(f"protected path mutated: {path.relative_to(ROOT)}")

    now=datetime.now(timezone.utc).isoformat()
    AUDIT.write_text(
        "# WORLD SIGNALS — EIA WPSR monitor AS transaction audit v0.1\n\n"
        f"- executed at: `{now}`\n"
        f"- exact base: `{EXPECTED_BASE_SHA}`\n"
        "- source registry: `v1.78 / 242` → `v1.79 / 242`\n"
        "- monitor expectations: `v0.9 / 7` → `v0.10 / 8`\n"
        f"- reviewed EIA schedule semantic SHA-256: `{EXPECTED_SCHEDULE_SHA}`\n"
        "- canonical registry mutation: **NONE**\n"
        "- Change Ledger mutation: **NONE**\n"
        "- Analysis mutation: **NONE**\n"
        "- operations policy mutation: **NONE**\n"
        "- automatic canonical commit: **OFF**\n"
        "- Google Calendar write: **OFF**\n"
        "- route contract: schedule rule/holiday exceptions only; elapsed time and schedule presence do not establish publication completion.\n"
        f"- post-AS monitor coverage totals: `{json.dumps(audit['totals'],sort_keys=True)}`\n",
        encoding="utf-8",
    )
    result["status"]="WROTE_CONTROLLED_AS_STATE"
    print(json.dumps(result,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
