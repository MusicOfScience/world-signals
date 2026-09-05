from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.apply_source_native_fiscal_analysis_v import (
    ANALYSIS_EVIDENCE_PATH,
    ANALYSIS_REVIEWS_PATH,
    ANALYSIS_SCHEMA_PATH,
    CANONICAL_PATH,
    CANONICAL_SCHEMA_PATH,
    LEDGER_PATH,
    OVERLAY_PATH,
    PLAN_PATH,
    SOURCE_PATH,
    build_post_state,
    load,
)
from src.world_signals.analysis import project_analysis_for_browser, validate_analysis


class SourceNativeFiscalAnalysisVTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load(PLAN_PATH)
        cls.canonical = load(CANONICAL_PATH)
        cls.canonical_schema = load(CANONICAL_SCHEMA_PATH)
        cls.sources = load(SOURCE_PATH)
        cls.ledger = load(LEDGER_PATH)
        cls.overlay = load(OVERLAY_PATH)
        cls.schema = load(ANALYSIS_SCHEMA_PATH)
        cls.reviews = load(ANALYSIS_REVIEWS_PATH)
        cls.evidence = load(ANALYSIS_EVIDENCE_PATH)

        p = cls.plan["preconditions"]
        cls.exact_pre = (
            str(cls.canonical.get("version")) == p["canonical_registry_version"]
            and len(cls.canonical.get("records", [])) == p["canonical_record_count"]
            and str(cls.sources.get("version")) == p["source_registry_version"]
            and len(cls.sources.get("sources", [])) == p["source_record_count"]
            and str(cls.ledger.get("version")) == p["change_ledger_version"]
            and len(cls.ledger.get("changes", [])) == p["change_ledger_count"]
            and str(cls.reviews.get("version")) == p["analysis_reviews_version"]
            and len(cls.reviews.get("reviews", [])) == p["analysis_review_count"]
            and str(cls.evidence.get("version")) == p["analysis_evidence_version"]
            and len(cls.evidence.get("evidence", [])) == p["analysis_evidence_count"]
        )
        if cls.exact_pre:
            cls.post_reviews, cls.post_evidence = build_post_state(
                cls.canonical,
                cls.canonical_schema,
                cls.sources,
                cls.ledger,
                cls.overlay,
                cls.schema,
                cls.reviews,
                cls.evidence,
                cls.plan,
            )
        else:
            cls.post_reviews = cls.reviews
            cls.post_evidence = cls.evidence

        cls.review_by_id = {
            row["analysis_id"]: row for row in cls.post_reviews.get("reviews", [])
        }
        cls.evidence_by_id = {
            row["evidence_id"]: row for row in cls.post_evidence.get("evidence", [])
        }

    def test_v_contract_schema_is_explicit_and_fail_closed(self):
        schema = self.schema
        self.assertIn("SOURCE_NATIVE_CALENDAR_DATE", schema["allowed_timing_types"])
        self.assertIn("NO_CLEAR_SURPRISE", schema["allowed_surprise_statuses"])
        self.assertIn("SOURCE_REPORTED_CHANGE_AND_ENDPOINT", schema["allowed_measurement_precision"])
        self.assertIn("OBSERVATION_CONTEXT", schema["allowed_interaction_types"])
        self.assertIn("NOT_A_CAUSAL_CLAIM", schema["allowed_causal_statuses"])
        self.assertIn("OBSERVED_SIGNAL", schema["allowed_second_order_statuses"])

    def test_check_only_transform_is_exact_and_does_not_mutate_inputs(self):
        if not self.exact_pre:
            self.skipTest("check-only transform is exercised only from exact V pre-state")
        reviews_before = json.dumps(self.reviews, sort_keys=True)
        evidence_before = json.dumps(self.evidence, sort_keys=True)
        post_reviews, post_evidence = build_post_state(
            self.canonical,
            self.canonical_schema,
            self.sources,
            self.ledger,
            self.overlay,
            self.schema,
            self.reviews,
            self.evidence,
            self.plan,
        )
        self.assertEqual(json.dumps(self.reviews, sort_keys=True), reviews_before)
        self.assertEqual(json.dumps(self.evidence, sort_keys=True), evidence_before)
        self.assertEqual(post_reviews["version"], self.plan["postconditions"]["analysis_reviews_version"])
        self.assertEqual(len(post_reviews["reviews"]), self.plan["postconditions"]["analysis_review_count"])
        self.assertEqual(post_evidence["version"], self.plan["postconditions"]["analysis_evidence_version"])
        self.assertEqual(len(post_evidence["evidence"]), self.plan["postconditions"]["analysis_evidence_count"])

    def test_expectation_history_prevents_false_headline_surprise(self):
        review = self.review_by_id["WSAN-NP-BUDGET-2026-001"]
        expected = review["what_was_expected"]
        surprised = review["what_surprised"]
        self.assertGreaterEqual(len(expected["benchmarks"]), 2)
        self.assertEqual(surprised["status"], "NO_CLEAR_SURPRISE")
        self.assertIn("not comparable", surprised["summary"].lower())
        self.assertIn("earlier", surprised["summary"].lower())

    def test_first_market_move_remains_noncausal_and_unreconstructed(self):
        review = self.review_by_id["WSAN-NP-BUDGET-2026-001"]
        self.assertEqual(len(review["what_moved"]), 1)
        movement = review["what_moved"][0]
        self.assertEqual(movement["measurement_precision"], "SOURCE_REPORTED_CHANGE_AND_ENDPOINT")
        self.assertFalse(movement["independently_reconstructed"])
        self.assertIsNone(movement["pre_value"])
        self.assertIsNotNone(movement["post_value"])
        connection = review["what_appears_connected"]
        self.assertEqual(connection["causal_status"], "NOT_A_CAUSAL_CLAIM")
        self.assertEqual(connection["interaction_type"], "OBSERVATION_CONTEXT")

    def test_observed_second_order_signal_preserves_reconciliation_warning(self):
        review = self.review_by_id["WSAN-NP-BUDGET-2026-001"]
        second = review["second_order_effects"]
        self.assertEqual(second["status"], "OBSERVED_SIGNAL")
        self.assertIn("reconciliation", second["summary"].lower())
        self.assertGreaterEqual(len(review["falsifiers"]), 2)

    def test_analysis_evidence_never_becomes_canonical_provenance_or_time(self):
        canonical = {
            row["occurrence_id"]: row for row in self.canonical.get("records", [])
        }["WSO-FIS-A-0018"]
        self.assertEqual(canonical["timing_type"], "SOURCE_NATIVE_CALENDAR_DATE")
        self.assertIsNone(canonical.get("start_local"))
        self.assertIsNone(canonical.get("start_utc"))
        self.assertEqual(canonical["source_native_date_label"], "15 Jestha 2083")
        self.assertEqual(canonical["gregorian_resolution_status"], "UNRESOLVED_BY_AUTHORITATIVE_SOURCE")
        self.assertNotEqual(canonical["source_id"], "Reuters")

    def test_public_projection_preserves_native_date_without_conversion(self):
        projection = project_analysis_for_browser(
            self.schema,
            self.post_reviews,
            self.post_evidence,
            self.canonical,
        )
        row = next(item for item in projection["reviews"] if item["analysis_id"] == "WSAN-NP-BUDGET-2026-001")
        self.assertEqual(row["canonical_timing"]["timing_type"], "SOURCE_NATIVE_CALENDAR_DATE")
        self.assertEqual(row["canonical_timing"]["source_native_date_label"], "15 Jestha 2083")
        self.assertIsNone(row["canonical_timing"]["start_local"])
        self.assertIsNone(row["canonical_timing"]["start_utc"])

    def test_browser_renders_source_native_truth_without_converter(self):
        source = (ROOT / "web/analysis.js").read_text(encoding="utf-8")
        self.assertIn("source_native_date_label", source)
        self.assertIn("gregorian_resolution_status", source)
        self.assertIn("Gregorian mapping unresolved by authoritative source", source)
        self.assertIn("canonical timing unresolved; no date inferred", source)
        self.assertNotIn("BIKRAM_SAMBAT_NEPAL", source)
        self.assertNotIn("Jestha 2083", source)
        self.assertNotIn("2026-05-29", source)
        self.assertNotIn("data/canonical", source)

    def test_v_write_gates_and_frozen_upstream_boundary_survive_descendants(self):
        for key, value in self.plan["guardrails"].items():
            self.assertFalse(value, key)
        pre = self.plan["preconditions"]
        self.assertEqual((pre["canonical_registry_version"], pre["canonical_record_count"]), ("0.30", 681))
        self.assertEqual((pre["source_registry_version"], pre["source_record_count"]), ("1.72", 237))
        self.assertEqual((pre["change_ledger_version"], pre["change_ledger_count"]), ("0.17", 51))
        self.assertGreaterEqual(float(self.canonical["version"]), 0.30)
        self.assertGreaterEqual(len(self.canonical["records"]), 681)
        self.assertGreaterEqual(float(self.sources["version"]), 1.72)
        self.assertGreaterEqual(len(self.sources["sources"]), 237)
        self.assertGreaterEqual(float(self.ledger["version"]), 0.17)
        self.assertGreaterEqual(len(self.ledger["changes"]), 51)
        self.assertGreaterEqual(float(self.overlay["version"]), 0.5)
        self.assertGreaterEqual(float(self.overlay["canonical_checkpoint"]["registry_version"]), 0.30)
        self.assertGreaterEqual(self.overlay["canonical_checkpoint"]["record_count"], 681)


if __name__ == "__main__":
    unittest.main()
