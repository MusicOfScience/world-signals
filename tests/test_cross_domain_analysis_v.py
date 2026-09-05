from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from world_signals.analysis import analysis_population_readiness, public_analysis_projection, validate_analysis
import apply_cross_domain_analysis_v as txn


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def version_tuple(value):
    return tuple(int(part) for part in str(value).split("."))


class CrossDomainAnalysisVTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load("data/analysis/CROSS_DOMAIN_ANALYSIS_V_PLAN_v0.1.json")
        cls.payload = load("data/analysis/CROSS_DOMAIN_ANALYSIS_V_PAYLOAD_v0.1.json")
        cls.schema = load("data/analysis/schema.json")
        cls.reviews = load("data/analysis/event_reviews.json")
        cls.evidence = load("data/analysis/evidence_registry.json")
        cls.canonical = load("data/canonical/registry.json")
        cls.sources = load("data/sources/registry.json")
        cls.by_occurrence = {row["occurrence_id"]: row for row in cls.canonical["records"]}
        cls.by_analysis = {row["analysis_id"]: row for row in cls.reviews["reviews"]}
        cls.by_evidence = {row["evidence_id"]: row for row in cls.evidence["evidence"]}
        cls.is_post = (
            version_tuple(cls.reviews.get("version", "0.0")) >= (0, 5)
            and len(cls.reviews.get("reviews", [])) >= 11
            and version_tuple(cls.evidence.get("version", "0.0")) >= (0, 5)
            and len(cls.evidence.get("evidence", [])) >= 29
        )

    def require_post(self):
        if not self.is_post:
            self.skipTest("exact V contribution assertions run after reviewed V transaction")

    def simulated_or_live_post(self):
        if self.is_post:
            return self.reviews, self.evidence
        reviews, evidence, _ = txn.transform(
            self.plan,
            self.payload,
            self.canonical,
            self.schema,
            self.reviews,
            self.evidence,
        )
        return reviews, evidence

    def test_check_only_transform_is_exact_from_frozen_pre_state(self):
        if self.is_post:
            self.skipTest("check-only transform is exercised only from exact V pre-state")
        reviews, evidence, readiness = txn.transform(
            self.plan,
            self.payload,
            self.canonical,
            self.schema,
            self.reviews,
            self.evidence,
        )
        self.assertEqual((reviews["version"], len(reviews["reviews"])), ("0.5", 11))
        self.assertEqual((evidence["version"], len(evidence["evidence"])), ("0.5", 29))
        self.assertEqual(reviews["canonical_checkpoint"], {"registry_version": "0.30", "record_count": 681})
        self.assertEqual(readiness["eligible_completed_occurrence_count"], 12)
        self.assertEqual(readiness["reviewed_occurrence_count"], 11)
        self.assertEqual(readiness["reviewed_event_type_diversity"], 10)
        self.assertEqual(readiness["broad_population_state"], "READY_FOR_CONTROLLED_EXPANSION")

    def test_exact_v_post_state_and_validator(self):
        self.require_post()
        self.assertEqual((self.canonical["version"], len(self.canonical["records"])), ("0.30", 681))
        self.assertEqual((self.reviews["version"], len(self.reviews["reviews"])), ("0.5", 11))
        self.assertEqual((self.evidence["version"], len(self.evidence["evidence"])), ("0.5", 29))
        self.assertEqual(self.reviews["canonical_checkpoint"], {"registry_version": "0.30", "record_count": 681})
        report = validate_analysis(self.schema, self.evidence, self.reviews, self.canonical)
        self.assertTrue(report.ok, report.errors)

    def test_three_new_reviews_bind_to_exact_u_anchors(self):
        reviews, _ = self.simulated_or_live_post()
        by_analysis = {row["analysis_id"]: row for row in reviews["reviews"]}
        expected = {
            "WSAN-BWC-WG8-20260213-001": ("WSO-BWC-WG-2026-S08", "TREATY_WORKING_GROUP_SESSION"),
            "WSAN-WOAH-GS93-20260522-001": ("WSO-WOAH-GS-093", "GOVERNANCE_ASSEMBLY_SESSION"),
            "WSAN-NP-BUDGET-2083-001": ("WSO-FIS-NP-BUDGET-2083", "FISCAL_POLICY_PROCESS"),
        }
        self.assertTrue(set(expected) <= set(by_analysis))
        for analysis_id, (occurrence_id, event_type) in expected.items():
            review = by_analysis[analysis_id]
            row = self.by_occurrence[occurrence_id]
            self.assertEqual(review["canonical_occurrence_id"], occurrence_id)
            self.assertEqual((row["event_type"], row["lifecycle_status"]), (event_type, "COMPLETED"))
            self.assertEqual(review["canonical_event_type"], event_type)
            self.assertEqual(review["canonical_release_utc"], row.get("start_utc"))
            self.assertTrue(review["canonical_mutation_prohibited"])
            self.assertFalse(review["google_calendar_write"])

    def test_bwc_preserves_draft_vs_substantive_outcome_boundary(self):
        reviews, _ = self.simulated_or_live_post()
        review = {row["analysis_id"]: row for row in reviews["reviews"]}["WSAN-BWC-WG8-20260213-001"]
        self.assertEqual(review["what_surprised"]["status"], "NOT_ESTABLISHED")
        self.assertEqual(review["what_moved"], [])
        self.assertEqual(review["what_appears_connected"]["interaction_type"], "STRUCTURAL_DEPENDENCY")
        self.assertEqual(review["what_appears_connected"]["causal_status"], "NOT_A_CAUSAL_CLAIM")
        self.assertEqual(review["second_order_effects"]["status"], "NOT_ESTABLISHED")
        text = " ".join(row["summary"] for row in review["what_may_be_noise"]).lower()
        self.assertIn("procedural report", text)
        self.assertIn("substantive", text)
        self.assertIn("future discussion", text)

    def test_woah_keeps_primary_category_and_prospective_implementation_distinct(self):
        reviews, _ = self.simulated_or_live_post()
        row = self.by_occurrence["WSO-WOAH-GS-093"]
        review = {row["analysis_id"]: row for row in reviews["reviews"]}["WSAN-WOAH-GS93-20260522-001"]
        self.assertEqual(row["category"], "AGRICULTURE_FOOD")
        self.assertEqual(review["what_surprised"]["status"], "NO_CLEAR_SURPRISE")
        self.assertEqual(review["what_moved"], [])
        actuals = {item["metric"]: item["value"] for item in review["what_happened"]["actuals"]}
        self.assertEqual(actuals, {"resolutions_adopted": 35, "international_standards_adopted": 51})
        self.assertEqual(review["second_order_effects"]["status"], "PLAUSIBLE_WATCH_ITEM")
        context = " ".join(item["summary"] for item in review["what_may_be_noise"]).lower()
        self.assertIn("agriculture_food", context)
        self.assertIn("one health", context)

    def test_nepal_preserves_source_native_date_and_observed_later_cycle(self):
        reviews, _ = self.simulated_or_live_post()
        row = self.by_occurrence["WSO-FIS-NP-BUDGET-2083"]
        review = {row["analysis_id"]: row for row in reviews["reviews"]}["WSAN-NP-BUDGET-2083-001"]
        self.assertEqual(row["timing_type"], "SOURCE_NATIVE_CALENDAR_DATE")
        self.assertEqual(row["source_native_date_label"], "15 Jestha 2083")
        self.assertEqual((row["native_calendar_year"], row["native_calendar_month"], row["native_calendar_day"]), (2083, "JESTHA", 15))
        self.assertEqual(row["gregorian_resolution_status"], "UNRESOLVED_AUTHORITATIVE_CONVERSION")
        self.assertIsNone(row["start_local"])
        self.assertIsNone(row["start_utc"])
        self.assertEqual(review["what_surprised"]["status"], "NO_CLEAR_SURPRISE")
        self.assertEqual(review["what_moved"], [])
        self.assertEqual(review["what_appears_connected"]["interaction_type"], "LEGAL_OR_OPERATIONAL_DEPENDENCY")
        self.assertEqual(review["second_order_effects"]["status"], "OBSERVED")
        self.assertIn("7 Saun 2083", review["second_order_effects"]["summary"])
        noise = " ".join(item["summary"] for item in review["what_may_be_noise"]).lower()
        self.assertIn("cms", noise)
        self.assertIn("third-party", noise)

    def test_public_projection_preserves_native_and_range_semantics_read_only(self):
        reviews, evidence = self.simulated_or_live_post()
        projection = public_analysis_projection(self.schema, evidence, reviews, self.canonical)
        by_analysis = {row["analysis_id"]: row for row in projection["reviews"]}
        nepal = by_analysis["WSAN-NP-BUDGET-2083-001"]["canonical"]
        self.assertEqual(nepal["timing_type"], "SOURCE_NATIVE_CALENDAR_DATE")
        self.assertEqual(nepal["source_native_date_label"], "15 Jestha 2083")
        self.assertEqual(nepal["native_calendar_system"], "BIKRAM_SAMBAT_NEPAL")
        self.assertEqual(nepal["gregorian_resolution_status"], "UNRESOLVED_AUTHORITATIVE_CONVERSION")
        self.assertIsNone(nepal["start_local"])
        self.assertIsNone(nepal["start_utc"])
        bwc = by_analysis["WSAN-BWC-WG8-20260213-001"]["canonical"]
        woah = by_analysis["WSAN-WOAH-GS93-20260522-001"]["canonical"]
        self.assertEqual((bwc["start_local"], bwc["end_local"]), ("2026-02-09", "2026-02-13"))
        self.assertEqual((woah["start_local"], woah["end_local"]), ("2026-05-18", "2026-05-22"))
        self.assertFalse(projection["metadata"]["canonical_mutation_allowed"])
        self.assertFalse(projection["metadata"]["google_calendar_write"])

    def test_browser_renders_canonical_temporal_semantics_without_conversion(self):
        js = (ROOT / "web/analysis.js").read_text(encoding="utf-8")
        self.assertIn("canonicalTiming", js)
        self.assertIn("SOURCE_NATIVE_CALENDAR_DATE", js)
        self.assertIn("source_native_date_label", js)
        self.assertIn("gregorian_resolution_status", js)
        self.assertIn("end_local", js)
        self.assertNotIn("Bikram Sambat converter", js)
        self.assertNotIn("data/canonical", js)
        self.assertNotIn("localStorage", js)

    def test_new_evidence_is_analysis_only_and_exactly_eight_records(self):
        _, evidence = self.simulated_or_live_post()
        by_evidence = {row["evidence_id"]: row for row in evidence["evidence"]}
        expected = set(self.plan["new_evidence_ids"])
        self.assertEqual(len(expected), 8)
        self.assertTrue(expected <= set(by_evidence))
        canonical_source_ids = {row.get("source_id") for row in self.canonical["records"]}
        self.assertTrue(expected.isdisjoint(canonical_source_ids))
        for evidence_id in expected:
            self.assertEqual(by_evidence[evidence_id]["canonical_provenance_effect"], "NONE")

    def test_v_readiness_leaves_only_boc_unreviewed(self):
        reviews, _ = self.simulated_or_live_post()
        readiness = analysis_population_readiness(self.schema, reviews, self.canonical)
        self.assertEqual(readiness["eligible_completed_occurrence_count"], 12)
        self.assertEqual(readiness["reviewed_occurrence_count"], 11)
        self.assertEqual(readiness["reviewed_event_type_diversity"], 10)
        self.assertEqual(readiness["broad_population_state"], "READY_FOR_CONTROLLED_EXPANSION")
        reviewed = set(readiness["reviewed_occurrence_ids"])
        remaining = sorted(
            row["occurrence_id"]
            for row in self.canonical["records"]
            if row.get("lifecycle_status") == "COMPLETED" and row["occurrence_id"] not in reviewed
        )
        self.assertEqual(remaining, ["WSO-ddb70f8ff05a58fb"])
        self.assertFalse(self.plan["guardrails"]["backlog_completion_is_population_objective"])

    def test_all_v_write_and_inference_gates_remain_closed(self):
        for value in self.plan["guardrails"].values():
            self.assertFalse(value)
        self.assertFalse(self.schema["layer_boundary"]["canonical_mutation_allowed"])
        self.assertFalse(self.schema["layer_boundary"]["calendar_mutation_allowed"])
        self.assertFalse(self.schema["layer_boundary"]["monitor_configuration_mutation_allowed"])


if __name__ == "__main__":
    unittest.main()
