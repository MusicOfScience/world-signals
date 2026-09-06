from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/analysis/WHO_WHA79_HEALTH_GOVERNANCE_ANALYSIS_AP_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/analysis/WHO_WHA79_HEALTH_GOVERNANCE_ANALYSIS_AP_PAYLOAD_v0.1.json"
SCRIPT_PATH = ROOT / "scripts/apply_who_wha79_health_governance_analysis_ap.py"

spec = importlib.util.spec_from_file_location("analysis_ap_apply", SCRIPT_PATH)
apply_ap = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(apply_ap)


class WHA79HealthGovernanceAnalysisAPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        cls.payload = json.loads(PAYLOAD_PATH.read_text(encoding="utf-8"))
        cls.canonical = apply_ap.load(apply_ap.CANONICAL_PATH)
        cls.sources = apply_ap.load(apply_ap.SOURCES_PATH)
        cls.ledger = apply_ap.load(apply_ap.LEDGER_PATH)
        cls.overlay = apply_ap.load(apply_ap.OVERLAY_PATH)
        cls.expectations = apply_ap.load(apply_ap.EXPECTATIONS_PATH)
        cls.schema = apply_ap.load(apply_ap.ANALYSIS_SCHEMA_PATH)
        cls.reviews = apply_ap.load(apply_ap.REVIEWS_PATH)
        cls.evidence = apply_ap.load(apply_ap.EVIDENCE_PATH)
        cls.review = cls.payload["reviews"][0]
        cls.target = next(
            row for row in cls.canonical["records"]
            if row.get("occurrence_id") == cls.plan["selection"]["selected_occurrence_id"]
        )

    def _live_or_simulated(self):
        ids = {row.get("analysis_id") for row in self.reviews.get("reviews", [])}
        if self.plan["new_analysis_id"] in ids:
            return self.reviews, self.evidence
        return apply_ap.transform(
            self.plan, self.payload, self.canonical, self.sources, self.ledger,
            self.overlay, self.expectations, self.schema, self.reviews, self.evidence,
        )

    def test_plan_is_exact_post_70_and_selects_completed_health_governance(self):
        self.assertEqual(self.plan["base_main_sha"], "fb795411b217a05a94874e06f30fa44d7fc3ff8d")
        self.assertEqual(self.plan["selection"]["selected_occurrence_id"], "WSO-HEALTH-WHA-079")
        pre = self.plan["preconditions"]
        self.assertEqual(pre["required_target_category"], "HEALTH_BIOSECURITY")
        self.assertEqual(pre["required_target_event_type"], "HEALTH_GOVERNANCE_EVENT")
        self.assertEqual(pre["required_target_lifecycle"], "COMPLETED")
        self.assertEqual(pre["analysis_schema_version"], "0.4")

    def test_canonical_window_remains_source_native_without_synthetic_utc(self):
        self.assertEqual(self.target["timing_type"], "MULTI_DAY_LOCAL")
        self.assertEqual(self.target["start_local"], "2026-05-18")
        self.assertEqual(self.target["end_local"], "2026-05-23")
        self.assertEqual(self.target["source_timezone"], "Europe/Zurich")
        self.assertEqual(self.target["time_precision"], "DAY")
        self.assertTrue(self.target["all_day_semantics"])
        self.assertIsNone(self.target["start_utc"])
        self.assertIsNone(self.target["end_utc"])
        self.assertIsNone(self.review["canonical_release_utc"])
        self.assertFalse(self.plan["guardrails"]["later_igwg_meeting_retimes_wha79"])
        self.assertFalse(self.plan["guardrails"]["analytical_evidence_resolves_missing_canonical_utc"])

    def test_decision_count_is_not_scalar_success_or_impact_metric(self):
        happened = self.review["what_happened"]["summary"]
        self.assertIn("more than 20 decisions and 13 resolutions", happened)
        joined_noise = " ".join(row["summary"] for row in self.review["what_may_be_noise"])
        self.assertIn("scalar success or impact score", joined_noise)
        self.assertFalse(self.plan["guardrails"]["decision_count_is_scalar_success_metric"])

    def test_assembly_completion_is_not_resolution_or_plan_implementation(self):
        happened = self.review["what_happened"]["summary"]
        joined_noise = " ".join(row["summary"] for row in self.review["what_may_be_noise"])
        self.assertIn("not completion or implementation of every process and plan", happened)
        self.assertIn("Assembly closure on 23 May", joined_noise)
        self.assertFalse(self.plan["guardrails"]["assembly_completion_implies_resolution_implementation"])

    def test_pabs_continuation_is_not_annex_adoption_or_ratification(self):
        happened = self.review["what_happened"]["summary"]
        connection = self.review["what_appears_connected"]["summary"]
        self.assertIn("it did not adopt the Annex", happened)
        self.assertIn("PABS Annex is complete", connection)
        self.assertFalse(self.plan["guardrails"]["pabs_continuation_equals_pabs_annex_adoption"])
        self.assertFalse(self.plan["guardrails"]["pabs_continuation_equals_pandemic_agreement_ratification"])

    def test_pre_wha_pabs_guidance_is_not_aggregate_consensus_forecast(self):
        expected = self.review["what_was_expected"]
        self.assertEqual(len(expected["benchmarks"]), 1)
        self.assertEqual(expected["benchmarks"][0]["benchmark_type"], "OFFICIAL_PRIOR_GUIDANCE")
        self.assertEqual(expected["benchmarks"][0]["metric"], "pabs_pre_wha_process_status")
        self.assertIn("PABS workstream only", expected["summary"])
        self.assertFalse(self.plan["guardrails"]["official_pre_event_process_guidance_is_aggregate_consensus_forecast"])

    def test_aggregate_surprise_is_not_established(self):
        surprise = self.review["what_surprised"]
        self.assertEqual(surprise["status"], "NOT_ESTABLISHED")
        self.assertEqual(surprise["comparisons"], [])
        self.assertIn("No defensible aggregate pre-event consensus benchmark", surprise["summary"])

    def test_global_health_architecture_process_establishment_is_not_reform_completion(self):
        happened = self.review["what_happened"]["summary"]
        joined_noise = " ".join(row["summary"] for row in self.review["what_may_be_noise"])
        self.assertIn("established a one-year", happened)
        self.assertIn("not equivalent to completing reform", joined_noise)
        self.assertFalse(self.plan["guardrails"]["gha_process_establishment_equals_reform_completion"])

    def test_amr_plan_adoption_is_not_realised_health_effect(self):
        happened = self.review["what_happened"]["summary"]
        joined_noise = " ".join(row["summary"] for row in self.review["what_may_be_noise"])
        self.assertIn("Global Action Plan on antimicrobial resistance 2026-2036", happened)
        self.assertIn("does not by itself establish national implementation", joined_noise)
        self.assertFalse(self.plan["guardrails"]["amr_plan_adoption_equals_health_effect"])

    def test_observed_second_order_effect_is_later_igwg_process_propagation_only(self):
        second = self.review["second_order_effects"]
        connection = self.review["what_appears_connected"]
        self.assertEqual(second["status"], "OBSERVED")
        self.assertEqual(connection["interaction_type"], "LEGAL_OR_OPERATIONAL_DEPENDENCY")
        self.assertEqual(connection["causal_status"], "NOT_A_CAUSAL_CLAIM")
        self.assertEqual(connection["confidence"], "HIGH")
        self.assertIn("seventh IGWG meeting on 6-17 July 2026", second["summary"])
        self.assertIn("substantive Annex agreement", second["summary"])

    def test_same_period_health_emergencies_are_context_not_assembly_effect(self):
        joined_noise = " ".join(row["summary"] for row in self.review["what_may_be_noise"])
        self.assertIn("not evidence that WHA79 caused the outbreaks", joined_noise)
        self.assertFalse(self.plan["guardrails"]["same_period_health_emergency_is_caused_by_assembly"])

    def test_no_market_response_or_exact_series_is_manufactured(self):
        self.assertEqual(self.review["what_moved"], [])
        self.assertFalse(self.plan["guardrails"]["empty_market_response_is_missing_work"])
        reviews, _ = self._live_or_simulated()
        self.assertEqual(apply_ap.exact_timestamp_series_rows(reviews), 0)

    def test_evidence_is_analysis_only_and_exactly_seven_primary_official_rows(self):
        rows = self.payload["evidence"]
        self.assertEqual({row["evidence_id"] for row in rows}, set(self.plan["new_evidence_ids"]))
        self.assertEqual(len(rows), 7)
        self.assertTrue(all(row["evidence_class"] == "PRIMARY_OFFICIAL" for row in rows))
        self.assertTrue(all(row["canonical_provenance_effect"] == "NONE" for row in rows))
        roles = {role for row in rows for role in row.get("roles", [])}
        self.assertIn("EXPECTATION_BENCHMARK", roles)
        self.assertIn("SECOND_ORDER_OBSERVATION", roles)

    def test_live_or_simulated_poststate_validates_and_adds_health_governance_type(self):
        reviews, evidence = self._live_or_simulated()
        report = apply_ap.validate_analysis(self.schema, evidence, reviews, self.canonical)
        self.assertTrue(report.ok, report.errors)
        readiness = apply_ap.analysis_population_readiness(self.schema, reviews, self.canonical)
        self.assertEqual(readiness["reviewed_by_event_type"].get("HEALTH_GOVERNANCE_EVENT"), 1)
        self.assertGreaterEqual(readiness["reviewed_occurrence_count"], 18)
        self.assertGreaterEqual(readiness["reviewed_event_type_diversity"], 16)
        self.assertGreaterEqual(tuple(map(int, reviews["version"].split("."))), (0, 14))
        self.assertGreaterEqual(tuple(map(int, evidence["version"].split("."))), (0, 14))
        self.assertGreaterEqual(len(evidence["evidence"]), 79)

    def test_remaining_frontier_is_not_fifo_or_quota(self):
        remaining = set(self.plan["postconditions"]["remaining_eligible_unreviewed_occurrence_ids"])
        self.assertEqual(remaining, {"WSO-MAC-B-0041", "WSO-TRD-EU-RU-SANC-20260625"})
        self.assertNotIn("WSO-HEALTH-WHA-079", remaining)
        self.assertFalse(self.plan["guardrails"]["queue_completion_is_population_objective"])
        self.assertFalse(self.plan["guardrails"]["market_structure_gap_must_be_filled_next"])

    def test_exact_prestate_transform_mutates_only_analysis_review_and_evidence(self):
        ids = {row.get("analysis_id") for row in self.reviews.get("reviews", [])}
        if self.plan["new_analysis_id"] in ids:
            self.skipTest("exact AP transform comparison belongs to exact post-70 pre-state")
        before = apply_ap.protected_hashes()
        new_reviews, new_evidence = apply_ap.transform(
            self.plan, self.payload, self.canonical, self.sources, self.ledger,
            self.overlay, self.expectations, self.schema, self.reviews, self.evidence,
        )
        self.assertEqual(apply_ap.protected_hashes(), before)
        self.assertEqual(len(new_reviews["reviews"]), len(self.reviews["reviews"]) + 1)
        self.assertEqual(len(new_evidence["evidence"]), len(self.evidence["evidence"]) + 7)
        self.assertEqual(new_reviews["version"], "0.14")
        self.assertEqual(new_evidence["version"], "0.14")


if __name__ == "__main__":
    unittest.main()
