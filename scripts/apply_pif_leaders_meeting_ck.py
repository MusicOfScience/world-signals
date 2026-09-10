#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.world_signals.analytical_overlays import validate_biosecurity_overlay
from src.world_signals.analysis import validate_analysis
from src.world_signals.validation import validate_registry

CANONICAL_PATH = ROOT / "data/canonical/registry.json"
CANONICAL_SCHEMA_PATH = ROOT / "data/canonical/schema.json"
SOURCE_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
OPERATIONS_PATH = ROOT / "data/monitor/operations_policy.json"
LIVE_SCHEMA_PATH = ROOT / "data/live_intelligence/schema.json"
LIVE_OBSERVATIONS_PATH = ROOT / "data/live_intelligence/observations.json"
LIVE_EVIDENCE_PATH = ROOT / "data/live_intelligence/evidence_registry.json"
ANALYSIS_SCHEMA_PATH = ROOT / "data/analysis/schema.json"
ANALYSIS_REVIEWS_PATH = ROOT / "data/analysis/event_reviews.json"
ANALYSIS_EVIDENCE_PATH = ROOT / "data/analysis/evidence_registry.json"
PLAN_PATH = ROOT / "data/coverage/PIF_LEADERS_MEETING_CK_PLAN_v0.1.json"
AUDIT_PATH = ROOT / "data/coverage/PIF_LEADERS_MEETING_CK_TRANSACTION_AUDIT_v0.1.md"
QUARANTINE_PATH = ROOT / "OPEC_QUARANTINE.md"
APPLY_ENV = "WORLD_SIGNALS_APPLY_PIF_LEADERS_CK"
APPLY_VALUE = "REVIEWED_APPLY"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transaction_time() -> str:
    return datetime.now(ZoneInfo("Australia/Melbourne")).isoformat(timespec="seconds")


def overlay_semantics(overlay: dict) -> dict:
    return {
        key: copy.deepcopy(value)
        for key, value in overlay.items()
        if key not in {"version", "canonical_checkpoint"}
    }


def source_without_dependency(row: dict) -> dict:
    out = copy.deepcopy(row)
    out.pop("canonical_dependency_count", None)
    return out


def counts_analysis_live_inputs(reviews: dict) -> tuple[int, int]:
    live_inputs = 0
    revisions = 0
    for review in reviews.get("reviews", []):
        live_inputs += len(review.get("live_inputs") or [])
        if review.get("revision_of_analysis_id"):
            revisions += 1
    return live_inputs, revisions


def preflight(
    registry: dict,
    schema: dict,
    sources: dict,
    ledger: dict,
    overlay: dict,
    expectations: dict,
    live_observations: dict,
    live_evidence: dict,
    analysis_schema: dict,
    analysis_reviews: dict,
    analysis_evidence: dict,
    plan: dict,
) -> None:
    p = plan["preconditions"]
    errors: list[str] = []
    live_input_count, revision_count = counts_analysis_live_inputs(analysis_reviews)

    checks = (
        (str(schema.get("version")) == p["canonical_schema_version"], "canonical schema version drift"),
        (str(registry.get("version")) == p["canonical_registry_version"], "canonical registry version drift"),
        (registry.get("record_count") == p["canonical_record_count"] == len(registry.get("records", [])), "canonical record-count drift"),
        (str(sources.get("version")) == p["source_registry_version"], "source registry version drift"),
        (len(sources.get("sources", [])) == p["source_record_count"], "source record-count drift"),
        (str(ledger.get("version")) == p["change_ledger_version"], "change ledger version drift"),
        (len(ledger.get("changes", [])) == p["change_ledger_count"], "change ledger count drift"),
        (str(overlay.get("version")) == p["biosecurity_overlay_version"], "biosecurity overlay version drift"),
        (overlay.get("canonical_checkpoint") == p["biosecurity_overlay_checkpoint"], "biosecurity overlay checkpoint drift"),
        (str(expectations.get("version")) == p["monitor_expectations_version"], "Monitor expectations version drift"),
        (len(expectations.get("adapters", [])) == p["monitor_adapter_count"], "Monitor adapter-count drift"),
        (len(live_observations.get("observations", [])) == p["live_observation_count"], "Live observation-count drift"),
        (len(live_evidence.get("evidence", [])) == p["live_evidence_count"], "Live evidence-count drift"),
        (len(analysis_reviews.get("reviews", [])) == p["analysis_review_count"], "Analysis review-count drift"),
        (len(analysis_evidence.get("evidence", [])) == p["analysis_evidence_count"], "Analysis evidence-count drift"),
        (live_input_count == p["production_live_input_count"], "Analysis production Live-input count drift"),
        (revision_count == p["production_revision_count"], "Analysis production revision count drift"),
    )
    for ok, message in checks:
        if not ok:
            errors.append(message)

    records = registry.get("records", [])
    source_rows = sources.get("sources", [])
    by_occ = {row.get("occurrence_id"): row for row in records}
    by_source = {row.get("source_id"): row for row in source_rows}
    series_ids = {row.get("series_id") for row in records}
    change_ids = {row.get("change_id") for row in ledger.get("changes", [])}

    for occurrence_id in p["required_absent_occurrence_ids"]:
        if occurrence_id in by_occ:
            errors.append(f"occurrence identity collision: {occurrence_id}")
    for series_id in p["required_absent_series_ids"]:
        if series_id in series_ids:
            errors.append(f"series identity collision: {series_id}")
    for source_id in p["required_absent_source_ids"]:
        if source_id in by_source:
            errors.append(f"source identity collision: {source_id}")
    for change_id in p["required_absent_change_ids"]:
        if change_id in change_ids:
            errors.append(f"change identity collision: {change_id}")

    expected_source = p["required_existing_primary_source"]
    primary_source = by_source.get(expected_source["source_id"])
    if primary_source is None:
        errors.append("required PIF host source missing")
    else:
        for key in ("institution", "authoritative_url", "source_timezone", "canonical_dependency_count"):
            if primary_source.get(key) != expected_source[key]:
                errors.append(f"PIF source field drift: {key}")
        actual_dependency_count = sum(
            1 for row in records if row.get("source_id") == expected_source["source_id"]
        )
        if actual_dependency_count != 0 or actual_dependency_count != primary_source.get("canonical_dependency_count"):
            errors.append("PIF source dependency count does not match Canonical truth")

    item = plan["occurrence"]
    timing = item["timing"]
    expected_timing = {
        "timing_type": "MULTI_DAY_LOCAL",
        "start_local": "2026-08-30",
        "end_local": "2026-09-04",
        "source_timezone": "Pacific/Palau",
        "start_utc": None,
        "end_utc": None,
        "time_precision": "DAY_RANGE",
        "all_day_semantics": True,
        "time_status": "CONFIRMED",
        "time_basis": "EXPLICIT_AUTHORITATIVE_SCHEDULE",
    }
    if timing != expected_timing:
        errors.append(f"PIF timing contract drift: {timing!r}")
    if item.get("lifecycle_status") != "COMPLETED" or item.get("certainty_status") != "CONFIRMED":
        errors.append("PIF reviewed lifecycle/certainty contract drift")
    if item.get("source_id") != expected_source["source_id"]:
        errors.append("PIF primary source identity drift")

    support = plan["supporting_source"]
    if support.get("canonical_dependency_count") != 0:
        errors.append("supporting completion source must have zero primary Canonical dependencies")
    if support.get("automated_monitoring_use") != "PROHIBITED_OR_RIGHTS_HOLD":
        errors.append("supporting completion source automation gate unexpectedly open")
    if support.get("verification_mode") != "RIGHTS_HELD_MANUAL_ONLY":
        errors.append("supporting completion source verification posture drift")
    if support.get("monitor_route_authorised") is not False:
        errors.append("supporting completion source must not authorise a Monitor route")

    future = plan["future_host_context"]
    if future.get("year") != 2027 or future.get("exact_dates_found") is not False:
        errors.append("2027 host-context/date boundary drift")
    if future.get("canonical_dated_occurrence_authorised") is not False:
        errors.append("2027 dated Canonical occurrence must remain unauthorised")

    if any(
        item["occurrence_id"] in (adapter.get("canonical_occurrence_ids") or [])
        or adapter.get("source_id") in {item["source_id"], support["source_id"]}
        for adapter in expectations.get("adapters", [])
    ):
        errors.append("PIF already appears in Monitor expectations before CK")

    validation = validate_registry(registry, sources)
    errors.extend(f"Canonical pre-state: {error}" for error in validation.errors)
    errors.extend(
        f"biosecurity overlay pre-state: {error}"
        for error in validate_biosecurity_overlay(registry, overlay)
    )
    analysis_report = validate_analysis(analysis_schema, analysis_evidence, analysis_reviews, registry)
    errors.extend(f"Analysis pre-state: {error}" for error in analysis_report.errors)

    if errors:
        raise SystemExit("PRECONDITION FAILED:\n- " + "\n- ".join(errors))


def build_supporting_source(primary_source: dict, item: dict, reference_date: str) -> dict:
    out = copy.deepcopy(primary_source)
    for key in (
        "live_adapter_id",
        "automated_monitoring_scope",
        "monitor_endpoints",
        "live_validation_evidence",
        "source_role_contract",
        "related_source_ids",
        "health_source_route_state",
    ):
        out.pop(key, None)
    out.update(
        source_id=item["source_id"],
        institution=item["institution"],
        jurisdiction=item["jurisdiction"],
        domain=item["domain"],
        endpoint_role=item["endpoint_role"],
        authoritative_url=item["authoritative_url"],
        source_type=item["source_type"],
        information_supplied=item["information_supplied"],
        future_schedule_horizon=item["future_schedule_horizon"],
        typical_advance_notice="post-event publication",
        machine_readable_available="HTML",
        source_timezone=item["source_timezone"],
        recommended_verification_cadence="manual historical recheck only",
        activation_status="ACTIVE_GUARDED",
        parser_type="MANUAL_HTML_PROVENANCE",
        parser_version=None,
        known_limitations=[
            "Supporting post-event completion/outcome corroboration only; not forward schedule authority.",
            "No general reuse licence or production automated-retrieval permission was established in CK.",
        ],
        backup_source=None,
        notes="Supporting-only Cook Islands first-party completion evidence for the 55th PIF Leaders Meeting; zero primary Canonical dependencies.",
        timezone_scope="FIXED",
        runtime_health_state="MANUAL_RESEARCH_ROUTE_VERIFIED_PRODUCTION_AUTOMATION_HOLD",
        licence_constraints="ALL_RIGHTS_RESERVED_NO_GENERAL_REUSE_PERMISSION_IDENTIFIED",
        ingestion_permission="CURATED_FACTUAL_METADATA_MANUAL_REFERENCE_ALLOWED",
        licence_review_status=item["licence_review_status"],
        automated_retrieval_permission=item["automated_retrieval_permission"],
        redistribution_permission=item["redistribution_permission"],
        rights_evidence_url=item["authoritative_url"],
        rights_summary=item["rights_evidence"],
        automation_summary="Public first-party access is not treated as permission for unattended production retrieval; CK retains manual supporting provenance only.",
        rights_reviewed_at=reference_date,
        rights_review_scope="CK_PIF_SUPPORTING_SOURCE_RIGHTS_REVIEW",
        rights_review_note="Operational WORLD SIGNALS source-governance classification; not legal advice.",
        monitoring_readiness_status="RIGHTS_OR_LICENSE_HOLD",
        monitoring_priority_score=0,
        canonical_dependency_count=0,
        monitoring_readiness_assessed_at=reference_date,
        last_successful_research_verification_at=reference_date,
        canonical_provenance_use=item["canonical_provenance_use"],
        automated_monitoring_use=item["automated_monitoring_use"],
        verification_mode=item["verification_mode"],
        governance_backfill_reviewed_at=reference_date,
        governance_backfill_basis="Cook Islands PMO supplies first-party post-event corroboration; no general automation/reuse permission was established, so the source is supporting manual provenance only.",
        monitoring_activation_status="MANUAL_AUTHORITATIVE_RECHECK_ONLY",
    )
    return out


def build_occurrence(item: dict, reference_date: str) -> dict:
    timing = item["timing"]
    return {
        "occurrence_id": item["occurrence_id"],
        "series_id": item["series_id"],
        "external_source_id": None,
        "canonical_name": item["canonical_name"],
        "short_calendar_title": item["short_calendar_title"],
        "category": item["category"],
        "subcategory": "multilateral_regional_governance",
        "jurisdiction": "Pacific Islands Forum",
        "region": item["region"],
        "institution": item["institution"],
        "event_type": item["event_type"],
        "record_class": "OCCURRENCE",
        "certainty_status": item["certainty_status"],
        "activation_mode": "EXPLICITLY_SCHEDULED",
        "lifecycle_status": item["lifecycle_status"],
        "condition_state": "NOT_REQUIRED",
        "condition_description": None,
        "trigger_source_id": None,
        "trigger_assertion_id": None,
        "triggered_at": None,
        "trigger_verification_status": "NOT_APPLICABLE",
        "timing_type": timing["timing_type"],
        "start_local": timing["start_local"],
        "end_local": timing["end_local"],
        "source_timezone": timing["source_timezone"],
        "start_utc": timing["start_utc"],
        "end_utc": timing["end_utc"],
        "date_earliest": None,
        "date_latest": None,
        "time_precision": timing["time_precision"],
        "all_day_semantics": timing["all_day_semantics"],
        "reference_period": None,
        "publication_datetime": None,
        "time_status": timing["time_status"],
        "time_basis": timing["time_basis"],
        "location": item["location"],
        "source_id": item["source_id"],
        "primary_source_assertion_id": item["primary_source_assertion_id"],
        "last_successful_assertion_id": item["completion_source_assertion_id"],
        "status_history": [
            {
                "as_of": reference_date,
                "certainty_status": item["certainty_status"],
                "lifecycle_status": item["lifecycle_status"],
                "condition_state": "NOT_REQUIRED",
                "change_reason": "Historical occurrence admitted after first-party post-event verification; completion is not inferred from elapsed time.",
                "source_assertion_id": item["completion_source_assertion_id"],
                "basis": "Cook Islands Office of the Prime Minister reported on 4 September 2026 that participation in the 55th PIF Leaders Meeting had concluded and that outcomes were captured in the 2026 Forum Communiqué.",
            }
        ],
        "first_announced_at": None,
        "first_discovered_at": reference_date,
        "last_verified_at": reference_date,
        "next_verification_due": "SOURCE_SPECIFIC",
        "parent_occurrence_id": None,
        "related_occurrence_ids": [],
        "related_documents": [
            {
                "source_id": item["completion_source_id"],
                "role": "COMPLETION_AND_OUTCOME_CORROBORATION",
                "source_locator": item["completion_url"],
            }
        ],
        "intrinsic_importance": "HIGH",
        "expected_market_sensitivity": "LOW",
        "geopolitical_sensitivity": "HIGH",
        "transmission_channels": [
            "regional_governance",
            "geopolitics",
            "security",
            "climate_policy",
            "fisheries_oceans",
            "development_finance",
            "trade",
        ],
        "render_policy": "INCLUDE",
        "visibility_tier": "ESSENTIAL",
        "deadline_is_actual_event_time": False,
        "derivation_sources": [item["source_id"], item["completion_source_id"]],
        "coverage_program_id": "WSCP-POST-CJ-CROSS-LAYER-PRESSURE",
        "coverage_repair_reason": "PACIFIC_APEX_INSTITUTIONAL_SIGNAL_CANONICAL_OMISSION",
        "population_horizon_policy": "SINGLE_VERIFIED_COMPLETED_2026_OCCURRENCE",
        "selection_rationale": "CJ found a stronger upstream Oceania/Pacific omission than a quota-driven Live specimen: the annual PIF Leaders Meeting had a governed source but no Canonical series/occurrence.",
        "future_schedule_deferred": "2027 Auckland host confirmed; exact dates not authoritatively established in CK and no dated successor is created.",
        "population_tranche": "PIF_LEADERS_MEETING_CK",
        "notes": "Palau host evidence supplies the 30 August–4 September 2026 civil range in Pacific/Palau. Cook Islands PMO supplies separate first-party completion/outcome corroboration. No opening/closing clock or UTC boundary is inferred, and 2027 host context is not converted into invented dates.",
    }


def build_ledger_change(item: dict, committed_at: str, before_version: str, after_version: str) -> dict:
    timing = item["timing"]
    return {
        "change_id": item["change_id"],
        "occurrence_id": item["occurrence_id"],
        "change_type": "HISTORICAL_OCCURRENCE_ADMISSION",
        "old_values": {"canonical_presence": False},
        "new_values": {
            "canonical_presence": True,
            "series_id": item["series_id"],
            "certainty_status": item["certainty_status"],
            "lifecycle_status": item["lifecycle_status"],
            "timing_type": timing["timing_type"],
            "start_local": timing["start_local"],
            "end_local": timing["end_local"],
            "source_timezone": timing["source_timezone"],
            "start_utc": None,
            "end_utc": None,
            "time_precision": timing["time_precision"],
        },
        "source_assertion_id": item["completion_source_assertion_id"],
        "review_state": "APPROVED_FOR_CANONICAL_COMMIT",
        "reviewed_at": committed_at,
        "review_basis": [
            item["primary_schedule_url"],
            item["completion_url"],
            "Existing WSSRC-INT-012 source identity is reused as timing/venue authority; a separate Cook Islands PMO supporting source records completion/outcome corroboration.",
            "Completion is admitted from first-party post-event evidence and is not inferred from elapsed time.",
            "Auckland/New Zealand 2027 host confirmation supplies no authoritative meeting dates and creates no dated successor occurrence.",
        ],
        "commit_mode": "REVIEWED_PIF_LEADERS_MEETING_CK",
        "committed_at": committed_at,
        "registry_version_before": before_version,
        "registry_version_after": after_version,
        "canonical_mutation_committed": True,
    }


def build_post_state(
    registry: dict,
    schema: dict,
    sources: dict,
    ledger: dict,
    overlay: dict,
    expectations: dict,
    live_schema: dict,
    live_observations: dict,
    live_evidence: dict,
    analysis_schema: dict,
    analysis_reviews: dict,
    analysis_evidence: dict,
    plan: dict,
    committed_at: str,
) -> tuple[dict, dict, dict, dict]:
    expected = plan["expected_post_state"]
    reference_date = plan["reference_date"]
    item = plan["occurrence"]
    support = plan["supporting_source"]

    old_records = copy.deepcopy(registry["records"])
    old_source_rows = copy.deepcopy(sources["sources"])
    old_changes = copy.deepcopy(ledger["changes"])
    old_overlay_semantics = overlay_semantics(overlay)

    post_registry = copy.deepcopy(registry)
    post_registry["version"] = expected["canonical_registry_version"]
    post_registry["reference_date"] = reference_date
    post_registry["records"].append(build_occurrence(item, reference_date))
    post_registry["record_count"] = len(post_registry["records"])

    post_sources = copy.deepcopy(sources)
    post_sources["version"] = expected["source_registry_version"]
    post_sources["reference_date"] = reference_date
    post_by_source = {row["source_id"]: row for row in post_sources["sources"]}
    primary_before = copy.deepcopy(post_by_source[item["source_id"]])
    post_by_source[item["source_id"]]["canonical_dependency_count"] = 1
    post_sources["sources"].append(build_supporting_source(primary_before, support, reference_date))

    post_ledger = copy.deepcopy(ledger)
    post_ledger["version"] = expected["change_ledger_version"]
    post_ledger["reference_date"] = reference_date
    post_ledger["changes"].append(
        build_ledger_change(
            item,
            committed_at,
            plan["preconditions"]["canonical_registry_version"],
            expected["canonical_registry_version"],
        )
    )

    post_overlay = copy.deepcopy(overlay)
    post_overlay["version"] = expected["biosecurity_overlay_version"]
    post_overlay["canonical_checkpoint"] = copy.deepcopy(expected["biosecurity_overlay_checkpoint"])

    errors: list[str] = []
    if post_registry["records"][:-1] != old_records:
        errors.append("pre-existing Canonical records changed")
    if post_registry["record_count"] != expected["canonical_record_count"]:
        errors.append("post Canonical record count mismatch")
    if len(post_sources["sources"]) != expected["source_record_count"]:
        errors.append("post source count mismatch")
    if len(post_ledger["changes"]) != expected["change_ledger_count"]:
        errors.append("post change-ledger count mismatch")
    if post_ledger["changes"][:-1] != old_changes:
        errors.append("pre-existing Change Ledger rows changed")
    if overlay_semantics(post_overlay) != old_overlay_semantics:
        errors.append("biosecurity overlay semantic content changed")

    original_by_source = {row["source_id"]: row for row in old_source_rows}
    final_by_source = {row["source_id"]: row for row in post_sources["sources"]}
    for source_id, before in original_by_source.items():
        after = final_by_source[source_id]
        if source_id == item["source_id"]:
            if source_without_dependency(after) != source_without_dependency(before):
                errors.append("existing PIF source changed outside canonical_dependency_count")
            if before.get("canonical_dependency_count") != 0 or after.get("canonical_dependency_count") != 1:
                errors.append("existing PIF source dependency change is not exactly 0→1")
        elif after != before:
            errors.append(f"unrelated source changed: {source_id}")

    new_occurrence = post_registry["records"][-1]
    if new_occurrence["occurrence_id"] != item["occurrence_id"]:
        errors.append("unexpected appended Canonical occurrence")
    if new_occurrence["timing_type"] != "MULTI_DAY_LOCAL" or new_occurrence["time_precision"] != "DAY_RANGE":
        errors.append("PIF multi-day temporal semantics drift")
    if new_occurrence["start_utc"] is not None or new_occurrence["end_utc"] is not None:
        errors.append("PIF civil-date range must not synthesize UTC endpoints")
    if new_occurrence["source_timezone"] != "Pacific/Palau":
        errors.append("PIF native timezone drift")
    if new_occurrence["lifecycle_status"] != "COMPLETED":
        errors.append("PIF post-state lifecycle is not COMPLETED")

    support_after = final_by_source.get(support["source_id"])
    if not support_after:
        errors.append("supporting Cook Islands source missing")
    else:
        if support_after.get("canonical_dependency_count") != 0:
            errors.append("supporting Cook Islands source gained a primary dependency")
        if support_after.get("automated_monitoring_use") != "PROHIBITED_OR_RIGHTS_HOLD":
            errors.append("supporting Cook Islands source automation gate opened")
        if support_after.get("live_adapter_id"):
            errors.append("supporting Cook Islands source unexpectedly has a Live/Monitor adapter")

    if any(row.get("series_id") == item["series_id"] and row.get("occurrence_id") != item["occurrence_id"] for row in post_registry["records"]):
        errors.append("CK created an additional PIF occurrence")
    if any("PIF" in str(row.get("canonical_name", "")) and "2027" in str(row.get("canonical_name", "")) for row in post_registry["records"]):
        errors.append("CK created a 2027 PIF occurrence")

    validation = validate_registry(post_registry, post_sources)
    errors.extend(f"Canonical post-state: {error}" for error in validation.errors)
    errors.extend(
        f"biosecurity overlay post-state: {error}"
        for error in validate_biosecurity_overlay(post_registry, post_overlay)
    )
    analysis_report = validate_analysis(analysis_schema, analysis_evidence, analysis_reviews, post_registry)
    errors.extend(f"Analysis post-state: {error}" for error in analysis_report.errors)

    if errors:
        raise SystemExit("POSTCONDITION FAILED:\n- " + "\n- ".join(errors))

    return post_registry, post_sources, post_ledger, post_overlay


def audit_markdown(plan: dict, committed_at: str, hashes_before: dict[str, str], hashes_after: dict[str, str]) -> str:
    item = plan["occurrence"]
    support = plan["supporting_source"]
    expected = plan["expected_post_state"]
    protected_ok = all(hashes_before[key] == hashes_after[key] for key in hashes_before)
    return f"""# WORLD SIGNALS — PIF Leaders Meeting CK transaction audit v0.1

**Status:** MATERIALISED / GUARDED  
**Reference date:** {plan['reference_date']}  
**Base main:** `{plan['base_main_sha']}`  
**Committed at:** `{committed_at}`

## Reviewed mutation

- admitted one stable series: `{plan['series']['series_id']}`;
- admitted one completed occurrence: `{item['occurrence_id']}` — {item['canonical_name']};
- timing: `{item['timing']['start_local']}` through `{item['timing']['end_local']}`, `MULTI_DAY_LOCAL`, `DAY_RANGE`, native timezone `Pacific/Palau`, no synthetic UTC endpoints;
- reused primary Palau host source `{item['source_id']}` and changed only its Canonical dependency count 0→1;
- added supporting-only Cook Islands completion source `{support['source_id']}` with zero primary Canonical dependencies and production automation held;
- no dated 2027 occurrence created; Auckland/New Zealand remains host context only until authoritative dates exist.

## Governed state transition

- Canonical: v0.41 / 689 → **v{expected['canonical_registry_version']} / {expected['canonical_record_count']}**;
- Sources: v2.03 / 257 → **v{expected['source_registry_version']} / {expected['source_record_count']}**;
- Change Ledger: v0.27 / 62 → **v{expected['change_ledger_version']} / {expected['change_ledger_count']}**;
- Biosecurity overlay: v0.16 → **v{expected['biosecurity_overlay_version']}**, semantic content unchanged, Canonical checkpoint advanced to v0.42 / 690;
- Monitor expectations: unchanged v0.28 / 26 adapters;
- Live Intelligence: unchanged 7 observations / 10 evidence rows;
- Analysis: unchanged 22 reviews / 97 evidence rows / 1 production Live input / 1 production revision.

## Authority boundary

- automatic Canonical commit: **OFF**;
- Google Calendar write: **OFF**;
- PIF Monitor route: **NOT CREATED**;
- Monitor→Live: **OFF**;
- PIF communiqué Live observation: **NOT CREATED**;
- Live→Analysis: **OFF**;
- public Live/Analysis projection: **OFF**;
- OPEC CE quarantine: **UNTOUCHED**.

## Protected-layer hash check

Protected non-CK layers byte-identical across the transaction: **{str(protected_ok).lower()}**.

The protected hash set covers Monitor expectations/operations, Live schema/observations/evidence, Analysis schema/reviews/evidence and `OPEC_QUARANTINE.md`.

## Provenance discipline

The Palau host site supplies the whole-event date range and venue. Cook Islands PMO supplies separate first-party post-event completion/outcome corroboration. Completion is not inferred from elapsed time. The confirmed 2027 Auckland host context is not upgraded into an unsourced date.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    registry = load(CANONICAL_PATH)
    schema = load(CANONICAL_SCHEMA_PATH)
    sources = load(SOURCE_PATH)
    ledger = load(LEDGER_PATH)
    overlay = load(OVERLAY_PATH)
    expectations = load(EXPECTATIONS_PATH)
    live_schema = load(LIVE_SCHEMA_PATH)
    live_observations = load(LIVE_OBSERVATIONS_PATH)
    live_evidence = load(LIVE_EVIDENCE_PATH)
    analysis_schema = load(ANALYSIS_SCHEMA_PATH)
    analysis_reviews = load(ANALYSIS_REVIEWS_PATH)
    analysis_evidence = load(ANALYSIS_EVIDENCE_PATH)
    plan = load(PLAN_PATH)

    preflight(
        registry,
        schema,
        sources,
        ledger,
        overlay,
        expectations,
        live_observations,
        live_evidence,
        analysis_schema,
        analysis_reviews,
        analysis_evidence,
        plan,
    )

    protected_paths = {
        "monitor_expectations": EXPECTATIONS_PATH,
        "monitor_operations": OPERATIONS_PATH,
        "live_schema": LIVE_SCHEMA_PATH,
        "live_observations": LIVE_OBSERVATIONS_PATH,
        "live_evidence": LIVE_EVIDENCE_PATH,
        "analysis_schema": ANALYSIS_SCHEMA_PATH,
        "analysis_reviews": ANALYSIS_REVIEWS_PATH,
        "analysis_evidence": ANALYSIS_EVIDENCE_PATH,
        "opec_quarantine": QUARANTINE_PATH,
    }
    hashes_before = {key: file_hash(path) for key, path in protected_paths.items()}
    committed_at = transaction_time()
    post_registry, post_sources, post_ledger, post_overlay = build_post_state(
        registry,
        schema,
        sources,
        ledger,
        overlay,
        expectations,
        live_schema,
        live_observations,
        live_evidence,
        analysis_schema,
        analysis_reviews,
        analysis_evidence,
        plan,
        committed_at,
    )

    result = {
        "status": "SIMULATION_PASS" if not args.apply else "MATERIALISED",
        "canonical": {
            "version": post_registry["version"],
            "record_count": post_registry["record_count"],
        },
        "sources": {
            "version": post_sources["version"],
            "count": len(post_sources["sources"]),
        },
        "change_ledger": {
            "version": post_ledger["version"],
            "count": len(post_ledger["changes"]),
        },
        "biosecurity_overlay": {
            "version": post_overlay["version"],
            "canonical_checkpoint": post_overlay["canonical_checkpoint"],
        },
        "automatic_canonical_commit": False,
        "google_calendar_write": False,
        "pif_monitor_route_created": False,
        "live_population_changed": False,
        "analysis_population_changed": False,
    }

    if not args.apply:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    if os.environ.get(APPLY_ENV) != APPLY_VALUE:
        raise SystemExit(f"WRITE GATE CLOSED: set {APPLY_ENV}={APPLY_VALUE} for reviewed CK materialisation")

    dump(CANONICAL_PATH, post_registry)
    dump(SOURCE_PATH, post_sources)
    dump(LEDGER_PATH, post_ledger)
    dump(OVERLAY_PATH, post_overlay)

    hashes_after = {key: file_hash(path) for key, path in protected_paths.items()}
    changed_protected = sorted(key for key in hashes_before if hashes_before[key] != hashes_after[key])
    if changed_protected:
        raise SystemExit("PROTECTED-LAYER MUTATION: " + ", ".join(changed_protected))

    AUDIT_PATH.write_text(
        audit_markdown(plan, committed_at, hashes_before, hashes_after),
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
