from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.apply_who_wha79_historical_anchor_ad import (
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


class WHA79HistoricalAnchorADTests(unittest.TestCase):
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
        p = cls.plan["preconditions"]
        cls.exact_pre = (
            str(cls.canonical.get("version")) == p["canonical_registry_version"]
            and len(cls.canonical.get("records", [])) == p["canonical_record_count"]
            and str(cls.sources.get("version")) == p["source_registry_version"]
            and len(cls.sources.get("sources", [])) == p["source_record_count"]
            and str(cls.ledger.get("version")) == p["change_ledger_version"]
            and len(cls.ledger.get("changes", [])) == p["change_ledger_count"]
            and str(cls.overlay.get("version")) == p["biosecurity_overlay_version"]
            and str(cls.reviews.get("version")) == p["analysis_reviews_version"]
            and len(cls.reviews.get("reviews", [])) == p["analysis_review_count"]
            and str(cls.evidence.get("version")) == p["analysis_evidence_version"]
            and len(cls.evidence.get("evidence", [])) == p["analysis_evidence_count"]
        )
        cls.has_ad = any(
            row.get("occurrence_id") == cls.plan["anchor"]["occurrence_id"]
            for row in cls.canonical.get("records", [])
        )
        if cls.exact_pre:
            (
                cls.post_canonical,
                cls.post_sources,
                cls.post_ledger,
                cls.post_overlay,
                cls.post_readiness,
            ) = build_post_state(
                cls.canonical,
                cls.canonical_schema,
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
            cls.post_canonical = cls.canonical
            cls.post_sources = cls.sources
            cls.post_ledger = cls.ledger
            cls.post_overlay = cls.overlay
            cls.post_readiness = analysis_population_readiness(
                cls.analysis_schema, cls.reviews, cls.canonical
            )
        cls.post_occ = {
            row["occurrence_id"]: row for row in cls.post_canonical.get("records", [])
        }
        cls.post_source = {
            row["source_id"]: row for row in cls.post_sources.get("sources", [])
        }

    def test_plan_is_exact_post_58_and_reuses_existing_wha_series(self):
        self.assertEqual(
            self.plan["base_main_sha"],
            "de352644445d6b5e445aba7793c0e16f5960efc4",
        )
        self.assertEqual(
            (self.plan["preconditions"]["canonical_registry_version"], self.plan["preconditions"]["canonical_record_count"]),
            ("0.32", 682),
        )
        self.assertEqual(self.plan["anchor"]["series_id"], "WSER-HEALTH-WHA")
        self.assertEqual(self.plan["anchor"]["template_occurrence_id"], "WSO-HEALTH-A-0010")
        self.assertFalse(self.plan["selection_discipline"]["new_series_created"])

    def test_authoritative_day_range_does_not_promote_opening_clock(self):
        timing = self.plan["anchor"]["timing"]
        self.assertEqual(timing["timing_type"], "MULTI_DAY_LOCAL")
        self.assertEqual((timing["start_local"], timing["end_local"]), ("2026-05-18", "2026-05-23"))
        self.assertEqual(timing["source_timezone"], "Europe/Zurich")
        self.assertEqual(timing["time_precision"], "DAY")
        self.assertTrue(timing["all_day_semantics"])
        self.assertIsNone(timing["start_utc"])
        self.assertIsNone(timing["end_utc"])
        self.assertNotIn("T09:00", timing["start_local"])
        self.assertFalse(self.plan["selection_discipline"]["opening_session_clock_is_whole_event_time"])

    def test_completion_is_first_party_and_distinct_from_pabs(self):
        anchor = self.post_occ["WSO-HEALTH-WHA-079"]
        self.assertEqual(anchor["lifecycle_status"], "COMPLETED")
        self.assertEqual(anchor["certainty_status"], "CONFIRMED")
        self.assertIn("not inferred from elapsed time", anchor["status_history"][-1]["change_reason"])
        self.assertIn("IGWG/PABS", anchor["notes"])
        self.assertFalse(self.plan["selection_discipline"]["wha_completion_implies_pabs_completion"])
        self.assertEqual(anchor["source_id"], "WSSRC-HEALTH-001")
        self.assertEqual(anchor["related_documents"][0]["source_id"], "WSSRC-HEALTH-006")
        self.assertEqual(anchor["derivation_sources"], ["WSSRC-HEALTH-001", "WSSRC-HEALTH-006"])

    def test_primary_source_dependency_helper_advances_with_canonical_truth(self):
        primary = self.post_source["WSSRC-HEALTH-001"]
        self.assertEqual(primary["canonical_dependency_count"], 7)
        self.assertEqual(actual_primary_dependency_count(self.post_canonical, "WSSRC-HEALTH-001"), 7)
        self.assertEqual(self.plan["preconditions"]["required_primary_source"]["canonical_dependency_count"], 6)
        self.assertEqual(self.plan["preconditions"]["required_primary_source"]["actual_primary_dependency_count"], 6)

    def test_supporting_source_is_nonprimary_and_keeps_conservative_rights_posture(self):
        source = self.post_source["WSSRC-HEALTH-006"]
        self.assertEqual(source["canonical_dependency_count"], 0)
        self.assertEqual(actual_primary_dependency_count(self.post_canonical, "WSSRC-HEALTH-006"), 0)
        self.assertEqual(source["canonical_provenance_use"], "MANUAL_INFORMATIONAL_REFERENCE_ONLY")
        self.assertEqual(source["automated_monitoring_use"], "PROHIBITED_OR_RIGHTS_HOLD")
        self.assertEqual(source["verification_mode"], "RIGHTS_HELD_MANUAL_ONLY")
        self.assertEqual(source["monitor_endpoints"], [])
        self.assertEqual(source["parser_type"], "MANUAL_HISTORICAL_ARCHIVE")
        self.assertFalse(self.plan["selection_discipline"]["supporting_source_becomes_primary_source"])

    def test_exact_prestate_transform_has_tight_mutation_boundaries(self):
        if not self.exact_pre:
            self.skipTest("exact mutation-boundary simulation belongs to AD pre-state")
        self.assertEqual(
            self.post_canonical["records"][: len(self.canonical["records"])],
            self.canonical["records"],
        )
        self.assertEqual(
            self.post_ledger["changes"][: len(self.ledger["changes"])],
            self.ledger["changes"],
        )
        self.assertEqual(overlay_semantics(self.post_overlay), overlay_semantics(self.overlay))

        old_by = {row["source_id"]: row for row in self.sources["sources"]}
        new_by = {row["source_id"]: row for row in self.post_sources["sources"]}
        self.assertEqual(set(new_by) - set(old_by), {"WSSRC-HEALTH-006"})
        for source_id, old in old_by.items():
            new = new_by[source_id]
            if source_id == "WSSRC-HEALTH-001":
                old_copy = copy.deepcopy(old)
                new_copy = copy.deepcopy(new)
                old_copy.pop("canonical_dependency_count")
                new_copy.pop("canonical_dependency_count")
                self.assertEqual(old_copy, new_copy)
                self.assertEqual((old["canonical_dependency_count"], new["canonical_dependency_count"]), (6, 7))
            else:
                self.assertEqual(old, new)

    def test_completed_health_gap_is_repaired_without_analysis_write(self):
        anchor = self.post_occ["WSO-HEALTH-WHA-079"]
        self.assertEqual(anchor["category"], "HEALTH_BIOSECURITY")
        self.assertEqual(anchor["event_type"], "HEALTH_GOVERNANCE_EVENT")
        self.assertGreaterEqual(self.post_readiness["eligible_completed_occurrence_count"], 16)
        self.assertGreaterEqual(self.post_readiness["reviewed_occurrence_count"], 12)
        self.assertNotIn("WSO-HEALTH-WHA-079", set(self.post_readiness["reviewed_occurrence_ids"]))
        report = validate_analysis(self.analysis_schema, self.evidence, self.reviews, self.post_canonical)
        self.assertTrue(report.ok, report.errors)
        self.assertEqual((self.reviews["version"], len(self.reviews["reviews"])), ("0.8", 12))
        self.assertEqual((self.evidence["version"], len(self.evidence["evidence"])), ("0.8", 44))

    def test_canonical_and_source_post_state_validate(self):
        report = validate_registry(self.post_canonical, self.post_sources)
        self.assertTrue(report.ok, report.errors)
        self.assertGreaterEqual(float(self.post_canonical["version"]), 0.33)
        self.assertGreaterEqual(len(self.post_canonical["records"]), 683)
        self.assertGreaterEqual(float(self.post_sources["version"]), 1.74)
        self.assertGreaterEqual(len(self.post_sources["sources"]), 240)

    def test_ledger_records_one_reviewed_historical_admission(self):
        change = next(
            row for row in self.post_ledger["changes"]
            if row.get("change_id") == "WSCHANGE-38d91b77af7e59dfe1"
        )
        self.assertEqual(change["occurrence_id"], "WSO-HEALTH-WHA-079")
        self.assertEqual(change["change_type"], "HISTORICAL_OCCURRENCE_ADMISSION")
        self.assertTrue(change["canonical_mutation_committed"])
        self.assertEqual(change["review_state"], "APPROVED_FOR_CANONICAL_COMMIT")

    def test_selection_guardrails_remain_closed(self):
        self.assertTrue(all(value is False for value in self.plan["selection_discipline"].values()))
        self.assertFalse(self.plan["mutation_policy"]["canonical_schema"])
        self.assertFalse(self.plan["mutation_policy"]["monitor_configuration"])
        self.assertFalse(self.plan["mutation_policy"]["analysis_schema"])
        self.assertFalse(self.plan["mutation_policy"]["analysis_reviews"])
        self.assertFalse(self.plan["mutation_policy"]["analysis_evidence"])
        self.assertFalse(self.plan["mutation_policy"]["calendar"])
        self.assertFalse(self.plan["mutation_policy"]["automatic_canonical_commit"])


if __name__ == "__main__":
    unittest.main()
