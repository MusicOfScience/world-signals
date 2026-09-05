from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.apply_east_asia_lifecycle_repair_z import (
    ANALYSIS_EVIDENCE_PATH,
    ANALYSIS_REVIEWS_PATH,
    ANALYSIS_SCHEMA_PATH,
    CANONICAL_PATH,
    CANONICAL_SCHEMA_PATH,
    LEDGER_PATH,
    OVERLAY_PATH,
    PLAN_PATH,
    SOURCE_PATH,
    TARGET_IDS,
    assertion_id,
    build_post_state,
    change_id,
    load,
)
from src.world_signals.analysis import analysis_population_readiness


class EastAsiaLifecycleRepairZTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load(PLAN_PATH)
        cls.canonical = load(CANONICAL_PATH)
        cls.canonical_schema = load(CANONICAL_SCHEMA_PATH)
        cls.sources = load(SOURCE_PATH)
        cls.ledger = load(LEDGER_PATH)
        cls.overlay = load(OVERLAY_PATH)
        cls.analysis_schema = load(ANALYSIS_SCHEMA_PATH)
        cls.reviews = load(ANALYSIS_REVIEWS_PATH)
        cls.evidence = load(ANALYSIS_EVIDENCE_PATH)

        exact_pre = (
            str(cls.canonical.get("version")) == cls.plan["preconditions"]["canonical_registry_version"]
            and len(cls.canonical.get("records", [])) == cls.plan["preconditions"]["canonical_record_count"]
            and str(cls.sources.get("version")) == cls.plan["preconditions"]["source_registry_version"]
            and str(cls.ledger.get("version")) == cls.plan["preconditions"]["change_ledger_version"]
        )
        if exact_pre:
            cls.post_canonical, cls.post_sources, cls.post_ledger, cls.post_overlay = build_post_state(
                cls.canonical, cls.canonical_schema, cls.sources, cls.ledger, cls.overlay,
                cls.analysis_schema, cls.reviews, cls.evidence, cls.plan,
                "2026-09-06T06:00:00+10:00",
            )
            cls.simulated = True
        else:
            cls.post_canonical = cls.canonical
            cls.post_sources = cls.sources
            cls.post_ledger = cls.ledger
            cls.post_overlay = cls.overlay
            cls.simulated = False

    def test_exact_prestate_or_z_contribution_present(self):
        p = self.plan["preconditions"]
        post = self.plan["postconditions"]
        if self.simulated:
            self.assertEqual((self.canonical["version"], len(self.canonical["records"])), (p["canonical_registry_version"], p["canonical_record_count"]))
            self.assertEqual((self.sources["version"], len(self.sources["sources"])), (p["source_registry_version"], p["source_record_count"]))
            self.assertEqual((self.ledger["version"], len(self.ledger["changes"])), (p["change_ledger_version"], p["change_ledger_count"]))
        else:
            self.assertGreaterEqual(float(self.post_canonical["version"]), float(post["canonical_registry_version"]))
            self.assertGreaterEqual(len(self.post_canonical["records"]), post["canonical_record_count"])

    def test_only_existing_stable_occurrences_are_repaired(self):
        by_id = {row["occurrence_id"]: row for row in self.post_canonical["records"]}
        self.assertTrue(set(TARGET_IDS).issubset(by_id))
        self.assertFalse(any(row.get("occurrence_id", "").startswith("WSO-KR-") for row in self.post_canonical["records"]))
        for oid in TARGET_IDS:
            self.assertEqual(by_id[oid]["lifecycle_status"], "COMPLETED")
            self.assertEqual(by_id[oid]["certainty_status"], "CONFIRMED")

    def test_timing_and_schedule_identity_are_preserved(self):
        before = {row["occurrence_id"]: row for row in self.canonical["records"]}
        after = {row["occurrence_id"]: row for row in self.post_canonical["records"]}
        baselines = self.plan["preconditions"]["targets"]
        for oid, baseline in baselines.items():
            row = after[oid]
            for key in ("series_id", "source_id", "start_local", "source_timezone", "start_utc", "time_precision", "time_status", "primary_source_assertion_id"):
                self.assertEqual(row.get(key), baseline.get(key))
            self.assertIsNone(row.get("start_utc"))
            self.assertIsNone(row.get("end_utc"))
            if self.simulated:
                for key in ("timing_type", "time_precision", "all_day_semantics", "time_status", "time_basis", "auction_stage"):
                    self.assertEqual(before[oid].get(key), row.get(key))

    def test_completion_assertions_and_documents_are_explicit(self):
        by_id = {row["occurrence_id"]: row for row in self.post_canonical["records"]}
        repairs = {item["occurrence_id"]: item for item in self.plan["repairs"]}
        for oid, item in repairs.items():
            row = by_id[oid]
            self.assertEqual(row["last_successful_assertion_id"], assertion_id(item))
            self.assertEqual(row["status_history"][-1]["source_assertion_id"], assertion_id(item))
            self.assertEqual(row["status_history"][-1]["lifecycle_status"], "COMPLETED")
            docs = [d for d in row.get("related_documents", []) if d.get("source_id") == item["completion_source_id"]]
            self.assertEqual(len(docs), 1)
            self.assertEqual(docs[0]["role"], "COMPLETION_OUTCOME_VERIFICATION")
            self.assertEqual(docs[0]["source_locator"], item["completion_source_url"])

    def test_completion_sources_are_supporting_only(self):
        by_id = {row["source_id"]: row for row in self.post_sources["sources"]}
        for item in self.plan["repairs"]:
            src = by_id[item["completion_source_id"]]
            self.assertEqual(src["authoritative_url"], item["completion_source_url"])
            self.assertEqual(src["canonical_dependency_count"], 0)
            self.assertEqual(src["verification_mode"], "MANUAL_AUTHORITATIVE_RECHECK")
            self.assertEqual(src["automated_monitoring_use"], "ENDPOINT_REVIEW_REQUIRED")

    def test_preexisting_sources_are_byte_semantically_unchanged_in_transform(self):
        if not self.simulated:
            self.skipTest("exact source mutation-boundary comparison belongs to Z prestate simulation")
        before = {row["source_id"]: row for row in self.sources["sources"]}
        after = {row["source_id"]: row for row in self.post_sources["sources"]}
        for sid, row in before.items():
            self.assertEqual(after[sid], row)

    def test_ledger_records_reviewed_lifecycle_repair(self):
        by_change = {row.get("change_id"): row for row in self.post_ledger.get("changes", [])}
        for item in self.plan["repairs"]:
            entry = by_change[change_id(item)]
            self.assertEqual(entry["occurrence_id"], item["occurrence_id"])
            self.assertEqual(entry["change_type"], "LIFECYCLE_AND_CERTAINTY_UPDATE")
            self.assertEqual(entry["old_values"]["lifecycle_status"], "PLANNED")
            self.assertEqual(entry["new_values"]["lifecycle_status"], "COMPLETED")
            self.assertEqual(entry["old_values"]["certainty_status"], "CONFIRMED")
            self.assertEqual(entry["new_values"]["certainty_status"], "CONFIRMED")
            self.assertIn("elapsed time", " ".join(entry["review_basis"]).lower())

    def test_analysis_population_expands_without_analysis_mutation(self):
        readiness = analysis_population_readiness(self.analysis_schema, self.reviews, self.post_canonical)
        self.assertGreaterEqual(readiness["eligible_completed_occurrence_count"], self.plan["postconditions"]["eligible_completed_occurrence_count"])
        self.assertEqual(readiness["reviewed_occurrence_count"], self.plan["postconditions"]["reviewed_occurrence_count"])
        completed_east = [row for row in self.post_canonical["records"] if row.get("region") == "East Asia" and row.get("lifecycle_status") == "COMPLETED"]
        self.assertGreaterEqual(len(completed_east), 2)

    def test_overlay_semantics_are_unchanged_in_transform(self):
        if not self.simulated:
            self.assertGreaterEqual(float(self.post_overlay["version"]), float(self.plan["postconditions"]["biosecurity_overlay_version"]))
            return
        before = {k: v for k, v in self.overlay.items() if k not in {"version", "canonical_checkpoint"}}
        after = {k: v for k, v in self.post_overlay.items() if k not in {"version", "canonical_checkpoint"}}
        self.assertEqual(after, before)
        self.assertEqual(self.post_overlay["canonical_checkpoint"], self.plan["postconditions"]["biosecurity_overlay_checkpoint"])


if __name__ == "__main__":
    unittest.main()
