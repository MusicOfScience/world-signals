from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts/apply_fao_release_calendar_monitor_bv.py"
SPEC = importlib.util.spec_from_file_location("apply_fao_release_calendar_monitor_bv", MODULE)
TX = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TX)

PLAN = json.loads((ROOT / "data/monitor/FAO_RELEASE_CALENDAR_BV_PLAN_v0.1.json").read_text())
CANONICAL = json.loads((ROOT / "data/canonical/registry.json").read_text())
SOURCES = json.loads((ROOT / "data/sources/registry.json").read_text())
EXPECTATIONS = json.loads((ROOT / "data/monitor/expectations.json").read_text())


def _version_tuple(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.split("."))


class FAOReleaseCalendarActivationBVTests(unittest.TestCase):
    @staticmethod
    def _source() -> dict:
        rows = [x for x in SOURCES.get("sources", []) if x.get("source_id") == TX.SOURCE_ID]
        if len(rows) != 1:
            raise AssertionError(f"expected exactly one {TX.SOURCE_ID}, found {len(rows)}")
        return rows[0]

    @classmethod
    def _is_pre(cls) -> bool:
        source = cls._source()
        return (
            SOURCES.get("version") == "1.94"
            and len(SOURCES.get("sources", [])) == 252
            and EXPECTATIONS.get("version") == "0.19"
            and len(EXPECTATIONS.get("adapters", [])) == 17
            and source.get("automated_monitoring_use") == "ENDPOINT_REVIEW_REQUIRED"
            and source.get("automated_retrieval_permission") == "PENDING"
            and source.get("monitoring_readiness_status") == "ENDPOINT_REVIEW_REQUIRED"
            and not any(x.get("adapter_id") == TX.ADAPTER_ID for x in EXPECTATIONS.get("adapters", []))
        )

    @classmethod
    def _is_bv_or_descendant(cls) -> bool:
        source = cls._source()
        update = PLAN["source_governance_update"]
        return (
            _version_tuple(SOURCES.get("version", "0")) >= (1, 95)
            and len(SOURCES.get("sources", [])) >= 252
            and _version_tuple(EXPECTATIONS.get("version", "0")) >= (0, 20)
            and len(EXPECTATIONS.get("adapters", [])) >= 18
            and source.get("automated_monitoring_use") == update["automated_monitoring_use"]
            and source.get("automated_retrieval_permission") == update["automated_retrieval_permission"]
            and source.get("monitoring_readiness_status") == update["monitoring_readiness_status"]
            and source.get("live_adapter_id") == TX.ADAPTER_ID
            and sum(x.get("adapter_id") == TX.ADAPTER_ID for x in EXPECTATIONS.get("adapters", [])) == 1
        )

    def _post(self):
        if self._is_pre():
            return TX.build_post_state(CANONICAL, SOURCES, EXPECTATIONS, PLAN)
        self.assertTrue(self._is_bv_or_descendant(), "state is neither exact BV pre-state nor a valid BV descendant")
        source = self._source()
        return SOURCES, EXPECTATIONS, None, None, None, source

    def test_exact_preflight_or_bv_descendant_state(self):
        self.assertEqual((CANONICAL["version"], len(CANONICAL["records"])), ("0.41", 689))
        if self._is_pre():
            TX.preflight(CANONICAL, SOURCES, EXPECTATIONS, PLAN)
        else:
            self.assertTrue(self._is_bv_or_descendant())

    def test_post_state_updates_one_source_identity_only(self):
        post_sources, post_expectations, *_ = self._post()
        before_by_id = {x["source_id"]: x for x in SOURCES["sources"]}
        after_by_id = {x["source_id"]: x for x in post_sources["sources"]}
        self.assertEqual(set(after_by_id), set(before_by_id))
        self.assertEqual(len(after_by_id), len(before_by_id))
        if self._is_pre():
            for source_id, before in before_by_id.items():
                if source_id == TX.SOURCE_ID:
                    continue
                self.assertEqual(after_by_id[source_id], before)
        source = after_by_id[TX.SOURCE_ID]
        update = PLAN["source_governance_update"]
        self.assertEqual(source["canonical_dependency_count"], 9)
        self.assertEqual(source["canonical_provenance_use"], "MANUAL_INFORMATIONAL_REFERENCE_ONLY")
        self.assertEqual(source["licence_review_status"], "CLEARED_FOR_FACTUAL_METADATA")
        self.assertEqual(source["ingestion_permission"], "PUBLIC_FACTS_ALLOWED")
        self.assertEqual(source["redistribution_permission"], "PUBLIC_FACTUAL_METADATA_ONLY")
        self.assertEqual(source["automated_monitoring_use"], update["automated_monitoring_use"])
        self.assertEqual(source["live_adapter_id"], TX.ADAPTER_ID)
        self.assertEqual(source["automated_retrieval_permission"], update["automated_retrieval_permission"])
        self.assertEqual(source["monitoring_readiness_status"], update["monitoring_readiness_status"])
        self.assertEqual(len(source["monitor_endpoints"]), 2)
        self.assertEqual(source["live_validation_evidence"]["request_count"], 2)
        self.assertEqual(source["live_validation_evidence"]["configured_match_count"], 6)
        self.assertFalse(source["live_validation_evidence"]["clock_exposed"])
        self.assertFalse(source["live_validation_evidence"]["automatic_commit_allowed"])

        routes = [x for x in post_expectations["adapters"] if x.get("adapter_id") == TX.ADAPTER_ID]
        self.assertEqual(len(routes), 1)
        route = routes[0]
        self.assertEqual(route["source_id"], TX.SOURCE_ID)
        self.assertEqual(route["canonical_schedule_source_id"], TX.SOURCE_ID)
        self.assertTrue(route["same_source_identity_for_canonical_and_monitor"])
        self.assertEqual(route["request_budget_per_run"], 2)
        self.assertEqual(route["robots_requests_per_run"], 1)
        self.assertEqual(route["calendar_requests_per_run"], 1)
        self.assertEqual(route["followup_requests_per_run"], 0)
        self.assertEqual(set(route["canonical_occurrence_ids"]), set(PLAN["canonical_occurrence_ids"]))
        self.assertFalse(route["schedule_authority"])
        self.assertFalse(route["lifecycle_authority"])
        self.assertFalse(route["certainty_authority"])
        self.assertFalse(route["canonical_clock_mutation_allowed"])
        self.assertFalse(route["automatic_amis_followup_allowed"])
        self.assertFalse(route["automatic_faostat_followup_allowed"])
        self.assertFalse(route["automatic_pdf_fetch_allowed"])
        self.assertFalse(route["automatic_news_followup_allowed"])
        self.assertFalse(route["automatic_search_route_discovery_allowed"])
        self.assertFalse(route["automatic_commit_allowed"])
        self.assertFalse(post_expectations["automatic_canonical_commit"])
        self.assertFalse(post_expectations["google_calendar_write"])
        if self._is_pre():
            self.assertEqual(post_expectations["adapters"][:-1], EXPECTATIONS["adapters"])

    def test_source_mutation_boundary_preserves_rights_and_provenance(self):
        if not self._is_pre():
            self.skipTest("exact mutation-boundary simulation applies only to BV pre-state")
        before = self._source()
        after = TX.updated_source(before, PLAN)
        changed = TX._changed_keys(before, after)
        self.assertTrue(changed)
        self.assertTrue(changed <= TX.ALLOWED_SOURCE_MUTATION_KEYS)
        for key in (
            "source_id", "institution", "jurisdiction", "domain", "endpoint_role", "authoritative_url",
            "source_type", "information_supplied", "source_timezone", "canonical_dependency_count",
            "canonical_provenance_use", "licence_constraints", "ingestion_permission", "licence_review_status",
            "redistribution_permission", "governance_backfill_basis", "governance_backfill_reviewed_at",
        ):
            self.assertEqual(after.get(key), before.get(key), key)

    def test_runtime_patch_wires_bounded_fao_route_only(self):
        if not self._is_pre():
            self.skipTest("patch simulation applies only to exact BV pre-state")
        _, _, live, smoke, adapter_init, _ = TX.build_post_state(CANONICAL, SOURCES, EXPECTATIONS, PLAN)
        self.assertIn('if "FAO_RELEASE_CALENDAR" in configs:', live)
        self.assertIn("fetch_fao_robots_policy", live)
        self.assertIn("fetch_fao_release_calendar", live)
        self.assertIn("fao_release_calendar_review_candidates", live)
        self.assertIn('"followup_request_count":0', live)
        self.assertIn('"amis_followup_request_count":0', live)
        self.assertIn('"faostat_followup_request_count":0', live)
        self.assertIn('"search_route_request_count":0', live)
        self.assertIn('"adapter":"FAO_RELEASE_CALENDAR"', smoke)
        self.assertIn("FAO_CALENDAR_URL", adapter_init)
        self.assertIn("parse_fao_release_calendar", adapter_init)

    def test_apply_without_environment_gate_never_writes(self):
        if not self._is_pre():
            self.skipTest("apply-gate test applies only to exact BV pre-state")
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
