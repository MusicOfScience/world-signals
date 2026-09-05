from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/apply_p1_balanced_governance_d.py"
SPEC = importlib.util.spec_from_file_location("apply_p1_balanced_governance_d", MODULE_PATH)
TX = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TX)

PLAN_PATH = ROOT / "data/coverage/P1_BALANCED_GOVERNANCE_D_PLAN_v0.1.json"
RESEARCH_PATH = ROOT / "data/coverage/P1_BALANCED_GOVERNANCE_D_RESEARCH_v0.1.md"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"


class P1BalancedGovernanceDTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        cls.research = RESEARCH_PATH.read_text(encoding="utf-8")
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
            self.canonical.get("version") == "0.24"
            and self.sources.get("version") == "1.65"
            and self.ledger.get("version") == "0.13"
        )

    def _is_post(self) -> bool:
        change_id = self.plan["ledger_entries"][0]["change_id"]
        return self._version_tuple(self.canonical.get("version")) >= (0, 25) and change_id in self._ledger_ids()

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
            committed_at="2026-09-05T16:30:00+10:00",
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
            self.assertEqual(self.overlay["canonical_checkpoint"]["registry_version"], self.canonical["version"])
            self.assertEqual(self.overlay["canonical_checkpoint"]["record_count"], len(self.canonical["records"]))

    def test_plan_is_exactly_eight_existing_sources_plus_one_wto_legal_source(self):
        expected = {
            "WSSRC-RISK-002",
            "WSSRC-COM-009",
            "WSSRC-COM-008",
            "WSSRC-INT-013",
            "WSSRC-HEALTH-002",
            "WSSRC-TRD-002",
            "WSSRC-REG2-003",
            "WSSRC-EL-VIC-001",
        }
        self.assertEqual(set(self.plan["source_updates"]), expected)
        self.assertEqual(set(TX.SELECTED_SOURCES), expected)
        self.assertEqual(len(self.plan["new_sources"]), 1)
        self.assertEqual(self.plan["new_sources"][0]["source_id"], "WSSRC-TRD-008")
        self.assertEqual(self.plan["new_sources"][0]["canonical_dependency_count"], 0)

    def test_research_does_not_claim_governance_backfill_repairs_coverage(self):
        self.assertIn("no forward-active P1 source remains in South Asia", self.research)
        self.assertIn("coverage/population research problem", self.research)
        self.assertIn("Closing its governance contract does **not** add canonical series diversity", self.research)

    def test_wto_is_provenance_repair_not_date_repair(self):
        self.assertEqual(set(self.plan["canonical_updates"]), {"WSO-TRD-A-0002"})
        update = self.plan["canonical_updates"]["WSO-TRD-A-0002"]["set"]
        self.assertEqual(update["legal_basis_source_id"], "WSSRC-TRD-008")
        self.assertEqual(update["governing_instrument"], "WTO Dispute Settlement Understanding, Article 4.7")
        for forbidden in (
            "start_local",
            "end_local",
            "start_utc",
            "end_utc",
            "date_earliest",
            "date_latest",
            "timing_type",
            "time_precision",
            "time_status",
            "certainty_status",
            "activation_mode",
            "condition_state",
            "source_id",
            "primary_source_assertion_id",
            "last_successful_assertion_id",
        ):
            self.assertNotIn(forbidden, update)
        baseline = self.plan["preconditions"]["wto_occurrence"]
        self.assertEqual(baseline["date_earliest"], "2026-09-25")
        self.assertEqual(baseline["date_latest"], "2026-09-28")
        self.assertEqual(baseline["certainty_status"], "PROVISIONAL")
        self.assertEqual(baseline["activation_mode"], "CONDITIONAL")
        self.assertEqual(baseline["condition_state"], "PENDING")
        self.assertTrue(baseline["procedural_eligibility_only"])

    def test_wto_source_roles_are_separated(self):
        status = self.plan["source_updates"]["WSSRC-TRD-002"]
        legal = self.plan["new_sources"][0]
        self.assertEqual(status["backup_source"], "WSSRC-TRD-008")
        self.assertIn("dispute-status", status["governance_backfill_basis"])
        self.assertEqual(legal["source_type"], "official_multilateral_legal_text")
        self.assertIn("Article 4.7", legal["endpoint_role"])
        self.assertIn("receipt", legal["known_limitations"][0].lower())
        self.assertEqual(legal["monitoring_activation_status"], "MANUAL_AUTHORITATIVE_RECHECK_ONLY")

    def test_no_selected_source_is_promoted_to_automated_pilot(self):
        for sid, update in self.plan["source_updates"].items():
            self.assertNotEqual(update["verification_mode"], "AUTOMATED_PILOT", sid)
        self.assertNotEqual(self.plan["new_sources"][0]["verification_mode"], "AUTOMATED_PILOT")
        self.assertIn("no source-specific implementation or fixture evidence", self.research)

    def test_rights_held_sources_are_explicit_negative_controls(self):
        for sid in ("WSSRC-HEALTH-002", "WSSRC-REG2-003"):
            update = self.plan["source_updates"][sid]
            self.assertEqual(update["canonical_provenance_use"], "MANUAL_INFORMATIONAL_REFERENCE_ONLY", sid)
            self.assertEqual(update["automated_monitoring_use"], "PROHIBITED_OR_RIGHTS_HOLD", sid)
            self.assertEqual(update["verification_mode"], "RIGHTS_HELD_MANUAL_ONLY", sid)

    def test_cleared_sources_still_require_endpoint_review(self):
        cleared = (
            "WSSRC-RISK-002",
            "WSSRC-COM-009",
            "WSSRC-COM-008",
            "WSSRC-INT-013",
            "WSSRC-TRD-002",
            "WSSRC-EL-VIC-001",
        )
        for sid in cleared:
            update = self.plan["source_updates"][sid]
            self.assertEqual(update["canonical_provenance_use"], "CLEARED_CURATED_FACTUAL_METADATA", sid)
            self.assertEqual(update["automated_monitoring_use"], "ENDPOINT_REVIEW_REQUIRED", sid)
            self.assertEqual(update["verification_mode"], "MANUAL_AUTHORITATIVE_RECHECK", sid)

    def test_brics_preserves_source_family_and_adds_specific_backup(self):
        update = self.plan["source_updates"]["WSSRC-INT-013"]
        self.assertIn("PressReleasePage.aspx?PRID=2305262", update["backup_source"])
        self.assertIn("12–13 September 2026", update["governance_backfill_basis"])
        self.assertNotIn("BRICS", self.plan["new_sources"][0]["endpoint_role"])

    def test_ledger_is_one_provenance_entry_and_committed_at_is_not_frozen(self):
        entries = self.plan["ledger_entries"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["occurrence_id"], "WSO-TRD-A-0002")
        self.assertEqual(entries[0]["change_type"], "PROVENANCE_SCOPE_REPAIR")
        self.assertNotIn("committed_at", entries[0])
        self.assertIn("SET_AT_APPLY_TIME", self.plan["ledger_commit_timestamp_policy"])

    def test_simulated_post_state_is_exact(self):
        canonical_post, sources_post, ledger_post, overlay_post, report = self._simulate()
        before_records = {r["occurrence_id"]: r for r in self.canonical["records"]}
        after_records = {r["occurrence_id"]: r for r in canonical_post["records"]}

        self.assertEqual(report["changed_occurrences"], ["WSO-TRD-A-0002"])
        self.assertEqual(set(report["changed_existing_sources"]), set(TX.SELECTED_SOURCES))
        self.assertEqual(report["new_source"], "WSSRC-TRD-008")
        self.assertEqual(canonical_post["version"], "0.25")
        self.assertEqual(len(canonical_post["records"]), 669)
        self.assertEqual(sources_post["version"], "1.66")
        self.assertEqual(len(sources_post["sources"]), 227)
        self.assertEqual(ledger_post["version"], "0.14")
        self.assertEqual(overlay_post["canonical_checkpoint"], {"registry_version": "0.25", "record_count": 669})
        self.assertEqual(
            report["governance"],
            {"fully_explicit": 90, "missing_any": 137, "p1_canonical_dependent": 66, "p2_registry_only": 71},
        )

        wto_before = before_records["WSO-TRD-A-0002"]
        wto_after = after_records["WSO-TRD-A-0002"]
        for field in TX.WTO_PROTECTED_FIELDS:
            self.assertEqual(wto_before.get(field), wto_after.get(field), field)
        self.assertEqual(wto_after["legal_basis_source_id"], "WSSRC-TRD-008")
        self.assertEqual(wto_after["date_earliest"], "2026-09-25")
        self.assertEqual(wto_after["date_latest"], "2026-09-28")

    def test_every_non_wto_canonical_record_is_byte_identical_in_simulation(self):
        canonical_post, _, _, _, _ = self._simulate()
        before = {r["occurrence_id"]: r for r in self.canonical["records"]}
        after = {r["occurrence_id"]: r for r in canonical_post["records"]}
        for oid, row in before.items():
            if oid != "WSO-TRD-A-0002":
                self.assertEqual(row, after[oid], oid)

    def test_global_write_gates_remain_closed(self):
        self.assertEqual(self.expectations["version"], "0.7")
        self.assertFalse(self.expectations["automatic_canonical_commit"])
        self.assertFalse(self.expectations["google_calendar_write"])

    def test_cli_read_only_path_never_writes(self):
        paths = (CANONICAL_PATH, SOURCES_PATH, LEDGER_PATH, OVERLAY_PATH, EXPECTATIONS_PATH)
        before = {path: path.read_bytes() for path in paths}
        result = subprocess.run(
            [sys.executable, str(MODULE_PATH), "--committed-at", "2026-09-05T16:30:00+10:00"],
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
            self.assertIn("P1 BALANCED GOVERNANCE D PRECONDITION FAILED", result.stderr + result.stdout)

    def test_apply_without_environment_gate_never_writes(self):
        paths = (CANONICAL_PATH, SOURCES_PATH, LEDGER_PATH, OVERLAY_PATH, EXPECTATIONS_PATH)
        before = {path: path.read_bytes() for path in paths}
        env = dict(os.environ)
        env.pop(TX.APPLY_ENV, None)
        result = subprocess.run(
            [sys.executable, str(MODULE_PATH), "--apply", "--committed-at", "2026-09-05T16:30:00+10:00"],
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
            self.assertIn("P1 BALANCED GOVERNANCE D PRECONDITION FAILED", combined)


if __name__ == "__main__":
    unittest.main()
