#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
from datetime import datetime
import json
import os
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.source_governance_audit import build_source_governance_audit
from world_signals.validation import validate_registry

PLAN_PATH = ROOT / "data/coverage/P1_SOURCE_SCOPE_LIFECYCLE_B_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"

APPLY_ENV = "WORLD_SIGNALS_ALLOW_P1_SOURCE_SCOPE_LIFECYCLE_B_APPLY"
APPLY_VALUE = "YES"

SELECTED_SOURCES = (
    "WSSRC-MAC-021",
    "WSSRC-REG2-005",
    "WSSRC-REG-005",
    "WSSRC-EL-ZA-001",
    "WSSRC-INT-021",
    "WSSRC-FIS-023",
)
NEW_SOURCE = "WSSRC-FIS-025"
ASEAN_OCCURRENCES = ("WSO-INT-A-0018", "WSO-INT-A-0019")
UNCHANGED_TIMING_OCCURRENCES = ("WSO-REG-B-0007", "WSO-REG-A-0008", "WSO-FIS-B-0011")

TIMING_FIELDS = (
    "start_local",
    "end_local",
    "start_utc",
    "end_utc",
    "date_earliest",
    "date_latest",
    "publication_datetime",
    "timing_type",
    "time_precision",
    "all_day_semantics",
    "source_timezone",
)
ASSERTION_FIELDS = (
    "primary_source_assertion_id",
    "last_successful_assertion_id",
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _sources(registry: dict) -> dict[str, dict]:
    return {row.get("source_id"): row for row in registry.get("sources", [])}


def _records(registry: dict) -> dict[str, dict]:
    return {row.get("occurrence_id"): row for row in registry.get("records", [])}


def _dep_count(canonical: dict, source_id: str) -> int:
    return sum(1 for row in canonical.get("records", []) if row.get("source_id") == source_id)


def _exact(row: dict, expected: dict, label: str, errors: list[str]) -> None:
    for key, value in expected.items():
        if row.get(key) != value:
            errors.append(f"{label} {key}: expected {value!r}, found {row.get(key)!r}")


def _timing(row: dict) -> dict:
    return {key: row.get(key) for key in TIMING_FIELDS}


def _overlay_checkpoint(overlay: dict) -> tuple[object, object]:
    c = overlay.get("canonical_checkpoint") or {}
    return c.get("registry_version"), c.get("record_count")


def preflight(canonical: dict, sources: dict, ledger: dict, overlay: dict, expectations: dict, plan: dict) -> None:
    p = plan["preconditions"]
    errors: list[str] = []

    if str(canonical.get("version")) != str(p["canonical_registry_version"]):
        errors.append("canonical version precondition failed")
    if len(canonical.get("records", [])) != p["canonical_record_count"] or canonical.get("record_count") != p["canonical_record_count"]:
        errors.append("canonical count precondition failed")
    if str(sources.get("version")) != str(p["source_registry_version"]):
        errors.append("source version precondition failed")
    if len(sources.get("sources", [])) != p["source_count"]:
        errors.append("source count precondition failed")
    if str(ledger.get("version")) != str(p["change_ledger_version"]):
        errors.append("ledger version precondition failed")
    if str(expectations.get("version")) != str(p["monitor_expectations_version"]):
        errors.append("monitor expectations version precondition failed")
    if expectations.get("automatic_canonical_commit") is not False:
        errors.append("automatic_canonical_commit must remain false")
    if expectations.get("google_calendar_write") is not False:
        errors.append("google_calendar_write must remain false")
    if _overlay_checkpoint(overlay) != (p["biosecurity_overlay_registry_version"], p["biosecurity_overlay_record_count"]):
        errors.append("biosecurity overlay checkpoint precondition failed")

    by_source = _sources(sources)
    if NEW_SOURCE in by_source:
        errors.append(f"new source already exists: {NEW_SOURCE}")
    for sid, baseline in p["source_baselines"].items():
        row = by_source.get(sid)
        if row is None:
            errors.append(f"required source missing: {sid}")
            continue
        _exact(row, {"authoritative_url": baseline["authoritative_url"], "source_type": baseline["source_type"]}, f"source {sid}", errors)
        if _dep_count(canonical, sid) != baseline["derived_dependency_count"]:
            errors.append(f"source {sid} derived dependency count drifted")
        for key in ("canonical_provenance_use", "automated_monitoring_use", "verification_mode"):
            if row.get(key) is not None:
                errors.append(f"source {sid} {key} is no longer missing")

    by_record = _records(canonical)
    for oid, baseline in p["canonical_baselines"].items():
        row = by_record.get(oid)
        if row is None:
            errors.append(f"required occurrence missing: {oid}")
            continue
        _exact(row, baseline, f"occurrence {oid}", errors)

    planned_change_ids = {x["change_id"] for x in plan["ledger_entries"]}
    existing_change_ids = {x.get("change_id") for x in ledger.get("changes", [])}
    overlap = planned_change_ids & existing_change_ids
    if overlap:
        errors.append(f"planned ledger entries already exist: {sorted(overlap)}")

    if errors:
        raise SystemExit("P1 SOURCE SCOPE/LIFECYCLE B PRECONDITION FAILED:\n- " + "\n- ".join(errors))


def build_post_state(canonical: dict, sources: dict, ledger: dict, overlay: dict, expectations: dict, plan: dict, *, committed_at: str) -> tuple[dict, dict, dict, dict, dict]:
    preflight(canonical, sources, ledger, overlay, expectations, plan)

    canonical_out = copy.deepcopy(canonical)
    sources_out = copy.deepcopy(sources)
    ledger_out = copy.deepcopy(ledger)
    overlay_out = copy.deepcopy(overlay)

    before_records = _records(canonical)
    after_records = _records(canonical_out)

    for oid, spec in plan["canonical_updates"].items():
        row = after_records[oid]
        for key, value in spec.get("set", {}).items():
            row[key] = copy.deepcopy(value)
        if spec.get("append_status_history"):
            row.setdefault("status_history", []).append(copy.deepcopy(spec["append_status_history"]))

    canonical_out["version"] = plan["postconditions"]["canonical_registry_version"]
    canonical_out["reference_date"] = plan["review_date"]

    by_source = _sources(sources_out)
    for sid, fields in plan["source_updates"].items():
        by_source[sid].update(copy.deepcopy(fields))
    if len(plan["new_sources"]) != 1 or plan["new_sources"][0].get("source_id") != NEW_SOURCE:
        raise ValueError("plan must define exactly one WSSRC-FIS-025 source")
    sources_out["sources"].append(copy.deepcopy(plan["new_sources"][0]))
    sources_out["version"] = plan["postconditions"]["source_registry_version"]
    sources_out["reference_date"] = plan["review_date"]

    for frozen in plan["ledger_entries"]:
        oid = frozen["occurrence_id"]
        update = plan["canonical_updates"][oid]
        before = before_records[oid]
        after = after_records[oid]
        changed_keys = list(update.get("set", {}).keys())
        if update.get("append_status_history"):
            changed_keys.append("status_history")
        entry = copy.deepcopy(frozen)
        entry["old_values"] = {k: copy.deepcopy(before.get(k)) for k in changed_keys}
        entry["new_values"] = {k: copy.deepcopy(after.get(k)) for k in changed_keys}
        entry["source_assertion_id"] = after.get("primary_source_assertion_id")
        entry["review_basis"] = [
            "Primary/authoritative source scope and timing precision were re-audited on 2026-09-05.",
            "Stable occurrence identity is preserved; exact dates remain unchanged except that two previously unscheduled ASEAN occurrences gain month-only forecast bounds.",
            "Automatic canonical commit and Google Calendar writes remain disabled."
        ]
        entry["registry_version_before"] = plan["preconditions"]["canonical_registry_version"]
        entry["registry_version_after"] = plan["postconditions"]["canonical_registry_version"]
        entry["canonical_mutation_committed"] = True
        entry["committed_at"] = committed_at
        ledger_out["changes"].append(entry)
    ledger_out["version"] = plan["postconditions"]["change_ledger_version"]
    ledger_out["reference_date"] = plan["review_date"]

    overlay_out["canonical_checkpoint"]["registry_version"] = plan["postconditions"]["biosecurity_overlay_registry_version"]
    overlay_out["canonical_checkpoint"]["record_count"] = plan["postconditions"]["biosecurity_overlay_record_count"]

    report = validate_post_state(canonical, sources, ledger, overlay, canonical_out, sources_out, ledger_out, overlay_out, expectations, plan)
    return canonical_out, sources_out, ledger_out, overlay_out, report


def validate_post_state(canonical_before: dict, sources_before: dict, ledger_before: dict, overlay_before: dict, canonical_after: dict, sources_after: dict, ledger_after: dict, overlay_after: dict, expectations: dict, plan: dict) -> dict:
    post = plan["postconditions"]
    errors: list[str] = []

    if canonical_after.get("version") != post["canonical_registry_version"] or len(canonical_after.get("records", [])) != post["canonical_record_count"]:
        errors.append("canonical post-state version/count mismatch")
    if sources_after.get("version") != post["source_registry_version"] or len(sources_after.get("sources", [])) != post["source_count"]:
        errors.append("source post-state version/count mismatch")
    if ledger_after.get("version") != post["change_ledger_version"]:
        errors.append("ledger post-state version mismatch")
    if _overlay_checkpoint(overlay_after) != (post["biosecurity_overlay_registry_version"], post["biosecurity_overlay_record_count"]):
        errors.append("biosecurity overlay post-state mismatch")

    expected_overlay = copy.deepcopy(overlay_before)
    expected_overlay["canonical_checkpoint"]["registry_version"] = post["biosecurity_overlay_registry_version"]
    expected_overlay["canonical_checkpoint"]["record_count"] = post["biosecurity_overlay_record_count"]
    if overlay_after != expected_overlay:
        errors.append("biosecurity overlay changed outside canonical checkpoint")

    before_records = _records(canonical_before)
    after_records = _records(canonical_after)
    if list(before_records) != list(after_records):
        errors.append("canonical occurrence identity/order changed")
    changed_occurrences = [oid for oid in before_records if before_records[oid] != after_records[oid]]
    if changed_occurrences != post["expected_changed_occurrences"]:
        errors.append(f"unexpected canonical changes/order: {changed_occurrences}")

    for oid in UNCHANGED_TIMING_OCCURRENCES:
        if _timing(before_records[oid]) != _timing(after_records[oid]):
            errors.append(f"protected timing changed for {oid}")
        for key in ASSERTION_FIELDS:
            if before_records[oid].get(key) != after_records[oid].get(key):
                errors.append(f"assertion id changed for {oid}: {key}")

    expected_windows = {
        "WSO-INT-A-0018": ("2027-05-01", "2027-05-31"),
        "WSO-INT-A-0019": ("2027-11-01", "2027-11-30"),
    }
    for oid in ASEAN_OCCURRENCES:
        before = before_records[oid]
        after = after_records[oid]
        if after.get("start_local") is not None or after.get("end_local") is not None or after.get("start_utc") is not None or after.get("end_utc") is not None:
            errors.append(f"ASEAN exact date/time invented for {oid}")
        lo, hi = expected_windows[oid]
        _exact(after, {"date_earliest": lo, "date_latest": hi, "timing_type": "EXPECTED_DATE_WINDOW", "time_precision": "MONTH", "certainty_status": "PROVISIONAL", "time_status": "PROVISIONAL", "time_basis": "EXPLICIT_AUTHORITATIVE_MONTH"}, f"ASEAN post-state {oid}", errors)
        for key in ASSERTION_FIELDS:
            if before.get(key) != after.get(key):
                errors.append(f"ASEAN assertion id changed for {oid}: {key}")

    # India remains unscheduled; only authority/activation semantics change.
    india = after_records["WSO-FIS-B-0011"]
    _exact(india, {"start_local": None, "date_earliest": None, "date_latest": None, "timing_type": "UNSCHEDULED_TBC", "certainty_status": "TBC", "activation_mode": "AUTHORITATIVE_RECURRING_RULE", "legal_basis_source_id": NEW_SOURCE}, "India post-state", errors)

    # Legal boundary dates are immovable in this transaction.
    _exact(after_records["WSO-REG-B-0007"], {"start_local": "2026-09-15", "certainty_status": "CONFIRMED"}, "Argentina protected date", errors)
    _exact(after_records["WSO-REG-A-0008"], {"start_local": "2026-10-31", "certainty_status": "CONFIRMED"}, "Indonesia protected date", errors)

    before_sources = _sources(sources_before)
    after_sources = _sources(sources_after)
    before_ids = [x.get("source_id") for x in sources_before.get("sources", [])]
    after_ids = [x.get("source_id") for x in sources_after.get("sources", [])]
    if after_ids != before_ids + [NEW_SOURCE]:
        errors.append("source identity/order changed outside one appended India constitutional source")
    changed_existing = [sid for sid in before_ids if before_sources[sid] != after_sources[sid]]
    if changed_existing != post["expected_changed_existing_sources"]:
        errors.append(f"unexpected existing source changes/order: {changed_existing}")
    for sid, fields in plan["source_updates"].items():
        _exact(after_sources[sid], fields, f"source post-state {sid}", errors)
    _exact(after_sources[NEW_SOURCE], plan["new_sources"][0], "new India constitutional source", errors)

    expected_deps = {sid: plan["preconditions"]["source_baselines"][sid]["derived_dependency_count"] for sid in SELECTED_SOURCES}
    expected_deps[NEW_SOURCE] = 0  # legal_basis_source_id does not change primary-source dependency count
    actual_deps = {sid: _dep_count(canonical_after, sid) for sid in expected_deps}
    if actual_deps != expected_deps:
        errors.append(f"derived dependency mismatch: {actual_deps!r} != {expected_deps!r}")

    if ledger_after.get("changes", [])[:len(ledger_before.get("changes", []))] != ledger_before.get("changes", []):
        errors.append("historical ledger changed")
    added = ledger_after.get("changes", [])[len(ledger_before.get("changes", [])):]
    if len(added) != len(plan["ledger_entries"]):
        errors.append("ledger did not gain exactly five entries")
    else:
        frozen_ids = [x["change_id"] for x in plan["ledger_entries"]]
        if [x.get("change_id") for x in added] != frozen_ids:
            errors.append("ledger added-entry identity/order mismatch")
        if any(not x.get("committed_at") for x in added):
            errors.append("ledger committed_at missing")

    validation = validate_registry(canonical_after, sources_after)
    errors.extend(validation.errors)

    audit = build_source_governance_audit(canonical_after, sources_after, expectations)
    totals = audit["totals"]
    actual_gov = {
        "fully_explicit": totals["fully_explicit_governance_source_count"],
        "missing_any": totals["source_records_with_one_or_more_missing_governance_fields"],
        "p1_canonical_dependent": totals["backfill_research_priority_counts"].get("P1_CANONICAL_DEPENDENCY", 0),
        "p2_registry_only": totals["backfill_research_priority_counts"].get("P2_REGISTRY_ONLY", 0),
    }
    if actual_gov != post["governance_expected"]:
        errors.append(f"governance totals mismatch: {actual_gov!r} != {post['governance_expected']!r}")

    if expectations.get("automatic_canonical_commit") is not False:
        errors.append("automatic_canonical_commit not false")
    if expectations.get("google_calendar_write") is not False:
        errors.append("google_calendar_write not false")

    # Protected global invariants.
    brazil = after_records.get("WSO-EL-A-0004")
    if not brazil or brazil.get("start_local") != "2027-01-05":
        errors.append("Brazil inauguration invariant failed")
    after_source_ids = set(after_sources)
    if not {"WSSRC-REG4-001", "WSSRC-REG4-002"}.issubset(after_source_ids):
        errors.append("Colombia split invariant failed")

    if errors:
        raise ValueError("P1 SOURCE SCOPE/LIFECYCLE B POST-STATE INVALID:\n- " + "\n- ".join(errors))

    return {
        "status": "PASS",
        "canonical_version": canonical_after.get("version"),
        "canonical_count": len(canonical_after.get("records", [])),
        "source_version": sources_after.get("version"),
        "source_count": len(sources_after.get("sources", [])),
        "ledger_version": ledger_after.get("version"),
        "changed_occurrences": changed_occurrences,
        "changed_existing_sources": changed_existing,
        "new_source": NEW_SOURCE,
        "governance": actual_gov,
        "automatic_canonical_commit": expectations.get("automatic_canonical_commit"),
        "google_calendar_write": expectations.get("google_calendar_write"),
    }


def run(*, apply: bool, committed_at: str | None = None) -> dict:
    plan = load(PLAN_PATH)
    canonical = load(CANONICAL_PATH)
    sources = load(SOURCES_PATH)
    ledger = load(LEDGER_PATH)
    overlay = load(OVERLAY_PATH)
    expectations = load(EXPECTATIONS_PATH)

    if committed_at is None:
        committed_at = datetime.now(ZoneInfo("Australia/Melbourne")).isoformat(timespec="seconds")

    canonical_out, sources_out, ledger_out, overlay_out, report = build_post_state(canonical, sources, ledger, overlay, expectations, plan, committed_at=committed_at)

    if apply:
        if os.environ.get(APPLY_ENV) != APPLY_VALUE:
            raise SystemExit(f"apply refused: set {APPLY_ENV}={APPLY_VALUE}")
        dump(CANONICAL_PATH, canonical_out)
        dump(SOURCES_PATH, sources_out)
        dump(LEDGER_PATH, ledger_out)
        dump(OVERLAY_PATH, overlay_out)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--committed-at")
    args = parser.parse_args()
    report = run(apply=args.apply, committed_at=args.committed_at)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
