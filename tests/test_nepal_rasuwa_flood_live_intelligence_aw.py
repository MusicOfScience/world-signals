from __future__ import annotations

import copy
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.live_intelligence import (
    public_live_intelligence_projection,
    validate_live_intelligence,
)

SCRIPT_PATH = ROOT / "scripts/apply_nepal_rasuwa_flood_live_intelligence_aw.py"
spec = importlib.util.spec_from_file_location("live_aw_apply", SCRIPT_PATH)
apply_aw = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(apply_aw)


class NepalRasuwaFloodLiveIntelligenceAWTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(apply_aw.PLAN_PATH.read_text(encoding="utf-8"))
        cls.payload = json.loads(apply_aw.PAYLOAD_PATH.read_text(encoding="utf-8"))
        cls.canonical = json.loads(apply_aw.CANONICAL_PATH.read_text(encoding="utf-8"))
        cls.current_schema = json.loads(apply_aw.LIVE_SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.current_observations = json.loads(apply_aw.LIVE_OBSERVATIONS_PATH.read_text(encoding="utf-8"))
        cls.current_evidence = json.loads(apply_aw.LIVE_EVIDENCE_PATH.read_text(encoding="utf-8"))

        if cls.current_schema.get("version") == "0.1":
            cls.schema, cls.observations, cls.evidence = apply_aw.transform(cls.plan, cls.payload)
            cls.simulated = True
        else:
            cls.schema = cls.current_schema
            cls.observations = cls.current_observations
            cls.evidence = cls.current_evidence
            cls.simulated = False

    def validate(self, schema=None, observations=None, evidence=None):
        return validate_live_intelligence(
            schema or self.schema,
            evidence or self.evidence,
            observations or self.observations,
            self.canonical,
        )

    def test_exact_post_77_base_and_prestate_are_frozen_in_plan(self):
        self.assertEqual(self.plan["base_sha"], "4768c73532c4ba4038b30314079b85be64fbee01")
        pre = self.plan["pre_state"]
        self.assertEqual((pre["canonical_registry_version"], pre["canonical_record_count"]), ("0.38", 688))
        self.assertEqual((pre["source_registry_version"], pre["source_count"]), ("1.80", 243))
        self.assertEqual((pre["monitor_expectations_version"], pre["monitor_adapter_count"]), ("0.10", 8))
        self.assertEqual((pre["analysis_reviews_version"], pre["analysis_review_count"]), ("0.16", 20))
        self.assertEqual((pre["analysis_evidence_version"], pre["analysis_evidence_count"]), ("0.16", 91))
        self.assertEqual(pre["live_intelligence_schema_version"], "0.1")
        self.assertEqual(pre["live_intelligence_observation_count"], 0)
        self.assertEqual(pre["live_intelligence_evidence_count"], 0)

    def test_target_is_v02_one_observation_two_evidence_rows(self):
        self.assertEqual(self.schema["version"], "0.2")
        self.assertEqual(self.observations["version"], "0.2")
        self.assertEqual(self.evidence["version"], "0.2")
        self.assertEqual(self.observations["population_state"], "CONTROLLED_SINGLE_SPECIMEN")
        self.assertEqual(len(self.observations["observations"]), 1)
        self.assertEqual(len(self.evidence["evidence"]), 2)
        report = self.validate()
        self.assertTrue(report.ok, report.errors)

    def test_av_foundation_checkpoint_is_frozen_inside_v02(self):
        checkpoint = self.schema["foundation_checkpoint"]
        self.assertEqual(checkpoint["schema_version"], "0.1")
        self.assertEqual(checkpoint["observations_version"], "0.1")
        self.assertEqual(checkpoint["evidence_version"], "0.1")
        self.assertEqual(checkpoint["population_state"], "FOUNDATION_ONLY_NO_POPULATION")
        self.assertEqual(checkpoint["observation_count"], 0)
        self.assertEqual(checkpoint["evidence_count"], 0)
        self.assertEqual(checkpoint["post_merge_main_sha"], "4768c73532c4ba4038b30314079b85be64fbee01")

    def test_first_observation_is_unscheduled_primary_confirmed_physical_shock(self):
        row = self.observations["observations"][0]
        self.assertEqual(row["observation_id"], "WSLI-RISK-NPL-FLOOD-20260826-001")
        self.assertEqual(row["observation_type"], "PHYSICAL_SHOCK")
        self.assertEqual(row["verification_state"], "PRIMARY_CONFIRMED")
        self.assertEqual(row["canonical_links"], [])
        self.assertIsNone(row["revision_of_observation_id"])
        self.assertIn("Nepal", row["jurisdictions"])
        self.assertIn("South Asia", row["regions"])
        self.assertFalse(row["automatic_canonical_commit"])
        self.assertFalse(row["google_calendar_write"])

    def test_nepal_native_time_resolves_exactly_without_melbourne_canonicalisation(self):
        row = self.observations["observations"][0]
        event_time = row["event_time"]
        self.assertEqual(event_time["precision"], "EXACT_TIMESTAMP")
        self.assertEqual(event_time["event_local"], "2026-08-26T08:40:00")
        self.assertEqual(event_time["event_timezone"], "Asia/Kathmandu")
        self.assertEqual(event_time["event_at_utc"], "2026-08-26T02:55:00Z")
        local = datetime.fromisoformat(event_time["event_local"]).replace(tzinfo=ZoneInfo("Asia/Kathmandu"))
        self.assertEqual(local.astimezone(timezone.utc), datetime(2026, 8, 26, 2, 55, tzinfo=timezone.utc))
        self.assertNotIn("Australia/Melbourne", json.dumps(row))

    def test_system_observation_time_is_distinct_from_real_world_event_time(self):
        row = self.observations["observations"][0]
        self.assertEqual(row["observed_at_utc"], "2026-09-06T07:08:00Z")
        self.assertNotEqual(row["observed_at_utc"], row["event_time"]["event_at_utc"])

    def test_evidence_is_first_party_civil_date_precision_and_noncanonical(self):
        rows = self.evidence["evidence"]
        self.assertEqual(
            {row["evidence_id"] for row in rows},
            {
                "WSEV-LI-NPL-FLOOD-MOHA-20260827",
                "WSEV-LI-NPL-FLOOD-WHO-20260830",
            },
        )
        self.assertTrue(all(row["evidence_class"] == "PRIMARY_OFFICIAL" for row in rows))
        self.assertTrue(all(row["canonical_provenance_effect"] == "NONE" for row in rows))
        self.assertEqual({row["publication_time"]["precision"] for row in rows}, {"CIVIL_DATE"})
        self.assertEqual(
            {row["publication_time"]["published_date"] for row in rows},
            {"2026-08-27", "2026-08-30"},
        )

    def test_civil_publication_date_cannot_be_upgraded_to_a_clock_time(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["evidence"][0]["publication_time"]["published_at_utc"] = "2026-08-27T00:00:00Z"
        report = self.validate(evidence=evidence)
        self.assertIn("civil publication date must not be upgraded", " ".join(report.errors))

    def test_publication_time_is_required_in_v02(self):
        evidence = copy.deepcopy(self.evidence)
        del evidence["evidence"][0]["publication_time"]
        report = self.validate(evidence=evidence)
        joined = " ".join(report.errors)
        self.assertIn("missing evidence fields", joined)
        self.assertIn("publication_time", joined)

    def test_population_policy_is_bounded_and_rejects_second_observation(self):
        policy = self.schema["population_policy"]
        self.assertEqual(policy["mode"], "CONTROLLED_SINGLE_SPECIMEN")
        self.assertEqual(policy["maximum_observation_count"], 1)
        self.assertEqual(policy["maximum_evidence_count"], 2)
        self.assertFalse(policy["automatic_ingestion_allowed"])
        self.assertFalse(policy["public_observation_projection_allowed"])

        observations = copy.deepcopy(self.observations)
        duplicate = copy.deepcopy(observations["observations"][0])
        duplicate["observation_id"] = "WSLI-RISK-NPL-FLOOD-20260826-002"
        observations["observations"].append(duplicate)
        report = self.validate(observations=observations)
        self.assertIn("observation population exceeds reviewed policy maximum", " ".join(report.errors))

    def test_population_policy_rejects_extra_evidence(self):
        evidence = copy.deepcopy(self.evidence)
        extra = copy.deepcopy(evidence["evidence"][0])
        extra["evidence_id"] = "WSEV-LI-NPL-FLOOD-EXTRA"
        evidence["evidence"].append(extra)
        report = self.validate(evidence=evidence)
        self.assertIn("evidence population exceeds reviewed policy maximum", " ".join(report.errors))

    def test_uncertain_upstream_trigger_is_not_promoted_into_observation(self):
        row = self.observations["observations"][0]
        text = (row["headline"] + " " + row["summary"]).lower()
        self.assertNotIn("ice avalanche", text)
        self.assertNotIn("temporary damming", text)
        self.assertNotIn("caused by", text)
        for prohibited in self.schema["prohibited_analysis_fields"]:
            self.assertNotIn(prohibited, row)

    def test_story_identity_is_not_created_for_first_specimen(self):
        row = self.observations["observations"][0]
        self.assertNotIn("story_id", row)
        self.assertFalse(self.schema["story_grouping_policy"]["automatic_clustering_allowed"])
        self.assertFalse(self.schema["story_grouping_policy"]["story_id_required"])

    def test_public_projection_reports_curated_internal_store_but_zero_public_observations(self):
        projection = public_live_intelligence_projection(
            self.schema, self.evidence, self.observations, self.canonical
        )
        meta = projection["metadata"]
        self.assertEqual(meta["projection_type"], "LIVE_INTELLIGENCE_CURATED_STORE_NOT_RUNTIME_FEED")
        self.assertEqual(meta["schema_version"], "0.2")
        self.assertEqual(meta["population_mode"], "CONTROLLED_SINGLE_SPECIMEN")
        self.assertEqual(meta["internal_observation_count"], 1)
        self.assertEqual(meta["internal_evidence_count"], 2)
        self.assertEqual(meta["public_observation_count"], 0)
        self.assertFalse(meta["runtime_feed_claim"])
        self.assertEqual(projection["observations"], [])

    def test_analysis_evidence_is_not_migrated(self):
        analysis = json.loads(apply_aw.ANALYSIS_EVIDENCE_PATH.read_text(encoding="utf-8"))
        analysis_ids = {row.get("evidence_id") for row in analysis["evidence"]}
        live_ids = {row.get("evidence_id") for row in self.evidence["evidence"]}
        self.assertTrue(analysis_ids.isdisjoint(live_ids))
        self.assertFalse(self.schema["population_policy"]["existing_analysis_evidence_migration_allowed"])

    def test_transaction_plan_protects_all_upstream_governed_layers(self):
        self.assertEqual(
            set(self.plan["protected_paths"]),
            {
                "data/canonical/registry.json",
                "data/canonical/schema.json",
                "data/sources/registry.json",
                "data/changes/ledger.json",
                "data/coverage/biosecurity_overlay.json",
                "data/monitor/expectations.json",
                "data/monitor/operations_policy.json",
                "data/analysis/schema.json",
                "data/analysis/event_reviews.json",
                "data/analysis/evidence_registry.json",
            },
        )
        self.assertTrue(self.plan["manual_merge_only"])


if __name__ == "__main__":
    unittest.main()
