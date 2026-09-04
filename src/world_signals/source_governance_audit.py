from __future__ import annotations

from collections import Counter


GOVERNANCE_FIELDS = (
    "canonical_provenance_use",
    "automated_monitoring_use",
    "verification_mode",
    "monitoring_readiness_status",
)


def _missing(source: dict, field: str) -> bool:
    return source.get(field) in (None, "")


def build_source_governance_audit(
    registry: dict,
    source_registry: dict,
    expectations: dict,
) -> dict:
    """Describe source-governance completeness without inferring permissions.

    Priority is based only on operational dependency:
    P0 = configured monitor source with at least one missing governance field;
    P1 = canonical dependency with at least one missing governance field;
    P2 = source-registry record with missing fields but no current canonical or
         configured-monitor dependency.

    The audit never derives rights from machine readability, domain, transport,
    source authority or successful monitoring.
    """
    sources = list(source_registry.get("sources", []))
    canonical_counts = Counter(
        record.get("source_id")
        for record in registry.get("records", [])
        if record.get("source_id")
    )
    monitor_counts = Counter(
        adapter.get("source_id")
        for adapter in expectations.get("adapters", [])
        if adapter.get("source_id")
    )

    missing_field_counts = Counter()
    readiness_counts = Counter()
    explicit_complete = 0
    rows = []

    for source in sources:
        source_id = source.get("source_id")
        missing_fields = [field for field in GOVERNANCE_FIELDS if _missing(source, field)]
        for field in missing_fields:
            missing_field_counts[field] += 1
        readiness_counts[str(source.get("monitoring_readiness_status") or "NOT_RECORDED_IN_REGISTRY")] += 1
        if not missing_fields:
            explicit_complete += 1
            continue

        canonical_count = canonical_counts.get(source_id, 0)
        monitor_count = monitor_counts.get(source_id, 0)
        priority = "P0_CONFIGURED_MONITOR_DEPENDENCY" if monitor_count else (
            "P1_CANONICAL_DEPENDENCY" if canonical_count else "P2_REGISTRY_ONLY"
        )
        rows.append({
            "source_id": source_id,
            "institution": source.get("institution"),
            "jurisdiction": source.get("jurisdiction"),
            "domain": source.get("domain"),
            "source_type": source.get("source_type"),
            "canonical_occurrence_dependency_count": canonical_count,
            "configured_monitor_route_count": monitor_count,
            "machine_readable_available": source.get("machine_readable_available"),
            "existing_monitoring_readiness_status": source.get("monitoring_readiness_status"),
            "missing_governance_fields": missing_fields,
            "research_priority": priority,
            "permission_inference": "PROHIBITED_BY_AUDIT_METHOD",
        })

    priority_order = {
        "P0_CONFIGURED_MONITOR_DEPENDENCY": 0,
        "P1_CANONICAL_DEPENDENCY": 1,
        "P2_REGISTRY_ONLY": 2,
    }
    rows.sort(key=lambda row: (
        priority_order[row["research_priority"]],
        -row["configured_monitor_route_count"],
        -row["canonical_occurrence_dependency_count"],
        str(row.get("source_id") or ""),
    ))

    priority_counts = Counter(row["research_priority"] for row in rows)
    canonical_source_ids = set(canonical_counts)
    monitor_source_ids = set(monitor_counts)

    return {
        "project": "WORLD SIGNALS",
        "dataset": "SOURCE_GOVERNANCE_COMPLETENESS_AUDIT",
        "version": "0.1",
        "canonical_registry_version": registry.get("version"),
        "source_registry_version": source_registry.get("version"),
        "monitor_expectations_version": expectations.get("version"),
        "methodology": {
            "purpose": "Prioritize explicit source-governance research/backfill; do not infer permission.",
            "permission_inference_from_machine_readability_prohibited": True,
            "permission_inference_from_public_access_prohibited": True,
            "permission_inference_from_official_domain_prohibited": True,
            "permission_inference_from_successful_parser_prohibited": True,
            "canonical_factual_provenance_separate_from_automated_monitoring": True,
            "priority_is_operational_dependency_not_importance": True,
        },
        "totals": {
            "source_count": len(sources),
            "fully_explicit_governance_source_count": explicit_complete,
            "source_records_with_one_or_more_missing_governance_fields": len(rows),
            "unique_sources_used_by_canonical_registry": len(canonical_source_ids),
            "unique_sources_used_by_configured_monitor": len(monitor_source_ids),
            "missing_field_counts": dict(sorted(missing_field_counts.items())),
            "backfill_research_priority_counts": dict(sorted(priority_counts.items())),
            "monitoring_readiness_status_counts": dict(sorted(readiness_counts.items())),
        },
        "backfill_research_queue": rows,
        "decision_rule": "Audit output ranks research attention only. Every substantive governance value requires direct evidence or an explicitly conservative not-audited/hold state allowed by the source contract; this audit never supplies that value automatically.",
    }
