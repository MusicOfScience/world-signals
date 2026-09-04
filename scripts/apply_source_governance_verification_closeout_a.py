#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.source_governance_audit import build_source_governance_audit
from world_signals.validation import validate_registry

PLAN_PATH = ROOT / "data/coverage/SOURCE_GOVERNANCE_VERIFICATION_CLOSEOUT_A_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
LIVE_RUNNER_PATH = ROOT / "scripts/run_live_monitor.py"

APPLY_ENV = "WORLD_SIGNALS_ALLOW_VERIFICATION_CLOSEOUT_A_APPLY"
APPLY_VALUE = "YES"
ABSENT = "ABSENT"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sources_by_id(registry: dict) -> dict[str, dict]:
    return {row.get("source_id"): row for row in registry.get("sources", [])}


def canonical_counts(canonical: dict) -> Counter:
    return Counter(r.get("source_id") for r in canonical.get("records", []) if r.get("source_id"))


def _expect_field(row: dict, key: str, expected, errors: list[str], source_id: str) -> None:
    if expected == ABSENT:
        if key in row:
            errors.append(f"{source_id} expected {key} absent, found {row.get(key)!r}")
    elif row.get(key) != expected:
        errors.append(f"{source_id} {key} changed: expected {expected!r}, found {row.get(key)!r}")


def preflight(canonical: dict, source_registry: dict, expectations: dict, plan: dict) -> None:
    p = plan["preconditions"]
    errors: list[str] = []

    if str(canonical.get("version")) != str(p["canonical_registry_version"]):
        errors.append("canonical version precondition failed")
    if canonical.get("record_count") != p["canonical_record_count"] or len(canonical.get("records", [])) != p["canonical_record_count"]:
        errors.append("canonical record-count precondition failed")
    if str(source_registry.get("version")) != str(p["source_registry_version"]):
        errors.append("source version precondition failed")
    if len(source_registry.get("sources", [])) != p["source_count"]:
        errors.append("source count precondition failed")
    if str(expectations.get("version")) != str(p["monitor_expectations_version"]):
        errors.append("monitor expectations version precondition failed")
    if expectations.get("automatic_canonical_commit") is not False:
        errors.append("automatic canonical commit must remain false")
    if expectations.get("google_calendar_write") is not False:
        errors.append("Google Calendar write must remain false")

    selected = set(plan["selection"]["selected_source_ids"])
    updates = set(plan["source_updates"])
    frozen = set(p["selected_actual_canonical_dependency_counts"])
    if not (selected == updates == frozen):
        errors.append("selected/update/frozen source sets differ")
    if sum(p["selected_actual_canonical_dependency_counts"].values()) != plan["selection"]["canonical_dependency_total"]:
        errors.append("selected canonical dependency total mismatch")

    by_id = sources_by_id(source_registry)
    counts = canonical_counts(canonical)
    existing = p["selected_existing_governance"]
    absent_fields = p["selected_fields_must_be_absent"]

    for source_id, expected_count in p["selected_actual_canonical_dependency_counts"].items():
        row = by_id.get(source_id)
        if row is None:
            errors.append(f"selected source missing: {source_id}")
            continue
        if counts.get(source_id, 0) != expected_count:
            errors.append(f"{source_id} canonical-derived dependency count changed")
        spec = existing[source_id]
        for key in [
            "canonical_provenance_use",
            "automated_monitoring_use",
            "monitoring_readiness_status",
            "monitoring_activation_status",
        ]:
            _expect_field(row, key, spec[key], errors, source_id)
        _expect_field(row, "canonical_dependency_count", spec["stored_canonical_dependency_count"], errors, source_id)
        for field in absent_fields:
            if field in row:
                errors.append(f"{source_id} {field} already populated; refusing replay")

    hold = p["vietnam_hold"]
    vietnam = by_id.get(hold["source_id"])
    if vietnam is None:
        errors.append("Vietnam held source missing")
    else:
        if vietnam.get("authoritative_url") != hold["expected_authoritative_url"]:
            errors.append("Vietnam held source scope changed; re-review before closeout")
        if counts.get(hold["source_id"], 0) != hold["expected_actual_canonical_dependency_count"]:
            errors.append("Vietnam canonical dependency count changed")
        if vietnam.get("verification_mode") not in (None, ""):
            errors.append("Vietnam held source unexpectedly gained verification_mode")

    audit = build_source_governance_audit(canonical, source_registry, expectations)
    queue = {row["source_id"]: row for row in audit["backfill_research_queue"]}
    for source_id in selected:
        row = queue.get(source_id)
        if row is None:
            errors.append(f"{source_id} not present in source-governance research queue")
        elif row.get("research_priority") != "P1_CANONICAL_DEPENDENCY" or row.get("missing_governance_fields") != ["verification_mode"]:
            errors.append(f"{source_id} no longer verification-only P1")

    if errors:
        raise SystemExit("VERIFICATION CLOSEOUT A PRECONDITION FAILED:\n- " + "\n- ".join(errors))


def changed_source_ids(before: dict, after: dict) -> list[str]:
    b = sources_by_id(before)
    a = sources_by_id(after)
    return sorted(sid for sid in set(b) | set(a) if b.get(sid) != a.get(sid))


def _audit_metrics(canonical: dict, sources: dict, expectations: dict) -> dict:
    audit = build_source_governance_audit(canonical, sources, expectations)
    totals = audit["totals"]
    priorities = totals["backfill_research_priority_counts"]
    missing = totals["missing_field_counts"]
    return {
        "fully_explicit_governance_sources": totals["fully_explicit_governance_source_count"],
        "sources_missing_any_governance_field": totals["source_records_with_one_or_more_missing_governance_fields"],
        "p1_canonical_dependent": priorities.get("P1_CANONICAL_DEPENDENCY", 0),
        "p2_registry_only": priorities.get("P2_REGISTRY_ONLY", 0),
        "missing_canonical_provenance_use": missing.get("canonical_provenance_use", 0),
        "missing_automated_monitoring_use": missing.get("automated_monitoring_use", 0),
        "missing_verification_mode": missing.get("verification_mode", 0),
    }


def validate_post_state(canonical: dict, before_registry: dict, after_registry: dict, expectations: dict, plan: dict) -> dict:
    post = plan["postconditions"]
    errors: list[str] = []

    if str(canonical.get("version")) != str(post["canonical_registry_version"]):
        errors.append("canonical version changed")
    if canonical.get("record_count") != post["canonical_record_count"] or len(canonical.get("records", [])) != post["canonical_record_count"]:
        errors.append("canonical count changed")
    if str(after_registry.get("version")) != str(post["source_registry_version"]):
        errors.append("post source version mismatch")
    if len(after_registry.get("sources", [])) != post["source_count"]:
        errors.append("post source count changed")

    before_ids = [r.get("source_id") for r in before_registry.get("sources", [])]
    after_ids = [r.get("source_id") for r in after_registry.get("sources", [])]
    if before_ids != after_ids or len(after_ids) != len(set(after_ids)):
        errors.append("source identity/order changed")

    actual_changed = changed_source_ids(before_registry, after_registry)
    if actual_changed != sorted(post["changed_source_ids"]):
        errors.append(f"changed source ids differ: {actual_changed}")

    before = sources_by_id(before_registry)
    after = sources_by_id(after_registry)
    for source_id, spec in plan["source_updates"].items():
        for field, value in spec["set"].items():
            if after[source_id].get(field) != value:
                errors.append(f"{source_id} {field} postcondition mismatch")
        allowed = set(spec["set"])
        all_keys = set(before[source_id]) | set(after[source_id])
        for key in all_keys - allowed:
            if after[source_id].get(key) != before[source_id].get(key) or (key in after[source_id]) != (key in before[source_id]):
                errors.append(f"{source_id} non-closeout field changed: {key}")

    hold_id = plan["preconditions"]["vietnam_hold"]["source_id"]
    if after.get(hold_id) != before.get(hold_id):
        errors.append("Vietnam held source changed")

    counts = canonical_counts(canonical)
    helper_mismatches = []
    for row in after_registry.get("sources", []):
        if "canonical_dependency_count" in row:
            expected = counts.get(row.get("source_id"), 0)
            if row.get("canonical_dependency_count") != expected:
                helper_mismatches.append((row.get("source_id"), row.get("canonical_dependency_count"), expected))
    if helper_mismatches:
        errors.append(f"stored dependency helper mismatch remains: {helper_mismatches}")

    if str(expectations.get("version")) != str(post["monitor_expectations_version"]):
        errors.append("monitor expectations changed")
    if expectations.get("automatic_canonical_commit") is not post["automatic_canonical_commit"]:
        errors.append("automatic canonical commit changed")
    if expectations.get("google_calendar_write") is not post["google_calendar_write"]:
        errors.append("Google Calendar write changed")

    actual_audit = _audit_metrics(canonical, after_registry, expectations)
    if actual_audit != post["expected_governance_audit"]:
        errors.append(f"post-governance audit differs: {actual_audit}")

    validation = validate_registry(canonical, after_registry)
    errors.extend(validation.errors)
    if errors:
        raise ValueError("VERIFICATION CLOSEOUT A POSTCONDITION FAILED:\n- " + "\n- ".join(errors))

    return {
        "project": "WORLD SIGNALS",
        "transaction": "SOURCE_GOVERNANCE_VERIFICATION_CLOSEOUT_A",
        "status": "PASS",
        "canonical_registry_version": canonical.get("version"),
        "canonical_record_count": canonical.get("record_count"),
        "source_registry_version_before": before_registry.get("version"),
        "source_registry_version_after": after_registry.get("version"),
        "source_count": len(after_registry.get("sources", [])),
        "changed_source_ids": actual_changed,
        "vietnam_held_unchanged": True,
        "dependency_helper_integrity": True,
        "governance_audit": actual_audit,
        "monitor_expectations_version": expectations.get("version"),
        "automatic_canonical_commit": expectations.get("automatic_canonical_commit"),
        "google_calendar_write": expectations.get("google_calendar_write"),
    }


def build_post_state(canonical: dict, source_registry: dict, expectations: dict, plan: dict) -> tuple[dict, dict]:
    out = copy.deepcopy(source_registry)
    by_id = sources_by_id(out)
    for source_id, spec in plan["source_updates"].items():
        by_id[source_id].update(copy.deepcopy(spec["set"]))
    out["version"] = plan["postconditions"]["source_registry_version"]
    out["reference_date"] = plan["review_date"]
    return out, validate_post_state(canonical, source_registry, out, expectations, plan)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check or apply guarded WORLD SIGNALS Verification Closeout A. Default is read-only simulation."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help=f"write data/sources/registry.json only; requires {APPLY_ENV}={APPLY_VALUE}",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    canonical_raw = CANONICAL_PATH.read_bytes()
    sources_raw = SOURCES_PATH.read_bytes()
    expectations_raw = EXPECTATIONS_PATH.read_bytes()
    ledger_raw = LEDGER_PATH.read_bytes()
    live_runner_raw = LIVE_RUNNER_PATH.read_bytes()

    canonical = json.loads(canonical_raw)
    sources = json.loads(sources_raw)
    expectations = json.loads(expectations_raw)
    plan = load(PLAN_PATH)

    preflight(canonical, sources, expectations, plan)
    post_sources, report = build_post_state(canonical, sources, expectations, plan)
    report.update({
        "mode": "APPLY" if args.apply else "READ_ONLY_PREFLIGHT",
        "canonical_sha256_before": stable_hash(canonical_raw),
        "source_registry_sha256_before": stable_hash(sources_raw),
        "monitor_expectations_sha256_before": stable_hash(expectations_raw),
        "change_ledger_sha256_before": stable_hash(ledger_raw),
        "live_monitor_runner_sha256_before": stable_hash(live_runner_raw),
    })

    if args.apply:
        if os.environ.get(APPLY_ENV) != APPLY_VALUE:
            raise SystemExit(f"VERIFICATION CLOSEOUT A APPLY REFUSED: set {APPLY_ENV}={APPLY_VALUE} after reviewed approval")
        SOURCES_PATH.write_text(json.dumps(post_sources, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if CANONICAL_PATH.read_bytes() != canonical_raw:
            raise SystemExit("APPLY FAILED CLOSED: canonical registry bytes changed")
        if EXPECTATIONS_PATH.read_bytes() != expectations_raw:
            raise SystemExit("APPLY FAILED CLOSED: monitor expectations bytes changed")
        if LEDGER_PATH.read_bytes() != ledger_raw:
            raise SystemExit("APPLY FAILED CLOSED: change ledger bytes changed")
        if LIVE_RUNNER_PATH.read_bytes() != live_runner_raw:
            raise SystemExit("APPLY FAILED CLOSED: live monitor runner bytes changed")
        validate_post_state(canonical, sources, load(SOURCES_PATH), expectations, plan)
        report["source_registry_sha256_after"] = stable_hash(SOURCES_PATH.read_bytes())

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
