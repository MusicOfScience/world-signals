#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.live_intelligence import validate_live_intelligence

CANONICAL_PATH = ROOT / "data/canonical/registry.json"
CANONICAL_SCHEMA_PATH = ROOT / "data/canonical/schema.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
OPERATIONS_PATH = ROOT / "data/monitor/operations_policy.json"
ANALYSIS_SCHEMA_PATH = ROOT / "data/analysis/schema.json"
ANALYSIS_REVIEWS_PATH = ROOT / "data/analysis/event_reviews.json"
ANALYSIS_EVIDENCE_PATH = ROOT / "data/analysis/evidence_registry.json"
LIVE_SCHEMA_PATH = ROOT / "data/live_intelligence/schema.json"
LIVE_OBSERVATIONS_PATH = ROOT / "data/live_intelligence/observations.json"
LIVE_EVIDENCE_PATH = ROOT / "data/live_intelligence/evidence_registry.json"
PLAN_PATH = ROOT / "data/live_intelligence/NEPAL_RASUWA_FLOOD_LIVE_INTELLIGENCE_AW_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/live_intelligence/NEPAL_RASUWA_FLOOD_LIVE_INTELLIGENCE_AW_PAYLOAD_v0.1.json"
AUDIT_PATH = ROOT / "data/live_intelligence/NEPAL_RASUWA_FLOOD_LIVE_INTELLIGENCE_AW_TRANSACTION_AUDIT_v0.1.md"

APPLY_ENV = "WORLD_SIGNALS_APPLY_LIVE_INTELLIGENCE_AW"

PROTECTED = {
    "canonical_registry": CANONICAL_PATH,
    "canonical_schema": CANONICAL_SCHEMA_PATH,
    "source_registry": SOURCES_PATH,
    "change_ledger": LEDGER_PATH,
    "biosecurity_overlay": OVERLAY_PATH,
    "monitor_expectations": EXPECTATIONS_PATH,
    "monitor_operations_policy": OPERATIONS_PATH,
    "analysis_schema": ANALYSIS_SCHEMA_PATH,
    "analysis_reviews": ANALYSIS_REVIEWS_PATH,
    "analysis_evidence": ANALYSIS_EVIDENCE_PATH,
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_hashes() -> dict[str, str]:
    return {name: sha256(path) for name, path in PROTECTED.items()}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def exact_timestamp_series_rows(reviews: dict[str, Any]) -> int:
    return sum(
        1
        for review in reviews.get("reviews", [])
        for movement in (review.get("what_moved") or [])
        if movement.get("measurement_precision") == "EXACT_TIMESTAMP_SERIES"
    )


def assert_pre(plan: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    pre = plan["pre_state"]
    canonical = load(CANONICAL_PATH)
    sources = load(SOURCES_PATH)
    ledger = load(LEDGER_PATH)
    expectations = load(EXPECTATIONS_PATH)
    analysis_schema = load(ANALYSIS_SCHEMA_PATH)
    analysis_reviews = load(ANALYSIS_REVIEWS_PATH)
    analysis_evidence = load(ANALYSIS_EVIDENCE_PATH)
    live_schema = load(LIVE_SCHEMA_PATH)
    live_observations = load(LIVE_OBSERVATIONS_PATH)
    live_evidence = load(LIVE_EVIDENCE_PATH)

    require((canonical.get("version"), len(canonical.get("records", []))) == (pre["canonical_registry_version"], pre["canonical_record_count"]), "AW canonical pre-state mismatch")
    require(load(CANONICAL_SCHEMA_PATH).get("version") == pre["canonical_schema_version"], "AW canonical schema pre-state mismatch")
    require((sources.get("version"), len(sources.get("sources", []))) == (pre["source_registry_version"], pre["source_count"]), "AW source pre-state mismatch")
    require((ledger.get("version"), len(ledger.get("changes", []))) == (pre["change_ledger_version"], pre["change_ledger_count"]), "AW ledger pre-state mismatch")
    require(expectations.get("version") == pre["monitor_expectations_version"], "AW monitor expectations pre-state mismatch")
    require(len(expectations.get("adapters", [])) == pre["monitor_adapter_count"], "AW monitor adapter count mismatch")
    require(analysis_schema.get("version") == pre["analysis_schema_version"], "AW Analysis schema pre-state mismatch")
    require((analysis_reviews.get("version"), len(analysis_reviews.get("reviews", []))) == (pre["analysis_reviews_version"], pre["analysis_review_count"]), "AW Analysis reviews pre-state mismatch")
    require((analysis_evidence.get("version"), len(analysis_evidence.get("evidence", []))) == (pre["analysis_evidence_version"], pre["analysis_evidence_count"]), "AW Analysis evidence pre-state mismatch")
    require(exact_timestamp_series_rows(analysis_reviews) == 0, "AW may not begin from a state containing exact market timestamp series")

    require(live_schema.get("version") == pre["live_intelligence_schema_version"], "AW Live schema pre-state mismatch")
    require(len(live_observations.get("observations", [])) == pre["live_intelligence_observation_count"], "AW Live observation pre-state mismatch")
    require(len(live_evidence.get("evidence", [])) == pre["live_intelligence_evidence_count"], "AW Live evidence pre-state mismatch")
    require(live_observations.get("population_state") == pre["live_intelligence_population_state"], "AW Live population-state mismatch")
    report = validate_live_intelligence(live_schema, live_evidence, live_observations, canonical)
    require(report.ok, "AW pre-state Live Intelligence validation failed: " + "; ".join(report.errors))
    return canonical, live_schema, live_observations, live_evidence


def assert_payload(plan: dict[str, Any], payload: dict[str, Any]) -> None:
    require(payload.get("tranche") == "AW", "wrong AW payload")
    target = plan["target_state"]
    require(payload.get("target_version") == target["live_intelligence_schema_version"], "AW payload version mismatch")
    require(len(payload.get("observations", [])) == target["observation_count"] == 1, "AW must contain exactly one observation")
    require(len(payload.get("evidence", [])) == target["evidence_count"] == 2, "AW must contain exactly two evidence rows")
    observation = payload["observations"][0]
    require(observation.get("observation_id") == target["observation_id"], "AW observation ID mismatch")
    require(observation.get("observation_type") == "PHYSICAL_SHOCK", "AW first specimen must remain PHYSICAL_SHOCK")
    require(observation.get("verification_state") == "PRIMARY_CONFIRMED", "AW verification state mismatch")
    require(observation.get("canonical_links") == [], "AW Nepal shock must not fabricate Canonical links")
    require(observation.get("revision_of_observation_id") is None, "AW first specimen cannot revise a prior Live observation")
    require(observation.get("automatic_canonical_commit") is False, "AW automatic canonical commit must remain false")
    require(observation.get("google_calendar_write") is False, "AW Google Calendar write must remain false")

    event_time = observation.get("event_time") or {}
    require(event_time.get("precision") == "EXACT_TIMESTAMP", "AW Nepal event time must remain exact")
    require(event_time.get("event_local") == "2026-08-26T08:40:00", "AW Nepal local timestamp drifted")
    require(event_time.get("event_timezone") == "Asia/Kathmandu", "AW Nepal source timezone drifted")
    require(event_time.get("event_at_utc") == "2026-08-26T02:55:00Z", "AW Nepal UTC timestamp drifted")
    require("Australia/Melbourne" not in json.dumps(observation), "AW may not canonicalise Melbourne time")

    evidence_ids = {row.get("evidence_id") for row in payload["evidence"]}
    require(evidence_ids == set(observation.get("evidence_refs") or []), "AW observation evidence references must equal the two payload evidence IDs")
    require(all(row.get("evidence_class") == "PRIMARY_OFFICIAL" for row in payload["evidence"]), "AW evidence must be primary official")
    require(all(row.get("canonical_provenance_effect") == "NONE" for row in payload["evidence"]), "AW evidence may not alter canonical provenance")
    require(all((row.get("publication_time") or {}).get("precision") == "CIVIL_DATE" for row in payload["evidence"]), "AW evidence publication precision must remain civil-date")

    serialized = json.dumps(observation, ensure_ascii=False).lower()
    prohibited_claims = ("ice avalanche", "temporary damming", "caused by", "cause of the flood")
    require(not any(term in serialized for term in prohibited_claims), "AW observation must not promote the uncertain upstream trigger into fact")

    policy = payload["population_policy"]
    require(policy.get("mode") == "CONTROLLED_SINGLE_SPECIMEN", "AW population mode mismatch")
    require(policy.get("maximum_observation_count") == 1, "AW must cap observations at one")
    require(policy.get("maximum_evidence_count") == 2, "AW must cap evidence at two rows")
    require(policy.get("automatic_ingestion_allowed") is False, "AW automatic ingestion must remain false")
    require(policy.get("public_observation_projection_allowed") is False, "AW public observation projection must remain closed")
    require(policy.get("existing_analysis_evidence_migration_allowed") is False, "AW may not migrate Analysis evidence")


def transform(plan: dict[str, Any], payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    canonical, live_schema, live_observations, live_evidence = assert_pre(plan)
    assert_payload(plan, payload)

    foundation = live_schema.get("foundation_population_policy") or {}
    require(foundation.get("production_population_allowed") is False, "AW requires frozen AV production gate")
    require(foundation.get("evidence_population_allowed") is False, "AW requires frozen AV evidence gate")
    require(foundation.get("existing_analysis_evidence_migration_allowed") is False, "AW requires frozen AV migration prohibition")
    require(foundation.get("public_observation_projection_allowed") is False, "AW requires frozen AV public projection gate")

    new_schema = copy.deepcopy(live_schema)
    new_schema["version"] = payload["target_version"]
    new_schema["reference_date"] = payload["reference_date"]
    new_schema["foundation_checkpoint"] = copy.deepcopy(payload["foundation_checkpoint"])
    new_schema.pop("foundation_population_policy", None)
    new_schema["population_policy"] = copy.deepcopy(payload["population_policy"])
    new_schema["controlled_vocabularies"]["publication_time_precision"] = copy.deepcopy(payload["publication_time_precision"])
    if "publication_time" not in new_schema["required_evidence_fields"]:
        new_schema["required_evidence_fields"].append("publication_time")
    public_policy = new_schema["public_projection_policy"]
    public_policy.pop("foundation_metadata_projection_allowed", None)
    public_policy["metadata_projection_allowed"] = True
    public_policy["observation_projection_allowed"] = False
    public_policy["runtime_feed_claim_allowed"] = False
    new_schema["guardrails"] = [
        line
        for line in new_schema.get("guardrails", [])
        if not line.startswith("Foundation v0.1 intentionally rejects production population")
    ]
    new_schema["guardrails"].extend(
        [
            "Evidence source-publication time uses explicit precision and may not be upgraded from a civil date to a fabricated clock time.",
            "AW v0.2 opens only a controlled single-specimen population; a later pressure audit is required before any second observation or broader ingestion.",
            "Public observation projection and runtime-feed claims remain prohibited in the controlled first-specimen state.",
        ]
    )

    new_observations = {
        "project": "WORLD SIGNALS",
        "dataset": "LIVE_INTELLIGENCE_OBSERVATIONS",
        "version": payload["target_version"],
        "reference_date": payload["reference_date"],
        "population_state": "CONTROLLED_SINGLE_SPECIMEN",
        "observations": copy.deepcopy(payload["observations"]),
    }
    new_evidence = {
        "project": "WORLD SIGNALS",
        "dataset": "LIVE_INTELLIGENCE_EVIDENCE_REGISTRY",
        "version": payload["target_version"],
        "reference_date": payload["reference_date"],
        "population_state": "CONTROLLED_SINGLE_SPECIMEN",
        "scope_note": "Evidence supports reviewed factual Live Intelligence observations, remains separate from canonical provenance and Analysis evidence, and AW v0.2 is bounded to the first controlled specimen.",
        "evidence": copy.deepcopy(payload["evidence"]),
    }

    report = validate_live_intelligence(new_schema, new_evidence, new_observations, canonical)
    require(report.ok, "AW post-state Live Intelligence validation failed: " + "; ".join(report.errors))

    target = plan["target_state"]
    require((new_schema["version"], new_observations["version"], new_evidence["version"]) == ("0.2", "0.2", "0.2"), "AW target versions mismatch")
    require(len(new_observations["observations"]) == target["observation_count"], "AW target observation count mismatch")
    require(len(new_evidence["evidence"]) == target["evidence_count"], "AW target evidence count mismatch")
    require(new_observations["population_state"] == target["live_intelligence_population_state"], "AW target population state mismatch")
    return new_schema, new_observations, new_evidence


def audit_markdown(plan: dict[str, Any], protected_before: dict[str, str], protected_after: dict[str, str]) -> str:
    target = plan["target_state"]
    lines = [
        "# WORLD SIGNALS — Nepal Rasuwa flood Live Intelligence AW transaction audit v0.1",
        "",
        f"**Applied at UTC:** {datetime.now(timezone.utc).isoformat()}",
        f"**Exact base:** `{plan['base_sha']}`",
        "",
        "## Controlled write",
        "",
        "- Live Intelligence schema: `v0.1 → v0.2`",
        f"- observations: `0 → {target['observation_count']}`",
        f"- evidence: `0 → {target['evidence_count']}`",
        f"- first observation: `{target['observation_id']}`",
        "- public observation projection: CLOSED",
        "- automatic ingestion: CLOSED",
        "- automatic canonical commit: CLOSED",
        "- Google Calendar write: CLOSED",
        "",
        "## Protected-state proof",
        "",
    ]
    for name in sorted(protected_before):
        same = protected_before[name] == protected_after[name]
        lines.append(f"- `{name}`: {'UNCHANGED' if same else 'CHANGED'} — `{protected_after[name]}`")
    lines.extend(
        [
            "",
            "## Mutation boundary",
            "",
            "The controlled transaction wrote only:",
            "",
            "- `data/live_intelligence/schema.json`",
            "- `data/live_intelligence/observations.json`",
            "- `data/live_intelligence/evidence_registry.json`",
            "- this transaction audit.",
            "",
            "Canonical, Source Registry, Change Ledger, biosecurity overlay, Source/Change Monitor and Analysis remained byte-identical.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    plan = load(PLAN_PATH)
    payload = load(PAYLOAD_PATH)
    protected_before = protected_hashes()
    new_schema, new_observations, new_evidence = transform(plan, payload)

    print(
        "AW simulation PASS: "
        f"schema={new_schema['version']} observations={len(new_observations['observations'])} "
        f"evidence={len(new_evidence['evidence'])} public_projection=false"
    )

    if not args.write:
        return

    require(os.environ.get(APPLY_ENV) == "1", f"AW write requires {APPLY_ENV}=1")
    write(LIVE_SCHEMA_PATH, new_schema)
    write(LIVE_OBSERVATIONS_PATH, new_observations)
    write(LIVE_EVIDENCE_PATH, new_evidence)

    protected_after = protected_hashes()
    require(protected_after == protected_before, "AW protected dataset changed during controlled write")
    AUDIT_PATH.write_text(audit_markdown(plan, protected_before, protected_after), encoding="utf-8")
    print("AW controlled write PASS")


if __name__ == "__main__":
    main()
