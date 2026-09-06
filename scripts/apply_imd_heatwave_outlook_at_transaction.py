#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import apply_imd_heatwave_outlook_at as base
from world_signals.analytical_overlays import validate_biosecurity_overlay
from world_signals.coverage import build_coverage_audit
from world_signals.validation import validate_registry

PLAN_PATH = base.PLAN_PATH
CANONICAL_PATH = base.CANONICAL_PATH
SCHEMA_PATH = base.SCHEMA_PATH
SOURCES_PATH = base.SOURCES_PATH
LEDGER_PATH = base.LEDGER_PATH
OVERLAY_PATH = base.OVERLAY_PATH
EXPECTATIONS_PATH = base.EXPECTATIONS_PATH
OPERATIONS_PATH = base.OPERATIONS_PATH
ANALYSIS_SCHEMA_PATH = base.ANALYSIS_SCHEMA_PATH
REVIEWS_PATH = base.REVIEWS_PATH
EVIDENCE_PATH = base.EVIDENCE_PATH
AUDIT_PATH = base.AUDIT_PATH
APPLY_ENV = base.APPLY_ENV

PROTECTED = {
    "canonical_schema": SCHEMA_PATH,
    "change_ledger": LEDGER_PATH,
    "monitor_expectations": EXPECTATIONS_PATH,
    "monitor_operations_policy": OPERATIONS_PATH,
    "analysis_schema": ANALYSIS_SCHEMA_PATH,
    "analysis_reviews": REVIEWS_PATH,
    "analysis_evidence": EVIDENCE_PATH,
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def protected_hashes() -> dict[str, str]:
    return {name: sha256(path) for name, path in PROTECTED.items()}


def overlay_semantics(overlay: dict[str, Any]) -> dict[str, Any]:
    return {
        key: copy.deepcopy(value)
        for key, value in overlay.items()
        if key not in {"version", "canonical_checkpoint"}
    }


def build_post_bundle(plan: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    pre = plan["preconditions"]
    post = plan["postconditions"]

    live_canonical = load(CANONICAL_PATH)
    overlay = load(OVERLAY_PATH)
    require(overlay.get("version") == pre["biosecurity_overlay_version"], "AT overlay version pre-state mismatch")
    require(overlay.get("canonical_checkpoint") == pre["biosecurity_overlay_checkpoint"], "AT overlay checkpoint pre-state mismatch")
    overlay_errors = validate_biosecurity_overlay(live_canonical, overlay)
    require(not overlay_errors, "AT overlay pre-state invalid: " + "; ".join(overlay_errors))

    semantic_before = overlay_semantics(overlay)
    candidate_canonical, candidate_sources, coverage = base.build_post_state(plan)

    candidate_overlay = copy.deepcopy(overlay)
    candidate_overlay["version"] = post["biosecurity_overlay_version"]
    candidate_overlay["canonical_checkpoint"] = copy.deepcopy(post["biosecurity_overlay_checkpoint"])

    require(overlay_semantics(candidate_overlay) == semantic_before, "AT overlay semantic content changed")
    require(candidate_overlay["canonical_checkpoint"] == {
        "registry_version": candidate_canonical["version"],
        "record_count": candidate_canonical["record_count"],
    }, "AT overlay checkpoint does not match candidate Canonical state")

    overlay_errors = validate_biosecurity_overlay(candidate_canonical, candidate_overlay)
    require(not overlay_errors, "AT candidate overlay invalid: " + "; ".join(overlay_errors))

    return candidate_canonical, candidate_sources, candidate_overlay, coverage


def render_audit(
    plan: dict[str, Any],
    coverage: dict[str, Any],
    protected_before: dict[str, str],
    protected_after: dict[str, str],
) -> str:
    pre = plan["preconditions"]
    post = plan["postconditions"]
    south_asia = next(row for row in coverage["by_region"] if row["region"] == "South Asia")
    physical = next(row for row in coverage["by_category"] if row["category"] == "PHYSICAL_CLIMATE_RISK")
    return f"""# WORLD SIGNALS — IMD heatwave outlook AT transaction audit v0.2

**Executed:** 2026-09-06
**Exact base:** `{plan['base_main_sha']}`

## Controlled governed-state mutation

- Canonical Registry: `v{pre['canonical_registry_version']} / {pre['canonical_record_count']}` → `v{post['canonical_registry_version']} / {post['canonical_record_count']}`
- Source Registry: `v{pre['source_registry_version']} / {pre['source_registry_count']}` → `v{post['source_registry_version']} / {post['source_registry_count']}`
- Biosecurity analytical overlay: `v{pre['biosecurity_overlay_version']} @ v{pre['biosecurity_overlay_checkpoint']['registry_version']}/{pre['biosecurity_overlay_checkpoint']['record_count']}` → `v{post['biosecurity_overlay_version']} @ v{post['biosecurity_overlay_checkpoint']['registry_version']}/{post['biosecurity_overlay_checkpoint']['record_count']}`
- added occurrence: `WSO-RISK-A-0002`
- added series: `WSER-RISK-IN-HEAT-OUTLOOK`
- added source: `WSSRC-RISK-005`

The overlay advance changes **only** `version` and `canonical_checkpoint`. Systems, relationships, canonical-series memberships, candidate nodes, principles and notes remain semantically unchanged. The IMD outlook receives no biosecurity membership.

## Object boundary

The new occurrence is the **31 March 2026 IMD publication event**. It is not an April–June heatwave season and not an observed heatwave shock. The April–June period remains forecast/reference scope only. No publication clock time or UTC timestamp was invented.

`WSFR-RISK-NIO-TC` remains deferred under `OFFICIAL_SOURCE_DEFINITION_CONFLICT`; AT does not choose April–May versus April–June.

## Coverage result

```json
{json.dumps({'totals': coverage['totals'], 'south_asia': south_asia, 'physical_climate_risk': physical, 'diagnostic_flags': coverage['diagnostic_flags']}, indent=2)}
```

The South Asia and physical-risk mechanical prompts remain open after the correction. This is intentional; AT is not a threshold-clearing transaction.

## Protected-state audit

Protected datasets unchanged: **{protected_before == protected_after}**

```json
{json.dumps({'before': protected_before, 'after': protected_after}, indent=2)}
```

## Deliberate non-actions

- no Canonical-schema mutation
- no Change Ledger mutation
- no monitor configuration or operations-policy mutation
- no Analysis schema/review/evidence mutation
- no biosecurity semantic-membership mutation
- no `EXACT_TIMESTAMP_SERIES` ingestion
- no future 2027 outlook occurrence
- no North Indian Ocean cyclone-season population
- no automatic canonical commit
- no Google Calendar write
"""


def run_check() -> dict[str, Any]:
    plan = load(PLAN_PATH)
    paths = [CANONICAL_PATH, SOURCES_PATH, OVERLAY_PATH, *PROTECTED.values()]
    before = {str(path): sha256(path) for path in paths}
    candidate_canonical, candidate_sources, candidate_overlay, coverage = build_post_bundle(plan)
    after = {str(path): sha256(path) for path in paths}
    require(after == before, "AT read-only transaction check mutated repository state")
    return {
        "status": "PASS",
        "mode": "READ_ONLY_CHECK",
        "canonical_post": [candidate_canonical["version"], candidate_canonical["record_count"]],
        "source_post": [candidate_sources["version"], len(candidate_sources["sources"])],
        "overlay_post": [candidate_overlay["version"], candidate_overlay["canonical_checkpoint"]],
        "occurrence_id": plan["occurrence"]["occurrence_id"],
        "coverage_totals": coverage["totals"],
        "north_indian_ocean_candidate": "DEFERRED_OFFICIAL_SOURCE_DEFINITION_CONFLICT",
        "automatic_canonical_commit": False,
        "google_calendar_write": False,
    }


def run_write() -> dict[str, Any]:
    require(os.environ.get(APPLY_ENV) == "1", f"AT write requires {APPLY_ENV}=1")
    plan = load(PLAN_PATH)
    protected_before = protected_hashes()
    candidate_canonical, candidate_sources, candidate_overlay, coverage = build_post_bundle(plan)

    dump(SOURCES_PATH, candidate_sources)
    dump(CANONICAL_PATH, candidate_canonical)
    dump(OVERLAY_PATH, candidate_overlay)

    protected_after = protected_hashes()
    require(protected_after == protected_before, "AT controlled write mutated protected datasets")

    written_canonical = load(CANONICAL_PATH)
    written_sources = load(SOURCES_PATH)
    written_overlay = load(OVERLAY_PATH)
    post_report = validate_registry(written_canonical, written_sources)
    require(post_report.ok, "AT written state failed canonical validation: " + "; ".join(post_report.errors))
    overlay_errors = validate_biosecurity_overlay(written_canonical, written_overlay)
    require(not overlay_errors, "AT written overlay failed validation: " + "; ".join(overlay_errors))
    require(written_overlay["canonical_checkpoint"] == {
        "registry_version": written_canonical["version"],
        "record_count": written_canonical["record_count"],
    }, "AT written overlay checkpoint drifted from Canonical")

    written_coverage = build_coverage_audit(written_canonical, written_sources)
    require(written_coverage["totals"] == coverage["totals"], "AT written coverage differs from simulated coverage")

    AUDIT_PATH.write_text(render_audit(plan, written_coverage, protected_before, protected_after), encoding="utf-8")
    return {
        "status": "WROTE_CONTROLLED_AT_STATE",
        "canonical_post": [candidate_canonical["version"], candidate_canonical["record_count"]],
        "source_post": [candidate_sources["version"], len(candidate_sources["sources"])],
        "overlay_post": [candidate_overlay["version"], candidate_overlay["canonical_checkpoint"]],
        "occurrence_id": plan["occurrence"]["occurrence_id"],
        "protected_unchanged": True,
        "overlay_semantics_unchanged": True,
        "automatic_canonical_commit": False,
        "google_calendar_write": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    require(args.check ^ args.write, "choose exactly one of --check or --write")
    result = run_write() if args.write else run_check()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
