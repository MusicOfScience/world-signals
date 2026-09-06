#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.analytical_overlays import validate_biosecurity_overlay
from world_signals.analysis import validate_analysis
from world_signals.analysis_revision import (
    production_analysis_revision_count,
    validate_analysis_revisions,
)
from world_signals.live_analysis_bridge import (
    production_live_input_count,
    validate_live_analysis_bridge,
)
from world_signals.live_intelligence import validate_live_intelligence
from world_signals.validation import validate_registry

PLAN_PATH = ROOT / "data/coverage/BARMM_PARLIAMENTARY_ELECTION_BB_PLAN_v0.1.json"
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
ANALYSIS_REVIEWS_PATH = ROOT / "data/analysis/event_reviews.json"
ANALYSIS_EVIDENCE_PATH = ROOT / "data/analysis/evidence_registry.json"
STATUS_PATH = ROOT / "PROJECT_STATUS.md"
ROADMAP_PATH = ROOT / "ROADMAP.md"

APPLY_ENV = "WORLD_SIGNALS_BB_ALLOW_WRITE"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def transaction_time() -> str:
    return datetime.now(ZoneInfo("Australia/Melbourne")).isoformat(timespec="seconds")


def overlay_semantics(overlay: dict[str, Any]) -> dict[str, Any]:
    return {
        key: copy.deepcopy(value)
        for key, value in overlay.items()
        if key not in {"version", "canonical_checkpoint"}
    }


def exact_series_count(reviews: dict[str, Any]) -> int:
    return sum(
        1
        for review in reviews.get("reviews", [])
        for movement in (review.get("what_moved") or [])
        if movement.get("measurement_precision") == "EXACT_TIMESTAMP_SERIES"
    )


def expected_assertion_id(item: dict[str, Any]) -> str:
    material = "|".join(
        [
            item["occurrence_id"],
            item["series_id"],
            item["source_id"],
            "PRIMARY",
            item["timing"]["start_local"],
        ]
    )
    return "WSA-BB-" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def expected_change_id(item: dict[str, Any]) -> str:
    material = "|".join(
        [
            item["occurrence_id"],
            item["series_id"],
            item["source_id"],
            item["timing"]["start_local"],
            "FORWARD_OCCURRENCE_ADMISSION",
        ]
    )
    return "WSCHANGE-" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:18]


def build_source(plan_source: dict[str, Any], reference_date: str) -> dict[str, Any]:
    rights = plan_source["rights"]
    return {
        "source_id": plan_source["source_id"],
        "institution": plan_source["institution"],
        "jurisdiction": plan_source["jurisdiction"],
        "domain": plan_source["domain"],
        "endpoint_role": plan_source["endpoint_role"],
        "authoritative_url": plan_source["authoritative_url"],
        "source_type": plan_source["source_type"],
        "information_supplied": plan_source["information_supplied"],
        "future_schedule_horizon": "event-specific 2026 BARMM parliamentary-election cycle",
        "typical_advance_notice": "event-specific official materials published ahead of polling day",
        "machine_readable_available": "PDF/HTML",
        "source_timezone": plan_source["source_timezone"],
        "recommended_verification_cadence": "manual weekly until polling day; post-event lifecycle verification separately",
        "activation_status": "ACTIVE_MANUAL_PROVENANCE_ONLY",
        "parser_type": plan_source["parser_type"],
        "known_limitations": [
            "The certified-candidate PDF is used only for the election-date fact in its official header; candidate-level content is out of scope.",
            "The source supports a civil polling date but BB does not infer polling hours or a canonical clock timestamp.",
            "Public accessibility and official status do not establish unrestricted production crawler permission.",
            *rights["automation_blockers"],
        ],
        "backup_source": None,
        "notes": "COMELEC is the competent polling-date authority for this BB occurrence. OPAPRU contextual material informed significance screening but is not a second Canonical timing authority.",
        "timezone_scope": "FIXED",
        "parser_version": None,
        "runtime_health_state": "UNKNOWN_NOT_LIVE_POLLED",
        "licence_constraints": rights["licence_constraints"],
        "ingestion_permission": rights["ingestion_permission"],
        "licence_review_status": rights["licence_review_status"],
        "automated_retrieval_permission": rights["automated_retrieval_permission"],
        "redistribution_permission": rights["redistribution_permission"],
        "rights_evidence_url": rights["rights_evidence_url"],
        "rights_summary": rights["rights_summary"],
        "automation_summary": "BB authorises manual first-party factual provenance only. No stable production endpoint or automated retrieval permission is established.",
        "rights_reviewed_at": reference_date,
        "rights_review_scope": "BARMM_PARLIAMENTARY_ELECTION_BB_FACTUAL_PROVENANCE_AND_AUTOMATION_SEPARATED",
        "rights_review_note": "Operational WORLD SIGNALS source-governance classification; not a legal opinion.",
        "monitoring_readiness_status": "RIGHTS_AUDIT_REQUIRED",
        "monitoring_priority_score": 220,
        "canonical_dependency_count": 1,
        "monitoring_readiness_assessed_at": reference_date,
        "last_successful_research_verification_at": reference_date,
        "canonical_provenance_use": plan_source["canonical_provenance_use"],
        "automated_monitoring_use": plan_source["automated_monitoring_use"],
        "verification_mode": plan_source["verification_mode"],
        "monitor_endpoints": [
            {
                "endpoint_role": "official_barmm_election_material",
                "url": plan_source["authoritative_url"],
                "transport": "PDF",
                "completeness_scope": "EVENT_DATE_FACT_ONLY_CANDIDATE_CONTENT_EXCLUDED",
                "preferred_for_monitoring": False,
            }
        ],
    }


def build_occurrence(item: dict[str, Any], reference_date: str) -> dict[str, Any]:
    timing = item["timing"]
    return {
        "occurrence_id": item["occurrence_id"],
        "series_id": item["series_id"],
        "external_source_id": None,
        "canonical_name": item["canonical_name"],
        "short_calendar_title": item["short_calendar_title"],
        "category": item["category"],
        "subcategory": item["subcategory"],
        "jurisdiction": item["jurisdiction"],
        "region": item["region"],
        "institution": item["institution"],
        "event_type": item["event_type"],
        "record_class": item["record_class"],
        "certainty_status": item["certainty_status"],
        "activation_mode": item["activation_mode"],
        "lifecycle_status": item["lifecycle_status"],
        "condition_state": "NOT_REQUIRED",
        "condition_description": None,
        "trigger_source_id": None,
        "trigger_assertion_id": None,
        "triggered_at": None,
        "trigger_verification_status": "NOT_APPLICABLE",
        "timing_type": timing["timing_type"],
        "start_local": timing["start_local"],
        "end_local": timing["end_local"],
        "source_timezone": timing["source_timezone"],
        "start_utc": timing["start_utc"],
        "end_utc": timing["end_utc"],
        "date_earliest": None,
        "date_latest": None,
        "time_precision": timing["time_precision"],
        "all_day_semantics": timing["all_day_semantics"],
        "reference_period": None,
        "publication_datetime": None,
        "time_status": timing["time_status"],
        "time_basis": timing["time_basis"],
        "source_id": item["source_id"],
        "primary_source_assertion_id": item["primary_source_assertion_id"],
        "last_successful_assertion_id": item["primary_source_assertion_id"],
        "status_history": [
            {
                "as_of": reference_date,
                "certainty_status": item["certainty_status"],
                "lifecycle_status": item["lifecycle_status"],
                "condition_state": "NOT_REQUIRED",
                "change_reason": "Forward election milestone admitted after competent first-party COMELEC date verification; future lifecycle remains PLANNED.",
                "source_assertion_id": item["primary_source_assertion_id"],
                "basis": "COMELEC certified-candidate material identifies the 14 September 2026 BARMM Parliamentary Elections in its official header.",
            }
        ],
        "first_announced_at": None,
        "first_discovered_at": reference_date,
        "last_verified_at": reference_date,
        "next_verification_due": "SOURCE_SPECIFIC",
        "parent_occurrence_id": None,
        "related_occurrence_ids": [],
        "related_documents": [
            {
                "source_id": item["source_id"],
                "role": "AUTHORITATIVE_ELECTION_DATE_VERIFICATION",
                "source_locator": item["source_url"],
            }
        ],
        "intrinsic_importance": item["intrinsic_importance"],
        "expected_market_sensitivity": item["expected_market_sensitivity"],
        "geopolitical_sensitivity": item["geopolitical_sensitivity"],
        "transmission_channels": item["transmission_channels"],
        "render_policy": item["render_policy"],
        "visibility_tier": item["visibility_tier"],
        "deadline_type": None,
        "deadline_semantics": None,
        "temporal_basis": "JURISDICTIONAL_CIVIL_DATE",
        "legal_basis_source_id": None,
        "governing_instrument": None,
        "must_occur_by_date": None,
        "dependency_occurrence_ids": [],
        "dependency_external_ids": [],
        "condition_expression": None,
        "resolution_evidence_assertion_id": None,
        "contingency_if_missed": None,
        "monitor_escalation_start": None,
        "render_cluster_key": None,
        "calendar_aggregation_policy": "STANDALONE",
        "election_process_id": item["election_process_id"],
        "election_milestone_type": item["election_milestone_type"],
        "election_date_basis": item["election_date_basis"],
        "round_number": item["round_number"],
        "round_activation_status": item["round_activation_status"],
        "legal_activation_status": item["legal_activation_status"],
        "result_dependency_occurrence_id": item["result_dependency_occurrence_id"],
        "court_dependency_monitor_id": item["court_dependency_monitor_id"],
        "transition_resolution_mode": item["transition_resolution_mode"],
        "deadline_is_actual_event_time": item["deadline_is_actual_event_time"],
        "derivation_sources": [item["source_id"]],
        "observed_market_response": None,
        "population_tranche": "BARMM_PARLIAMENTARY_ELECTION_BB",
        "notes": "Polling day is stored at source-native civil-date precision only. COMELEC is the Canonical date authority; OPAPRU peace-process material supports significance screening only. No polling-hour, UTC, result, market-response or causal claim is asserted in BB.",
    }


def build_ledger_change(
    item: dict[str, Any], committed_at: str, before_version: str, after_version: str
) -> dict[str, Any]:
    timing = item["timing"]
    return {
        "change_id": item["change_id"],
        "occurrence_id": item["occurrence_id"],
        "change_type": "FORWARD_OCCURRENCE_ADMISSION",
        "old_values": {"canonical_presence": False},
        "new_values": {
            "canonical_presence": True,
            "series_id": item["series_id"],
            "source_id": item["source_id"],
            "certainty_status": item["certainty_status"],
            "lifecycle_status": item["lifecycle_status"],
            "category": item["category"],
            "subcategory": item["subcategory"],
            "event_type": item["event_type"],
            "timing_type": timing["timing_type"],
            "start_local": timing["start_local"],
            "source_timezone": timing["source_timezone"],
            "start_utc": timing["start_utc"],
            "time_precision": timing["time_precision"],
            "election_process_id": item["election_process_id"],
            "election_milestone_type": item["election_milestone_type"],
            "election_date_basis": item["election_date_basis"],
        },
        "source_assertion_id": item["primary_source_assertion_id"],
        "review_state": "APPROVED_FOR_CANONICAL_COMMIT",
        "reviewed_at": committed_at,
        "review_basis": [
            item["source_url"],
            "COMELEC is the competent electoral authority and the official document header identifies the September 14, 2026 BARMM Parliamentary Elections.",
            "The event is admitted prospectively as PLANNED; completion is not inferred from the future date or from elapsed time.",
            "The election is a civil-date milestone. BB does not infer polling hours, a midnight timestamp or start_utc.",
            "OPAPRU material informed significance screening but is not promoted into a second Canonical timing authority.",
            "Candidate-level content is not ingested or republished; source automation remains held pending a separate rights/endpoint review.",
        ],
        "commit_mode": "REVIEWED_BARMM_PARLIAMENTARY_ELECTION_BB",
        "committed_at": committed_at,
        "registry_version_before": before_version,
        "registry_version_after": after_version,
        "canonical_mutation_committed": True,
    }


def target_status(current: str, plan: dict[str, Any]) -> str:
    old_header = "# CURRENT RECOVERY OVERRIDE — POST-AZ / BA ANALYSIS REVISION FOUNDATION"
    new_header = "# CURRENT RECOVERY OVERRIDE — POST-BA / BB BARMM CANONICAL COVERAGE REPAIR"
    require(old_header in current or new_header in current, "BB status header drift")
    text = current.replace(old_header, new_header, 1)
    text = text.replace(
        "**Exact post-#78 main base:** `721206169033eb0ceb695075d44fb38e7fa2edc3`",
        f"**Exact post-BA main base:** `{plan['exact_base_main_sha']}`",
        1,
    )
    replacements = {
        "- Canonical Registry: **v0.38 / 688 occurrences**": "- Canonical Registry: **v0.39 / 689 occurrences**",
        "- Source Registry: **v1.80 / 243 sources**": "- Source Registry: **v1.81 / 244 sources**",
        "- reviewed Change Ledger: **v0.24 / 59 entries**": "- reviewed Change Ledger: **v0.25 / 60 entries**",
        "- biosecurity overlay: **v0.13 @ canonical v0.38 / 688**": "- biosecurity overlay: **v0.14 @ canonical v0.39 / 689**",
    }
    for old, new in replacements.items():
        if old in text:
            text = text.replace(old, new, 1)
        else:
            require(new in text, f"BB status count line missing: {old}")

    marker = "## Current architecture decision\n\n"
    paragraph = (
        "BB repairs an upstream Southeast Asian election-coverage omission before any further Live or Analysis population: "
        "one manually governed COMELEC source and the confirmed **14 September 2026 BARMM parliamentary-election polling day** "
        "are admitted to Source Registry / Canonical / Change Ledger. The occurrence remains `PLANNED`, uses `CIVIL_DATE` / day "
        "precision in `Asia/Manila`, and carries no fabricated UTC timestamp, outcome or market response. OPAPRU peace-process "
        "material informed significance screening but is not a second Canonical timing authority. Source automation remains held.\n\n"
    )
    if paragraph not in text:
        require(marker in text, "BB status architecture marker missing")
        text = text.replace(marker, marker + paragraph, 1)

    old_next = (
        "After BA, another pressure audit must decide whether the first real Analysis revision, a fifth Live observation, or a second "
        "production Live→Analysis relationship creates the highest marginal contract pressure. None is a population quota."
    )
    new_next = (
        "After BB, a fresh pressure audit must decide whether the now-anchored BARMM transition warrants downstream Live/Analysis work, "
        "whether another Live class creates greater contract pressure, or whether a genuinely evidence-driven first Analysis revision has emerged. "
        "No downstream population is pre-authorised by this coverage repair."
    )
    if old_next in text:
        text = text.replace(old_next, new_next, 1)
    elif new_next not in text:
        require(False, "BB status next-pressure paragraph drift")
    return text


def target_roadmap(current: str) -> str:
    heading = "### BB — BARMM election source + Canonical coverage repair — DONE / BOUNDED"
    if heading in current:
        return current
    marker = "## Stage 2 — heterogeneous Source / Change Monitor, review-only — DONE / EXPANDING CAUTIOUSLY"
    require(marker in current, "BB roadmap Stage 2 marker missing")
    section = """### BB — BARMM election source + Canonical coverage repair — DONE / BOUNDED

BB corrects a documented upstream omission before any further Live/Analysis expansion: the 14 September 2026 BARMM parliamentary-election polling day is admitted from competent COMELEC evidence together with one manually governed source record and one reviewed Change Ledger admission. The occurrence remains a planned civil-date `ELECTION_MILESTONE`; no polling clock time, UTC timestamp, result or market response is invented. COMELEC automation remains on rights/endpoint hold, and OPAPRU context is not promoted into a second timing authority.

"""
    return current.replace(marker, section + marker, 1)


def assert_preconditions(plan: dict[str, Any]) -> None:
    p = plan["preconditions"]
    canonical = load(CANONICAL_PATH)
    schema = load(CANONICAL_SCHEMA_PATH)
    sources = load(SOURCES_PATH)
    ledger = load(LEDGER_PATH)
    overlay = load(OVERLAY_PATH)
    expectations = load(EXPECTATIONS_PATH)
    live_schema = load(LIVE_SCHEMA_PATH)
    live_observations = load(LIVE_OBSERVATIONS_PATH)
    live_evidence = load(LIVE_EVIDENCE_PATH)
    analysis_schema = load(ANALYSIS_SCHEMA_PATH)
    reviews = load(ANALYSIS_REVIEWS_PATH)
    analysis_evidence = load(ANALYSIS_EVIDENCE_PATH)

    require(schema.get("version") == p["canonical_schema_version"], "BB Canonical schema version drift")
    require(canonical.get("version") == p["canonical_registry_version"], "BB Canonical version drift")
    require(canonical.get("record_count") == p["canonical_record_count"] == len(canonical.get("records", [])), "BB Canonical count drift")
    require(sources.get("version") == p["source_registry_version"], "BB Source version drift")
    require(len(sources.get("sources", [])) == p["source_record_count"], "BB Source count drift")
    require(ledger.get("version") == p["change_ledger_version"], "BB Change Ledger version drift")
    require(len(ledger.get("changes", [])) == p["change_ledger_count"], "BB Change Ledger count drift")
    require(overlay.get("version") == p["biosecurity_overlay_version"], "BB overlay version drift")
    require(overlay.get("canonical_checkpoint") == p["biosecurity_overlay_checkpoint"], "BB overlay checkpoint drift")
    require(expectations.get("version") == p["monitor_expectations_version"], "BB monitor expectations version drift")
    require(len(expectations.get("adapters", [])) == p["monitor_adapter_count"], "BB monitor adapter count drift")
    require(live_schema.get("version") == p["live_schema_version"], "BB Live schema drift")
    require(live_observations.get("version") == p["live_schema_version"], "BB Live observations version drift")
    require(live_evidence.get("version") == p["live_schema_version"], "BB Live evidence version drift")
    require(len(live_observations.get("observations", [])) == p["live_observation_count"], "BB Live observation count drift")
    require(len(live_evidence.get("evidence", [])) == p["live_evidence_count"], "BB Live evidence count drift")
    require(analysis_schema.get("version") == p["analysis_schema_version"], "BB Analysis schema drift")
    require(reviews.get("version") == p["analysis_reviews_version"], "BB Analysis reviews version drift")
    require(analysis_evidence.get("version") == p["analysis_reviews_version"], "BB Analysis evidence version drift")
    require(len(reviews.get("reviews", [])) == p["analysis_review_count"], "BB Analysis review count drift")
    require(len(analysis_evidence.get("evidence", [])) == p["analysis_evidence_count"], "BB Analysis evidence count drift")
    require(production_live_input_count(reviews) == p["production_live_input_count"], "BB production live-input drift")
    require(production_analysis_revision_count(reviews) == p["production_analysis_revision_count"], "BB Analysis revision count drift")
    require(exact_series_count(reviews) == p["production_exact_timestamp_series_count"], "BB exact-series count drift")

    occurrence_ids = {row.get("occurrence_id") for row in canonical.get("records", [])}
    series_ids = {row.get("series_id") for row in canonical.get("records", [])}
    source_ids = {row.get("source_id") for row in sources.get("sources", [])}
    change_ids = {row.get("change_id") for row in ledger.get("changes", [])}
    require(not occurrence_ids.intersection(p["required_absent_occurrence_ids"]), "BB occurrence identity collision")
    require(not series_ids.intersection(p["required_absent_series_ids"]), "BB series identity collision")
    require(not source_ids.intersection(p["required_absent_source_ids"]), "BB source identity collision")
    require(not change_ids.intersection(p["required_absent_change_ids"]), "BB change identity collision")

    item = plan["occurrence"]
    source = plan["source"]
    require(item["primary_source_assertion_id"] == expected_assertion_id(item), "BB source assertion identity drift")
    require(item["change_id"] == expected_change_id(item), "BB change identity drift")
    require(item["source_id"] == source["source_id"], "BB source/occurrence identity mismatch")
    require(item["timing"]["timing_type"] == "CIVIL_DATE", "BB must remain CIVIL_DATE")
    require(item["timing"]["start_local"] == "2026-09-14", "BB polling date drift")
    require(item["timing"]["source_timezone"] == "Asia/Manila", "BB source timezone drift")
    require(item["timing"]["start_utc"] is None and item["timing"]["end_utc"] is None, "BB must not fabricate UTC")
    require(item["lifecycle_status"] == "PLANNED", "BB future election must remain PLANNED")
    require(item["election_milestone_type"] == "POLL_GENERAL", "BB election milestone drift")
    require(item["election_date_basis"] == "EXPLICIT_ELECTORAL_AUTHORITY_SCHEDULE", "BB election date-basis drift")
    require(item["visibility_tier"] == "ESSENTIAL" and item["render_policy"] == "INCLUDE", "BB render contract drift")
    require(source["canonical_provenance_use"] == "MANUAL_INFORMATIONAL_REFERENCE_ONLY", "BB provenance-use drift")
    require(source["automated_monitoring_use"] == "PROHIBITED_OR_RIGHTS_HOLD", "BB automation-use drift")
    require(source["verification_mode"] == "RIGHTS_HELD_MANUAL_ONLY", "BB verification-mode drift")

    registry_report = validate_registry(canonical, sources)
    require(registry_report.ok, "BB prestate Canonical validation failed: " + "; ".join(registry_report.errors))
    overlay_errors = validate_biosecurity_overlay(canonical, overlay)
    require(not overlay_errors, "BB prestate overlay validation failed: " + "; ".join(overlay_errors))
    live_report = validate_live_intelligence(live_schema, live_evidence, live_observations, canonical)
    require(live_report.ok, "BB prestate Live validation failed: " + "; ".join(live_report.errors))
    analysis_report = validate_analysis(analysis_schema, analysis_evidence, reviews, canonical)
    require(analysis_report.ok, "BB prestate Analysis validation failed: " + "; ".join(analysis_report.errors))
    revision_report = validate_analysis_revisions(analysis_schema, reviews)
    require(revision_report.ok, "BB prestate Analysis revision validation failed: " + "; ".join(revision_report.errors))
    bridge_report = validate_live_analysis_bridge(analysis_schema, reviews, live_observations)
    require(bridge_report.ok, "BB prestate Live→Analysis validation failed: " + "; ".join(bridge_report.errors))


def simulate(plan: dict[str, Any], committed_at: str = "2026-09-06T21:30:00+10:00") -> dict[str, Any]:
    assert_preconditions(plan)
    p = plan["preconditions"]
    post = plan["postconditions"]
    reference_date = plan["reference_date"]

    canonical = load(CANONICAL_PATH)
    sources = load(SOURCES_PATH)
    ledger = load(LEDGER_PATH)
    overlay = load(OVERLAY_PATH)

    target_canonical = copy.deepcopy(canonical)
    target_canonical["version"] = post["canonical_registry_version"]
    target_canonical["reference_date"] = reference_date
    target_canonical["records"].append(build_occurrence(plan["occurrence"], reference_date))
    target_canonical["record_count"] = len(target_canonical["records"])

    target_sources = copy.deepcopy(sources)
    target_sources["version"] = post["source_registry_version"]
    target_sources["reference_date"] = reference_date
    target_sources["sources"].append(build_source(plan["source"], reference_date))

    target_ledger = copy.deepcopy(ledger)
    target_ledger["version"] = post["change_ledger_version"]
    target_ledger["reference_date"] = reference_date
    target_ledger["changes"].append(
        build_ledger_change(
            plan["occurrence"],
            committed_at,
            p["canonical_registry_version"],
            post["canonical_registry_version"],
        )
    )

    target_overlay = copy.deepcopy(overlay)
    before_overlay_semantics = overlay_semantics(overlay)
    target_overlay["version"] = post["biosecurity_overlay_version"]
    target_overlay["canonical_checkpoint"] = copy.deepcopy(post["biosecurity_overlay_checkpoint"])
    require(overlay_semantics(target_overlay) == before_overlay_semantics, "BB overlay semantic mutation detected")

    target = {
        "canonical": target_canonical,
        "sources": target_sources,
        "ledger": target_ledger,
        "overlay": target_overlay,
        "status": target_status(STATUS_PATH.read_text(encoding="utf-8"), plan),
        "roadmap": target_roadmap(ROADMAP_PATH.read_text(encoding="utf-8")),
    }
    assert_target(plan, target)
    return target


def assert_target(plan: dict[str, Any], target: dict[str, Any]) -> None:
    post = plan["postconditions"]
    canonical_before = load(CANONICAL_PATH)
    sources_before = load(SOURCES_PATH)
    ledger_before = load(LEDGER_PATH)
    overlay_before = load(OVERLAY_PATH)

    canonical = target["canonical"]
    sources = target["sources"]
    ledger = target["ledger"]
    overlay = target["overlay"]

    require(canonical["version"] == post["canonical_registry_version"], "BB target Canonical version mismatch")
    require(canonical["record_count"] == post["canonical_record_count"] == len(canonical["records"]), "BB target Canonical count mismatch")
    require(sources["version"] == post["source_registry_version"], "BB target Source version mismatch")
    require(len(sources["sources"]) == post["source_record_count"], "BB target Source count mismatch")
    require(ledger["version"] == post["change_ledger_version"], "BB target Change Ledger version mismatch")
    require(len(ledger["changes"]) == post["change_ledger_count"], "BB target Change Ledger count mismatch")
    require(overlay["version"] == post["biosecurity_overlay_version"], "BB target overlay version mismatch")
    require(overlay["canonical_checkpoint"] == post["biosecurity_overlay_checkpoint"], "BB target overlay checkpoint mismatch")

    require(canonical["records"][: len(canonical_before["records"])] == canonical_before["records"], "BB changed pre-existing Canonical rows")
    require(sources["sources"][: len(sources_before["sources"])] == sources_before["sources"], "BB changed pre-existing Source rows")
    require(ledger["changes"][: len(ledger_before["changes"])] == ledger_before["changes"], "BB changed pre-existing Change Ledger rows")
    require(overlay_semantics(overlay) == overlay_semantics(overlay_before), "BB changed biosecurity overlay semantics")

    new_occurrence = canonical["records"][-1]
    new_source = sources["sources"][-1]
    new_change = ledger["changes"][-1]
    item = plan["occurrence"]
    require(new_occurrence["occurrence_id"] == item["occurrence_id"], "BB target occurrence identity mismatch")
    require(new_source["source_id"] == plan["source"]["source_id"], "BB target source identity mismatch")
    require(new_change["change_id"] == item["change_id"], "BB target change identity mismatch")
    require(new_change["change_type"] == "FORWARD_OCCURRENCE_ADMISSION", "BB target change type mismatch")
    require(new_occurrence["lifecycle_status"] == "PLANNED", "BB target future lifecycle mismatch")
    require(new_occurrence["start_utc"] is None and new_occurrence["end_utc"] is None, "BB target fabricated UTC")
    require(new_occurrence["time_precision"] == "DAY" and new_occurrence["all_day_semantics"] is True, "BB target civil-date precision mismatch")
    require(new_occurrence["election_process_id"] == "WSEP-PH-BARMM-2026", "BB election process identity mismatch")
    require(new_occurrence["election_milestone_type"] == "POLL_GENERAL", "BB target election milestone mismatch")
    require("publication_bundle_type" not in new_occurrence, "BB election must not inherit publication-release semantics")
    require(new_source["canonical_dependency_count"] == 1, "BB source dependency helper mismatch")
    require(new_source["automated_monitoring_use"] == "PROHIBITED_OR_RIGHTS_HOLD", "BB target automation gate opened")
    require(new_source["monitor_endpoints"][0]["preferred_for_monitoring"] is False, "BB target source unexpectedly preferred for monitoring")

    registry_report = validate_registry(canonical, sources)
    require(registry_report.ok, "BB target Canonical validation failed: " + "; ".join(registry_report.errors))
    overlay_errors = validate_biosecurity_overlay(canonical, overlay)
    require(not overlay_errors, "BB target overlay validation failed: " + "; ".join(overlay_errors))

    live_schema = load(LIVE_SCHEMA_PATH)
    live_observations = load(LIVE_OBSERVATIONS_PATH)
    live_evidence = load(LIVE_EVIDENCE_PATH)
    analysis_schema = load(ANALYSIS_SCHEMA_PATH)
    reviews = load(ANALYSIS_REVIEWS_PATH)
    analysis_evidence = load(ANALYSIS_EVIDENCE_PATH)

    live_report = validate_live_intelligence(live_schema, live_evidence, live_observations, canonical)
    require(live_report.ok, "BB target Live validation failed: " + "; ".join(live_report.errors))
    analysis_report = validate_analysis(analysis_schema, analysis_evidence, reviews, canonical)
    require(analysis_report.ok, "BB target Analysis validation failed: " + "; ".join(analysis_report.errors))
    revision_report = validate_analysis_revisions(analysis_schema, reviews)
    require(revision_report.ok, "BB target Analysis revision validation failed: " + "; ".join(revision_report.errors))
    bridge_report = validate_live_analysis_bridge(analysis_schema, reviews, live_observations)
    require(bridge_report.ok, "BB target Live→Analysis validation failed: " + "; ".join(bridge_report.errors))

    require(len(live_observations.get("observations", [])) == post["live_observation_count"], "BB target changed Live population")
    require(len(live_evidence.get("evidence", [])) == post["live_evidence_count"], "BB target changed Live evidence")
    require(len(reviews.get("reviews", [])) == post["analysis_review_count"], "BB target changed Analysis reviews")
    require(len(analysis_evidence.get("evidence", [])) == post["analysis_evidence_count"], "BB target changed Analysis evidence")
    require(production_live_input_count(reviews) == post["production_live_input_count"], "BB target changed production live-input count")
    require(production_analysis_revision_count(reviews) == post["production_analysis_revision_count"], "BB target changed Analysis revisions")
    require(exact_series_count(reviews) == post["production_exact_timestamp_series_count"], "BB target changed exact-series population")

    require("Canonical Registry: **v0.39 / 689 occurrences**" in target["status"], "BB status target count missing")
    require("BB repairs an upstream Southeast Asian election-coverage omission" in target["status"], "BB status target decision missing")
    require("BB — BARMM election source + Canonical coverage repair" in target["roadmap"], "BB roadmap target missing")


def write_target(target: dict[str, Any]) -> None:
    CANONICAL_PATH.write_text(dump(target["canonical"]), encoding="utf-8")
    SOURCES_PATH.write_text(dump(target["sources"]), encoding="utf-8")
    LEDGER_PATH.write_text(dump(target["ledger"]), encoding="utf-8")
    OVERLAY_PATH.write_text(dump(target["overlay"]), encoding="utf-8")
    STATUS_PATH.write_text(target["status"], encoding="utf-8")
    ROADMAP_PATH.write_text(target["roadmap"], encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-only", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    plan = load(PLAN_PATH)
    target = simulate(plan, transaction_time())
    if args.check_only:
        print("BB read-only simulation: PASS")
        return

    require(os.environ.get(APPLY_ENV) == "1", f"BB apply requires {APPLY_ENV}=1")
    write_target(target)
    print("BB BARMM source + Canonical coverage repair materialised: PASS")


if __name__ == "__main__":
    main()
