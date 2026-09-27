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

from world_signals.world_state_production import (  # noqa: E402
    WorldStateProductionReadError,
    compare_production_world_state,
    read_production_world_state,
    successor_preflight,
    validate_production_read_request,
)
from world_signals.world_state_read import read_world_state  # noqa: E402
from world_signals.world_state_history import DIMENSIONS  # noqa: E402


COMPONENT_ID = "WSDIM-HEALTH-COD-BVD-REPORTED-BURDEN-202609-001"
SNAPSHOT_ID = "WSSNAP-HEALTH-COD-BVD-202609-R1"
ADMISSION_ID = "WS-ADMISSION-HEALTH-COD-BVD-20260927-001"


def query(
    knowledge: str = "2026-09-27T15:14:00Z",
    *,
    mode: str = "KNOWLEDGE_AS_OF",
    effective: str | None = None,
    dimensions: list[str] | None = None,
    jurisdictions: list[str] | None = None,
) -> dict:
    return {
        "query_mode": mode,
        "knowledge_cutoff_utc": knowledge,
        "effective_as_of_utc": effective,
        "scope": {
            "dimensions": dimensions or [],
            "jurisdictions": jurisdictions or [],
            "systems": [],
            "component_ids": [],
        },
        "include_withdrawn_history": False,
    }


def production_file_hashes(root: Path = ROOT) -> dict[str, str]:
    directory = root / "data" / "world_state"
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def upstream_file_hashes(root: Path = ROOT) -> dict[str, str]:
    directories = ("canonical", "live_intelligence", "analysis", "signals", "relationships", "risks", "scenarios", "forecasts", "outcomes", "evaluation")
    paths = [path for directory in directories for path in (root / "data" / directory).rglob("*") if path.is_file()]
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)
    }


class WorldStateProductionReadTests(unittest.TestCase):
    def test_production_history_is_valid_and_crosslinked(self):
        view = read_production_world_state(query())
        self.assertEqual(view["status"], "ADMITTED_ASSESSMENT_AVAILABLE")
        self.assertEqual(view["selected_snapshot"]["snapshot_revision_id"], SNAPSHOT_ID)
        self.assertEqual(view["admission_refs"][0]["transaction_id"], ADMISSION_ID)
        self.assertEqual(view["production_counts"], {"actors": 0, "components": 1, "snapshots": 1, "admissions": 1})
        self.assertIn("CANONICAL_HISTORICAL_AS_OF_UNSUPPORTED", view["limitations"])

    def test_explicit_query_contract_rejects_implicit_latest_and_missing_effective_cutoff(self):
        with self.assertRaises(WorldStateProductionReadError):
            validate_production_read_request({"latest": True})
        with self.assertRaises(WorldStateProductionReadError):
            validate_production_read_request(query(mode="EFFECTIVE_AS_OF"))

    def test_invalid_timestamp_and_dimension_are_rejected(self):
        bad = query(knowledge="2026-09-27T15:14:00+00:00")
        with self.assertRaises(WorldStateProductionReadError):
            validate_production_read_request(bad)
        bad = query(dimensions=["NOT_A_DIMENSION"])
        with self.assertRaises(WorldStateProductionReadError):
            validate_production_read_request(bad)

    def test_snapshot_and_component_refs_resolve_exact_hashes(self):
        view = read_production_world_state(query())
        snapshot_ref = view["selected_snapshot"]["component_refs"][0]
        component = view["selected_components"][0]
        self.assertEqual(snapshot_ref["component_id"], component["component_id"])
        self.assertEqual(snapshot_ref["revision_id"], component["revision_id"])
        self.assertEqual(snapshot_ref["object_sha256"], component["object_sha256"])

    def test_knowledge_before_admission_returns_no_production_state(self):
        view = read_production_world_state(query("2026-09-27T15:13:57Z"))
        self.assertEqual(view["component_count"], 0)
        self.assertEqual(view["status"], "NO_ADMITTED_ASSESSMENT")
        self.assertIsNone(view["selected_snapshot"])

    def test_knowledge_after_admission_selects_r1(self):
        view = read_production_world_state(query())
        self.assertEqual([row["revision_id"] for row in view["selected_components"]], [COMPONENT_ID + "-R1"])

    def test_effective_before_date_excludes_component(self):
        view = read_production_world_state(query(mode="EFFECTIVE_AS_OF", effective="2026-08-29T23:59:59Z"))
        self.assertEqual(view["component_count"], 0)

    def test_effective_on_civil_date_selects_without_inventing_utc(self):
        view = read_production_world_state(query(mode="EFFECTIVE_AS_OF", effective="2026-08-30T00:00:00Z"))
        component = view["selected_components"][0]
        self.assertEqual(view["component_count"], 1)
        self.assertIsNone(component["effective_at"])
        self.assertEqual(component["effective_date"], "2026-08-30")
        self.assertEqual(component["effective_time_precision"], "CIVIL_DATE")

    def test_scoped_dimension_and_jurisdiction_remain_narrow(self):
        view = read_production_world_state(query(dimensions=["HEALTH_BIOSECURITY"], jurisdictions=["Democratic Republic of the Congo"]))
        component = view["selected_components"][0]
        self.assertEqual(component["scope"]["systems"], ["REPORTED_BUNDIBUGYO_OUTBREAK_BURDEN"])
        self.assertEqual(view["dimensions_assessed"], ["HEALTH_BIOSECURITY"])
        self.assertNotIn("HEALTH_BIOSECURITY", view["dimensions_unassessed"])

    def test_other_dimensions_are_unassessed_not_inferred(self):
        view = read_production_world_state(query())
        self.assertEqual(view["dimensions_assessed"], ["HEALTH_BIOSECURITY"])
        self.assertEqual(set(view["dimensions_unassessed"]), DIMENSIONS - {"HEALTH_BIOSECURITY"})
        self.assertEqual(view["briefing_read"]["narrative_generated"], False)

    def test_freshness_is_current_before_review_window(self):
        view = read_production_world_state(query("2026-09-27T16:00:00Z"))
        self.assertEqual(view["freshness"][0]["status"], "CURRENT")

    def test_freshness_enters_review_due_soon_window(self):
        view = read_production_world_state(query("2026-10-01T00:00:00Z"))
        self.assertEqual(view["freshness"][0]["status"], "REVIEW_DUE_SOON")

    def test_freshness_at_due_and_after_due_are_distinct(self):
        due = read_production_world_state(query("2026-10-06T07:41:00Z"))
        stale = read_production_world_state(query("2026-10-06T07:41:01Z"))
        self.assertEqual(due["freshness"][0]["status"], "REVIEW_DUE")
        self.assertEqual(stale["freshness"][0]["status"], "STALE_REVIEW_REQUIRED")

    def test_freshness_does_not_mutate_lifecycle_or_component_hash(self):
        before = production_file_hashes()
        first = read_production_world_state(query("2026-09-27T16:00:00Z"))
        second = read_production_world_state(query("2026-10-07T00:00:00Z"))
        after = production_file_hashes()
        self.assertEqual(first["selected_components"][0]["lifecycle_state"], "ACTIVE")
        self.assertEqual(second["selected_components"][0]["lifecycle_state"], "ACTIVE")
        self.assertEqual(first["selected_components"][0]["object_sha256"], second["selected_components"][0]["object_sha256"])
        self.assertEqual(before, after)

    def test_first_admission_is_knowledge_change_not_effective_change(self):
        before = read_production_world_state(query("2026-09-27T15:13:57Z"))
        after = read_production_world_state(query("2026-09-27T15:14:00Z"))
        delta = compare_production_world_state(before, after)
        self.assertEqual(delta["delta_class"], "KNOWLEDGE_STATE_CHANGE")
        self.assertTrue(delta["knowledge_state_change"])
        self.assertFalse(delta["effective_state_change"])
        self.assertEqual(delta["components_added"], [COMPONENT_ID])

    def test_same_admitted_content_is_no_change(self):
        first = read_production_world_state(query("2026-09-27T15:14:00Z"))
        second = read_production_world_state(query("2026-09-27T16:00:00Z"))
        delta = compare_production_world_state(first, second)
        self.assertEqual(delta["delta_class"], "NO_CHANGE")
        self.assertEqual(delta["components_unchanged"], [COMPONENT_ID])
        self.assertFalse(delta["freshness_only"])

    def test_freshness_transition_is_separate_from_content_delta(self):
        first = read_production_world_state(query("2026-09-27T16:00:00Z"))
        second = read_production_world_state(query("2026-10-01T00:00:00Z"))
        delta = compare_production_world_state(first, second)
        self.assertEqual(delta["delta_class"], "NO_CHANGE")
        self.assertTrue(delta["freshness_only"])
        self.assertEqual(delta["freshness_transitions"][0]["from"], "CURRENT")
        self.assertEqual(delta["freshness_transitions"][0]["to"], "REVIEW_DUE_SOON")

    def test_effective_delta_is_distinguished(self):
        before = read_production_world_state(query(mode="EFFECTIVE_AS_OF", effective="2026-08-29T23:59:59Z"))
        after = read_production_world_state(query(mode="EFFECTIVE_AS_OF", effective="2026-08-30T00:00:00Z"))
        delta = compare_production_world_state(before, after)
        self.assertEqual(delta["delta_class"], "EFFECTIVE_STATE_CHANGE")
        self.assertTrue(delta["effective_state_change"])
        self.assertFalse(delta["knowledge_state_change"])

    def test_stale_does_not_create_successor(self):
        view = read_production_world_state(query("2026-10-07T00:00:00Z"))
        result = successor_preflight(view)
        self.assertEqual(result["result"], "REVIEW_DUE")
        self.assertFalse(result["successor_revision_created"])
        self.assertFalse(result["production_write_performed"])

    def test_successor_preflight_distinguishes_evidence_and_correction(self):
        view = read_production_world_state(query())
        self.assertEqual(successor_preflight(view, new_governed_evidence=True)["result"], "NEW_GOVERNED_EVIDENCE_AVAILABLE")
        self.assertEqual(successor_preflight(view, correction_or_retraction=True)["result"], "CORRECTION_OR_CONTRADICTION_REQUIRES_REVIEW")
        self.assertEqual(successor_preflight(view, contradiction=True)["result"], "CORRECTION_OR_CONTRADICTION_REQUIRES_REVIEW")

    def test_internal_briefing_read_preserves_coverage_and_visibility(self):
        briefing = read_production_world_state(query())["briefing_read"]
        health = next(row for row in briefing["dimensions"] if row["dimension"] == "HEALTH_BIOSECURITY")
        self.assertEqual(health["coverage"], "SCOPED_ASSESSMENT_AVAILABLE")
        self.assertEqual(health["assessment"]["qualitative_confidence"], "LOW")
        self.assertEqual(health["assessment"]["visibility"], "INTERNAL_ONLY")
        self.assertFalse(briefing["public_projection_permitted"])
        self.assertEqual(briefing["narrative_generated"], False)

    def test_explicit_production_query_integrates_with_evidence_reader(self):
        evidence_request = {
            "contract_version": "0.1",
            "as_of_utc": "2026-09-27T16:00:00Z",
            "scope": {"jurisdictions": ["*"], "dimensions": sorted(DIMENSIONS), "actor_ids": None},
            "include_negative_evidence": True,
            "input_policy": "ACCEPTED_REVIEWED_HEADS_ONLY",
        }
        proposal = read_world_state(evidence_request, production_query=query("2026-09-27T16:00:00Z"))
        self.assertEqual(proposal["production_world_state"]["status"], "ADMITTED_ASSESSMENT_AVAILABLE")
        self.assertEqual(proposal["production_world_state"]["component_count"], 1)
        self.assertNotIn("WORLD_STATE_ASSESSMENT_NOT_SYNTHESISED", {row["code"] for row in proposal["limitations"]})

    def test_legacy_evidence_read_does_not_silently_change_contract(self):
        evidence_request = {
            "contract_version": "0.1",
            "as_of_utc": "2026-09-27T16:00:00Z",
            "scope": {"jurisdictions": ["*"], "dimensions": sorted(DIMENSIONS), "actor_ids": None},
            "include_negative_evidence": True,
            "input_policy": "ACCEPTED_REVIEWED_HEADS_ONLY",
        }
        proposal = read_world_state(evidence_request)
        self.assertNotIn("production_world_state", proposal)
        self.assertIn("WORLD_STATE_ASSESSMENT_NOT_SYNTHESISED", {row["code"] for row in proposal["limitations"]})

    def test_production_history_read_is_deterministic(self):
        first = read_production_world_state(query())
        second = read_production_world_state(query())
        self.assertEqual(first["semantic_fingerprint"], second["semantic_fingerprint"])
        self.assertEqual(first, second)

    def test_tampered_snapshot_reference_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory)
            shutil.copytree(ROOT / "data" / "world_state", temp_root / "data" / "world_state")
            path = temp_root / "data" / "world_state" / "snapshots.json"
            document = json.loads(path.read_text(encoding="utf-8"))
            document["snapshots"][0]["component_refs"][0]["object_sha256"] = "0" * 64
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(WorldStateProductionReadError):
                read_production_world_state(query(), root=temp_root)

    def test_reads_do_not_write_production_state_or_public_projection(self):
        before = production_file_hashes()
        upstream_before = upstream_file_hashes()
        view = read_production_world_state(query())
        after = production_file_hashes()
        upstream_after = upstream_file_hashes()
        self.assertEqual(view["production_file_mutation_check"]["status"], "PASS")
        self.assertEqual(before, after)
        self.assertEqual(upstream_before, upstream_after)
        self.assertEqual(len(view["selected_components"]), 1)
        self.assertFalse((ROOT / "data" / "world_state" / "state.json").exists())
        self.assertFalse(view["briefing_read"]["public_projection_permitted"])

    def test_production_population_remains_exactly_one_component_snapshot_admission_and_no_actors(self):
        view = read_production_world_state(query())
        self.assertEqual(view["component_count"], 1)
        self.assertEqual(len(view["selected_snapshot"]["component_refs"]), 1)
        self.assertEqual(view["selected_snapshot"]["admission_transaction_id"], ADMISSION_ID)
        self.assertEqual(view["selected_components"][0]["component_id"], COMPONENT_ID)


if __name__ == "__main__":
    unittest.main()
