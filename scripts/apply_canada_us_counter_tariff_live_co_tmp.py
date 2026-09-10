#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.canada_us_counter_tariff_co import (
    EVIDENCE_IDS,
    OBSERVATION_ID,
    target_evidence,
    target_live_schema,
    target_observations,
    validate_co_contract,
)
from world_signals.live_intelligence import validate_live_intelligence

PLAN_PATH = ROOT / "data/live_intelligence/CANADA_US_COUNTER_TARIFF_LIVE_CO_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/live_intelligence/CANADA_US_COUNTER_TARIFF_LIVE_CO_PAYLOAD_v0.1.json"
SCHEMA_PATH = ROOT / "data/live_intelligence/schema.json"
OBSERVATIONS_PATH = ROOT / "data/live_intelligence/observations.json"
EVIDENCE_PATH = ROOT / "data/live_intelligence/evidence_registry.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
MONITOR_PATH = ROOT / "data/monitor/expectations.json"
ANALYSIS_SCHEMA_PATH = ROOT / "data/analysis/schema.json"
ANALYSIS_REVIEWS_PATH = ROOT / "data/analysis/event_reviews.json"
ANALYSIS_EVIDENCE_PATH = ROOT / "data/analysis/evidence_registry.json"
APPLY_ENV = "WORLD_SIGNALS_APPLY_CANADA_US_COUNTER_TARIFF_LIVE_CO"
APPLY_VALUE = "REVIEWED_APPLY"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def by_id(rows: list[dict[str, Any]], key: str, value: str) -> dict[str, Any] | None:
    matches = [row for row in rows if row.get(key) == value]
    require(len(matches) <= 1, f"CO duplicate {key}={value}")
    return matches[0] if matches else None


def production_live_input_count(reviews: dict[str, Any]) -> int:
    return sum(len(row.get("live_inputs") or []) for row in reviews.get("reviews", []))


def production_analysis_revision_count(reviews: dict[str, Any]) -> int:
    return sum(1 for row in reviews.get("reviews", []) if row.get("revision_of_analysis_id"))


def assert_prestate_or_reviewed_descendant(plan: dict[str, Any]) -> bool:
    canonical = load(CANONICAL_PATH)
    sources = load(SOURCES_PATH)
    ledger = load(LEDGER_PATH)
    monitor = load(MONITOR_PATH)
    schema = load(SCHEMA_PATH)
    observations = load(OBSERVATIONS_PATH)
    evidence = load(EVIDENCE_PATH)
    analysis_schema = load(ANALYSIS_SCHEMA_PATH)
    reviews = load(ANALYSIS_REVIEWS_PATH)
    analysis_evidence = load(ANALYSIS_EVIDENCE_PATH)
    pre = plan["pre_state"]

    obs = by_id(observations.get("observations", []), "observation_id", OBSERVATION_ID)
    evs = [by_id(evidence.get("evidence", []), "evidence_id", evidence_id) for evidence_id in EVIDENCE_IDS]
    any_evidence = any(row is not None for row in evs)
    all_evidence = all(row is not None for row in evs)
    require(not any_evidence or all_evidence, "CO partial evidence materialisation detected")
    require(bool(obs) == all_evidence, "CO partial observation/evidence materialisation detected")
    descendant = obs is not None

    if not descendant:
        require(str(canonical.get("version")) == pre["canonical_registry_version"], "CO exact Canonical version drift")
        require(len(canonical.get("records", [])) == pre["canonical_record_count"], "CO exact Canonical population drift")
        require(str(sources.get("version")) == pre["source_registry_version"], "CO exact Source Registry version drift")
        require(len(sources.get("sources", [])) == pre["source_count"], "CO exact Source population drift")
        require(str(ledger.get("version")) == pre["change_ledger_version"], "CO exact Change Ledger version drift")
        require(len(ledger.get("changes", [])) == pre["change_ledger_count"], "CO exact Change Ledger population drift")
        require(str(monitor.get("version")) == pre["monitor_expectations_version"], "CO exact Monitor expectations version drift")
        require(len(monitor.get("adapters", [])) == pre["monitor_adapter_count"], "CO exact Monitor adapter population drift")
        require(str(schema.get("version")) == pre["live_schema_version"], "CO exact Live schema drift")
        require(len(observations.get("observations", [])) == pre["live_observation_count"], "CO exact Live observation population drift")
        require(len(evidence.get("evidence", [])) == pre["live_evidence_count"], "CO exact Live evidence population drift")
        require(str(analysis_schema.get("version")) == pre["analysis_schema_version"], "CO exact Analysis schema drift")
        require(len(reviews.get("reviews", [])) == pre["analysis_review_count"], "CO exact Analysis review population drift")
        require(len(analysis_evidence.get("evidence", [])) == pre["analysis_evidence_count"], "CO exact Analysis evidence population drift")
        require(production_live_input_count(reviews) == pre["production_live_input_count"], "CO production Live-input prestate drift")
        require(production_analysis_revision_count(reviews) == pre["production_analysis_revision_count"], "CO production Analysis-revision prestate drift")

    require(monitor.get("automatic_canonical_commit") is False, "CO automatic Canonical commit gate opened")
    require(monitor.get("google_calendar_write") is False, "CO Google Calendar write gate opened")
    require((ROOT / "OPEC_QUARANTINE.md").is_file(), "CO OPEC quarantine record missing")
    require((ROOT / "tests/test_opec_quarantine_cf.py").is_file(), "CO OPEC quarantine regression test missing")
    return descendant


def build_target(plan: dict[str, Any], payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    schema = load(SCHEMA_PATH)
    observations = load(OBSERVATIONS_PATH)
    evidence = load(EVIDENCE_PATH)
    target_schema = target_live_schema(schema, plan)
    target_obs = target_observations(observations, payload, plan)
    target_ev = target_evidence(evidence, payload, plan)
    errors = validate_co_contract(target_schema, target_obs, target_ev, plan)
    require(not errors, "CO pure contract failed: " + "; ".join(errors))
    live_report = validate_live_intelligence(target_schema, target_ev, target_obs, load(CANONICAL_PATH))
    require(live_report.ok, "CO Live validator simulation failed: " + "; ".join(live_report.errors))
    return target_schema, target_obs, target_ev


def verify_materialised(plan: dict[str, Any]) -> None:
    schema = load(SCHEMA_PATH)
    observations = load(OBSERVATIONS_PATH)
    evidence = load(EVIDENCE_PATH)
    errors = validate_co_contract(schema, observations, evidence, plan)
    require(not errors, "CO materialised contract failed: " + "; ".join(errors))
    report = validate_live_intelligence(schema, evidence, observations, load(CANONICAL_PATH))
    require(report.ok, "CO materialised Live validation failed: " + "; ".join(report.errors))
    row = by_id(observations["observations"], "observation_id", OBSERVATION_ID)
    require(row is not None and row.get("canonical_links") == [], "CO observation acquired a Canonical link")
    print(json.dumps({
        "schema_version": schema["version"],
        "observations": len(observations["observations"]),
        "evidence": len(evidence["evidence"]),
        "observation_id": OBSERVATION_ID,
        "evidence_ids": list(EVIDENCE_IDS),
        "canonical_links": row["canonical_links"],
        "automatic_canonical_commit": row["automatic_canonical_commit"],
        "google_calendar_write": row["google_calendar_write"],
    }, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description="Guarded CO Canada counter-tariff Live materialisation helper")
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    require(sum(bool(x) for x in (args.simulate, args.apply, args.verify)) == 1, "choose exactly one of --simulate/--apply/--verify")

    plan = load(PLAN_PATH)
    payload = load(PAYLOAD_PATH)
    descendant = assert_prestate_or_reviewed_descendant(plan)

    if args.simulate:
        target_schema, target_obs, target_ev = build_target(plan, payload)
        print(json.dumps({
            "mode": "simulate",
            "already_materialised": descendant,
            "schema_version": target_schema["version"],
            "observations": len(target_obs["observations"]),
            "evidence": len(target_ev["evidence"]),
            "observation_id": OBSERVATION_ID,
        }, sort_keys=True))
        return 0

    if args.verify:
        require(descendant, "CO verify requested before materialisation")
        verify_materialised(plan)
        return 0

    require(os.environ.get(APPLY_ENV) == APPLY_VALUE, f"CO --apply requires {APPLY_ENV}={APPLY_VALUE}")
    require(not descendant, "CO reviewed target is already materialised")
    target_schema, target_obs, target_ev = build_target(plan, payload)
    SCHEMA_PATH.write_text(dump(target_schema), encoding="utf-8")
    OBSERVATIONS_PATH.write_text(dump(target_obs), encoding="utf-8")
    EVIDENCE_PATH.write_text(dump(target_ev), encoding="utf-8")
    verify_materialised(plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
