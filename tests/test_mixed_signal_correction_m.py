from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/apply_mixed_signal_correction_m.py"
SPEC = importlib.util.spec_from_file_location("apply_mixed_signal_correction_m", MODULE_PATH)
TX = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TX)

PLAN_PATH = ROOT / "data/coverage/MIXED_SIGNAL_CORRECTION_M_PLAN_v0.1.json"
RESEARCH_PATH = ROOT / "data/coverage/MIXED_SIGNAL_CORRECTION_M_RESEARCH_v0.1.md"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"


class MixedSignalCorrectionMTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        cls.research = RESEARCH_PATH.read_text(encoding="utf-8")
        cls.canonical = json.loads(CANONICAL_PATH.read_text(encoding="utf-8"))
        cls.sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
        cls.overlay = json.loads(OVERLAY_PATH.read_text(encoding="utf-8"))

    def _is_pre(self):
        return (
            self.canonical.get("version") == "0.26"
            and len(self.canonical.get("records", [])) == 669
            and self.sources.get("version") == "1.67"
            and len(self.sources.get("sources", [])) == 228
            and self.overlay.get("version") == "0.1"
        )

    def _is_post(self):
        ids = {row.get("occurrence_id") for row in self.canonical.get("records", [])}
        source_ids = {row.get("source_id") for row in self.sources.get("sources", [])}
        return (
            self.canonical.get("version") == "0.27"
            and len(self.canonical.get("records", [])) == 673
            and self.sources.get("version") == "1.68"
            and len(self.sources.get("sources", [])) == 231
            and self.overlay.get("version") == "0.2"
            and set(self.plan["preconditions"]["required_absent_occurrence_ids"]).issubset(ids)
            and set(self.plan["preconditions"]["required_absent_source_ids"]).issubset(source_ids)
        )

    def _post_objects(self):
        if self._is_pre():
            TX.preflight(self.canonical, self.sources, self.overlay, self.plan)
            canonical, sources, overlay, _ = TX.build_post_state(
                self.canonical, self.sources, self.overlay, self.plan
            )
            return canonical, sources, overlay
        if self._is_post():
            return self.canonical, self.sources, self.overlay
        self.fail("repository is neither exact Correction M pre-state nor reviewed post-state")

    def test_repository_is_exact_pre_or_post_state(self):
        self.assertTrue(self._is_pre() or self._is_post())
        canonical, sources, overlay = self._post_objects()
        self.assertEqual(canonical["version"], "0.27")
        self.assertEqual(len(canonical["records"]), 673)
        self.assertEqual(sources["version"], "1.68")
        self.assertEqual(len(sources["sources"]), 231)
        self.assertEqual(overlay["canonical_checkpoint"], {"registry_version": "0.27", "record_count": 673})

    def test_frozen_scope_is_three_series_four_occurrences_three_sources(self):
        self.assertEqual(len(self.plan["series"]), 3)
        self.assertEqual(len(self.plan["occurrences"]), 4)
        self.assertEqual(len(self.plan["source_plan"]), 3)
        self.assertEqual(
            [row["source_id"] for row in self.plan["source_plan"]],
            ["WSSRC-CB-014", "WSSRC-INT-032", "WSSRC-INT-033"],
        )
        self.assertEqual(
            [row["occurrence_id"] for row in self.plan["occurrences"]],
            ["WSO-CBN-MPC-307", "WSO-CBN-MPC-308", "WSO-BWC-WG-2026-S10", "WSO-WOAH-GS-094"],
        )

    def test_cbn_preserves_two_day_meeting_window_semantics(self):
        canonical, _, _ = self._post_objects()
        rows = {row["occurrence_id"]: row for row in canonical["records"]}
        expected = {
            "WSO-CBN-MPC-307": ("2026-09-21", "2026-09-22"),
            "WSO-CBN-MPC-308": ("2026-11-23", "2026-11-24"),
        }
        for oid, dates in expected.items():
            row = rows[oid]
            self.assertEqual(row["source_id"], "WSSRC-CB-014")
            self.assertEqual(row["event_type"], "MONETARY_POLICY_DECISION_PROCESS")
            self.assertEqual(row["timing_type"], "MULTI_DAY_LOCAL")
            self.assertEqual((row["start_local"], row["end_local"]), dates)
            self.assertEqual(row["time_precision"], "DAY_RANGE")
            self.assertIsNone(row["start_utc"])
            self.assertIsNone(row["location"])
            self.assertNotIn("publication day", row["notes"].lower())

    def test_bwc_and_woah_keep_natural_primary_categories(self):
        canonical, _, overlay = self._post_objects()
        rows = {row["occurrence_id"]: row for row in canonical["records"]}
        bwc = rows["WSO-BWC-WG-2026-S10"]
        woah = rows["WSO-WOAH-GS-094"]
        self.assertEqual(bwc["category"], "INTERNATIONAL_INSTITUTIONS")
        self.assertEqual(bwc["subcategory"], "biological_security_arms_control")
        self.assertEqual(bwc["event_type"], "TREATY_WORKING_GROUP_SESSION")
        self.assertEqual((bwc["start_local"], bwc["end_local"]), ("2026-12-07", "2026-12-11"))
        self.assertEqual(woah["category"], "AGRICULTURE_FOOD")
        self.assertEqual(woah["subcategory"], "animal_health_standards_governance")
        self.assertEqual((woah["start_local"], woah["end_local"]), ("2027-05-24", "2027-05-28"))

        memberships = {row["series_id"]: row for row in overlay["canonical_series_memberships"]}
        self.assertEqual(memberships["WSER-INT-BWC-WG-STRENGTHENING"]["system_ids"], ["BIO-BIOLOGICAL-SECURITY-ARMS-CONTROL"])
        self.assertEqual(memberships["WSER-AGF-WOAH-GENERAL-SESSION"]["system_ids"], ["BIO-ANIMAL-ZOONOTIC-HEALTH"])
        candidate_ids = {row["candidate_node_id"] for row in overlay["candidate_nodes"]}
        self.assertNotIn("BIO-CAND-BWC", candidate_ids)
        self.assertNotIn("BIO-CAND-WOAH", candidate_ids)
        self.assertEqual(candidate_ids, {"BIO-CAND-IPPC-CPM", "BIO-CAND-AFRICA-CDC"})

    def test_source_governance_separates_provenance_and_automation(self):
        _, sources, _ = self._post_objects()
        by_id = {row["source_id"]: row for row in sources["sources"]}
        cbn = by_id["WSSRC-CB-014"]
        self.assertEqual(cbn["canonical_provenance_use"], "CLEARED_CURATED_FACTUAL_METADATA")
        self.assertEqual(cbn["automated_monitoring_use"], "ENDPOINT_REVIEW_REQUIRED")
        self.assertEqual(cbn["verification_mode"], "MANUAL_AUTHORITATIVE_RECHECK")
        for source_id in ("WSSRC-INT-032", "WSSRC-INT-033"):
            row = by_id[source_id]
            self.assertEqual(row["canonical_provenance_use"], "MANUAL_INFORMATIONAL_REFERENCE_ONLY")
            self.assertEqual(row["automated_monitoring_use"], "PROHIBITED_OR_RIGHTS_HOLD")
            self.assertEqual(row["verification_mode"], "RIGHTS_HELD_MANUAL_ONLY")

    def test_explicit_holds_are_not_silently_population_authority(self):
        holds = {row["candidate"]: row["reason"] for row in self.plan["explicit_holds"]}
        self.assertIn("IPPC CPM-21", holds)
        self.assertIn("North Indian Ocean tropical cyclone seasons", holds)
        self.assertIn("conflict", holds["IPPC CPM-21"].lower())
        self.assertIn("conflict", holds["North Indian Ocean tropical cyclone seasons"].lower())
        self.assertIn("April-June", holds["North Indian Ocean tropical cyclone seasons"])
        self.assertIn("April-May", holds["North Indian Ocean tropical cyclone seasons"])

    def test_global_write_gates_remain_closed(self):
        post = self.plan["postconditions"]
        self.assertFalse(post["automatic_canonical_commit"])
        self.assertFalse(post["google_calendar_write"])
        self.assertTrue(post["monitor_expectations_unchanged"])
        self.assertTrue(post["change_ledger_unchanged"])

    def test_apply_without_environment_gate_never_writes(self):
        if not self._is_pre():
            self.skipTest("apply-gate mutation test is exercised only from exact pre-state")
        before = {path: path.read_bytes() for path in (CANONICAL_PATH, SOURCES_PATH, OVERLAY_PATH, LEDGER_PATH, EXPECTATIONS_PATH)}
        env = dict(os.environ)
        env.pop(TX.APPLY_ENV, None)
        proc = subprocess.run([sys.executable, str(MODULE_PATH), "--apply"], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("APPLY BLOCKED", proc.stdout + proc.stderr)
        for path, raw in before.items():
            self.assertEqual(path.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
