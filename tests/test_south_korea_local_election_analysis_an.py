from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/analysis/SOUTH_KOREA_LOCAL_ELECTION_ANALYSIS_AN_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/analysis/SOUTH_KOREA_LOCAL_ELECTION_ANALYSIS_AN_PAYLOAD_v0.1.json"
SCRIPT_PATH = ROOT / "scripts/apply_south_korea_local_election_analysis_an.py"

spec = importlib.util.spec_from_file_location("analysis_an_apply", SCRIPT_PATH)
apply_an = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(apply_an)


class SouthKoreaLocalElectionAnalysisANTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        cls.payload = json.loads(PAYLOAD_PATH.read_text(encoding="utf-8"))
        cls.canonical = apply_an.load(apply_an.CANONICAL_PATH)
        cls.sources = apply_an.load(apply_an.SOURCES_PATH)
        cls.ledger = apply_an.load(apply_an.LEDGER_PATH)
        cls.overlay = apply_an.load(apply_an.OVERLAY_PATH)
        cls.expectations = apply_an.load(apply_an.EXPECTATIONS_PATH)
        cls.schema = apply_an.load(apply_an.ANALYSIS_SCHEMA_PATH)
        cls.reviews = apply_an.load(apply_an.REVIEWS_PATH)
        cls.evidence = apply_an.load(apply_an.EVIDENCE_PATH)
        cls.review = cls.payload["reviews"][0]
        cls.target = next(
            row for row in cls.canonical["records"]
            if row.get("occurrence_id") == cls.plan["selection"]["selected_occurrence_id"]
        )

    def _live_or_simulated(self):
        ids = {row.get("analysis_id") for row in self.reviews.get("reviews", [])}
        if self.plan["new_analysis_id"] in ids:
            return self.reviews, self.evidence
        return apply_an.transform(
            self.plan,
            self.payload,
            self.canonical,
            self.sources,
            self.ledger,
            self.overlay,
            self.expectations,
            self.schema,
            self.reviews,
            self.evidence,
        )

    def test_plan_is_exact_post_68_and_selects_completed_election(self):
        self.assertEqual(self.plan["base_main_sha"], "d9dc06da84608f74297f94c426ab77706d9223e0")
        self.assertEqual(self.plan["selection"]["selected_occurrence_id"], "WSO-EL-KR-LGE-20260603")
        pre = self.plan["preconditions"]
        self.assertEqual(pre["required_target_event_type"], "ELECTION_MILESTONE")
        self.assertEqual(pre["required_target_category"], "ELECTIONS_GOVERNANCE")
        self.assertEqual(pre["required_target_lifecycle"], "COMPLETED")
        self.assertEqual(pre["analysis_schema_version"], "0.4")

    def test_canonical_election_remains_civil_date_without_synthetic_utc(self):
        self.assertEqual(self.target["timing_type"], "CIVIL_DATE")
        self.assertEqual(self.target["start_local"], "2026-06-03")
        self.assertEqual(self.target["source_timezone"], "Asia/Seoul")
        self.assertEqual(self.target["time_precision"], "DAY")
        self.assertTrue(self.target["all_day_semantics"])
        self.assertIsNone(self.target["start_utc"])
        self.assertIsNone(self.review["canonical_release_utc"])
        self.assertFalse(self.plan["guardrails"]["polling_hours_resolve_canonical_utc"])
        self.assertFalse(self.plan["guardrails"]["early_voting_redefines_canonical_election_day"])

    def test_major_result_is_subaggregate_not_single_national_result(self):
        actuals = {row["metric"]: row["value"] for row in self.review["what_happened"]["actuals"]}
        self.assertEqual(actuals["major_mayoral_provincial_contests_won_by_democratic_party"], 12)
        self.assertEqual(actuals["major_mayoral_provincial_contests_won_by_people_power_party"], 4)
        self.assertIn("important subset", self.review["what_happened"]["summary"])
        self.assertFalse(self.plan["guardrails"]["nationwide_simultaneous_election_is_single_national_result"])
        self.assertFalse(self.plan["guardrails"]["major_mayoral_provincial_12_of_16_is_complete_election_result"])

    def test_pre_election_context_is_directional_not_exact_seat_forecast(self):
        expected = self.review["what_was_expected"]
        self.assertEqual(len(expected["benchmarks"]), 1)
        self.assertEqual(expected["benchmarks"][0]["benchmark_type"], "OTHER_DEFENSIBLE_EXPECTATION")
        self.assertIn("directional", expected["summary"].lower())
        self.assertIn("does not infer an expected 12-4 result", expected["summary"])
        self.assertFalse(self.plan["guardrails"]["party_polling_is_exact_seat_forecast"])

    def test_post_vote_exit_poll_is_not_pre_event_expectation(self):
        expected_refs = set(self.review["what_was_expected"]["evidence_refs"])
        surprise_refs = set(self.review["what_surprised"]["evidence_refs"])
        exit_ref = "WSEV-KR-LGE-REUTERS-EXITPOLL-20260603"
        self.assertNotIn(exit_ref, expected_refs)
        self.assertIn(exit_ref, surprise_refs)
        self.assertEqual(self.review["what_surprised"]["status"], "NOT_ESTABLISHED")
        self.assertEqual(self.review["what_surprised"]["comparisons"], [])
        self.assertFalse(self.plan["guardrails"]["post_vote_exit_poll_is_pre_event_expectation"])

    def test_ballot_administration_counts_remain_three_distinct_quantities(self):
        actuals = {row["metric"]: row["value"] for row in self.review["what_happened"]["actuals"]}
        self.assertEqual(actuals["polling_stations_receiving_supplemental_ballots"], 140)
        self.assertEqual(actuals["polling_stations_using_supplemental_ballots"], 91)
        self.assertEqual(actuals["polling_stations_with_temporary_voting_interruption_and_resumption"], 26)
        self.assertGreater(actuals["polling_stations_receiving_supplemental_ballots"], actuals["polling_stations_using_supplemental_ballots"])
        self.assertGreater(actuals["polling_stations_using_supplemental_ballots"], actuals["polling_stations_with_temporary_voting_interruption_and_resumption"])

    def test_ballot_failure_is_not_fraud_invalidity_or_partisan_result_cause(self):
        joined_noise = " ".join(row["summary"] for row in self.review["what_may_be_noise"])
        self.assertIn("not adjudicated evidence of fraud", joined_noise)
        self.assertIn("does not establish that the overall partisan result", joined_noise)
        self.assertFalse(self.plan["guardrails"]["ballot_shortage_establishes_fraud"])
        self.assertFalse(self.plan["guardrails"]["ballot_shortage_automatically_invalidates_reported_winners"])
        self.assertFalse(self.plan["guardrails"]["ballot_shortage_is_proven_cause_of_partisan_result"])

    def test_observed_connection_attaches_to_administration_response_not_dp_result(self):
        connection = self.review["what_appears_connected"]
        self.assertEqual(connection["interaction_type"], "POLICY_RESPONSE_CONTEXT")
        self.assertEqual(connection["causal_status"], "OBSERVED_ASSOCIATION")
        self.assertEqual(connection["confidence"], "MEDIUM")
        self.assertIn("election administration", connection["summary"])
        self.assertIn("not a claim that ballot shortages caused the 12-4 partisan distribution", connection["summary"])
        self.assertFalse(self.plan["guardrails"]["protests_and_reform_are_caused_by_dp_12_of_16_result"])

    def test_second_order_institutional_consequences_are_observed(self):
        second = self.review["second_order_effects"]
        self.assertEqual(second["status"], "OBSERVED")
        self.assertIn("protests", second["summary"])
        self.assertIn("National Election Commission", second["summary"])
        self.assertIn("not consequences attributed to the DP's 12-of-16", second["summary"])
        self.assertGreaterEqual(len(second["evidence_refs"]), 3)

    def test_no_market_response_or_exact_timestamp_series_is_manufactured(self):
        self.assertEqual(self.review["what_moved"], [])
        self.assertFalse(self.plan["guardrails"]["empty_market_response_is_missing_work"])
        reviews, _ = self._live_or_simulated()
        self.assertEqual(apply_an.exact_timestamp_series_rows(reviews), 0)

    def test_evidence_is_analysis_only_and_exactly_eight_rows(self):
        evidence = self.payload["evidence"]
        self.assertEqual({row["evidence_id"] for row in evidence}, set(self.plan["new_evidence_ids"]))
        self.assertEqual(len(evidence), 8)
        self.assertEqual(sum(row["evidence_class"] == "PRIMARY_OFFICIAL" for row in evidence), 1)
        self.assertEqual(sum(row["evidence_class"] == "REPUTABLE_NEWSWIRE" for row in evidence), 5)
        self.assertEqual(sum(row["evidence_class"] == "REPUTABLE_MEDIA" for row in evidence), 2)
        for row in evidence:
            self.assertEqual(row["canonical_provenance_effect"], "NONE")

    def test_live_or_simulated_poststate_validates_and_adds_election_type(self):
        reviews, evidence = self._live_or_simulated()
        report = apply_an.validate_analysis(self.schema, evidence, reviews, self.canonical)
        self.assertTrue(report.ok, report.errors)
        readiness = apply_an.analysis_population_readiness(self.schema, reviews, self.canonical)
        self.assertEqual(readiness["reviewed_by_event_type"].get("ELECTION_MILESTONE"), 1)
        self.assertEqual(readiness["reviewed_occurrence_count"], 16)
        self.assertEqual(readiness["reviewed_event_type_diversity"], 14)

    def test_remaining_frontier_is_not_fifo_or_quota(self):
        remaining = set(self.plan["postconditions"]["remaining_eligible_unreviewed_occurrence_ids"])
        self.assertEqual(len(remaining), 4)
        self.assertNotIn("WSO-EL-KR-LGE-20260603", remaining)
        self.assertIn("WSO-CLIM-UNFCCC-SB64-202606", remaining)
        self.assertIn("WSO-HEALTH-WHA-079", remaining)
        self.assertFalse(self.plan["guardrails"]["queue_completion_is_population_objective"])
        self.assertFalse(self.plan["guardrails"]["market_structure_gap_must_be_filled_next"])

    def test_exact_prestate_transform_mutates_only_analysis_review_and_evidence(self):
        ids = {row.get("analysis_id") for row in self.reviews.get("reviews", [])}
        if self.plan["new_analysis_id"] in ids:
            self.skipTest("exact AN transform comparison belongs to exact post-68 pre-state")
        before = apply_an.protected_hashes()
        new_reviews, new_evidence = apply_an.transform(
            self.plan,
            self.payload,
            self.canonical,
            self.sources,
            self.ledger,
            self.overlay,
            self.expectations,
            self.schema,
            self.reviews,
            self.evidence,
        )
        self.assertEqual(apply_an.protected_hashes(), before)
        self.assertEqual(len(new_reviews["reviews"]), len(self.reviews["reviews"]) + 1)
        self.assertEqual(len(new_evidence["evidence"]), len(self.evidence["evidence"]) + 8)
        self.assertEqual(new_reviews["version"], "0.12")
        self.assertEqual(new_evidence["version"], "0.12")


if __name__ == "__main__":
    unittest.main()
