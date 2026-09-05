from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from apply_nonmarket_institutional_analysis_w import transform
from world_signals.analysis import analysis_population_readiness, public_analysis_projection


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class NonMarketInstitutionalAnalysisWTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load("data/analysis/NONMARKET_INSTITUTIONAL_ANALYSIS_W_PLAN_v0.1.json")
        cls.payload = load("data/analysis/NONMARKET_INSTITUTIONAL_ANALYSIS_W_PAYLOAD_v0.1.json")
        cls.canonical = load("data/canonical/registry.json")
        cls.sources = load("data/sources/registry.json")
        cls.ledger = load("data/changes/ledger.json")
        cls.overlay = load("data/coverage/biosecurity_overlay.json")
        cls.schema = load("data/analysis/schema.json")
        cls.reviews = load("data/analysis/event_reviews.json")
        cls.evidence = load("data/analysis/evidence_registry.json")
        cls.has_w = any(row.get("analysis_id") == cls.plan["new_analysis_id"] for row in cls.reviews.get("reviews", []))

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

    def test_payload_exercises_nonmarket_contract(self):
        review = self.payload["reviews"][0]
        self.assertEqual(review["analysis_id"], "WSAN-BWC-WG8-2026-001")
        self.assertEqual(review["canonical_occurrence_id"], "WSO-BWC-WG-2026-S08")
        self.assertEqual(review["what_surprised"]["status"], "NOT_ESTABLISHED")
        self.assertEqual(review["what_surprised"]["comparisons"], [])
        self.assertEqual(review["what_moved"], [])
        self.assertEqual(review["what_appears_connected"]["interaction_type"], "LEGAL_OR_OPERATIONAL_DEPENDENCY")
        self.assertEqual(review["what_appears_connected"]["causal_status"], "NOT_A_CAUSAL_CLAIM")
        self.assertEqual(review["second_order_effects"]["status"], "PLAUSIBLE_WATCH_ITEM")
        evidence_ids = {row["evidence_id"] for row in self.payload["evidence"]}
        self.assertEqual(evidence_ids, set(self.plan["new_evidence_ids"]))

    def test_transform_or_live_descendant_preserves_w_contract(self):
        if self.has_w:
            new_reviews, new_evidence = self.reviews, self.evidence
            readiness = analysis_population_readiness(self.schema, new_reviews, self.canonical)
            projection = public_analysis_projection(self.schema, new_evidence, new_reviews, self.canonical)
        else:
            new_reviews, new_evidence, readiness, projection = transform(
                self.plan, self.payload, self.canonical, self.sources, self.ledger,
                self.overlay, self.schema, self.reviews, self.evidence,
            )
        post = self.plan["postconditions"]
        self.assertGreaterEqual(len(new_reviews["reviews"]), post["analysis_review_count"])
        self.assertGreaterEqual(len(new_evidence["evidence"]), post["analysis_evidence_count"])
        self.assertGreaterEqual(readiness["eligible_completed_occurrence_count"], 12)
        self.assertGreaterEqual(readiness["reviewed_occurrence_count"], 10)
        self.assertGreaterEqual(readiness["reviewed_event_type_diversity"], 9)
        self.assertEqual(readiness["broad_population_state"], "READY_FOR_CONTROLLED_EXPANSION")
        by_id = {row["analysis_id"]: row for row in projection["reviews"]}
        projected = by_id["WSAN-BWC-WG8-2026-001"]
        self.assertEqual(projected["what_moved"], [])
        self.assertEqual(projected["what_surprised"]["status"], "NOT_ESTABLISHED")
        self.assertEqual(projected["canonical"]["event_type"], "TREATY_WORKING_GROUP_SESSION")

    def test_w_historical_boundary_is_frozen_without_forbidding_descendants(self):
        post = self.plan["postconditions"]
        self.assertEqual(post["analysis_reviews_version"], "0.6")
        self.assertEqual(post["analysis_review_count"], 10)
        self.assertEqual(post["analysis_evidence_version"], "0.6")
        self.assertEqual(post["analysis_evidence_count"], 32)
        self.assertEqual(set(post["remaining_eligible_unreviewed_occurrence_ids"]),
                         {"WSO-WOAH-GS-093", "WSO-ddb70f8ff05a58fb"})
        self.assertGreaterEqual(len(self.reviews["reviews"]), post["analysis_review_count"])
        self.assertGreaterEqual(len(self.evidence["evidence"]), post["analysis_evidence_count"])

    def test_current_public_renderer_supports_empty_market_response(self):
        source = (ROOT / "web/analysis.js").read_text(encoding="utf-8")
        self.assertIn("No observed market response established.", source)
        self.assertNotIn("WSAN-BWC-WG8-2026-001", source)

    def test_w_script_protects_upstream_and_schema(self):
        source = (ROOT / "scripts/apply_nonmarket_institutional_analysis_w.py").read_text(encoding="utf-8")
        self.assertIn('"Analysis schema": ANALYSIS_SCHEMA_PATH', source)
        self.assertIn("before == after", source)
        self.assertNotIn("write(ANALYSIS_SCHEMA_PATH", source)
        self.assertNotIn("write(CANONICAL_PATH", source)
        self.assertNotIn("write(SOURCES_PATH", source)
        self.assertNotIn("write(LEDGER_PATH", source)
        self.assertNotIn("write(OVERLAY_PATH", source)


if __name__ == "__main__":
    unittest.main()
