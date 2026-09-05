import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.apply_australian_tropical_cyclone_season_anchor_af import (
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


class AustralianTropicalCycloneSeasonAnchorAFTests(unittest.TestCase):
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
        cls.is_post = any(row.get("occurrence_id") == cls.oid for row in cls.registry.get("records", []))
        if cls.is_post:
            cls.post_registry = cls.registry
            cls.post_sources = cls.sources
            cls.post_ledger = cls.ledger
            cls.post_overlay = cls.overlay
            cls.readiness = analysis_population_readiness(cls.analysis_schema, cls.reviews, cls.post_registry)
        else:
            (
                cls.post_registry,
                cls.post_sources,
                cls.post_ledger,
                cls.post_overlay,
                cls.readiness,
            ) = build_post_state(
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

    def test_plan_is_exact_post_60_and_reuses_existing_series_source(self):
        self.assertEqual(self.plan["exact_base_main"], "e576719bcbaf94730444cf64b1a1abeeacb25727")
        item = self.plan["anchor"]
        self.assertEqual(item["occurrence_id"], "WSO-RISK-AU-TC-2025-26")
        self.assertEqual(item["series_id"], "WSER-RISK-AU-TC")
        self.assertEqual(item["source_id"], "WSSRC-RISK-001")
        self.assertFalse(self.plan["source_mutation"]["new_source_identity_allowed"])

    def test_regional_season_preserves_source_native_window_without_timezone_invention(self):
        row = next(row for row in self.post_registry["records"] if row.get("occurrence_id") == self.oid)
        self.assertEqual(row["timing_type"], "ALL_DAY_RANGE")
        self.assertEqual(row["start_local"], "2025-11-01")
        self.assertEqual(row["end_local"], "2026-04-30")
        self.assertEqual(row["time_precision"], "DAY")
        self.assertTrue(row["all_day_semantics"])
        self.assertIsNone(row["source_timezone"])
        self.assertIsNone(row["start_utc"])
        self.assertIsNone(row["end_utc"])
        source = next(row for row in self.post_sources["sources"] if row.get("source_id") == "WSSRC-RISK-001")
        self.assertEqual(source["source_timezone"], "Australia/Brisbane")

    def test_completion_requires_bureau_post_season_evidence_not_elapsed_time(self):
        row = next(row for row in self.post_registry["records"] if row.get("occurrence_id") == self.oid)
        self.assertEqual(row["lifecycle_status"], "COMPLETED")
        self.assertEqual(row["certainty_status"], "CONFIRMED")
        self.assertIn("14 May 2026", row["notes"])
        self.assertIn("not inferred from elapsed time alone", row["notes"])
        self.assertEqual(row["related_documents"], [{
            "source_id": "WSSRC-RISK-001",
            "role": "COMPLETION_OUTCOME_VERIFICATION",
            "source_locator": "https://www.bom.gov.au/climate/current/season/tropics/summary.shtml",
        }])

    def test_risk_window_is_not_promoted_to_named_cyclone_or_market_effect(self):
        row = next(row for row in self.post_registry["records"] if row.get("occurrence_id") == self.oid)
        self.assertEqual(row["category"], "PHYSICAL_CLIMATE_RISK")
        self.assertEqual(row["event_type"], "PHYSICAL_RISK_WINDOW")
        self.assertEqual(row["record_class"], "PHYSICAL_RISK_WINDOW")
        self.assertEqual(row["signal_object_class"], "PHYSICAL_RISK_WINDOW")
        self.assertEqual(row["physical_shock_routing"], "ROUTE_ACTUAL_EVENT_TO_SHOCK_REGISTER")
        self.assertIsNone(row["observed_market_response"])
        self.assertIn("individual tropical cyclone occurrence", row["notes"])
        self.assertIn("climate-change attribution", row["notes"])

    def test_only_one_canonical_record_is_added_in_simulation(self):
        if self.is_post:
            self.skipTest("exact add-only comparison belongs to AF pre-state simulation")
        old_ids = {row["occurrence_id"] for row in self.registry["records"]}
        new_ids = {row["occurrence_id"] for row in self.post_registry["records"]}
        self.assertEqual(new_ids - old_ids, {self.oid})
        self.assertEqual(old_ids - new_ids, set())

    def test_future_australian_season_descendants_are_unchanged(self):
        if self.is_post:
            by_id = {row["occurrence_id"]: row for row in self.post_registry["records"]}
            self.assertEqual(by_id["WSO-COM-A-0051"]["canonical_name"], "Australian tropical cyclone season 2026–27")
            self.assertEqual(by_id["WSO-COM-A-0052"]["canonical_name"], "Australian tropical cyclone season 2027–28")
            return
        old = {row["occurrence_id"]: row for row in self.registry["records"]}
        new = {row["occurrence_id"]: row for row in self.post_registry["records"]}
        for oid in ("WSO-COM-A-0051", "WSO-COM-A-0052"):
            self.assertEqual(old[oid], new[oid])

    def test_active_atlantic_2026_season_remains_active(self):
        row = next(row for row in self.post_registry["records"] if row.get("occurrence_id") == "WSO-COM-A-0049")
        self.assertEqual(row["series_id"], "WSER-RISK-ATL-HURR")
        self.assertEqual(row["lifecycle_status"], "ACTIVE")
        self.assertEqual(row["end_local"], "2026-11-30")

    def test_source_dependency_helper_advances_exactly_one(self):
        source = next(row for row in self.post_sources["sources"] if row.get("source_id") == "WSSRC-RISK-001")
        self.assertEqual(source["canonical_dependency_count"], 3)
        self.assertEqual(actual_primary_dependency_count(self.post_registry, "WSSRC-RISK-001"), 3)

    def test_no_other_source_record_changes_in_exact_simulation(self):
        if self.is_post:
            self.skipTest("exact source mutation comparison belongs to AF pre-state simulation")
        old = {row["source_id"]: row for row in self.sources["sources"]}
        new = {row["source_id"]: row for row in self.post_sources["sources"]}
        self.assertEqual(set(old), set(new))
        changed = [source_id for source_id in old if old[source_id] != new[source_id]]
        self.assertEqual(changed, ["WSSRC-RISK-001"])
        before = copy.deepcopy(old["WSSRC-RISK-001"])
        after = copy.deepcopy(new["WSSRC-RISK-001"])
        self.assertEqual(before.pop("canonical_dependency_count"), 2)
        self.assertEqual(after.pop("canonical_dependency_count"), 3)
        self.assertEqual(before, after)

    def test_physical_risk_gap_repaired_without_analysis_write(self):
        self.assertTrue(any(
            row.get("category") == "PHYSICAL_CLIMATE_RISK" and row.get("lifecycle_status") == "COMPLETED"
            for row in self.post_registry["records"]
        ))
        self.assertTrue(any(
            row.get("event_type") == "PHYSICAL_RISK_WINDOW" and row.get("lifecycle_status") == "COMPLETED"
            for row in self.post_registry["records"]
        ))
        self.assertEqual(self.readiness["eligible_completed_occurrence_count"], 18)
        self.assertEqual(self.readiness["reviewed_occurrence_count"], 12)
        self.assertEqual(len(self.reviews["reviews"]), 12)
        self.assertEqual(len(self.evidence["evidence"]), 44)

    def test_post_state_counts_are_exact(self):
        self.assertEqual((self.post_registry["version"], self.post_registry["record_count"]), ("0.35", 685))
        self.assertEqual((self.post_sources["version"], len(self.post_sources["sources"])), ("1.76", 240))
        self.assertEqual((self.post_ledger["version"], len(self.post_ledger["changes"])), ("0.22", 57))
        self.assertEqual(self.post_overlay["version"], "0.10")
        self.assertEqual(self.post_overlay["canonical_checkpoint"], {"registry_version": "0.35", "record_count": 685})

    def test_overlay_semantics_are_unchanged_in_simulation(self):
        if self.is_post:
            self.assertEqual(self.post_overlay["version"], "0.10")
        else:
            self.assertEqual(overlay_semantics(self.overlay), overlay_semantics(self.post_overlay))

    def test_registry_and_analysis_validate(self):
        registry_report = validate_registry(self.post_registry, self.post_sources)
        self.assertTrue(registry_report.ok, registry_report.errors)
        analysis_report = validate_analysis(self.analysis_schema, self.evidence, self.reviews, self.post_registry)
        self.assertFalse(analysis_report.errors, analysis_report.errors)


if __name__ == "__main__":
    unittest.main()
