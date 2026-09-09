from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import apply_un_correct_map_live_bf as bf
from world_signals.live_intelligence import public_live_intelligence_projection, validate_live_intelligence


class UNCorrectMapLiveBFTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = bf.load(bf.PLAN_PATH)
        cls.payload = bf.load(bf.PAYLOAD_PATH)
        cls.schema = bf.load(bf.LIVE_SCHEMA_PATH)
        cls.observations = bf.load(bf.LIVE_OBSERVATIONS_PATH)
        cls.evidence = bf.load(bf.LIVE_EVIDENCE_PATH)
        cls.canonical = bf.load(bf.CANONICAL_PATH)

    def simulate(self):
        return (
            bf.target_live_schema(self.schema, self.plan),
            bf.target_observations(self.observations, self.payload),
            bf.target_evidence(self.evidence, self.payload),
        )

    def validate(self, schema=None, observations=None, evidence=None):
        return validate_live_intelligence(
            schema or self.schema,
            evidence or self.evidence,
            observations or self.observations,
            self.canonical,
        )

    def test_plan_freezes_exact_post_be_prestate_and_bounded_target(self):
        self.assertEqual(self.plan["exact_base_main_sha"], "629ab595ecccaf86a92bbd8cdfdab4297496b298")
        self.assertEqual(self.plan["pre_state"]["live_schema_version"], "0.5")
        self.assertEqual(self.plan["pre_state"]["live_observation_count"], 5)
        self.assertEqual(self.plan["pre_state"]["live_evidence_count"], 7)
        self.assertEqual(self.plan["target_state"]["live_schema_version"], "0.6")
        self.assertEqual(self.plan["target_state"]["live_observation_count"], 6)
        self.assertEqual(self.plan["target_state"]["live_evidence_count"], 9)
        self.assertTrue(self.plan["gates"]["seventh_live_observation_requires_new_pressure_audit"])
        self.assertTrue(self.plan["manual_merge_only"])

    def test_payload_is_one_primary_confirmed_institutional_development(self):
        self.assertEqual(len(self.payload["live_evidence"]), 2)
        row = self.payload["live_observation"]
        self.assertEqual(row["observation_id"], "WSLI-INST-UNGA-CORRECTMAP-20260904-001")
        self.assertEqual(row["observation_type"], "INSTITUTIONAL_DEVELOPMENT")
        self.assertEqual(row["verification_state"], "PRIMARY_CONFIRMED")
        self.assertEqual(row["canonical_links"], [])
        self.assertIsNone(row["revision_of_observation_id"])
        self.assertEqual(row["regions"], ["Global"])
        self.assertEqual(row["domain_tags"], ["INSTITUTIONS", "POLITICS"])
        self.assertTrue(all(e["evidence_class"] == "PRIMARY_OFFICIAL" for e in self.payload["live_evidence"]))
        self.assertTrue(all(e["canonical_provenance_effect"] == "NONE" for e in self.payload["live_evidence"]))

    def test_vote_identity_and_civil_date_precision_are_frozen(self):
        selection = self.plan["selection"]
        self.assertEqual(selection["resolution_symbol"], "A/RES/80/307")
        self.assertEqual(selection["draft_symbol"], "A/80/L.104")
        self.assertEqual(selection["meeting_record"], "A/80/PV.114")
        self.assertEqual(selection["recorded_vote"], {"in_favour": 164, "against": 1, "abstentions": 6})
        self.assertEqual(self.payload["live_observation"]["event_time"], {"precision": "CIVIL_DATE", "event_date": "2026-09-04"})
        for e in self.payload["live_evidence"]:
            self.assertEqual(e["publication_time"], {"precision": "CIVIL_DATE", "published_date": "2026-09-04"})

    def test_payload_explicitly_avoids_overclaiming(self):
        summary = self.payload["live_observation"]["summary"].lower()
        self.assertIn("does not claim", summary)
        self.assertIn("compulsory single world map", summary)
        self.assertIn("borders or sovereignty", summary)
        self.assertIn("market consequence", summary)
        forbidden = {
            "what_was_expected", "what_surprised", "what_moved", "what_appears_connected",
            "what_may_be_noise", "alternative_explanations", "second_order_effects",
            "falsifiers", "causal_status", "confidence", "analytical_conclusion",
        }
        self.assertFalse(forbidden & set(self.payload["live_observation"]))

    def test_simulated_target_validates_with_exact_bf_population(self):
        schema, observations, evidence = self.simulate()
        report = self.validate(schema=schema, observations=observations, evidence=evidence)
        self.assertTrue(report.ok, report.errors)
        self.assertGreaterEqual(tuple(map(int, schema["version"].split("."))), (0, 6))
        self.assertGreaterEqual(tuple(map(int, observations["version"].split("."))), (0, 6))
        self.assertGreaterEqual(tuple(map(int, evidence["version"].split("."))), (0, 6))
        self.assertGreaterEqual(len(observations["observations"]), 6)
        self.assertGreaterEqual(len(evidence["evidence"]), 9)
        self.assertEqual(observations["population_state"], "CONTROLLED_INSTITUTIONAL_SPECIMEN")
        bf_obs = next(row for row in observations["observations"] if row.get("observation_id") == "WSLI-INST-UNGA-CORRECTMAP-20260904-001")
        self.assertEqual(bf_obs, self.payload["live_observation"])
        evidence_by_id = {row["evidence_id"]: row for row in evidence["evidence"]}
        for historical in self.payload["live_evidence"]:
            self.assertEqual(evidence_by_id[historical["evidence_id"]], historical)

    def test_schema_preserves_bd_checkpoint_and_all_public_automation_gates_closed(self):
        schema, observations, evidence = self.simulate()
        self.assertEqual(schema["bd_checkpoint"]["schema_version"], "0.5")
        self.assertEqual(schema["bd_checkpoint"]["observation_count"], 5)
        self.assertEqual(schema["bd_checkpoint"]["evidence_count"], 7)
        policy = schema["population_policy"]
        self.assertEqual(policy["mode"], "CONTROLLED_INSTITUTIONAL_SPECIMEN")
        self.assertGreaterEqual(policy["maximum_observation_count"], 6)
        self.assertGreaterEqual(policy["maximum_evidence_count"], 9)
        self.assertFalse(policy["automatic_ingestion_allowed"])
        self.assertFalse(policy["public_observation_projection_allowed"])
        public = public_live_intelligence_projection(schema, evidence, observations, self.canonical)
        self.assertEqual(public["observations"], [])

    def test_population_overflow_fails_closed(self):
        schema, observations, evidence = self.simulate()
        overflow = copy.deepcopy(observations)
        extra = copy.deepcopy(self.payload["live_observation"])
        extra["observation_id"] = "WSLI-TEST-BF-OVERFLOW"
        overflow["observations"].append(extra)
        report = self.validate(schema=schema, observations=overflow, evidence=evidence)
        self.assertFalse(report.ok)
        self.assertTrue(any("exceeds reviewed policy maximum" in err for err in report.errors), report.errors)

    def test_bf_target_functions_leave_analysis_contract_unchanged(self):
        reviews = bf.load(bf.REVIEWS_PATH)
        evidence = bf.load(bf.ANALYSIS_EVIDENCE_PATH)
        self.assertGreaterEqual(len(reviews["reviews"]), 21)
        self.assertGreaterEqual(len(evidence["evidence"]), 95)
        self.assertGreaterEqual(bf.production_live_input_count(reviews), 1)
        self.assertGreaterEqual(bf.analysis_revision_count(reviews), 0)
        self.assertGreaterEqual(bf.exact_series_count(reviews), 0)

    def test_status_and_roadmap_targets_record_bf_without_rewriting_history(self):
        target_status = bf.target_status(bf.STATUS_PATH.read_text(encoding="utf-8"))
        target_roadmap = bf.target_roadmap(bf.ROADMAP_PATH.read_text(encoding="utf-8"))
        self.assertIn("POST-BE / BF SIXTH LIVE INSTITUTIONAL SPECIMEN", target_status)
        self.assertIn("v0.6 / 6 reviewed internal observations / 9 primary-official evidence rows", target_status)
        self.assertIn("### BF — sixth Live institutional specimen", target_roadmap)
        self.assertIn("# WORLD SIGNALS — project status / branch-recovery checkpoint", target_status)

    def test_reviewed_bf_descendant_is_idempotent_and_not_downgraded(self):
        schema, observations, evidence = self.simulate()
        self.assertEqual(bf.target_live_schema(schema, self.plan), schema)
        self.assertEqual(bf.target_observations(observations, self.payload), observations)
        self.assertEqual(bf.target_evidence(evidence, self.payload), evidence)


if __name__ == "__main__":
    unittest.main()
