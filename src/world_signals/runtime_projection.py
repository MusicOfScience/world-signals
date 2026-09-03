from __future__ import annotations

from typing import Any


ALLOWED_REPORT_STATUSES={"NO_CHANGE","REVIEW_REQUIRED","DEGRADED","FAIL_CANONICAL_GUARD"}


def _layer_states(health: dict) -> list[dict]:
    layers=health.get("layers") or {}
    out=[]
    for name, payload in sorted(layers.items()):
        if isinstance(payload,dict):
            out.append({
                "layer":name,
                "state":payload.get("state"),
                "failure_stage":payload.get("failure_stage"),
            })
    return out


def _candidate_type(candidate: dict) -> str | None:
    return candidate.get("candidate_type") or candidate.get("diff_type")


def _candidate_occurrence_ids(candidate: dict) -> list[str]:
    if candidate.get("occurrence_ids"):
        return list(candidate.get("occurrence_ids") or [])
    if candidate.get("occurrence_id"):
        return [candidate["occurrence_id"]]
    return []


def _candidate_source_id(candidate: dict) -> str | None:
    if candidate.get("source_id"):
        return candidate["source_id"]
    assertion=candidate.get("source_assertion") or {}
    return assertion.get("source_id")


def _changed_fields(candidate: dict) -> list[str]:
    old=candidate.get("old_value") or {}
    new=candidate.get("new_value") or {}
    if not isinstance(old,dict) or not isinstance(new,dict):
        return []
    keys=sorted(set(old)|set(new))
    return [key for key in keys if old.get(key)!=new.get(key)]


def _assert_candidate_safe(candidate: dict) -> None:
    if candidate.get("automatic_commit_allowed") is not False:
        raise ValueError(f"review candidate {candidate.get('candidate_id')} does not explicitly prohibit automatic commit")
    if not candidate.get("candidate_id"):
        raise ValueError("review candidate missing candidate_id")


def _alignment(report: dict,current: dict) -> dict:
    comparisons={
        "canonical_registry_version":(
            str(report.get("canonical_registry_version")),
            str(current.get("canonical_registry_version")),
        ),
        "source_registry_version":(
            str(report.get("source_registry_version")),
            str(current.get("source_registry_version")),
        ),
        "monitor_expectations_version":(
            str(report.get("monitor_expectations_version")),
            str(current.get("monitor_expectations_version")),
        ),
        "monitor_operations_policy_version":(
            str(report.get("monitor_operations_policy_version")),
            str(current.get("monitor_operations_policy_version")),
        ),
    }
    fields={
        key:{"run":run,"current":cur,"matches":run==cur}
        for key,(run,cur) in comparisons.items()
    }
    return {
        "state":"ALIGNED_WITH_CURRENT_SITE" if all(value["matches"] for value in fields.values()) else "STALE_RELATIVE_TO_CURRENT_SITE",
        "fields":fields,
    }


def public_runtime_projection(report: dict,manifest: dict,candidates: list[dict],current: dict) -> dict:
    """Sanitize one retained monitor run for public static presentation.

    No raw snapshots, parser errors, observations, legal/source payloads or candidate
    old/new values are copied. The result is a dated evidence summary, never a
    claim of current source health.
    """
    status=report.get("status")
    if status not in ALLOWED_REPORT_STATUSES:
        raise ValueError(f"unsupported monitor status: {status}")
    if report.get("automatic_canonical_commit") is not False:
        raise ValueError("monitor report does not explicitly prohibit automatic canonical commit")
    if report.get("google_calendar_write") is not False:
        raise ValueError("monitor report does not explicitly prohibit Google Calendar writes")
    if report.get("canonical_unchanged") is not True:
        raise ValueError("monitor report failed canonical unchanged guard")

    report_count=int(report.get("candidate_count",len(report.get("review_candidates") or [])))
    manifest_count=int(manifest.get("candidate_count",len(candidates)))
    if report_count!=manifest_count or manifest_count!=len(candidates):
        raise ValueError(
            f"candidate count mismatch report={report_count} manifest={manifest_count} files={len(candidates)}"
        )
    if manifest.get("automatic_canonical_commit") is not False:
        raise ValueError("candidate manifest does not explicitly prohibit automatic commit")

    sanitized_candidates=[]
    for candidate in candidates:
        _assert_candidate_safe(candidate)
        sanitized_candidates.append({
            "candidate_id":candidate.get("candidate_id"),
            "candidate_type":_candidate_type(candidate),
            "source_id":_candidate_source_id(candidate),
            "occurrence_ids":_candidate_occurrence_ids(candidate),
            "review_state":candidate.get("review_state") or "PENDING_REVIEW",
            "candidate_origin":candidate.get("candidate_origin") or "LIVE_READ_ONLY_MONITOR",
            "changed_fields":_changed_fields(candidate),
            "automatic_commit_allowed":False,
        })

    source_health=[]
    for health in report.get("source_health") or []:
        source_health.append({
            "adapter_id":health.get("adapter_id"),
            "source_id":health.get("source_id"),
            "state":health.get("state"),
            "layer_states":_layer_states(health),
        })

    health_summary=report.get("source_health_summary") or {}
    context=report.get("workflow_context") or {}
    return {
        "availability":"AVAILABLE",
        "projection_type":"DATED_RECORDED_MONITOR_RUN_NOT_CURRENT_HEALTH",
        "run_at":report.get("run_at"),
        "status":status,
        "github_run_id":context.get("github_run_id"),
        "github_sha":context.get("github_sha"),
        "report_schema_version":report.get("report_schema_version"),
        "canonical_registry_version":report.get("canonical_registry_version"),
        "source_registry_version":report.get("source_registry_version"),
        "monitor_expectations_version":report.get("monitor_expectations_version"),
        "monitor_operations_policy_version":report.get("monitor_operations_policy_version"),
        "configuration_fingerprint_sha256":report.get("configuration_fingerprint_sha256"),
        "canonical_unchanged":True,
        "automatic_canonical_commit":False,
        "google_calendar_write":False,
        "healthy_adapter_count":int(health_summary.get("healthy",0)),
        "degraded_adapter_count":int(health_summary.get("degraded",0)),
        "candidate_count":len(sanitized_candidates),
        "all_expected_adapters_observed":bool(health_summary.get("all_expected_adapters_observed",False)),
        "configuration_alignment":_alignment(report,current),
        "source_health":source_health,
        "candidates":sanitized_candidates,
    }


def unavailable_runtime_projection(reason: str,current: dict) -> dict:
    return {
        "availability":"UNAVAILABLE_AT_BUILD",
        "projection_type":"NO_RETAINED_RUNTIME_ARTIFACT_EMBEDDED",
        "reason":reason,
        "current_configuration":current,
        "automatic_canonical_commit":False,
        "google_calendar_write":False,
        "source_health":[],
        "candidates":[],
    }


def prohibited_field_hits(value: Any,prohibited: set[str],path: str="$") -> list[str]:
    hits=[]
    if isinstance(value,dict):
        for key,child in value.items():
            child_path=f"{path}.{key}"
            if key in prohibited:
                hits.append(child_path)
            hits.extend(prohibited_field_hits(child,prohibited,child_path))
    elif isinstance(value,list):
        for index,child in enumerate(value):
            hits.extend(prohibited_field_hits(child,prohibited,f"{path}[{index}]"))
    return hits
