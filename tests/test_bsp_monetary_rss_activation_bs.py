from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts/apply_bsp_monetary_rss_monitor_bs.py"
SPEC = importlib.util.spec_from_file_location("apply_bsp_monetary_rss_monitor_bs", MODULE)
TX = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TX)

PLAN = json.loads((ROOT / "data/monitor/BSP_MONETARY_RSS_BS_PLAN_v0.1.json").read_text())
CANONICAL = json.loads((ROOT / "data/canonical/registry.json").read_text())
SOURCES = json.loads((ROOT / "data/sources/registry.json").read_text())
EXPECTATIONS = json.loads((ROOT / "data/monitor/expectations.json").read_text())


class BSPMonetaryRSSActivationBSTests(unittest.TestCase):
    @staticmethod
    def _is_pre() -> bool:
        return (
            SOURCES.get("version") == "1.91"
            and len(SOURCES.get("sources", [])) == 249
            and EXPECTATIONS.get("version") == "0.16"
            and len(EXPECTATIONS.get("adapters", [])) == 14
            and not any(x.get("source_id") == "WSSRC-REGJ-006" for x in SOURCES.get("sources", []))
        )

    def _post(self):
        if self._is_pre():
            return TX.build_post_state(CANONICAL, SOURCES, EXPECTATIONS, PLAN)
        self.assertEqual((SOURCES["version"], len(SOURCES["sources"])), ("1.92", 250))
        self.assertEqual((EXPECTATIONS["version"], len(EXPECTATIONS["adapters"])), ("0.17", 15))
        return SOURCES, EXPECTATIONS, None, None, None

    def test_exact_preflight_or_bs_descendant_state(self):
        self.assertEqual((CANONICAL["version"], len(CANONICAL["records"])), ("0.41", 689))
        if self._is_pre():
            TX.preflight(CANONICAL, SOURCES, EXPECTATIONS, PLAN)
        else:
            by_source = {x["source_id"]: x for x in SOURCES["sources"]}
            self.assertIn("WSSRC-REGJ-006", by_source)
            self.assertEqual(by_source["WSSRC-REGJ-003"]["automated_monitoring_use"], "ENDPOINT_REVIEW_REQUIRED")
            self.assertEqual(by_source["WSSRC-REGJ-003"]["automated_retrieval_permission"], "PENDING_ENDPOINT_OPERATIONAL_REVIEW")
            self.assertIn("BSP_MONETARY_POLICY_RSS", {x["adapter_id"] for x in EXPECTATIONS["adapters"]})

    def test_post_state_backfills_legacy_schedule_governance_but_preserves_hold_and_adds_separate_machine_source(self):
        post_sources, post_expectations, *_ = self._post()
        before = {x["source_id"]: x for x in SOURCES["sources"]}
        after = {x["source_id"]: x for x in post_sources["sources"]}
        schedule = after["WSSRC-REGJ-003"]
        self.assertEqual(schedule["canonical_dependency_count"], 2)
        self.assertEqual(schedule["canonical_provenance_use"], "CLEARED_CURATED_FACTUAL_METADATA")
        self.assertEqual(schedule["automated_monitoring_use"], "ENDPOINT_REVIEW_REQUIRED")
        self.assertEqual(schedule["automated_retrieval_permission"], "PENDING_ENDPOINT_OPERATIONAL_REVIEW")
        self.assertEqual(schedule["verification_mode"], "MANUAL_AUTHORITATIVE_RECHECK")
        self.assertEqual(schedule["monitoring_activation_status"], "HOLD_NO_LIVE_ROUTE")
        for key in (
            "source_id", "institution", "jurisdiction", "domain", "endpoint_role", "authoritative_url", "source_type",
            "information_supplied", "future_schedule_horizon", "typical_advance_notice", "machine_readable_available",
            "source_timezone", "timezone_scope", "canonical_dependency_count", "automated_retrieval_permission",
            "monitoring_readiness_status", "parser_type", "rights_evidence_url", "rights_summary", "redistribution_permission"
        ):
            self.assertEqual(schedule.get(key), before["WSSRC-REGJ-003"].get(key))
        machine = after["WSSRC-REGJ-006"]
        self.assertEqual(machine["canonical_dependency_count"], 0)
        self.assertEqual(machine["automated_monitoring_use"], "CLEARED")
        self.assertEqual(machine["canonical_provenance_use"], "MONITOR_ONLY_PUBLICATION_SENTINEL_NO_CANONICAL_SCHEDULE_AUTHORITY")
        self.assertEqual(machine["related_source_ids"], ["WSSRC-REGJ-003"])
        self.assertEqual(post_expectations["adapters"][: len(EXPECTATIONS["adapters"])], EXPECTATIONS["adapters"])
        route = post_expectations["adapters"][-1]
        self.assertEqual(route["adapter_id"], "BSP_MONETARY_POLICY_RSS")
        self.assertEqual(route["source_id"], "WSSRC-REGJ-006")
        self.assertEqual(route["request_budget_per_run"], 1)
        self.assertEqual(set(route["canonical_occurrence_ids"]), set(PLAN["canonical_occurrence_ids"]))
        self.assertFalse(route["schedule_authority"])
        self.assertFalse(route["lifecycle_authority"])
        self.assertFalse(route["certainty_authority"])
        self.assertFalse(route["canonical_clock_mutation_allowed"])
        self.assertFalse(route["automatic_schedule_html_fetch_allowed"])
        self.assertFalse(route["automatic_commit_allowed"])
        self.assertFalse(post_expectations["automatic_canonical_commit"])
        self.assertFalse(post_expectations["google_calendar_write"])

    def test_runtime_patch_wires_only_rss_machine_source(self):
        if not self._is_pre():
            self.skipTest("patch simulation applies only to exact BS pre-state")
        _, _, live, smoke, adapter_init = TX.build_post_state(CANONICAL, SOURCES, EXPECTATIONS, PLAN)
        self.assertIn('if "BSP_MONETARY_POLICY_RSS" in configs:', live)
        self.assertIn("fetch_bsp_media_releases_rss", live)
        self.assertIn("bsp_monetary_rss_review_candidates", live)
        self.assertNotIn("ScheduleOfMeetingsOfTheAdvisoryCommitteeAndMonetaryBoardOnMonetaryPolicy", live)
        self.assertIn('"adapter":"BSP_MONETARY_POLICY_RSS"', smoke)
        self.assertIn("BSP_MEDIA_RELEASES_RSS", adapter_init)
        self.assertIn("parse_bsp_media_releases_rss", adapter_init)

    def test_apply_without_environment_gate_never_writes(self):
        if not self._is_pre():
            self.skipTest("apply-gate test applies only to exact BS pre-state")
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
