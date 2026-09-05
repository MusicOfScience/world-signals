from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.apply_south_korea_local_election_anchor_ag import (
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
    overlay_semantics,
)
from src.world_signals.analysis import analysis_population_readiness, validate_analysis
from src.world_signals.validation import validate_registry


def version_tuple(raw):
    return tuple(int(part) for part in str(raw).split("."))


class SouthKoreaLocalElectionAnchorAGTests(unittest.TestCase):
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
        cls.sid = cls.plan["anchor"]["source_id"]
        cls.series_id = cls.plan["anchor"]["series_id"]
        cls.is_post = any(row.get("occurrence_id") == cls.oid for row in cls.registry.get("records", []))
        if cls.is_post:
            cls.post_registry = cls.registry
            cls.post_sources = cls.sources
            cls.post_ledger = cls.ledger
            cls.post_overlay = cls.overlay
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
                "2026-09-06T09:00:00+10:00",
            )

    def anchor(self):
        return next(row for row in self.post_registry["records"] if row.get("occurrence_id") == self.oid)

    def source(self):
        return next(row for row in self.post_sources["sources"] if row.get("source_id") == self.sid)

    def test_plan_is_exact_post_61_and_reuses_existing_election_taxonomy(self):
        self.assertEqual(self.plan["exact_base_main"], "3ebd01e1f6f3ba2b09343f238f3ac72262484391")
        self.assertEqual(self.plan["preconditions"]["canonical_registry_version"], "0.35")
        self.assertEqual(self.plan["preconditions"]["canonical_record_count"], 685)
        template = self.plan["preconditions"]["required_template"]
        self.assertEqual(template["subcategory"], "local_government_election")
        self.assertEqual(template["event_type"], "ELECTION_MILESTONE")
        self.assertEqual(self.schema["version"], "0.52")

    def test_new_identity_is_one_clean_south_korea_election_series(self):
        rows = [row for row in self.post_registry["records"] if row.get("series_id") == self.series_id]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["occurrence_id"], "WSO-EL-KR-LGE-20260603")
        self.assertEqual(row["jurisdiction"], "South Korea")
        self.assertEqual(row["region"], "East Asia")
        self.assertEqual(row["institution"], "National Election Commission of the Republic of Korea")
        self.assertNotIn("South Africa", json.dumps(row, ensure_ascii=False))

    def test_election_day_is_civil_date_not_polling_hours(self):
        row = self.anchor()
        self.assertEqual(row["timing_type"], "CIVIL_DATE")
        self.assertEqual(row["start_local"], "2026-06-03")
        self.assertIsNone(row["end_local"])
        self.assertEqual(row["source_timezone"], "Asia/Seoul")
        self.assertIsNone(row["start_utc"])
        self.assertIsNone(row["end_utc"])
        self.assertEqual(row["time_precision"], "DAY")
        self.assertTrue(row["all_day_semantics"])
        self.assertEqual(row["time_status"], "CONFIRMED")
        self.assertEqual(row["time_basis"], "EXPLICIT_AUTHORITATIVE_SCHEDULE")
        self.assertNotEqual(row["start_local"], "2026-06-03T06:00:00")

    def test_early_voting_is_not_promoted_into_election_day_timing(self):
        row = self.anchor()
        self.assertNotEqual(row["start_local"], "2026-05-29")
        self.assertNotEqual(row.get("end_local"), "2026-05-30")
        self.assertIn("early voting", row["notes"].lower())
        self.assertIn("not canonical election-day clock time", row["notes"])

    def test_completion_is_first_party_and_not_elapsed_time(self):
        row = self.anchor()
        self.assertEqual(row["lifecycle_status"], "COMPLETED")
        self.assertEqual(row["certainty_status"], "CONFIRMED")
        docs = {doc["role"]: doc for doc in row["related_documents"]}
        self.assertIn("AUTHORITATIVE_SCHEDULE_VERIFICATION", docs)
        self.assertIn("COMPLETION_OUTCOME_VERIFICATION", docs)
        self.assertEqual(docs["COMPLETION_OUTCOME_VERIFICATION"]["source_locator"], "https://policy.nec.go.kr/plc/main/initUMAMain.do")
        self.assertIn("not inferred from elapsed time", row["status_history"][-1]["change_reason"])

    def test_nationwide_event_is_not_a_synthetic_single_result(self):
        row = self.anchor()
        text = (row["notes"] + " " + self.plan["anchor"]["semantic_guardrail"]).lower()
        self.assertIn("individual local contests", text)
        self.assertIn("government formation", text)
        self.assertNotIn("national winner:", text)
        self.assertEqual(sum(1 for r in self.post_registry["records"] if r.get("series_id") == self.series_id), 1)

    def test_importance_and_expected_market_sensitivity_are_separate(self):
        row = self.anchor()
        self.assertEqual(row["intrinsic_importance"], "HIGH")
        self.assertEqual(row["expected_market_sensitivity"], "MEDIUM")
        self.assertIsNone(row.get("observed_market_response"))

    def test_new_source_is_conservatively_governed(self):
        source = self.source()
        self.assertEqual(source["canonical_provenance_use"], "CLEARED_CURATED_FACTUAL_METADATA")
        self.assertEqual(source["automated_monitoring_use"], "ENDPOINT_REVIEW_REQUIRED")
        self.assertEqual(source["verification_mode"], "MANUAL_AUTHORITATIVE_RECHECK")
        self.assertEqual(source["canonical_dependency_count"], 1)
        self.assertEqual(source["source_timezone"], "Asia/Seoul")
        self.assertIn("KOGL", source["licence_constraints"])
        self.assertIn("do not establish production crawler permission", source["automation_summary"])

    def test_new_source_dependency_helper_matches_canonical_truth(self):
        source = self.source()
        actual = sum(1 for row in self.post_registry["records"] if row.get("source_id") == self.sid)
        self.assertEqual(actual, 1)
        self.assertEqual(source["canonical_dependency_count"], actual)

    def test_preexisting_sources_are_unchanged_in_exact_simulation(self):
        if self.is_post:
            self.skipTest("exact source append boundary belongs to AG pre-state simulation")
        self.assertEqual(self.post_sources["sources"][:-1], self.sources["sources"])
        self.assertEqual(len(self.post_sources["sources"]), len(self.sources["sources"]) + 1)

    def test_overlay_semantics_are_unchanged(self):
        if self.is_post:
            self.assertGreaterEqual(version_tuple(self.post_overlay["version"]), version_tuple("0.11"))
            self.assertGreaterEqual(self.post_overlay["canonical_checkpoint"]["record_count"], 686)
            return
        self.assertEqual(overlay_semantics(self.overlay), overlay_semantics(self.post_overlay))
        self.assertEqual(self.post_overlay["canonical_checkpoint"], {"registry_version": "0.36", "record_count": 686})

    def test_analysis_population_expands_without_analysis_write(self):
        readiness = analysis_population_readiness(self.analysis_schema, self.reviews, self.post_registry)
        self.assertGreaterEqual(readiness["eligible_completed_occurrence_count"], 19)

        # AG's historical transaction contract held Analysis fixed at v0.8 / 12
        # reviews / 44 evidence. Descendant Analysis tranches may grow those
        # registries without changing the fact that AG itself wrote no Analysis.
        post = self.plan["postconditions"]
        self.assertEqual((post["analysis_reviews_version"], post["analysis_review_count"]), ("0.8", 12))
        self.assertEqual((post["analysis_evidence_version"], post["analysis_evidence_count"]), ("0.8", 44))
        self.assertIn("No Analysis review or evidence row is created.", self.plan["guardrails"])
        self.assertGreaterEqual(readiness["reviewed_occurrence_count"], post["reviewed_completed_count"])
        self.assertGreaterEqual(version_tuple(self.reviews["version"]), version_tuple(post["analysis_reviews_version"]))
        self.assertGreaterEqual(len(self.reviews["reviews"]), post["analysis_review_count"])
        self.assertGreaterEqual(version_tuple(self.evidence["version"]), version_tuple(post["analysis_evidence_version"]))
        self.assertGreaterEqual(len(self.evidence["evidence"]), post["analysis_evidence_count"])

    def test_completed_elections_governance_gap_is_repaired(self):
        completed = [row for row in self.post_registry["records"] if row.get("lifecycle_status") == "COMPLETED"]
        self.assertTrue(any(row.get("category") == "ELECTIONS_GOVERNANCE" for row in completed))
        self.assertTrue(any(row.get("event_type") == "ELECTION_MILESTONE" for row in completed))

    def test_post_state_versions_and_counts_are_exact_or_descendant_safe(self):
        if not self.is_post:
            self.assertEqual((self.post_registry["version"], self.post_registry["record_count"]), ("0.36", 686))
            self.assertEqual((self.post_sources["version"], len(self.post_sources["sources"])), ("1.77", 241))
            self.assertEqual((self.post_ledger["version"], len(self.post_ledger["changes"])), ("0.23", 58))
            self.assertEqual(self.post_overlay["version"], "0.11")
            return
        self.assertGreaterEqual(version_tuple(self.post_registry["version"]), version_tuple("0.36"))
        self.assertGreaterEqual(self.post_registry["record_count"], 686)
        self.assertGreaterEqual(version_tuple(self.post_sources["version"]), version_tuple("1.77"))
        self.assertGreaterEqual(len(self.post_sources["sources"]), 241)
        self.assertGreaterEqual(version_tuple(self.post_ledger["version"]), version_tuple("0.23"))
        self.assertGreaterEqual(len(self.post_ledger["changes"]), 58)

    def test_registry_and_analysis_validate(self):
        report = validate_registry(self.post_registry, self.post_sources)
        self.assertTrue(report.ok, report.errors)
        analysis = validate_analysis(self.analysis_schema, self.evidence, self.reviews, self.post_registry)
        self.assertFalse(analysis.errors, analysis.errors)


if __name__ == "__main__":
    unittest.main()
