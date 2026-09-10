#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.analysis import validate_analysis
from world_signals.analysis_revision import validate_analysis_revisions
from world_signals.analytical_overlays import validate_biosecurity_overlay
from world_signals.ecb_monetary_outcome_cp import build_target_state, validate_cp_contract
from world_signals.live_analysis_bridge import validate_live_analysis_bridge
from world_signals.live_intelligence import validate_live_intelligence
from world_signals.validation import validate_registry

CANONICAL = ROOT / "data/canonical/registry.json"
SOURCES = ROOT / "data/sources/registry.json"
LEDGER = ROOT / "data/changes/ledger.json"
OVERLAY = ROOT / "data/coverage/biosecurity_overlay.json"
LIVE_SCHEMA = ROOT / "data/live_intelligence/schema.json"
LIVE_OBSERVATIONS = ROOT / "data/live_intelligence/observations.json"
LIVE_EVIDENCE = ROOT / "data/live_intelligence/evidence_registry.json"
ANALYSIS_SCHEMA = ROOT / "data/analysis/schema.json"
ANALYSIS_REVIEWS = ROOT / "data/analysis/event_reviews.json"
ANALYSIS_EVIDENCE = ROOT / "data/analysis/evidence_registry.json"
MONITOR_EXPECTATIONS = ROOT / "data/monitor/expectations.json"
MONITOR_OPERATIONS = ROOT / "data/monitor/operations_policy.json"
CANONICAL_SCHEMA = ROOT / "data/canonical/schema.json"
OPEC_QUARANTINE = ROOT / "OPEC_QUARANTINE.md"
OPEC_TEST = ROOT / "tests/test_opec_quarantine_cf.py"
PLAN = ROOT / "data/live_intelligence/ECB_MONETARY_OUTCOME_CP_PRODUCTION_PLAN_v0.1.json"
PAYLOAD = ROOT / "data/live_intelligence/ECB_MONETARY_OUTCOME_CP_PAYLOAD_v0.1.json"

APPLY_ENV = "WORLD_SIGNALS_APPLY_ECB_CP"
APPLY_VALUE = "REVIEWED_APPLY"

PROTECTED = {
    "canonical_schema": CANONICAL_SCHEMA,
    "source_registry": SOURCES,
    "monitor_expectations": MONITOR_EXPECTATIONS,
    "monitor_operations": MONITOR_OPERATIONS,
    "analysis_schema": ANALYSIS_SCHEMA,
    "analysis_reviews": ANALYSIS_REVIEWS,
    "analysis_evidence": ANALYSIS_EVIDENCE,
    "opec_quarantine": OPEC_QUARANTINE,
    "opec_quarantine_test": OPEC_TEST,
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transaction_time() -> str:
    return datetime.now(ZoneInfo("Australia/Melbourne")).isoformat(timespec="seconds")


def load_state() -> tuple[dict, ...]:
    return (
        load(CANONICAL),
        load(SOURCES),
        load(LEDGER),
        load(OVERLAY),
        load(LIVE_SCHEMA),
        load(LIVE_OBSERVATIONS),
        load(LIVE_EVIDENCE),
        load(ANALYSIS_SCHEMA),
        load(ANALYSIS_REVIEWS),
        load(ANALYSIS_EVIDENCE),
        load(PLAN),
        load(PAYLOAD),
    )


def validate_target(
    post_registry: dict,
    sources: dict,
    post_ledger: dict,
    post_overlay: dict,
    post_live_schema: dict,
    post_observations: dict,
    post_evidence: dict,
    analysis_schema: dict,
    analysis_reviews: dict,
    analysis_evidence: dict,
    plan: dict,
) -> None:
    errors = validate_cp_contract(
        post_registry,
        sources,
        post_ledger,
        post_overlay,
        post_live_schema,
        post_observations,
        post_evidence,
        plan,
    )

    canonical = validate_registry(post_registry, sources)
    errors.extend(f"Canonical target: {err}" for err in canonical.errors)

    errors.extend(
        f"Biosecurity overlay target: {err}"
        for err in validate_biosecurity_overlay(post_registry, post_overlay)
    )

    live = validate_live_intelligence(
        post_live_schema,
        post_evidence,
        post_observations,
        post_registry,
    )
    errors.extend(f"Live target: {err}" for err in live.errors)

    analysis = validate_analysis(
        analysis_schema,
        analysis_evidence,
        analysis_reviews,
        post_registry,
    )
    errors.extend(f"Analysis target: {err}" for err in analysis.errors)

    revisions = validate_analysis_revisions(analysis_schema, analysis_reviews)
    errors.extend(f"Analysis revisions: {err}" for err in revisions.errors)

    bridge = validate_live_analysis_bridge(
        analysis_schema,
        analysis_reviews,
        post_observations,
    )
    errors.extend(f"Live→Analysis bridge: {err}" for err in bridge.errors)

    if errors:
        raise SystemExit("CP TARGET VALIDATION FAILED:\n- " + "\n- ".join(errors))


def build(committed_at: str | None = None):
    (
        registry,
        sources,
        ledger,
        overlay,
        live_schema,
        observations,
        evidence,
        analysis_schema,
        analysis_reviews,
        analysis_evidence,
        plan,
        payload,
    ) = load_state()

    target = build_target_state(
        registry,
        sources,
        ledger,
        overlay,
        live_schema,
        observations,
        evidence,
        payload,
        plan,
        committed_at=committed_at,
    )

    validate_target(
        target[0],
        sources,
        target[1],
        target[2],
        target[3],
        target[4],
        target[5],
        analysis_schema,
        analysis_reviews,
        analysis_evidence,
        plan,
    )
    return target, sources, plan


def verify_materialized() -> dict:
    (
        registry,
        sources,
        ledger,
        overlay,
        live_schema,
        observations,
        evidence,
        analysis_schema,
        analysis_reviews,
        analysis_evidence,
        plan,
        _payload,
    ) = load_state()

    validate_target(
        registry,
        sources,
        ledger,
        overlay,
        live_schema,
        observations,
        evidence,
        analysis_schema,
        analysis_reviews,
        analysis_evidence,
        plan,
    )
    return {
        "status": "MATERIALISED_TARGET_VALID",
        "canonical_version": registry["version"],
        "canonical_count": len(registry["records"]),
        "ledger_version": ledger["version"],
        "ledger_count": len(ledger["changes"]),
        "live_version": observations["version"],
        "live_observations": len(observations["observations"]),
        "live_evidence": len(evidence["evidence"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--verify-materialized", action="store_true")
    args = parser.parse_args()

    if args.apply and args.verify_materialized:
        raise SystemExit("Choose either --apply or --verify-materialized")

    if args.verify_materialized:
        print(json.dumps(verify_materialized(), indent=2))
        return 0

    committed_at = transaction_time() if args.apply else None
    protected_before = {name: sha256(path) for name, path in PROTECTED.items()}
    target, _sources, plan = build(committed_at=committed_at)

    result = {
        "status": "SIMULATION_PASS" if not args.apply else "TARGET_VALIDATED_PRE_WRITE",
        "canonical": {
            "version": target[0]["version"],
            "record_count": len(target[0]["records"]),
        },
        "change_ledger": {
            "version": target[1]["version"],
            "count": len(target[1]["changes"]),
        },
        "biosecurity_overlay": {
            "version": target[2]["version"],
            "canonical_checkpoint": target[2]["canonical_checkpoint"],
        },
        "live": {
            "schema_version": target[3]["version"],
            "observations_version": target[4]["version"],
            "observation_count": len(target[4]["observations"]),
            "evidence_version": target[5]["version"],
            "evidence_count": len(target[5]["evidence"]),
        },
        "automatic_canonical_commit": False,
        "google_calendar_write": False,
        "automatic_monitor_to_live": False,
        "automatic_live_to_analysis": False,
        "public_projection": False,
    }

    if not args.apply:
        print(json.dumps(result, indent=2))
        return 0

    if os.environ.get(APPLY_ENV) != APPLY_VALUE:
        raise SystemExit(
            f"WRITE GATE CLOSED: set {APPLY_ENV}={APPLY_VALUE} for reviewed CP materialisation"
        )

    dump(CANONICAL, target[0])
    dump(LEDGER, target[1])
    dump(OVERLAY, target[2])
    dump(LIVE_SCHEMA, target[3])
    dump(LIVE_OBSERVATIONS, target[4])
    dump(LIVE_EVIDENCE, target[5])

    protected_after = {name: sha256(path) for name, path in PROTECTED.items()}
    changed = sorted(
        name for name in protected_before
        if protected_before[name] != protected_after[name]
    )
    if changed:
        raise SystemExit("PROTECTED-LAYER MUTATION: " + ", ".join(changed))

    verified = verify_materialized()
    result["status"] = "MATERIALISED_EPHEMERAL_TARGET_VALID"
    result["committed_at"] = committed_at
    result["verified"] = verified
    result["expected_post_state"] = plan["expected_post_state"]
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
