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
from world_signals.checkpoint_contract import validate_descendant_checkpoint, version_at_least
from world_signals.analysis_revision import (
    production_analysis_revision_count,
    validate_analysis_revisions,
)
from world_signals.live_analysis_bridge import (
    production_live_input_count,
    validate_live_analysis_bridge,
)
from world_signals.live_intelligence import validate_live_intelligence

PLAN_PATH = ROOT / "data/analysis/ANALYSIS_REVISION_CONTRACT_BA_PLAN_v0.1.json"

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


def target_revision_policy() -> dict[str, Any]:
    return {
        "mode": "FOUNDATION_ONLY_NO_PRODUCTION_REVISIONS",
        "production_analysis_revisions_allowed": False,
        "public_revision_metadata_projection_allowed": False,
        "required_revision_fields": [
            "revision_of_analysis_id",
            "analysis_revision_kind",
            "analysis_revision_reason",
        ],
        "allowed_revision_fields": [
            "revision_of_analysis_id",
            "analysis_revision_kind",
            "analysis_revision_reason",
        ],
        "allowed_revision_kinds": [
            "FACTUAL_CORRECTION",
            "NEW_EVIDENCE",
            "NEW_LIVE_EVIDENCE",
            "METHODOLOGICAL_REASSESSMENT",
            "CAUSAL_REASSESSMENT",
            "SCOPE_OR_FRAMING_UPDATE",
        ],
        "parent_snapshot_must_remain_present": True,
        "same_canonical_occurrence_required": True,
        "analysis_as_of_must_strictly_advance": True,
        "cycles_prohibited": True,
        "branching_prohibited_in_first_controlled_mode": True,
        "new_live_evidence_revision_requires_novel_live_input": True,
        "live_observation_does_not_automatically_create_revision": True,
        "live_revision_and_analysis_revision_are_distinct": True,
        "upstream_canonical_mutation_allowed": False,
        "upstream_live_mutation_allowed": False,
        "upstream_monitor_mutation_allowed": False,
        "google_calendar_write_allowed": False,
        "automatic_latest_analysis_selection_allowed": False,
        "public_revision_head_collapse_allowed": False,
        "future_production_revision_requires_pressure_audit": True,
    }


def target_analysis_schema(current: dict[str, Any]) -> dict[str, Any]:
    if current.get("version") != "0.6":
        policy = current.get("analysis_revision_policy") or {}
        required_fields = set(policy.get("required_revision_fields") or [])
        require(
            set(target_revision_policy()["required_revision_fields"]).issubset(required_fields),
            "BA Analysis descendant lost required revision fields",
        )
        report = validate_descendant_checkpoint(
            versions_at_least={
                "BA Analysis schema": (current.get("version"), "0.7"),
            },
            exact_values={
                "BA parent preservation": (policy.get("parent_snapshot_must_remain_present"), True),
                "BA same Canonical occurrence": (policy.get("same_canonical_occurrence_required"), True),
                "BA as-of advancement": (policy.get("analysis_as_of_must_strictly_advance"), True),
                "BA cycle prohibition": (policy.get("cycles_prohibited"), True),
                "BA Live/Analysis lineage separation": (policy.get("live_revision_and_analysis_revision_are_distinct"), True),
                "BA upstream Canonical mutation": (policy.get("upstream_canonical_mutation_allowed"), False),
                "BA upstream Live mutation": (policy.get("upstream_live_mutation_allowed"), False),
                "BA upstream monitor mutation": (policy.get("upstream_monitor_mutation_allowed"), False),
                "BA Calendar write": (policy.get("google_calendar_write_allowed"), False),
            },
        )
        require(
            report.ok,
            "BA Analysis descendant contract failed: " + "; ".join(report.errors),
        )
        return deepcopy(current)

    target = deepcopy(current)
    target["version"] = "0.7"
    target["reference_date"] = "2026-09-06"
    target["analysis_revision_policy"] = target_revision_policy()

    additions = [
        "BA v0.7 introduces a prospective Analysis revision-lineage contract while production revisions remain closed and the existing 21 reviewed snapshots remain unchanged.",
        "A future Analysis revision must be a new immutable analysis_id with an explicit direct parent, preserved parent snapshot, same Canonical occurrence and strictly later analysis_as_of_utc; silent in-place analytical history rewrite is prohibited.",
        "Live observations never automatically revise Analysis, Live revision/state-update lineage remains distinct from Analysis revision lineage, automatic latest-Analysis selection remains prohibited, and further production revision population requires another pressure audit.",
    ]
    guardrails = list(target.get("guardrails") or [])
    for item in additions:
        if item not in guardrails:
            guardrails.append(item)
    target["guardrails"] = guardrails
    return target

def target_status(current: str) -> str:
    old_header = "# CURRENT RECOVERY OVERRIDE — POST-AY / AZ FIRST PRODUCTION LIVE→ANALYSIS LINK"
    new_header = "# CURRENT RECOVERY OVERRIDE — POST-AZ / BA ANALYSIS REVISION FOUNDATION"
    if old_header not in current and new_header not in current:
        # Later recovery overrides are mutable documentation, not governed BA state.
        # BA descendant truth is enforced by Analysis schema/revision-policy invariants.
        return current
    text = current.replace(old_header, new_header, 1)
    text = text.replace("- Analysis schema: **v0.6**", "- Analysis schema: **v0.7**", 1)

    live_line = "- production `live_inputs`: **1 / reviewed maximum 1 / public projection CLOSED**\n"
    revision_line = "- production Analysis revisions: **0 / gate CLOSED / public revision metadata projection CLOSED**\n"
    if revision_line not in text:
        require(live_line in text, "BA status could not locate production live-input line")
        text = text.replace(live_line, live_line + revision_line, 1)

    marker = "## Current architecture decision\n\n"
    paragraph = (
        "BA adds a **production-closed Analysis revision-lineage contract** before any further Live or bridge population. "
        "A future revision must be a new immutable Analysis snapshot with an explicit direct parent, preserved prior snapshot, "
        "the same Canonical occurrence and a strictly later `analysis_as_of_utc`. Automatic latest-head selection, public revision "
        "metadata projection and all upstream writes remain closed. BA adds no production revision, no Live observation and no Analysis evidence.\n\n"
    )
    if paragraph not in text:
        require(marker in text, "BA status could not locate architecture-decision marker")
        text = text.replace(marker, marker + paragraph, 1)

    stale = (
        "The next audit should decide whether prospective Live Intelligence → Analysis linkage now creates more architectural value "
        "than another isolated Live specimen. Japan household spending remains a valid held Analysis specimen, not a queue-completion obligation."
    )
    replacement = (
        "After BA, another pressure audit must decide whether the first real Analysis revision, a fifth Live observation, or a second "
        "production Live→Analysis relationship creates the highest marginal contract pressure. None is a population quota."
    )
    if stale in text:
        text = text.replace(stale, replacement, 1)
    return text

def target_roadmap(current: str) -> str:
    heading = "## Stage 8A — Analysis revision lineage — BA FOUNDATION DONE / PRODUCTION CLOSED"
    if heading in current or "BA establishes the prospective grammar for changing an analytical judgement without rewriting the prior snapshot." in current:
        return current
    marker = "## Stage 9 — broader Live Intelligence population / monitoring — ONLY AFTER AUDIT"
    require(marker in current, "BA roadmap could not locate Stage 9 marker")
    section = """## Stage 8A — Analysis revision lineage — BA FOUNDATION DONE / PRODUCTION CLOSED

BA establishes the prospective grammar for changing an analytical judgement without rewriting the prior snapshot. Production revision population remains zero.

A future revision must be a new immutable `analysis_id` linked by `revision_of_analysis_id`, preserve the parent row, remain on the same Canonical occurrence and advance `analysis_as_of_utc`. Revision kind and reason are explicit. Cycles and first-mode branching are prohibited. `NEW_LIVE_EVIDENCE` revisions must identify at least one novel immutable Live observation relative to the parent.

Live observations never automatically revise Analysis. Live correction/state-update lineage and Analysis revision lineage remain separate. No public latest-head collapse or revision-metadata projection is opened by BA. The first production Analysis revision requires another pressure audit.

"""
    return current.replace(marker, section + marker, 1)


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

    materialised = version_at_least(analysis_schema.get("version"), "0.7")
    if not materialised:
        require(canonical.get("version") == pre["canonical_registry_version"], "BA Canonical version drift")
        require(len(canonical.get("records", [])) == pre["canonical_record_count"], "BA Canonical count drift")
        require(sources.get("version") == pre["source_registry_version"], "BA Source version drift")
        require(len(sources.get("sources", [])) == pre["source_count"], "BA Source count drift")
        require(ledger.get("version") == pre["change_ledger_version"], "BA Change Ledger version drift")
        require(len(ledger.get("changes", [])) == pre["change_ledger_count"], "BA Change Ledger count drift")
        require(expectations.get("version") == pre["monitor_expectations_version"], "BA monitor version drift")
        require(len(expectations.get("adapters", [])) == pre["monitor_adapter_count"], "BA monitor adapter count drift")
        require(live_schema.get("version") == pre["live_schema_version"], "BA Live schema drift")
        require(len(live_observations.get("observations", [])) == pre["live_observation_count"], "BA Live observation count drift")
        require(len(live_evidence.get("evidence", [])) == pre["live_evidence_count"], "BA Live evidence count drift")
        require(analysis_schema.get("version") == pre["analysis_schema_version"], "BA Analysis schema drift")
        require(reviews.get("version") == pre["analysis_reviews_version"], "BA Analysis reviews version drift")
        require(len(reviews.get("reviews", [])) == pre["analysis_review_count"], "BA Analysis review count drift")
        require(analysis_evidence.get("version") == pre["analysis_evidence_version"], "BA Analysis evidence version drift")
        require(len(analysis_evidence.get("evidence", [])) == pre["analysis_evidence_count"], "BA Analysis evidence count drift")
        require(production_live_input_count(reviews) == pre["production_live_input_count"], "BA production live-input drift")
        require(production_analysis_revision_count(reviews) == 0, "BA requires zero pre-existing Analysis revisions")
        require(exact_series_count(reviews) == pre["production_exact_timestamp_series_count"], "BA exact-series drift")
        return

    report = validate_descendant_checkpoint(
        versions_at_least={
            "BA Analysis schema": (analysis_schema.get("version"), "0.7"),
            "BA Analysis reviews": (reviews.get("version"), pre["analysis_reviews_version"]),
            "BA Analysis evidence": (analysis_evidence.get("version"), pre["analysis_evidence_version"]),
            "BA Live schema": (live_schema.get("version"), pre["live_schema_version"]),
        },
        counts_at_least={
            "BA Analysis review population": (len(reviews.get("reviews", [])), pre["analysis_review_count"]),
            "BA Analysis evidence population": (len(analysis_evidence.get("evidence", [])), pre["analysis_evidence_count"]),
            "BA Live observation population": (len(live_observations.get("observations", [])), pre["live_observation_count"]),
            "BA Live evidence population": (len(live_evidence.get("evidence", [])), pre["live_evidence_count"]),
            "BA production Live inputs": (production_live_input_count(reviews), pre["production_live_input_count"]),
        },
    )
    require(report.ok, "BA descendant precondition failed: " + "; ".join(report.errors))
    target_analysis_schema(analysis_schema)

def simulate() -> dict[str, Any]:
    return {
        "analysis_schema": target_analysis_schema(load(ANALYSIS_SCHEMA_PATH)),
        "status": target_status(STATUS_PATH.read_text(encoding="utf-8")),
        "roadmap": target_roadmap(ROADMAP_PATH.read_text(encoding="utf-8")),
    }


def assert_target(plan: dict[str, Any], target: dict[str, Any]) -> None:
    schema = target["analysis_schema"]
    reviews = load(REVIEWS_PATH)
    evidence = load(ANALYSIS_EVIDENCE_PATH)
    canonical = load(CANONICAL_PATH)
    live_schema = load(LIVE_SCHEMA_PATH)
    live_evidence = load(LIVE_EVIDENCE_PATH)
    live_observations = load(LIVE_OBSERVATIONS_PATH)

    target_analysis_schema(schema)
    exact_foundation = (
        schema.get("version") == "0.7"
        and len(reviews.get("reviews", [])) == 21
        and len(evidence.get("evidence", [])) == 95
        and production_analysis_revision_count(reviews) == 0
        and production_live_input_count(reviews) == 1
    )
    if exact_foundation:
        require(schema.get("analysis_revision_policy") == target_revision_policy(), "BA revision policy drift")
        require(exact_series_count(reviews) == 0, "BA target must preserve EXACT_TIMESTAMP_SERIES=0")
    else:
        report = validate_descendant_checkpoint(
            versions_at_least={
                "BA target Analysis schema": (schema.get("version"), "0.7"),
                "BA target reviews": (reviews.get("version"), "0.17"),
                "BA target evidence": (evidence.get("version"), "0.17"),
            },
            counts_at_least={
                "BA target review population": (len(reviews.get("reviews", [])), 21),
                "BA target evidence population": (len(evidence.get("evidence", [])), 95),
                "BA target production Live inputs": (production_live_input_count(reviews), 1),
            },
        )
        require(report.ok, "BA target descendant failed: " + "; ".join(report.errors))

    core = validate_analysis(schema, evidence, reviews, canonical)
    require(core.ok, "BA target core Analysis validation failed: " + "; ".join(core.errors))
    revisions = validate_analysis_revisions(schema, reviews)
    require(revisions.ok, "BA target revision validation failed: " + "; ".join(revisions.errors))
    bridge = validate_live_analysis_bridge(schema, reviews, live_observations)
    require(bridge.ok, "BA target Live→Analysis bridge validation failed: " + "; ".join(bridge.errors))
    live = validate_live_intelligence(live_schema, live_evidence, live_observations, canonical)
    require(live.ok, "BA target Live validation failed: " + "; ".join(live.errors))

    required_doc_markers = {
        "BA roadmap": (target["roadmap"], ["BA establishes the prospective grammar for changing an analytical judgement without rewriting the prior snapshot."]),
    }
    if target["status"].startswith("# CURRENT RECOVERY OVERRIDE — POST-AZ / BA ANALYSIS REVISION FOUNDATION"):
        required_doc_markers["BA status"] = (
            target["status"],
            ["BA adds a **production-closed Analysis revision-lineage contract**"],
        )
    docs = validate_descendant_checkpoint(required_markers=required_doc_markers)
    require(docs.ok, "BA target documentation drift: " + "; ".join(docs.errors))

def write_target(target: dict[str, Any]) -> None:
    ANALYSIS_SCHEMA_PATH.write_text(dump(target["analysis_schema"]), encoding="utf-8")
    STATUS_PATH.write_text(target["status"], encoding="utf-8")
    ROADMAP_PATH.write_text(target["roadmap"], encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-only", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    plan = load(PLAN_PATH)
    assert_preconditions(plan)
    target = simulate()
    assert_target(plan, target)

    if args.check_only:
        print("BA read-only simulation: PASS")
        return

    require(
        os.environ.get("WORLD_SIGNALS_BA_ALLOW_WRITE") == "1",
        "BA apply requires WORLD_SIGNALS_BA_ALLOW_WRITE=1",
    )
    write_target(target)
    print("BA Analysis revision foundation materialised: PASS")


if __name__ == "__main__":
    main()
