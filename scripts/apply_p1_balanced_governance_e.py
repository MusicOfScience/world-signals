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
sys.path.insert(0, str(ROOT / "src"))

from world_signals.source_governance_audit import build_source_governance_audit
from world_signals.validation import validate_registry

PLAN_PATH = ROOT / "data/coverage/P1_BALANCED_GOVERNANCE_E_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"

APPLY_ENV = "WORLD_SIGNALS_ALLOW_P1_BALANCED_GOVERNANCE_E_APPLY"
APPLY_VALUE = "YES"
NEW_SOURCE_ID = "WSSRC-INT-031"
APEC_OID = "WSO-INT-A-0012"
IPCC_SLCF_OID = "WSO-CLIM-A-0009"
IPCC_CDR_OID = "WSO-CLIM-A-0010"
NDB_OID = "WSO-INT-B-0113"
CHANGED_OIDS = (APEC_OID, IPCC_SLCF_OID, IPCC_CDR_OID, NDB_OID)
SELECTED_SOURCES = (
    "WSSRC-MAC-023",
    "WSSRC-REG-008",
    "WSSRC-COM-006",
    "WSSRC-CLIM-002",
    "WSSRC-INT-024",
    "WSSRC-INT-011",
    "WSSRC-INT-028",
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


def assertion_id(record: dict) -> str:
    material = "|".join(
        str(record.get(key) or "")
        for key in (
            "occurrence_id",
            "series_id",
            "source_id",
            "canonical_name",
            "start_local",
            "end_local",
            "publication_datetime",
        )
    )
    return "WSA-" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def changed_keys(before: dict, after: dict) -> set[str]:
    return {key for key in set(before) | set(after) if before.get(key) != after.get(key)}


def preflight(
    canonical: dict,
    source_registry: dict,
    ledger: dict,
    overlay: dict,
    expectations: dict,
    plan: dict,
) -> None:
    p = plan["preconditions"]
    errors: list[str] = []

    if str(canonical.get("version")) != str(p["canonical_registry_version"]):
        errors.append("canonical version precondition failed")
    if canonical.get("record_count") != p["canonical_record_count"] or len(canonical.get("records", [])) != p["canonical_record_count"]:
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
        exact(row, {"authoritative_url": baseline["authoritative_url"], "source_type": baseline["source_type"]}, f"source {sid}", errors)
        if dep_count(canonical, sid) != baseline["derived_dependency_count"]:
            errors.append(f"source {sid} derived dependency count drifted")
        for key in ("canonical_provenance_use", "automated_monitoring_use", "verification_mode"):
            if row.get(key) is not None:
                errors.append(f"source {sid} {key} is no longer missing")

    by_record = records(canonical)
    for oid, baseline in p["canonical_baselines"].items():
        row = by_record.get(oid)
        if row is None:
            errors.append(f"required occurrence missing: {oid}")
            continue
        exact(row, baseline, f"occurrence {oid}", errors)

    planned_ids = {entry["change_id"] for entry in plan["ledger_entries"]}
    existing_ids = {entry.get("change_id") for entry in ledger.get("changes", [])}
    overlap = planned_ids & existing_ids
    if overlap:
        errors.append(f"planned ledger entries already exist: {sorted(overlap)}")

    if errors:
        raise SystemExit("P1 BALANCED GOVERNANCE E PRECONDITION FAILED:\n- " + "\n- ".join(errors))


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
    for oid, spec in plan["canonical_updates"].items():
        after_records[oid].update(copy.deepcopy(spec["set"]))

    canonical_out["version"] = plan["postconditions"]["canonical_registry_version"]
    canonical_out["reference_date"] = plan["review_date"]

    by_source = sources_map(sources_out)
    for sid, fields in plan["source_updates"].items():
        by_source[sid].update(copy.deepcopy(fields))
    if len(plan.get("new_sources", [])) != 1 or plan["new_sources"][0].get("source_id") != NEW_SOURCE_ID:
        raise ValueError("plan must define exactly one WSSRC-INT-031 source")
    sources_out["sources"].append(copy.deepcopy(plan["new_sources"][0]))
    sources_out["version"] = plan["postconditions"]["source_registry_version"]
    sources_out["reference_date"] = plan["review_date"]

    for frozen_entry in plan["ledger_entries"]:
        entry = copy.deepcopy(frozen_entry)
        oid = entry["occurrence_id"]
        before = before_records[oid]
        after = after_records[oid]
        keys = list(plan["canonical_updates"][oid]["set"].keys())
        entry["old_values"] = {key: copy.deepcopy(before.get(key)) for key in keys}
        entry["new_values"] = {key: copy.deepcopy(after.get(key)) for key in keys}
        entry["source_assertion_id"] = after.get("primary_source_assertion_id")
        entry["review_basis"] = [
            "Current first-order source scope and timing precision were re-audited on 2026-09-05.",
            "Stable occurrence identity is preserved and no timing precision is manufactured beyond the competent source evidence.",
            "Canonical provenance and automated-monitoring permission remain separate governance dimensions.",
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

    report = validate_post_state(
        canonical,
        source_registry,
        ledger,
        overlay,
        canonical_out,
        sources_out,
        ledger_out,
        overlay_out,
        expectations,
        plan,
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
    actual_changed = {oid for oid in before_records if before_records[oid] != after_records[oid]}
    if actual_changed != set(post["expected_changed_occurrences"]):
        errors.append(f"unexpected canonical changed occurrence set: {sorted(actual_changed)}")

    # Everything outside the four authorised occurrences is immutable.
    for oid, row in before_records.items():
        if oid not in CHANGED_OIDS and row != after_records[oid]:
            errors.append(f"unexpected canonical mutation outside authorised cohort: {oid}")
            break

    # APEC: provenance changes; event timing and host semantics do not.
    apec_before = before_records[APEC_OID]
    apec_after = after_records[APEC_OID]
    allowed_apec = {"source_id", "primary_source_assertion_id", "last_successful_assertion_id", "schedule_authority_scope", "notes", "last_verified_at"}
    if changed_keys(apec_before, apec_after) != allowed_apec:
        errors.append(f"APEC changed fields outside frozen provenance set: {sorted(changed_keys(apec_before, apec_after))}")
    exact(apec_after, {
        "source_id": NEW_SOURCE_ID,
        "start_local": "2026-11-18",
        "end_local": "2026-11-19",
        "certainty_status": "CONFIRMED",
        "timing_type": "MULTI_DAY_LOCAL",
        "time_precision": "DAY",
        "time_status": "CONFIRMED",
        "host_confirmed": True,
        "host_jurisdiction": "China",
        "host_city": "Shenzhen",
        "primary_source_assertion_id": "WSA-070677934abbc0f0",
        "last_successful_assertion_id": "WSA-070677934abbc0f0",
        "schedule_authority_scope": "EVENT_SPECIFIC",
    }, "APEC post-state", errors)
    if assertion_id(apec_after) != "WSA-070677934abbc0f0":
        errors.append("APEC assertion hash does not match new source identity")

    # IPCC: month precision only; source/assertion/certainty stay stable.
    for oid, old_precision, old_lo in (
        (IPCC_SLCF_OID, "HALF_YEAR", "2027-07-01"),
        (IPCC_CDR_OID, "YEAR", "2027-01-01"),
    ):
        before = before_records[oid]
        after = after_records[oid]
        allowed = {"date_earliest", "time_precision", "approval_publication_semantics", "last_verified_at"}
        if changed_keys(before, after) != allowed:
            errors.append(f"IPCC {oid} changed fields outside frozen precision set: {sorted(changed_keys(before, after))}")
        exact(before, {"date_earliest": old_lo, "date_latest": "2027-12-31", "time_precision": old_precision}, f"IPCC {oid} pre-state", errors)
        exact(after, {
            "source_id": "WSSRC-CLIM-002",
            "date_earliest": "2027-12-01",
            "date_latest": "2027-12-31",
            "time_precision": "MONTH",
            "timing_type": "EXPECTED_DATE_WINDOW",
            "certainty_status": "CONFIRMED",
            "time_status": "CONFIRMED",
            "primary_source_assertion_id": before.get("primary_source_assertion_id"),
            "last_successful_assertion_id": before.get("last_successful_assertion_id"),
        }, f"IPCC {oid} post-state", errors)

    # NDB: only semantic precision/explanation; still completely undated.
    ndb_before = before_records[NDB_OID]
    ndb_after = after_records[NDB_OID]
    allowed_ndb = {"time_precision", "notes", "last_verified_at"}
    if changed_keys(ndb_before, ndb_after) != allowed_ndb:
        errors.append(f"NDB changed fields outside frozen semantic set: {sorted(changed_keys(ndb_before, ndb_after))}")
    exact(ndb_after, {
        "source_id": "WSSRC-INT-028",
        "start_local": None,
        "end_local": None,
        "date_earliest": None,
        "date_latest": None,
        "timing_type": "UNSCHEDULED_TBC",
        "time_precision": "TBC",
        "time_status": "TBC",
        "certainty_status": "TBC",
        "host_confirmed": True,
        "host_jurisdiction": "India",
        "host_city": None,
        "primary_source_assertion_id": "WSA-ddfc58840300a4f6",
        "last_successful_assertion_id": "WSA-ddfc58840300a4f6",
    }, "NDB post-state", errors)

    before_sources = sources_map(sources_before)
    after_sources = sources_map(sources_after)
    before_ids = [row.get("source_id") for row in sources_before.get("sources", [])]
    after_ids = [row.get("source_id") for row in sources_after.get("sources", [])]
    if after_ids != before_ids + [NEW_SOURCE_ID]:
        errors.append("source identity/order changed outside appended WSSRC-INT-031")
    actual_source_changes = {sid for sid in before_ids if before_sources[sid] != after_sources[sid]}
    if actual_source_changes != set(post["expected_changed_existing_sources"]):
        errors.append(f"unexpected existing source changed set: {sorted(actual_source_changes)}")
    for sid, fields in plan["source_updates"].items():
        exact(after_sources[sid], fields, f"source post-state {sid}", errors)
    exact(after_sources[NEW_SOURCE_ID], plan["new_sources"][0], "new APEC exact-date source", errors)

    # Primary-source dependency truth after APEC reassignment.
    for sid, baseline in plan["preconditions"]["source_baselines"].items():
        expected = 0 if sid == "WSSRC-INT-011" else baseline["derived_dependency_count"]
        if dep_count(canonical_after, sid) != expected:
            errors.append(f"derived dependency mismatch after transaction: {sid}")
    if dep_count(canonical_after, NEW_SOURCE_ID) != 1:
        errors.append("WSSRC-INT-031 must have exactly one primary canonical dependency")
    if after_sources["WSSRC-INT-011"].get("canonical_dependency_count") != 0:
        errors.append("WSSRC-INT-011 stored dependency helper must be zero after reassignment")
    if after_sources[NEW_SOURCE_ID].get("canonical_dependency_count") != 1:
        errors.append("WSSRC-INT-031 stored dependency helper must be one")

    # Historical/global invariants.
    exact(after_records["WSO-EL-A-0004"], {"start_local": "2027-01-05"}, "Brazil inauguration", errors)
    if not {"WSSRC-REG4-001", "WSSRC-REG4-002"}.issubset(set(after_sources)):
        errors.append("Colombia source split invariant failed")
    if expectations.get("automatic_canonical_commit") is not False:
        errors.append("automatic_canonical_commit not false")
    if expectations.get("google_calendar_write") is not False:
        errors.append("google_calendar_write not false")

    if ledger_after.get("changes", [])[:len(ledger_before.get("changes", []))] != ledger_before.get("changes", []):
        errors.append("historical ledger changed")
    added = ledger_after.get("changes", [])[len(ledger_before.get("changes", [])):]
    if len(added) != 4:
        errors.append("ledger did not gain exactly four entries")
    else:
        expected_ids = [entry["change_id"] for entry in plan["ledger_entries"]]
        if [entry.get("change_id") for entry in added] != expected_ids:
            errors.append("ledger added-entry identity/order mismatch")
        if any(not entry.get("committed_at") for entry in added):
            errors.append("ledger committed_at missing")

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

    if errors:
        raise ValueError("P1 BALANCED GOVERNANCE E POST-STATE INVALID:\n- " + "\n- ".join(errors))

    return {
        "status": "PASS",
        "canonical_version": canonical_after.get("version"),
        "canonical_count": len(canonical_after.get("records", [])),
        "source_version": sources_after.get("version"),
        "source_count": len(sources_after.get("sources", [])),
        "ledger_version": ledger_after.get("version"),
        "changed_occurrences": sorted(actual_changed),
        "changed_existing_sources": sorted(actual_source_changes),
        "new_source": NEW_SOURCE_ID,
        "governance": actual_governance,
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
