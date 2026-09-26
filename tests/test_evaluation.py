import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.evaluation import (
    aggregate_evaluation,
    evaluate_forecasts,
    public_evaluation_projection,
    validate_evaluation,
)
import tests.test_outcomes as outcomes_fixture_module


class EvaluationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        outcomes_fixture_module.OutcomeContractTests.setUpClass()
        cls.schema = json.loads((ROOT / "data/evaluation/schema.json").read_text())
        cls.config = json.loads((ROOT / "data/evaluation/config.json").read_text())
        cls.dataset = json.loads((ROOT / "data/evaluation/evaluation.json").read_text())

    @classmethod
    def prepared_forecasts(cls, *, categorical=False, numeric=False):
        forecasts = outcomes_fixture_module.OutcomeContractTests.forecasts(categorical=categorical, numeric=numeric)
        for row in forecasts["forecasts"]:
            row["revision_created_at_utc"] = row["issued_at_utc"]
            row["information_cutoff_at_utc"] = "2025-12-31T00:00:00Z"
        return forecasts

    @classmethod
    def prepared_outcome(cls, forecasts=None, *, status="RESOLVED", observed=None):
        forecasts = forecasts or cls.prepared_forecasts()
        if status == "RESOLVED" and observed is None:
            observed = {"event_occurred": True}
        return {"version": "0.1", "outcomes": [outcomes_fixture_module.OutcomeContractTests.outcome(forecasts, status, observed)]}

    def evaluate(self, forecasts=None, outcomes=None, *, at="2026-02-02T00:00:00Z"):
        return evaluate_forecasts(
            self.config,
            forecasts or self.prepared_forecasts(),
            outcomes or self.prepared_outcome(),
            as_of_utc=at,
        )

    def test_zero_production_evaluation_validates_and_public_projection_is_closed(self):
        report = validate_evaluation(
            self.schema,
            self.config,
            self.dataset,
            {"version": "0.1", "forecasts": []},
            {"version": "0.1", "outcomes": []},
        )
        self.assertTrue(report.ok, report.errors)
        projection = public_evaluation_projection(
            self.schema, self.config, self.dataset,
            {"version": "0.1", "forecasts": []},
            {"version": "0.1", "outcomes": []},
        )
        self.assertFalse(projection["metadata"]["public_evaluation_projection_allowed"])
        self.assertEqual(projection["evaluations"], [])

    def test_production_population_gate_rejects_evaluation_rows(self):
        dataset = copy.deepcopy(self.dataset)
        dataset["evaluations"] = [{"evaluation_id": "SYNTHETIC-LEAK"}]
        report = validate_evaluation(
            self.schema, self.config, dataset,
            {"version": "0.1", "forecasts": []},
            {"version": "0.1", "outcomes": []},
        )
        self.assertFalse(report.ok)
        self.assertTrue(any("closed Evaluation production gate" in error for error in report.errors))

    def test_binary_brier_and_log_loss_are_correct(self):
        result = self.evaluate()
        scored = [row for row in result["records"] if row["eligibility_state"] == "SCORED"]
        self.assertEqual(len(scored), 2)
        self.assertAlmostEqual(scored[0]["metrics"]["BRIER"]["metric_value"], 0.36)
        self.assertAlmostEqual(scored[0]["metrics"]["LOG_LOSS"]["metric_value"], -__import__("math").log(0.4))
        self.assertEqual(result["summary"]["counts"]["scored"], 2)

    def test_binary_extreme_wrong_probability_reports_infinite_log_loss_without_clamping(self):
        forecasts = self.prepared_forecasts()
        forecasts["forecasts"][0]["forecast_value"]["probability"] = 0.0
        result = self.evaluate(forecasts)
        record = result["records"][0]
        self.assertEqual(record["metrics"]["LOG_LOSS"], {"metric_value": None, "metric_status": "INFINITE"})
        self.assertEqual(record["metrics"]["BRIER"]["metric_value"], 1.0)

    def test_categorical_brier_and_log_loss_use_full_distribution(self):
        forecasts = self.prepared_forecasts(categorical=True)
        outcomes = self.prepared_outcome(forecasts, observed={"outcome_id": "SYN-A"})
        result = self.evaluate(forecasts, outcomes)
        metrics = result["records"][0]["metrics"]
        self.assertAlmostEqual(metrics["MULTICLASS_BRIER"]["metric_value"], 0.32)
        self.assertAlmostEqual(metrics["MULTICLASS_LOG_LOSS"]["metric_value"], -__import__("math").log(0.6))

    def test_numeric_signed_absolute_and_squared_error_are_correct(self):
        forecasts = self.prepared_forecasts(numeric=True)
        outcomes = self.prepared_outcome(forecasts, observed={"value": 12.0, "unit": "synthetic units"})
        result = self.evaluate(forecasts, outcomes)
        metrics = result["records"][0]["metrics"]
        self.assertEqual(metrics["SIGNED_ERROR"]["metric_value"], -2.0)
        self.assertEqual(metrics["ABSOLUTE_ERROR"]["metric_value"], 2.0)
        self.assertEqual(metrics["SQUARED_ERROR"]["metric_value"], 4.0)

    def test_incompatible_metric_configuration_is_rejected(self):
        config = copy.deepcopy(self.config)
        config["metric_compatibility"]["BINARY_EVENT"] = ["ABSOLUTE_ERROR"]
        with self.assertRaises(ValueError):
            evaluate_forecasts(config, self.prepared_forecasts(), self.prepared_outcome(), as_of_utc="2026-02-02T00:00:00Z")

    def test_one_outcome_scores_all_eligible_issuances_but_not_as_independent_targets(self):
        result = self.evaluate()
        self.assertEqual({row["outcome_id"] for row in result["records"]}, {"FORECAST-SERIES-SYN-1"})
        self.assertEqual(result["summary"]["counts"]["issued"], 2)
        self.assertEqual(result["summary"]["counts"]["distinct_series"], 1)
        self.assertTrue(result["summary"]["series_updates_are_not_independent_targets"])

    def test_administrative_outcome_correction_does_not_duplicate_evaluation_target(self):
        forecasts = self.prepared_forecasts()
        original = outcomes_fixture_module.OutcomeContractTests.outcome(forecasts, "RESOLVED", {"event_occurred": True})
        correction = copy.deepcopy(original)
        correction.update({
            "revision_id": "OUTCOME-SERIES-SYN-1-R2",
            "revision_number": 2,
            "previous_revision_id": original["revision_id"],
            "revision_kind": "ADMINISTRATIVE_CORRECTION",
            "world_signals_reviewed_at_utc": "2026-02-02T04:00:00Z",
            "revision_reason": "Corrected only a source locator label.",
        })
        result = self.evaluate(forecasts, {"version": "0.1", "outcomes": [original, correction]}, at="2026-02-02T05:00:00Z")
        self.assertEqual(len(result["records"]), 2)
        self.assertEqual({row["outcome_id"] for row in result["records"]}, {"FORECAST-SERIES-SYN-1"})
        self.assertEqual({row["outcome_revision_id"] for row in result["records"]}, {"OUTCOME-SERIES-SYN-1-R2"})

    def test_pending_void_unresolvable_disputed_and_overdue_remain_visible(self):
        for status, expected in (("PENDING", "OVERDUE"), ("VOID", "VOID"), ("UNRESOLVABLE", "UNRESOLVABLE"), ("DISPUTED", "DISPUTED")):
            forecasts = self.prepared_forecasts()
            outcome = outcomes_fixture_module.OutcomeContractTests.outcome(forecasts, status)
            if status == "VOID":
                outcome["void_reason"] = "The defined target was cancelled under its pre-declared policy."
                outcome["resolution_at_utc"] = "2026-02-01T03:00:00Z"
            elif status == "UNRESOLVABLE":
                outcome["resolution_at_utc"] = "2026-02-01T03:00:00Z"
                outcome["resolution_rationale"] = "The authoritative result fell outside the governed rule."
            elif status == "DISPUTED":
                outcome.update({
                    "resolution_at_utc": "2026-02-01T03:00:00Z",
                    "resolution_source_id": "SRC-OUTCOME-PRIMARY",
                    "source_locator": "https://synthetic.invalid/dispute",
                    "dispute_notes": "Two pre-authorised records conflict.",
                })
            result = self.evaluate(forecasts, {"version": "0.1", "outcomes": [outcome]})
            self.assertTrue(all(row["eligibility_state"] == expected for row in result["records"]))
        pending = self.evaluate(outcomes=self.prepared_outcome(status="PENDING"))
        self.assertTrue(all(row["eligibility_state"] == "OVERDUE" for row in pending["records"]))

    def test_future_resolution_evidence_cannot_score_an_earlier_as_of_evaluation(self):
        forecasts = self.prepared_forecasts()
        outcomes = self.prepared_outcome()
        historical = self.evaluate(forecasts, outcomes, at="2026-02-01T02:30:00Z")
        current = self.evaluate(forecasts, outcomes, at="2026-02-02T00:00:00Z")
        self.assertNotEqual(historical["records"][0]["eligibility_state"], "SCORED")
        self.assertEqual(current["records"][0]["eligibility_state"], "SCORED")

    def test_lead_time_is_resolution_window_end_minus_issue_time(self):
        result = self.evaluate()
        self.assertEqual(result["records"][0]["lead_time_seconds"], 31 * 24 * 60 * 60)

    def test_issuance_and_resolution_denominators_are_explicit(self):
        result = self.evaluate(outcomes=self.prepared_outcome(status="PENDING"))
        counts = result["summary"]["counts"]
        coverage = result["summary"]["resolution_coverage"]
        self.assertEqual(counts["issued"], 2)
        self.assertEqual(counts["overdue"], 2)
        self.assertEqual(coverage["basis"], "issuance_level")
        self.assertEqual(coverage["due"], 2)
        self.assertEqual(coverage["resolved"], 0)
        self.assertEqual(coverage["coverage"], 0.0)
        self.assertEqual(coverage["target_series"]["coverage"], 0.0)

    def test_calibration_zero_and_tiny_samples_do_not_claim_calibration(self):
        empty = self.evaluate({"version": "0.1", "forecasts": []}, {"version": "0.1", "outcomes": []})
        self.assertEqual(empty["summary"]["calibration"]["state"], "NO_SAMPLE")
        forecasts = self.prepared_forecasts()
        forecasts["forecasts"] = forecasts["forecasts"][:1]
        outcomes = self.prepared_outcome(forecasts)
        outcomes["outcomes"][0]["eligible_issuance_ids"] = ["FORECAST-SERIES-SYN-1-I1"]
        one = self.evaluate(forecasts, outcomes)
        self.assertEqual(one["summary"]["calibration"]["state"], "INSUFFICIENT_SAMPLE")

    def test_numeric_aggregation_does_not_merge_incompatible_units(self):
        records = [
            {"eligibility_state": "SCORED", "forecast_type": "NUMERIC_POINT", "target_identifier": "x", "unit": "A", "metrics": {"ABSOLUTE_ERROR": {"metric_value": 1.0, "metric_status": "FINITE"}}},
            {"eligibility_state": "SCORED", "forecast_type": "NUMERIC_POINT", "target_identifier": "x", "unit": "B", "metrics": {"ABSOLUTE_ERROR": {"metric_value": 2.0, "metric_status": "FINITE"}}},
        ]
        with self.assertRaises(ValueError):
            aggregate_evaluation(records, group_by=("forecast_type", "metric_family", "target_identifier"))
        self.assertEqual(len(aggregate_evaluation(records)), 2)

    def test_malformed_timestamp_and_missing_as_of_fail_without_scoring(self):
        with self.assertRaises(ValueError):
            evaluate_forecasts(self.config, self.prepared_forecasts(), self.prepared_outcome(), as_of_utc="not-a-time")
        malformed = self.prepared_forecasts()
        malformed["forecasts"][0]["revision_created_at_utc"] = "not-a-time"
        with self.assertRaises(ValueError):
            evaluate_forecasts(self.config, malformed, self.prepared_outcome(), as_of_utc="2026-02-02T00:00:00Z")

    def test_methodology_revision_changes_derived_identity_without_mutating_sources(self):
        original = self.evaluate()
        revised_config = copy.deepcopy(self.config)
        revised_config["version"] = "0.2"
        revised_config["methodology"]["version"] = "0.2"
        revised = evaluate_forecasts(revised_config, self.prepared_forecasts(), self.prepared_outcome(), as_of_utc="2026-02-02T00:00:00Z")
        self.assertNotEqual(original["records"][0]["evaluation_id"], revised["records"][0]["evaluation_id"])
        self.assertEqual(original["records"][0]["forecast_value_snapshot"], revised["records"][0]["forecast_value_snapshot"])

    def test_upstream_production_and_existing_outputs_remain_unchanged(self):
        for path, key in (
            ("data/signals/signals.json", "signals"),
            ("data/relationships/relationships.json", "relationships"),
            ("data/risks/states.json", "states"),
            ("data/scenarios/scenarios.json", "scenarios"),
            ("data/forecasts/forecasts.json", "forecasts"),
            ("data/outcomes/outcomes.json", "outcomes"),
            ("data/evaluation/evaluation.json", "evaluations"),
        ):
            data = json.loads((ROOT / path).read_text())
            if key == "signals":
                self.assertEqual(len(data[key]), 1)
                self.assertEqual(data["population_state"], "CONTROLLED_REVIEWED_SIGNAL_SPECIMEN")
            elif key == "forecasts":
                self.assertEqual(len(data[key]), 4)
                self.assertEqual(data["population_state"], "PILOT_PRODUCTION_FORECASTS_REVIEWED")
            else:
                self.assertEqual(data[key], [])
        self.assertTrue((ROOT / "docs/world-signals.ics").exists())
        self.assertTrue((ROOT / "docs/data/risk_overlay.json").exists())


if __name__ == "__main__":
    unittest.main()
