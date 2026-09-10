from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts/apply_japan_cpi_monitor_bw.py"
SPEC = importlib.util.spec_from_file_location("apply_japan_cpi_monitor_bw", MODULE)
TX = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TX)

PLAN = json.loads((ROOT / "data/monitor/JAPAN_CPI_RELEASE_SCHEDULE_BW_PLAN_v0.1.json").read_text())
CANONICAL = json.loads((ROOT / "data/canonical/registry.json").read_text())
SOURCES = json.loads((ROOT / "data/sources/registry.json").read_text())
EXPECTATIONS = json.loads((ROOT / "data/monitor/expectations.json").read_text())


def _version_tuple(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.split("."))


class JapanCPIScheduleActivationBWTests(unittest.TestCase):
    @staticmethod
    def _source() -> dict:
        rows = [x for x in SOURCES.get("sources", []) if x.get("source_id") == TX.SOURCE_ID]
        if len(rows) != 1:
            raise AssertionError(f"expected exactly one {TX.SOURCE_ID}, found {len(rows)}")
        return rows[0]

    @classmethod
    def _is_pre(cls) -> bool:
        source = cls._source()
        p = PLAN["preconditions"]
        return (
            SOURCES.get("version") == p["source_registry_version"]
            and len(SOURCES.get("sources", [])) == p["source_count"]
            and EXPECTATIONS.get("version") == p["monitor_expectations_version"]
            and len(EXPECTATIONS.get("adapters", [])) == p["configured_monitor_adapter_count"]
            and source.get("automated_monitoring_use") == p["source_automated_monitoring_use"]
            and source.get("automated_retrieval_permission") == p["source_automated_retrieval_permission"]
            and source.get("monitoring_readiness_status") == p["source_monitoring_readiness_status"]
            and source.get("monitoring_activation_status") == p["source_monitoring_activation_status"]
            and source.get("parser_version") == p["source_parser_version"]
            and not any(x.get("adapter_id") == TX.ADAPTER_ID for x in EXPECTATIONS.get("adapters", []))
        )

    @classmethod
    def _is_bw_or_descendant(cls) -> bool:
        source = cls._source()
        update = PLAN["source_governance_update"]
        routes = [x for x in EXPECTATIONS.get("adapters", []) if x.get("adapter_id") == TX.ADAPTER_ID]
        return (
            _version_tuple(str(SOURCES.get("version", "0"))) >= (1, 96)
            and len(SOURCES.get("sources", [])) >= 252
            and _version_tuple(str(EXPECTATIONS.get("version", "0"))) >= (0, 21)
            and len(EXPECTATIONS.get("adapters", [])) >= 19
            and source.get("automated_monitoring_use") == update["automated_monitoring_use"]
            and source.get("automated_retrieval_permission") == update["automated_retrieval_permission"]
            and source.get("monitoring_readiness_status") == update["monitoring_readiness_status"]
            and source.get("monitoring_activation_status") == update["monitoring_activation_status"]
            and source.get("live_adapter_id") == TX.ADAPTER_ID
            and source.get("parser_version") == "jp-stat-cpi-0.2"
            and len(routes) == 1
        )

    def _post(self):
        if self._is_pre():
            return TX.build_post_state(
                CANONICAL,
                SOURCES,
                EXPECTATIONS,
                PLAN,
                adapter_init_text=TX.ADAPTER_INIT_PATH.read_text(encoding="utf-8"),
                live_runner_text=TX.LIVE_RUNNER_PATH.read_text(encoding="utf-8"),
                smoke_runner_text=TX.SMOKE_RUNNER_PATH.read_text(encoding="utf-8"),
            )
        self.assertTrue(self._is_bw_or_descendant(), "state is neither exact BW pre-state nor a valid BW descendant")
        return SOURCES, EXPECTATIONS, None, None, None, {}

    def test_exact_preflight_or_bw_descendant_state(self):
        self.assertGreaterEqual(tuple(map(int, CANONICAL["version"].split("."))), (0, 41))
        self.assertGreaterEqual(len(CANONICAL["records"]), 689)
        if self._is_pre():
            TX.preflight(CANONICAL, SOURCES, EXPECTATIONS, PLAN)
        else:
            self.assertTrue(self._is_bw_or_descendant())

    def test_post_state_reuses_one_source_identity_and_adds_one_route(self):
        post_sources, post_expectations, *_ = self._post()
        before_by_id = {x["source_id"]: x for x in SOURCES["sources"]}
        after_by_id = {x["source_id"]: x for x in post_sources["sources"]}
        self.assertEqual(set(after_by_id), set(before_by_id))
        self.assertEqual(len(after_by_id), len(before_by_id))
        if self._is_pre():
            for source_id, before in before_by_id.items():
                if source_id != TX.SOURCE_ID:
                    self.assertEqual(after_by_id[source_id], before)

        source = after_by_id[TX.SOURCE_ID]
        update = PLAN["source_governance_update"]
        self.assertEqual(source["canonical_dependency_count"], 7)
        self.assertEqual(source["canonical_provenance_use"], "CLEARED_CURATED_FACTUAL_METADATA")
        self.assertEqual(source["rights_evidence_url"], TX.RIGHTS_URL)
        self.assertEqual(source["automated_monitoring_use"], update["automated_monitoring_use"])
        self.assertEqual(source["automated_retrieval_permission"], update["automated_retrieval_permission"])
        self.assertEqual(source["monitoring_readiness_status"], update["monitoring_readiness_status"])
        self.assertEqual(source["monitoring_activation_status"], update["monitoring_activation_status"])
        self.assertEqual(source["live_adapter_id"], TX.ADAPTER_ID)
        self.assertEqual(source["parser_version"], "jp-stat-cpi-0.2")
        self.assertEqual(len(source["monitor_endpoints"]), 2)
        self.assertEqual(source["monitor_endpoints"][0]["url"], TX.SCHEDULE_URL)
        self.assertEqual(source["monitor_endpoints"][1]["url"], TX.ROBOTS_URL)
        self.assertEqual(source["notes"]["time_rule_url"], TX.CLOCK_RULE_URL)
        self.assertEqual(source["live_validation_evidence"]["request_budget_per_run"], 2)
        self.assertEqual(source["live_validation_evidence"]["configured_exact_unique_match_count"], 7)
        self.assertFalse(source["live_validation_evidence"]["clock_exposed_by_schedule"])
        self.assertFalse(source["live_validation_evidence"]["automatic_commit_allowed"])

        routes = [x for x in post_expectations["adapters"] if x.get("adapter_id") == TX.ADAPTER_ID]
        self.assertEqual(len(routes), 1)
        route = routes[0]
        self.assertEqual(route["source_id"], TX.SOURCE_ID)
        self.assertEqual(route["canonical_schedule_source_id"], TX.SOURCE_ID)
        self.assertTrue(route["same_source_identity_for_canonical_and_monitor"])
        self.assertEqual(route["request_budget_per_run"], 2)
        self.assertEqual(route["robots_requests_per_run"], 1)
        self.assertEqual(route["schedule_requests_per_run"], 1)
        self.assertEqual(route["followup_requests_per_run"], 0)
        self.assertEqual(set(route["canonical_occurrence_ids"]), set(PLAN["canonical_occurrence_ids"]))
        for gate in (
            "schedule_mutation_authority",
            "clock_authority",
            "lifecycle_authority",
            "certainty_authority",
            "canonical_clock_mutation_allowed",
            "automatic_tokyo_cpi_followup_allowed",
            "automatic_estat_api_followup_allowed",
            "automatic_data_release_followup_allowed",
            "automatic_pdf_fetch_allowed",
            "automatic_news_followup_allowed",
            "automatic_search_route_discovery_allowed",
            "automatic_commit_allowed",
        ):
            self.assertFalse(route[gate], gate)
        self.assertFalse(post_expectations["automatic_canonical_commit"])
        self.assertFalse(post_expectations["google_calendar_write"])
        if self._is_pre():
            self.assertEqual(post_expectations["adapters"][:-1], EXPECTATIONS["adapters"])

    def test_source_mutation_boundary_preserves_identity_rights_and_clock_provenance(self):
        if not self._is_pre():
            self.skipTest("exact mutation-boundary simulation applies only to BW pre-state")
        before = self._source()
        after = TX.updated_source(before, PLAN)
        changed = TX._changed_keys(before, after)
        self.assertTrue(changed)
        self.assertTrue(changed <= TX.ALLOWED_SOURCE_MUTATION_KEYS)
        for key in TX.IMMUTABLE_SOURCE_KEYS:
            self.assertEqual(after.get(key), before.get(key), key)
        self.assertEqual(after["notes"], before["notes"])
        self.assertEqual(after["notes"]["time_rule_url"], TX.CLOCK_RULE_URL)

    def test_canonical_exact_datetimes_and_clock_provenance_remain_unchanged(self):
        by_id = {r["occurrence_id"]: r for r in CANONICAL["records"]}
        for expected in PLAN["canonical_occurrences"]:
            row = by_id[expected["occurrence_id"]]
            self.assertEqual(row["start_local"], expected["canonical_start_local"])
            self.assertEqual(row["start_utc"], expected["canonical_start_utc"])
            self.assertEqual(row["time_precision"], "MINUTE")
            self.assertEqual(row["time_basis"], "EXPLICIT_OCCURRENCE_TIME")
            self.assertEqual(row["timing_type"], "LOCAL_DATETIME")
            self.assertEqual(
                row["notes"],
                "Date from official schedule; 08:30 JST from official CPI publication rule.",
            )

    def test_runtime_patch_wires_bounded_date_only_route(self):
        if not self._is_pre():
            self.skipTest("patch simulation applies only to exact BW pre-state")
        _, _, adapter_init, live, smoke, _ = TX.build_post_state(
            CANONICAL,
            SOURCES,
            EXPECTATIONS,
            PLAN,
            adapter_init_text=TX.ADAPTER_INIT_PATH.read_text(encoding="utf-8"),
            live_runner_text=TX.LIVE_RUNNER_PATH.read_text(encoding="utf-8"),
            smoke_runner_text=TX.SMOKE_RUNNER_PATH.read_text(encoding="utf-8"),
        )
        self.assertIn('if "JAPAN_CPI_RELEASE_SCHEDULE" in configs:', live)
        self.assertIn("fetch_japan_cpi_robots_policy", live)
        self.assertIn("fetch_japan_cpi_schedule", live)
        self.assertIn("japan_cpi_schedule_review_candidates", live)
        self.assertIn('"followup_request_count":0', live)
        self.assertIn('"tokyo_cpi_followup_request_count":0', live)
        self.assertIn('"estat_api_followup_request_count":0', live)
        self.assertIn('"canonical_clock_mutation_allowed":False', live)
        self.assertIn('"adapter":"JAPAN_CPI_RELEASE_SCHEDULE"', smoke)
        self.assertIn("JAPAN_CPI_SCHEDULE_URL", adapter_init)
        self.assertIn("parse_japan_cpi_schedule", adapter_init)

    def test_apply_without_environment_gate_never_writes(self):
        if not self._is_pre():
            self.skipTest("apply-gate test applies only to exact BW pre-state")
        paths = [TX.SOURCES_PATH, TX.EXPECTATIONS_PATH, TX.LIVE_RUNNER_PATH, TX.SMOKE_RUNNER_PATH, TX.ADAPTER_INIT_PATH]
        before = {p: p.read_bytes() for p in paths}
        env = dict(os.environ)
        env.pop(TX.APPLY_ENV, None)
        proc = subprocess.run(
            [sys.executable, str(MODULE), "--apply"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        for path, raw in before.items():
            self.assertEqual(path.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
