from __future__ import annotations

from copy import deepcopy
from typing import Any


OBSERVATION_ID = "WSLI-TRD-CAN-US-SURTAX-20260908-001"
EVIDENCE_IDS = (
    "WSEV-LI-CAN-FIN-USTARIFFS-20260825",
    "WSEV-LI-CAN-CBSA-SURTAX-20260907",
)
TARGET_VERSION = "0.11"
TARGET_OBSERVATION_COUNT = 10
TARGET_EVIDENCE_COUNT = 14
TARGET_POPULATION_STATE = "CONTROLLED_NORTH_AMERICA_TRADE_POLICY_IMPLEMENTATION_SPECIMEN"


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
        raise ValueError(f"CO duplicate {key}={value}")
    return matches[0] if matches else None


def target_live_schema(schema: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    target = plan["target_state"]
    if version_at_least(schema.get("version"), target["live_schema_version"]):
        checkpoint = schema.get("co_checkpoint") or {}
        if (
            checkpoint.get("observation_count") == target["live_observation_count"]
            and checkpoint.get("evidence_count") == target["live_evidence_count"]
        ):
            return deepcopy(schema)
        raise ValueError("CO descendant Live schema is at/above target without the CO checkpoint")

    pre = plan["pre_state"]
    if str(schema.get("version")) != pre["live_schema_version"]:
        raise ValueError("CO Live schema prestate drift")
    policy = schema.get("population_policy") or {}
    if policy.get("maximum_observation_count") != pre["live_observation_count"]:
        raise ValueError("CO Live observation policy ceiling drift")
    if policy.get("maximum_evidence_count") != pre["live_evidence_count"]:
        raise ValueError("CO Live evidence policy ceiling drift")

    correction_contract = deepcopy(schema.get("correction_conflict_policy"))
    if not isinstance(correction_contract, dict) or correction_contract.get("mode") != "FOUNDATION_CONTRACT_NO_PRODUCTION_SPECIMEN":
        raise ValueError("CO requires the merged CM correction/conflict contract")

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
        "reason": "CO adds exactly one pressure-audited Canadian counter-tariff implementation observation using two bounded primary-official evidence rows; U.S. response actions, Canonical creation, Monitor routing and Analysis remain outside the specimen."
    }

    guardrails = list(out.get("guardrails") or [])
    old_gate = "A tenth Live observation, production correction/conflict specimen, second production Live-to-Analysis link, further Analysis revision or additional Monitor activation requires another pressure audit."
    guardrails = [item for item in guardrails if item != old_gate]
    additions = [
        "CN v0.10 remains the frozen nine-observation/twelve-evidence checkpoint; CO is the separately pressure-audited tenth observation.",
        "CO v0.11 adds one PRIMARY_CONFIRMED Canada POLICY_DEVELOPMENT recording implementation of the United States Surtax Order (2026) from 8 September 2026, with zero Canonical links and two primary-official Canadian evidence rows.",
        "CO preserves the implementation event at CIVIL_DATE precision because the Department of Finance source's displayed 12:01 a.m. effective clock time is not accompanied by an established IANA timezone.",
        "CO records source-reported rates of 15%, 25% and 50% and a $27.6 billion covered import scope without implying that all covered imports face one rate or independently inferring the source currency.",
        "The separate U.S. presidential actions of 8 September 2026 are not collapsed into the Canadian sovereign observation; CO creates no bilateral story identity or conflict state merely because governments characterize the dispute differently.",
        "CO makes no independent legality/fairness judgment and no observed price, inflation, trade-flow, currency, equity or other market-effect claim.",
        "CO creates no Canonical occurrence, Source Registry authority, Monitor route or Analysis review; automatic ingestion, automatic Canonical commit, Google Calendar writes and public Live projection remain prohibited.",
        "CM correction/retraction/conflicting-report semantics remain unchanged and fully applicable in CO v0.11.",
        "An eleventh Live observation, U.S. response specimen, production correction/conflict specimen, second production Live-to-Analysis link, further Analysis revision or additional Monitor activation requires another pressure audit."
    ]
    for item in additions:
        if item not in guardrails:
            guardrails.append(item)
    out["guardrails"] = guardrails
    out["co_checkpoint"] = {
        "schema_version": target["live_schema_version"],
        "observations_version": target["live_schema_version"],
        "evidence_version": target["live_schema_version"],
        "population_state": TARGET_POPULATION_STATE,
        "observation_count": target["live_observation_count"],
        "evidence_count": target["live_evidence_count"],
        "canonical_linked_observation_count": target["canonical_linked_live_observation_count"],
        "base_main_sha": plan["exact_base_main_sha"],
        "historical_contract": "CO adds one bounded Canadian trade-policy implementation observation while keeping the distinct U.S. response outside the row and preserving all upstream/downstream write boundaries."
    }
    if out.get("correction_conflict_policy") != correction_contract:
        raise ValueError("CO mutated the CM correction/conflict policy")
    return out


def target_observations(dataset: dict[str, Any], payload: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    rows = dataset.get("observations") or []
    existing = _by_id(rows, "observation_id", OBSERVATION_ID)
    target = plan["target_state"]
    if existing is not None:
        if not version_at_least(dataset.get("version"), target["live_schema_version"]):
            raise ValueError("CO observation exists below target dataset version")
        return deepcopy(dataset)

    pre = plan["pre_state"]
    if str(dataset.get("version")) != pre["live_schema_version"] or len(rows) != pre["live_observation_count"]:
        raise ValueError("CO Live observations prestate drift")

    out = deepcopy(dataset)
    out["version"] = target["live_schema_version"]
    out["reference_date"] = plan["reference_date"]
    out["population_state"] = TARGET_POPULATION_STATE
    out["observations"].append(deepcopy(payload["live_observation"]))
    out["scope_note"] = "Bounded reviewed internal Live Intelligence store through CO: ten observations. CO adds one primary-confirmed Canadian counter-tariff implementation with zero Canonical links; separate U.S. response actions, causal attribution, market effects and story grouping remain outside the observation. Public projection and automatic ingestion remain closed."
    return out


def target_evidence(dataset: dict[str, Any], payload: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    rows = dataset.get("evidence") or []
    found = [_by_id(rows, "evidence_id", evidence_id) is not None for evidence_id in EVIDENCE_IDS]
    target = plan["target_state"]
    if any(found):
        if not all(found):
            raise ValueError("CO evidence is partially materialised")
        if not version_at_least(dataset.get("version"), target["live_schema_version"]):
            raise ValueError("CO evidence exists below target dataset version")
        return deepcopy(dataset)

    pre = plan["pre_state"]
    if str(dataset.get("version")) != pre["live_schema_version"] or len(rows) != pre["live_evidence_count"]:
        raise ValueError("CO Live evidence prestate drift")

    payload_rows = payload.get("live_evidence") or []
    payload_ids = tuple(row.get("evidence_id") for row in payload_rows)
    if payload_ids != EVIDENCE_IDS:
        raise ValueError("CO payload evidence identity/order drift")

    out = deepcopy(dataset)
    out["version"] = target["live_schema_version"]
    out["reference_date"] = plan["reference_date"]
    out["population_state"] = TARGET_POPULATION_STATE
    out["evidence"].extend(deepcopy(payload_rows))
    out["scope_note"] = "Evidence supports the bounded reviewed Live store through CO. CO adds two primary-official Canadian rows: Department of Finance tariff scope/effective-date evidence and CBSA operative border-application evidence. Neither supplies Canonical provenance, unattended-monitoring authority or Analysis conclusions."
    return out


def validate_co_contract(schema: dict[str, Any], observations: dict[str, Any], evidence: dict[str, Any], plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    target = plan["target_state"]
    rows = observations.get("observations") or []
    evidence_rows = evidence.get("evidence") or []
    obs = _by_id(rows, "observation_id", OBSERVATION_ID)
    evs = {evidence_id: _by_id(evidence_rows, "evidence_id", evidence_id) for evidence_id in EVIDENCE_IDS}

    if str(schema.get("version")) != target["live_schema_version"]:
        errors.append("CO schema version mismatch")
    if str(observations.get("version")) != target["live_schema_version"]:
        errors.append("CO observations version mismatch")
    if str(evidence.get("version")) != target["live_schema_version"]:
        errors.append("CO evidence version mismatch")
    if len(rows) != target["live_observation_count"]:
        errors.append("CO observation count mismatch")
    if len(evidence_rows) != target["live_evidence_count"]:
        errors.append("CO evidence count mismatch")
    if obs is None:
        errors.append("CO observation missing")
    for evidence_id, row in evs.items():
        if row is None:
            errors.append(f"CO evidence missing: {evidence_id}")

    if obs is not None:
        if obs.get("observation_type") != "POLICY_DEVELOPMENT":
            errors.append("CO observation type drift")
        if obs.get("verification_state") != "PRIMARY_CONFIRMED":
            errors.append("CO verification state drift")
        if obs.get("canonical_links") != []:
            errors.append("CO must remain zero-Canonical-link")
        if obs.get("revision_of_observation_id") is not None:
            errors.append("CO is not a Live correction/retraction")
        if "story_id" in obs:
            errors.append("CO must not manufacture a bilateral story identity")
        if obs.get("event_time") != {"precision": "CIVIL_DATE", "event_date": "2026-09-08"}:
            errors.append("CO event time must remain 8 September CIVIL_DATE")
        if obs.get("jurisdictions") != ["Canada"]:
            errors.append("CO jurisdiction must remain the Canadian sovereign act")
        if obs.get("regions") != ["North America"]:
            errors.append("CO region drift")
        if obs.get("domain_tags") != ["TRADE", "ECONOMICS", "GEOPOLITICS"]:
            errors.append("CO domain-tag drift")
        if obs.get("automatic_canonical_commit") is not False or obs.get("google_calendar_write") is not False:
            errors.append("CO write gates opened")
        summary = str(obs.get("summary") or "").lower()
        required_phrases = (
            "does not promote",
            "does not imply",
            "does not fold",
            "does not independently adjudicate",
            "does not claim",
        )
        for phrase in required_phrases:
            if phrase not in summary:
                errors.append(f"CO claim-boundary caveat missing: {phrase}")

    expected_publications = {
        EVIDENCE_IDS[0]: {"precision": "CIVIL_DATE", "published_date": "2026-08-25"},
        EVIDENCE_IDS[1]: {"precision": "CIVIL_DATE", "published_date": "2026-09-07"},
    }
    for evidence_id, row in evs.items():
        if row is None:
            continue
        if row.get("evidence_class") != "PRIMARY_OFFICIAL":
            errors.append(f"CO evidence must remain PRIMARY_OFFICIAL: {evidence_id}")
        if row.get("canonical_provenance_effect") != "NONE":
            errors.append(f"CO evidence acquired Canonical provenance authority: {evidence_id}")
        if row.get("publication_time") != expected_publications[evidence_id]:
            errors.append(f"CO publication-time drift: {evidence_id}")

    policy = schema.get("population_policy") or {}
    if policy.get("maximum_observation_count") != target["live_observation_count"]:
        errors.append("CO observation ceiling mismatch")
    if policy.get("maximum_evidence_count") != target["live_evidence_count"]:
        errors.append("CO evidence ceiling mismatch")
    if policy.get("automatic_ingestion_allowed") is not False or policy.get("public_observation_projection_allowed") is not False:
        errors.append("CO public/automatic Live gates opened")

    cm = schema.get("correction_conflict_policy") or {}
    if cm.get("mode") != "FOUNDATION_CONTRACT_NO_PRODUCTION_SPECIMEN":
        errors.append("CO weakened CM correction/conflict mode")
    if cm.get("minimum_unique_conflict_evidence_refs") != 2 or cm.get("minimum_distinct_conflict_providers") != 2:
        errors.append("CO weakened CM conflict evidence plurality")
    if cm.get("corrected_or_retracted_requires_correction_evidence") is not True:
        errors.append("CO weakened CM correction evidence gate")

    return errors
