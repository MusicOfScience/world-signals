from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.live_intelligence import public_live_intelligence_projection, validate_live_intelligence

SCRIPT_PATH = ROOT / "scripts/apply_drc_bundibugyo_evolving_state_ax.py"
spec = importlib.util.spec_from_file_location("live_ax_apply", SCRIPT_PATH)
apply_ax = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(apply_ax)


def version_tuple(raw: str) -> tuple[int, ...]:
    return tuple(int(part) for part in str(raw).split("."))


class DRCBundibugyoEvolvingStateAXTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(apply_ax.PLAN_PATH.read_text(encoding="utf-8"))
        cls.payload = json.loads(apply_ax.PAYLOAD_PATH.read_text(encoding="utf-8"))
        cls.canonical = json.loads(apply_ax.CANONICAL_PATH.read_text(encoding="utf-8"))
        cls.current_schema = json.loads(apply_ax.LIVE_SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.current_observations = json.loads(apply_ax.LIVE_OBSERVATIONS_PATH.read_text(encoding="utf-8"))
        cls.current_evidence = json.loads(apply_ax.LIVE_EVIDENCE_PATH.read_text(encoding="utf-8"))

        if cls.current_schema.get("version") == "0.2":
            cls.schema, cls.observations, cls.evidence = apply_ax.transform(cls.plan, cls.payload)
            cls.simulated = True
        else:
            cls.schema = cls.current_schema
            cls.observations = cls.current_observations
            cls.evidence = cls.current_evidence
            cls.simulated = False

        cls.by_id = {row["observation_id"]: row for row in cls.observations["observations"]}
        cls.evidence_by_id = {row["evidence_id"]: row for row in cls.evidence["evidence"]}

    def validate(self, schema=None, observations=None, evidence=None):
        return validate_live_intelligence(
            schema or self.schema,
            evidence or self.evidence,
            observations or self.observations,
            self.canonical,
        )

    def test_exact_post_78_base_and_prestate_are_frozen(self):
        self.assertEqual(self.plan["base_sha"], "721206169033eb0ceb695075d44fb38e7fa2edc3")
        pre = self.plan["pre_state"]
        self.assertEqual((pre["canonical_registry_version"], pre["canonical_record_count"]), ("0.38", 688))
        self.assertEqual((pre["source_registry_version"], pre["source_count"]), ("1.80", 243))
        self.assertEqual((pre["monitor_expectations_version"], pre["monitor_adapter_count"]), ("0.10", 8))
        self.assertEqual((pre["analysis_reviews_version"], pre["analysis_review_count"]), ("0.16", 20))
        self.assertEqual((pre["analysis_evidence_version"], pre["analysis_evidence_count"]), ("0.16", 91))
        self.assertEqual(pre["live_intelligence_schema_version"], "0.2")
        self.assertEqual(pre["live_intelligence_observation_count"], 1)
        self.assertEqual(pre["live_intelligence_evidence_count"], 2)
        self.assertEqual(pre["live_intelligence_population_state"], "CONTROLLED_SINGLE_SPECIMEN")

    def test_ax_target_checkpoint_is_frozen_and_live_descendant_validates(self):
        target = self.plan["target_state"]
        self.assertEqual(target["live_intelligence_schema_version"], "0.3")
        self.assertEqual(target["observation_count"], 3)
        self.assertEqual(target["evidence_count"], 4)
        self.assertEqual(target["live_intelligence_population_state"], "CONTROLLED_MULTI_SNAPSHOT_SPECIMEN")

        self.assertGreaterEqual(version_tuple(self.schema["version"]), (0, 3))
        self.assertGreaterEqual(len(self.observations["observations"]), 3)
        self.assertGreaterEqual(len(self.evidence["evidence"]), 4)
        self.assertEqual(self.observations["version"], self.schema["version"])
        self.assertEqual(self.evidence["version"], self.schema["version"])
        report = self.validate()
        self.assertTrue(report.ok, report.errors)

    def test_aw_nepal_specimen_remains_unchanged_and_ungrouped(self):
        nepal = self.by_id["WSLI-RISK-NPL-FLOOD-20260826-001"]
        self.assertEqual(nepal["event_time"]["event_at_utc"], "2026-08-26T02:55:00Z")
        self.assertEqual(nepal["event_time"]["event_timezone"], "Asia/Kathmandu")
        self.assertEqual(nepal["canonical_links"], [])
        self.assertNotIn("story_id", nepal)
        self.assertNotIn("state_as_of", nepal)
        self.assertNotIn("state_update_of_observation_id", nepal)

    def test_drc_snapshots_share_one_manual_story_but_are_distinct_observations(self):
        first = self.by_id["WSLI-HEALTH-COD-BVD-20260826-001"]
        second = self.by_id["WSLI-HEALTH-COD-BVD-20260830-001"]
        self.assertNotEqual(first["observation_id"], second["observation_id"])
        self.assertEqual(first["story_id"], "WSSTORY-HEALTH-COD-BVD-2026")
        self.assertEqual(second["story_id"], first["story_id"])
        self.assertEqual(first["observation_type"], "HEALTH_EMERGENCY")
        self.assertEqual(second["observation_type"], "HEALTH_EMERGENCY")
        self.assertEqual(first["canonical_links"], [])
        self.assertEqual(second["canonical_links"], [])

    def test_state_update_is_explicit_and_not_a_revision(self):
        first = self.by_id["WSLI-HEALTH-COD-BVD-20260826-001"]
        second = self.by_id["WSLI-HEALTH-COD-BVD-20260830-001"]
        self.assertIsNone(first["state_update_of_observation_id"])
        self.assertEqual(second["state_update_of_observation_id"], first["observation_id"])
        self.assertIsNone(first["revision_of_observation_id"])
        self.assertIsNone(second["revision_of_observation_id"])
        self.assertTrue(self.schema["revision_policy"]["state_update_is_not_revision"])
        self.assertTrue(self.schema["revision_policy"]["state_update_preserves_prior_snapshot"])

    def test_state_as_of_is_civil_date_and_separate_from_observation_time(self):
        first = self.by_id["WSLI-HEALTH-COD-BVD-20260826-001"]
        second = self.by_id["WSLI-HEALTH-COD-BVD-20260830-001"]
        self.assertEqual(first["state_as_of"], {"precision": "CIVIL_DATE", "as_of_date": "2026-08-26"})
        self.assertEqual(second["state_as_of"], {"precision": "CIVIL_DATE", "as_of_date": "2026-08-30"})
        self.assertNotEqual(first["observed_at_utc"][:10], first["state_as_of"]["as_of_date"])
        self.assertNotEqual(second["observed_at_utc"][:10], second["state_as_of"]["as_of_date"])
        self.assertTrue(self.schema["time_policy"]["state_as_of_time_is_distinct_from_event_publication_and_observation_time"])

    def test_later_snapshot_preserves_prior_snapshot_counts_in_text(self):
        first = self.by_id["WSLI-HEALTH-COD-BVD-20260826-001"]
        second = self.by_id["WSLI-HEALTH-COD-BVD-20260830-001"]
        self.assertIn("5,794", first["headline"] + first["summary"])
        self.assertIn("2,786", first["summary"])
        self.assertIn("6,100", second["headline"] + second["summary"])
        self.assertIn("2,950", second["summary"])
        self.assertIn("not a correction or retraction", second["summary"].lower())

    def test_drc_evidence_is_primary_official_and_publication_dates_remain_civil(self):
        ids = {
            "WSEV-LI-COD-BVD-WHO-DON616-20260828",
            "WSEV-LI-COD-BVD-WHO-AFRO-SITREP16-20260830",
        }
        rows = [self.evidence_by_id[item] for item in ids]
        self.assertTrue(all(row["evidence_class"] == "PRIMARY_OFFICIAL" for row in rows))
        self.assertTrue(all(row["canonical_provenance_effect"] == "NONE" for row in rows))
        self.assertEqual({row["publication_time"]["precision"] for row in rows}, {"CIVIL_DATE"})
        self.assertEqual({row["publication_time"]["published_date"] for row in rows}, {"2026-08-28", "2026-08-30"})

    def test_civil_state_as_of_cannot_be_upgraded_to_timestamp(self):
        observations = copy.deepcopy(self.observations)
        row = next(r for r in observations["observations"] if r["observation_id"] == "WSLI-HEALTH-COD-BVD-20260826-001")
        row["state_as_of"]["as_of_at_utc"] = "2026-08-26T00:00:00Z"
        report = self.validate(observations=observations)
        self.assertIn("civil state-as-of date must not be upgraded", " ".join(report.errors))

    def test_state_update_must_reference_same_story(self):
        observations = copy.deepcopy(self.observations)
        row = next(r for r in observations["observations"] if r["observation_id"] == "WSLI-HEALTH-COD-BVD-20260830-001")
        row["story_id"] = "WSSTORY-WRONG"
        report = self.validate(observations=observations)
        self.assertIn("same story", " ".join(report.errors))

    def test_state_update_must_move_forward_in_as_of_time(self):
        observations = copy.deepcopy(self.observations)
        row = next(r for r in observations["observations"] if r["observation_id"] == "WSLI-HEALTH-COD-BVD-20260830-001")
        row["state_as_of"]["as_of_date"] = "2026-08-26"
        report = self.validate(observations=observations)
        self.assertIn("later state_as_of", " ".join(report.errors))

    def test_state_evolution_cannot_also_use_revision_link(self):
        observations = copy.deepcopy(self.observations)
        row = next(r for r in observations["observations"] if r["observation_id"] == "WSLI-HEALTH-COD-BVD-20260830-001")
        row["revision_of_observation_id"] = "WSLI-HEALTH-COD-BVD-20260826-001"
        report = self.validate(observations=observations)
        self.assertIn("state evolution must not also use revision_of_observation_id", " ".join(report.errors))

    def test_story_policy_allows_manual_identity_but_keeps_clustering_closed(self):
        policy = self.schema["story_grouping_policy"]
        self.assertTrue(policy["manual_reviewed_story_id_allowed"])
        self.assertTrue(policy["story_id_is_not_canonical_identity"])
        self.assertTrue(policy["story_id_is_not_causal_claim"])
        self.assertFalse(policy["automatic_clustering_allowed"])
        self.assertFalse(policy["story_id_required"])

    def test_population_ceiling_rejects_growth_beyond_current_reviewed_policy(self):
        self.assertEqual(self.plan["target_state"]["observation_count"], 3)
        self.assertEqual(self.plan["target_state"]["evidence_count"], 4)
        policy = self.schema["population_policy"]
        max_observations = policy["maximum_observation_count"]
        self.assertGreaterEqual(max_observations, 3)

        observations = copy.deepcopy(self.observations)
        template = copy.deepcopy(self.by_id["WSLI-HEALTH-COD-BVD-20260830-001"])
        counter = 1
        while len(observations["observations"]) <= max_observations:
            extra = copy.deepcopy(template)
            extra["observation_id"] = f"WSLI-HEALTH-COD-BVD-OVERFLOW-{counter}"
            extra["state_update_of_observation_id"] = None
            extra["revision_of_observation_id"] = None
            observations["observations"].append(extra)
            counter += 1
        report = self.validate(observations=observations)
        self.assertIn("observation population exceeds reviewed policy maximum", " ".join(report.errors))

    def test_public_projection_stays_metadata_only_for_live_descendant(self):
        projection = public_live_intelligence_projection(self.schema, self.evidence, self.observations, self.canonical)
        meta = projection["metadata"]
        self.assertEqual(meta["schema_version"], self.schema["version"])
        self.assertEqual(meta["population_mode"], self.schema["population_policy"]["mode"])
        self.assertEqual(meta["internal_observation_count"], len(self.observations["observations"]))
        self.assertEqual(meta["internal_evidence_count"], len(self.evidence["evidence"]))
        self.assertEqual(meta["public_observation_count"], 0)
        self.assertFalse(meta["runtime_feed_claim"])
        self.assertEqual(projection["observations"], [])

    def test_no_analysis_or_causal_fields_enter_drc_rows(self):
        for observation_id in ("WSLI-HEALTH-COD-BVD-20260826-001", "WSLI-HEALTH-COD-BVD-20260830-001"):
            row = self.by_id[observation_id]
            for prohibited in self.schema["prohibited_analysis_fields"]:
                self.assertNotIn(prohibited, row)
            self.assertFalse(row["automatic_canonical_commit"])
            self.assertFalse(row["google_calendar_write"])

    def test_transaction_plan_protects_upstream_layers_and_requires_manual_merge(self):
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
