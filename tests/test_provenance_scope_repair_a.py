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
MODULE_PATH = ROOT / "scripts/apply_provenance_scope_repair_a.py"
SPEC = importlib.util.spec_from_file_location("apply_provenance_scope_repair_a", MODULE_PATH)
REPAIR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(REPAIR)

PLAN_PATH = ROOT / "data/coverage/PROVENANCE_SCOPE_REPAIR_A_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"


class ProvenanceScopeRepairATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        cls.canonical = json.loads(CANONICAL_PATH.read_text(encoding="utf-8"))
        cls.sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
        cls.ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
        cls.expectations = json.loads(EXPECTATIONS_PATH.read_text(encoding="utf-8"))

    def _post_state(self):
        return REPAIR.build_post_state(
            self.canonical, self.sources, self.ledger, self.expectations, self.plan
        )

    def test_plan_is_provenance_repair_not_date_repair(self):
        update = self.plan["canonical_update"]
        self.assertEqual(update["occurrence_id"], "WSO-EL-A-0004")
        self.assertEqual(update["must_preserve"]["start_local"], "2027-01-05")
        self.assertEqual(update["set"]["source_id"], "WSSRC-EL-BR-002")
        self.assertEqual(update["set"]["election_date_basis"], "CONSTITUTIONAL_RULE_DERIVED")
        self.assertEqual(update["set"]["primary_source_assertion_id"], "WSA-66b042250a27801e")
        self.assertEqual(self.plan["postconditions"]["canonical_record_count"], 669)

    def test_source_decomposition_is_exact(self):
        self.assertEqual(set(self.plan["source_updates"]), {"WSSRC-EL-BR-001", "WSSRC-CB-009"})
        self.assertEqual(len(self.plan["new_sources"]), 1)
        self.assertEqual(self.plan["new_sources"][0]["source_id"], "WSSRC-EL-BR-002")
        self.assertEqual(self.plan["source_updates"]["WSSRC-EL-BR-001"]["set"]["canonical_dependency_count"], 3)
        self.assertEqual(self.plan["new_sources"][0]["canonical_dependency_count"], 1)
        self.assertEqual(self.plan["source_updates"]["WSSRC-CB-009"]["set"]["authoritative_url"], "https://www.snb.ch/en/services-events/digital-services/event-schedule")

    def test_content_reuse_and_automation_remain_separate(self):
        for source_id in ("WSSRC-EL-BR-001", "WSSRC-CB-009"):
            row = self.plan["source_updates"][source_id]["set"]
            self.assertEqual(row["canonical_provenance_use"], "CLEARED_CURATED_FACTUAL_METADATA")
            self.assertEqual(row["automated_monitoring_use"], "ENDPOINT_REVIEW_REQUIRED")
            self.assertEqual(row["verification_mode"], "MANUAL_AUTHORITATIVE_RECHECK")
        new = self.plan["new_sources"][0]
        self.assertEqual(new["canonical_provenance_use"], "CLEARED_CURATED_FACTUAL_METADATA")
        self.assertEqual(new["automated_monitoring_use"], "ENDPOINT_REVIEW_REQUIRED")
        self.assertEqual(new["verification_mode"], "MANUAL_AUTHORITATIVE_RECHECK")

    def test_simulation_changes_one_occurrence_two_existing_sources_and_adds_one_source(self):
        canonical_before = copy.deepcopy(self.canonical)
        sources_before = copy.deepcopy(self.sources)
        ledger_before = copy.deepcopy(self.ledger)
        canonical_post, sources_post, ledger_post, report = self._post_state()
        self.assertEqual(self.canonical, canonical_before)
        self.assertEqual(self.sources, sources_before)
        self.assertEqual(self.ledger, ledger_before)
        self.assertEqual(report["changed_occurrence_ids"], ["WSO-EL-A-0004"])
        self.assertEqual(set(report["changed_existing_source_ids"]), {"WSSRC-EL-BR-001", "WSSRC-CB-009"})
        self.assertEqual(report["new_source_ids"], ["WSSRC-EL-BR-002"])
        self.assertEqual(canonical_post["version"], "0.21")
        self.assertEqual(canonical_post["record_count"], 669)
        self.assertEqual(sources_post["version"], "1.61")
        self.assertEqual(len(sources_post["sources"]), 224)
        self.assertEqual(ledger_post["version"], "0.10")

    def test_every_canonical_date_and_time_is_byte_semantically_preserved(self):
        canonical_post, _, _, _ = self._post_state()
        before = {r["occurrence_id"]: r for r in self.canonical["records"]}
        after = {r["occurrence_id"]: r for r in canonical_post["records"]}
        for oid in before:
            for field in REPAIR.TIMING_FIELDS:
                self.assertEqual(after[oid].get(field), before[oid].get(field), (oid, field))

    def test_snb_18_canonical_records_are_unchanged(self):
        canonical_post, _, _, _ = self._post_state()
        before = [r for r in self.canonical["records"] if r.get("source_id") == "WSSRC-CB-009"]
        after = [r for r in canonical_post["records"] if r.get("source_id") == "WSSRC-CB-009"]
        self.assertEqual(len(before), 18)
        self.assertEqual(after, before)

    def test_brazil_assertion_identity_is_recomputed_from_repaired_source(self):
        canonical_post, _, _, _ = self._post_state()
        record = next(r for r in canonical_post["records"] if r["occurrence_id"] == "WSO-EL-A-0004")
        self.assertEqual(REPAIR._assertion_id(record), "WSA-66b042250a27801e")
        self.assertEqual(record["primary_source_assertion_id"], REPAIR._assertion_id(record))
        self.assertEqual(record["last_successful_assertion_id"], REPAIR._assertion_id(record))

    def test_change_ledger_appends_one_reviewed_provenance_entry(self):
        _, _, ledger_post, _ = self._post_state()
        self.assertEqual(len(ledger_post["changes"]), len(self.ledger["changes"]) + 1)
        self.assertEqual(ledger_post["changes"][:-1], self.ledger["changes"])
        entry = ledger_post["changes"][-1]
        self.assertEqual(entry["change_type"], "PROVENANCE_SCOPE_REPAIR")
        self.assertEqual(entry["occurrence_id"], "WSO-EL-A-0004")
        self.assertEqual(entry["old_values"]["source_id"], "WSSRC-EL-BR-001")
        self.assertEqual(entry["new_values"]["source_id"], "WSSRC-EL-BR-002")
        self.assertTrue(entry["canonical_mutation_committed"])

    def test_safety_controls_remain_closed(self):
        _, _, _, report = self._post_state()
        self.assertFalse(report["automatic_canonical_commit"])
        self.assertFalse(report["google_calendar_write"])
        self.assertEqual(self.expectations["version"], "0.7")

    def test_cli_is_read_only_by_default(self):
        before = {p: p.read_bytes() for p in (CANONICAL_PATH, SOURCES_PATH, LEDGER_PATH, EXPECTATIONS_PATH)}
        result = subprocess.run([sys.executable, str(MODULE_PATH)], cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["mode"], "READ_ONLY_PREFLIGHT")
        for path, raw in before.items():
            self.assertEqual(path.read_bytes(), raw)

    def test_apply_without_environment_gate_never_writes(self):
        before = {p: p.read_bytes() for p in (CANONICAL_PATH, SOURCES_PATH, LEDGER_PATH, EXPECTATIONS_PATH)}
        env = dict(os.environ)
        env.pop(REPAIR.APPLY_ENV, None)
        result = subprocess.run([sys.executable, str(MODULE_PATH), "--apply"], cwd=ROOT, env=env, capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PROVENANCE REPAIR A APPLY REFUSED", result.stderr + result.stdout)
        for path, raw in before.items():
            self.assertEqual(path.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
