#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = "1e4a6bbc8670fc36a452740401461f28e313c031"

SCHEMA = ROOT / "data/live_intelligence/schema.json"
OBSERVATIONS = ROOT / "data/live_intelligence/observations.json"
EVIDENCE = ROOT / "data/live_intelligence/evidence_registry.json"
VALIDATOR = ROOT / "src/world_signals/live_intelligence.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def git_json(path: str) -> dict:
    raw = subprocess.check_output(
        ["git", "show", f"{BASE}:{path}"], cwd=ROOT, text=True
    )
    return json.loads(raw)


def preflight() -> tuple[dict, dict, dict]:
    schema = load(SCHEMA)
    observations = load(OBSERVATIONS)
    evidence = load(EVIDENCE)

    require(schema.get("version") == "0.8", "CM requires exact Live schema v0.8 prestate")
    require(observations.get("version") == "0.8", "CM requires exact observations v0.8 prestate")
    require(evidence.get("version") == "0.8", "CM requires exact evidence v0.8 prestate")
    require(len(observations.get("observations", [])) == 8, "CM requires exactly eight Live observations")
    require(len(evidence.get("evidence", [])) == 11, "CM requires exactly eleven Live evidence rows")
    require(schema.get("population_policy", {}).get("maximum_observation_count") == 8, "CM requires CL observation ceiling 8")
    require(schema.get("population_policy", {}).get("maximum_evidence_count") == 11, "CM requires CL evidence ceiling 11")
    require("correction_conflict_policy" not in schema, "CM correction/conflict policy already exists")
    require("cm_checkpoint" not in schema, "CM checkpoint already exists")

    base_observations = git_json("data/live_intelligence/observations.json")
    base_evidence = git_json("data/live_intelligence/evidence_registry.json")
    require(
        observations.get("observations") == base_observations.get("observations"),
        "CM preflight: production observation rows drifted from exact merged CL base",
    )
    require(
        evidence.get("evidence") == base_evidence.get("evidence"),
        "CM preflight: production evidence rows drifted from exact merged CL base",
    )
    return schema, observations, evidence


def target_schema(schema: dict) -> dict:
    schema["version"] = "0.9"
    schema["reference_date"] = "2026-09-10"

    revision_policy = schema.get("revision_policy") or {}
    revision_policy["corrected_or_retracted_requires_correction_evidence"] = True
    revision_policy["corrected_or_retracted_observed_at_must_follow_target"] = True
    schema["revision_policy"] = revision_policy

    conflict_policy = {
        "mode": "FOUNDATION_CONTRACT_NO_PRODUCTION_SPECIMEN",
        "corrected_or_retracted_states": ["CORRECTED", "RETRACTED"],
        "corrected_or_retracted_requires_revision_reference": True,
        "corrected_or_retracted_requires_correction_evidence": True,
        "corrected_or_retracted_observed_at_must_follow_target": True,
        "conflict_state": "CONFLICTING_REPORTS",
        "conflict_description_field": "conflict_description",
        "conflict_description_required": True,
        "conflict_description_prohibited_outside_conflict_state": True,
        "minimum_unique_conflict_evidence_refs": 2,
        "minimum_distinct_conflict_providers": 2,
        "provider_identity_normalisation": "STRIP_CASEFOLD",
        "conflict_requires_winner_selection": False,
        "conflict_requires_synthetic_consensus": False,
        "external_data_revision_requires_prior_live_observation": False,
    }

    rebuilt: dict = {}
    for key, value in schema.items():
        rebuilt[key] = value
        if key == "revision_policy":
            rebuilt["correction_conflict_policy"] = conflict_policy
    schema = rebuilt

    guardrails = list(schema.get("guardrails") or [])
    old_final = (
        "A ninth Live observation, second production Live-to-Analysis link, further Analysis revision or additional Monitor activation requires another pressure audit."
    )
    require(old_final in guardrails, "CM expected CL final pressure guardrail missing")
    index = guardrails.index(old_final)
    cm_guardrails = [
        "CM v0.9 hardens Live correction, retraction and conflicting-report semantics without adding a ninth production observation or twelfth evidence row.",
        "A CORRECTED or RETRACTED Live observation must preserve an explicit prior Live target, cite correction/revision evidence and be observed strictly later than the target; silent in-place history rewrite remains prohibited.",
        "CONFLICTING_REPORTS requires at least two unique evidence records from at least two distinct normalised providers plus an explicit factual conflict_description; Live does not choose a winning source or synthetic consensus merely because reports disagree.",
        "conflict_description is reserved for CONFLICTING_REPORTS observations; ordinary verified observations may not carry hidden conflict semantics.",
        "DATA_REVISION remains an external-data revision concept and does not require a synthetic prior WORLD SIGNALS Live observation.",
        "CM does not reinterpret or populate Waqa Moana; the CL source-wording discrepancy remains preserved as historical pressure evidence only.",
    ]
    guardrails[index:index] = cm_guardrails
    schema["guardrails"] = guardrails

    population = schema.get("population_policy") or {}
    population["mode"] = "CONTROLLED_POPULATION_WITH_CORRECTION_CONFLICT_CONTRACT"
    population["reason"] = (
        "CM retains the reviewed CL population at eight observations and eleven evidence rows while hardening correction, retraction and conflicting-report validation; no production row is added."
    )
    population["maximum_observation_count"] = 8
    population["maximum_evidence_count"] = 11
    population["automatic_ingestion_allowed"] = False
    population["public_observation_projection_allowed"] = False
    schema["population_policy"] = population

    schema["cm_checkpoint"] = {
        "schema_version": "0.9",
        "observations_version": "0.9",
        "evidence_version": "0.9",
        "population_state": "CONTROLLED_CANONICAL_LINKED_INSTITUTIONAL_OUTCOME_SPECIMEN",
        "observation_count": 8,
        "evidence_count": 11,
        "base_main_sha": BASE,
        "historical_contract": (
            "CM preserves all eight CL observations and eleven evidence rows while adding a no-population executable contract for CORRECTED, RETRACTED and CONFLICTING_REPORTS semantics."
        ),
    }
    return schema


def target_observations(observations: dict) -> dict:
    observations["version"] = "0.9"
    observations["reference_date"] = "2026-09-10"
    observations["scope_note"] = (
        "Bounded reviewed internal Live Intelligence store through CM: the eight CL observations are retained unchanged while v0.9 hardens correction, retraction and conflicting-report semantics using synthetic contract tests only. Waqa Moana remains excluded; public projection and automatic ingestion remain closed."
    )
    return observations


def target_evidence(evidence: dict) -> dict:
    evidence["version"] = "0.9"
    evidence["reference_date"] = "2026-09-10"
    evidence["scope_note"] = (
        "Evidence supports the unchanged eight-observation Live store through CM. No production evidence row is added; v0.9 hardens correction, retraction and conflicting-report validation using synthetic fixtures only. Live evidence remains separate from Canonical provenance and Analysis evidence, and public observation projection remains closed."
    )
    return evidence


def patch_validator() -> None:
    text = VALIDATOR.read_text(encoding="utf-8")
    import_anchor = "from zoneinfo import ZoneInfo, ZoneInfoNotFoundError\n"
    import_line = (
        "from world_signals.live_correction_conflict import validate_correction_conflict_contract\n"
    )
    require(import_anchor in text, "CM validator import anchor missing")
    require(import_line not in text, "CM validator import already present")
    text = text.replace(import_anchor, import_anchor + "\n" + import_line, 1)

    old_block = '''        if row.get("verification_state") in {"CORRECTED", "RETRACTED"} and not revision_ref:\n            errors.append(f"{observation_id}: corrected/retracted live observation requires revision reference")\n\n'''
    require(old_block in text, "CM weak correction block missing")
    text = text.replace(old_block, "", 1)

    loop_anchor = '''    observations_by_id = {\n        row.get("observation_id"): row\n        for row in observations\n        if row.get("observation_id")\n    }\n\n    for row in observations:\n'''
    replacement = '''    observations_by_id = {\n        row.get("observation_id"): row\n        for row in observations\n        if row.get("observation_id")\n    }\n\n    errors.extend(\n        validate_correction_conflict_contract(schema, evidence_by_id, observations)\n    )\n\n    for row in observations:\n'''
    require(loop_anchor in text, "CM validator integration anchor missing")
    text = text.replace(loop_anchor, replacement, 1)
    VALIDATOR.write_text(text, encoding="utf-8")


def prove_rows_unchanged() -> None:
    base_observations = git_json("data/live_intelligence/observations.json")
    base_evidence = git_json("data/live_intelligence/evidence_registry.json")
    current_observations = load(OBSERVATIONS)
    current_evidence = load(EVIDENCE)
    require(
        current_observations.get("observations") == base_observations.get("observations"),
        "CM must preserve every production Live observation object exactly",
    )
    require(
        current_evidence.get("evidence") == base_evidence.get("evidence"),
        "CM must preserve every production Live evidence object exactly",
    )
    states = {
        row.get("verification_state")
        for row in current_observations.get("observations", [])
    }
    require(
        states.isdisjoint({"CONFLICTING_REPORTS", "CORRECTED", "RETRACTED"}),
        "CM must not populate production conflict/correction/retraction rows",
    )


def main() -> None:
    schema, observations, evidence = preflight()
    write_json(SCHEMA, target_schema(schema))
    write_json(OBSERVATIONS, target_observations(observations))
    write_json(EVIDENCE, target_evidence(evidence))
    patch_validator()
    prove_rows_unchanged()

    env = dict(__import__("os").environ)
    env["WORLD_SIGNALS_WRITE_DERIVED_STATE"] = "YES"
    subprocess.run(
        ["python", "scripts/project_state_snapshot.py", "--write"],
        cwd=ROOT,
        env=env,
        check=True,
    )
    print("CM_CONTRACT_MATERIALISED_IN_WORKTREE")


if __name__ == "__main__":
    main()
