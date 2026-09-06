from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/analysis/RBA_FINANCIAL_STABILITY_ANALYSIS_AM_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/analysis/RBA_FINANCIAL_STABILITY_ANALYSIS_AM_PAYLOAD_v0.1.json"
SCRIPT_PATH = ROOT / "scripts/apply_rba_financial_stability_analysis_am.py"

spec = importlib.util.spec_from_file_location("analysis_am_apply", SCRIPT_PATH)
apply_am = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(apply_am)


class RBAFinancialStabilityAnalysisAMTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        cls.payload = json.loads(PAYLOAD_PATH.read_text(encoding="utf-8"))
        cls.canonical = apply_am.load(apply_am.CANONICAL_PATH)
        cls.sources = apply_am.load(apply_am.SOURCES_PATH)
        cls.ledger = apply_am.load(apply_am.LEDGER_PATH)
        cls.overlay = apply_am.load(apply_am.OVERLAY_PATH)
        cls.expectations = apply_am.load(apply_am.EXPECTATIONS_PATH)
        cls.schema = apply_am.load(apply_am.ANALYSIS_SCHEMA_PATH)
        cls.reviews = apply_am.load(apply_am.REVIEWS_PATH)
        cls.evidence = apply_am.load(apply_am.EVIDENCE_PATH)
        cls.review = cls.payload["reviews"][0]

    def _live_or_simulated(self):
        ids = {row.get("analysis_id") for row in self.reviews.get("reviews", [])}
        if self.plan["new_analysis_id"] in ids:
            return self.reviews, self.evidence
        return apply_am.transform(
            self.plan, self.payload, self.canonical, self.sources, self.ledger,
            self.overlay, self.expectations, self.schema, self.reviews, self.evidence,
        )

    def test_plan_is_exact_post_67_and_selects_completed_fsr(self):
        self.assertEqual(self.plan["base_main_sha"], "fd8b69b5edf95a1c7d14c1e236e1a2e8891c74f9")
        self.assertEqual(self.plan["selection"]["selected_occurrence_id"], "WSO-FIN-B-0004")
        pre = self.plan["preconditions"]
        self.assertEqual(pre["required_target_event_type"], "FINANCIAL_STABILITY_REPORT")
        self.assertEqual(pre["required_target_lifecycle"], "COMPLETED")
        self.assertEqual(pre["required_target_start_utc"], "2026-03-19T00:30:00Z")
        self.assertEqual(pre["monitor_expectations_version"], "0.9")

    def test_live_or_simulated_poststate_validates_and_adds_fsr_type(self):
        reviews, evidence = self._live_or_simulated()
        report = apply_am.validate_analysis(self.schema, evidence, reviews, self.canonical)
        self.assertTrue(report.ok, report.errors)
        readiness = apply_am.analysis_population_readiness(self.schema, reviews, self.canonical)
        self.assertEqual(readiness["reviewed_by_event_type"].get("FINANCIAL_STABILITY_REPORT"), 1)
        self.assertGreaterEqual(readiness["reviewed_occurrence_count"], 15)
        self.assertGreaterEqual(readiness["reviewed_event_type_diversity"], 13)

    def test_prior_official_guidance_is_not_promoted_to_consensus(self):
        expected = self.review["what_was_expected"]
        self.assertEqual(len(expected["benchmarks"]), 1)
        self.assertEqual(expected["benchmarks"][0]["benchmark_type"], "OFFICIAL_PRIOR_GUIDANCE")
        self.assertIn("not a forecast", expected["summary"].lower())
        self.assertEqual(self.review["what_surprised"]["status"], "NOT_ESTABLISHED")
        self.assertEqual(self.review["what_surprised"]["comparisons"], [])

    def test_changed_risk_conditions_are_not_directional_surprise(self):
        surprised = self.review["what_surprised"]
        self.assertIn("deterioration", surprised["summary"].lower())
        self.assertIn("not itself forecast error", surprised["summary"].lower())
        self.assertFalse(self.plan["guardrails"]["changed_risk_assessment_is_directional_surprise"])

    def test_exact_canonical_time_does_not_create_market_response(self):
        self.assertEqual(self.review["canonical_release_utc"], "2026-03-19T00:30:00Z")
        self.assertEqual(self.review["what_moved"], [])
        self.assertFalse(self.plan["guardrails"]["same_day_aud_move_is_fsr_specific_market_response"])
        self.assertFalse(self.plan["guardrails"]["exact_canonical_timestamp_confers_exact_market_precision"])
        reviews, _ = self._live_or_simulated()
        self.assertEqual(apply_am.exact_timestamp_series_rows(reviews), 0)

    def test_common_driver_direction_is_not_reversed(self):
        connection = self.review["what_appears_connected"]
        self.assertEqual(connection["interaction_type"], "COMMON_DRIVER_CONTEXT")
        self.assertEqual(connection["causal_status"], "NOT_A_CAUSAL_CLAIM")
        self.assertEqual(connection["confidence"], "HIGH")
        self.assertIn("does not reverse the causal arrow", connection["summary"])
        self.assertFalse(self.plan["guardrails"]["market_volatility_described_by_report_is_caused_by_report"])

    def test_market_context_is_retained_as_noise_and_alternative_not_movement(self):
        joined_noise = " ".join(row["summary"] for row in self.review["what_may_be_noise"])
        joined_alt = " ".join(row["summary"] for row in self.review["alternative_explanations"])
        self.assertIn("Australian dollar", joined_noise)
        self.assertIn("5-4", joined_alt)
        self.assertIn("Fed, ECB, BoJ, BoE, SNB and BoC", joined_alt)
        self.assertEqual(self.review["what_moved"], [])

    def test_second_order_channels_are_watch_items_not_publication_effects(self):
        second = self.review["second_order_effects"]
        self.assertEqual(second["status"], "PLAUSIBLE_WATCH_ITEM")
        self.assertIn("not observed consequences caused by publication", second["summary"])
        self.assertFalse(self.plan["guardrails"]["risk_warning_is_crisis_forecast"])
        self.assertFalse(self.plan["guardrails"]["financial_system_resilience_means_no_vulnerability"])

    def test_evidence_is_analysis_only_and_exactly_five_rows(self):
        evidence = self.payload["evidence"]
        self.assertEqual({row["evidence_id"] for row in evidence}, set(self.plan["new_evidence_ids"]))
        self.assertEqual(len(evidence), 5)
        self.assertEqual(sum(row["evidence_class"] == "PRIMARY_OFFICIAL" for row in evidence), 3)
        self.assertEqual(sum(row["evidence_class"] == "REPUTABLE_NEWSWIRE" for row in evidence), 2)
        for row in evidence:
            self.assertEqual(row["canonical_provenance_effect"], "NONE")

    def test_remaining_frontier_is_not_fifo_or_quota(self):
        remaining = set(self.plan["postconditions"]["remaining_eligible_unreviewed_occurrence_ids"])
        self.assertEqual(len(remaining), 5)
        self.assertNotIn("WSO-FIN-B-0004", remaining)
        self.assertIn("WSO-HEALTH-WHA-079", remaining)
        self.assertFalse(self.plan["guardrails"]["queue_completion_is_population_objective"])
        self.assertFalse(self.plan["guardrails"]["market_structure_gap_must_be_filled_next"])

    def test_exact_prestate_transform_mutates_only_analysis_review_and_evidence(self):
        ids = {row.get("analysis_id") for row in self.reviews.get("reviews", [])}
        if self.plan["new_analysis_id"] in ids:
            self.skipTest("exact AM transform comparison belongs to exact post-67 pre-state")
        before = apply_am.protected_hashes()
        new_reviews, new_evidence = apply_am.transform(
            self.plan, self.payload, self.canonical, self.sources, self.ledger,
            self.overlay, self.expectations, self.schema, self.reviews, self.evidence,
        )
        self.assertEqual(apply_am.protected_hashes(), before)
        self.assertEqual(len(new_reviews["reviews"]), len(self.reviews["reviews"]) + 1)
        self.assertEqual(len(new_evidence["evidence"]), len(self.evidence["evidence"]) + 5)


if __name__ == "__main__":
    unittest.main()
