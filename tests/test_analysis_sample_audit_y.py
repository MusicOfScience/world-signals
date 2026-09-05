from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_analysis_sample_y import audit, markdown, BASE_MAIN_SHA


class AnalysisSampleAuditYTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = audit()

    def test_exact_checkpoint_is_post_x(self):
        checkpoint = self.report["checkpoint"]
        self.assertEqual(BASE_MAIN_SHA, "f05b9623f973aed84a420354d273e039a4b61f8e")
        self.assertEqual((checkpoint["canonical_registry_version"], checkpoint["canonical_record_count"]), ("0.30", 681))
        self.assertEqual(checkpoint["analysis_schema_version"], "0.3")
        self.assertEqual((checkpoint["analysis_reviews_version"], checkpoint["analysis_review_count"]), ("0.7", 11))
        self.assertEqual((checkpoint["analysis_evidence_version"], checkpoint["analysis_evidence_count"]), ("0.7", 40))
        self.assertTrue(checkpoint["analysis_validation_ok"])

    def test_audit_is_read_only(self):
        policy = self.report["mutation_policy"]
        self.assertTrue(policy)
        self.assertTrue(all(value is False for value in policy.values()))

    def test_current_frontier_is_not_treated_as_queue_goal(self):
        frontier = self.report["eligible_unreviewed_frontier"]
        self.assertEqual([row["occurrence_id"] for row in frontier], ["WSO-ddb70f8ff05a58fb"])
        self.assertIn("QUEUE_COMPLETION_IS_NOT_THE_OBJECTIVE", {row["finding"] for row in self.report["findings"]})
        self.assertIn("not quotas", self.report["next_stage"]["anti_quota_note"])

    def test_readiness_gate_is_not_representativeness_claim(self):
        readiness = self.report["readiness"]
        self.assertEqual(readiness["eligible_completed_occurrence_count"], 12)
        self.assertEqual(readiness["reviewed_occurrence_count"], 11)
        self.assertEqual(readiness["reviewed_event_type_diversity"], 10)
        self.assertEqual(readiness["broad_population_state"], "READY_FOR_CONTROLLED_EXPANSION")
        self.assertIn("CONTROLLED_EXPANSION_GATE_IS_NOT_REPRESENTATIVE_COVERAGE", {row["finding"] for row in self.report["findings"]})

    def test_audit_identifies_upstream_completed_anchor_gaps(self):
        gaps = self.report["upstream_population_gaps"]
        self.assertTrue(gaps["regions_present_in_registry_but_absent_from_completed_anchors"])
        self.assertIn("UPSTREAM_COMPLETED_ANCHOR_REGION_GAPS", {row["finding"] for row in self.report["findings"]})

    def test_market_precision_is_measured_not_assumed(self):
        semantics = self.report["analysis_semantics"]
        self.assertGreater(semantics["total_market_movement_rows"], 0)
        self.assertEqual(semantics["exact_timestamp_series_rows"], 0)
        self.assertIn("MARKET_MEASUREMENT_PRECISION_GAP", {row["finding"] for row in self.report["findings"]})

    def test_every_review_keeps_falsifiers(self):
        self.assertGreaterEqual(self.report["analysis_semantics"]["minimum_falsifier_count_per_review"], 1)

    def test_evidence_refs_are_resolved(self):
        evidence = self.report["evidence_profile"]
        self.assertEqual(evidence["missing_evidence_refs"], [])
        self.assertGreater(evidence["referenced_evidence_count"], 0)
        self.assertGreater(evidence["primary_official_share_percent"], 0)

    def test_markdown_preserves_methodological_warnings(self):
        text = markdown(self.report)
        self.assertIn("sample population → audit", text)
        self.assertIn("not evidence of representative global coverage", text)
        self.assertIn("Finishing this list is **not** the objective", text)
        self.assertIn("EXACT_TIMESTAMP_SERIES", text)
        self.assertIn("controlled expansion with upstream gap repair", text)


if __name__ == "__main__":
    unittest.main()
