from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import apply_japan_sovereign_financing_analysis_aa as txn
from world_signals.analysis import analysis_population_readiness, public_analysis_projection, validate_analysis


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class JapanSovereignFinancingAnalysisAATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load("data/analysis/JAPAN_SOVEREIGN_FINANCING_ANALYSIS_AA_PLAN_v0.1.json")
        cls.payload = load("data/analysis/JAPAN_SOVEREIGN_FINANCING_ANALYSIS_AA_PAYLOAD_v0.1.json")
        cls.canonical = load("data/canonical/registry.json")
        cls.sources = load("data/sources/registry.json")
        cls.ledger = load("data/changes/ledger.json")
        cls.overlay = load("data/coverage/biosecurity_overlay.json")
        cls.schema = load("data/analysis/schema.json")
        cls.reviews = load("data/analysis/event_reviews.json")
        cls.evidence = load("data/analysis/evidence_registry.json")
        cls.has_aa = any(row.get("analysis_id") == cls.plan["new_analysis_id"] for row in cls.reviews.get("reviews", []))

    def live_or_simulated(self):
        if self.has_aa:
            readiness = analysis_population_readiness(self.schema, self.reviews, self.canonical)
            projection = public_analysis_projection(self.schema, self.evidence, self.reviews, self.canonical)
            return self.reviews, self.evidence, readiness, projection
        return txn.transform(
            self.plan, self.payload, self.canonical, self.sources, self.ledger,
            self.overlay, self.schema, self.reviews, self.evidence,
        )

    def test_frozen_aa_boundary_and_no_schema_change(self):
        pre = self.plan["preconditions"]
        post = self.plan["postconditions"]
        self.assertEqual(pre["canonical_registry_version"], "0.31")
        self.assertEqual(pre["canonical_record_count"], 681)
        self.assertEqual((pre["analysis_reviews_version"], pre["analysis_review_count"]), ("0.7", 11))
        self.assertEqual((pre["analysis_evidence_version"], pre["analysis_evidence_count"]), ("0.7", 40))
        self.assertEqual((post["analysis_reviews_version"], post["analysis_review_count"]), ("0.8", 12))
        self.assertEqual((post["analysis_evidence_version"], post["analysis_evidence_count"]), ("0.8", 44))
        self.assertEqual(self.schema["version"], "0.3")
        self.assertEqual(self.plan["schema_decision"]["version_unchanged"], "0.3")
        for key in (
            "canonical_mutation", "source_registry_mutation", "change_ledger_mutation",
            "biosecurity_overlay_mutation", "analysis_schema_mutation", "monitor_configuration_mutation",
            "calendar_write", "automatic_canonical_commit",
        ):
            self.assertFalse(self.plan["guardrails"][key])

    def test_payload_separates_auction_mechanics_from_secondary_market(self):
        review = self.payload["reviews"][0]
        actuals = {row["metric"]: row["value"] for row in review["what_happened"]["actuals"]}
        self.assertEqual(actuals["weighted_average_yield"], 4.079)
        self.assertEqual(actuals["lowest_accepted_yield"], 4.1)
        self.assertEqual(actuals["bid_to_cover_ratio"], 3.79)
        self.assertEqual(actuals["auction_tail"], 0.28)
        noise = " ".join(row["summary"] for row in review["what_may_be_noise"])
        self.assertIn("auction-clearing metrics", noise)
        self.assertIn("secondary-market", noise)
        self.assertFalse(self.plan["guardrails"]["auction_clearing_yield_is_secondary_market_move"])

    def test_no_clear_surprise_does_not_promote_previous_auction_to_consensus(self):
        review = self.payload["reviews"][0]
        self.assertEqual(review["what_surprised"]["status"], "NO_CLEAR_SURPRISE")
        comparison = review["what_surprised"]["comparisons"][0]
        self.assertEqual(comparison["comparison_kind"], "QUALITATIVE")
        self.assertIn("3.79 versus 3.86", comparison["actual"])
        self.assertIn("largely uneventful as expected", comparison["expected"])
        self.assertFalse(self.plan["guardrails"]["previous_auction_is_market_consensus"])

    def test_same_session_yield_move_is_recorded_without_auction_causality(self):
        review = self.payload["reviews"][0]
        move = review["what_moved"][0]
        self.assertEqual(move["movement_type"], "SOVEREIGN_YIELD")
        self.assertEqual(move["movement_representation"], "CHANGE_AND_ENDPOINT")
        self.assertEqual(move["measurement_precision"], "SOURCE_REPORTED_CHANGE_AND_ENDPOINT")
        self.assertEqual((move["after_value"], move["change"]), (4.07, -9.5))
        self.assertIsNone(move["before_value"])
        self.assertFalse(move["independently_reconstructed"])
        self.assertIn("unchanged after the auction", move["measurement_window"])
        connection = review["what_appears_connected"]
        self.assertEqual(connection["interaction_type"], "OBSERVATION_CONTEXT")
        self.assertEqual(connection["causal_status"], "NOT_A_CAUSAL_CLAIM")
        self.assertIn("unchanged after the auction", connection["summary"])
        self.assertFalse(self.plan["guardrails"]["same_session_yield_move_is_auction_causality"])

    def test_aa_preserves_unresolved_canonical_clock_time(self):
        target = next(row for row in self.canonical["records"] if row.get("occurrence_id") == "WSO-FIS-A-0015")
        self.assertEqual(target["start_local"], "2026-09-03")
        self.assertEqual(target["source_timezone"], "Asia/Tokyo")
        self.assertIsNone(target.get("start_utc"))
        self.assertIsNone(self.payload["reviews"][0]["canonical_release_utc"])
        self.assertFalse(self.plan["guardrails"]["exact_timestamp_precision_without_independent_series"])

    def test_second_order_channel_is_watch_item_not_one_auction_effect(self):
        second = self.payload["reviews"][0]["second_order_effects"]
        self.assertEqual(second["status"], "PLAUSIBLE_WATCH_ITEM")
        self.assertIn("does not attribute", second["summary"])
        self.assertFalse(self.plan["guardrails"]["one_auction_establishes_capital_repatriation"])

    def test_transform_or_live_descendant_preserves_aa_contract(self):
        reviews, evidence, readiness, projection = self.live_or_simulated()
        post = self.plan["postconditions"]
        self.assertGreaterEqual(len(reviews["reviews"]), post["analysis_review_count"])
        self.assertGreaterEqual(len(evidence["evidence"]), post["analysis_evidence_count"])
        self.assertGreaterEqual(readiness["eligible_completed_occurrence_count"], post["eligible_completed_occurrence_count"])
        self.assertGreaterEqual(readiness["reviewed_occurrence_count"], post["reviewed_occurrence_count"])
        self.assertGreaterEqual(readiness["reviewed_event_type_diversity"], post["reviewed_event_type_diversity"])
        self.assertGreaterEqual(readiness["reviewed_by_region"].get("East Asia", 0), 1)
        self.assertEqual(readiness["broad_population_state"], "READY_FOR_CONTROLLED_EXPANSION")
        by_id = {row["analysis_id"]: row for row in projection["reviews"]}
        projected = by_id["WSAN-JP-JGB30-20260903-001"]
        self.assertEqual(projected["canonical"]["event_type"], "FISCAL_FINANCING_EVENT")
        self.assertEqual(projected["canonical"]["category"], "FISCAL_SOVEREIGN_FINANCE")
        self.assertIsNone(projected["canonical"]["start_utc"])
        self.assertEqual(projected["what_surprised"]["status"], "NO_CLEAR_SURPRISE")
        self.assertEqual(projected["what_appears_connected"]["causal_status"], "NOT_A_CAUSAL_CLAIM")
        self.assertTrue(validate_analysis(self.schema, evidence, reviews, self.canonical).ok)

    def test_aa_historical_frontier_is_frozen_without_fifo_goal(self):
        self.assertEqual(
            self.plan["postconditions"]["remaining_eligible_unreviewed_occurrence_ids"],
            ["WSO-MAC-B-0041", "WSO-ddb70f8ff05a58fb"],
        )
        self.assertEqual(
            set(self.plan["selection"]["held_occurrence_ids"]),
            {"WSO-MAC-B-0041", "WSO-ddb70f8ff05a58fb"},
        )
        self.assertFalse(self.plan["guardrails"]["queue_completion_is_population_objective"])

    def test_aa_evidence_is_analysis_only_and_exact(self):
        rows = self.payload["evidence"]
        self.assertEqual({row["evidence_id"] for row in rows}, set(self.plan["new_evidence_ids"]))
        self.assertTrue(all(row["canonical_provenance_effect"] == "NONE" for row in rows))
        by_id = {row["evidence_id"]: row for row in rows}
        self.assertIn("OFFICIAL_OUTCOME", by_id["WSEV-JP-JGB30-MOF-RESULT-20260903"]["roles"])
        self.assertIn("MARKET_OBSERVATION", by_id["WSEV-JP-JGB30-REUTERS-REACTION-20260903"]["roles"])
        self.assertIn("SECOND_ORDER_OBSERVATION", by_id["WSEV-JP-JGB-REUTERS-CAPITAL-FLOWS-20260902"]["roles"])

    def test_aa_script_protects_upstream_and_schema(self):
        source = (ROOT / "scripts/apply_japan_sovereign_financing_analysis_aa.py").read_text(encoding="utf-8")
        self.assertIn('"Analysis schema": ANALYSIS_SCHEMA_PATH', source)
        self.assertIn("before == after", source)
        for forbidden in (
            "write(ANALYSIS_SCHEMA_PATH", "write(CANONICAL_PATH", "write(SOURCES_PATH",
            "write(LEDGER_PATH", "write(OVERLAY_PATH",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
