from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLAN = json.loads((ROOT / "data/monitor/EUROPEAN_COUNCIL_MEETINGS_RSS_BZ_PLAN_v0.1.json").read_text())
CANONICAL = json.loads((ROOT / "data/canonical/registry.json").read_text())
SOURCES = json.loads((ROOT / "data/sources/registry.json").read_text())
EXPECTATIONS = json.loads((ROOT / "data/monitor/expectations.json").read_text())
HELPER_PATH = ROOT / "scripts/apply_european_council_rss_monitor_bz.py"

spec = importlib.util.spec_from_file_location("bz_helper", HELPER_PATH)
assert spec and spec.loader
HELPER = importlib.util.module_from_spec(spec)
spec.loader.exec_module(HELPER)

CANONICAL_SOURCE_ID = "WSSRC-INT-003"
MACHINE_SOURCE_ID = "WSSRC-INT-035"
ADAPTER_ID = "EUROPEAN_COUNCIL_MEETINGS_RSS"


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
        and SOURCES.get("version") == "1.98"
        and len(SOURCES.get("sources", [])) == 254
        and EXPECTATIONS.get("version") == "0.23"
        and len(EXPECTATIONS.get("adapters", [])) == 21
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


class EuropeanCouncilRSSActivationBZTests(unittest.TestCase):
    def test_frozen_prestate_or_descendant_poststate_is_coherent(self):
        if exact_prestate():
            self.assertEqual((CANONICAL["version"], len(CANONICAL["records"])), ("0.41", 689))
        else:
            self.assertGreaterEqual(float(CANONICAL.get("version", 0)), 0.41)
            self.assertGreaterEqual(len(CANONICAL.get("records", [])), 689)
            self.assertGreaterEqual(float(SOURCES.get("version", 0)), 1.99)
            self.assertGreaterEqual(len(SOURCES.get("sources", [])), 255)
            self.assertGreaterEqual(float(EXPECTATIONS.get("version", 0)), 0.24)
            self.assertGreaterEqual(len(EXPECTATIONS.get("adapters", [])), 22)

        sources, expectations, _, _, _ = effective_poststate()
        self.assertEqual(len([x for x in sources["sources"] if x.get("source_id") == MACHINE_SOURCE_ID]), 1)
        self.assertEqual(len([x for x in expectations["adapters"] if x.get("adapter_id") == ADAPTER_ID]), 1)

    def test_canonical_calendar_source_remains_unchanged_and_endpoint_held(self):
        sources, _, _, _, _ = effective_poststate()
        source = source_by_id(sources, CANONICAL_SOURCE_ID)
        expected = {
            "institution": "European Council / Council of the EU",
            "jurisdiction": "European Union",
            "domain": "international_institutions",
            "endpoint_role": "Meetings calendar",
            "authoritative_url": "https://www.consilium.europa.eu/en/meetings/calendar/",
            "source_type": "official_calendar",
            "source_timezone": "Europe/Brussels",
            "canonical_dependency_count": 3,
            "licence_review_status": "CLEARED_COUNCIL_EU_REUSE_WITH_ATTRIBUTION",
            "automated_retrieval_permission": "PENDING_ENDPOINT_OPERATIONAL_REVIEW",
            "monitoring_readiness_status": "ENDPOINT_REVIEW_REQUIRED",
            "runtime_health_state": "UNKNOWN_NOT_LIVE_POLLED",
        }
        for key, value in expected.items():
            self.assertEqual(source.get(key), value, key)

    def test_machine_source_is_separate_monitor_only_rss_identity(self):
        sources, _, _, _, _ = effective_poststate()
        source = source_by_id(sources, MACHINE_SOURCE_ID)
        self.assertEqual(source["authoritative_url"], PLAN["selection"]["rss_url"])
        self.assertEqual(source["source_type"], "official_rss_feed")
        self.assertEqual(source["canonical_dependency_count"], 0)
        self.assertEqual(source["automated_monitoring_use"], "CLEARED")
        self.assertEqual(source["automated_retrieval_permission"], "OFFICIAL_CONSILIUM_RSS_AUTOMATIC_LOADING_INTERFACE")
        self.assertEqual(source["monitoring_readiness_status"], "LIVE_VALIDATED_NO_AUTO_COMMIT")
        self.assertEqual(source["verification_mode"], "AUTOMATED_PILOT")
        self.assertEqual(source["canonical_provenance_use"], "MONITOR_ONLY_EUROPEAN_COUNCIL_RSS_NO_CANONICAL_DATE_AUTHORITY")
        self.assertEqual(source["related_source_ids"], [CANONICAL_SOURCE_ID])
        self.assertFalse(source["live_validation_evidence"]["automatic_commit_allowed"])
        self.assertEqual(source["live_validation_evidence"]["request_count"], 1)
        self.assertEqual(source["live_validation_evidence"]["direct_calendar_html_request_count"], 0)
        self.assertEqual(source["live_validation_evidence"]["item_followup_request_count"], 0)

    def test_route_has_exact_guid_scope_one_request_and_closed_authority_gates(self):
        _, expectations, _, _, _ = effective_poststate()
        route = route_by_id(expectations, ADAPTER_ID)
        self.assertEqual(route["source_id"], MACHINE_SOURCE_ID)
        self.assertEqual(route["canonical_schedule_source_id"], CANONICAL_SOURCE_ID)
        self.assertEqual(route["canonical_occurrence_ids"], PLAN["canonical_occurrence_ids"])
        self.assertEqual(
            route["configured_guid_to_occurrence"],
            {guid: row["occurrence_id"] for guid, row in PLAN["configured_feed_identity_by_guid"].items()},
        )
        self.assertEqual(
            route["configured_guid_titles"],
            {guid: row["expected_title"] for guid, row in PLAN["configured_feed_identity_by_guid"].items()},
        )
        self.assertEqual(route["request_budget_per_run"], 1)
        self.assertEqual(route["rss_request_count_per_run"], 1)
        self.assertEqual(route["machine_access_basis"], "OFFICIAL_CONSILIUM_RSS_AUTOMATIC_LOADING_INTERFACE")
        self.assertEqual(route["observed_date_source"], "OFFICIAL_RSS_ITEM_LINK_PATH_ONLY")
        self.assertEqual(route["absence_semantics"], "NONE")
        self.assertFalse(route["feed_item_count_is_permanent_invariant"])
        self.assertFalse(route["updated_field_is_event_time"])
        self.assertFalse(route["description_field_is_event_time"])
        for key in (
            "robots_request_count_per_run",
            "direct_calendar_html_request_count_per_run",
            "item_followup_request_count_per_run",
            "search_route_discovery_request_count_per_run",
        ):
            self.assertEqual(route[key], 0, key)
        for key in (
            "schedule_authority",
            "clock_authority",
            "lifecycle_authority",
            "certainty_authority",
            "canonical_date_mutation_allowed",
            "automatic_calendar_html_fetch_allowed",
            "automatic_item_link_fetch_allowed",
            "automatic_new_occurrence_creation_allowed",
            "automatic_search_route_discovery_allowed",
            "automatic_live_or_analysis_promotion_allowed",
            "automatic_commit_allowed",
        ):
            self.assertIs(route[key], False, key)
        self.assertIs(expectations["automatic_canonical_commit"], False)
        self.assertIs(expectations["google_calendar_write"], False)

    def test_exact_three_canonical_occurrences_remain_identifiable_and_date_only(self):
        ids = set(PLAN["canonical_occurrence_ids"])
        by_id = {r.get("occurrence_id"): r for r in CANONICAL.get("records", []) if r.get("occurrence_id") in ids}
        self.assertEqual(set(by_id), ids)
        for occurrence_id, row in by_id.items():
            self.assertEqual(row.get("series_id"), "WSER-INT-EUCO", occurrence_id)
            self.assertEqual(row.get("source_id"), CANONICAL_SOURCE_ID, occurrence_id)
            self.assertEqual(row.get("source_timezone"), "Europe/Brussels", occurrence_id)
            self.assertEqual(row.get("category"), "INTERNATIONAL_INSTITUTIONS", occurrence_id)
            self.assertEqual(row.get("event_type"), "INSTITUTIONAL_MEETING", occurrence_id)
            self.assertEqual(row.get("time_precision"), "DAY", occurrence_id)
            self.assertIs(row.get("all_day_semantics"), True, occurrence_id)
            self.assertIsNone(row.get("start_utc"), occurrence_id)
            self.assertIsNone(row.get("end_utc"), occurrence_id)

    def test_runtime_and_export_wiring_is_present(self):
        _, _, live, smoke, init = effective_poststate()
        self.assertIn("fetch_european_council_meetings_rss", live)
        self.assertIn("european_council_rss_review_candidates", live)
        self.assertIn('"EUROPEAN_COUNCIL_MEETINGS_RSS" in configs', live)
        self.assertIn("direct_calendar_html_request_count", live)
        self.assertIn("automatic_new_occurrence_creation_allowed", live)
        self.assertIn("fetch_european_council_meetings_rss", smoke)
        self.assertIn('"EUROPEAN_COUNCIL_MEETINGS_RSS"', smoke)
        self.assertIn("from .european_council_rss import (", init)
        self.assertIn('"EUROPEAN_COUNCIL_MEETINGS_RSS"', init)
        self.assertIn('"fetch_european_council_meetings_rss"', init)

    def test_check_only_helper_does_not_write_on_frozen_prestate(self):
        if not exact_prestate():
            self.skipTest("check-only write audit is frozen to exact pre-BZ state")
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
            self.skipTest("apply-gate audit is frozen to exact pre-BZ state")
        env = dict(os.environ)
        env.pop("WORLD_SIGNALS_APPLY_MONITOR_BZ", None)
        proc = subprocess.run(
            [sys.executable, str(HELPER_PATH), "--apply"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("WORLD_SIGNALS_APPLY_MONITOR_BZ=1", proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
