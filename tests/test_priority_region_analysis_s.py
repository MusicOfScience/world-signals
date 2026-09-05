from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.analysis import analysis_population_readiness, validate_analysis


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def version_tuple(value):
    return tuple(int(part) for part in str(value).split("."))


class PriorityRegionAnalysisSTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load("data/analysis/PRIORITY_REGION_ANALYSIS_S_PLAN_v0.1.json")
        cls.schema = load("data/analysis/schema.json")
        cls.reviews = load("data/analysis/event_reviews.json")
        cls.evidence = load("data/analysis/evidence_registry.json")
        cls.canonical = load("data/canonical/registry.json")
        cls.sources = load("data/sources/registry.json")
        cls.expectations = load("data/monitor/expectations.json")
        cls.operations = load("data/monitor/operations_policy.json")
        cls.by_analysis = {row["analysis_id"]: row for row in cls.reviews["reviews"]}
        cls.by_occurrence = {row["occurrence_id"]: row for row in cls.canonical["records"]}
        cls.by_evidence = {row["evidence_id"]: row for row in cls.evidence["evidence"]}

    def test_s_state_survives_descendant_population_and_validator(self):
        self.assertGreaterEqual(version_tuple(self.canonical["version"]), (0, 29))
        self.assertGreaterEqual(len(self.canonical["records"]), 678)
        s_post = self.plan["analysis_post_state"]
        self.assertEqual(s_post["review_count"], 6)
        self.assertEqual(s_post["evidence_count"], 14)
        self.assertGreaterEqual(len(self.reviews["reviews"]), 6)
        self.assertGreaterEqual(len(self.evidence["evidence"]), 14)
        self.assertEqual(self.reviews["canonical_checkpoint"], {"registry_version": "0.29", "record_count": 678})
        s_analysis_ids = {row["analysis_id"] for row in self.plan["new_reviews"]}
        self.assertTrue(s_analysis_ids <= set(self.by_analysis))
        self.assertTrue(set(self.plan["new_evidence_ids"]) <= set(self.by_evidence))
        report = validate_analysis(self.schema, self.evidence, self.reviews, self.canonical)
        self.assertTrue(report.ok, report.errors)

    def test_four_new_samples_bind_to_exact_completed_r_anchors(self):
        expected = {
            "WSAN-IN-GDP-2026Q1-001": ("WSO-HIST-R-IN-GDP-2026Q1", "South Asia", "DATA_RELEASE"),
            "WSAN-ID-BI-202608-001": ("WSO-HIST-R-ID-BI-202608", "Southeast Asia", "MONETARY_POLICY_DECISION_PROCESS"),
            "WSAN-EG-CBE-20260820-001": ("WSO-HIST-R-EG-CBE-20260820", "Africa", "MONETARY_POLICY_DECISION"),
            "WSAN-AR-CPI-202607-001": ("WSO-HIST-R-AR-CPI-202607", "Latin America", "OFFICIAL_STATISTICAL_RELEASE"),
        }
        self.assertTrue(set(expected) <= set(self.by_analysis))
        for analysis_id, (occurrence_id, region, event_type) in expected.items():
            review = self.by_analysis[analysis_id]
            row = self.by_occurrence[occurrence_id]
            self.assertEqual(review["canonical_occurrence_id"], occurrence_id)
            self.assertEqual((row["region"], row["event_type"], row["lifecycle_status"]), (region, event_type, "COMPLETED"))
            self.assertEqual(review["canonical_event_type"], event_type)
            self.assertEqual(review["canonical_release_utc"], row.get("start_utc"))
            self.assertTrue(review["canonical_mutation_prohibited"])
            self.assertFalse(review["google_calendar_write"])

    def test_india_surprise_and_fx_association_preserve_contamination(self):
        review = self.by_analysis["WSAN-IN-GDP-2026Q1-001"]
        self.assertEqual(review["what_surprised"]["status"], "UPSIDE")
        comparison = review["what_surprised"]["comparisons"][0]
        self.assertEqual((comparison["actual"], comparison["expected"], comparison["difference_percentage_points"]), (7.8, 7.1, 0.7))
        self.assertEqual(len(review["what_moved"]), 1)
        move = review["what_moved"][0]
        self.assertEqual(move["movement_representation"], "CHANGE_AND_ENDPOINT")
        self.assertIsNone(move["before_value"])
        self.assertEqual(move["after_value"], 94.95)
        self.assertEqual(move["change"], 0.2)
        self.assertFalse(move["independently_reconstructed"])
        connection = review["what_appears_connected"]
        self.assertEqual((connection["causal_status"], connection["confidence"]), ("OBSERVED_ASSOCIATION", "LOW"))
        alternatives = " ".join(row["summary"] for row in review["alternative_explanations"]).lower()
        self.assertIn("intervention", alternatives)
        self.assertIn("dollar", alternatives)

    def test_null_market_results_are_explicit_not_missing_work(self):
        for analysis_id in (
            "WSAN-ID-BI-202608-001",
            "WSAN-EG-CBE-20260820-001",
            "WSAN-AR-CPI-202607-001",
        ):
            review = self.by_analysis[analysis_id]
            self.assertEqual(review["what_moved"], [])
            connection = review["what_appears_connected"]
            self.assertEqual(connection["causal_status"], "NOT_A_CAUSAL_CLAIM")
            self.assertEqual(connection["confidence"], "LOW")
            self.assertEqual(review["second_order_effects"]["status"], "NOT_ESTABLISHED")

    def test_bi_expected_hold_is_not_relabelled_as_surprise(self):
        review = self.by_analysis["WSAN-ID-BI-202608-001"]
        self.assertEqual(review["what_surprised"]["status"], "NO_CLEAR_SURPRISE")
        benchmark = review["what_was_expected"]["benchmarks"][0]
        self.assertEqual((benchmark["value"], benchmark["benchmark_type"]), (5.75, "MARKET_CONSENSUS_DECISION"))
        comparison = review["what_surprised"]["comparisons"][0]
        self.assertEqual((comparison["actual"], comparison["expected"]), (5.75, 5.75))

    def test_cbe_single_institution_expectation_is_not_synthetic_consensus(self):
        review = self.by_analysis["WSAN-EG-CBE-20260820-001"]
        self.assertEqual(review["what_surprised"]["status"], "NO_CLEAR_SURPRISE")
        benchmark = review["what_was_expected"]["benchmarks"][0]
        self.assertEqual(benchmark["benchmark_type"], "OTHER_DEFENSIBLE_EXPECTATION")
        self.assertEqual(benchmark["value"], "HOLD")
        self.assertIn("does not turn a single institutional forecast", review["what_surprised"]["summary"])

    def test_argentina_surprise_is_preserved_without_market_story(self):
        review = self.by_analysis["WSAN-AR-CPI-202607-001"]
        self.assertEqual(review["what_surprised"]["status"], "UPSIDE")
        comparison = review["what_surprised"]["comparisons"][0]
        self.assertEqual((comparison["actual"], comparison["expected"], comparison["difference_percentage_points"]), (2.1, 2.0, 0.1))
        self.assertEqual(review["what_moved"], [])
        context = " ".join(row["summary"] for row in review["what_may_be_noise"]).lower()
        self.assertIn("winter-holiday", context)

    def test_new_analytical_evidence_is_separate_from_canonical_source_identity(self):
        expected = set(self.plan["new_evidence_ids"])
        self.assertEqual(len(expected), 9)
        self.assertTrue(expected <= set(self.by_evidence))
        canonical_source_ids = {row.get("source_id") for row in self.canonical["records"]}
        self.assertTrue(expected.isdisjoint(canonical_source_ids))
        for evidence_id in expected:
            self.assertEqual(self.by_evidence[evidence_id]["canonical_provenance_effect"], "NONE")

    def test_readiness_remains_controlled_expansion_not_completeness(self):
        readiness = analysis_population_readiness(self.schema, self.reviews, self.canonical)
        self.assertGreaterEqual(readiness["eligible_completed_occurrence_count"], 9)
        self.assertGreaterEqual(readiness["reviewed_occurrence_count"], 6)
        self.assertEqual(readiness["broad_population_state"], "READY_FOR_CONTROLLED_EXPANSION")
        priority = {row["region"]: row for row in readiness["priority_geographic_stress_regions"]}
        for region in ("Africa", "South Asia", "Southeast Asia", "Latin America"):
            self.assertGreaterEqual(priority[region]["eligible_completed_count"], 1)
            self.assertGreaterEqual(priority[region]["reviewed_count"], 1)
            self.assertEqual(priority[region]["state"], "REVIEWED_SAMPLE_PRESENT")
        self.assertGreaterEqual(readiness["reviewed_event_type_diversity"], 2)
        self.assertIn("not a claim of analytical completeness", " ".join(readiness["notes"]).lower())

    def test_plan_and_runtime_keep_all_write_gates_closed(self):
        guardrails = self.plan["guardrails"]
        for key in (
            "canonical_mutation",
            "source_registry_mutation",
            "monitor_configuration_mutation",
            "change_ledger_mutation",
            "biosecurity_overlay_mutation",
            "google_calendar_write",
            "automatic_canonical_commit",
            "missing_market_baseline_may_be_reconstructed",
            "temporal_sequence_establishes_causality",
            "one_review_per_priority_region_implies_completeness",
        ):
            self.assertFalse(guardrails[key])
        self.assertTrue(guardrails["missing_market_move_may_remain_empty"])
        self.assertFalse(self.schema["layer_boundary"]["canonical_mutation_allowed"])
        self.assertFalse(self.schema["layer_boundary"]["calendar_mutation_allowed"])


if __name__ == "__main__":
    unittest.main()
