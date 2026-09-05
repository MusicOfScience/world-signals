from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_analysis_sample_y import audit, markdown, BASE_MAIN_SHA

FROZEN_AUDIT_PATH = ROOT / "data/analysis/ANALYSIS_SAMPLE_AUDIT_Y_v0.1.json"


class AnalysisSampleAuditYTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frozen = json.loads(FROZEN_AUDIT_PATH.read_text(encoding="utf-8"))
        cls.live = audit()

    def test_frozen_y_checkpoint_is_exactly_post_x(self):
        checkpoint = self.frozen["checkpoint"]
        self.assertEqual(BASE_MAIN_SHA, "f05b9623f973aed84a420354d273e039a4b61f8e")
        self.assertEqual(self.frozen["base_main_sha"], BASE_MAIN_SHA)
        self.assertEqual((checkpoint["canonical_registry_version"], checkpoint["canonical_record_count"]), ("0.30", 681))
        self.assertEqual(checkpoint["analysis_schema_version"], "0.3")
        self.assertEqual((checkpoint["analysis_reviews_version"], checkpoint["analysis_review_count"]), ("0.7", 11))
        self.assertEqual((checkpoint["analysis_evidence_version"], checkpoint["analysis_evidence_count"]), ("0.7", 40))
        self.assertTrue(checkpoint["analysis_validation_ok"])

    def test_audit_is_read_only_in_frozen_and_live_views(self):
        for report in (self.frozen, self.live):
            policy = report["mutation_policy"]
            self.assertTrue(policy)
            self.assertTrue(all(value is False for value in policy.values()))

    def test_y_historical_frontier_is_frozen_without_making_queue_completion_a_goal(self):
        frozen_frontier = self.frozen["eligible_unreviewed_frontier"]
        self.assertEqual([row["occurrence_id"] for row in frozen_frontier], ["WSO-ddb70f8ff05a58fb"])
        for report in (self.frozen, self.live):
            self.assertIn("QUEUE_COMPLETION_IS_NOT_THE_OBJECTIVE", {row["finding"] for row in report["findings"]})
            self.assertIn("not quotas", report["next_stage"]["anti_quota_note"])

        # Y freezes the historical frontier at its own checkpoint. A descendant
        # Analysis tranche may legitimately review a frozen frontier member, in
        # which case it must leave the live frontier and appear in reviewed IDs.
        boc_id = "WSO-ddb70f8ff05a58fb"
        live_frontier_ids = {row["occurrence_id"] for row in self.live["eligible_unreviewed_frontier"]}
        live_reviewed_ids = set(self.live["readiness"]["reviewed_occurrence_ids"])
        self.assertIn(boc_id, live_frontier_ids | live_reviewed_ids)
        self.assertFalse(boc_id in live_frontier_ids and boc_id in live_reviewed_ids)

    def test_readiness_gate_is_minimum_not_representativeness_claim(self):
        frozen = self.frozen["readiness"]
        self.assertEqual(frozen["eligible_completed_occurrence_count"], 12)
        self.assertEqual(frozen["reviewed_occurrence_count"], 11)
        self.assertEqual(frozen["reviewed_event_type_diversity"], 10)
        self.assertEqual(frozen["broad_population_state"], "READY_FOR_CONTROLLED_EXPANSION")
        self.assertIn("CONTROLLED_EXPANSION_GATE_IS_NOT_REPRESENTATIVE_COVERAGE", {row["finding"] for row in self.frozen["findings"]})

        live = self.live["readiness"]
        self.assertGreaterEqual(live["eligible_completed_occurrence_count"], frozen["eligible_completed_occurrence_count"])
        self.assertGreaterEqual(live["reviewed_occurrence_count"], frozen["reviewed_occurrence_count"])
        self.assertGreaterEqual(live["reviewed_event_type_diversity"], frozen["reviewed_event_type_diversity"])
        self.assertEqual(live["broad_population_state"], "READY_FOR_CONTROLLED_EXPANSION")
        self.assertIn("CONTROLLED_EXPANSION_GATE_IS_NOT_REPRESENTATIVE_COVERAGE", {row["finding"] for row in self.live["findings"]})

    def test_y_historically_identified_east_asia_gap_but_descendants_may_repair_it(self):
        frozen_gaps = self.frozen["upstream_population_gaps"]
        self.assertIn("East Asia", frozen_gaps["regions_present_in_registry_but_absent_from_completed_anchors"])
        self.assertIn("UPSTREAM_COMPLETED_ANCHOR_REGION_GAPS", {row["finding"] for row in self.frozen["findings"]})

        live_gaps = self.live["upstream_population_gaps"]["regions_present_in_registry_but_absent_from_completed_anchors"]
        if self.live["checkpoint"]["canonical_registry_version"] == "0.30":
            self.assertIn("East Asia", live_gaps)
        else:
            # A descendant transaction may legitimately repair the gap Y discovered.
            self.assertIsInstance(live_gaps, list)

    def test_market_precision_is_measured_not_assumed(self):
        for report in (self.frozen, self.live):
            semantics = report["analysis_semantics"]
            self.assertGreater(semantics["total_market_movement_rows"], 0)
            self.assertEqual(semantics["exact_timestamp_series_rows"], 0)
            self.assertIn("MARKET_MEASUREMENT_PRECISION_GAP", {row["finding"] for row in report["findings"]})

    def test_every_review_keeps_falsifiers(self):
        self.assertGreaterEqual(self.live["analysis_semantics"]["minimum_falsifier_count_per_review"], 1)

    def test_evidence_refs_are_resolved(self):
        evidence = self.live["evidence_profile"]
        self.assertEqual(evidence["missing_evidence_refs"], [])
        self.assertGreater(evidence["referenced_evidence_count"], 0)
        self.assertGreater(evidence["primary_official_share_percent"], 0)

    def test_frozen_markdown_preserves_y_methodological_warnings(self):
        text = markdown(self.frozen)
        self.assertIn("sample population → audit", text)
        self.assertIn("**not** evidence of representative global coverage", text)
        self.assertIn("Finishing this list is **not** the objective", text)
        self.assertIn("EXACT_TIMESTAMP_SERIES", text)
        self.assertIn("controlled expansion with upstream gap repair", text)


if __name__ == "__main__":
    unittest.main()
