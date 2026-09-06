from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/monitor/RBA_FSR_MONITOR_ALIGNMENT_AL_PLAN_v0.1.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
REVIEWS_PATH = ROOT / "data/analysis/event_reviews.json"
SCRIPT_PATH = ROOT / "scripts/apply_rba_fsr_monitor_alignment_al.py"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def load_apply_module():
    spec = importlib.util.spec_from_file_location("apply_rba_fsr_monitor_alignment_al", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class RbaFsrMonitorAlignmentALTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load(PLAN_PATH)
        cls.canonical = load(CANONICAL_PATH)
        cls.expectations = load(EXPECTATIONS_PATH)
        cls.reviews = load(REVIEWS_PATH)
        cls.apply = load_apply_module()

    def candidate_expectations(self) -> dict:
        """Return AL's repaired scope while allowing later monitor descendants.

        AL's historical transform remains exact at v0.8 -> v0.9. Live descendants
        may legitimately advance the monitor dataset version or add adapters, but
        must preserve AL's explicit RBA scope and matching semantics.
        """
        version = self.expectations.get("version")
        if version == self.plan["monitor_change"]["from_version"]:
            return self.apply.transform(self.expectations, self.plan)
        self.assertGreaterEqual(
            version_tuple(version),
            version_tuple(self.plan["monitor_change"]["to_version"]),
        )
        return copy.deepcopy(self.expectations)

    def assert_live_descendant_preserves_al_contract(self, candidate: dict) -> None:
        self.assertGreaterEqual(
            version_tuple(candidate["version"]),
            version_tuple(self.plan["monitor_change"]["to_version"]),
        )
        self.assertFalse(candidate["automatic_canonical_commit"])
        self.assertFalse(candidate["google_calendar_write"])
        cfg = self.apply.adapter(candidate)
        self.assertEqual(
            cfg["canonical_occurrence_ids"],
            ["WSO-FIN-B-0001", "WSO-FIN-B-0004"],
        )
        self.assertEqual(
            cfg["matching"],
            {"same_year": True, "nearest_planned_occurrence_max_days": 75},
        )
        self.assertFalse(cfg["automatic_commit_allowed"])

        march_candidates, march_observations = self.apply.rba_fsr_review_candidates(
            self.canonical["records"], [self.apply.current_march_item(self.plan)], cfg
        )
        self.assertEqual(march_candidates, [])
        self.assertEqual(len(march_observations), 1)
        self.assertEqual(march_observations[0]["type"], "RBA_PUBLICATION_ALREADY_REFLECTED")
        self.assertEqual(march_observations[0]["occurrence_id"], "WSO-FIN-B-0004")

        october_candidates, october_observations = self.apply.rba_fsr_review_candidates(
            self.canonical["records"], [self.apply.october_item()], cfg
        )
        self.assertEqual(october_observations, [])
        self.assertEqual(len(october_candidates), 1)
        self.assertEqual(october_candidates[0]["occurrence_id"], "WSO-FIN-B-0001")
        self.assertEqual(october_candidates[0]["diff_type"], "LIFECYCLE_CHANGED")
        self.assertFalse(october_candidates[0]["automatic_commit_allowed"])

    def test_plan_is_frozen_to_exact_post_ak_main(self):
        self.assertEqual(
            self.plan["base_main_sha"],
            "72103267f90475b04c80129e03b41b605d4b7f58",
        )
        self.assertEqual(self.plan["architecture_layer"], "SOURCE_CHANGE_MONITOR")
        self.assertFalse(self.plan["guardrails"]["canonical_mutation_allowed"])
        self.assertFalse(self.plan["guardrails"]["analysis_mutation_allowed"])
        self.assertFalse(self.plan["guardrails"]["google_calendar_write"])
        self.assertFalse(self.plan["guardrails"]["auto_merge"])

    def test_canonical_rba_occurrences_remain_distinct_and_source_native(self):
        rows = {
            row["occurrence_id"]: row
            for row in self.canonical["records"]
            if row.get("occurrence_id") in {"WSO-FIN-B-0001", "WSO-FIN-B-0004"}
        }
        self.assertEqual(set(rows), {"WSO-FIN-B-0001", "WSO-FIN-B-0004"})
        self.assertEqual(rows["WSO-FIN-B-0004"]["lifecycle_status"], "COMPLETED")
        self.assertEqual(rows["WSO-FIN-B-0004"]["start_local"], "2026-03-19T11:30:00")
        self.assertEqual(rows["WSO-FIN-B-0004"]["source_timezone"], "Australia/Sydney")
        self.assertEqual(rows["WSO-FIN-B-0004"]["start_utc"], "2026-03-19T00:30:00Z")
        self.assertEqual(rows["WSO-FIN-B-0001"]["lifecycle_status"], "PLANNED")
        self.assertEqual(rows["WSO-FIN-B-0001"]["start_local"], "2026-10-01T11:30:00")
        self.assertEqual(rows["WSO-FIN-B-0001"]["source_timezone"], "Australia/Sydney")

    def test_pre_repair_scope_reproduces_unmatched_observation(self):
        pre = self.candidate_expectations()
        pre["version"] = self.plan["monitor_change"]["from_version"]
        cfg = self.apply.adapter(pre)
        cfg["canonical_occurrence_ids"] = list(self.plan["monitor_change"]["preserve_occurrence_ids"])
        self.apply.prove_pre_defect(self.plan, self.canonical, pre)

    def test_candidate_scope_resolves_march_and_preserves_october(self):
        candidate = self.candidate_expectations()
        if candidate.get("version") == self.plan["monitor_change"]["to_version"]:
            self.apply.validate_candidate(self.plan, self.canonical, candidate)
        else:
            self.assert_live_descendant_preserves_al_contract(candidate)
        cfg = self.apply.adapter(candidate)
        self.assertEqual(
            cfg["canonical_occurrence_ids"],
            ["WSO-FIN-B-0001", "WSO-FIN-B-0004"],
        )
        self.assertEqual(cfg["matching"], {"same_year": True, "nearest_planned_occurrence_max_days": 75})
        self.assertFalse(cfg["automatic_commit_allowed"])

    def test_transform_changes_only_version_and_rba_scope(self):
        if self.expectations.get("version") != self.plan["monitor_change"]["from_version"]:
            self.skipTest("historical transform boundary is exercised only against frozen v0.8 pre-state")
        candidate = self.apply.transform(self.expectations, self.plan)
        expected = copy.deepcopy(self.expectations)
        expected["version"] = "0.9"
        self.apply.adapter(expected)["canonical_occurrence_ids"] = ["WSO-FIN-B-0001", "WSO-FIN-B-0004"]
        self.assertEqual(candidate, expected)

    def test_explicit_scope_is_not_dynamic_series_expansion(self):
        candidate = self.candidate_expectations()
        cfg = self.apply.adapter(candidate)
        configured = set(cfg["canonical_occurrence_ids"])
        series_ids = {
            row["occurrence_id"]
            for row in self.canonical["records"]
            if row.get("series_id") == "WSER-FIN-AU-RBA-FSR"
        }
        self.assertEqual(configured, {"WSO-FIN-B-0001", "WSO-FIN-B-0004"})
        self.assertTrue(configured.issubset(series_ids))
        self.assertTrue(self.plan["guardrails"]["explicit_monitor_scope_remains_reviewed_configuration"])
        self.assertTrue(self.plan["guardrails"]["dynamic_series_scope_expansion_prohibited_in_this_tranche"])

    def test_analysis_population_and_exact_series_remain_untouched(self):
        post = self.plan["postconditions"]
        self.assertEqual((post["analysis_reviews_version"], post["analysis_review_count"]), ("0.10", 14))
        self.assertGreaterEqual(version_tuple(self.reviews["version"]), version_tuple(post["analysis_reviews_version"]))
        self.assertGreaterEqual(len(self.reviews["reviews"]), post["analysis_review_count"])
        exact = [
            (review.get("analysis_id"), movement.get("movement_id"))
            for review in self.reviews["reviews"]
            for movement in (review.get("what_moved") or [])
            if movement.get("measurement_precision") == "EXACT_TIMESTAMP_SERIES"
        ]
        self.assertEqual(exact, [])
        protected = set(self.plan["mutation_boundary"]["protected_unchanged_paths"])
        self.assertIn("data/analysis/schema.json", protected)
        self.assertIn("data/analysis/event_reviews.json", protected)
        self.assertIn("data/analysis/evidence_registry.json", protected)


if __name__ == "__main__":
    unittest.main()