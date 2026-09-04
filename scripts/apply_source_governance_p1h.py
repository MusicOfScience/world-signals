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

from world_signals.validation import validate_registry

PLAN_PATH = ROOT / "data/coverage/SOURCE_GOVERNANCE_P1H_BACKFILL_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
LIVE_RUNNER_PATH = ROOT / "scripts/run_live_monitor.py"

APPLY_ENV = "WORLD_SIGNALS_ALLOW_P1H_GOVERNANCE_APPLY"
APPLY_VALUE = "YES"
HELD_SOURCE_IDS = {"WSSRC-EL-BR-001", "WSSRC-CB-009"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sources_by_id(registry: dict) -> dict[str, dict]:
    return {row.get("source_id"): row for row in registry.get("sources", [])}


def _canonical_counts(canonical: dict) -> Counter:
    return Counter(r.get("source_id") for r in canonical.get("records", []) if r.get("source_id"))


def _brazil_inauguration_records(canonical: dict, guard: dict) -> list[dict]:
    return [
        row for row in canonical.get("records", [])
        if row.get("source_id") == guard["source_id"]
        and row.get("election_milestone_type") == guard["election_milestone_type"]
    ]


def _assert_brazil_guard(canonical: dict, guard: dict, errors: list[str]) -> None:
    rows = _brazil_inauguration_records(canonical, guard)
    if len(rows) != 1:
        errors.append(f"Brazil inauguration guard expected one record, found {len(rows)}")
    elif rows[0].get("start_local") != guard["expected_start_local"]:
        errors.append("Brazil inauguration start_local changed")


def _assert_held_sources(
    sources: dict[str, dict], counts: Counter, required_missing: list[str], plan: dict, errors: list[str]
) -> None:
    brazil = plan["preconditions"]["brazil_inauguration_guard"]
    tse = sources.get(brazil["source_id"])
    if tse is None:
        errors.append("held TSE source missing")
    else:
        expected = brazil["expected_canonical_dependency_count"]
        if counts.get(brazil["source_id"], 0) != expected or tse.get("canonical_dependency_count") != expected:
            errors.append("held TSE dependency count changed")
        for field in required_missing:
            if tse.get(field) not in (None, ""):
                errors.append(f"held TSE unexpectedly gained {field}")

    snb_guard = plan["preconditions"]["snb_scope_guard"]
    snb = sources.get(snb_guard["source_id"])
    if snb is None:
        errors.append("held SNB source missing")
    else:
        expected = snb_guard["expected_canonical_dependency_count"]
        if counts.get(snb_guard["source_id"], 0) != expected or snb.get("canonical_dependency_count") != expected:
            errors.append("held SNB dependency count changed")
        if snb.get("authoritative_url") != snb_guard["expected_authoritative_url"]:
            errors.append("held SNB source scope changed; review repair before P1-H")
        for field in required_missing:
            if snb.get(field) not in (None, ""):
                errors.append(f"held SNB unexpectedly gained {field}")


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

    sources = _sources_by_id(source_registry)
    counts = _canonical_counts(canonical)
    selected = set(plan["selection"]["selected_source_ids"])
    updates = set(plan["source_updates"])
    frozen = set(p["approved_source_dependency_counts"])
    if not (selected == updates == frozen):
        errors.append("selected/update/frozen source sets differ")
    if updates & HELD_SOURCE_IDS:
        errors.append("held source included in P1-H update set")
    if sum(p["approved_source_dependency_counts"].values()) != plan["selection"]["canonical_dependency_total"]:
        errors.append("frozen dependency total mismatch")

    required_missing = p["required_missing_governance_fields"]
    for source_id, expected in p["approved_source_dependency_counts"].items():
        row = sources.get(source_id)
        if row is None:
            errors.append(f"approved source missing: {source_id}")
            continue
        if counts.get(source_id, 0) != expected or row.get("canonical_dependency_count") != expected:
            errors.append(f"{source_id} dependency count changed")
        for field in required_missing:
            if row.get(field) not in (None, ""):
                errors.append(f"{source_id} {field} already populated; refusing replay")

    _assert_held_sources(sources, counts, required_missing, plan, errors)
    _assert_brazil_guard(canonical, p["brazil_inauguration_guard"], errors)
    if errors:
        raise SystemExit("P1-H GOVERNANCE PRECONDITION FAILED:\n- " + "\n- ".join(errors))


def changed_source_ids(before: dict, after: dict) -> list[str]:
    b = _sources_by_id(before)
    a = _sources_by_id(after)
    return sorted(sid for sid in set(b) | set(a) if b.get(sid) != a.get(sid))


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

    before = _sources_by_id(before_registry)
    after = _sources_by_id(after_registry)
    for source_id, spec in plan["source_updates"].items():
        for field, value in spec["set"].items():
            if after[source_id].get(field) != value:
                errors.append(f"{source_id} {field} classification mismatch")
        for key in set(before[source_id]) - set(spec["set"]):
            if after[source_id].get(key) != before[source_id].get(key):
                errors.append(f"{source_id} non-P1-H field changed: {key}")

    for held_id in HELD_SOURCE_IDS:
        if after.get(held_id) != before.get(held_id):
            errors.append(f"held source changed: {held_id}")

    if str(expectations.get("version")) != str(post["monitor_expectations_version"]):
        errors.append("monitor expectations changed")
    if expectations.get("automatic_canonical_commit") is not post["automatic_canonical_commit"]:
        errors.append("automatic canonical commit changed")
    if expectations.get("google_calendar_write") is not post["google_calendar_write"]:
        errors.append("Google Calendar write changed")

    guard = plan["preconditions"]["brazil_inauguration_guard"]
    _assert_brazil_guard(canonical, guard, errors)
    validation = validate_registry(canonical, after_registry)
    errors.extend(validation.errors)
    if errors:
        raise ValueError("P1-H GOVERNANCE POSTCONDITION FAILED:\n- " + "\n- ".join(errors))

    return {
        "project": "WORLD SIGNALS",
        "transaction": "SOURCE_GOVERNANCE_P1H_BACKFILL",
        "status": "PASS",
        "canonical_registry_version": canonical.get("version"),
        "canonical_record_count": canonical.get("record_count"),
        "source_registry_version_before": before_registry.get("version"),
        "source_registry_version_after": after_registry.get("version"),
        "source_count": len(after_registry.get("sources", [])),
        "changed_source_ids": actual_changed,
        "held_source_ids": sorted(HELD_SOURCE_IDS),
        "held_sources_unchanged": True,
        "brazil_inauguration_start_local": guard["expected_start_local"],
        "monitor_expectations_version": expectations.get("version"),
        "automatic_canonical_commit": expectations.get("automatic_canonical_commit"),
        "google_calendar_write": expectations.get("google_calendar_write")
    }


def build_post_state(canonical: dict, source_registry: dict, expectations: dict, plan: dict) -> tuple[dict, dict]:
    out = copy.deepcopy(source_registry)
    by_id = _sources_by_id(out)
    for source_id, spec in plan["source_updates"].items():
        by_id[source_id].update(copy.deepcopy(spec["set"]))
    out["version"] = plan["postconditions"]["source_registry_version"]
    out["reference_date"] = plan["review_date"]
    return out, validate_post_state(canonical, source_registry, out, expectations, plan)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check or apply guarded WORLD SIGNALS P1-H source-governance backfill. Default is read-only simulation.")
    parser.add_argument("--apply", action="store_true", help=f"write data/sources/registry.json only; requires {APPLY_ENV}={APPLY_VALUE}")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    canonical_raw = CANONICAL_PATH.read_bytes()
    sources_raw = SOURCES_PATH.read_bytes()
    expectations_raw = EXPECTATIONS_PATH.read_bytes()
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
        "live_monitor_runner_sha256_before": stable_hash(live_runner_raw)
    })

    if args.apply:
        if os.environ.get(APPLY_ENV) != APPLY_VALUE:
            raise SystemExit(f"P1-H APPLY REFUSED: set {APPLY_ENV}={APPLY_VALUE} after reviewed approval")
        SOURCES_PATH.write_text(json.dumps(post_sources, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if CANONICAL_PATH.read_bytes() != canonical_raw:
            raise SystemExit("P1-H APPLY FAILED CLOSED: canonical registry bytes changed")
        if EXPECTATIONS_PATH.read_bytes() != expectations_raw:
            raise SystemExit("P1-H APPLY FAILED CLOSED: monitor expectations bytes changed")
        if LIVE_RUNNER_PATH.read_bytes() != live_runner_raw:
            raise SystemExit("P1-H APPLY FAILED CLOSED: live monitor runner bytes changed")
        validate_post_state(canonical, sources, load(SOURCES_PATH), expectations, plan)
        report["source_registry_sha256_after"] = stable_hash(SOURCES_PATH.read_bytes())

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
