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
PLAN_PATH = ROOT / "data/live_intelligence/DRC_BUNDIBUGYO_EVOLVING_STATE_AX_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/live_intelligence/DRC_BUNDIBUGYO_EVOLVING_STATE_AX_PAYLOAD_v0.1.json"
AUDIT_PATH = ROOT / "data/live_intelligence/DRC_BUNDIBUGYO_EVOLVING_STATE_AX_TRANSACTION_AUDIT_v0.1.md"

APPLY_ENV = "WORLD_SIGNALS_APPLY_LIVE_INTELLIGENCE_AX"

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

    require((canonical.get("version"), len(canonical.get("records", []))) == (pre["canonical_registry_version"], pre["canonical_record_count"]), "AX canonical pre-state mismatch")
    require(load(CANONICAL_SCHEMA_PATH).get("version") == pre["canonical_schema_version"], "AX canonical schema pre-state mismatch")
    require((sources.get("version"), len(sources.get("sources", []))) == (pre["source_registry_version"], pre["source_count"]), "AX source pre-state mismatch")
    require((ledger.get("version"), len(ledger.get("changes", []))) == (pre["change_ledger_version"], pre["change_ledger_count"]), "AX ledger pre-state mismatch")
    require(expectations.get("version") == pre["monitor_expectations_version"], "AX monitor expectations pre-state mismatch")
    require(len(expectations.get("adapters", [])) == pre["monitor_adapter_count"], "AX monitor adapter count mismatch")
    require(analysis_schema.get("version") == pre["analysis_schema_version"], "AX Analysis schema pre-state mismatch")
    require((analysis_reviews.get("version"), len(analysis_reviews.get("reviews", []))) == (pre["analysis_reviews_version"], pre["analysis_review_count"]), "AX Analysis reviews pre-state mismatch")
    require((analysis_evidence.get("version"), len(analysis_evidence.get("evidence", []))) == (pre["analysis_evidence_version"], pre["analysis_evidence_count"]), "AX Analysis evidence pre-state mismatch")
    require(exact_timestamp_series_rows(analysis_reviews) == 0, "AX may not begin from a state containing exact market timestamp series")

    require(live_schema.get("version") == pre["live_intelligence_schema_version"], "AX Live schema pre-state mismatch")
    require(len(live_observations.get("observations", [])) == pre["live_intelligence_observation_count"], "AX Live observation pre-state mismatch")
    require(len(live_evidence.get("evidence", [])) == pre["live_intelligence_evidence_count"], "AX Live evidence pre-state mismatch")
    require(live_observations.get("population_state") == pre["live_intelligence_population_state"], "AX Live population-state mismatch")
    require(live_schema.get("population_policy", {}).get("maximum_observation_count") == 1, "AX requires frozen AW one-observation ceiling")
    require(live_schema.get("population_policy", {}).get("maximum_evidence_count") == 2, "AX requires frozen AW two-evidence ceiling")

    report = validate_live_intelligence(live_schema, live_evidence, live_observations, canonical)
    require(report.ok, "AX pre-state Live Intelligence validation failed: " + "; ".join(report.errors))
    return canonical, live_schema, live_observations, live_evidence


def assert_payload(plan: dict[str, Any], payload: dict[str, Any]) -> None:
    require(payload.get("tranche") == "AX", "wrong AX payload")
    target = plan["target_state"]
    require(payload.get("target_version") == target["live_intelligence_schema_version"] == "0.3", "AX payload version mismatch")
    require(len(payload.get("observations", [])) == 2, "AX must add exactly two DRC observations")
    require(len(payload.get("evidence", [])) == 2, "AX must add exactly two DRC evidence rows")

    rows = payload["observations"]
    ids = [row.get("observation_id") for row in rows]
    require(ids == target["new_observation_ids"], "AX observation IDs/order mismatch")
    require(all(row.get("observation_type") == "HEALTH_EMERGENCY" for row in rows), "AX DRC rows must be HEALTH_EMERGENCY")
    require(all(row.get("verification_state") == "PRIMARY_CONFIRMED" for row in rows), "AX DRC rows must be primary confirmed")
    require(all(row.get("canonical_links") == [] for row in rows), "AX DRC outbreak must not fabricate Canonical links")
    require(all(row.get("revision_of_observation_id") is None for row in rows), "AX state evolution must not use revision links")
    require(all(row.get("story_id") == target["new_story_id"] for row in rows), "AX DRC story ID mismatch")
    require(rows[0].get("state_update_of_observation_id") is None, "AX first DRC snapshot must not update a prior Live row")
    require(rows[1].get("state_update_of_observation_id") == rows[0].get("observation_id"), "AX later DRC snapshot must point to the earlier snapshot")
    require((rows[0].get("state_as_of") or {}).get("precision") == "CIVIL_DATE", "AX first DRC state-as-of precision mismatch")
    require((rows[1].get("state_as_of") or {}).get("precision") == "CIVIL_DATE", "AX second DRC state-as-of precision mismatch")
    require((rows[0].get("state_as_of") or {}).get("as_of_date") == "2026-08-26", "AX first DRC as-of date drifted")
    require((rows[1].get("state_as_of") or {}).get("as_of_date") == "2026-08-30", "AX second DRC as-of date drifted")
    require(all(row.get("automatic_canonical_commit") is False for row in rows), "AX automatic canonical commit must remain false")
    require(all(row.get("google_calendar_write") is False for row in rows), "AX Google Calendar writes must remain false")

    evidence = payload["evidence"]
    require(all(row.get("evidence_class") == "PRIMARY_OFFICIAL" for row in evidence), "AX evidence must be primary official")
    require(all(row.get("canonical_provenance_effect") == "NONE" for row in evidence), "AX evidence may not alter Canonical provenance")
    require(all((row.get("publication_time") or {}).get("precision") == "CIVIL_DATE" for row in evidence), "AX evidence publication precision must remain CIVIL_DATE")
    require({row.get("publication_time", {}).get("published_date") for row in evidence} == {"2026-08-28", "2026-08-30"}, "AX evidence publication dates drifted")

    policy = payload["population_policy"]
    require(policy.get("mode") == "CONTROLLED_MULTI_SNAPSHOT_SPECIMEN", "AX population mode mismatch")
    require(policy.get("maximum_observation_count") == 3, "AX must cap observations at three")
    require(policy.get("maximum_evidence_count") == 4, "AX must cap evidence at four")
    require(policy.get("automatic_ingestion_allowed") is False, "AX automatic ingestion must remain false")
    require(policy.get("public_observation_projection_allowed") is False, "AX public projection must remain closed")
    require(policy.get("existing_analysis_evidence_migration_allowed") is False, "AX may not migrate Analysis evidence")

    story_policy = payload["story_policy_patch"]
    require(story_policy.get("manual_reviewed_story_id_allowed") is True, "AX must explicitly allow manual reviewed story IDs")
    require(story_policy.get("automatic_clustering_allowed") is False, "AX automatic story clustering must remain false")
    require(story_policy.get("story_id_is_not_canonical_identity") is True, "AX story ID must not become Canonical identity")
    require(story_policy.get("story_id_is_not_causal_claim") is True, "AX story ID must not become causal claim")


def transform(plan: dict[str, Any], payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    canonical, live_schema, live_observations, live_evidence = assert_pre(plan)
    assert_payload(plan, payload)

    existing_nepal = copy.deepcopy(live_observations.get("observations", []))
    existing_evidence = copy.deepcopy(live_evidence.get("evidence", []))
    require(len(existing_nepal) == 1 and existing_nepal[0].get("observation_id") == "WSLI-RISK-NPL-FLOOD-20260826-001", "AX requires the AW Nepal specimen unchanged")
    require({row.get("evidence_id") for row in existing_evidence} == {"WSEV-LI-NPL-FLOOD-MOHA-20260827", "WSEV-LI-NPL-FLOOD-WHO-20260830"}, "AX requires the two AW Nepal evidence rows unchanged")

    new_schema = copy.deepcopy(live_schema)
    new_schema["version"] = payload["target_version"]
    new_schema["reference_date"] = payload["reference_date"]
    new_schema["aw_checkpoint"] = copy.deepcopy(payload["aw_checkpoint"])
    new_schema["population_policy"] = copy.deepcopy(payload["population_policy"])
    new_schema["story_grouping_policy"] = copy.deepcopy(payload["story_policy_patch"])
    new_schema["controlled_vocabularies"]["state_as_of_precision"] = copy.deepcopy(payload["state_as_of_precision"])
    new_schema["revision_policy"]["state_update_is_not_revision"] = True
    new_schema["revision_policy"]["state_update_preserves_prior_snapshot"] = True
    new_schema["time_policy"]["state_as_of_time_is_distinct_from_event_publication_and_observation_time"] = True
    new_schema["time_policy"]["civil_state_as_of_must_not_be_upgraded_to_clock_time"] = True
    new_schema["guardrails"] = [
        line for line in new_schema.get("guardrails", [])
        if not line.startswith("AW v0.2 opens only a controlled single-specimen population")
        and not line.startswith("Public observation projection and runtime-feed claims remain prohibited in the controlled first-specimen state")
    ]
    new_schema["guardrails"].extend([
        "A later as-of snapshot of a developing story is a new state observation, not a correction of the earlier snapshot unless the source explicitly corrects prior facts.",
        "Manual reviewed story IDs are grouping keys only; they are not Canonical occurrence identities, causal claims or analytical conclusions.",
        "State-as-of time is separate from event time, source publication time and WORLD SIGNALS observation time; civil dates may not be promoted to synthetic timestamps.",
        "AX v0.3 allows only the AW Nepal specimen plus two reviewed DRC outbreak snapshots; a later pressure audit is required before any fourth observation or broader ingestion.",
        "Public observation projection, automatic ingestion and automatic story clustering remain prohibited in AX v0.3."
    ])

    new_observations = copy.deepcopy(live_observations)
    new_observations["version"] = payload["target_version"]
    new_observations["reference_date"] = payload["reference_date"]
    new_observations["population_state"] = "CONTROLLED_MULTI_SNAPSHOT_SPECIMEN"
    new_observations["observations"].extend(copy.deepcopy(payload["observations"]))

    new_evidence = copy.deepcopy(live_evidence)
    new_evidence["version"] = payload["target_version"]
    new_evidence["reference_date"] = payload["reference_date"]
    new_evidence["population_state"] = "CONTROLLED_MULTI_SNAPSHOT_SPECIMEN"
    new_evidence["scope_note"] = "Evidence supports a bounded reviewed Live Intelligence store: the AW Nepal shock plus two AX DRC Bundibugyo as-of snapshots. It remains separate from Canonical provenance and Analysis evidence."
    new_evidence["evidence"].extend(copy.deepcopy(payload["evidence"]))

    report = validate_live_intelligence(new_schema, new_evidence, new_observations, canonical)
    require(report.ok, "AX post-state Live Intelligence validation failed: " + "; ".join(report.errors))

    target = plan["target_state"]
    require((new_schema["version"], new_observations["version"], new_evidence["version"]) == ("0.3", "0.3", "0.3"), "AX target versions mismatch")
    require(len(new_observations["observations"]) == target["observation_count"] == 3, "AX target observation count mismatch")
    require(len(new_evidence["evidence"]) == target["evidence_count"] == 4, "AX target evidence count mismatch")
    require(new_observations["population_state"] == target["live_intelligence_population_state"], "AX target population-state mismatch")
    require(new_observations["observations"][0] == existing_nepal[0], "AX must preserve the AW Nepal observation byte-semantically")
    require(new_evidence["evidence"][:2] == existing_evidence, "AX must preserve AW Nepal evidence rows")
    return new_schema, new_observations, new_evidence


def audit_markdown(plan: dict[str, Any], protected_before: dict[str, str], protected_after: dict[str, str]) -> str:
    target = plan["target_state"]
    lines = [
        "# WORLD SIGNALS — DRC Bundibugyo evolving-state Live Intelligence AX transaction audit v0.1",
        "",
        f"**Applied at UTC:** {datetime.now(timezone.utc).isoformat()}",
        f"**Exact base:** `{plan['base_sha']}`",
        "",
        "## Controlled write",
        "",
        "- Live Intelligence schema: `v0.2 → v0.3`",
        f"- observations: `1 → {target['observation_count']}`",
        f"- evidence: `2 → {target['evidence_count']}`",
        f"- manual story: `{target['new_story_id']}`",
        "- DRC snapshots: `2026-08-26 → 2026-08-30`",
        "- revision links for DRC state evolution: `0`",
        "- public observation projection: CLOSED",
        "- automatic ingestion: CLOSED",
        "- automatic story clustering: CLOSED",
        "- automatic canonical commit: CLOSED",
        "- Google Calendar write: CLOSED",
        "",
        "## Protected-state proof",
        "",
    ]
    for name in sorted(protected_before):
        same = protected_before[name] == protected_after[name]
        lines.append(f"- `{name}`: {'UNCHANGED' if same else 'CHANGED'} — `{protected_after[name]}`")
    lines.extend([
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
        "Canonical, Source Registry, Change Ledger, biosecurity overlay, Source/Change Monitor and Analysis remained byte-identical."
    ])
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
        "AX simulation PASS: "
        f"schema={new_schema['version']} observations={len(new_observations['observations'])} "
        f"evidence={len(new_evidence['evidence'])} public_projection=false"
    )

    if not args.write:
        return

    require(os.environ.get(APPLY_ENV) == "1", f"AX write requires {APPLY_ENV}=1")
    write(LIVE_SCHEMA_PATH, new_schema)
    write(LIVE_OBSERVATIONS_PATH, new_observations)
    write(LIVE_EVIDENCE_PATH, new_evidence)

    protected_after = protected_hashes()
    require(protected_after == protected_before, "AX protected dataset changed during controlled write")
    AUDIT_PATH.write_text(audit_markdown(plan, protected_before, protected_after), encoding="utf-8")
    print("AX controlled write PASS")


if __name__ == "__main__":
    main()
