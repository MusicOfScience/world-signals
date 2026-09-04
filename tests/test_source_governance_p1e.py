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
MODULE_PATH = ROOT / "scripts/apply_source_governance_p1e.py"
SPEC = importlib.util.spec_from_file_location("apply_source_governance_p1e", MODULE_PATH)
MIGRATION = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MIGRATION)

PLAN_PATH = ROOT / "data/coverage/SOURCE_GOVERNANCE_P1E_BACKFILL_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"

APPROVED = {
    "WSSRC-CB-004",
    "WSSRC-CB-005",
    "WSSRC-CLIM-003",
    "WSSRC-MAC-011",
    "WSSRC-MAC-025",
    "WSSRC-REGJ-005",
}
HELD = {"WSSRC-EL-BR-001", "WSSRC-CB-009"}

EXPECTED_DEPENDENCIES = {
    "WSSRC-CB-004": 11,
    "WSSRC-CB-005": 11,
    "WSSRC-MAC-025": 8,
    "WSSRC-MAC-011": 6,
    "WSSRC-CLIM-003": 4,
    "WSSRC-REGJ-005": 3,
}

EXPECTED_CLASSIFICATIONS = {
    "WSSRC-CB-004": (
        "CLEARED_CURATED_FACTUAL_METADATA",
        "ENDPOINT_REVIEW_REQUIRED",
        "MANUAL_AUTHORITATIVE_RECHECK",
    ),
    "WSSRC-CB-005": (
        "MANUAL_INFORMATIONAL_REFERENCE_ONLY",
        "PROHIBITED_OR_RIGHTS_HOLD",
        "RIGHTS_HELD_MANUAL_ONLY",
    ),
    "WSSRC-MAC-025": (
        "CLEARED_CURATED_FACTUAL_METADATA",
        "ENDPOINT_REVIEW_REQUIRED",
        "AUTOMATED_PILOT",
    ),
    "WSSRC-MAC-011": (
        "CLEARED_CURATED_FACTUAL_METADATA",
        "ENDPOINT_REVIEW_REQUIRED",
        "AUTOMATED_PILOT",
    ),
    "WSSRC-CLIM-003": (
        "MANUAL_INFORMATIONAL_REFERENCE_ONLY",
        "PROHIBITED_OR_RIGHTS_HOLD",
        "RIGHTS_HELD_MANUAL_ONLY",
    ),
    "WSSRC-REGJ-005": (
        "CLEARED_CURATED_FACTUAL_METADATA",
        "ENDPOINT_REVIEW_REQUIRED",
        "MANUAL_AUTHORITATIVE_RECHECK",
    ),
}


class P1EGovernanceMigrationTests(unittest.TestCase):
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

    def test_plan_is_exactly_six_sources_and_excludes_holds(self):
        self.assertEqual(set(self.plan["source_updates"]), APPROVED)
        self.assertEqual(set(self.plan["selection"]["selected_source_ids"]), APPROVED)
        self.assertTrue(APPROVED.isdisjoint(HELD))
        self.assertEqual(self.plan["selection"]["canonical_dependency_total"], 43)
        self.assertFalse(self.plan["principles"]["automatic_canonical_commit"])
        self.assertFalse(self.plan["principles"]["google_calendar_write"])
        self.assertTrue(self.plan["principles"]["canonical_provenance_and_automation_are_separate"])
        self.assertTrue(self.plan["principles"]["source_native_precision_must_be_preserved"])
        self.assertTrue(self.plan["principles"]["institution_native_event_semantics_must_be_preserved"])

    def test_frozen_dependency_counts_are_exact(self):
        self.assertEqual(
            self.plan["preconditions"]["approved_source_dependency_counts"],
            EXPECTED_DEPENDENCIES,
        )
        self.assertEqual(sum(EXPECTED_DEPENDENCIES.values()), 43)

    def test_frozen_classifications_preserve_provenance_automation_split(self):
        for source_id, values in EXPECTED_CLASSIFICATIONS.items():
            row = self.plan["source_updates"][source_id]["set"]
            self.assertEqual(row["canonical_provenance_use"], values[0])
            self.assertEqual(row["automated_monitoring_use"], values[1])
            self.assertEqual(row["verification_mode"], values[2])

    def test_pilots_and_rights_holds_are_not_conflated(self):
        japan = self.plan["source_updates"]["WSSRC-MAC-025"]["set"]
        abs_cpi = self.plan["source_updates"]["WSSRC-MAC-011"]["set"]
        boe = self.plan["source_updates"]["WSSRC-CB-005"]["set"]
        cbd = self.plan["source_updates"]["WSSRC-CLIM-003"]["set"]
        self.assertEqual(japan["verification_mode"], "AUTOMATED_PILOT")
        self.assertEqual(abs_cpi["verification_mode"], "AUTOMATED_PILOT")
        for row in (boe, cbd):
            self.assertEqual(row["automated_monitoring_use"], "PROHIBITED_OR_RIGHTS_HOLD")
            self.assertEqual(row["verification_mode"], "RIGHTS_HELD_MANUAL_ONLY")

    def test_source_native_semantics_are_frozen(self):
        updates = self.plan["source_updates"]
        self.assertIn("Confirmed and provisional", updates["WSSRC-CB-005"]["set"]["governance_backfill_basis"])
        self.assertIn("08:50/09:30 JST", updates["WSSRC-MAC-025"]["set"]["governance_backfill_basis"])
        self.assertIn("Australia/Sydney", updates["WSSRC-MAC-011"]["set"]["governance_backfill_basis"])
        self.assertIn("mixed-regime", updates["WSSRC-CLIM-003"]["set"]["governance_backfill_basis"])
        self.assertIn("date-only", updates["WSSRC-REGJ-005"]["set"]["governance_backfill_basis"])
        self.assertIn("distinct publication occurrences", updates["WSSRC-CB-004"]["set"]["governance_backfill_basis"])

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

    def test_brazil_inauguration_guard_is_exact(self):
        guard = self.plan["preconditions"]["brazil_inauguration_guard"]
        matches = MIGRATION._brazil_inauguration_records(self.canonical, guard)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["start_local"], "2027-01-05")
        self.assertEqual(matches[0]["source_id"], "WSSRC-EL-BR-001")
        self.assertEqual(matches[0]["election_milestone_type"], "INAUGURATION_OR_ASSUMPTION")

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
            self.assertIn("P1-E GOVERNANCE PRECONDITION FAILED", result.stderr + result.stdout)

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
            self.assertIn("P1-E APPLY REFUSED", combined)
        else:
            self.assertIn("P1-E GOVERNANCE PRECONDITION FAILED", combined)


if __name__ == "__main__":
    unittest.main()
