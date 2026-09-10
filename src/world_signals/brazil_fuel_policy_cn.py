from __future__ import annotations

from copy import deepcopy
from typing import Any


OBSERVATION_ID = "WSLI-POL-BRA-FUEL-POLICY-20260909-001"
EVIDENCE_ID = "WSEV-LI-BRA-MF-FUEL-POLICY-20260909"
TARGET_VERSION = "0.10"
TARGET_OBSERVATION_COUNT = 9
TARGET_EVIDENCE_COUNT = 12
TARGET_POPULATION_STATE = "CONTROLLED_UNSCHEDULED_LATIN_AMERICA_POLICY_SPECIMEN"


def version_tuple(value: Any) -> tuple[int, ...]:
    return tuple(int(part) for part in str(value).split("."))


def version_at_least(value: Any, floor: str) -> bool:
    try:
        return version_tuple(value) >= version_tuple(floor)
    except (TypeError, ValueError):
        return False


def _by_id(rows: list[dict[str, Any]], key: str, value: str) -> dict[str, Any] | None:
    matches = [row for row in rows if row.get(key) == value]
    if len(matches) > 1:
        raise ValueError(f"CN duplicate {key}={value}")
    return matches[0] if matches else None


def target_live_schema(schema: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    target = plan["target_state"]
    if version_at_least(schema.get("version"), target["live_schema_version"]):
        checkpoint = schema.get("cn_checkpoint") or {}
        if checkpoint.get("observation_count") == target["live_observation_count"] and checkpoint.get("evidence_count") == target["live_evidence_count"]:
            return deepcopy(schema)
        raise ValueError("CN descendant Live schema is at/above target without the CN checkpoint")

    pre = plan["pre_state"]
    if str(schema.get("version")) != pre["live_schema_version"]:
        raise ValueError("CN Live schema prestate drift")
    policy = schema.get("population_policy") or {}
    if policy.get("maximum_observation_count") != pre["live_observation_count"]:
        raise ValueError("CN Live observation policy ceiling drift")
    if policy.get("maximum_evidence_count") != pre["live_evidence_count"]:
        raise ValueError("CN Live evidence policy ceiling drift")

    correction_contract = deepcopy(schema.get("correction_conflict_policy"))
    if not isinstance(correction_contract, dict) or correction_contract.get("mode") != "FOUNDATION_CONTRACT_NO_PRODUCTION_SPECIMEN":
        raise ValueError("CN requires the merged CM correction/conflict contract")

    out = deepcopy(schema)
    out["version"] = target["live_schema_version"]
    out["reference_date"] = plan["reference_date"]
    out["population_policy"] = {
        "mode": TARGET_POPULATION_STATE,
        "production_population_allowed": True,
        "evidence_population_allowed": True,
        "maximum_observation_count": target["live_observation_count"],
        "maximum_evidence_count": target["live_evidence_count"],
        "automatic_ingestion_allowed": False,
        "existing_analysis_evidence_migration_allowed": False,
        "public_observation_projection_allowed": False,
        "reason": "CN adds exactly one pressure-audited unscheduled Brazilian fuel-policy development using bounded primary-official evidence; legal publication/effect, Canonical creation, Monitor routing and Analysis remain outside the specimen."
    }

    guardrails = list(out.get("guardrails") or [])
    old_gate = "A ninth Live observation, second production Live-to-Analysis link, further Analysis revision or additional Monitor activation requires another pressure audit."
    guardrails = [item for item in guardrails if item != old_gate]
    additions = [
        "CM v0.9 remains the frozen eight-observation/eleven-evidence checkpoint; CN is the separately pressure-audited ninth observation.",
        "CN v0.10 adds one PRIMARY_CONFIRMED unscheduled Brazil POLICY_DEVELOPMENT with zero Canonical links and one primary-official Ministry of Finance evidence row.",
        "CN records only the government's 9 September adoption/signing announcement and stated fuel-policy parameters; it does not infer Diário Oficial publication, entry into force or legal instrument numbers not established by the reviewed sources.",
        "CN preserves both event time and source-publication time at CIVIL_DATE precision; the source page's displayed 18h47 is not converted to UTC without an established source timezone.",
        "CN retains the government's geopolitical-conflict framing as attributed source context and does not convert it into independent WORLD SIGNALS causal analysis or observed inflation, pump-price, supply or market effects.",
        "CN creates no Canonical occurrence, Source Registry authority, Monitor route or Analysis review; automatic ingestion, automatic Canonical commit, Google Calendar writes and public Live projection remain prohibited.",
        "CM correction/retraction/conflicting-report semantics remain unchanged and fully applicable in CN v0.10.",
        "A tenth Live observation, production correction/conflict specimen, second production Live-to-Analysis link, further Analysis revision or additional Monitor activation requires another pressure audit."
    ]
    for item in additions:
        if item not in guardrails:
            guardrails.append(item)
    out["guardrails"] = guardrails
    out["cn_checkpoint"] = {
        "schema_version": target["live_schema_version"],
        "observations_version": target["live_schema_version"],
        "evidence_version": target["live_schema_version"],
        "population_state": TARGET_POPULATION_STATE,
        "observation_count": target["live_observation_count"],
        "evidence_count": target["live_evidence_count"],
        "canonical_linked_observation_count": target["canonical_linked_live_observation_count"],
        "base_main_sha": plan["exact_base_main_sha"],
        "historical_contract": "CN adds one bounded unscheduled Brazilian policy-adoption observation while preserving the CM correction/conflict contract and all upstream/downstream write boundaries."
    }
    if out.get("correction_conflict_policy") != correction_contract:
        raise ValueError("CN mutated the CM correction/conflict policy")
    return out


def target_observations(dataset: dict[str, Any], payload: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    rows = dataset.get("observations") or []
    existing = _by_id(rows, "observation_id", OBSERVATION_ID)
    target = plan["target_state"]
    if existing is not None:
        if not version_at_least(dataset.get("version"), target["live_schema_version"]):
            raise ValueError("CN observation exists below target dataset version")
        return deepcopy(dataset)

    pre = plan["pre_state"]
    if str(dataset.get("version")) != pre["live_schema_version"] or len(rows) != pre["live_observation_count"]:
        raise ValueError("CN Live observations prestate drift")

    out = deepcopy(dataset)
    out["version"] = target["live_schema_version"]
    out["reference_date"] = plan["reference_date"]
    out["population_state"] = TARGET_POPULATION_STATE
    out["observations"].append(deepcopy(payload["live_observation"]))
    out["scope_note"] = "Bounded reviewed internal Live Intelligence store through CN: nine observations. CN adds one unscheduled primary-confirmed Brazilian fuel-policy development with zero Canonical links; the observation records the government's adoption/signing announcement without upgrading unresolved legal-publication/effect status. Public projection and automatic ingestion remain closed."
    return out


def target_evidence(dataset: dict[str, Any], payload: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    rows = dataset.get("evidence") or []
    existing = _by_id(rows, "evidence_id", EVIDENCE_ID)
    target = plan["target_state"]
    if existing is not None:
        if not version_at_least(dataset.get("version"), target["live_schema_version"]):
            raise ValueError("CN evidence exists below target dataset version")
        return deepcopy(dataset)

    pre = plan["pre_state"]
    if str(dataset.get("version")) != pre["live_schema_version"] or len(rows) != pre["live_evidence_count"]:
        raise ValueError("CN Live evidence prestate drift")

    out = deepcopy(dataset)
    out["version"] = target["live_schema_version"]
    out["reference_date"] = plan["reference_date"]
    out["population_state"] = TARGET_POPULATION_STATE
    out["evidence"].append(deepcopy(payload["live_evidence"][0]))
    out["scope_note"] = "Evidence supports the bounded reviewed Live store through CN. CN adds one primary-official Brazil Ministry of Finance announcement row at civil-date publication precision; it supplies no Canonical provenance, unattended-monitoring authority or Analysis conclusion."
    return out


def validate_cn_contract(schema: dict[str, Any], observations: dict[str, Any], evidence: dict[str, Any], plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    target = plan["target_state"]
    rows = observations.get("observations") or []
    evidence_rows = evidence.get("evidence") or []
    obs = _by_id(rows, "observation_id", OBSERVATION_ID)
    ev = _by_id(evidence_rows, "evidence_id", EVIDENCE_ID)

    if str(schema.get("version")) != target["live_schema_version"]:
        errors.append("CN schema version mismatch")
    if str(observations.get("version")) != target["live_schema_version"]:
        errors.append("CN observations version mismatch")
    if str(evidence.get("version")) != target["live_schema_version"]:
        errors.append("CN evidence version mismatch")
    if len(rows) != target["live_observation_count"]:
        errors.append("CN observation count mismatch")
    if len(evidence_rows) != target["live_evidence_count"]:
        errors.append("CN evidence count mismatch")
    if obs is None:
        errors.append("CN observation missing")
    if ev is None:
        errors.append("CN evidence missing")

    if obs is not None:
        if obs.get("observation_type") != "POLICY_DEVELOPMENT":
            errors.append("CN observation type drift")
        if obs.get("verification_state") != "PRIMARY_CONFIRMED":
            errors.append("CN verification state drift")
        if obs.get("canonical_links") != []:
            errors.append("CN must remain zero-Canonical-link")
        if obs.get("revision_of_observation_id") is not None:
            errors.append("CN is not a Live correction/retraction")
        if obs.get("event_time") != {"precision": "CIVIL_DATE", "event_date": "2026-09-09"}:
            errors.append("CN event time must remain 9 September CIVIL_DATE")
        if obs.get("automatic_canonical_commit") is not False or obs.get("google_calendar_write") is not False:
            errors.append("CN write gates opened")
        summary = str(obs.get("summary") or "").lower()
        for phrase in ("does not assert", "does not assign", "does not claim"):
            if phrase not in summary:
                errors.append(f"CN legal/analytical caveat missing: {phrase}")

    if ev is not None:
        if ev.get("evidence_class") != "PRIMARY_OFFICIAL":
            errors.append("CN evidence must remain PRIMARY_OFFICIAL")
        if ev.get("canonical_provenance_effect") != "NONE":
            errors.append("CN evidence acquired Canonical provenance authority")
        if ev.get("publication_time") != {"precision": "CIVIL_DATE", "published_date": "2026-09-09"}:
            errors.append("CN publication time must remain 9 September CIVIL_DATE")

    policy = schema.get("population_policy") or {}
    if policy.get("maximum_observation_count") != target["live_observation_count"]:
        errors.append("CN observation ceiling mismatch")
    if policy.get("maximum_evidence_count") != target["live_evidence_count"]:
        errors.append("CN evidence ceiling mismatch")
    if policy.get("automatic_ingestion_allowed") is not False or policy.get("public_observation_projection_allowed") is not False:
        errors.append("CN public/automatic Live gates opened")

    cm = schema.get("correction_conflict_policy") or {}
    if cm.get("mode") != "FOUNDATION_CONTRACT_NO_PRODUCTION_SPECIMEN":
        errors.append("CN weakened CM correction/conflict mode")
    if cm.get("minimum_unique_conflict_evidence_refs") != 2 or cm.get("minimum_distinct_conflict_providers") != 2:
        errors.append("CN weakened CM conflict evidence plurality")
    if cm.get("corrected_or_retracted_requires_correction_evidence") is not True:
        errors.append("CN weakened CM correction evidence gate")

    return errors
