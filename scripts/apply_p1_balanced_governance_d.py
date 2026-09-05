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

PLAN_PATH = ROOT / "data/coverage/P1_BALANCED_GOVERNANCE_D_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"

APPLY_ENV = "WORLD_SIGNALS_ALLOW_P1_BALANCED_GOVERNANCE_D_APPLY"
APPLY_VALUE = "YES"
WTO_OID = "WSO-TRD-A-0002"
NEW_SOURCE_ID = "WSSRC-TRD-008"
SELECTED_SOURCES = (
    "WSSRC-RISK-002",
    "WSSRC-COM-009",
    "WSSRC-COM-008",
    "WSSRC-INT-013",
    "WSSRC-HEALTH-002",
    "WSSRC-TRD-002",
    "WSSRC-REG2-003",
    "WSSRC-EL-VIC-001",
)

# These fields define WTO DS646's event identity, timing, procedural state and
# assertion identity. Cohort D may not alter any of them.
WTO_PROTECTED_FIELDS = (
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
    "time_status",
    "certainty_status",
    "lifecycle_status",
    "activation_mode",
    "condition_description",
    "condition_state",
    "procedural_eligibility_only",
    "trigger_assertion_id",
    "trigger_source_id",
    "trigger_verification_status",
    "primary_source_assertion_id",
    "last_successful_assertion_id",
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def records(registry: dict) -> dict[str, dict]:
    return {row.get("occurrence_id"): row for row in registry.get("records", [])}


def sources_map(registry: dict) -> dict[str, dict]:
    return {row.get("source_id"): row for row in registry.get("sources", [])}


def dep_count(canonical: dict, source_id: str) -> int:
    return sum(1 for row in canonical.get("records", []) if row.get("source_id") == source_id)


def overlay_checkpoint(overlay: dict) -> tuple[object, object]:
    checkpoint = overlay.get("canonical_checkpoint") or {}
    return checkpoint.get("registry_version"), checkpoint.get("record_count")


def exact(row: dict, expected: dict, label: str, errors: list[str]) -> None:
    for key, value in expected.items():
        if row.get(key) != value:
            errors.append(f"{label} {key}: expected {value!r}, found {row.get(key)!r}")


def snapshot(row: dict, fields: tuple[str, ...]) -> dict:
    return {key: copy.deepcopy(row.get(key)) for key in fields}


def preflight(canonical: dict, source_registry: dict, ledger: dict, overlay: dict, expectations: dict, plan: dict) -> None:
    p = plan["preconditions"]
    errors: list[str] = []

    if str(canonical.get("version")) != str(p["canonical_registry_version"]):
        errors.append("canonical version precondition failed")
    if len(canonical.get("records", [])) != p["canonical_record_count"] or canonical.get("record_count") != p["canonical_record_count"]:
        errors.append("canonical count precondition failed")
    if str(source_registry.get("version")) != str(p["source_registry_version"]):
        errors.append("source version precondition failed")
    if len(source_registry.get("sources", [])) != p["source_count"]:
        errors.append("source count precondition failed")
    if str(ledger.get("version")) != str(p["change_ledger_version"]):
        errors.append("ledger version precondition failed")
    if str(expectations.get("version")) != str(p["monitor_expectations_version"]):
        errors.append("monitor expectations version precondition failed")
    if expectations.get("automatic_canonical_commit") is not False:
        errors.append("automatic_canonical_commit must remain false")
    if expectations.get("google_calendar_write") is not False:
        errors.append("google_calendar_write must remain false")
    if overlay_checkpoint(overlay) != (p["biosecurity_overlay_registry_version"], p["biosecurity_overlay_record_count"]):
        errors.append("biosecurity overlay checkpoint precondition failed")

    by_source = sources_map(source_registry)
    for sid in p.get("required_absent_source_ids", []):
        if sid in by_source:
            errors.append(f"required-absent source already exists: {sid}")

    for sid, baseline in p["source_baselines"].items():
        row = by_source.get(sid)
        if row is None:
            errors.append(f"required source missing: {sid}")
            continue
        exact(
            row,
            {"authoritative_url": baseline["authoritative_url"], "source_type": baseline["source_type"]},
            f"source baseline {sid}",
            errors,
        )
        if dep_count(canonical, sid) != baseline["derived_dependency_count"]:
            errors.append(f"source {sid} derived dependency count drifted")
        for key in ("canonical_provenance_use", "automated_monitoring_use", "verification_mode"):
            if row.get(key) is not None:
                errors.append(f"source {sid} {key} is no longer missing")

    wto = records(canonical).get(WTO_OID)
    if wto is None:
        errors.append("WTO DS646 occurrence missing")
    else:
        baseline = p["wto_occurrence"]
        exact(wto, {k: v for k, v in baseline.items() if k != "occurrence_id"}, "WTO DS646 baseline", errors)

    planned_ids = {entry["change_id"] for entry in plan["ledger_entries"]}
    existing_ids = {entry.get("change_id") for entry in ledger.get("changes", [])}
    overlap = planned_ids & existing_ids
    if overlap:
        errors.append(f"planned ledger entry already exists: {sorted(overlap)}")

    if errors:
        raise SystemExit("P1 BALANCED GOVERNANCE D PRECONDITION FAILED:\n- " + "\n- ".join(errors))


def build_post_state(
    canonical: dict,
    source_registry: dict,
    ledger: dict,
    overlay: dict,
    expectations: dict,
    plan: dict,
    *,
    committed_at: str,
) -> tuple[dict, dict, dict, dict, dict]:
    preflight(canonical, source_registry, ledger, overlay, expectations, plan)

    canonical_out = copy.deepcopy(canonical)
    sources_out = copy.deepcopy(source_registry)
    ledger_out = copy.deepcopy(ledger)
    overlay_out = copy.deepcopy(overlay)

    before_records = records(canonical)
    after_records = records(canonical_out)
    wto_spec = plan["canonical_updates"][WTO_OID]
    after_records[WTO_OID].update(copy.deepcopy(wto_spec["set"]))
    canonical_out["version"] = plan["postconditions"]["canonical_registry_version"]
    canonical_out["reference_date"] = plan["review_date"]

    by_source = sources_map(sources_out)
    for sid, fields in plan["source_updates"].items():
        by_source[sid].update(copy.deepcopy(fields))
    if len(plan.get("new_sources", [])) != 1 or plan["new_sources"][0].get("source_id") != NEW_SOURCE_ID:
        raise ValueError("plan must define exactly one WSSRC-TRD-008 source")
    sources_out["sources"].append(copy.deepcopy(plan["new_sources"][0]))
    sources_out["version"] = plan["postconditions"]["source_registry_version"]
    sources_out["reference_date"] = plan["review_date"]

    frozen = copy.deepcopy(plan["ledger_entries"][0])
    before = before_records[WTO_OID]
    after = after_records[WTO_OID]
    changed_keys = list(wto_spec["set"].keys())
    frozen["old_values"] = {key: copy.deepcopy(before.get(key)) for key in changed_keys}
    frozen["new_values"] = {key: copy.deepcopy(after.get(key)) for key in changed_keys}
    frozen["source_assertion_id"] = after.get("primary_source_assertion_id")
    frozen["review_basis"] = [
        "WTO DS646 dispute-status evidence and DSU Article 4.7 legal authority were re-audited separately.",
        "The standing 60-day rule runs from receipt of the consultation request; accessible first-order evidence still does not establish the respondent receipt date.",
        "The existing 25–28 September 2026 conditional eligibility window, certainty, condition state and assertion identities therefore remain unchanged.",
        "WSSRC-TRD-008 is added only as explicit first-order legal-basis provenance.",
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
        canonical, source_registry, ledger, overlay,
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
    if overlay_checkpoint(overlay_after) != (post["biosecurity_overlay_registry_version"], post["biosecurity_overlay_record_count"]):
        errors.append("biosecurity overlay post-state mismatch")

    expected_overlay = copy.deepcopy(overlay_before)
    expected_overlay["canonical_checkpoint"]["registry_version"] = post["biosecurity_overlay_registry_version"]
    expected_overlay["canonical_checkpoint"]["record_count"] = post["biosecurity_overlay_record_count"]
    if overlay_after != expected_overlay:
        errors.append("biosecurity overlay changed outside canonical checkpoint")

    before_records = records(canonical_before)
    after_records = records(canonical_after)
    if list(before_records) != list(after_records):
        errors.append("canonical occurrence identity/order changed")
    changed_occurrences = [oid for oid in before_records if before_records[oid] != after_records[oid]]
    if changed_occurrences != post["expected_changed_occurrences"]:
        errors.append(f"unexpected canonical changed occurrences: {changed_occurrences}")

    wto_before = before_records[WTO_OID]
    wto_after = after_records[WTO_OID]
    if snapshot(wto_before, WTO_PROTECTED_FIELDS) != snapshot(wto_after, WTO_PROTECTED_FIELDS):
        errors.append("WTO timing/procedural/assertion identity fields changed")
    exact(
        wto_after,
        {
            "date_earliest": "2026-09-25",
            "date_latest": "2026-09-28",
            "timing_type": "EXPECTED_DATE_WINDOW",
            "certainty_status": "PROVISIONAL",
            "activation_mode": "CONDITIONAL",
            "condition_state": "PENDING",
            "procedural_eligibility_only": True,
            "legal_basis_source_id": NEW_SOURCE_ID,
            "governing_instrument": "WTO Dispute Settlement Understanding, Article 4.7",
        },
        "WTO DS646 post-state",
        errors,
    )

    # Every non-WTO canonical occurrence must remain byte-identical.
    for oid, row in before_records.items():
        if oid != WTO_OID and row != after_records[oid]:
            errors.append(f"unexpected canonical mutation outside WTO DS646: {oid}")
            break

    before_sources = sources_map(sources_before)
    after_sources = sources_map(sources_after)
    before_ids = [row.get("source_id") for row in sources_before.get("sources", [])]
    after_ids = [row.get("source_id") for row in sources_after.get("sources", [])]
    if after_ids != before_ids + [NEW_SOURCE_ID]:
        errors.append("source identity/order changed outside appended WSSRC-TRD-008")
    changed_existing = [sid for sid in before_ids if before_sources[sid] != after_sources[sid]]
    if set(changed_existing) != set(post["expected_changed_existing_sources"]) or len(changed_existing) != len(post["expected_changed_existing_sources"]):
        errors.append(f"unexpected existing source changes: {changed_existing}")
    for sid, fields in plan["source_updates"].items():
        exact(after_sources[sid], fields, f"source post-state {sid}", errors)
    exact(after_sources[NEW_SOURCE_ID], plan["new_sources"][0], "new WTO legal source", errors)

    for sid, baseline in plan["preconditions"]["source_baselines"].items():
        if dep_count(canonical_after, sid) != baseline["derived_dependency_count"]:
            errors.append(f"primary dependency count changed: {sid}")
    if dep_count(canonical_after, NEW_SOURCE_ID) != 0:
        errors.append("WSSRC-TRD-008 must have zero primary source_id dependencies")

    # Historical/global invariants.
    exact(after_records["WSO-REG-A-0014"], {"start_local": "2026-10-09", "certainty_status": "CONFIRMED", "population_horizon_policy": "EXACT_LEGAL_OR_POLICY_MILESTONE_ONLY"}, "Malaysia Budget", errors)
    exact(after_records["WSO-EL-A-0004"], {"start_local": "2027-01-05"}, "Brazil inauguration", errors)
    exact(after_records["WSO-FIS-B-0011"], {"start_local": None, "date_earliest": None, "date_latest": None, "certainty_status": "TBC"}, "India Budget", errors)
    exact(after_records["WSO-INT-A-0018"], {"date_earliest": "2027-05-01", "date_latest": "2027-05-31", "time_precision": "MONTH"}, "ASEAN 50", errors)
    exact(after_records["WSO-INT-A-0019"], {"date_earliest": "2027-11-01", "date_latest": "2027-11-30", "time_precision": "MONTH"}, "ASEAN 51", errors)
    if not {"WSSRC-REG4-001", "WSSRC-REG4-002"}.issubset(set(after_sources)):
        errors.append("Colombia split invariant failed")

    historical_changes = ledger_before.get("changes", [])
    if ledger_after.get("changes", [])[:len(historical_changes)] != historical_changes:
        errors.append("historical ledger changed")
    added = ledger_after.get("changes", [])[len(historical_changes):]
    if len(added) != 1:
        errors.append("ledger must gain exactly one entry")
    else:
        entry = added[0]
        frozen = plan["ledger_entries"][0]
        exact(entry, {k: v for k, v in frozen.items()}, "ledger frozen fields", errors)
        if entry.get("source_assertion_id") != wto_after.get("primary_source_assertion_id"):
            errors.append("ledger source assertion mismatch")
        if not entry.get("committed_at"):
            errors.append("ledger committed_at missing")
        if entry.get("registry_version_before") != plan["preconditions"]["canonical_registry_version"] or entry.get("registry_version_after") != post["canonical_registry_version"]:
            errors.append("ledger registry lineage mismatch")

    validation = validate_registry(canonical_after, sources_after)
    errors.extend(validation.errors)

    audit = build_source_governance_audit(canonical_after, sources_after, expectations)["totals"]
    actual_governance = {
        "fully_explicit": audit["fully_explicit_governance_source_count"],
        "missing_any": audit["source_records_with_one_or_more_missing_governance_fields"],
        "p1_canonical_dependent": audit["backfill_research_priority_counts"].get("P1_CANONICAL_DEPENDENCY", 0),
        "p2_registry_only": audit["backfill_research_priority_counts"].get("P2_REGISTRY_ONLY", 0),
    }
    if actual_governance != post["governance_expected"]:
        errors.append(f"governance totals mismatch: {actual_governance!r} != {post['governance_expected']!r}")

    if expectations.get("automatic_canonical_commit") is not False:
        errors.append("automatic_canonical_commit not false")
    if expectations.get("google_calendar_write") is not False:
        errors.append("google_calendar_write not false")

    if errors:
        raise ValueError("P1 BALANCED GOVERNANCE D POST-STATE INVALID:\n- " + "\n- ".join(errors))

    return {
        "status": "PASS",
        "canonical_version": canonical_after.get("version"),
        "canonical_count": len(canonical_after.get("records", [])),
        "source_version": sources_after.get("version"),
        "source_count": len(sources_after.get("sources", [])),
        "ledger_version": ledger_after.get("version"),
        "changed_occurrences": changed_occurrences,
        "changed_existing_sources": changed_existing,
        "new_source": NEW_SOURCE_ID,
        "governance": actual_governance,
        "automatic_canonical_commit": expectations.get("automatic_canonical_commit"),
        "google_calendar_write": expectations.get("google_calendar_write"),
    }


def run(*, apply: bool, committed_at: str | None = None) -> dict:
    plan = load(PLAN_PATH)
    canonical = load(CANONICAL_PATH)
    source_registry = load(SOURCES_PATH)
    ledger = load(LEDGER_PATH)
    overlay = load(OVERLAY_PATH)
    expectations = load(EXPECTATIONS_PATH)

    if committed_at is None:
        committed_at = datetime.now(ZoneInfo("Australia/Melbourne")).isoformat(timespec="seconds")

    canonical_out, sources_out, ledger_out, overlay_out, report = build_post_state(
        canonical, source_registry, ledger, overlay, expectations, plan, committed_at=committed_at
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
