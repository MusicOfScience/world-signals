from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from world_signals.analysis import analysis_population_readiness, validate_analysis
import apply_institutional_analysis_w as txn


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def version_tuple(value):
    return tuple(int(part) for part in str(value).split("."))


class InstitutionalAnalysisWTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load("data/analysis/INSTITUTIONAL_ANALYSIS_W_PLAN_v0.1.json")
        cls.payload = load("data/analysis/INSTITUTIONAL_ANALYSIS_W_PAYLOAD_v0.1.json")
        cls.schema = load("data/analysis/schema.json")
        cls.reviews = load("data/analysis/event_reviews.json")
        cls.evidence = load("data/analysis/evidence_registry.json")
        cls.canonical = load("data/canonical/registry.json")
        cls.by_occurrence = {row["occurrence_id"]: row for row in cls.canonical["records"]}
        cls.is_post = (
            version_tuple(cls.reviews.get("version", "0.0")) >= (0, 6)
            and len(cls.reviews.get("reviews", [])) >= 11
            and version_tuple(cls.evidence.get("version", "0.0")) >= (0, 6)
            and len(cls.evidence.get("evidence", [])) >= 33
        )

    def simulated_or_live_post(self):
        if self.is_post:
            return self.reviews, self.evidence
        reviews, evidence, _ = txn.transform(
            self.plan, self.payload, self.canonical, self.schema, self.reviews, self.evidence
        )
        return reviews, evidence

    def test_check_only_transform_is_exact_from_frozen_pre_state(self):
        if self.is_post:
            self.skipTest("check-only transform is exercised only from exact W pre-state")
        reviews, evidence, readiness = txn.transform(
            self.plan, self.payload, self.canonical, self.schema, self.reviews, self.evidence
        )
        self.assertEqual((reviews["version"], len(reviews["reviews"])), ("0.6", 11))
        self.assertEqual((evidence["version"], len(evidence["evidence"])), ("0.6", 33))
        self.assertEqual(reviews["canonical_checkpoint"], {"registry_version": "0.30", "record_count": 681})
        self.assertEqual(readiness["eligible_completed_occurrence_count"], 12)
        self.assertEqual(readiness["reviewed_occurrence_count"], 11)
        self.assertEqual(readiness["reviewed_event_type_diversity"], 10)
        self.assertEqual(readiness["broad_population_state"], "READY_FOR_CONTROLLED_EXPANSION")

    def test_exact_w_post_state_and_validator(self):
        if not self.is_post:
            self.skipTest("exact W terminal-state assertion runs after reviewed apply")
        self.assertEqual((self.canonical["version"], len(self.canonical["records"])), ("0.30", 681))
        self.assertEqual((self.schema["version"]), "0.3")
        self.assertEqual((self.reviews["version"], len(self.reviews["reviews"])), ("0.6", 11))
        self.assertEqual((self.evidence["version"], len(self.evidence["evidence"])), ("0.6", 33))
        self.assertEqual(self.reviews["canonical_checkpoint"], {"registry_version": "0.30", "record_count": 681})
        report = validate_analysis(self.schema, self.evidence, self.reviews, self.canonical)
        self.assertTrue(report.ok, report.errors)

    def test_two_reviews_bind_to_exact_completed_anchors(self):
        reviews, _ = self.simulated_or_live_post()
        by_analysis = {row["analysis_id"]: row for row in reviews["reviews"]}
        expected = {
            "WSAN-BWC-WG8-20260213-001": ("WSO-BWC-WG-2026-S08", "TREATY_WORKING_GROUP_SESSION", "INTERNATIONAL_INSTITUTIONS"),
            "WSAN-WOAH-GS93-20260522-001": ("WSO-WOAH-GS-093", "GOVERNANCE_ASSEMBLY_SESSION", "AGRICULTURE_FOOD"),
        }
        for analysis_id, (occurrence_id, event_type, category) in expected.items():
            self.assertIn(analysis_id, by_analysis)
            review = by_analysis[analysis_id]
            row = self.by_occurrence[occurrence_id]
            self.assertEqual(review["canonical_occurrence_id"], occurrence_id)
            self.assertEqual((row["event_type"], row["category"], row["lifecycle_status"]), (event_type, category, "COMPLETED"))
            self.assertEqual(review["canonical_release_utc"], row.get("start_utc"))
            self.assertTrue(review["canonical_mutation_prohibited"])
            self.assertFalse(review["google_calendar_write"])

    def test_bwc_procedural_consensus_is_not_substantive_consensus(self):
        reviews, _ = self.simulated_or_live_post()
        review = {row["analysis_id"]: row for row in reviews["reviews"]}["WSAN-BWC-WG8-20260213-001"]
        self.assertEqual(review["what_surprised"]["status"], "NOT_ESTABLISHED")
        self.assertEqual(review["what_moved"], [])
        self.assertEqual(review["what_appears_connected"]["interaction_type"], "STRUCTURAL_DEPENDENCY")
        self.assertEqual(review["what_appears_connected"]["causal_status"], "NOT_A_CAUSAL_CLAIM")
        self.assertEqual(review["what_appears_connected"]["confidence"], "HIGH")
        self.assertEqual(review["second_order_effects"]["status"], "NOT_ESTABLISHED")
        noise = " ".join(item["summary"] for item in review["what_may_be_noise"]).lower()
        self.assertIn("procedural report", noise)
        self.assertIn("substantive", noise)
        self.assertIn("future discussions", noise)

    def test_woah_realised_output_is_not_synthetic_directional_surprise(self):
        reviews, _ = self.simulated_or_live_post()
        review = {row["analysis_id"]: row for row in reviews["reviews"]}["WSAN-WOAH-GS93-20260522-001"]
        actuals = {item["metric"]: item["value"] for item in review["what_happened"]["actuals"]}
        self.assertEqual(actuals["resolutions_adopted"], 35)
        self.assertEqual(actuals["international_standards_adopted_or_revised"], 51)
        self.assertEqual(review["what_surprised"]["status"], "NO_CLEAR_SURPRISE")
        self.assertEqual(review["what_moved"], [])
        self.assertEqual(review["second_order_effects"]["status"], "PLAUSIBLE_WATCH_ITEM")
        self.assertEqual(review["what_appears_connected"]["causal_status"], "NOT_A_CAUSAL_CLAIM")

    def test_woah_primary_category_survives_cross_domain_context(self):
        row = self.by_occurrence["WSO-WOAH-GS-093"]
        self.assertEqual(row["category"], "AGRICULTURE_FOOD")
        reviews, _ = self.simulated_or_live_post()
        review = {row["analysis_id"]: row for row in reviews["reviews"]}["WSAN-WOAH-GS93-20260522-001"]
        context = " ".join(item["summary"] for item in review["what_may_be_noise"]).lower()
        self.assertIn("one health", context)
        self.assertIn("biosecurity", context)
        self.assertIn("agriculture_food", context)

    def test_both_institutional_reviews_preserve_null_market_result(self):
        reviews, _ = self.simulated_or_live_post()
        by_analysis = {row["analysis_id"]: row for row in reviews["reviews"]}
        for analysis_id in self.plan["new_analysis_ids"]:
            self.assertEqual(by_analysis[analysis_id]["what_moved"], [])
        self.assertFalse(self.plan["guardrails"]["market_reaction_required_for_high_importance_institutional_event"])

    def test_new_evidence_is_analysis_only(self):
        _, evidence = self.simulated_or_live_post()
        by_evidence = {row["evidence_id"]: row for row in evidence["evidence"]}
        expected = set(self.plan["new_evidence_ids"])
        self.assertEqual(len(expected), 5)
        self.assertTrue(expected <= set(by_evidence))
        canonical_source_ids = {row.get("source_id") for row in self.canonical["records"]}
        self.assertTrue(expected.isdisjoint(canonical_source_ids))
        for evidence_id in expected:
            self.assertEqual(by_evidence[evidence_id]["canonical_provenance_effect"], "NONE")

    def test_w_readiness_leaves_only_boc_unreviewed(self):
        reviews, _ = self.simulated_or_live_post()
        readiness = analysis_population_readiness(self.schema, reviews, self.canonical)
        self.assertEqual(readiness["eligible_completed_occurrence_count"], 12)
        self.assertEqual(readiness["reviewed_occurrence_count"], 11)
        self.assertEqual(readiness["reviewed_event_type_diversity"], 10)
        self.assertEqual(readiness["broad_population_state"], "READY_FOR_CONTROLLED_EXPANSION")
        reviewed = set(readiness["reviewed_occurrence_ids"])
        remaining = sorted(row["occurrence_id"] for row in self.canonical["records"] if row.get("lifecycle_status") == "COMPLETED" and row["occurrence_id"] not in reviewed)
        self.assertEqual(remaining, ["WSO-ddb70f8ff05a58fb"])
        self.assertFalse(self.plan["guardrails"]["backlog_completion_is_population_objective"])

    def test_all_w_write_and_inference_gates_remain_closed(self):
        for value in self.plan["guardrails"].values():
            self.assertFalse(value)
        self.assertFalse(self.schema["layer_boundary"]["canonical_mutation_allowed"])
        self.assertFalse(self.schema["layer_boundary"]["calendar_mutation_allowed"])
        self.assertFalse(self.schema["layer_boundary"]["monitor_configuration_mutation_allowed"])


if __name__ == "__main__":
    unittest.main()
