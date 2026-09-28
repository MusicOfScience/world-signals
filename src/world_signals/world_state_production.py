"""Read-only access to admitted World State history.

This module is deliberately downstream of the Step 3 evidence reader.  It
selects immutable production component and snapshot revisions, derives
query-relative freshness, computes non-narrative deltas, and exposes a
structured internal briefing view.  It never proposes, admits, updates, or
publishes a World State revision.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from .world_state_admission import load_production_state, validate_production_state
from .world_state_history import (
    DIMENSIONS,
    QUERY_MODES,
    WorldStateHistoryError,
    select_component_revisions,
    validate_history_query,
)
from .world_state_composition import build_composition_view


ROOT = Path(__file__).resolve().parents[2]
FRESHNESS_STATES = {
    "CURRENT",
    "REVIEW_DUE_SOON",
    "REVIEW_DUE",
    "STALE_REVIEW_REQUIRED",
    "NO_FRESHNESS_POLICY",
    "UNKNOWN",
}
CURRENT_USE_STATES = {
    "CURRENTLY_USABLE_WITHIN_SCOPE",
    "CURRENT_WITH_REVIEW_DUE_SOON",
    "CURRENT_USE_REQUIRES_REVIEW",
    "NO_CURRENTNESS_CLAIM",
    "UNKNOWN",
}
REVIEW_DUE_SOON_WINDOW_DAYS = 7


class WorldStateProductionReadError(ValueError):
    """Raised when a production-history read cannot be made safely."""


def _compact(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def semantic_fingerprint(value: Any) -> str:
    return hashlib.sha256(_compact(value).encode("utf-8")).hexdigest()


def _parse_utc(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or len(value) != 20 or not value.endswith("Z"):
        raise WorldStateProductionReadError(f"{field} must be exact UTC ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise WorldStateProductionReadError(f"{field} is not valid UTC") from exc
    if parsed.tzinfo != timezone.utc:
        raise WorldStateProductionReadError(f"{field} must be UTC")
    return parsed


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_production_read_request(request: Any) -> dict[str, Any]:
    """Validate the explicit production-history query contract."""
    if not isinstance(request, dict):
        raise WorldStateProductionReadError("production read request must be an object")
    required = {
        "query_mode",
        "knowledge_cutoff_utc",
        "effective_as_of_utc",
        "scope",
        "include_withdrawn_history",
    }
    if set(request) != required:
        raise WorldStateProductionReadError(
            f"production read request keys mismatch; missing={sorted(required - set(request))} "
            f"extra={sorted(set(request) - required)}"
        )
    if request["query_mode"] not in QUERY_MODES:
        raise WorldStateProductionReadError("query_mode must be KNOWLEDGE_AS_OF or EFFECTIVE_AS_OF")
    knowledge = _parse_utc(request["knowledge_cutoff_utc"], "knowledge_cutoff_utc")
    effective_value = request["effective_as_of_utc"]
    effective = None
    if request["query_mode"] == "EFFECTIVE_AS_OF":
        effective = _parse_utc(effective_value, "effective_as_of_utc")
    elif effective_value is not None:
        _parse_utc(effective_value, "effective_as_of_utc")
    if not isinstance(request["scope"], dict):
        raise WorldStateProductionReadError("scope must be an object")
    scope = request["scope"]
    allowed_scope = {"jurisdictions", "dimensions", "systems", "component_ids"}
    if set(scope) - allowed_scope:
        raise WorldStateProductionReadError("scope contains unsupported keys")
    normalized_scope: dict[str, list[str]] = {}
    for key in sorted(allowed_scope):
        values = scope.get(key, [])
        if not isinstance(values, list) or any(not isinstance(value, str) or not value.strip() for value in values):
            raise WorldStateProductionReadError(f"scope.{key} must be a list of non-empty strings")
        if len(set(values)) != len(values):
            raise WorldStateProductionReadError(f"scope.{key} must not contain duplicates")
        normalized_scope[key] = list(values)
    unknown_dimensions = sorted(set(normalized_scope["dimensions"]) - DIMENSIONS)
    if unknown_dimensions:
        raise WorldStateProductionReadError(f"unsupported dimension vocabulary: {unknown_dimensions}")
    if type(request["include_withdrawn_history"]) is not bool:
        raise WorldStateProductionReadError("include_withdrawn_history must be boolean")
    # Reuse the repository's shared query validator as the final common check.
    shared_errors = validate_history_query({
        "query_mode": request["query_mode"],
        "knowledge_cutoff_utc": request["knowledge_cutoff_utc"],
        "effective_as_of_utc": request["effective_as_of_utc"],
        "scope": normalized_scope,
        "include_withdrawn_history": request["include_withdrawn_history"],
    })
    if shared_errors:
        raise WorldStateProductionReadError("invalid production history query: " + "; ".join(shared_errors))
    return {
        "query_mode": request["query_mode"],
        "knowledge_cutoff_utc": request["knowledge_cutoff_utc"],
        "effective_as_of_utc": request["effective_as_of_utc"],
        "scope": normalized_scope,
        "include_withdrawn_history": request["include_withdrawn_history"],
    }


def _file_hashes(root: Path) -> dict[str, str]:
    directory = root / "data" / "world_state"
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def _scope_matches(row: dict[str, Any], scope: dict[str, list[str]]) -> bool:
    if scope["component_ids"] and row.get("component_id") not in scope["component_ids"]:
        return False
    if scope["dimensions"] and row.get("dimension") not in scope["dimensions"]:
        return False
    row_scope = row.get("scope") if isinstance(row.get("scope"), dict) else {}
    if scope["jurisdictions"] and "*" not in scope["jurisdictions"]:
        jurisdictions = set(row_scope.get("jurisdictions", []))
        if not jurisdictions.intersection(scope["jurisdictions"]):
            return False
    if scope["systems"]:
        systems = set(row_scope.get("systems", []))
        if not systems.intersection(scope["systems"]):
            return False
    return True


def _component_effective_matches(row: dict[str, Any], effective: datetime) -> bool:
    if row.get("effective_at"):
        return _parse_utc(row["effective_at"], "component.effective_at") <= effective
    if row.get("effective_time_precision") == "CIVIL_DATE" and isinstance(row.get("effective_date"), str):
        try:
            return datetime.fromisoformat(row["effective_date"]).date() <= effective.date()
        except ValueError:
            return False
    return False


def _eligible_components(rows: list[dict[str, Any]], query: dict[str, Any]) -> list[dict[str, Any]]:
    selected_query = {
        "query_mode": query["query_mode"],
        "knowledge_cutoff_utc": query["knowledge_cutoff_utc"],
        "effective_as_of_utc": query["effective_as_of_utc"],
        "scope": query["scope"],
        "include_withdrawn_history": query["include_withdrawn_history"],
    }
    try:
        selected = select_component_revisions(rows, selected_query)
    except WorldStateHistoryError as exc:
        raise WorldStateProductionReadError(str(exc)) from exc
    return [row for row in selected if _scope_matches(row, query["scope"])]


def _resolve_snapshot_series(
    snapshots: list[dict[str, Any]],
    components: list[dict[str, Any]],
    admissions: list[dict[str, Any]],
    query: dict[str, Any],
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    knowledge = _parse_utc(query["knowledge_cutoff_utc"], "knowledge_cutoff_utc")
    effective = _parse_utc(query["effective_as_of_utc"], "effective_as_of_utc") if query["effective_as_of_utc"] else None
    component_index = {(row.get("component_type"), row.get("revision_id")): row for row in components}
    admission_index = {row.get("transaction_id"): row for row in admissions}
    eligible_components = {
        (row.get("component_type"), row.get("revision_id")): row
        for row in _eligible_components(components, query)
    }
    candidates: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
    for snapshot in snapshots:
        if snapshot.get("lifecycle_state") in {"WITHDRAWN", "EXPIRED"} and not query["include_withdrawn_history"]:
            continue
        try:
            admitted = _parse_utc(snapshot.get("admitted_at_utc"), "snapshot.admitted_at_utc")
            snapshot_knowledge = _parse_utc(snapshot.get("knowledge_cutoff_utc"), "snapshot.knowledge_cutoff_utc")
        except WorldStateProductionReadError:
            continue
        if admitted > knowledge or snapshot_knowledge > knowledge:
            continue
        transaction = admission_index.get(snapshot.get("admission_transaction_id"))
        if transaction is None:
            raise WorldStateProductionReadError(f"snapshot admission transaction is unavailable: {snapshot.get('admission_transaction_id')}")
        identity = transaction.get("snapshot_revision_identity", {})
        if identity.get("snapshot_revision_id") != snapshot.get("snapshot_revision_id") or identity.get("snapshot_series_id") != snapshot.get("snapshot_series_id"):
            raise WorldStateProductionReadError(f"snapshot admission identity mismatch: {snapshot.get('snapshot_revision_id')}")
        resolved: list[dict[str, Any]] = []
        for ref in snapshot.get("component_refs", []):
            key = (ref.get("component_type"), ref.get("revision_id"))
            row = component_index.get(key)
            if row is None or row.get("component_id") != ref.get("component_id") or row.get("object_sha256") != ref.get("object_sha256"):
                raise WorldStateProductionReadError(f"snapshot component reference mismatch: {key}")
            if row.get("review_transaction_id") != snapshot.get("review_transaction_id"):
                raise WorldStateProductionReadError(f"snapshot/component review transaction mismatch: {key}")
            transaction_refs = {
                (item.get("component_type"), item.get("revision_id"), item.get("component_id"), item.get("object_sha256"))
                for item in transaction.get("component_fingerprints", [])
                if isinstance(item, dict)
            }
            if (ref.get("component_type"), ref.get("revision_id"), ref.get("component_id"), ref.get("object_sha256")) not in transaction_refs:
                raise WorldStateProductionReadError(f"admission transaction does not pin snapshot component: {key}")
            if key in eligible_components:
                resolved.append(row)
        if not resolved:
            continue
        if effective is not None:
            resolved = [row for row in resolved if _component_effective_matches(row, effective)]
            if not resolved:
                continue
        candidates.append((snapshot, resolved))
    if not candidates:
        return []
    # Selecting the greatest admitted revision within each declared series is
    # as-of selection, not an implicit latest query: the cutoff is mandatory.
    by_series: dict[str, tuple[dict[str, Any], list[dict[str, Any]]]] = {}
    for snapshot, resolved in sorted(candidates, key=lambda item: (item[0].get("snapshot_series_id", ""), item[0].get("revision_number", 0), item[0].get("admitted_at_utc", ""))):
        by_series[snapshot["snapshot_series_id"]] = (snapshot, resolved)
    selected = [by_series[key] for key in sorted(by_series)]
    return selected


def _resolve_snapshot(
    snapshots: list[dict[str, Any]],
    components: list[dict[str, Any]],
    admissions: list[dict[str, Any]],
    query: dict[str, Any],
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """Retain the single-series helper for Step 9A callers."""
    selected = _resolve_snapshot_series(snapshots, components, admissions, query)
    if len(selected) != 1:
        raise WorldStateProductionReadError("query selected multiple snapshot series; use the composition view")
    return selected[0]


def derive_freshness(component: dict[str, Any], at_utc: str) -> dict[str, Any]:
    """Derive freshness without changing immutable component content."""
    at = _parse_utc(at_utc, "freshness.at_utc")
    policy = component.get("freshness")
    if not isinstance(policy, dict):
        return {"status": "NO_FRESHNESS_POLICY", "at_utc": at_utc}
    due_value = policy.get("stale_review_due_at_utc")
    latest_value = policy.get("latest_supporting_observed_at_utc")
    if not due_value or not latest_value:
        return {"status": "UNKNOWN", "at_utc": at_utc, "reason": "freshness policy is incomplete"}
    try:
        due = _parse_utc(due_value, "freshness.stale_review_due_at_utc")
        latest = _parse_utc(latest_value, "freshness.latest_supporting_observed_at_utc")
    except WorldStateProductionReadError:
        return {"status": "UNKNOWN", "at_utc": at_utc, "reason": "freshness policy contains an invalid UTC timestamp"}
    remaining = due - at
    if at > due:
        status = "STALE_REVIEW_REQUIRED"
    elif at == due:
        status = "REVIEW_DUE"
    elif remaining <= timedelta(days=REVIEW_DUE_SOON_WINDOW_DAYS):
        status = "REVIEW_DUE_SOON"
    else:
        status = "CURRENT"
    return {
        "status": status,
        "at_utc": at_utc,
        "latest_supporting_observed_at_utc": latest_value,
        "stale_review_due_at_utc": due_value,
        "stale_after_days": policy.get("stale_after_days"),
        "elapsed_days": (at - latest).total_seconds() / 86400,
        "remaining_until_review_seconds": remaining.total_seconds(),
        "reason": "read-time freshness derivation; immutable lifecycle is unchanged",
    }


def derive_current_use(component: dict[str, Any], freshness: dict[str, Any]) -> dict[str, Any]:
    """Derive current applicability without changing lifecycle or history."""
    lifecycle = component.get("lifecycle_state")
    freshness_status = freshness.get("status")
    if lifecycle != "ACTIVE":
        status = "CURRENT_USE_REQUIRES_REVIEW" if lifecycle else "UNKNOWN"
        reason = "inactive lifecycle cannot support a current-use claim" if lifecycle else "lifecycle state is unavailable"
    else:
        mapping = {
            "CURRENT": "CURRENTLY_USABLE_WITHIN_SCOPE",
            "REVIEW_DUE_SOON": "CURRENT_WITH_REVIEW_DUE_SOON",
            "REVIEW_DUE": "CURRENT_USE_REQUIRES_REVIEW",
            "STALE_REVIEW_REQUIRED": "CURRENT_USE_REQUIRES_REVIEW",
            "NO_FRESHNESS_POLICY": "NO_CURRENTNESS_CLAIM",
            "UNKNOWN": "UNKNOWN",
        }
        status = mapping.get(freshness_status, "UNKNOWN")
        reason = {
            "CURRENTLY_USABLE_WITHIN_SCOPE": "active revision has a governed freshness policy currently within scope",
            "CURRENT_WITH_REVIEW_DUE_SOON": "active revision remains usable within scope but its governed review deadline is near",
            "CURRENT_USE_REQUIRES_REVIEW": "active revision remains historical state but its governed review status requires review",
            "NO_CURRENTNESS_CLAIM": "active revision has no governed freshness/currentness policy; historical use remains permitted",
            "UNKNOWN": "current applicability cannot be established from the available lifecycle/freshness contract",
        }[status]
    return {
        "component_id": component.get("component_id"),
        "status": status,
        "lifecycle_state": lifecycle,
        "freshness_status": freshness_status,
        "reason": reason,
    }


def current_use_summary(current_use: list[dict[str, Any]]) -> dict[str, int]:
    """Summarise current-use states without averaging heterogeneous policy."""
    statuses = [row.get("status") for row in current_use]
    return {
        "selected_components": len(statuses),
        "currently_usable_components": sum(status in {"CURRENTLY_USABLE_WITHIN_SCOPE", "CURRENT_WITH_REVIEW_DUE_SOON"} for status in statuses),
        "review_required_components": sum(status == "CURRENT_USE_REQUIRES_REVIEW" for status in statuses),
        "no_currentness_claim_components": sum(status == "NO_CURRENTNESS_CLAIM" for status in statuses),
        "unknown_current_use_components": sum(status == "UNKNOWN" for status in statuses),
    }


def build_internal_briefing_read(
    selected_components: list[dict[str, Any]],
    query: dict[str, Any],
    freshness: list[dict[str, Any]],
    current_use: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a non-narrative briefing view without collapsing scoped state."""
    current_use = current_use or [
        {"component_id": row.get("component_id"), "status": "UNKNOWN", "freshness_status": None, "lifecycle_state": row.get("lifecycle_state"), "reason": "current-use status was not supplied by the caller"}
        for row in selected_components
    ]
    queried = query["scope"]["dimensions"] or sorted(DIMENSIONS)
    by_dimension: dict[str, list[dict[str, Any]]] = {}
    for row in selected_components:
        by_dimension.setdefault(row.get("dimension"), []).append(row)
    entries = []
    for dimension in queried:
        rows = sorted(by_dimension.get(dimension, []), key=lambda row: (row.get("component_id", ""), row.get("revision_number", 0)))
        if not rows:
            entries.append({"dimension": dimension, "coverage": "NOT_ASSESSED", "coverage_detail": "NO_SCOPED_ASSESSMENT", "scoped_assessments": [], "assessment": None})
            continue
        assessments = [{
            "component_id": row["component_id"],
            "revision_id": row["revision_id"],
            "lifecycle_state": row.get("lifecycle_state"),
            "scope": deepcopy(row["scope"]),
            "state_label": row.get("state_label"),
            "direction": row.get("direction"),
            "qualitative_confidence": row.get("qualitative_confidence"),
            "effective_date": row.get("effective_date"),
            "effective_time_precision": row.get("effective_time_precision"),
            "known_at_utc": row.get("known_at_utc"),
            "admitted_at_utc": row.get("admitted_at_utc"),
            "freshness": next((item for item in freshness if item.get("component_id") == row.get("component_id")), None),
            "current_use": next((item for item in current_use if item.get("component_id") == row.get("component_id")), None),
            "current_use_status": next((item.get("status") for item in current_use if item.get("component_id") == row.get("component_id")), "UNKNOWN"),
            "visibility": row.get("visibility"),
            "limitations": deepcopy(row.get("limitations", [])),
        } for row in rows]
        entries.append({
            "dimension": dimension,
            "coverage": "SCOPED_ASSESSMENT_AVAILABLE" if len(assessments) == 1 else "MULTIPLE_SCOPED_ASSESSMENTS",
            "coverage_detail": "ONE_SCOPED_ASSESSMENT" if len(assessments) == 1 else "MULTIPLE_SCOPED_ASSESSMENTS",
            "scoped_assessments": assessments,
            # Compatibility for the original one-assessment read contract. It
            # is deliberately null when multiple scoped assessments exist.
            "assessment": assessments[0] if len(assessments) == 1 else None,
        })
    return {
        "surface": "INTERNAL_BRIEFING_READ",
        "coverage_statement": "Structured admitted state only; absence is not a global assessment.",
        "dimensions": entries,
        "public_projection_permitted": False,
        "narrative_generated": False,
    }


# Kept as a private compatibility alias for callers from the Step 9A tranche.
_briefing_view = build_internal_briefing_read


def read_production_world_state(request: dict[str, Any], *, root: Path = ROOT) -> dict[str, Any]:
    """Read admitted history for one explicit knowledge/effective query."""
    query = validate_production_read_request(request)
    before = _file_hashes(root)
    errors = validate_production_state(root, enforce_first_population=False)
    if errors:
        raise WorldStateProductionReadError("production history validation failed: " + "; ".join(errors))
    state = load_production_state(root)
    selected_series = _resolve_snapshot_series(state["snapshots"], state["components"], state["admissions"], query)
    composition_view = None
    if len(selected_series) == 1:
        snapshot, selected_components = selected_series[0]
    elif selected_series:
        selected_components_for_composition = [
            (snapshot, rows) for snapshot, rows in selected_series
        ]
        composition_components = [row for _, rows in selected_components_for_composition for row in rows]
        composition_freshness = [
            {"component_id": row["component_id"], **derive_freshness(row, query["knowledge_cutoff_utc"])}
            for row in composition_components
        ]
        composition_current_use = [
            derive_current_use(row, next(item for item in composition_freshness if item["component_id"] == row["component_id"]))
            for row in composition_components
        ]
        composition_view = build_composition_view(
            query,
            selected_components_for_composition,
            freshness=composition_freshness,
            current_use=composition_current_use,
            dimensions=sorted(DIMENSIONS),
        )
        snapshot = None
        selected_components = composition_view["selected_components"]
    else:
        snapshot = None
        selected_components = []
    freshness = [
        {"component_id": row["component_id"], **derive_freshness(row, query["knowledge_cutoff_utc"])}
        for row in selected_components
    ]
    current_use = [
        derive_current_use(row, next(item for item in freshness if item["component_id"] == row["component_id"]))
        for row in selected_components
    ]
    query_scope = query["scope"]
    queried_dimensions = query_scope["dimensions"] or sorted(DIMENSIONS)
    assessed_dimensions = sorted({row.get("dimension") for row in selected_components if row.get("dimension")})
    unassessed_dimensions = sorted(set(queried_dimensions) - set(assessed_dimensions))
    unqueried_dimensions = sorted(DIMENSIONS - set(queried_dimensions))
    status = "ADMITTED_ASSESSMENT_AVAILABLE" if selected_components else "NO_ADMITTED_ASSESSMENT"
    production = {
        "query": query,
        "status": status,
        "selected_snapshot": deepcopy(snapshot),
        "selected_components": deepcopy(selected_components),
        "production_counts": {
            "actors": len(state["actors"]),
            "components": len(state["components"]),
            "snapshots": len(state["snapshots"]),
            "admissions": len(state["admissions"]),
        },
        "component_count": len(selected_components),
        "dimensions_assessed": assessed_dimensions,
        "dimensions_unassessed": unassessed_dimensions,
        "unqueried_dimensions": unqueried_dimensions,
        "scope": deepcopy(query_scope),
        "empty_queried_domains": [json.loads(value) for value in sorted({
            json.dumps(domain, sort_keys=True, separators=(",", ":"))
            for selected_snapshot, _ in selected_series
            for domain in selected_snapshot.get("empty_queried_domains", [])
        })],
        "visibility": snapshot.get("visibility") if snapshot else "INTERNAL_ONLY",
        "public_projection_permitted": False,
        "admission_refs": [
            {
                "transaction_id": selected_snapshot.get("admission_transaction_id"),
                "snapshot_revision_id": selected_snapshot.get("snapshot_revision_id"),
                "snapshot_series_id": selected_snapshot.get("snapshot_series_id"),
                "component_ids": [item.get("component_id") for item in rows],
            }
            for selected_snapshot, rows in selected_series
        ],
        "freshness": freshness,
        "current_use": current_use,
        "current_use_summary": current_use_summary(current_use),
        "composition_view": deepcopy(composition_view),
        "limitations": [
            "freshness is derived at query time and does not mutate lifecycle or history",
            "a scoped assessment is not a dimension-wide or global assessment",
            "unassessed and unqueried dimensions are not filled by inference",
        ],
        "briefing_read": _briefing_view(selected_components, query, freshness, current_use),
        "production_file_mutation_check": {"before": before, "after": _file_hashes(root)},
    }
    if composition_view is not None:
        production["limitations"].extend(composition_view["limitations"])
    after = production["production_file_mutation_check"]["after"]
    production["production_file_mutation_check"]["status"] = "PASS" if before == after else "FAIL"
    if before != after:
        raise WorldStateProductionReadError("production history files changed during read")
    if any(item.get("state") == "UNSUPPORTED" and item.get("domain") == "CANONICAL_HISTORICAL_AS_OF" for item in production["empty_queried_domains"]):
        production["limitations"].append("CANONICAL_HISTORICAL_AS_OF_UNSUPPORTED")
    production["semantic_fingerprint"] = semantic_fingerprint({key: value for key, value in production.items() if key != "semantic_fingerprint"})
    return production


def compare_production_world_state(from_view: dict[str, Any], to_view: dict[str, Any]) -> dict[str, Any]:
    """Compute deterministic knowledge/effective/freshness deltas."""
    from_components = {row.get("component_id"): row for row in from_view.get("selected_components", [])}
    to_components = {row.get("component_id"): row for row in to_view.get("selected_components", [])}
    added = sorted(set(to_components) - set(from_components))
    removed = sorted(set(from_components) - set(to_components))
    revision_changed = sorted(
        component_id for component_id in set(from_components) & set(to_components)
        if from_components[component_id].get("revision_id") != to_components[component_id].get("revision_id")
    )
    unchanged = sorted(
        component_id for component_id in set(from_components) & set(to_components)
        if from_components[component_id].get("revision_id") == to_components[component_id].get("revision_id")
    )
    freshness_transitions = []
    from_freshness = {row.get("component_id"): row for row in from_view.get("freshness", [])}
    to_freshness = {row.get("component_id"): row for row in to_view.get("freshness", [])}
    for component_id in sorted(set(from_freshness) & set(to_freshness)):
        old = from_freshness[component_id].get("status")
        new = to_freshness[component_id].get("status")
        if old != new:
            freshness_transitions.append({"component_id": component_id, "from": old, "to": new})
    current_use_transitions = []
    from_current_use = {row.get("component_id"): row for row in from_view.get("current_use", [])}
    to_current_use = {row.get("component_id"): row for row in to_view.get("current_use", [])}
    for component_id in sorted(set(from_current_use) & set(to_current_use)):
        old = from_current_use[component_id].get("status")
        new = to_current_use[component_id].get("status")
        if old != new:
            current_use_transitions.append({"component_id": component_id, "from": old, "to": new})
    from_dims = set(from_view.get("dimensions_assessed", []))
    to_dims = set(to_view.get("dimensions_assessed", []))
    def series_state(view: dict[str, Any]) -> dict[str, str]:
        composition = view.get("composition_view") or {}
        if composition:
            return {
                row.get("snapshot_series_id"): row.get("snapshot_revision_id")
                for row in composition.get("selected_series", [])
            }
        snapshot = view.get("selected_snapshot") or {}
        if snapshot.get("snapshot_series_id"):
            return {snapshot.get("snapshot_series_id"): snapshot.get("snapshot_revision_id")}
        return {}

    from_series = series_state(from_view)
    to_series = series_state(to_view)
    series_added = sorted(set(to_series) - set(from_series))
    series_removed = sorted(set(from_series) - set(to_series))
    series_revision_advanced = sorted(
        series_id for series_id in set(from_series) & set(to_series)
        if from_series[series_id] != to_series[series_id]
    )
    content_change = bool(added or removed or revision_changed or series_added or series_removed or series_revision_advanced)
    effective_view = from_view.get("query", {}).get("query_mode") == "EFFECTIVE_AS_OF" or to_view.get("query", {}).get("query_mode") == "EFFECTIVE_AS_OF"
    effective_change = effective_view and content_change
    knowledge_change = not effective_view and content_change
    if effective_view and content_change:
        knowledge_change = bool(revision_changed) or bool(from_view.get("query", {}).get("knowledge_cutoff_utc") != to_view.get("query", {}).get("knowledge_cutoff_utc"))
    if knowledge_change and effective_change:
        delta_class = "BOTH"
    elif effective_change:
        delta_class = "EFFECTIVE_STATE_CHANGE"
    elif knowledge_change:
        delta_class = "KNOWLEDGE_STATE_CHANGE"
    else:
        delta_class = "NO_CHANGE"
    from_snapshot = (from_view.get("selected_snapshot") or {}).get("snapshot_revision_id")
    to_snapshot = (to_view.get("selected_snapshot") or {}).get("snapshot_revision_id")
    return {
        "from_query": deepcopy(from_view.get("query")),
        "to_query": deepcopy(to_view.get("query")),
        "components_added": added,
        "components_removed": removed,
        "components_revision_changed": revision_changed,
        "components_unchanged": unchanged,
        "snapshot_series_added": series_added,
        "snapshot_series_removed": series_removed,
        "snapshot_series_revision_advanced": series_revision_advanced,
        "dimensions_newly_assessed": sorted(to_dims - from_dims),
        "dimensions_no_longer_current": sorted(from_dims - to_dims),
        "freshness_transitions": freshness_transitions,
        "current_use_transitions": current_use_transitions,
        "snapshot_transition": {"from": from_snapshot, "to": to_snapshot},
        "delta_class": delta_class,
        "knowledge_state_change": knowledge_change,
        "effective_state_change": effective_change,
        "freshness_only": bool(freshness_transitions) and not content_change,
        "current_use_only": bool(current_use_transitions) and not content_change,
        "successor_revision_created": False,
    }


def successor_preflight(view: dict[str, Any], *, new_governed_evidence: bool = False, correction_or_retraction: bool = False, contradiction: bool = False) -> dict[str, Any]:
    """Legacy test scaffolding; production review uses derived lineage packets.

    The flags remain for Step 9A compatibility tests only. They are not a
    production authority and cannot create a review packet or successor.
    """
    components = view.get("selected_components", [])
    if not components:
        result = "NO_ADMITTED_COMPONENT"
    elif correction_or_retraction or contradiction:
        result = "CORRECTION_OR_CONTRADICTION_REQUIRES_REVIEW"
    elif new_governed_evidence:
        result = "NEW_GOVERNED_EVIDENCE_AVAILABLE"
    else:
        due_values = [row.get("stale_review_due_at_utc") for row in view.get("freshness", []) if row.get("stale_review_due_at_utc")]
        query_at = view.get("query", {}).get("knowledge_cutoff_utc")
        if due_values and query_at and _parse_utc(query_at, "query.knowledge_cutoff_utc") >= min(_parse_utc(value, "freshness.stale_review_due_at_utc") for value in due_values):
            result = "REVIEW_DUE"
        else:
            result = "NO_SUCCESSOR_NEEDED_YET"
    return {
        "result": result,
        "component_ids": sorted(row.get("component_id") for row in components),
        "review_due_at_utc": sorted({row.get("stale_review_due_at_utc") for row in view.get("freshness", []) if row.get("stale_review_due_at_utc")}),
        "successor_revision_created": False,
        "production_write_performed": False,
    }
