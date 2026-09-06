from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.analysis import validate_analysis
from world_signals.checkpoint_contract import validate_descendant_checkpoint, version_at_least
from world_signals.live_analysis_bridge import production_live_input_count
from world_signals.live_intelligence import (
    public_live_intelligence_projection,
    validate_live_intelligence,
)

PLAN_PATH = ROOT / "data/live_intelligence/VIETNAM_MYANMAR_LIVE_BD_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/live_intelligence/VIETNAM_MYANMAR_LIVE_BD_PAYLOAD_v0.1.json"

CANONICAL_PATH = ROOT / "data/canonical/registry.json"
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
    require(len(matches) <= 1, f"BD duplicate {key}={value}")
    return matches[0] if matches else None


def assert_protected_current_state(plan: dict[str, Any]) -> None:
    pre = plan["pre_state"]
    analysis_schema = load(ANALYSIS_SCHEMA_PATH)
    reviews = load(REVIEWS_PATH)
    evidence = load(ANALYSIS_EVIDENCE_PATH)
    require(version_at_least(analysis_schema.get("version"), pre["analysis_schema_version"]), "BD Analysis schema regressed")
    require(len(reviews.get("reviews", [])) >= pre["analysis_review_count"], "BD Analysis review population regressed")
    require(len(evidence.get("evidence", [])) >= pre["analysis_evidence_count"], "BD Analysis evidence population regressed")
    require(production_live_input_count(reviews) == pre["production_live_input_count"], "BD must not change production live_inputs")
    require(analysis_revision_count(reviews) == pre["production_analysis_revision_count"], "BD must not change Analysis revision population")
    require(exact_series_count(reviews) == pre["production_exact_timestamp_series_count"], "BD must not change exact timestamp series population")


def assert_preconditions(plan: dict[str, Any], payload: dict[str, Any]) -> bool:
    pre = plan["pre_state"]
    canonical = load(CANONICAL_PATH)
    sources = load(SOURCES_PATH)
    ledger = load(LEDGER_PATH)
    live_schema = load(LIVE_SCHEMA_PATH)
    observations = load(LIVE_OBSERVATIONS_PATH)
    evidence = load(LIVE_EVIDENCE_PATH)

    observation = payload["live_observation"]
    evidence_row = payload["live_evidence"][0]
    present_observation = find_by_id(observations.get("observations", []), "observation_id", observation["observation_id"])
    present_evidence = find_by_id(evidence.get("evidence", []), "evidence_id", evidence_row["evidence_id"])
    require(bool(present_observation) == bool(present_evidence), "BD partial materialisation detected")

    require(observation.get("observation_type") == "GEOPOLITICAL_DEVELOPMENT", "BD observation type drift")
    require(observation.get("canonical_links") == [], "BD must remain an unscheduled zero-Canonical-link observation")
    require(observation.get("revision_of_observation_id") is None, "BD is not a Live revision")
    require(observation.get("event_time") == {"precision": "CIVIL_DATE", "event_date": "2026-09-05"}, "BD event time must remain civil-date only")
    require(evidence_row.get("publication_time") == {"precision": "EXACT_TIMESTAMP", "published_at_utc": "2026-09-05T09:16:00Z"}, "BD publication-time evidence drift")
    require(evidence_row.get("canonical_provenance_effect") == "NONE", "BD Live evidence cannot alter Canonical provenance")

    assert_protected_current_state(plan)

    if not present_observation:
        require(canonical.get("version") == pre["canonical_registry_version"], "BD Canonical version drift")
        require(len(canonical.get("records", [])) == pre["canonical_record_count"], "BD Canonical count drift")
        require(sources.get("version") == pre["source_registry_version"], "BD Source version drift")
        require(len(sources.get("sources", [])) == pre["source_count"], "BD Source count drift")
        require(ledger.get("version") == pre["change_ledger_version"], "BD Change Ledger version drift")
        require(len(ledger.get("changes", [])) == pre["change_ledger_count"], "BD Change Ledger count drift")
        require(live_schema.get("version") == pre["live_schema_version"], "BD Live schema prestate drift")
        require(len(observations.get("observations", [])) == pre["live_observation_count"], "BD Live observation prestate drift")
        require(len(evidence.get("evidence", [])) == pre["live_evidence_count"], "BD Live evidence prestate drift")
        return False

    target = plan["target_state"]
    require(present_observation == observation, "BD reviewed observation identity/content drift")
    require(present_evidence == evidence_row, "BD reviewed evidence identity/content drift")
    report = validate_descendant_checkpoint(
        versions_at_least={"BD Live schema": (live_schema.get("version"), target["live_schema_version"])},
        counts_at_least={
            "BD Live observations": (len(observations.get("observations", [])), target["live_observation_count"]),
            "BD Live evidence": (len(evidence.get("evidence", [])), target["live_evidence_count"]),
        },
    )
    require(report.ok, "BD descendant precondition failed: " + "; ".join(report.errors))
    return True


def target_live_schema(current: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    if current.get("version") != "0.4":
        require(version_at_least(current.get("version"), "0.5"), "BD Live schema requires v0.4 prestate or v0.5+ reviewed descendant")
        return deepcopy(current)
    target = deepcopy(current)
    target["version"] = "0.5"
    target["reference_date"] = "2026-09-06"
    target["az_checkpoint"] = {
        "schema_version": "0.4",
        "observations_version": "0.4",
        "evidence_version": "0.4",
        "population_state": "CONTROLLED_CANONICAL_LINKED_ECONOMIC_SPECIMEN",
        "observation_count": 4,
        "evidence_count": 6,
        "post_merge_main_sha": "802ca5b94b6e80a055ac363f48a6c8392f038048",
        "historical_contract": "AZ v0.4 preserved AW/AX and added the first Canonical-linked economic-data Live observation, with public projection and automatic ingestion closed."
    }
    target["population_policy"] = {
        "mode": "CONTROLLED_GEOPOLITICAL_SPECIMEN",
        "production_population_allowed": True,
        "evidence_population_allowed": True,
        "maximum_observation_count": 5,
        "maximum_evidence_count": 7,
        "automatic_ingestion_allowed": False,
        "existing_analysis_evidence_migration_allowed": False,
        "public_observation_projection_allowed": False,
        "reason": "BD adds exactly one pressure-audited Vietnam-Myanmar GEOPOLITICAL_DEVELOPMENT with one primary-official evidence row and zero Canonical links."
    }
    guardrails = [item for item in (target.get("guardrails") or []) if item != "A fifth Live observation or broader ingestion requires another pressure audit."]
    additions = [
        "AZ v0.4 remains the frozen four-observation/six-evidence checkpoint; BD is the separately pressure-audited fifth observation.",
        "BD v0.5 adds one primary-confirmed Vietnam-Myanmar GEOPOLITICAL_DEVELOPMENT with zero Canonical links; absence of a scheduled Canonical identity is not repaired by invention.",
        "BD preserves the 5 September summit as CIVIL_DATE event time while retaining the source's independently explicit publication timestamp; publication time is not event time.",
        "BD makes no causal, strategic-alignment, legitimacy, conflict-effect or market-attribution claim.",
        "Public observation projection, automatic ingestion, automatic story clustering, automatic Canonical commit and Google Calendar writes remain prohibited in BD v0.5.",
        "A sixth Live observation, broader ingestion, second production Live-to-Analysis link or first production Analysis revision requires another pressure audit."
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
    require(len(target.get("observations", [])) == 4, "BD expected exactly four pre-existing Live observations")
    target["observations"].append(row)
    target["version"] = "0.5"
    target["reference_date"] = "2026-09-06"
    target["population_state"] = "CONTROLLED_GEOPOLITICAL_SPECIMEN"
    target["scope_note"] = "Bounded reviewed internal Live Intelligence store through BD: AW Nepal physical shock, AX DRC evolving-state pair, AZ Japan FIES economic data, and one Vietnam-Myanmar geopolitical development. Public projection and automatic ingestion remain closed."
    return target


def target_evidence(current: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    target = deepcopy(current)
    row = deepcopy(payload["live_evidence"][0])
    ids = {item.get("evidence_id") for item in target.get("evidence", [])}
    if row["evidence_id"] in ids:
        return target
    require(len(target.get("evidence", [])) == 6, "BD expected exactly six pre-existing Live evidence rows")
    target["evidence"].append(row)
    target["version"] = "0.5"
    target["reference_date"] = "2026-09-06"
    target["population_state"] = "CONTROLLED_GEOPOLITICAL_SPECIMEN"
    target["scope_note"] = "Evidence supports the bounded reviewed Live store through BD. Live evidence remains separate from Canonical provenance and Analysis evidence; public observation projection remains closed."
    return target


def target_status(current: str) -> str:
    marker = "\n---\n\n# WORLD SIGNALS — project status / branch-recovery checkpoint"
    require(marker in current, "BD status historical-body marker missing")
    historical = current.split(marker, 1)[1]
    override = """# CURRENT RECOVERY OVERRIDE — POST-BC / BD FIFTH LIVE SPECIMEN

**Effective checkpoint:** 2026-09-06
**Exact post-BC main base:** `667d0fbcc92f937b0cb609d619b664a2a97e8165`

This override supersedes stale \"current\" counts in the historical body below while preserving that body as an audit/recovery record. `WORLD_SIGNALS_PROJECT_CHARTER.md` remains authoritative; governed registry/contract files remain operational truth.

## Current governed state

- Canonical Registry: **v0.39 / 689 occurrences**
- Canonical schema: **v0.52**
- Source Registry: **v1.81 / 244 sources**
- reviewed Change Ledger: **v0.25 / 60 entries**
- biosecurity overlay: **v0.14 @ canonical v0.39 / 689**
- Source/Change Monitor expectations: **v0.10 / 8 configured adapters**
- Monitor operations policy: **v0.1**
- Live Intelligence: **v0.5 / 5 reviewed internal observations / 7 primary-official evidence rows / public observation projection CLOSED**
- Analysis schema: **v0.7**
- Analysis: **v0.17 / 21 reviews / 95 evidence / 18 reviewed event types**
- completed Analysis-eligible occurrences: **21**
- completed/unreviewed Analysis-eligible occurrences: **0** (not a population target)
- production `live_inputs`: **1 / public projection CLOSED**
- production Analysis revisions: **0 / gate CLOSED / public revision metadata projection CLOSED**
- production `EXACT_TIMESTAMP_SERIES`: **0**
- automatic canonical commit: **OFF / gate closed**
- Google Calendar writes: **OFF**

## Current architecture decision

BD adds the fifth pressure-audited Live observation: a **primary-confirmed 5 September 2026 Vietnam-Myanmar geopolitical development** sourced to the Government of Viet Nam. It has zero Canonical links because no scheduled Canonical identity exists and none is manufactured. The summit event is retained at civil-date precision while the source's independently explicit publication timestamp is preserved separately. No causal, strategic-alignment, legitimacy, conflict-effect or market-attribution claim is encoded.

BC remains the reviewed historical-checkpoint / legitimate-descendant contract. BB remains the bounded BARMM election Canonical coverage repair. BA's Analysis revision-lineage grammar remains production-closed. AZ's inaugural Live-to-Analysis relationship remains the only production `live_input`.

Public Live observation projection, automatic ingestion, automatic story clustering, automatic Canonical commit and Google Calendar writes remain closed. A sixth Live observation, broader ingestion, second production Live-to-Analysis link or first production Analysis revision requires another pressure audit.

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
    marker = "\n## Stage 8 — prospective Live Intelligence → Analysis linkage"
    if "### BD — fifth Live geopolitical specimen" in current:
        return current
    require(marker in current, "BD roadmap Stage 8 marker missing")
    addition = """

### BD — fifth Live geopolitical specimen — DONE / BOUNDED

BD selects the 5 September 2026 Vietnam-Myanmar defence/security agreement as the fifth pressure-audited Live observation. It is stored as `GEOPOLITICAL_DEVELOPMENT` with one primary Government of Viet Nam evidence row and **zero Canonical links**: an unscheduled current development does not acquire a synthetic Canonical identity merely to make downstream linkage easier.

The official article supplies an exact publication time, preserved independently, but describes the leaders' meeting only as occurring on 5 September / Saturday morning. BD therefore keeps event time at `CIVIL_DATE` and does not fabricate a summit timestamp. Public observation projection, automatic ingestion, automatic story clustering, automatic Canonical commit and Calendar writes remain closed. A sixth Live observation requires another pressure audit.
"""
    return current.replace(marker, addition + marker, 1)


def build_targets(plan: dict[str, Any], payload: dict[str, Any]) -> dict[Path, str]:
    schema = target_live_schema(load(LIVE_SCHEMA_PATH), plan)
    observations = target_observations(load(LIVE_OBSERVATIONS_PATH), payload)
    evidence = target_evidence(load(LIVE_EVIDENCE_PATH), payload)
    return {
        LIVE_SCHEMA_PATH: dump(schema),
        LIVE_OBSERVATIONS_PATH: dump(observations),
        LIVE_EVIDENCE_PATH: dump(evidence),
        STATUS_PATH: target_status(STATUS_PATH.read_text(encoding="utf-8")),
        ROADMAP_PATH: target_roadmap(ROADMAP_PATH.read_text(encoding="utf-8")),
    }


def validate_targets(plan: dict[str, Any], targets: dict[Path, str]) -> None:
    schema = json.loads(targets[LIVE_SCHEMA_PATH])
    observations = json.loads(targets[LIVE_OBSERVATIONS_PATH])
    evidence = json.loads(targets[LIVE_EVIDENCE_PATH])
    canonical = load(CANONICAL_PATH)
    report = validate_live_intelligence(schema, evidence, observations, canonical)
    require(report.ok, "BD Live validation failed: " + "; ".join(report.errors))
    target = plan["target_state"]
    require(schema.get("version") == target["live_schema_version"], "BD target schema version mismatch")
    require(len(observations.get("observations", [])) == target["live_observation_count"], "BD target observation count mismatch")
    require(len(evidence.get("evidence", [])) == target["live_evidence_count"], "BD target evidence count mismatch")
    policy = schema.get("population_policy") or {}
    require(policy.get("maximum_observation_count") == 5, "BD observation cap mismatch")
    require(policy.get("maximum_evidence_count") == 7, "BD evidence cap mismatch")
    require(policy.get("automatic_ingestion_allowed") is False, "BD automatic ingestion must remain closed")
    require(policy.get("public_observation_projection_allowed") is False, "BD public projection must remain closed")
    public = public_live_intelligence_projection(schema, evidence, observations)
    require(public.get("observations") == [], "BD public projection leaked observations")
    assert_protected_current_state(plan)
    analysis_report = validate_analysis(load(ANALYSIS_SCHEMA_PATH), load(REVIEWS_PATH), load(ANALYSIS_EVIDENCE_PATH), canonical)
    require(analysis_report.ok, "BD protected Analysis validation failed: " + "; ".join(analysis_report.errors))


def write_targets(targets: dict[Path, str]) -> None:
    for path, content in targets.items():
        path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply the reviewed BD Vietnam-Myanmar Live Intelligence specimen")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check-only", action="store_true")
    group.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    plan = load(PLAN_PATH)
    payload = load(PAYLOAD_PATH)
    already_present = assert_preconditions(plan, payload)
    targets = build_targets(plan, payload)
    validate_targets(plan, targets)

    if args.check_only:
        print("BD read-only simulation: PASS" if not already_present else "BD reviewed descendant check: PASS")
        return 0

    if already_present:
        print("BD already materialised; reviewed descendant unchanged")
        return 0

    write_targets(targets)
    print("BD controlled target materialised")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
