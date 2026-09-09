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
    ch_descendant_heading = "## Stage 7 — Analysis revision lineage — FIRST PRODUCTION REVISION DONE / PUBLIC CLOSED"
    ch_state_marker = "<!-- WORLD_SIGNALS_CURRENT_STATE_BEGIN -->"
    if (
        heading in current
        or "BA establishes the prospective grammar for changing an analytical judgement without rewriting the prior snapshot." in current
        or (ch_state_marker in current and ch_descendant_heading in current)
    ):
        # Later reviewed roadmaps are mutable recovery documentation. Once the
        # current derived-state contract and a production revision stage are
        # present, BA's historical roadmap transform is already superseded.
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
        },
        exact_values={
            "BA automatic Canonical commit gate": (expectations.get("automatic_canonical_commit"), False),
            "BA Google Calendar write gate": (expectations.get("google_calendar_write"), False),
        },
    )
    require(report.ok, "BA descendant preconditions failed: " + "; ".join(report.errors))


def assert_target(plan: dict[str, Any], target_schema: dict[str, Any]) -> None:
    target = plan["target_state"]
    require(version_at_least(target_schema.get("version"), target["analysis_schema_version"]), "BA target Analysis schema version mismatch")
    policy = target_schema.get("analysis_revision_policy") or {}
    require(policy.get("parent_snapshot_must_remain_present") is True, "BA must preserve revision parent")
    require(policy.get("same_canonical_occurrence_required") is True, "BA revision must stay on same Canonical occurrence")
    require(policy.get("analysis_as_of_must_strictly_advance") is True, "BA revision must advance analysis as-of")
    require(policy.get("cycles_prohibited") is True, "BA revision cycles must be prohibited")
    require(policy.get("branching_prohibited_in_first_controlled_mode") is True, "BA first mode must prohibit branching")
    require(policy.get("new_live_evidence_revision_requires_novel_live_input") is True, "BA novel Live evidence rule missing")
    require(policy.get("live_observation_does_not_automatically_create_revision") is True, "BA must prohibit automatic Live-to-revision promotion")
    require(policy.get("live_revision_and_analysis_revision_are_distinct") is True, "BA must separate Live and Analysis revision lineage")
    require(policy.get("upstream_canonical_mutation_allowed") is False, "BA must not mutate Canonical")
    require(policy.get("upstream_live_mutation_allowed") is False, "BA must not mutate Live")
    require(policy.get("upstream_monitor_mutation_allowed") is False, "BA must not mutate Monitor")
    require(policy.get("google_calendar_write_allowed") is False, "BA Calendar write must remain closed")
    require(policy.get("automatic_latest_analysis_selection_allowed") is False, "BA latest-head selection must remain closed")
    require(policy.get("public_revision_head_collapse_allowed") is False, "BA public revision-head collapse must remain closed")
    require(set(target_revision_policy()["required_revision_fields"]).issubset(set(policy.get("required_revision_fields") or [])), "BA required revision fields missing")


def simulate(plan: dict[str, Any]) -> dict[str, Any]:
    assert_preconditions(plan)
    current_schema = load(ANALYSIS_SCHEMA_PATH)
    target_schema = target_analysis_schema(current_schema)
    assert_target(plan, target_schema)
    return {
        "analysis_schema_version": target_schema["version"],
        "analysis_revision_policy_mode": (target_schema.get("analysis_revision_policy") or {}).get("mode"),
        "already_materialised_descendant": version_at_least(current_schema.get("version"), "0.7"),
    }


def apply(plan: dict[str, Any]) -> dict[str, Any]:
    require(os.environ.get("WORLD_SIGNALS_APPLY_ANALYSIS_REVISION_CONTRACT_BA") == "YES", "BA apply gate is closed")
    assert_preconditions(plan)

    current_schema = load(ANALYSIS_SCHEMA_PATH)
    target_schema = target_analysis_schema(current_schema)
    if current_schema != target_schema:
        ANALYSIS_SCHEMA_PATH.write_text(dump(target_schema), encoding="utf-8")

    current_status = STATUS_PATH.read_text(encoding="utf-8")
    target_status_text = target_status(current_status)
    if current_status != target_status_text:
        STATUS_PATH.write_text(target_status_text, encoding="utf-8")

    current_roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    target_roadmap_text = target_roadmap(current_roadmap)
    if current_roadmap != target_roadmap_text:
        ROADMAP_PATH.write_text(target_roadmap_text, encoding="utf-8")

    assert_target(plan, load(ANALYSIS_SCHEMA_PATH))
    return simulate(plan)


def validate_repository() -> None:
    canonical = load(CANONICAL_PATH)
    live_schema = load(LIVE_SCHEMA_PATH)
    live_observations = load(LIVE_OBSERVATIONS_PATH)
    live_evidence = load(LIVE_EVIDENCE_PATH)
    analysis_schema = load(ANALYSIS_SCHEMA_PATH)
    reviews = load(REVIEWS_PATH)
    evidence = load(ANALYSIS_EVIDENCE_PATH)

    live_errors = validate_live_intelligence(
        live_schema,
        live_observations,
        live_evidence,
        canonical,
    )
    require(not live_errors, "BA Live validation failed: " + "; ".join(live_errors))
    analysis_errors = validate_analysis(
        analysis_schema,
        reviews,
        evidence,
        canonical,
    )
    require(not analysis_errors, "BA Analysis validation failed: " + "; ".join(analysis_errors))
    bridge_errors = validate_live_analysis_bridge(
        analysis_schema,
        reviews,
        live_schema,
        live_observations,
        canonical,
    )
    require(not bridge_errors, "BA Live/Analysis bridge validation failed: " + "; ".join(bridge_errors))
    revision_errors = validate_analysis_revisions(
        analysis_schema,
        reviews,
        live_observations,
    )
    require(not revision_errors, "BA Analysis revision validation failed: " + "; ".join(revision_errors))


def main() -> int:
    parser = argparse.ArgumentParser(description="WORLD SIGNALS BA Analysis revision contract")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    require(args.check or args.apply or args.validate, "choose --check, --apply or --validate")
    plan = load(PLAN_PATH)

    if args.apply:
        result = apply(plan)
        print(json.dumps(result, indent=2))
    elif args.check:
        print(json.dumps(simulate(plan), indent=2))

    if args.validate:
        validate_repository()
        print("BA validation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
