from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.analysis import analysis_population_readiness, validate_analysis
from world_signals.live_analysis_bridge import (
    production_live_input_count,
    validate_live_analysis_bridge,
)
from world_signals.live_intelligence import (
    public_live_intelligence_projection,
    validate_live_intelligence,
)

PLAN_PATH = ROOT / "data/analysis/JAPAN_FIES_LIVE_ANALYSIS_AZ_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/analysis/JAPAN_FIES_LIVE_ANALYSIS_AZ_PAYLOAD_v0.1.json"

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


def version_tuple(raw: str) -> tuple[int, ...]:
    return tuple(int(part) for part in str(raw).split("."))


def exact_series_count(reviews: dict[str, Any]) -> int:
    return sum(
        1
        for review in reviews.get("reviews", [])
        for movement in (review.get("what_moved") or [])
        if movement.get("measurement_precision") == "EXACT_TIMESTAMP_SERIES"
    )


def canonical_target(canonical: dict[str, Any], occurrence_id: str) -> dict[str, Any]:
    matches = [
        row for row in canonical.get("records", [])
        if row.get("occurrence_id") == occurrence_id
    ]
    require(len(matches) == 1, f"AZ requires exactly one Canonical row {occurrence_id}")
    return matches[0]


def assert_preconditions(plan: dict[str, Any]) -> None:
    pre = plan["pre_state"]
    canonical = load(CANONICAL_PATH)
    sources = load(SOURCES_PATH)
    ledger = load(LEDGER_PATH)
    expectations = load(EXPECTATIONS_PATH)
    live_schema = load(LIVE_SCHEMA_PATH)
    live_observations = load(LIVE_OBSERVATIONS_PATH)
    live_evidence = load(LIVE_EVIDENCE_PATH)
    analysis_schema = load(ANALYSIS_SCHEMA_PATH)
    reviews = load(REVIEWS_PATH)
    analysis_evidence = load(ANALYSIS_EVIDENCE_PATH)

    require(canonical.get("version") == pre["canonical_registry_version"], "AZ Canonical version drift")
    require(len(canonical.get("records", [])) == pre["canonical_record_count"], "AZ Canonical count drift")
    require(sources.get("version") == pre["source_registry_version"], "AZ Source version drift")
    require(len(sources.get("sources", [])) == pre["source_count"], "AZ Source count drift")
    require(ledger.get("version") == pre["change_ledger_version"], "AZ Change Ledger version drift")
    require(len(ledger.get("changes", [])) == pre["change_ledger_count"], "AZ Change Ledger count drift")
    require(expectations.get("version") == pre["monitor_expectations_version"], "AZ monitor version drift")
    require(len(expectations.get("adapters", [])) == pre["monitor_adapter_count"], "AZ monitor adapter count drift")

    target = canonical_target(canonical, plan["selection"]["canonical_occurrence_id"])
    require(target.get("series_id") == plan["selection"]["canonical_series_id"], "AZ target series drift")
    require(target.get("jurisdiction") == "Japan", "AZ target jurisdiction drift")
    require((target.get("region") or target.get("broad_region")) == "East Asia", "AZ target region drift")
    require(target.get("category") == "MACROECONOMIC_RELEASE", "AZ target category drift")
    require(target.get("event_type") == "DATA_RELEASE", "AZ target event type drift")
    require(target.get("lifecycle_status") == "COMPLETED", "AZ target must already be COMPLETED")
    require(target.get("source_timezone") == "Asia/Tokyo", "AZ target timezone drift")
    require(target.get("start_local") == "2026-09-04", "AZ target civil date drift")
    require(target.get("time_precision") == "DAY", "AZ target time precision drift")
    require(target.get("start_utc") is None, "AZ must not start from a fabricated Canonical UTC")

    if live_schema.get("version") == pre["live_schema_version"]:
        require(len(live_observations.get("observations", [])) == pre["live_observation_count"], "AZ Live observation count drift")
        require(len(live_evidence.get("evidence", [])) == pre["live_evidence_count"], "AZ Live evidence count drift")
    else:
        require(live_schema.get("version") == plan["target_state"]["live_schema_version"], "AZ unexpected Live schema descendant")

    if analysis_schema.get("version") == pre["analysis_schema_version"]:
        require(reviews.get("version") == pre["analysis_reviews_version"], "AZ reviews version drift")
        require(len(reviews.get("reviews", [])) == pre["analysis_review_count"], "AZ review count drift")
        require(analysis_evidence.get("version") == pre["analysis_evidence_version"], "AZ Analysis evidence version drift")
        require(len(analysis_evidence.get("evidence", [])) == pre["analysis_evidence_count"], "AZ Analysis evidence count drift")
        require(production_live_input_count(reviews) == pre["production_live_input_count"], "AZ live-input prestate drift")
    else:
        require(analysis_schema.get("version") == plan["target_state"]["analysis_schema_version"], "AZ unexpected Analysis schema descendant")

    require(exact_series_count(reviews) == pre["production_exact_timestamp_series_count"], "AZ exact-series prestate drift")


def target_live_schema(current: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    if current.get("version") == "0.4":
        return deepcopy(current)
    require(current.get("version") == "0.3", "AZ Live schema requires v0.3 prestate")
    target = deepcopy(current)
    target["version"] = "0.4"
    target["reference_date"] = "2026-09-06"
    target["ax_checkpoint"] = {
        "schema_version": "0.3",
        "observations_version": "0.3",
        "evidence_version": "0.3",
        "population_state": "CONTROLLED_MULTI_SNAPSHOT_SPECIMEN",
        "observation_count": 3,
        "evidence_count": 4,
        "post_merge_main_sha": "0a7608ab56116d0f65ffd1492a3da87bcbf35f47",
        "historical_contract": "AX v0.3 preserved the AW Nepal shock and added two reviewed DRC evolving-state snapshots while public projection, automatic ingestion and automatic story clustering remained closed."
    }
    target["population_policy"] = {
        "mode": "CONTROLLED_CANONICAL_LINKED_ECONOMIC_SPECIMEN",
        "production_population_allowed": True,
        "evidence_population_allowed": True,
        "maximum_observation_count": 4,
        "maximum_evidence_count": 6,
        "automatic_ingestion_allowed": False,
        "existing_analysis_evidence_migration_allowed": False,
        "public_observation_projection_allowed": False,
        "reason": "AZ adds exactly one reviewed Japan FIES economic-data observation with a real OUTCOME_OF Canonical link and two primary-official Live evidence rows. Further Live population requires another pressure audit."
    }
    guardrails = [
        item for item in (target.get("guardrails") or [])
        if not item.startswith("AX v0.3 allows only")
        and not item.startswith("Public observation projection, automatic ingestion")
    ]
    additions = [
        "AX v0.3 is a frozen historical checkpoint of three observations and four evidence rows; legitimate later descendants may grow only through a separately pressure-audited contract.",
        "AZ v0.4 adds exactly one reviewed ECONOMIC_DATA_OBSERVATION for Japan July 2026 FIES and does not convert the same release's retrospective April-June data-vintage note into synthetic prior Live history.",
        "A scheduled Live economic-data observation may link OUTCOME_OF a real completed Canonical occurrence without changing Canonical identity, provenance or timing.",
        "Public observation projection, automatic ingestion, automatic story clustering, automatic Canonical commit and Google Calendar writes remain prohibited in AZ v0.4.",
        "A fifth Live observation or broader ingestion requires another pressure audit."
    ]
    for item in additions:
        if item not in guardrails:
            guardrails.append(item)
    target["guardrails"] = guardrails
    return target


def target_live_observations(current: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    target = deepcopy(current)
    ids = {row.get("observation_id") for row in target.get("observations", [])}
    row = deepcopy(payload["live_observation"])
    if row["observation_id"] not in ids:
        require(len(target.get("observations", [])) == 3, "AZ expected exactly three pre-existing Live observations")
        target["observations"].append(row)
    target["version"] = "0.4"
    target["reference_date"] = "2026-09-06"
    target["population_state"] = "CONTROLLED_CANONICAL_LINKED_ECONOMIC_SPECIMEN"
    target["scope_note"] = "Bounded reviewed internal Live Intelligence store: AW Nepal shock, AX DRC evolving-state pair, and one AZ Japan FIES Canonical-linked economic-data specimen. Public projection and automatic ingestion remain closed."
    return target


def target_live_evidence(current: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    target = deepcopy(current)
    existing = {row.get("evidence_id") for row in target.get("evidence", [])}
    for row in payload["live_evidence"]:
        if row["evidence_id"] not in existing:
            target["evidence"].append(deepcopy(row))
            existing.add(row["evidence_id"])
    target["version"] = "0.4"
    target["reference_date"] = "2026-09-06"
    target["population_state"] = "CONTROLLED_CANONICAL_LINKED_ECONOMIC_SPECIMEN"
    target["scope_note"] = "Evidence supports the bounded reviewed Live store through AZ. Live evidence remains separate from Canonical provenance and Analysis evidence; public observation projection remains closed."
    return target


def target_analysis_schema(current: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    raw_version = current.get("version")
    if raw_version != "0.5":
        try:
            parsed = tuple(int(part) for part in str(raw_version).split("."))
        except (TypeError, ValueError):
            parsed = ()
        require(
            parsed >= (0, 6),
            "AZ Analysis schema requires v0.5 prestate or v0.6+ reviewed descendant",
        )
        return deepcopy(current)
    target = deepcopy(current)
    target["version"] = "0.6"
    target["reference_date"] = "2026-09-06"
    policy = deepcopy(target["live_input_policy"])
    policy.update({
        "mode": "CONTROLLED_SINGLE_PRODUCTION_LINK",
        "production_live_inputs_allowed": True,
        "public_live_input_projection_allowed": False,
        "maximum_production_live_inputs": 1,
        "maximum_live_inputs_per_review": 1,
        "factual_input_requires_matching_canonical_occurrence": True,
        "future_production_population_requires_pressure_audit": True,
    })
    target["live_input_policy"] = policy
    guardrails = [
        item for item in (target.get("guardrails") or [])
        if not item.startswith("AY keeps production Live Intelligence inputs")
        and not item.startswith("A future production Live Intelligence input requires")
    ]
    additions = [
        "AY v0.5 is the frozen production-closed bridge checkpoint; AZ is the first pressure-audited descendant to populate exactly one production Live Intelligence input.",
        "In AZ, a FACTUAL_INPUT Live observation must explicitly link the same Canonical occurrence as the Analysis review; this role-specific requirement does not silently turn story identity into Canonical identity.",
        "AZ permits at most one production Live input in total and at most one per review; public Live-input projection remains closed.",
        "Further production Live-input population beyond the AZ bounded relationship requires another pressure audit."
    ]
    for item in additions:
        if item not in guardrails:
            guardrails.append(item)
    target["guardrails"] = guardrails
    return target


def target_reviews(current: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    target = deepcopy(current)
    ids = {row.get("analysis_id") for row in target.get("reviews", [])}
    row = deepcopy(payload["analysis_review"])
    if row["analysis_id"] not in ids:
        require(len(target.get("reviews", [])) == 20, "AZ expected 20 Analysis reviews prestate")
        target["reviews"].append(row)
    target["version"] = "0.17"
    target["reference_date"] = "2026-09-06"
    return target


def target_analysis_evidence(current: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    target = deepcopy(current)
    ids = {row.get("evidence_id") for row in target.get("evidence", [])}
    for row in payload["analysis_evidence"]:
        if row["evidence_id"] not in ids:
            target["evidence"].append(deepcopy(row))
            ids.add(row["evidence_id"])
    target["version"] = "0.17"
    target["reference_date"] = "2026-09-06"
    return target


def target_status(current: str) -> str:
    if "# CURRENT RECOVERY OVERRIDE — POST-AY / AZ FIRST PRODUCTION LIVE→ANALYSIS LINK" in current:
        return current
    ba_title = "# CURRENT RECOVERY OVERRIDE — POST-AZ / BA ANALYSIS REVISION FOUNDATION"
    if ba_title in current:
        require(
            "- Live Intelligence: **v0.4 / 4 reviewed internal observations / 6 primary-official evidence rows / public observation projection CLOSED**" in current,
            "AZ PROJECT_STATUS BA descendant lost Live v0.4 checkpoint",
        )
        require(
            "- Analysis: **v0.17 / 21 reviews / 95 evidence / 18 reviewed event types**" in current,
            "AZ PROJECT_STATUS BA descendant lost Analysis v0.17 population",
        )
        require(
            "- production `live_inputs`: **1 / reviewed maximum 1 / public projection CLOSED**" in current,
            "AZ PROJECT_STATUS BA descendant lost first production Live input",
        )
        return current
    require("# CURRENT RECOVERY OVERRIDE — POST-AX / AY LIVE→ANALYSIS BRIDGE FOUNDATION" in current, "AZ PROJECT_STATUS title drift")
    text = current.replace(
        "# CURRENT RECOVERY OVERRIDE — POST-AX / AY LIVE→ANALYSIS BRIDGE FOUNDATION",
        "# CURRENT RECOVERY OVERRIDE — POST-AY / AZ FIRST PRODUCTION LIVE→ANALYSIS LINK",
        1,
    )
    text = text.replace(
        "- Live Intelligence: **v0.3 / 3 reviewed internal observations / 4 primary-official evidence rows / public observation projection CLOSED**",
        "- Live Intelligence: **v0.4 / 4 reviewed internal observations / 6 primary-official evidence rows / public observation projection CLOSED**",
        1,
    )
    text = text.replace("- Analysis schema: **v0.5**", "- Analysis schema: **v0.6**", 1)
    text = text.replace(
        "- Analysis: **v0.16 / 20 reviews / 91 evidence / 18 reviewed event types**",
        "- Analysis: **v0.17 / 21 reviews / 95 evidence / 18 reviewed event types**",
        1,
    )
    text = text.replace(
        "- sole completed/unreviewed occurrence: **`WSO-MAC-B-0041`**",
        "- completed/unreviewed Analysis-eligible occurrences: **0** (not a population target)",
        1,
    )
    text = text.replace(
        "- production `EXACT_TIMESTAMP_SERIES`: **0**",
        "- production `live_inputs`: **1 / reviewed maximum 1 / public projection CLOSED**\n- production `EXACT_TIMESTAMP_SERIES`: **0**",
        1,
    )
    old = (
        "AY establishes a **production-closed prospective Live Intelligence → Analysis input contract**. "
        "Analysis may eventually select immutable Live `observation_id` values as factual inputs, but AY leaves production `live_inputs` at **0**, public Live-input projection closed, and all 20 existing Analysis reviews / 91 evidence rows unchanged. Story IDs, latest-state selectors, automatic story expansion, transitive Live-evidence migration and upstream Live mutation are prohibited. A later pressure audit is required before the first real populated relationship.\n\n"
    )
    new = (
        "AZ exercises the first **production Live Intelligence → Analysis relationship** with one bounded Japan July 2026 FIES specimen. The Live row is an `ECONOMIC_DATA_OBSERVATION` linked `OUTCOME_OF` the already-completed Canonical occurrence `WSO-MAC-B-0041`; the Analysis packet selects that immutable observation as `FACTUAL_INPUT`. Live and Analysis evidence remain separate, public Live-input projection remains closed, and no market movement is manufactured. The same release's April–June CPI-rebase revisions are retained as data-vintage context rather than synthetic prior Live history. Further bridge population requires another pressure audit.\n\n"
    )
    require(old in text, "AZ PROJECT_STATUS AY decision paragraph drift")
    return text.replace(old, new, 1)


def target_roadmap(current: str) -> str:
    if "## Stage 8 — prospective Live Intelligence → Analysis linkage — AZ FIRST PRODUCTION LINK DONE / PUBLIC CLOSED" in current:
        return current
    text = current.replace(
        "Current bounded population is three observations and four primary-official evidence rows.",
        "AX's frozen checkpoint is three observations and four primary-official evidence rows. AZ v0.4 adds one separately pressure-audited Japan economic-data observation and two primary-official evidence rows, taking the current bounded internal population to four observations and six evidence rows.",
        1,
    )
    text = text.replace(
        "Before any fourth observation, run another pressure audit. The next high-value candidate is prospective Live Intelligence → Analysis linkage rather than automatic continuation of the DRC story.",
        "AZ completed the required pre-fourth-observation audit before adding the Japan FIES specimen. Before any fifth observation or broader ingestion, run another pressure audit.",
        1,
    )
    old = """## Stage 8 — prospective Live Intelligence → Analysis linkage — AY FOUNDATION DONE / PRODUCTION CLOSED

AY establishes the executable bridge contract without populating a production relationship. Analysis may prospectively select immutable Live `observation_id` values as factual inputs while keeping those inputs distinct from Analysis evidence and prohibiting any rewrite of upstream Live records.

The target relationship remains:

`factual observation -> optional canonical context -> analytical interpretation`

not:

`headline -> inferred cause -> rewritten event`.

AY admits no story selector, latest-state lookup or automatic story expansion: a developing story must be referenced snapshot-by-snapshot. Production `live_inputs` remain exactly zero and public Live-input projection remains closed. A later pressure audit must select and authorise the first real production relationship.
"""
    new = """## Stage 8 — prospective Live Intelligence → Analysis linkage — AZ FIRST PRODUCTION LINK DONE / PUBLIC CLOSED

AY established the executable bridge grammar with production population closed. AZ then pressure-audited and populated exactly one relationship: the completed July 2026 Japan FIES Canonical occurrence -> one reviewed Live `ECONOMIC_DATA_OBSERVATION` -> one Analysis review selecting that immutable observation as `FACTUAL_INPUT`.

The relationship remains:

`factual observation -> optional canonical context -> analytical interpretation`

not:

`headline -> inferred cause -> rewritten event`.

Live evidence is not transitively migrated into Analysis evidence, upstream Live records remain immutable, and story/latest selectors remain prohibited. The inaugural factual input must share the review's Canonical occurrence. Production `live_inputs` are capped at one and public Live-input projection remains closed. Another pressure audit is required before any second production relationship.
"""
    require(old in text, "AZ ROADMAP Stage 8 drift")
    return text.replace(old, new, 1)


def simulate(plan: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    canonical = load(CANONICAL_PATH)
    live_schema = target_live_schema(load(LIVE_SCHEMA_PATH), plan)
    live_observations = target_live_observations(load(LIVE_OBSERVATIONS_PATH), payload)
    live_evidence = target_live_evidence(load(LIVE_EVIDENCE_PATH), payload)
    analysis_schema = target_analysis_schema(load(ANALYSIS_SCHEMA_PATH), plan)
    reviews = target_reviews(load(REVIEWS_PATH), payload)
    analysis_evidence = target_analysis_evidence(load(ANALYSIS_EVIDENCE_PATH), payload)

    live_report = validate_live_intelligence(live_schema, live_evidence, live_observations, canonical)
    require(live_report.ok, "AZ simulated Live validation failed: " + "; ".join(live_report.errors))
    analysis_report = validate_analysis(analysis_schema, analysis_evidence, reviews, canonical)
    require(analysis_report.ok, "AZ simulated Analysis validation failed: " + "; ".join(analysis_report.errors))
    bridge_report = validate_live_analysis_bridge(analysis_schema, reviews, live_observations)
    require(bridge_report.ok, "AZ simulated bridge validation failed: " + "; ".join(bridge_report.errors))

    return {
        "live_schema": live_schema,
        "live_observations": live_observations,
        "live_evidence": live_evidence,
        "analysis_schema": analysis_schema,
        "reviews": reviews,
        "analysis_evidence": analysis_evidence,
        "status": target_status(STATUS_PATH.read_text(encoding="utf-8")),
        "roadmap": target_roadmap(ROADMAP_PATH.read_text(encoding="utf-8")),
    }


def assert_target(plan: dict[str, Any], target: dict[str, Any]) -> None:
    post = plan["target_state"]
    live_schema = target["live_schema"]
    live_observations = target["live_observations"]
    live_evidence = target["live_evidence"]
    analysis_schema = target["analysis_schema"]
    reviews = target["reviews"]
    analysis_evidence = target["analysis_evidence"]

    require(live_schema.get("version") == post["live_schema_version"], "AZ target Live schema mismatch")
    require(len(live_observations.get("observations", [])) == post["live_observation_count"], "AZ target Live observation count mismatch")
    require(len(live_evidence.get("evidence", [])) == post["live_evidence_count"], "AZ target Live evidence count mismatch")
    require(live_observations.get("population_state") == post["live_population_state"], "AZ target Live population state mismatch")
    raw_analysis_version = analysis_schema.get("version")
    raw_az_version = post["analysis_schema_version"]
    try:
        analysis_version = tuple(int(part) for part in str(raw_analysis_version).split("."))
        az_version = tuple(int(part) for part in str(raw_az_version).split("."))
    except (TypeError, ValueError):
        analysis_version = ()
        az_version = (0, 6)
    require(
        analysis_version >= az_version,
        "AZ target Analysis schema must preserve v0.6 or a reviewed descendant",
    )
    require(reviews.get("version") == post["analysis_reviews_version"], "AZ target review version mismatch")
    require(len(reviews.get("reviews", [])) == post["analysis_review_count"], "AZ target review count mismatch")
    require(analysis_evidence.get("version") == post["analysis_evidence_version"], "AZ target evidence version mismatch")
    require(len(analysis_evidence.get("evidence", [])) == post["analysis_evidence_count"], "AZ target evidence count mismatch")
    require(production_live_input_count(reviews) == post["production_live_input_count"], "AZ target production live-input count mismatch")
    require(exact_series_count(reviews) == post["production_exact_timestamp_series_count"], "AZ target exact-series mismatch")

    policy = analysis_schema["live_input_policy"]
    require(policy["mode"] == "CONTROLLED_SINGLE_PRODUCTION_LINK", "AZ target bridge mode mismatch")
    require(policy["maximum_production_live_inputs"] == 1, "AZ target max live-input mismatch")
    require(policy["maximum_live_inputs_per_review"] == 1, "AZ target per-review max mismatch")
    require(policy["factual_input_requires_matching_canonical_occurrence"] is True, "AZ target same-anchor gate missing")
    require(policy["public_live_input_projection_allowed"] is False, "AZ public bridge projection opened")
    require(live_schema["population_policy"]["public_observation_projection_allowed"] is False, "AZ public Live projection opened")

    new_live = [
        row for row in live_observations["observations"]
        if row.get("observation_id") == plan["selection"]["live_observation_id"]
    ]
    require(len(new_live) == 1, "AZ target Live observation missing/duplicated")
    require(new_live[0].get("observation_type") == "ECONOMIC_DATA_OBSERVATION", "AZ must not relabel July FIES as DATA_REVISION")
    require(new_live[0].get("revision_of_observation_id") is None, "AZ must not invent Live revision ancestry")
    require(new_live[0].get("canonical_links") == [{"occurrence_id": "WSO-MAC-B-0041", "relationship": "OUTCOME_OF"}], "AZ Live canonical link drift")

    review = next(
        row for row in reviews["reviews"]
        if row.get("analysis_id") == plan["selection"]["analysis_id"]
    )
    require(review.get("what_moved") == [], "AZ must not manufacture market movement")
    require(review.get("what_surprised", {}).get("status") == "DOWNSIDE", "AZ surprise status drift")
    require(review.get("canonical_release_utc") is None, "AZ must preserve unresolved Canonical release UTC")
    require(review.get("live_inputs") == [{
        "observation_id": plan["selection"]["live_observation_id"],
        "roles": ["FACTUAL_INPUT"],
        "analysis_sections": ["what_happened", "what_surprised", "what_may_be_noise", "alternative_explanations"],
    }], "AZ production Live-input relationship drift")

    public = public_live_intelligence_projection(
        live_schema, live_evidence, live_observations, load(CANONICAL_PATH)
    )
    require(public["metadata"]["public_observation_count"] == 0, "AZ public Live observation projection must remain zero")
    require(public["observations"] == [], "AZ public Live observation rows must remain empty")

    readiness = analysis_population_readiness(analysis_schema, reviews, load(CANONICAL_PATH))
    require(readiness["reviewed_occurrence_count"] == 21, "AZ reviewed occurrence count mismatch")


def write_target(target: dict[str, Any]) -> None:
    LIVE_SCHEMA_PATH.write_text(dump(target["live_schema"]), encoding="utf-8")
    LIVE_OBSERVATIONS_PATH.write_text(dump(target["live_observations"]), encoding="utf-8")
    LIVE_EVIDENCE_PATH.write_text(dump(target["live_evidence"]), encoding="utf-8")
    ANALYSIS_SCHEMA_PATH.write_text(dump(target["analysis_schema"]), encoding="utf-8")
    REVIEWS_PATH.write_text(dump(target["reviews"]), encoding="utf-8")
    ANALYSIS_EVIDENCE_PATH.write_text(dump(target["analysis_evidence"]), encoding="utf-8")
    STATUS_PATH.write_text(target["status"], encoding="utf-8")
    ROADMAP_PATH.write_text(target["roadmap"], encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check-only", action="store_true")
    group.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    plan = load(PLAN_PATH)
    payload = load(PAYLOAD_PATH)
    assert_preconditions(plan)
    target = simulate(plan, payload)
    assert_target(plan, target)

    if args.check_only:
        print("AZ read-only simulation: PASS")
        return

    write_target(target)
    print("AZ reviewed target materialised: PASS")


if __name__ == "__main__":
    main()
