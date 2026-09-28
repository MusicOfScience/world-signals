from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from world_signals.world_state_history import validate_actor_registry
from world_signals.world_state_rbnz_candidate import (
    ANALYSIS_ID,
    MACRO_COMPONENT_ID,
    MARKET_COMPONENT_ID,
    build_corrected_rbnz_candidate,
    validate_corrected_rbnz_candidate_package,
)


ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "data/world_state_audit/STEP11A_RBNZ_CANDIDATE_REVIEW_PENDING.json"


class WorldStateRbnzTemporalIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_bytes = ORIGINAL.read_bytes()
        cls.original_sha256 = hashlib.sha256(cls.original_bytes).hexdigest()
        cls.corrected = build_corrected_rbnz_candidate(ROOT)

    @staticmethod
    def _protected_hashes():
        paths = []
        for directory in (
            "canonical",
            "analysis",
            "live_intelligence",
            "signals",
            "relationships",
            "risks",
            "scenarios",
            "forecasts",
            "outcomes",
            "evaluation",
        ):
            paths.extend((ROOT / "data" / directory).rglob("*"))
        paths.extend(
            ROOT / "data" / "world_state" / name
            for name in ("components.json", "snapshots.json", "admission_transactions.json")
        )
        return {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths)
            if path.is_file()
        }

    def test_original_step11a_artifact_is_preserved_byte_for_byte(self):
        self.assertEqual(ORIGINAL.read_bytes(), self.original_bytes)
        self.assertEqual(self.original_sha256, "38ac088534f7f61c60be0e528894aec0e0d167a7a7abcada3b40f53de698add3")
        self.assertEqual(self.corrected["correction_lineage"]["predecessor_candidate_fingerprint"], "455ac3d2402ac7370fe6b4a4b5b69fbc666183dd57a191c3da23525a85b3dc39")

    def test_macro_effective_time_can_precede_corrected_known_at(self):
        macro = next(row for row in self.corrected["dimension_assessment_candidates"] if row["component_id"] == MACRO_COMPONENT_ID)
        self.assertEqual(macro["effective_at"], "2026-09-02T02:00:00Z")
        self.assertEqual(macro["known_at_utc"], "2026-09-05T14:40:00Z")
        self.assertEqual(macro["known_at_basis"], "ANALYSIS_REVIEW_BOUNDARY_FOR_COMPARATIVE_FORWARD_PATH_PROPOSITION")

    def test_official_only_and_comparative_propositions_remain_distinct(self):
        macro = next(row for row in self.corrected["dimension_assessment_candidates"] if row["component_id"] == MACRO_COMPONENT_ID)
        parts = {part["part"]: part for part in macro["proposition_parts"]}
        self.assertEqual(parts["OFFICIAL_DECISION"]["known_at_utc"], "2026-09-02T02:00:00Z")
        self.assertEqual(parts["COMPARATIVE_FORWARD_PATH"]["known_at_utc"], "2026-09-05T14:40:00Z")
        self.assertNotEqual(parts["OFFICIAL_DECISION"]["basis"], parts["COMPARATIVE_FORWARD_PATH"]["basis"])

    def test_market_event_anchor_is_not_exact_movement_time(self):
        market = next(row for row in self.corrected["dimension_assessment_candidates"] if row["component_id"] == MARKET_COMPONENT_ID)
        self.assertIsNone(market["effective_at"])
        self.assertEqual(market["effective_date"], "2026-09-02")
        self.assertEqual(market["effective_time_precision"], "CIVIL_DATE")
        self.assertIsNone(market["effective_window"]["exact_start_at_utc"])
        self.assertIsNone(market["effective_window"]["exact_end_at_utc"])
        self.assertEqual(market["known_at_utc"], "2026-09-05T14:40:00Z")

    def test_market_measurements_and_null_before_values_are_unchanged(self):
        market = next(row for row in self.corrected["dimension_assessment_candidates"] if row["component_id"] == MARKET_COMPONENT_ID)
        self.assertEqual([move["before_value"] for move in market["market_measurements"]], [None, None])
        self.assertEqual([move["change"] for move in market["market_measurements"]], [-3, -0.7])
        self.assertEqual(market["analytical_association"]["causal_status"], "OBSERVED_ASSOCIATION")

    def test_pending_snapshot_has_no_single_exact_effective_instant(self):
        snapshot = self.corrected["proposed_snapshot"]["snapshot"]
        self.assertIsNone(snapshot["effective_as_of_utc"])
        self.assertEqual(snapshot["effective_date"], "2026-09-02")
        self.assertEqual(snapshot["effective_time_precision"], "CIVIL_DATE")
        self.assertEqual(snapshot["review_state"], "CANDIDATE")

    def test_actor_identity_temporal_contract_is_explicit_and_valid(self):
        actor = self.corrected["actor_identity_candidate"]
        self.assertEqual(actor["effective_from"], None)
        self.assertEqual(actor["effective_from_precision"], "UNKNOWN")
        self.assertEqual(actor["identity_known_at_utc"], "2026-09-05T14:40:00Z")
        self.assertEqual(validate_actor_registry({"actors": [actor], "relationships": []}), [])
        self.assertNotIn("implementation_state", actor)

    def test_actor_simulation_is_temporary_and_population_stays_zero(self):
        simulation = self.corrected["actor_identity_admission"]["simulation"]
        self.assertEqual(simulation["status"], "PASS")
        self.assertFalse(simulation["production_write_performed"])
        self.assertEqual(self.corrected["production_state"]["actors"], 0)
        self.assertEqual(self.corrected["actor_identity_admission"]["production_population_performed"], False)

    def test_correction_keeps_candidates_pending_and_admission_closed(self):
        self.assertEqual(validate_corrected_rbnz_candidate_package(self.corrected), [])
        self.assertEqual(self.corrected["correction_review"]["status"], "REVIEW_PENDING")
        for disposition in self.corrected["correction_review"]["component_readiness"].values():
            self.assertIn(disposition, {"READY_FOR_HUMAN_COMPONENT_REVIEW", "DEFER_IDENTITY_TEMPORAL_CONTRACT"})
        self.assertFalse(self.corrected["public_projection_permitted"])
        self.assertEqual(self.corrected["production_state"]["writes"], [])

    def test_source_manifest_is_unchanged(self):
        self.assertEqual(self.corrected["source_manifest_sha256"], "b5eecfedcc9b0d6ae6572e52b394e9157116ced7d8d8393c9e8189b6300ba8d4")
        self.assertEqual(self.corrected["source_manifest_sha256"], build_corrected_rbnz_candidate(ROOT)["source_manifest_sha256"])

    def test_fingerprints_reproduce_after_correction(self):
        again = build_corrected_rbnz_candidate(ROOT)
        self.assertEqual(self.corrected["candidate_semantic_fingerprint"], again["candidate_semantic_fingerprint"])
        self.assertEqual(self.corrected["proposed_snapshot"]["snapshot_semantic_fingerprint"], again["proposed_snapshot"]["snapshot_semantic_fingerprint"])
        self.assertNotEqual(self.corrected["candidate_semantic_fingerprint"], self.corrected["correction_lineage"]["predecessor_candidate_fingerprint"])

    def test_retained_corrected_artifact_matches_deterministic_builder(self):
        retained = json.loads(
            (ROOT / "data/world_state_audit/STEP11A1_RBNZ_CANDIDATE_REVIEW_PENDING_CORRECTED.json").read_text(encoding="utf-8")
        )
        self.assertEqual(retained, self.corrected)

    def test_no_production_component_snapshot_or_admission_is_created(self):
        self.assertEqual(self.corrected["production_state"], {"actors": 0, "components": 1, "snapshots": 1, "admissions": 1, "writes": []})
        self.assertFalse((ROOT / "data/world_state/actor_registry.json").exists())
        self.assertEqual(self.corrected["relationships"], [])
        self.assertEqual(self.corrected["implementation_claims"], [])

    def test_original_file_remains_identical_after_repeated_builds(self):
        build_corrected_rbnz_candidate(ROOT)
        self.assertEqual(ORIGINAL.read_bytes(), self.original_bytes)

    def test_correction_build_does_not_mutate_production_or_upstream_inputs(self):
        before = self._protected_hashes()
        build_corrected_rbnz_candidate(ROOT)
        after = self._protected_hashes()
        self.assertEqual(before, after)
