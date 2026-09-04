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

PLAN_PATH = ROOT / "data/coverage/VIETNAM_SOURCE_SCOPE_REPAIR_A_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"

APPLY_ENV = "WORLD_SIGNALS_ALLOW_VIETNAM_SOURCE_SCOPE_REPAIR_A_APPLY"
APPLY_VALUE = "YES"
OLD_SOURCE = "WSSRC-REG5-001"
NEW_SOURCE = "WSSRC-REG5-002"
OCCURRENCE = "WSO-REG-G-0001"

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


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _sources_by_id(registry: dict) -> dict[str, dict]:
    return {row.get("source_id"): row for row in registry.get("sources", [])}


def _records_by_id(registry: dict) -> dict[str, dict]:
    return {row.get("occurrence_id"): row for row in registry.get("records", [])}


def _source_dependency_count(canonical: dict, source_id: str) -> int:
    return sum(1 for row in canonical.get("records", []) if row.get("source_id") == source_id)


def _assertion_id(record: dict) -> str:
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


def _exact_fields(row: dict, expected: dict, label: str, errors: list[str]) -> None:
    for key, value in expected.items():
        if row.get(key) != value:
            errors.append(f"{label} {key}: expected {value!r}, found {row.get(key)!r}")


def _check_overlay(overlay: dict, expected: dict, label: str, errors: list[str]) -> None:
    checkpoint = overlay.get("canonical_checkpoint") or {}
    if overlay.get("dataset") != expected["dataset"]:
        errors.append(f"{label} dataset mismatch")
    if overlay.get("version") != expected["version"]:
        errors.append(f"{label} version mismatch")
    if checkpoint.get("registry_version") != expected["canonical_checkpoint_registry_version"]:
        errors.append(f"{label} canonical checkpoint version mismatch")
    if checkpoint.get("record_count") != expected["canonical_checkpoint_record_count"]:
        errors.append(f"{label} canonical checkpoint count mismatch")


def preflight(canonical: dict, sources: dict, ledger: dict, overlay: dict, expectations: dict, plan: dict) -> None:
    p = plan["preconditions"]
    errors: list[str] = []

    if str(canonical.get("version")) != str(p["canonical_registry_version"]):
        errors.append("canonical version precondition failed")
    if canonical.get("record_count") != p["canonical_record_count"] or len(canonical.get("records", [])) != p["canonical_record_count"]:
        errors.append("canonical count precondition failed")
    if str(sources.get("version")) != str(p["source_registry_version"]):
        errors.append("source version precondition failed")
    if len(sources.get("sources", [])) != p["source_count"]:
        errors.append("source count precondition failed")
    if str(ledger.get("version")) != str(p["change_ledger_version"]):
        errors.append("change-ledger version precondition failed")
    if str(expectations.get("version")) != str(p["monitor_expectations_version"]):
        errors.append("monitor expectations version precondition failed")
    if expectations.get("automatic_canonical_commit") is not False:
        errors.append("automatic_canonical_commit must remain false")
    if expectations.get("google_calendar_write") is not False:
        errors.append("google_calendar_write must remain false")
    _check_overlay(overlay, p["biosecurity_overlay"], "biosecurity overlay precondition", errors)

    by_source = _sources_by_id(sources)
    if OLD_SOURCE not in by_source:
        errors.append(f"required source missing: {OLD_SOURCE}")
    for source_id in p["required_absent_source_ids"]:
        if source_id in by_source:
            errors.append(f"new source already exists: {source_id}")

    old = p["existing_government_news_source"]
    if OLD_SOURCE in by_source:
        _exact_fields(
            by_source[OLD_SOURCE],
            {
                "source_id": old["source_id"],
                "institution": old["institution"],
                "authoritative_url": old["authoritative_url"],
                "source_type": old["source_type"],
                "verification_mode": old["verification_mode"],
            },
            "existing Vietnam government-news source",
            errors,
        )
        if _source_dependency_count(canonical, OLD_SOURCE) != old["derived_canonical_dependency_count"]:
            errors.append("existing Vietnam source derived dependency precondition failed")

    records = _records_by_id(canonical)
    row = records.get(OCCURRENCE)
    if row is None:
        errors.append("Vietnam occurrence missing")
    else:
        _exact_fields(row, p["occurrence"], "Vietnam occurrence", errors)
        _exact_fields(row, plan["canonical_update"]["must_preserve"], "Vietnam preserved field", errors)
        if row.get("session_phases") != plan["canonical_update"]["must_preserve_session_phases"]:
            errors.append("Vietnam session phase precondition failed")

    for source_id, spec in plan["source_updates"].items():
        source = by_source.get(source_id)
        if source is not None:
            _exact_fields(source, spec.get("expected", {}), f"source {source_id}", errors)

    if any(change.get("change_id") == plan["change_ledger_entry"]["change_id"] for change in ledger.get("changes", [])):
        errors.append("planned Vietnam provenance-repair ledger entry already exists")

    if errors:
        raise SystemExit("VIETNAM SOURCE SCOPE REPAIR A PRECONDITION FAILED:\n- " + "\n- ".join(errors))


def build_post_state(
    canonical: dict,
    sources: dict,
    ledger: dict,
    overlay: dict,
    expectations: dict,
    plan: dict,
    *,
    committed_at: str,
) -> tuple[dict, dict, dict, dict, dict]:
    preflight(canonical, sources, ledger, overlay, expectations, plan)

    canonical_out = copy.deepcopy(canonical)
    sources_out = copy.deepcopy(sources)
    ledger_out = copy.deepcopy(ledger)
    overlay_out = copy.deepcopy(overlay)

    occurrence = _records_by_id(canonical_out)[OCCURRENCE]
    for key, value in plan["canonical_update"]["set"].items():
        occurrence[key] = copy.deepcopy(value)

    expected_assertion = _assertion_id(occurrence)
    frozen_assertion = plan["canonical_update"]["set"]["primary_source_assertion_id"]
    if expected_assertion != frozen_assertion:
        raise ValueError(f"frozen Vietnam assertion id mismatch: {expected_assertion} != {frozen_assertion}")

    canonical_out["version"] = plan["postconditions"]["canonical_registry_version"]
    canonical_out["reference_date"] = plan["review_date"]

    by_source = _sources_by_id(sources_out)
    for source_id, spec in plan["source_updates"].items():
        by_source[source_id].update(copy.deepcopy(spec["set"]))

    new_sources = copy.deepcopy(plan["new_sources"])
    if len(new_sources) != 1 or new_sources[0].get("source_id") != NEW_SOURCE:
        raise ValueError("plan must define exactly one new National Assembly source")
    sources_out["sources"].append(new_sources[0])
    sources_out["version"] = plan["postconditions"]["source_registry_version"]
    sources_out["reference_date"] = plan["review_date"]

    change_entry = copy.deepcopy(plan["change_ledger_entry"])
    if "committed_at" in change_entry:
        raise ValueError("committed_at must not be frozen in research plan")
    change_entry["committed_at"] = committed_at
    ledger_out["changes"].append(change_entry)
    ledger_out["version"] = plan["postconditions"]["change_ledger_version"]
    ledger_out["reference_date"] = plan["review_date"]

    overlay_out["canonical_checkpoint"]["registry_version"] = plan["postconditions"]["canonical_registry_version"]
    overlay_out["canonical_checkpoint"]["record_count"] = plan["postconditions"]["canonical_record_count"]

    report = validate_post_state(
        canonical,
        sources,
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

    if canonical_after.get("version") != post["canonical_registry_version"]:
        errors.append("canonical post-version mismatch")
    if canonical_after.get("record_count") != post["canonical_record_count"] or len(canonical_after.get("records", [])) != post["canonical_record_count"]:
        errors.append("canonical post-count mismatch")
    if sources_after.get("version") != post["source_registry_version"] or len(sources_after.get("sources", [])) != post["source_count"]:
        errors.append("source post-state mismatch")
    if ledger_after.get("version") != post["change_ledger_version"]:
        errors.append("ledger post-version mismatch")
    _check_overlay(overlay_after, post["biosecurity_overlay"], "biosecurity overlay postcondition", errors)

    overlay_expected = copy.deepcopy(overlay_before)
    overlay_expected["canonical_checkpoint"]["registry_version"] = post["canonical_registry_version"]
    overlay_expected["canonical_checkpoint"]["record_count"] = post["canonical_record_count"]
    if overlay_after != overlay_expected:
        errors.append("biosecurity overlay changed outside canonical checkpoint advancement")

    before_records = _records_by_id(canonical_before)
    after_records = _records_by_id(canonical_after)
    if list(before_records) != list(after_records):
        errors.append("canonical occurrence identity/order changed")

    changed_occurrences = [oid for oid in before_records if before_records[oid] != after_records[oid]]
    if changed_occurrences != [OCCURRENCE]:
        errors.append(f"unexpected canonical changes: {changed_occurrences}")

    for oid in before_records:
        before_timing = {field: before_records[oid].get(field) for field in TIMING_FIELDS}
        after_timing = {field: after_records[oid].get(field) for field in TIMING_FIELDS}
        if before_timing != after_timing:
            errors.append(f"timing changed for {oid}: {before_timing!r} -> {after_timing!r}")
            break

    occurrence = after_records[OCCURRENCE]
    _exact_fields(occurrence, plan["canonical_update"]["set"], "Vietnam post-state", errors)
    _exact_fields(occurrence, plan["canonical_update"]["must_preserve"], "Vietnam preserved post-state", errors)
    if occurrence.get("session_phases") != plan["canonical_update"]["must_preserve_session_phases"]:
        errors.append("Vietnam session phases changed")

    before_ids = [s.get("source_id") for s in sources_before.get("sources", [])]
    after_ids = [s.get("source_id") for s in sources_after.get("sources", [])]
    if after_ids != before_ids + [NEW_SOURCE]:
        errors.append("source identity/order changed outside one appended National Assembly source")

    before_sources = _sources_by_id(sources_before)
    after_sources = _sources_by_id(sources_after)
    changed_existing_sources = [sid for sid in before_ids if before_sources[sid] != after_sources[sid]]
    if changed_existing_sources != [OLD_SOURCE]:
        errors.append(f"unexpected existing source changes: {changed_existing_sources}")

    for source_id, spec in plan["source_updates"].items():
        _exact_fields(after_sources[source_id], spec["set"], f"post source {source_id}", errors)
    _exact_fields(after_sources[NEW_SOURCE], plan["new_sources"][0], "new National Assembly source", errors)

    derived_counts = {
        OLD_SOURCE: _source_dependency_count(canonical_after, OLD_SOURCE),
        NEW_SOURCE: _source_dependency_count(canonical_after, NEW_SOURCE),
    }
    expected_counts = {
        OLD_SOURCE: post["old_government_news_derived_dependency_count"],
        NEW_SOURCE: post["new_national_assembly_derived_dependency_count"],
    }
    if derived_counts != expected_counts:
        errors.append(f"post dependency counts mismatch: {derived_counts!r} != {expected_counts!r}")

    if len(ledger_after.get("changes", [])) != len(ledger_before.get("changes", [])) + 1:
        errors.append("ledger must gain exactly one entry")
    elif ledger_after["changes"][:-1] != ledger_before.get("changes", []):
        errors.append("historical ledger entries changed")
    else:
        actual_change = copy.deepcopy(ledger_after["changes"][-1])
        committed_at = actual_change.pop("committed_at", None)
        if not committed_at:
            errors.append("ledger repair entry must receive committed_at at transaction time")
        if actual_change != plan["change_ledger_entry"]:
            errors.append("ledger repair entry differs from frozen plan apart from committed_at")

    validation = validate_registry(canonical_after, sources_after)
    errors.extend(validation.errors)

    audit = build_source_governance_audit(canonical_after, sources_after, expectations)
    totals = audit["totals"]
    expected_gov = post["governance_expected"]
    actual_gov = {
        "fully_explicit": totals["fully_explicit_governance_source_count"],
        "missing_any": totals["source_records_with_one_or_more_missing_governance_fields"],
        "p1_canonical_dependent": totals["backfill_research_priority_counts"].get("P1_CANONICAL_DEPENDENCY", 0),
        "p2_registry_only": totals["backfill_research_priority_counts"].get("P2_REGISTRY_ONLY", 0),
    }
    if actual_gov != expected_gov:
        errors.append(f"source-governance totals mismatch: {actual_gov!r} != {expected_gov!r}")

    if expectations.get("automatic_canonical_commit") is not False:
        errors.append("automatic_canonical_commit not false")
    if expectations.get("google_calendar_write") is not False:
        errors.append("google_calendar_write not false")

    if errors:
        raise ValueError("VIETNAM SOURCE SCOPE REPAIR A POST-STATE FAILED:\n- " + "\n- ".join(errors))

    return {
        "transaction": plan["transaction"],
        "canonical_version": canonical_after["version"],
        "canonical_record_count": canonical_after["record_count"],
        "source_version": sources_after["version"],
        "source_count": len(sources_after["sources"]),
        "ledger_version": ledger_after["version"],
        "changed_occurrence_ids": changed_occurrences,
        "changed_existing_source_ids": changed_existing_sources,
        "new_source_ids": [NEW_SOURCE],
        "derived_dependency_counts": derived_counts,
        "governance": actual_gov,
        "automatic_canonical_commit": expectations.get("automatic_canonical_commit"),
        "google_calendar_write": expectations.get("google_calendar_write"),
    }


def _load_all() -> tuple[dict, dict, dict, dict, dict, dict]:
    return (
        load(CANONICAL_PATH),
        load(SOURCES_PATH),
        load(LEDGER_PATH),
        load(OVERLAY_PATH),
        load(EXPECTATIONS_PATH),
        load(PLAN_PATH),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Guarded Vietnam source-scope provenance repair A")
    parser.add_argument("--apply", action="store_true", help="write the reviewed four-file repair")
    args = parser.parse_args()

    canonical, sources, ledger, overlay, expectations, plan = _load_all()
    preflight(canonical, sources, ledger, overlay, expectations, plan)

    if not args.apply:
        canonical_post, sources_post, ledger_post, overlay_post, report = build_post_state(
            canonical,
            sources,
            ledger,
            overlay,
            expectations,
            plan,
            committed_at=plan["change_ledger_entry"]["reviewed_at"],
        )
        report["mode"] = "READ_ONLY_PREFLIGHT"
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    if os.environ.get(APPLY_ENV) != APPLY_VALUE:
        raise SystemExit(f"VIETNAM SOURCE SCOPE REPAIR A APPLY REFUSED: set {APPLY_ENV}={APPLY_VALUE}")

    committed_at = datetime.now(ZoneInfo("Australia/Melbourne")).replace(microsecond=0).isoformat()
    canonical_post, sources_post, ledger_post, overlay_post, report = build_post_state(
        canonical,
        sources,
        ledger,
        overlay,
        expectations,
        plan,
        committed_at=committed_at,
    )
    dump(CANONICAL_PATH, canonical_post)
    dump(SOURCES_PATH, sources_post)
    dump(LEDGER_PATH, ledger_post)
    dump(OVERLAY_PATH, overlay_post)
    report["mode"] = "APPLIED_REVIEWED_TRANSACTION"
    report["committed_at"] = committed_at
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
