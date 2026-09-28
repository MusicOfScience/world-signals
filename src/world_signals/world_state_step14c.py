"""Guarded Step 14C admissions.

This module contains two deliberately separate, explicit transactions:

* the historical Australian tropical-cyclone Baseline and Dimension
  components; and
* two manual-only Treasury provenance sources plus the recovered 2026 IGR
  Canonical occurrence.

Builders are deterministic and side-effect free.  Materialisation is opt-in,
preflights a temporary copy, and replaces only the files owned by that
transaction.  No Analysis, Signal, Relationship, Risk, Scenario, Forecast,
Outcome or public projection is created here.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any

from .validation import validate_registry
from .world_state_admission import load_production_state, validate_production_state
from .world_state_climate_candidate import validate_climate_candidate_package
from .world_state_history import (
    fingerprint,
    state_hashes,
    validate_admission_transaction,
    validate_component_history,
    validate_snapshot,
    validate_snapshot_history,
    with_object_fingerprint,
)


PACKAGE_RELATIVE = Path("data/world_state_audit/STEP14A_AU_TROPICAL_CYCLONE_CANDIDATE_REVIEW_PENDING.json")
SOURCE_CANDIDATE_RELATIVE = Path("data/coverage/STEP14B_AU_TREASURY_SOURCE_GOVERNANCE_CANDIDATES_v0.1.json")
IGR_CANDIDATE_RELATIVE = Path("data/coverage/STEP14B_AU_IGR_CANONICAL_RECOVERY_CANDIDATE_REVIEW_PENDING.json")
IGR_GAP_RELATIVE = Path("data/coverage/STEP14B_AU_IGR_COVERAGE_GAP_AUDIT_v0.1.json")

EXPECTED_SOURCE_MANIFEST = "672924298cedc998f243531e27e6bdb577220f357169c2959ecf26d74c02d8a7"
EXPECTED_BASELINE_FINGERPRINT = "17b586da3a8733ab1aad5051fd35e35d9b016167450b937d16292fa49cc2991c"
EXPECTED_DIMENSION_FINGERPRINT = "20dc4e2177aa5ea9284cdc962a78fe05cd8a39f71ae41b0547c34bbd35b3c9e9"
EXPECTED_PACKAGE_FINGERPRINT = "fe6a9f080037c753de5b64507789b1a70238201005ad5960a069d9aaf6a35687"

BASELINE_ID = "WSBASE-CLIMATE-AU-TC-CLIMATOLOGY-1980-81-001"
BASELINE_REVISION_ID = f"{BASELINE_ID}-R1"
DIMENSION_ID = "WSDIM-CLIMATE-AU-TCSEASON-2025-26-001"
DIMENSION_REVISION_ID = f"{DIMENSION_ID}-R1"
CLIMATE_SNAPSHOT_SERIES_ID = "WSSNAP-CLIMATE-AU-TCSEASON-2025-26"
CLIMATE_SNAPSHOT_REVISION_ID = f"{CLIMATE_SNAPSHOT_SERIES_ID}-R1"
CLIMATE_REVIEW_ID = "WS-STEP14C-AU-TC-COMPONENT-REVIEW-20260929-001"
CLIMATE_ADMISSION_ID = "WS-ADMISSION-CLIMATE-AU-TCSEASON-20260929-001"

TREASURY_SOURCE_IDS = ("WSSRC-FIS-030", "WSSRC-FIS-031")
IGR_SERIES_ID = "WSER-FIS-AU-IGR"
IGR_OCCURRENCE_ID = "WSO-FIS-AU-IGR-20260921"
IGR_REVIEW_ID = "WS-STEP14C-AU-IGR-SOURCES-CANONICAL-REVIEW-20260929-001"
IGR_ADMISSION_ID = "WS-ADMISSION-AU-TREASURY-IGR-20260929-001"

REVIEWER = {"reviewer_id": "operator-human-review", "role": "human-review"}


class Step14CError(ValueError):
    """Raised when a Step 14C transaction fails closed."""


def _load(root: Path, relative: Path) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def _dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _parse_utc(value: str, field: str) -> str:
    if not isinstance(value, str) or len(value) != 20 or not value.endswith("Z"):
        raise Step14CError(f"{field} must be exact UTC")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise Step14CError(f"{field} is invalid UTC") from exc
    if parsed.tzinfo != timezone.utc:
        raise Step14CError(f"{field} must be UTC")
    return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")


def _ordered_unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _audit_hashes(root: Path, relative_paths: list[Path]) -> dict[str, str]:
    return {
        str(path): hashlib.sha256((root / path).read_bytes()).hexdigest()
        for path in relative_paths
        if (root / path).exists()
    }


def _component_ref(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "component_type": row["component_type"],
        "component_id": row["component_id"],
        "revision_id": row["revision_id"],
        "object_sha256": row["object_sha256"],
    }


def _manifest_citations(package: dict[str, Any]) -> list[dict[str, Any]]:
    citations = []
    for entry in package["source_manifest"]:
        citations.append({
            "layer": entry["layer"],
            "object_id": entry["object_id"],
            "revision_id": entry.get("revision_id"),
            "object_sha256": entry["object_sha256"],
            "epistemic_class": "FACTUAL_SOURCE" if entry["layer"] != "ANALYSIS" else "HYPOTHESIS",
            "factual_claim": entry["layer"] != "ANALYSIS",
            "role": "STEP14C_CLIMATE_LINEAGE",
        })
    return citations


def _assert_step14a_package(root: Path) -> dict[str, Any]:
    package = _load(root, PACKAGE_RELATIVE)
    errors = validate_climate_candidate_package(package)
    if errors:
        raise Step14CError("Step 14A package validation failed: " + "; ".join(errors))
    if (
        package.get("source_manifest_sha256") != EXPECTED_SOURCE_MANIFEST
        or package.get("baseline_candidate_fingerprint") != EXPECTED_BASELINE_FINGERPRINT
        or package.get("dimension_candidate_fingerprint") != EXPECTED_DIMENSION_FINGERPRINT
        or package.get("candidate_semantic_fingerprint") != EXPECTED_PACKAGE_FINGERPRINT
    ):
        raise Step14CError("Step 14A package fingerprint pin failed")
    return package


def _admit_component(candidate: dict[str, Any], review_id: str, admission_id: str, admitted_at: str) -> dict[str, Any]:
    row = deepcopy(candidate)
    row.update({
        "review_state": "ACCEPTED",
        "lifecycle_state": "EXPIRED",
        "review_transaction_id": review_id,
        "admission_transaction_id": admission_id,
        "reviewed_at_utc": admitted_at,
        "admitted_at_utc": admitted_at,
        "revision_reason": "Step 14C human-admitted historical climate Baseline/Dimension; current use is HISTORICAL_ONLY and no impact or attribution claim is admitted.",
    })
    return with_object_fingerprint(row)


def build_climate_transaction(root: Path, *, reviewed_at_utc: str, admitted_at_utc: str) -> dict[str, Any]:
    reviewed = _parse_utc(reviewed_at_utc, "reviewed_at_utc")
    admitted = _parse_utc(admitted_at_utc, "admitted_at_utc")
    if reviewed > admitted:
        raise Step14CError("reviewed_at_utc must not be later than admitted_at_utc")
    package = _assert_step14a_package(root)
    before = load_production_state(root)
    if (len(before["actors"]), len(before["components"]), len(before["snapshots"]), len(before["admissions"])) != (0, 3, 2, 2):
        raise Step14CError("Step 14C climate pre-state population drift")
    baseline = _admit_component(package["baseline_candidate"], CLIMATE_REVIEW_ID, CLIMATE_ADMISSION_ID, admitted)
    dimension = _admit_component(package["dimension_assessment_candidate"], CLIMATE_REVIEW_ID, CLIMATE_ADMISSION_ID, admitted)
    citations = _manifest_citations(package)
    snapshot = {
        "snapshot_series_id": CLIMATE_SNAPSHOT_SERIES_ID,
        "snapshot_revision_id": CLIMATE_SNAPSHOT_REVISION_ID,
        "revision_number": 1,
        "previous_snapshot_revision_id": None,
        "snapshot_kind": "COMPOSITIONAL_INDEX",
        "scope": {"jurisdictions": ["Australia"], "systems": ["AUSTRALIAN_TROPICAL_CYCLONE_REGION"]},
        "knowledge_cutoff_utc": package["knowledge_cutoff_utc"],
        "effective_as_of_utc": None,
        "effective_date": "2026-04-30",
        "effective_time_precision": "DAY_RANGE",
        "effective_time_basis": "Completed source-native 2025–26 season window; no UTC instant is manufactured.",
        "component_refs": [_component_ref(baseline), _component_ref(dimension)],
        "upstream_refs": citations,
        "source_manifest_sha256": package["source_manifest_sha256"],
        "proposal_id": package["baseline_candidate"]["source_proposal_id"] + "+" + package["dimension_assessment_candidate"]["source_proposal_id"],
        "review_transaction_id": CLIMATE_REVIEW_ID,
        "admission_transaction_id": CLIMATE_ADMISSION_ID,
        "limitations": [
            "Historical climate Baseline and completed-season Dimension only.",
            "No current Australian cyclone-risk, impact, attribution, Relationship, Risk, Scenario, Forecast or Outcome claim.",
            "Other World State dimensions remain unassessed or explicitly empty as recorded.",
        ],
        "empty_queried_domains": deepcopy(package["known_empty_or_unsupported_domains"]),
        "lifecycle_state": "EXPIRED",
        "visibility": "INTERNAL_ONLY",
        "reviewer": deepcopy(REVIEWER),
        "reviewed_at_utc": reviewed,
        "admitted_at_utc": admitted,
        "object_sha256": None,
    }
    snapshot = with_object_fingerprint(snapshot)
    post_state = {key: deepcopy(value) for key, value in before.items()}
    post_state["components"] = before["components"] + [baseline, dimension]
    post_state["snapshots"] = before["snapshots"] + [snapshot]
    pre_hashes = state_hashes(before)
    post_hashes = state_hashes(post_state)
    transaction = {
        "transaction_id": CLIMATE_ADMISSION_ID,
        "contract_version": "0.1",
        "transaction_type": "WORLD_STATE_PRODUCTION_ADMISSION",
        "decision": "ACCEPTED",
        "proposal_id": snapshot["proposal_id"],
        "proposal_semantic_fingerprint": package["candidate_semantic_fingerprint"],
        "source_manifest_sha256": package["source_manifest_sha256"],
        "candidate_component_fingerprints": [
            {"component_id": BASELINE_ID, "component_type": "BASELINE", "revision_id": BASELINE_REVISION_ID, "object_sha256": package["baseline_candidate"]["object_sha256"]},
            {"component_id": DIMENSION_ID, "component_type": "DIMENSION_ASSESSMENT", "revision_id": DIMENSION_REVISION_ID, "object_sha256": package["dimension_assessment_candidate"]["object_sha256"]},
        ],
        "component_fingerprints": [_component_ref(baseline), _component_ref(dimension)],
        "reviewer": deepcopy(REVIEWER),
        "review_transaction_id": CLIMATE_REVIEW_ID,
        "decided_at_utc": reviewed,
        "component_dispositions": [
            {"component_id": BASELINE_ID, "revision_id": BASELINE_REVISION_ID, "disposition": "ADMITTED", "reason": "Historical official-reference Baseline accepted under the explicit Step 14C review."},
            {"component_id": DIMENSION_ID, "revision_id": DIMENSION_REVISION_ID, "disposition": "ADMITTED", "reason": "Narrow completed-season Dimension accepted under the explicit Step 14C review."},
        ],
        "snapshot_revision_identity": {"snapshot_series_id": CLIMATE_SNAPSHOT_SERIES_ID, "snapshot_revision_id": CLIMATE_SNAPSHOT_REVISION_ID},
        "snapshot_fingerprint": snapshot["object_sha256"],
        "write_targets": ["data/world_state/components.json", "data/world_state/snapshots.json", "data/world_state/admission_transactions.json", "data/world_state_audit/STEP14C_AU_TC_COMPONENT_REVIEW_ACCEPTED.json"],
        "pre_state_hashes": pre_hashes,
        "post_state_hashes": post_hashes,
        "visibility_decision": "INTERNAL_ONLY",
        "public_projection_permitted": False,
        "admitted_at_utc": admitted,
        "validator_version": "world-state-step14c-climate-admission-v1",
        "transaction_fingerprint": None,
    }
    transaction["transaction_fingerprint"] = fingerprint(transaction, exclude={"transaction_fingerprint"})
    errors = validate_component_history(post_state["components"])
    errors.extend(validate_snapshot_history(post_state["snapshots"], component_index={(r["component_type"], r["revision_id"]): r for r in post_state["components"]}))
    errors.extend(validate_admission_transaction(transaction))
    errors.extend(validate_snapshot(snapshot, component_index={(r["component_type"], r["revision_id"]): r for r in post_state["components"]}))
    if errors:
        raise Step14CError("climate transaction failed validation: " + "; ".join(errors))
    return {"package": package, "components": [baseline, dimension], "snapshot": snapshot, "transaction": transaction, "reviewed_at_utc": reviewed, "admitted_at_utc": admitted}


def _source_record(candidate: dict[str, Any], source_id: str, *, role: str) -> dict[str, Any]:
    manual = deepcopy(candidate)
    for candidate_only in (
        "proposed_source_id", "source_type_candidate", "rights_result", "robots_result",
        "feed_result", "automated_monitoring_permission", "automatic_admission",
        "redistribution_permission",
    ):
        manual.pop(candidate_only, None)
    manual.update({
        "source_id": source_id,
        "endpoint_role": role,
        "source_type": candidate["source_type_candidate"],
        "future_schedule_horizon": "historical strategic publication provenance only; no forward schedule authority",
        "typical_advance_notice": "manual historical recheck",
        "machine_readable_available": "HTML/PDF/manual document bundle",
        "source_timezone": "Australia/Sydney",
        "recommended_verification_cadence": "manual authoritative recheck only",
        "activation_status": "ACTIVE_GUARDED",
        "parser_type": "MANUAL_HTML_PROVENANCE",
        "known_limitations": ["Manual provenance source only; no automated retrieval or polling route is admitted."],
        "backup_source": None,
        "notes": "Step 14C manual-only Treasury provenance; not a monitor route and not an automatic analytical intake.",
        "timezone_scope": "FIXED",
        "parser_version": None,
        "runtime_health_state": "MANUAL_ONLY_NOT_POLLED",
        "licence_constraints": candidate.get("rights_result"),
        "ingestion_permission": "CURATED_FACTUAL_METADATA_MANUAL_REFERENCE_ONLY",
        "licence_review_status": "MANUAL_ONLY_RIGHTS_HOLD",
        "automated_retrieval_permission": "PRODUCTION_AUTOMATION_HOLD",
        "redistribution_permission": "NOT_CLEARED_UNLESS_SOURCE_SPECIFICALLY_REVIEWED",
        "rights_evidence_url": candidate.get("rights_evidence_url"),
        "rights_summary": candidate.get("rights_result"),
        "automation_summary": "Manual authoritative recheck only; no automated polling, monitor route, adapter or expectation is created.",
        "rights_reviewed_at": "2026-09-29",
        "rights_review_scope": "STEP14C_MANUAL_ONLY_TREASURY_SOURCE_GOVERNANCE",
        "rights_review_note": "Operational governance classification; not legal advice.",
        "monitoring_readiness_status": "MANUAL_ONLY_RIGHTS_HOLD",
        "monitoring_priority_score": 0,
        "canonical_dependency_count": 1 if "IGR" in source_id or "publication" in role.lower() else 0,
        "monitoring_readiness_assessed_at": "2026-09-29",
        "monitoring_activation_status": "PRODUCTION_AUTOMATION_HOLD",
        "last_successful_research_verification_at": "2026-09-28T14:17:45Z",
        "monitor_endpoints": [],
        "canonical_provenance_use": "MANUAL_AUTHORITATIVE_PROVENANCE_ONLY",
        "automated_monitoring_use": "MANUAL_ONLY_RIGHTS_HOLD",
        "verification_mode": "MANUAL_AUTHORITATIVE_RECHECK",
        "governance_backfill_reviewed_at": "2026-09-29",
        "governance_backfill_basis": "Step 14C explicitly admits manual-only provenance and does not infer automated monitoring permission from public availability.",
    })
    return manual


def _igr_record(source_id: str) -> dict[str, Any]:
    return {
        "occurrence_id": IGR_OCCURRENCE_ID,
        "series_id": IGR_SERIES_ID,
        "external_source_id": None,
        "canonical_name": "2026 Intergenerational Report",
        "short_calendar_title": "2026 Intergenerational Report",
        "category": "FISCAL_SOVEREIGN_FINANCE",
        "subcategory": "strategic_fiscal_projection_publication",
        "jurisdiction": "Australia",
        "region": "Oceania / Pacific",
        "institution": "Australian Treasury",
        "event_type": "INFORMATION_RELEASE",
        "record_class": "OCCURRENCE",
        "certainty_status": "CONFIRMED",
        "activation_mode": "REVIEWED_HISTORICAL_RECOVERY",
        "lifecycle_status": "COMPLETED",
        "condition_state": "NOT_REQUIRED",
        "condition_description": None,
        "trigger_source_id": None,
        "trigger_assertion_id": None,
        "triggered_at": None,
        "trigger_verification_status": "NOT_APPLICABLE",
        "timing_type": "CIVIL_DATE",
        "start_local": "2026-09-21",
        "end_local": None,
        "source_timezone": "Australia/Sydney",
        "start_utc": None,
        "end_utc": None,
        "date_earliest": None,
        "date_latest": None,
        "time_precision": "DAY",
        "time_status": "CONFIRMED",
        "time_basis": "Official Treasury publication date at source-native civil-date precision; no UTC instant is manufactured.",
        "all_day_semantics": True,
        "reference_period": "2026 Intergenerational Report",
        "publication_datetime": None,
        "location": None,
        "source_id": source_id,
        "primary_source_assertion_id": "WSA-AU-IGR-TREASURY-20260921",
        "last_successful_assertion_id": "WSA-AU-IGR-TREASURY-20260921",
        "status_history": [{"as_of": "2026-09-29", "certainty_status": "CONFIRMED", "lifecycle_status": "COMPLETED", "change_reason": "Historical Canonical recovery accepted from official Treasury publication bundle; no recurring series inferred.", "source_assertion_id": "WSA-AU-IGR-TREASURY-20260921"}],
        "first_announced_at": "2026-09-09",
        "first_discovered_at": "2026-09-28T14:17:45Z",
        "last_verified_at": "2026-09-28T14:17:45Z",
        "next_verification_due": "SOURCE_SPECIFIC",
        "parent_occurrence_id": None,
        "related_occurrence_ids": [],
        "related_documents": [
            {"source_id": source_id, "role": "AUTHORITATIVE_MAIN_REPORT_BUNDLE", "source_locator": "https://treasury.gov.au/publication/2026-intergenerational-report", "document_types": ["MAIN_REPORT", "FACT_SHEET", "CHART_DATA"]},
            {"source_id": TREASURY_SOURCE_IDS[1], "role": "FIRST_ANNOUNCEMENT_CONTEXT", "source_locator": "https://ministers.treasury.gov.au/ministers/jim-chalmers-2022/media-releases/2026-intergenerational-report"},
        ],
        "intrinsic_importance": "HIGH",
        "expected_market_sensitivity": "MEDIUM",
        "geopolitical_sensitivity": "LOW",
        "transmission_channels": ["fiscal_sustainability", "demographics", "productivity", "public_finance"],
        "render_policy": "EXCLUDE",
        "visibility_tier": "INTERNAL_ONLY",
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
        "recurrence": None,
        "derivation_sources": [source_id, TREASURY_SOURCE_IDS[1]],
        "observed_market_response": None,
        "population_tranche": "STEP14C_HISTORICAL_CANONICAL_RECOVERY",
        "notes": "Official projection only. Recovered after a coverage-gap audit; no World State, Analysis, Signal, Forecast, Scenario, Risk or Relationship intake is created. No recurrence is inferred.",
    }


def build_source_canonical_transaction(root: Path, *, reviewed_at_utc: str, admitted_at_utc: str) -> dict[str, Any]:
    reviewed = _parse_utc(reviewed_at_utc, "reviewed_at_utc")
    admitted = _parse_utc(admitted_at_utc, "admitted_at_utc")
    if reviewed > admitted:
        raise Step14CError("source/Canonical reviewed_at_utc must not be later than admitted_at_utc")
    source_candidate = _load(root, SOURCE_CANDIDATE_RELATIVE)
    igr_candidate = _load(root, IGR_CANDIDATE_RELATIVE)
    gap = _load(root, IGR_GAP_RELATIVE)
    if source_candidate.get("review_state") != "CANDIDATE_REVIEW_REQUIRED" or source_candidate.get("production_registry_write") is not False:
        raise Step14CError("Treasury source candidate is not the retained unadmitted artifact")
    if igr_candidate.get("candidate_id") != "WSCAND-AU-IGR-20260921-001" or igr_candidate.get("canonical_write_permitted") is not False:
        raise Step14CError("IGR Canonical candidate is not the retained unadmitted artifact")
    if gap.get("review_state") not in {"CANDIDATE_REVIEW_REQUIRED", "REVIEWED_COVERAGE_GAP", "REVIEW_PENDING"}:
        raise Step14CError("IGR coverage-gap audit is unavailable")
    sources = _load(root, Path("data/sources/registry.json"))
    canonical = _load(root, Path("data/canonical/registry.json"))
    existing_source_ids = {row.get("source_id") for row in sources.get("sources", [])}
    existing_occurrence_ids = {row.get("occurrence_id") for row in canonical.get("records", [])}
    if existing_source_ids.intersection(TREASURY_SOURCE_IDS) or IGR_OCCURRENCE_ID in existing_occurrence_ids or IGR_SERIES_ID in {row.get("series_id") for row in canonical.get("records", [])}:
        raise Step14CError("Step 14C source or Canonical identity collision")
    candidates = source_candidate["candidates"]
    source_a = _source_record(candidates[0], TREASURY_SOURCE_IDS[0], role="Australian Treasury strategic fiscal publications / IGR report authority")
    source_b = _source_record(candidates[1], TREASURY_SOURCE_IDS[1], role="Treasury Ministers advance announcement and publication context")
    igr = _igr_record(TREASURY_SOURCE_IDS[0])
    post_sources = deepcopy(sources)
    post_sources["version"] = "2.05"
    post_sources["sources"] = sources["sources"] + [source_a, source_b]
    post_canonical = deepcopy(canonical)
    post_canonical["version"] = "0.44"
    post_canonical["reference_date"] = "2026-09-29"
    post_canonical["records"] = canonical["records"] + [igr]
    post_canonical["record_count"] = len(post_canonical["records"])
    source_report = validate_registry(post_canonical, post_sources)
    if not source_report.ok:
        raise Step14CError("source/Canonical transaction failed validation: " + "; ".join(source_report.errors))
    review = {
        "transaction_id": IGR_REVIEW_ID,
        "transaction_type": "WORLD_STATE_SOURCE_CANONICAL_REVIEW",
        "decision": "ACCEPTED",
        "decision_scope": "MANUAL_AUTHORITATIVE_PROVENANCE_AND_CANONICAL_RECOVERY_ONLY",
        "candidate_source_ids": list(TREASURY_SOURCE_IDS),
        "candidate_id": igr_candidate["candidate_id"],
        "source_candidate_artifact": str(SOURCE_CANDIDATE_RELATIVE),
        "canonical_candidate_artifact": str(IGR_CANDIDATE_RELATIVE),
        "coverage_gap_artifact": str(IGR_GAP_RELATIVE),
        "reviewer": deepcopy(REVIEWER),
        "reviewed_at_utc": reviewed,
        "review_basis": [
            "Treasury authority and ministerial announcement roles remain separate.",
            "Sources are manual-only; no automated monitoring, polling or route is admitted.",
            "IGR is recovered as one completed official projection occurrence with a publication bundle and no recurrence.",
            "No analytical intake or public projection is authorised.",
        ],
        "write_targets": ["data/sources/registry.json", "data/canonical/registry.json"],
        "public_projection_permitted": False,
        "world_state_write_permitted": False,
        "review_fingerprint": None,
    }
    review["review_fingerprint"] = fingerprint(review, exclude={"review_fingerprint"})
    pre_hashes = _audit_hashes(root, [Path("data/sources/registry.json"), Path("data/canonical/registry.json")])
    post_hashes = {"sources": fingerprint(post_sources), "canonical": fingerprint(post_canonical)}
    transaction = {
        "transaction_id": IGR_ADMISSION_ID,
        "transaction_type": "SOURCE_CANONICAL_CONTROLLED_ADMISSION",
        "contract_version": "0.1",
        "decision": "ACCEPTED",
        "review_transaction_id": IGR_REVIEW_ID,
        "reviewer": deepcopy(REVIEWER),
        "decided_at_utc": reviewed,
        "admitted_at_utc": admitted,
        "source_ids": list(TREASURY_SOURCE_IDS),
        "canonical_series_id": IGR_SERIES_ID,
        "canonical_occurrence_id": IGR_OCCURRENCE_ID,
        "candidate_id": igr_candidate["candidate_id"],
        "first_announced_at": igr["first_announced_at"],
        "first_discovered_at_utc": igr["first_discovered_at"],
        "publication_date": igr["start_local"],
        "publication_time_precision": igr["time_precision"],
        "bundle_document_types": ["MAIN_REPORT", "FACT_SHEET", "CHART_DATA"],
        "recurrence": None,
        "manual_only": True,
        "automation_status": "PRODUCTION_AUTOMATION_HOLD",
        "analytical_promotion": False,
        "public_projection_permitted": False,
        "pre_state_hashes": pre_hashes,
        "post_state_hashes": post_hashes,
        "write_targets": ["data/sources/registry.json", "data/canonical/registry.json", "data/coverage/STEP14C_AU_IGR_SOURCE_CANONICAL_REVIEW_ACCEPTED.json", "data/coverage/STEP14C_AU_IGR_SOURCE_CANONICAL_ADMISSION_TRANSACTION.json"],
        "validator_version": "world-state-step14c-source-canonical-admission-v1",
        "transaction_fingerprint": None,
    }
    transaction["transaction_fingerprint"] = fingerprint(transaction, exclude={"transaction_fingerprint"})
    return {"sources": [source_a, source_b], "canonical": igr, "post_sources": post_sources, "post_canonical": post_canonical, "review": review, "transaction": transaction, "reviewed_at_utc": reviewed, "admitted_at_utc": admitted}


def _write_world_state_transaction(root: Path, built: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory(prefix="world-signals-step14c-climate-") as temporary:
        temp_root = Path(temporary) / "repo"
        shutil.copytree(root / "data" / "world_state", temp_root / "data" / "world_state")
        current = load_production_state(root)
        components_doc = _load(root, Path("data/world_state/components.json"))
        snapshots_doc = _load(root, Path("data/world_state/snapshots.json"))
        admissions_doc = _load(root, Path("data/world_state/admission_transactions.json"))
        components_doc["components"].extend(built["components"])
        snapshots_doc["snapshots"].append(built["snapshot"])
        admissions_doc["transactions"].append(built["transaction"])
        _dump(temp_root / "data/world_state/components.json", components_doc)
        _dump(temp_root / "data/world_state/snapshots.json", snapshots_doc)
        _dump(temp_root / "data/world_state/admission_transactions.json", admissions_doc)
        errors = validate_production_state(temp_root, enforce_first_population=False)
        if errors:
            raise Step14CError("climate temporary materialisation failed: " + "; ".join(errors))
        review = {
            "transaction_id": CLIMATE_REVIEW_ID,
            "transaction_type": "WORLD_STATE_COMPONENT_REVIEW",
            "decision": "ACCEPTED",
            "decision_scope": "HISTORICAL_CLIMATE_BASELINE_AND_DIMENSION_ONLY",
            "candidate_package": str(PACKAGE_RELATIVE),
            "candidate_semantic_fingerprint": EXPECTED_PACKAGE_FINGERPRINT,
            "source_manifest_sha256": EXPECTED_SOURCE_MANIFEST,
            "component_decisions": [{"component_id": row["component_id"], "revision_id": row["revision_id"], "decision": "ACCEPTED", "impact_or_attribution_promotion": "NONE"} for row in built["components"]],
            "reviewer": deepcopy(REVIEWER),
            "reviewed_at_utc": built["reviewed_at_utc"],
            "visibility": "INTERNAL_ONLY",
            "public_projection_permitted": False,
            "production_world_state_admitted": True,
            "write_targets": ["data/world_state/components.json", "data/world_state/snapshots.json", "data/world_state/admission_transactions.json"],
            "historical_only_current_use": True,
            "review_fingerprint": None,
        }
        review["review_fingerprint"] = fingerprint(review, exclude={"review_fingerprint"})
        destination = root / "data/world_state_audit/STEP14C_AU_TC_COMPONENT_REVIEW_ACCEPTED.json"
        _dump(temp_root / "data/world_state_audit/STEP14C_AU_TC_COMPONENT_REVIEW_ACCEPTED.json", review)
        targets = (Path("data/world_state/components.json"), Path("data/world_state/snapshots.json"), Path("data/world_state/admission_transactions.json"))
        original_bytes = {relative: (root / relative).read_bytes() for relative in targets}
        try:
            for relative in targets:
                (root / relative).write_bytes((temp_root / relative).read_bytes())
        except Exception:
            for relative, content in original_bytes.items():
                (root / relative).write_bytes(content)
            raise
        _dump(destination, review)


def _write_source_canonical_transaction(root: Path, built: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory(prefix="world-signals-step14c-sources-") as temporary:
        temp_root = Path(temporary) / "repo"
        shutil.copytree(root / "data" / "sources", temp_root / "data" / "sources")
        shutil.copytree(root / "data" / "canonical", temp_root / "data" / "canonical")
        _dump(temp_root / "data/sources/registry.json", built["post_sources"])
        _dump(temp_root / "data/canonical/registry.json", built["post_canonical"])
        report = validate_registry(built["post_canonical"], built["post_sources"])
        if not report.ok:
            raise Step14CError("source/Canonical temporary materialisation failed: " + "; ".join(report.errors))
        _dump(temp_root / "data/coverage/STEP14C_AU_IGR_SOURCE_CANONICAL_REVIEW_ACCEPTED.json", built["review"])
        _dump(temp_root / "data/coverage/STEP14C_AU_IGR_SOURCE_CANONICAL_ADMISSION_TRANSACTION.json", built["transaction"])
        targets = (Path("data/sources/registry.json"), Path("data/canonical/registry.json"))
        original_bytes = {relative: (root / relative).read_bytes() for relative in targets}
        try:
            for relative in targets:
                (root / relative).write_bytes((temp_root / relative).read_bytes())
        except Exception:
            for relative, content in original_bytes.items():
                (root / relative).write_bytes(content)
            raise
        _dump(root / "data/coverage/STEP14C_AU_IGR_SOURCE_CANONICAL_REVIEW_ACCEPTED.json", built["review"])
        _dump(root / "data/coverage/STEP14C_AU_IGR_SOURCE_CANONICAL_ADMISSION_TRANSACTION.json", built["transaction"])


def materialize_step14c(root: Path, *, reviewed_at_utc: str, admitted_at_utc: str, climate: bool = True, sources_and_canonical: bool = True) -> dict[str, Any]:
    """Preflight and materialise explicitly requested independent transactions."""
    if not climate and not sources_and_canonical:
        raise Step14CError("at least one independent Step 14C transaction must be selected")
    result: dict[str, Any] = {}
    climate_built = build_climate_transaction(root, reviewed_at_utc=reviewed_at_utc, admitted_at_utc=admitted_at_utc) if climate else None
    source_built = build_source_canonical_transaction(root, reviewed_at_utc=reviewed_at_utc, admitted_at_utc=admitted_at_utc) if sources_and_canonical else None
    if climate:
        assert climate_built is not None
        _write_world_state_transaction(root, climate_built)
        result["climate"] = climate_built["transaction"]
    if sources_and_canonical:
        assert source_built is not None
        _write_source_canonical_transaction(root, source_built)
        result["sources_and_canonical"] = source_built["transaction"]
    return result


__all__ = [
    "Step14CError",
    "build_climate_transaction",
    "build_source_canonical_transaction",
    "materialize_step14c",
]
