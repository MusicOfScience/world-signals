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
MODULE_PATH = ROOT / "scripts/apply_vietnam_source_scope_repair_a.py"
SPEC = importlib.util.spec_from_file_location("apply_vietnam_source_scope_repair_a", MODULE_PATH)
REPAIR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(REPAIR)

PLAN_PATH = ROOT / "data/coverage/VIETNAM_SOURCE_SCOPE_REPAIR_A_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"


class VietnamSourceScopeRepairATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        cls.canonical = json.loads(CANONICAL_PATH.read_text(encoding="utf-8"))
        cls.sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
        cls.ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
        cls.overlay = json.loads(OVERLAY_PATH.read_text(encoding="utf-8"))
        cls.expectations = json.loads(EXPECTATIONS_PATH.read_text(encoding="utf-8"))

    def _source_ids(self) -> set[str]:
        return {row.get("source_id") for row in self.sources.get("sources", [])}

    def _is_pre(self) -> bool:
        return (
            self.canonical.get("version") == "0.21"
            and self.sources.get("version") == "1.62"
            and self.ledger.get("version") == "0.10"
            and "WSSRC-REG5-002" not in self._source_ids()
        )

    def _is_post(self) -> bool:
        return (
            tuple(int(p) for p in str(self.canonical.get("version")).split(".")) >= (0, 22)
            and "WSSRC-REG5-002" in self._source_ids()
            and any(c.get("change_id") == self.plan["change_ledger_entry"]["change_id"] for c in self.ledger.get("changes", []))
        )

    def _simulate(self):
        if not self._is_pre():
            self.skipTest("simulation is exercised only from the exact pre-repair checkpoint")
        return REPAIR.build_post_state(
            self.canonical,
            self.sources,
            self.ledger,
            self.overlay,
            self.expectations,
            self.plan,
            committed_at=self.plan["change_ledger_entry"]["reviewed_at"],
        )

    def test_plan_is_provenance_repair_not_date_repair(self):
        update = self.plan["canonical_update"]
        self.assertEqual(update["occurrence_id"], "WSO-REG-G-0001")
        self.assertEqual(update["must_preserve"]["start_local"], "2026-10-20")
        self.assertEqual(update["set"]["source_id"], "WSSRC-REG5-002")
        self.assertEqual(update["set"]["primary_source_assertion_id"], "WSA-6b2aa27a0df846dc")
        self.assertEqual(self.plan["postconditions"]["canonical_record_count"], 669)
        self.assertNotIn("committed_at", self.plan["change_ledger_entry"])
        self.assertIn("SET_AT_APPLY_TIME", self.plan["ledger_commit_timestamp_policy"])

    def test_source_split_preserves_stable_old_source_identity(self):
        self.assertEqual(set(self.plan["source_updates"]), {"WSSRC-REG5-001"})
        self.assertEqual([s["source_id"] for s in self.plan["new_sources"]], ["WSSRC-REG5-002"])
        old = self.plan["source_updates"]["WSSRC-REG5-001"]
        self.assertIn("Government Electronic Newspaper", old["expected"]["institution"])
        self.assertEqual(old["set"]["verification_mode"], "MANUAL_AUTHORITATIVE_RECHECK")
        new = self.plan["new_sources"][0]
        self.assertIn("National Assembly", new["institution"])
        self.assertEqual(new["canonical_dependency_count"], 1)

    def test_first_order_source_is_manual_only_under_rights_hold(self):
        new = self.plan["new_sources"][0]
        self.assertEqual(new["canonical_provenance_use"], "MANUAL_INFORMATIONAL_REFERENCE_ONLY")
        self.assertEqual(new["automated_monitoring_use"], "PROHIBITED_OR_RIGHTS_HOLD")
        self.assertEqual(new["verification_mode"], "RIGHTS_HELD_MANUAL_ONLY")
        self.assertEqual(new["monitoring_activation_status"], "MANUAL_AUTHORITATIVE_RECHECK_ONLY")
        self.assertEqual(new["monitoring_readiness_status"], "RIGHTS_AUDIT_REQUIRED")

    def test_repository_is_exact_pre_state_or_reviewed_repair_lineage(self):
        self.assertTrue(self._is_pre() or self._is_post())
        if self._is_pre():
            REPAIR.preflight(self.canonical, self.sources, self.ledger, self.overlay, self.expectations, self.plan)
            self.assertEqual(self.overlay["canonical_checkpoint"], {"registry_version": "0.21", "record_count": 669})
        else:
            occurrence = next(r for r in self.canonical["records"] if r["occurrence_id"] == "WSO-REG-G-0001")
            self.assertEqual(occurrence["source_id"], "WSSRC-REG5-002")
            self.assertEqual(occurrence["start_local"], "2026-10-20")
            self.assertEqual(occurrence["certainty_status"], "PROVISIONAL")
            self.assertEqual(self.overlay["canonical_checkpoint"], {"registry_version": self.canonical["version"], "record_count": 669})
            entry = next(c for c in self.ledger["changes"] if c.get("change_id") == self.plan["change_ledger_entry"]["change_id"])
            self.assertTrue(entry.get("committed_at"))
            planned = copy.deepcopy(entry)
            planned.pop("committed_at")
            self.assertEqual(planned, self.plan["change_ledger_entry"])

    def test_simulated_post_state_changes_only_one_occurrence_and_no_timing(self):
        canonical_post, sources_post, ledger_post, overlay_post, report = self._simulate()
        before = {r["occurrence_id"]: r for r in self.canonical["records"]}
        after = {r["occurrence_id"]: r for r in canonical_post["records"]}
        self.assertEqual(report["changed_occurrence_ids"], ["WSO-REG-G-0001"])
        self.assertEqual(report["changed_existing_source_ids"], ["WSSRC-REG5-001"])
        self.assertEqual(report["new_source_ids"], ["WSSRC-REG5-002"])
        for oid in before:
            for field in REPAIR.TIMING_FIELDS:
                self.assertEqual(after[oid].get(field), before[oid].get(field), (oid, field))
        self.assertEqual(after["WSO-REG-G-0001"]["session_phases"], before["WSO-REG-G-0001"]["session_phases"])
        self.assertEqual(sources_post["version"], "1.63")
        self.assertEqual(len(sources_post["sources"]), 225)
        self.assertEqual(ledger_post["version"], "0.11")
        self.assertEqual(overlay_post["canonical_checkpoint"], {"registry_version": "0.22", "record_count": 669})
        self.assertEqual(report["derived_dependency_counts"], {"WSSRC-REG5-001": 0, "WSSRC-REG5-002": 1})
        self.assertEqual(report["governance"], {"fully_explicit": 67, "missing_any": 158, "p1_canonical_dependent": 87, "p2_registry_only": 71})

    def test_assertion_identity_is_exact(self):
        if self._is_pre():
            canonical_post, _, _, _, _ = self._simulate()
            row = next(r for r in canonical_post["records"] if r["occurrence_id"] == "WSO-REG-G-0001")
        else:
            row = next(r for r in self.canonical["records"] if r["occurrence_id"] == "WSO-REG-G-0001")
        self.assertEqual(REPAIR._assertion_id(row), "WSA-6b2aa27a0df846dc")
        self.assertEqual(row["primary_source_assertion_id"], "WSA-6b2aa27a0df846dc")
        self.assertEqual(row["last_successful_assertion_id"], "WSA-6b2aa27a0df846dc")
        self.assertEqual(row["start_local"], "2026-10-20")

    def test_safety_controls_remain_closed(self):
        self.assertEqual(self.expectations["version"], "0.7")
        self.assertFalse(self.expectations["automatic_canonical_commit"])
        self.assertFalse(self.expectations["google_calendar_write"])

    def test_cli_is_read_only_preflight_or_blocks_replay(self):
        paths = (CANONICAL_PATH, SOURCES_PATH, LEDGER_PATH, OVERLAY_PATH, EXPECTATIONS_PATH)
        before = {p: p.read_bytes() for p in paths}
        result = subprocess.run([sys.executable, str(MODULE_PATH)], cwd=ROOT, capture_output=True, text=True, check=False)
        for path, raw in before.items():
            self.assertEqual(path.read_bytes(), raw)
        if self._is_pre():
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["mode"], "READ_ONLY_PREFLIGHT")
        else:
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("VIETNAM SOURCE SCOPE REPAIR A PRECONDITION FAILED", result.stderr + result.stdout)

    def test_apply_without_environment_gate_never_writes(self):
        paths = (CANONICAL_PATH, SOURCES_PATH, LEDGER_PATH, OVERLAY_PATH, EXPECTATIONS_PATH)
        before = {p: p.read_bytes() for p in paths}
        env = dict(os.environ)
        env.pop(REPAIR.APPLY_ENV, None)
        result = subprocess.run([sys.executable, str(MODULE_PATH), "--apply"], cwd=ROOT, env=env, capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        for path, raw in before.items():
            self.assertEqual(path.read_bytes(), raw)
        combined = result.stderr + result.stdout
        if self._is_pre():
            self.assertIn("VIETNAM SOURCE SCOPE REPAIR A APPLY REFUSED", combined)
        else:
            self.assertIn("VIETNAM SOURCE SCOPE REPAIR A PRECONDITION FAILED", combined)


if __name__ == "__main__":
    unittest.main()
