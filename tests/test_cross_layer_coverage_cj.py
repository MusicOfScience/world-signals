from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.cross_layer_coverage import (
    LIVE_REGION_TO_CANONICAL_COMPARISON_REGION,
    build_cross_layer_coverage_audit,
)


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class CrossLayerCoverageUnitTests(unittest.TestCase):
    def setUp(self):
        self.registry = {
            "version": "test-canonical",
            "records": [
                {
                    "occurrence_id": "O1",
                    "series_id": "S1",
                    "region": "Region A",
                    "category": "CAT_A",
                    "institution": "Inst A",
                    "lifecycle_status": "COMPLETED",
                },
                {
                    "occurrence_id": "O2",
                    "series_id": "S2",
                    "region": "Region B",
                    "category": "CAT_B",
                    "institution": "Inst B",
                    "lifecycle_status": "PLANNED",
                },
                {
                    "occurrence_id": "O3",
                    "series_id": "S3",
                    "region": "Region B",
                    "category": "CAT_B",
                    "institution": "Inst C",
                    "lifecycle_status": "COMPLETED",
                },
            ],
        }
        self.expectations = {
            "version": "test-monitor",
            "adapters": [
                {"adapter_id": "A1", "canonical_occurrence_ids": ["O1", "O2"]}
            ],
        }
        self.live = {
            "version": "test-live",
            "observations": [
                {
                    "observation_id": "L1",
                    "regions": ["Region A"],
                    "domain_tags": ["DOMAIN_A"],
                    "canonical_links": [{"occurrence_id": "O1", "relationship": "OUTCOME_OF"}],
                },
                {
                    "observation_id": "L2",
                    "regions": ["Region B"],
                    "domain_tags": ["DOMAIN_B"],
                    "canonical_links": [{"occurrence_id": "O2", "relationship": "CONTEXT_FOR"}],
                },
                {
                    "observation_id": "L3",
                    "regions": ["Region C"],
                    "domain_tags": ["DOMAIN_A"],
                    "canonical_links": [],
                },
            ],
        }
        self.analysis = {
            "version": "test-analysis",
            "reviews": [
                {
                    "analysis_id": "AN1",
                    "canonical_occurrence_id": "O1",
                    "live_inputs": [
                        {
                            "observation_id": "L1",
                            "roles": ["FACTUAL_INPUT"],
                            "analysis_sections": ["what_happened"],
                        }
                    ],
                },
                {
                    "analysis_id": "AN2",
                    "canonical_occurrence_id": "O3",
                },
            ],
        }

    def test_layer_shape_is_kept_separate(self):
        audit = build_cross_layer_coverage_audit(
            self.registry, self.expectations, self.live, self.analysis
        )
        totals = audit["totals"]
        self.assertEqual(totals["canonical_occurrence_count"], 3)
        self.assertEqual(totals["canonical_unique_series_count"], 3)
        self.assertEqual(totals["configured_monitor_adapter_count"], 1)
        self.assertEqual(totals["configured_monitor_scoped_occurrence_count"], 2)
        self.assertEqual(totals["live_observation_count"], 3)
        self.assertEqual(totals["canonical_linked_live_observation_count"], 2)
        self.assertEqual(totals["analysis_review_count"], 2)
        self.assertEqual(totals["production_live_input_count"], 1)
        self.assertTrue(
            audit["methodology"]["canonical_categories_and_live_domain_tags_not_forced_into_one_taxonomy"]
        )
        self.assertTrue(audit["methodology"]["count_only_selection_prohibited"])
        self.assertTrue(audit["methodology"]["quota_filling_prohibited"])

    def test_bridge_frontier_distinguishes_used_pre_event_and_unlinked(self):
        audit = build_cross_layer_coverage_audit(
            self.registry, self.expectations, self.live, self.analysis
        )
        frontier = audit["bridge_frontier"]
        self.assertEqual(frontier["used_live_observation_ids"], ["L1"])
        self.assertEqual(frontier["factual_same_anchor_candidate_count"], 0)
        self.assertEqual(
            frontier["noncompleted_linked_unconsumed"][0]["observation_id"], "L2"
        )
        self.assertEqual(
            frontier["noncompleted_linked_unconsumed"][0]["lifecycle_statuses"]["O2"],
            "PLANNED",
        )
        self.assertEqual(frontier["unlinked_live_observation_ids"], ["L3"])

    def test_completed_linked_observation_with_existing_analysis_is_visible_not_selected(self):
        self.live["observations"].append(
            {
                "observation_id": "L4",
                "regions": ["Region B"],
                "domain_tags": ["DOMAIN_C"],
                "canonical_links": [{"occurrence_id": "O3", "relationship": "OUTCOME_OF"}],
            }
        )
        audit = build_cross_layer_coverage_audit(
            self.registry, self.expectations, self.live, self.analysis
        )
        frontier = audit["bridge_frontier"]
        self.assertEqual(frontier["factual_same_anchor_candidate_count"], 1)
        candidate = frontier["completed_linked_with_existing_analysis_unconsumed"][0]
        self.assertEqual(candidate["observation_id"], "L4")
        self.assertEqual(candidate["canonical_occurrence_id"], "O3")
        self.assertEqual(candidate["analysis_ids"], ["AN2"])
        self.assertFalse(audit["methodology"]["automatic_live_analysis_bridge_population"])

    def test_region_equivalence_is_explicit_audit_only_and_raw_label_is_preserved(self):
        registry = {
            "version": "regions",
            "records": [
                {
                    "occurrence_id": "OA",
                    "series_id": "SA",
                    "region": "Africa",
                    "category": "CAT",
                    "institution": "Inst",
                    "lifecycle_status": "COMPLETED",
                }
            ],
        }
        live = {
            "version": "regions",
            "observations": [
                {
                    "observation_id": "LA",
                    "regions": ["Central Africa"],
                    "domain_tags": ["DOMAIN"],
                    "canonical_links": [],
                }
            ],
        }
        audit = build_cross_layer_coverage_audit(
            registry,
            {"version": "regions", "adapters": []},
            live,
            {"version": "regions", "reviews": []},
        )
        self.assertEqual(
            LIVE_REGION_TO_CANONICAL_COMPARISON_REGION,
            {"Central Africa": "Africa", "Global": "Cross-regional / Global"},
        )
        self.assertTrue(
            audit["methodology"]["region_equivalence_is_explicit_audit_only_and_nonmutating"]
        )
        self.assertFalse(audit["region_comparison"]["governed_region_mutation"])
        self.assertEqual(audit["lookup"]["regions"]["Africa"]["live_observation_count"], 1)
        self.assertEqual(
            audit["lookup"]["regions"]["Africa"]["raw_live_region_labels"],
            ["Central Africa"],
        )
        raw = {row["region"]: row for row in audit["raw_region_shape"]}
        self.assertEqual(raw["Central Africa"]["live_observation_count"], 1)
        self.assertEqual(raw["Central Africa"]["canonical_occurrence_count"], 0)
        self.assertNotIn(
            "Africa",
            audit["diagnostic_prompts"]["regions_with_canonical_series_but_no_live_observation"],
        )
        self.assertEqual(registry["records"][0]["region"], "Africa")
        self.assertEqual(live["observations"][0]["regions"], ["Central Africa"])

    def test_unknown_cross_layer_references_fail_closed(self):
        bad_monitor = {
            "version": "bad",
            "adapters": [{"adapter_id": "A1", "canonical_occurrence_ids": ["MISSING"]}],
        }
        with self.assertRaises(ValueError):
            build_cross_layer_coverage_audit(
                self.registry, bad_monitor, self.live, self.analysis
            )


class CrossLayerCoverageCurrentStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = build_cross_layer_coverage_audit(
            load("data/canonical/registry.json"),
            load("data/monitor/expectations.json"),
            load("data/live_intelligence/observations.json"),
            load("data/analysis/event_reviews.json"),
        )

    def test_post_ci_layer_counts(self):
        totals = self.audit["totals"]
        self.assertEqual(totals["canonical_occurrence_count"], 690)
        self.assertEqual(totals["configured_monitor_adapter_count"], 26)
        self.assertEqual(totals["configured_monitor_scoped_occurrence_count"], 217)
        self.assertGreaterEqual(totals["live_observation_count"], 7)
        self.assertGreaterEqual(totals["canonical_linked_live_observation_count"], 2)
        self.assertEqual(totals["analysis_review_count"], 22)
        self.assertEqual(totals["production_live_input_count"], 1)
        self.assertEqual(totals["production_revision_count"], 1)

    def test_current_bridge_frontier_does_not_force_barmm_downstream(self):
        frontier = self.audit["bridge_frontier"]
        self.assertEqual(
            frontier["used_live_observation_ids"],
            ["WSLI-MAC-JPN-FIES-202607-001"],
        )
        self.assertEqual(frontier["factual_same_anchor_candidate_count"], 0)
        barmm = [
            row
            for row in frontier["noncompleted_linked_unconsumed"]
            if row["observation_id"] == "WSLI-INST-PHL-BARMM-PREELECT-20260909-001"
        ]
        self.assertEqual(len(barmm), 1)
        self.assertEqual(
            barmm[0]["lifecycle_statuses"]["WSO-EL-PH-BARMM-20260914"],
            "PLANNED",
        )

    def test_current_region_comparison_does_not_report_granularity_artifacts_as_gaps(self):
        regions = self.audit["lookup"]["regions"]
        self.assertEqual(regions["Africa"]["live_observation_count"], 2)
        self.assertEqual(regions["Africa"]["raw_live_region_labels"], ["Central Africa"])
        self.assertEqual(regions["Cross-regional / Global"]["live_observation_count"], 1)
        self.assertEqual(
            regions["Cross-regional / Global"]["raw_live_region_labels"], ["Global"]
        )
        prompts = self.audit["diagnostic_prompts"]
        self.assertNotIn(
            "Africa", prompts["regions_with_canonical_series_but_no_live_observation"]
        )
        self.assertNotIn(
            "Cross-regional / Global",
            prompts["regions_with_canonical_series_but_no_live_observation"],
        )
        self.assertEqual(prompts["regions_with_live_observation_but_no_analysis_review"], [])

    def test_audit_has_no_write_or_auto_population_authority(self):
        method = self.audit["methodology"]
        self.assertTrue(method["read_only"])
        self.assertFalse(method["automatic_canonical_commit"])
        self.assertFalse(method["automatic_monitor_route_creation"])
        self.assertFalse(method["automatic_live_population"])
        self.assertFalse(method["automatic_live_analysis_bridge_population"])
        self.assertFalse(method["automatic_analysis_population"])


if __name__ == "__main__":
    unittest.main()
