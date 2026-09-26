from __future__ import annotations

from copy import deepcopy
from typing import Any

OCCURRENCE_ID = "WSO-ad4d0618a65059f2"
SERIES_ID = "WS.CB.ECB.MONETARY_POLICY_DECISION"
SCHEDULE_SOURCE_ID = "WSSRC-CB-003"
OUTCOME_SOURCE_ID = "WSSRC-CB-004"
ASSERTION_ID = "WSA-CP-19be487885570ab9"
CHANGE_ID = "WSCHANGE-e94c7fb7c8d8bd02"
OBSERVATION_ID = "WSLI-MON-ECB-RATES-20260910-001"
EVIDENCE_ID = "WSEV-LI-ECB-MP-20260910"
TARGET_CANONICAL_VERSION = "0.43"
TARGET_LEDGER_VERSION = "0.29"
TARGET_OVERLAY_VERSION = "0.18"
TARGET_LIVE_VERSION = "0.12"
TARGET_POPULATION_STATE = "CONTROLLED_EUROPE_ECB_MONETARY_POLICY_OUTCOME_SPECIMEN"

ALLOWED_CANONICAL_FIELDS = {
    "lifecycle_status",
    "last_successful_assertion_id",
    "status_history",
    "last_verified_at",
    "related_documents",
    "notes",
}


def version_tuple(value: Any) -> tuple[int, ...]:
    return tuple(int(part) for part in str(value).split("."))


def version_at_least(value: Any, floor: str) -> bool:
    try:
        return version_tuple(value) >= version_tuple(floor)
    except (TypeError, ValueError):
        return False


def _one(rows: list[dict[str, Any]], key: str, value: str) -> dict[str, Any] | None:
    found = [row for row in rows if row.get(key) == value]
    if len(found) > 1:
        raise ValueError(f"CP duplicate {key}={value}")
    return found[0] if found else None


def changed_fields(before: dict[str, Any], after: dict[str, Any]) -> set[str]:
    return {key for key in set(before) | set(after) if before.get(key) != after.get(key)}


def _require_prestate(registry: dict[str, Any], sources: dict[str, Any], ledger: dict[str, Any], overlay: dict[str, Any], schema: dict[str, Any], observations: dict[str, Any], evidence: dict[str, Any], plan: dict[str, Any]) -> None:
    p = plan["preconditions"]
    checks = [
        (str(registry.get("version")) == p["canonical_registry_version"], "Canonical version drift"),
        (registry.get("record_count") == p["canonical_record_count"] == len(registry.get("records") or []), "Canonical count drift"),
        (str(sources.get("version")) == p["source_registry_version"], "Source version drift"),
        (len(sources.get("sources") or []) == p["source_record_count"], "Source count drift"),
        (str(ledger.get("version")) == p["change_ledger_version"], "Ledger version drift"),
        (len(ledger.get("changes") or []) == p["change_ledger_count"], "Ledger count drift"),
        (str(overlay.get("version")) == p["biosecurity_overlay_version"], "Overlay version drift"),
        ((overlay.get("canonical_checkpoint") or {}).get("registry_version") == p["biosecurity_overlay_registry_version"], "Overlay checkpoint drift"),
        (str(schema.get("version")) == p["live_schema_version"], "Live schema version drift"),
        (str(observations.get("version")) == p["live_observations_version"], "Live observations version drift"),
        (len(observations.get("observations") or []) == p["live_observation_count"], "Live observation count drift"),
        (str(evidence.get("version")) == p["live_evidence_version"], "Live evidence version drift"),
        (len(evidence.get("evidence") or []) == p["live_evidence_count"], "Live evidence count drift"),
    ]
    errors = [msg for ok, msg in checks if not ok]
    target = _one(registry.get("records") or [], "occurrence_id", OCCURRENCE_ID)
    if target is None:
        errors.append("ECB Canonical target missing")
    else:
        exact = {
            "series_id": SERIES_ID,
            "lifecycle_status": p["target_lifecycle_status"],
            "certainty_status": p["target_certainty_status"],
            "start_local": p["target_start_local"],
            "source_timezone": p["target_timezone"],
            "start_utc": p["target_start_utc"],
            "primary_source_assertion_id": p["target_primary_source_assertion_id"],
            "last_successful_assertion_id": p["target_last_successful_assertion_id"],
            "last_verified_at": p["target_last_verified_at"],
            "source_id": SCHEDULE_SOURCE_ID,
        }
        for key, expected in exact.items():
            if target.get(key) != expected:
                errors.append(f"ECB target prestate drift: {key}")
        if target.get("related_documents") != p["target_related_documents"]:
            errors.append("ECB related_documents prestate drift")
    source = _one(sources.get("sources") or [], "source_id", OUTCOME_SOURCE_ID)
    if source is None:
        errors.append("ECB outcome source missing")
    else:
        if source.get("canonical_provenance_use") != p["source_004_canonical_provenance_use"]:
            errors.append("ECB outcome source provenance posture drift")
        if source.get("automated_monitoring_use") != p["source_004_automated_monitoring_use"]:
            errors.append("ECB outcome source automation posture drift")
        if source.get("verification_mode") != p["source_004_verification_mode"]:
            errors.append("ECB outcome source verification mode drift")
    if _one(ledger.get("changes") or [], "change_id", CHANGE_ID) is not None:
        errors.append("CP change ID collision")
    if _one(observations.get("observations") or [], "observation_id", OBSERVATION_ID) is not None:
        errors.append("CP observation ID collision")
    if _one(evidence.get("evidence") or [], "evidence_id", EVIDENCE_ID) is not None:
        errors.append("CP evidence ID collision")
    if errors:
        raise ValueError("; ".join(errors))


def target_canonical_registry(registry: dict[str, Any], payload: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    target = _one(registry.get("records") or [], "occurrence_id", OCCURRENCE_ID)
    if target is None:
        raise ValueError("ECB Canonical target missing")
    if version_at_least(registry.get("version"), TARGET_CANONICAL_VERSION):
        if target.get("lifecycle_status") == "COMPLETED" and target.get("last_successful_assertion_id") == ASSERTION_ID:
            return deepcopy(registry)
        raise ValueError("CP descendant Canonical state lacks expected completion checkpoint")
    c = payload["canonical_lifecycle"]
    before = deepcopy(target)
    after = deepcopy(before)
    after["lifecycle_status"] = "COMPLETED"
    after["last_successful_assertion_id"] = ASSERTION_ID
    after["last_verified_at"] = c["last_verified_at"]
    after["status_history"] = deepcopy(before.get("status_history") or []) + [{
        "as_of": plan["reference_date"],
        "certainty_status": "CONFIRMED",
        "lifecycle_status": "COMPLETED",
        "condition_state": "NOT_REQUIRED",
        "change_reason": "ECB first-party monetary-policy decision publication verifies completion; not inferred from elapsed time.",
        "source_assertion_id": ASSERTION_ID,
        "basis": c["completion_basis"],
    }]
    after["related_documents"] = deepcopy(before.get("related_documents") or []) + [deepcopy(c["related_document"])]
    after["notes"] = c["notes"]
    if changed_fields(before, after) != ALLOWED_CANONICAL_FIELDS:
        raise ValueError("CP Canonical transform changed fields outside the lifecycle allowance")
    out = deepcopy(registry)
    idx = next(i for i, row in enumerate(out["records"]) if row.get("occurrence_id") == OCCURRENCE_ID)
    out["records"][idx] = after
    out["version"] = TARGET_CANONICAL_VERSION
    out["reference_date"] = plan["reference_date"]
    out["record_count"] = len(out["records"])
    return out


def _ledger_payload_matches(existing: dict[str, Any], frozen: dict[str, Any]) -> bool:
    return {key: value for key, value in existing.items() if key != "committed_at"} == frozen and isinstance(existing.get("committed_at"), str) and bool(existing["committed_at"].strip())


def target_change_ledger(ledger: dict[str, Any], payload: dict[str, Any], plan: dict[str, Any], committed_at: str | None = None) -> dict[str, Any]:
    frozen = payload["change_ledger"]
    existing = _one(ledger.get("changes") or [], "change_id", CHANGE_ID)
    if existing is not None:
        if version_at_least(ledger.get("version"), TARGET_LEDGER_VERSION) and _ledger_payload_matches(existing, frozen):
            return deepcopy(ledger)
        raise ValueError("CP ledger is partially or inconsistently materialised")
    if str(ledger.get("version")) != plan["preconditions"]["change_ledger_version"]:
        raise ValueError("CP ledger prestate drift")
    row = deepcopy(frozen)
    row["committed_at"] = committed_at or frozen["reviewed_at"]
    out = deepcopy(ledger)
    out["version"] = TARGET_LEDGER_VERSION
    out["reference_date"] = plan["reference_date"]
    out["changes"].append(row)
    return out


def target_overlay(overlay: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    if version_at_least(overlay.get("version"), TARGET_OVERLAY_VERSION):
        cp = overlay.get("canonical_checkpoint") or {}
        if cp.get("registry_version") == TARGET_CANONICAL_VERSION and cp.get("record_count") == plan["expected_post_state"]["canonical_record_count"]:
            return deepcopy(overlay)
        raise ValueError("CP descendant overlay lacks target Canonical checkpoint")
    if str(overlay.get("version")) != plan["preconditions"]["biosecurity_overlay_version"]:
        raise ValueError("CP overlay prestate drift")
    out = deepcopy(overlay)
    out["version"] = TARGET_OVERLAY_VERSION
    out["canonical_checkpoint"] = {"registry_version": TARGET_CANONICAL_VERSION, "record_count": plan["expected_post_state"]["canonical_record_count"]}
    return out


def target_live_schema(schema: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    if version_at_least(schema.get("version"), TARGET_LIVE_VERSION):
        checkpoint = schema.get("cp_checkpoint") or {}
        if checkpoint.get("observation_count") == 11 and checkpoint.get("evidence_count") == 15:
            return deepcopy(schema)
        raise ValueError("CP descendant Live schema lacks CP checkpoint")
    if str(schema.get("version")) != plan["preconditions"]["live_schema_version"]:
        raise ValueError("CP Live schema prestate drift")
    cm = deepcopy(schema.get("correction_conflict_policy"))
    if not isinstance(cm, dict) or cm.get("mode") != "FOUNDATION_CONTRACT_NO_PRODUCTION_SPECIMEN":
        raise ValueError("CP requires the merged CM correction/conflict contract")
    out = deepcopy(schema)
    out["version"] = TARGET_LIVE_VERSION
    out["reference_date"] = plan["reference_date"]
    out["population_policy"] = {
        "mode": TARGET_POPULATION_STATE,
        "production_population_allowed": True,
        "evidence_population_allowed": True,
        "maximum_observation_count": 11,
        "maximum_evidence_count": 15,
        "automatic_ingestion_allowed": False,
        "existing_analysis_evidence_migration_allowed": False,
        "public_observation_projection_allowed": False,
        "reason": "CP adds exactly one reviewed ECB rate-decision outcome linked OUTCOME_OF the separately completed scheduled Canonical occurrence, supported by one primary-official ECB evidence row."
    }
    guardrails = list(out.get("guardrails") or [])
    old = "An eleventh Live observation, U.S. response specimen, production correction/conflict specimen, second production Live-to-Analysis link, further Analysis revision or additional Monitor activation requires another pressure audit."
    guardrails = [item for item in guardrails if item != old]
    additions = [
        "CO v0.11 remains the frozen ten-observation/fourteen-evidence checkpoint; CP is the separately pressure-audited eleventh observation.",
        "CP v0.12 adds one PRIMARY_CONFIRMED ECB POLICY_DEVELOPMENT linked OUTCOME_OF WSO-ad4d0618a65059f2 after a separately auditable first-party lifecycle completion of that existing Canonical decision occurrence.",
        "CP records the 25-basis-point increase in all three key ECB interest rates and their 2.50%, 2.65% and 2.90% levels effective 16 September 2026; staff projections and press-conference interpretation remain outside the Live observation.",
        "CP uses the ECB decision publication and exact ECB RSS publication timestamp as primary evidence; Live evidence has no authority to rewrite Canonical timing or source provenance.",
        "CP creates no new ECB source identity or Monitor route and opens no automatic ingestion, Canonical, Calendar, Analysis or public-projection gate.",
        "CM correction/retraction/conflicting-report semantics remain unchanged and fully applicable in CP v0.12.",
        "A twelfth Live observation, production correction/conflict specimen, second production Live-to-Analysis link, further Analysis revision or additional Monitor activation requires another pressure audit."
    ]
    for item in additions:
        if item not in guardrails:
            guardrails.append(item)
    out["guardrails"] = guardrails
    out["cp_checkpoint"] = {
        "schema_version": TARGET_LIVE_VERSION,
        "observations_version": TARGET_LIVE_VERSION,
        "evidence_version": TARGET_LIVE_VERSION,
        "population_state": TARGET_POPULATION_STATE,
        "observation_count": 11,
        "evidence_count": 15,
        "canonical_linked_observation_count": 4,
        "base_main_sha": plan["base_main_sha"],
        "canonical_occurrence_id": OCCURRENCE_ID,
        "historical_contract": "CP adds one bounded ECB rate-decision outcome only after first-party lifecycle completion, while preserving timing identity and all automatic/public gates."
    }
    if out.get("correction_conflict_policy") != cm:
        raise ValueError("CP mutated the CM correction/conflict policy")
    return out


def target_observations(observations: dict[str, Any], payload: dict[str, Any], plan: dict[str, Any], post_registry: dict[str, Any]) -> dict[str, Any]:
    target = _one(post_registry.get("records") or [], "occurrence_id", OCCURRENCE_ID)
    if target is None or target.get("lifecycle_status") != "COMPLETED":
        raise ValueError("CP Stage 2 requires a COMPLETED ECB Canonical anchor")
    existing = _one(observations.get("observations") or [], "observation_id", OBSERVATION_ID)
    if existing is not None:
        if version_at_least(observations.get("version"), TARGET_LIVE_VERSION):
            return deepcopy(observations)
        raise ValueError("CP observation exists below target version")
    if str(observations.get("version")) != plan["preconditions"]["live_observations_version"] or len(observations.get("observations") or []) != 10:
        raise ValueError("CP Live observation prestate drift")
    out = deepcopy(observations)
    out["version"] = TARGET_LIVE_VERSION
    out["reference_date"] = plan["reference_date"]
    out["population_state"] = TARGET_POPULATION_STATE
    out["observations"].append(deepcopy(payload["live_observation"]))
    out["scope_note"] = "Bounded reviewed internal Live Intelligence store through CP: eleven observations. CP adds one primary-confirmed ECB rate-decision outcome linked to the completed scheduled Canonical decision occurrence. Projections, expectations, surprise, market attribution and Analysis remain outside the observation; public projection and automatic ingestion remain closed."
    return out


def target_evidence(evidence: dict[str, Any], payload: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    existing = _one(evidence.get("evidence") or [], "evidence_id", EVIDENCE_ID)
    if existing is not None:
        if version_at_least(evidence.get("version"), TARGET_LIVE_VERSION):
            return deepcopy(evidence)
        raise ValueError("CP evidence exists below target version")
    if str(evidence.get("version")) != plan["preconditions"]["live_evidence_version"] or len(evidence.get("evidence") or []) != 14:
        raise ValueError("CP Live evidence prestate drift")
    out = deepcopy(evidence)
    out["version"] = TARGET_LIVE_VERSION
    out["reference_date"] = plan["reference_date"]
    out["population_state"] = TARGET_POPULATION_STATE
    out["evidence"].extend(deepcopy(payload["live_evidence"]))
    out["scope_note"] = "Evidence supports the bounded reviewed Live store through CP. CP adds one primary-official ECB decision row; the exact publication timestamp comes from the ECB's own press RSS item for the exact decision URL. It grants no automated Monitor authority or Analytical conclusion."
    return out


def build_target_state(registry: dict[str, Any], sources: dict[str, Any], ledger: dict[str, Any], overlay: dict[str, Any], schema: dict[str, Any], observations: dict[str, Any], evidence: dict[str, Any], payload: dict[str, Any], plan: dict[str, Any], committed_at: str | None = None) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    post_already = version_at_least(registry.get("version"), TARGET_CANONICAL_VERSION) and version_at_least(observations.get("version"), TARGET_LIVE_VERSION)
    if not post_already:
        _require_prestate(registry, sources, ledger, overlay, schema, observations, evidence, plan)
    post_registry = target_canonical_registry(registry, payload, plan)
    post_ledger = target_change_ledger(ledger, payload, plan, committed_at=committed_at)
    post_overlay = target_overlay(overlay, plan)
    post_schema = target_live_schema(schema, plan)
    post_observations = target_observations(observations, payload, plan, post_registry)
    post_evidence = target_evidence(evidence, payload, plan)
    return post_registry, post_ledger, post_overlay, post_schema, post_observations, post_evidence


def validate_cp_contract(registry: dict[str, Any], sources: dict[str, Any], ledger: dict[str, Any], overlay: dict[str, Any], schema: dict[str, Any], observations: dict[str, Any], evidence: dict[str, Any], plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected = plan["expected_post_state"]
    target = _one(registry.get("records") or [], "occurrence_id", OCCURRENCE_ID)
    obs = _one(observations.get("observations") or [], "observation_id", OBSERVATION_ID)
    ev = _one(evidence.get("evidence") or [], "evidence_id", EVIDENCE_ID)
    change = _one(ledger.get("changes") or [], "change_id", CHANGE_ID)
    if str(registry.get("version")) != TARGET_CANONICAL_VERSION or len(registry.get("records") or []) != expected["canonical_record_count"]:
        errors.append("CP Canonical target state mismatch")
    if str(ledger.get("version")) != TARGET_LEDGER_VERSION or len(ledger.get("changes") or []) != expected["change_ledger_count"]:
        errors.append("CP Change Ledger target state mismatch")
    if str(overlay.get("version")) != TARGET_OVERLAY_VERSION or (overlay.get("canonical_checkpoint") or {}).get("registry_version") != TARGET_CANONICAL_VERSION:
        errors.append("CP overlay checkpoint mismatch")
    live_descendant = (
        version_at_least(schema.get("version"), TARGET_LIVE_VERSION)
        and version_at_least(observations.get("version"), TARGET_LIVE_VERSION)
        and version_at_least(evidence.get("version"), TARGET_LIVE_VERSION)
        and (schema.get("cp_checkpoint") or {}).get("observation_count") == 11
        and (schema.get("cp_checkpoint") or {}).get("evidence_count") == 15
    )
    if not live_descendant:
        errors.append("CP Live version mismatch")
    if len(observations.get("observations") or []) < 11 or len(evidence.get("evidence") or []) < 15:
        errors.append("CP Live population count mismatch")
    if target is None or target.get("lifecycle_status") != "COMPLETED" or target.get("last_successful_assertion_id") != ASSERTION_ID:
        errors.append("CP Canonical lifecycle completion missing")
    if target is not None:
        protected = {
            "series_id": SERIES_ID,
            "source_id": SCHEDULE_SOURCE_ID,
            "certainty_status": "CONFIRMED",
            "timing_type": "LOCAL_DATETIME",
            "start_local": "2026-09-10T14:15:00",
            "source_timezone": "Europe/Berlin",
            "start_utc": "2026-09-10T12:15:00Z",
            "time_precision": "MINUTE",
            "time_status": "CONFIRMED",
            "time_basis": "AUTHORITATIVE_STANDARD_PUBLICATION_RULE",
            "intrinsic_importance": "UNRATED_PENDING_CALIBRATION",
            "expected_market_sensitivity": "UNRATED_PENDING_CALIBRATION",
            "geopolitical_sensitivity": "UNRATED_PENDING_CALIBRATION",
        }
        for key, value in protected.items():
            if target.get(key) != value:
                errors.append(f"CP protected Canonical field drift: {key}")
    if change is None or change.get("source_assertion_id") != ASSERTION_ID or change.get("change_type") != "LIFECYCLE_COMPLETION":
        errors.append("CP lifecycle Change Ledger row missing or malformed")
    elif not _ledger_payload_matches(change, payload_frozen := {key: value for key, value in change.items() if key != "committed_at"}):
        # Defensive shape check; exact frozen-payload comparison is performed by idempotent targeting.
        errors.append("CP lifecycle Change Ledger commit timestamp missing")
    if change is not None and (not isinstance(change.get("committed_at"), str) or not change["committed_at"].strip()):
        errors.append("CP lifecycle Change Ledger commit timestamp missing")
    if obs is None:
        errors.append("CP Live observation missing")
    else:
        if obs.get("observation_type") != "POLICY_DEVELOPMENT" or obs.get("verification_state") != "PRIMARY_CONFIRMED":
            errors.append("CP Live observation semantics drift")
        if obs.get("canonical_links") != [{"occurrence_id": OCCURRENCE_ID, "relationship": "OUTCOME_OF"}]:
            errors.append("CP OUTCOME_OF relationship drift")
        if obs.get("revision_of_observation_id") is not None:
            errors.append("CP is not a correction/retraction")
        if obs.get("automatic_canonical_commit") is not False or obs.get("google_calendar_write") is not False:
            errors.append("CP Live write gates opened")
        if obs.get("evidence_refs") != [EVIDENCE_ID]:
            errors.append("CP Live evidence reference drift")
    if ev is None:
        errors.append("CP Live evidence missing")
    else:
        if ev.get("evidence_class") != "PRIMARY_OFFICIAL" or ev.get("provider") != "European Central Bank":
            errors.append("CP evidence authority drift")
        if ev.get("publication_time") != {"precision": "EXACT_TIMESTAMP", "published_at_utc": "2026-09-10T12:15:00Z"}:
            errors.append("CP evidence publication time drift")
        if ev.get("canonical_provenance_effect") != "NONE":
            errors.append("CP Live evidence acquired Canonical provenance authority")
    source = _one(sources.get("sources") or [], "source_id", OUTCOME_SOURCE_ID)
    if source is None or source.get("automated_monitoring_use") != "ENDPOINT_REVIEW_REQUIRED":
        errors.append("CP source governance/automation boundary drift")
    cm = schema.get("correction_conflict_policy") or {}
    if cm.get("mode") != "FOUNDATION_CONTRACT_NO_PRODUCTION_SPECIMEN" or cm.get("minimum_unique_conflict_evidence_refs") != 2 or cm.get("minimum_distinct_conflict_providers") != 2:
        errors.append("CP weakened CM correction/conflict contract")
    checkpoint = schema.get("cp_checkpoint") or {}
    if checkpoint.get("canonical_linked_observation_count") != 4:
        errors.append("CP linked-observation checkpoint mismatch")
    return errors
