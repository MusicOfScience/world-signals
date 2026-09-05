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
PLAN_PATH = ROOT / "data/coverage/UNFCCC_SB64_HISTORICAL_ANCHOR_AH_PLAN_v0.1.json"
AUDIT_PATH = ROOT / "data/coverage/UNFCCC_SB64_HISTORICAL_ANCHOR_AH_TRANSACTION_AUDIT_v0.1.md"
APPLY_ENV = "WORLD_SIGNALS_APPLY_UNFCCC_SB64_ANCHOR_AH"


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
    return {k: copy.deepcopy(v) for k, v in overlay.items() if k not in {"version", "canonical_checkpoint"}}


def transaction_time() -> str:
    return datetime.now(ZoneInfo("Australia/Melbourne")).isoformat(timespec="seconds")


def expected_assertion_id(item: dict, role: str) -> str:
    material = "|".join(
        [item["occurrence_id"], item["series_id"], item["source_id"], role, item["timing"]["start_local"]]
    )
    return "WSA-AH-" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def expected_change_id(item: dict) -> str:
    material = "|".join(
        [item["occurrence_id"], item["series_id"], item["source_id"], item["timing"]["start_local"], "HISTORICAL_OCCURRENCE_ADMISSION"]
    )
    return "WSCHANGE-" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:18]


def actual_primary_dependency_count(registry: dict, source_id: str) -> int:
    return sum(1 for row in registry.get("records", []) if row.get("source_id") == source_id)


def preflight(registry: dict, schema: dict, sources: dict, ledger: dict, overlay: dict,
              analysis_schema: dict, reviews: dict, evidence: dict, plan: dict) -> None:
    p = plan["preconditions"]
    item = plan["anchor"]
    errors: list[str] = []
    checks = [
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
        (str(reviews.get("version")) == p["analysis_reviews_version"] and len(reviews.get("reviews", [])) == p["analysis_review_count"], "Analysis reviews drift"),
        (str(evidence.get("version")) == p["analysis_evidence_version"] and len(evidence.get("evidence", [])) == p["analysis_evidence_count"], "Analysis evidence drift"),
    ]
    errors.extend(message for ok, message in checks if not ok)

    by_occ = {row.get("occurrence_id"): row for row in registry.get("records", [])}
    by_source = {row.get("source_id"): row for row in sources.get("sources", [])}
    series_ids = {row.get("series_id") for row in registry.get("records", [])}
    change_ids = {row.get("change_id") for row in ledger.get("changes", [])}
    for oid in p["required_absent_occurrence_ids"]:
        if oid in by_occ:
            errors.append(f"occurrence identity collision: {oid}")
    for sid in p["required_absent_series_ids"]:
        if sid in series_ids:
            errors.append(f"series identity collision: {sid}")
    for sid in p["required_absent_source_ids"]:
        if sid in by_source:
            errors.append(f"source identity collision: {sid}")
    for cid in p["required_absent_change_ids"]:
        if cid in change_ids:
            errors.append(f"change identity collision: {cid}")

    template_expected = p["required_template"]
    template = by_occ.get(template_expected["occurrence_id"])
    if template is None:
        errors.append("required UNFCCC environmental-governance template missing")
    else:
        for key, expected in template_expected.items():
            if key != "occurrence_id" and template.get(key) != expected:
                errors.append(f"environmental template drift: {key} expected {expected!r} got {template.get(key)!r}")

    source_expected = p["required_source_family"]
    source = by_source.get(source_expected["source_id"])
    if source is None:
        errors.append("required UNFCCC source family missing")
    else:
        for key, expected in source_expected.items():
            if key != "source_id" and source.get(key) != expected:
                errors.append(f"UNFCCC source-governance drift: {key}")

    if item["primary_source_assertion_id"] != expected_assertion_id(item, "PRIMARY"):
        errors.append("primary assertion identity drift")
    if item["completion_source_assertion_id"] != expected_assertion_id(item, "COMPLETION"):
        errors.append("completion assertion identity drift")
    if item["change_id"] != expected_change_id(item):
        errors.append("change identity drift")
    timing = item["timing"]
    if timing.get("timing_type") != "MULTI_DAY_LOCAL" or timing.get("start_local") != "2026-06-08" or timing.get("end_local") != "2026-06-18":
        errors.append("SB64 authoritative day-range contract drift")
    if timing.get("source_timezone") != "Europe/Berlin":
        errors.append("SB64 source timezone drift")
    if timing.get("start_utc") is not None or timing.get("end_utc") is not None:
        errors.append("SB64 multi-day anchor must not synthesize UTC endpoints")
    if timing.get("time_precision") != "DAY" or timing.get("all_day_semantics") is not True:
        errors.append("SB64 day-precision/all-day semantics drift")
    if item.get("environmental_process_type") != "HISTORICAL_CONTEXT_ANCHOR":
        errors.append("SB64 must use existing HISTORICAL_CONTEXT_ANCHOR environmental-process vocabulary")

    if not validate_registry(registry, sources).ok:
        errors.extend(validate_registry(registry, sources).errors)
    errors.extend(f"overlay pre-state: {e}" for e in validate_biosecurity_overlay(registry, overlay))
    errors.extend(f"Analysis pre-state: {e}" for e in validate_analysis(analysis_schema, evidence, reviews, registry).errors)
    readiness = analysis_population_readiness(analysis_schema, reviews, registry)
    if readiness["eligible_completed_occurrence_count"] != 19 or readiness["reviewed_occurrence_count"] != 12:
        errors.append("unexpected post-AG Analysis population checkpoint")
    if errors:
        raise SystemExit("PRECONDITION FAILED:\n- " + "\n- ".join(errors))


def build_source(base: dict, source_plan: dict, reference_date: str) -> dict:
    out = copy.deepcopy(base)
    out.update(
        source_id=source_plan["source_id"], institution=source_plan["institution"], jurisdiction=source_plan["jurisdiction"],
        domain=source_plan["domain"], endpoint_role=source_plan["endpoint_role"], authoritative_url=source_plan["authoritative_url"],
        backup_source=source_plan["backup_source"], source_type=source_plan["source_type"], information_supplied=source_plan["information_supplied"],
        future_schedule_horizon=source_plan["future_schedule_horizon"], typical_advance_notice=source_plan["typical_advance_notice"],
        source_timezone=source_plan["source_timezone"], canonical_dependency_count=source_plan["canonical_dependency_count"], notes=source_plan["notes"],
        recommended_verification_cadence="manual historical recheck if the retained UNFCCC SB64 page changes",
        monitoring_priority_score=0, monitoring_readiness_assessed_at=reference_date,
        runtime_health_state="UNKNOWN_NOT_LIVE_POLLED", parser_type="HTML", parser_version=None,
        monitor_endpoints=[], last_successful_research_verification_at=reference_date,
    )
    return out


def build_anchor(template: dict, item: dict, reference_date: str) -> dict:
    out = copy.deepcopy(template)
    timing = item["timing"]
    out.update(
        occurrence_id=item["occurrence_id"], series_id=item["series_id"], canonical_name=item["canonical_name"],
        short_calendar_title=item["short_calendar_title"], certainty_status=item["certainty_status"], lifecycle_status=item["lifecycle_status"],
        timing_type=timing["timing_type"], start_local=timing["start_local"], end_local=timing["end_local"],
        source_timezone=timing["source_timezone"], start_utc=None, end_utc=None, date_earliest=None, date_latest=None,
        time_precision=timing["time_precision"], all_day_semantics=True, time_status=timing["time_status"], time_basis=timing["time_basis"],
        publication_datetime=None, location=item["location"], source_id=item["source_id"],
        primary_source_assertion_id=item["primary_source_assertion_id"], last_successful_assertion_id=item["completion_source_assertion_id"],
        first_announced_at=None, first_discovered_at=reference_date, last_verified_at=reference_date, next_verification_due="SOURCE_SPECIFIC",
        environmental_process_type=item["environmental_process_type"], treaty_or_assessment_body=item["treaty_or_assessment_body"],
        legal_session_identity=item["legal_session_identity"], conference_complex_id=None, render_cluster_key=None,
        publication_bundle_type="SINGLE_RELEASE", calendar_aggregation_policy="STANDALONE", assessment_product_name=None,
        approval_publication_semantics=None, population_tranche="UNFCCC_SB64_HISTORICAL_ANCHOR_AH",
        related_documents=[
            {"source_id": item["source_id"], "role": "AUTHORITATIVE_SCHEDULE_VERIFICATION", "source_locator": item["event_page_url"]},
            {"source_id": item["source_id"], "role": item["related_document_role"], "source_locator": item["closing_statement_url"]},
        ],
        derivation_sources=[item["source_id"]],
        status_history=[{
            "as_of": reference_date, "certainty_status": item["certainty_status"], "lifecycle_status": item["lifecycle_status"],
            "condition_state": out.get("condition_state", "NOT_REQUIRED"),
            "change_reason": "Historical climate-governance occurrence admitted after first-party UNFCCC closure verification; completion is not inferred from elapsed time.",
            "source_assertion_id": item["completion_source_assertion_id"], "basis": item["completion_basis"],
        }],
        notes=(item["completion_basis"] + " Meeting completion does not establish negotiation success, implementation, emissions effects, climate outcomes, observed market response or causal attribution. SBSTA64 and SBI64 remain legally distinct sessions under the SB64 umbrella."),
    )
    return out


def build_ledger_change(item: dict, committed_at: str, before_version: str, after_version: str) -> dict:
    t = item["timing"]
    return {
        "change_id": item["change_id"], "occurrence_id": item["occurrence_id"], "change_type": "HISTORICAL_OCCURRENCE_ADMISSION",
        "old_values": {"canonical_presence": False},
        "new_values": {"canonical_presence": True, "series_id": item["series_id"], "source_id": item["source_id"],
            "certainty_status": item["certainty_status"], "lifecycle_status": item["lifecycle_status"], "category": "CLIMATE_ENVIRONMENT",
            "event_type": "ENVIRONMENTAL_GOVERNANCE_EVENT", "timing_type": t["timing_type"], "start_local": t["start_local"],
            "end_local": t["end_local"], "source_timezone": t["source_timezone"], "start_utc": None, "time_precision": t["time_precision"]},
        "source_assertion_id": item["completion_source_assertion_id"], "review_state": "APPROVED_FOR_CANONICAL_COMMIT",
        "reviewed_at": committed_at,
        "review_basis": [item["event_page_url"], item["closing_statement_url"], item["completion_basis"],
            "The 23:45 closure update is completion evidence, not the canonical endpoint of the multi-day meeting.",
            "SB64 umbrella identity does not merge SBSTA64 and SBI64 legal session identities.",
            "Meeting closure does not imply negotiation success, implementation, climate outcome or market causality.",
            "UNFCCC source governance remains manual-information / production-automation hold."],
        "commit_mode": "REVIEWED_UNFCCC_SB64_HISTORICAL_ANCHOR_AH", "committed_at": committed_at,
        "registry_version_before": before_version, "registry_version_after": after_version, "canonical_mutation_committed": True,
    }


def build_post_state(registry: dict, schema: dict, sources: dict, ledger: dict, overlay: dict,
                     analysis_schema: dict, reviews: dict, evidence: dict, plan: dict, committed_at: str):
    preflight(registry, schema, sources, ledger, overlay, analysis_schema, reviews, evidence, plan)
    p, post, item = plan["preconditions"], plan["postconditions"], plan["anchor"]
    ref = plan["reference_date"]
    old_records, old_sources, old_changes = copy.deepcopy(registry["records"]), copy.deepcopy(sources["sources"]), copy.deepcopy(ledger["changes"])
    old_overlay = overlay_semantics(overlay)
    by_occ = {r["occurrence_id"]: r for r in registry["records"]}
    by_source = {s["source_id"]: s for s in sources["sources"]}

    post_registry = copy.deepcopy(registry)
    post_registry.update(version=post["canonical_registry_version"], reference_date=ref)
    post_registry["records"].append(build_anchor(by_occ[item["template_occurrence_id"]], item, ref))
    post_registry["record_count"] = len(post_registry["records"])

    post_sources = copy.deepcopy(sources)
    post_sources.update(version=post["source_registry_version"], reference_date=ref)
    post_sources["sources"].append(build_source(by_source[plan["new_source"]["clone_source_id"]], plan["new_source"], ref))

    post_ledger = copy.deepcopy(ledger)
    post_ledger.update(version=post["change_ledger_version"], reference_date=ref)
    post_ledger["changes"].append(build_ledger_change(item, committed_at, p["canonical_registry_version"], post["canonical_registry_version"]))

    post_overlay = copy.deepcopy(overlay)
    post_overlay["version"] = post["biosecurity_overlay_version"]
    post_overlay["canonical_checkpoint"] = copy.deepcopy(post["biosecurity_overlay_checkpoint"])

    errors: list[str] = []
    if post_registry["records"][:len(old_records)] != old_records: errors.append("pre-existing canonical records changed")
    if post_sources["sources"][:len(old_sources)] != old_sources: errors.append("pre-existing source records changed")
    if post_ledger["changes"][:len(old_changes)] != old_changes: errors.append("pre-existing ledger records changed")
    if overlay_semantics(post_overlay) != old_overlay: errors.append("biosecurity overlay semantic content changed")
    if post_registry["record_count"] != post["canonical_record_count"]: errors.append("canonical post-count mismatch")
    if len(post_sources["sources"]) != post["source_record_count"]: errors.append("source post-count mismatch")
    if len(post_ledger["changes"]) != post["change_ledger_count"]: errors.append("ledger post-count mismatch")

    row, source = post_registry["records"][-1], post_sources["sources"][-1]
    if row.get("occurrence_id") != item["occurrence_id"] or row.get("series_id") != item["series_id"]: errors.append("SB64 identity postcondition failed")
    if row.get("category") != "CLIMATE_ENVIRONMENT" or row.get("event_type") != "ENVIRONMENTAL_GOVERNANCE_EVENT": errors.append("SB64 primary taxonomy drift")
    if row.get("environmental_process_type") != "HISTORICAL_CONTEXT_ANCHOR": errors.append("SB64 environmental-process contract drift")
    if row.get("conference_complex_id") is not None or row.get("render_cluster_key") is not None or row.get("calendar_aggregation_policy") != "STANDALONE": errors.append("SB64 inherited COP render/complex identity")
    if row.get("start_local") != "2026-06-08" or row.get("end_local") != "2026-06-18" or row.get("source_timezone") != "Europe/Berlin": errors.append("SB64 timing postcondition failed")
    if row.get("start_utc") is not None or row.get("end_utc") is not None: errors.append("SB64 gained synthetic UTC endpoint")
    if row.get("lifecycle_status") != "COMPLETED" or row.get("certainty_status") != "CONFIRMED": errors.append("SB64 completion/certainty failed")
    if source.get("source_id") != item["source_id"] or source.get("canonical_dependency_count") != post["new_source_dependency_count"]: errors.append("SB64 source identity/dependency failed")
    if actual_primary_dependency_count(post_registry, item["source_id"]) != post["new_source_dependency_count"]: errors.append("SB64 source dependency truth mismatch")
    for key, expected in (("canonical_provenance_use", "MANUAL_INFORMATIONAL_REFERENCE_ONLY"), ("automated_monitoring_use", "PROHIBITED_OR_RIGHTS_HOLD"), ("verification_mode", "RIGHTS_HELD_MANUAL_ONLY")):
        if source.get(key) != expected: errors.append(f"SB64 source governance drift: {key}")
    if source.get("monitor_endpoints") != []: errors.append("SB64 historical source must not create a production monitor endpoint")
    if sum(1 for r in post_registry["records"] if r.get("series_id") == item["series_id"]) != 1: errors.append("SB64 tranche must create exactly one occurrence in the new series")

    rr = validate_registry(post_registry, post_sources)
    if not rr.ok: errors.extend(f"registry post-state: {e}" for e in rr.errors)
    errors.extend(f"overlay post-state: {e}" for e in validate_biosecurity_overlay(post_registry, post_overlay))
    errors.extend(f"Analysis post-state: {e}" for e in validate_analysis(analysis_schema, evidence, reviews, post_registry).errors)
    readiness = analysis_population_readiness(analysis_schema, reviews, post_registry)
    if readiness["eligible_completed_occurrence_count"] != post["eligible_completed_occurrence_count"]: errors.append("completed Analysis population mismatch")
    if readiness["reviewed_occurrence_count"] != post["reviewed_occurrence_count"]: errors.append("reviewed Analysis population changed")
    if not any(r.get("lifecycle_status") == "COMPLETED" and r.get("category") == "CLIMATE_ENVIRONMENT" for r in post_registry["records"]): errors.append("climate/environment completed-anchor gap not repaired")
    if not any(r.get("lifecycle_status") == "COMPLETED" and r.get("event_type") == "ENVIRONMENTAL_GOVERNANCE_EVENT" for r in post_registry["records"]): errors.append("environmental-governance completed type gap not repaired")
    if errors: raise SystemExit("POSTCONDITION FAILED:\n- " + "\n- ".join(errors))
    return post_registry, post_sources, post_ledger, post_overlay, readiness


def audit_text(plan: dict, committed_at: str, registry: dict, sources: dict, ledger: dict, overlay: dict, readiness: dict) -> str:
    item = plan["anchor"]
    protected = {
        "canonical_schema": file_hash(CANONICAL_SCHEMA_PATH), "monitor_expectations": file_hash(EXPECTATIONS_PATH),
        "monitor_operations_policy": file_hash(OPERATIONS_PATH), "analysis_schema": file_hash(ANALYSIS_SCHEMA_PATH),
        "analysis_reviews": file_hash(ANALYSIS_REVIEWS_PATH), "analysis_evidence": file_hash(ANALYSIS_EVIDENCE_PATH),
    }
    lines = [
        "# WORLD SIGNALS — AH transaction audit", "", "- tranche: `UNFCCC_SB64_HISTORICAL_ANCHOR_AH`",
        f"- committed_at: `{committed_at}`", f"- occurrence: `{item['occurrence_id']}`", f"- new series: `{item['series_id']}`",
        f"- new official source: `{item['source_id']}`", "- taxonomy: `CLIMATE_ENVIRONMENT` / `ENVIRONMENTAL_GOVERNANCE_EVENT`; environmental process uses existing `HISTORICAL_CONTEXT_ANCHOR` vocabulary",
        f"- canonical post-state: `v{registry['version']} / {registry['record_count']}`", f"- source post-state: `v{sources['version']} / {len(sources['sources'])}`",
        f"- ledger post-state: `v{ledger['version']} / {len(ledger['changes'])}`", f"- overlay post-state: `v{overlay['version']} @ canonical v{overlay['canonical_checkpoint']['registry_version']} / {overlay['canonical_checkpoint']['record_count']}`",
        f"- completed Analysis population: `{readiness['eligible_completed_occurrence_count']}`", f"- reviewed post-event population: `{readiness['reviewed_occurrence_count']}`",
        "- Analysis mutation: `none`", "- timing guardrail: 8–18 June 2026 Bonn day-range in `Europe/Berlin`; no synthetic UTC endpoints",
        "- closure-clock guardrail: 23:45 UNFCCC close update is completion evidence, not canonical end time", "- legal-identity guardrail: SBSTA64 and SBI64 remain distinct sessions under the SB64 umbrella",
        "- outcome guardrail: meeting completion is not negotiation success, implementation, climate outcome, market response or causality",
        "- automation guardrail: retained UNFCCC manual-information / production-automation hold; no monitor endpoint added", "- PR #40: untouched", "", "## Protected SHA-256", "",
    ]
    lines.extend(f"- {name}: `{digest}`" for name, digest in protected.items())
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    plan, registry, schema, sources = load(PLAN_PATH), load(CANONICAL_PATH), load(CANONICAL_SCHEMA_PATH), load(SOURCE_PATH)
    ledger, overlay = load(LEDGER_PATH), load(OVERLAY_PATH)
    analysis_schema, reviews, evidence = load(ANALYSIS_SCHEMA_PATH), load(ANALYSIS_REVIEWS_PATH), load(ANALYSIS_EVIDENCE_PATH)
    committed_at = transaction_time()
    before_analysis = (semantic_hash(analysis_schema), semantic_hash(reviews), semantic_hash(evidence))
    post_registry, post_sources, post_ledger, post_overlay, readiness = build_post_state(
        registry, schema, sources, ledger, overlay, analysis_schema, reviews, evidence, plan, committed_at
    )
    result = {"occurrence_id": plan["anchor"]["occurrence_id"], "canonical_post": [post_registry["version"], post_registry["record_count"]],
              "source_post": [post_sources["version"], len(post_sources["sources"])], "ledger_post": [post_ledger["version"], len(post_ledger["changes"])],
              "overlay_post": [post_overlay["version"], post_overlay["canonical_checkpoint"]], "completed_analysis_population": readiness["eligible_completed_occurrence_count"],
              "reviewed_post_event_population": readiness["reviewed_occurrence_count"]}
    if not args.apply:
        print("CHECK_ONLY_OK")
        print(json.dumps(result, indent=2))
        return
    if os.environ.get(APPLY_ENV) != "REVIEWED_APPLY":
        raise SystemExit(f"APPLY BLOCKED: set {APPLY_ENV}=REVIEWED_APPLY in the reviewed transaction workflow")
    dump(CANONICAL_PATH, post_registry); dump(SOURCE_PATH, post_sources); dump(LEDGER_PATH, post_ledger); dump(OVERLAY_PATH, post_overlay)
    AUDIT_PATH.write_text(audit_text(plan, committed_at, post_registry, post_sources, post_ledger, post_overlay, readiness), encoding="utf-8")
    after_analysis = (semantic_hash(load(ANALYSIS_SCHEMA_PATH)), semantic_hash(load(ANALYSIS_REVIEWS_PATH)), semantic_hash(load(ANALYSIS_EVIDENCE_PATH)))
    if after_analysis != before_analysis: raise SystemExit("POST-WRITE FAILED: Analysis drift detected")
    print("APPLY_OK")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
