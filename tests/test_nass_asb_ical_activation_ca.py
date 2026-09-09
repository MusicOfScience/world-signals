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
MODULE_PATH = ROOT / "scripts/apply_nass_asb_ical_monitor_ca.py"
SPEC = importlib.util.spec_from_file_location("apply_nass_asb_ical_monitor_ca", MODULE_PATH)
TX = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TX)

PLAN_PATH = ROOT / "data/monitor/USDA_NASS_ASB_ICAL_CA_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
LIVE_PATH = ROOT / "scripts/run_live_monitor.py"
SMOKE_PATH = ROOT / "scripts/run_adapter_smoke.py"
INIT_PATH = ROOT / "src/world_signals/adapters/__init__.py"


def exact_prestate(canonical: dict, sources: dict, expectations: dict) -> bool:
    return (
        canonical.get("version") == "0.41"
        and len(canonical.get("records", [])) == 689
        and sources.get("version") == "1.99"
        and len(sources.get("sources", [])) == 255
        and expectations.get("version") == "0.24"
        and len(expectations.get("adapters", [])) == 22
        and not any(x.get("adapter_id") == TX.ADAPTER_ID for x in expectations.get("adapters", []))
    )


class NASSASBActivationCATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        cls.canonical = json.loads(CANONICAL_PATH.read_text(encoding="utf-8"))
        cls.sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
        cls.expectations = json.loads(EXPECTATIONS_PATH.read_text(encoding="utf-8"))

    def _is_post_or_descendant(self) -> bool:
        source = TX.source_by_id(self.sources, TX.SOURCE_ID)
        routes = [x for x in self.expectations.get("adapters", []) if x.get("adapter_id") == TX.ADAPTER_ID]
        return (
            len(routes) == 1
            and source.get("live_adapter_id") == TX.ADAPTER_ID
            and source.get("automated_monitoring_use") == "CLEARED_BOUNDED_OFFICIAL_ICAL"
            and source.get("canonical_provenance_use") == "CLEARED_CURATED_FACTUAL_METADATA"
            and self.expectations.get("automatic_canonical_commit") is False
            and self.expectations.get("google_calendar_write") is False
        )

    def _simulate(self):
        if not exact_prestate(self.canonical, self.sources, self.expectations):
            self.skipTest("CA exact patch simulation is frozen to exact post-BZ pre-state")
        return TX.build_post_state(self.canonical, self.sources, self.expectations, self.plan)

    def test_exact_prestate_or_valid_ca_descendant(self):
        self.assertTrue(exact_prestate(self.canonical, self.sources, self.expectations) or self._is_post_or_descendant())

    def test_source_identity_rights_and_provenance_are_preserved(self):
        if exact_prestate(self.canonical, self.sources, self.expectations):
            sources_post, _, _, _, _, _ = self._simulate()
        else:
            sources_post = self.sources
        before = TX.source_by_id(self.sources, TX.SOURCE_ID)
        after = TX.source_by_id(sources_post, TX.SOURCE_ID)
        for key in (
            "source_id", "institution", "jurisdiction", "domain", "endpoint_role", "authoritative_url",
            "source_type", "source_timezone", "canonical_dependency_count", "canonical_provenance_use",
            "licence_review_status", "ingestion_permission", "redistribution_permission", "rights_evidence_url",
            "rights_summary", "machine_readable_available",
        ):
            self.assertEqual(after.get(key), before.get(key), key)
        self.assertEqual(after["canonical_dependency_count"], 5)
        self.assertEqual(after["canonical_provenance_use"], "CLEARED_CURATED_FACTUAL_METADATA")

    def test_exact_source_mutation_boundary_and_no_duplicate_source(self):
        if not exact_prestate(self.canonical, self.sources, self.expectations):
            self.skipTest("exact source mutation audit is frozen to CA pre-state")
        sources_post, _, _, _, _, _ = self._simulate()
        before = {x["source_id"]: x for x in self.sources["sources"]}
        after = {x["source_id"]: x for x in sources_post["sources"]}
        self.assertEqual(set(before), set(after))
        self.assertEqual(len(after), 255)
        for sid, row in before.items():
            if sid != TX.SOURCE_ID:
                self.assertEqual(after[sid], row, sid)
        changed = {k for k in set(before[TX.SOURCE_ID]) | set(after[TX.SOURCE_ID]) if before[TX.SOURCE_ID].get(k) != after[TX.SOURCE_ID].get(k)}
        self.assertLessEqual(changed, TX.ALLOWED_SOURCE_MUTATION_KEYS)
        self.assertTrue(changed)

    def test_route_is_exact_one_request_same_source_and_all_authority_closed(self):
        if exact_prestate(self.canonical, self.sources, self.expectations):
            _, expectations_post, _, _, _, _ = self._simulate()
        else:
            expectations_post = self.expectations
        route = TX.route_by_id(expectations_post, TX.ADAPTER_ID)
        self.assertEqual(route["source_id"], TX.SOURCE_ID)
        self.assertEqual(route["canonical_schedule_source_id"], TX.SOURCE_ID)
        self.assertEqual(route["canonical_occurrence_ids"], self.plan["canonical_occurrence_ids"])
        self.assertEqual(route["request_budget_per_run"], 1)
        self.assertEqual(route["ical_request_count_per_run"], 1)
        for key in (
            "robots_request_count_per_run", "calendar_html_request_count_per_run", "report_followup_request_count_per_run",
            "search_route_discovery_request_count_per_run",
        ):
            self.assertEqual(route[key], 0, key)
        self.assertEqual(route["floating_datetime_timezone"], "America/New_York")
        self.assertEqual(route["floating_timezone_basis"], "FIRST_PARTY_NASS_REPORTS_BY_DATE_PAGES_LABEL_TARGET_RELEASES_ET")
        for key in (
            "dtend_is_event_end", "dtstamp_is_event_time", "sequence_is_event_state", "description_is_event_time",
            "schedule_authority", "clock_authority", "lifecycle_authority", "certainty_authority",
            "canonical_datetime_mutation_allowed", "automatic_calendar_html_fetch_allowed", "automatic_report_followup_allowed",
            "automatic_new_occurrence_creation_allowed", "automatic_search_route_discovery_allowed",
            "automatic_live_or_analysis_promotion_allowed", "automatic_commit_allowed",
        ):
            self.assertFalse(route[key], key)

    def test_canonical_five_rows_are_byte_semantically_unchanged(self):
        before = {r["occurrence_id"]: deepcopy(r) for r in self.canonical["records"] if r.get("source_id") == TX.SOURCE_ID}
        self.assertEqual(set(before), set(self.plan["canonical_occurrence_ids"]))
        self.assertEqual(len(before), 5)
        if exact_prestate(self.canonical, self.sources, self.expectations):
            self._simulate()
        after = {r["occurrence_id"]: r for r in self.canonical["records"] if r.get("source_id") == TX.SOURCE_ID}
        self.assertEqual(after, before)

    def test_runtime_and_export_patch_contains_only_bounded_nass_route(self):
        if exact_prestate(self.canonical, self.sources, self.expectations):
            _, _, live, smoke, init, _ = self._simulate()
        else:
            live = LIVE_PATH.read_text(encoding="utf-8")
            smoke = SMOKE_PATH.read_text(encoding="utf-8")
            init = INIT_PATH.read_text(encoding="utf-8")
        self.assertIn("fetch_nass_asb_ical", live)
        self.assertIn("nass_asb_ical_review_candidates", live)
        self.assertIn('"USDA_NASS_ASB_ICAL" in configs', live)
        self.assertIn('"calendar_html_request_count":0', live)
        self.assertIn('"report_followup_request_count":0', live)
        self.assertIn('"automatic_commit_allowed":False', live)
        self.assertIn("fetch_nass_asb_ical", smoke)
        self.assertIn('"USDA_NASS_ASB_ICAL"', smoke)
        self.assertIn("NASS_ASB_ICAL_URL", init)
        self.assertIn("NASSASBRelease", init)
        self.assertIn("parse_nass_asb_ical", init)

    def test_check_only_helper_is_read_only_on_frozen_prestate(self):
        if not exact_prestate(self.canonical, self.sources, self.expectations):
            self.skipTest("check-only write audit is frozen to exact CA pre-state")
        paths = (SOURCES_PATH, EXPECTATIONS_PATH, LIVE_PATH, SMOKE_PATH, INIT_PATH, CANONICAL_PATH)
        before = {p: p.read_bytes() for p in paths}
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        result = subprocess.run([sys.executable, str(MODULE_PATH)], cwd=ROOT, env=env, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "PASS")
        for path, raw in before.items():
            self.assertEqual(path.read_bytes(), raw, path)

    def test_apply_requires_explicit_environment_gate(self):
        if not exact_prestate(self.canonical, self.sources, self.expectations):
            self.skipTest("apply-gate audit is frozen to exact CA pre-state")
        paths = (SOURCES_PATH, EXPECTATIONS_PATH, LIVE_PATH, SMOKE_PATH, INIT_PATH, CANONICAL_PATH)
        before = {p: p.read_bytes() for p in paths}
        env = dict(os.environ)
        env.pop(TX.APPLY_ENV, None)
        env["PYTHONPATH"] = str(ROOT / "src")
        result = subprocess.run([sys.executable, str(MODULE_PATH), "--apply"], cwd=ROOT, env=env, capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("apply refused", result.stderr + result.stdout)
        for path, raw in before.items():
            self.assertEqual(path.read_bytes(), raw, path)

    def test_plan_poststate_is_narrow_and_write_gates_closed(self):
        self.assertEqual(self.plan["postconditions"]["source_registry_version"], "2.00")
        self.assertEqual(self.plan["postconditions"]["source_count"], 255)
        self.assertEqual(self.plan["postconditions"]["monitor_expectations_version"], "0.25")
        self.assertEqual(self.plan["postconditions"]["configured_monitor_adapter_count"], 23)
        self.assertFalse(self.plan["postconditions"]["automatic_canonical_commit"])
        self.assertFalse(self.plan["postconditions"]["google_calendar_write"])
        self.assertEqual(len(self.plan["mutation_boundary"]), 5)


if __name__ == "__main__":
    unittest.main()
