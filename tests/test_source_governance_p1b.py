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
MODULE_PATH = ROOT / "scripts/apply_source_governance_p1b.py"
SPEC = importlib.util.spec_from_file_location("apply_source_governance_p1b", MODULE_PATH)
MIGRATION = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MIGRATION)

PLAN_PATH = ROOT / "data/coverage/SOURCE_GOVERNANCE_P1B_BACKFILL_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"

APPROVED = {
    "WSSRC-CB-001",
    "WSSRC-CB-002",
    "WSSRC-CB-003",
    "WSSRC-CB-006",
    "WSSRC-CB-007",
    "WSSRC-MAC-006",
}
HELD = "WSSRC-EL-BR-001"


class P1BGovernanceMigrationTests(unittest.TestCase):
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
            self, source_registry, {HELD},
            self.plan["preconditions"]["required_missing_governance_fields"],
        )

    def test_plan_is_exactly_six_sources_and_excludes_tse(self):
        self.assertEqual(set(self.plan["source_updates"]), APPROVED)
        self.assertEqual(set(self.plan["selection"]["selected_source_ids"]), APPROVED)
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
        self.assertTrue(
            self.plan["principles"]["rba_meeting_window_and_decision_release_remain_distinct"]
        )

    def test_frozen_dependency_counts_are_exact(self):
        self.assertEqual(
            self.plan["preconditions"]["approved_source_dependency_counts"],
            {
                "WSSRC-CB-001": 44,
                "WSSRC-CB-006": 44,
                "WSSRC-CB-002": 33,
                "WSSRC-CB-003": 22,
                "WSSRC-MAC-006": 19,
                "WSSRC-CB-007": 11,
            },
        )

    def test_frozen_classifications_preserve_provenance_automation_split(self):
        updates = self.plan["source_updates"]
        expected = {
            "WSSRC-CB-001": (
                "CLEARED_CURATED_FACTUAL_METADATA",
                "ENDPOINT_REVIEW_REQUIRED",
                "AUTOMATED_PILOT",
            ),
            "WSSRC-CB-006": (
                "CLEARED_CURATED_FACTUAL_METADATA",
                "ENDPOINT_REVIEW_REQUIRED",
                "MANUAL_AUTHORITATIVE_RECHECK",
            ),
            "WSSRC-CB-002": (
                "CLEARED_CURATED_FACTUAL_METADATA",
                "ENDPOINT_REVIEW_REQUIRED",
                "AUTOMATED_PILOT",
            ),
            "WSSRC-CB-003": (
                "CLEARED_CURATED_FACTUAL_METADATA",
                "ENDPOINT_REVIEW_REQUIRED",
                "MANUAL_AUTHORITATIVE_RECHECK",
            ),
            "WSSRC-MAC-006": (
                "CLEARED_CURATED_FACTUAL_METADATA",
                "CLEARED",
                "AUTOMATED_PILOT",
            ),
            "WSSRC-CB-007": (
                "CLEARED_CURATED_FACTUAL_METADATA",
                "PROHIBITED_OR_RIGHTS_HOLD",
                "RIGHTS_HELD_MANUAL_ONLY",
            ),
        }
        for source_id, values in expected.items():
            row = updates[source_id]["set"]
            self.assertEqual(row["canonical_provenance_use"], values[0])
            self.assertEqual(row["automated_monitoring_use"], values[1])
            self.assertEqual(row["verification_mode"], values[2])

    def test_ons_and_rbnz_lock_opposite_automation_controls(self):
        ons = self.plan["source_updates"]["WSSRC-MAC-006"]["set"]
        rbnz = self.plan["source_updates"]["WSSRC-CB-007"]["set"]
        self.assertEqual(ons["automated_monitoring_use"], "CLEARED")
        self.assertEqual(ons["verification_mode"], "AUTOMATED_PILOT")
        self.assertEqual(rbnz["automated_monitoring_use"], "PROHIBITED_OR_RIGHTS_HOLD")
        self.assertEqual(rbnz["verification_mode"], "RIGHTS_HELD_MANUAL_ONLY")

    def test_repository_state_is_valid_before_or_after_transaction(self):
        self.assertGreaterEqual(
            self._version_tuple(self.source_version),
            self._version_tuple(self.pre_version),
        )
        if self.source_version == self.pre_version:
            MIGRATION.preflight(
                self.canonical,
                self.sources,
                self.expectations,
                self.plan,
            )
        else:
            self._assert_completed_source_state(self.sources)
            with self.assertRaises(SystemExit):
                MIGRATION.preflight(
                    self.canonical,
                    self.sources,
                    self.expectations,
                    self.plan,
                )

    def test_transition_or_completed_state_preserves_exact_six_source_scope(self):
        canonical_before = copy.deepcopy(self.canonical)
        expectations_before = copy.deepcopy(self.expectations)
        held_before = copy.deepcopy(MIGRATION._sources_by_id(self.sources)[HELD])

        if self.source_version == self.pre_version:
            sources_before = copy.deepcopy(self.sources)
            post_sources, report = MIGRATION.build_post_state(
                self.canonical,
                self.sources,
                self.expectations,
                self.plan,
            )
            self.assertEqual(self.sources, sources_before)
            self.assertEqual(set(report["changed_source_ids"]), APPROVED)
            self._assert_completed_source_state(post_sources)
            self.assertEqual(MIGRATION._sources_by_id(post_sources)[HELD], held_before)
            self.assertTrue(report["held_source_unchanged"])
            self.assertEqual(report["brazil_inauguration_start_local"], "2027-01-05")
            self.assertFalse(report["automatic_canonical_commit"])
            self.assertFalse(report["google_calendar_write"])
        else:
            self._assert_completed_source_state(self.sources)

        self.assertEqual(self.canonical, canonical_before)
        self.assertEqual(self.expectations, expectations_before)
        self.assertEqual(MIGRATION._sources_by_id(self.sources)[HELD], held_before)

    def test_brazil_inauguration_guard_is_exact_and_constitutional_date_is_preserved(self):
        assert_brazil_inauguration_compatible(self, self.canonical)

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
        after = SOURCES_PATH.read_bytes()
        self.assertEqual(after, before)

        if self.source_version == self.pre_version:
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["mode"], "READ_ONLY_PREFLIGHT")
            self.assertEqual(set(report["changed_source_ids"]), APPROVED)
        else:
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("P1-B GOVERNANCE PRECONDITION FAILED", result.stderr + result.stdout)

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
        after = SOURCES_PATH.read_bytes()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(after, before)
        combined = result.stderr + result.stdout
        if self.source_version == self.pre_version:
            self.assertIn("P1-B APPLY REFUSED", combined)
        else:
            self.assertIn("P1-B GOVERNANCE PRECONDITION FAILED", combined)


if __name__ == "__main__":
    unittest.main()
