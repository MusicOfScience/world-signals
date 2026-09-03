from __future__ import annotations

from collections import Counter
from typing import Any


def _count(values: list[Any]) -> dict[str, int]:
    counts = Counter(str(value) if value not in (None, "") else "NOT_RECORDED_IN_REGISTRY" for value in values)
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _recorded_observation_times(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(child, str) and (key == "observed_at" or key.endswith("_observed_at")):
                found.append(child)
            else:
                found.extend(_recorded_observation_times(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_recorded_observation_times(child))
    return found


def operations_projection(
    registry: dict,
    sources: dict,
    expectations: dict,
    policy: dict,
    changes: dict,
) -> dict:
    """Build a browser-safe read-only operations projection.

    The projection deliberately distinguishes configured monitor routes and recorded
    repository evidence from current runtime health. It never infers source health
    from a static build and never exposes a browser mutation path.
    """

    source_records = sources.get("sources", [])
    source_map = {source.get("source_id"): source for source in source_records}
    routes = []

    for route in expectations.get("adapters", []):
        source = source_map.get(route.get("source_id"), {})
        times = sorted(set(_recorded_observation_times(route)))
        routes.append(
            {
                "adapter_id": route.get("adapter_id"),
                "source_id": route.get("source_id"),
                "source_institution": source.get("institution"),
                "jurisdiction": source.get("jurisdiction"),
                "domain": source.get("domain"),
                "monitor_role": route.get("monitor_role"),
                "cadence": route.get("cadence"),
                "canonical_occurrence_ids": route.get("canonical_occurrence_ids", []),
                "last_recorded_evidence_at": times[-1] if times else None,
                "recorded_evidence_timestamps": times,
                "source_failure_policy": route.get("source_failure_policy"),
                "automatic_commit_allowed": False,
                "canonical_provenance_use": source.get("canonical_provenance_use"),
                "automated_monitoring_use": source.get("automated_monitoring_use"),
                "verification_mode": source.get("verification_mode"),
                "monitoring_readiness_status": source.get("monitoring_readiness_status"),
                "rights_reviewed_at": source.get("rights_reviewed_at"),
                "last_successful_research_verification_at": source.get("last_successful_research_verification_at"),
            }
        )

    browser_sources = []
    for source in source_records:
        browser_sources.append(
            {
                "source_id": source.get("source_id"),
                "institution": source.get("institution"),
                "jurisdiction": source.get("jurisdiction"),
                "domain": source.get("domain"),
                "source_type": source.get("source_type"),
                "authoritative_url": source.get("authoritative_url"),
                "canonical_provenance_use": source.get("canonical_provenance_use"),
                "automated_monitoring_use": source.get("automated_monitoring_use"),
                "verification_mode": source.get("verification_mode"),
                "monitoring_readiness_status": source.get("monitoring_readiness_status"),
                "rights_reviewed_at": source.get("rights_reviewed_at"),
                "last_successful_research_verification_at": source.get("last_successful_research_verification_at"),
                "machine_readable_available": source.get("machine_readable_available"),
                "endpoint_role": source.get("endpoint_role"),
            }
        )

    architecture = policy.get("architecture_boundary", {})
    auto_gate = policy.get("canonical_auto_commit_gate", {})
    evidence = policy.get("evidence", {})
    candidate_policy = policy.get("review_candidate_lifecycle", {})
    health_policy = policy.get("source_health", {})

    return {
        "metadata": {
            "projection_type": "STATIC_RECORDED_OPERATIONS_STATE_NOT_CURRENT_RUNTIME_HEALTH",
            "canonical_registry_version": registry.get("version"),
            "canonical_record_count": registry.get("record_count"),
            "source_registry_version": sources.get("version"),
            "source_count": len(source_records),
            "monitor_expectations_version": expectations.get("version"),
            "monitor_operations_policy_version": policy.get("version"),
            "configured_monitor_route_count": len(routes),
            "reviewed_change_count": len(changes.get("changes", [])),
            "runtime_health_embedded": False,
            "pending_review_queue_embedded": False,
            "automatic_canonical_commit": False,
            "google_calendar_write": False,
        },
        "governance": {
            "architecture_boundary": architecture,
            "run_status_vocabulary": policy.get("run_status_vocabulary", []),
            "source_health_states": health_policy.get("per_run_states", []),
            "source_health_rules": health_policy.get("rules", []),
            "review_candidate_states": candidate_policy.get("states", []),
            "artifact_retention_days": evidence.get("artifact_retention_days"),
            "canonical_auto_commit_gate": {
                "state": auto_gate.get("state"),
                "remaining_real_world_evidence": auto_gate.get("remaining_real_world_evidence", []),
            },
        },
        "source_governance_summary": {
            "canonical_provenance_use": _count([s.get("canonical_provenance_use") for s in source_records]),
            "automated_monitoring_use": _count([s.get("automated_monitoring_use") for s in source_records]),
            "verification_mode": _count([s.get("verification_mode") for s in source_records]),
            "monitoring_readiness_status": _count([s.get("monitoring_readiness_status") for s in source_records]),
        },
        "configured_routes": routes,
        "sources": browser_sources,
    }
