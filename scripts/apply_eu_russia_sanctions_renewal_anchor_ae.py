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
ANALYSIS_SCHEMA_PATH = ROOT / "data/analysis/schema.json"
ANALYSIS_REVIEWS_PATH = ROOT / "data/analysis/event_reviews.json"
ANALYSIS_EVIDENCE_PATH = ROOT / "data/analysis/evidence_registry.json"
PLAN_PATH = ROOT / "data/coverage/EU_RUSSIA_SANCTIONS_RENEWAL_HISTORICAL_ANCHOR_AE_PLAN_v0.1.json"
AUDIT_PATH = ROOT / "data/coverage/EU_RUSSIA_SANCTIONS_RENEWAL_HISTORICAL_ANCHOR_AE_TRANSACTION_AUDIT_v0.1.md"
APPLY_ENV = "WORLD_SIGNALS_APPLY_EU_SANCTIONS_ANCHOR_AE"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def semantic_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def transaction_time() -> str:
    return datetime.now(ZoneInfo("Australia/Melbourne")).isoformat(timespec="seconds")


def expected_assertion_id(item: dict, role: str) -> str:
    material = "|".join([item["occurrence_id"], item["series_id"], item["source_id"], role, item["timing"]["start_local"]])
    return "WSA-AE-" + hashlib.sha256(material.encode()).hexdigest()[:16]


def expected_change_id(item: dict) -> str:
    material = "|".join([item["occurrence_id"], item["series_id"], item["source_id"], item["timing"]["start_local"], "HISTORICAL_OCCURRENCE_ADMISSION"])
    return "WSCHANGE-" + hashlib.sha256(material.encode()).hexdigest()[:18]


def actual_primary_dependency_count(registry: dict, source_id: str) -> int:
    return sum(1 for row in registry.get("records", []) if row.get("source_id") == source_id)


def overlay_semantics(overlay: dict) -> dict:
    return {k: copy.deepcopy(v) for k, v in overlay.items() if k not in {"version", "canonical_checkpoint"}}


def preflight(registry: dict, schema: dict, sources: dict, ledger: dict, overlay: dict, analysis_schema: dict, reviews: dict, evidence: dict, plan: dict) -> None:
    p = plan["preconditions"]
    item = plan["anchor"]
    errors: list[str] = []
    checks = [
        (str(schema.get("version")) == p["canonical_schema_version"], "canonical schema version drift"),
        (str(registry.get("version")) == p["canonical_registry_version"], "canonical registry version drift"),
        (registry.get("record_count") == p["canonical_record_count"] == len(registry.get("records", [])), "canonical record count drift"),
        (str(sources.get("version")) == p["source_registry_version"], "source registry version drift"),
        (len(sources.get("sources", [])) == p["source_record_count"], "source count drift"),
        (str(ledger.get("version")) == p["change_ledger_version"], "ledger version drift"),
        (len(ledger.get("changes", [])) == p["change_ledger_count"], "ledger count drift"),
        (str(overlay.get("version")) == p["biosecurity_overlay_version"], "overlay version drift"),
        (overlay.get("canonical_checkpoint") == p["biosecurity_overlay_checkpoint"], "overlay checkpoint drift"),
        (str(analysis_schema.get("version")) == p["analysis_schema_version"], "Analysis schema drift"),
        (str(reviews.get("version")) == p["analysis_reviews_version"] and len(reviews.get("reviews", [])) == p["analysis_review_count"], "Analysis reviews drift"),
        (str(evidence.get("version")) == p["analysis_evidence_version"] and len(evidence.get("evidence", [])) == p["analysis_evidence_count"], "Analysis evidence drift"),
    ]
    errors.extend(msg for ok, msg in checks if not ok)

    by_occ = {r.get("occurrence_id"): r for r in registry.get("records", [])}
    by_source = {s.get("source_id"): s for s in sources.get("sources", [])}
    change_ids = {c.get("change_id") for c in ledger.get("changes", [])}
    for oid in p["required_absent_occurrence_ids"]:
        if oid in by_occ:
            errors.append(f"occurrence identity collision: {oid}")
    for cid in p["required_absent_change_ids"]:
        if cid in change_ids:
            errors.append(f"change identity collision: {cid}")

    expected_template = p["required_template"]
    template = by_occ.get(expected_template["occurrence_id"])
    if template is None:
        errors.append("required sanctions template missing")
    else:
        for key, expected in expected_template.items():
            if key != "occurrence_id" and template.get(key) != expected:
                errors.append(f"template field drift: {key}")

    expected_source = p["required_primary_source"]
    source = by_source.get(expected_source["source_id"])
    if source is None:
        errors.append("required Council source missing")
    else:
        for key in ("institution", "authoritative_url", "canonical_dependency_count", "source_timezone", "parser_type"):
            if source.get(key) != expected_source[key]:
                errors.append(f"Council source field drift: {key}")
        actual = actual_primary_dependency_count(registry, expected_source["source_id"])
        if actual != expected_source["actual_primary_dependency_count"]:
            errors.append("Council actual dependency count drift")
        if actual != source.get("canonical_dependency_count"):
            errors.append("Council dependency helper does not match canonical truth")

    if item["primary_source_assertion_id"] != expected_assertion_id(item, "PRIMARY"):
        errors.append("primary assertion identity drift")
    if item["completion_source_assertion_id"] != expected_assertion_id(item, "COMPLETION"):
        errors.append("completion assertion identity drift")
    if item["change_id"] != expected_change_id(item):
        errors.append("change identity drift")
    if "T" in item["timing"]["start_local"] or item["timing"].get("start_utc") is not None:
        errors.append("AE must preserve day precision and must not promote the press-release clock")
    if item["trade_policy_temporal_role"] != "LEGAL_ADOPTION":
        errors.append("AE renewal decision must use LEGAL_ADOPTION")

    reg_report = validate_registry(registry, sources)
    if not reg_report.ok:
        errors.extend(f"canonical pre-state: {e}" for e in reg_report.errors)
    overlay_errors = validate_biosecurity_overlay(registry, overlay)
    errors.extend(f"overlay pre-state: {e}" for e in overlay_errors)
    analysis_report = validate_analysis(analysis_schema, evidence, reviews, registry)
    errors.extend(f"Analysis pre-state: {e}" for e in analysis_report.errors)
    if errors:
        raise SystemExit("PRECONDITION FAILED:\n- " + "\n- ".join(errors))


def build_anchor(template: dict, item: dict, reference_date: str) -> dict:
    out = copy.deepcopy(template)
    timing = item["timing"]
    out.update(
        occurrence_id=item["occurrence_id"],
        canonical_name=item["canonical_name"],
        short_calendar_title=item["short_calendar_title"],
        record_class=item["record_class"],
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
        time_status=timing["time_status"],
        time_basis=timing["time_basis"],
        publication_datetime=None,
        trade_policy_temporal_role=item["trade_policy_temporal_role"],
        trade_measure_state=item["trade_measure_state"],
        review_or_renewal_required=item["review_or_renewal_required"],
        expiry_does_not_imply_termination=item["expiry_does_not_imply_termination"],
        primary_source_assertion_id=item["primary_source_assertion_id"],
        last_successful_assertion_id=item["completion_source_assertion_id"],
        first_announced_at=None,
        first_discovered_at=reference_date,
        last_verified_at=reference_date,
        next_verification_due="SOURCE_SPECIFIC",
        population_tranche="EU_RUSSIA_SANCTIONS_RENEWAL_HISTORICAL_ANCHOR_AE",
        related_documents=[{
            "source_id": item["source_id"],
            "role": item["related_document_role"],
            "source_locator": item["source_url"]
        }],
        derivation_sources=[item["source_id"]],
        status_history=[{
            "as_of": reference_date,
            "certainty_status": item["certainty_status"],
            "lifecycle_status": item["lifecycle_status"],
            "condition_state": out.get("condition_state", "NOT_REQUIRED"),
            "change_reason": "Historical renewal decision admitted after competent first-party post-event verification; completion is not inferred from elapsed time.",
            "source_assertion_id": item["completion_source_assertion_id"],
            "basis": item["completion_basis"]
        }],
        notes=item["completion_basis"] + " This legal-adoption occurrence is distinct from the 31 July 2027 expiry/renewal boundary and does not encode a market reaction."
    )
    return out


def build_ledger_change(item: dict, committed_at: str, before_version: str, after_version: str) -> dict:
    t = item["timing"]
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
            "timing_type": t["timing_type"],
            "start_local": t["start_local"],
            "source_timezone": t["source_timezone"],
            "start_utc": t["start_utc"],
            "time_precision": t["time_precision"],
            "trade_policy_temporal_role": item["trade_policy_temporal_role"],
            "trade_measure_state": item["trade_measure_state"]
        },
        "source_assertion_id": item["completion_source_assertion_id"],
        "review_state": "APPROVED_FOR_CANONICAL_COMMIT",
        "reviewed_at": committed_at,
        "review_basis": [
            item["source_url"],
            item["completion_basis"],
            "The Council source already serves the existing forward renewal-boundary series and is competent first-party evidence for the 25 June 2026 renewal decision.",
            "The page's 19:45 timestamp is publication time and is not promoted to canonical decision time.",
            "Legal adoption, future expiry/renewal boundary, observed market response and causal attribution remain distinct."
        ],
        "commit_mode": "REVIEWED_EU_RUSSIA_SANCTIONS_RENEWAL_HISTORICAL_ANCHOR_AE",
        "committed_at": committed_at,
        "registry_version_before": before_version,
        "registry_version_after": after_version,
        "canonical_mutation_committed": True
    }


def build_post_state(registry: dict, schema: dict, sources: dict, ledger: dict, overlay: dict, analysis_schema: dict, reviews: dict, evidence: dict, plan: dict, committed_at: str):
    preflight(registry, schema, sources, ledger, overlay, analysis_schema, reviews, evidence, plan)
    p = plan["preconditions"]
    post = plan["postconditions"]
    item = plan["anchor"]
    reference_date = plan["reference_date"]

    old_records = copy.deepcopy(registry["records"])
    old_sources = copy.deepcopy(sources["sources"])
    old_changes = copy.deepcopy(ledger["changes"])
    old_overlay_semantics = overlay_semantics(overlay)
    by_occ = {r["occurrence_id"]: r for r in registry["records"]}

    post_registry = copy.deepcopy(registry)
    post_registry["version"] = post["canonical_registry_version"]
    post_registry["reference_date"] = reference_date
    post_registry["records"].append(build_anchor(by_occ[item["template_occurrence_id"]], item, reference_date))
    post_registry["record_count"] = len(post_registry["records"])

    post_sources = copy.deepcopy(sources)
    post_sources["version"] = post["source_registry_version"]
    post_sources["reference_date"] = reference_date
    target = next(s for s in post_sources["sources"] if s.get("source_id") == item["source_id"])
    target["canonical_dependency_count"] = plan["source_mutation"]["allowed_existing_field_changes"]["canonical_dependency_count"]["to"]

    post_ledger = copy.deepcopy(ledger)
    post_ledger["version"] = post["change_ledger_version"]
    post_ledger["reference_date"] = reference_date
    post_ledger["changes"].append(build_ledger_change(item, committed_at, p["canonical_registry_version"], post["canonical_registry_version"]))

    post_overlay = copy.deepcopy(overlay)
    post_overlay["version"] = post["biosecurity_overlay_version"]
    post_overlay["canonical_checkpoint"] = copy.deepcopy(post["biosecurity_overlay_checkpoint"])

    errors: list[str] = []
    if post_registry["records"][:len(old_records)] != old_records:
        errors.append("pre-existing canonical records changed")
    if post_ledger["changes"][:len(old_changes)] != old_changes:
        errors.append("pre-existing ledger records changed")
    if overlay_semantics(post_overlay) != old_overlay_semantics:
        errors.append("biosecurity overlay semantic content changed")

    old_by_source = {s["source_id"]: s for s in old_sources}
    new_by_source = {s["source_id"]: s for s in post_sources["sources"]}
    if set(old_by_source) != set(new_by_source):
        errors.append("source identity set changed")
    changed_source_ids = []
    for sid in old_by_source:
        if old_by_source[sid] != new_by_source[sid]:
            changed_source_ids.append(sid)
    if changed_source_ids != [item["source_id"]]:
        errors.append(f"existing source mutation scope drift: {changed_source_ids}")
    else:
        before = copy.deepcopy(old_by_source[item["source_id"]])
        after = copy.deepcopy(new_by_source[item["source_id"]])
        before_count = before.pop("canonical_dependency_count", None)
        after_count = after.pop("canonical_dependency_count", None)
        if before != after or (before_count, after_count) != (1, 2):
            errors.append("Council source mutation exceeds dependency helper 1->2")

    if post_registry.get("record_count") != post["canonical_record_count"]:
        errors.append("canonical post-count mismatch")
    if len(post_sources.get("sources", [])) != post["source_record_count"]:
        errors.append("source post-count mismatch")
    if len(post_ledger.get("changes", [])) != post["change_ledger_count"]:
        errors.append("ledger post-count mismatch")
    if actual_primary_dependency_count(post_registry, item["source_id"]) != 2:
        errors.append("post-state Council primary dependency truth is not 2")
    target_post = next(s for s in post_sources["sources"] if s.get("source_id") == item["source_id"])
    if target_post.get("canonical_dependency_count") != actual_primary_dependency_count(post_registry, item["source_id"]):
        errors.append("post-state Council dependency helper mismatch")

    new_row = post_registry["records"][-1]
    if new_row.get("trade_policy_temporal_role") != "LEGAL_ADOPTION" or new_row.get("trade_measure_state") != "IN_FORCE":
        errors.append("trade semantic postcondition failed")
    if new_row.get("start_local") != "2026-06-25" or new_row.get("start_utc") is not None or new_row.get("publication_datetime") is not None:
        errors.append("day-precision decision-time guardrail failed")
    if new_row.get("lifecycle_status") != "COMPLETED":
        errors.append("historical anchor is not completed")

    reg_report = validate_registry(post_registry, post_sources)
    if not reg_report.ok:
        errors.extend(f"registry post-state: {e}" for e in reg_report.errors)
    overlay_errors = validate_biosecurity_overlay(post_registry, post_overlay)
    errors.extend(f"overlay post-state: {e}" for e in overlay_errors)
    analysis_report = validate_analysis(analysis_schema, evidence, reviews, post_registry)
    errors.extend(f"Analysis post-state: {e}" for e in analysis_report.errors)

    completed = [r for r in post_registry["records"] if r.get("lifecycle_status") == "COMPLETED"]
    reviewed_ids = {r.get("canonical_occurrence_id") for r in reviews.get("reviews", [])}
    if len(completed) != post["completed_analysis_eligible_count"]:
        errors.append(f"completed count mismatch: {len(completed)}")
    if sum(r.get("occurrence_id") in reviewed_ids for r in completed) != post["reviewed_completed_count"]:
        errors.append("reviewed-completed count mismatch")
    if not any(r.get("lifecycle_status") == "COMPLETED" and r.get("category") == post["new_completed_category"] for r in post_registry["records"]):
        errors.append("trade category completion gap not repaired")
    if not any(r.get("lifecycle_status") == "COMPLETED" and r.get("event_type") == post["new_completed_event_type"] for r in post_registry["records"]):
        errors.append("sanctions-process completion gap not repaired")

    if errors:
        raise SystemExit("POSTCONDITION FAILED:\n- " + "\n- ".join(errors))
    return post_registry, post_sources, post_ledger, post_overlay


def audit_text(plan: dict, committed_at: str, registry: dict, sources: dict, ledger: dict, overlay: dict) -> str:
    item = plan["anchor"]
    return f"""# WORLD SIGNALS — AE transaction audit\n\n- tranche: `EU_RUSSIA_SANCTIONS_RENEWAL_HISTORICAL_ANCHOR_AE`\n- committed_at: `{committed_at}`\n- occurrence: `{item['occurrence_id']}`\n- series reused: `{item['series_id']}`\n- primary source reused: `{item['source_id']}`\n- source dependency helper: `1 -> 2`\n- canonical post-state: `v{registry['version']} / {registry['record_count']}`\n- source post-state: `v{sources['version']} / {len(sources['sources'])}`\n- ledger post-state: `v{ledger['version']} / {len(ledger['changes'])}`\n- overlay post-state: `v{overlay['version']} @ canonical v{overlay['canonical_checkpoint']['registry_version']} / {overlay['canonical_checkpoint']['record_count']}`\n- Analysis mutation: `none`\n- timing guardrail: `2026-06-25` day precision, `Europe/Brussels`; Council page publication time 19:45 is not canonical decision time\n- semantic guardrail: renewal decision != publication timestamp != 2027 expiry/renewal boundary != market move != causal attribution\n- new source identities: `0`\n- PR #40: untouched\n"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    plan = load(PLAN_PATH)
    registry = load(CANONICAL_PATH)
    schema = load(CANONICAL_SCHEMA_PATH)
    sources = load(SOURCE_PATH)
    ledger = load(LEDGER_PATH)
    overlay = load(OVERLAY_PATH)
    analysis_schema = load(ANALYSIS_SCHEMA_PATH)
    reviews = load(ANALYSIS_REVIEWS_PATH)
    evidence = load(ANALYSIS_EVIDENCE_PATH)
    committed_at = transaction_time()
    before_analysis = (semantic_hash(analysis_schema), semantic_hash(reviews), semantic_hash(evidence))
    post_registry, post_sources, post_ledger, post_overlay = build_post_state(
        registry, schema, sources, ledger, overlay, analysis_schema, reviews, evidence, plan, committed_at
    )
    result = {
        "occurrence_id": plan["anchor"]["occurrence_id"],
        "canonical_post": [post_registry["version"], post_registry["record_count"]],
        "source_post": [post_sources["version"], len(post_sources["sources"])],
        "ledger_post": [post_ledger["version"], len(post_ledger["changes"])],
        "overlay_post": [post_overlay["version"], post_overlay["canonical_checkpoint"]],
        "completed": sum(r.get("lifecycle_status") == "COMPLETED" for r in post_registry["records"]),
        "reviews": len(reviews.get("reviews", []))
    }
    if not args.apply:
        print("CHECK_ONLY_OK")
        print(json.dumps(result, indent=2))
        return
    if os.environ.get(APPLY_ENV) != "REVIEWED_APPLY":
        raise SystemExit(f"APPLY BLOCKED: set {APPLY_ENV}=REVIEWED_APPLY in the reviewed transaction workflow")
    dump(CANONICAL_PATH, post_registry)
    dump(SOURCE_PATH, post_sources)
    dump(LEDGER_PATH, post_ledger)
    dump(OVERLAY_PATH, post_overlay)
    AUDIT_PATH.write_text(audit_text(plan, committed_at, post_registry, post_sources, post_ledger, post_overlay), encoding="utf-8")
    after_analysis = (semantic_hash(load(ANALYSIS_SCHEMA_PATH)), semantic_hash(load(ANALYSIS_REVIEWS_PATH)), semantic_hash(load(ANALYSIS_EVIDENCE_PATH)))
    if after_analysis != before_analysis:
        raise SystemExit("POST-WRITE FAILED: Analysis drift detected")
    print("APPLY_OK")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
