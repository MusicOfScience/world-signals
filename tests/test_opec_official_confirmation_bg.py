from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import apply_opec_official_confirmation_bg as bg


class OPECOfficialConfirmationBGTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = bg.load(bg.PLAN_PATH)
        cls.state = bg.load_state()
        cls.is_target = bg.is_materialised(cls.state, cls.plan)
        cls.target = cls.state if cls.is_target else bg.simulate(cls.state, cls.plan)

    def test_plan_freezes_post_bf_boundary_and_nonpopulation_target(self):
        self.assertEqual(self.plan["exact_base_main_sha"], "363c5ff249ca8833744f15d74750d9377e8a9002")
        self.assertEqual(self.plan["preconditions"]["canonical_registry_version"], "0.40")
        self.assertEqual(self.plan["preconditions"]["source_registry_version"], "1.82")
        self.assertEqual(self.plan["preconditions"]["change_ledger_version"], "0.26")
        self.assertEqual(self.plan["postconditions"]["canonical_registry_version"], "0.41")
        self.assertEqual(self.plan["postconditions"]["canonical_record_count"], 689)
        self.assertEqual(self.plan["postconditions"]["source_record_count"], 246)
        self.assertEqual(self.plan["postconditions"]["change_ledger_count"], 62)
        self.assertTrue(self.plan["manual_merge_only"])

    def test_spa_is_official_supporting_confirmation_not_opec_primary(self):
        source = self.plan["official_confirmation_source"]
        self.assertEqual(source["source_id"], "WSSRC-COM-016")
        self.assertEqual(source["institution"], "Saudi Press Agency (SPA)")
        self.assertEqual(source["canonical_dependency_count"], 0)
        self.assertEqual(source["automated_monitoring_use"], "PROHIBITED_OR_RIGHTS_HOLD")
        self.assertTrue(any("not the competent OPEC issuing institution" in item for item in source["known_limitations"]))
        self.assertEqual(self.plan["provenance_basis"]["primary_opec_provenance_state"], "REQUIRED_WHEN_RETRIEVABLE")

    def test_spa_publication_timestamp_never_becomes_event_timestamp(self):
        pub = self.plan["publication_time"]
        self.assertEqual(pub["published_local"], "2026-09-06T15:57:00+03:00")
        self.assertEqual(pub["published_at_utc"], "2026-09-06T12:57:00Z")
        self.assertEqual(pub["source_timezone"], "Asia/Riyadh")
        self.assertEqual(pub["event_time_effect"], "NONE")
        row = bg.by_occurrence(self.target["canonical"])[bg.TARGET_ID]
        self.assertEqual(row["start_local"], "2026-09-06")
        self.assertIsNone(row["start_utc"])
        self.assertIsNone(row["source_timezone"])
        self.assertEqual(row["timing_type"], "CIVIL_DATE")

    def test_target_preserves_completed_lifecycle_and_reuters_history(self):
        row = bg.by_occurrence(self.target["canonical"])[bg.TARGET_ID]
        self.assertEqual(row["lifecycle_status"], "COMPLETED")
        self.assertEqual(row["certainty_status"], "CONFIRMED")
        self.assertIsNotNone(bg.related(row, bg.REUTERS_ID))
        self.assertIsNotNone(bg.related(row, bg.SPA_ID))
        self.assertEqual(
            bg.related(row, bg.SPA_ID)["primary_opec_provenance_state"],
            "REQUIRED_WHEN_RETRIEVABLE",
        )
        self.assertEqual(row["last_successful_assertion_id"], self.plan["provenance_basis"]["assertion_id"])

    def test_target_is_exactly_one_provenance_change_with_no_population_growth(self):
        self.assertEqual(len(self.target["canonical"]["records"]), 689)
        self.assertEqual(len(self.target["sources"]["sources"]), 246)
        self.assertEqual(len(self.target["ledger"]["changes"]), 62)
        change = self.target["ledger"]["changes"][-1]
        self.assertEqual(change["change_id"], "WSCHANGE-5c0629586cdf3ce7")
        self.assertEqual(change["change_type"], "SOURCE_PROVENANCE_STRENGTHENING")
        self.assertTrue(change["new_values"]["reuters_fallback_preserved"])
        self.assertEqual(change["new_values"]["primary_opec_provenance_state"], "REQUIRED_WHEN_RETRIEVABLE")

    def test_live_analysis_monitor_gates_remain_closed_and_unchanged(self):
        self.assertEqual(self.target["live_schema"]["version"], "0.6")
        self.assertEqual(len(self.target["live_observations"]["observations"]), 6)
        self.assertEqual(len(self.target["live_evidence"]["evidence"]), 9)
        self.assertFalse(self.target["live_schema"]["population_policy"]["automatic_ingestion_allowed"])
        self.assertFalse(self.target["live_schema"]["population_policy"]["public_observation_projection_allowed"])
        self.assertEqual(len(self.target["analysis_reviews"]["reviews"]), 21)
        self.assertEqual(len(self.target["analysis_evidence"]["evidence"]), 95)
        self.assertEqual(bg.production_live_input_count(self.target["analysis_reviews"]), 1)
        self.assertEqual(bg.revision_count(self.target["analysis_reviews"]), 0)
        self.assertEqual(len(self.target["expectations"]["adapters"]), 8)

    def test_bg_does_not_create_october_voluntary_adjustment_occurrence(self):
        matches = [
            row for row in self.target["canonical"]["records"]
            if row.get("series_id") == self.plan["selection"]["series_id"]
            and str(row.get("start_local", "")).startswith("2026-10-04")
        ]
        self.assertEqual(matches, [])

    def test_status_and_roadmap_record_bounded_bg_contract(self):
        status = bg.target_status(bg.STATUS_PATH.read_text(encoding="utf-8"), self.plan)
        roadmap = bg.target_roadmap(bg.ROADMAP_PATH.read_text(encoding="utf-8"))
        self.assertIn("BG OPEC OFFICIAL-CONFIRMATION PROVENANCE STRENGTHENING", status)
        self.assertIn("v0.41 / 689 occurrences", status)
        self.assertIn("v1.83 / 246 sources", status)
        self.assertIn("OPEC PRIMARY STILL PENDING", roadmap)
        self.assertIn("Reuters `WSSRC-COM-015` remains preserved", roadmap)

    def test_materialised_target_validates_or_simulation_is_clean(self):
        bg.assert_common_layers(self.target, self.plan, target=True)
        if not self.is_target:
            bg.assert_poststate(self.state, self.target, self.plan)
        else:
            bg.assert_materialised(self.state, self.plan)


if __name__ == "__main__":
    unittest.main()
