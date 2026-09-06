#!/usr/bin/env python3
from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.analysis import validate_analysis
from world_signals.checkpoint_contract import version_at_least
from world_signals.live_analysis_bridge import production_live_input_count
from world_signals.live_intelligence import public_live_intelligence_projection, validate_live_intelligence

PLAN_PATH = ROOT / "data/live_intelligence/UN_CORRECT_MAP_LIVE_BF_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/live_intelligence/UN_CORRECT_MAP_LIVE_BF_PAYLOAD_v0.1.json"

CANONICAL_PATH = ROOT / "data/canonical/registry.json"
CANONICAL_SCHEMA_PATH = ROOT / "data/canonical/schema.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
OPERATIONS_PATH = ROOT / "data/monitor/operations_policy.json"

LIVE_SCHEMA_PATH = ROOT / "data/live_intelligence/schema.json"
LIVE_OBSERVATIONS_PATH = ROOT / "data/live_intelligence/observations.json"
LIVE_EVIDENCE_PATH = ROOT / "data/live_intelligence/evidence_registry.json"

ANALYSIS_SCHEMA_PATH = ROOT / "data/analysis/schema.json"
REVIEWS_PATH = ROOT / "data/analysis/event_reviews.json"
ANALYSIS_EVIDENCE_PATH = ROOT / "data/analysis/evidence_registry.json"

STATUS_PATH = ROOT / "PROJECT_STATUS.md"
ROADMAP_PATH = ROOT / "ROADMAP.md"

APPLY_ENV = "WORLD_SIGNALS_APPLY_UN_CORRECT_MAP_LIVE_BF"
APPLY_VALUE = "YES"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def exact_series_count(reviews: dict[str, Any]) -> int:
    return sum(
        1
        for review in reviews.get("reviews", [])
        for movement in (review.get("what_moved") or [])
        if movement.get("measurement_precision") == "EXACT_TIMESTAMP_SERIES"
    )


def analysis_revision_count(reviews: dict[str, Any]) -> int:
    return sum(1 for review in reviews.get("reviews", []) if review.get("revision_of_analysis_id"))


def find_by_id(rows: list[dict[str, Any]], key: str, value: str) -> dict[str, Any] | None:
    matches = [row for row in rows if row.get(key) == value]
    require(len(matches) <= 1, f"BF duplicate {key}={value}")
    return matches[0] if matches else None


def assert_protected_state(plan: dict[str, Any], *, exact_upstream: bool) -> None:
    pre = plan["pre_state"]
    canonical = load(CANONICAL_PATH)
    sources = load(SOURCES_PATH)
    ledger = load(LEDGER_PATH)
    analysis_schema = load(ANALYSIS_SCHEMA_PATH)
    reviews = load(REVIEWS_PATH)
    analysis_evidence = load(ANALYSIS_EVIDENCE_PATH)

    if exact_upstream:
        require(canonical.get("version") == pre["canonical_registry_version"], "BF Canonical version drift")
        require(len(canonical.get("records", [])) == pre["canonical_record_count"], "BF Canonical population drift")
        require(sources.get("version") == pre["source_registry_version"], "BF Source Registry version drift")
        require(len(sources.get("sources", [])) == pre["source_count"], "BF Source Registry population drift")
        require(ledger.get("version") == pre["change_ledger_version"], "BF Change Ledger version drift")
        require(len(ledger.get("changes", [])) == pre["change_ledger_count"], "BF Change Ledger population drift")
    else:
        require(version_at_least(canonical.get("version"), pre["canonical_registry_version"]), "BF descendant Canonical version regressed")
        require(len(canonical.get("records", [])) >= pre["canonical_record_count"], "BF descendant Canonical population regressed")
        require(version_at_least(sources.get("version"), pre["source_registry_version"]), "BF descendant Source Registry version regressed")
        require(len(sources.get("sources", [])) >= pre["source_count"], "BF descendant Source Registry population regressed")
        require(version_at_least(ledger.get("version"), pre["change_ledger_version"]), "BF descendant Change Ledger version regressed")
        require(len(ledger.get("changes", [])) >= pre["change_ledger_count"], "BF descendant Change Ledger population regressed")
    require(version_at_least(analysis_schema.get("version"), pre["analysis_schema_version"]), "BF Analysis schema regressed")
    require(len(reviews.get("reviews", [])) >= pre["analysis_review_count"], "BF Analysis review population regressed")
    require(len(analysis_evidence.get("evidence", [])) >= pre["analysis_evidence_count"], "BF Analysis evidence population regressed")
    require(production_live_input_count(reviews) == pre["production_live_input_count"], "BF must not change production live_inputs")
    require(analysis_revision_count(reviews) == pre["production_analysis_revision_count"], "BF must not change Analysis revisions")
    require(exact_series_count(reviews) == pre["production_exact_timestamp_series_count"], "BF must not change exact timestamp series")


def assert_preconditions(plan: dict[str, Any], payload: dict[str, Any]) -> bool:
    pre = plan["pre_state"]
    schema = load(LIVE_SCHEMA_PATH)
    observations = load(LIVE_OBSERVATIONS_PATH)
    evidence = load(LIVE_EVIDENCE_PATH)
    observation = payload["live_observation"]
    evidence_rows = payload["live_evidence"]

    present_observation = find_by_id(observations.get("observations", []), "observation_id", observation["observation_id"])
    present_evidence = [find_by_id(evidence.get("evidence", []), "evidence_id", row["evidence_id"]) for row in evidence_rows]
    any_evidence = any(row is not None for row in present_evidence)
    all_evidence = all(row is not None for row in present_evidence)
    require(bool(present_observation) == all_evidence, "BF partial materialisation detected")
    require(not any_evidence or all_evidence, "BF partial evidence materialisation detected")

    require(observation.get("observation_type") == "INSTITUTIONAL_DEVELOPMENT", "BF observation type drift")
    require(observation.get("canonical_links") == [], "BF must remain zero-Canonical-link")
    require(observation.get("revision_of_observation_id") is None, "BF is not a Live revision")
    require(observation.get("event_time") == {"precision": "CIVIL_DATE", "event_date": "2026-09-04"}, "BF event time must remain civil-date only")
    require(observation.get("domain_tags") == ["INSTITUTIONS", "POLITICS"], "BF domain contract drift")
    require(observation.get("regions") == ["Global"], "BF region contract drift")
    for row in evidence_rows:
        require(row.get("evidence_class") == "PRIMARY_OFFICIAL", "BF evidence must remain primary official")
        require(row.get("canonical_provenance_effect") == "NONE", "BF Live evidence cannot alter Canonical provenance")
        require(row.get("publication_time") == {"precision": "CIVIL_DATE", "published_date": "2026-09-04"}, "BF publication time must remain civil-date only")

    assert_protected_state(plan, exact_upstream=not bool(present_observation))

    if not present_observation:
        require(schema.get("version") == pre["live_schema_version"], "BF Live schema prestate drift")
        require(len(observations.get("observations", [])) == pre["live_observation_count"], "BF Live observation prestate drift")
        require(len(evidence.get("evidence", [])) == pre["live_evidence_count"], "BF Live evidence prestate drift")
        return False

    target = plan["target_state"]
    require(present_observation == observation, "BF reviewed observation identity/content drift")
    for actual, expected in zip(present_evidence, evidence_rows):
        require(actual == expected, f"BF reviewed evidence identity/content drift: {expected['evidence_id']}")
    require(version_at_least(schema.get("version"), target["live_schema_version"]), "BF reviewed descendant schema regressed")
    require(len(observations.get("observations", [])) >= target["live_observation_count"], "BF reviewed descendant observations regressed")
    require(len(evidence.get("evidence", [])) >= target["live_evidence_count"], "BF reviewed descendant evidence regressed")
    return True


def target_live_schema(current: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    if current.get("version") != "0.5":
        require(version_at_least(current.get("version"), "0.6"), "BF requires v0.5 prestate or v0.6+ reviewed descendant")
        return deepcopy(current)
    target = deepcopy(current)
    target["version"] = "0.6"
    target["reference_date"] = "2026-09-07"
    target["bd_checkpoint"] = {
        "schema_version": "0.5",
        "observations_version": "0.5",
        "evidence_version": "0.5",
        "population_state": "CONTROLLED_GEOPOLITICAL_SPECIMEN",
        "observation_count": 5,
        "evidence_count": 7,
        "post_merge_main_sha": "e54dddbaa0d60a39babc2fa47c1f054954b5c9ac",
        "historical_contract": "BD v0.5 preserved AW/AX/AZ and added one reviewed Vietnam-Myanmar GEOPOLITICAL_DEVELOPMENT with zero Canonical links while all public/automatic gates remained closed."
    }
    target["population_policy"] = {
        "mode": "CONTROLLED_INSTITUTIONAL_SPECIMEN",
        "production_population_allowed": True,
        "evidence_population_allowed": True,
        "maximum_observation_count": 6,
        "maximum_evidence_count": 9,
        "automatic_ingestion_allowed": False,
        "existing_analysis_evidence_migration_allowed": False,
        "public_observation_projection_allowed": False,
        "reason": "BF adds exactly one pressure-audited UN General Assembly INSTITUTIONAL_DEVELOPMENT with two primary-official evidence rows and zero Canonical links."
    }
    guardrails = [item for item in (target.get("guardrails") or []) if item != "A sixth Live observation, broader ingestion, second production Live-to-Analysis link or first production Analysis revision requires another pressure audit."]
    additions = [
        "BD v0.5 remains the frozen five-observation/seven-evidence checkpoint; BF is the separately pressure-audited sixth observation.",
        "BF v0.6 adds one primary-confirmed UN General Assembly INSTITUTIONAL_DEVELOPMENT for adoption of A/RES/80/307 with two primary-official evidence rows and zero Canonical links.",
        "BF records the institutional adoption and vote without implying a compulsory single world map, territorial or sovereignty change, or economic/market consequence.",
        "BF preserves event and source-publication timing at CIVIL_DATE because no source-native clock time is required for the reviewed factual claim.",
        "Public observation projection, automatic ingestion, automatic story clustering, automatic Canonical commit and Google Calendar writes remain prohibited in BF v0.6.",
        "A seventh Live observation, broader ingestion, second production Live-to-Analysis link or first production Analysis revision requires another pressure audit."
    ]
    for item in additions:
        if item not in guardrails:
            guardrails.append(item)
    target["guardrails"] = guardrails
    return target


def target_observations(current: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    target = deepcopy(current)
    row = deepcopy(payload["live_observation"])
    ids = {item.get("observation_id") for item in target.get("observations", [])}
    if row["observation_id"] in ids:
        return target
    require(len(target.get("observations", [])) == 5, "BF expected exactly five pre-existing Live observations")
    target["observations"].append(row)
    target["version"] = "0.6"
    target["reference_date"] = "2026-09-07"
    target["population_state"] = "CONTROLLED_INSTITUTIONAL_SPECIMEN"
    target["scope_note"] = "Bounded reviewed internal Live Intelligence store through BF: AW Nepal physical shock, AX DRC evolving-state pair, AZ Japan FIES economic data, BD Vietnam-Myanmar geopolitical development, and one UN General Assembly institutional development. Public projection and automatic ingestion remain closed."
    return target


def target_evidence(current: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    target = deepcopy(current)
    ids = {item.get("evidence_id") for item in target.get("evidence", [])}
    additions = [deepcopy(row) for row in payload["live_evidence"] if row["evidence_id"] not in ids]
    if not additions:
        return target
    require(len(target.get("evidence", [])) == 7, "BF expected exactly seven pre-existing Live evidence rows")
    require(len(additions) == 2, "BF requires exactly two new evidence rows")
    target["evidence"].extend(additions)
    target["version"] = "0.6"
    target["reference_date"] = "2026-09-07"
    target["population_state"] = "CONTROLLED_INSTITUTIONAL_SPECIMEN"
    target["scope_note"] = "Evidence supports the bounded reviewed Live store through BF. Live evidence remains separate from Canonical provenance and Analysis evidence; public observation projection remains closed."
    return target


def target_status(current: str) -> str:
    marker = "\n---\n\n# WORLD SIGNALS — project status / branch-recovery checkpoint"
    require(marker in current, "BF status historical-body marker missing")
    historical = current.split(marker, 1)[1]
    override = """# CURRENT RECOVERY OVERRIDE — POST-BE / BF SIXTH LIVE INSTITUTIONAL SPECIMEN

**Effective checkpoint:** 2026-09-07
**Exact post-BE main base:** `629ab595ecccaf86a92bbd8cdfdab4297496b298`

This override supersedes stale \"current\" counts in the historical body below while preserving that body as an audit/recovery record. `WORLD_SIGNALS_PROJECT_CHARTER.md` remains authoritative; governed registry/contract files remain operational truth.

## Current governed state

- Canonical Registry: **v0.40 / 689 occurrences**
- Canonical schema: **v0.52**
- Source Registry: **v1.82 / 245 sources**
- reviewed Change Ledger: **v0.26 / 61 entries**
- biosecurity overlay: **v0.15 @ canonical v0.40 / 689**
- Source/Change Monitor expectations: **v0.10 / 8 configured adapters**
- Monitor operations policy: **v0.1**
- Live Intelligence: **v0.6 / 6 reviewed internal observations / 9 primary-official evidence rows / public observation projection CLOSED**
- Analysis schema: **v0.7**
- Analysis: **v0.17 / 21 reviews / 95 evidence / 18 reviewed event types**
- completed Analysis-eligible occurrences: **22**
- completed/unreviewed Analysis-eligible occurrences: **1** (`WSO-COM-A-0001`; not a population target)
- production `live_inputs`: **1 / public projection CLOSED**
- production Analysis revisions: **0 / gate CLOSED / public revision metadata projection CLOSED**
- production `EXACT_TIMESTAMP_SERIES`: **0**
- automatic canonical commit: **OFF / gate closed**
- Google Calendar writes: **OFF**

## Current architecture decision

BF adds the sixth pressure-audited Live observation: the **4 September 2026 UN General Assembly adoption of A/RES/80/307, ‘Correct the Map’**, stored as a primary-confirmed `INSTITUTIONAL_DEVELOPMENT`. Two primary-official evidence rows preserve the UN vote/adoption record and African Union institutional context. The observation has zero Canonical links because no scheduled Canonical occurrence is manufactured for the specific resolution adoption.

BF does not claim that the resolution mandates one compulsory world map, changes borders or sovereignty, or establishes an economic, political or market consequence. Event and source-publication timing remain at civil-date precision. No Analysis packet, second Live→Analysis link or Analysis revision is created.

BE's OPEC lifecycle repair and pending primary-provenance upgrade remain unchanged. BD remains the fifth Live specimen; AZ remains the only production `live_input`; BA's Analysis revision grammar remains production-closed.

Public Live observation projection, automatic ingestion, automatic story clustering, automatic Canonical commit and Google Calendar writes remain closed. A seventh Live observation, broader ingestion, second production Live-to-Analysis link or first production Analysis revision requires another pressure audit.

## Current configured monitor cohort

Eight configured adapters: RBA FSR; Colombia SUIN/Socrata; EU CRA/Cellar; three EU CBAM legal-rule routes; ONS release-calendar RSS; EIA WPSR schedule. Route presence does not imply blanket source automation permission, and all routes remain review-only with automatic canonical commit disabled.

## Recovery order

1. `WORLD_SIGNALS_PROJECT_CHARTER.md`
2. this current override
3. `data/canonical/registry.json`, `data/sources/registry.json`, `data/monitor/*`, `data/live_intelligence/*`, `data/analysis/*`
4. latest pressure/transaction audits
5. current `main` SHA and Actions runs
"""
    return override.rstrip() + marker + historical


def target_roadmap(current: str) -> str:
    if "### BF — sixth Live institutional specimen" in current:
        return current
    marker = "\n## Stage 8 — prospective Live Intelligence → Analysis linkage"
    require(marker in current, "BF roadmap Stage 8 marker missing")
    addition = """

### BF — sixth Live institutional specimen — DONE / BOUNDED

BF selects the 4 September 2026 UN General Assembly adoption of A/RES/80/307, ‘Correct the Map’, as the sixth pressure-audited Live observation. It is stored as `INSTITUTIONAL_DEVELOPMENT` with two primary-official evidence rows: the UN adoption/vote record and African Union institutional context. The observation has zero Canonical links; no specific scheduled Canonical resolution-adoption identity is manufactured.

The UN record fixes the 114th plenary meeting and 164–1–6 vote. The AU confirms Togo's role on behalf of the African Group and the Africa-led implementation framing. BF records only those institutional facts: it does not imply a compulsory single world map, territorial or sovereignty change, economic effect, market response or broader causal consequence. Event and source-publication precision remain `CIVIL_DATE`.

Public observation projection, automatic ingestion, automatic story clustering, automatic Canonical commit and Google Calendar writes remain closed. A seventh Live observation requires another pressure audit.
"""
    return current.replace(marker, addition.rstrip() + marker, 1)


def simulate(plan: dict[str, Any], payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    schema = target_live_schema(load(LIVE_SCHEMA_PATH), plan)
    observations = target_observations(load(LIVE_OBSERVATIONS_PATH), payload)
    evidence = target_evidence(load(LIVE_EVIDENCE_PATH), payload)
    canonical = load(CANONICAL_PATH)
    report = validate_live_intelligence(schema, evidence, observations, canonical)
    require(report.ok, "BF simulated Live validation failed: " + "; ".join(report.errors))
    public = public_live_intelligence_projection(schema, evidence, observations, canonical)
    require(public.get("observations") == [], "BF must keep public Live observation projection closed")
    analysis_report = validate_analysis(load(ANALYSIS_SCHEMA_PATH), load(ANALYSIS_EVIDENCE_PATH), load(REVIEWS_PATH), canonical)
    require(analysis_report.ok, "BF protected Analysis state invalid: " + "; ".join(analysis_report.errors))
    return schema, observations, evidence


def assert_target(plan: dict[str, Any], payload: dict[str, Any]) -> None:
    target = plan["target_state"]
    schema = load(LIVE_SCHEMA_PATH)
    observations = load(LIVE_OBSERVATIONS_PATH)
    evidence = load(LIVE_EVIDENCE_PATH)
    canonical = load(CANONICAL_PATH)
    report = validate_live_intelligence(schema, evidence, observations, canonical)
    require(report.ok, "BF materialised Live validation failed: " + "; ".join(report.errors))
    require(schema.get("version") == target["live_schema_version"], "BF target schema version mismatch")
    require(len(observations.get("observations", [])) == target["live_observation_count"], "BF target observation count mismatch")
    require(len(evidence.get("evidence", [])) == target["live_evidence_count"], "BF target evidence count mismatch")
    require(schema.get("population_policy", {}).get("mode") == target["population_state"], "BF target population mode mismatch")
    require(schema.get("population_policy", {}).get("maximum_observation_count") == 6, "BF observation cap mismatch")
    require(schema.get("population_policy", {}).get("maximum_evidence_count") == 9, "BF evidence cap mismatch")
    require(public_live_intelligence_projection(schema, evidence, observations, canonical).get("observations") == [], "BF public projection opened unexpectedly")
    assert_preconditions(plan, payload)


def apply(plan: dict[str, Any], payload: dict[str, Any]) -> None:
    require(os.environ.get(APPLY_ENV) == APPLY_VALUE, f"BF apply requires {APPLY_ENV}={APPLY_VALUE}")
    already = assert_preconditions(plan, payload)
    if already:
        assert_target(plan, payload)
        print("BF already materialised; descendant-safe no-op")
        return
    schema, observations, evidence = simulate(plan, payload)
    LIVE_SCHEMA_PATH.write_text(dump(schema), encoding="utf-8")
    LIVE_OBSERVATIONS_PATH.write_text(dump(observations), encoding="utf-8")
    LIVE_EVIDENCE_PATH.write_text(dump(evidence), encoding="utf-8")
    STATUS_PATH.write_text(target_status(STATUS_PATH.read_text(encoding="utf-8")), encoding="utf-8")
    ROADMAP_PATH.write_text(target_roadmap(ROADMAP_PATH.read_text(encoding="utf-8")), encoding="utf-8")
    assert_target(plan, payload)
    print("BF controlled target materialised")


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply the bounded WORLD SIGNALS UN Correct the Map Live specimen BF.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check-only", action="store_true")
    group.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    plan = load(PLAN_PATH)
    payload = load(PAYLOAD_PATH)
    already = assert_preconditions(plan, payload)
    if args.check_only:
        if already:
            assert_target(plan, payload)
            print("BF read-only descendant check: PASS")
        else:
            simulate(plan, payload)
            target_status(STATUS_PATH.read_text(encoding="utf-8"))
            target_roadmap(ROADMAP_PATH.read_text(encoding="utf-8"))
            print("BF read-only simulation: PASS")
        return
    apply(plan, payload)


if __name__ == "__main__":
    main()
