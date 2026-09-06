from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/analysis/EU_RUSSIA_SANCTIONS_ANALYSIS_AQ_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/analysis/EU_RUSSIA_SANCTIONS_ANALYSIS_AQ_PAYLOAD_v0.1.json"
SCRIPT_PATH = ROOT / "scripts/apply_eu_russia_sanctions_analysis_aq.py"

spec = importlib.util.spec_from_file_location("analysis_aq_apply", SCRIPT_PATH)
apply_aq = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(apply_aq)


class EURussiaSanctionsAnalysisAQTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        cls.payload = json.loads(PAYLOAD_PATH.read_text(encoding="utf-8"))
        cls.canonical = apply_aq.load(apply_aq.CANONICAL_PATH)
        cls.sources = apply_aq.load(apply_aq.SOURCES_PATH)
        cls.ledger = apply_aq.load(apply_aq.LEDGER_PATH)
        cls.overlay = apply_aq.load(apply_aq.OVERLAY_PATH)
        cls.expectations = apply_aq.load(apply_aq.EXPECTATIONS_PATH)
        cls.schema = apply_aq.load(apply_aq.ANALYSIS_SCHEMA_PATH)
        cls.reviews = apply_aq.load(apply_aq.REVIEWS_PATH)
        cls.evidence = apply_aq.load(apply_aq.EVIDENCE_PATH)
        cls.review = cls.payload["reviews"][0]
        cls.target = next(
            row for row in cls.canonical["records"]
            if row.get("occurrence_id") == cls.plan["selection"]["selected_occurrence_id"]
        )

    def _live_or_simulated(self):
        ids = {row.get("analysis_id") for row in self.reviews.get("reviews", [])}
        if self.plan["new_analysis_id"] in ids:
            return self.reviews, self.evidence
        return apply_aq.transform(
            self.plan, self.payload, self.canonical, self.sources, self.ledger,
            self.overlay, self.expectations, self.schema, self.reviews, self.evidence,
        )

    def test_plan_is_exact_post_71_and_selects_completed_sanctions_process(self):
        self.assertEqual(self.plan["base_main_sha"], "c7381ff684e6aeb8c458cdf5eb1740ef6a8a8e3b")
        self.assertEqual(self.plan["selection"]["selected_occurrence_id"], "WSO-TRD-EU-RU-SANC-20260625")
        pre = self.plan["preconditions"]
        self.assertEqual(pre["required_target_category"], "TRADE_SANCTIONS_INDUSTRIAL_POLICY")
        self.assertEqual(pre["required_target_event_type"], "SANCTIONS_PROCESS")
        self.assertEqual(pre["required_target_lifecycle"], "COMPLETED")
        self.assertEqual(pre["analysis_schema_version"], "0.4")

    def test_canonical_legal_adoption_remains_civil_date_without_synthetic_utc(self):
        self.assertEqual(self.target["trade_policy_temporal_role"], "LEGAL_ADOPTION")
        self.assertEqual(self.target["trade_measure_state"], "IN_FORCE")
        self.assertEqual(self.target["timing_type"], "CIVIL_DATE")
        self.assertEqual(self.target["start_local"], "2026-06-25")
        self.assertEqual(self.target["source_timezone"], "Europe/Brussels")
        self.assertEqual(self.target["time_precision"], "DAY")
        self.assertTrue(self.target["all_day_semantics"])
        self.assertIsNone(self.target["start_utc"])
        self.assertIsNone(self.target["end_utc"])
        self.assertIsNone(self.review["canonical_release_utc"])
        self.assertFalse(self.plan["guardrails"]["press_release_publication_time_equals_decision_time"])
        self.assertFalse(self.plan["guardrails"]["analytical_evidence_resolves_missing_canonical_utc"])

    def test_political_agreement_is_expectation_not_binding_adoption(self):
        expected = self.review["what_was_expected"]
        self.assertEqual(len(expected["benchmarks"]), 1)
        benchmark = expected["benchmarks"][0]
        self.assertEqual(benchmark["benchmark_type"], "OTHER_DEFENSIBLE_EXPECTATION")
        self.assertEqual(benchmark["metric"], "pre_adoption_political_agreement")
        self.assertIn("not the binding legal act itself", expected["summary"])
        self.assertFalse(self.plan["guardrails"]["political_agreement_equals_binding_legal_adoption"])

    def test_annual_cadence_novelty_is_not_promoted_to_surprise(self):
        surprise = self.review["what_surprised"]
        self.assertEqual(surprise["status"], "NOT_ESTABLISHED")
        self.assertEqual(surprise["comparisons"], [])
        self.assertIn("novelty is not the same thing as surprise", surprise["summary"])
        self.assertIn("publicly reported as politically agreed", surprise["summary"])
        self.assertFalse(self.plan["guardrails"]["annual_cadence_novelty_equals_surprise"])

    def test_binding_act_and_future_expiry_boundary_remain_distinct(self):
        happened = self.review["what_happened"]["summary"]
        connection = self.review["what_appears_connected"]["summary"]
        self.assertIn("31 July 2027 renewal/expiry boundary remains a separate future canonical occurrence", happened)
        self.assertIn("separate legal-policy decision point", connection)
        self.assertFalse(self.plan["guardrails"]["legal_adoption_equals_future_expiry_boundary"])
        self.assertFalse(self.plan["guardrails"]["expiry_boundary_implies_automatic_termination"])

    def test_renewal_does_not_freeze_later_sanctions_calibration(self):
        connection = self.review["what_appears_connected"]["summary"]
        joined_noise = " ".join(row["summary"] for row in self.review["what_may_be_noise"])
        self.assertIn("21st sanctions package", connection)
        self.assertIn("does not mean its content is fixed until that date", joined_noise)
        self.assertFalse(self.plan["guardrails"]["renewal_freezes_policy_content_until_2027"])
        self.assertFalse(self.plan["guardrails"]["later_sanctions_package_is_caused_by_renewal"])

    def test_same_period_oil_move_is_context_not_renewal_response(self):
        joined_noise = " ".join(row["summary"] for row in self.review["what_may_be_noise"])
        joined_alts = " ".join(row["summary"] for row in self.review["alternative_explanations"])
        self.assertIn("Strait of Hormuz", joined_noise)
        self.assertIn("Iran and Strait of Hormuz", joined_alts)
        self.assertFalse(self.plan["guardrails"]["same_period_oil_move_is_renewal_response"])

    def test_no_market_response_or_exact_series_is_manufactured(self):
        self.assertEqual(self.review["what_moved"], [])
        self.assertFalse(self.plan["guardrails"]["empty_market_response_is_missing_work"])
        reviews, _ = self._live_or_simulated()
        self.assertEqual(apply_aq.exact_timestamp_series_rows(reviews), 0)

    def test_legal_dependency_is_high_confidence_but_noncausal(self):
        connection = self.review["what_appears_connected"]
        self.assertEqual(connection["interaction_type"], "LEGAL_OR_OPERATIONAL_DEPENDENCY")
        self.assertEqual(connection["causal_status"], "NOT_A_CAUSAL_CLAIM")
        self.assertEqual(connection["confidence"], "HIGH")
        self.assertIn("documentary legal dependency", connection["summary"])

    def test_second_order_annual_cadence_effects_remain_watch_items(self):
        second = self.review["second_order_effects"]
        self.assertEqual(second["status"], "PLAUSIBLE_WATCH_ITEM")
        self.assertIn("reduces the frequency of formal renewal decision points", second["summary"])
        self.assertIn("does not claim these effects are realised or caused", second["summary"])

    def test_evidence_packet_is_six_rows_with_separate_roles(self):
        rows = self.payload["evidence"]
        self.assertEqual({row["evidence_id"] for row in rows}, set(self.plan["new_evidence_ids"]))
        self.assertEqual(len(rows), 6)
        self.assertEqual(sum(row["evidence_class"] == "PRIMARY_OFFICIAL" for row in rows), 4)
        self.assertEqual(sum(row["evidence_class"] == "REPUTABLE_NEWSWIRE" for row in rows), 2)
        self.assertTrue(all(row["canonical_provenance_effect"] == "NONE" for row in rows))
        roles = {role for row in rows for role in row.get("roles", [])}
        self.assertIn("OFFICIAL_OUTCOME", roles)
        self.assertIn("EXPECTATION_BENCHMARK", roles)
        self.assertIn("CONTEXT_OR_ALTERNATIVE", roles)

    def test_eurlex_evidence_is_binding_legal_outcome(self):
        row = next(row for row in self.payload["evidence"] if row["evidence_id"] == "WSEV-EU-SANC-EURLEX-20261437")
        joined = " ".join(row["supports"])
        self.assertEqual(row["evidence_class"], "PRIMARY_OFFICIAL")
        self.assertIn("31 July 2027", joined)
        self.assertIn("day following publication", joined)

    def test_live_or_simulated_poststate_validates_and_adds_sanctions_type(self):
        reviews, evidence = self._live_or_simulated()
        report = apply_aq.validate_analysis(self.schema, evidence, reviews, self.canonical)
        self.assertTrue(report.ok, report.errors)
        readiness = apply_aq.analysis_population_readiness(self.schema, reviews, self.canonical)
        self.assertEqual(readiness["reviewed_by_event_type"].get("SANCTIONS_PROCESS"), 1)
        self.assertEqual(readiness["reviewed_occurrence_count"], 19)
        self.assertEqual(readiness["reviewed_event_type_diversity"], 17)
        self.assertEqual(reviews["version"], "0.15")
        self.assertEqual(evidence["version"], "0.15")
        self.assertEqual(len(evidence["evidence"]), 85)

    def test_remaining_frontier_is_japan_only_but_not_a_queue_goal(self):
        remaining = self.plan["postconditions"]["remaining_eligible_unreviewed_occurrence_ids"]
        self.assertEqual(remaining, ["WSO-MAC-B-0041"])
        self.assertFalse(self.plan["guardrails"]["queue_completion_is_population_objective"])
        self.assertFalse(self.plan["guardrails"]["market_structure_gap_must_be_filled_next"])

    def test_exact_prestate_transform_mutates_only_analysis_review_and_evidence(self):
        ids = {row.get("analysis_id") for row in self.reviews.get("reviews", [])}
        if self.plan["new_analysis_id"] in ids:
            self.skipTest("exact AQ transform comparison belongs to exact post-71 pre-state")
        before = apply_aq.protected_hashes()
        new_reviews, new_evidence = apply_aq.transform(
            self.plan, self.payload, self.canonical, self.sources, self.ledger,
            self.overlay, self.expectations, self.schema, self.reviews, self.evidence,
        )
        self.assertEqual(apply_aq.protected_hashes(), before)
        self.assertEqual(len(new_reviews["reviews"]), len(self.reviews["reviews"]) + 1)
        self.assertEqual(len(new_evidence["evidence"]), len(self.evidence["evidence"]) + 6)
        self.assertEqual(new_reviews["version"], "0.15")
        self.assertEqual(new_evidence["version"], "0.15")


if __name__ == "__main__":
    unittest.main()
