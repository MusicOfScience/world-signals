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

from world_signals.analysis import analysis_population_readiness, public_analysis_projection, validate_analysis
import apply_source_native_fiscal_analysis_v as txn


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class SourceNativeFiscalAnalysisVTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load("data/analysis/SOURCE_NATIVE_FISCAL_ANALYSIS_V_PLAN_v0.1.json")
        cls.payload = load("data/analysis/SOURCE_NATIVE_FISCAL_ANALYSIS_V_PAYLOAD_v0.1.json")
        cls.canonical = load("data/canonical/registry.json")
        cls.sources = load("data/sources/registry.json")
        cls.ledger = load("data/changes/ledger.json")
        cls.overlay = load("data/coverage/biosecurity_overlay.json")
        cls.schema = load("data/analysis/schema.json")
        cls.reviews = load("data/analysis/event_reviews.json")
        cls.evidence = load("data/analysis/evidence_registry.json")
        cls.is_post = (
            cls.schema.get("version") == "0.3"
            and cls.reviews.get("version") == "0.5"
            and len(cls.reviews.get("reviews", [])) == 9
            and cls.evidence.get("version") == "0.5"
            and len(cls.evidence.get("evidence", [])) == 28
        )

    def post_objects(self):
        if self.is_post:
            return self.reviews, self.evidence
        reviews, evidence, _readiness, _projection = txn.transform(
            self.plan,
            self.payload,
            self.canonical,
            self.sources,
            self.ledger,
            self.overlay,
            self.schema,
            self.reviews,
            self.evidence,
        )
        return reviews, evidence

    def test_v_contract_schema_is_explicit_and_fail_closed(self):
        self.assertEqual(self.schema["version"], "0.3")
        policy = self.schema["temporal_context_policy"]
        for key, value in self.plan["analysis_schema_evolution"]["new_policy"].items():
            self.assertIs(policy[key], value)
        report = validate_analysis(self.schema, self.evidence, self.reviews, self.canonical)
        self.assertTrue(report.ok, report.errors)
        broken = deepcopy(self.schema)
        broken["temporal_context_policy"]["public_projection_may_not_infer_missing_canonical_time"] = False
        self.assertTrue(any("temporal-context policy" in e for e in validate_analysis(broken, self.evidence, self.reviews, self.canonical).errors))

    def test_check_only_transform_is_exact_and_does_not_mutate_inputs(self):
        if self.is_post:
            self.skipTest("check-only transform is exercised from exact V pre-state")
        before = {
            "canonical": digest(self.canonical),
            "sources": digest(self.sources),
            "ledger": digest(self.ledger),
            "overlay": digest(self.overlay),
            "reviews": digest(self.reviews),
            "evidence": digest(self.evidence),
        }
        reviews, evidence, readiness, projection = txn.transform(
            self.plan,
            self.payload,
            self.canonical,
            self.sources,
            self.ledger,
            self.overlay,
            self.schema,
            self.reviews,
            self.evidence,
        )
        self.assertEqual((reviews["version"], len(reviews["reviews"])), ("0.5", 9))
        self.assertEqual((evidence["version"], len(evidence["evidence"])), ("0.5", 28))
        self.assertEqual(readiness["reviewed_occurrence_count"], 9)
        self.assertEqual(readiness["reviewed_event_type_diversity"], 8)
        self.assertEqual(len(projection["reviews"]), 9)
        after = {
            "canonical": digest(self.canonical),
            "sources": digest(self.sources),
            "ledger": digest(self.ledger),
            "overlay": digest(self.overlay),
            "reviews": digest(self.reviews),
            "evidence": digest(self.evidence),
        }
        self.assertEqual(before, after)

    def test_public_projection_preserves_native_date_without_conversion(self):
        reviews, evidence = self.post_objects()
        projection = public_analysis_projection(self.schema, evidence, reviews, self.canonical)
        row = next(x for x in projection["reviews"] if x["analysis_id"] == "WSAN-NP-BUDGET-2083-001")
        c = row["canonical"]
        self.assertEqual(c["timing_type"], "SOURCE_NATIVE_CALENDAR_DATE")
        self.assertEqual(c["source_native_date_label"], "15 Jestha 2083")
        self.assertEqual(c["native_calendar_system"], "BIKRAM_SAMBAT_NEPAL")
        self.assertEqual(c["gregorian_resolution_status"], "UNRESOLVED_AUTHORITATIVE_CONVERSION")
        self.assertIsNone(c["start_local"])
        self.assertIsNone(c["start_utc"])
        for field in self.plan["analysis_schema_evolution"]["required_public_canonical_temporal_fields"]:
            self.assertIn(field, c)

    def test_expectation_history_prevents_false_headline_surprise(self):
        reviews, _ = self.post_objects()
        review = next(x for x in reviews["reviews"] if x["analysis_id"] == "WSAN-NP-BUDGET-2083-001")
        self.assertEqual(review["what_surprised"]["status"], "NO_CLEAR_SURPRISE")
        benchmarks = {x["metric"]: x for x in review["what_was_expected"]["benchmarks"]}
        self.assertEqual(benchmarks["initial_planning_ceiling"]["value"], 1890.0)
        self.assertEqual(benchmarks["reported_revised_ceiling"]["value"], 2150.0)
        self.assertEqual(benchmarks["latest_reported_budget_range"]["value"], "approximately NPR 2.1-2.2 trillion")
        comparison = next(x for x in review["what_surprised"]["comparisons"] if x["comparison_kind"] == "QUANTITATIVE")
        self.assertEqual((comparison["actual"], comparison["expected"]), (2124.34, 2150.0))
        self.assertIn("latest", review["what_surprised"]["summary"].lower())

    def test_first_market_move_remains_noncausal_and_unreconstructed(self):
        reviews, _ = self.post_objects()
        review = next(x for x in reviews["reviews"] if x["analysis_id"] == "WSAN-NP-BUDGET-2083-001")
        move = review["what_moved"][0]
        self.assertEqual(move["movement_type"], "EQUITY_INDEX")
        self.assertEqual(move["movement_representation"], "CHANGE_AND_ENDPOINT")
        self.assertEqual((move["after_value"], move["change"]), (2755.37, -26.72))
        self.assertIsNone(move["before_value"])
        self.assertFalse(move["independently_reconstructed"])
        connection = review["what_appears_connected"]
        self.assertEqual(connection["interaction_type"], "TEMPORAL_COINCIDENCE_ONLY")
        self.assertEqual(connection["causal_status"], "NOT_A_CAUSAL_CLAIM")
        self.assertGreaterEqual(len(review["alternative_explanations"]), 2)

    def test_observed_second_order_signal_preserves_reconciliation_warning(self):
        reviews, _ = self.post_objects()
        review = next(x for x in reviews["reviews"] if x["analysis_id"] == "WSAN-NP-BUDGET-2083-001")
        second = review["second_order_effects"]
        self.assertEqual(second["status"], "OBSERVED")
        values = {x["metric"]: x["value"] for x in second["observations"]}
        self.assertEqual(values["total_expenditure_share_of_annual_budget"], 5.79)
        self.assertEqual(values["capital_expenditure_share_of_annual_budget"], 1.19)
        self.assertIn("reconciliation", second["summary"].lower())
        self.assertNotIn("failure", second["summary"].lower())
        self.assertNotIn("success", second["summary"].lower())

    def test_analysis_evidence_never_becomes_canonical_provenance_or_time(self):
        reviews, evidence = self.post_objects()
        expected = set(self.plan["new_evidence_ids"])
        by_id = {x["evidence_id"]: x for x in evidence["evidence"]}
        self.assertTrue(expected <= set(by_id))
        canonical_source_ids = {x.get("source_id") for x in self.canonical["records"]}
        self.assertTrue(expected.isdisjoint(canonical_source_ids))
        for evidence_id in expected:
            self.assertEqual(by_id[evidence_id]["canonical_provenance_effect"], "NONE")
        anchor = next(x for x in self.canonical["records"] if x["occurrence_id"] == "WSO-FIS-NP-BUDGET-2083")
        self.assertEqual(anchor["source_native_date_label"], "15 Jestha 2083")
        self.assertIsNone(anchor["start_local"])
        self.assertIsNone(anchor["start_utc"])
        review = next(x for x in reviews["reviews"] if x["analysis_id"] == "WSAN-NP-BUDGET-2083-001")
        self.assertIsNone(review["canonical_release_utc"])

    def test_v_expands_reviewed_type_diversity_but_not_backlog_completion(self):
        reviews, _ = self.post_objects()
        readiness = analysis_population_readiness(self.schema, reviews, self.canonical)
        self.assertEqual(readiness["eligible_completed_occurrence_count"], 12)
        self.assertEqual(readiness["reviewed_occurrence_count"], 9)
        self.assertEqual(readiness["reviewed_event_type_diversity"], 8)
        self.assertEqual(readiness["reviewed_by_event_type"]["FISCAL_POLICY_PROCESS"], 1)
        remaining = sorted(
            x["occurrence_id"] for x in self.canonical["records"]
            if x.get("lifecycle_status") == "COMPLETED"
            and x["occurrence_id"] not in set(readiness["reviewed_occurrence_ids"])
        )
        self.assertEqual(remaining, sorted(self.plan["postconditions"]["remaining_eligible_unreviewed_occurrence_ids"]))
        self.assertEqual(set(self.plan["selection"]["held_occurrence_ids"]), set(remaining))
        self.assertFalse(self.plan["guardrails"]["backlog_completion_is_population_objective"])

    def test_browser_renders_source_native_truth_without_converter(self):
        source = (ROOT / "web/analysis.js").read_text(encoding="utf-8")
        self.assertIn("source_native_date_label", source)
        self.assertIn("gregorian_resolution_status", source)
        self.assertIn("Gregorian mapping unresolved by authoritative source", source)
        self.assertIn("canonical timing unresolved; no date inferred", source)
        self.assertNotIn("BIKRAM_SAMBAT_NEPAL", source)
        self.assertNotIn("Jestha 2083", source)
        self.assertNotIn("2026-05-29", source)
        self.assertNotIn("data/canonical", source)

    def test_all_v_write_gates_and_upstream_versions_remain_closed(self):
        for key, value in self.plan["guardrails"].items():
            self.assertFalse(value, key)
        self.assertEqual((self.canonical["version"], len(self.canonical["records"])), ("0.30", 681))
        self.assertEqual((self.sources["version"], len(self.sources["sources"])), ("1.72", 237))
        self.assertEqual((self.ledger["version"], len(self.ledger["changes"])), ("0.17", 51))
        self.assertEqual((self.overlay["version"], self.overlay["canonical_checkpoint"]),
                         ("0.5", {"registry_version": "0.30", "record_count": 681}))


if __name__ == "__main__":
    unittest.main()
