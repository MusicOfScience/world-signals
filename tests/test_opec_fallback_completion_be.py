from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts import apply_opec_fallback_completion_be as be
from world_signals.analysis import analysis_population_readiness
from world_signals.checkpoint_contract import version_at_least


class OpecFallbackCompletionBETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads((ROOT / "data/coverage/OPEC_FALLBACK_COMPLETION_BE_PLAN_v0.1.json").read_text())
        cls.state = be.load_all()

    def _is_pre_state(self) -> bool:
        return str(self.state["canonical"].get("version")) == self.plan["preconditions"]["canonical_registry_version"]

    def _post_state(self) -> dict[str, dict]:
        if self._is_pre_state():
            return be.build_post_state(self.state, self.plan, "2026-09-07T00:30:00+10:00")
        return self.state

    def test_plan_is_exactly_one_existing_occurrence_and_one_fallback_source(self):
        self.assertEqual(self.plan["selection"]["occurrence_id"], "WSO-COM-A-0001")
        self.assertEqual(self.plan["selection"]["series_id"], "WSER-COM-OPEC-VOL")
        self.assertEqual(self.plan["selection"]["schedule_source_id"], "WSSRC-COM-001")
        self.assertEqual(self.plan["selection"]["completion_source_id"], "WSSRC-COM-015")
        self.assertTrue(self.plan["selection"]["primary_upgrade_required_when_retrievable"])
        self.assertFalse(self.plan["selection"]["next_meeting_date_from_fallback_may_create_canonical_occurrence"])
        self.assertTrue(self.plan["manual_merge_only"])

    def test_pressure_audit_preserves_source_hierarchy_and_rejects_october_creation(self):
        text = (ROOT / "data/coverage/POST_BD_PRESSURE_AUDIT_BE_v0.1.md").read_text()
        self.assertIn("OPEC 6 September lifecycle completion — SELECTED", text)
        self.assertIn("Create the Reuters-reported 4 October next meeting — REJECTED", text)
        self.assertIn("reputable newswire when primary material is unavailable", text)
        self.assertIn("not a target to fill", text)

    def test_pre_or_post_state_has_stable_opec_identity(self):
        if self._is_pre_state():
            be.preflight(self.state, self.plan)
            row = be.by_occurrence(self.state["canonical"])[be.TARGET_ID]
            self.assertEqual(row["lifecycle_status"], "PLANNED")
            self.assertNotIn(be.COMPLETION_SOURCE_ID, be.by_source(self.state["sources"]))
        else:
            post = self.plan["postconditions"]
            self.assertTrue(
                version_at_least(
                    str(self.state["canonical"].get("version")),
                    post["canonical_registry_version"],
                )
            )
            self.assertGreaterEqual(
                len(self.state["canonical"]["records"]),
                post["canonical_record_count"],
            )
            row = be.by_occurrence(self.state["canonical"])[be.TARGET_ID]
            self.assertEqual(row["lifecycle_status"], "COMPLETED")
            self.assertEqual(row["series_id"], "WSER-COM-OPEC-VOL")
            self.assertEqual(row["source_id"], "WSSRC-COM-001")
            self.assertEqual(row["start_local"], "2026-09-06")
            self.assertIsNone(row["start_utc"])
            self.assertIsNone(row["source_timezone"])
            self.assertEqual(row["timing_type"], "CIVIL_DATE")
            self.assertEqual(row["time_precision"], "DAY")

    def test_simulated_post_state_changes_only_authorised_canonical_fields(self):
        if not self._is_pre_state():
            self.skipTest("Exact mutation simulation belongs to the post-BD pre-state.")
        post = be.build_post_state(self.state, self.plan, "2026-09-07T00:30:00+10:00")
        before = be.by_occurrence(self.state["canonical"])
        after = be.by_occurrence(post["canonical"])
        changed = [oid for oid in before if before[oid] != after[oid]]
        self.assertEqual(changed, [be.TARGET_ID])
        changed_fields = {
            k for k in set(before[be.TARGET_ID]) | set(after[be.TARGET_ID])
            if before[be.TARGET_ID].get(k) != after[be.TARGET_ID].get(k)
        }
        self.assertEqual(
            changed_fields,
            {"lifecycle_status", "last_verified_at", "last_successful_assertion_id", "status_history", "related_documents"},
        )
        self.assertIsNone(after[be.TARGET_ID]["start_utc"])
        self.assertEqual(after[be.TARGET_ID]["start_local"], before[be.TARGET_ID]["start_local"])

    def test_fallback_source_is_secondary_completion_only_and_nonautomated(self):
        post = self._post_state()
        source = be.by_source(post["sources"])[be.COMPLETION_SOURCE_ID]
        self.assertEqual(source["institution"], "Reuters")
        self.assertEqual(source["source_type"], "reputable_newswire_fallback")
        self.assertEqual(source["canonical_dependency_count"], 0)
        self.assertEqual(source["automated_monitoring_use"], "PROHIBITED_OR_RIGHTS_HOLD")
        self.assertIn("no future occurrence", source["future_schedule_horizon"].lower())
        limitations = " ".join(source.get("known_limitations", []))
        self.assertIn("primary OPEC provenance", limitations)
        self.assertNotEqual(source["source_id"], self.plan["selection"]["schedule_source_id"])

    def test_completion_history_marks_primary_provenance_pending(self):
        post = self._post_state()
        row = be.by_occurrence(post["canonical"])[be.TARGET_ID]
        self.assertEqual(row["status_history"][-1]["lifecycle_status"], "COMPLETED")
        self.assertEqual(row["status_history"][-1]["primary_provenance_upgrade_state"], "REQUIRED_WHEN_RETRIEVABLE")
        docs = [d for d in row["related_documents"] if d.get("source_id") == be.COMPLETION_SOURCE_ID]
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["role"], "COMPLETION_FALLBACK_VERIFICATION_PRIMARY_PENDING")
        self.assertEqual(docs[0]["primary_provenance_upgrade_state"], "REQUIRED_WHEN_RETRIEVABLE")

    def test_change_ledger_is_one_reviewed_lifecycle_entry(self):
        post = self._post_state()
        matches = [x for x in post["ledger"]["changes"] if x.get("change_id") == self.plan["completion_basis"]["change_id"]]
        self.assertEqual(len(matches), 1)
        row = matches[0]
        self.assertEqual(row["occurrence_id"], be.TARGET_ID)
        self.assertEqual(row["change_type"], "LIFECYCLE_AND_CERTAINTY_UPDATE")
        self.assertEqual(row["review_state"], "APPROVED_FOR_CANONICAL_COMMIT")
        self.assertEqual(row["new_values"]["lifecycle_status"], "COMPLETED")
        self.assertEqual(row["new_values"]["primary_outcome_provenance_state"], "PENDING_PRIMARY_UPGRADE")
        self.assertFalse(row["automatic_canonical_commit"])
        self.assertFalse(row["google_calendar_write"])

    def test_analysis_readiness_expands_without_analysis_mutation(self):
        post = self._post_state()
        readiness = analysis_population_readiness(post["analysis_schema"], post["analysis_reviews"], post["canonical"])
        self.assertEqual(readiness["eligible_completed_occurrence_count"], 22)
        self.assertEqual(readiness["reviewed_occurrence_count"], 21)
        self.assertEqual(22 - 21, self.plan["postconditions"]["completed_unreviewed_analysis_anchor_count"])
        self.assertEqual(post["analysis_schema"], self.state["analysis_schema"])
        self.assertEqual(post["analysis_reviews"], self.state["analysis_reviews"])
        self.assertEqual(post["analysis_evidence"], self.state["analysis_evidence"])

    def test_no_october_4_occurrence_is_created(self):
        post = self._post_state()
        rows = [
            r for r in post["canonical"]["records"]
            if r.get("series_id") == "WSER-COM-OPEC-VOL" and str(r.get("start_local", "")).startswith("2026-10-04")
        ]
        self.assertEqual(rows, [])

    def test_monitor_live_and_review_state_layers_are_unchanged(self):
        post = self._post_state()
        for key in (
            "expectations", "operations", "review_contract", "review_decisions",
            "live_schema", "live_observations", "live_evidence",
        ):
            self.assertEqual(post[key], self.state[key], key)

    def test_biosecurity_overlay_only_advances_checkpoint(self):
        post = self._post_state()
        self.assertEqual(be.overlay_semantics(post["overlay"]), be.overlay_semantics(self.state["overlay"]))
        checkpoint = post["overlay"]["canonical_checkpoint"]
        self.assertTrue(version_at_least(str(checkpoint["registry_version"]), "0.40"))
        self.assertGreaterEqual(checkpoint["record_count"], 689)
        self.assertEqual(checkpoint["registry_version"], str(post["canonical"].get("version")))
        self.assertEqual(checkpoint["record_count"], len(post["canonical"]["records"]))

    def test_helper_cli_check_only_is_available(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts/apply_opec_fallback_completion_be.py"), "--check-only"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if self._is_pre_state():
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn('"mode": "CHECK_ONLY"', proc.stdout)
            self.assertIn('"primary_provenance_upgrade_state": "REQUIRED_WHEN_RETRIEVABLE"', proc.stdout)
        else:
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("BE PRECONDITION FAILED", proc.stderr + proc.stdout)


if __name__ == "__main__":
    unittest.main()
