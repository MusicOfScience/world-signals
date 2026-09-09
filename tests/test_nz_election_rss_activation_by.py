from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLAN = json.loads((ROOT / "data/monitor/NZ_ELECTION_TIMETABLE_CHANGE_RSS_BY_PLAN_v0.1.json").read_text())
CANONICAL = json.loads((ROOT / "data/canonical/registry.json").read_text())
SOURCES = json.loads((ROOT / "data/sources/registry.json").read_text())
EXPECTATIONS = json.loads((ROOT / "data/monitor/expectations.json").read_text())
HELPER_PATH = ROOT / "scripts/apply_nz_election_rss_monitor_by.py"

spec = importlib.util.spec_from_file_location("by_helper", HELPER_PATH)
assert spec and spec.loader
HELPER = importlib.util.module_from_spec(spec)
spec.loader.exec_module(HELPER)

CANONICAL_SOURCE_ID = "WSSRC-EL-NZ-001"
MACHINE_SOURCE_ID = "WSSRC-EL-NZ-002"
ADAPTER_ID = "NZ_ELECTION_TIMETABLE_CHANGE_RSS"


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
        CANONICAL.get("version") == "0.41"
        and len(CANONICAL.get("records", [])) == 689
        and SOURCES.get("version") == "1.97"
        and len(SOURCES.get("sources", [])) == 253
        and EXPECTATIONS.get("version") == "0.22"
        and len(EXPECTATIONS.get("adapters", [])) == 20
        and not any(x.get("source_id") == MACHINE_SOURCE_ID for x in SOURCES.get("sources", []))
        and not any(x.get("adapter_id") == ADAPTER_ID for x in EXPECTATIONS.get("adapters", []))
    )


def effective_poststate() -> tuple[dict, dict, str, str, str]:
    if exact_prestate():
        sources, expectations, init, live, smoke, _ = HELPER.simulate()
        return sources, expectations, live, smoke, init
    return (
        SOURCES,
        EXPECTATIONS,
        (ROOT / "scripts/run_live_monitor.py").read_text(),
        (ROOT / "scripts/run_adapter_smoke.py").read_text(),
        (ROOT / "src/world_signals/adapters/__init__.py").read_text(),
    )


class NZElectionRSSActivationBYTests(unittest.TestCase):
    def test_frozen_prestate_or_descendant_poststate_is_coherent(self):
        if exact_prestate():
            self.assertEqual((CANONICAL["version"], len(CANONICAL["records"])), ("0.41", 689))
        else:
            self.assertGreaterEqual(float(CANONICAL.get("version", 0)), 0.41)
            self.assertGreaterEqual(len(CANONICAL.get("records", [])), 689)
            self.assertGreaterEqual(float(SOURCES.get("version", 0)), 1.98)
            self.assertGreaterEqual(len(SOURCES.get("sources", [])), 254)
            self.assertGreaterEqual(float(EXPECTATIONS.get("version", 0)), 0.23)
            self.assertGreaterEqual(len(EXPECTATIONS.get("adapters", [])), 21)

        sources, expectations, _, _, _ = effective_poststate()
        self.assertEqual(len([x for x in sources["sources"] if x.get("source_id") == MACHINE_SOURCE_ID]), 1)
        self.assertEqual(len([x for x in expectations["adapters"] if x.get("adapter_id") == ADAPTER_ID]), 1)

    def test_canonical_timetable_source_identity_and_factual_role_are_preserved(self):
        sources, _, _, _, _ = effective_poststate()
        source = source_by_id(sources, CANONICAL_SOURCE_ID)
        expected = {
            "institution": "Electoral Commission New Zealand",
            "jurisdiction": "New Zealand",
            "domain": "elections",
            "endpoint_role": "2026 General Election confirmed timetable",
            "authoritative_url": "https://elections.nz/media-and-news/2026/key-dates-for-2026-general-election",
            "source_type": "official_electoral_timetable",
            "source_timezone": "Pacific/Auckland",
            "canonical_dependency_count": 6,
            "canonical_provenance_use": "CLEARED_CURATED_FACTUAL_METADATA",
        }
        for key, value in expected.items():
            self.assertEqual(source.get(key), value, key)
        if exact_prestate():
            self.assertEqual(source.get("automated_monitoring_use"), "ENDPOINT_REVIEW_REQUIRED")
            self.assertEqual(source.get("automated_retrieval_permission"), "PENDING")
            self.assertEqual(source.get("verification_mode"), "MANUAL_AUTHORITATIVE_RECHECK")

    def test_machine_source_is_monitor_only_and_zero_dependency(self):
        sources, _, _, _, _ = effective_poststate()
        source = source_by_id(sources, MACHINE_SOURCE_ID)
        self.assertEqual(source["authoritative_url"], "https://elections.nz/media-and-news/rss")
        self.assertEqual(source["source_type"], "official_rss_feed")
        self.assertEqual(source["canonical_dependency_count"], 0)
        self.assertEqual(source["automated_monitoring_use"], "CLEARED")
        self.assertEqual(
            source["automated_retrieval_permission"],
            "OFFICIAL_ADVERTISED_RSS_SUBSCRIPTION_INTERFACE_ROBOTS_COMPATIBLE_WITH_CRAWL_DELAY",
        )
        self.assertEqual(source["monitoring_readiness_status"], "LIVE_VALIDATED_NO_AUTO_COMMIT")
        self.assertEqual(source["verification_mode"], "AUTOMATED_PILOT")
        self.assertEqual(
            source["canonical_provenance_use"],
            "MONITOR_ONLY_TIMETABLE_PAGE_UPDATE_SENTINEL_NO_CANONICAL_DATE_AUTHORITY",
        )
        self.assertEqual(source["related_source_ids"], [CANONICAL_SOURCE_ID])
        self.assertFalse(source["live_validation_evidence"]["automatic_commit_allowed"])

    def test_route_has_exact_six_bundle_scope_rolling_limit_and_closed_authority_gates(self):
        _, expectations, _, _, _ = effective_poststate()
        route = route_by_id(expectations, ADAPTER_ID)
        self.assertEqual(route["source_id"], MACHINE_SOURCE_ID)
        self.assertEqual(route["canonical_schedule_source_id"], CANONICAL_SOURCE_ID)
        self.assertEqual(route["canonical_occurrence_ids"], PLAN["canonical_occurrence_ids"])
        self.assertEqual(
            route["canonical_timetable_page_identity"],
            PLAN["selection"]["canonical_timetable_url"],
        )
        self.assertEqual(route["request_budget_per_run"], 2)
        self.assertEqual(route["robots_request_count_per_run"], 1)
        self.assertEqual(route["rss_request_count_per_run"], 1)
        self.assertEqual(route["minimum_inter_request_delay_seconds"], 2)
        self.assertTrue(route["respect_greater_live_robots_crawl_delay"])
        self.assertEqual(route["rolling_feed_completeness"], "FINITE_ROLLING_WINDOW_NOT_EXHAUSTIVE_CHANGE_LOG")
        self.assertEqual(route["absence_semantics"], "NONE")
        for key in (
            "timetable_html_request_count_per_run",
            "item_followup_request_count_per_run",
            "results_data_request_count_per_run",
            "search_route_discovery_request_count_per_run",
        ):
            self.assertEqual(route[key], 0, key)
        for key in (
            "schedule_authority",
            "clock_authority",
            "lifecycle_authority",
            "certainty_authority",
            "canonical_date_mutation_allowed",
            "automatic_timetable_html_fetch_allowed",
            "automatic_item_link_fetch_allowed",
            "automatic_results_data_fetch_allowed",
            "automatic_search_route_discovery_allowed",
            "automatic_live_or_analysis_promotion_allowed",
            "automatic_commit_allowed",
        ):
            self.assertIs(route[key], False, key)
        self.assertIs(expectations["automatic_canonical_commit"], False)
        self.assertIs(expectations["google_calendar_write"], False)

    def test_exact_six_canonical_occurrences_remain_identifiable(self):
        ids = set(PLAN["canonical_occurrence_ids"])
        by_id = {r.get("occurrence_id"): r for r in CANONICAL.get("records", []) if r.get("occurrence_id") in ids}
        self.assertEqual(set(by_id), ids)
        for occurrence_id, row in by_id.items():
            self.assertEqual(row.get("series_id"), "WSER-EL-NZ-GEN", occurrence_id)
            self.assertEqual(row.get("source_id"), CANONICAL_SOURCE_ID, occurrence_id)
            self.assertEqual(row.get("source_timezone"), "Pacific/Auckland", occurrence_id)
            self.assertEqual(row.get("timing_type"), "CIVIL_DATE", occurrence_id)
            self.assertEqual(row.get("time_precision"), "DAY", occurrence_id)
            self.assertIs(row.get("all_day_semantics"), True, occurrence_id)

    def test_runtime_and_export_wiring_is_present(self):
        _, _, live, smoke, init = effective_poststate()
        self.assertIn("fetch_nz_election_robots_policy", live)
        self.assertIn("fetch_nz_election_rss", live)
        self.assertIn("nz_election_timetable_change_review_candidates", live)
        self.assertIn('"NZ_ELECTION_TIMETABLE_CHANGE_RSS" in configs', live)
        self.assertIn("time.sleep(nz_delay)", live)
        self.assertIn("fetch_nz_election_robots_policy", smoke)
        self.assertIn("fetch_nz_election_rss", smoke)
        self.assertIn('"NZ_ELECTION_TIMETABLE_CHANGE_RSS"', smoke)
        self.assertIn("from .nz_election_rss import (", init)
        self.assertIn('"NZ_ELECTION_RSS_URL"', init)
        self.assertIn('"fetch_nz_election_rss"', init)

    def test_check_only_helper_does_not_write_on_frozen_prestate(self):
        if not exact_prestate():
            self.skipTest("check-only write audit is frozen to exact pre-BY state")
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
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("READ_ONLY_PREFLIGHT", proc.stdout)
        self.assertEqual([p.read_bytes() for p in paths], before)

    def test_apply_requires_environment_gate_on_frozen_prestate(self):
        if not exact_prestate():
            self.skipTest("apply-gate audit is frozen to exact pre-BY state")
        env = dict(os.environ)
        env.pop("WORLD_SIGNALS_APPLY_MONITOR_BY", None)
        proc = subprocess.run(
            [sys.executable, str(HELPER_PATH), "--apply"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("WORLD_SIGNALS_APPLY_MONITOR_BY=1", proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
