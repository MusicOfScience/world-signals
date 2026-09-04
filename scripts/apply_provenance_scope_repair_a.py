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

from world_signals.validation import validate_registry

PLAN_PATH = ROOT / "data/coverage/PROVENANCE_SCOPE_REPAIR_A_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
BIOSECURITY_OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
LIVE_RUNNER_PATH = ROOT / "scripts/run_live_monitor.py"

APPLY_ENV = "WORLD_SIGNALS_ALLOW_PROVENANCE_REPAIR_A_APPLY"
APPLY_VALUE = "YES"
BRAZIL_TSE = "WSSRC-EL-BR-001"
BRAZIL_CONSTITUTION = "WSSRC-EL-BR-002"
SNB = "WSSRC-CB-009"
BRAZIL_OCCURRENCE = "WSO-EL-A-0004"

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
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


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


def preflight(
    canonical: dict,
    sources: dict,
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
    for source_id in (BRAZIL_TSE, SNB):
        if source_id not in by_source:
            errors.append(f"required source missing: {source_id}")
    for source_id in p["required_absent_source_ids"]:
        if source_id in by_source:
            errors.append(f"new source already exists: {source_id}")

    tse = p["brazil_tse"]
    if BRAZIL_TSE in by_source:
        if by_source[BRAZIL_TSE].get("authoritative_url") != tse["expected_authoritative_url"]:
            errors.append("TSE authoritative URL precondition failed")
        if _source_dependency_count(canonical, BRAZIL_TSE) != tse["expected_canonical_dependency_count"]:
            errors.append("TSE canonical dependency precondition failed")

    snb = p["snb"]
    if SNB in by_source:
        if by_source[SNB].get("authoritative_url") != snb["expected_authoritative_url"]:
            errors.append("SNB authoritative URL precondition failed")
        if _source_dependency_count(canonical, SNB) != snb["expected_canonical_dependency_count"]:
            errors.append("SNB canonical dependency precondition failed")

    records = _records_by_id(canonical)
    occurrence = records.get(BRAZIL_OCCURRENCE)
    if occurrence is None:
        errors.append("Brazil inauguration occurrence missing")
    else:
        _exact_fields(occurrence, p["brazil_inauguration"], "Brazil inauguration", errors)
        _exact_fields(occurrence, plan["canonical_update"]["must_preserve"], "Brazil inauguration preserved field", errors)

    for source_id, spec in plan["source_updates"].items():
        row = by_source.get(source_id)
        if row is not None:
            _exact_fields(row, spec.get("expected", {}), f"source {source_id}", errors)

    if any(change.get("change_id") == plan["change_ledger_entry"]["change_id"] for change in ledger.get("changes", [])):
        errors.append("planned provenance-repair ledger entry already exists")

    if errors:
        raise SystemExit("PROVENANCE REPAIR A PRECONDITION FAILED:\n- " + "\n- ".join(errors))


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

    records = _records_by_id(canonical_out)
    occurrence = records[BRAZIL_OCCURRENCE]
    for key, value in plan["canonical_update"]["set"].items():
        occurrence[key] = copy.deepcopy(value)

    expected_assertion = _assertion_id(occurrence)
    if expected_assertion != plan["canonical_update"]["set"]["primary_source_assertion_id"]:
        raise ValueError(f"frozen Brazil assertion id mismatch: {expected_assertion}")

    canonical_out["version"] = plan["postconditions"]["canonical_registry_version"]
    canonical_out["reference_date"] = plan["review_date"]

    by_source = _sources_by_id(sources_out)
    for source_id, spec in plan["source_updates"].items():
        by_source[source_id].update(copy.deepcopy(spec["set"]))

    new_sources = copy.deepcopy(plan["new_sources"])
    if len(new_sources) != 1 or new_sources[0].get("source_id") != BRAZIL_CONSTITUTION:
        raise ValueError("plan must define exactly one Brazil constitutional source")
    sources_out["sources"].append(new_sources[0])
    sources_out["version"] = plan["postconditions"]["source_registry_version"]
    sources_out["reference_date"] = plan["review_date"]

    change_entry = copy.deepcopy(plan["change_ledger_entry"])
    if "committed_at" in change_entry:
        raise ValueError("committed_at must not be frozen in the research plan")
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
    if changed_occurrences != [BRAZIL_OCCURRENCE]:
        errors.append(f"unexpected canonical changes: {changed_occurrences}")

    for oid in before_records:
        before_timing = {field: before_records[oid].get(field) for field in TIMING_FIELDS}
        after_timing = {field: after_records[oid].get(field) for field in TIMING_FIELDS}
        if before_timing != after_timing:
            errors.append(f"timing changed for {oid}: {before_timing!r} -> {after_timing!r}")
            break

    occurrence = after_records[BRAZIL_OCCURRENCE]
    _exact_fields(occurrence, plan["canonical_update"]["set"], "Brazil post-state", errors)
    _exact_fields(occurrence, plan["canonical_update"]["must_preserve"], "Brazil preserved post-state", errors)

    before_ids = [s.get("source_id") for s in sources_before.get("sources", [])]
    after_ids = [s.get("source_id") for s in sources_after.get("sources", [])]
    if after_ids != before_ids + [BRAZIL_CONSTITUTION]:
        errors.append("source identity/order changed outside one appended constitutional source")

    before_sources = _sources_by_id(sources_before)
    after_sources = _sources_by_id(sources_after)
    changed_existing_sources = [sid for sid in before_ids if before_sources[sid] != after_sources[sid]]
    if set(changed_existing_sources) != {BRAZIL_TSE, SNB}:
        errors.append(f"unexpected existing source changes: {changed_existing_sources}")

    for source_id, spec in plan["source_updates"].items():
        _exact_fields(after_sources[source_id], spec["set"], f"post source {source_id}", errors)
    _exact_fields(after_sources[BRAZIL_CONSTITUTION], plan["new_sources"][0], "new Brazil constitutional source", errors)

    derived_counts = {
        BRAZIL_TSE: _source_dependency_count(canonical_after, BRAZIL_TSE),
        BRAZIL_CONSTITUTION: _source_dependency_count(canonical_after, BRAZIL_CONSTITUTION),
        SNB: _source_dependency_count(canonical_after, SNB),
    }
    expected_counts = {
        BRAZIL_TSE: post["brazil_tse_canonical_dependency_count"],
        BRAZIL_CONSTITUTION: post["brazil_constitution_canonical_dependency_count"],
        SNB: post["snb_canonical_dependency_count"],
    }
    if derived_counts != expected_counts:
        errors.append(f"post dependency counts mismatch: {derived_counts!r} != {expected_counts!r}")

    snb_before = [copy.deepcopy(r) for r in canonical_before.get("records", []) if r.get("source_id") == SNB]
    snb_after = [copy.deepcopy(r) for r in canonical_after.get("records", []) if r.get("source_id") == SNB]
    if snb_before != snb_after:
        errors.append("SNB canonical occurrences changed during source-scope repair")

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

    if expectations.get("automatic_canonical_commit") is not False:
        errors.append("automatic_canonical_commit not false")
    if expectations.get("google_calendar_write") is not False:
        errors.append("google_calendar_write not false")

    if errors:
        raise ValueError("PROVENANCE REPAIR A POST-STATE INVALID:\n- " + "\n- ".join(errors))

    return {
        "status": "PASS",
        "transaction": plan["transaction"],
        "canonical_version_before": canonical_before.get("version"),
        "canonical_version_after": canonical_after.get("version"),
        "canonical_record_count": canonical_after.get("record_count"),
        "source_version_before": sources_before.get("version"),
        "source_version_after": sources_after.get("version"),
        "source_count_before": len(sources_before.get("sources", [])),
        "source_count_after": len(sources_after.get("sources", [])),
        "change_ledger_version_before": ledger_before.get("version"),
        "change_ledger_version_after": ledger_after.get("version"),
        "biosecurity_overlay_checkpoint_before": (overlay_before.get("canonical_checkpoint") or {}).get("registry_version"),
        "biosecurity_overlay_checkpoint_after": (overlay_after.get("canonical_checkpoint") or {}).get("registry_version"),
        "changed_occurrence_ids": changed_occurrences,
        "changed_existing_source_ids": changed_existing_sources,
        "new_source_ids": [BRAZIL_CONSTITUTION],
        "source_dependency_counts_after": derived_counts,
        "brazil_inauguration_start_local": occurrence.get("start_local"),
        "automatic_canonical_commit": expectations.get("automatic_canonical_commit"),
        "google_calendar_write": expectations.get("google_calendar_write"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Guarded WORLD SIGNALS provenance-scope repair A")
    parser.add_argument("--apply", action="store_true", help=f"write the frozen four-file transaction; requires {APPLY_ENV}={APPLY_VALUE}")
    args = parser.parse_args()

    canonical_raw = CANONICAL_PATH.read_bytes()
    sources_raw = SOURCES_PATH.read_bytes()
    ledger_raw = LEDGER_PATH.read_bytes()
    overlay_raw = BIOSECURITY_OVERLAY_PATH.read_bytes()
    expectations_raw = EXPECTATIONS_PATH.read_bytes()
    runner_raw = LIVE_RUNNER_PATH.read_bytes()

    canonical = json.loads(canonical_raw)
    sources = json.loads(sources_raw)
    ledger = json.loads(ledger_raw)
    overlay = json.loads(overlay_raw)
    expectations = json.loads(expectations_raw)
    plan = load(PLAN_PATH)

    committed_at = (
        datetime.now(ZoneInfo("Australia/Melbourne")).isoformat(timespec="seconds")
        if args.apply
        else plan["change_ledger_entry"]["reviewed_at"]
    )
    canonical_out, sources_out, ledger_out, overlay_out, report = build_post_state(
        canonical,
        sources,
        ledger,
        overlay,
        expectations,
        plan,
        committed_at=committed_at,
    )
    report.update({
        "mode": "APPLY" if args.apply else "READ_ONLY_PREFLIGHT",
        "canonical_sha256_before": sha256(canonical_raw),
        "source_sha256_before": sha256(sources_raw),
        "ledger_sha256_before": sha256(ledger_raw),
        "biosecurity_overlay_sha256_before": sha256(overlay_raw),
        "monitor_expectations_sha256_before": sha256(expectations_raw),
        "live_monitor_runner_sha256_before": sha256(runner_raw),
    })

    if not args.apply:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    if os.environ.get(APPLY_ENV) != APPLY_VALUE:
        raise SystemExit(f"PROVENANCE REPAIR A APPLY REFUSED: set {APPLY_ENV}={APPLY_VALUE}")

    dump(CANONICAL_PATH, canonical_out)
    dump(SOURCES_PATH, sources_out)
    dump(LEDGER_PATH, ledger_out)
    dump(BIOSECURITY_OVERLAY_PATH, overlay_out)

    if EXPECTATIONS_PATH.read_bytes() != expectations_raw:
        raise SystemExit("monitor expectations changed during provenance repair")
    if LIVE_RUNNER_PATH.read_bytes() != runner_raw:
        raise SystemExit("live monitor runner changed during provenance repair")

    report.update({
        "canonical_sha256_after": sha256(CANONICAL_PATH.read_bytes()),
        "source_sha256_after": sha256(SOURCES_PATH.read_bytes()),
        "ledger_sha256_after": sha256(LEDGER_PATH.read_bytes()),
        "biosecurity_overlay_sha256_after": sha256(BIOSECURITY_OVERLAY_PATH.read_bytes()),
        "committed_at": committed_at,
    })
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
