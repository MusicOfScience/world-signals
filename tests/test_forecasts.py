import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.forecasts import (
    forecast_state_as_of,
    public_forecast_projection,
    validate_forecast_history,
    validate_forecasts,
)


class ForecastContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / "data/forecasts/schema.json").read_text())
        cls.dataset = json.loads((ROOT / "data/forecasts/forecasts.json").read_text())
        cls.canonical = {"records": []}
        cls.sources = {
            "sources": [
                {"source_id": "SRC-PRIMARY"},
                {"source_id": "SRC-FALLBACK"},
            ]
        }
        cls.observations = {
            "observations": [
                {
                    "observation_id": "OBS-SYN-1",
                    "observed_at_utc": "2026-01-01T00:00:00Z",
                    "evidence_refs": ["EVID-SYN-1"],
                },
                {
                    "observation_id": "OBS-SYN-2",
                    "observed_at_utc": "2026-01-02T00:00:00Z",
                    "evidence_refs": ["EVID-SYN-2"],
                },
            ]
        }
        cls.evidence = {
            "evidence": [
                {
                    "evidence_id": "EVID-SYN-1",
                    "provider": "Synthetic Provider One",
                    "publication_time": {"published_at_utc": "2026-01-01T01:00:00Z"},
                },
                {
                    "evidence_id": "EVID-SYN-2",
                    "provider": "Synthetic Provider Two",
                    "publication_time": {"published_at_utc": "2026-01-02T01:00:00Z"},
                },
            ]
        }
        cls.scenarios = {"scenario_sets": [], "scenarios": [cls.upstream("scenario_id", "SCENARIO-SYN-1", "SCENARIO-SYN-1-R1")]}
        cls.risks = {"states": [cls.upstream("state_id", "RISK-SYN-1", "RISK-SYN-1-R1")]}
        cls.signals = {"signals": [cls.upstream("signal_id", "SIGNAL-SYN-1", "SIGNAL-SYN-1-R1")]}
        cls.relationships = {"relationships": [cls.upstream("relationship_id", "RELATIONSHIP-SYN-1", "RELATIONSHIP-SYN-1-R1")]}

    @staticmethod
    def upstream(id_key, object_id, revision_id, lifecycle="ACTIVE", review="ACCEPTED"):
        return {
            id_key: object_id,
            "revision_id": revision_id,
            "review_state": review,
            "lifecycle_state": lifecycle,
            "review_provenance": {
                "created_by": "synthetic-reviewer",
                "created_at_utc": "2026-01-04T00:00:00Z",
                "reviewed_by": "synthetic-reviewer" if review == "ACCEPTED" else None,
                "reviewed_at_utc": "2026-01-04T01:00:00Z" if review == "ACCEPTED" else None,
                "decision_basis": "Synthetic reviewed upstream fixture" if review == "ACCEPTED" else None,
            },
        }

    @classmethod
    def base_row(cls):
        return {
            "forecast_id": "FORECAST-SYN-1",
            "issuance_id": "FORECAST-SYN-1-I1",
            "issuance_number": 1,
            "previous_issuance_id": None,
            "issuance_kind": "INITIAL",
            "revision_id": "FORECAST-SYN-1-I1-R1",
            "revision_number": 1,
            "previous_revision_id": None,
            "revision_kind": "ORIGINAL",
            "forecast_type": "BINARY_EVENT",
            "question": "Will the synthetic threshold event occur by the resolution date?",
            "target": {
                "target_kind": "EVENT",
                "target_identifier": "synthetic-threshold-event",
                "definition": "A synthetic event defined by the test resolution rule.",
            },
            "forecast_value": {"probability": 0.40},
            "issued_at_utc": "2026-01-05T00:00:00Z",
            "information_cutoff_at_utc": "2026-01-04T00:00:00Z",
            "revision_created_at_utc": "2026-01-05T00:00:00Z",
            "horizon": {
                "horizon_type": "FIXED_DATE",
                "end_at_utc": "2026-02-01T00:00:00Z",
                "description": "Resolve at the synthetic fixed date.",
            },
            "resolution": {
                "window_start_at_utc": "2026-02-01T00:00:00Z",
                "window_end_at_utc": "2026-02-01T00:00:00Z",
                "resolution_rule": "Resolve yes if the defined synthetic event is recorded by the authoritative source on the resolution date.",
                "resolution_source_ids": ["SRC-PRIMARY", "SRC-FALLBACK"],
                "fallback_source_ids": ["SRC-FALLBACK"],
                "resolution_source_basis": "Synthetic authoritative source policy fixed at issuance.",
                "missing_data_policy": "USE_FALLBACK_THEN_VOID",
                "cancellation_policy": "VOID_IF_TARGET_CANCELLED",
                "vintage_policy": "NOT_APPLICABLE",
                "vintage_definition": "Not applicable to a binary event.",
                "measurement_time_basis": "UTC date of the authoritative record.",
            },
            "scenario_references": [{"scenario_id": "SCENARIO-SYN-1", "revision_id": "SCENARIO-SYN-1-R1"}],
            "risk_state_references": [{"state_id": "RISK-SYN-1", "revision_id": "RISK-SYN-1-R1"}],
            "signal_references": [{"signal_id": "SIGNAL-SYN-1", "revision_id": "SIGNAL-SYN-1-R1"}],
            "relationship_references": [{"relationship_id": "RELATIONSHIP-SYN-1", "revision_id": "RELATIONSHIP-SYN-1-R1"}],
            "supporting_observation_ids": ["OBS-SYN-1"],
            "supporting_evidence_refs": ["EVID-SYN-1"],
            "assumptions": [
                {
                    "assumption_id": "ASSUMPTION-SYN-1",
                    "statement": "The synthetic authoritative source remains available through the resolution window.",
                    "rationale": "A source availability assumption is needed to define void handling.",
                    "provenance": "Synthetic analyst review.",
                    "basis_observation_ids": ["OBS-SYN-1"],
                    "basis_evidence_refs": ["EVID-SYN-1"],
                }
            ],
            "rationale": "Synthetic forecast rationale for contract testing only.",
            "forecast_provenance": {
                "issuer_type": "HUMAN_ANALYST",
                "issuer_id": "synthetic-analyst",
                "method_family": "structured-review",
                "human_reviewed": True,
            },
            "review_state": "ACCEPTED",
            "lifecycle_state": "OPEN",
            "void_reason": None,
            "voided_at_utc": None,
            "review_provenance": {
                "created_by": "synthetic-analyst",
                "created_at_utc": "2026-01-05T00:00:00Z",
                "reviewed_by": "synthetic-reviewer",
                "reviewed_at_utc": "2026-01-05T01:00:00Z",
                "decision_basis": "Synthetic contract review.",
            },
            "revision_reason": "Synthetic initial forecast issuance.",
        }

    @classmethod
    def validate_rows(cls, rows, *, previous_revisions=None):
        return validate_forecast_history(
            cls.schema,
            rows,
            cls.scenarios,
            cls.risks,
            cls.signals,
            cls.relationships,
            cls.observations,
            cls.evidence,
            cls.canonical,
            cls.sources,
            previous_revisions=previous_revisions,
        )

    def assert_valid(self, rows):
        report = self.validate_rows(rows)
        self.assertTrue(report.ok, report.errors)

    def assert_invalid(self, rows, text):
        report = self.validate_rows(rows)
        self.assertFalse(report.ok)
        self.assertTrue(any(text in error for error in report.errors), report.errors)

    def test_zero_production_forecasts_validate_and_projection_is_closed(self):
        dataset = copy.deepcopy(self.dataset)
        dataset["population_state"] = "CLOSED_NO_PRODUCTION_FORECASTS"
        dataset["forecasts"] = []
        report = validate_forecasts(
            self.schema, dataset, self.scenarios, self.risks, self.signals,
            self.relationships, self.observations, self.evidence, self.canonical, self.sources,
        )
        self.assertTrue(report.ok, report.errors)
        projection = public_forecast_projection(
            self.schema, dataset, self.scenarios, self.risks, self.signals,
            self.relationships, self.observations, self.evidence, self.canonical, self.sources,
        )
        self.assertFalse(projection["metadata"]["public_forecast_projection_allowed"])
        self.assertEqual(projection["forecasts"], [])

    def test_populated_production_dataset_is_rejected(self):
        dataset = copy.deepcopy(self.dataset)
        dataset["forecasts"] = [self.base_row()]
        report = validate_forecasts(
            self.schema, dataset, self.scenarios, self.risks, self.signals,
            self.relationships, self.observations, self.evidence, self.canonical, self.sources,
        )
        self.assertFalse(report.ok)
        self.assertTrue(any("admission transaction" in error for error in report.errors))

    def test_valid_context_references_are_accepted(self):
        self.assert_valid([self.base_row()])

    def test_unknown_upstream_revision_is_rejected(self):
        row = self.base_row()
        row["scenario_references"][0]["revision_id"] = "UNKNOWN"
        self.assert_invalid([row], "unknown scenario_references revision")

    def test_withdrawn_upstream_cannot_support_open_forecast(self):
        risks = copy.deepcopy(self.risks)
        risks["states"][0]["lifecycle_state"] = "WITHDRAWN"
        report = validate_forecast_history(
            self.schema, [self.base_row()], self.scenarios, risks, self.signals,
            self.relationships, self.observations, self.evidence, self.canonical, self.sources,
        )
        self.assertFalse(report.ok)
        self.assertTrue(any("withdrawn upstream" in error or "non-active upstream" in error for error in report.errors))

    def test_binary_probability_lower_and_upper_bounds_are_enforced(self):
        for probability in (-0.01, 1.01):
            row = self.base_row()
            row["forecast_value"]["probability"] = probability
            self.assert_invalid([row], "binary probability")

    def test_categorical_probabilities_are_complete_and_sum_to_one(self):
        row = self.base_row()
        row["forecast_type"] = "CATEGORICAL"
        row["forecast_value"] = {
            "outcomes": [
                {"outcome_id": "A", "label": "Synthetic A", "definition": "A", "probability": 0.6},
                {"outcome_id": "B", "label": "Synthetic B", "definition": "B", "probability": 0.4},
            ],
            "mutually_exclusive": True,
            "collectively_exhaustive": True,
            "coverage_basis": "The two synthetic outcomes exhaust the defined rule.",
        }
        self.assert_valid([row])
        row["forecast_value"]["outcomes"][1]["probability"] = 0.3
        self.assert_invalid([row], "sum to 1")

    def test_categorical_outcomes_must_be_unique_and_exhaustive(self):
        row = self.base_row()
        row["forecast_type"] = "CATEGORICAL"
        row["forecast_value"] = {
            "outcomes": [
                {"outcome_id": "A", "label": "Synthetic A", "definition": "A", "probability": 0.5},
                {"outcome_id": "A", "label": "Synthetic A again", "definition": "A", "probability": 0.5},
            ],
            "mutually_exclusive": True,
            "collectively_exhaustive": False,
            "coverage_basis": "Incomplete synthetic categories.",
        }
        self.assert_invalid([row], "unique")
        self.assert_invalid([row], "exhaustive")

    def test_numeric_forecast_requires_unit_and_explicit_vintage_policy(self):
        row = self.base_row()
        row["forecast_type"] = "NUMERIC_POINT"
        row["forecast_value"] = {"estimate": 12.0}
        self.assert_invalid([row], "finite estimate and unit")
        row["forecast_value"] = {"estimate": 12.0, "unit": "synthetic units"}
        row["resolution"]["vintage_policy"] = "NOT_APPLICABLE"
        self.assert_invalid([row], "vintage policy")
        row["resolution"]["vintage_policy"] = "FIRST_OFFICIAL_RELEASE"
        row["resolution"]["vintage_definition"] = "First official release, as published by the named source."
        self.assert_valid([row])

    def test_information_cutoff_is_not_after_issue_and_rejects_late_publication(self):
        row = self.base_row()
        row["information_cutoff_at_utc"] = "2026-01-06T00:00:00Z"
        self.assert_invalid([row], "cutoff cannot follow")
        row = self.base_row()
        evidence = copy.deepcopy(self.evidence)
        evidence["evidence"][0]["publication_time"]["published_at_utc"] = "2026-01-05T00:01:00Z"
        report = validate_forecast_history(
            self.schema, [row], self.scenarios, self.risks, self.signals,
            self.relationships, self.observations, evidence, self.canonical, self.sources,
        )
        self.assertFalse(report.ok)
        self.assertTrue(any("published after information cutoff" in error for error in report.errors))

    def test_late_assumption_evidence_cannot_be_attached_to_an_earlier_issuance(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["evidence"][0]["publication_time"]["published_at_utc"] = "2026-01-05T00:01:00Z"
        report = validate_forecast_history(
            self.schema, [self.base_row()], self.scenarios, self.risks, self.signals,
            self.relationships, self.observations, evidence, self.canonical, self.sources,
        )
        self.assertFalse(report.ok)
        self.assertTrue(any("assumption evidence published after" in error for error in report.errors))

    def test_analytical_update_is_a_distinct_scoreable_issuance(self):
        initial = self.base_row()
        update = copy.deepcopy(initial)
        update.update({
            "issuance_id": "FORECAST-SYN-1-I2",
            "issuance_number": 2,
            "previous_issuance_id": "FORECAST-SYN-1-I1",
            "issuance_kind": "ANALYTICAL_UPDATE",
            "revision_id": "FORECAST-SYN-1-I2-R1",
            "issued_at_utc": "2026-01-10T00:00:00Z",
            "information_cutoff_at_utc": "2026-01-09T00:00:00Z",
            "revision_created_at_utc": "2026-01-10T00:00:00Z",
            "forecast_value": {"probability": 0.60},
            "revision_reason": "Synthetic analytical update.",
        })
        self.assert_valid([initial, update])

    def test_administrative_correction_preserves_substantive_content(self):
        original = self.base_row()
        correction = copy.deepcopy(original)
        correction.update({
            "revision_id": "FORECAST-SYN-1-I1-R2",
            "revision_number": 2,
            "previous_revision_id": original["revision_id"],
            "revision_kind": "ADMINISTRATIVE_CORRECTION",
            "revision_created_at_utc": "2026-01-05T02:00:00Z",
            "review_provenance": {
                "created_by": "synthetic-analyst",
                "created_at_utc": "2026-01-05T00:00:00Z",
                "reviewed_by": "synthetic-reviewer",
                "reviewed_at_utc": "2026-01-05T03:00:00Z",
                "decision_basis": "Corrected synthetic source URL metadata outside the substantive contract.",
            },
            "revision_reason": "Administrative correction only.",
        })
        self.assert_valid([original, correction])
        correction["forecast_value"]["probability"] = 0.5
        self.assert_invalid([original, correction], "substantive forecast content")

    def test_question_resolution_and_target_date_are_immutable_across_issuances(self):
        original = self.base_row()
        update = copy.deepcopy(original)
        update.update({
            "issuance_id": "FORECAST-SYN-1-I2",
            "issuance_number": 2,
            "previous_issuance_id": "FORECAST-SYN-1-I1",
            "issuance_kind": "ANALYTICAL_UPDATE",
            "revision_id": "FORECAST-SYN-1-I2-R1",
            "issued_at_utc": "2026-01-10T00:00:00Z",
            "information_cutoff_at_utc": "2026-01-09T00:00:00Z",
            "revision_created_at_utc": "2026-01-10T00:00:00Z",
            "revision_reason": "Synthetic update.",
        })
        update["question"] = "A different synthetic question?"
        self.assert_invalid([original, update], "question, target or resolution changed")
        update = copy.deepcopy(update)
        update["question"] = original["question"]
        update["resolution"]["window_end_at_utc"] = "2026-02-02T00:00:00Z"
        self.assert_invalid([original, update], "question, target or resolution changed")

    def test_void_requires_explicit_governed_reason(self):
        row = self.base_row()
        row["lifecycle_state"] = "VOID"
        self.assert_invalid([row], "VOID forecast requires")
        row["void_reason"] = "Target event was formally cancelled under the predeclared policy."
        row["voided_at_utc"] = "2026-01-10T00:00:00Z"
        self.assert_valid([row])

    def test_scenario_probability_and_ranking_fields_are_not_forecast_fields(self):
        row = self.base_row()
        row["scenario_probability"] = 0.8
        self.assert_invalid([row], "missing/unknown Forecast fields")
        row = self.base_row()
        row["ranking"] = 1
        self.assert_invalid([row], "missing/unknown Forecast fields")

    def test_probability_is_not_required_for_numeric_forecast(self):
        row = self.base_row()
        row["forecast_type"] = "NUMERIC_POINT"
        row["forecast_value"] = {"estimate": 15.0, "unit": "synthetic units"}
        row["resolution"]["vintage_policy"] = "FIRST_OFFICIAL_RELEASE"
        self.assert_valid([row])

    def test_duplicate_issuance_key_is_rejected(self):
        first = self.base_row()
        second = copy.deepcopy(first)
        second["issuance_id"] = "FORECAST-SYN-1-I2"
        second["issuance_number"] = 2
        second["previous_issuance_id"] = first["issuance_id"]
        second["issuance_kind"] = "ANALYTICAL_UPDATE"
        second["revision_id"] = "FORECAST-SYN-1-I2-R1"
        self.assert_invalid([first, second], "duplicate issuance key")

    def test_as_of_state_excludes_later_issuances_and_retains_prior_history(self):
        initial = self.base_row()
        update = copy.deepcopy(initial)
        update.update({
            "issuance_id": "FORECAST-SYN-1-I2",
            "issuance_number": 2,
            "previous_issuance_id": "FORECAST-SYN-1-I1",
            "issuance_kind": "ANALYTICAL_UPDATE",
            "revision_id": "FORECAST-SYN-1-I2-R1",
            "issued_at_utc": "2026-01-10T00:00:00Z",
            "information_cutoff_at_utc": "2026-01-09T00:00:00Z",
            "revision_created_at_utc": "2026-01-10T00:00:00Z",
            "forecast_value": {"probability": 0.60},
            "revision_reason": "Synthetic analytical update.",
        })
        rows = [initial, update]
        state = forecast_state_as_of(
            self.schema, rows, self.scenarios, self.risks, self.signals,
            self.relationships, self.observations, self.evidence, self.canonical, self.sources,
            "2026-01-06T00:00:00Z",
        )
        self.assertEqual(set(state), {initial["issuance_id"]})
        self.assertEqual(state[initial["issuance_id"]]["forecast_value"], {"probability": 0.40})
        later = forecast_state_as_of(
            self.schema, rows, self.scenarios, self.risks, self.signals,
            self.relationships, self.observations, self.evidence, self.canonical, self.sources,
            "2026-01-11T00:00:00Z",
        )
        self.assertEqual(set(later), {initial["issuance_id"], update["issuance_id"]})

    def test_previous_revision_guard_rejects_rewritten_history(self):
        original = self.base_row()
        retained = copy.deepcopy(original)
        retained["forecast_value"]["probability"] = 0.99
        report = self.validate_rows([original], previous_revisions=[retained])
        self.assertFalse(report.ok)
        self.assertTrue(any("removed or rewritten" in error for error in report.errors))

    def test_synthetic_forecast_fixture_has_no_outcome_or_scoring_results(self):
        row = self.base_row()
        self.assertNotIn("outcome", row)
        self.assertNotIn("score", row)
        self.assertNotIn("resolution_result", row)
        self.assertNotIn("calibration", row)

    def test_malformed_inputs_fail_closed_without_validator_exceptions(self):
        malformed = [None, {"forecast_id": "missing-fields"}, "not-an-object"]
        for value in malformed:
            try:
                report = self.validate_rows([value])
            except Exception as exc:  # pragma: no cover - the assertion documents the contract
                self.fail(f"malformed Forecast input raised {exc!r}")
            self.assertFalse(report.ok)

    def test_production_upstream_populations_and_risk_overlay_input_are_untouched(self):
        for data, key in ((self.signals, "signals"), (self.relationships, "relationships"), (self.risks, "states"), (self.scenarios, "scenarios")):
            self.assertEqual(len(data[key]), 1)  # synthetic fixtures stay out of production files
        for path in (
            ROOT / "data/signals/signals.json",
            ROOT / "data/relationships/relationships.json",
            ROOT / "data/risks/states.json",
            ROOT / "data/scenarios/scenarios.json",
        ):
            data = json.loads(path.read_text())
            key = "signals" if "signals" in data else "relationships" if "relationships" in data else "states" if "states" in data else "scenarios"
            self.assertEqual(data[key], [])


if __name__ == "__main__":
    unittest.main()
