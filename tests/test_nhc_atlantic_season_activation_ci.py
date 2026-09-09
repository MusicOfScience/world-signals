from __future__ import annotations

import json
from pathlib import Path
import unittest

from scripts.apply_nhc_atlantic_season_monitor_ci import (
    ADAPTER_ID,
    CANONICAL,
    EXPECTATIONS,
    PLAN,
    ROADMAP,
    RUNNER,
    SOURCE_ID,
    SOURCES,
    TARGET_IDS,
    assert_prestate,
    build_poststate,
)


class NHCAtlanticSeasonActivationCITests(unittest.TestCase):
    def load(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def state(self):
        return self.load(CANONICAL), self.load(SOURCES), self.load(EXPECTATIONS)

    def test_plan_is_exact_post_ch_and_opec_is_not_target(self):
        plan = self.load(PLAN)
        self.assertEqual(plan["exact_base_sha"], "c4f359c2c70f023c32990f20234aaf154dced152")
        self.assertEqual(plan["selection"]["source_id"], SOURCE_ID)
        self.assertEqual(plan["selection"]["canonical_occurrence_ids"], TARGET_IDS)
        self.assertTrue(plan["opec_quarantine_respected"])
        self.assertNotIn("OPEC", json.dumps(plan["selection"]))
        self.assertFalse(plan["authority_gates"]["automatic_commit_allowed"])
        self.assertFalse(plan["authority_gates"]["google_calendar_write"])

    def test_repository_is_exact_prestate_or_controlled_ci_poststate(self):
        canonical, sources, expectations = self.state()
        routes = [row for row in expectations["adapters"] if row.get("adapter_id") == ADAPTER_ID]
        if not routes:
            assert_prestate(canonical, sources, expectations)
            new_sources, new_expectations, new_runner, new_roadmap, pre, post = build_poststate(
                canonical,
                sources,
                expectations,
                RUNNER.read_text(encoding="utf-8"),
                ROADMAP.read_text(encoding="utf-8"),
            )
            self.assertEqual((new_sources["version"], len(new_sources["sources"])), ("2.03", 257))
            self.assertEqual((new_expectations["version"], len(new_expectations["adapters"])), ("0.28", 26))
            self.assertEqual(post["configured_adapter_count"], pre["configured_adapter_count"] + 1)
            self.assertIn('if "NHC_ATLANTIC_SEASON" in configs:', new_runner)
            self.assertIn("Stage 8 — recovery/status truth surfaces — DONE / GUARDED", new_roadmap)
        else:
            self.assertEqual(len(routes), 1)
            self.assertEqual((sources["version"], len(sources["sources"])), ("2.03", 257))
            self.assertEqual((expectations["version"], len(expectations["adapters"])), ("0.28", 26))

    def test_post_route_is_exact_two_occurrence_review_only_sentinel(self):
        canonical, sources, expectations = self.state()
        route = next((row for row in expectations["adapters"] if row.get("adapter_id") == ADAPTER_ID), None)
        if route is None:
            _, simulated, _, _, _, _ = build_poststate(
                canonical, sources, expectations, RUNNER.read_text(encoding="utf-8"), ROADMAP.read_text(encoding="utf-8")
            )
            route = next(row for row in simulated["adapters"] if row["adapter_id"] == ADAPTER_ID)
        self.assertEqual(route["source_id"], SOURCE_ID)
        self.assertEqual(route["canonical_occurrence_ids"], TARGET_IDS)
        self.assertEqual(route["cadence"], "DAILY")
        self.assertEqual(route["endpoint"]["request_budget_per_run"], 2)
        self.assertEqual(route["baseline"]["start_month_day"], "06-01")
        self.assertEqual(route["baseline"]["end_month_day"], "11-30")
        for gate in (
            "schedule_authority",
            "lifecycle_authority",
            "certainty_authority",
            "canonical_date_mutation_allowed",
            "automatic_new_occurrence_creation_allowed",
            "automatic_live_or_analysis_promotion_allowed",
            "automatic_commit_allowed",
        ):
            self.assertFalse(route[gate], gate)
        self.assertIn("NO_SEASON_DATE_OR_EVENT_STATE_SEMANTICS", route["rss_activity_policy"])

    def test_post_source_clearance_is_bounded_not_blanket_permission(self):
        canonical, sources, expectations = self.state()
        if not any(row.get("adapter_id") == ADAPTER_ID for row in expectations["adapters"]):
            sources, _, _, _, _, _ = build_poststate(
                canonical, sources, expectations, RUNNER.read_text(encoding="utf-8"), ROADMAP.read_text(encoding="utf-8")
            )
        source = next(row for row in sources["sources"] if row.get("source_id") == SOURCE_ID)
        self.assertEqual(source["automated_monitoring_use"], "CLEARED")
        self.assertEqual(source["verification_mode"], "AUTOMATED_PILOT")
        self.assertEqual(source["monitoring_readiness_status"], "PILOT_VALIDATED_NO_AUTO_COMMIT")
        self.assertEqual(source["live_adapter_id"], ADAPTER_ID)
        self.assertIn("READ_ONLY_SENTINEL_ONLY", source["automated_monitoring_scope"])
        self.assertIn("LOW_RATE_NHC_ENDPOINTS", source["automated_retrieval_permission"])
        self.assertIn("no schedule, lifecycle, certainty or completion authority", source["monitor_route_scope_note"])

    def test_canonical_targets_keep_source_native_window_and_identity(self):
        canonical, _, _ = self.state()
        by_id = {row["occurrence_id"]: row for row in canonical["records"]}
        first, second = by_id[TARGET_IDS[0]], by_id[TARGET_IDS[1]]
        self.assertEqual((first["start_local"], first["end_local"]), ("2026-06-01", "2026-11-30"))
        self.assertEqual((second["start_local"], second["end_local"]), ("2027-06-01", "2027-11-30"))
        for row in (first, second):
            self.assertEqual(row["timing_type"], "ALL_DAY_RANGE")
            self.assertEqual(row["time_precision"], "DAY")
            self.assertEqual(row["source_id"], SOURCE_ID)
            self.assertIsNone(row.get("start_utc"))

    def test_runtime_wiring_is_present_in_simulated_or_poststate(self):
        canonical, sources, expectations = self.state()
        runner = RUNNER.read_text(encoding="utf-8")
        if 'if "NHC_ATLANTIC_SEASON" in configs:' not in runner:
            _, _, runner, _, _, _ = build_poststate(
                canonical, sources, expectations, runner, ROADMAP.read_text(encoding="utf-8")
            )
        self.assertIn("fetch_nhc_atlantic_climatology", runner)
        self.assertIn("fetch_nhc_atlantic_outlook_health", runner)
        self.assertIn("nhc_atlantic_season_review_candidates", runner)
        self.assertIn('if "NHC_ATLANTIC_SEASON" in configs:', runner)
        self.assertIn('"request_budget_per_run":2', runner)
        self.assertIn('"rss_has_season_date_authority":False', runner)
        self.assertIn('"automatic_commit_allowed":False', runner)


if __name__ == "__main__":
    unittest.main()
