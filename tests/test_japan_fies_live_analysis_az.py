from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import apply_japan_fies_live_analysis_az as apply_az
from world_signals.analysis import analysis_population_readiness, validate_analysis
from world_signals.live_analysis_bridge import (
    production_live_input_count,
    public_review_without_live_inputs,
    validate_live_analysis_bridge,
)
from world_signals.live_intelligence import (
    public_live_intelligence_projection,
    validate_live_intelligence,
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def stable_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class JapanFIESLiveAnalysisAZTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load(apply_az.PLAN_PATH)
        cls.payload = load(apply_az.PAYLOAD_PATH)
        cls.canonical = load(apply_az.CANONICAL_PATH)
        cls.current_live_schema = load(apply_az.LIVE_SCHEMA_PATH)
        cls.current_live_observations = load(apply_az.LIVE_OBSERVATIONS_PATH)
        cls.current_live_evidence = load(apply_az.LIVE_EVIDENCE_PATH)
        cls.current_analysis_schema = load(apply_az.ANALYSIS_SCHEMA_PATH)
        cls.current_reviews = load(apply_az.REVIEWS_PATH)
        cls.current_analysis_evidence = load(apply_az.ANALYSIS_EVIDENCE_PATH)
        cls.target = apply_az.simulate(cls.plan, cls.payload)
        apply_az.assert_target(cls.plan, cls.target)
        cls.live_by_id = {
            row["observation_id"]: row
            for row in cls.target["live_observations"]["observations"]
        }
        cls.analysis_by_id = {
            row["analysis_id"]: row for row in cls.target["reviews"]["reviews"]
        }
        cls.analysis_evidence_by_id = {
            row["evidence_id"]: row
            for row in cls.target["analysis_evidence"]["evidence"]
        }

    def test_exact_post_80_base_and_canonical_target_are_frozen(self):
        self.assertEqual(
            self.plan["exact_base_main_sha"],
            "bc8e588624e8a76f6847d7c80aef7e7fa5ecafa9",
        )
        row = next(
            item for item in self.canonical["records"]
            if item.get("occurrence_id") == "WSO-MAC-B-0041"
        )
        self.assertEqual(row["series_id"], "WSER-MAC-JP-HHSPEND")
        self.assertEqual(row["jurisdiction"], "Japan")
        self.assertEqual(row.get("region") or row.get("broad_region"), "East Asia")
        self.assertEqual(row["event_type"], "DATA_RELEASE")
        self.assertEqual(row["lifecycle_status"], "COMPLETED")
        self.assertEqual(row["start_local"], "2026-09-04")
        self.assertEqual(row["source_timezone"], "Asia/Tokyo")
        self.assertEqual(row["time_precision"], "DAY")
        self.assertIsNone(row["start_utc"])

    def test_read_only_simulation_validates_all_three_contracts(self):
        live = validate_live_intelligence(
            self.target["live_schema"],
            self.target["live_evidence"],
            self.target["live_observations"],
            self.canonical,
        )
        self.assertTrue(live.ok, live.errors)
        analysis = validate_analysis(
            self.target["analysis_schema"],
            self.target["analysis_evidence"],
            self.target["reviews"],
            self.canonical,
        )
        self.assertTrue(analysis.ok, analysis.errors)
        bridge = validate_live_analysis_bridge(
            self.target["analysis_schema"],
            self.target["reviews"],
            self.target["live_observations"],
        )
        self.assertTrue(bridge.ok, bridge.errors)

    def test_target_population_is_bounded_and_public_gates_stay_closed(self):
        post = self.plan["target_state"]
        self.assertEqual(self.target["live_schema"]["version"], "0.4")
        self.assertEqual(len(self.target["live_observations"]["observations"]), 4)
        self.assertEqual(len(self.target["live_evidence"]["evidence"]), 6)
        # AZ introduced Analysis schema v0.6; descendants may advance the schema
        # while preserving AZ-owned Live→Analysis population and bridge invariants.
        analysis_version = tuple(
            int(part) for part in self.target["analysis_schema"]["version"].split(".")
        )
        self.assertGreaterEqual(analysis_version, (0, 6))
        self.assertEqual(self.target["reviews"]["version"], "0.17")
        self.assertEqual(len(self.target["reviews"]["reviews"]), 21)
        self.assertEqual(self.target["analysis_evidence"]["version"], "0.17")
        self.assertEqual(len(self.target["analysis_evidence"]["evidence"]), 95)
        self.assertEqual(production_live_input_count(self.target["reviews"]), 1)
        policy = self.target["analysis_schema"]["live_input_policy"]
        self.assertEqual(policy["maximum_production_live_inputs"], 1)
        self.assertEqual(policy["maximum_live_inputs_per_review"], 1)
        self.assertFalse(policy["public_live_input_projection_allowed"])
        self.assertFalse(
            self.target["live_schema"]["population_policy"]["public_observation_projection_allowed"]
        )
        self.assertEqual(post["analysis_evidence_count"], 95)

    def test_new_live_row_is_economic_outcome_not_revision(self):
        row = self.live_by_id["WSLI-MAC-JPN-FIES-202607-001"]
        self.assertEqual(row["observation_type"], "ECONOMIC_DATA_OBSERVATION")
        self.assertEqual(row["verification_state"], "PRIMARY_CONFIRMED")
        self.assertEqual(
            row["canonical_links"],
            [{"occurrence_id": "WSO-MAC-B-0041", "relationship": "OUTCOME_OF"}],
        )
        self.assertIsNone(row["revision_of_observation_id"])
        self.assertIn("does not invent prior Live Intelligence history", row["summary"])
        self.assertFalse(row["automatic_canonical_commit"])
        self.assertFalse(row["google_calendar_write"])
        for prohibited in self.target["live_schema"]["prohibited_analysis_fields"]:
            self.assertNotIn(prohibited, row)

    def test_live_evidence_keeps_civil_publication_time_and_revision_context(self):
        ids = {
            "WSEV-LI-JP-FIES-STATGO-20260904",
            "WSEV-LI-JP-FIES-REVISION-20260904",
        }
        rows = {
            row["evidence_id"]: row for row in self.target["live_evidence"]["evidence"]
            if row.get("evidence_id") in ids
        }
        self.assertEqual(set(rows), ids)
        self.assertTrue(all(row["evidence_class"] == "PRIMARY_OFFICIAL" for row in rows.values()))
        self.assertTrue(all(row["publication_time"]["precision"] == "CIVIL_DATE" for row in rows.values()))
        self.assertTrue(all(row["publication_time"]["published_date"] == "2026-09-04" for row in rows.values()))
        self.assertIn("CORRECTION_OR_REVISION", rows["WSEV-LI-JP-FIES-REVISION-20260904"]["roles"])

    def test_analysis_evidence_proves_preannouncement_without_collapsing_layers(self):
        notice = self.analysis_evidence_by_id["WSEV-JP-FIES-REBASING-NOTICE-20260707"]
        self.assertEqual(notice["evidence_class"], "PRIMARY_OFFICIAL")
        self.assertEqual(notice["published_at"], "2026-07-07")
        self.assertTrue(any("4 September" in item for item in notice["supports"]))
        self.assertTrue(any("must not be treated" in item for item in notice["supports"]))

        live_ids = {
            row["evidence_id"] for row in self.target["live_evidence"]["evidence"]
        }
        analysis_ids = {
            row["evidence_id"] for row in self.target["analysis_evidence"]["evidence"]
        }
        self.assertTrue(
            {
                "WSEV-LI-JP-FIES-STATGO-20260904",
                "WSEV-LI-JP-FIES-REVISION-20260904",
            }.issubset(live_ids)
        )
        self.assertTrue(
            {
                "WSEV-JP-FIES-STATGO-20260904",
                "WSEV-JP-FIES-REVISION-20260904",
                "WSEV-JP-FIES-REBASING-NOTICE-20260707",
                "WSEV-JP-FIES-REUTERS-20260904",
            }.issubset(analysis_ids)
        )
        self.assertTrue(live_ids.isdisjoint(analysis_ids))

    def test_actual_expected_and_surprise_are_separate_and_vintage_caveated(self):
        review = self.analysis_by_id["WSAN-JP-FIES-202607-001"]
        actuals = {
            row["metric"]: row["value"]
            for row in review["what_happened"]["actuals"]
        }
        benchmarks = {
            row["metric"]: row["value"]
            for row in review["what_was_expected"]["benchmarks"]
        }
        self.assertEqual(actuals["real_consumption_yoy"], -3.6)
        self.assertEqual(actuals["real_consumption_mom_sa"], 0.5)
        self.assertEqual(benchmarks["real_consumption_yoy"], -1.6)
        self.assertEqual(benchmarks["real_consumption_mom_sa"], 2.6)
        self.assertEqual(review["what_surprised"]["status"], "DOWNSIDE")
        comparisons = {
            row["metric"]: row["difference_percentage_points"]
            for row in review["what_surprised"]["comparisons"]
        }
        self.assertEqual(comparisons["real_consumption_yoy"], -2.0)
        self.assertEqual(comparisons["real_consumption_mom_sa"], -2.1)
        self.assertIn("pre-announced", review["what_surprised"]["summary"])
        self.assertIn("methodological vintage", " ".join(
            row["summary"] for row in review["what_may_be_noise"]
        ))

    def test_no_market_move_or_policy_causality_is_manufactured(self):
        review = self.analysis_by_id["WSAN-JP-FIES-202607-001"]
        self.assertEqual(review["what_moved"], [])
        connection = review["what_appears_connected"]
        self.assertEqual(connection["interaction_type"], "POLICY_RESPONSE_CONTEXT")
        self.assertEqual(connection["causal_status"], "NOT_A_CAUSAL_CLAIM")
        self.assertEqual(connection["confidence"], "MEDIUM")
        self.assertEqual(review["second_order_effects"]["status"], "NOT_ESTABLISHED")
        self.assertEqual(apply_az.exact_series_count(self.target["reviews"]), 0)

    def test_first_production_input_is_explicit_and_same_canonical_anchor(self):
        review = self.analysis_by_id["WSAN-JP-FIES-202607-001"]
        self.assertEqual(
            review["live_inputs"],
            [{
                "observation_id": "WSLI-MAC-JPN-FIES-202607-001",
                "roles": ["FACTUAL_INPUT"],
                "analysis_sections": [
                    "what_happened",
                    "what_surprised",
                    "what_may_be_noise",
                    "alternative_explanations",
                ],
            }],
        )
        live = self.live_by_id[review["live_inputs"][0]["observation_id"]]
        self.assertEqual(review["canonical_occurrence_id"], live["canonical_links"][0]["occurrence_id"])
        self.assertTrue(
            self.target["analysis_schema"]["live_input_policy"][
                "factual_input_requires_matching_canonical_occurrence"
            ]
        )

    def test_factual_input_with_wrong_canonical_anchor_fails_closed(self):
        observations = deepcopy(self.target["live_observations"])
        row = next(
            item for item in observations["observations"]
            if item["observation_id"] == "WSLI-MAC-JPN-FIES-202607-001"
        )
        row["canonical_links"] = []
        report = validate_live_analysis_bridge(
            self.target["analysis_schema"], self.target["reviews"], observations
        )
        self.assertFalse(report.ok)
        self.assertTrue(any("must link to the Analysis canonical occurrence" in error for error in report.errors))

    def test_second_production_input_fails_population_cap(self):
        reviews = deepcopy(self.target["reviews"])
        row = next(
            item for item in reviews["reviews"]
            if item["analysis_id"] == "WSAN-JP-FIES-202607-001"
        )
        row["live_inputs"].append({
            "observation_id": "WSLI-RISK-NPL-FLOOD-20260826-001",
            "roles": ["CONTEXT_OR_ALTERNATIVE_INPUT"],
            "analysis_sections": ["alternative_explanations"],
        })
        report = validate_live_analysis_bridge(
            self.target["analysis_schema"], reviews, self.target["live_observations"]
        )
        self.assertFalse(report.ok)
        joined = " ".join(report.errors)
        self.assertIn("exceeds reviewed maximum", joined)
        self.assertIn("per-review maximum", joined)

    def test_public_projection_exposes_neither_live_rows_nor_live_inputs(self):
        live_public = public_live_intelligence_projection(
            self.target["live_schema"],
            self.target["live_evidence"],
            self.target["live_observations"],
            self.canonical,
        )
        self.assertEqual(live_public["metadata"]["public_observation_count"], 0)
        self.assertEqual(live_public["observations"], [])

        review = self.analysis_by_id["WSAN-JP-FIES-202607-001"]
        public_review = public_review_without_live_inputs(
            self.target["analysis_schema"], review
        )
        self.assertNotIn("live_inputs", public_review)
        self.assertEqual(public_review["what_happened"], review["what_happened"])

    def test_readiness_reaches_21_without_turning_frontier_completion_into_goal(self):
        readiness = analysis_population_readiness(
            self.target["analysis_schema"], self.target["reviews"], self.canonical
        )
        self.assertEqual(readiness["eligible_completed_occurrence_count"], 21)
        self.assertEqual(readiness["reviewed_occurrence_count"], 21)
        self.assertEqual(readiness["reviewed_event_type_diversity"], 18)
        audit_text = (ROOT / "data/analysis/POST_AY_PRESSURE_AUDIT_AZ_v0.1.md").read_text(encoding="utf-8")
        self.assertIn("not an ex-post surprise", audit_text)
        self.assertIn("Coverage diagnostics remain prompts rather than quotas", audit_text)

    def test_simulation_is_read_only_and_protected_paths_are_outside_target_writes(self):
        before = {path: stable_hash(ROOT / path) for path in self.plan["protected_paths"]}
        again = apply_az.simulate(self.plan, self.payload)
        apply_az.assert_target(self.plan, again)
        after = {path: stable_hash(ROOT / path) for path in self.plan["protected_paths"]}
        self.assertEqual(before, after)

        target_write_paths = {
            apply_az.LIVE_SCHEMA_PATH,
            apply_az.LIVE_OBSERVATIONS_PATH,
            apply_az.LIVE_EVIDENCE_PATH,
            apply_az.ANALYSIS_SCHEMA_PATH,
            apply_az.REVIEWS_PATH,
            apply_az.ANALYSIS_EVIDENCE_PATH,
            apply_az.STATUS_PATH,
            apply_az.ROADMAP_PATH,
        }
        self.assertTrue(
            all((ROOT / protected) not in target_write_paths for protected in self.plan["protected_paths"])
        )
        self.assertTrue(self.plan["manual_merge_only"])


if __name__ == "__main__":
    unittest.main()
