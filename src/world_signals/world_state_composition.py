"""Read-time composition of independently admitted World State snapshots.

Composition views are ephemeral read results.  They are not snapshot
revisions, evidence, synthesis components, or admission transactions.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any


COMPOSITION_ATOMICITY = "INDEPENDENT_ADMISSIONS"
COMPOSITION_TYPE = "WORLD_STATE_COMPOSITION_VIEW"
COMPOSITION_READINESS = "MULTI_SERIES_READ_CONTRACT_READY"
VISIBILITY_STATES = {"INTERNAL_ONLY", "PUBLIC_ELIGIBLE", "PUBLIC_PROJECTED"}


class WorldStateCompositionError(ValueError):
    """Raised when independent snapshot series cannot be composed safely."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


def _compact(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def composition_fingerprint(value: Any) -> str:
    normalized = deepcopy(value)
    if isinstance(normalized, dict):
        if isinstance(normalized.get("selected_series"), list):
            normalized["selected_series"] = sorted(
                normalized["selected_series"],
                key=lambda item: (item.get("snapshot_series_id", ""), item.get("snapshot_revision_id", "")) if isinstance(item, dict) else str(item),
            )
        if isinstance(normalized.get("selected_components"), list):
            normalized["selected_components"] = sorted(
                normalized["selected_components"],
                key=lambda item: (item.get("component_id", ""), item.get("revision_id", "")) if isinstance(item, dict) else str(item),
            )
    return hashlib.sha256(_compact(normalized).encode("utf-8")).hexdigest()


def _series_ref(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "snapshot_series_id": snapshot.get("snapshot_series_id"),
        "snapshot_revision_id": snapshot.get("snapshot_revision_id"),
        "object_sha256": snapshot.get("object_sha256"),
        "admission_transaction_id": snapshot.get("admission_transaction_id"),
        "admitted_at_utc": snapshot.get("admitted_at_utc"),
        "review_transaction_id": snapshot.get("review_transaction_id"),
        "knowledge_cutoff_utc": snapshot.get("knowledge_cutoff_utc"),
        "effective_as_of_utc": snapshot.get("effective_as_of_utc"),
        "scope": deepcopy(snapshot.get("scope", {})),
        "component_refs": deepcopy(snapshot.get("component_refs", [])),
    }


def _coverage(components: list[dict[str, Any]], dimensions: list[str]) -> dict[str, Any]:
    by_dimension: dict[str, list[dict[str, Any]]] = {}
    for row in components:
        by_dimension.setdefault(row.get("dimension"), []).append(row)
    entries: list[dict[str, Any]] = []
    for dimension in dimensions:
        rows = by_dimension.get(dimension, [])
        if not rows:
            status = "NOT_ASSESSED"
        elif len(rows) == 1:
            status = "ONE_SCOPED_ASSESSMENT"
        else:
            status = "MULTIPLE_SCOPED_ASSESSMENTS"
        entries.append({
            "dimension": dimension,
            "coverage": status,
            "component_ids": sorted(row.get("component_id") for row in rows),
        })
    assessed = sum(1 for entry in entries if entry["coverage"] != "NOT_ASSESSED")
    return {
        "dimensions": entries,
        "dimensions_with_scoped_assessments": assessed,
        "controlled_dimensions_total": len(dimensions),
        "global_coverage_complete": False,
    }


def build_composition_view(
    query: dict[str, Any],
    selected_series: list[tuple[dict[str, Any], list[dict[str, Any]]]],
    *,
    freshness: list[dict[str, Any]],
    dimensions: list[str],
) -> dict[str, Any]:
    """Build a deterministic view from already validated series selections."""
    if len(selected_series) < 2:
        raise WorldStateCompositionError("COMPOSITION_REQUIRES_MULTIPLE_SERIES", "at least two series are required")

    ordered_series = sorted(selected_series, key=lambda item: item[0].get("snapshot_series_id", ""))
    for snapshot, _ in ordered_series:
        if snapshot.get("visibility") not in VISIBILITY_STATES:
            raise WorldStateCompositionError("INVALID_VISIBILITY", f"snapshot {snapshot.get('snapshot_revision_id')} has invalid visibility")
        if not snapshot.get("admission_transaction_id") or not snapshot.get("admitted_at_utc"):
            raise WorldStateCompositionError("UNRESOLVED_SNAPSHOT_ADMISSION", f"snapshot {snapshot.get('snapshot_revision_id')} is not admitted")
    series_refs = [_series_ref(snapshot) for snapshot, _ in ordered_series]
    components_by_id: dict[str, dict[str, Any]] = {}
    component_sources: dict[str, list[dict[str, Any]]] = {}
    for snapshot, rows in ordered_series:
        if snapshot.get("component_refs") and not rows:
            raise WorldStateCompositionError("MISSING_COMPONENT_REFERENCE", f"selected snapshot {snapshot.get('snapshot_revision_id')} has no resolved components")
        refs_by_key = {
            (ref.get("component_type"), ref.get("revision_id")): ref
            for ref in snapshot.get("component_refs", [])
        }
        for row in rows:
            component_id = row.get("component_id")
            if not component_id:
                raise WorldStateCompositionError("MISSING_COMPONENT", "selected component has no component_id")
            ref = refs_by_key.get((row.get("component_type"), row.get("revision_id")))
            if ref is None:
                raise WorldStateCompositionError("MISSING_COMPONENT_REFERENCE", f"{component_id} is not pinned by its snapshot")
            if ref.get("component_id") != component_id or ref.get("object_sha256") != row.get("object_sha256"):
                raise WorldStateCompositionError("COMPONENT_HASH_MISMATCH", f"snapshot reference does not match {component_id}")
            identity = (row.get("component_type"), row.get("revision_id"), row.get("object_sha256"))
            existing = components_by_id.get(component_id)
            if existing is not None:
                existing_identity = (existing.get("component_type"), existing.get("revision_id"), existing.get("object_sha256"))
                if existing_identity != identity:
                    raise WorldStateCompositionError(
                        "COMPONENT_HEAD_CONFLICT_ACROSS_SERIES",
                        f"independent series select incompatible revisions for {component_id}",
                    )
            else:
                components_by_id[component_id] = deepcopy(row)
            component_sources.setdefault(component_id, []).append({
                "snapshot_series_id": snapshot.get("snapshot_series_id"),
                "snapshot_revision_id": snapshot.get("snapshot_revision_id"),
            })

    selected_components: list[dict[str, Any]] = []
    for component_id in sorted(components_by_id):
        row = components_by_id[component_id]
        row["composition_sources"] = sorted(component_sources[component_id], key=lambda item: (item["snapshot_series_id"], item["snapshot_revision_id"]))
        selected_components.append(row)
    coverage = _coverage(selected_components, dimensions)
    semantic = {
        "query": deepcopy(query),
        "selected_series": series_refs,
        "selected_components": [
            {"component_type": row.get("component_type"), "component_id": row.get("component_id"), "revision_id": row.get("revision_id"), "object_sha256": row.get("object_sha256")}
            for row in selected_components
        ],
        "coverage": coverage,
        "composition_atomicity": COMPOSITION_ATOMICITY,
        "limitations": [
            "This is a read-time composition of independently admitted snapshot series, not a jointly reviewed or atomically admitted World State snapshot.",
            "Composition does not create evidence, synthesis, Relationships, Risks, Scenarios or Forecasts.",
            "Independent snapshot series remain separate immutable histories.",
        ],
    }
    return {
        "composition_type": COMPOSITION_TYPE,
        "composition_contract_status": COMPOSITION_READINESS,
        "composition_atomicity": COMPOSITION_ATOMICITY,
        "query": deepcopy(query),
        "selected_series": series_refs,
        "selected_components": selected_components,
        "selected_series_count": len(series_refs),
        "selected_component_count": len(selected_components),
        "coverage": coverage,
        "freshness": deepcopy(freshness),
        "admission_transaction_id": None,
        "production_snapshot_revision_id": None,
        "public_projection_permitted": False,
        "narrative_generated": False,
        "limitations": semantic["limitations"],
        "semantic_fingerprint": composition_fingerprint(semantic),
    }
