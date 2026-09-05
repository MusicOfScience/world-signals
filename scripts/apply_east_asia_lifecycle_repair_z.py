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
PLAN_PATH = ROOT / "data/coverage/EAST_ASIA_LIFECYCLE_REPAIR_Z_PLAN_v0.1.json"
AUDIT_PATH = ROOT / "data/coverage/EAST_ASIA_LIFECYCLE_REPAIR_Z_TRANSACTION_AUDIT_v0.1.md"

APPLY_ENV = "WORLD_SIGNALS_APPLY_EAST_ASIA_LIFECYCLE_REPAIR_Z"
APPLY_VALUE = "YES"
TARGET_IDS = ("WSO-FIS-A-0015", "WSO-MAC-B-0041")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transaction_time() -> str:
    return datetime.now(ZoneInfo("Australia/Melbourne")).isoformat(timespec="seconds")


def assertion_id(item: dict) -> str:
    material = "|".join((
        item["occurrence_id"], item["completion_source_id"], item["completion_source_url"], "COMPLETED"
    ))
    return "WSA-" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def change_id(item: dict) -> str:
    material = "|".join((
        "Z", item["occurrence_id"], item["completion_source_id"], "PLANNED", "COMPLETED"
    ))
    return "WSCHANGE-" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:18]


def overlay_semantics(value: dict) -> dict:
    return {k: copy.deepcopy(v) for k, v in value.items() if k not in {"version", "canonical_checkpoint"}}


def by_occurrence(registry: dict) -> dict[str, dict]:
    return {row.get("occurrence_id"): row for row in registry.get("records", [])}


def by_source(sources: dict) -> dict[str, dict]:
    return {row.get("source_id"): row for row in sources.get("sources", [])}


def exact_subset(row: dict, expected: dict, label: str, errors: list[str]) -> None:
    for key, value in expected.items():
        if row.get(key) != value:
            errors.append(f"{label} {key}: expected {value!r}, found {row.get(key)!r}")


def preflight(canonical: dict, canonical_schema: dict, sources: dict, ledger: dict, overlay: dict,
              analysis_schema: dict, reviews: dict, evidence: dict, plan: dict) -> None:
    p = plan["preconditions"]
    errors: list[str] = []

    checks = [
        (str(canonical_schema.get("version")) == p["canonical_schema_version"], "canonical schema version drift"),
        (str(canonical.get("version")) == p["canonical_registry_version"], "canonical registry version drift"),
        (canonical.get("record_count") == p["canonical_record_count"] == len(canonical.get("records", [])), "canonical record count drift"),
        (str(sources.get("version")) == p["source_registry_version"], "source registry version drift"),
        (len(sources.get("sources", [])) == p["source_record_count"], "source record count drift"),
        (str(ledger.get("version")) == p["change_ledger_version"], "change ledger version drift"),
        (len(ledger.get("changes", [])) == p["change_ledger_count"], "change ledger count drift"),
        (str(overlay.get("version")) == p["biosecurity_overlay_version"], "biosecurity overlay version drift"),
        (overlay.get("canonical_checkpoint") == p["biosecurity_overlay_checkpoint"], "biosecurity overlay checkpoint drift"),
        (str(analysis_schema.get("version")) == p["analysis_schema_version"], "Analysis schema version drift"),
        (str(reviews.get("version")) == p["analysis_reviews_version"] and len(reviews.get("reviews", [])) == p["analysis_review_count"], "Analysis reviews drift"),
        (str(evidence.get("version")) == p["analysis_evidence_version"] and len(evidence.get("evidence", [])) == p["analysis_evidence_count"], "Analysis evidence drift"),
    ]
    errors.extend(label for ok, label in checks if not ok)

    occ = by_occurrence(canonical)
    for oid, baseline in p["targets"].items():
        if oid not in occ:
            errors.append(f"missing target occurrence {oid}")
        else:
            exact_subset(occ[oid], baseline, f"target {oid}", errors)

    src = by_source(sources)
    for sid in p["required_absent_source_ids"]:
        if sid in src:
            errors.append(f"completion source already exists: {sid}")
    for item in plan["repairs"]:
        if item["completion_source_clone_id"] not in src:
            errors.append(f"missing source clone {item['completion_source_clone_id']}")
        if change_id(item) in {row.get("change_id") for row in ledger.get("changes", [])}:
            errors.append(f"change identity collision for {item['occurrence_id']}")

    readiness = analysis_population_readiness(analysis_schema, reviews, canonical)
    if readiness["eligible_completed_occurrence_count"] != p["eligible_completed_occurrence_count"]:
        errors.append("eligible completed pre-count drift")
    if readiness["reviewed_occurrence_count"] != p["reviewed_occurrence_count"]:
        errors.append("reviewed occurrence pre-count drift")

    errors.extend(f"biosecurity pre-state: {e}" for e in validate_biosecurity_overlay(canonical, overlay))
    analysis_validation = validate_analysis(analysis_schema, evidence, reviews, canonical)
    errors.extend(f"Analysis pre-state: {e}" for e in analysis_validation.errors)
    if errors:
        raise SystemExit("Z PRECONDITION FAILED:\n- " + "\n- ".join(errors))


def build_completion_source(base: dict, item: dict, reference_date: str) -> dict:
    out = copy.deepcopy(base)
    out.update(
        source_id=item["completion_source_id"],
        endpoint_role=item["completion_source_endpoint_role"],
        authoritative_url=item["completion_source_url"],
        source_type=item["completion_source_type"],
        information_supplied=item["completion_information_supplied"],
        future_schedule_horizon="post-event completion/outcome surface; not forward schedule authority",
        typical_advance_notice="post-event publication",
        parser_type="MANUAL_OFFICIAL_RESULT_VERIFICATION",
        parser_version=None,
        runtime_health_state="MANUAL_RESEARCH_VERIFIED",
        verification_mode="MANUAL_AUTHORITATIVE_RECHECK",
        automated_monitoring_use="ENDPOINT_REVIEW_REQUIRED",
        canonical_dependency_count=0,
        monitoring_priority_score=0,
        last_successful_research_verification_at=reference_date,
        monitoring_readiness_assessed_at=reference_date,
        notes=(item["completion_basis"] + " Supporting completion source only; forward schedule authority remains " + item["completion_source_clone_id"] + "."),
    )
    return out


def patch_target(before: dict, item: dict, reference_date: str) -> dict:
    out = copy.deepcopy(before)
    aid = assertion_id(item)
    out["lifecycle_status"] = "COMPLETED"
    out["last_verified_at"] = reference_date
    out["last_successful_assertion_id"] = aid
    out.setdefault("status_history", []).append({
        "as_of": reference_date,
        "certainty_status": "CONFIRMED",
        "lifecycle_status": "COMPLETED",
        "condition_state": out.get("condition_state", "NOT_REQUIRED"),
        "change_reason": "Existing scheduled occurrence marked completed after authoritative first-party post-event verification; completion is not inferred from elapsed time.",
        "source_assertion_id": aid,
        "basis": item["completion_basis"],
    })
    out.setdefault("related_documents", []).append({
        "source_id": item["completion_source_id"],
        "role": item["related_document_role"],
        "source_locator": item["completion_source_url"],
    })
    return out


def build_ledger_entry(before: dict, after: dict, item: dict, committed_at: str, before_version: str, after_version: str) -> dict:
    return {
        "change_id": change_id(item),
        "occurrence_id": item["occurrence_id"],
        "change_type": "LIFECYCLE_AND_CERTAINTY_UPDATE",
        "old_values": {
            "certainty_status": before.get("certainty_status"),
            "lifecycle_status": before.get("lifecycle_status"),
            "last_verified_at": before.get("last_verified_at"),
            "last_successful_assertion_id": before.get("last_successful_assertion_id"),
        },
        "new_values": {
            "certainty_status": after.get("certainty_status"),
            "lifecycle_status": after.get("lifecycle_status"),
            "last_verified_at": after.get("last_verified_at"),
            "last_successful_assertion_id": after.get("last_successful_assertion_id"),
            "completion_source_id": item["completion_source_id"],
            "completion_source_url": item["completion_source_url"],
        },
        "source_assertion_id": assertion_id(item),
        "review_state": "APPROVED_FOR_CANONICAL_COMMIT",
        "reviewed_at": committed_at,
        "review_basis": [
            item["completion_source_url"],
            item["completion_basis"],
            "Stable occurrence, series and forward schedule-source identities are preserved.",
            "Source-native day precision and null UTC fields are preserved; no clock time is inferred from publication/result material.",
            "Lifecycle completion is supported by competent first-party post-event evidence and is not inferred from elapsed time alone.",
        ],
        "commit_mode": "REVIEWED_LIFECYCLE_REPAIR_Z",
        "committed_at": committed_at,
        "registry_version_before": before_version,
        "registry_version_after": after_version,
        "canonical_mutation_committed": True,
    }


def build_post_state(canonical: dict, canonical_schema: dict, sources: dict, ledger: dict, overlay: dict,
                     analysis_schema: dict, reviews: dict, evidence: dict, plan: dict, committed_at: str):
    preflight(canonical, canonical_schema, sources, ledger, overlay, analysis_schema, reviews, evidence, plan)
    reference_date = plan["reference_date"]
    post = plan["postconditions"]

    post_canonical = copy.deepcopy(canonical)
    post_sources = copy.deepcopy(sources)
    post_ledger = copy.deepcopy(ledger)
    post_overlay = copy.deepcopy(overlay)

    before_occ = by_occurrence(canonical)
    after_occ = by_occurrence(post_canonical)
    source_map = by_source(sources)

    for item in plan["repairs"]:
        oid = item["occurrence_id"]
        after_occ[oid].clear()
        after_occ[oid].update(patch_target(before_occ[oid], item, reference_date))
        post_sources["sources"].append(build_completion_source(source_map[item["completion_source_clone_id"]], item, reference_date))
        post_ledger["changes"].append(build_ledger_entry(before_occ[oid], after_occ[oid], item, committed_at,
                                                         plan["preconditions"]["canonical_registry_version"],
                                                         post["canonical_registry_version"]))

    post_canonical["version"] = post["canonical_registry_version"]
    post_canonical["reference_date"] = reference_date
    post_canonical["record_count"] = len(post_canonical["records"])

    post_sources["version"] = post["source_registry_version"]
    post_sources["reference_date"] = reference_date

    post_ledger["version"] = post["change_ledger_version"]
    post_ledger["reference_date"] = reference_date

    post_overlay["version"] = post["biosecurity_overlay_version"]
    post_overlay["canonical_checkpoint"] = copy.deepcopy(post["biosecurity_overlay_checkpoint"])

    validate_post_state(canonical, sources, ledger, overlay, post_canonical, post_sources, post_ledger, post_overlay,
                        canonical_schema, analysis_schema, reviews, evidence, plan)
    return post_canonical, post_sources, post_ledger, post_overlay


def validate_post_state(canonical_before: dict, sources_before: dict, ledger_before: dict, overlay_before: dict,
                        canonical_after: dict, sources_after: dict, ledger_after: dict, overlay_after: dict,
                        canonical_schema: dict, analysis_schema: dict, reviews: dict, evidence: dict, plan: dict) -> None:
    post = plan["postconditions"]
    errors: list[str] = []

    if (canonical_after.get("version"), canonical_after.get("record_count"), len(canonical_after.get("records", []))) != (post["canonical_registry_version"], post["canonical_record_count"], post["canonical_record_count"]):
        errors.append("canonical post-state mismatch")
    if (sources_after.get("version"), len(sources_after.get("sources", []))) != (post["source_registry_version"], post["source_record_count"]):
        errors.append("source post-state mismatch")
    if (ledger_after.get("version"), len(ledger_after.get("changes", []))) != (post["change_ledger_version"], post["change_ledger_count"]):
        errors.append("ledger post-state mismatch")
    if overlay_after.get("version") != post["biosecurity_overlay_version"] or overlay_after.get("canonical_checkpoint") != post["biosecurity_overlay_checkpoint"]:
        errors.append("overlay checkpoint post-state mismatch")
    if overlay_semantics(overlay_after) != overlay_semantics(overlay_before):
        errors.append("overlay semantics changed")

    before_occ = by_occurrence(canonical_before)
    after_occ = by_occurrence(canonical_after)
    if list(before_occ) != list(after_occ):
        errors.append("canonical occurrence identity/order changed")
    changed = [oid for oid in before_occ if before_occ[oid] != after_occ[oid]]
    if set(changed) != set(TARGET_IDS) or len(changed) != 2:
        errors.append(f"unexpected canonical mutation scope: {changed}")

    allowed_fields = {"lifecycle_status", "last_verified_at", "last_successful_assertion_id", "status_history", "related_documents"}
    for oid in TARGET_IDS:
        before, after = before_occ[oid], after_occ[oid]
        changed_fields = {key for key in set(before) | set(after) if before.get(key) != after.get(key)}
        if not changed_fields.issubset(allowed_fields):
            errors.append(f"target {oid} changed outside allowed fields: {sorted(changed_fields - allowed_fields)}")
        if after.get("lifecycle_status") != "COMPLETED" or after.get("certainty_status") != "CONFIRMED":
            errors.append(f"target {oid} lifecycle/certainty mismatch")
        for key in ("occurrence_id", "series_id", "source_id", "start_local", "end_local", "source_timezone", "start_utc", "end_utc", "timing_type", "time_precision", "all_day_semantics", "time_status", "time_basis", "primary_source_assertion_id", "event_type", "category", "intrinsic_importance", "expected_market_sensitivity", "auction_stage"):
            if before.get(key) != after.get(key):
                errors.append(f"protected target field changed: {oid} {key}")

    before_sources = by_source(sources_before)
    after_sources = by_source(sources_after)
    for sid, row in before_sources.items():
        if after_sources.get(sid) != row:
            errors.append(f"pre-existing source changed: {sid}")
    for item in plan["repairs"]:
        source = after_sources.get(item["completion_source_id"])
        if not source:
            errors.append(f"missing completion source {item['completion_source_id']}")
        elif source.get("canonical_dependency_count") != 0 or source.get("authoritative_url") != item["completion_source_url"]:
            errors.append(f"completion source contract mismatch: {item['completion_source_id']}")

    if ledger_after.get("changes", [])[:len(ledger_before.get("changes", []))] != ledger_before.get("changes", []):
        errors.append("historical change ledger entries changed")
    new_ledger = ledger_after.get("changes", [])[len(ledger_before.get("changes", [])):]
    if len(new_ledger) != 2 or {row.get("occurrence_id") for row in new_ledger} != set(TARGET_IDS):
        errors.append("new ledger entry scope mismatch")
    for row in new_ledger:
        if row.get("change_type") != "LIFECYCLE_AND_CERTAINTY_UPDATE" or row.get("new_values", {}).get("lifecycle_status") != "COMPLETED":
            errors.append(f"ledger lifecycle contract mismatch: {row.get('occurrence_id')}")

    registry_validation = validate_registry(canonical_after, sources_after)
    errors.extend(f"canonical validation: {e}" for e in registry_validation.errors)
    errors.extend(f"biosecurity validation: {e}" for e in validate_biosecurity_overlay(canonical_after, overlay_after))
    analysis_validation = validate_analysis(analysis_schema, evidence, reviews, canonical_after)
    errors.extend(f"Analysis validation: {e}" for e in analysis_validation.errors)

    readiness = analysis_population_readiness(analysis_schema, reviews, canonical_after)
    if readiness["eligible_completed_occurrence_count"] != post["eligible_completed_occurrence_count"]:
        errors.append(f"eligible completed post-count mismatch: {readiness}")
    if readiness["reviewed_occurrence_count"] != post["reviewed_occurrence_count"]:
        errors.append("reviewed count changed")
    east_completed = sum(1 for row in canonical_after.get("records", []) if row.get("region") == "East Asia" and row.get("lifecycle_status") == "COMPLETED")
    if east_completed != post["east_asia_completed_occurrence_count"]:
        errors.append(f"East Asia completed count mismatch: {east_completed}")

    if errors:
        raise SystemExit("Z POSTCONDITION FAILED:\n- " + "\n- ".join(errors))


def audit_markdown(plan: dict, canonical: dict, sources: dict, ledger: dict, overlay: dict, protected_hashes: dict[str, str]) -> str:
    post = plan["postconditions"]
    lines = [
        "# WORLD SIGNALS — East Asia lifecycle repair Z transaction audit v0.1",
        "",
        f"**Transaction date:** {plan['reference_date']}  ",
        f"**Canonical post-state:** v{post['canonical_registry_version']} / {post['canonical_record_count']}  ",
        f"**Source post-state:** v{post['source_registry_version']} / {post['source_record_count']}  ",
        f"**Change-ledger post-state:** v{post['change_ledger_version']} / {post['change_ledger_count']}  ",
        "",
        "## Repaired stable occurrences",
        "",
        "- `WSO-FIS-A-0015` — Japan 30-year JGB auction — `PLANNED → COMPLETED` from official MOF auction-result evidence.",
        "- `WSO-MAC-B-0041` — Japan Family Income and Expenditure Survey — July 2026 — `PLANNED → COMPLETED` from official Statistics Bureau release/result evidence.",
        "",
        "No new occurrence or series identity is created. Original schedule source IDs, dates, Asia/Tokyo timezone, day precision, null UTC values and certainty remain unchanged.",
        "",
        "## Supporting completion sources",
        "",
        "- `WSSRC-FIS-028` — MOF 30-year JGB auction result endpoint — supporting completion provenance only — primary canonical dependency count 0.",
        "- `WSSRC-MAC-029` — Statistics Bureau Family Income and Expenditure Survey result endpoint — supporting completion provenance only — primary canonical dependency count 0.",
        "",
        "## Analytical population effect",
        "",
        f"- eligible completed occurrences: **{post['eligible_completed_occurrence_count']}**",
        f"- reviewed completed occurrences: **{post['reviewed_occurrence_count']}**",
        f"- completed East Asia occurrences: **{post['east_asia_completed_occurrence_count']}**",
        "- Analysis schema/reviews/evidence are unchanged.",
        "- South Korea local elections are not added by this transaction.",
        "",
        "## Protected-file SHA-256",
        "",
    ]
    lines.extend(f"- {name}: `{value}`" for name, value in protected_hashes.items())
    lines.extend([
        "",
        "Completion is based on first-party post-event evidence, never elapsed time alone. Biosecurity overlay semantic content is unchanged; only its canonical checkpoint/version advances.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    plan = load(PLAN_PATH)
    canonical = load(CANONICAL_PATH)
    canonical_schema = load(CANONICAL_SCHEMA_PATH)
    sources = load(SOURCE_PATH)
    ledger = load(LEDGER_PATH)
    overlay = load(OVERLAY_PATH)
    analysis_schema = load(ANALYSIS_SCHEMA_PATH)
    reviews = load(ANALYSIS_REVIEWS_PATH)
    evidence = load(ANALYSIS_EVIDENCE_PATH)

    committed_at = transaction_time()
    post_canonical, post_sources, post_ledger, post_overlay = build_post_state(
        canonical, canonical_schema, sources, ledger, overlay, analysis_schema, reviews, evidence, plan, committed_at
    )

    if not args.apply:
        print(json.dumps({
            "transaction": plan["transaction"],
            "mode": "CHECK_ONLY",
            "post": plan["postconditions"],
            "completion_assertions": {item["occurrence_id"]: assertion_id(item) for item in plan["repairs"]},
            "change_ids": {item["occurrence_id"]: change_id(item) for item in plan["repairs"]},
        }, indent=2))
        return

    if os.environ.get(APPLY_ENV) != APPLY_VALUE:
        raise SystemExit(f"APPLY BLOCKED: set {APPLY_ENV}={APPLY_VALUE}")

    protected_paths = {
        "canonical_schema": CANONICAL_SCHEMA_PATH,
        "monitor_expectations": EXPECTATIONS_PATH,
        "monitor_operations_policy": OPERATIONS_PATH,
        "analysis_schema": ANALYSIS_SCHEMA_PATH,
        "analysis_reviews": ANALYSIS_REVIEWS_PATH,
        "analysis_evidence": ANALYSIS_EVIDENCE_PATH,
    }
    before_hashes = {name: sha(path) for name, path in protected_paths.items()}

    dump(CANONICAL_PATH, post_canonical)
    dump(SOURCE_PATH, post_sources)
    dump(LEDGER_PATH, post_ledger)
    dump(OVERLAY_PATH, post_overlay)

    after_hashes = {name: sha(path) for name, path in protected_paths.items()}
    if before_hashes != after_hashes:
        raise SystemExit("Z MUTATION BOUNDARY FAILED: protected file changed")

    AUDIT_PATH.write_text(audit_markdown(plan, post_canonical, post_sources, post_ledger, post_overlay, after_hashes), encoding="utf-8")
    print(f"Applied {plan['transaction']} and wrote {AUDIT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
