from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass(frozen=True)
class LiveIntelligenceValidationReport:
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def _exact_utc(raw: Any) -> datetime | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (TypeError, ValueError, AttributeError):
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        return None
    return parsed.astimezone(timezone.utc)


def _civil_date(raw: Any) -> date | None:
    if not isinstance(raw, str):
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def _local_datetime(raw: Any) -> datetime | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        parsed = datetime.fromisoformat(raw)
    except (TypeError, ValueError, AttributeError):
        return None
    if parsed.tzinfo is not None:
        return None
    return parsed


def _iana_timezone(raw: Any) -> ZoneInfo | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        return ZoneInfo(raw)
    except (ZoneInfoNotFoundError, ValueError):
        return None


def _all_keys(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            found.add(str(key))
            found.update(_all_keys(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_all_keys(child))
    return found


def _cycle_in_revision_graph(observations: list[dict[str, Any]]) -> bool:
    parent = {
        row.get("observation_id"): row.get("revision_of_observation_id")
        for row in observations
        if row.get("observation_id") and row.get("revision_of_observation_id")
    }
    for start in parent:
        seen: set[str] = set()
        current = start
        while current in parent:
            if current in seen:
                return True
            seen.add(current)
            current = parent[current]
    return False


def validate_live_intelligence(
    schema: dict[str, Any],
    evidence_registry: dict[str, Any],
    observations_dataset: dict[str, Any],
    canonical_registry: dict[str, Any],
) -> LiveIntelligenceValidationReport:
    errors: list[str] = []

    if schema.get("architecture_position") != "LIVE_INTELLIGENCE":
        errors.append("Live Intelligence schema architecture_position must be LIVE_INTELLIGENCE")

    boundary = schema.get("layer_boundary") or {}
    required_false = (
        "canonical_mutation_allowed",
        "calendar_mutation_allowed",
        "source_monitor_mutation_allowed",
        "analysis_mutation_allowed",
        "causal_interpretation_allowed",
        "market_move_attribution_allowed",
        "live_evidence_may_resolve_missing_canonical_time",
        "source_failure_or_absence_may_create_live_fact",
    )
    for key in required_false:
        if boundary.get(key) is not False:
            errors.append(f"Live Intelligence boundary must keep {key}=false")
    if boundary.get("observation_may_link_zero_or_more_canonical_occurrences") is not True:
        errors.append("Live Intelligence must permit optional canonical links")
    if boundary.get("unscheduled_observation_without_canonical_occurrence_allowed") is not True:
        errors.append("Live Intelligence must permit unscheduled observations without canonical IDs")

    monitor_bridge = schema.get("monitor_bridge_policy") or {}
    if monitor_bridge.get("automatic_promotion_from_monitor_candidate") is not False:
        errors.append("Live Intelligence must prohibit automatic promotion from monitor candidates")
    if monitor_bridge.get("positive_monitor_evidence_requires_separate_live_evidence_record") is not True:
        errors.append("Live Intelligence monitor bridge must require separate live evidence")
    if monitor_bridge.get("monitor_review_candidate_is_not_live_intelligence_observation") is not True:
        errors.append("Monitor review candidates must remain distinct from Live Intelligence observations")

    grouping = schema.get("story_grouping_policy") or {}
    if grouping.get("automatic_clustering_allowed") is not False:
        errors.append("Live Intelligence v0.1 must prohibit automatic story clustering")
    if grouping.get("future_story_identity_requires_pressure_audited_contract") is not True:
        errors.append("Future Live Intelligence story identity must require a pressure-audited contract")

    foundation = schema.get("foundation_population_policy") or {}
    observations = observations_dataset.get("observations") or []
    evidence = evidence_registry.get("evidence") or []
    if foundation.get("production_population_allowed") is False and observations:
        errors.append("Live Intelligence v0.1 foundation prohibits production observation population")
    if foundation.get("evidence_population_allowed") is False and evidence:
        errors.append("Live Intelligence v0.1 foundation prohibits evidence population")
    if foundation.get("existing_analysis_evidence_migration_allowed") is not False:
        errors.append("Live Intelligence foundation must prohibit retrospective Analysis-evidence migration")
    if foundation.get("public_observation_projection_allowed") is not False:
        errors.append("Live Intelligence foundation must not claim a public live observation feed")

    schema_version = schema.get("version")
    if evidence_registry.get("version") != schema_version:
        errors.append("Live Intelligence evidence version must match schema version")
    if observations_dataset.get("version") != schema_version:
        errors.append("Live Intelligence observations version must match schema version")

    vocab = schema.get("controlled_vocabularies") or {}
    allowed_evidence_classes = set(vocab.get("evidence_class") or [])
    allowed_evidence_roles = set(vocab.get("evidence_role") or [])
    allowed_observation_types = set(vocab.get("observation_type") or [])
    allowed_verification_states = set(vocab.get("verification_state") or [])
    allowed_domains = set(vocab.get("domain_tag") or [])
    allowed_relationships = set(vocab.get("canonical_relationship") or [])
    allowed_time_precision = set(vocab.get("event_time_precision") or [])
    required_evidence_fields = set(schema.get("required_evidence_fields") or [])
    required_observation_fields = set(schema.get("required_observation_fields") or [])
    prohibited_analysis_fields = set(schema.get("prohibited_analysis_fields") or [])

    evidence_by_id: dict[str, dict[str, Any]] = {}
    for row in evidence:
        missing = sorted(field for field in required_evidence_fields if field not in row)
        evidence_id = row.get("evidence_id") or "<missing-evidence-id>"
        if missing:
            errors.append(f"{evidence_id}: missing evidence fields {missing}")
        if not row.get("evidence_id"):
            continue
        if evidence_id in evidence_by_id:
            errors.append(f"duplicate Live Intelligence evidence_id {evidence_id}")
        evidence_by_id[evidence_id] = row
        if row.get("evidence_class") not in allowed_evidence_classes:
            errors.append(f"{evidence_id}: invalid evidence_class {row.get('evidence_class')}")
        roles = row.get("roles") or []
        if not roles or any(role not in allowed_evidence_roles for role in roles):
            errors.append(f"{evidence_id}: invalid or empty evidence roles")
        if not str(row.get("provider") or "").strip():
            errors.append(f"{evidence_id}: provider required")
        if not str(row.get("title") or "").strip():
            errors.append(f"{evidence_id}: title required")
        if not str(row.get("url") or "").strip():
            errors.append(f"{evidence_id}: url required")
        if row.get("canonical_provenance_effect") != "NONE":
            errors.append(f"{evidence_id}: live evidence cannot alter canonical provenance")

    canonical_ids = {
        row.get("occurrence_id")
        for row in canonical_registry.get("records", [])
        if row.get("occurrence_id")
    }
    observation_ids = [row.get("observation_id") for row in observations if row.get("observation_id")]
    observation_id_set = set(observation_ids)
    if len(observation_ids) != len(observation_id_set):
        errors.append("duplicate Live Intelligence observation_id")

    for row in observations:
        observation_id = row.get("observation_id") or "<missing-observation-id>"
        missing = sorted(field for field in required_observation_fields if field not in row)
        if missing:
            errors.append(f"{observation_id}: missing observation fields {missing}")

        if _exact_utc(row.get("observed_at_utc")) is None:
            errors.append(f"{observation_id}: observed_at_utc must be an exact UTC timestamp")
        if row.get("observation_type") not in allowed_observation_types:
            errors.append(f"{observation_id}: invalid observation_type {row.get('observation_type')}")
        if row.get("verification_state") not in allowed_verification_states:
            errors.append(f"{observation_id}: invalid verification_state {row.get('verification_state')}")
        if not str(row.get("headline") or "").strip():
            errors.append(f"{observation_id}: headline required")
        if not str(row.get("summary") or "").strip():
            errors.append(f"{observation_id}: summary required")

        domains = row.get("domain_tags") or []
        if not domains or any(tag not in allowed_domains for tag in domains):
            errors.append(f"{observation_id}: invalid or empty domain_tags")
        if not isinstance(row.get("jurisdictions"), list):
            errors.append(f"{observation_id}: jurisdictions must be a list")
        if not isinstance(row.get("regions"), list):
            errors.append(f"{observation_id}: regions must be a list")

        refs = row.get("evidence_refs") or []
        if not refs:
            errors.append(f"{observation_id}: at least one evidence_ref required")
        for ref in refs:
            if ref not in evidence_by_id:
                errors.append(f"{observation_id}: unknown evidence_ref {ref}")

        links = row.get("canonical_links")
        if not isinstance(links, list):
            errors.append(f"{observation_id}: canonical_links must be a list")
        else:
            for link in links:
                occurrence_id = link.get("occurrence_id") if isinstance(link, dict) else None
                relationship = link.get("relationship") if isinstance(link, dict) else None
                if occurrence_id not in canonical_ids:
                    errors.append(f"{observation_id}: unknown canonical occurrence {occurrence_id}")
                if relationship not in allowed_relationships:
                    errors.append(f"{observation_id}: invalid canonical relationship {relationship}")

        revision_ref = row.get("revision_of_observation_id")
        if revision_ref is not None and revision_ref not in observation_id_set:
            errors.append(f"{observation_id}: unknown revision_of_observation_id {revision_ref}")
        if revision_ref == observation_id and revision_ref is not None:
            errors.append(f"{observation_id}: observation cannot revise itself")
        if row.get("observation_type") == "DATA_REVISION":
            if not str(row.get("revision_target_description") or "").strip():
                errors.append(f"{observation_id}: DATA_REVISION requires revision_target_description")
            revision_evidence = [
                evidence_by_id[ref]
                for ref in refs
                if ref in evidence_by_id
                and "CORRECTION_OR_REVISION" in (evidence_by_id[ref].get("roles") or [])
            ]
            if not revision_evidence:
                errors.append(
                    f"{observation_id}: DATA_REVISION requires evidence with CORRECTION_OR_REVISION role"
                )
        if row.get("verification_state") in {"CORRECTED", "RETRACTED"} and not revision_ref:
            errors.append(f"{observation_id}: corrected/retracted live observation requires revision reference")

        event_time = row.get("event_time")
        if event_time is not None:
            if not isinstance(event_time, dict):
                errors.append(f"{observation_id}: event_time must be an object when supplied")
            else:
                precision = event_time.get("precision")
                if precision not in allowed_time_precision:
                    errors.append(f"{observation_id}: invalid event_time precision {precision}")
                if precision == "EXACT_TIMESTAMP":
                    event_utc = _exact_utc(event_time.get("event_at_utc"))
                    if event_utc is None:
                        errors.append(f"{observation_id}: exact event_time requires event_at_utc in UTC")
                    local_raw = event_time.get("event_local")
                    timezone_raw = event_time.get("event_timezone")
                    if (local_raw is None) != (timezone_raw is None):
                        errors.append(
                            f"{observation_id}: event_local and event_timezone must be supplied together"
                        )
                    if local_raw is not None and timezone_raw is not None:
                        local_dt = _local_datetime(local_raw)
                        zone = _iana_timezone(timezone_raw)
                        if local_dt is None:
                            errors.append(
                                f"{observation_id}: event_local must be an offset-free ISO local datetime"
                            )
                        if zone is None:
                            errors.append(f"{observation_id}: event_timezone must be a valid IANA timezone")
                        if local_dt is not None and zone is not None and event_utc is not None:
                            resolved_utc = local_dt.replace(tzinfo=zone).astimezone(timezone.utc)
                            if resolved_utc != event_utc:
                                errors.append(
                                    f"{observation_id}: event_local/event_timezone do not match event_at_utc"
                                )
                elif precision == "CIVIL_DATE":
                    if _civil_date(event_time.get("event_date")) is None:
                        errors.append(f"{observation_id}: civil event_time requires YYYY-MM-DD event_date")
                    if event_time.get("event_at_utc") is not None:
                        errors.append(f"{observation_id}: civil date must not be upgraded to event_at_utc")
                elif precision == "RANGE":
                    start = _exact_utc(event_time.get("start_utc"))
                    end = _exact_utc(event_time.get("end_utc"))
                    if start is None or end is None or end < start:
                        errors.append(f"{observation_id}: range event_time requires ordered UTC start/end")
                elif precision == "UNKNOWN":
                    precise_keys = {"event_at_utc", "event_date", "start_utc", "end_utc"}
                    if any(event_time.get(key) is not None for key in precise_keys):
                        errors.append(f"{observation_id}: UNKNOWN event_time may not carry precise time fields")

        forbidden_found = prohibited_analysis_fields.intersection(_all_keys(row))
        if forbidden_found:
            errors.append(
                f"{observation_id}: Analysis-only fields prohibited in Live Intelligence: {sorted(forbidden_found)}"
            )
        if row.get("automatic_canonical_commit") is not False:
            errors.append(f"{observation_id}: automatic_canonical_commit must remain false")
        if row.get("google_calendar_write") is not False:
            errors.append(f"{observation_id}: google_calendar_write must remain false")

    if _cycle_in_revision_graph(observations):
        errors.append("Live Intelligence revision graph contains a cycle")

    return LiveIntelligenceValidationReport(tuple(errors))


def public_live_intelligence_projection(
    schema: dict[str, Any],
    evidence_registry: dict[str, Any],
    observations_dataset: dict[str, Any],
    canonical_registry: dict[str, Any],
) -> dict[str, Any]:
    report = validate_live_intelligence(schema, evidence_registry, observations_dataset, canonical_registry)
    if not report.ok:
        raise ValueError("invalid Live Intelligence state: " + "; ".join(report.errors))

    policy = schema.get("public_projection_policy") or {}
    observations = observations_dataset.get("observations") or []
    evidence = evidence_registry.get("evidence") or []
    projection_allowed = policy.get("observation_projection_allowed") is True

    return {
        "metadata": {
            "projection_type": "LIVE_INTELLIGENCE_FOUNDATION_NOT_RUNTIME_FEED",
            "schema_version": schema.get("version"),
            "observations_version": observations_dataset.get("version"),
            "evidence_version": evidence_registry.get("version"),
            "population_state": observations_dataset.get("population_state"),
            "internal_observation_count": len(observations),
            "internal_evidence_count": len(evidence),
            "public_observation_count": len(observations) if projection_allowed else 0,
            "canonical_registry_version_at_build": canonical_registry.get("version"),
            "canonical_record_count_at_build": len(canonical_registry.get("records", [])),
            "runtime_feed_claim": False,
            "automatic_canonical_commit": False,
            "google_calendar_write": False,
        },
        "observations": observations if projection_allowed else [],
    }
