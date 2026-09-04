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
    assert_source_registry_compatible,
    repair_a_active,
)

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/apply_provenance_scope_repair_a.py"
SPEC = importlib.util.spec_from_file_location("apply_provenance_scope_repair_a", MODULE_PATH)
REPAIR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(REPAIR)

PLAN_PATH = ROOT / "data/coverage/PROVENANCE_SCOPE_REPAIR_A_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"


class ProvenanceScopeRepairATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        cls.canonical = json.loads(CANONICAL_PATH.read_text(encoding="utf-8"))
        cls.sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
        cls.ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
        cls.overlay = json.loads(OVERLAY_PATH.read_text(encoding="utf-8"))
        cls.expectations = json.loads(EXPECTATIONS_PATH.read_text(encoding="utf-8"))

    def _is_pre(self) -> bool:
        return (
            self.canonical.get("version") == "0.20"
            and self.sources.get("version") == "1.60"
            and self.ledger.get("version") == "0.9"
            and not repair_a_active(self.sources)
        )

    def _is_post(self) -> bool:
        return (
            tuple(int(p) for p in str(self.canonical.get("version")).split(".")) >= (0, 21)
            and repair_a_active(self.sources)
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
        self.assertEqual(update["occurrence_id"], "WSO-EL-A-0004")
        self.assertEqual(update["must_preserve"]["start_local"], "2027-01-05")
        self.assertEqual(update["set"]["source_id"], "WSSRC-EL-BR-002")
        self.assertEqual(update["set"]["election_date_basis"], "CONSTITUTIONAL_RULE_DERIVED")
        self.assertEqual(update["set"]["primary_source_assertion_id"], "WSA-66b042250a27801e")
        self.assertEqual(self.plan["postconditions"]["canonical_record_count"], 669)
        self.assertNotIn("committed_at", self.plan["change_ledger_entry"])
        self.assertIn("SET_AT_APPLY_TIME", self.plan["ledger_commit_timestamp_policy"])

    def test_source_decomposition_and_overlay_checkpoint_are_exact(self):
        self.assertEqual(set(self.plan["source_updates"]), {"WSSRC-EL-BR-001", "WSSRC-CB-009"})
        self.assertEqual([s["source_id"] for s in self.plan["new_sources"]], ["WSSRC-EL-BR-002"])
        self.assertEqual(self.plan["source_updates"]["WSSRC-EL-BR-001"]["set"]["canonical_dependency_count"], 3)
        self.assertEqual(self.plan["new_sources"][0]["canonical_dependency_count"], 1)
        self.assertEqual(
            self.plan["source_updates"]["WSSRC-CB-009"]["set"]["authoritative_url"],
            "https://www.snb.ch/en/services-events/digital-services/event-schedule",
        )
        self.assertEqual(self.plan["preconditions"]["biosecurity_overlay"]["canonical_checkpoint_registry_version"], "0.20")
        self.assertEqual(self.plan["postconditions"]["biosecurity_overlay"]["canonical_checkpoint_registry_version"], "0.21")

    def test_content_reuse_and_automation_remain_separate(self):
        rows = [self.plan["source_updates"][sid]["set"] for sid in ("WSSRC-EL-BR-001", "WSSRC-CB-009")]
        rows.append(self.plan["new_sources"][0])
        for row in rows:
            self.assertEqual(row["canonical_provenance_use"], "CLEARED_CURATED_FACTUAL_METADATA")
            self.assertEqual(row["automated_monitoring_use"], "ENDPOINT_REVIEW_REQUIRED")
            self.assertEqual(row["verification_mode"], "MANUAL_AUTHORITATIVE_RECHECK")

    def test_repository_is_exact_pre_state_or_reviewed_repair_lineage(self):
        self.assertTrue(self._is_pre() or self._is_post())
        if self._is_pre():
            REPAIR.preflight(self.canonical, self.sources, self.ledger, self.overlay, self.expectations, self.plan)
            self.assertEqual(self.overlay["canonical_checkpoint"], {"registry_version": "0.20", "record_count": 669})
        else:
            assert_source_registry_compatible(self, self.sources)
            assert_brazil_inauguration_compatible(self, self.canonical)
            self.assertEqual(self.overlay["canonical_checkpoint"], {"registry_version": self.canonical["version"], "record_count": 669})
            entry = next(c for c in self.ledger["changes"] if c.get("change_id") == self.plan["change_ledger_entry"]["change_id"])
            self.assertTrue(entry.get("committed_at"))
            planned = copy.deepcopy(entry)
            planned.pop("committed_at")
            self.assertEqual(planned, self.plan["change_ledger_entry"])

    def test_simulated_post_state_changes_no_timing_and_no_snb_occurrence(self):
        canonical_post, sources_post, ledger_post, overlay_post, report = self._simulate()
        before = {r["occurrence_id"]: r for r in self.canonical["records"]}
        after = {r["occurrence_id"]: r for r in canonical_post["records"]}
        self.assertEqual(report["changed_occurrence_ids"], ["WSO-EL-A-0004"])
        self.assertEqual(set(report["changed_existing_source_ids"]), {"WSSRC-EL-BR-001", "WSSRC-CB-009"})
        self.assertEqual(report["new_source_ids"], ["WSSRC-EL-BR-002"])
        for oid in before:
            for field in REPAIR.TIMING_FIELDS:
                self.assertEqual(after[oid].get(field), before[oid].get(field), (oid, field))
        snb_before = [r for r in self.canonical["records"] if r.get("source_id") == "WSSRC-CB-009"]
        snb_after = [r for r in canonical_post["records"] if r.get("source_id") == "WSSRC-CB-009"]
        self.assertEqual(len(snb_before), 18)
        self.assertEqual(snb_after, snb_before)
        self.assertEqual(sources_post["version"], "1.61")
        self.assertEqual(len(sources_post["sources"]), 224)
        self.assertEqual(ledger_post["version"], "0.10")
        self.assertEqual(overlay_post["canonical_checkpoint"], {"registry_version": "0.21", "record_count": 669})

    def test_brazil_assertion_identity_is_exact_in_simulation_or_post_state(self):
        if self._is_pre():
            canonical_post, _, _, _, _ = self._simulate()
            row = next(r for r in canonical_post["records"] if r["occurrence_id"] == "WSO-EL-A-0004")
        else:
            row = next(r for r in self.canonical["records"] if r["occurrence_id"] == "WSO-EL-A-0004")
        self.assertEqual(REPAIR._assertion_id(row), "WSA-66b042250a27801e")
        self.assertEqual(row["primary_source_assertion_id"], "WSA-66b042250a27801e")
        self.assertEqual(row["last_successful_assertion_id"], "WSA-66b042250a27801e")
        self.assertEqual(row["start_local"], "2027-01-05")

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
            self.assertIn("PROVENANCE REPAIR A PRECONDITION FAILED", result.stderr + result.stdout)

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
            self.assertIn("PROVENANCE REPAIR A APPLY REFUSED", combined)
        else:
            self.assertIn("PROVENANCE REPAIR A PRECONDITION FAILED", combined)


if __name__ == "__main__":
    unittest.main()
