from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import apply_vietnam_myanmar_live_bd as bd
from world_signals.live_intelligence import public_live_intelligence_projection, validate_live_intelligence


class VietnamMyanmarLiveBDTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = bd.load(bd.PLAN_PATH)
        cls.payload = bd.load(bd.PAYLOAD_PATH)
        cls.schema = bd.load(bd.LIVE_SCHEMA_PATH)
        cls.observations = bd.load(bd.LIVE_OBSERVATIONS_PATH)
        cls.evidence = bd.load(bd.LIVE_EVIDENCE_PATH)
        cls.canonical = bd.load(bd.CANONICAL_PATH)

    def simulate(self):
        return (
            bd.target_live_schema(self.schema, self.plan),
            bd.target_observations(self.observations, self.payload),
            bd.target_evidence(self.evidence, self.payload),
        )

    def validate(self, schema=None, observations=None, evidence=None):
        schema = schema or self.schema
        observations = observations or self.observations
        evidence = evidence or self.evidence
        return validate_live_intelligence(schema, evidence, observations, self.canonical)

    def test_plan_freezes_exact_post_bc_prestate_and_bounded_target(self):
        self.assertEqual(self.plan["exact_base_main_sha"], "667d0fbcc92f937b0cb609d619b664a2a97e8165")
        self.assertEqual(self.plan["pre_state"]["live_schema_version"], "0.4")
        self.assertEqual(self.plan["pre_state"]["live_observation_count"], 4)
        self.assertEqual(self.plan["pre_state"]["live_evidence_count"], 6)
        self.assertEqual(self.plan["target_state"]["live_schema_version"], "0.5")
        self.assertEqual(self.plan["target_state"]["live_observation_count"], 5)
        self.assertEqual(self.plan["target_state"]["live_evidence_count"], 7)
        self.assertTrue(self.plan["gates"]["sixth_live_observation_requires_new_pressure_audit"])

    def test_payload_is_one_primary_official_geopolitical_observation(self):
        self.assertEqual(len(self.payload["live_evidence"]), 1)
        row = self.payload["live_observation"]
        evidence = self.payload["live_evidence"][0]
        self.assertEqual(row["observation_id"], "WSLI-GEO-VNM-MMR-SECURITY-20260905-001")
        self.assertEqual(row["observation_type"], "GEOPOLITICAL_DEVELOPMENT")
        self.assertEqual(row["verification_state"], "PRIMARY_CONFIRMED")
        self.assertEqual(row["canonical_links"], [])
        self.assertIsNone(row["revision_of_observation_id"])
        self.assertEqual(evidence["evidence_class"], "PRIMARY_OFFICIAL")
        self.assertEqual(evidence["canonical_provenance_effect"], "NONE")

    def test_publication_timestamp_does_not_become_event_timestamp(self):
        row = self.payload["live_observation"]
        evidence = self.payload["live_evidence"][0]
        self.assertEqual(
            evidence["publication_time"],
            {"precision": "EXACT_TIMESTAMP", "published_at_utc": "2026-09-05T09:16:00Z"},
        )
        self.assertEqual(row["event_time"], {"precision": "CIVIL_DATE", "event_date": "2026-09-05"})
        self.assertNotIn("event_at_utc", row["event_time"])
        self.assertNotIn("event_local", row["event_time"])

    def test_payload_contains_no_analysis_only_or_causal_fields(self):
        forbidden = {
            "what_was_expected", "what_surprised", "what_moved", "what_appears_connected",
            "what_may_be_noise", "alternative_explanations", "second_order_effects",
            "falsifiers", "causal_status", "confidence", "analytical_conclusion",
        }
        self.assertFalse(forbidden & set(self.payload["live_observation"]))
        summary = self.payload["live_observation"]["summary"].lower()
        self.assertIn("without inferring", summary)

    def test_simulated_target_validates_and_has_exact_bd_population(self):
        schema, observations, evidence = self.simulate()
        report = self.validate(schema=schema, observations=observations, evidence=evidence)
        self.assertTrue(report.ok, report.errors)
        self.assertEqual(schema["version"], "0.5")
        self.assertEqual(observations["version"], "0.5")
        self.assertEqual(evidence["version"], "0.5")
        self.assertEqual(len(observations["observations"]), 5)
        self.assertEqual(len(evidence["evidence"]), 7)
        self.assertEqual(observations["population_state"], "CONTROLLED_GEOPOLITICAL_SPECIMEN")

    def test_schema_preserves_az_checkpoint_and_closes_public_automation_gates(self):
        schema, observations, evidence = self.simulate()
        self.assertEqual(schema["az_checkpoint"]["schema_version"], "0.4")
        self.assertEqual(schema["az_checkpoint"]["observation_count"], 4)
        self.assertEqual(schema["az_checkpoint"]["evidence_count"], 6)
        policy = schema["population_policy"]
        self.assertEqual(policy["maximum_observation_count"], 5)
        self.assertEqual(policy["maximum_evidence_count"], 7)
        self.assertFalse(policy["automatic_ingestion_allowed"])
        self.assertFalse(policy["public_observation_projection_allowed"])
        public = public_live_intelligence_projection(schema, evidence, observations, self.canonical)
        self.assertEqual(public["observations"], [])

    def test_population_overflow_fails_closed(self):
        schema, observations, evidence = self.simulate()
        overflow = copy.deepcopy(observations)
        extra = copy.deepcopy(self.payload["live_observation"])
        extra["observation_id"] = "WSLI-TEST-BD-OVERFLOW"
        overflow["observations"].append(extra)
        report = self.validate(schema=schema, observations=overflow, evidence=evidence)
        self.assertFalse(report.ok)
        self.assertTrue(any("exceeds reviewed policy maximum" in err for err in report.errors), report.errors)

    def test_bd_target_functions_do_not_touch_analysis_population(self):
        reviews = bd.load(bd.REVIEWS_PATH)
        evidence = bd.load(bd.ANALYSIS_EVIDENCE_PATH)
        self.assertEqual(len(reviews["reviews"]), 21)
        self.assertEqual(len(evidence["evidence"]), 95)
        self.assertEqual(bd.production_live_input_count(reviews), 1)
        self.assertEqual(bd.analysis_revision_count(reviews), 0)
        self.assertEqual(bd.exact_series_count(reviews), 0)

    def test_status_and_roadmap_targets_record_bd_without_changing_history_body(self):
        status = bd.STATUS_PATH.read_text(encoding="utf-8")
        roadmap = bd.ROADMAP_PATH.read_text(encoding="utf-8")
        target_status = bd.target_status(status)
        target_roadmap = bd.target_roadmap(roadmap)
        self.assertIn("POST-BC / BD FIFTH LIVE SPECIMEN", target_status)
        self.assertIn("v0.5 / 5 reviewed internal observations / 7 primary-official evidence rows", target_status)
        self.assertIn("### BD — fifth Live geopolitical specimen", target_roadmap)
        self.assertIn("# WORLD SIGNALS — project status / branch-recovery checkpoint", target_status)

    def test_reviewed_bd_descendant_is_idempotent_and_not_downgraded(self):
        schema, observations, evidence = self.simulate()
        self.assertEqual(bd.target_live_schema(schema, self.plan), schema)
        self.assertEqual(bd.target_observations(observations, self.payload), observations)
        self.assertEqual(bd.target_evidence(evidence, self.payload), evidence)


if __name__ == "__main__":
    unittest.main()
