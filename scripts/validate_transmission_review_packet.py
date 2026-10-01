#!/usr/bin/env python3
"""Validate a review-only WORLD SIGNALS transmission packet.

This validator is deliberately independent of governed production stores. It
checks the candidate envelope and anti-overreach invariants only; successful
validation never constitutes admission into Signal, Relationship, Risk/Regime,
Scenario or World State production state.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

EXPECTED_GRAMMAR = [
    "SHOCK",
    "EXPOSURE",
    "TRANSMISSION",
    "BUFFER",
    "BEHAVIOURAL_RESPONSE",
    "FEEDBACK",
    "OUTCOME",
]
ALLOWED_LEVELS = {"GLOBAL_STATE", "JURISDICTION_STATE"}
ALLOWED_RELATIONSHIP_CLASSES = {
    "CO_OCCURRENCE",
    "ASSOCIATION",
    "DEPENDENCY",
    "COMMON_DRIVER",
    "HYPOTHESISED_TRANSMISSION",
    "MECHANISTICALLY_SUPPORTED",
    "CAUSAL_EVIDENCE",
    "FEEDBACK_LOOP",
}
PROHIBITED_KEYS = {
    "probability",
    "probability_percent",
    "likelihood",
    "odds",
    "rank",
    "ranking",
    "winner",
    "scenario_probability",
    "forecast_horizon",
    "predicted_outcome",
}


def walk_keys(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in PROHIBITED_KEYS:
                errors.append(f"prohibited field {path}.{key}")
            errors.extend(walk_keys(nested, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            errors.extend(walk_keys(nested, f"{path}[{index}]"))
    return errors


def validate(packet: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if packet.get("project") != "WORLD SIGNALS":
        errors.append("project must be WORLD SIGNALS")
    if packet.get("package_type") != "WORLD_STATE_STEP16A_AU_MACRO_TRANSMISSION_CANDIDATE":
        errors.append("unexpected package_type")
    if packet.get("package_version") != "0.1":
        errors.append("unsupported package_version")
    if packet.get("status") != "REVIEW_PENDING":
        errors.append("packet must remain REVIEW_PENDING")
    if packet.get("preflight_classification") != "READY_FOR_HUMAN_TRANSMISSION_REVIEW":
        errors.append("unexpected preflight_classification")

    scope = packet.get("scope", {})
    if set(scope.get("levels", [])) != ALLOWED_LEVELS:
        errors.append("scope.levels must be exactly GLOBAL_STATE and JURISDICTION_STATE")
    if not str(scope.get("network_state", "")).startswith("DEFERRED_"):
        errors.append("Network State must remain explicitly deferred in Step 16A")
    if packet.get("transmission_grammar") != EXPECTED_GRAMMAR:
        errors.append("transmission_grammar is not the controlled portable sequence")

    governance = packet.get("governance", {})
    if governance.get("visibility") != "INTERNAL_ONLY":
        errors.append("visibility must remain INTERNAL_ONLY")
    if governance.get("public_projection_permitted") is not False:
        errors.append("public projection must remain closed")
    if governance.get("production_write_targets") != []:
        errors.append("production_write_targets must be empty")
    for key in (
        "canonical_mutation_allowed",
        "live_intelligence_mutation_allowed",
        "signal_mutation_allowed",
        "relationship_mutation_allowed",
        "risk_regime_mutation_allowed",
        "scenario_mutation_allowed",
        "automatic_promotion_allowed",
    ):
        if governance.get(key) is not False:
            errors.append(f"{key} must be false")

    sources = packet.get("sources", [])
    source_ids = {row.get("source_id") for row in sources}
    if None in source_ids or len(source_ids) != len(sources):
        errors.append("source IDs must be unique and non-null")
    for row in sources:
        if row.get("source_class") == "SECONDARY_DISCOVERY" and row.get("production_support_eligible") is not False:
            errors.append(f"secondary source {row.get('source_id')} cannot be production-support eligible")
        if not row.get("url"):
            errors.append(f"source {row.get('source_id')} missing URL")

    observations = packet.get("observation_candidates", [])
    observation_ids = {row.get("candidate_id") for row in observations}
    if None in observation_ids or len(observation_ids) != len(observations):
        errors.append("observation candidate IDs must be unique and non-null")
    for row in observations:
        if row.get("level") not in ALLOWED_LEVELS:
            errors.append(f"invalid level on {row.get('candidate_id')}")
        refs = row.get("source_refs", [])
        if not refs or not set(refs) <= source_ids:
            errors.append(f"unknown or missing source_refs on {row.get('candidate_id')}")
        if row.get("evidence_role") == "SECONDARY_CONTEXT" and row.get("production_support_eligible") is not False:
            errors.append(f"secondary context {row.get('candidate_id')} cannot support production")

    relationships = packet.get("relationship_candidates", [])
    for row in relationships:
        if row.get("review_state") != "CANDIDATE":
            errors.append(f"relationship {row.get('candidate_id')} must remain CANDIDATE")
        if row.get("relationship_class_candidate") not in ALLOWED_RELATIONSHIP_CLASSES:
            errors.append(f"invalid relationship class on {row.get('candidate_id')}")
        refs = set(row.get("supporting_observation_candidate_ids", []))
        if not refs or not refs <= observation_ids:
            errors.append(f"invalid observation support on {row.get('candidate_id')}")
        if row.get("relationship_class_candidate") in {"MECHANISTICALLY_SUPPORTED", "CAUSAL_EVIDENCE"} and not row.get("causal_basis_candidate"):
            errors.append(f"strong relationship class lacks causal basis: {row.get('candidate_id')}")

    risk = packet.get("risk_state_candidate", {})
    if risk.get("review_state") != "CANDIDATE":
        errors.append("risk state must remain CANDIDATE")
    stages = {row.get("stage"): row.get("assessment") for row in risk.get("stages", [])}
    if stages != {1: "ACTIVE", 2: "EMERGING", 3: "NOT_ESTABLISHED"}:
        errors.append("AU housing stages must remain 1=ACTIVE, 2=EMERGING, 3=NOT_ESTABLISHED")
    if not set(risk.get("disconfirming_observation_candidate_ids", [])) <= observation_ids:
        errors.append("risk state has unknown disconfirming observation")

    scenario_set = packet.get("scenario_set_candidate", {})
    scenarios = packet.get("scenario_candidates", [])
    if scenario_set.get("review_state") != "DRAFT":
        errors.append("scenario set must remain DRAFT")
    scenario_ids = {row.get("scenario_id") for row in scenarios}
    if None in scenario_ids or len(scenario_ids) != len(scenarios) or len(scenarios) < 2:
        errors.append("scenario set must contain at least two distinct competing scenarios")
    for row in scenarios:
        if row.get("review_state") != "DRAFT":
            errors.append(f"scenario {row.get('scenario_id')} must remain DRAFT")
        if row.get("scenario_set_id") != scenario_set.get("scenario_set_id"):
            errors.append(f"scenario set mismatch on {row.get('scenario_id')}")
        if not row.get("signposts") or not row.get("disconfirming_signposts"):
            errors.append(f"scenario {row.get('scenario_id')} needs confirming and disconfirming signposts")

    counts = packet.get("expected_counts", {})
    actual = {
        "sources": len(sources),
        "observation_candidates": len(observations),
        "relationship_candidates": len(relationships),
        "risk_state_candidates": 1 if risk else 0,
        "scenario_candidates": len(scenarios),
    }
    if counts != actual:
        errors.append(f"expected_counts mismatch: expected={counts} actual={actual}")

    errors.extend(walk_keys(packet))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    args = parser.parse_args()
    packet = json.loads(args.packet.read_text(encoding="utf-8"))
    errors = validate(packet)
    if errors:
        print("Step 16A transmission packet: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        "Step 16A transmission packet: PASS "
        f"observations={len(packet['observation_candidates'])} "
        f"relationships={len(packet['relationship_candidates'])} "
        f"scenarios={len(packet['scenario_candidates'])} "
        "production_writes=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
