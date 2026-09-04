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

PLAN_PATH = ROOT / "data/coverage/SOURCE_GOVERNANCE_P1B_BACKFILL_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
LIVE_RUNNER_PATH = ROOT / "scripts/run_live_monitor.py"

APPLY_ENV = "WORLD_SIGNALS_ALLOW_P1B_GOVERNANCE_APPLY"
APPLY_VALUE = "YES"
HELD_SOURCE_ID = "WSSRC-EL-BR-001"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sources_by_id(source_registry: dict) -> dict[str, dict]:
    return {source.get("source_id"): source for source in source_registry.get("sources", [])}


def _canonical_counts(canonical: dict) -> Counter:
    return Counter(
        record.get("source_id")
        for record in canonical.get("records", [])
        if record.get("source_id")
    )


def _brazil_inauguration_records(canonical: dict, guard: dict) -> list[dict]:
    return [
        record
        for record in canonical.get("records", [])
        if record.get("source_id") == guard["source_id"]
        and record.get("election_milestone_type") == guard["election_milestone_type"]
    ]


def _assert_brazil_inauguration(canonical: dict, guard: dict, errors: list[str]) -> None:
    matches = _brazil_inauguration_records(canonical, guard)
    if len(matches) != 1:
        errors.append(
            "Brazil inauguration guard expected exactly one TSE-linked "
            f"{guard['election_milestone_type']} record, found {len(matches)}"
        )
        return
    if matches[0].get("start_local") != guard["expected_start_local"]:
        errors.append(
            "Brazil inauguration start_local changed: "
            f"{matches[0].get('start_local')!r} != {guard['expected_start_local']!r}"
        )


def preflight(
    canonical: dict,
    source_registry: dict,
    expectations: dict,
    plan: dict,
) -> None:
    p = plan["preconditions"]
    errors: list[str] = []

    if str(canonical.get("version")) != str(p["canonical_registry_version"]):
        errors.append(
            f"canonical version {canonical.get('version')!r} != {p['canonical_registry_version']!r}"
        )
    if canonical.get("record_count") != p["canonical_record_count"]:
        errors.append("canonical record_count precondition failed")
    if len(canonical.get("records", [])) != p["canonical_record_count"]:
        errors.append("canonical records length precondition failed")

    if str(source_registry.get("version")) != str(p["source_registry_version"]):
        errors.append(
            f"source version {source_registry.get('version')!r} != {p['source_registry_version']!r}"
        )
    if len(source_registry.get("sources", [])) != p["source_count"]:
        errors.append("source count precondition failed")

    if str(expectations.get("version")) != str(p["monitor_expectations_version"]):
        errors.append(
            f"expectations version {expectations.get('version')!r} != {p['monitor_expectations_version']!r}"
        )
    if expectations.get("automatic_canonical_commit") is not False:
        errors.append("automatic canonical commit must remain false")
    if expectations.get("google_calendar_write") is not False:
        errors.append("Google Calendar write policy must remain false")

    sources = _sources_by_id(source_registry)
    counts = _canonical_counts(canonical)
    approved = set(plan["source_updates"])
    expected_approved = set(p["approved_source_dependency_counts"])
    selected = set(plan["selection"]["selected_source_ids"])
    if approved != expected_approved:
        errors.append(
            "plan source_updates do not exactly match frozen approved source ids: "
            f"{sorted(approved)} != {sorted(expected_approved)}"
        )
    if selected != approved:
        errors.append(
            "selection does not exactly match source_updates: "
            f"{sorted(selected)} != {sorted(approved)}"
        )
    if HELD_SOURCE_ID in approved:
        errors.append("Brazil TSE held source must not appear in source_updates")

    required_missing = p["required_missing_governance_fields"]
    for source_id, expected_count in p["approved_source_dependency_counts"].items():
        source = sources.get(source_id)
        if source is None:
            errors.append(f"approved source missing: {source_id}")
            continue
        actual_count = counts.get(source_id, 0)
        if actual_count != expected_count:
            errors.append(
                f"{source_id} canonical dependency count {actual_count} != {expected_count}"
            )
        if source.get("canonical_dependency_count") != expected_count:
            errors.append(
                f"{source_id} stored canonical_dependency_count "
                f"{source.get('canonical_dependency_count')!r} != {expected_count}"
            )
        for field in required_missing:
            if source.get(field) not in (None, ""):
                errors.append(
                    f"{source_id} {field} is already populated; refusing replay/overwrite"
                )

    held = sources.get(p["held_source_id"])
    if held is None:
        errors.append(f"held source missing: {p['held_source_id']}")
    else:
        held_count = counts.get(p["held_source_id"], 0)
        if held_count != p["held_source_canonical_dependency_count"]:
            errors.append(
                f"held TSE canonical dependency count {held_count} != "
                f"{p['held_source_canonical_dependency_count']}"
            )
        if held.get("canonical_dependency_count") != p["held_source_canonical_dependency_count"]:
            errors.append("held TSE stored canonical_dependency_count precondition failed")
        for field in required_missing:
            if held.get(field) not in (None, ""):
                errors.append(
                    f"held TSE source unexpectedly gained {field}; provenance repair must be reconciled first"
                )

    _assert_brazil_inauguration(canonical, p["brazil_inauguration_guard"], errors)

    if errors:
        raise SystemExit("P1-B GOVERNANCE PRECONDITION FAILED:\n- " + "\n- ".join(errors))


def changed_source_ids(before: dict, after: dict) -> list[str]:
    before_by_id = _sources_by_id(before)
    after_by_id = _sources_by_id(after)
    ids = set(before_by_id) | set(after_by_id)
    return sorted(
        source_id
        for source_id in ids
        if before_by_id.get(source_id) != after_by_id.get(source_id)
    )


def build_post_state(
    canonical: dict,
    source_registry: dict,
    expectations: dict,
    plan: dict,
) -> tuple[dict, dict]:
    sources_out = copy.deepcopy(source_registry)
    sources = _sources_by_id(sources_out)

    for source_id, spec in plan["source_updates"].items():
        sources[source_id].update(copy.deepcopy(spec["set"]))

    sources_out["version"] = plan["postconditions"]["source_registry_version"]
    sources_out["reference_date"] = plan["review_date"]

    report = validate_post_state(
        canonical,
        source_registry,
        sources_out,
        expectations,
        plan,
    )
    return sources_out, report


def validate_post_state(
    canonical: dict,
    source_registry_before: dict,
    source_registry_after: dict,
    expectations: dict,
    plan: dict,
) -> dict:
    post = plan["postconditions"]
    errors: list[str] = []

    if str(canonical.get("version")) != str(post["canonical_registry_version"]):
        errors.append("canonical version changed")
    if canonical.get("record_count") != post["canonical_record_count"]:
        errors.append("canonical record count changed")
    if len(canonical.get("records", [])) != post["canonical_record_count"]:
        errors.append("canonical records length changed")

    if str(source_registry_after.get("version")) != str(post["source_registry_version"]):
        errors.append("post source registry version mismatch")
    if len(source_registry_after.get("sources", [])) != post["source_count"]:
        errors.append("post source count changed")

    before_ids = [row.get("source_id") for row in source_registry_before.get("sources", [])]
    after_ids = [row.get("source_id") for row in source_registry_after.get("sources", [])]
    if before_ids != after_ids:
        errors.append("source identity/order changed during governance-only transaction")
    if len(after_ids) != len(set(after_ids)):
        errors.append("duplicate source_id after migration")

    actual_changed = changed_source_ids(source_registry_before, source_registry_after)
    expected_changed = sorted(post["changed_source_ids"])
    if actual_changed != expected_changed:
        errors.append(
            f"changed source ids {actual_changed} != frozen approved set {expected_changed}"
        )

    before = _sources_by_id(source_registry_before)
    after = _sources_by_id(source_registry_after)
    for source_id, spec in plan["source_updates"].items():
        row = after[source_id]
        for field, value in spec["set"].items():
            if row.get(field) != value:
                errors.append(
                    f"{source_id} {field}: expected {value!r}, found {row.get(field)!r}"
                )
        untouched_keys = set(before[source_id]) - set(spec["set"])
        for key in untouched_keys:
            if after[source_id].get(key) != before[source_id].get(key):
                errors.append(f"{source_id} non-P1-B field changed: {key}")

    if after.get(HELD_SOURCE_ID) != before.get(HELD_SOURCE_ID):
        errors.append("Brazil TSE held source changed")

    if str(expectations.get("version")) != str(post["monitor_expectations_version"]):
        errors.append("monitor expectations version changed")
    if expectations.get("automatic_canonical_commit") is not post["automatic_canonical_commit"]:
        errors.append("automatic canonical commit changed")
    if expectations.get("google_calendar_write") is not post["google_calendar_write"]:
        errors.append("Google Calendar write policy changed")

    guard = plan["preconditions"]["brazil_inauguration_guard"]
    _assert_brazil_inauguration(canonical, guard, errors)

    validation = validate_registry(canonical, source_registry_after)
    errors.extend(validation.errors)

    if errors:
        raise ValueError("P1-B GOVERNANCE POSTCONDITION FAILED:\n- " + "\n- ".join(errors))

    return {
        "project": "WORLD SIGNALS",
        "transaction": "SOURCE_GOVERNANCE_P1B_BACKFILL",
        "status": "PASS",
        "canonical_registry_version": canonical.get("version"),
        "canonical_record_count": canonical.get("record_count"),
        "source_registry_version_before": source_registry_before.get("version"),
        "source_registry_version_after": source_registry_after.get("version"),
        "source_count": len(source_registry_after.get("sources", [])),
        "changed_source_ids": actual_changed,
        "held_source_id": HELD_SOURCE_ID,
        "held_source_unchanged": True,
        "brazil_inauguration_start_local": guard["expected_start_local"],
        "monitor_expectations_version": expectations.get("version"),
        "automatic_canonical_commit": expectations.get("automatic_canonical_commit"),
        "google_calendar_write": expectations.get("google_calendar_write"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check or apply the guarded WORLD SIGNALS P1-B source-governance "
            "backfill. Default is read-only preflight/post-state simulation."
        )
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            f"write data/sources/registry.json only; requires {APPLY_ENV}={APPLY_VALUE}"
        ),
    )
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
    report.update(
        {
            "mode": "APPLY" if args.apply else "READ_ONLY_PREFLIGHT",
            "canonical_sha256_before": stable_hash(canonical_raw),
            "monitor_expectations_sha256_before": stable_hash(expectations_raw),
            "live_monitor_runner_sha256_before": stable_hash(live_runner_raw),
        }
    )

    if args.apply:
        if os.environ.get(APPLY_ENV) != APPLY_VALUE:
            raise SystemExit(
                f"P1-B APPLY REFUSED: set {APPLY_ENV}={APPLY_VALUE} after reviewed approval"
            )
        SOURCES_PATH.write_text(
            json.dumps(post_sources, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        if CANONICAL_PATH.read_bytes() != canonical_raw:
            raise SystemExit("P1-B APPLY FAILED CLOSED: canonical registry bytes changed")
        if EXPECTATIONS_PATH.read_bytes() != expectations_raw:
            raise SystemExit("P1-B APPLY FAILED CLOSED: monitor expectations bytes changed")
        if LIVE_RUNNER_PATH.read_bytes() != live_runner_raw:
            raise SystemExit("P1-B APPLY FAILED CLOSED: live monitor runner bytes changed")

        written = load(SOURCES_PATH)
        validate_post_state(canonical, sources, written, expectations, plan)
        report["source_registry_sha256_after"] = stable_hash(SOURCES_PATH.read_bytes())
    else:
        if SOURCES_PATH.read_bytes() != sources_raw:
            raise SystemExit("P1-B READ-ONLY PREFLIGHT FAILED: source registry bytes changed")

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
