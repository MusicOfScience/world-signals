from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.audit_post_aa_pressure_ab import BASE_MAIN_SHA, build_report


class PostAAPressureAuditABTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = build_report()
        cls.frozen = json.loads(
            (ROOT / "data/analysis/POST_AA_PRESSURE_AUDIT_AB_v0.1.json").read_text(encoding="utf-8")
        )

    def test_exact_ab_base_is_frozen(self):
        self.assertEqual(BASE_MAIN_SHA, "c4b499436db54f6dc3ebbe045cfda2fba7f730dd")
        self.assertEqual(self.report["base_main_sha"], BASE_MAIN_SHA)
        self.assertEqual(self.report["audit"], "POST_AA_PRESSURE_AUDIT_AB")

    def test_ab_is_read_only(self):
        self.assertTrue(all(value is False for value in self.report["mutation_policy"].values()))

    def test_aa_repairs_are_visible(self):
        comparison = self.report["post_aa_comparison"]
        self.assertTrue(comparison["east_asia_completed_anchor_gap_repaired"])
        self.assertTrue(comparison["east_asia_reviewed_sample_present"])
        self.assertTrue(comparison["fiscal_financing_event_reviewed"])

    def test_measurement_gap_is_measured_not_filled(self):
        semantics = self.report["analysis_semantics"]
        self.assertEqual(semantics["exact_timestamp_series_rows"], 0)
        self.assertGreater(semantics["source_reported_or_session_market_rows"], 0)
        self.assertTrue(self.report["selection_discipline"]["market_precision_gap_is_not_permission_to_infer_timestamps"])

    def test_frontier_is_not_backlog(self):
        frozen_ids = {
            row["occurrence_id"] for row in self.frozen["frontier_ranked_by_sample_novelty"]
        }
        self.assertEqual(frozen_ids, {"WSO-MAC-B-0041", "WSO-ddb70f8ff05a58fb"})

        live_ids = {
            row["occurrence_id"] for row in self.report["frontier_ranked_by_sample_novelty"]
        }
        self.assertTrue(frozen_ids.issubset(live_ids))
        self.assertTrue(self.report["selection_discipline"]["frontier_is_not_backlog"])

    def test_boc_has_more_sample_novelty_than_household_spending(self):
        frontier = {row["occurrence_id"]: row for row in self.report["frontier_ranked_by_sample_novelty"]}
        self.assertGreater(
            frontier["WSO-ddb70f8ff05a58fb"]["novel_dimension_count"],
            frontier["WSO-MAC-B-0041"]["novel_dimension_count"],
        )
        self.assertTrue(frontier["WSO-ddb70f8ff05a58fb"]["novelty_against_reviewed_sample"]["new_region"])
        self.assertFalse(frontier["WSO-MAC-B-0041"]["novelty_against_reviewed_sample"]["new_region"])

    def test_no_completed_region_gap_remains(self):
        gaps = self.report["upstream_population_gaps"]
        self.assertEqual(gaps["regions_present_in_registry_but_absent_from_completed_anchors"], [])
        self.assertGreater(len(gaps["categories_present_in_registry_but_absent_from_completed_anchors"]), 0)
        self.assertGreater(len(gaps["event_types_present_in_registry_but_absent_from_completed_anchors"]), 0)


if __name__ == "__main__":
    unittest.main()
