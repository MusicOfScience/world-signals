from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from world_signals.analysis import analysis_population_readiness, validate_analysis
import apply_australian_tropical_cyclone_season_analysis_aj as txn


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class AustralianTropicalCycloneSeasonAnalysisAJTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load("data/analysis/AUSTRALIAN_TROPICAL_CYCLONE_SEASON_ANALYSIS_AJ_PLAN_v0.1.json")
        cls.payload = load("data/analysis/AUSTRALIAN_TROPICAL_CYCLONE_SEASON_ANALYSIS_AJ_PAYLOAD_v0.1.json")
        cls.schema = load("data/analysis/schema.json")
        cls.reviews = load("data/analysis/event_reviews.json")
        cls.evidence = load("data/analysis/evidence_registry.json")
        cls.canonical = load("data/canonical/registry.json")
        cls.sources = load("data/sources/registry.json")
        cls.ledger = load("data/changes/ledger.json")
        cls.overlay = load("data/coverage/biosecurity_overlay.json")
        cls.review = cls.payload["reviews"][0]
        cls.evidence_rows = {row["evidence_id"]: row for row in cls.payload["evidence"]}
        cls.target = next(
            row for row in cls.canonical["records"]
            if row.get("occurrence_id") == cls.plan["selection"]["selected_occurrence_id"]
        )
        p = cls.plan["preconditions"]
        cls.is_exact_pre = (
            (cls.canonical.get("version"), len(cls.canonical.get("records", []))) ==
            (p["canonical_registry_version"], p["canonical_record_count"])
            and (cls.reviews.get("version"), len(cls.reviews.get("reviews", []))) ==
            (p["analysis_reviews_version"], p["analysis_review_count"])
            and (cls.evidence.get("version"), len(cls.evidence.get("evidence", []))) ==
            (p["analysis_evidence_version"], p["analysis_evidence_count"])
        )
        cls.has_aj = cls.plan["new_analysis_id"] in {
            row.get("analysis_id") for row in cls.reviews.get("reviews", [])
        }

    def test_plan_is_exact_post_64_and_selects_completed_physical_risk_window(self):
        self.assertEqual(self.plan["base_main_sha"], "c85db2ec3a675a749acb8201705fb6f1f85de27d")
        pre = self.plan["preconditions"]
        self.assertEqual((pre["canonical_registry_version"], pre["canonical_record_count"]), ("0.37", 687))
        self.assertGreaterEqual(len(self.canonical["records"]), pre["canonical_record_count"])
        self.assertEqual(self.target["category"], "PHYSICAL_CLIMATE_RISK")
        self.assertEqual(self.target["event_type"], "PHYSICAL_RISK_WINDOW")
        self.assertEqual(self.target["lifecycle_status"], "COMPLETED")
        self.assertEqual(self.target["series_id"], "WSER-RISK-AU-TC")

    def test_canonical_season_window_remains_regional_and_has_no_synthetic_clock(self):
        self.assertEqual(self.target["timing_type"], "ALL_DAY_RANGE")
        self.assertEqual((self.target["start_local"], self.target["end_local"]), ("2025-11-01", "2026-04-30"))
        self.assertEqual(self.target["time_precision"], "DAY")
        self.assertTrue(self.target["all_day_semantics"])
        self.assertIsNone(self.target["source_timezone"])
        self.assertIsNone(self.target["start_utc"])
        self.assertIsNone(self.target["end_utc"])
        self.assertIsNone(self.review["canonical_release_utc"])

    def test_bureau_actuals_are_exactly_11_7_4_2(self):
        actuals = {row["metric"]: row["value"] for row in self.review["what_happened"]["actuals"]}
        self.assertEqual(actuals["australian_region_tropical_cyclone_count"], 11)
        self.assertEqual(actuals["severe_tropical_cyclone_count"], 7)
        self.assertEqual(actuals["mainland_landfall_count_at_tropical_cyclone_strength"], 4)
        self.assertEqual(actuals["mainland_crossing_count_at_tropical_low_strength"], 2)

    def test_climatology_is_not_promoted_to_season_specific_forecast(self):
        benchmarks = {row["metric"]: row for row in self.review["what_was_expected"]["benchmarks"]}
        count = benchmarks["climatological_australian_region_tropical_cyclone_count"]
        self.assertEqual(count["value"], 10)
        self.assertEqual(count["benchmark_type"], "OTHER_DEFENSIBLE_EXPECTATION")
        landfall = benchmarks["typical_mainland_landfalls"]
        self.assertEqual(landfall["value"], "3-4")
        self.assertEqual(landfall["benchmark_type"], "OTHER_DEFENSIBLE_EXPECTATION")
        self.assertFalse(self.plan["guardrails"]["climatological_average_is_season_specific_forecast"])

    def test_surprise_is_not_established_and_has_no_fake_forecast_error(self):
        surprise = self.review["what_surprised"]
        self.assertEqual(surprise["status"], "NOT_ESTABLISHED")
        self.assertEqual(surprise["comparisons"], [])
        self.assertIn("Climatology is therefore not converted into forecast error", surprise["summary"])
        self.assertFalse(self.plan["guardrails"]["eleven_vs_ten_is_directional_surprise"])

    def test_aggregate_season_has_no_market_move(self):
        self.assertEqual(self.review["what_moved"], [])
        self.assertFalse(self.plan["guardrails"]["empty_market_response_is_missing_work"])
        self.assertFalse(self.plan["guardrails"]["landfall_count_implies_market_move"])

    def test_warm_sst_context_is_not_climate_attribution(self):
        connection = self.review["what_appears_connected"]
        self.assertEqual(connection["interaction_type"], "COMMON_DRIVER_CONTEXT")
        self.assertEqual(connection["causal_status"], "NOT_A_CAUSAL_CLAIM")
        self.assertEqual(connection["confidence"], "HIGH")
        self.assertFalse(self.plan["guardrails"]["warm_sst_context_is_climate_change_attribution"])
        self.assertGreaterEqual(len(self.review["alternative_explanations"]), 2)

    def test_second_order_effects_remain_unestablished_at_season_window_level(self):
        second = self.review["second_order_effects"]
        self.assertEqual(second["status"], "NOT_ESTABLISHED")
        self.assertIn("named-cyclone", second["summary"])
        self.assertIn("shock", second["summary"])
        self.assertFalse(self.plan["guardrails"]["season_window_equals_named_cyclone_occurrence"])
        self.assertFalse(self.plan["guardrails"]["severe_cyclone_count_implies_damage"])

    def test_evidence_is_four_primary_official_analysis_only_rows(self):
        self.assertEqual(set(self.evidence_rows), set(self.plan["new_evidence_ids"]))
        self.assertEqual(len(self.evidence_rows), 4)
        for row in self.evidence_rows.values():
            self.assertEqual(row["evidence_class"], "PRIMARY_OFFICIAL")
            self.assertEqual(row["provider"], "Australian Bureau of Meteorology")
            self.assertEqual(row["canonical_provenance_effect"], "NONE")

    def test_exact_prestate_transform_mutates_only_analysis_review_and_evidence(self):
        if not self.is_exact_pre:
            self.skipTest("exact AJ transform comparison belongs to exact post-64 pre-state")
        new_reviews, new_evidence, readiness, projection = txn.transform(
            self.plan,
            self.payload,
            self.canonical,
            self.sources,
            self.ledger,
            self.overlay,
            self.schema,
            self.reviews,
            self.evidence,
        )
        self.assertEqual((new_reviews["version"], len(new_reviews["reviews"])), ("0.10", 14))
        self.assertEqual((new_evidence["version"], len(new_evidence["evidence"])), ("0.10", 54))
        self.assertEqual(new_reviews["reviews"][:-1], self.reviews["reviews"])
        self.assertEqual(new_evidence["evidence"][:-4], self.evidence["evidence"])
        self.assertEqual(readiness["reviewed_occurrence_count"], 14)
        self.assertEqual(readiness["reviewed_event_type_diversity"], 12)
        projected = next(row for row in projection["reviews"] if row["analysis_id"] == self.plan["new_analysis_id"])
        self.assertEqual(projected["what_moved"], [])
        self.assertIsNone(projected["canonical"]["start_utc"])

    def test_live_or_simulated_poststate_validates_and_adds_physical_risk_type(self):
        if self.has_aj:
            post_reviews = self.reviews
            post_evidence = self.evidence
        else:
            post_reviews, post_evidence, _, _ = txn.transform(
                self.plan, self.payload, self.canonical, self.sources, self.ledger,
                self.overlay, self.schema, self.reviews, self.evidence
            )
        report = validate_analysis(self.schema, post_evidence, post_reviews, self.canonical)
        self.assertTrue(report.ok, report.errors)
        readiness = analysis_population_readiness(self.schema, post_reviews, self.canonical)
        self.assertGreaterEqual(readiness["eligible_completed_occurrence_count"], 20)
        self.assertGreaterEqual(readiness["reviewed_occurrence_count"], self.plan["postconditions"]["reviewed_occurrence_count"])
        self.assertGreaterEqual(readiness["reviewed_event_type_diversity"], self.plan["postconditions"]["reviewed_event_type_diversity"])
        self.assertEqual(readiness["reviewed_by_event_type"].get("PHYSICAL_RISK_WINDOW"), 1)
        self.assertIn(self.plan["selection"]["selected_occurrence_id"], readiness["reviewed_occurrence_ids"])

    def test_remaining_frontier_is_not_fifo_and_market_structure_is_not_auto_filled(self):
        self.assertFalse(self.plan["guardrails"]["queue_completion_is_population_objective"])
        self.assertFalse(self.plan["guardrails"]["market_structure_gap_must_be_filled_next"])
        self.assertNotIn("WSO-RISK-AU-TC-2025-26", self.plan["postconditions"]["remaining_eligible_unreviewed_occurrence_ids"])
        self.assertIn("WSO-FIN-B-0004", self.plan["postconditions"]["remaining_eligible_unreviewed_occurrence_ids"])

    def test_public_projection_preserves_seasonal_timing_and_null_utc(self):
        if self.has_aj:
            from world_signals.analysis import public_analysis_projection
            projection = public_analysis_projection(self.schema, self.evidence, self.reviews, self.canonical)
        else:
            _, _, _, projection = txn.transform(
                self.plan, self.payload, self.canonical, self.sources, self.ledger,
                self.overlay, self.schema, self.reviews, self.evidence
            )
        row = next(item for item in projection["reviews"] if item["analysis_id"] == self.plan["new_analysis_id"])
        self.assertEqual(row["canonical"]["start_local"], "2025-11-01")
        self.assertEqual(row["canonical"]["end_local"], "2026-04-30")
        self.assertIsNone(row["canonical"]["start_utc"])
        self.assertIsNone(row["canonical"]["source_timezone"])
        self.assertEqual(row["what_surprised"]["status"], "NOT_ESTABLISHED")


if __name__ == "__main__":
    unittest.main()
