from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/analysis/IMD_HEATWAVE_OUTLOOK_ANALYSIS_AU_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/analysis/IMD_HEATWAVE_OUTLOOK_ANALYSIS_AU_PAYLOAD_v0.1.json"
SCRIPT_PATH = ROOT / "scripts/apply_imd_heatwave_outlook_analysis_au.py"

spec = importlib.util.spec_from_file_location("analysis_au_apply", SCRIPT_PATH)
apply_au = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(apply_au)


def version_tuple(raw: str) -> tuple[int, ...]:
    return tuple(int(part) for part in str(raw).split("."))


class IMDHeatwaveOutlookAnalysisAUTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        cls.payload = json.loads(PAYLOAD_PATH.read_text(encoding="utf-8"))
        cls.canonical = apply_au.load(apply_au.CANONICAL_PATH)
        cls.sources = apply_au.load(apply_au.SOURCES_PATH)
        cls.ledger = apply_au.load(apply_au.LEDGER_PATH)
        cls.overlay = apply_au.load(apply_au.OVERLAY_PATH)
        cls.expectations = apply_au.load(apply_au.EXPECTATIONS_PATH)
        cls.schema = apply_au.load(apply_au.ANALYSIS_SCHEMA_PATH)
        cls.reviews = apply_au.load(apply_au.REVIEWS_PATH)
        cls.evidence = apply_au.load(apply_au.EVIDENCE_PATH)
        cls.review = cls.payload["reviews"][0]
        cls.target = next(
            row for row in cls.canonical["records"]
            if row.get("occurrence_id") == cls.plan["selection"]["selected_occurrence_id"]
        )

    def _live_or_simulated(self):
        ids = {row.get("analysis_id") for row in self.reviews.get("reviews", [])}
        if self.plan["new_analysis_id"] in ids:
            return self.reviews, self.evidence
        return apply_au.transform(
            self.plan, self.payload, self.canonical, self.sources, self.ledger,
            self.overlay, self.expectations, self.schema, self.reviews, self.evidence,
        )

    def test_plan_is_exact_post_75_and_selects_physical_risk_outlook(self):
        self.assertEqual(self.plan["base_main_sha"], "03a8f87f17570c2520edadf78237ed07d946107a")
        self.assertEqual(self.plan["selection"]["selected_occurrence_id"], "WSO-RISK-A-0002")
        pre = self.plan["preconditions"]
        self.assertEqual((pre["canonical_registry_version"], pre["canonical_record_count"]), ("0.38", 688))
        self.assertEqual(pre["required_target_category"], "PHYSICAL_CLIMATE_RISK")
        self.assertEqual(pre["required_target_event_type"], "PHYSICAL_RISK_OUTLOOK_RELEASE")
        self.assertEqual(pre["required_target_signal_object_class"], "SCHEDULED_INFORMATION_CATALYST")
        self.assertEqual(pre["required_target_lifecycle"], "COMPLETED")
        self.assertEqual(pre["eligible_completed_occurrence_count"], 21)

    def test_canonical_object_is_publication_not_heatwave_window(self):
        self.assertEqual(self.target["timing_type"], "CIVIL_DATE")
        self.assertEqual(self.target["start_local"], "2026-03-31")
        self.assertIsNone(self.target["end_local"])
        self.assertEqual(self.target["source_timezone"], "Asia/Kolkata")
        self.assertEqual(self.target["time_precision"], "DAY")
        self.assertTrue(self.target["all_day_semantics"])
        self.assertIsNone(self.target["start_utc"])
        self.assertIsNone(self.target["end_utc"])
        self.assertEqual(self.target["publication_time_semantics"], "DATE_ONLY")
        self.assertEqual(self.target["physical_shock_routing"], "NO_SHOCK_IN_THIS_RECORD")
        self.assertIn("April–June 2026", self.target["reference_period"])
        self.assertFalse(self.plan["guardrails"]["forecast_period_equals_occurrence_timing"])
        self.assertFalse(self.plan["guardrails"]["hazard_equals_publication_event"])

    def test_prior_guidance_is_not_matched_forecast_error_benchmark(self):
        expected = self.review["what_was_expected"]
        self.assertEqual(len(expected["benchmarks"]), 1)
        benchmark = expected["benchmarks"][0]
        self.assertEqual(benchmark["benchmark_type"], "OFFICIAL_PRIOR_GUIDANCE")
        self.assertEqual(benchmark["metric"], "prior_official_seasonal_heatwave_guidance")
        self.assertIn("March-May", expected["summary"])
        self.assertIn("April-June", expected["summary"])
        self.assertFalse(self.plan["guardrails"]["prior_mam_guidance_equals_matched_amj_benchmark"])

    def test_surprise_is_not_established_without_matching_pre_release_benchmark(self):
        surprise = self.review["what_surprised"]
        self.assertEqual(surprise["status"], "NOT_ESTABLISHED")
        self.assertEqual(surprise["comparisons"], [])
        self.assertIn("non-identical", surprise["summary"])
        self.assertFalse(self.plan["guardrails"]["forecast_evolution_equals_surprise"])

    def test_later_monthly_and_operational_products_are_context_not_skill_score(self):
        connection = self.review["what_appears_connected"]
        self.assertEqual(connection["interaction_type"], "OBSERVATION_CONTEXT")
        self.assertEqual(connection["causal_status"], "NOT_A_CAUSAL_CLAIM")
        self.assertEqual(connection["confidence"], "HIGH")
        self.assertIn("forecast-evolution", connection["summary"])
        self.assertIn("skill metric", connection["summary"])
        self.assertFalse(self.plan["guardrails"]["later_monthly_forecast_equals_verifying_observation"])
        self.assertFalse(self.plan["guardrails"]["spatial_overlap_equals_skill_score"])
        self.assertFalse(self.plan["guardrails"]["later_heatwave_equals_forecast_success"])
        self.assertFalse(self.plan["guardrails"]["later_abatement_equals_forecast_failure"])

    def test_publication_is_not_causal_driver_of_heatwave_or_impacts(self):
        joined = " ".join(row["summary"] for row in self.review["what_may_be_noise"])
        self.assertIn("publication does not cause", joined)
        self.assertFalse(self.plan["guardrails"]["publication_causes_heatwave"])
        self.assertFalse(self.plan["guardrails"]["publication_causes_preparedness_or_impacts"])

    def test_second_order_channels_are_watch_items_not_observed_effects(self):
        second = self.review["second_order_effects"]
        self.assertEqual(second["status"], "PLAUSIBLE_WATCH_ITEM")
        self.assertIn("public-health", second["summary"])
        self.assertIn("does not claim", second["summary"])

    def test_no_market_response_or_exact_series_is_manufactured(self):
        self.assertEqual(self.review["what_moved"], [])
        self.assertFalse(self.plan["guardrails"]["same_period_market_move_is_publication_response"])
        self.assertFalse(self.plan["guardrails"]["empty_market_response_is_missing_work"])
        reviews, _ = self._live_or_simulated()
        self.assertEqual(apply_au.exact_timestamp_series_rows(reviews), 0)

    def test_evidence_packet_is_six_primary_official_analysis_only_rows(self):
        rows = self.payload["evidence"]
        self.assertEqual({row["evidence_id"] for row in rows}, set(self.plan["new_evidence_ids"]))
        self.assertEqual(len(rows), 6)
        self.assertTrue(all(row["evidence_class"] == "PRIMARY_OFFICIAL" for row in rows))
        self.assertTrue(all(row["canonical_provenance_effect"] == "NONE" for row in rows))
        roles = {role for row in rows for role in row.get("roles", [])}
        self.assertIn("OFFICIAL_OUTCOME", roles)
        self.assertIn("EXPECTATION_BENCHMARK", roles)
        self.assertIn("CONTEXT_OR_ALTERNATIVE", roles)

    def test_noise_alternatives_and_falsifiers_are_substantive(self):
        self.assertGreaterEqual(len(self.review["what_may_be_noise"]), 10)
        self.assertGreaterEqual(len(self.review["alternative_explanations"]), 4)
        self.assertGreaterEqual(len(self.review["falsifiers"]), 10)

    def test_live_or_simulated_poststate_validates_and_preserves_au_checkpoint(self):
        reviews, evidence = self._live_or_simulated()
        report = apply_au.validate_analysis(self.schema, evidence, reviews, self.canonical)
        self.assertTrue(report.ok, report.errors)
        readiness = apply_au.analysis_population_readiness(self.schema, reviews, self.canonical)
        self.assertEqual(readiness["reviewed_by_event_type"].get("PHYSICAL_RISK_OUTLOOK_RELEASE"), 1)
        self.assertGreaterEqual(readiness["reviewed_occurrence_count"], 20)
        self.assertGreaterEqual(readiness["reviewed_event_type_diversity"], 18)
        # AU freezes the historical eligible-completed checkpoint at 21; later reviewed
        # Canonical lifecycle growth may legitimately increase that population.
        self.assertGreaterEqual(
            readiness["eligible_completed_occurrence_count"],
            self.plan["preconditions"]["eligible_completed_occurrence_count"],
        )
        self.assertGreaterEqual(version_tuple(reviews["version"]), (0, 16))
        self.assertEqual(reviews["canonical_checkpoint"], {"registry_version": "0.38", "record_count": 688})
        self.assertGreaterEqual(version_tuple(evidence["version"]), (0, 16))
        self.assertGreaterEqual(len(evidence["evidence"]), 91)

        # The historical AU post-state itself remains exact in the frozen plan.
        post = self.plan["postconditions"]
        self.assertEqual(post["analysis_reviews_version"], "0.16")
        self.assertEqual(post["analysis_review_count"], 20)
        self.assertEqual(post["analysis_evidence_version"], "0.16")
        self.assertEqual(post["analysis_evidence_count"], 91)

    def test_remaining_frontier_is_japan_only_but_not_queue_goal(self):
        self.assertEqual(self.plan["postconditions"]["remaining_eligible_unreviewed_occurrence_ids"], ["WSO-MAC-B-0041"])
        self.assertFalse(self.plan["guardrails"]["queue_completion_is_population_objective"])
        self.assertFalse(self.plan["guardrails"]["japan_revision_requires_canonical_retiming"])

    def test_exact_prestate_transform_mutates_only_analysis_review_and_evidence(self):
        ids = {row.get("analysis_id") for row in self.reviews.get("reviews", [])}
        if self.plan["new_analysis_id"] in ids:
            self.skipTest("exact AU transform comparison belongs to exact post-#75 pre-state")
        before = apply_au.protected_hashes()
        new_reviews, new_evidence = apply_au.transform(
            self.plan, self.payload, self.canonical, self.sources, self.ledger,
            self.overlay, self.expectations, self.schema, self.reviews, self.evidence,
        )
        self.assertEqual(apply_au.protected_hashes(), before)
        self.assertEqual(len(new_reviews["reviews"]), len(self.reviews["reviews"]) + 1)
        self.assertEqual(len(new_evidence["evidence"]), len(self.evidence["evidence"]) + 6)
        self.assertEqual(new_reviews["version"], "0.16")
        self.assertEqual(new_reviews["canonical_checkpoint"], {"registry_version": "0.38", "record_count": 688})
        self.assertEqual(new_evidence["version"], "0.16")


if __name__ == "__main__":
    unittest.main()
