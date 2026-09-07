from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import apply_opec_primary_provenance_bh as bh


class OPECPrimaryProvenanceBHTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = bh.load(bh.PLAN_PATH)
        cls.state = bh.load_state()
        cls.materialised = bh.is_materialised(cls.state, cls.plan)
        cls.target = cls.state if cls.materialised else bh.build_post_state(
            cls.state, cls.plan, "2026-09-08T01:00:00+10:00"
        )

    def test_plan_freezes_exact_post_bg_prestate_and_population_neutral_target(self):
        self.assertEqual(self.plan["exact_base_main_sha"], "eb0845c791133bb8262692c8ebe38ab362dfeff1")
        pre = self.plan["preconditions"]
        post = self.plan["postconditions"]
        self.assertEqual((pre["canonical_registry_version"], pre["canonical_record_count"]), ("0.41", 689))
        self.assertEqual((pre["source_registry_version"], pre["source_record_count"]), ("1.83", 246))
        self.assertEqual((pre["change_ledger_version"], pre["change_ledger_count"]), ("0.27", 62))
        self.assertEqual((post["canonical_registry_version"], post["canonical_record_count"]), ("0.42", 689))
        self.assertEqual((post["source_registry_version"], post["source_record_count"]), ("1.83", 246))
        self.assertEqual((post["change_ledger_version"], post["change_ledger_count"]), ("0.28", 63))
        self.assertTrue(self.plan["manual_merge_only"])

    def test_competent_opec_primary_reuses_existing_source_identity(self):
        selection = self.plan["selection"]
        self.assertEqual(selection["competent_source_id"], "WSSRC-COM-001")
        self.assertEqual(selection["official_outcome_class"], "COMPETENT_ISSUING_INSTITUTION_PRIMARY_OUTCOME")
        self.assertEqual(selection["official_outcome_event_date"], "2026-09-06")
        self.assertEqual(
            selection["official_outcome_url"],
            "https://www.opec.org/pr-detail/613-6-september-2026.html",
        )
        self.assertEqual(len(self.target["sources"]["sources"]), len(self.state["sources"]["sources"]))
        self.assertEqual(self.target["sources"], self.state["sources"])

    def test_event_time_remains_civil_date_with_no_manufactured_timestamp(self):
        contract = self.plan["event_time_contract"]
        self.assertEqual(contract["timing_type"], "CIVIL_DATE")
        self.assertEqual(contract["start_local"], "2026-09-06")
        self.assertIsNone(contract["start_utc"])
        self.assertIsNone(contract["source_timezone"])
        self.assertFalse(contract["publication_metadata_promoted_to_event_time"])
        row = bh.by_occurrence(self.target["canonical"])[bh.TARGET_ID]
        self.assertEqual(row["start_local"], "2026-09-06")
        self.assertIsNone(row["start_utc"])
        self.assertIsNone(row["source_timezone"])
        self.assertEqual(row["timing_type"], "CIVIL_DATE")
        self.assertEqual(row["time_precision"], "DAY")

    def test_reuters_and_spa_historical_provenance_are_preserved_byte_for_byte(self):
        before = bh.by_occurrence(self.state["canonical"])[bh.TARGET_ID]
        after = bh.by_occurrence(self.target["canonical"])[bh.TARGET_ID]
        self.assertEqual(bh.related_rows(after, bh.REUTERS_ID), bh.related_rows(before, bh.REUTERS_ID))
        self.assertEqual(bh.related_rows(after, bh.SPA_ID), bh.related_rows(before, bh.SPA_ID))
        self.assertEqual(
            bh.related_rows(after, bh.SPA_ID)[0]["primary_opec_provenance_state"],
            "REQUIRED_WHEN_RETRIEVABLE",
        )

    def test_competent_opec_related_document_satisfies_later_requirement(self):
        row = bh.by_occurrence(self.target["canonical"])[bh.TARGET_ID]
        docs = [
            item for item in bh.related_rows(row, bh.OPEC_ID)
            if item.get("role") == self.plan["provenance_basis"]["related_document_role"]
        ]
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["source_locator"], self.plan["selection"]["official_outcome_url"])
        self.assertEqual(
            docs[0]["primary_opec_provenance_state"],
            "SATISFIED_BY_COMPETENT_OPEC_PRIMARY",
        )

    def test_only_target_provenance_fields_change_in_exact_bh_simulation(self):
        if self.materialised:
            self.skipTest("Exact BH mutation simulation belongs to the frozen post-BG prestate.")
        before = bh.by_occurrence(self.state["canonical"])
        after = bh.by_occurrence(self.target["canonical"])
        changed = [oid for oid in before if before[oid] != after[oid]]
        self.assertEqual(changed, [bh.TARGET_ID])
        t0, t1 = before[bh.TARGET_ID], after[bh.TARGET_ID]
        fields = {k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
        self.assertEqual(fields, {"last_successful_assertion_id", "related_documents"})
        bh.assert_exact_poststate(self.state, self.target, self.plan)

    def test_change_ledger_records_primary_recovery_without_write_gate_change(self):
        matches = [
            row for row in self.target["ledger"]["changes"]
            if row.get("change_id") == self.plan["provenance_basis"]["change_id"]
        ]
        self.assertEqual(len(matches), 1)
        change = matches[0]
        self.assertEqual(change["change_type"], "SOURCE_PROVENANCE_PRIMARY_RECOVERY")
        self.assertEqual(
            change["new_values"]["primary_opec_provenance_state"],
            "SATISFIED_BY_COMPETENT_OPEC_PRIMARY",
        )
        self.assertTrue(change["new_values"]["reuters_fallback_preserved"])
        self.assertTrue(change["new_values"]["spa_confirmation_preserved"])
        self.assertFalse(change["automatic_canonical_commit"])
        self.assertFalse(change["google_calendar_write"])

    def test_monitor_live_analysis_and_source_populations_do_not_change(self):
        for key in (
            "sources", "canonical_schema", "expectations", "operations", "review_contract",
            "review_decisions", "live_schema", "live_observations", "live_evidence",
            "analysis_schema", "analysis_reviews", "analysis_evidence",
        ):
            self.assertEqual(self.target[key], self.state[key], key)

    def test_no_october_voluntary_adjustment_occurrence_is_created(self):
        matches = [
            row for row in self.target["canonical"]["records"]
            if row.get("series_id") == self.plan["selection"]["series_id"]
            and str(row.get("start_local", "")).startswith("2026-10-04")
        ]
        self.assertEqual(matches, [])

    def test_status_and_roadmap_mark_primary_gap_closed_without_downstream_population(self):
        status = bh.target_status(bh.STATUS_PATH.read_text(encoding="utf-8"), self.plan)
        roadmap = bh.target_roadmap(bh.ROADMAP_PATH.read_text(encoding="utf-8"))
        self.assertIn("BH OPEC COMPETENT-PRIMARY PROVENANCE RECOVERY", status)
        self.assertIn("v0.42 / 689 occurrences", status)
        self.assertIn("v1.83 / 246 sources", status)
        self.assertIn("BH — OPEC competent-primary provenance recovery — DONE", roadmap)
        self.assertIn("A standalone OPEC Analysis review remains a separate future pressure decision", roadmap)

    def test_materialised_or_simulated_target_validates(self):
        if self.materialised:
            bh.assert_materialised_or_descendant(self.state, self.plan)
        else:
            bh.validate_layers(self.target)


if __name__ == "__main__":
    unittest.main()
