#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

from src.world_signals.analytical_overlays import validate_biosecurity_overlay
from src.world_signals.validation import validate_registry

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data/canonical/registry.json"
SOURCE_PATH = ROOT / "data/sources/registry.json"
OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
PLAN_PATH = ROOT / "data/coverage/MIXED_SIGNAL_CORRECTION_M_PLAN_v0.1.json"
AUDIT_PATH = ROOT / "data/coverage/MIXED_SIGNAL_CORRECTION_M_TRANSACTION_AUDIT_v0.1.md"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"

APPLY_ENV = "WORLD_SIGNALS_APPLY_MIXED_SIGNAL_M"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assertion_id(item: dict) -> str:
    material = "|".join(
        str(item.get(key) or "")
        for key in (
            "occurrence_id",
            "series_id",
            "source_id",
            "canonical_name",
            "start_local",
            "end_local",
        )
    )
    return "WSA-" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def preflight(registry: dict, sources: dict, overlay: dict, plan: dict) -> None:
    p = plan["preconditions"]
    errors: list[str] = []

    if str(registry.get("version")) != p["canonical_registry_version"]:
        errors.append(f"canonical version {registry.get('version')} != {p['canonical_registry_version']}")
    if registry.get("record_count") != p["canonical_record_count"] or len(registry.get("records", [])) != p["canonical_record_count"]:
        errors.append("canonical record-count precondition failed")
    if str(sources.get("version")) != p["source_registry_version"]:
        errors.append(f"source version {sources.get('version')} != {p['source_registry_version']}")
    if len(sources.get("sources", [])) != p["source_record_count"]:
        errors.append("source record-count precondition failed")
    if str(overlay.get("version")) != p["biosecurity_overlay_version"]:
        errors.append(f"overlay version {overlay.get('version')} != {p['biosecurity_overlay_version']}")
    if overlay.get("canonical_checkpoint") != {
        "registry_version": p["canonical_registry_version"],
        "record_count": p["canonical_record_count"],
    }:
        errors.append("overlay canonical checkpoint does not match pre-state")

    existing_oids = {row.get("occurrence_id") for row in registry.get("records", [])}
    existing_series = {row.get("series_id") for row in registry.get("records", [])}
    existing_source_ids = {row.get("source_id") for row in sources.get("sources", [])}
    canonical_institutions = {str(row.get("institution") or "").casefold() for row in registry.get("records", [])}
    source_institutions = {str(row.get("institution") or "").casefold() for row in sources.get("sources", [])}

    for oid in p["required_absent_occurrence_ids"]:
        if oid in existing_oids:
            errors.append(f"occurrence identity collision: {oid}")
    for series_id in p["required_absent_series_ids"]:
        if series_id in existing_series:
            errors.append(f"series identity collision: {series_id}")
    for source_id in p["required_absent_source_ids"]:
        if source_id in existing_source_ids:
            errors.append(f"source identity collision: {source_id}")

    for source in plan["source_plan"]:
        folded = source["institution"].casefold()
        if folded in canonical_institutions or folded in source_institutions:
            errors.append(f"institution already present; reconcile identity before population: {source['institution']}")

    if [row["occurrence_id"] for row in plan["occurrences"]] != p["required_absent_occurrence_ids"]:
        errors.append("planned occurrence sequence differs from frozen precondition")
    if [row["source_id"] for row in plan["source_plan"]] != p["required_absent_source_ids"]:
        errors.append("planned source sequence differs from frozen precondition")
    if [row["series_id"] for row in plan["series"]] != p["required_absent_series_ids"]:
        errors.append("planned series sequence differs from frozen precondition")

    series_map = {row["series_id"]: row for row in plan["series"]}
    for item in plan["occurrences"]:
        series = series_map.get(item["series_id"])
        if not series:
            errors.append(f"missing frozen series metadata for {item['occurrence_id']}")
            continue
        if item["source_id"] != series["source_id"]:
            errors.append(f"series/source mismatch for {item['occurrence_id']}")
        if item["end_local"] < item["start_local"]:
            errors.append(f"negative date range for {item['occurrence_id']}")

    candidates = {row.get("candidate_node_id") for row in overlay.get("candidate_nodes", [])}
    for required in ("BIO-CAND-BWC", "BIO-CAND-WOAH"):
        if required not in candidates:
            errors.append(f"overlay graduation candidate missing at pre-state: {required}")

    if errors:
        raise SystemExit("PRECONDITION FAILED:\n- " + "\n- ".join(errors))


def build_source(source: dict) -> dict:
    common = {
        "source_id": source["source_id"],
        "institution": source["institution"],
        "jurisdiction": source["jurisdiction"],
        "domain": source["domain"],
        "authoritative_url": source["authoritative_url"],
        "source_type": source["source_type"],
        "rights_evidence_url": source["rights_evidence_url"],
        "recommended_verification_cadence": "manual weekly; daily inside 14 days of next occurrence",
        "activation_status": "ACTIVE_MANUAL_PROVENANCE_ONLY",
        "parser_version": None,
        "runtime_health_state": "UNKNOWN_NOT_LIVE_POLLED",
        "backup_source": None,
        "timezone_scope": "FIXED",
        "rights_reviewed_at": "2026-09-05",
        "rights_review_scope": "MIXED_SIGNAL_CORRECTION_M_PROVENANCE_AND_AUTOMATION_SEPARATED",
        "rights_review_note": "Operational governance classification for WORLD SIGNALS; not a legal opinion.",
        "monitoring_readiness_assessed_at": "2026-09-05",
        "last_successful_research_verification_at": "2026-09-05",
        "canonical_provenance_use": source["canonical_provenance_use"],
        "automated_monitoring_use": source["automated_monitoring_use"],
        "verification_mode": source["verification_mode"],
    }

    if source["source_id"] == "WSSRC-CB-012":
        specific = {
            "endpoint_role": "2026 Monetary Policy Committee meeting calendar",
            "information_supplied": "MPC meeting numbers and Day 1 / Day 2 civil dates for 2026",
            "future_schedule_horizon": "through November 2026 verified",
            "typical_advance_notice": "annual calendar",
            "machine_readable_available": "HTML",
            "source_timezone": "Africa/Lagos",
            "parser_type": "MANUAL_HTML_PROVENANCE",
            "known_limitations": [
                "The calendar gives meeting-day windows but no forward decision publication clock time.",
                "Historical day-specific meeting notices do not create a standard-time rule for future meetings.",
            ],
            "notes": "Curated factual provenance with attribution; production endpoint review remains separate.",
            "licence_constraints": "SOURCE_ATTRIBUTION_AND_NO_DISTORTION",
            "ingestion_permission": "CURATED_FACTUAL_METADATA_ALLOWED_WITH_ATTRIBUTION",
            "licence_review_status": "CLEARED_REUSE_WITH_ATTRIBUTION_ACCURACY",
            "automated_retrieval_permission": "PENDING_ENDPOINT_OPERATIONAL_REVIEW",
            "redistribution_permission": "FACTUAL_METADATA_ALLOWED_WITH_SOURCE_CITATION_NO_DISTORTION",
            "rights_summary": "CBN permits electronic or paper copying when CBN is expressly stated as source and material is not amended or distorted.",
            "automation_summary": "Reuse permission is not treated as unrestricted automated website retrieval; endpoint review is still required.",
            "monitoring_readiness_status": "ENDPOINT_REVIEW_REQUIRED",
            "monitoring_priority_score": 620,
            "canonical_dependency_count": 2,
        }
    elif source["source_id"] == "WSSRC-INT-032":
        specific = {
            "endpoint_role": "BWC Working Group tenth-session official meeting page",
            "information_supplied": "7-11 December 2026 date range, Geneva venue and daily split session hours",
            "future_schedule_horizon": "explicit December 2026 session",
            "typical_advance_notice": "months",
            "machine_readable_available": "HTML",
            "source_timezone": "Europe/Zurich",
            "parser_type": "MANUAL_HTML_PROVENANCE",
            "known_limitations": [
                "UN general web terms limit ordinary copying to personal non-commercial use and do not grant redistribution/compilation rights.",
                "Daily 10:00-13:00 and 15:00-18:00 sessions are programme detail, not one continuous canonical timestamp.",
            ],
            "notes": "Manual authoritative factual reference only; no production crawler dependency.",
            "licence_constraints": "GENERAL_UN_WEB_TERMS_PERSONAL_NONCOMMERCIAL_ONLY",
            "ingestion_permission": "CURATED_FACTUAL_METADATA_MANUAL_ONLY_RIGHTS_HOLD",
            "licence_review_status": "RIGHTS_HELD_GENERAL_UN_WEB_TERMS",
            "automated_retrieval_permission": "PRODUCTION_AUTOMATION_HOLD",
            "redistribution_permission": "NO_REDISTRIBUTION_OR_COMPILATION_RIGHT_INFERRED",
            "rights_summary": "UN website terms permit personal non-commercial download/copy but not resale, redistribution, compilation or derivative works.",
            "automation_summary": "Production automated retrieval remains held under the reviewed general UN terms.",
            "monitoring_readiness_status": "RIGHTS_OR_LICENSE_HOLD",
            "monitoring_priority_score": 180,
            "canonical_dependency_count": 1,
        }
    elif source["source_id"] == "WSSRC-INT-033":
        specific = {
            "endpoint_role": "93rd General Session final report / 94th General Session dates",
            "information_supplied": "24-28 May 2027 date range and CNIT Forest, Paris venue for the 94th General Session",
            "future_schedule_horizon": "explicit May 2027 session",
            "typical_advance_notice": "approximately one year",
            "machine_readable_available": "PDF",
            "source_timezone": "Europe/Paris",
            "parser_type": "MANUAL_PDF_PROVENANCE",
            "known_limitations": [
                "The authoritative forward date is embedded in the prior General Session final report.",
                "No less restrictive licence specific to this final report was established in this pass.",
                "Reviewed WOAH terms prohibit data-mining/robots on the reviewed WOAH web surface; production automation is therefore held.",
            ],
            "notes": "Manual factual provenance only. Animal-health standards governance is primary; One Health remains an analytical cross-domain relationship.",
            "licence_constraints": "WOAH_RIGHTS_REVIEW_HOLD_AND_AUTOMATED_EXTRACTION_RESTRICTION",
            "ingestion_permission": "CURATED_FACTUAL_METADATA_MANUAL_ONLY_RIGHTS_HOLD",
            "licence_review_status": "RIGHTS_HOLD_NO_REPORT_SPECIFIC_OPEN_LICENCE_ESTABLISHED",
            "automated_retrieval_permission": "PRODUCTION_AUTOMATION_HOLD",
            "redistribution_permission": "FACTUAL_REFERENCE_ONLY_NO_CONTENT_REPRODUCTION_RIGHT_INFERRED",
            "rights_summary": "Reviewed WOAH terms restrict commercial reuse and data-mining/robots; no more permissive licence for the General Session final report was established.",
            "automation_summary": "Production automated retrieval remains held; only manually checked factual metadata is used.",
            "monitoring_readiness_status": "RIGHTS_OR_LICENSE_HOLD",
            "monitoring_priority_score": 220,
            "canonical_dependency_count": 1,
        }
    else:
        raise SystemExit(f"unknown Correction M source: {source['source_id']}")

    return common | specific


def build_occurrence(item: dict, series: dict) -> dict:
    aid = assertion_id(item)
    if item["series_id"] == "WSER-CB-NG-CBN-MPC":
        transmission = [
            "monetary_policy", "inflation", "currencies", "sovereign_bonds",
            "equities", "credit", "trade", "investment",
        ]
        notes = (
            "CBN's official 2026 calendar publishes this as a two-day MPC meeting. "
            "No decision publication day or clock time is inferred from historical practice."
        )
        selection = "Adds a systemically material African monetary-policy process using exact first-party meeting-window evidence."
    elif item["series_id"] == "WSER-INT-BWC-WG-STRENGTHENING":
        transmission = [
            "geopolitical_security", "arms_control", "biosecurity", "dual_use_technology",
            "international_law", "health_security",
        ]
        notes = (
            "UNODA publishes daily programme sessions at 10:00-13:00 and 15:00-18:00. "
            "The canonical occurrence preserves the five-day meeting range and does not render those split hours as a continuous timestamp."
        )
        selection = "Adds missing biological-security arms-control governance without misclassifying it as human-health governance."
    else:
        transmission = [
            "animal_health", "zoonotic_risk", "food_security", "agricultural_trade",
            "veterinary_standards", "antimicrobial_resistance", "livestock",
        ]
        notes = (
            "WOAH's 93rd General Session final report states that the 94th General Session "
            "will take place 24-28 May 2027 at CNIT Forest in Paris. "
            "One Health is represented analytically, not as the primary canonical category."
        )
        selection = "Adds global animal-health standards governance with direct food-security, trade and zoonotic-risk relevance."

    return {
        "occurrence_id": item["occurrence_id"],
        "series_id": item["series_id"],
        "external_source_id": None,
        "canonical_name": item["canonical_name"],
        "short_calendar_title": item["short_calendar_title"],
        "category": series["category"],
        "subcategory": series["subcategory"],
        "jurisdiction": series["jurisdiction"],
        "region": series["region"],
        "institution": series["institution"],
        "event_type": series["event_type"],
        "record_class": "OCCURRENCE",
        "certainty_status": "CONFIRMED",
        "activation_mode": "EXPLICITLY_SCHEDULED",
        "lifecycle_status": "PLANNED",
        "condition_state": "NOT_REQUIRED",
        "condition_description": None,
        "trigger_source_id": None,
        "trigger_assertion_id": None,
        "triggered_at": None,
        "trigger_verification_status": "NOT_APPLICABLE",
        "timing_type": series["timing_type"],
        "start_local": item["start_local"],
        "end_local": item["end_local"],
        "source_timezone": series["source_timezone"],
        "start_utc": None,
        "end_utc": None,
        "date_earliest": None,
        "date_latest": None,
        "time_precision": "DAY_RANGE",
        "time_status": "CONFIRMED",
        "time_basis": "EXPLICIT_AUTHORITATIVE_SCHEDULE",
        "all_day_semantics": True,
        "reference_period": None,
        "publication_datetime": None,
        "location": item["location"],
        "source_id": item["source_id"],
        "primary_source_assertion_id": aid,
        "last_successful_assertion_id": aid,
        "status_history": [
            {
                "as_of": "2026-09-05",
                "certainty_status": "CONFIRMED",
                "lifecycle_status": "PLANNED",
                "basis": "Authoritative first-order schedule/date statement verified in Correction M research pass.",
            }
        ],
        "first_announced_at": None,
        "first_discovered_at": "2026-09-05",
        "last_verified_at": "2026-09-05",
        "next_verification_due": "SOURCE_SPECIFIC",
        "parent_occurrence_id": None,
        "related_occurrence_ids": [],
        "related_documents": [],
        "intrinsic_importance": item["intrinsic_importance"],
        "expected_market_sensitivity": item["expected_market_sensitivity"],
        "geopolitical_sensitivity": item["geopolitical_sensitivity"],
        "transmission_channels": transmission,
        "render_policy": "INCLUDE",
        "visibility_tier": "ESSENTIAL",
        "deadline_is_actual_event_time": False,
        "derivation_sources": [],
        "coverage_program_id": "WSCP-MIXED-SIGNAL-CORRECTION-M",
        "coverage_repair_reason": "MISSING_SYSTEMIC_SIGNAL_FAMILY",
        "population_horizon_policy": "BOUNDED_RESEARCHED_OCCURRENCES_ONLY",
        "selection_rationale": selection,
        "notes": notes,
    }


def migrate_overlay(overlay: dict, registry_post: dict) -> dict:
    out = copy.deepcopy(overlay)
    out["version"] = "0.2"
    out["canonical_checkpoint"] = {
        "registry_version": registry_post["version"],
        "record_count": len(registry_post["records"]),
    }

    additions = [
        {
            "series_id": "WSER-INT-BWC-WG-STRENGTHENING",
            "system_ids": ["BIO-BIOLOGICAL-SECURITY-ARMS-CONTROL"],
            "canonical_primary_category": "INTERNATIONAL_INSTITUTIONS",
            "canonical_institution": "Biological Weapons Convention / UNODA",
            "basis": "Correction M canonical admission of the BWC strengthening Working Group in its natural arms-control/international-institutions category.",
        },
        {
            "series_id": "WSER-AGF-WOAH-GENERAL-SESSION",
            "system_ids": ["BIO-ANIMAL-ZOONOTIC-HEALTH"],
            "canonical_primary_category": "AGRICULTURE_FOOD",
            "canonical_institution": "World Organisation for Animal Health",
            "basis": "Correction M canonical admission of the WOAH World Assembly General Session in its natural animal-health/agriculture-food category.",
        },
    ]
    out["canonical_series_memberships"] = list(out.get("canonical_series_memberships", [])) + additions
    graduated = {"BIO-CAND-BWC", "BIO-CAND-WOAH"}
    out["candidate_nodes"] = [
        row for row in out.get("candidate_nodes", [])
        if row.get("candidate_node_id") not in graduated
    ]
    out["notes"] = [
        "The overlay describes cross-domain analytical relationships; it does not change canonical event categories.",
        "Canonical memberships now include the five WHO human-health series plus BWC biological-security arms-control and WOAH animal/zoonotic-health governance.",
        "BWC and WOAH were graduated from research candidates only after separate source, timing, rights and canonical-admission review in Correction M.",
        "IPPC/CPM and Africa CDC remain noncanonical research candidates and intentionally carry no series_id or occurrence_id.",
        "No event population is authorized by this dataset; Correction M population authority comes from its separately reviewed transaction plan.",
    ]
    return out


def build_post_state(registry: dict, sources: dict, overlay: dict, plan: dict):
    pre_registry = copy.deepcopy(registry)
    pre_sources = copy.deepcopy(sources)

    post_registry = copy.deepcopy(registry)
    post_sources = copy.deepcopy(sources)

    series_map = {row["series_id"]: row for row in plan["series"]}
    new_records = [build_occurrence(item, series_map[item["series_id"]]) for item in plan["occurrences"]]
    new_sources = [build_source(item) for item in plan["source_plan"]]

    post_registry["version"] = plan["postconditions"]["canonical_registry_version"]
    post_registry["reference_date"] = "2026-09-05"
    post_registry["records"].extend(new_records)
    post_registry["record_count"] = len(post_registry["records"])

    post_sources["version"] = plan["postconditions"]["source_registry_version"]
    post_sources["reference_date"] = "2026-09-05"
    post_sources["sources"].extend(new_sources)

    post_overlay = migrate_overlay(overlay, post_registry)

    if post_registry["records"][: len(pre_registry["records"])] != pre_registry["records"]:
        raise SystemExit("POSTCONDITION FAILED: pre-existing canonical records changed")
    if post_sources["sources"][: len(pre_sources["sources"])] != pre_sources["sources"]:
        raise SystemExit("POSTCONDITION FAILED: pre-existing source records changed")

    report = validate_registry(post_registry, post_sources)
    if not report.ok:
        raise SystemExit("POSTCONDITION FAILED: registry validation: " + "; ".join(report.errors))
    overlay_errors = validate_biosecurity_overlay(post_registry, post_overlay)
    if overlay_errors:
        raise SystemExit("POSTCONDITION FAILED: biosecurity overlay: " + "; ".join(overlay_errors))

    expected = plan["postconditions"]
    checks = {
        "canonical_version": post_registry["version"] == expected["canonical_registry_version"],
        "canonical_count": len(post_registry["records"]) == expected["canonical_record_count"],
        "source_version": post_sources["version"] == expected["source_registry_version"],
        "source_count": len(post_sources["sources"]) == expected["source_record_count"],
        "overlay_version": post_overlay["version"] == expected["biosecurity_overlay_version"],
        "overlay_checkpoint": post_overlay["canonical_checkpoint"] == {
            "registry_version": expected["canonical_registry_version"],
            "record_count": expected["canonical_record_count"],
        },
        "new_occurrence_count": len(new_records) == expected["new_occurrence_count"],
        "new_series_count": len({row["series_id"] for row in new_records}) == expected["new_series_count"],
        "new_source_count": len(new_sources) == expected["new_source_count"],
        "write_gate_closed": expected["automatic_canonical_commit"] is False,
        "calendar_gate_closed": expected["google_calendar_write"] is False,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise SystemExit("POSTCONDITION FAILED: " + ", ".join(failed))

    return post_registry, post_sources, post_overlay, {
        "checks": checks,
        "warnings": report.warnings,
        "new_occurrence_ids": [row["occurrence_id"] for row in new_records],
        "new_source_ids": [row["source_id"] for row in new_sources],
    }


def audit_text(report: dict, ledger_hash: str, expectations_hash: str) -> str:
    ids = "\n".join(f"- `{oid}`" for oid in report["new_occurrence_ids"])
    sources = "\n".join(f"- `{sid}`" for sid in report["new_source_ids"])
    warnings = "\n".join(f"- {warning}" for warning in report["warnings"]) if report["warnings"] else "- none"
    return f"""# WORLD SIGNALS — Mixed-signal correction M transaction audit v0.1

**Transaction date:** 2026-09-05  
**Base:** canonical v0.26 / 669; source v1.67 / 228; biosecurity overlay v0.1  
**Simulated and applied post-state:** canonical **v0.27 / 673**; source **v1.68 / 231**; biosecurity overlay **v0.2**

## Scope

Four canonical occurrences were added across three newly admitted series and three first-order authoritative sources.

### Occurrences

{ids}

### Sources

{sources}

## Invariants

- all 669 pre-existing canonical occurrence objects remained unchanged as parsed JSON objects;
- all 228 pre-existing source-registry objects remained unchanged;
- registry validation passed after in-memory simulation;
- biosecurity overlay validation passed after BWC/WOAH candidate graduation;
- BWC remains `INTERNATIONAL_INSTITUTIONS`, not human `HEALTH_BIOSECURITY`;
- WOAH remains `AGRICULTURE_FOOD`, with animal/zoonotic biosecurity represented through the analytical overlay;
- CBN meeting dates remain two-day process windows with no synthetic decision timestamp;
- IPPC CPM-21 and North Indian Ocean cyclone seasons remain held;
- automatic canonical commit remains OFF;
- Google Calendar writes remain OFF.

## Protected files

Change ledger SHA-256 before transaction: `{ledger_hash}`

Monitor expectations SHA-256 before transaction: `{expectations_hash}`

The transaction helper does not write either file. The apply workflow additionally checks its final diff boundary before commit.

## Validation warning state

Registry warnings are inherited legacy/backfill warnings only:

{warnings}

## Authority boundary

This audit records a branch transaction only. It does not authorise automatic canonical commits, production web crawling, Google Calendar writes, or any analytical causal claim.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write reviewed post-state; requires explicit environment gate")
    args = parser.parse_args()

    registry = load(REGISTRY_PATH)
    sources = load(SOURCE_PATH)
    overlay = load(OVERLAY_PATH)
    plan = load(PLAN_PATH)

    ledger_hash = file_hash(LEDGER_PATH)
    expectations_hash = file_hash(EXPECTATIONS_PATH)

    preflight(registry, sources, overlay, plan)
    post_registry, post_sources, post_overlay, report = build_post_state(registry, sources, overlay, plan)

    print(json.dumps({
        "mode": "APPLY" if args.apply else "CHECK_ONLY",
        "post": {
            "canonical_version": post_registry["version"],
            "canonical_count": len(post_registry["records"]),
            "source_version": post_sources["version"],
            "source_count": len(post_sources["sources"]),
            "overlay_version": post_overlay["version"],
        },
        "new_occurrence_ids": report["new_occurrence_ids"],
        "new_source_ids": report["new_source_ids"],
        "warnings": report["warnings"],
    }, indent=2))

    if not args.apply:
        return

    if os.environ.get(APPLY_ENV) != "YES":
        raise SystemExit(f"APPLY BLOCKED: set {APPLY_ENV}=YES")

    dump(REGISTRY_PATH, post_registry)
    dump(SOURCE_PATH, post_sources)
    dump(OVERLAY_PATH, post_overlay)
    AUDIT_PATH.write_text(audit_text(report, ledger_hash, expectations_hash), encoding="utf-8")

    if file_hash(LEDGER_PATH) != ledger_hash:
        raise SystemExit("PROTECTED FILE CHANGED: change ledger")
    if file_hash(EXPECTATIONS_PATH) != expectations_hash:
        raise SystemExit("PROTECTED FILE CHANGED: monitor expectations")

    print("APPLIED: mixed-signal correction M")


if __name__ == "__main__":
    main()
