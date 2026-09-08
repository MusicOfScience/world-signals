from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "scripts/apply_cbsl_mpr_rss_monitor_bt.py"
PLAN_PATH = ROOT / "data/monitor/CBSL_MPR_RSS_BT_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
MATERIALISED_PATHS = (
    SOURCES_PATH,
    EXPECTATIONS_PATH,
    ROOT / "scripts/run_live_monitor.py",
    ROOT / "scripts/run_adapter_smoke.py",
    ROOT / "src/world_signals/adapters/__init__.py",
)

spec = importlib.util.spec_from_file_location("apply_cbsl_mpr_rss_monitor_bt", HELPER_PATH)
assert spec and spec.loader
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)

PLAN = json.loads(PLAN_PATH.read_text())
CANONICAL = json.loads(CANONICAL_PATH.read_text())
SOURCES = json.loads(SOURCES_PATH.read_text())
EXPECTATIONS = json.loads(EXPECTATIONS_PATH.read_text())


def source(data: dict, source_id: str) -> dict:
    return next(row for row in data["sources"] if row["source_id"] == source_id)


def _version_tuple(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.split("."))


class CBSLActivationTests(unittest.TestCase):
    @staticmethod
    def _is_pre() -> bool:
        return (
            SOURCES.get("version") == "1.92"
            and len(SOURCES.get("sources", [])) == 250
            and EXPECTATIONS.get("version") == "0.17"
            and len(EXPECTATIONS.get("adapters", [])) == 15
            and not any(row.get("source_id") == "WSSRC-REGJ-007" for row in SOURCES.get("sources", []))
            and not any(row.get("adapter_id") == "CBSL_MONETARY_POLICY_RSS" for row in EXPECTATIONS.get("adapters", []))
        )

    @staticmethod
    def _is_bt_or_descendant() -> bool:
        return (
            _version_tuple(SOURCES.get("version", "0")) >= (1, 93)
            and len(SOURCES.get("sources", [])) >= 251
            and _version_tuple(EXPECTATIONS.get("version", "0")) >= (0, 18)
            and len(EXPECTATIONS.get("adapters", [])) >= 16
            and sum(row.get("source_id") == "WSSRC-REGJ-007" for row in SOURCES.get("sources", [])) == 1
            and sum(row.get("adapter_id") == "CBSL_MONETARY_POLICY_RSS" for row in EXPECTATIONS.get("adapters", [])) == 1
        )

    def _post(self):
        if self._is_pre():
            return helper.build_post_state(
                deepcopy(CANONICAL), deepcopy(SOURCES), deepcopy(EXPECTATIONS), deepcopy(PLAN)
            )
        self.assertTrue(self._is_bt_or_descendant(), "state is neither exact BT pre-state nor a valid BT descendant")
        return (
            SOURCES,
            EXPECTATIONS,
            (ROOT / "scripts/run_live_monitor.py").read_text(),
            (ROOT / "scripts/run_adapter_smoke.py").read_text(),
            (ROOT / "src/world_signals/adapters/__init__.py").read_text(),
        )

    def test_plan_is_frozen_to_exact_post_bs_governed_state_or_valid_descendant(self) -> None:
        self.assertEqual(PLAN["exact_base_main_sha"], "2b74c10905760c98c75b3598df96441f99841b00")
        self.assertEqual((CANONICAL["version"], len(CANONICAL["records"])), ("0.41", 689))
        if self._is_pre():
            self.assertEqual((SOURCES["version"], len(SOURCES["sources"])), ("1.92", 250))
            self.assertEqual((EXPECTATIONS["version"], len(EXPECTATIONS["adapters"])), ("0.17", 15))
        else:
            self.assertTrue(self._is_bt_or_descendant())
        self.assertFalse(EXPECTATIONS["automatic_canonical_commit"])
        self.assertFalse(EXPECTATIONS["google_calendar_write"])

    def test_build_post_state_adds_only_machine_source_and_monitor_route_semantically(self) -> None:
        schedule_before = deepcopy(source(SOURCES, "WSSRC-REGJ-002"))
        post_sources, post_expectations, live, smoke, adapter_init = self._post()
        if self._is_pre():
            self.assertEqual((post_sources["version"], len(post_sources["sources"])), ("1.93", 251))
            self.assertEqual((post_expectations["version"], len(post_expectations["adapters"])), ("0.18", 16))
        else:
            self.assertTrue(_version_tuple(post_sources["version"]) >= (1, 93))
            self.assertGreaterEqual(len(post_sources["sources"]), 251)
            self.assertTrue(_version_tuple(post_expectations["version"]) >= (0, 18))
            self.assertGreaterEqual(len(post_expectations["adapters"]), 16)
        self.assertEqual(source(post_sources, "WSSRC-REGJ-002"), schedule_before)

        machine = source(post_sources, "WSSRC-REGJ-007")
        self.assertEqual(machine["canonical_dependency_count"], 0)
        self.assertEqual(machine["automated_monitoring_use"], "CLEARED")
        self.assertEqual(machine["verification_mode"], "AUTOMATED_PILOT")
        self.assertEqual(machine["canonical_provenance_use"], "MONITOR_ONLY_PUBLICATION_SENTINEL_NO_CANONICAL_SCHEDULE_AUTHORITY")
        self.assertIn("BOUNDED_METADATA_MONITORING", machine["automated_retrieval_permission"])
        self.assertIn("All Rights Reserved", machine["rights_summary"])

        routes = [row for row in post_expectations["adapters"] if row.get("adapter_id") == "CBSL_MONETARY_POLICY_RSS"]
        self.assertEqual(len(routes), 1)
        route = routes[0]
        self.assertEqual(route["source_id"], "WSSRC-REGJ-007")
        self.assertEqual(route["canonical_occurrence_ids"], ["WSO-REG-J-0006", "WSO-REG-J-0007"])
        self.assertEqual(route["request_budget_per_run"], 1)
        self.assertFalse(route["schedule_authority"])
        self.assertFalse(route["lifecycle_authority"])
        self.assertFalse(route["certainty_authority"])
        self.assertFalse(route["rss_has_publication_clock"])
        self.assertFalse(route["official_link_filename_date_is_clock_time"])
        self.assertFalse(route["automatic_item_link_fetch_allowed"])
        self.assertFalse(route["automatic_schedule_html_fetch_allowed"])
        self.assertFalse(route["automatic_commit_allowed"])
        self.assertEqual(
            route["review_identity_by_occurrence_id"]["WSO-REG-J-0006"],
            {"review_number": 5, "year": 2026, "announcement_date": "2026-09-30"},
        )

        self.assertIn("fetch_cbsl_mpr_rss", live)
        self.assertIn('if "CBSL_MONETARY_POLICY_RSS" in configs:', live)
        self.assertIn("cbsl_mpr_rss_review_candidates", live)
        self.assertIn('"adapter":"CBSL_MONETARY_POLICY_RSS"', smoke)
        self.assertIn("CBSL_MPR_RSS", adapter_init)
        self.assertIn("parse_cbsl_mpr_rss", adapter_init)

    def test_existing_monitor_routes_are_preserved_at_exact_bt_pre_state(self) -> None:
        if not self._is_pre():
            self.skipTest("exact route-prefix preservation is tested only while simulating the frozen BT pre-state")
        _, post_expectations, _, _, _ = helper.build_post_state(
            deepcopy(CANONICAL), deepcopy(SOURCES), deepcopy(EXPECTATIONS), deepcopy(PLAN)
        )
        self.assertEqual(post_expectations["adapters"][:-1], EXPECTATIONS["adapters"])

    def test_check_only_cli_does_not_write_materialised_files(self) -> None:
        if not self._is_pre():
            self.skipTest("check-only transaction simulation applies only to exact BT pre-state")
        before = {path: path.read_bytes() for path in MATERIALISED_PATHS}
        env = dict(os.environ)
        env.pop("WORLD_SIGNALS_APPLY_MONITOR_BT", None)
        completed = subprocess.run(
            [sys.executable, str(HELPER_PATH)],
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("BT CHECK-ONLY PASS", completed.stdout)
        for path, raw in before.items():
            self.assertEqual(path.read_bytes(), raw, path)

    def test_apply_requires_explicit_environment_gate(self) -> None:
        if not self._is_pre():
            self.skipTest("apply-gate simulation applies only to exact BT pre-state")
        env = dict(os.environ)
        env.pop("WORLD_SIGNALS_APPLY_MONITOR_BT", None)
        completed = subprocess.run(
            [sys.executable, str(HELPER_PATH), "--apply"],
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("WORLD_SIGNALS_APPLY_MONITOR_BT", completed.stderr)


if __name__ == "__main__":
    unittest.main()
