from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLAN = json.loads((ROOT / "data/monitor/CHINA_NBS_NATIVE_RSS_BX_PLAN_v0.1.json").read_text())
CANONICAL = json.loads((ROOT / "data/canonical/registry.json").read_text())
SOURCES = json.loads((ROOT / "data/sources/registry.json").read_text())
EXPECTATIONS = json.loads((ROOT / "data/monitor/expectations.json").read_text())
HELPER_PATH = ROOT / "scripts/apply_china_nbs_native_rss_monitor_bx.py"

spec = importlib.util.spec_from_file_location("bx_helper", HELPER_PATH)
assert spec and spec.loader
HELPER = importlib.util.module_from_spec(spec)
spec.loader.exec_module(HELPER)

CANONICAL_SOURCE_ID = "WSSRC-MAC-007"
MACHINE_SOURCE_ID = "WSSRC-MAC-026"
ADAPTER_ID = "CHINA_NBS_LATEST_RELEASES_RSS"


def source_by_id(data: dict, source_id: str) -> dict:
    rows = [row for row in data.get("sources", []) if row.get("source_id") == source_id]
    if len(rows) != 1:
        raise AssertionError(f"expected exactly one source {source_id}, found {len(rows)}")
    return rows[0]


def route_by_id(data: dict, adapter_id: str) -> dict:
    rows = [row for row in data.get("adapters", []) if row.get("adapter_id") == adapter_id]
    if len(rows) != 1:
        raise AssertionError(f"expected exactly one route {adapter_id}, found {len(rows)}")
    return rows[0]


def exact_prestate() -> bool:
    return (
        SOURCES.get("version") == "1.96"
        and len(SOURCES.get("sources", [])) == 252
        and EXPECTATIONS.get("version") == "0.21"
        and len(EXPECTATIONS.get("adapters", [])) == 19
        and not any(x.get("source_id") == MACHINE_SOURCE_ID for x in SOURCES.get("sources", []))
        and not any(x.get("adapter_id") == ADAPTER_ID for x in EXPECTATIONS.get("adapters", []))
    )


def effective_poststate() -> tuple[dict, dict, str, str, str]:
    if exact_prestate():
        _, sources, expectations, _, live, smoke, init = HELPER.simulate()
        return sources, expectations, live, smoke, init
    return (
        SOURCES,
        EXPECTATIONS,
        (ROOT / "scripts/run_live_monitor.py").read_text(),
        (ROOT / "scripts/run_adapter_smoke.py").read_text(),
        (ROOT / "src/world_signals/adapters/__init__.py").read_text(),
    )


class NBSNativeRSSActivationBXTests(unittest.TestCase):
    def test_frozen_prestate_or_descendant_poststate_is_coherent(self):
        self.assertEqual((CANONICAL.get("version"), len(CANONICAL.get("records", []))), ("0.41", 689))
        if not exact_prestate():
            self.assertGreaterEqual(float(SOURCES.get("version")), 1.97)
            self.assertGreaterEqual(len(SOURCES.get("sources", [])), 253)
            self.assertGreaterEqual(float(EXPECTATIONS.get("version")), 0.22)
            self.assertGreaterEqual(len(EXPECTATIONS.get("adapters", [])), 20)

        sources, expectations, _, _, _ = effective_poststate()
        self.assertEqual(len([x for x in sources["sources"] if x.get("source_id") == MACHINE_SOURCE_ID]), 1)
        self.assertEqual(len([x for x in expectations["adapters"] if x.get("adapter_id") == ADAPTER_ID]), 1)

    def test_canonical_schedule_source_remains_endpoint_review_authority(self):
        sources, _, _, _, _ = effective_poststate()
        source = source_by_id(sources, CANONICAL_SOURCE_ID)
        expected = {
            "institution": "National Bureau of Statistics of China",
            "jurisdiction": "China",
            "domain": "macroeconomic_releases",
            "endpoint_role": "Annual regular press-release calendar",
            "authoritative_url": "https://www.stats.gov.cn/english/PressRelease/ReleaseCalendar/",
            "source_type": "official_calendar",
            "source_timezone": "Asia/Shanghai",
            "canonical_dependency_count": 36,
            "canonical_provenance_use": "CLEARED_CURATED_FACTUAL_METADATA",
            "automated_monitoring_use": "ENDPOINT_REVIEW_REQUIRED",
            "automated_retrieval_permission": "NOT_EXPRESSLY_GRANTED_REVIEW_REQUIRED",
            "monitoring_readiness_status": "ENDPOINT_REVIEW_REQUIRED",
            "verification_mode": "MANUAL_AUTHORITATIVE_RECHECK",
        }
        for key, value in expected.items():
            self.assertEqual(source.get(key), value, key)

    def test_machine_source_is_monitor_only_and_zero_dependency(self):
        sources, _, _, _, _ = effective_poststate()
        source = source_by_id(sources, MACHINE_SOURCE_ID)
        self.assertEqual(source["authoritative_url"], "https://www.stats.gov.cn/sj/zxfb/rss.xml")
        self.assertEqual(source["source_type"], "official_rss_feed")
        self.assertEqual(source["canonical_dependency_count"], 0)
        self.assertEqual(source["automated_monitoring_use"], "CLEARED")
        self.assertEqual(
            source["automated_retrieval_permission"],
            "OFFICIAL_DEDICATED_RSS_INTERFACE_BOUNDED_METADATA_MONITORING",
        )
        self.assertEqual(source["monitoring_readiness_status"], "LIVE_VALIDATED_NO_AUTO_COMMIT")
        self.assertEqual(source["verification_mode"], "AUTOMATED_PILOT")
        self.assertEqual(
            source["canonical_provenance_use"],
            "MONITOR_ONLY_PUBLICATION_SENTINEL_NO_CANONICAL_SCHEDULE_AUTHORITY",
        )
        self.assertEqual(source["related_source_ids"], [CANONICAL_SOURCE_ID])
        self.assertFalse(source["live_validation_evidence"]["automatic_commit_allowed"])

    def test_route_has_exact_36_scope_and_all_authority_gates_closed(self):
        _, expectations, _, _, _ = effective_poststate()
        route = route_by_id(expectations, ADAPTER_ID)
        self.assertEqual(route["source_id"], MACHINE_SOURCE_ID)
        self.assertEqual(route["canonical_schedule_source_id"], CANONICAL_SOURCE_ID)
        self.assertEqual(route["canonical_occurrence_ids"], PLAN["canonical_occurrence_ids"])
        self.assertEqual(route["identity_by_occurrence_id"], PLAN["canonical_identity_by_occurrence_id"])
        self.assertEqual(route["request_budget_per_run"], 1)
        self.assertEqual(route["native_rss_request_count_per_run"], 1)
        for key in (
            "schedule_request_count_per_run",
            "english_rss_request_count_per_run",
            "article_followup_request_count_per_run",
            "data_api_followup_request_count_per_run",
            "search_route_discovery_request_count_per_run",
        ):
            self.assertEqual(route[key], 0, key)
        for key in (
            "schedule_authority",
            "clock_authority",
            "lifecycle_authority",
            "certainty_authority",
            "rss_publication_metadata_is_event_clock_authority",
            "rss_publication_metadata_is_schedule_authority",
            "canonical_clock_mutation_allowed",
            "automatic_item_link_fetch_allowed",
            "automatic_schedule_html_fetch_allowed",
            "automatic_english_rss_fetch_allowed",
            "automatic_data_api_fetch_allowed",
            "automatic_search_route_discovery_allowed",
            "automatic_commit_allowed",
        ):
            self.assertIs(route[key], False, key)
        self.assertIs(expectations["automatic_canonical_commit"], False)
        self.assertIs(expectations["google_calendar_write"], False)

    def test_runtime_and_export_wiring_is_present(self):
        _, _, live, smoke, init = effective_poststate()
        self.assertIn("fetch_nbs_native_latest_releases_rss", live)
        self.assertIn("nbs_native_rss_review_candidates", live)
        self.assertIn('"CHINA_NBS_LATEST_RELEASES_RSS" in configs', live)
        self.assertIn("fetch_nbs_native_latest_releases_rss", smoke)
        self.assertIn('"CHINA_NBS_LATEST_RELEASES_RSS"', smoke)
        self.assertIn("from .nbs_native_rss import (", init)
        self.assertIn('"NBS_NATIVE_LATEST_RELEASES_RSS"', init)
        self.assertIn('"fetch_nbs_native_latest_releases_rss"', init)

    def test_check_only_helper_does_not_write_on_frozen_prestate(self):
        if not exact_prestate():
            self.skipTest("check-only write audit is frozen to the exact pre-BX state")
        paths = [ROOT / x for x in (
            "data/sources/registry.json",
            "data/monitor/expectations.json",
            "scripts/run_live_monitor.py",
            "scripts/run_adapter_smoke.py",
            "src/world_signals/adapters/__init__.py",
        )]
        before = [p.read_bytes() for p in paths]
        proc = subprocess.run(
            [sys.executable, str(HELPER_PATH)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("CHECK_ONLY", proc.stdout)
        self.assertEqual([p.read_bytes() for p in paths], before)

    def test_apply_requires_environment_gate_on_frozen_prestate(self):
        if not exact_prestate():
            self.skipTest("apply-gate audit is frozen to the exact pre-BX state")
        env = dict(__import__("os").environ)
        env.pop("WORLD_SIGNALS_APPLY_MONITOR_BX", None)
        proc = subprocess.run(
            [sys.executable, str(HELPER_PATH), "--apply"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("WORLD_SIGNALS_APPLY_MONITOR_BX=1", proc.stderr)


if __name__ == "__main__":
    unittest.main()
