from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts/apply_indec_cpi_calendar_monitor_bu.py"
SPEC = importlib.util.spec_from_file_location("apply_indec_cpi_calendar_monitor_bu", MODULE)
TX = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TX)

PLAN = json.loads((ROOT / "data/monitor/INDEC_CPI_CALENDAR_BU_PLAN_v0.1.json").read_text())
CANONICAL = json.loads((ROOT / "data/canonical/registry.json").read_text())
SOURCES = json.loads((ROOT / "data/sources/registry.json").read_text())
EXPECTATIONS = json.loads((ROOT / "data/monitor/expectations.json").read_text())


def _version_tuple(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.split("."))


class INDECCPICalendarActivationBUTests(unittest.TestCase):
    @staticmethod
    def _is_pre() -> bool:
        return (
            SOURCES.get("version") == "1.93"
            and len(SOURCES.get("sources", [])) == 251
            and EXPECTATIONS.get("version") == "0.18"
            and len(EXPECTATIONS.get("adapters", [])) == 16
            and not any(x.get("source_id") == "WSSRC-REG2-009" for x in SOURCES.get("sources", []))
            and not any(x.get("adapter_id") == "INDEC_CPI_CALENDAR" for x in EXPECTATIONS.get("adapters", []))
        )

    @staticmethod
    def _is_bu_or_descendant() -> bool:
        return (
            _version_tuple(SOURCES.get("version", "0")) >= (1, 94)
            and len(SOURCES.get("sources", [])) >= 252
            and _version_tuple(EXPECTATIONS.get("version", "0")) >= (0, 19)
            and len(EXPECTATIONS.get("adapters", [])) >= 17
            and sum(x.get("source_id") == "WSSRC-REG2-009" for x in SOURCES.get("sources", [])) == 1
            and sum(x.get("adapter_id") == "INDEC_CPI_CALENDAR" for x in EXPECTATIONS.get("adapters", [])) == 1
        )

    def _post(self):
        if self._is_pre():
            return TX.build_post_state(CANONICAL, SOURCES, EXPECTATIONS, PLAN)
        self.assertTrue(self._is_bu_or_descendant(), "state is neither exact BU pre-state nor a valid BU descendant")
        return SOURCES, EXPECTATIONS, None, None, None

    def test_exact_preflight_or_bu_descendant_state(self):
        self.assertGreaterEqual(tuple(map(int, CANONICAL["version"].split("."))), (0, 41))
        self.assertGreaterEqual(len(CANONICAL["records"]), 689)
        if self._is_pre():
            TX.preflight(CANONICAL, SOURCES, EXPECTATIONS, PLAN)
        else:
            self.assertTrue(self._is_bu_or_descendant())

    def test_post_state_preserves_existing_indec_provenance_and_adds_machine_source(self):
        post_sources, post_expectations, *_ = self._post()
        before = {x["source_id"]: x for x in SOURCES["sources"]}
        after = {x["source_id"]: x for x in post_sources["sources"]}
        self.assertEqual(after["WSSRC-REG2-006"], before["WSSRC-REG2-006"])
        self.assertEqual(after["WSSRC-REG2-008"], before["WSSRC-REG2-008"])
        machine = after["WSSRC-REG2-009"]
        self.assertEqual(machine["canonical_dependency_count"], 0)
        self.assertEqual(machine["automated_monitoring_use"], "CLEARED")
        self.assertEqual(machine["related_source_ids"], ["WSSRC-REG2-006", "WSSRC-REG2-008"])
        self.assertEqual(machine["live_adapter_id"], "INDEC_CPI_CALENDAR")
        self.assertIn("BOUNDED", machine["automated_retrieval_permission"])

        routes = [x for x in post_expectations["adapters"] if x.get("adapter_id") == "INDEC_CPI_CALENDAR"]
        self.assertEqual(len(routes), 1)
        route = routes[0]
        self.assertEqual(route["source_id"], "WSSRC-REG2-009")
        self.assertEqual(route["canonical_schedule_source_id"], "WSSRC-REG2-006")
        self.assertEqual(route["completed_release_source_id"], "WSSRC-REG2-008")
        self.assertEqual(route["request_budget_per_run"], 5)
        self.assertEqual(route["robots_requests_per_run"], 1)
        self.assertEqual(route["maximum_month_route_requests_per_run"], 4)
        self.assertEqual(route["month_slugs"], PLAN["request_contract"]["month_slugs"])
        self.assertEqual(set(route["canonical_occurrence_ids"]), set(PLAN["canonical_occurrence_ids"]))
        self.assertFalse(route["schedule_authority"])
        self.assertFalse(route["lifecycle_authority"])
        self.assertFalse(route["certainty_authority"])
        self.assertFalse(route["canonical_clock_mutation_allowed"])
        self.assertFalse(route["automatic_pdf_fetch_allowed"])
        self.assertFalse(route["automatic_completed_release_fetch_allowed"])
        self.assertFalse(route["automatic_google_fetch_allowed"])
        self.assertFalse(route["automatic_search_route_discovery_allowed"])
        self.assertFalse(route["automatic_commit_allowed"])
        self.assertFalse(post_expectations["automatic_canonical_commit"])
        self.assertFalse(post_expectations["google_calendar_write"])
        if self._is_pre():
            self.assertEqual(post_expectations["adapters"][:-1], EXPECTATIONS["adapters"])

    def test_runtime_patch_wires_bounded_first_party_routes_only(self):
        if not self._is_pre():
            self.skipTest("patch simulation applies only to exact BU pre-state")
        _, _, live, smoke, adapter_init = TX.build_post_state(CANONICAL, SOURCES, EXPECTATIONS, PLAN)
        self.assertIn('if "INDEC_CPI_CALENDAR" in configs:', live)
        self.assertIn("fetch_indec_robots_policy", live)
        self.assertIn("fetch_indec_cpi_months", live)
        self.assertIn("indec_cpi_calendar_review_candidates", live)
        self.assertIn('"google_followup_request_count":0', live)
        self.assertIn('"search_route_request_count":0', live)
        self.assertIn('"adapter":"INDEC_CPI_CALENDAR"', smoke)
        self.assertIn("INDEC_MONTH_ROUTE_TEMPLATE", adapter_init)
        self.assertIn("parse_indec_cpi_month", adapter_init)

    def test_apply_without_environment_gate_never_writes(self):
        if not self._is_pre():
            self.skipTest("apply-gate test applies only to exact BU pre-state")
        paths = [TX.SOURCES_PATH, TX.EXPECTATIONS_PATH, TX.LIVE_RUNNER_PATH, TX.SMOKE_RUNNER_PATH, TX.ADAPTER_INIT_PATH]
        before = {p: p.read_bytes() for p in paths}
        env = dict(os.environ)
        env.pop(TX.APPLY_ENV, None)
        proc = subprocess.run([sys.executable, str(MODULE), "--apply"], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        for path, raw in before.items():
            self.assertEqual(path.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
