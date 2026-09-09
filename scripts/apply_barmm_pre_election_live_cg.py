#!/usr/bin/env python3
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/live_intelligence/BARMM_PRE_ELECTION_LIVE_CG_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/live_intelligence/BARMM_PRE_ELECTION_LIVE_CG_PAYLOAD_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
LIVE_SCHEMA_PATH = ROOT / "data/live_intelligence/schema.json"
LIVE_OBSERVATIONS_PATH = ROOT / "data/live_intelligence/observations.json"
LIVE_EVIDENCE_PATH = ROOT / "data/live_intelligence/evidence_registry.json"
ANALYSIS_SCHEMA_PATH = ROOT / "data/analysis/schema.json"
ANALYSIS_REVIEWS_PATH = ROOT / "data/analysis/event_reviews.json"
ANALYSIS_EVIDENCE_PATH = ROOT / "data/analysis/evidence_registry.json"
APPLY_ENV = "WORLD_SIGNALS_APPLY_BARMM_PRE_ELECTION_LIVE_CG"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def by_id(rows: list[dict[str, Any]], key: str, value: str) -> dict[str, Any] | None:
    matches = [row for row in rows if row.get(key) == value]
    require(len(matches) <= 1, f"CG duplicate {key}={value}")
    return matches[0] if matches else None


def production_analysis_revision_count(reviews: dict[str, Any]) -> int:
    return sum(1 for row in reviews.get("reviews", []) if row.get("revision_of_analysis_id"))


def production_live_input_count(reviews: dict[str, Any]) -> int:
    return sum(len(row.get("live_inputs") or []) for row in reviews.get("reviews", []))


def assert_upstream_prestate(plan: dict[str, Any]) -> None:
    pre = plan["pre_state"]
    canonical = load(CANONICAL_PATH)
    sources = load(SOURCES_PATH)
    expectations = load(EXPECTATIONS_PATH)
    analysis_schema = load(ANALYSIS_SCHEMA_PATH)
    reviews = load(ANALYSIS_REVIEWS_PATH)
    analysis_evidence = load(ANALYSIS_EVIDENCE_PATH)

    require(canonical.get("version") == pre["canonical_registry_version"], "CG Canonical version drift")
    require(len(canonical.get("records", [])) == pre["canonical_record_count"], "CG Canonical population drift")
    require(sources.get("version") == pre["source_registry_version"], "CG Source Registry version drift")
    require(len(sources.get("sources", [])) == pre["source_count"], "CG Source population drift")
    require(expectations.get("version") == pre["monitor_expectations_version"], "CG Monitor expectations drift")
    require(len(expectations.get("adapters", [])) == pre["monitor_adapter_count"], "CG Monitor adapter count drift")
    require(analysis_schema.get("version") == pre["analysis_schema_version"], "CG Analysis schema drift")
    require(len(reviews.get("reviews", [])) == pre["analysis_review_count"], "CG Analysis review count drift")
    require(len(analysis_evidence.get("evidence", [])) == pre["analysis_evidence_count"], "CG Analysis evidence count drift")
    require(production_analysis_revision_count(reviews) == pre["production_analysis_revision_count"], "CG Analysis revision count drift")
    require(production_live_input_count(reviews) == pre["production_live_input_count"], "CG production live_inputs drift")

    target = by_id(canonical.get("records", []), "occurrence_id", plan["target"]["canonical_occurrence_id"])
    require(target is not None, "CG target Canonical BARMM occurrence missing")
    require(target.get("series_id") == "WSER-EL-PH-BARMM-PE", "CG BARMM series identity drift")
    timing = target.get("timing") or {}
    require(timing.get("timing_type") == "CIVIL_DATE", "CG BARMM timing type drift")
    require(timing.get("start_local") == "2026-09-14", "CG BARMM Canonical date drift")
    require(timing.get("source_timezone") == "Asia/Manila", "CG BARMM native timezone drift")
    require(timing.get("start_utc") is None, "CG BARMM must not acquire synthetic UTC timestamp")
    require(target.get("lifecycle_status") == "PLANNED", "CG BARMM lifecycle drift")
    require(target.get("certainty_status") == "CONFIRMED", "CG BARMM certainty drift")


def build_target(observed_at_utc: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    plan = load(PLAN_PATH)
    payload = load(PAYLOAD_PATH)
    schema = load(LIVE_SCHEMA_PATH)
    observations = load(LIVE_OBSERVATIONS_PATH)
    evidence = load(LIVE_EVIDENCE_PATH)
    pre = plan["pre_state"]

    obs_template = deepcopy(payload["observation_template"])
    evidence_row = deepcopy(payload["live_evidence"][0])
    obs_id = obs_template["observation_id"]
    ev_id = evidence_row["evidence_id"]
    existing_obs = by_id(observations.get("observations", []), "observation_id", obs_id)
    existing_ev = by_id(evidence.get("evidence", []), "evidence_id", ev_id)
    require(bool(existing_obs) == bool(existing_ev), "CG partial materialization detected")

    if existing_obs:
        require(schema.get("version") == "0.7", "CG reviewed Live schema drift")
        return schema, observations, evidence

    require(schema.get("version") == pre["live_schema_version"], "CG Live schema prestate drift")
    require(len(observations.get("observations", [])) == pre["live_observation_count"], "CG Live observation prestate drift")
    require(len(evidence.get("evidence", [])) == pre["live_evidence_count"], "CG Live evidence prestate drift")

    obs_template["observed_at_utc"] = observed_at_utc

    new_schema = deepcopy(schema)
    new_schema["version"] = "0.7"
    new_schema["reference_date"] = "2026-09-10"
    new_schema["population_policy"] = {
        "mode": "CONTROLLED_CANONICAL_CONTEXT_SPECIMEN",
        "production_population_allowed": True,
        "evidence_population_allowed": True,
        "maximum_observation_count": 7,
        "maximum_evidence_count": 10,
        "automatic_ingestion_allowed": False,
        "existing_analysis_evidence_migration_allowed": False,
        "public_observation_projection_allowed": False,
        "reason": "CG adds exactly one pressure-audited BARMM pre-election INSTITUTIONAL_DEVELOPMENT linked CONTEXT_FOR the existing 14 September 2026 Canonical election occurrence."
    }
    guardrails = list(new_schema.get("guardrails") or [])
    old_gate = "A seventh Live observation, broader ingestion, second production Live-to-Analysis link or first production Analysis revision requires another pressure audit."
    guardrails = [item for item in guardrails if item != old_gate]
    additions = [
        "BF v0.6 remains the frozen six-observation/nine-evidence checkpoint; CG is the separately pressure-audited seventh observation.",
        "CG v0.7 adds one primary-confirmed BARMM pre-election INSTITUTIONAL_DEVELOPMENT with a reviewed CONTEXT_FOR link to WSO-EL-PH-BARMM-20260914.",
        "CG Live evidence has no Canonical provenance or timing authority; the COMELEC-governed 14 September 2026 election identity remains unchanged.",
        "CG does not infer a real-world signing timestamp from a 9 September publication date or the source wording 'recently'.",
        "Public observation projection, automatic ingestion, automatic Canonical commit and Google Calendar writes remain prohibited in CG v0.7.",
        "An eighth Live observation, automatic context linking, second production Live-to-Analysis link, further Analysis revision or NHC Monitor activation requires another pressure audit."
    ]
    for item in additions:
        if item not in guardrails:
            guardrails.append(item)
    new_schema["guardrails"] = guardrails
    new_schema["cg_checkpoint"] = {
        "schema_version": "0.7",
        "observations_version": "0.7",
        "evidence_version": "0.7",
        "population_state": "CONTROLLED_CANONICAL_CONTEXT_SPECIMEN",
        "observation_count": 7,
        "evidence_count": 10,
        "base_main_sha": plan["base_main_sha"],
        "historical_contract": "CG adds one reviewed Southeast Asia elections-context Live observation and exercises CONTEXT_FOR without changing Canonical, Monitor or Analysis state."
    }

    new_observations = deepcopy(observations)
    new_observations["version"] = "0.7"
    new_observations["reference_date"] = "2026-09-10"
    new_observations["population_state"] = "CONTROLLED_CANONICAL_CONTEXT_SPECIMEN"
    new_observations["observations"].append(obs_template)
    new_observations["scope_note"] = "Bounded reviewed internal Live Intelligence store through CG: seven observations, including the first reviewed CONTEXT_FOR link from current pre-election institutional context to an existing Canonical occurrence. Public projection and automatic ingestion remain closed."

    new_evidence = deepcopy(evidence)
    new_evidence["version"] = "0.7"
    new_evidence["reference_date"] = "2026-09-10"
    new_evidence["population_state"] = "CONTROLLED_CANONICAL_CONTEXT_SPECIMEN"
    new_evidence["evidence"].append(evidence_row)
    new_evidence["scope_note"] = "Evidence supports the bounded reviewed Live store through CG. Live evidence remains separate from Canonical provenance and Analysis evidence; public observation projection remains closed."

    return new_schema, new_observations, new_evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--observed-at-utc")
    args = parser.parse_args()
    require(args.check ^ args.apply, "choose exactly one of --check or --apply")

    plan = load(PLAN_PATH)
    assert_upstream_prestate(plan)
    observed_at = args.observed_at_utc or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    require(observed_at.endswith("Z"), "CG observed_at_utc must be UTC Z time")
    schema, observations, evidence = build_target(observed_at)

    target = plan["target_state"]
    require(schema.get("version") == target["live_schema_version"], "CG target schema version mismatch")
    require(len(observations.get("observations", [])) == target["live_observation_count"], "CG target observation count mismatch")
    require(len(evidence.get("evidence", [])) == target["live_evidence_count"], "CG target evidence count mismatch")
    obs = by_id(observations["observations"], "observation_id", plan["target"]["observation_id"])
    require(obs is not None, "CG target observation missing")
    require(obs.get("canonical_links") == [{"occurrence_id": "WSO-EL-PH-BARMM-20260914", "relationship": "CONTEXT_FOR"}], "CG CONTEXT_FOR contract drift")
    require("event_time" not in obs, "CG must not manufacture event_time")
    require(obs.get("automatic_canonical_commit") is False, "CG automatic Canonical commit must remain false")
    require(obs.get("google_calendar_write") is False, "CG Calendar write must remain false")

    if args.check:
        print(json.dumps({"verdict": "CG_SIMULATION_VALID", "observations": len(observations["observations"]), "evidence": len(evidence["evidence"]), "canonical_link": obs["canonical_links"][0]}, sort_keys=True))
        return 0

    require(os.environ.get(APPLY_ENV) == "YES", f"set {APPLY_ENV}=YES to apply")
    LIVE_SCHEMA_PATH.write_text(dump(schema), encoding="utf-8")
    LIVE_OBSERVATIONS_PATH.write_text(dump(observations), encoding="utf-8")
    LIVE_EVIDENCE_PATH.write_text(dump(evidence), encoding="utf-8")
    print(json.dumps({"verdict": "CG_MATERIALIZED_REVIEWED_LIVE_CONTEXT", "observed_at_utc": obs["observed_at_utc"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
