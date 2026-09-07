from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/coverage/OPEC_PRIMARY_PROVENANCE_BH_PLAN_v0.1.json"
SCRIPT_PATH = ROOT / "scripts/apply_opec_primary_provenance_bh.py"

spec = importlib.util.spec_from_file_location("opec_primary_bh", SCRIPT_PATH)
bh = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(bh)


class OPECPrimaryProvenanceBHTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        cls.state = bh.load_state()
        cls.materialised = bh.is_materialised(cls.state, cls.plan)
        cls.target_state = cls.state if cls.materialised else bh.simulate(cls.state, cls.plan)

    def test_plan_freezes_exact_post_bg_boundary_and_population_neutral_target(self):
        self.assertEqual(self.plan["exact_base_main_sha"], "eb0845c791133bb8262692c8ebe38ab362dfeff1")
        pre = self.plan["preconditions"]
        post = self.plan["postconditions"]
        self.assertEqual((pre["canonical_registry_version"], pre["canonical_record_count"]), ("0.41", 689))
        self.assertEqual((pre["source_registry_version"], pre["source_record_count"]), ("1.83", 246))
        self.assertEqual((pre["change_ledger_version"], pre["change_ledger_count"]), ("0.27", 62))
        self.assertEqual((post["canonical_registry_version"], post["canonical_record_count"]), ("0.42", 689))
        self.assertEqual((post["source_registry_version"], post["source_record_count"]), ("1.84", 246))
        self.assertEqual((post["change_ledger_version"], post["change_ledger_count"]), ("0.28", 63))
        self.assertEqual(post["analysis_review_count"], 21)
        self.assertEqual(post["live_observation_count"], 6)
        self.assertTrue(self.plan["manual_merge_only"])

    def test_competent_opec_source_is_exactly_the_issuing_authority_route(self):
        selection = self.plan["selection"]
        self.assertEqual(selection["schedule_and_outcome_source_id"], "WSSRC-COM-001")
        self.assertEqual(selection["competent_source_class"], "COMPETENT_ISSUING_AUTHORITY_OPEC")
        self.assertEqual(selection["official_primary_outcome_url"], "https://www.opec.org/pr-detail/613-6-september-2026.html")
        self.assertEqual(selection["current_press_release_index_url"], "https://www.opec.org/press-releases.html")
        self.assertEqual(selection["primary_provenance_state_after"], "SATISFIED_COMPETENT_ISSUING_AUTHORITY")
        self.assertFalse(selection["next_meeting_date_from_outcome_may_create_canonical_occurrence"])

    def test_target_identity_lifecycle_and_time_are_unchanged(self):
        before = bh.by_occurrence(self.state["canonical"])[bh.TARGET_ID]
        after = bh.by_occurrence(self.target_state["canonical"])[bh.TARGET_ID]
        for field in (
            "occurrence_id", "series_id", "source_id", "canonical_name", "category", "event_type",
            "certainty_status", "lifecycle_status", "start_local", "start_utc", "source_timezone",
            "timing_type", "time_precision", "time_status", "intrinsic_importance", "expected_market_sensitivity",
        ):
            self.assertEqual(after.get(field), before.get(field), field)
        self.assertEqual(after["lifecycle_status"], "COMPLETED")
        self.assertEqual(after["start_local"], "2026-09-06")
        self.assertIsNone(after["start_utc"])
        self.assertIsNone(after["source_timezone"])
        self.assertEqual(after["timing_type"], "CIVIL_DATE")

    def test_reuters_and_spa_history_are_preserved_while_opec_primary_is_added(self):
        row = bh.by_occurrence(self.target_state["canonical"])[bh.TARGET_ID]
        reuters = bh.related_rows(row, bh.REUTERS_ID)
        spa = bh.related_rows(row, bh.SPA_ID)
        opec = bh.related_rows(row, bh.OPEC_ID)
        self.assertTrue(any(doc.get("role") == "COMPLETION_FALLBACK_VERIFICATION_PRIMARY_PENDING" for doc in reuters))
        self.assertTrue(any(doc.get("role") == "OFFICIAL_PARTICIPATING_GOVERNMENT_COMPLETION_CONFIRMATION_PRIMARY_OPEC_PENDING" for doc in spa))
        self.assertTrue(any(doc.get("primary_opec_provenance_state") == "REQUIRED_WHEN_RETRIEVABLE" for doc in spa))
        recovered = [doc for doc in opec if doc.get("role") == "COMPETENT_OPEC_PRIMARY_OUTCOME_PROVENANCE_RECOVERED"]
        self.assertEqual(len(recovered), 1)
        self.assertEqual(recovered[0]["source_locator"], self.plan["selection"]["official_primary_outcome_url"])
        self.assertEqual(recovered[0]["primary_opec_provenance_state"], "SATISFIED_COMPETENT_ISSUING_AUTHORITY")

    def test_source_route_repairs_do_not_open_automation_rights(self):
        before = bh.by_source(self.state["sources"])
        after = bh.by_source(self.target_state["sources"])
        self.assertEqual(after[bh.OPEC_ID]["authoritative_url"], "https://www.opec.org/press-releases.html")
        self.assertEqual(after[bh.OPEC_ID]["automated_monitoring_use"], "PROHIBITED_OR_RIGHTS_HOLD")
        self.assertEqual(after[bh.SPA_ID]["automated_monitoring_use"], "PROHIBITED_OR_RIGHTS_HOLD")
        for sid in (bh.OPEC_ID, bh.SPA_ID):
            for field in (
                "source_id", "institution", "canonical_dependency_count", "canonical_provenance_use",
                "automated_monitoring_use", "automated_retrieval_permission", "verification_mode",
                "ingestion_permission", "redistribution_permission", "licence_review_status",
            ):
                self.assertEqual(after[sid].get(field), before[sid].get(field), f"{sid}.{field}")

    def test_current_spa_source_text_records_recovery_not_a_current_pending_debt(self):
        source = bh.by_source(self.target_state["sources"])[bh.SPA_ID]
        self.assertFalse(bh.current_spa_pending(source))
        self.assertIn("BH subsequently recovered competent OPEC", source["information_supplied"])
        self.assertIn("SPA remains supporting evidence", source["notes"])

    def test_exact_simulation_changes_one_canonical_occurrence_and_two_source_objects(self):
        if self.materialised:
            self.skipTest("exact BH transform belongs to exact post-BG prestate")
        before_c = bh.by_occurrence(self.state["canonical"])
        after_c = bh.by_occurrence(self.target_state["canonical"])
        self.assertEqual([oid for oid in before_c if before_c[oid] != after_c[oid]], [bh.TARGET_ID])
        changed_fields = {key for key in set(before_c[bh.TARGET_ID]) | set(after_c[bh.TARGET_ID]) if before_c[bh.TARGET_ID].get(key) != after_c[bh.TARGET_ID].get(key)}
        self.assertEqual(changed_fields, {"last_successful_assertion_id", "last_verified_at", "related_documents"})
        before_s = bh.by_source(self.state["sources"])
        after_s = bh.by_source(self.target_state["sources"])
        self.assertEqual({sid for sid in before_s if before_s[sid] != after_s[sid]}, {bh.OPEC_ID, bh.SPA_ID})

    def test_change_ledger_records_primary_recovery_without_new_event_state(self):
        matches = [row for row in self.target_state["ledger"]["changes"] if row.get("change_id") == self.plan["provenance_basis"]["change_id"]]
        self.assertEqual(len(matches), 1)
        row = matches[0]
        self.assertEqual(row["change_type"], "SOURCE_PROVENANCE_STRENGTHENING")
        self.assertEqual(row["old_values"]["primary_opec_provenance_state"], "REQUIRED_WHEN_RETRIEVABLE")
        self.assertEqual(row["new_values"]["primary_opec_provenance_state"], "SATISFIED_COMPETENT_ISSUING_AUTHORITY")
        self.assertTrue(row["new_values"]["reuters_fallback_preserved"])
        self.assertTrue(row["new_values"]["spa_confirmation_preserved"])
        self.assertFalse(row["automatic_canonical_commit"])
        self.assertFalse(row["google_calendar_write"])

    def test_live_analysis_monitor_populations_and_gates_remain_unchanged(self):
        target = self.target_state
        self.assertEqual(target["expectations"], self.state["expectations"])
        self.assertEqual(target["live_schema"], self.state["live_schema"])
        self.assertEqual(target["live_observations"], self.state["live_observations"])
        self.assertEqual(target["live_evidence"], self.state["live_evidence"])
        self.assertEqual(target["analysis_schema"], self.state["analysis_schema"])
        self.assertEqual(target["analysis_reviews"], self.state["analysis_reviews"])
        self.assertEqual(target["analysis_evidence"], self.state["analysis_evidence"])
        self.assertEqual(bh.production_live_input_count(target["analysis_reviews"]), 1)
        self.assertEqual(bh.revision_count(target["analysis_reviews"]), 0)
        self.assertEqual(bh.exact_series_count(target["analysis_reviews"]), 0)
        readiness = bh.analysis_population_readiness(target["analysis_schema"], target["analysis_reviews"], target["canonical"])
        self.assertEqual(readiness["eligible_completed_occurrence_count"], 22)
        self.assertEqual(readiness["reviewed_occurrence_count"], 21)

    def test_bh_does_not_create_october_voluntary_adjustment_occurrence(self):
        rows = [
            row for row in self.target_state["canonical"]["records"]
            if row.get("series_id") == "WSER-COM-OPEC-VOL" and str(row.get("start_local", "")).startswith("2026-10-04")
        ]
        self.assertEqual(rows, [])

    def test_status_roadmap_and_historical_bg_contract_can_coexist(self):
        status = bh.target_status(bh.STATUS_PATH.read_text(encoding="utf-8"), self.plan)
        roadmap = bh.target_roadmap(bh.ROADMAP_PATH.read_text(encoding="utf-8"))
        self.assertIn("BH OPEC COMPETENT-PRIMARY PROVENANCE RECOVERY", status)
        self.assertIn("v0.42 / 689 occurrences", status)
        self.assertIn("v1.84 / 246 sources", status)
        self.assertIn("OPEC competent-primary provenance recovery", roadmap)
        bg_plan = json.loads((ROOT / "data/coverage/OPEC_OFFICIAL_CONFIRMATION_BG_PLAN_v0.1.json").read_text(encoding="utf-8"))
        self.assertEqual(bg_plan["provenance_basis"]["primary_opec_provenance_state"], "REQUIRED_WHEN_RETRIEVABLE")
        self.assertTrue(bg_plan["historical_preservation"]["competent_opec_primary_remains_pending"])

    def test_materialised_or_simulated_target_validates(self):
        bh.assert_downstream(self.target_state, self.plan)
        if self.materialised:
            bh.assert_materialised(self.state, self.plan)
        else:
            bh.assert_poststate(self.state, self.target_state, self.plan)

    def test_helper_cli_check_only_is_available(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--check-only"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        if not self.materialised:
            self.assertIn('"primary_opec_provenance_state": "SATISFIED_COMPETENT_ISSUING_AUTHORITY"', proc.stdout)


if __name__ == "__main__":
    unittest.main()
