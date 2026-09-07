from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import apply_opec_official_confirmation_bg as bg
from src.world_signals.checkpoint_contract import version_at_least


class OPECOfficialConfirmationBGTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = bg.load(bg.PLAN_PATH)
        cls.state = bg.load_state()
        cls.is_exact_pre = (
            str(cls.state["canonical"].get("version")) == cls.plan["preconditions"]["canonical_registry_version"]
            and str(cls.state["sources"].get("version")) == cls.plan["preconditions"]["source_registry_version"]
        )
        cls.target = bg.simulate(cls.state, cls.plan) if cls.is_exact_pre else cls.state

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
        # BG's exact assertion remains frozen in its reviewed ledger entry even when a
        # later reviewed descendant legitimately advances the occurrence assertion.
        changes = [
            item for item in self.target["ledger"].get("changes", [])
            if item.get("change_id") == self.plan["provenance_basis"]["change_id"]
        ]
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]["source_assertion_id"], self.plan["provenance_basis"]["assertion_id"])

    def test_bg_historical_change_survives_legitimate_descendant_growth(self):
        post = self.plan["postconditions"]
        self.assertTrue(version_at_least(str(self.target["canonical"].get("version")), post["canonical_registry_version"]))
        self.assertGreaterEqual(len(self.target["canonical"]["records"]), post["canonical_record_count"])
        self.assertTrue(version_at_least(str(self.target["sources"].get("version")), post["source_registry_version"]))
        self.assertGreaterEqual(len(self.target["sources"]["sources"]), post["source_record_count"])
        self.assertTrue(version_at_least(str(self.target["ledger"].get("version")), post["change_ledger_version"]))
        self.assertGreaterEqual(len(self.target["ledger"]["changes"]), post["change_ledger_count"])
        changes = [
            item for item in self.target["ledger"].get("changes", [])
            if item.get("change_id") == "WSCHANGE-5c0629586cdf3ce7"
        ]
        self.assertEqual(len(changes), 1)
        change = changes[0]
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

    def test_status_and_roadmap_record_bounded_bg_historical_contract(self):
        # The frozen BG transforms still express the exact historical checkpoint.
        historical_status = bg.target_status(
            (ROOT / "PROJECT_STATUS.md").read_text(encoding="utf-8"), self.plan
        )
        historical_roadmap = bg.target_roadmap((ROOT / "ROADMAP.md").read_text(encoding="utf-8"))
        self.assertIn("BG OPEC OFFICIAL-CONFIRMATION PROVENANCE STRENGTHENING", historical_status)
        self.assertIn("v0.41 / 689 occurrences", historical_status)
        self.assertIn("v1.83 / 246 sources", historical_status)
        self.assertIn("OPEC PRIMARY STILL PENDING", historical_roadmap)
        self.assertIn("Reuters `WSSRC-COM-015` remains preserved", historical_roadmap)

    def test_materialised_target_validates_without_freezing_descendant_counts(self):
        bg.assert_common_layers(self.target, self.plan, target=True)
        if self.is_exact_pre:
            bg.assert_poststate(self.state, self.target, self.plan)
        else:
            post = self.plan["postconditions"]
            self.assertTrue(version_at_least(str(self.target["canonical"].get("version")), post["canonical_registry_version"]))
            self.assertTrue(version_at_least(str(self.target["sources"].get("version")), post["source_registry_version"]))
            self.assertTrue(version_at_least(str(self.target["ledger"].get("version")), post["change_ledger_version"]))
            row = bg.by_occurrence(self.target["canonical"])[bg.TARGET_ID]
            self.assertEqual(row["lifecycle_status"], "COMPLETED")
            self.assertEqual(row["start_local"], "2026-09-06")
            self.assertIsNone(row["start_utc"])
            self.assertIsNotNone(bg.related(row, bg.REUTERS_ID))
            self.assertIsNotNone(bg.related(row, bg.SPA_ID))
            self.assertIn("WSSRC-COM-016", bg.by_source(self.target["sources"]))


if __name__ == "__main__":
    unittest.main()
