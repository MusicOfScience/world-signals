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
PLAN_PATH = ROOT / "data/live_intelligence/PIF_PARTNER_FRAMEWORK_LIVE_CL_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/live_intelligence/PIF_PARTNER_FRAMEWORK_LIVE_CL_PAYLOAD_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
LIVE_SCHEMA_PATH = ROOT / "data/live_intelligence/schema.json"
LIVE_OBSERVATIONS_PATH = ROOT / "data/live_intelligence/observations.json"
LIVE_EVIDENCE_PATH = ROOT / "data/live_intelligence/evidence_registry.json"
ANALYSIS_SCHEMA_PATH = ROOT / "data/analysis/schema.json"
ANALYSIS_REVIEWS_PATH = ROOT / "data/analysis/event_reviews.json"
ANALYSIS_EVIDENCE_PATH = ROOT / "data/analysis/evidence_registry.json"
APPLY_ENV = "WORLD_SIGNALS_APPLY_PIF_PARTNER_FRAMEWORK_LIVE_CL"
APPLY_VALUE = "REVIEWED_APPLY"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def version_tuple(value: Any) -> tuple[int, ...]:
    return tuple(int(part) for part in str(value).split("."))


def by_id(rows: list[dict[str, Any]], key: str, value: str) -> dict[str, Any] | None:
    matches = [row for row in rows if row.get(key) == value]
    require(len(matches) <= 1, f"CL duplicate {key}={value}")
    return matches[0] if matches else None


def production_analysis_revision_count(reviews: dict[str, Any]) -> int:
    return sum(1 for row in reviews.get("reviews", []) if row.get("revision_of_analysis_id"))


def production_live_input_count(reviews: dict[str, Any]) -> int:
    return sum(len(row.get("live_inputs") or []) for row in reviews.get("reviews", []))


def exact_utc(raw: str) -> bool:
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (TypeError, ValueError, AttributeError):
        return False
    return raw.endswith("Z") and parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(parsed)


def assert_anchor(canonical: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    expected = plan["required_anchor"]
    row = by_id(canonical.get("records", []), "occurrence_id", expected["occurrence_id"])
    require(row is not None, "CL PIF Canonical anchor missing")
    checks = {
        "series_id": expected["series_id"],
        "canonical_name": expected["canonical_name"],
        "category": expected["category"],
        "region": expected["region"],
        "institution": expected["institution"],
        "lifecycle_status": expected["lifecycle_status"],
        "certainty_status": expected["certainty_status"],
        "timing_type": expected["timing_type"],
        "start_local": expected["start_local"],
        "end_local": expected["end_local"],
        "source_timezone": expected["source_timezone"],
        "time_precision": expected["time_precision"],
        "source_id": expected["source_id"],
        "last_successful_assertion_id": expected["completion_assertion_id"],
    }
    for key, value in checks.items():
        require(row.get(key) == value, f"CL PIF anchor drift: {key}")
    require(row.get("start_utc") is None and row.get("end_utc") is None, "CL must preserve PIF civil-date range without synthetic UTC endpoints")
    return row


def assert_upstream_contract(plan: dict[str, Any]) -> None:
    pre = plan["pre_state"]
    canonical = load(CANONICAL_PATH)
    sources = load(SOURCES_PATH)
    ledger = load(LEDGER_PATH)
    expectations = load(EXPECTATIONS_PATH)
    live_schema = load(LIVE_SCHEMA_PATH)
    observations = load(LIVE_OBSERVATIONS_PATH)
    live_evidence = load(LIVE_EVIDENCE_PATH)
    analysis_schema = load(ANALYSIS_SCHEMA_PATH)
    reviews = load(ANALYSIS_REVIEWS_PATH)
    analysis_evidence = load(ANALYSIS_EVIDENCE_PATH)

    target_obs = by_id(observations.get("observations", []), "observation_id", plan["target"]["observation_id"])
    target_ev = by_id(live_evidence.get("evidence", []), "evidence_id", plan["target"]["evidence_ids"][0])
    require(bool(target_obs) == bool(target_ev), "CL partial materialisation detected before transaction")
    descendant = target_obs is not None

    if not descendant:
        require(str(canonical.get("version")) == pre["canonical_registry_version"], "CL exact Canonical prestate drift")
        require(len(canonical.get("records", [])) == pre["canonical_record_count"], "CL exact Canonical population drift")
        require(str(sources.get("version")) == pre["source_registry_version"], "CL exact Source Registry prestate drift")
        require(len(sources.get("sources", [])) == pre["source_count"], "CL exact Source population drift")
        require(str(ledger.get("version")) == pre["change_ledger_version"], "CL exact Change Ledger prestate drift")
        require(len(ledger.get("changes", [])) == pre["change_ledger_count"], "CL exact Change Ledger population drift")
        require(str(expectations.get("version")) == pre["monitor_expectations_version"], "CL exact Monitor expectations prestate drift")
        require(len(expectations.get("adapters", [])) == pre["monitor_adapter_count"], "CL exact Monitor adapter population drift")
        require(str(live_schema.get("version")) == pre["live_schema_version"], "CL exact Live schema prestate drift")
        require(len(observations.get("observations", [])) == pre["live_observation_count"], "CL exact Live observation prestate drift")
        require(len(live_evidence.get("evidence", [])) == pre["live_evidence_count"], "CL exact Live evidence prestate drift")
        require(str(analysis_schema.get("version")) == pre["analysis_schema_version"], "CL exact Analysis schema prestate drift")
        require(len(reviews.get("reviews", [])) == pre["analysis_review_count"], "CL exact Analysis review prestate drift")
        require(len(analysis_evidence.get("evidence", [])) == pre["analysis_evidence_count"], "CL exact Analysis evidence prestate drift")
        require(production_analysis_revision_count(reviews) == pre["production_analysis_revision_count"], "CL exact Analysis revision prestate drift")
        require(production_live_input_count(reviews) == pre["production_live_input_count"], "CL exact production live_inputs prestate drift")
    else:
        require(version_tuple(canonical.get("version")) >= version_tuple(pre["canonical_registry_version"]), "CL descendant Canonical version regression")
        require(len(canonical.get("records", [])) >= pre["canonical_record_count"], "CL descendant Canonical population regression")
        require(version_tuple(sources.get("version")) >= version_tuple(pre["source_registry_version"]), "CL descendant Source version regression")
        require(len(sources.get("sources", [])) >= pre["source_count"], "CL descendant Source population regression")
        require(version_tuple(ledger.get("version")) >= version_tuple(pre["change_ledger_version"]), "CL descendant Change Ledger regression")
        require(len(ledger.get("changes", [])) >= pre["change_ledger_count"], "CL descendant Change Ledger population regression")
        require(version_tuple(expectations.get("version")) >= version_tuple(pre["monitor_expectations_version"]), "CL descendant Monitor version regression")
        require(len(expectations.get("adapters", [])) >= pre["monitor_adapter_count"], "CL descendant Monitor population regression")
        require(version_tuple(analysis_schema.get("version")) >= version_tuple(pre["analysis_schema_version"]), "CL descendant Analysis schema regression")
        require(len(reviews.get("reviews", [])) >= pre["analysis_review_count"], "CL descendant Analysis review regression")
        require(len(analysis_evidence.get("evidence", [])) >= pre["analysis_evidence_count"], "CL descendant Analysis evidence regression")
        require(production_analysis_revision_count(reviews) >= pre["production_analysis_revision_count"], "CL descendant Analysis revision regression")
        require(production_live_input_count(reviews) >= pre["production_live_input_count"], "CL descendant production live_inputs regression")

    require(expectations.get("automatic_canonical_commit") is False, "CL descendant opened automatic Canonical commit")
    require(expectations.get("google_calendar_write") is False, "CL descendant opened Google Calendar write")
    assert_anchor(canonical, plan)


def build_target(observed_at_utc: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    plan = load(PLAN_PATH)
    payload = load(PAYLOAD_PATH)
    schema = load(LIVE_SCHEMA_PATH)
    observations = load(LIVE_OBSERVATIONS_PATH)
    evidence = load(LIVE_EVIDENCE_PATH)
    pre = plan["pre_state"]
    target = plan["target_state"]

    obs_template = deepcopy(payload["observation_template"])
    evidence_rows = deepcopy(payload["live_evidence"])
    obs_id = obs_template["observation_id"]
    evidence_ids = [row["evidence_id"] for row in evidence_rows]
    existing_obs = by_id(observations.get("observations", []), "observation_id", obs_id)
    existing_evidence = [by_id(evidence.get("evidence", []), "evidence_id", ev_id) for ev_id in evidence_ids]
    require(all(row is None for row in existing_evidence) or all(row is not None for row in existing_evidence), "CL partial evidence materialisation detected")
    require(bool(existing_obs) == all(row is not None for row in existing_evidence), "CL partial observation/evidence materialisation detected")

    if existing_obs:
        require(version_tuple(schema.get("version")) >= version_tuple(target["live_schema_version"]), "CL reviewed Live schema regressed below v0.8")
        require(version_tuple(observations.get("version")) >= version_tuple(target["live_schema_version"]), "CL reviewed observations version regressed below v0.8")
        require(version_tuple(evidence.get("version")) >= version_tuple(target["live_schema_version"]), "CL reviewed evidence version regressed below v0.8")
        require(len(observations.get("observations", [])) >= target["live_observation_count"], "CL reviewed observation population regressed")
        require(len(evidence.get("evidence", [])) >= target["live_evidence_count"], "CL reviewed evidence population regressed")
        return schema, observations, evidence

    require(str(schema.get("version")) == pre["live_schema_version"], "CL Live schema prestate drift")
    require(str(observations.get("version")) == pre["live_schema_version"], "CL Live observations prestate drift")
    require(str(evidence.get("version")) == pre["live_schema_version"], "CL Live evidence prestate drift")
    require(len(observations.get("observations", [])) == pre["live_observation_count"], "CL Live observation prestate count drift")
    require(len(evidence.get("evidence", [])) == pre["live_evidence_count"], "CL Live evidence prestate count drift")
    policy = schema.get("population_policy") or {}
    require(policy.get("maximum_observation_count") == pre["live_observation_count"], "CL Live observation policy ceiling drift")
    require(policy.get("maximum_evidence_count") == pre["live_evidence_count"], "CL Live evidence policy ceiling drift")
    require(exact_utc(observed_at_utc), "CL observed_at_utc must be an exact UTC Z timestamp")

    obs_template["observed_at_utc"] = observed_at_utc

    new_schema = deepcopy(schema)
    new_schema["version"] = target["live_schema_version"]
    new_schema["reference_date"] = plan["reference_date"]
    new_schema["population_policy"] = {
        "mode": "CONTROLLED_CANONICAL_LINKED_INSTITUTIONAL_OUTCOME_SPECIMEN",
        "production_population_allowed": True,
        "evidence_population_allowed": True,
        "maximum_observation_count": target["live_observation_count"],
        "maximum_evidence_count": target["live_evidence_count"],
        "automatic_ingestion_allowed": False,
        "existing_analysis_evidence_migration_allowed": False,
        "public_observation_projection_allowed": False,
        "reason": "CL adds exactly one pressure-audited PIF scheduled institutional outcome linked OUTCOME_OF the completed 55th Pacific Islands Forum Leaders Meeting."
    }
    guardrails = list(new_schema.get("guardrails") or [])
    old_gate = "An eighth Live observation, automatic context linking, second production Live-to-Analysis link, further Analysis revision or NHC Monitor activation requires another pressure audit."
    guardrails = [item for item in guardrails if item != old_gate]
    additions = [
        "CG v0.7 remains the frozen seven-observation/ten-evidence checkpoint; CL is the separately pressure-audited eighth observation.",
        "CL v0.8 adds one primary-confirmed PIF INSTITUTIONAL_DEVELOPMENT linked OUTCOME_OF WSO-INT-A-0001 and bounded to the partner-engagement framework outcome.",
        "CL excludes Waqa Moana from the Live payload because fresh research found unreconciled stronger Australian official wording and more qualified indexed final-communiqué wording; no stronger institutional status is silently selected.",
        "CL does not manufacture event_time from a post-event publication date or collapse the multi-day Canonical occurrence into a synthetic clock/range.",
        "CL Live evidence has no Canonical provenance, Monitor-route or Analysis-population authority.",
        "Public observation projection, automatic ingestion, automatic Canonical commit and Google Calendar writes remain prohibited in CL v0.8.",
        "A ninth Live observation, second production Live-to-Analysis link, further Analysis revision or additional Monitor activation requires another pressure audit."
    ]
    for item in additions:
        if item not in guardrails:
            guardrails.append(item)
    new_schema["guardrails"] = guardrails
    new_schema["cl_checkpoint"] = {
        "schema_version": target["live_schema_version"],
        "observations_version": target["live_schema_version"],
        "evidence_version": target["live_schema_version"],
        "population_state": "CONTROLLED_CANONICAL_LINKED_INSTITUTIONAL_OUTCOME_SPECIMEN",
        "observation_count": target["live_observation_count"],
        "evidence_count": target["live_evidence_count"],
        "base_main_sha": plan["base_main_sha"],
        "historical_contract": "CL preserves the completed PIF Canonical identity and adds one reviewed factual partner-engagement-framework outcome through OUTCOME_OF without changing Canonical, Monitor or Analysis state."
    }

    new_observations = deepcopy(observations)
    new_observations["version"] = target["live_schema_version"]
    new_observations["reference_date"] = plan["reference_date"]
    new_observations["population_state"] = "CONTROLLED_CANONICAL_LINKED_INSTITUTIONAL_OUTCOME_SPECIMEN"
    new_observations["observations"].append(obs_template)
    new_observations["scope_note"] = "Bounded reviewed internal Live Intelligence store through CL: eight observations, including one scheduled PIF institutional outcome linked OUTCOME_OF a completed Canonical occurrence. Waqa Moana remains excluded from the CL payload pending direct reconciliation of final institutional wording. Public projection and automatic ingestion remain closed."

    new_evidence = deepcopy(evidence)
    new_evidence["version"] = target["live_schema_version"]
    new_evidence["reference_date"] = plan["reference_date"]
    new_evidence["population_state"] = "CONTROLLED_CANONICAL_LINKED_INSTITUTIONAL_OUTCOME_SPECIMEN"
    new_evidence["evidence"].extend(evidence_rows)
    new_evidence["scope_note"] = "Evidence supports the bounded reviewed Live store through CL. CL adds one primary-official Cook Islands post-event evidence row for the PIF partner-engagement framework outcome; Live evidence remains separate from Canonical provenance and Analysis evidence, and public observation projection remains closed."

    return new_schema, new_observations, new_evidence


def verify_target(plan: dict[str, Any], schema: dict[str, Any], observations: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    target_state = plan["target_state"]
    target = plan["target"]
    require(version_tuple(schema.get("version")) >= version_tuple(target_state["live_schema_version"]), "CL target schema version mismatch")
    require(version_tuple(observations.get("version")) >= version_tuple(target_state["live_schema_version"]), "CL target observations version mismatch")
    require(version_tuple(evidence.get("version")) >= version_tuple(target_state["live_schema_version"]), "CL target evidence version mismatch")
    require(len(observations.get("observations", [])) >= target_state["live_observation_count"], "CL target observation count mismatch")
    require(len(evidence.get("evidence", [])) >= target_state["live_evidence_count"], "CL target evidence count mismatch")

    row = by_id(observations.get("observations", []), "observation_id", target["observation_id"])
    require(row is not None, "CL target observation missing")
    require(row.get("observation_type") == target["observation_type"], "CL observation type drift")
    require(row.get("verification_state") == target["verification_state"], "CL verification state drift")
    require(row.get("regions") == [target["region"]], "CL region drift")
    require(row.get("domain_tags") == target["domain_tags"], "CL domain-tag drift")
    require(row.get("canonical_links") == [{"occurrence_id": target["canonical_occurrence_id"], "relationship": target["canonical_relationship"]}], "CL OUTCOME_OF contract drift")
    require(row.get("evidence_refs") == target["evidence_ids"], "CL evidence-ref drift")
    require("event_time" not in row, "CL must not manufacture event_time")
    require(row.get("automatic_canonical_commit") is False, "CL automatic Canonical commit must remain false")
    require(row.get("google_calendar_write") is False, "CL Calendar write must remain false")
    require(exact_utc(row.get("observed_at_utc")), "CL materialised observation time must be exact UTC")

    evidence_ids = {item.get("evidence_id") for item in evidence.get("evidence", [])}
    require(all(ev_id in evidence_ids for ev_id in target["evidence_ids"]), "CL evidence row missing")
    linked_count = sum(1 for item in observations.get("observations", []) if item.get("canonical_links"))
    require(linked_count >= target_state["canonical_linked_live_observation_count"], "CL canonical-linked Live count mismatch")
    policy = schema.get("population_policy") or {}
    require(policy.get("maximum_observation_count", 0) >= target_state["live_observation_count"], "CL observation policy ceiling too low")
    require(policy.get("maximum_evidence_count", 0) >= target_state["live_evidence_count"], "CL evidence policy ceiling too low")
    require(policy.get("automatic_ingestion_allowed") is False, "CL automatic ingestion must remain closed")
    require(policy.get("public_observation_projection_allowed") is False, "CL public Live projection must remain closed")
    return row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--observed-at-utc")
    args = parser.parse_args()
    require(args.check ^ args.apply, "choose exactly one of --check or --apply")

    plan = load(PLAN_PATH)
    assert_upstream_contract(plan)
    observed_at = args.observed_at_utc or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    require(exact_utc(observed_at), "CL observed_at_utc must be UTC Z time")
    schema, observations, evidence = build_target(observed_at)
    row = verify_target(plan, schema, observations, evidence)

    if args.check:
        print(json.dumps({
            "verdict": "CL_SIMULATION_VALID",
            "schema_version": schema.get("version"),
            "observations": len(observations.get("observations", [])),
            "evidence": len(evidence.get("evidence", [])),
            "observation_id": row["observation_id"],
            "canonical_link": row["canonical_links"][0],
            "event_time_materialised": "event_time" in row,
        }, sort_keys=True))
        return 0

    require(os.environ.get(APPLY_ENV) == APPLY_VALUE, f"set {APPLY_ENV}={APPLY_VALUE} to apply")
    LIVE_SCHEMA_PATH.write_text(dump(schema), encoding="utf-8")
    LIVE_OBSERVATIONS_PATH.write_text(dump(observations), encoding="utf-8")
    LIVE_EVIDENCE_PATH.write_text(dump(evidence), encoding="utf-8")
    print(json.dumps({
        "verdict": "CL_MATERIALIZED_REVIEWED_PIF_LIVE_OUTCOME",
        "observation_id": row["observation_id"],
        "observed_at_utc": row["observed_at_utc"],
        "canonical_link": row["canonical_links"][0],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
