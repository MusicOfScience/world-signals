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

PLAN_PATH = ROOT / "data/coverage/P1_BALANCED_GOVERNANCE_C_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"

APPLY_ENV = "WORLD_SIGNALS_ALLOW_P1_BALANCED_GOVERNANCE_C_APPLY"
APPLY_VALUE = "YES"
MALAYSIA_OID = "WSO-REG-A-0014"
SELECTED_SOURCES = (
    "WSSRC-REGJ-002",
    "WSSRC-RISK-001",
    "WSSRC-REG2-004",
    "WSSRC-HEALTH-004",
    "WSSRC-REG-009",
    "WSSRC-INT-018",
    "WSSRC-COM-005",
)

TIMING_AND_IDENTITY_FIELDS = (
    "occurrence_id",
    "series_id",
    "source_id",
    "source_timezone",
    "start_local",
    "end_local",
    "start_utc",
    "end_utc",
    "date_earliest",
    "date_latest",
    "publication_datetime",
    "timing_type",
    "time_precision",
    "certainty_status",
    "lifecycle_status",
    "primary_source_assertion_id",
    "last_successful_assertion_id",
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _records(registry: dict) -> dict[str, dict]:
    return {row.get("occurrence_id"): row for row in registry.get("records", [])}


def _sources(registry: dict) -> dict[str, dict]:
    return {row.get("source_id"): row for row in registry.get("sources", [])}


def _dep_count(canonical: dict, source_id: str) -> int:
    return sum(1 for row in canonical.get("records", []) if row.get("source_id") == source_id)


def _overlay_checkpoint(overlay: dict) -> tuple[object, object]:
    checkpoint = overlay.get("canonical_checkpoint") or {}
    return checkpoint.get("registry_version"), checkpoint.get("record_count")


def _exact(row: dict, expected: dict, label: str, errors: list[str]) -> None:
    for key, value in expected.items():
        if row.get(key) != value:
            errors.append(f"{label} {key}: expected {value!r}, found {row.get(key)!r}")


def _identity_timing_snapshot(row: dict) -> dict:
    return {key: copy.deepcopy(row.get(key)) for key in TIMING_AND_IDENTITY_FIELDS}


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
    for sid, baseline in p["source_baselines"].items():
        row = by_source.get(sid)
        if row is None:
            errors.append(f"required source missing: {sid}")
            continue
        if row.get("authoritative_url") != baseline["authoritative_url"]:
            errors.append(f"source {sid} authoritative_url drifted")
        if _dep_count(canonical, sid) != baseline["derived_dependency_count"]:
            errors.append(f"source {sid} derived dependency count drifted")
        for key in ("canonical_provenance_use", "automated_monitoring_use", "verification_mode"):
            if row.get(key) is not None:
                errors.append(f"source {sid} {key} is no longer missing")

    malaysia = _records(canonical).get(MALAYSIA_OID)
    if malaysia is None:
        errors.append("Malaysia occurrence missing")
    else:
        baseline = p["malaysia_occurrence"]
        _exact(malaysia, {k: v for k, v in baseline.items() if k != "occurrence_id"}, "Malaysia baseline", errors)

    planned_ids = {entry["change_id"] for entry in plan["ledger_entries"]}
    existing_ids = {entry.get("change_id") for entry in ledger.get("changes", [])}
    overlap = planned_ids & existing_ids
    if overlap:
        errors.append(f"planned ledger entry already exists: {sorted(overlap)}")

    if errors:
        raise SystemExit("P1 BALANCED GOVERNANCE C PRECONDITION FAILED:\n- " + "\n- ".join(errors))


def build_post_state(canonical: dict, sources: dict, ledger: dict, overlay: dict, expectations: dict, plan: dict, *, committed_at: str) -> tuple[dict, dict, dict, dict, dict]:
    preflight(canonical, sources, ledger, overlay, expectations, plan)

    canonical_out = copy.deepcopy(canonical)
    sources_out = copy.deepcopy(sources)
    ledger_out = copy.deepcopy(ledger)
    overlay_out = copy.deepcopy(overlay)

    before_records = _records(canonical)
    after_records = _records(canonical_out)
    malaysia_spec = plan["canonical_updates"][MALAYSIA_OID]
    after_records[MALAYSIA_OID].update(copy.deepcopy(malaysia_spec["set"]))
    canonical_out["version"] = plan["postconditions"]["canonical_registry_version"]
    canonical_out["reference_date"] = plan["review_date"]

    by_source = _sources(sources_out)
    for sid, fields in plan["source_updates"].items():
        by_source[sid].update(copy.deepcopy(fields))
    sources_out["version"] = plan["postconditions"]["source_registry_version"]
    sources_out["reference_date"] = plan["review_date"]

    frozen = copy.deepcopy(plan["ledger_entries"][0])
    before = before_records[MALAYSIA_OID]
    after = after_records[MALAYSIA_OID]
    changed_keys = list(malaysia_spec["set"].keys())
    frozen["old_values"] = {key: copy.deepcopy(before.get(key)) for key in changed_keys}
    frozen["new_values"] = {key: copy.deepcopy(after.get(key)) for key in changed_keys}
    frozen["source_assertion_id"] = after.get("primary_source_assertion_id")
    frozen["review_basis"] = [
        "Malaysia Ministry of Finance Pre-Budget Statement 2027 explicitly announces tabling on 9 October 2026.",
        "The source establishes an authoritatively scheduled policy milestone, not an independently established statutory deadline.",
        "The 9 October civil date, certainty status, source identity and assertion identity remain unchanged.",
        "Automatic canonical commit and Google Calendar writes remain disabled."
    ]
    frozen["registry_version_before"] = plan["preconditions"]["canonical_registry_version"]
    frozen["registry_version_after"] = plan["postconditions"]["canonical_registry_version"]
    frozen["canonical_mutation_committed"] = True
    frozen["committed_at"] = committed_at
    ledger_out["changes"].append(frozen)
    ledger_out["version"] = plan["postconditions"]["change_ledger_version"]
    ledger_out["reference_date"] = plan["review_date"]

    overlay_out["canonical_checkpoint"]["registry_version"] = plan["postconditions"]["biosecurity_overlay_registry_version"]
    overlay_out["canonical_checkpoint"]["record_count"] = plan["postconditions"]["biosecurity_overlay_record_count"]

    report = validate_post_state(
        canonical, sources, ledger, overlay,
        canonical_out, sources_out, ledger_out, overlay_out,
        expectations, plan,
    )
    return canonical_out, sources_out, ledger_out, overlay_out, report


def validate_post_state(
    canonical_before: dict,
    sources_before: dict,
    ledger_before: dict,
    overlay_before: dict,
    canonical_after: dict,
    sources_after: dict,
    ledger_after: dict,
    overlay_after: dict,
    expectations: dict,
    plan: dict,
) -> dict:
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
        errors.append(f"unexpected canonical changed occurrences: {changed_occurrences}")

    malaysia_before = before_records[MALAYSIA_OID]
    malaysia_after = after_records[MALAYSIA_OID]
    if _identity_timing_snapshot(malaysia_before) != _identity_timing_snapshot(malaysia_after):
        errors.append("Malaysia timing/identity/assertion fields changed")
    _exact(
        malaysia_after,
        {
            "start_local": "2026-10-09",
            "certainty_status": "CONFIRMED",
            "population_horizon_policy": "EXACT_LEGAL_OR_POLICY_MILESTONE_ONLY",
        },
        "Malaysia post-state",
        errors,
    )

    before_sources = _sources(sources_before)
    after_sources = _sources(sources_after)
    if list(before_sources) != list(after_sources):
        errors.append("source identity/order changed")
    changed_sources = [sid for sid in before_sources if before_sources[sid] != after_sources[sid]]
    if set(changed_sources) != set(post["expected_changed_sources"]) or len(changed_sources) != len(post["expected_changed_sources"]):
        errors.append(f"unexpected changed source set: {changed_sources}")
    for sid, fields in plan["source_updates"].items():
        _exact(after_sources[sid], fields, f"source post-state {sid}", errors)

    # Primary source dependencies remain exactly unchanged in this governance transaction.
    for sid, baseline in plan["preconditions"]["source_baselines"].items():
        if _dep_count(canonical_after, sid) != baseline["derived_dependency_count"]:
            errors.append(f"source dependency count changed: {sid}")

    # Selected canonical contracts are protected explicitly.
    protected = {
        "WSO-REG-J-0006": {"start_local": "2026-09-30"},
        "WSO-REG-J-0007": {"start_local": "2026-11-20"},
        "WSO-COM-A-0051": {"date_earliest": "2026-11-01", "date_latest": "2027-04-30"},
        "WSO-COM-A-0052": {"date_earliest": "2027-11-01", "date_latest": "2028-04-30"},
        "WSO-REG-B-0005": {"start_local": "2026-11-16"},
        "WSO-REG-B-0006": {"start_local": "2026-11-17"},
        "WSO-HEALTH-A-0005": {"start_local": "2026-10-19", "end_local": "2026-10-22"},
        "WSO-INT-A-0014": {"start_local": "2027-05-24", "end_local": "2027-05-28", "certainty_status": "PROVISIONAL"},
    }
    for oid, expected in protected.items():
        row = after_records.get(oid)
        if row is None:
            errors.append(f"protected occurrence missing: {oid}")
        else:
            _exact(row, expected, f"protected occurrence {oid}", errors)
            if before_records[oid] != row:
                errors.append(f"protected occurrence mutated: {oid}")

    # Every USDA dependency remains byte-identical.
    for oid, row in before_records.items():
        if row.get("source_id") == "WSSRC-COM-005" and row != after_records[oid]:
            errors.append(f"USDA canonical dependency mutated: {oid}")

    # Historical/global invariants.
    _exact(after_records["WSO-EL-A-0004"], {"start_local": "2027-01-05"}, "Brazil inauguration", errors)
    india = after_records["WSO-FIS-B-0011"]
    _exact(india, {"start_local": None, "date_earliest": None, "date_latest": None, "certainty_status": "TBC"}, "India Budget", errors)
    _exact(after_records["WSO-INT-A-0018"], {"date_earliest": "2027-05-01", "date_latest": "2027-05-31", "time_precision": "MONTH"}, "ASEAN 50", errors)
    _exact(after_records["WSO-INT-A-0019"], {"date_earliest": "2027-11-01", "date_latest": "2027-11-30", "time_precision": "MONTH"}, "ASEAN 51", errors)
    if not {"WSSRC-REG4-001", "WSSRC-REG4-002"}.issubset(set(after_sources)):
        errors.append("Colombia split invariant failed")

    historical_changes = ledger_before.get("changes", [])
    if ledger_after.get("changes", [])[:len(historical_changes)] != historical_changes:
        errors.append("historical ledger changed")
    added = ledger_after.get("changes", [])[len(historical_changes):]
    if len(added) != 1 or added[0].get("change_id") != plan["ledger_entries"][0]["change_id"]:
        errors.append("ledger did not gain exactly the frozen Malaysia semantic entry")
    elif not added[0].get("committed_at"):
        errors.append("Malaysia ledger committed_at missing")

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

    if errors:
        raise ValueError("P1 BALANCED GOVERNANCE C POST-STATE INVALID:\n- " + "\n- ".join(errors))

    return {
        "status": "PASS",
        "canonical_version": canonical_after.get("version"),
        "canonical_count": len(canonical_after.get("records", [])),
        "source_version": sources_after.get("version"),
        "source_count": len(sources_after.get("sources", [])),
        "ledger_version": ledger_after.get("version"),
        "changed_occurrences": changed_occurrences,
        "changed_sources": changed_sources,
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

    canonical_out, sources_out, ledger_out, overlay_out, report = build_post_state(
        canonical, sources, ledger, overlay, expectations, plan, committed_at=committed_at
    )

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
