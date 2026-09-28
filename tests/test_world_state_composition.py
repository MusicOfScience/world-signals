from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.world_state_admission import load_production_state, validate_production_state  # noqa: E402
from world_signals.world_state_composition import (  # noqa: E402
    COMPOSITION_ATOMICITY,
    COMPOSITION_READINESS,
    WorldStateCompositionError,
    build_composition_view,
    composition_fingerprint,
)
from world_signals.world_state_history import DIMENSIONS, fingerprint, with_object_fingerprint  # noqa: E402
from world_signals.world_state_production import (  # noqa: E402
    WorldStateProductionReadError,
    compare_production_world_state,
    read_production_world_state,
)


def query(knowledge: str = "2026-09-27T20:00:00Z", *, mode: str = "KNOWLEDGE_AS_OF", effective: str | None = None, jurisdictions: list[str] | None = None, dimensions: list[str] | None = None) -> dict:
    return {
        "query_mode": mode,
        "knowledge_cutoff_utc": knowledge,
        "effective_as_of_utc": effective,
        "scope": {"dimensions": dimensions or [], "jurisdictions": jurisdictions or [], "systems": [], "component_ids": []},
        "include_withdrawn_history": False,
    }


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _synthetic_component(base: dict, component_id: str, dimension: str, jurisdiction: str, admitted_at: str, effective_date: str) -> dict:
    row = deepcopy(base)
    row.update({
        "component_id": component_id,
        "revision_id": component_id + "-R1",
        "component_type": "DIMENSION_ASSESSMENT",
        "dimension": dimension,
        "scope": {"jurisdictions": [jurisdiction], "systems": ["SYNTHETIC_SYSTEM"], "boundaries": ["test-only"]},
        "state_label": "SYNTHETIC_REVIEWED_STATE",
        "direction": "UPWARD",
        "effective_at": None,
        "effective_date": effective_date,
        "effective_time_precision": "CIVIL_DATE",
        "known_at_utc": admitted_at,
        "reviewed_at_utc": admitted_at,
        "admitted_at_utc": admitted_at,
        "review_transaction_id": "WS-SYNTH-REVIEW-" + component_id,
        "admission_transaction_id": "WS-SYNTH-ADMISSION-" + component_id,
        "source_proposal_id": "WS-SYNTH-PROPOSAL-" + component_id,
        "revision_kind": "INITIAL",
        "revision_number": 1,
        "previous_revision_id": None,
        "lifecycle_state": "ACTIVE",
        "review_state": "ACCEPTED",
        "visibility": "INTERNAL_ONLY",
        "freshness": {
            "latest_supporting_observed_at_utc": admitted_at,
            "stale_after_days": 30,
            "stale_review_due_at_utc": "2026-11-01T00:00:00Z",
        },
        "source_manifest_sha256": "a" * 64,
        "admission_transaction_id": "WS-SYNTH-ADMISSION-" + component_id,
    })
    return with_object_fingerprint(row)


def _synthetic_snapshot(base: dict, series_id: str, component: dict, admitted_at: str, knowledge_cutoff: str, admission_id: str) -> dict:
    row = deepcopy(base)
    row.update({
        "snapshot_series_id": series_id,
        "snapshot_revision_id": series_id + "-R1",
        "revision_number": 1,
        "previous_snapshot_revision_id": None,
        "knowledge_cutoff_utc": knowledge_cutoff,
        "admitted_at_utc": admitted_at,
        "review_transaction_id": component["review_transaction_id"],
        "admission_transaction_id": admission_id,
        "proposal_id": "WS-SYNTH-SNAPSHOT-PROPOSAL-" + series_id,
        "component_refs": [{
            "component_type": component["component_type"],
            "component_id": component["component_id"],
            "revision_id": component["revision_id"],
            "object_sha256": component["object_sha256"],
        }],
        "scope": deepcopy(component["scope"]),
        "source_manifest_sha256": "b" * 64,
        "limitations": ["synthetic test-only independent snapshot series"],
        "upstream_refs": [deepcopy(base["upstream_refs"][0])],
        "object_sha256": None,
    })
    return with_object_fingerprint(row)


def _synthetic_admission(base: dict, admission_id: str, component: dict, snapshot: dict) -> dict:
    row = deepcopy(base)
    row.update({
        "transaction_id": admission_id,
        "proposal_id": snapshot["proposal_id"],
        "proposal_semantic_fingerprint": "c" * 64,
        "source_manifest_sha256": snapshot["source_manifest_sha256"],
        "component_fingerprints": [{
            "component_type": component["component_type"],
            "component_id": component["component_id"],
            "revision_id": component["revision_id"],
            "object_sha256": component["object_sha256"],
        }],
        "review_transaction_id": component["review_transaction_id"],
        "decided_at_utc": snapshot["admitted_at_utc"],
        "admitted_at_utc": snapshot["admitted_at_utc"],
        "component_dispositions": [{
            "component_id": component["component_id"],
            "revision_id": component["revision_id"],
            "disposition": "ADMITTED",
            "reason": "synthetic test-only admission",
        }],
        "snapshot_revision_identity": {
            "snapshot_series_id": snapshot["snapshot_series_id"],
            "snapshot_revision_id": snapshot["snapshot_revision_id"],
        },
        "pre_state_hashes": {"actors": "d" * 64, "components": "d" * 64, "snapshots": "d" * 64},
        "post_state_hashes": {"actors": "e" * 64, "components": "e" * 64, "snapshots": "e" * 64},
        "write_targets": ["data/world_state/components.json", "data/world_state/snapshots.json"],
        "visibility_decision": "INTERNAL_ONLY",
        "public_projection_permitted": False,
        "transaction_fingerprint": None,
    })
    row["transaction_fingerprint"] = fingerprint(row, exclude={"transaction_fingerprint"})
    return row


def synthetic_root() -> Path:
    temp = Path(tempfile.mkdtemp(prefix="world-state-composition-"))
    shutil.copytree(ROOT / "data", temp / "data")
    state = load_production_state(temp)
    base_component = state["components"][0]
    base_snapshot = state["snapshots"][0]
    base_admission = state["admissions"][0]
    health = _synthetic_component(base_component, "WSDIM-SYNTH-HEALTH-A", "HEALTH_BIOSECURITY", "SYNTH-A", "2026-09-02T00:00:00Z", "2026-09-01")
    macro = _synthetic_component(base_component, "WSDIM-SYNTH-MACRO-B", "MACROECONOMIC_FINANCIAL_CONDITIONS", "SYNTH-B", "2026-09-20T00:00:00Z", "2026-09-15")
    snapshot_a = _synthetic_snapshot(base_snapshot, "WSSNAP-SYNTH-A", health, "2026-09-02T00:00:00Z", "2026-09-02T00:00:00Z", "WS-SYNTH-ADMISSION-A")
    snapshot_b = _synthetic_snapshot(base_snapshot, "WSSNAP-SYNTH-B", macro, "2026-09-20T00:00:00Z", "2026-09-20T00:00:00Z", "WS-SYNTH-ADMISSION-B")
    admission_a = _synthetic_admission(base_admission, "WS-SYNTH-ADMISSION-A", health, snapshot_a)
    admission_b = _synthetic_admission(base_admission, "WS-SYNTH-ADMISSION-B", macro, snapshot_b)
    components_doc = json.loads((temp / "data/world_state/components.json").read_text())
    snapshots_doc = json.loads((temp / "data/world_state/snapshots.json").read_text())
    admissions_doc = json.loads((temp / "data/world_state/admission_transactions.json").read_text())
    components_doc["components"].extend([health, macro])
    snapshots_doc["snapshots"].extend([snapshot_a, snapshot_b])
    admissions_doc["transactions"].extend([admission_a, admission_b])
    _write_json(temp / "data/world_state/components.json", components_doc)
    _write_json(temp / "data/world_state/snapshots.json", snapshots_doc)
    _write_json(temp / "data/world_state/admission_transactions.json", admissions_doc)
    return temp


class WorldStateCompositionTests(unittest.TestCase):
    def test_current_real_single_series_remains_unchanged(self):
        view = read_production_world_state(query(dimensions=["HEALTH_BIOSECURITY"]))
        self.assertIsNone(view["composition_view"])
        self.assertEqual(view["selected_snapshot"]["snapshot_series_id"], "WSSNAP-HEALTH-COD-BVD-202609")
        self.assertEqual(view["production_counts"], {"actors": 0, "components": 3, "snapshots": 2, "admissions": 2})

    def test_two_independent_series_compose_read_only(self):
        root = synthetic_root()
        try:
            self.assertEqual(validate_production_state(root, enforce_first_population=False), [])
            view = read_production_world_state(query(jurisdictions=["SYNTH-A", "SYNTH-B"]), root=root)
            composition = view["composition_view"]
            self.assertEqual(composition["selected_series_count"], 2)
            self.assertEqual(composition["selected_component_count"], 2)
            self.assertEqual(composition["composition_atomicity"], COMPOSITION_ATOMICITY)
            self.assertEqual(composition["composition_contract_status"], COMPOSITION_READINESS)
            self.assertIsNone(composition["admission_transaction_id"])
            self.assertEqual({row["component_id"] for row in view["selected_components"]}, {"WSDIM-SYNTH-HEALTH-A", "WSDIM-SYNTH-MACRO-B"})
        finally:
            shutil.rmtree(root)

    def test_staggered_admission_selects_a_then_b(self):
        root = synthetic_root()
        try:
            first = read_production_world_state(query("2026-09-10T00:00:00Z", jurisdictions=["SYNTH-A", "SYNTH-B"]), root=root)
            self.assertIsNone(first["composition_view"])
            self.assertEqual([row["component_id"] for row in first["selected_components"]], ["WSDIM-SYNTH-HEALTH-A"])
            both = read_production_world_state(query("2026-09-21T00:00:00Z", jurisdictions=["SYNTH-A", "SYNTH-B"]), root=root)
            self.assertEqual(both["composition_view"]["selected_series_count"], 2)
        finally:
            shutil.rmtree(root)

    def test_effective_query_filters_each_component_without_utc_invention(self):
        root = synthetic_root()
        try:
            view = read_production_world_state(query("2026-09-21T00:00:00Z", mode="EFFECTIVE_AS_OF", effective="2026-09-10T00:00:00Z", jurisdictions=["SYNTH-A", "SYNTH-B"]), root=root)
            self.assertEqual([row["component_id"] for row in view["selected_components"]], ["WSDIM-SYNTH-HEALTH-A"])
            self.assertEqual(view["selected_components"][0]["effective_time_precision"], "CIVIL_DATE")
        finally:
            shutil.rmtree(root)

    def test_same_component_identical_reference_dedupes_and_keeps_provenance(self):
        component = {"component_id": "X", "component_type": "DIMENSION_ASSESSMENT", "revision_id": "X-R1", "object_sha256": "a" * 64, "dimension": "HEALTH_BIOSECURITY", "scope": {}}
        ref = {"component_type": "DIMENSION_ASSESSMENT", "component_id": "X", "revision_id": "X-R1", "object_sha256": "a" * 64}
        snapshots = []
        for series in ("A", "B"):
            snapshots.append(({"snapshot_series_id": series, "snapshot_revision_id": series + "-R1", "object_sha256": series.lower() * 64, "admission_transaction_id": "TX-" + series, "admitted_at_utc": "2026-09-01T00:00:00Z", "review_transaction_id": "REV-" + series, "knowledge_cutoff_utc": "2026-09-01T00:00:00Z", "effective_as_of_utc": None, "scope": {}, "visibility": "INTERNAL_ONLY", "component_refs": [ref]}, [component]))
        view = build_composition_view(query(), snapshots, freshness=[{"component_id": "X", "status": "CURRENT"}], dimensions=sorted(DIMENSIONS))
        self.assertEqual(view["selected_component_count"], 1)
        self.assertEqual(len(view["selected_components"][0]["composition_sources"]), 2)

    def test_same_component_conflicting_revision_fails_closed(self):
        first = {"component_id": "X", "component_type": "DIMENSION_ASSESSMENT", "revision_id": "X-R1", "object_sha256": "a" * 64, "dimension": "HEALTH_BIOSECURITY", "scope": {}}
        second = {**first, "revision_id": "X-R2", "object_sha256": "b" * 64}
        selected = []
        for series, row in (("A", first), ("B", second)):
            selected.append(({"snapshot_series_id": series, "snapshot_revision_id": series + "-R1", "object_sha256": series.lower() * 64, "admission_transaction_id": "TX-" + series, "admitted_at_utc": "2026-09-01T00:00:00Z", "review_transaction_id": "REV-" + series, "knowledge_cutoff_utc": "2026-09-01T00:00:00Z", "effective_as_of_utc": None, "scope": {}, "visibility": "INTERNAL_ONLY", "component_refs": [{"component_type": row["component_type"], "component_id": "X", "revision_id": row["revision_id"], "object_sha256": row["object_sha256"]}]}, [row]))
        with self.assertRaises(WorldStateCompositionError) as context:
            build_composition_view(query(), selected, freshness=[], dimensions=sorted(DIMENSIONS))
        self.assertEqual(context.exception.code, "COMPONENT_HEAD_CONFLICT_ACROSS_SERIES")

    def test_missing_component_and_invalid_visibility_fail_closed(self):
        snapshot = {
            "snapshot_series_id": "A",
            "snapshot_revision_id": "A-R1",
            "object_sha256": "a" * 64,
            "admission_transaction_id": "TX-A",
            "admitted_at_utc": "2026-09-01T00:00:00Z",
            "review_transaction_id": "REV-A",
            "knowledge_cutoff_utc": "2026-09-01T00:00:00Z",
            "visibility": "INTERNAL_ONLY",
            "component_refs": [{"component_type": "DIMENSION_ASSESSMENT", "component_id": "MISSING", "revision_id": "MISSING-R1", "object_sha256": "b" * 64}],
        }
        valid_snapshot = deepcopy(snapshot)
        valid_snapshot.update({"snapshot_series_id": "B", "snapshot_revision_id": "B-R1", "component_refs": [{"component_type": "DIMENSION_ASSESSMENT", "component_id": "VALID", "revision_id": "VALID-R1", "object_sha256": "c" * 64}]})
        valid_component = {"component_id": "VALID", "component_type": "DIMENSION_ASSESSMENT", "revision_id": "VALID-R1", "object_sha256": "c" * 64, "dimension": "HEALTH_BIOSECURITY", "scope": {}}
        with self.assertRaises(WorldStateCompositionError) as context:
            build_composition_view(query(), [(snapshot, []), (valid_snapshot, [valid_component])], freshness=[], dimensions=sorted(DIMENSIONS))
        self.assertEqual(context.exception.code, "MISSING_COMPONENT_REFERENCE")
        invalid = deepcopy(snapshot)
        invalid["snapshot_series_id"] = "B"
        invalid["snapshot_revision_id"] = "B-R1"
        invalid["visibility"] = "NOT_A_VISIBILITY"
        with self.assertRaises(WorldStateCompositionError) as context:
            build_composition_view(query(), [(snapshot, []), (invalid, [])], freshness=[], dimensions=sorted(DIMENSIONS))
        self.assertEqual(context.exception.code, "INVALID_VISIBILITY")

    def test_freshness_is_per_component_and_stale_remains_visible(self):
        selected = []
        for series, component_id in (("A", "A"), ("B", "B")):
            component = {"component_id": component_id, "component_type": "DIMENSION_ASSESSMENT", "revision_id": component_id + "-R1", "object_sha256": series.lower() * 64, "dimension": "HEALTH_BIOSECURITY", "scope": {"jurisdictions": [series]}}
            snapshot = {"snapshot_series_id": series, "snapshot_revision_id": series + "-R1", "object_sha256": series.lower() * 64, "admission_transaction_id": "TX-" + series, "admitted_at_utc": "2026-09-01T00:00:00Z", "review_transaction_id": "REV-" + series, "knowledge_cutoff_utc": "2026-09-01T00:00:00Z", "visibility": "INTERNAL_ONLY", "component_refs": [{"component_type": component["component_type"], "component_id": component_id, "revision_id": component["revision_id"], "object_sha256": component["object_sha256"]}]}
            selected.append((snapshot, [component]))
        freshness = [{"component_id": "A", "status": "CURRENT"}, {"component_id": "B", "status": "STALE_REVIEW_REQUIRED"}]
        view = build_composition_view(query(), selected, freshness=freshness, dimensions=sorted(DIMENSIONS))
        self.assertEqual([row["status"] for row in view["freshness"]], ["CURRENT", "STALE_REVIEW_REQUIRED"])
        self.assertNotIn("average", json.dumps(view["freshness"]).lower())
        self.assertFalse(view["public_projection_permitted"])

    def test_same_dimension_scopes_remain_multiple_not_global(self):
        rows = []
        for suffix, jurisdiction in (("A", "SYNTH-A"), ("B", "SYNTH-B")):
            row = {"component_id": "H-" + suffix, "component_type": "DIMENSION_ASSESSMENT", "revision_id": "H-" + suffix + "-R1", "object_sha256": (suffix.lower() * 64), "dimension": "HEALTH_BIOSECURITY", "scope": {"jurisdictions": [jurisdiction]}}
            snapshot = {"snapshot_series_id": suffix, "snapshot_revision_id": suffix + "-R1", "object_sha256": suffix.lower() * 64, "admission_transaction_id": "TX-" + suffix, "admitted_at_utc": "2026-09-01T00:00:00Z", "review_transaction_id": "REV-" + suffix, "knowledge_cutoff_utc": "2026-09-01T00:00:00Z", "effective_as_of_utc": None, "scope": {}, "visibility": "INTERNAL_ONLY", "component_refs": [{"component_type": row["component_type"], "component_id": row["component_id"], "revision_id": row["revision_id"], "object_sha256": row["object_sha256"]}]}
            rows.append((snapshot, [row]))
        view = build_composition_view(query(), rows, freshness=[], dimensions=sorted(DIMENSIONS))
        coverage = next(item for item in view["coverage"]["dimensions"] if item["dimension"] == "HEALTH_BIOSECURITY")
        self.assertEqual(coverage["coverage"], "MULTIPLE_SCOPED_ASSESSMENTS")
        self.assertFalse(view["coverage"]["global_coverage_complete"])

    def test_fingerprint_is_order_independent_and_has_no_admission(self):
        base = {"query": query(), "selected_series": [{"snapshot_series_id": "A"}, {"snapshot_series_id": "B"}], "selected_components": [], "coverage": {}, "composition_atomicity": COMPOSITION_ATOMICITY, "limitations": []}
        reordered = deepcopy(base)
        reordered["selected_series"] = list(reversed(reordered["selected_series"]))
        self.assertEqual(composition_fingerprint(base), composition_fingerprint(reordered))
        self.assertIsNone(build_composition_view(query(), [({"snapshot_series_id": "A", "snapshot_revision_id": "A-R1", "object_sha256": "a" * 64, "admission_transaction_id": "TX-A", "admitted_at_utc": "2026-09-01T00:00:00Z", "review_transaction_id": "REV-A", "knowledge_cutoff_utc": "2026-09-01T00:00:00Z", "visibility": "INTERNAL_ONLY", "component_refs": [{"component_type": "DIMENSION_ASSESSMENT", "component_id": "A", "revision_id": "A-R1", "object_sha256": "a" * 64}]}, [{"component_id": "A", "component_type": "DIMENSION_ASSESSMENT", "revision_id": "A-R1", "object_sha256": "a" * 64, "dimension": "HEALTH_BIOSECURITY", "scope": {}}]), ({"snapshot_series_id": "B", "snapshot_revision_id": "B-R1", "object_sha256": "b" * 64, "admission_transaction_id": "TX-B", "admitted_at_utc": "2026-09-01T00:00:00Z", "review_transaction_id": "REV-B", "knowledge_cutoff_utc": "2026-09-01T00:00:00Z", "visibility": "INTERNAL_ONLY", "component_refs": [{"component_type": "DIMENSION_ASSESSMENT", "component_id": "B", "revision_id": "B-R1", "object_sha256": "b" * 64}]}, [{"component_id": "B", "component_type": "DIMENSION_ASSESSMENT", "revision_id": "B-R1", "object_sha256": "b" * 64, "dimension": "MACROECONOMIC_FINANCIAL_CONDITIONS", "scope": {}}])], freshness=[], dimensions=sorted(DIMENSIONS))["admission_transaction_id"])

    def test_composition_delta_reports_series_without_calling_it_world_change(self):
        root = synthetic_root()
        try:
            first = read_production_world_state(query("2026-09-10T00:00:00Z", jurisdictions=["SYNTH-A", "SYNTH-B"]), root=root)
            both = read_production_world_state(query("2026-09-21T00:00:00Z", jurisdictions=["SYNTH-A", "SYNTH-B"]), root=root)
            delta = compare_production_world_state(first, both)
            self.assertEqual(delta["snapshot_series_added"], ["WSSNAP-SYNTH-B"])
            self.assertEqual(delta["delta_class"], "KNOWLEDGE_STATE_CHANGE")
            self.assertTrue(delta["knowledge_state_change"])
            self.assertFalse(delta["effective_state_change"])
        finally:
            shutil.rmtree(root)

    def test_composition_does_not_write_production_or_public_state(self):
        root = synthetic_root()
        try:
            before = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in (root / "data/world_state").rglob("*") if path.is_file()}
            view = read_production_world_state(query(jurisdictions=["SYNTH-A", "SYNTH-B"]), root=root)
            after = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in (root / "data/world_state").rglob("*") if path.is_file()}
            self.assertEqual(before, after)
            self.assertFalse(view["public_projection_permitted"])
            self.assertFalse(view["briefing_read"]["narrative_generated"])
        finally:
            shutil.rmtree(root)


if __name__ == "__main__":
    unittest.main()
