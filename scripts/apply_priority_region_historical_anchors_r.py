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
from src.world_signals.analysis import analysis_population_readiness
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
PLAN_PATH = ROOT / "data/coverage/PRIORITY_REGION_HISTORICAL_ANCHORS_R_PLAN_v0.1.json"
TRANSACTION_AUDIT_PATH = ROOT / "data/coverage/PRIORITY_REGION_HISTORICAL_ANCHORS_R_TRANSACTION_AUDIT_v0.1.md"
APPLY_ENV = "WORLD_SIGNALS_APPLY_HISTORICAL_ANCHORS_R"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def overlay_semantics(overlay: dict) -> dict:
    return {k: copy.deepcopy(v) for k, v in overlay.items() if k not in {"version", "canonical_checkpoint"}}


def transaction_time() -> str:
    return datetime.now(ZoneInfo("Australia/Melbourne")).isoformat(timespec="seconds")


def preflight(registry: dict, schema: dict, sources: dict, ledger: dict, overlay: dict, plan: dict) -> None:
    p = plan["preconditions"]
    errors: list[str] = []
    if str(schema.get("version")) != p["canonical_schema_version"]:
        errors.append("canonical schema version drift")
    if str(registry.get("version")) != p["canonical_registry_version"]:
        errors.append("canonical registry version drift")
    if registry.get("record_count") != p["canonical_record_count"] or len(registry.get("records", [])) != p["canonical_record_count"]:
        errors.append("canonical record-count drift")
    if str(sources.get("version")) != p["source_registry_version"] or len(sources.get("sources", [])) != p["source_record_count"]:
        errors.append("source registry drift")
    if str(ledger.get("version")) != p["change_ledger_version"] or len(ledger.get("changes", [])) != p["change_ledger_count"]:
        errors.append("change ledger drift")
    if str(overlay.get("version")) != p["biosecurity_overlay_version"] or overlay.get("canonical_checkpoint") != p["biosecurity_overlay_checkpoint"]:
        errors.append("biosecurity overlay checkpoint drift")

    by_occ = {r.get("occurrence_id"): r for r in registry.get("records", [])}
    by_source = {s.get("source_id"): s for s in sources.get("sources", [])}
    existing_change_ids = {c.get("change_id") for c in ledger.get("changes", [])}

    for oid in p["required_absent_occurrence_ids"]:
        if oid in by_occ:
            errors.append(f"occurrence identity collision: {oid}")
    for sid in p["required_absent_source_ids"]:
        if sid in by_source:
            errors.append(f"source identity collision: {sid}")
    for anchor in plan["anchors"]:
        template = by_occ.get(anchor["template_occurrence_id"])
        if not template:
            errors.append(f"missing template occurrence {anchor['template_occurrence_id']}")
            continue
        if template.get("series_id") != anchor["series_id"]:
            errors.append(f"template series mismatch for {anchor['occurrence_id']}")
        if template.get("source_id") != anchor["schedule_source_id"]:
            errors.append(f"template schedule-source mismatch for {anchor['occurrence_id']}")
        if anchor["change_id"] in existing_change_ids:
            errors.append(f"change identity collision: {anchor['change_id']}")
        if anchor["schedule_source_id"] not in by_source:
            errors.append(f"missing schedule source {anchor['schedule_source_id']}")

    for sid, count in p["required_source_dependency_counts"].items():
        row = by_source.get(sid)
        if not row or row.get("canonical_dependency_count") != count:
            errors.append(f"source dependency-count drift for {sid}")

    for item in plan["new_completion_sources"]:
        if item["clone_source_id"] not in by_source:
            errors.append(f"missing completion-source clone {item['clone_source_id']}")

    overlay_errors = validate_biosecurity_overlay(registry, overlay)
    errors.extend(f"biosecurity overlay pre-state: {e}" for e in overlay_errors)
    if errors:
        raise SystemExit("PRECONDITION FAILED:\n- " + "\n- ".join(errors))


def build_completion_source(base: dict, item: dict, reference_date: str) -> dict:
    out = copy.deepcopy(base)
    out.update(
        source_id=item["source_id"],
        institution=item["institution"],
        jurisdiction=item["jurisdiction"],
        endpoint_role=item["endpoint_role"],
        authoritative_url=item["authoritative_url"],
        source_type=item["source_type"],
        information_supplied=item["information_supplied"],
        future_schedule_horizon="post-event publication surface; not forward schedule authority",
        typical_advance_notice="post-event publication",
        notes=item["notes"],
        canonical_dependency_count=0,
        last_successful_research_verification_at=reference_date,
        monitoring_readiness_assessed_at=reference_date,
    )
    return out


def patch_data_products(row: dict, reference_period: str) -> None:
    for product in row.get("data_products") or []:
        if isinstance(product, dict):
            product["reference_period"] = reference_period


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

    out.update(
        occurrence_id=item["occurrence_id"],
        series_id=item["series_id"],
        canonical_name=item["canonical_name"],
        short_calendar_title=item["short_calendar_title"],
        certainty_status="CONFIRMED",
        lifecycle_status="COMPLETED",
        timing_type=timing["timing_type"],
        start_local=timing["start_local"],
        end_local=timing["end_local"],
        source_timezone=timing["source_timezone"],
        start_utc=timing["start_utc"],
        end_utc=timing["end_utc"],
        date_earliest=None,
        date_latest=None,
        time_precision=timing["time_precision"],
        all_day_semantics=timing["all_day_semantics"],
        reference_period=item["reference_period"],
        publication_datetime=timing["publication_datetime"],
        time_status=timing["time_status"],
        time_basis=timing["time_basis"],
        source_id=item["schedule_source_id"],
        primary_source_assertion_id=item["schedule_assertion_id"],
        last_successful_assertion_id=item["completion_assertion_id"],
        first_announced_at=None,
        first_discovered_at=reference_date,
        last_verified_at=reference_date,
        next_verification_due="SOURCE_SPECIFIC",
        population_tranche="ANALYSIS_HISTORICAL_ANCHOR_R",
        related_documents=[{
            "source_id": item["completion_source_id"],
            "role": "COMPLETION_OUTCOME_VERIFICATION",
            "source_locator": item["outcome_url"],
        }],
        derivation_sources=list(dict.fromkeys([item["schedule_source_id"], item["completion_source_id"]])),
        status_history=[{
            "as_of": reference_date,
            "certainty_status": "CONFIRMED",
            "lifecycle_status": "COMPLETED",
            "condition_state": out.get("condition_state", "NOT_REQUIRED"),
            "change_reason": "Historical occurrence admitted after authoritative post-event verification; completion is not inferred from elapsed time.",
            "source_assertion_id": item["completion_assertion_id"],
            "basis": item["completion_basis"],
        }],
        notes=(item["completion_basis"] + " Historical admission preserves the existing series/timing source separately from completion/outcome evidence."),
    )
    if item["occurrence_id"] == "WSO-HIST-R-IN-GDP-2026Q1":
        out["publication_time_semantics"] = "EXACT_LOCAL_TIME"
    patch_data_products(out, item["reference_period"])
    return out


def build_ledger_change(item: dict, committed_at: str, before_version: str, after_version: str) -> dict:
    timing = item["timing"]
    new_values = {
        "canonical_presence": True,
        "series_id": item["series_id"],
        "certainty_status": "CONFIRMED",
        "lifecycle_status": "COMPLETED",
        "timing_type": timing["timing_type"],
        "start_local": timing["start_local"],
        "end_local": timing["end_local"],
        "start_utc": timing["start_utc"],
        "reference_period": item["reference_period"],
    }
    return {
        "change_id": item["change_id"],
        "occurrence_id": item["occurrence_id"],
        "change_type": "HISTORICAL_OCCURRENCE_ADMISSION",
        "old_values": {"canonical_presence": False},
        "new_values": new_values,
        "source_assertion_id": item["completion_assertion_id"],
        "review_state": "APPROVED_FOR_CANONICAL_COMMIT",
        "reviewed_at": committed_at,
        "review_basis": [
            item["outcome_url"],
            item["completion_basis"],
            "Existing series and schedule-source identity are reused; no new series taxonomy is created.",
            "The occurrence is admitted as completed only because a competent first-party post-event source verifies it; elapsed time alone is not evidence of completion.",
        ],
        "commit_mode": "REVIEWED_HISTORICAL_ANCHOR_R",
        "committed_at": committed_at,
        "registry_version_before": before_version,
        "registry_version_after": after_version,
        "canonical_mutation_committed": True,
    }


def build_post_state(registry: dict, schema: dict, sources: dict, ledger: dict, overlay: dict, plan: dict, committed_at: str):
    old_records = copy.deepcopy(registry["records"])
    old_sources = copy.deepcopy(sources["sources"])
    old_changes = copy.deepcopy(ledger["changes"])
    old_overlay_semantics = overlay_semantics(overlay)
    by_occ = {r["occurrence_id"]: r for r in registry["records"]}
    by_source = {s["source_id"]: s for s in sources["sources"]}
    reference_date = plan["reference_date"]

    post_registry = copy.deepcopy(registry)
    anchors = [build_anchor(by_occ[item["template_occurrence_id"]], item, reference_date) for item in plan["anchors"]]
    post_registry["version"] = plan["postconditions"]["canonical_registry_version"]
    post_registry["reference_date"] = reference_date
    post_registry["records"].extend(anchors)
    post_registry["record_count"] = len(post_registry["records"])

    post_sources = copy.deepcopy(sources)
    post_sources["version"] = plan["postconditions"]["source_registry_version"]
    post_sources["reference_date"] = reference_date
    post_source_by_id = {s["source_id"]: s for s in post_sources["sources"]}
    for sid, before_count in plan["preconditions"]["required_source_dependency_counts"].items():
        post_source_by_id[sid]["canonical_dependency_count"] = before_count + 1
    new_sources = [
        build_completion_source(by_source[item["clone_source_id"]], item, reference_date)
        for item in plan["new_completion_sources"]
    ]
    post_sources["sources"].extend(new_sources)

    post_ledger = copy.deepcopy(ledger)
    post_ledger["version"] = plan["postconditions"]["change_ledger_version"]
    post_ledger["reference_date"] = reference_date
    post_ledger["changes"].extend(
        build_ledger_change(
            item,
            committed_at,
            plan["preconditions"]["canonical_registry_version"],
            plan["postconditions"]["canonical_registry_version"],
        )
        for item in plan["anchors"]
    )

    post_overlay = copy.deepcopy(overlay)
    post_overlay["version"] = plan["postconditions"]["biosecurity_overlay_version"]
    post_overlay["canonical_checkpoint"] = copy.deepcopy(plan["postconditions"]["biosecurity_overlay_checkpoint"])

    if post_registry["records"][: len(old_records)] != old_records:
        raise SystemExit("POSTCONDITION FAILED: pre-existing canonical records changed")
    if post_ledger["changes"][: len(old_changes)] != old_changes:
        raise SystemExit("POSTCONDITION FAILED: pre-existing change ledger entries changed")
    if overlay_semantics(post_overlay) != old_overlay_semantics:
        raise SystemExit("POSTCONDITION FAILED: biosecurity overlay semantic content changed")

    changed_existing_sources = []
    for before, after in zip(old_sources, post_sources["sources"][: len(old_sources)]):
        if before != after:
            changed_existing_sources.append(before["source_id"])
            expected = copy.deepcopy(before)
            expected["canonical_dependency_count"] = before.get("canonical_dependency_count", 0) + 1
            if after != expected:
                raise SystemExit(f"POSTCONDITION FAILED: unexpected existing-source mutation {before['source_id']}")
    expected_changed = sorted(plan["preconditions"]["required_source_dependency_counts"])
    if sorted(changed_existing_sources) != expected_changed:
        raise SystemExit("POSTCONDITION FAILED: existing-source mutation scope drift")

    validation = validate_registry(post_registry, post_sources)
    if not validation.ok:
        raise SystemExit("POSTCONDITION FAILED: registry validation: " + "; ".join(validation.errors))
    overlay_errors = validate_biosecurity_overlay(post_registry, post_overlay)
    if overlay_errors:
        raise SystemExit("POSTCONDITION FAILED: biosecurity overlay validation: " + "; ".join(overlay_errors))

    expected = plan["postconditions"]
    if str(schema.get("version")) != expected["canonical_schema_version"]:
        raise SystemExit("POSTCONDITION FAILED: canonical schema changed or drifted")
    if post_registry.get("version") != expected["canonical_registry_version"] or post_registry.get("record_count") != expected["canonical_record_count"]:
        raise SystemExit("POSTCONDITION FAILED: canonical post-state mismatch")
    if post_sources.get("version") != expected["source_registry_version"] or len(post_sources["sources"]) != expected["source_record_count"]:
        raise SystemExit("POSTCONDITION FAILED: source post-state mismatch")
    if post_ledger.get("version") != expected["change_ledger_version"] or len(post_ledger["changes"]) != expected["change_ledger_count"]:
        raise SystemExit("POSTCONDITION FAILED: ledger post-state mismatch")
    if post_overlay.get("version") != expected["biosecurity_overlay_version"] or post_overlay.get("canonical_checkpoint") != expected["biosecurity_overlay_checkpoint"]:
        raise SystemExit("POSTCONDITION FAILED: overlay post-state mismatch")

    new_ids = {a["occurrence_id"] for a in anchors}
    if new_ids != set(plan["preconditions"]["required_absent_occurrence_ids"]):
        raise SystemExit("POSTCONDITION FAILED: new occurrence scope mismatch")
    for anchor in anchors:
        if anchor.get("lifecycle_status") != "COMPLETED" or anchor.get("certainty_status") != "CONFIRMED":
            raise SystemExit(f"POSTCONDITION FAILED: incomplete historical anchor {anchor['occurrence_id']}")
        history = anchor.get("status_history") or []
        if len(history) != 1 or history[0].get("source_assertion_id") != anchor.get("last_successful_assertion_id"):
            raise SystemExit(f"POSTCONDITION FAILED: completion assertion history mismatch {anchor['occurrence_id']}")

    analysis_schema = load(ANALYSIS_SCHEMA_PATH)
    analysis_reviews = load(ANALYSIS_REVIEWS_PATH)
    readiness = analysis_population_readiness(analysis_schema, analysis_reviews, post_registry)
    if readiness["eligible_completed_occurrence_count"] != 9:
        raise SystemExit("POSTCONDITION FAILED: expected exactly nine completed analytical anchors")
    priority = {row["region"]: row for row in readiness["priority_geographic_stress_regions"]}
    for region, count in expected["priority_region_completed_anchor_counts"].items():
        if priority.get(region, {}).get("eligible_completed_count") != count:
            raise SystemExit(f"POSTCONDITION FAILED: priority anchor count mismatch for {region}")
        if priority[region].get("state") != "ELIGIBLE_UNREVIEWED":
            raise SystemExit(f"POSTCONDITION FAILED: priority readiness state mismatch for {region}")
    if readiness["broad_population_state"] != expected["analysis_readiness_broad_state"]:
        raise SystemExit("POSTCONDITION FAILED: Analysis readiness did not move to review-gap state")

    return post_registry, post_sources, post_ledger, post_overlay, {
        "anchors": anchors,
        "new_sources": new_sources,
        "changed_existing_sources": changed_existing_sources,
        "warnings": validation.warnings,
        "readiness": readiness,
    }


def audit_text(report: dict, hashes: dict) -> str:
    warnings = "\n".join(f"- {w}" for w in report["warnings"]) or "- none"
    anchors = "\n".join(
        f"- `{a['occurrence_id']}` — {a['canonical_name']} — {a['region']} — `{a['event_type']}`"
        for a in report["anchors"]
    )
    sources = "\n".join(f"- `{s['source_id']}` — {s['endpoint_role']}" for s in report["new_sources"])
    priority = "\n".join(
        f"- {row['region']}: {row['eligible_completed_count']} completed; {row['state']}"
        for row in report["readiness"]["priority_geographic_stress_regions"]
    )
    return f"""# WORLD SIGNALS — Priority-region historical anchors R transaction audit v0.1

**Transaction date:** 2026-09-06  
**Post-state:** canonical **v0.29 / 678**; sources **v1.71 / 236**; change ledger **v0.16 / 48**; biosecurity overlay **v0.4 @ v0.29/678**

## Added completed historical anchors
{anchors}

## Added completion/outcome source surfaces
{sources}

## Existing schedule-source dependency updates
- `WSSRC-MAC-017`: 17 → 18
- `WSSRC-REG-004`: 4 → 5
- `WSSRC-REGJ-005`: 3 → 4
- `WSSRC-REG2-006`: 4 → 5

No other pre-existing source object changes.

## Analysis readiness after canonical admission
{priority}

Broad population state: **`{report['readiness']['broad_population_state']}`**.

This is intentionally still blocked: R supplies canonical anchors but does not add reviewed Analysis packets.

## Invariants
- all 674 pre-existing canonical records unchanged;
- all 44 pre-existing change-ledger records unchanged;
- no new event series;
- completion is supported by first-party post-event evidence, never elapsed time alone;
- BI remains one two-day decision-process occurrence rather than a duplicate meeting + announcement pair;
- no clock time is inferred for BI, CBE or INDEC;
- MoSPI 16:00 local is occurrence-specific first-party evidence only, not a series-wide rule;
- biosecurity semantic membership unchanged; overlay advances checkpoint only;
- automatic canonical commit OFF; Google Calendar writes OFF.

## Protected-file SHA-256 before transaction
- canonical schema: `{hashes['schema']}`
- monitor expectations: `{hashes['expectations']}`
- monitor operations policy: `{hashes['operations']}`

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
    plan = load(PLAN_PATH)
    hashes = {
        "schema": file_hash(SCHEMA_PATH),
        "expectations": file_hash(EXPECTATIONS_PATH),
        "operations": file_hash(OPERATIONS_PATH),
    }
    preflight(registry, schema, sources, ledger, overlay, plan)
    committed_at = transaction_time()
    post_registry, post_sources, post_ledger, post_overlay, report = build_post_state(
        registry, schema, sources, ledger, overlay, plan, committed_at
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
            "analysis_readiness": report["readiness"]["broad_population_state"],
        },
        "occurrence_ids": [a["occurrence_id"] for a in report["anchors"]],
        "new_source_ids": [s["source_id"] for s in report["new_sources"]],
        "warnings": report["warnings"],
    }, indent=2))

    if not args.apply:
        return
    if os.environ.get(APPLY_ENV) != "YES":
        raise SystemExit(f"APPLY BLOCKED: set {APPLY_ENV}=YES")

    dump(REGISTRY_PATH, post_registry)
    dump(SOURCE_PATH, post_sources)
    dump(LEDGER_PATH, post_ledger)
    dump(OVERLAY_PATH, post_overlay)
    TRANSACTION_AUDIT_PATH.write_text(audit_text(report, hashes), encoding="utf-8")

    if file_hash(SCHEMA_PATH) != hashes["schema"]:
        raise SystemExit("POST-WRITE FAILED: canonical schema changed")
    if file_hash(EXPECTATIONS_PATH) != hashes["expectations"]:
        raise SystemExit("POST-WRITE FAILED: monitor expectations changed")
    if file_hash(OPERATIONS_PATH) != hashes["operations"]:
        raise SystemExit("POST-WRITE FAILED: monitor operations policy changed")


if __name__ == "__main__":
    main()
