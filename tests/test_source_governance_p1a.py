from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/apply_source_governance_p1a.py"
SPEC = importlib.util.spec_from_file_location("apply_source_governance_p1a", MODULE_PATH)
MIGRATION = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MIGRATION)

PLAN_PATH = ROOT / "data/coverage/SOURCE_GOVERNANCE_P1A_BACKFILL_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"

APPROVED = {
    "WSSRC-MAC-007",
    "WSSRC-MAC-017",
    "WSSRC-COM-003",
    "WSSRC-COM-010",
    "WSSRC-HEALTH-001",
    "WSSRC-CLIM-001",
}
HELD = "WSSRC-EL-BR-001"


class P1AGovernanceMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        cls.canonical = json.loads(CANONICAL_PATH.read_text(encoding="utf-8"))
        cls.sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
        cls.expectations = json.loads(EXPECTATIONS_PATH.read_text(encoding="utf-8"))

    def test_plan_is_exactly_six_sources_and_excludes_tse(self):
        self.assertEqual(set(self.plan["source_updates"]), APPROVED)
        self.assertNotIn(HELD, self.plan["source_updates"])
        self.assertEqual(
            self.plan["held_source_controls"][HELD]["transaction_status"],
            "EXCLUDED_PROVENANCE_SCOPE_REPAIR_REQUIRED",
        )
        self.assertTrue(
            self.plan["held_source_controls"][HELD]["must_remain_byte_identical"]
        )
        self.assertFalse(
            self.plan["held_source_controls"][HELD]["canonical_date_correction_required"]
        )
        self.assertFalse(self.plan["principles"]["automatic_canonical_commit"])
        self.assertFalse(self.plan["principles"]["google_calendar_write"])

    def test_frozen_classifications_preserve_provenance_automation_split(self):
        updates = self.plan["source_updates"]
        expected = {
            "WSSRC-MAC-007": (
                "CLEARED_CURATED_FACTUAL_METADATA",
                "ENDPOINT_REVIEW_REQUIRED",
                "MANUAL_AUTHORITATIVE_RECHECK",
            ),
            "WSSRC-MAC-017": (
                "CLEARED_CURATED_FACTUAL_METADATA",
                "ENDPOINT_REVIEW_REQUIRED",
                "MANUAL_AUTHORITATIVE_RECHECK",
            ),
            "WSSRC-COM-003": (
                "CLEARED_CURATED_FACTUAL_METADATA",
                "ENDPOINT_REVIEW_REQUIRED",
                "AUTOMATED_PILOT",
            ),
            "WSSRC-COM-010": (
                "MANUAL_INFORMATIONAL_REFERENCE_ONLY",
                "ENDPOINT_REVIEW_REQUIRED",
                "MANUAL_AUTHORITATIVE_RECHECK",
            ),
            "WSSRC-HEALTH-001": (
                "MANUAL_INFORMATIONAL_REFERENCE_ONLY",
                "PROHIBITED_OR_RIGHTS_HOLD",
                "RIGHTS_HELD_MANUAL_ONLY",
            ),
            "WSSRC-CLIM-001": (
                "MANUAL_INFORMATIONAL_REFERENCE_ONLY",
                "PROHIBITED_OR_RIGHTS_HOLD",
                "RIGHTS_HELD_MANUAL_ONLY",
            ),
        }
        for source_id, values in expected.items():
            row = updates[source_id]["set"]
            self.assertEqual(row["canonical_provenance_use"], values[0])
            self.assertEqual(row["automated_monitoring_use"], values[1])
            self.assertEqual(row["verification_mode"], values[2])

    def test_repository_preflight_passes_at_verified_checkpoint(self):
        MIGRATION.preflight(
            self.canonical,
            self.sources,
            self.expectations,
            self.plan,
        )

    def test_simulated_post_state_changes_only_six_source_records(self):
        canonical_before = copy.deepcopy(self.canonical)
        sources_before = copy.deepcopy(self.sources)
        expectations_before = copy.deepcopy(self.expectations)
        held_before = copy.deepcopy(MIGRATION._sources_by_id(self.sources)[HELD])

        post_sources, report = MIGRATION.build_post_state(
            self.canonical,
            self.sources,
            self.expectations,
            self.plan,
        )

        self.assertEqual(self.canonical, canonical_before)
        self.assertEqual(self.sources, sources_before)
        self.assertEqual(self.expectations, expectations_before)
        self.assertEqual(set(report["changed_source_ids"]), APPROVED)
        self.assertEqual(post_sources["version"], "1.53")
        self.assertEqual(len(post_sources["sources"]), 223)
        self.assertEqual(MIGRATION._sources_by_id(post_sources)[HELD], held_before)
        self.assertTrue(report["held_source_unchanged"])
        self.assertEqual(report["brazil_inauguration_start_local"], "2027-01-05")
        self.assertFalse(report["automatic_canonical_commit"])
        self.assertFalse(report["google_calendar_write"])

    def test_brazil_inauguration_guard_is_exact_and_constitutional_date_is_preserved(self):
        guard = self.plan["preconditions"]["brazil_inauguration_guard"]
        matches = MIGRATION._brazil_inauguration_records(self.canonical, guard)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["start_local"], "2027-01-05")
        self.assertEqual(matches[0]["source_id"], HELD)
        self.assertEqual(
            matches[0]["election_milestone_type"],
            "INAUGURATION_OR_ASSUMPTION",
        )

    def test_script_executes_as_cli_from_repository_root(self):
        result = subprocess.run(
            [sys.executable, str(MODULE_PATH), "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--apply", result.stdout)
        self.assertIn(MIGRATION.APPLY_ENV, result.stdout)

    def test_default_cli_is_read_only(self):
        before = SOURCES_PATH.read_bytes()
        result = subprocess.run(
            [sys.executable, str(MODULE_PATH)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        after = SOURCES_PATH.read_bytes()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(after, before)
        report = json.loads(result.stdout)
        self.assertEqual(report["mode"], "READ_ONLY_PREFLIGHT")
        self.assertEqual(set(report["changed_source_ids"]), APPROVED)

    def test_apply_fails_closed_without_explicit_environment_gate(self):
        before = SOURCES_PATH.read_bytes()
        env = dict(os.environ)
        env.pop(MIGRATION.APPLY_ENV, None)
        result = subprocess.run(
            [sys.executable, str(MODULE_PATH), "--apply"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        after = SOURCES_PATH.read_bytes()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("P1-A APPLY REFUSED", result.stderr + result.stdout)
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
