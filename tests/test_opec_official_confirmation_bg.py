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
        cls.row = bg.by_occurrence(cls.state["canonical"])[bg.TARGET_ID]
        cls.has_bg = (
            bg.by_source(cls.state["sources"]).get(bg.SPA_ID) is not None
            and bg.related(cls.row, bg.SPA_ID) is not None
            and cls.plan["provenance_basis"]["change_id"]
            in {x.get("change_id") for x in cls.state["ledger"].get("changes", [])}
        )
        cls.target = cls.state if cls.has_bg else bg.simulate(cls.state, cls.plan)

    def test_plan_freezes_exact_historical_post_bf_boundary(self):
        self.assertEqual(self.plan["exact_base_main_sha"], "363c5ff249ca8833744f15d74750d9377e8a9002")
        self.assertEqual(self.plan["preconditions"]["canonical_registry_version"], "0.40")
        self.assertEqual(self.plan["preconditions"]["source_registry_version"], "1.82")
        self.assertEqual(self.plan["preconditions"]["change_ledger_version"], "0.26")
        self.assertEqual(self.plan["postconditions"]["canonical_registry_version"], "0.41")
        self.assertEqual(self.plan["postconditions"]["canonical_record_count"], 689)
        self.assertEqual(self.plan["postconditions"]["source_registry_version"], "1.83")
        self.assertEqual(self.plan["postconditions"]["source_record_count"], 246)
        self.assertEqual(self.plan["postconditions"]["change_ledger_version"], "0.27")
        self.assertEqual(self.plan["postconditions"]["change_ledger_count"], 62)
        self.assertTrue(self.plan["manual_merge_only"])

    def test_spa_remains_historical_official_support_not_opec_primary(self):
        source = bg.by_source(self.target["sources"])[bg.SPA_ID]
        self.assertEqual(source["institution"], "Saudi Press Agency (SPA)")
        self.assertEqual(source["canonical_dependency_count"], 0)
        self.assertEqual(source["automated_monitoring_use"], "PROHIBITED_OR_RIGHTS_HOLD")
        self.assertTrue(any("not the competent OPEC issuing institution" in item for item in source["known_limitations"]))
        doc = bg.related(bg.by_occurrence(self.target["canonical"])[bg.TARGET_ID], bg.SPA_ID)
        self.assertIsNotNone(doc)
        self.assertEqual(doc["primary_opec_provenance_state"], "REQUIRED_WHEN_RETRIEVABLE")

    def test_spa_publication_timestamp_never_became_event_timestamp(self):
        pub = self.plan["publication_time"]
        self.assertEqual(pub["published_local"], "2026-09-06T15:57:00+03:00")
        self.assertEqual(pub["published_at_utc"], "2026-09-06T12:57:00Z")
        self.assertEqual(pub["event_time_effect"], "NONE")
        row = bg.by_occurrence(self.target["canonical"])[bg.TARGET_ID]
        self.assertEqual(row["start_local"], "2026-09-06")
        self.assertIsNone(row["start_utc"])
        self.assertIsNone(row["source_timezone"])
        self.assertEqual(row["timing_type"], "CIVIL_DATE")

    def test_bg_historical_evidence_survives_legitimate_descendants(self):
        row = bg.by_occurrence(self.target["canonical"])[bg.TARGET_ID]
        self.assertEqual(row["lifecycle_status"], "COMPLETED")
        self.assertEqual(row["certainty_status"], "CONFIRMED")
        self.assertIsNotNone(bg.related(row, bg.REUTERS_ID))
        self.assertIsNotNone(bg.related(row, bg.SPA_ID))
        self.assertIn(
            self.plan["provenance_basis"]["change_id"],
            {x.get("change_id") for x in self.target["ledger"].get("changes", [])},
        )
        self.assertTrue(
            version_at_least(
                str(self.target["canonical"].get("version")),
                self.plan["postconditions"]["canonical_registry_version"],
            )
        )
        self.assertGreaterEqual(len(self.target["canonical"].get("records", [])), 689)
        self.assertGreaterEqual(len(self.target["sources"].get("sources", [])), 246)
        self.assertGreaterEqual(len(self.target["ledger"].get("changes", [])), 62)

    def test_exact_bg_mutation_contract_only_on_historical_prestate(self):
        if self.has_bg:
            self.skipTest("Exact BG mutation simulation is frozen to the historical post-BF prestate.")
        self.assertEqual(len(self.target["canonical"]["records"]), 689)
        self.assertEqual(len(self.target["sources"]["sources"]), 246)
        self.assertEqual(len(self.target["ledger"]["changes"]), 62)
        change = self.target["ledger"]["changes"][-1]
        self.assertEqual(change["change_id"], "WSCHANGE-5c0629586cdf3ce7")
        self.assertEqual(change["change_type"], "SOURCE_PROVENANCE_STRENGTHENING")
        bg.assert_poststate(self.state, self.target, self.plan)

    def test_bg_did_not_create_october_voluntary_adjustment_occurrence(self):
        matches = [
            row for row in self.target["canonical"]["records"]
            if row.get("series_id") == self.plan["selection"]["series_id"]
            and str(row.get("start_local", "")).startswith("2026-10-04")
        ]
        self.assertEqual(matches, [])

    def test_historical_bg_plan_and_roadmap_record_bounded_contract(self):
        self.assertEqual(self.plan["provenance_basis"]["primary_opec_provenance_state"], "REQUIRED_WHEN_RETRIEVABLE")
        roadmap = bg.ROADMAP_PATH.read_text(encoding="utf-8")
        self.assertIn("BG — OPEC official participating-government provenance strengthening", roadmap)
        self.assertIn("Reuters `WSSRC-COM-015` remains preserved", roadmap)

    def test_current_descendant_validates_without_latest_assertion_ceiling(self):
        bg.validate_layers(self.target)
        row = bg.by_occurrence(self.target["canonical"])[bg.TARGET_ID]
        self.assertEqual(row["lifecycle_status"], "COMPLETED")
        self.assertEqual(row["start_local"], "2026-09-06")
        self.assertIsNone(row["start_utc"])
        # A later reviewed provenance assertion may legitimately become current.
        self.assertIsInstance(row.get("last_successful_assertion_id"), str)


if __name__ == "__main__":
    unittest.main()
