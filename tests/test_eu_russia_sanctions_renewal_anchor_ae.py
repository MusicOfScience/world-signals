import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.apply_eu_russia_sanctions_renewal_anchor_ae import (
    ANALYSIS_EVIDENCE_PATH,
    ANALYSIS_REVIEWS_PATH,
    ANALYSIS_SCHEMA_PATH,
    CANONICAL_PATH,
    CANONICAL_SCHEMA_PATH,
    LEDGER_PATH,
    OVERLAY_PATH,
    PLAN_PATH,
    SOURCE_PATH,
    actual_primary_dependency_count,
    build_post_state,
    load,
    overlay_semantics,
)
from src.world_signals.analysis import validate_analysis
from src.world_signals.validation import validate_registry


def version_tuple(raw):
    return tuple(int(part) for part in str(raw).split("."))


class EURussiaSanctionsRenewalAnchorAETests(unittest.TestCase):
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
        cls.oid = cls.plan["anchor"]["occurrence_id"]
        cls.is_post = any(r.get("occurrence_id") == cls.oid for r in cls.registry.get("records", []))
        if cls.is_post:
            cls.post_registry = cls.registry
            cls.post_sources = cls.sources
            cls.post_ledger = cls.ledger
            cls.post_overlay = cls.overlay
        else:
            cls.post_registry, cls.post_sources, cls.post_ledger, cls.post_overlay = build_post_state(
                cls.registry,
                cls.schema,
                cls.sources,
                cls.ledger,
                cls.overlay,
                cls.analysis_schema,
                cls.reviews,
                cls.evidence,
                cls.plan,
                "2026-09-06T12:00:00+10:00",
            )

    def test_plan_is_exact_post_59_and_reuses_existing_series_source(self):
        self.assertEqual(self.plan["exact_base_main"], "7933a9880649ec6a98872fa557566a6b62d55c9d")
        item = self.plan["anchor"]
        self.assertEqual(item["series_id"], "WSER-TRD-EU-RU-SANC")
        self.assertEqual(item["source_id"], "WSSRC-TRD-004")
        self.assertEqual(self.plan["source_mutation"]["new_sources"], 0)

    def test_legal_adoption_is_distinct_from_future_expiry_boundary(self):
        by_id = {r["occurrence_id"]: r for r in self.post_registry["records"]}
        hist = by_id[self.oid]
        future = by_id["WSO-TRD-A-0005"]
        self.assertEqual(hist["trade_policy_temporal_role"], "LEGAL_ADOPTION")
        self.assertEqual(future["trade_policy_temporal_role"], "EXPIRY_OR_RENEWAL_BOUNDARY")
        self.assertTrue(future["expiry_does_not_imply_termination"])

    def test_press_release_clock_is_not_promoted_to_decision_time(self):
        row = next(r for r in self.post_registry["records"] if r.get("occurrence_id") == self.oid)
        self.assertEqual(row["start_local"], "2026-06-25")
        self.assertEqual(row["source_timezone"], "Europe/Brussels")
        self.assertEqual(row["time_precision"], "DAY")
        self.assertIsNone(row["start_utc"])
        self.assertIsNone(row["publication_datetime"])

    def test_completion_is_first_party_not_elapsed_time(self):
        row = next(r for r in self.post_registry["records"] if r.get("occurrence_id") == self.oid)
        self.assertEqual(row["lifecycle_status"], "COMPLETED")
        self.assertIn("Council of the European Union first-party notice", row["notes"])
        self.assertIn("not as the decision time", row["notes"])

    def test_source_dependency_helper_advances_exactly_one(self):
        source = next(s for s in self.post_sources["sources"] if s.get("source_id") == "WSSRC-TRD-004")
        self.assertEqual(source["canonical_dependency_count"], 2)
        self.assertEqual(actual_primary_dependency_count(self.post_registry, "WSSRC-TRD-004"), 2)

    def test_no_other_source_record_changes_in_exact_simulation(self):
        if self.is_post:
            self.skipTest("exact source mutation comparison belongs to AE pre-state simulation")
        old = {s["source_id"]: s for s in self.sources["sources"]}
        new = {s["source_id"]: s for s in self.post_sources["sources"]}
        self.assertEqual(set(old), set(new))
        changed = [sid for sid in old if old[sid] != new[sid]]
        self.assertEqual(changed, ["WSSRC-TRD-004"])
        a = copy.deepcopy(old["WSSRC-TRD-004"])
        b = copy.deepcopy(new["WSSRC-TRD-004"])
        self.assertEqual(a.pop("canonical_dependency_count"), 1)
        self.assertEqual(b.pop("canonical_dependency_count"), 2)
        self.assertEqual(a, b)

    def test_trade_gap_repaired_without_analysis_write(self):
        self.assertTrue(any(r.get("category") == "TRADE_SANCTIONS_INDUSTRIAL_POLICY" and r.get("lifecycle_status") == "COMPLETED" for r in self.post_registry["records"]))
        self.assertTrue(any(r.get("event_type") == "SANCTIONS_PROCESS" and r.get("lifecycle_status") == "COMPLETED" for r in self.post_registry["records"]))

        # AE's own frozen transaction contract wrote no Analysis rows. Later
        # Analysis tranches may legitimately grow the live registries.
        post = self.plan["postconditions"]
        self.assertEqual((post["analysis_reviews_version"], post["analysis_review_count"]), ("0.8", 12))
        self.assertEqual((post["analysis_evidence_version"], post["analysis_evidence_count"]), ("0.8", 44))
        self.assertIn("No Analysis review or evidence row is created.", self.plan["guardrails"])
        self.assertGreaterEqual(version_tuple(self.reviews["version"]), version_tuple(post["analysis_reviews_version"]))
        self.assertGreaterEqual(len(self.reviews["reviews"]), post["analysis_review_count"])
        self.assertGreaterEqual(version_tuple(self.evidence["version"]), version_tuple(post["analysis_evidence_version"]))
        self.assertGreaterEqual(len(self.evidence["evidence"]), post["analysis_evidence_count"])

    def test_post_state_counts_are_exact(self):
        post = self.plan["postconditions"]
        self.assertEqual((post["canonical_registry_version"], post["canonical_record_count"]), ("0.34", 684))
        self.assertEqual((post["source_registry_version"], post["source_record_count"]), ("1.75", 240))
        self.assertEqual((post["change_ledger_version"], post["change_ledger_count"]), ("0.21", 56))
        self.assertEqual(post["biosecurity_overlay_checkpoint"], {"registry_version": "0.34", "record_count": 684})

        self.assertGreaterEqual(version_tuple(self.post_registry["version"]), version_tuple(post["canonical_registry_version"]))
        self.assertGreaterEqual(self.post_registry["record_count"], post["canonical_record_count"])
        self.assertGreaterEqual(version_tuple(self.post_sources["version"]), version_tuple(post["source_registry_version"]))
        self.assertGreaterEqual(len(self.post_sources["sources"]), post["source_record_count"])
        self.assertGreaterEqual(version_tuple(self.post_ledger["version"]), version_tuple(post["change_ledger_version"]))
        self.assertGreaterEqual(len(self.post_ledger["changes"]), post["change_ledger_count"])
        self.assertGreaterEqual(
            version_tuple(self.post_overlay["canonical_checkpoint"]["registry_version"]),
            version_tuple(post["biosecurity_overlay_checkpoint"]["registry_version"]),
        )
        self.assertGreaterEqual(
            self.post_overlay["canonical_checkpoint"]["record_count"],
            post["biosecurity_overlay_checkpoint"]["record_count"],
        )

    def test_overlay_semantics_are_unchanged_in_simulation(self):
        if self.is_post:
            self.assertGreaterEqual(
                version_tuple(self.post_overlay["version"]),
                version_tuple(self.plan["postconditions"]["biosecurity_overlay_version"]),
            )
        else:
            self.assertEqual(overlay_semantics(self.overlay), overlay_semantics(self.post_overlay))

    def test_registry_and_analysis_validate(self):
        report = validate_registry(self.post_registry, self.post_sources)
        self.assertTrue(report.ok, report.errors)
        analysis = validate_analysis(self.analysis_schema, self.evidence, self.reviews, self.post_registry)
        self.assertFalse(analysis.errors, analysis.errors)


if __name__ == "__main__":
    unittest.main()
