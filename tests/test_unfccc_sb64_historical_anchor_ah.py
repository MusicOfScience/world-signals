import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.apply_unfccc_sb64_historical_anchor_ah import (
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
from src.world_signals.analysis import analysis_population_readiness, validate_analysis
from src.world_signals.validation import validate_registry


def version_tuple(raw):
    return tuple(int(part) for part in str(raw).split("."))


class UNFCCCSB64HistoricalAnchorAHTests(unittest.TestCase):
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
            cls.readiness = analysis_population_readiness(cls.analysis_schema, cls.reviews, cls.post_registry)
        else:
            cls.post_registry, cls.post_sources, cls.post_ledger, cls.post_overlay, cls.readiness = build_post_state(
                cls.registry, cls.schema, cls.sources, cls.ledger, cls.overlay,
                cls.analysis_schema, cls.reviews, cls.evidence, cls.plan,
                "2026-09-06T09:00:00+10:00",
            )

    def row(self):
        return next(r for r in self.post_registry["records"] if r.get("occurrence_id") == self.oid)

    def source(self):
        sid = self.plan["anchor"]["source_id"]
        return next(s for s in self.post_sources["sources"] if s.get("source_id") == sid)

    def test_plan_is_exact_post_62_and_source_identity_is_new(self):
        self.assertEqual(self.plan["base_main_sha"], "0d55a9dcd877736886dd9ee3e8fcaa8a93a869d1")
        self.assertEqual(self.plan["anchor"]["series_id"], "WSER-CLIM-UNFCCC-SB")
        self.assertEqual(self.plan["anchor"]["source_id"], "WSSRC-CLIM-005")
        self.assertNotEqual(self.plan["anchor"]["source_id"], "WSSRC-CLIM-004")

    def test_sb64_uses_existing_environmental_taxonomy_without_cop_misclassification(self):
        row = self.row()
        self.assertEqual(row["category"], "CLIMATE_ENVIRONMENT")
        self.assertEqual(row["event_type"], "ENVIRONMENTAL_GOVERNANCE_EVENT")
        self.assertEqual(row["environmental_process_type"], "HISTORICAL_CONTEXT_ANCHOR")
        self.assertIn("SBSTA64", row["legal_session_identity"])
        self.assertIn("SBI64", row["legal_session_identity"])

    def test_authoritative_bonn_day_range_preserves_native_timezone_without_synthetic_utc(self):
        row = self.row()
        self.assertEqual(row["timing_type"], "MULTI_DAY_LOCAL")
        self.assertEqual((row["start_local"], row["end_local"]), ("2026-06-08", "2026-06-18"))
        self.assertEqual(row["source_timezone"], "Europe/Berlin")
        self.assertEqual(row["time_precision"], "DAY")
        self.assertTrue(row["all_day_semantics"])
        self.assertIsNone(row["start_utc"])
        self.assertIsNone(row["end_utc"])

    def test_2345_closure_update_is_evidence_not_canonical_endpoint(self):
        row = self.row()
        self.assertNotIn("T23:45", str(row["end_local"]))
        self.assertIn("23:45", row["notes"])
        self.assertIn("completion evidence only", row["notes"])

    def test_completion_requires_first_party_closure_not_elapsed_time(self):
        row = self.row()
        self.assertEqual(row["lifecycle_status"], "COMPLETED")
        self.assertEqual(row["certainty_status"], "CONFIRMED")
        self.assertIn("Completion is not inferred from elapsed time", row["notes"])
        roles = {d["role"] for d in row["related_documents"]}
        self.assertIn("COMPLETION_OUTCOME_VERIFICATION", roles)

    def test_meeting_closure_does_not_encode_outcome_or_causality(self):
        row = self.row()
        for phrase in ("negotiation success", "implementation", "climate outcomes", "market response", "causal attribution"):
            self.assertIn(phrase, row["notes"])

    def test_sb64_is_standalone_not_inherited_cop31_cluster(self):
        row = self.row()
        self.assertIsNone(row["conference_complex_id"])
        self.assertIsNone(row["render_cluster_key"])
        self.assertEqual(row["publication_bundle_type"], "SINGLE_RELEASE")
        self.assertEqual(row["calendar_aggregation_policy"], "STANDALONE")

    def test_new_source_inherits_conservative_unfccc_governance_without_monitor_route(self):
        source = self.source()
        self.assertEqual(source["canonical_provenance_use"], "MANUAL_INFORMATIONAL_REFERENCE_ONLY")
        self.assertEqual(source["automated_monitoring_use"], "PROHIBITED_OR_RIGHTS_HOLD")
        self.assertEqual(source["verification_mode"], "RIGHTS_HELD_MANUAL_ONLY")
        self.assertEqual(source["monitor_endpoints"], [])

    def test_new_source_dependency_helper_matches_canonical_truth(self):
        source = self.source()
        self.assertEqual(source["canonical_dependency_count"], 1)
        self.assertEqual(actual_primary_dependency_count(self.post_registry, source["source_id"]), 1)

    def test_exact_simulation_is_add_only_for_canonical_source_and_ledger(self):
        if self.is_post:
            self.skipTest("exact add-only comparison belongs to AH pre-state simulation")
        self.assertEqual(self.post_registry["records"][:-1], self.registry["records"])
        self.assertEqual(self.post_sources["sources"][:-1], self.sources["sources"])
        self.assertEqual(self.post_ledger["changes"][:-1], self.ledger["changes"])

    def test_overlay_semantics_are_unchanged(self):
        if self.is_post:
            self.assertEqual(self.post_overlay["canonical_checkpoint"]["registry_version"], "0.37")
        else:
            self.assertEqual(overlay_semantics(self.overlay), overlay_semantics(self.post_overlay))

    def test_climate_gap_repaired_without_analysis_write(self):
        self.assertTrue(any(r.get("category") == "CLIMATE_ENVIRONMENT" and r.get("lifecycle_status") == "COMPLETED" for r in self.post_registry["records"]))
        self.assertTrue(any(r.get("event_type") == "ENVIRONMENTAL_GOVERNANCE_EVENT" and r.get("lifecycle_status") == "COMPLETED" for r in self.post_registry["records"]))
        self.assertEqual(self.readiness["eligible_completed_occurrence_count"], 20)

        # AH froze Analysis at 12 reviews / 44 evidence and explicitly prohibited
        # an Analysis write in the same transaction. Descendant Analysis work may
        # grow the live registries while preserving that historical boundary.
        post = self.plan["postconditions"]
        self.assertEqual((post["analysis_reviews_version"], post["analysis_review_count"]), ("0.8", 12))
        self.assertEqual((post["analysis_evidence_version"], post["analysis_evidence_count"]), ("0.8", 44))
        self.assertFalse(self.plan["selection_discipline"]["analysis_write_in_same_transaction"])
        self.assertGreaterEqual(self.readiness["reviewed_occurrence_count"], post["reviewed_occurrence_count"])
        self.assertGreaterEqual(version_tuple(self.reviews["version"]), version_tuple(post["analysis_reviews_version"]))
        self.assertGreaterEqual(len(self.reviews["reviews"]), post["analysis_review_count"])
        self.assertGreaterEqual(version_tuple(self.evidence["version"]), version_tuple(post["analysis_evidence_version"]))
        self.assertGreaterEqual(len(self.evidence["evidence"]), post["analysis_evidence_count"])

    def test_post_state_versions_and_counts_are_exact_or_descendant_safe(self):
        if self.is_post:
            self.assertGreaterEqual(self.post_registry["record_count"], 687)
            self.assertGreaterEqual(len(self.post_sources["sources"]), 242)
            self.assertGreaterEqual(len(self.post_ledger["changes"]), 59)
        else:
            self.assertEqual((self.post_registry["version"], self.post_registry["record_count"]), ("0.37", 687))
            self.assertEqual((self.post_sources["version"], len(self.post_sources["sources"])), ("1.78", 242))
            self.assertEqual((self.post_ledger["version"], len(self.post_ledger["changes"])), ("0.24", 59))
            self.assertEqual(self.post_overlay["version"], "0.12")
            self.assertEqual(self.post_overlay["canonical_checkpoint"], {"registry_version": "0.37", "record_count": 687})

    def test_registry_and_analysis_validate(self):
        rr = validate_registry(self.post_registry, self.post_sources)
        self.assertTrue(rr.ok, rr.errors)
        ar = validate_analysis(self.analysis_schema, self.evidence, self.reviews, self.post_registry)
        self.assertFalse(ar.errors, ar.errors)


if __name__ == "__main__":
    unittest.main()
