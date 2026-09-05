from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.apply_rba_financial_stability_anchor_ac import (
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
    expected_assertion_id,
    expected_change_id,
    load,
    overlay_semantics,
    utc_from_local,
)
from src.world_signals.analysis import analysis_population_readiness


class RBAFinancialStabilityHistoricalAnchorACTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load(PLAN_PATH)
        cls.registry = load(CANONICAL_PATH)
        cls.schema = load(CANONICAL_SCHEMA_PATH)
        cls.sources = load(SOURCE_PATH)
        cls.ledger = load(LEDGER_PATH)
        cls.overlay = load(OVERLAY_PATH)
        cls.analysis_schema = load(ANALYSIS_SCHEMA_PATH)
        cls.reviews = load(ANALYSIS_REVIEWS_PATH)
        cls.evidence = load(ANALYSIS_EVIDENCE_PATH)
        p = cls.plan["preconditions"]
        cls.exact_pre = (
            str(cls.registry.get("version")) == p["canonical_registry_version"]
            and len(cls.registry.get("records", [])) == p["canonical_record_count"]
            and str(cls.ledger.get("version")) == p["change_ledger_version"]
            and len(cls.ledger.get("changes", [])) == p["change_ledger_count"]
        )
        if cls.exact_pre:
            cls.post_registry, cls.post_ledger, cls.post_overlay = build_post_state(
                cls.registry,
                cls.schema,
                cls.sources,
                cls.ledger,
                cls.overlay,
                cls.analysis_schema,
                cls.reviews,
                cls.evidence,
                cls.plan,
                "2026-09-06T07:00:00+10:00",
            )
        else:
            cls.post_registry = cls.registry
            cls.post_ledger = cls.ledger
            cls.post_overlay = cls.overlay

    def test_plan_is_exactly_post_57_and_no_new_series_or_source(self):
        self.assertEqual(self.plan["base_main_sha"], "09433d3a6ed0aca957271be49777eab33f08ee72")
        discipline = self.plan["selection_discipline"]
        self.assertFalse(discipline["new_series_created"])
        self.assertFalse(discipline["new_source_created"])
        self.assertFalse(discipline["elapsed_time_is_completion_evidence"])
        self.assertFalse(self.plan["mutation_policy"]["source_registry"])
        self.assertFalse(self.plan["mutation_policy"]["analysis_reviews"])
        self.assertFalse(self.plan["mutation_policy"]["analysis_evidence"])

    def test_stable_identity_and_series_reuse(self):
        item = self.plan["anchor"]
        rows = {row["occurrence_id"]: row for row in self.post_registry["records"]}
        self.assertIn(item["occurrence_id"], rows)
        row = rows[item["occurrence_id"]]
        self.assertEqual(row["series_id"], "WSER-FIN-AU-RBA-FSR")
        self.assertEqual(row["source_id"], "WSSRC-FIN-001")
        self.assertEqual(row["category"], "FINANCIAL_STABILITY_REGULATION")
        self.assertEqual(row["event_type"], "FINANCIAL_STABILITY_REPORT")
        if self.exact_pre:
            before_ids = {existing["occurrence_id"] for existing in self.registry["records"]}
            self.assertNotIn(item["occurrence_id"], before_ids)
            after_ids = {existing["occurrence_id"] for existing in self.post_registry["records"]}
            self.assertEqual(after_ids, before_ids | {item["occurrence_id"]})

    def test_authoritative_native_time_and_utc_conversion(self):
        item = self.plan["anchor"]
        timing = item["timing"]
        self.assertEqual(timing["start_local"], "2026-03-19T11:30:00")
        self.assertEqual(timing["source_timezone"], "Australia/Sydney")
        self.assertEqual(timing["source_timezone_label"], "AEDT")
        self.assertEqual(timing["start_utc"], "2026-03-19T00:30:00Z")
        self.assertEqual(utc_from_local(timing["start_local"], timing["source_timezone"]), timing["start_utc"])
        rows = {row["occurrence_id"]: row for row in self.post_registry["records"]}
        row = rows[item["occurrence_id"]]
        self.assertEqual(row["time_precision"], "MINUTE")
        self.assertEqual(row["time_status"], "CONFIRMED")
        self.assertEqual(row["time_basis"], "EXPLICIT_AUTHORITATIVE_SCHEDULE")

    def test_completion_is_evidence_based(self):
        item = self.plan["anchor"]
        self.assertEqual(item["primary_source_assertion_id"], expected_assertion_id(item, "PRIMARY"))
        self.assertEqual(item["completion_source_assertion_id"], expected_assertion_id(item, "COMPLETION"))
        self.assertEqual(item["change_id"], expected_change_id(item))
        rows = {row["occurrence_id"]: row for row in self.post_registry["records"]}
        row = rows[item["occurrence_id"]]
        self.assertEqual(row["lifecycle_status"], "COMPLETED")
        self.assertEqual(row["certainty_status"], "CONFIRMED")
        self.assertIn("not inferred from elapsed time", row["status_history"][-1]["change_reason"])
        self.assertEqual(row["status_history"][-1]["source_assertion_id"], item["completion_source_assertion_id"])
        docs = [doc for doc in row.get("related_documents", []) if doc.get("role") == "COMPLETION_OUTCOME_VERIFICATION"]
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["source_id"], "WSSRC-FIN-001")
        self.assertEqual(docs[0]["source_locator"], item["publication_url"])

    def test_exact_transform_preserves_preexisting_rows_sources_and_overlay_semantics(self):
        if not self.exact_pre:
            self.skipTest("exact mutation-boundary semantics belong to AC pre-state simulation")
        self.assertEqual(self.post_registry["records"][:-1], self.registry["records"])
        self.assertEqual(self.sources, load(SOURCE_PATH))
        self.assertEqual(self.post_ledger["changes"][:-1], self.ledger["changes"])
        self.assertEqual(overlay_semantics(self.post_overlay), overlay_semantics(self.overlay))

    def test_financial_stability_completed_gap_is_repaired(self):
        completed = [row for row in self.post_registry["records"] if row.get("lifecycle_status") == "COMPLETED"]
        self.assertIn("FINANCIAL_STABILITY_REGULATION", {row.get("category") for row in completed})
        self.assertIn("FINANCIAL_STABILITY_REPORT", {row.get("event_type") for row in completed})

    def test_analysis_population_expands_without_analysis_write(self):
        readiness = analysis_population_readiness(self.analysis_schema, self.reviews, self.post_registry)
        expected = self.plan["postconditions"]
        self.assertGreaterEqual(readiness["eligible_completed_occurrence_count"], expected["eligible_completed_occurrence_count"])
        self.assertGreaterEqual(readiness["reviewed_occurrence_count"], expected["reviewed_occurrence_count"])
        if self.exact_pre:
            self.assertEqual(readiness["eligible_completed_occurrence_count"], expected["eligible_completed_occurrence_count"])
            self.assertEqual(readiness["reviewed_occurrence_count"], expected["reviewed_occurrence_count"])

    def test_change_ledger_records_historical_admission(self):
        item = self.plan["anchor"]
        changes = {row.get("change_id"): row for row in self.post_ledger.get("changes", [])}
        self.assertIn(item["change_id"], changes)
        change = changes[item["change_id"]]
        self.assertEqual(change["change_type"], "HISTORICAL_OCCURRENCE_ADMISSION")
        self.assertFalse(change["old_values"]["canonical_presence"])
        self.assertTrue(change["new_values"]["canonical_presence"])
        self.assertIn("elapsed time", " ".join(change["review_basis"]).lower())


if __name__ == "__main__":
    unittest.main()
