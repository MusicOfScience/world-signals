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

ALLOWED_TARGET_FIELDS = {
    "lifecycle_status",
    "last_successful_assertion_id",
    "status_history",
    "last_verified_at",
    "related_documents",
    "notes",
}


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


def changed_fields(before: dict, after: dict) -> set[str]:
    return {
        key
        for key in set(before) | set(after)
        if before.get(key) != after.get(key)
    }


def counts_analysis_live_inputs(reviews: dict) -> tuple[int, int]:
    live_inputs = 0
    revisions = 0
    for review in reviews.get("reviews", []):
        live_inputs += len(review.get("live_inputs") or [])
        if review.get("revision_of_analysis_id"):
            revisions += 1
    return live_inputs, revisions


def exact_target_fields(row: dict) -> dict:
    keys = (
        "occurrence_id",
        "series_id",
        "canonical_name",
        "category",
        "subcategory",
        "jurisdiction",
        "region",
        "institution",
        "institution_key",
        "event_type",
        "certainty_status",
        "lifecycle_status",
        "timing_type",
        "start_local",
        "end_local",
        "source_timezone",
        "start_utc",
        "end_utc",
        "time_precision",
        "all_day_semantics",
        "time_status",
        "time_basis",
        "source_id",
        "primary_source_assertion_id",
        "last_successful_assertion_id",
        "last_verified_at",
        "intrinsic_importance",
        "expected_market_sensitivity",
        "geopolitical_sensitivity",
        "host_binding_id",
        "schedule_authority_scope",
        "host_confirmed",
        "host_jurisdiction",
        "host_city",
        "notes",
    )
    return {key: row.get(key) for key in keys}


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
    change_ids = {row.get("change_id") for row in ledger.get("changes", [])}

    target_expected = p["required_existing_occurrence"]
    target = by_occ.get(target_expected["occurrence_id"])
    if target is None:
        errors.append("required existing PIF occurrence missing")
    else:
        actual = exact_target_fields(target)
        expected = {key: target_expected.get(key) for key in actual}
        if actual != expected:
            for key in actual:
                if actual[key] != expected[key]:
                    errors.append(
                        f"PIF target field drift: {key} expected {expected[key]!r} got {actual[key]!r}"
                    )
        if target.get("related_documents") != []:
            errors.append("PIF target related_documents no longer at exact CK prestate")
        if target.get("status_history") != [
            {
                "as_of": "2026-09-02",
                "certainty_status": "CONFIRMED",
                "lifecycle_status": "ACTIVE",
            }
        ]:
            errors.append("PIF target status_history no longer at exact CK prestate")

    source_expected = p["required_existing_primary_source"]
    primary_source = by_source.get(source_expected["source_id"])
    if primary_source is None:
        errors.append("required PIF host source missing")
    else:
        for key, expected in source_expected.items():
            if key == "source_id":
                continue
            if primary_source.get(key) != expected:
                errors.append(f"PIF source field drift: {key}")
        actual_dependency_count = sum(
            1 for row in records if row.get("source_id") == source_expected["source_id"]
        )
        if actual_dependency_count != 1 or actual_dependency_count != primary_source.get("canonical_dependency_count"):
            errors.append("PIF source dependency count does not match Canonical truth")

    support = plan["supporting_source"]
    if support["source_id"] in by_source:
        errors.append(f"supporting source identity collision: {support['source_id']}")
    if plan["change"]["change_id"] in change_ids:
        errors.append(f"change identity collision: {plan['change']['change_id']}")
    if support.get("canonical_dependency_count") != 0:
        errors.append("supporting source must have zero primary Canonical dependencies")
    if support.get("automated_monitoring_use") != "PROHIBITED_OR_RIGHTS_HOLD":
        errors.append("supporting source automation gate unexpectedly open")
    if support.get("verification_mode") != "RIGHTS_HELD_MANUAL_ONLY":
        errors.append("supporting source verification posture drift")

    future = plan["future_host_context"]
    if future.get("exact_dates_found") is not False or future.get("canonical_dated_occurrence_authorised") is not False:
        errors.append("2027 host-context/date boundary drift")

    if any(
        adapter.get("source_id") in {target_expected["source_id"], support["source_id"]}
        or target_expected["occurrence_id"] in (adapter.get("canonical_occurrence_ids") or [])
        for adapter in expectations.get("adapters", [])
    ):
        errors.append("PIF unexpectedly appears in Monitor expectations before CK")

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
        notes="Supporting-only Cook Islands first-party completion evidence for WSO-INT-A-0001; zero primary Canonical dependencies.",
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


def update_target_occurrence(before: dict, plan: dict) -> dict:
    after = copy.deepcopy(before)
    change = plan["change"]
    support = plan["supporting_source"]
    after["lifecycle_status"] = "COMPLETED"
    after["last_successful_assertion_id"] = change["completion_source_assertion_id"]
    after["last_verified_at"] = plan["reference_date"]
    after["status_history"] = copy.deepcopy(before["status_history"]) + [
        {
            "as_of": plan["reference_date"],
            "certainty_status": "CONFIRMED",
            "lifecycle_status": "COMPLETED",
            "condition_state": "NOT_REQUIRED",
            "change_reason": "Post-event completion verified from first-party Cook Islands PMO evidence; not inferred from elapsed time.",
            "source_assertion_id": change["completion_source_assertion_id"],
            "basis": change["completion_basis"],
        }
    ]
    after["related_documents"] = copy.deepcopy(before.get("related_documents") or []) + [
        {
            "source_id": support["source_id"],
            "role": "COMPLETION_AND_OUTCOME_CORROBORATION",
            "source_locator": support["authoritative_url"],
        }
    ]
    after["notes"] = (
        "The Palau host source continues to govern the 30 August–4 September 2026 civil-date range. "
        "Cook Islands PMO first-party post-event evidence verifies completion and Forum outcomes; "
        "completion is not inferred from elapsed time."
    )
    return after


def build_ledger_change(plan: dict, committed_at: str) -> dict:
    change = plan["change"]
    target = plan["preconditions"]["required_existing_occurrence"]
    return {
        "change_id": change["change_id"],
        "occurrence_id": target["occurrence_id"],
        "change_type": "LIFECYCLE_COMPLETION",
        "old_values": {
            "lifecycle_status": "ACTIVE",
            "last_successful_assertion_id": target["last_successful_assertion_id"],
        },
        "new_values": {
            "lifecycle_status": "COMPLETED",
            "last_successful_assertion_id": change["completion_source_assertion_id"],
        },
        "source_assertion_id": change["completion_source_assertion_id"],
        "review_state": "APPROVED_FOR_CANONICAL_COMMIT",
        "reviewed_at": committed_at,
        "review_basis": [
            change["completion_url"],
            change["completion_basis"],
            "Stable occurrence WSO-INT-A-0001 and series WSER-INT-PIF-LEADERS are preserved; CK corrects lifecycle/provenance only.",
            "Existing Palau timing fields remain unchanged, including Pacific/Palau civil-date semantics and null UTC endpoints.",
            "Completion is admitted from first-party post-event evidence and is not inferred from elapsed time.",
            "Auckland/New Zealand 2027 host confirmation supplies no authoritative meeting dates and creates no dated successor occurrence.",
        ],
        "commit_mode": "REVIEWED_PIF_LIFECYCLE_COMPLETION_CK",
        "committed_at": committed_at,
        "registry_version_before": plan["preconditions"]["canonical_registry_version"],
        "registry_version_after": plan["expected_post_state"]["canonical_registry_version"],
        "canonical_mutation_committed": True,
    }


def build_post_state(
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
    committed_at: str,
) -> tuple[dict, dict, dict, dict]:
    expected = plan["expected_post_state"]
    target_id = plan["preconditions"]["required_existing_occurrence"]["occurrence_id"]
    support = plan["supporting_source"]

    old_records = copy.deepcopy(registry["records"])
    old_sources = copy.deepcopy(sources["sources"])
    old_changes = copy.deepcopy(ledger["changes"])
    old_overlay_semantics = overlay_semantics(overlay)

    target_index = next(i for i, row in enumerate(registry["records"]) if row["occurrence_id"] == target_id)
    target_before = copy.deepcopy(registry["records"][target_index])
    target_after = update_target_occurrence(target_before, plan)

    post_registry = copy.deepcopy(registry)
    post_registry["version"] = expected["canonical_registry_version"]
    post_registry["reference_date"] = plan["reference_date"]
    post_registry["records"][target_index] = target_after
    post_registry["record_count"] = len(post_registry["records"])

    post_sources = copy.deepcopy(sources)
    post_sources["version"] = expected["source_registry_version"]
    post_sources["reference_date"] = plan["reference_date"]
    primary_source = next(row for row in sources["sources"] if row["source_id"] == target_before["source_id"])
    post_sources["sources"].append(
        build_supporting_source(primary_source, support, plan["reference_date"])
    )

    post_ledger = copy.deepcopy(ledger)
    post_ledger["version"] = expected["change_ledger_version"]
    post_ledger["reference_date"] = plan["reference_date"]
    post_ledger["changes"].append(build_ledger_change(plan, committed_at))

    post_overlay = copy.deepcopy(overlay)
    post_overlay["version"] = expected["biosecurity_overlay_version"]
    post_overlay["canonical_checkpoint"] = copy.deepcopy(expected["biosecurity_overlay_checkpoint"])

    errors: list[str] = []
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

    for i, before in enumerate(old_records):
        after = post_registry["records"][i]
        if before["occurrence_id"] == target_id:
            actual_changed = changed_fields(before, after)
            if actual_changed != ALLOWED_TARGET_FIELDS:
                errors.append(
                    f"PIF target changed fields {sorted(actual_changed)} != allowed {sorted(ALLOWED_TARGET_FIELDS)}"
                )
        elif after != before:
            errors.append(f"unrelated Canonical occurrence changed: {before['occurrence_id']}")

    if target_after["series_id"] != "WSER-INT-PIF-LEADERS":
        errors.append("PIF stable series identity changed")
    if target_after["lifecycle_status"] != "COMPLETED" or target_after["certainty_status"] != "CONFIRMED":
        errors.append("PIF lifecycle/certainty post-state drift")
    for key, expected_value in {
        "timing_type": "MULTI_DAY_LOCAL",
        "start_local": "2026-08-30",
        "end_local": "2026-09-04",
        "source_timezone": "Pacific/Palau",
        "start_utc": None,
        "end_utc": None,
        "time_precision": "DAY",
        "all_day_semantics": True,
        "time_status": "CONFIRMED",
        "time_basis": "EXPLICIT_AUTHORITATIVE_SCHEDULE",
        "intrinsic_importance": "HIGH",
        "expected_market_sensitivity": "MEDIUM_HIGH",
        "geopolitical_sensitivity": "HIGH",
        "host_binding_id": "WSHB-PIF-2026-PW",
        "host_jurisdiction": "Palau",
        "host_city": "Koror",
    }.items():
        if target_after.get(key) != expected_value:
            errors.append(f"PIF protected target field drift: {key}")

    if old_sources != post_sources["sources"][:-1]:
        errors.append("pre-existing Source Registry rows changed")
    support_after = post_sources["sources"][-1]
    if support_after.get("source_id") != support["source_id"]:
        errors.append("unexpected supporting source appended")
    if support_after.get("canonical_dependency_count") != 0:
        errors.append("supporting Cook Islands source gained a primary dependency")
    if support_after.get("automated_monitoring_use") != "PROHIBITED_OR_RIGHTS_HOLD":
        errors.append("supporting Cook Islands source automation gate opened")
    if support_after.get("live_adapter_id"):
        errors.append("supporting Cook Islands source unexpectedly has an adapter")

    if any(
        row.get("series_id") == "WSER-INT-PIF-LM"
        or row.get("occurrence_id") == "WSO-INT-PIF-LM-055-2026"
        for row in post_registry["records"]
    ):
        errors.append("obsolete duplicate PIF identity was materialised")
    if any(
        row.get("series_id") == "WSER-INT-PIF-LEADERS" and "2027" in row.get("occurrence_id", "")
        for row in post_registry["records"]
    ):
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


def audit_markdown(plan: dict, committed_at: str, protected_ok: bool) -> str:
    expected = plan["expected_post_state"]
    change = plan["change"]
    failed = plan["failed_attempts"]
    return f"""# WORLD SIGNALS — PIF Leaders Meeting CK transaction audit v0.2

**Status:** MATERIALISED / GUARDED  
**Reference date:** {plan['reference_date']}  
**Base main:** `{plan['base_main_sha']}`  
**Committed at:** `{committed_at}`

## Correction to the initial CK premise

CJ's text-based discovery recorded the 55th Pacific Islands Forum Leaders Meeting as absent from Canonical. CK's guarded transaction disproved that assumption before any write. The existing stable identity is `WSO-INT-A-0001` / `WSER-INT-PIF-LEADERS`, sourced by `WSSRC-INT-012` and host-bound by `WSHB-PIF-2026-PW`.

CK therefore performs **lifecycle/provenance completion repair only**. It creates no replacement occurrence or series.

## Failed guarded attempts preserved

1. run `{failed[0]['run_id']}` / job `{failed[0]['job_id']}` — exact base passed; obsolete admission simulation failed on the incorrect zero-dependency assumption; no write occurred.
2. run `{failed[1]['run_id']}` / job `{failed[1]['job_id']}` — exact base and read-only identity probe passed; probe found the existing PIF occurrence/source; obsolete admission simulation failed; no write occurred.

## Reviewed mutation

- target: `WSO-INT-A-0001` / `WSER-INT-PIF-LEADERS`;
- lifecycle: **ACTIVE → COMPLETED**;
- certainty remains `CONFIRMED`;
- all timing fields remain unchanged: `MULTI_DAY_LOCAL`, 30 August–4 September 2026, `Pacific/Palau`, DAY precision, null UTC endpoints;
- intrinsic importance remains `HIGH`; expected market sensitivity remains `MEDIUM_HIGH`; geopolitical sensitivity remains `HIGH`;
- host binding `WSHB-PIF-2026-PW` remains unchanged;
- existing source `WSSRC-INT-012` remains byte-identical;
- new supporting-only completion source `WSSRC-INT-036` has zero primary Canonical dependencies and production automation held;
- no dated 2027 occurrence is created.

## Governed state transition

- Canonical: v0.41 / 689 → **v{expected['canonical_registry_version']} / {expected['canonical_record_count']}**;
- Sources: v2.03 / 257 → **v{expected['source_registry_version']} / {expected['source_record_count']}**;
- Change Ledger: v0.27 / 62 → **v{expected['change_ledger_version']} / {expected['change_ledger_count']}**;
- Biosecurity overlay: v0.16 → **v{expected['biosecurity_overlay_version']}**, semantic content unchanged, Canonical checkpoint v0.42 / 689;
- Monitor expectations unchanged v0.28 / 26 adapters;
- Live Intelligence unchanged 7 observations / 10 evidence rows;
- Analysis unchanged 22 reviews / 97 evidence rows / 1 production Live input / 1 production revision.

## Completion provenance

Completion assertion: `{change['completion_source_assertion_id']}`. Cook Islands PMO first-party post-event evidence states that participation in the 55th PIF Leaders Meeting had concluded and that Leaders' Retreat outcomes were captured in the 2026 Forum Communiqué. Completion is not inferred from elapsed time.

## Identity-discovery control

Future material-family absence claims should not rely on literal name search alone. Stable occurrence/series identities, source dependencies, institution keys and host bindings must also be interrogated where available before creating a new Canonical identity.

## Authority boundary

- automatic Canonical commit: **OFF**;
- Google Calendar write: **OFF**;
- PIF Monitor route: **NOT CREATED**;
- PIF Live observation: **NOT CREATED**;
- Live→Analysis: **OFF**;
- public Live/Analysis projection: **OFF**;
- OPEC CE quarantine: **UNTOUCHED**.

Protected Monitor, Live, Analysis and OPEC files byte-identical across the transaction: **{str(protected_ok).lower()}**.
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
        "target_occurrence_id": "WSO-INT-A-0001",
        "stable_series_id": "WSER-INT-PIF-LEADERS",
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
        audit_markdown(plan, committed_at, protected_ok=True),
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
