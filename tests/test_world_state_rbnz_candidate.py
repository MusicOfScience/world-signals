from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from world_signals.world_state_history import fingerprint
from world_signals.world_state_rbnz_candidate import (
    ANALYSIS_ID,
    EVIDENCE_IDS,
    MACRO_COMPONENT_ID,
    MARKET_COMPONENT_ID,
    build_rbnz_candidate,
    validate_rbnz_candidate_package,
)


ROOT = Path(__file__).resolve().parents[1]


class WorldStateRbnzCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = build_rbnz_candidate(ROOT)
        cls.protected_before = cls._protected_hashes()

    @staticmethod
    def _protected_hashes():
        paths = []
        for directory in ("canonical", "analysis", "live_intelligence", "signals", "relationships", "risks", "scenarios", "forecasts", "outcomes", "evaluation"):
            paths.extend((ROOT / "data" / directory).rglob("*"))
        paths.extend(ROOT / "data" / "world_state" / name for name in ("components.json", "snapshots.json", "admission_transactions.json"))
        return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(paths) if path.is_file()}

    def test_exact_analysis_and_evidence_are_pinned(self):
        self.assertEqual(self.package["analysis_id"], ANALYSIS_ID)
        self.assertEqual({entry["object_id"] for entry in self.package["source_manifest"] if entry["layer"] == "ANALYSIS_EVIDENCE"}, set(EVIDENCE_IDS))
        self.assertEqual(validate_rbnz_candidate_package(self.package), [])

    def test_two_narrow_scoped_candidates_are_review_pending(self):
        candidates = {row["component_id"]: row for row in self.package["dimension_assessment_candidates"]}
        self.assertEqual(set(candidates), {MACRO_COMPONENT_ID, MARKET_COMPONENT_ID})
        self.assertEqual(candidates[MACRO_COMPONENT_ID]["dimension"], "MACROECONOMIC_FINANCIAL_CONDITIONS")
        self.assertEqual(candidates[MARKET_COMPONENT_ID]["dimension"], "MARKETS_AS_SENSORS")
        for row in candidates.values():
            self.assertEqual(row["review_state"], "UNDER_REVIEW")
            self.assertIsNone(row["admitted_at_utc"])
            self.assertEqual(row["visibility"], "INTERNAL_ONLY")

    def test_known_at_boundaries_are_not_collapsed(self):
        rows = {row["component_id"]: row for row in self.package["dimension_assessment_candidates"]}
        self.assertEqual(rows[MACRO_COMPONENT_ID]["known_at_utc"], "2026-09-02T02:00:00Z")
        self.assertEqual(rows[MARKET_COMPONENT_ID]["known_at_utc"], "2026-09-05T14:40:00Z")
        self.assertNotEqual(rows[MACRO_COMPONENT_ID]["known_at_utc"], rows[MARKET_COMPONENT_ID]["known_at_utc"])

    def test_market_measurements_preserve_null_before_and_alternatives(self):
        market = next(row for row in self.package["dimension_assessment_candidates"] if row["component_id"] == MARKET_COMPONENT_ID)
        self.assertTrue(all(move["before_value"] is None for move in market["market_measurements"]))
        self.assertEqual(market["analytical_association"]["causal_status"], "OBSERVED_ASSOCIATION")
        self.assertFalse(self.package["relationships"])
        self.assertTrue(market["analytical_association"]["alternative_explanations"])

    def test_expectation_bases_remain_distinct(self):
        macro = next(row for row in self.package["dimension_assessment_candidates"] if row["component_id"] == MACRO_COMPONENT_ID)
        self.assertEqual(len(macro["expectation_baselines"]), 2)
        self.assertNotEqual(macro["expectation_baselines"][0]["basis"], macro["expectation_baselines"][1]["basis"])
        self.assertEqual(self.package["baseline_treatment"]["standalone_baseline_candidates"], [])

    def test_actor_is_identity_only_and_unadmitted(self):
        actor = self.package["actor_identity_candidate"]
        self.assertEqual(actor["actor_type"], "CENTRAL_BANK")
        self.assertNotIn("policy_position", actor)
        self.assertNotIn("implementation_state", actor)
        self.assertEqual(self.package["actor_identity_admission"]["status"], "REVIEW_PENDING_UNADMITTED")
        self.assertFalse(self.package["actor_identity_admission"]["production_population_performed"])

    def test_model_provenance_is_fail_honest_and_not_evidence(self):
        for row in self.package["dimension_assessment_candidates"]:
            provenance = row["model_provenance"]
            self.assertEqual(provenance["model_identity"], "UNAVAILABLE")
            self.assertEqual(provenance["model_version"], "UNAVAILABLE")
            self.assertEqual(provenance["factual_evidence_status"], "MODEL_OUTPUT_IS_NOT_FACTUAL_CORROBORATION")

    def test_pending_snapshot_is_not_production_state(self):
        snapshot = self.package["proposed_snapshot"]["snapshot"]
        self.assertIsNone(snapshot["admission_transaction_id"])
        self.assertIsNone(snapshot["admitted_at_utc"])
        self.assertEqual(snapshot["review_state"], "CANDIDATE")
        self.assertEqual(self.package["production_state"], {"actors": 0, "components": 1, "snapshots": 1, "admissions": 1, "writes": []})

    def test_package_fingerprints_reproduce(self):
        again = build_rbnz_candidate(ROOT)
        self.assertEqual(self.package["source_manifest_sha256"], again["source_manifest_sha256"])
        self.assertEqual(self.package["candidate_semantic_fingerprint"], again["candidate_semantic_fingerprint"])
        self.assertEqual(self.package["proposed_snapshot"]["snapshot_semantic_fingerprint"], again["proposed_snapshot"]["snapshot_semantic_fingerprint"])

    def test_no_real_world_state_or_public_projection_is_written(self):
        self.assertFalse((ROOT / "data/world_state/actor_registry.json").exists())
        self.assertEqual(self.package["public_projection_permitted"], False)
        self.assertFalse(self.package["actor_state_assertions"])
        self.assertFalse(self.package["implementation_claims"])
        self.assertFalse(self.package["forecasts"])

    def test_candidate_build_does_not_mutate_production_or_upstream_inputs(self):
        build_rbnz_candidate(ROOT)
        self.assertEqual(self.protected_before, self._protected_hashes())
        production = json.loads((ROOT / "data/world_state/components.json").read_text())
        self.assertEqual(len(production["components"]), 1)

    def test_package_mutation_is_detectable(self):
        changed = deepcopy(self.package)
        changed["source_manifest"][0]["object"]["tampered"] = True
        self.assertNotEqual(changed["source_manifest_sha256"], fingerprint(changed["source_manifest"]))

    def test_retained_package_matches_builder(self):
        path = ROOT / "data/world_state_audit/STEP11A_RBNZ_CANDIDATE_REVIEW_PENDING.json"
        if path.exists():
            retained = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(retained, self.package)
