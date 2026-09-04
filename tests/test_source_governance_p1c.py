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
MODULE_PATH = ROOT / "scripts/apply_source_governance_p1c.py"
SPEC = importlib.util.spec_from_file_location("apply_source_governance_p1c", MODULE_PATH)
MIGRATION = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MIGRATION)

PLAN_PATH = ROOT / "data/coverage/SOURCE_GOVERNANCE_P1C_BACKFILL_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"

APPROVED = {
    "WSSRC-CB-008",
    "WSSRC-CN-013",
    "WSSRC-EL-NZ-001",
    "WSSRC-FIS-007",
    "WSSRC-INT-027",
    "WSSRC-MAC-005",
}
HELD = {"WSSRC-EL-BR-001", "WSSRC-CB-009"}


class P1CGovernanceMigrationTests(unittest.TestCase):
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
        self.assertEqual(len(source_registry.get("sources", [])), 223)
        by_id = MIGRATION._sources_by_id(source_registry)
        for source_id, spec in self.plan["source_updates"].items():
            for field, value in spec["set"].items():
                self.assertEqual(by_id[source_id].get(field), value)
        for held_id in HELD:
            for field in self.plan["preconditions"]["required_missing_governance_fields"]:
                self.assertIn(by_id[held_id].get(field), (None, ""))

    def test_plan_is_exactly_six_sources_and_excludes_both_held_sources(self):
        self.assertEqual(set(self.plan["source_updates"]), APPROVED)
        self.assertEqual(set(self.plan["selection"]["selected_source_ids"]), APPROVED)
        self.assertTrue(APPROVED.isdisjoint(HELD))
        for held_id in HELD:
            control = self.plan["held_source_controls"][held_id]
            self.assertEqual(
                control["transaction_status"],
                "EXCLUDED_PROVENANCE_SCOPE_REPAIR_REQUIRED",
            )
            self.assertTrue(control["must_remain_byte_identical"])
            self.assertFalse(control["canonical_date_correction_required"])
        self.assertFalse(self.plan["principles"]["automatic_canonical_commit"])
        self.assertFalse(self.plan["principles"]["google_calendar_write"])
        self.assertTrue(self.plan["principles"]["source_native_precision_must_be_preserved"])

    def test_frozen_dependency_counts_are_exact(self):
        self.assertEqual(
            self.plan["preconditions"]["approved_source_dependency_counts"],
            {
                "WSSRC-MAC-005": 12,
                "WSSRC-CB-008": 11,
                "WSSRC-FIS-007": 10,
                "WSSRC-EL-NZ-001": 6,
                "WSSRC-CN-013": 5,
                "WSSRC-INT-027": 5,
            },
        )

    def test_frozen_classifications_preserve_provenance_automation_split(self):
        expected = {
            "WSSRC-MAC-005": (
                "CLEARED_CURATED_FACTUAL_METADATA", "CLEARED", "AUTOMATED_PILOT"
            ),
            "WSSRC-CB-008": (
                "CLEARED_CURATED_FACTUAL_METADATA", "ENDPOINT_REVIEW_REQUIRED", "AUTOMATED_PILOT"
            ),
            "WSSRC-FIS-007": (
                "CLEARED_CURATED_FACTUAL_METADATA", "ENDPOINT_REVIEW_REQUIRED", "AUTOMATED_PILOT"
            ),
            "WSSRC-EL-NZ-001": (
                "CLEARED_CURATED_FACTUAL_METADATA", "ENDPOINT_REVIEW_REQUIRED", "MANUAL_AUTHORITATIVE_RECHECK"
            ),
            "WSSRC-CN-013": (
                "CLEARED_CURATED_FACTUAL_METADATA", "ENDPOINT_REVIEW_REQUIRED", "MANUAL_AUTHORITATIVE_RECHECK"
            ),
            "WSSRC-INT-027": (
                "MANUAL_INFORMATIONAL_REFERENCE_ONLY", "PROHIBITED_OR_RIGHTS_HOLD", "RIGHTS_HELD_MANUAL_ONLY"
            ),
        }
        for source_id, values in expected.items():
            row = self.plan["source_updates"][source_id]["set"]
            self.assertEqual(row["canonical_provenance_use"], values[0])
            self.assertEqual(row["automated_monitoring_use"], values[1])
            self.assertEqual(row["verification_mode"], values[2])

    def test_eurostat_and_un_lock_opposite_automation_controls(self):
        eurostat = self.plan["source_updates"]["WSSRC-MAC-005"]["set"]
        unga = self.plan["source_updates"]["WSSRC-INT-027"]["set"]
        self.assertEqual(eurostat["automated_monitoring_use"], "CLEARED")
        self.assertEqual(eurostat["verification_mode"], "AUTOMATED_PILOT")
        self.assertEqual(unga["automated_monitoring_use"], "PROHIBITED_OR_RIGHTS_HOLD")
        self.assertEqual(unga["verification_mode"], "RIGHTS_HELD_MANUAL_ONLY")

    def test_snb_scope_guard_is_exact(self):
        guard = self.plan["preconditions"]["snb_scope_guard"]
        self.assertEqual(guard["source_id"], "WSSRC-CB-009")
        self.assertEqual(guard["expected_canonical_dependency_count"], 18)
        self.assertEqual(
            guard["expected_authoritative_url"],
            "https://www.snb.ch/en/the-snb/mandates-goals/monetary-policy/decisions",
        )
        self.assertEqual(
            guard["repair_status"], "EXCLUDED_PROVENANCE_SCOPE_REPAIR_REQUIRED"
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

    def test_transition_or_completed_state_preserves_exact_six_source_scope(self):
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
        current_by_id = MIGRATION._sources_by_id(self.sources)
        for held_id in HELD:
            self.assertEqual(current_by_id[held_id], held_before[held_id])

    def test_brazil_inauguration_guard_is_exact(self):
        guard = self.plan["preconditions"]["brazil_inauguration_guard"]
        matches = MIGRATION._brazil_inauguration_records(self.canonical, guard)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["start_local"], "2027-01-05")
        self.assertEqual(matches[0]["source_id"], "WSSRC-EL-BR-001")
        self.assertEqual(
            matches[0]["election_milestone_type"], "INAUGURATION_OR_ASSUMPTION"
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
            self.assertIn("P1-C GOVERNANCE PRECONDITION FAILED", result.stderr + result.stdout)

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
            self.assertIn("P1-C APPLY REFUSED", combined)
        else:
            self.assertIn("P1-C GOVERNANCE PRECONDITION FAILED", combined)


if __name__ == "__main__":
    unittest.main()
