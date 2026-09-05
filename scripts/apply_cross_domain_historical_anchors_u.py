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
from src.world_signals.analysis import analysis_population_readiness, validate_analysis
from src.world_signals.validation import validate_registry

REGISTRY_PATH = ROOT / "data/canonical/registry.json"
SCHEMA_PATH = ROOT / "data/canonical/schema.json"
SOURCE_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
OPERATIONS_PATH = ROOT / "data/monitor/operations_policy.json"
ANALYSIS_SCHEMA_PATH = ROOT / "data/analysis/schema.json"
ANALYSIS_REVIEWS_PATH = ROOT / "data/analysis/event_reviews.json"
ANALYSIS_EVIDENCE_PATH = ROOT / "data/analysis/evidence_registry.json"
PLAN_PATH = ROOT / "data/coverage/CROSS_DOMAIN_HISTORICAL_ANCHORS_U_PLAN_v0.1.json"
AUDIT_PATH = ROOT / "data/coverage/CROSS_DOMAIN_HISTORICAL_ANCHORS_U_TRANSACTION_AUDIT_v0.1.md"
APPLY_ENV = "WORLD_SIGNALS_APPLY_HISTORICAL_ANCHORS_U"


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


def assertion_id(item: dict, role: str) -> str:
    material = "|".join(
        str(value)
        for value in (
            item["occurrence_id"],
            item["series_id"],
            item["source_id"],
            item["completion_source_id"],
            role,
            item["timing"].get("start_local"),
            item["timing"].get("end_local"),
            item["timing"].get("source_native_date_label"),
        )
    )
    return "WSA-HU-" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def preflight(
    registry: dict,
    schema: dict,
    sources: dict,
    ledger: dict,
    overlay: dict,
    analysis_schema: dict,
    analysis_reviews: dict,
    analysis_evidence: dict,
    plan: dict,
) -> None:
    p = plan["preconditions"]
    errors: list[str] = []

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
        (str(analysis_reviews.get("version")) == p["analysis_reviews_version"], "Analysis reviews version drift"),
        (len(analysis_reviews.get("reviews", [])) == p["analysis_review_count"], "Analysis review-count drift"),
        (str(analysis_evidence.get("version")) == p["analysis_evidence_version"], "Analysis evidence version drift"),
        (len(analysis_evidence.get("evidence", [])) == p["analysis_evidence_count"], "Analysis evidence-count drift"),
    )
    for ok, message in checks:
        if not ok:
            errors.append(message)

    by_occ = {row.get("occurrence_id"): row for row in registry.get("records", [])}
    by_source = {row.get("source_id"): row for row in sources.get("sources", [])}
    existing_change_ids = {row.get("change_id") for row in ledger.get("changes", [])}

    for occurrence_id in p["required_absent_occurrence_ids"]:
        if occurrence_id in by_occ:
            errors.append(f"occurrence identity collision: {occurrence_id}")
    for source_id in p["required_absent_source_ids"]:
        if source_id in by_source:
            errors.append(f"source identity collision: {source_id}")
    for template_id, expected_series in p["required_templates"].items():
        template = by_occ.get(template_id)
        if not template:
            errors.append(f"missing template occurrence: {template_id}")
        elif template.get("series_id") != expected_series:
            errors.append(f"template series drift: {template_id}")
    for source_id, expected_count in p["required_existing_source_dependency_counts"].items():
        source = by_source.get(source_id)
        if not source:
            errors.append(f"missing required existing source: {source_id}")
        elif source.get("canonical_dependency_count") != expected_count:
            errors.append(f"source dependency-count drift: {source_id}")
    for item in plan["anchors"]:
        if item["change_id"] in existing_change_ids:
            errors.append(f"change identity collision: {item['change_id']}")
        if by_occ.get(item["template_occurrence_id"], {}).get("series_id") != item["series_id"]:
            errors.append(f"anchor/template series mismatch: {item['occurrence_id']}")

    overlay_errors = validate_biosecurity_overlay(registry, overlay)
    errors.extend(f"biosecurity overlay pre-state: {error}" for error in overlay_errors)
    analysis_report = validate_analysis(analysis_schema, analysis_evidence, analysis_reviews, registry)
    errors.extend(f"Analysis pre-state: {error}" for error in analysis_report.errors)

    if errors:
        raise SystemExit("PRECONDITION FAILED:\n- " + "\n- ".join(errors))


def build_new_source(base: dict, item: dict, reference_date: str) -> dict:
    out = copy.deepcopy(base)
    out.update(
        source_id=item["source_id"],
        institution=item["institution"],
        jurisdiction=item["jurisdiction"],
        domain=item["domain"],
        endpoint_role=item["endpoint_role"],
        authoritative_url=item["authoritative_url"],
        backup_source=item["backup_source"],
        source_type=item["source_type"],
        information_supplied=item["information_supplied"],
        future_schedule_horizon=item["future_schedule_horizon"],
        typical_advance_notice=item["typical_advance_notice"],
        source_timezone=item["source_timezone"],
        notes=item["notes"],
        canonical_dependency_count=item["canonical_dependency_count"],
        recommended_verification_cadence="manual historical recheck if the official archive or final-report surface changes",
        last_successful_research_verification_at=reference_date,
        monitoring_readiness_assessed_at=reference_date,
    )
    return out


def build_anchor(template: dict, item: dict, reference_date: str) -> dict:
    out = copy.deepcopy(template)
    timing = item["timing"]
    for key in (
        "population_horizon_policy",
        "coverage_program_id",
        "coverage_repair_reason",
        "selection_rationale",
        "future_schedule_deferred",
    ):
        out.pop(key, None)

    primary_assertion = assertion_id(item, "PRIMARY")
    completion_assertion = assertion_id(item, "COMPLETION")

    out.update(
        occurrence_id=item["occurrence_id"],
        series_id=item["series_id"],
        canonical_name=item["canonical_name"],
        short_calendar_title=item["short_calendar_title"],
        certainty_status="CONFIRMED",
        lifecycle_status="COMPLETED",
        timing_type=timing["timing_type"],
        start_local=timing.get("start_local"),
        end_local=timing.get("end_local"),
        source_timezone=timing["source_timezone"],
        start_utc=timing.get("start_utc"),
        end_utc=timing.get("end_utc"),
        date_earliest=None,
        date_latest=None,
        time_precision=timing["time_precision"],
        all_day_semantics=timing["all_day_semantics"],
        publication_datetime=None,
        time_status=timing["time_status"],
        time_basis=timing["time_basis"],
        location=item.get("location"),
        source_id=item["source_id"],
        primary_source_assertion_id=primary_assertion,
        last_successful_assertion_id=completion_assertion,
        first_announced_at=None,
        first_discovered_at=reference_date,
        last_verified_at=reference_date,
        next_verification_due="SOURCE_SPECIFIC",
        population_tranche="ANALYSIS_HISTORICAL_ANCHOR_U",
        related_documents=[{
            "source_id": item["completion_source_id"],
            "role": item["related_document_role"],
            "source_locator": item["outcome_url"],
        }],
        derivation_sources=list(dict.fromkeys([item["source_id"], item["completion_source_id"]])),
        status_history=[{
            "as_of": reference_date,
            "certainty_status": "CONFIRMED",
            "lifecycle_status": "COMPLETED",
            "condition_state": out.get("condition_state", "NOT_REQUIRED"),
            "change_reason": "Historical occurrence admitted after authoritative post-event verification; completion is not inferred from elapsed time.",
            "source_assertion_id": completion_assertion,
            "basis": item["completion_basis"],
        }],
        notes=item["completion_basis"] + " Historical admission preserves series identity and does not infer missing event-time precision.",
    )

    if item["series_id"] == "WSER-FIS-NP-FEDERAL-BUDGET":
        out.update(
            reference_period=item["reference_period"],
            publication_time_semantics=timing["publication_time_semantics"],
            native_calendar_system=timing["native_calendar_system"],
            native_calendar_year=timing["native_calendar_year"],
            native_calendar_month=timing["native_calendar_month"],
            native_calendar_day=timing["native_calendar_day"],
            source_native_date_label=timing["source_native_date_label"],
            gregorian_resolution_status=timing["gregorian_resolution_status"],
        )
    return out


def build_ledger_change(item: dict, committed_at: str, before_version: str, after_version: str) -> dict:
    timing = item["timing"]
    new_values = {
        "canonical_presence": True,
        "series_id": item["series_id"],
        "certainty_status": "CONFIRMED",
        "lifecycle_status": "COMPLETED",
        "timing_type": timing["timing_type"],
        "start_local": timing.get("start_local"),
        "end_local": timing.get("end_local"),
        "start_utc": timing.get("start_utc"),
    }
    if timing["timing_type"] == "SOURCE_NATIVE_CALENDAR_DATE":
        new_values.update(
            source_native_date_label=timing["source_native_date_label"],
            native_calendar_system=timing["native_calendar_system"],
            gregorian_resolution_status=timing["gregorian_resolution_status"],
        )
    return {
        "change_id": item["change_id"],
        "occurrence_id": item["occurrence_id"],
        "change_type": "HISTORICAL_OCCURRENCE_ADMISSION",
        "old_values": {"canonical_presence": False},
        "new_values": new_values,
        "source_assertion_id": assertion_id(item, "COMPLETION"),
        "review_state": "APPROVED_FOR_CANONICAL_COMMIT",
        "reviewed_at": committed_at,
        "review_basis": [
            item["outcome_url"],
            item["completion_basis"],
            "Existing canonical series identity is reused; no new series taxonomy is created.",
            "Completion is admitted only from competent first-party post-event evidence, never elapsed time alone.",
        ],
        "commit_mode": "REVIEWED_HISTORICAL_ANCHOR_U",
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
    analysis_schema: dict,
    analysis_reviews: dict,
    analysis_evidence: dict,
    plan: dict,
    committed_at: str,
):
    old_records = copy.deepcopy(registry["records"])
    old_sources = copy.deepcopy(sources["sources"])
    old_changes = copy.deepcopy(ledger["changes"])
    old_overlay_semantics = overlay_semantics(overlay)
    by_occ = {row["occurrence_id"]: row for row in registry["records"]}
    by_source = {row["source_id"]: row for row in sources["sources"]}
    reference_date = plan["reference_date"]
    expected = plan["postconditions"]

    post_registry = copy.deepcopy(registry)
    new_anchors = [
        build_anchor(by_occ[item["template_occurrence_id"]], item, reference_date)
        for item in plan["anchors"]
    ]
    post_registry["version"] = expected["canonical_registry_version"]
    post_registry["reference_date"] = reference_date
    post_registry["records"].extend(new_anchors)
    post_registry["record_count"] = len(post_registry["records"])

    post_sources = copy.deepcopy(sources)
    post_sources["version"] = expected["source_registry_version"]
    post_sources["reference_date"] = reference_date
    post_source_by_id = {row["source_id"]: row for row in post_sources["sources"]}
    for source_id in ("WSSRC-INT-033", "WSSRC-FIS-026"):
        post_source_by_id[source_id]["canonical_dependency_count"] += 1
    new_sources = [
        build_new_source(by_source[item["clone_source_id"]], item, reference_date)
        for item in plan["new_sources"]
    ]
    post_sources["sources"].extend(new_sources)

    post_ledger = copy.deepcopy(ledger)
    post_ledger["version"] = expected["change_ledger_version"]
    post_ledger["reference_date"] = reference_date
    post_ledger["changes"].extend(
        build_ledger_change(
            item,
            committed_at,
            plan["preconditions"]["canonical_registry_version"],
            expected["canonical_registry_version"],
        )
        for item in plan["anchors"]
    )

    post_overlay = copy.deepcopy(overlay)
    post_overlay["version"] = expected["biosecurity_overlay_version"]
    post_overlay["canonical_checkpoint"] = copy.deepcopy(expected["biosecurity_overlay_checkpoint"])

    if post_registry["records"][: len(old_records)] != old_records:
        raise SystemExit("POSTCONDITION FAILED: pre-existing canonical records changed")
    if post_ledger["changes"][: len(old_changes)] != old_changes:
        raise SystemExit("POSTCONDITION FAILED: pre-existing change-ledger rows changed")
    if overlay_semantics(post_overlay) != old_overlay_semantics:
        raise SystemExit("POSTCONDITION FAILED: biosecurity overlay semantic content changed")

    changed_existing_sources: list[str] = []
    for before, after in zip(old_sources, post_sources["sources"][: len(old_sources)]):
        if before != after:
            changed_existing_sources.append(before["source_id"])
            expected_row = copy.deepcopy(before)
            if before["source_id"] in {"WSSRC-INT-033", "WSSRC-FIS-026"}:
                expected_row["canonical_dependency_count"] = before.get("canonical_dependency_count", 0) + 1
            if after != expected_row:
                raise SystemExit(f"POSTCONDITION FAILED: unexpected existing-source mutation {before['source_id']}")
    if sorted(changed_existing_sources) != ["WSSRC-FIS-026", "WSSRC-INT-033"]:
        raise SystemExit("POSTCONDITION FAILED: existing-source mutation scope drift")

    registry_report = validate_registry(post_registry, post_sources)
    if not registry_report.ok:
        raise SystemExit("POSTCONDITION FAILED: registry validation: " + "; ".join(registry_report.errors))
    overlay_errors = validate_biosecurity_overlay(post_registry, post_overlay)
    if overlay_errors:
        raise SystemExit("POSTCONDITION FAILED: biosecurity overlay validation: " + "; ".join(overlay_errors))
    analysis_report = validate_analysis(analysis_schema, analysis_evidence, analysis_reviews, post_registry)
    if not analysis_report.ok:
        raise SystemExit("POSTCONDITION FAILED: Analysis validation: " + "; ".join(analysis_report.errors))

    checks = (
        (str(schema.get("version")) == expected["canonical_schema_version"], "canonical schema drift"),
        (post_registry["version"] == expected["canonical_registry_version"] and post_registry["record_count"] == expected["canonical_record_count"], "canonical post-state mismatch"),
        (post_sources["version"] == expected["source_registry_version"] and len(post_sources["sources"]) == expected["source_record_count"], "source post-state mismatch"),
        (post_ledger["version"] == expected["change_ledger_version"] and len(post_ledger["changes"]) == expected["change_ledger_count"], "ledger post-state mismatch"),
        (post_overlay["version"] == expected["biosecurity_overlay_version"] and post_overlay["canonical_checkpoint"] == expected["biosecurity_overlay_checkpoint"], "overlay post-state mismatch"),
        (str(analysis_reviews.get("version")) == expected["analysis_reviews_version"] and len(analysis_reviews.get("reviews", [])) == expected["analysis_review_count"], "Analysis reviews changed"),
        (str(analysis_evidence.get("version")) == expected["analysis_evidence_version"] and len(analysis_evidence.get("evidence", [])) == expected["analysis_evidence_count"], "Analysis evidence changed"),
    )
    for ok, message in checks:
        if not ok:
            raise SystemExit("POSTCONDITION FAILED: " + message)

    readiness = analysis_population_readiness(analysis_schema, analysis_reviews, post_registry)
    if readiness["eligible_completed_occurrence_count"] != expected["eligible_completed_occurrence_count"]:
        raise SystemExit("POSTCONDITION FAILED: completed-anchor count mismatch")
    if readiness["reviewed_occurrence_count"] != expected["reviewed_occurrence_count"]:
        raise SystemExit("POSTCONDITION FAILED: reviewed-anchor count mismatch")
    if readiness["broad_population_state"] != expected["broad_population_state"]:
        raise SystemExit("POSTCONDITION FAILED: broad Analysis readiness mismatch")

    return post_registry, post_sources, post_ledger, post_overlay, {
        "anchors": new_anchors,
        "new_sources": new_sources,
        "changed_existing_sources": changed_existing_sources,
        "readiness": readiness,
        "registry_warnings": list(registry_report.warnings),
    }


def audit_text(report: dict, hashes: dict[str, str]) -> str:
    anchor_lines = "\n".join(
        f"- `{row['occurrence_id']}` — {row['canonical_name']} — `{row['event_type']}`"
        for row in report["anchors"]
    )
    warnings = "\n".join(f"- {warning}" for warning in report["registry_warnings"]) or "- none"
    readiness = report["readiness"]
    return f"""# WORLD SIGNALS — Cross-domain historical anchors U transaction audit v0.1

**Transaction date:** 2026-09-06  
**Post-state:** canonical **v0.30 / 681**; sources **v1.72 / 237**; change ledger **v0.17 / 51**; biosecurity overlay **v0.5 @ v0.30/681**  
**Analysis:** reviews **v0.4 / 8**; evidence **v0.4 / 21** — unchanged

## Added completed historical anchors
{anchor_lines}

## Source changes
- added `WSSRC-INT-034` — UNODA BWC 2026 past-meeting archive — canonical dependency count 1;
- `WSSRC-INT-033` — WOAH final report: dependency count 1 → 2;
- `WSSRC-FIS-026` — Nepal constitutional budget-date authority: dependency count 1 → 2;
- `WSSRC-FIS-027` remains 0: it is supporting completion/publication evidence, not primary legal-date authority;
- no other pre-existing source object changes.

## Analysis readiness after canonical admission
- eligible completed occurrences: **{readiness['eligible_completed_occurrence_count']}**;
- reviewed occurrences: **{readiness['reviewed_occurrence_count']}**;
- reviewed event-type diversity: **{readiness['reviewed_event_type_diversity']}**;
- broad state: **`{readiness['broad_population_state']}`**.

This tranche deliberately creates new analytical choice. It does not review the three new anchors and does not promote the previously held Bank of Canada event merely because it was the prior final backlog item.

## Temporal and ontology invariants
- BWC split daily programme hours are not converted into a continuous canonical timestamp;
- WOAH remains `AGRICULTURE_FOOD`; One Health/biosecurity relationships remain cross-domain analytical context;
- Nepal remains source-native `15 Jestha 2083` with `UNRESOLVED_AUTHORITATIVE_CONVERSION` and no fabricated Gregorian or UTC timestamp;
- the Nepal Ministry of Finance CMS publication time is not treated as the constitutional presentation time;
- no new event series or canonical schema vocabulary is introduced;
- all 678 pre-existing canonical records remain byte-structurally unchanged inside the JSON dataset;
- all 48 pre-existing change-ledger rows remain unchanged;
- biosecurity overlay semantic content remains unchanged; only version/checkpoint advances;
- automatic canonical commit remains OFF; Google Calendar writes remain OFF.

## Protected-file SHA-256 before transaction
- canonical schema: `{hashes['canonical_schema']}`
- monitor expectations: `{hashes['monitor_expectations']}`
- monitor operations policy: `{hashes['monitor_operations']}`
- Analysis schema: `{hashes['analysis_schema']}`
- Analysis reviews: `{hashes['analysis_reviews']}`
- Analysis evidence: `{hashes['analysis_evidence']}`

## Validator warnings
{warnings}
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    registry = load(REGISTRY_PATH)
    schema = load(SCHEMA_PATH)
    sources = load(SOURCE_PATH)
    ledger = load(LEDGER_PATH)
    overlay = load(OVERLAY_PATH)
    analysis_schema = load(ANALYSIS_SCHEMA_PATH)
    analysis_reviews = load(ANALYSIS_REVIEWS_PATH)
    analysis_evidence = load(ANALYSIS_EVIDENCE_PATH)
    plan = load(PLAN_PATH)

    hashes = {
        "canonical_schema": file_hash(SCHEMA_PATH),
        "monitor_expectations": file_hash(EXPECTATIONS_PATH),
        "monitor_operations": file_hash(OPERATIONS_PATH),
        "analysis_schema": file_hash(ANALYSIS_SCHEMA_PATH),
        "analysis_reviews": file_hash(ANALYSIS_REVIEWS_PATH),
        "analysis_evidence": file_hash(ANALYSIS_EVIDENCE_PATH),
    }

    preflight(
        registry,
        schema,
        sources,
        ledger,
        overlay,
        analysis_schema,
        analysis_reviews,
        analysis_evidence,
        plan,
    )
    committed_at = transaction_time()
    post_registry, post_sources, post_ledger, post_overlay, report = build_post_state(
        registry,
        schema,
        sources,
        ledger,
        overlay,
        analysis_schema,
        analysis_reviews,
        analysis_evidence,
        plan,
        committed_at,
    )

    print(json.dumps({
        "mode": "APPLY" if args.apply else "CHECK_ONLY",
        "post": {
            "canonical_version": post_registry["version"],
            "canonical_count": post_registry["record_count"],
            "source_version": post_sources["version"],
            "source_count": len(post_sources["sources"]),
            "ledger_version": post_ledger["version"],
            "ledger_count": len(post_ledger["changes"]),
            "overlay_version": post_overlay["version"],
            "overlay_checkpoint": post_overlay["canonical_checkpoint"],
            "eligible_completed": report["readiness"]["eligible_completed_occurrence_count"],
            "reviewed_completed": report["readiness"]["reviewed_occurrence_count"],
            "analysis_readiness": report["readiness"]["broad_population_state"],
        },
        "occurrence_ids": [row["occurrence_id"] for row in report["anchors"]],
        "new_source_ids": [row["source_id"] for row in report["new_sources"]],
        "changed_existing_source_ids": sorted(report["changed_existing_sources"]),
        "warnings": report["registry_warnings"],
    }, indent=2, ensure_ascii=False))

    if not args.apply:
        return
    if os.environ.get(APPLY_ENV) != "YES":
        raise SystemExit(f"APPLY BLOCKED: set {APPLY_ENV}=YES")

    dump(REGISTRY_PATH, post_registry)
    dump(SOURCE_PATH, post_sources)
    dump(LEDGER_PATH, post_ledger)
    dump(OVERLAY_PATH, post_overlay)
    AUDIT_PATH.write_text(audit_text(report, hashes), encoding="utf-8")

    protected = {
        SCHEMA_PATH: hashes["canonical_schema"],
        EXPECTATIONS_PATH: hashes["monitor_expectations"],
        OPERATIONS_PATH: hashes["monitor_operations"],
        ANALYSIS_SCHEMA_PATH: hashes["analysis_schema"],
        ANALYSIS_REVIEWS_PATH: hashes["analysis_reviews"],
        ANALYSIS_EVIDENCE_PATH: hashes["analysis_evidence"],
    }
    for path, before_hash in protected.items():
        if file_hash(path) != before_hash:
            raise SystemExit(f"POST-WRITE FAILED: protected file changed: {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
