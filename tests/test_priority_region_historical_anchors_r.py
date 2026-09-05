from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.apply_priority_region_historical_anchors_r import (
    build_post_state,
    overlay_semantics,
    preflight,
)
from src.world_signals.analysis import analysis_population_readiness


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def version_tuple(value):
    return tuple(int(part) for part in str(value).split("."))


class PriorityRegionHistoricalAnchorsRTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load("data/coverage/PRIORITY_REGION_HISTORICAL_ANCHORS_R_PLAN_v0.1.json")
        cls.registry = load("data/canonical/registry.json")
        cls.schema = load("data/canonical/schema.json")
        cls.sources = load("data/sources/registry.json")
        cls.ledger = load("data/changes/ledger.json")
        cls.overlay = load("data/coverage/biosecurity_overlay.json")
        cls.analysis_schema = load("data/analysis/schema.json")
        cls.analysis_reviews = load("data/analysis/event_reviews.json")

    def state(self):
        return (
            str(self.registry.get("version")),
            len(self.registry.get("records", [])),
            str(self.sources.get("version")),
            len(self.sources.get("sources", [])),
            str(self.ledger.get("version")),
            len(self.ledger.get("changes", [])),
        )

    def simulated_or_live_post(self):
        if self.state()[:2] == ("0.28", 674):
            preflight(self.registry, self.schema, self.sources, self.ledger, self.overlay, self.plan)
            return build_post_state(
                deepcopy(self.registry),
                deepcopy(self.schema),
                deepcopy(self.sources),
                deepcopy(self.ledger),
                deepcopy(self.overlay),
                self.plan,
                "2026-09-06T01:15:00+10:00",
            )
        return self.registry, self.sources, self.ledger, self.overlay, {
            "readiness": analysis_population_readiness(
                self.analysis_schema, self.analysis_reviews, self.registry
            )
        }

    def test_repository_is_exact_pre_or_reviewed_post_state(self):
        state = self.state()
        if state == ("0.28", 674, "1.70", 233, "0.15", 44):
            pass
        else:
            self.assertGreaterEqual(version_tuple(state[0]), (0, 29))
            self.assertGreaterEqual(state[1], 678)
            self.assertGreaterEqual(version_tuple(state[2]), (1, 71))
            self.assertGreaterEqual(state[3], 236)
            self.assertGreaterEqual(version_tuple(state[4]), (0, 16))
            self.assertGreaterEqual(state[5], 48)
        self.assertEqual(str(self.schema.get("version")), "0.52")

    def test_scope_is_four_existing_series_one_per_priority_region(self):
        anchors = self.plan["anchors"]
        self.assertEqual(len(anchors), 4)
        self.assertEqual(
            {a["region"] for a in anchors},
            {"Africa", "South Asia", "Southeast Asia", "Latin America"},
        )
        existing_series = {r.get("series_id") for r in self.registry.get("records", [])}
        for anchor in anchors:
            self.assertIn(anchor["series_id"], existing_series)
        self.assertEqual(self.plan["postconditions"]["new_series_count"], 0)

    def test_simulation_preserves_all_preexisting_canonical_records(self):
        if self.state()[:2] != ("0.28", 674):
            self.skipTest("exact transform simulation is exercised only from pre-state")
        before_registry = digest(self.registry)
        before_schema = digest(self.schema)
        before_analysis_reviews = digest(self.analysis_reviews)
        post_registry, post_sources, post_ledger, post_overlay, report = self.simulated_or_live_post()
        self.assertEqual(digest(self.registry), before_registry)
        self.assertEqual(digest(self.schema), before_schema)
        self.assertEqual(digest(self.analysis_reviews), before_analysis_reviews)
        self.assertEqual(post_registry["records"][:674], self.registry["records"])
        self.assertEqual(post_ledger["changes"][:44], self.ledger["changes"])
        self.assertEqual(len(post_registry["records"]), 678)
        self.assertEqual(len(post_sources["sources"]), 236)
        self.assertEqual(len(post_ledger["changes"]), 48)
        self.assertEqual(report["readiness"]["broad_population_state"], "BLOCKED_PRIORITY_REGION_REVIEW_GAP")

    def test_completed_anchor_semantics_and_timing_are_exact(self):
        post_registry, *_ = self.simulated_or_live_post()
        by_id = {r["occurrence_id"]: r for r in post_registry["records"]}
        india = by_id["WSO-HIST-R-IN-GDP-2026Q1"]
        bi = by_id["WSO-HIST-R-ID-BI-202608"]
        cbe = by_id["WSO-HIST-R-EG-CBE-20260820"]
        ar = by_id["WSO-HIST-R-AR-CPI-202607"]
        for row in (india, bi, cbe, ar):
            self.assertEqual(row["lifecycle_status"], "COMPLETED")
            self.assertEqual(row["certainty_status"], "CONFIRMED")
            self.assertEqual(row["population_tranche"], "ANALYSIS_HISTORICAL_ANCHOR_R")
            self.assertEqual(len(row["status_history"]), 1)
            self.assertIn("not inferred from elapsed time", row["status_history"][0]["change_reason"])
        self.assertEqual(india["start_local"], "2026-08-31T16:00:00")
        self.assertEqual(india["start_utc"], "2026-08-31T10:30:00Z")
        self.assertEqual(india["publication_time_semantics"], "EXACT_LOCAL_TIME")
        self.assertFalse(india["all_day_semantics"])
        self.assertEqual((bi["start_local"], bi["end_local"]), ("2026-08-18", "2026-08-19"))
        for row in (bi, cbe, ar):
            self.assertIsNone(row.get("start_utc"))
            self.assertIsNone(row.get("publication_datetime"))
            self.assertTrue(row["all_day_semantics"])

    def test_schedule_and_completion_provenance_remain_distinct(self):
        post_registry, post_sources, post_ledger, *_ = self.simulated_or_live_post()
        by_id = {r["occurrence_id"]: r for r in post_registry["records"]}
        plan_by_id = {a["occurrence_id"]: a for a in self.plan["anchors"]}
        for oid, item in plan_by_id.items():
            row = by_id[oid]
            self.assertEqual(row["source_id"], item["schedule_source_id"])
            self.assertEqual(row["primary_source_assertion_id"], item["schedule_assertion_id"])
            self.assertEqual(row["last_successful_assertion_id"], item["completion_assertion_id"])
            self.assertEqual(row["status_history"][0]["source_assertion_id"], item["completion_assertion_id"])
            self.assertEqual(row["related_documents"][0]["source_id"], item["completion_source_id"])
            self.assertEqual(row["related_documents"][0]["source_locator"], item["outcome_url"])
        change_by_id = {c["occurrence_id"]: c for c in post_ledger["changes"]}
        for oid, item in plan_by_id.items():
            self.assertEqual(change_by_id[oid]["source_assertion_id"], item["completion_assertion_id"])
            self.assertEqual(change_by_id[oid]["old_values"], {"canonical_presence": False})
            self.assertTrue(change_by_id[oid]["new_values"]["canonical_presence"])

    def test_outcome_sources_do_not_gain_automation_permission(self):
        _, post_sources, *_ = self.simulated_or_live_post()
        by_id = {s["source_id"]: s for s in post_sources["sources"]}
        self.assertEqual(by_id["WSSRC-MAC-028"]["canonical_dependency_count"], 0)
        self.assertEqual(by_id["WSSRC-REG-012"]["canonical_dependency_count"], 0)
        self.assertEqual(by_id["WSSRC-REG2-008"]["canonical_dependency_count"], 0)
        self.assertEqual(
            by_id["WSSRC-REG-012"].get("automated_monitoring_use"),
            by_id["WSSRC-REG-004"].get("automated_monitoring_use"),
        )
        self.assertEqual(
            by_id["WSSRC-REG-012"].get("verification_mode"),
            by_id["WSSRC-REG-004"].get("verification_mode"),
        )
        self.assertIn("rights", (by_id["WSSRC-REG-012"].get("notes") or "").lower())

    def test_schedule_source_dependency_counts_advance_exactly_once(self):
        _, post_sources, *_ = self.simulated_or_live_post()
        by_id = {s["source_id"]: s for s in post_sources["sources"]}
        expected = {"WSSRC-MAC-017": 18, "WSSRC-REG-004": 5, "WSSRC-REGJ-005": 4, "WSSRC-REG2-006": 5}
        for sid, count in expected.items():
            self.assertEqual(by_id[sid]["canonical_dependency_count"], count)

    def test_biosecurity_overlay_changes_checkpoint_only(self):
        if self.state()[:2] == ("0.28", 674):
            _, _, _, post_overlay, _ = self.simulated_or_live_post()
            self.assertEqual(overlay_semantics(post_overlay), overlay_semantics(self.overlay))
            self.assertEqual(post_overlay["version"], "0.4")
            self.assertEqual(post_overlay["canonical_checkpoint"], {"registry_version": "0.29", "record_count": 678})
        else:
            self.assertGreaterEqual(version_tuple(self.overlay["version"]), (0, 4))
            self.assertEqual(
                self.overlay["canonical_checkpoint"],
                {"registry_version": self.registry["version"], "record_count": len(self.registry["records"])},
            )

    def test_analysis_readiness_preserves_r_anchor_contribution_through_descendants(self):
        post_registry, *_rest, report = self.simulated_or_live_post()
        readiness = report.get("readiness") or analysis_population_readiness(
            self.analysis_schema, self.analysis_reviews, post_registry
        )
        self.assertGreaterEqual(readiness["eligible_completed_occurrence_count"], 9)
        priority = {r["region"]: r for r in readiness["priority_geographic_stress_regions"]}
        for region in ("Africa", "South Asia", "Southeast Asia", "Latin America"):
            row = priority[region]
            self.assertGreaterEqual(row["eligible_completed_count"], 1)
            self.assertGreaterEqual(row["reviewed_count"], 1)
            self.assertEqual(row["state"], "REVIEWED_SAMPLE_PRESENT")
        self.assertGreaterEqual(readiness["reviewed_occurrence_count"], 6)
        self.assertEqual(readiness["broad_population_state"], "READY_FOR_CONTROLLED_EXPANSION")

    def test_frozen_plan_keeps_global_write_gates_closed(self):
        post = self.plan["postconditions"]
        self.assertFalse(post["automatic_canonical_commit"])
        self.assertFalse(post["google_calendar_write"])


if __name__ == "__main__":
    unittest.main()
