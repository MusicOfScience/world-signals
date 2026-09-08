from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts/apply_japan_mof_jgb_rss_monitor_br.py"
SPEC = importlib.util.spec_from_file_location("apply_japan_mof_jgb_rss_monitor_br", MODULE)
TX = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TX)

PLAN = json.loads((ROOT / "data/monitor/JGB_RSS_MONITOR_BR_PLAN_v0.1.json").read_text())
CANONICAL = json.loads((ROOT / "data/canonical/registry.json").read_text())
SOURCES = json.loads((ROOT / "data/sources/registry.json").read_text())
EXPECTATIONS = json.loads((ROOT / "data/monitor/expectations.json").read_text())


class JapanMOFJGBRSSActivationBRTests(unittest.TestCase):
    @staticmethod
    def _is_pre() -> bool:
        return (
            SOURCES.get("version") == "1.90"
            and len(SOURCES.get("sources", [])) == 248
            and EXPECTATIONS.get("version") == "0.15"
            and len(EXPECTATIONS.get("adapters", [])) == 13
            and not any(x.get("source_id") == "WSSRC-FIS-029" for x in SOURCES.get("sources", []))
        )

    def _post(self):
        if self._is_pre():
            return TX.build_post_state(CANONICAL, SOURCES, EXPECTATIONS, PLAN)
        self.assertEqual((SOURCES["version"], len(SOURCES["sources"])), ("1.91", 249))
        self.assertEqual((EXPECTATIONS["version"], len(EXPECTATIONS["adapters"])), ("0.16", 14))
        return SOURCES, EXPECTATIONS, None, None, None

    def test_exact_preflight_or_complete_br_descendant(self):
        self.assertEqual((CANONICAL["version"], len(CANONICAL["records"])), ("0.41", 689))
        if self._is_pre():
            TX.preflight(CANONICAL, SOURCES, EXPECTATIONS, PLAN)
        else:
            TX.validate_post_state(CANONICAL, SOURCES, EXPECTATIONS, PLAN)

    def test_post_state_adds_only_separate_machine_source_and_one_route(self):
        post_sources, post_expectations, *_ = self._post()
        TX.validate_post_state(CANONICAL, post_sources, post_expectations, PLAN)
        before = {x["source_id"]: x for x in SOURCES["sources"]}
        after = {x["source_id"]: x for x in post_sources["sources"]}
        schedule_before = before["WSSRC-FIS-007"]
        schedule_after = after["WSSRC-FIS-007"]
        self.assertEqual(schedule_before, schedule_after)
        machine = after["WSSRC-FIS-029"]
        self.assertEqual(machine["canonical_dependency_count"], 0)
        self.assertEqual(machine["automated_monitoring_use"], "CLEARED")
        self.assertEqual(machine["verification_mode"], "AUTOMATED_PILOT")
        self.assertEqual(machine["canonical_provenance_use"], "MONITOR_ONLY_PUBLICATION_CHANGE_SENTINEL_NO_CANONICAL_SCHEDULE_AUTHORITY")
        self.assertEqual(machine["related_source_ids"], ["WSSRC-FIS-007"])
        self.assertEqual(post_expectations["adapters"][: len(EXPECTATIONS["adapters"])], EXPECTATIONS["adapters"])
        route = post_expectations["adapters"][-1]
        self.assertEqual(route["adapter_id"], "JAPAN_MOF_JGB_RSS")
        self.assertEqual(route["request_budget_per_run"], 1)
        self.assertEqual(set(route["canonical_occurrence_ids"]), set(PLAN["canonical_occurrence_ids"]))
        self.assertFalse(route["schedule_authority"])
        self.assertFalse(route["lifecycle_authority"])
        self.assertFalse(route["certainty_authority"])
        self.assertFalse(route["automatic_calendar_html_fetch_allowed"])
        self.assertFalse(route["automatic_commit_allowed"])

    def test_runtime_patch_wires_rss_only_not_html_calendar(self):
        if not self._is_pre():
            self.skipTest("patch simulation applies only to exact BR pre-state")
        _, _, live, smoke, adapter_init = TX.build_post_state(CANONICAL, SOURCES, EXPECTATIONS, PLAN)
        self.assertIn('if "JAPAN_MOF_JGB_RSS" in configs:', live)
        self.assertIn("fetch_japan_mof_news_rss", live)
        self.assertIn("japan_mof_jgb_rss_review_candidates", live)
        self.assertNotIn("fetch_jgb_monthly_auction_calendar()", live)
        self.assertIn('"adapter":"JAPAN_MOF_JGB_RSS"', smoke)
        self.assertIn("JAPAN_MOF_NEWS_RSS", adapter_init)
        self.assertIn("parse_japan_mof_news_rss", adapter_init)

    def test_apply_without_environment_gate_never_writes(self):
        if not self._is_pre():
            self.skipTest("apply-gate test applies only to exact BR pre-state")
        paths = [TX.SOURCES_PATH, TX.EXPECTATIONS_PATH, TX.LIVE_RUNNER_PATH, TX.SMOKE_RUNNER_PATH, TX.ADAPTER_INIT_PATH]
        before = {p: p.read_bytes() for p in paths}
        env = dict(os.environ)
        env.pop(TX.APPLY_ENV, None)
        proc = subprocess.run([sys.executable, str(MODULE), "--apply"], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("APPLY BLOCKED", proc.stdout + proc.stderr)
        for path, raw in before.items():
            self.assertEqual(path.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
