from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/apply_p1_balanced_governance_e.py"
SPEC = importlib.util.spec_from_file_location("apply_p1_balanced_governance_e", MODULE_PATH)
TX = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TX)

PLAN_PATH = ROOT / "data/coverage/P1_BALANCED_GOVERNANCE_E_PLAN_v0.1.json"
RESEARCH_PATH = ROOT / "data/coverage/P1_BALANCED_GOVERNANCE_E_RESEARCH_v0.1.md"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"


class P1BalancedGovernanceETests(unittest.TestCase):
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
            self.canonical.get("version") == "0.25"
            and self.sources.get("version") == "1.66"
            and self.ledger.get("version") == "0.14"
        )

    def _is_post(self) -> bool:
        ids = {entry["change_id"] for entry in self.plan["ledger_entries"]}
        return self._version_tuple(self.canonical.get("version")) >= (0, 26) and ids.issubset(self._ledger_ids())

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
            committed_at="2026-09-05T17:20:00+10:00",
        )

    def test_repository_is_exact_pre_state_or_reviewed_post_lineage(self):
        self.assertTrue(self._is_pre() or self._is_post())
        if self._is_pre():
            TX.preflight(self.canonical, self.sources, self.ledger, self.overlay, self.expectations, self.plan)
        else:
            self.assertEqual(self.overlay["canonical_checkpoint"]["registry_version"], self.canonical["version"])
            self.assertEqual(self.overlay["canonical_checkpoint"]["record_count"], len(self.canonical["records"]))

    def test_plan_is_exactly_seven_existing_sources_plus_one_apec_source(self):
        expected = {
            "WSSRC-MAC-023",
            "WSSRC-REG-008",
            "WSSRC-COM-006",
            "WSSRC-CLIM-002",
            "WSSRC-INT-024",
            "WSSRC-INT-011",
            "WSSRC-INT-028",
        }
        self.assertEqual(set(self.plan["source_updates"]), expected)
        self.assertEqual(set(TX.SELECTED_SOURCES), expected)
        self.assertEqual(len(self.plan["new_sources"]), 1)
        self.assertEqual(self.plan["new_sources"][0]["source_id"], "WSSRC-INT-031")
        self.assertEqual(self.plan["new_sources"][0]["canonical_dependency_count"], 1)

    def test_research_keeps_governance_and_population_layers_separate(self):
        self.assertIn("does **not** claim to repair the remaining South Asia", self.research)
        self.assertIn("Governance backfill and canonical population are separate layers", self.research)

    def test_no_selected_source_is_promoted_to_automated_pilot(self):
        for sid, update in self.plan["source_updates"].items():
            self.assertNotEqual(update["verification_mode"], "AUTOMATED_PILOT", sid)
        self.assertNotEqual(self.plan["new_sources"][0]["verification_mode"], "AUTOMATED_PILOT")
        self.assertIn("no actual adapter/fixture/monitor implementation", self.research)

    def test_apec_is_provenance_repair_not_date_repair(self):
        update = self.plan["canonical_updates"]["WSO-INT-A-0012"]["set"]
        self.assertEqual(update["source_id"], "WSSRC-INT-031")
        self.assertEqual(update["primary_source_assertion_id"], "WSA-070677934abbc0f0")
        self.assertEqual(update["last_successful_assertion_id"], "WSA-070677934abbc0f0")
        for forbidden in ("start_local", "end_local", "date_earliest", "date_latest", "time_precision", "certainty_status"):
            self.assertNotIn(forbidden, update)
        baseline = self.plan["preconditions"]["canonical_baselines"]["WSO-INT-A-0012"]
        self.assertEqual(baseline["start_local"], "2026-11-18")
        self.assertEqual(baseline["end_local"], "2026-11-19")
        self.assertEqual(baseline["host_city"], "Shenzhen")
        self.assertEqual(baseline["certainty_status"], "CONFIRMED")

    def test_apec_source_roles_and_dependency_helpers_are_separated(self):
        old = self.plan["source_updates"]["WSSRC-INT-011"]
        new = self.plan["new_sources"][0]
        self.assertEqual(old["canonical_dependency_count"], 0)
        self.assertEqual(old["backup_source"], "WSSRC-INT-031")
        self.assertIn("month-level", old["information_supplied"])
        self.assertEqual(new["source_type"], "official_host_government_announcement")
        self.assertEqual(new["canonical_dependency_count"], 1)
        self.assertIn("18–19 November 2026", new["information_supplied"])

    def test_apec_assertion_hash_matches_new_source_identity(self):
        baseline = next(r for r in self.canonical["records"] if r["occurrence_id"] == "WSO-INT-A-0012")
        changed = dict(baseline)
        changed.update(self.plan["canonical_updates"]["WSO-INT-A-0012"]["set"])
        self.assertEqual(TX.assertion_id(changed), "WSA-070677934abbc0f0")

    def test_ipcc_uses_december_month_precision_without_inventing_day(self):
        for oid in ("WSO-CLIM-A-0009", "WSO-CLIM-A-0010"):
            update = self.plan["canonical_updates"][oid]["set"]
            self.assertEqual(update["date_earliest"], "2027-12-01")
            self.assertEqual(update["date_latest"], "2027-12-31")
            self.assertEqual(update["time_precision"], "MONTH")
            for forbidden in ("start_local", "end_local", "publication_datetime", "source_id", "certainty_status", "time_status"):
                self.assertNotIn(forbidden, update)
        self.assertIn("December 2027", self.research)

    def test_ndb_precision_repair_remains_completely_unscheduled(self):
        update = self.plan["canonical_updates"]["WSO-INT-B-0113"]["set"]
        self.assertEqual(update["time_precision"], "TBC")
        for forbidden in ("start_local", "end_local", "date_earliest", "date_latest", "host_city", "source_id", "certainty_status"):
            self.assertNotIn(forbidden, update)
        baseline = self.plan["preconditions"]["canonical_baselines"]["WSO-INT-B-0113"]
        self.assertIsNone(baseline["start_local"])
        self.assertIsNone(baseline["date_earliest"])
        self.assertIsNone(baseline["host_city"])
        self.assertTrue(baseline["host_confirmed"])
        self.assertEqual(baseline["host_jurisdiction"], "India")

    def test_rights_held_sources_are_explicit_negative_controls(self):
        for sid in ("WSSRC-CLIM-002", "WSSRC-INT-024", "WSSRC-INT-011", "WSSRC-INT-028"):
            update = self.plan["source_updates"][sid]
            self.assertEqual(update["canonical_provenance_use"], "MANUAL_INFORMATIONAL_REFERENCE_ONLY", sid)
            self.assertEqual(update["automated_monitoring_use"], "PROHIBITED_OR_RIGHTS_HOLD", sid)
            self.assertEqual(update["verification_mode"], "RIGHTS_HELD_MANUAL_ONLY", sid)

    def test_cleared_sources_still_require_endpoint_review(self):
        for sid in ("WSSRC-MAC-023", "WSSRC-REG-008", "WSSRC-COM-006"):
            update = self.plan["source_updates"][sid]
            self.assertEqual(update["canonical_provenance_use"], "CLEARED_CURATED_FACTUAL_METADATA", sid)
            self.assertEqual(update["automated_monitoring_use"], "ENDPOINT_REVIEW_REQUIRED", sid)
            self.assertEqual(update["verification_mode"], "MANUAL_AUTHORITATIVE_RECHECK", sid)

    def test_ledger_uses_existing_change_vocabulary_and_dynamic_commit_time(self):
        entries = self.plan["ledger_entries"]
        self.assertEqual(len(entries), 4)
        self.assertEqual([e["occurrence_id"] for e in entries], [
            "WSO-INT-A-0012", "WSO-CLIM-A-0009", "WSO-CLIM-A-0010", "WSO-INT-B-0113"
        ])
        self.assertEqual(entries[0]["change_type"], "PROVENANCE_SCOPE_REPAIR")
        self.assertEqual(entries[1]["change_type"], "LIFECYCLE_AND_CERTAINTY_UPDATE")
        self.assertEqual(entries[2]["change_type"], "LIFECYCLE_AND_CERTAINTY_UPDATE")
        self.assertEqual(entries[3]["change_type"], "CANONICAL_SEMANTIC_CLASSIFICATION_REPAIR")
        self.assertTrue(all("committed_at" not in e for e in entries))
        self.assertIn("SET_AT_APPLY_TIME", self.plan["ledger_commit_timestamp_policy"])

    def test_simulated_post_state_is_exact(self):
        canonical_post, sources_post, ledger_post, overlay_post, report = self._simulate()
        self.assertEqual(canonical_post["version"], "0.26")
        self.assertEqual(len(canonical_post["records"]), 669)
        self.assertEqual(sources_post["version"], "1.67")
        self.assertEqual(len(sources_post["sources"]), 228)
        self.assertEqual(ledger_post["version"], "0.15")
        self.assertEqual(overlay_post["canonical_checkpoint"], {"registry_version": "0.26", "record_count": 669})
        self.assertEqual(set(report["changed_occurrences"]), set(TX.CHANGED_OIDS))
        self.assertEqual(set(report["changed_existing_sources"]), set(TX.SELECTED_SOURCES))
        self.assertEqual(report["new_source"], "WSSRC-INT-031")
        self.assertEqual(report["governance"], {
            "fully_explicit": 98,
            "missing_any": 130,
            "p1_canonical_dependent": 59,
            "p2_registry_only": 71,
        })

    def test_every_non_authorised_canonical_record_is_byte_identical_in_simulation(self):
        canonical_post, _, _, _, _ = self._simulate()
        before = {r["occurrence_id"]: r for r in self.canonical["records"]}
        after = {r["occurrence_id"]: r for r in canonical_post["records"]}
        for oid, row in before.items():
            if oid not in TX.CHANGED_OIDS:
                self.assertEqual(row, after[oid], oid)

    def test_simulated_apec_ipcc_ndb_invariants(self):
        canonical_post, sources_post, _, _, _ = self._simulate()
        after = {r["occurrence_id"]: r for r in canonical_post["records"]}
        apec = after["WSO-INT-A-0012"]
        self.assertEqual((apec["start_local"], apec["end_local"]), ("2026-11-18", "2026-11-19"))
        self.assertEqual(apec["source_id"], "WSSRC-INT-031")
        self.assertEqual(apec["primary_source_assertion_id"], "WSA-070677934abbc0f0")
        for oid in ("WSO-CLIM-A-0009", "WSO-CLIM-A-0010"):
            row = after[oid]
            self.assertEqual((row["date_earliest"], row["date_latest"], row["time_precision"]), ("2027-12-01", "2027-12-31", "MONTH"))
        ndb = after["WSO-INT-B-0113"]
        self.assertEqual(ndb["time_precision"], "TBC")
        self.assertIsNone(ndb["start_local"])
        self.assertIsNone(ndb["date_earliest"])
        self.assertIsNone(ndb["host_city"])
        sm = {s["source_id"]: s for s in sources_post["sources"]}
        self.assertEqual(sm["WSSRC-INT-011"]["canonical_dependency_count"], 0)
        self.assertEqual(sm["WSSRC-INT-031"]["canonical_dependency_count"], 1)

    def test_global_write_gates_remain_closed(self):
        self.assertEqual(self.expectations["version"], "0.7")
        self.assertFalse(self.expectations["automatic_canonical_commit"])
        self.assertFalse(self.expectations["google_calendar_write"])

    def test_cli_read_only_path_never_writes(self):
        paths = (CANONICAL_PATH, SOURCES_PATH, LEDGER_PATH, OVERLAY_PATH, EXPECTATIONS_PATH)
        before = {path: path.read_bytes() for path in paths}
        result = subprocess.run(
            [sys.executable, str(MODULE_PATH), "--committed-at", "2026-09-05T17:20:00+10:00"],
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
            self.assertIn("P1 BALANCED GOVERNANCE E PRECONDITION FAILED", result.stderr + result.stdout)

    def test_apply_without_environment_gate_never_writes(self):
        paths = (CANONICAL_PATH, SOURCES_PATH, LEDGER_PATH, OVERLAY_PATH, EXPECTATIONS_PATH)
        before = {path: path.read_bytes() for path in paths}
        env = dict(os.environ)
        env.pop(TX.APPLY_ENV, None)
        result = subprocess.run(
            [sys.executable, str(MODULE_PATH), "--apply", "--committed-at", "2026-09-05T17:20:00+10:00"],
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
            self.assertIn("P1 BALANCED GOVERNANCE E PRECONDITION FAILED", combined)


if __name__ == "__main__":
    unittest.main()
