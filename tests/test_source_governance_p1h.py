from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from provenance_repair_compat import (
    assert_brazil_inauguration_compatible,
    assert_held_sources_compatible,
    assert_source_registry_compatible,
)

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/apply_source_governance_p1h.py"
SPEC = importlib.util.spec_from_file_location("apply_source_governance_p1h", MODULE_PATH)
MIGRATION = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MIGRATION)

PLAN_PATH = ROOT / "data/coverage/SOURCE_GOVERNANCE_P1H_BACKFILL_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"

APPROVED = {
    "WSSRC-CB-011",
    "WSSRC-COM-001",
    "WSSRC-INT-001",
    "WSSRC-MAC-016",
    "WSSRC-REG-006",
    "WSSRC-REG-010",
}
HELD = {"WSSRC-EL-BR-001", "WSSRC-CB-009"}
EXPECTED_DEPENDENCIES = {
    "WSSRC-COM-001": 3,
    "WSSRC-MAC-016": 5,
    "WSSRC-CB-011": 2,
    "WSSRC-REG-006": 2,
    "WSSRC-REG-010": 2,
    "WSSRC-INT-001": 2,
}
EXPECTED_CLASSIFICATIONS = {
    "WSSRC-COM-001": (
        "MANUAL_INFORMATIONAL_REFERENCE_ONLY",
        "PROHIBITED_OR_RIGHTS_HOLD",
        "RIGHTS_HELD_MANUAL_ONLY",
    ),
    "WSSRC-MAC-016": (
        "CLEARED_CURATED_FACTUAL_METADATA",
        "ENDPOINT_REVIEW_REQUIRED",
        "AUTOMATED_PILOT",
    ),
    "WSSRC-CB-011": (
        "MANUAL_INFORMATIONAL_REFERENCE_ONLY",
        "PROHIBITED_OR_RIGHTS_HOLD",
        "RIGHTS_HELD_MANUAL_ONLY",
    ),
    "WSSRC-REG-006": (
        "MANUAL_INFORMATIONAL_REFERENCE_ONLY",
        "PROHIBITED_OR_RIGHTS_HOLD",
        "RIGHTS_HELD_MANUAL_ONLY",
    ),
    "WSSRC-REG-010": (
        "CLEARED_CURATED_FACTUAL_METADATA",
        "ENDPOINT_REVIEW_REQUIRED",
        "MANUAL_AUTHORITATIVE_RECHECK",
    ),
    "WSSRC-INT-001": (
        "MANUAL_INFORMATIONAL_REFERENCE_ONLY",
        "PROHIBITED_OR_RIGHTS_HOLD",
        "RIGHTS_HELD_MANUAL_ONLY",
    ),
}


class P1HGovernanceMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        cls.canonical = json.loads(CANONICAL_PATH.read_text(encoding="utf-8"))
        cls.sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
        cls.expectations = json.loads(EXPECTATIONS_PATH.read_text(encoding="utf-8"))
        cls.source_version = str(cls.sources.get("version"))
        cls.pre_version = str(cls.plan["preconditions"]["source_registry_version"])
        cls.post_version = str(cls.plan["postconditions"]["source_registry_version"])

    @staticmethod
    def _version_tuple(value: str) -> tuple[int, ...]:
        return tuple(int(part) for part in str(value).split("."))

    def _assert_completed_source_state(self, source_registry: dict) -> None:
        self.assertGreaterEqual(
            self._version_tuple(str(source_registry.get("version"))),
            self._version_tuple(self.post_version),
        )
        assert_source_registry_compatible(self, source_registry)
        by_id = MIGRATION._sources_by_id(source_registry)
        for source_id, spec in self.plan["source_updates"].items():
            for field, value in spec["set"].items():
                self.assertEqual(by_id[source_id].get(field), value)
        assert_held_sources_compatible(
            self, source_registry, HELD,
            self.plan["preconditions"]["required_missing_governance_fields"],
        )

    def test_plan_scope_is_exact_and_geographically_corrective(self):
        self.assertEqual(set(self.plan["source_updates"]), APPROVED)
        self.assertEqual(set(self.plan["selection"]["selected_source_ids"]), APPROVED)
        self.assertTrue(APPROVED.isdisjoint(HELD))
        self.assertEqual(self.plan["selection"]["canonical_dependency_total"], 16)
        self.assertEqual(len(self.plan["selection"]["regional_mix"]), 5)
        self.assertFalse(self.plan["principles"]["automatic_canonical_commit"])
        self.assertFalse(self.plan["principles"]["google_calendar_write"])
        self.assertTrue(self.plan["principles"]["canonical_provenance_and_automation_are_separate"])
        self.assertTrue(self.plan["principles"]["regional_balance_is_a_selection_constraint_not_a_permission_signal"])

    def test_frozen_dependency_counts_are_exact(self):
        self.assertEqual(
            self.plan["preconditions"]["approved_source_dependency_counts"],
            EXPECTED_DEPENDENCIES,
        )
        self.assertEqual(sum(EXPECTED_DEPENDENCIES.values()), 16)

    def test_frozen_classifications_preserve_provenance_automation_split(self):
        for source_id, values in EXPECTED_CLASSIFICATIONS.items():
            row = self.plan["source_updates"][source_id]["set"]
            self.assertEqual(row["canonical_provenance_use"], values[0])
            self.assertEqual(row["automated_monitoring_use"], values[1])
            self.assertEqual(row["verification_mode"], values[2])

    def test_source_native_semantics_are_explicit(self):
        updates = self.plan["source_updates"]
        self.assertIn("08:50 JST", updates["WSSRC-MAC-016"]["set"]["governance_backfill_basis"])
        self.assertIn("multi-day MPC meeting windows", updates["WSSRC-CB-011"]["set"]["governance_backfill_basis"])
        self.assertIn("does not supply a separate decision-release clock time", updates["WSSRC-CB-011"]["set"]["governance_backfill_basis"])
        self.assertIn("15:00", updates["WSSRC-REG-006"]["set"]["governance_backfill_basis"])
        self.assertIn("8 September", updates["WSSRC-REG-010"]["set"]["governance_backfill_basis"])
        self.assertIn("15 November", updates["WSSRC-REG-010"]["set"]["governance_backfill_basis"])
        self.assertIn("provisional", updates["WSSRC-INT-001"]["set"]["governance_backfill_basis"].lower())

    def test_rights_findings_are_not_conflated_with_public_access(self):
        updates = self.plan["source_updates"]
        self.assertIn("shared electronic archives or databases", updates["WSSRC-COM-001"]["set"]["governance_backfill_basis"])
        self.assertIn("Article 14(VIII)", updates["WSSRC-REG-010"]["set"]["governance_backfill_basis"])
        for source_id in ("WSSRC-COM-001", "WSSRC-CB-011", "WSSRC-REG-006", "WSSRC-INT-001"):
            row = updates[source_id]["set"]
            self.assertEqual(row["automated_monitoring_use"], "PROHIBITED_OR_RIGHTS_HOLD")
            self.assertEqual(row["verification_mode"], "RIGHTS_HELD_MANUAL_ONLY")

    def test_held_source_controls_are_exact(self):
        for held_id in HELD:
            control = self.plan["held_source_controls"][held_id]
            self.assertEqual(control["transaction_status"], "EXCLUDED_PROVENANCE_SCOPE_REPAIR_REQUIRED")
            self.assertTrue(control["must_remain_byte_identical"])
            self.assertTrue(control["must_not_gain_governance_fields"])
            self.assertFalse(control["canonical_date_correction_required"])
        snb = self.plan["preconditions"]["snb_scope_guard"]
        self.assertEqual(snb["expected_canonical_dependency_count"], 18)
        self.assertEqual(
            snb["expected_authoritative_url"],
            "https://www.snb.ch/en/the-snb/mandates-goals/monetary-policy/decisions",
        )

    def test_repository_state_is_valid_before_or_after_transaction(self):
        self.assertGreaterEqual(
            self._version_tuple(self.source_version), self._version_tuple(self.pre_version)
        )
        if self.source_version == self.pre_version:
            MIGRATION.preflight(self.canonical, self.sources, self.expectations, self.plan)
        else:
            self._assert_completed_source_state(self.sources)
            with self.assertRaises(SystemExit):
                MIGRATION.preflight(self.canonical, self.sources, self.expectations, self.plan)

    def test_transition_or_completed_state_preserves_exact_scope(self):
        canonical_before = copy.deepcopy(self.canonical)
        expectations_before = copy.deepcopy(self.expectations)
        by_id = MIGRATION._sources_by_id(self.sources)
        held_before = {held_id: copy.deepcopy(by_id[held_id]) for held_id in HELD}

        if self.source_version == self.pre_version:
            sources_before = copy.deepcopy(self.sources)
            post_sources, report = MIGRATION.build_post_state(
                self.canonical, self.sources, self.expectations, self.plan
            )
            self.assertEqual(self.sources, sources_before)
            self.assertEqual(set(report["changed_source_ids"]), APPROVED)
            self._assert_completed_source_state(post_sources)
            post_by_id = MIGRATION._sources_by_id(post_sources)
            for held_id in HELD:
                self.assertEqual(post_by_id[held_id], held_before[held_id])
            self.assertTrue(report["held_sources_unchanged"])
            self.assertEqual(report["brazil_inauguration_start_local"], "2027-01-05")
            self.assertFalse(report["automatic_canonical_commit"])
            self.assertFalse(report["google_calendar_write"])
        else:
            self._assert_completed_source_state(self.sources)

        self.assertEqual(self.canonical, canonical_before)
        self.assertEqual(self.expectations, expectations_before)

    def test_brazil_inauguration_guard_is_exact(self):
        assert_brazil_inauguration_compatible(self, self.canonical)

    def test_script_help_is_available(self):
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

    def test_default_cli_is_read_only_or_blocks_replay_after_completion(self):
        before = SOURCES_PATH.read_bytes()
        result = subprocess.run(
            [sys.executable, str(MODULE_PATH)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(SOURCES_PATH.read_bytes(), before)
        if self.source_version == self.pre_version:
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["mode"], "READ_ONLY_PREFLIGHT")
            self.assertEqual(set(report["changed_source_ids"]), APPROVED)
        else:
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("P1-H GOVERNANCE PRECONDITION FAILED", result.stderr + result.stdout)

    def test_apply_without_environment_gate_never_writes(self):
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
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(SOURCES_PATH.read_bytes(), before)
        combined = result.stderr + result.stdout
        if self.source_version == self.pre_version:
            self.assertIn("P1-H APPLY REFUSED", combined)
        else:
            self.assertIn("P1-H GOVERNANCE PRECONDITION FAILED", combined)


if __name__ == "__main__":
    unittest.main()
