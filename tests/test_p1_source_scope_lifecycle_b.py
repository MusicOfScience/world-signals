from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/apply_p1_source_scope_lifecycle_b.py"
SPEC = importlib.util.spec_from_file_location("apply_p1_source_scope_lifecycle_b", MODULE_PATH)
REPAIR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(REPAIR)

PLAN_PATH = ROOT / "data/coverage/P1_SOURCE_SCOPE_LIFECYCLE_B_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"


class P1SourceScopeLifecycleBTests(unittest.TestCase):
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

    def _ledger_ids(self) -> set[str]:
        return {row.get("change_id") for row in self.ledger.get("changes", [])}

    def _is_pre(self) -> bool:
        return (
            self.canonical.get("version") == "0.22"
            and self.sources.get("version") == "1.63"
            and self.ledger.get("version") == "0.11"
            and "WSSRC-FIS-025" not in self._source_ids()
        )

    def _is_post(self) -> bool:
        planned = {row["change_id"] for row in self.plan["ledger_entries"]}
        return (
            tuple(int(p) for p in str(self.canonical.get("version")).split(".")) >= (0, 23)
            and "WSSRC-FIS-025" in self._source_ids()
            and planned.issubset(self._ledger_ids())
        )

    def _simulate(self):
        if not self._is_pre():
            self.skipTest("simulation is exercised only from the exact pre-transaction checkpoint")
        return REPAIR.build_post_state(
            self.canonical,
            self.sources,
            self.ledger,
            self.overlay,
            self.expectations,
            self.plan,
            committed_at="2026-09-05T08:30:00+10:00",
        )

    def test_repository_is_exact_pre_state_or_reviewed_post_lineage(self):
        self.assertTrue(self._is_pre() or self._is_post())
        if self._is_pre():
            REPAIR.preflight(
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

    def test_plan_has_exact_six_source_cohort_and_one_new_legal_source(self):
        self.assertEqual(set(self.plan["source_updates"]), set(REPAIR.SELECTED_SOURCES))
        self.assertEqual(len(self.plan["new_sources"]), 1)
        new = self.plan["new_sources"][0]
        self.assertEqual(new["source_id"], "WSSRC-FIS-025")
        self.assertEqual(new["canonical_dependency_count"], 0)
        self.assertEqual(new["verification_mode"], "RIGHTS_HELD_MANUAL_ONLY")
        self.assertEqual(new["automated_monitoring_use"], "PROHIBITED_OR_RIGHTS_HOLD")

    def test_abs_and_south_africa_are_governance_only(self):
        self.assertNotIn("WSO-MAC", json.dumps(self.plan["canonical_updates"]))
        canonical_updates = self.plan["canonical_updates"]
        self.assertNotIn("WSO-EL", canonical_updates)
        self.assertEqual(
            self.plan["source_updates"]["WSSRC-MAC-021"]["canonical_provenance_use"],
            "CLEARED_CURATED_FACTUAL_METADATA",
        )
        self.assertEqual(
            self.plan["source_updates"]["WSSRC-EL-ZA-001"]["verification_mode"],
            "RIGHTS_HELD_MANUAL_ONLY",
        )

    def test_argentina_and_indonesia_dates_are_frozen(self):
        baselines = self.plan["preconditions"]["canonical_baselines"]
        self.assertEqual(baselines["WSO-REG-B-0007"]["start_local"], "2026-09-15")
        self.assertEqual(baselines["WSO-REG-A-0008"]["start_local"], "2026-10-31")
        for oid in ("WSO-REG-B-0007", "WSO-REG-A-0008"):
            self.assertNotIn("start_local", self.plan["canonical_updates"][oid]["set"])
            self.assertNotIn("date_earliest", self.plan["canonical_updates"][oid]["set"])
            self.assertNotIn("date_latest", self.plan["canonical_updates"][oid]["set"])

    def test_asean_uses_month_windows_only(self):
        expected = {
            "WSO-INT-A-0018": ("2027-05-01", "2027-05-31"),
            "WSO-INT-A-0019": ("2027-11-01", "2027-11-30"),
        }
        for oid, (lo, hi) in expected.items():
            fields = self.plan["canonical_updates"][oid]["set"]
            self.assertEqual(fields["certainty_status"], "PROVISIONAL")
            self.assertEqual(fields["timing_type"], "EXPECTED_DATE_WINDOW")
            self.assertEqual(fields["time_precision"], "MONTH")
            self.assertEqual(fields["date_earliest"], lo)
            self.assertEqual(fields["date_latest"], hi)
            self.assertEqual(fields["schedule_authority_scope"], "EVENT_SPECIFIC")
            for forbidden in ("start_local", "end_local", "start_utc", "end_utc"):
                self.assertNotIn(forbidden, fields)

    def test_india_stays_unscheduled_and_splits_legal_authority(self):
        fields = self.plan["canonical_updates"]["WSO-FIS-B-0011"]["set"]
        self.assertEqual(fields["activation_mode"], "AUTHORITATIVE_RECURRING_RULE")
        self.assertEqual(fields["legal_basis_source_id"], "WSSRC-FIS-025")
        self.assertNotIn("start_local", fields)
        self.assertNotIn("date_earliest", fields)
        self.assertNotIn("date_latest", fields)
        new = self.plan["new_sources"][0]
        self.assertIn("Article 112", new["information_supplied"])
        self.assertIn("not a 2027 presentation date", new["information_supplied"])

    def test_ledger_is_five_entries_and_committed_at_is_not_frozen(self):
        entries = self.plan["ledger_entries"]
        self.assertEqual(len(entries), 5)
        self.assertEqual(
            [x["change_type"] for x in entries].count("PROVENANCE_SCOPE_REPAIR"),
            3,
        )
        self.assertEqual(
            [x["change_type"] for x in entries].count("LIFECYCLE_AND_CERTAINTY_UPDATE"),
            2,
        )
        self.assertTrue(all("committed_at" not in x for x in entries))
        self.assertIn("SET_AT_APPLY_TIME", self.plan["ledger_commit_timestamp_policy"])

    def test_simulated_post_state_preserves_protected_timing_and_assertions(self):
        canonical_post, sources_post, ledger_post, overlay_post, report = self._simulate()
        before = {r["occurrence_id"]: r for r in self.canonical["records"]}
        after = {r["occurrence_id"]: r for r in canonical_post["records"]}

        self.assertEqual(set(report["changed_occurrences"]), set(self.plan["postconditions"]["expected_changed_occurrences"]))
        self.assertEqual(set(report["changed_existing_sources"]), set(self.plan["postconditions"]["expected_changed_existing_sources"]))
        self.assertEqual(report["new_source"], "WSSRC-FIS-025")

        for oid in REPAIR.UNCHANGED_TIMING_OCCURRENCES:
            for field in REPAIR.TIMING_FIELDS:
                self.assertEqual(before[oid].get(field), after[oid].get(field), (oid, field))
            for field in REPAIR.ASSERTION_FIELDS:
                self.assertEqual(before[oid].get(field), after[oid].get(field), (oid, field))

        for oid in REPAIR.ASEAN_OCCURRENCES:
            self.assertIsNone(after[oid].get("start_local"))
            self.assertIsNone(after[oid].get("end_local"))
            self.assertIsNone(after[oid].get("start_utc"))
            self.assertIsNone(after[oid].get("end_utc"))
            for field in REPAIR.ASSERTION_FIELDS:
                self.assertEqual(before[oid].get(field), after[oid].get(field), (oid, field))

        self.assertEqual(after["WSO-REG-B-0007"]["start_local"], "2026-09-15")
        self.assertEqual(after["WSO-REG-A-0008"]["start_local"], "2026-10-31")
        self.assertIsNone(after["WSO-FIS-B-0011"]["start_local"])
        self.assertIsNone(after["WSO-FIS-B-0011"]["date_earliest"])
        self.assertIsNone(after["WSO-FIS-B-0011"]["date_latest"])

        self.assertEqual(canonical_post["version"], "0.23")
        self.assertEqual(len(canonical_post["records"]), 669)
        self.assertEqual(sources_post["version"], "1.64")
        self.assertEqual(len(sources_post["sources"]), 226)
        self.assertEqual(ledger_post["version"], "0.12")
        self.assertEqual(
            overlay_post["canonical_checkpoint"],
            {"registry_version": "0.23", "record_count": 669},
        )
        self.assertEqual(
            report["governance"],
            {"fully_explicit": 74, "missing_any": 152, "p1_canonical_dependent": 81, "p2_registry_only": 71},
        )

    def test_simulated_source_dependency_helper_stays_consistent(self):
        canonical_post, sources_post, _, _, _ = self._simulate()
        by_source = {r["source_id"]: r for r in sources_post["sources"]}
        self.assertEqual(by_source["WSSRC-FIS-025"]["canonical_dependency_count"], 0)
        self.assertEqual(REPAIR._dep_count(canonical_post, "WSSRC-FIS-025"), 0)
        for sid in REPAIR.SELECTED_SOURCES:
            self.assertEqual(
                REPAIR._dep_count(canonical_post, sid),
                self.plan["preconditions"]["source_baselines"][sid]["derived_dependency_count"],
            )

    def test_global_write_gates_remain_closed(self):
        self.assertFalse(self.expectations["automatic_canonical_commit"])
        self.assertFalse(self.expectations["google_calendar_write"])

    def test_cli_read_only_path_never_writes(self):
        paths = (CANONICAL_PATH, SOURCES_PATH, LEDGER_PATH, OVERLAY_PATH, EXPECTATIONS_PATH)
        before = {p: p.read_bytes() for p in paths}
        result = subprocess.run(
            [sys.executable, str(MODULE_PATH), "--committed-at", "2026-09-05T08:30:00+10:00"],
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
            self.assertIn("P1 SOURCE SCOPE/LIFECYCLE B PRECONDITION FAILED", result.stderr + result.stdout)

    def test_apply_without_environment_gate_never_writes(self):
        paths = (CANONICAL_PATH, SOURCES_PATH, LEDGER_PATH, OVERLAY_PATH, EXPECTATIONS_PATH)
        before = {p: p.read_bytes() for p in paths}
        env = dict(os.environ)
        env.pop(REPAIR.APPLY_ENV, None)
        result = subprocess.run(
            [sys.executable, str(MODULE_PATH), "--apply", "--committed-at", "2026-09-05T08:30:00+10:00"],
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
            self.assertIn("P1 SOURCE SCOPE/LIFECYCLE B PRECONDITION FAILED", combined)


if __name__ == "__main__":
    unittest.main()
