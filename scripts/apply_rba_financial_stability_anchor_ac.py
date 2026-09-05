#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
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

CANONICAL_PATH = ROOT / "data/canonical/registry.json"
CANONICAL_SCHEMA_PATH = ROOT / "data/canonical/schema.json"
SOURCE_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
OPERATIONS_PATH = ROOT / "data/monitor/operations_policy.json"
ANALYSIS_SCHEMA_PATH = ROOT / "data/analysis/schema.json"
ANALYSIS_REVIEWS_PATH = ROOT / "data/analysis/event_reviews.json"
ANALYSIS_EVIDENCE_PATH = ROOT / "data/analysis/evidence_registry.json"
PLAN_PATH = ROOT / "data/coverage/RBA_FINANCIAL_STABILITY_HISTORICAL_ANCHOR_AC_PLAN_v0.1.json"
AUDIT_PATH = ROOT / "data/coverage/RBA_FINANCIAL_STABILITY_HISTORICAL_ANCHOR_AC_TRANSACTION_AUDIT_v0.1.md"
APPLY_ENV = "WORLD_SIGNALS_APPLY_RBA_FSR_ANCHOR_AC"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_hash(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def semantic_hash(value: object) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def overlay_semantics(overlay: dict) -> dict:
    return {
        key: copy.deepcopy(value)
        for key, value in overlay.items()
        if key not in {"version", "canonical_checkpoint"}
    }


def transaction_time() -> str:
    return datetime.now(ZoneInfo("Australia/Melbourne")).isoformat(timespec="seconds")


def expected_assertion_id(item: dict, role: str) -> str:
    material = "|".join(
        [
            item["occurrence_id"],
            item["series_id"],
            item["source_id"],
            role,
            item["timing"]["start_local"],
        ]
    )
    return "WSA-AC-" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def expected_change_id(item: dict) -> str:
    material = "|".join(
        [
            item["occurrence_id"],
            item["series_id"],
            item["source_id"],
            item["timing"]["start_local"],
            "HISTORICAL_OCCURRENCE_ADMISSION",
        ]
    )
    return "WSCHANGE-" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:18]


def utc_from_local(start_local: str, source_timezone: str) -> str:
    local_dt = datetime.fromisoformat(start_local).replace(tzinfo=ZoneInfo(source_timezone))
    return local_dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


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
    item = plan["anchor"]
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
        (str(analysis_schema.get("version")) == p["analysis_schema_version"], "Analysis schema version drift"),
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
    change_ids = {row.get("change_id") for row in ledger.get("changes", [])}

    for occurrence_id in p["required_absent_occurrence_ids"]:
        if occurrence_id in by_occ:
            errors.append(f"occurrence identity collision: {occurrence_id}")
    for change_id in p["required_absent_change_ids"]:
        if change_id in change_ids:
            errors.append(f"change identity collision: {change_id}")

    template_expected = p["required_template"]
    template = by_occ.get(template_expected["occurrence_id"])
    if not template:
        errors.append("required RBA FSR template occurrence missing")
    else:
        for key, expected in template_expected.items():
            if key == "occurrence_id":
                continue
            if template.get(key) != expected:
                errors.append(f"template field drift: {key} expected {expected!r} got {template.get(key)!r}")

    source = by_source.get(item["source_id"])
    if not source:
        errors.append(f"required source missing: {item['source_id']}")
    else:
        if source.get("institution") != "Reserve Bank of Australia":
            errors.append("RBA FSR source institution drift")
        if source.get("authoritative_url") != item["series_url"]:
            errors.append("RBA FSR source endpoint drift")
        if source.get("source_timezone") != "Australia/Sydney":
            errors.append("RBA FSR source timezone drift")

    if item["primary_source_assertion_id"] != expected_assertion_id(item, "PRIMARY"):
        errors.append("primary assertion identity drift")
    if item["completion_source_assertion_id"] != expected_assertion_id(item, "COMPLETION"):
        errors.append("completion assertion identity drift")
    if item["change_id"] != expected_change_id(item):
        errors.append("change identity drift")
    if utc_from_local(item["timing"]["start_local"], item["timing"]["source_timezone"]) != item["timing"]["start_utc"]:
        errors.append("authoritative local-time to UTC conversion drift")

    overlay_errors = validate_biosecurity_overlay(registry, overlay)
    errors.extend(f"biosecurity overlay pre-state: {error}" for error in overlay_errors)
    analysis_report = validate_analysis(analysis_schema, analysis_evidence, analysis_reviews, registry)
    errors.extend(f"Analysis pre-state: {error}" for error in analysis_report.errors)

    if errors:
        raise SystemExit("PRECONDITION FAILED:\n- " + "\n- ".join(errors))


def build_anchor(template: dict, item: dict, reference_date: str) -> dict:
    out = copy.deepcopy(template)
    for key in (
        "population_horizon_policy",
        "coverage_program_id",
        "coverage_repair_reason",
        "selection_rationale",
        "future_schedule_deferred",
    ):
        out.pop(key, None)

    timing = item["timing"]
    out.update(
        occurrence_id=item["occurrence_id"],
        series_id=item["series_id"],
        canonical_name=item["canonical_name"],
        short_calendar_title=item["short_calendar_title"],
        certainty_status=item["certainty_status"],
        lifecycle_status=item["lifecycle_status"],
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
        publication_datetime=None,
        time_status=timing["time_status"],
        time_basis=timing["time_basis"],
        source_id=item["source_id"],
        primary_source_assertion_id=item["primary_source_assertion_id"],
        last_successful_assertion_id=item["completion_source_assertion_id"],
        first_announced_at=None,
        first_discovered_at=reference_date,
        last_verified_at=reference_date,
        next_verification_due="SOURCE_SPECIFIC",
        population_tranche="RBA_FINANCIAL_STABILITY_HISTORICAL_ANCHOR_AC",
        related_documents=[
            {
                "source_id": item["source_id"],
                "role": item["related_document_role"],
                "source_locator": item["publication_url"],
            }
        ],
        derivation_sources=[item["source_id"]],
        status_history=[
            {
                "as_of": reference_date,
                "certainty_status": item["certainty_status"],
                "lifecycle_status": item["lifecycle_status"],
                "condition_state": out.get("condition_state", "NOT_REQUIRED"),
                "change_reason": "Historical occurrence admitted after authoritative post-event verification; completion is not inferred from elapsed time.",
                "source_assertion_id": item["completion_source_assertion_id"],
                "basis": item["completion_basis"],
            }
        ],
        notes=(
            item["completion_basis"]
            + " The occurrence reuses the existing RBA FSR series and source; no new series or source identity is created."
        ),
    )
    return out


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
            "start_utc": timing["start_utc"],
            "time_precision": timing["time_precision"],
        },
        "source_assertion_id": item["completion_source_assertion_id"],
        "review_state": "APPROVED_FOR_CANONICAL_COMMIT",
        "reviewed_at": committed_at,
        "review_basis": [
            item["series_url"],
            item["publication_url"],
            item["completion_media_release_url"],
            item["authoritative_time_url"],
            item["completion_basis"],
            "Existing canonical series and source identities are reused; no new taxonomy or source endpoint identity is created.",
            "Completion is admitted only from first-party post-event evidence, never elapsed time alone.",
        ],
        "commit_mode": "REVIEWED_RBA_FINANCIAL_STABILITY_HISTORICAL_ANCHOR_AC",
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
) -> tuple[dict, dict, dict]:
    preflight(registry, schema, sources, ledger, overlay, analysis_schema, analysis_reviews, analysis_evidence, plan)
    item = plan["anchor"]
    expected = plan["postconditions"]
    reference_date = plan["reference_date"]

    old_records = copy.deepcopy(registry["records"])
    old_changes = copy.deepcopy(ledger["changes"])
    old_overlay_semantics = overlay_semantics(overlay)
    old_sources = copy.deepcopy(sources)
    by_occ = {row["occurrence_id"]: row for row in registry["records"]}

    post_registry = copy.deepcopy(registry)
    post_registry["version"] = expected["canonical_registry_version"]
    post_registry["reference_date"] = reference_date
    post_registry["records"].append(build_anchor(by_occ[item["template_occurrence_id"]], item, reference_date))
    post_registry["record_count"] = len(post_registry["records"])

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
    if post_registry["records"][: len(old_records)] != old_records:
        errors.append("pre-existing canonical records changed")
    if post_ledger["changes"][: len(old_changes)] != old_changes:
        errors.append("pre-existing ledger records changed")
    if sources != old_sources:
        errors.append("source registry changed during build")
    if overlay_semantics(post_overlay) != old_overlay_semantics:
        errors.append("biosecurity overlay semantic content changed")

    if post_registry.get("record_count") != expected["canonical_record_count"]:
        errors.append("canonical post-count mismatch")
    if len(post_ledger.get("changes", [])) != expected["change_ledger_count"]:
        errors.append("ledger post-count mismatch")

    new_row = post_registry["records"][-1]
    for key in (
        "occurrence_id",
        "series_id",
        "source_id",
        "canonical_name",
        "short_calendar_title",
        "lifecycle_status",
        "certainty_status",
        "primary_source_assertion_id",
        "last_successful_assertion_id",
    ):
        expected_value = {
            "last_successful_assertion_id": item["completion_source_assertion_id"],
        }.get(key, item.get(key))
        if new_row.get(key) != expected_value:
            errors.append(f"new anchor field mismatch: {key}")

    registry_report = validate_registry(post_registry, sources)
    errors.extend(f"registry validation: {error}" for error in registry_report.errors)
    overlay_errors = validate_biosecurity_overlay(post_registry, post_overlay)
    errors.extend(f"biosecurity overlay: {error}" for error in overlay_errors)
    analysis_report = validate_analysis(analysis_schema, analysis_evidence, analysis_reviews, post_registry)
    errors.extend(f"Analysis validation: {error}" for error in analysis_report.errors)

    readiness = analysis_population_readiness(analysis_schema, analysis_reviews, post_registry)
    if readiness["eligible_completed_occurrence_count"] != expected["eligible_completed_occurrence_count"]:
        errors.append("eligible completed occurrence count mismatch")
    if readiness["reviewed_occurrence_count"] != expected["reviewed_occurrence_count"]:
        errors.append("reviewed occurrence count mismatch")

    completed = [row for row in post_registry["records"] if row.get("lifecycle_status") == "COMPLETED"]
    completed_categories = {row.get("category") for row in completed}
    completed_event_types = {row.get("event_type") for row in completed}
    if "FINANCIAL_STABILITY_REGULATION" not in completed_categories:
        errors.append("financial-stability category gap not repaired")
    if "FINANCIAL_STABILITY_REPORT" not in completed_event_types:
        errors.append("financial-stability-report event-type gap not repaired")

    if errors:
        raise SystemExit("POSTCONDITION FAILED:\n- " + "\n- ".join(errors))

    return post_registry, post_ledger, post_overlay


def write_audit(
    plan: dict,
    post_registry: dict,
    post_ledger: dict,
    post_overlay: dict,
    sources: dict,
    analysis_schema: dict,
    analysis_reviews: dict,
    analysis_evidence: dict,
    protected_hashes_before: dict[str, str],
    overlay_semantics_before_hash: str,
) -> None:
    item = plan["anchor"]
    readiness = analysis_population_readiness(analysis_schema, analysis_reviews, post_registry)
    protected_hashes_after = {
        "canonical_schema": file_hash(CANONICAL_SCHEMA_PATH),
        "source_registry": file_hash(SOURCE_PATH),
        "monitor_expectations": file_hash(EXPECTATIONS_PATH),
        "monitor_operations_policy": file_hash(OPERATIONS_PATH),
        "analysis_schema": file_hash(ANALYSIS_SCHEMA_PATH),
        "analysis_reviews": file_hash(ANALYSIS_REVIEWS_PATH),
        "analysis_evidence": file_hash(ANALYSIS_EVIDENCE_PATH),
    }
    if protected_hashes_after != protected_hashes_before:
        raise SystemExit("AUDIT FAILED: protected-file hashes changed")
    if semantic_hash(overlay_semantics(post_overlay)) != overlay_semantics_before_hash:
        raise SystemExit("AUDIT FAILED: overlay semantic hash changed")

    lines = [
        "# WORLD SIGNALS — RBA financial-stability historical anchor AC transaction audit v0.1",
        "",
        "**Transaction date:** 2026-09-06  ",
        f"**Canonical post-state:** v{post_registry['version']} / {post_registry['record_count']}  ",
        f"**Source registry:** v{sources['version']} / {len(sources.get('sources', []))} — unchanged  ",
        f"**Change ledger post-state:** v{post_ledger['version']} / {len(post_ledger.get('changes', []))}  ",
        f"**Analysis:** schema v{analysis_schema['version']}; reviews v{analysis_reviews['version']} / {len(analysis_reviews.get('reviews', []))}; evidence v{analysis_evidence['version']} / {len(analysis_evidence.get('evidence', []))} — unchanged",
        "",
        "## Added historical anchor",
        "",
        f"- `{item['occurrence_id']}` — {item['canonical_name']}",
        f"- series `{item['series_id']}` — reused",
        f"- source `{item['source_id']}` — reused; source registry byte-identical",
        "- category `FINANCIAL_STABILITY_REGULATION`",
        "- event type `FINANCIAL_STABILITY_REPORT`",
        f"- source-native time `{item['timing']['start_local']}` `{item['timing']['source_timezone']}` ({item['timing']['source_timezone_label']})",
        f"- canonical UTC `{item['timing']['start_utc']}`",
        "- lifecycle `COMPLETED`, certainty `CONFIRMED`",
        "- completion established by first-party RBA publication/release evidence, not elapsed time",
        "",
        "## Population effect",
        "",
        f"- completed Analysis-eligible occurrences: {readiness['eligible_completed_occurrence_count']}",
        f"- reviewed completed occurrences: {readiness['reviewed_occurrence_count']}",
        "- `FINANCIAL_STABILITY_REGULATION` is now present in completed anchors",
        "- `FINANCIAL_STABILITY_REPORT` is now present in completed event types",
        "- no Analysis review is added by AC",
        "",
        "## Mutation boundary",
        "",
        "Allowed production mutations:",
        "1. `data/canonical/registry.json` — append one occurrence and bump checkpoint version/count",
        "2. `data/changes/ledger.json` — append one reviewed historical-admission change",
        "3. `data/coverage/biosecurity_overlay.json` — checkpoint/version metadata only; semantic payload unchanged",
        "4. this generated transaction audit",
        "",
        "Protected files remain byte-identical:",
    ]
    for key, value in protected_hashes_after.items():
        lines.append(f"- {key}: `{value}`")
    lines += [
        "",
        f"Biosecurity overlay semantic SHA-256: `{overlay_semantics_before_hash}`",
        "",
        "## Discipline",
        "",
        "- no new series",
        "- no new source",
        "- no source-registry rewrite for a legacy dependency counter",
        "- no Analysis mutation",
        "- no Calendar mutation",
        "- no inference of completion from elapsed time",
        "",
    ]
    AUDIT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    registry = load(CANONICAL_PATH)
    schema = load(CANONICAL_SCHEMA_PATH)
    sources = load(SOURCE_PATH)
    ledger = load(LEDGER_PATH)
    overlay = load(OVERLAY_PATH)
    analysis_schema = load(ANALYSIS_SCHEMA_PATH)
    analysis_reviews = load(ANALYSIS_REVIEWS_PATH)
    analysis_evidence = load(ANALYSIS_EVIDENCE_PATH)
    plan = load(PLAN_PATH)

    protected_hashes_before = {
        "canonical_schema": file_hash(CANONICAL_SCHEMA_PATH),
        "source_registry": file_hash(SOURCE_PATH),
        "monitor_expectations": file_hash(EXPECTATIONS_PATH),
        "monitor_operations_policy": file_hash(OPERATIONS_PATH),
        "analysis_schema": file_hash(ANALYSIS_SCHEMA_PATH),
        "analysis_reviews": file_hash(ANALYSIS_REVIEWS_PATH),
        "analysis_evidence": file_hash(ANALYSIS_EVIDENCE_PATH),
    }
    overlay_semantics_before_hash = semantic_hash(overlay_semantics(overlay))
    committed_at = transaction_time()
    post_registry, post_ledger, post_overlay = build_post_state(
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

    if not args.apply:
        print("CHECK_ONLY_OK")
        print(json.dumps({
            "occurrence_id": plan["anchor"]["occurrence_id"],
            "canonical_post": [post_registry["version"], post_registry["record_count"]],
            "ledger_post": [post_ledger["version"], len(post_ledger["changes"])],
            "overlay_post": [post_overlay["version"], post_overlay["canonical_checkpoint"]],
            "source_registry_unchanged": True,
            "analysis_unchanged": True,
        }, indent=2))
        return

    if os.environ.get(APPLY_ENV) != "REVIEWED_APPLY":
        raise SystemExit(f"APPLY REFUSED: set {APPLY_ENV}=REVIEWED_APPLY after reviewed simulation")

    dump(CANONICAL_PATH, post_registry)
    dump(LEDGER_PATH, post_ledger)
    dump(OVERLAY_PATH, post_overlay)
    write_audit(
        plan,
        post_registry,
        post_ledger,
        post_overlay,
        sources,
        analysis_schema,
        analysis_reviews,
        analysis_evidence,
        protected_hashes_before,
        overlay_semantics_before_hash,
    )
    print("APPLY_OK")


if __name__ == "__main__":
    main()
