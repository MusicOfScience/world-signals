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
PLAN_PATH = ROOT / "data/coverage/WHO_WHA79_HISTORICAL_ANCHOR_AD_PLAN_v0.1.json"
AUDIT_PATH = ROOT / "data/coverage/WHO_WHA79_HISTORICAL_ANCHOR_AD_TRANSACTION_AUDIT_v0.1.md"
APPLY_ENV = "WORLD_SIGNALS_APPLY_WHA79_ANCHOR_AD"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def semantic_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def overlay_semantics(overlay: dict) -> dict:
    return {
        key: copy.deepcopy(value)
        for key, value in overlay.items()
        if key not in {"version", "canonical_checkpoint"}
    }


def transaction_time() -> str:
    return datetime.now(ZoneInfo("Australia/Melbourne")).isoformat(timespec="seconds")


def expected_assertion_id(item: dict, role: str) -> str:
    source_id = item["source_id"] if role == "PRIMARY" else item["completion_source_id"]
    material = "|".join(
        [item["occurrence_id"], item["series_id"], source_id, role, item["timing"]["start_local"]]
    )
    return "WSA-AD-" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


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


def actual_primary_dependency_count(registry: dict, source_id: str) -> int:
    return sum(1 for row in registry.get("records", []) if row.get("source_id") == source_id)


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
    for source_id in p["required_absent_source_ids"]:
        if source_id in by_source:
            errors.append(f"source identity collision: {source_id}")
    for change_id in p["required_absent_change_ids"]:
        if change_id in change_ids:
            errors.append(f"change identity collision: {change_id}")

    template_expected = p["required_template"]
    template = by_occ.get(template_expected["occurrence_id"])
    if not template:
        errors.append("required WHA80 template occurrence missing")
    else:
        for key, expected in template_expected.items():
            if key == "occurrence_id":
                continue
            if template.get(key) != expected:
                errors.append(f"template field drift: {key} expected {expected!r} got {template.get(key)!r}")

    source_expected = p["required_primary_source"]
    source = by_source.get(source_expected["source_id"])
    if not source:
        errors.append("required WHO governance source missing")
    else:
        for key in ("institution", "authoritative_url", "canonical_dependency_count"):
            if source.get(key) != source_expected[key]:
                errors.append(f"WHO source field drift: {key}")
        actual = actual_primary_dependency_count(registry, source_expected["source_id"])
        if actual != source_expected["actual_primary_dependency_count"]:
            errors.append(f"WHO actual primary dependency count drift: {actual}")
        if actual != source.get("canonical_dependency_count"):
            errors.append("WHO dependency helper does not match canonical truth")
        expected_rights = {
            "canonical_provenance_use": "MANUAL_INFORMATIONAL_REFERENCE_ONLY",
            "automated_monitoring_use": "PROHIBITED_OR_RIGHTS_HOLD",
            "verification_mode": "RIGHTS_HELD_MANUAL_ONLY",
        }
        for key, expected in expected_rights.items():
            if source.get(key) != expected:
                errors.append(f"WHO reviewed source-governance posture drift: {key}")

    if item["primary_source_assertion_id"] != expected_assertion_id(item, "PRIMARY"):
        errors.append("primary assertion identity drift")
    if item["completion_source_assertion_id"] != expected_assertion_id(item, "COMPLETION"):
        errors.append("completion assertion identity drift")
    if item["change_id"] != expected_change_id(item):
        errors.append("change identity drift")
    if item["timing"].get("start_utc") is not None or item["timing"].get("end_utc") is not None:
        errors.append("WHA79 multi-day anchor must not synthesize UTC endpoints")
    if "T" in item["timing"]["start_local"] or "T" in item["timing"]["end_local"]:
        errors.append("WHA79 anchor must preserve day-range semantics, not opening-session clock time")

    overlay_errors = validate_biosecurity_overlay(registry, overlay)
    errors.extend(f"biosecurity overlay pre-state: {error}" for error in overlay_errors)
    analysis_report = validate_analysis(analysis_schema, analysis_evidence, analysis_reviews, registry)
    errors.extend(f"Analysis pre-state: {error}" for error in analysis_report.errors)

    if errors:
        raise SystemExit("PRECONDITION FAILED:\n- " + "\n- ".join(errors))


def build_supporting_source(base: dict, item: dict, reference_date: str) -> dict:
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
        canonical_dependency_count=item["canonical_dependency_count"],
        notes=item["notes"],
        machine_readable_available="NOT_ASSESSED_SUPPORTING_HISTORICAL_ARCHIVE",
        monitor_endpoints=[],
        parser_type="MANUAL_HISTORICAL_ARCHIVE",
        parser_version="not-applicable",
        monitoring_priority_score=0,
        recommended_verification_cadence="manual historical recheck if WHO archive or closing material changes",
        monitoring_readiness_assessed_at=reference_date,
        runtime_health_state="MANUAL_RESEARCH_ROUTE_VERIFIED_PRODUCTION_RIGHTS_HOLD",
        health_source_route_state="AUTHORITATIVE_MANUAL_PROVENANCE_PRODUCTION_HOLD",
    )
    return out


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
        location=item["location"],
        source_id=item["source_id"],
        primary_source_assertion_id=item["primary_source_assertion_id"],
        last_successful_assertion_id=item["completion_source_assertion_id"],
        first_announced_at=None,
        first_discovered_at=reference_date,
        last_verified_at=reference_date,
        next_verification_due="SOURCE_SPECIFIC",
        population_tranche="WHO_WHA79_HISTORICAL_ANCHOR_AD",
        related_documents=[
            {
                "source_id": item["completion_source_id"],
                "role": item["related_document_role"],
                "source_locator": item["archive_url"],
            }
        ],
        derivation_sources=[item["source_id"], item["completion_source_id"]],
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
            + " WHA79 remains distinct from the continuing WHO Pandemic Agreement IGWG/PABS process; the Assembly's opening-session clock is not promoted to whole-event canonical time."
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
            item["schedule_url"],
            item["assembly_page_url"],
            item["archive_url"],
            item["closing_update_url"],
            item["closing_remarks_url"],
            item["completion_basis"],
            "Existing WHA series and primary schedule source are reused; supporting outcome provenance remains a distinct source role.",
            "Completion is admitted only from WHO first-party post-event evidence, never elapsed time alone.",
        ],
        "commit_mode": "REVIEWED_WHO_WHA79_HISTORICAL_ANCHOR_AD",
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
) -> tuple[dict, dict, dict, dict, dict]:
    preflight(registry, schema, sources, ledger, overlay, analysis_schema, analysis_reviews, analysis_evidence, plan)
    item = plan["anchor"]
    new_source_plan = plan["new_source"]
    expected = plan["postconditions"]
    reference_date = plan["reference_date"]

    old_records = copy.deepcopy(registry["records"])
    old_sources = copy.deepcopy(sources["sources"])
    old_changes = copy.deepcopy(ledger["changes"])
    old_overlay_semantics = overlay_semantics(overlay)
    by_occ = {row["occurrence_id"]: row for row in registry["records"]}
    by_source = {row["source_id"]: row for row in sources["sources"]}

    post_registry = copy.deepcopy(registry)
    post_registry["version"] = expected["canonical_registry_version"]
    post_registry["reference_date"] = reference_date
    post_registry["records"].append(build_anchor(by_occ[item["template_occurrence_id"]], item, reference_date))
    post_registry["record_count"] = len(post_registry["records"])

    post_sources = copy.deepcopy(sources)
    post_sources["version"] = expected["source_registry_version"]
    post_sources["reference_date"] = reference_date
    post_source_by_id = {row["source_id"]: row for row in post_sources["sources"]}
    post_source_by_id[item["source_id"]]["canonical_dependency_count"] = expected["primary_source_dependency_count"]
    post_sources["sources"].append(
        build_supporting_source(by_source[new_source_plan["clone_source_id"]], new_source_plan, reference_date)
    )

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
        errors.append("pre-existing ledger rows changed")
    if overlay_semantics(post_overlay) != old_overlay_semantics:
        errors.append("biosecurity overlay semantic content changed")

    post_source_map = {row["source_id"]: row for row in post_sources["sources"]}
    old_source_map = {row["source_id"]: row for row in old_sources}
    for source_id, old in old_source_map.items():
        new = post_source_map[source_id]
        if source_id == item["source_id"]:
            old_copy = copy.deepcopy(old)
            new_copy = copy.deepcopy(new)
            old_copy.pop("canonical_dependency_count", None)
            new_copy.pop("canonical_dependency_count", None)
            if old_copy != new_copy:
                errors.append("WHO primary source changed beyond canonical_dependency_count")
        elif new != old:
            errors.append(f"unexpected pre-existing source mutation: {source_id}")
    new_source_ids = set(post_source_map) - set(old_source_map)
    if new_source_ids != {new_source_plan["source_id"]}:
        errors.append(f"unexpected new source scope: {sorted(new_source_ids)}")

    if post_registry.get("record_count") != expected["canonical_record_count"]:
        errors.append("canonical post-count mismatch")
    if len(post_sources.get("sources", [])) != expected["source_record_count"]:
        errors.append("source post-count mismatch")
    if len(post_ledger.get("changes", [])) != expected["change_ledger_count"]:
        errors.append("ledger post-count mismatch")

    primary = post_source_map[item["source_id"]]
    support = post_source_map[new_source_plan["source_id"]]
    if primary.get("canonical_dependency_count") != expected["primary_source_dependency_count"]:
        errors.append("WHO primary dependency helper postcondition failed")
    if actual_primary_dependency_count(post_registry, item["source_id"]) != expected["primary_source_dependency_count"]:
        errors.append("WHO canonical primary dependency truth postcondition failed")
    if support.get("canonical_dependency_count") != expected["supporting_source_dependency_count"]:
        errors.append("WHO supporting source dependency helper postcondition failed")
    if actual_primary_dependency_count(post_registry, new_source_plan["source_id"]) != 0:
        errors.append("supporting completion source became a canonical primary source")
    for key in ("canonical_provenance_use", "automated_monitoring_use", "verification_mode"):
        if support.get(key) != by_source[new_source_plan["clone_source_id"]].get(key):
            errors.append(f"supporting source governance posture changed: {key}")
    if support.get("monitor_endpoints") != []:
        errors.append("supporting historical source retained a forward monitor endpoint")

    registry_report = validate_registry(post_registry, post_sources)
    errors.extend(f"canonical post-state: {error}" for error in registry_report.errors)
    overlay_errors = validate_biosecurity_overlay(post_registry, post_overlay)
    errors.extend(f"biosecurity overlay post-state: {error}" for error in overlay_errors)
    analysis_report = validate_analysis(analysis_schema, analysis_evidence, analysis_reviews, post_registry)
    errors.extend(f"Analysis post-state: {error}" for error in analysis_report.errors)

    readiness = analysis_population_readiness(analysis_schema, analysis_reviews, post_registry)
    if readiness["eligible_completed_occurrence_count"] != expected["eligible_completed_occurrence_count"]:
        errors.append("eligible completed Analysis population mismatch")
    if readiness["reviewed_occurrence_count"] != expected["reviewed_occurrence_count"]:
        errors.append("reviewed Analysis population changed unexpectedly")
    anchor = post_registry["records"][-1]
    if anchor.get("category") != "HEALTH_BIOSECURITY" or anchor.get("event_type") != "HEALTH_GOVERNANCE_EVENT":
        errors.append("WHA79 primary taxonomy drift")
    if anchor.get("start_utc") is not None or anchor.get("end_utc") is not None:
        errors.append("WHA79 synthetic UTC drift")

    if errors:
        raise SystemExit("POSTCONDITION FAILED:\n- " + "\n- ".join(errors))

    return post_registry, post_sources, post_ledger, post_overlay, readiness


def audit_text(
    post_registry: dict,
    post_sources: dict,
    post_ledger: dict,
    post_overlay: dict,
    readiness: dict,
    plan: dict,
) -> str:
    protected = {
        "canonical_schema": file_hash(CANONICAL_SCHEMA_PATH),
        "monitor_expectations": file_hash(EXPECTATIONS_PATH),
        "monitor_operations_policy": file_hash(OPERATIONS_PATH),
        "analysis_schema": file_hash(ANALYSIS_SCHEMA_PATH),
        "analysis_reviews": file_hash(ANALYSIS_REVIEWS_PATH),
        "analysis_evidence": file_hash(ANALYSIS_EVIDENCE_PATH),
    }
    item = plan["anchor"]
    support_id = plan["new_source"]["source_id"]
    by_source = {row["source_id"]: row for row in post_sources["sources"]}
    lines = [
        "# WORLD SIGNALS — WHO WHA79 historical anchor AD transaction audit v0.1",
        "",
        f"**Transaction date:** {plan['reference_date']}  ",
        f"**Canonical post-state:** v{post_registry['version']} / {len(post_registry['records'])}  ",
        f"**Source registry post-state:** v{post_sources['version']} / {len(post_sources['sources'])}  ",
        f"**Change ledger post-state:** v{post_ledger['version']} / {len(post_ledger['changes'])}  ",
        "**Analysis:** schema v0.3; reviews v0.8 / 12; evidence v0.8 / 44 — unchanged",
        "",
        "## Added historical anchor",
        "",
        f"- `{item['occurrence_id']}` — 79th World Health Assembly",
        f"- series `{item['series_id']}` — reused",
        f"- primary schedule source `{item['source_id']}` — reused",
        f"- supporting completion source `{support_id}` — new, supporting-only",
        "- category `HEALTH_BIOSECURITY`",
        "- event type `HEALTH_GOVERNANCE_EVENT`",
        "- local date range `2026-05-18` to `2026-05-23`, `Europe/Zurich`",
        "- UTC endpoints intentionally null; the 09:00 opening-session time is not the whole Assembly timestamp",
        "- lifecycle `COMPLETED`, certainty `CONFIRMED`",
        "- completion established from WHO first-party archive/closing evidence, not elapsed time",
        "",
        "## Source mutation scope",
        "",
        f"- `{item['source_id']}.canonical_dependency_count`: 6 → {by_source[item['source_id']]['canonical_dependency_count']}",
        f"- actual canonical primary dependencies for `{item['source_id']}`: {actual_primary_dependency_count(post_registry, item['source_id'])}",
        f"- `{support_id}` added with canonical dependency count {by_source[support_id]['canonical_dependency_count']}",
        f"- `{support_id}` primary canonical dependencies: {actual_primary_dependency_count(post_registry, support_id)}",
        "- supporting source inherits WHO manual-information / rights-held automation posture and has no forward monitor endpoint",
        "",
        "## Population effect",
        "",
        f"- completed Analysis-eligible occurrences: {readiness['eligible_completed_occurrence_count']}",
        f"- reviewed completed occurrences: {readiness['reviewed_occurrence_count']}",
        "- `HEALTH_BIOSECURITY` is now present in completed anchors",
        "- `HEALTH_GOVERNANCE_EVENT` is now present in completed event types",
        "- WHO-only institutional concentration is not claimed repaired",
        "- no Analysis review is added by AD",
        "",
        "## Protected SHA-256",
        "",
    ]
    for name, digest in protected.items():
        lines.append(f"- {name}: `{digest}`")
    lines.extend(
        [
            "",
            f"Biosecurity overlay semantic SHA-256: `{semantic_hash(overlay_semantics(post_overlay))}`",
            "",
            "## Discipline",
            "",
            "- no new series",
            "- primary schedule provenance and supporting outcome provenance remain distinct",
            "- no PABS/IGWG completion inference",
            "- no Analysis mutation",
            "- no monitor-configuration mutation",
            "- no Calendar mutation",
            "- no completion inference from elapsed time",
            "- no conversion of an opening-session clock into a synthetic whole-event timestamp",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply reviewed WHO WHA79 historical anchor AD transaction")
    parser.add_argument("--apply", action="store_true", help="write the reviewed post-state")
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
    committed_at = transaction_time()

    post_registry, post_sources, post_ledger, post_overlay, readiness = build_post_state(
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
            "canonical_post": [post_registry["version"], len(post_registry["records"])],
            "source_post": [post_sources["version"], len(post_sources["sources"])],
            "ledger_post": [post_ledger["version"], len(post_ledger["changes"])],
            "overlay_post": [post_overlay["version"], post_overlay["canonical_checkpoint"]],
            "eligible_completed": readiness["eligible_completed_occurrence_count"],
            "reviewed": readiness["reviewed_occurrence_count"],
        }, indent=2))
        return

    if os.environ.get(APPLY_ENV) != "REVIEWED_APPLY":
        raise SystemExit(f"WRITE GATE CLOSED: set {APPLY_ENV}=REVIEWED_APPLY for reviewed transaction")

    dump(CANONICAL_PATH, post_registry)
    dump(SOURCE_PATH, post_sources)
    dump(LEDGER_PATH, post_ledger)
    dump(OVERLAY_PATH, post_overlay)
    AUDIT_PATH.write_text(
        audit_text(post_registry, post_sources, post_ledger, post_overlay, readiness, plan),
        encoding="utf-8",
    )
    print("APPLY_OK")


if __name__ == "__main__":
    main()
