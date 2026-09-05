from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/apply_p1_balanced_governance_c.py"
SPEC = importlib.util.spec_from_file_location("apply_p1_balanced_governance_c", MODULE_PATH)
TX = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TX)

PLAN_PATH = ROOT / "data/coverage/P1_BALANCED_GOVERNANCE_C_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"


class P1BalancedGovernanceCTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        cls.canonical = json.loads(CANONICAL_PATH.read_text(encoding="utf-8"))
        cls.sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
        cls.ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
        cls.overlay = json.loads(OVERLAY_PATH.read_text(encoding="utf-8"))
        cls.expectations = json.loads(EXPECTATIONS_PATH.read_text(encoding="utf-8"))

    def _ledger_ids(self) -> set[str]:
        return {row.get("change_id") for row in self.ledger.get("changes", [])}

    def _version_tuple(self, value: object) -> tuple[int, ...]:
        return tuple(int(part) for part in str(value).split("."))

    def _is_pre(self) -> bool:
        return (
            self.canonical.get("version") == "0.23"
            and self.sources.get("version") == "1.64"
            and self.ledger.get("version") == "0.12"
        )

    def _is_post(self) -> bool:
        change_id = self.plan["ledger_entries"][0]["change_id"]
        return self._version_tuple(self.canonical.get("version")) >= (0, 24) and change_id in self._ledger_ids()

    def _simulate(self):
        if not self._is_pre():
            self.skipTest("simulation is exercised only from the exact pre-transaction checkpoint")
        return TX.build_post_state(
            self.canonical,
            self.sources,
            self.ledger,
            self.overlay,
            self.expectations,
            self.plan,
            committed_at="2026-09-05T12:15:00+10:00",
        )

    def test_repository_is_exact_pre_state_or_reviewed_post_lineage(self):
        self.assertTrue(self._is_pre() or self._is_post())
        if self._is_pre():
            TX.preflight(
                self.canonical,
                self.sources,
                self.ledger,
                self.overlay,
                self.expectations,
                self.plan,
            )
        else:
            self.assertEqual(
                self.overlay["canonical_checkpoint"]["registry_version"],
                self.canonical["version"],
            )
            self.assertEqual(
                self.overlay["canonical_checkpoint"]["record_count"],
                len(self.canonical["records"]),
            )

    def test_plan_is_exactly_seven_sources_and_geographically_corrective(self):
        expected = {
            "WSSRC-REGJ-002",
            "WSSRC-RISK-001",
            "WSSRC-REG2-004",
            "WSSRC-HEALTH-004",
            "WSSRC-REG-009",
            "WSSRC-INT-018",
            "WSSRC-COM-005",
        }
        self.assertEqual(set(self.plan["source_updates"]), expected)
        self.assertEqual(set(TX.SELECTED_SOURCES), expected)
        self.assertEqual(len(self.plan["source_updates"]), 7)

    def test_only_malaysia_is_a_canonical_mutation(self):
        self.assertEqual(set(self.plan["canonical_updates"]), {"WSO-REG-A-0014"})
        fields = self.plan["canonical_updates"]["WSO-REG-A-0014"]["set"]
        self.assertEqual(fields["population_horizon_policy"], "EXACT_LEGAL_OR_POLICY_MILESTONE_ONLY")
        for forbidden in (
            "start_local",
            "end_local",
            "start_utc",
            "end_utc",
            "date_earliest",
            "date_latest",
            "certainty_status",
            "source_id",
        ):
            self.assertNotIn(forbidden, fields)
        self.assertEqual(self.plan["preconditions"]["malaysia_occurrence"]["start_local"], "2026-10-09")
        self.assertEqual(self.plan["preconditions"]["malaysia_occurrence"]["certainty_status"], "CONFIRMED")

    def test_rights_holds_are_not_mistaken_for_automation_permission(self):
        held = {
            "WSSRC-REGJ-002",
            "WSSRC-RISK-001",
            "WSSRC-REG2-004",
            "WSSRC-HEALTH-004",
            "WSSRC-REG-009",
            "WSSRC-INT-018",
        }
        for sid in held:
            update = self.plan["source_updates"][sid]
            self.assertEqual(update["automated_monitoring_use"], "PROHIBITED_OR_RIGHTS_HOLD", sid)
            self.assertEqual(update["verification_mode"], "RIGHTS_HELD_MANUAL_ONLY", sid)
            self.assertEqual(update["canonical_provenance_use"], "MANUAL_INFORMATIONAL_REFERENCE_ONLY", sid)

    def test_usda_machine_readability_does_not_create_automated_pilot(self):
        update = self.plan["source_updates"]["WSSRC-COM-005"]
        self.assertEqual(update["canonical_provenance_use"], "CLEARED_CURATED_FACTUAL_METADATA")
        self.assertEqual(update["automated_monitoring_use"], "ENDPOINT_REVIEW_REQUIRED")
        self.assertEqual(update["verification_mode"], "MANUAL_AUTHORITATIVE_RECHECK")
        self.assertIn("no NASS-specific parser implementation", update["governance_backfill_basis"])

    def test_afdb_keeps_stable_source_family_and_direct_resolution_backup(self):
        baseline = self.plan["preconditions"]["source_baselines"]["WSSRC-INT-018"]
        self.assertIn("official-records-of-the-annual-meetings", baseline["authoritative_url"])
        update = self.plan["source_updates"]["WSSRC-INT-018"]
        self.assertIn("2021_annual_meetings_-_official_record.pdf", update["backup_source"])
        self.assertIn("fallback", " ".join(update["known_limitations"]).lower())
        self.assertNotIn("WSSRC-INT-018", json.dumps(self.plan.get("new_sources", [])))

    def test_bom_page_element_cc_does_not_become_blanket_permission(self):
        update = self.plan["source_updates"]["WSSRC-RISK-001"]
        self.assertIn("page/element", update["governance_backfill_basis"])
        self.assertEqual(update["canonical_provenance_use"], "MANUAL_INFORMATIONAL_REFERENCE_ONLY")
        self.assertEqual(update["verification_mode"], "RIGHTS_HELD_MANUAL_ONLY")

    def test_ledger_is_one_semantic_entry_and_committed_at_is_not_frozen(self):
        entries = self.plan["ledger_entries"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["occurrence_id"], "WSO-REG-A-0014")
        self.assertEqual(entries[0]["change_type"], "CANONICAL_SEMANTIC_CLASSIFICATION_REPAIR")
        self.assertNotIn("committed_at", entries[0])
        self.assertIn("SET_AT_APPLY_TIME", self.plan["ledger_commit_timestamp_policy"])

    def test_simulated_post_state_is_exact(self):
        canonical_post, sources_post, ledger_post, overlay_post, report = self._simulate()
        before_records = {r["occurrence_id"]: r for r in self.canonical["records"]}
        after_records = {r["occurrence_id"]: r for r in canonical_post["records"]}

        self.assertEqual(report["changed_occurrences"], ["WSO-REG-A-0014"])
        self.assertEqual(set(report["changed_sources"]), set(TX.SELECTED_SOURCES))
        self.assertEqual(canonical_post["version"], "0.24")
        self.assertEqual(len(canonical_post["records"]), 669)
        self.assertEqual(sources_post["version"], "1.65")
        self.assertEqual(len(sources_post["sources"]), 226)
        self.assertEqual(ledger_post["version"], "0.13")
        self.assertEqual(
            overlay_post["canonical_checkpoint"],
            {"registry_version": "0.24", "record_count": 669},
        )
        self.assertEqual(
            report["governance"],
            {"fully_explicit": 81, "missing_any": 145, "p1_canonical_dependent": 74, "p2_registry_only": 71},
        )

        malaysia_before = before_records["WSO-REG-A-0014"]
        malaysia_after = after_records["WSO-REG-A-0014"]
        for field in TX.TIMING_AND_IDENTITY_FIELDS:
            self.assertEqual(malaysia_before.get(field), malaysia_after.get(field), field)
        self.assertEqual(malaysia_after["start_local"], "2026-10-09")
        self.assertEqual(malaysia_after["certainty_status"], "CONFIRMED")
        self.assertEqual(malaysia_after["population_horizon_policy"], "EXACT_LEGAL_OR_POLICY_MILESTONE_ONLY")

    def test_selected_non_malaysia_canonical_records_are_byte_identical_in_simulation(self):
        canonical_post, _, _, _, _ = self._simulate()
        before = {r["occurrence_id"]: r for r in self.canonical["records"]}
        after = {r["occurrence_id"]: r for r in canonical_post["records"]}
        selected_source_ids = set(TX.SELECTED_SOURCES) - {"WSSRC-REG-009"}
        for oid, row in before.items():
            if row.get("source_id") in selected_source_ids:
                self.assertEqual(row, after[oid], oid)

    def test_global_write_gates_remain_closed(self):
        self.assertFalse(self.expectations["automatic_canonical_commit"])
        self.assertFalse(self.expectations["google_calendar_write"])

    def test_cli_read_only_path_never_writes(self):
        paths = (CANONICAL_PATH, SOURCES_PATH, LEDGER_PATH, OVERLAY_PATH, EXPECTATIONS_PATH)
        before = {path: path.read_bytes() for path in paths}
        result = subprocess.run(
            [sys.executable, str(MODULE_PATH), "--committed-at", "2026-09-05T12:15:00+10:00"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        for path, raw in before.items():
            self.assertEqual(path.read_bytes(), raw)
        if self._is_pre():
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "PASS")
        else:
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("P1 BALANCED GOVERNANCE C PRECONDITION FAILED", result.stderr + result.stdout)

    def test_apply_without_environment_gate_never_writes(self):
        paths = (CANONICAL_PATH, SOURCES_PATH, LEDGER_PATH, OVERLAY_PATH, EXPECTATIONS_PATH)
        before = {path: path.read_bytes() for path in paths}
        env = dict(os.environ)
        env.pop(TX.APPLY_ENV, None)
        result = subprocess.run(
            [sys.executable, str(MODULE_PATH), "--apply", "--committed-at", "2026-09-05T12:15:00+10:00"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        for path, raw in before.items():
            self.assertEqual(path.read_bytes(), raw)
        combined = result.stderr + result.stdout
        if self._is_pre():
            self.assertIn("apply refused", combined)
        else:
            self.assertIn("P1 BALANCED GOVERNANCE C PRECONDITION FAILED", combined)


if __name__ == "__main__":
    unittest.main()
