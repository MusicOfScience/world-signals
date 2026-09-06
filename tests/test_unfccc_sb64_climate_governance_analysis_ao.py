from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/analysis/UNFCCC_SB64_CLIMATE_GOVERNANCE_ANALYSIS_AO_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/analysis/UNFCCC_SB64_CLIMATE_GOVERNANCE_ANALYSIS_AO_PAYLOAD_v0.1.json"
SCRIPT_PATH = ROOT / "scripts/apply_unfccc_sb64_climate_governance_analysis_ao.py"

spec = importlib.util.spec_from_file_location("analysis_ao_apply", SCRIPT_PATH)
apply_ao = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(apply_ao)


class UNFCCCSB64ClimateGovernanceAnalysisAOTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        cls.payload = json.loads(PAYLOAD_PATH.read_text(encoding="utf-8"))
        cls.canonical = apply_ao.load(apply_ao.CANONICAL_PATH)
        cls.sources = apply_ao.load(apply_ao.SOURCES_PATH)
        cls.ledger = apply_ao.load(apply_ao.LEDGER_PATH)
        cls.overlay = apply_ao.load(apply_ao.OVERLAY_PATH)
        cls.expectations = apply_ao.load(apply_ao.EXPECTATIONS_PATH)
        cls.schema = apply_ao.load(apply_ao.ANALYSIS_SCHEMA_PATH)
        cls.reviews = apply_ao.load(apply_ao.REVIEWS_PATH)
        cls.evidence = apply_ao.load(apply_ao.EVIDENCE_PATH)
        cls.review = cls.payload["reviews"][0]
        cls.target = next(
            row for row in cls.canonical["records"]
            if row.get("occurrence_id") == cls.plan["selection"]["selected_occurrence_id"]
        )

    def _live_or_simulated(self):
        ids = {row.get("analysis_id") for row in self.reviews.get("reviews", [])}
        if self.plan["new_analysis_id"] in ids:
            return self.reviews, self.evidence
        return apply_ao.transform(
            self.plan, self.payload, self.canonical, self.sources, self.ledger,
            self.overlay, self.expectations, self.schema, self.reviews, self.evidence,
        )

    def test_plan_is_exact_post_69_and_selects_completed_climate_governance(self):
        self.assertEqual(self.plan["base_main_sha"], "35bcb5616e99c7fce58f82cfc14bfed901929f3a")
        self.assertEqual(self.plan["selection"]["selected_occurrence_id"], "WSO-CLIM-UNFCCC-SB64-202606")
        pre = self.plan["preconditions"]
        self.assertEqual(pre["required_target_category"], "CLIMATE_ENVIRONMENT")
        self.assertEqual(pre["required_target_event_type"], "ENVIRONMENTAL_GOVERNANCE_EVENT")
        self.assertEqual(pre["required_target_lifecycle"], "COMPLETED")
        self.assertEqual(pre["analysis_schema_version"], "0.4")

    def test_canonical_window_remains_source_native_without_synthetic_utc(self):
        self.assertEqual(self.target["timing_type"], "MULTI_DAY_LOCAL")
        self.assertEqual(self.target["start_local"], "2026-06-08")
        self.assertEqual(self.target["end_local"], "2026-06-18")
        self.assertEqual(self.target["source_timezone"], "Europe/Berlin")
        self.assertEqual(self.target["time_precision"], "DAY")
        self.assertTrue(self.target["all_day_semantics"])
        self.assertIsNone(self.target["start_utc"])
        self.assertIsNone(self.target["end_utc"])
        self.assertIsNone(self.review["canonical_release_utc"])
        self.assertFalse(self.plan["guardrails"]["closing_update_clock_resolves_canonical_end_utc"])
        self.assertFalse(self.plan["guardrails"]["post_session_report_publication_retimes_event"])

    def test_sb64_umbrella_preserves_distinct_sbi_and_sbsta_identity(self):
        self.assertIn("SBSTA64 and SBI64 remain legally distinct sessions", self.target["legal_session_identity"])
        happened = self.review["what_happened"]["summary"]
        self.assertIn("legally distinct SBI 64 and SBSTA 64", happened)
        self.assertFalse(self.plan["guardrails"]["sb64_umbrella_merges_sbi64_and_sbsta64"])

    def test_closure_is_not_substantive_resolution(self):
        happened = self.review["what_happened"]["summary"]
        conclusion = self.review["analytical_conclusion"]
        self.assertIn("significant remaining divides", happened)
        self.assertIn("completion did not mean substantive resolution", conclusion)
        self.assertFalse(self.plan["guardrails"]["meeting_completion_implies_negotiation_success"])
        self.assertFalse(self.plan["guardrails"]["meeting_completion_implies_all_agenda_items_resolved"])

    def test_mixed_outcome_is_not_promoted_to_mixed_surprise(self):
        surprise = self.review["what_surprised"]
        self.assertEqual(surprise["status"], "NOT_ESTABLISHED")
        self.assertEqual(surprise["comparisons"], [])
        self.assertIn("does not itself establish a MIXED surprise", surprise["summary"])
        self.assertFalse(self.plan["guardrails"]["mixed_substantive_outcome_is_mixed_surprise"])

    def test_official_scope_is_guidance_not_resolution_forecast(self):
        expected = self.review["what_was_expected"]
        self.assertEqual(len(expected["benchmarks"]), 1)
        self.assertEqual(expected["benchmarks"][0]["benchmark_type"], "OFFICIAL_PRIOR_GUIDANCE")
        self.assertIn("not a forecast", expected["summary"])
        self.assertFalse(self.plan["guardrails"]["agenda_or_draft_count_is_scalar_progress_metric"])

    def test_forwarded_drafts_are_not_adopted_higher_body_decisions(self):
        connection = self.review["what_appears_connected"]
        self.assertEqual(connection["interaction_type"], "LEGAL_OR_OPERATIONAL_DEPENDENCY")
        self.assertEqual(connection["causal_status"], "NOT_A_CAUSAL_CLAIM")
        self.assertEqual(connection["confidence"], "HIGH")
        self.assertIn("does not establish that COP, CMP or CMA will adopt the drafts unchanged", connection["summary"])
        self.assertFalse(self.plan["guardrails"]["draft_decision_forwarded_equals_adopted_decision"])
        self.assertFalse(self.plan["guardrails"]["forwarding_guarantees_later_adoption_unchanged"])

    def test_second_order_effect_is_observed_process_propagation_only(self):
        second = self.review["second_order_effects"]
        self.assertEqual(second["status"], "OBSERVED")
        self.assertIn("formal future-decision inputs", second["summary"])
        self.assertIn("subsequent adoption, amendment, rejection or deferral remains unresolved", second["summary"])
        self.assertGreaterEqual(len(second["evidence_refs"]), 2)

    def test_executive_statement_is_context_not_consensus_text(self):
        joined_noise = " ".join(row["summary"] for row in self.review["what_may_be_noise"])
        self.assertIn("not itself a consensus decision text", joined_noise)
        self.assertFalse(self.plan["guardrails"]["executive_secretary_statement_is_consensus_decision_text"])

    def test_no_market_response_or_exact_series_is_manufactured(self):
        self.assertEqual(self.review["what_moved"], [])
        self.assertFalse(self.plan["guardrails"]["empty_market_response_is_missing_work"])
        reviews, _ = self._live_or_simulated()
        self.assertEqual(apply_ao.exact_timestamp_series_rows(reviews), 0)

    def test_evidence_is_analysis_only_and_five_primary_official_rows(self):
        rows = self.payload["evidence"]
        self.assertEqual({row["evidence_id"] for row in rows}, set(self.plan["new_evidence_ids"]))
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(row["evidence_class"] == "PRIMARY_OFFICIAL" for row in rows))
        self.assertTrue(all(row["canonical_provenance_effect"] == "NONE" for row in rows))
        post_session = {row["evidence_id"]: row for row in rows if row["evidence_id"].endswith("20260828")}
        self.assertEqual(len(post_session), 2)
        self.assertTrue(all(row["published_at"] == "2026-08-28" for row in post_session.values()))

    def test_live_or_simulated_poststate_validates_and_adds_climate_type(self):
        reviews, evidence = self._live_or_simulated()
        report = apply_ao.validate_analysis(self.schema, evidence, reviews, self.canonical)
        self.assertTrue(report.ok, report.errors)
        readiness = apply_ao.analysis_population_readiness(self.schema, reviews, self.canonical)
        self.assertEqual(readiness["reviewed_by_event_type"].get("ENVIRONMENTAL_GOVERNANCE_EVENT"), 1)
        self.assertEqual(readiness["reviewed_occurrence_count"], 17)
        self.assertEqual(readiness["reviewed_event_type_diversity"], 15)

    def test_remaining_frontier_is_not_fifo_or_quota(self):
        remaining = set(self.plan["postconditions"]["remaining_eligible_unreviewed_occurrence_ids"])
        self.assertEqual(len(remaining), 3)
        self.assertNotIn("WSO-CLIM-UNFCCC-SB64-202606", remaining)
        self.assertIn("WSO-HEALTH-WHA-079", remaining)
        self.assertIn("WSO-TRD-EU-RU-SANC-20260625", remaining)
        self.assertIn("WSO-MAC-B-0041", remaining)
        self.assertFalse(self.plan["guardrails"]["queue_completion_is_population_objective"])
        self.assertFalse(self.plan["guardrails"]["market_structure_gap_must_be_filled_next"])

    def test_exact_prestate_transform_mutates_only_analysis_review_and_evidence(self):
        ids = {row.get("analysis_id") for row in self.reviews.get("reviews", [])}
        if self.plan["new_analysis_id"] in ids:
            self.skipTest("exact AO transform comparison belongs to exact post-69 pre-state")
        before = apply_ao.protected_hashes()
        new_reviews, new_evidence = apply_ao.transform(
            self.plan, self.payload, self.canonical, self.sources, self.ledger,
            self.overlay, self.expectations, self.schema, self.reviews, self.evidence,
        )
        self.assertEqual(apply_ao.protected_hashes(), before)
        self.assertEqual(len(new_reviews["reviews"]), len(self.reviews["reviews"]) + 1)
        self.assertEqual(len(new_evidence["evidence"]), len(self.evidence["evidence"]) + 5)
        self.assertEqual(new_reviews["version"], "0.13")
        self.assertEqual(new_evidence["version"], "0.13")


if __name__ == "__main__":
    unittest.main()
