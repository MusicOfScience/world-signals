from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import apply_live_analysis_bridge_ay as apply_ay
from world_signals.analysis import validate_analysis
from world_signals.live_analysis_bridge import (
    production_live_input_count,
    public_review_without_live_inputs,
    validate_live_analysis_bridge,
)


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def version_tuple(raw: str) -> tuple[int, ...]:
    return tuple(int(part) for part in str(raw).split("."))


class LiveAnalysisBridgeAYTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load("data/analysis/LIVE_ANALYSIS_BRIDGE_AY_PLAN_v0.1.json")
        cls.schema = load("data/analysis/schema.json")
        cls.reviews = load("data/analysis/event_reviews.json")
        cls.evidence = load("data/analysis/evidence_registry.json")
        cls.live_observations = load("data/live_intelligence/observations.json")
        cls.live_evidence = load("data/live_intelligence/evidence_registry.json")
        cls.canonical = load("data/canonical/registry.json")

        # Freeze AY's historical target at v0.5 even when a later legitimate
        # descendant has opened a bounded production population.
        if version_tuple(cls.schema.get("version")) > (0, 5):
            historical_pre = deepcopy(cls.schema)
            historical_pre["version"] = "0.4"
            historical_pre.pop("live_input_policy", None)
            cls.target_schema = apply_ay.target_schema(historical_pre)
        else:
            cls.target_schema = apply_ay.target_schema(cls.schema)

    def simulated_open_schema(self):
        # AY hypothetical fixtures exercise the prospective grammar. They must
        # opt into the reviewed controlled mode rather than mutating the frozen
        # FOUNDATION_ONLY_NO_PRODUCTION_LINKS mode into an impossible hybrid.
        schema = deepcopy(self.target_schema)
        policy = schema["live_input_policy"]
        policy["mode"] = "CONTROLLED_SINGLE_PRODUCTION_LINK"
        policy["production_live_inputs_allowed"] = True
        policy["maximum_production_live_inputs"] = 4
        policy["maximum_live_inputs_per_review"] = 2
        policy["factual_input_requires_matching_canonical_occurrence"] = False
        return schema

    def review_with_inputs(self, inputs, analysis_id="WSAN-AY-HYPOTHETICAL-001"):
        review = deepcopy(self.reviews["reviews"][0])
        review["analysis_id"] = analysis_id
        review["analysis_as_of_utc"] = "2026-09-06T08:30:00Z"
        review["live_inputs"] = inputs
        return review

    def test_exact_checkpoint_and_zero_population_are_preserved(self):
        self.assertEqual(self.plan["exact_base_main_sha"], "0a7608ab56116d0f65ffd1492a3da87bcbf35f47")
        target = self.plan["target"]
        self.assertEqual(target["analysis_review_count"], 20)
        self.assertEqual(target["analysis_evidence_count"], 91)
        self.assertEqual(target["live_observation_count"], 3)
        self.assertEqual(target["live_evidence_count"], 4)
        self.assertEqual(target["production_live_input_count"], 0)
        self.assertEqual(target["analysis_schema_version"], "0.5")
        self.assertFalse(target["production_live_inputs_allowed"])
        self.assertFalse(target["public_live_input_projection_allowed"])

        # Live descendants may grow after a separately reviewed tranche; the
        # exact AY checkpoint above is the frozen history, not a permanent cap.
        self.assertGreaterEqual(len(self.reviews["reviews"]), 20)
        self.assertGreaterEqual(len(self.evidence["evidence"]), 91)
        self.assertGreaterEqual(len(self.live_observations["observations"]), 3)
        self.assertGreaterEqual(len(self.live_evidence["evidence"]), 4)
        self.assertGreaterEqual(production_live_input_count(self.reviews), 0)
        self.assertEqual(self.target_schema["version"], "0.5")
        self.assertFalse(self.target_schema["live_input_policy"]["production_live_inputs_allowed"])
        self.assertFalse(self.target_schema["live_input_policy"]["public_live_input_projection_allowed"])

    def test_target_schema_validates_core_analysis_and_closed_bridge(self):
        historical_reviews = deepcopy(self.reviews)
        for review in historical_reviews.get("reviews", []):
            review.pop("live_inputs", None)
        core = validate_analysis(self.target_schema, self.evidence, historical_reviews, self.canonical)
        self.assertTrue(core.ok, core.errors)
        bridge = validate_live_analysis_bridge(
            self.target_schema, historical_reviews, self.live_observations
        )
        self.assertTrue(bridge.ok, bridge.errors)

    def test_live_descendant_state_matches_ax_contract(self):
        rows = {row["observation_id"]: row for row in self.live_observations["observations"]}
        ax_ids = {
            "WSLI-RISK-NPL-FLOOD-20260826-001",
            "WSLI-HEALTH-COD-BVD-20260826-001",
            "WSLI-HEALTH-COD-BVD-20260830-001",
        }
        self.assertTrue(ax_ids.issubset(set(rows)))
        older = rows["WSLI-HEALTH-COD-BVD-20260826-001"]
        newer = rows["WSLI-HEALTH-COD-BVD-20260830-001"]
        self.assertEqual(older["story_id"], "WSSTORY-HEALTH-COD-BVD-2026")
        self.assertEqual(newer["story_id"], older["story_id"])
        self.assertEqual(newer["state_update_of_observation_id"], older["observation_id"])
        self.assertIsNone(older["revision_of_observation_id"])
        self.assertIsNone(newer["revision_of_observation_id"])

    def test_closed_production_gate_rejects_any_live_input(self):
        reviews = {"reviews": [self.review_with_inputs([{
            "observation_id": "WSLI-HEALTH-COD-BVD-20260830-001",
            "roles": ["FACTUAL_INPUT"],
            "analysis_sections": ["what_happened"],
        }])]}
        report = validate_live_analysis_bridge(self.target_schema, reviews, self.live_observations)
        self.assertFalse(report.ok)
        self.assertTrue(any("production gate is closed" in error for error in report.errors))

    def test_hypothetical_explicit_observation_reference_resolves(self):
        schema = self.simulated_open_schema()
        review = self.review_with_inputs([{
            "observation_id": "WSLI-HEALTH-COD-BVD-20260830-001",
            "roles": ["FACTUAL_INPUT"],
            "analysis_sections": ["what_happened", "second_order_effects"],
        }])
        report = validate_live_analysis_bridge(schema, {"reviews": [review]}, self.live_observations)
        self.assertTrue(report.ok, report.errors)

    def test_unknown_live_observation_fails_closed(self):
        schema = self.simulated_open_schema()
        review = self.review_with_inputs([{
            "observation_id": "WSLI-NOT-REAL",
            "roles": ["FACTUAL_INPUT"],
            "analysis_sections": ["what_happened"],
        }])
        report = validate_live_analysis_bridge(schema, {"reviews": [review]}, self.live_observations)
        self.assertFalse(report.ok)
        self.assertTrue(any("unknown Live observation_id" in error for error in report.errors))

    def test_analysis_cannot_select_observation_before_world_signals_observed_it(self):
        schema = self.simulated_open_schema()
        review = self.review_with_inputs([{
            "observation_id": "WSLI-HEALTH-COD-BVD-20260830-001",
            "roles": ["FACTUAL_INPUT"],
            "analysis_sections": ["what_happened"],
        }])
        review["analysis_as_of_utc"] = "2026-09-06T07:40:59Z"
        report = validate_live_analysis_bridge(schema, {"reviews": [review]}, self.live_observations)
        self.assertFalse(report.ok)
        self.assertTrue(any("predates Live observed_at_utc" in error for error in report.errors))

    def test_story_latest_and_shadow_copy_fields_are_not_selector_grammar(self):
        schema = self.simulated_open_schema()
        bad_fields = {
            "story_id": "WSSTORY-HEALTH-COD-BVD-2026",
            "latest": True,
            "headline": "copied downstream headline",
            "evidence_refs": ["WSEV-LI-COD-BVD-WHO-AFRO-SITREP16-20260830"],
        }
        review = self.review_with_inputs([{
            "observation_id": "WSLI-HEALTH-COD-BVD-20260830-001",
            "roles": ["FACTUAL_INPUT"],
            "analysis_sections": ["what_happened"],
            **bad_fields,
        }])
        report = validate_live_analysis_bridge(schema, {"reviews": [review]}, self.live_observations)
        joined = "\n".join(report.errors)
        self.assertIn("unexpected fields", joined)
        for field in bad_fields:
            self.assertIn(field, joined)

    def test_evolving_story_requires_explicit_snapshot_ids(self):
        schema = self.simulated_open_schema()
        review = self.review_with_inputs([
            {
                "observation_id": "WSLI-HEALTH-COD-BVD-20260826-001",
                "roles": ["FACTUAL_INPUT"],
                "analysis_sections": ["what_happened"],
            },
            {
                "observation_id": "WSLI-HEALTH-COD-BVD-20260830-001",
                "roles": ["FACTUAL_INPUT"],
                "analysis_sections": ["what_happened", "second_order_effects"],
            },
        ])
        report = validate_live_analysis_bridge(schema, {"reviews": [review]}, self.live_observations)
        self.assertTrue(report.ok, report.errors)
        self.assertTrue(schema["live_input_policy"]["multiple_story_snapshots_require_explicit_observation_ids"])
        self.assertFalse(schema["live_input_policy"]["automatic_story_expansion_allowed"])

    def test_same_live_observation_may_support_multiple_analyses(self):
        schema = self.simulated_open_schema()
        input_row = {
            "observation_id": "WSLI-RISK-NPL-FLOOD-20260826-001",
            "roles": ["CONTEXT_OR_ALTERNATIVE_INPUT"],
            "analysis_sections": ["alternative_explanations"],
        }
        reviews = {
            "reviews": [
                self.review_with_inputs([deepcopy(input_row)], "WSAN-AY-HYPOTHETICAL-A"),
                self.review_with_inputs([deepcopy(input_row)], "WSAN-AY-HYPOTHETICAL-B"),
            ]
        }
        report = validate_live_analysis_bridge(schema, reviews, self.live_observations)
        self.assertTrue(report.ok, report.errors)
        self.assertTrue(schema["live_input_policy"]["one_live_observation_may_support_multiple_analyses"])

    def test_duplicate_reference_within_one_analysis_is_rejected(self):
        schema = self.simulated_open_schema()
        input_row = {
            "observation_id": "WSLI-RISK-NPL-FLOOD-20260826-001",
            "roles": ["FACTUAL_INPUT"],
            "analysis_sections": ["what_happened"],
        }
        review = self.review_with_inputs([deepcopy(input_row), deepcopy(input_row)])
        report = validate_live_analysis_bridge(schema, {"reviews": [review]}, self.live_observations)
        self.assertFalse(report.ok)
        self.assertTrue(any("duplicate live observation reference" in error for error in report.errors))

    def test_public_boundary_strips_live_inputs_without_migrating_live_evidence(self):
        review = self.review_with_inputs([{
            "observation_id": "WSLI-HEALTH-COD-BVD-20260830-001",
            "roles": ["FACTUAL_INPUT"],
            "analysis_sections": ["what_happened"],
        }])
        before_refs = set(review.get("what_happened", {}).get("evidence_refs", []))
        public = public_review_without_live_inputs(self.target_schema, review)
        self.assertNotIn("live_inputs", public)
        self.assertEqual(set(public.get("what_happened", {}).get("evidence_refs", [])), before_refs)
        live_evidence_ids = {row["evidence_id"] for row in self.live_evidence["evidence"]}
        self.assertTrue(live_evidence_ids.isdisjoint(before_refs))
        self.assertFalse(self.target_schema["live_input_policy"]["transitive_live_evidence_migration_allowed"])

    def test_apply_helper_exact_transform_remains_frozen_to_ay_checkpoint(self):
        if version_tuple(self.schema.get("version")) > (0, 5):
            self.assertEqual(self.plan["target"]["analysis_schema_version"], "0.5")
            self.assertEqual(self.plan["target"]["analysis_review_count"], 20)
            self.assertEqual(self.plan["target"]["production_live_input_count"], 0)
            self.skipTest("AY exact apply-helper transform belongs to the exact post-AX pre-state")
        apply_ay.assert_preconditions(self.plan)
        texts = apply_ay.target_texts()
        self.assertEqual(set(texts), {
            apply_ay.VALIDATE_SCRIPT_PATH,
            apply_ay.BUILD_SCRIPT_PATH,
            apply_ay.CI_PATH,
            apply_ay.STATUS_PATH,
            apply_ay.ROADMAP_PATH,
        })
        for protected in self.plan["protected_paths"]:
            self.assertNotIn(ROOT / protected, texts)


if __name__ == "__main__":
    unittest.main()
