from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from apply_formal_standards_analysis_x import transform
from world_signals.analysis import analysis_population_readiness, public_analysis_projection, validate_analysis


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class FormalStandardsAnalysisXTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load("data/analysis/FORMAL_STANDARDS_ANALYSIS_X_PLAN_v0.1.json")
        cls.payload = load("data/analysis/FORMAL_STANDARDS_ANALYSIS_X_PAYLOAD_v0.1.json")
        cls.canonical = load("data/canonical/registry.json")
        cls.sources = load("data/sources/registry.json")
        cls.ledger = load("data/changes/ledger.json")
        cls.overlay = load("data/coverage/biosecurity_overlay.json")
        cls.schema = load("data/analysis/schema.json")
        cls.reviews = load("data/analysis/event_reviews.json")
        cls.evidence = load("data/analysis/evidence_registry.json")
        cls.has_x = any(row.get("analysis_id") == cls.plan["new_analysis_id"] for row in cls.reviews.get("reviews", []))

    def review(self):
        source = self.reviews if self.has_x else self.payload
        return next(row for row in source["reviews"] if row["analysis_id"] == "WSAN-WOAH-GS93-2026-001")

    def test_frozen_prestate_contract_and_no_schema_change(self):
        pre = self.plan["preconditions"]
        self.assertEqual((pre["canonical_registry_version"], pre["canonical_record_count"]), ("0.30", 681))
        self.assertGreaterEqual(float(self.canonical["version"]), float(pre["canonical_registry_version"]))
        self.assertGreaterEqual(len(self.canonical["records"]), pre["canonical_record_count"])
        self.assertEqual(self.schema["version"], "0.3")
        self.assertEqual(self.plan["schema_decision"]["version_unchanged"], "0.3")
        for key in (
            "canonical_mutation", "source_registry_mutation", "change_ledger_mutation",
            "biosecurity_overlay_mutation", "analysis_schema_mutation", "monitor_configuration_mutation",
            "calendar_write", "automatic_canonical_commit",
        ):
            self.assertFalse(self.plan["guardrails"][key])

    def test_payload_preserves_formal_adoption_without_impact_inference(self):
        review = self.payload["reviews"][0]
        actuals = {row["metric"]: row["value"] for row in review["what_happened"]["actuals"]}
        self.assertEqual(actuals["resolutions_adopted"], 35)
        self.assertEqual(actuals["international_standards_adopted_or_revised"], 51)
        self.assertEqual(review["what_surprised"]["status"], "NOT_ESTABLISHED")
        self.assertEqual(review["what_surprised"]["comparisons"], [])
        self.assertEqual(review["what_moved"], [])
        self.assertEqual(review["second_order_effects"]["status"], "PLAUSIBLE_WATCH_ITEM")
        self.assertIn("implementation", review["second_order_effects"]["summary"].lower())

    def test_regulatory_overlap_is_differentiated_not_homogenised(self):
        review = self.review()
        connection = review["what_appears_connected"]
        self.assertEqual(connection["interaction_type"], "REGULATORY_OVERLAP")
        self.assertEqual(connection["causal_status"], "NOT_A_CAUSAL_CLAIM")
        self.assertEqual(connection["confidence"], "HIGH")
        refs = set(connection["evidence_refs"])
        self.assertIn("WSEV-WTO-WOAH-SPS-RELATIONSHIP", refs)
        self.assertIn("WSEV-WOAH-ANIMAL-WELFARE-SPS-CARVEOUT", refs)
        text = connection["summary"].lower()
        self.assertIn("animal-welfare", text)
        self.assertIn("not recognised", text)
        self.assertIn("automatic domestic legal changes", text)
        self.assertIn("rather than treating all 51 standards", text)

    def test_one_health_relationship_does_not_change_primary_ontology(self):
        target = next(row for row in self.canonical["records"] if row.get("occurrence_id") == "WSO-WOAH-GS-093")
        self.assertEqual(target["category"], "AGRICULTURE_FOOD")
        self.assertEqual(target["event_type"], "GOVERNANCE_ASSEMBLY_SESSION")
        self.assertFalse(self.plan["guardrails"]["one_health_relationship_changes_primary_category"])

    def test_transform_or_live_descendant_preserves_x_contract(self):
        if self.has_x:
            reviews, evidence = self.reviews, self.evidence
            readiness = analysis_population_readiness(self.schema, reviews, self.canonical)
            projection = public_analysis_projection(self.schema, evidence, reviews, self.canonical)
        else:
            reviews, evidence, readiness, projection = transform(
                self.plan, self.payload, self.canonical, self.sources, self.ledger,
                self.overlay, self.schema, self.reviews, self.evidence,
            )
        post = self.plan["postconditions"]
        self.assertGreaterEqual(len(reviews["reviews"]), post["analysis_review_count"])
        self.assertGreaterEqual(len(evidence["evidence"]), post["analysis_evidence_count"])
        self.assertGreaterEqual(readiness["reviewed_occurrence_count"], post["reviewed_occurrence_count"])
        self.assertGreaterEqual(readiness["reviewed_event_type_diversity"], post["reviewed_event_type_diversity"])
        self.assertGreaterEqual(readiness["eligible_completed_occurrence_count"], 12)
        self.assertEqual(readiness["broad_population_state"], "READY_FOR_CONTROLLED_EXPANSION")
        by_id = {row["analysis_id"]: row for row in projection["reviews"]}
        projected = by_id["WSAN-WOAH-GS93-2026-001"]
        self.assertEqual(projected["what_moved"], [])
        self.assertEqual(projected["what_surprised"]["status"], "NOT_ESTABLISHED")
        self.assertEqual(projected["what_appears_connected"]["interaction_type"], "REGULATORY_OVERLAP")
        self.assertEqual(projected["canonical"]["event_type"], "GOVERNANCE_ASSEMBLY_SESSION")
        self.assertEqual(projected["canonical"]["category"], "AGRICULTURE_FOOD")
        self.assertTrue(validate_analysis(self.schema, evidence, reviews, self.canonical).ok)

    def test_x_boundary_leaves_only_boc_unreviewed_without_making_fifo_a_goal(self):
        post = self.plan["postconditions"]
        self.assertEqual(post["remaining_eligible_unreviewed_occurrence_ids"], ["WSO-ddb70f8ff05a58fb"])
        self.assertEqual(self.plan["selection"]["held_occurrence_ids"], ["WSO-ddb70f8ff05a58fb"])
        self.assertFalse(self.plan["guardrails"]["backlog_completion_is_population_objective"])

    def test_current_renderer_supports_empty_market_response(self):
        source = (ROOT / "web/analysis.js").read_text(encoding="utf-8")
        self.assertIn("No observed market response established.", source)
        self.assertNotIn("WSAN-WOAH-GS93-2026-001", source)

    def test_x_script_protects_upstream_and_schema(self):
        source = (ROOT / "scripts/apply_formal_standards_analysis_x.py").read_text(encoding="utf-8")
        self.assertIn('"Analysis schema": ANALYSIS_SCHEMA_PATH', source)
        self.assertIn("before == after", source)
        for forbidden in (
            "write(ANALYSIS_SCHEMA_PATH", "write(CANONICAL_PATH", "write(SOURCES_PATH",
            "write(LEDGER_PATH", "write(OVERLAY_PATH",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
