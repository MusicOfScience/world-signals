from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from world_signals.analysis import analysis_population_readiness, validate_analysis
import apply_controlled_analysis_expansion_t as txn


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class ControlledAnalysisExpansionTTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load("data/analysis/CONTROLLED_ANALYSIS_EXPANSION_T_PLAN_v0.1.json")
        cls.payload = load("data/analysis/CONTROLLED_ANALYSIS_EXPANSION_T_PAYLOAD_v0.1.json")
        cls.schema = load("data/analysis/schema.json")
        cls.reviews = load("data/analysis/event_reviews.json")
        cls.evidence = load("data/analysis/evidence_registry.json")
        cls.canonical = load("data/canonical/registry.json")
        cls.sources = load("data/sources/registry.json")
        cls.by_occurrence = {row["occurrence_id"]: row for row in cls.canonical["records"]}
        cls.by_analysis = {row["analysis_id"]: row for row in cls.reviews["reviews"]}
        cls.by_evidence = {row["evidence_id"]: row for row in cls.evidence["evidence"]}
        cls.is_post = (
            cls.reviews.get("version") == "0.4"
            and len(cls.reviews.get("reviews", [])) == 8
            and cls.evidence.get("version") == "0.4"
            and len(cls.evidence.get("evidence", [])) == 21
        )

    def require_post(self):
        if not self.is_post:
            self.skipTest("exact T post-state assertions run after reviewed T transaction")

    def test_check_only_transform_is_exact_from_frozen_pre_state(self):
        if self.is_post:
            self.skipTest("check-only transform is exercised only from exact T pre-state")
        new_reviews, new_evidence, readiness = txn.transform(
            self.plan,
            self.payload,
            self.canonical,
            self.schema,
            self.reviews,
            self.evidence,
        )
        self.assertEqual((new_reviews["version"], len(new_reviews["reviews"])), ("0.4", 8))
        self.assertEqual((new_evidence["version"], len(new_evidence["evidence"])), ("0.4", 21))
        self.assertEqual(readiness["reviewed_occurrence_count"], 8)
        self.assertEqual(readiness["reviewed_event_type_diversity"], 7)
        self.assertEqual(readiness["broad_population_state"], "READY_FOR_CONTROLLED_EXPANSION")

    def test_exact_t_post_state_and_validator(self):
        self.require_post()
        self.assertEqual((self.canonical["version"], len(self.canonical["records"])), ("0.29", 678))
        self.assertEqual((self.reviews["version"], len(self.reviews["reviews"])), ("0.4", 8))
        self.assertEqual(self.reviews["canonical_checkpoint"], {"registry_version": "0.29", "record_count": 678})
        self.assertEqual((self.evidence["version"], len(self.evidence["evidence"])), ("0.4", 21))
        report = validate_analysis(self.schema, self.evidence, self.reviews, self.canonical)
        self.assertTrue(report.ok, report.errors)

    def test_selected_samples_bind_to_exact_completed_anchors(self):
        self.require_post()
        expected = {
            "WSAN-EIA-WPSR-20260902-001": ("WSO-COM-A-0013", "Cross-regional / Global", "INFORMATION_RELEASE"),
            "WSAN-EU-CHIPS-EVAL-20260603-001": ("WSO-TECH-A-0002", "Europe", "TECHNOLOGY_POLICY_MILESTONE"),
        }
        for analysis_id, (occurrence_id, region, event_type) in expected.items():
            review = self.by_analysis[analysis_id]
            row = self.by_occurrence[occurrence_id]
            self.assertEqual(review["canonical_occurrence_id"], occurrence_id)
            self.assertEqual((row["region"], row["event_type"], row["lifecycle_status"]), (region, event_type, "COMPLETED"))
            self.assertEqual(review["canonical_event_type"], event_type)
            self.assertEqual(review["canonical_release_utc"], row.get("start_utc"))
            self.assertTrue(review["canonical_mutation_prohibited"])
            self.assertFalse(review["google_calendar_write"])

    def test_eia_mixed_surprise_and_market_observation_preserve_contamination(self):
        self.require_post()
        review = self.by_analysis["WSAN-EIA-WPSR-20260902-001"]
        self.assertEqual(review["what_surprised"]["status"], "MIXED")
        comparisons = {row["metric"]: row for row in review["what_surprised"]["comparisons"]}
        self.assertEqual((comparisons["commercial_crude_stock_change"]["actual"], comparisons["commercial_crude_stock_change"]["expected"]), (-4.45, -1.1))
        self.assertEqual((comparisons["distillate_stock_change"]["actual"], comparisons["distillate_stock_change"]["expected"]), (0.796, -1.3))
        self.assertEqual(len(review["what_moved"]), 2)
        for move in review["what_moved"]:
            self.assertEqual(move["movement_type"], "COMMODITY_PRICE")
            self.assertEqual(move["movement_representation"], "CHANGE_AND_ENDPOINT")
            self.assertEqual(move["measurement_precision"], "SOURCE_REPORTED_CHANGE_AND_ENDPOINT")
            self.assertIsNone(move["before_value"])
            self.assertFalse(move["independently_reconstructed"])
        connection = review["what_appears_connected"]
        self.assertEqual((connection["causal_status"], connection["confidence"]), ("OBSERVED_ASSOCIATION", "LOW"))
        evidence_refs = set()
        for row in review["what_may_be_noise"] + review["alternative_explanations"]:
            evidence_refs.update(row["evidence_refs"])
        self.assertIn("WSEV-EIA-OIL-REUTERS-20260901", evidence_refs)

    def test_eu_deadline_completion_and_indicative_window_remain_distinct(self):
        self.require_post()
        row = self.by_occurrence["WSO-TECH-A-0002"]
        self.assertEqual(row["start_local"], "2026-09-20")
        self.assertIsNone(row["start_utc"])
        self.assertEqual(row["completion_verified_by_date"], "2026-06-03")
        self.assertEqual(row["deadline_completion_relation"], "COMPLETED_BEFORE_DEADLINE")
        self.assertFalse(row["deadline_is_actual_publication_time"])
        review = self.by_analysis["WSAN-EU-CHIPS-EVAL-20260603-001"]
        self.assertIsNone(review["canonical_release_utc"])
        benchmarks = {row["metric"]: row for row in review["what_was_expected"]["benchmarks"]}
        self.assertEqual(benchmarks["statutory_submission_deadline"]["value"], "2026-09-20")
        self.assertEqual(benchmarks["statutory_submission_deadline"]["benchmark_type"], "OTHER_DEFENSIBLE_EXPECTATION")
        self.assertEqual(benchmarks["indicative_adoption_window"]["value"], "Q1 2026")
        self.assertEqual(benchmarks["indicative_adoption_window"]["benchmark_type"], "OFFICIAL_PRIOR_GUIDANCE")
        self.assertEqual(review["what_surprised"]["status"], "MIXED")

    def test_eu_high_importance_does_not_require_market_move_or_causal_story(self):
        self.require_post()
        row = self.by_occurrence["WSO-TECH-A-0002"]
        review = self.by_analysis["WSAN-EU-CHIPS-EVAL-20260603-001"]
        self.assertEqual(row["intrinsic_importance"], "HIGH")
        self.assertEqual(review["what_moved"], [])
        connection = review["what_appears_connected"]
        self.assertEqual(connection["interaction_type"], "POLICY_RESPONSE_CONTEXT")
        self.assertEqual(connection["causal_status"], "NOT_A_CAUSAL_CLAIM")
        self.assertEqual(connection["confidence"], "HIGH")
        self.assertEqual(review["second_order_effects"]["status"], "NOT_ESTABLISHED")

    def test_boc_remains_deliberately_eligible_unreviewed(self):
        self.require_post()
        boc = self.by_occurrence["WSO-ddb70f8ff05a58fb"]
        self.assertEqual((boc["event_type"], boc["lifecycle_status"]), ("DECISION", "COMPLETED"))
        reviewed_occurrences = {row["canonical_occurrence_id"] for row in self.reviews["reviews"]}
        self.assertNotIn(boc["occurrence_id"], reviewed_occurrences)
        self.assertEqual(self.plan["hold_occurrence_ids"], [boc["occurrence_id"]])
        self.assertFalse(self.plan["guardrails"]["backlog_completion_is_population_objective"])

    def test_evidence_is_analysis_only_and_exactly_seven_new_records(self):
        self.require_post()
        expected = set(self.plan["new_evidence_ids"])
        self.assertEqual(len(expected), 7)
        self.assertTrue(expected <= set(self.by_evidence))
        canonical_source_ids = {row.get("source_id") for row in self.canonical["records"]}
        self.assertTrue(expected.isdisjoint(canonical_source_ids))
        for evidence_id in expected:
            self.assertEqual(self.by_evidence[evidence_id]["canonical_provenance_effect"], "NONE")

    def test_t_readiness_expands_domain_diversity_without_claiming_completeness(self):
        self.require_post()
        readiness = analysis_population_readiness(self.schema, self.reviews, self.canonical)
        self.assertEqual(readiness["eligible_completed_occurrence_count"], 9)
        self.assertEqual(readiness["reviewed_occurrence_count"], 8)
        self.assertEqual(readiness["reviewed_event_type_diversity"], 7)
        self.assertEqual(readiness["broad_population_state"], "READY_FOR_CONTROLLED_EXPANSION")
        remaining = sorted(
            row["occurrence_id"] for row in self.canonical["records"]
            if row.get("lifecycle_status") == "COMPLETED"
            and row["occurrence_id"] not in set(readiness["reviewed_occurrence_ids"])
        )
        self.assertEqual(remaining, ["WSO-ddb70f8ff05a58fb"])
        self.assertIn("not a claim of analytical completeness", " ".join(readiness["notes"]).lower())

    def test_all_t_write_gates_remain_closed(self):
        for value in self.plan["guardrails"].values():
            self.assertFalse(value)
        self.assertFalse(self.schema["layer_boundary"]["canonical_mutation_allowed"])
        self.assertFalse(self.schema["layer_boundary"]["calendar_mutation_allowed"])
        self.assertFalse(self.schema["layer_boundary"]["monitor_configuration_mutation_allowed"])


if __name__ == "__main__":
    unittest.main()
