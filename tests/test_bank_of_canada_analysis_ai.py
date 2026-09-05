from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from scripts.apply_bank_of_canada_analysis_ai import exact_timestamp_series_rows, transform
from src.world_signals.analysis import analysis_population_readiness, validate_analysis

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class BankOfCanadaAnalysisAITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load("data/analysis/BANK_OF_CANADA_ANALYSIS_AI_PLAN_v0.1.json")
        cls.payload = load("data/analysis/BANK_OF_CANADA_ANALYSIS_AI_PAYLOAD_v0.1.json")
        cls.canonical = load("data/canonical/registry.json")
        cls.sources = load("data/sources/registry.json")
        cls.ledger = load("data/changes/ledger.json")
        cls.overlay = load("data/coverage/biosecurity_overlay.json")
        cls.schema = load("data/analysis/schema.json")
        cls.reviews = load("data/analysis/event_reviews.json")
        cls.evidence = load("data/analysis/evidence_registry.json")
        cls.review = cls.payload["reviews"][0]
        cls.target = next(r for r in cls.canonical["records"] if r.get("occurrence_id") == "WSO-ddb70f8ff05a58fb")

    def test_plan_is_exact_post_63_and_selects_north_america_pressure(self):
        self.assertEqual(self.plan["base_main_sha"], "b12058d260a8139c893feb52ad864258044e83b2")
        pre = self.plan["preconditions"]
        self.assertEqual((pre["canonical_registry_version"], pre["canonical_record_count"]), ("0.37", 687))
        self.assertEqual((pre["analysis_reviews_version"], pre["analysis_review_count"]), ("0.8", 12))
        self.assertEqual(self.plan["selection"]["selected_occurrence_id"], "WSO-ddb70f8ff05a58fb")
        self.assertFalse(self.plan["guardrails"]["queue_completion_is_population_objective"])
        self.assertFalse(self.plan["guardrails"]["market_structure_gap_must_be_filled_next"])

    def test_target_preserves_exact_canonical_time_without_granting_market_precision(self):
        self.assertEqual(self.target["start_local"], "2026-09-02T09:45:00")
        self.assertEqual(self.target["source_timezone"], "America/Toronto")
        self.assertEqual(self.target["start_utc"], "2026-09-02T13:45:00Z")
        self.assertEqual(self.target["time_precision"], "MINUTE")
        self.assertEqual(self.review["canonical_release_utc"], self.target["start_utc"])
        self.assertFalse(self.plan["guardrails"]["exact_canonical_timestamp_implies_exact_market_series"])

    def test_headline_hold_and_guidance_surprise_are_separate(self):
        surprise = self.review["what_surprised"]
        self.assertEqual(surprise["status"], "MIXED")
        by_metric = {row["metric"]: row for row in surprise["comparisons"]}
        rate = by_metric["overnight_rate_target"]
        self.assertEqual((rate["actual"], rate["expected"], rate["difference_percentage_points"]), (2.25, 2.25, 0.0))
        self.assertEqual(rate["direction"], "MATCHED_EXPECTATION")
        self.assertEqual(by_metric["policy_path_and_guidance"]["direction"], "HAWKISHER_THAN_EXPECTED")
        self.assertFalse(self.plan["guardrails"]["headline_hold_equals_guidance_surprise"])

    def test_reuters_poll_is_explicit_consensus_and_path_benchmark(self):
        benchmarks = {row["metric"]: row for row in self.review["what_was_expected"]["benchmarks"]}
        self.assertEqual(benchmarks["overnight_rate_target"]["benchmark_type"], "MARKET_CONSENSUS_DECISION")
        self.assertEqual(benchmarks["overnight_rate_target"]["value"], 2.25)
        self.assertEqual(benchmarks["median_policy_path"]["benchmark_type"], "MARKET_FORECAST")
        self.assertIn("2027 Q3", benchmarks["median_policy_path"]["value"])

    def test_market_observations_refuse_exact_timestamp_series(self):
        moves = {row["movement_type"]: row for row in self.review["what_moved"]}
        fx = moves["FX_SPOT"]
        self.assertEqual(fx["movement_representation"], "CHANGE_AND_ENDPOINT")
        self.assertEqual(fx["measurement_precision"], "SOURCE_REPORTED_CHANGE_AND_ENDPOINT")
        self.assertFalse(fx["independently_reconstructed"])
        self.assertIsNone(fx["before_value"])
        self.assertEqual((fx["after_value"], fx["change"]), (1.384, 0.4))
        self.assertIn("not an independently reconstructed 09:45 event window", fx["measurement_window"])
        path = moves["POLICY_PROBABILITY_REPRICING"]
        self.assertEqual(path["movement_representation"], "QUALITATIVE_ONLY")
        self.assertEqual(path["measurement_precision"], "QUALITATIVE_ONLY")
        self.assertFalse(path["independently_reconstructed"])
        self.assertTrue(all(row["measurement_precision"] != "EXACT_TIMESTAMP_SERIES" for row in self.review["what_moved"]))

    def test_observed_association_keeps_alternative_explanations(self):
        connection = self.review["what_appears_connected"]
        self.assertEqual(connection["interaction_type"], "OBSERVATION_CONTEXT")
        self.assertEqual(connection["causal_status"], "OBSERVED_ASSOCIATION")
        self.assertEqual(connection["confidence"], "MEDIUM")
        self.assertGreaterEqual(len(self.review["alternative_explanations"]), 3)
        alternatives = " ".join(row["summary"] for row in self.review["alternative_explanations"]).lower()
        self.assertIn("global bond", alternatives)
        self.assertIn("energy", alternatives)
        self.assertFalse(self.plan["guardrails"]["source_reported_market_repricing_is_causal_estimate"])

    def test_tsx_is_explicitly_excluded_as_clean_boc_reaction(self):
        noise = " ".join(row["summary"] for row in self.review["what_may_be_noise"]).lower()
        self.assertIn("s&p/tsx", noise)
        self.assertIn("sector", noise)
        self.assertFalse(self.plan["guardrails"]["same_day_tsx_move_is_clean_boc_reaction"])

    def test_evidence_is_analysis_only_and_exactly_six_rows(self):
        payload_ids = {row["evidence_id"] for row in self.payload["evidence"]}
        self.assertEqual(payload_ids, set(self.plan["new_evidence_ids"]))
        self.assertEqual(len(payload_ids), 6)
        for row in self.payload["evidence"]:
            self.assertEqual(row["canonical_provenance_effect"], "NONE")
        classes = {row["evidence_class"] for row in self.payload["evidence"]}
        self.assertEqual(classes, {"PRIMARY_OFFICIAL", "REPUTABLE_NEWSWIRE"})

    def test_exact_prestate_transform_mutates_only_analysis_review_and_evidence(self):
        if any(row.get("analysis_id") == self.plan["new_analysis_id"] for row in self.reviews.get("reviews", [])):
            self.skipTest("exact transform comparison belongs to AI pre-state simulation")
        canonical_before = copy.deepcopy(self.canonical)
        sources_before = copy.deepcopy(self.sources)
        ledger_before = copy.deepcopy(self.ledger)
        overlay_before = copy.deepcopy(self.overlay)
        schema_before = copy.deepcopy(self.schema)
        new_reviews, new_evidence, readiness, _ = transform(
            self.plan, self.payload, self.canonical, self.sources, self.ledger,
            self.overlay, self.schema, self.reviews, self.evidence
        )
        self.assertEqual(self.canonical, canonical_before)
        self.assertEqual(self.sources, sources_before)
        self.assertEqual(self.ledger, ledger_before)
        self.assertEqual(self.overlay, overlay_before)
        self.assertEqual(self.schema, schema_before)
        self.assertEqual((new_reviews["version"], len(new_reviews["reviews"])), ("0.9", 13))
        self.assertEqual((new_evidence["version"], len(new_evidence["evidence"])), ("0.9", 50))
        self.assertEqual(readiness["reviewed_by_region"].get("North America"), 1)
        self.assertEqual(exact_timestamp_series_rows(new_reviews), 0)

    def test_live_or_simulated_poststate_validates_and_closes_reviewed_region_gap(self):
        if any(row.get("analysis_id") == self.plan["new_analysis_id"] for row in self.reviews.get("reviews", [])):
            reviews, evidence = self.reviews, self.evidence
        else:
            reviews, evidence, _readiness, _projection = transform(
                self.plan, self.payload, self.canonical, self.sources, self.ledger,
                self.overlay, self.schema, self.reviews, self.evidence
            )
        validation = validate_analysis(self.schema, evidence, reviews, self.canonical)
        self.assertTrue(validation.ok, validation.errors)
        readiness = analysis_population_readiness(self.schema, reviews, self.canonical)
        self.assertEqual(readiness["eligible_completed_occurrence_count"], 20)
        self.assertEqual(readiness["reviewed_occurrence_count"], 13)
        self.assertEqual(readiness["reviewed_by_region"].get("North America"), 1)
        self.assertEqual(exact_timestamp_series_rows(reviews), 0)

    def test_remaining_frontier_is_not_treated_as_fifo(self):
        expected = set(self.plan["postconditions"]["remaining_eligible_unreviewed_occurrence_ids"])
        self.assertEqual(len(expected), 7)
        self.assertIn("WSO-FIN-B-0004", expected)
        self.assertIn("WSO-CLIM-UNFCCC-SB64-202606", expected)
        self.assertNotIn("WSO-ddb70f8ff05a58fb", expected)
        self.assertFalse(self.plan["guardrails"]["queue_completion_is_population_objective"])

    def test_second_order_is_watch_item_not_realised_effect(self):
        second = self.review["second_order_effects"]
        self.assertEqual(second["status"], "PLAUSIBLE_WATCH_ITEM")
        self.assertIn("not observed consequences", second["summary"])


if __name__ == "__main__":
    unittest.main()
