import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.outcomes import (
    forecast_resolution_due_state,
    outcome_state_as_of,
    public_outcome_projection,
    validate_outcome_history,
    validate_outcomes,
)


class OutcomeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / "data/outcomes/schema.json").read_text())
        cls.dataset = json.loads((ROOT / "data/outcomes/outcomes.json").read_text())
        cls.sources = {
            "sources": [
                {"source_id": "SRC-OUTCOME-PRIMARY"},
                {"source_id": "SRC-OUTCOME-FALLBACK"},
            ]
        }
        cls.evidence = {
            "evidence": [
                {
                    "evidence_id": "EVID-OUTCOME-1",
                    "provider": "Synthetic authoritative provider",
                    "publication_time": {"published_at_utc": "2026-02-01T02:00:00Z"},
                },
                {
                    "evidence_id": "EVID-OUTCOME-CORRECTION",
                    "provider": "Synthetic authoritative provider",
                    "publication_time": {"published_at_utc": "2026-02-02T02:00:00Z"},
                },
            ]
        }

    @staticmethod
    def forecast_row(
        issuance_id="FORECAST-SERIES-SYN-1-I1",
        issuance_number=1,
        issue="2026-01-01T00:00:00Z",
        forecast_type="BINARY_EVENT",
        forecast_value=None,
        forecast_id="FORECAST-SERIES-SYN-1",
        lifecycle="OPEN",
    ):
        if forecast_value is None:
            forecast_value = {"probability": 0.4}
        vintage = "NOT_APPLICABLE" if forecast_type != "NUMERIC_POINT" else "FIRST_OFFICIAL_RELEASE"
        return {
            "forecast_id": forecast_id,
            "issuance_id": issuance_id,
            "issuance_number": issuance_number,
            "issued_at_utc": issue,
            "forecast_type": forecast_type,
            "forecast_value": forecast_value,
            "lifecycle_state": lifecycle,
            "target": {
                "target_kind": "EVENT" if forecast_type == "BINARY_EVENT" else "MEASURE" if forecast_type == "NUMERIC_POINT" else "STATE",
                "target_identifier": "synthetic-target",
                "definition": "Synthetic target with a fixed contract definition.",
            },
            "horizon": {
                "horizon_type": "FIXED_DATE",
                "end_at_utc": "2026-02-01T00:00:00Z",
                "description": "Synthetic fixed resolution date.",
            },
            "resolution": {
                "window_start_at_utc": "2026-02-01T00:00:00Z",
                "window_end_at_utc": "2026-02-01T00:00:00Z",
                "resolution_rule": "Use the named authoritative source to determine the defined synthetic result by the exact deadline.",
                "resolution_source_ids": ["SRC-OUTCOME-PRIMARY", "SRC-OUTCOME-FALLBACK"],
                "fallback_source_ids": ["SRC-OUTCOME-FALLBACK"],
                "resolution_source_basis": "Synthetic source policy fixed at issuance.",
                "missing_data_policy": "USE_FALLBACK_THEN_VOID",
                "cancellation_policy": "VOID_IF_TARGET_CANCELLED",
                "vintage_policy": vintage,
                "vintage_definition": "First official release." if vintage != "NOT_APPLICABLE" else "Not applicable to this event.",
                "measurement_time_basis": "UTC date of the authoritative record.",
            },
        }

    @classmethod
    def forecasts(cls, *, second_series=False, categorical=False, numeric=False):
        if categorical:
            forecast_type = "CATEGORICAL"
            value = {
                "outcomes": [
                    {"outcome_id": "SYN-A", "label": "Synthetic A", "definition": "A", "probability": 0.6},
                    {"outcome_id": "SYN-B", "label": "Synthetic B", "definition": "B", "probability": 0.4},
                ]
            }
        elif numeric:
            forecast_type = "NUMERIC_POINT"
            value = {"estimate": 10.0, "unit": "synthetic units"}
        else:
            forecast_type = "BINARY_EVENT"
            value = {"probability": 0.4}
        first = cls.forecast_row(forecast_type=forecast_type, forecast_value=value)
        second = cls.forecast_row(
            issuance_id="FORECAST-SERIES-SYN-1-I2",
            issuance_number=2,
            issue="2026-01-15T00:00:00Z",
            forecast_type=forecast_type,
            forecast_value=value,
        )
        rows = [first, second]
        if second_series:
            rows.append(cls.forecast_row(
                issuance_id="FORECAST-SERIES-SYN-2-I1",
                issuance_number=1,
                issue="2026-01-02T00:00:00Z",
                forecast_type="BINARY_EVENT",
                forecast_value={"probability": 0.8},
                forecast_id="FORECAST-SERIES-SYN-2",
            ))
        return {"version": "0.1", "forecasts": rows}

    @staticmethod
    def rule(forecast):
        resolution = forecast["resolution"]
        return {
            "forecast_id": forecast["forecast_id"],
            "forecast_type": forecast["forecast_type"],
            "target": forecast["target"],
            "horizon": forecast["horizon"],
            "window_start_at_utc": resolution["window_start_at_utc"],
            "window_end_at_utc": resolution["window_end_at_utc"],
            "resolution_rule": resolution["resolution_rule"],
            "resolution_source_ids": resolution["resolution_source_ids"],
            "fallback_source_ids": resolution["fallback_source_ids"],
            "resolution_source_basis": resolution["resolution_source_basis"],
            "missing_data_policy": resolution["missing_data_policy"],
            "cancellation_policy": resolution["cancellation_policy"],
            "vintage_policy": resolution["vintage_policy"],
            "vintage_definition": resolution["vintage_definition"],
            "measurement_time_basis": resolution["measurement_time_basis"],
        }

    @classmethod
    def outcome(cls, forecasts=None, status="PENDING", observed=None):
        forecasts = forecasts or cls.forecasts()
        forecast = forecasts["forecasts"][0]
        resolved = status == "RESOLVED"
        return {
            "outcome_id": forecast["forecast_id"],
            "forecast_id": forecast["forecast_id"],
            "forecast_type": forecast["forecast_type"],
            "revision_id": "OUTCOME-SERIES-SYN-1-R1",
            "revision_number": 1,
            "previous_revision_id": None,
            "revision_kind": "ORIGINAL",
            "resolution_status": status,
            "observed_outcome": observed if resolved else None,
            "resolution_rule_reference": cls.rule(forecast),
            "eligible_issuance_ids": ["FORECAST-SERIES-SYN-1-I1", "FORECAST-SERIES-SYN-1-I2"],
            "resolution_source_id": "SRC-OUTCOME-PRIMARY" if resolved else None,
            "fallback_source_used": False,
            "fallback_reason": None,
            "resolution_at_utc": "2026-02-01T03:00:00Z" if resolved else None,
            "event_at_utc": "2026-02-01T00:00:00Z" if resolved else None,
            "evidence_publication_at_utc": "2026-02-01T02:00:00Z" if resolved else None,
            "world_signals_reviewed_at_utc": "2026-02-01T03:00:00Z",
            "evidence_refs": ["EVID-OUTCOME-1"] if resolved else [],
            "source_locator": "https://synthetic.invalid/authoritative-result" if resolved else None,
            "resolution_rationale": "Synthetic resolution fixture follows the pinned rule." if resolved else "Awaiting the pre-declared resolution evidence.",
            "void_reason": None,
            "dispute_notes": None,
            "review_provenance": {
                "created_by": "synthetic-reviewer",
                "created_at_utc": "2026-02-01T03:00:00Z",
                "reviewed_by": "synthetic-reviewer",
                "reviewed_at_utc": "2026-02-01T03:00:00Z",
                "decision_basis": "Synthetic Outcome contract review.",
            },
            "provenance": {
                "outcome_established_by": "synthetic-reviewer",
                "method": "predeclared-authoritative-source-review",
                "reviewed": True,
            },
            "revision_reason": "Synthetic initial Outcome record.",
        }

    @classmethod
    def validate(cls, rows, forecasts=None):
        return validate_outcome_history(cls.schema, rows, forecasts or cls.forecasts(), cls.evidence, cls.sources)

    def assert_valid(self, rows, forecasts=None):
        report = self.validate(rows, forecasts)
        self.assertTrue(report.ok, report.errors)

    def assert_invalid(self, rows, text, forecasts=None):
        report = self.validate(rows, forecasts)
        self.assertFalse(report.ok)
        self.assertTrue(any(text in error for error in report.errors), report.errors)

    def test_zero_production_outcomes_validate_and_public_projection_is_closed(self):
        forecasts = {"version": "0.1", "forecasts": []}
        report = validate_outcomes(self.schema, self.dataset, forecasts, self.evidence, self.sources)
        self.assertTrue(report.ok, report.errors)
        projection = public_outcome_projection(self.schema, self.dataset, forecasts, self.evidence, self.sources)
        self.assertFalse(projection["metadata"]["public_outcome_projection_allowed"])
        self.assertEqual(projection["outcomes"], [])

    def test_populated_production_outcome_gate_is_closed(self):
        dataset = copy.deepcopy(self.dataset)
        dataset["outcomes"] = [self.outcome()]
        report = validate_outcomes(self.schema, dataset, self.forecasts(), self.evidence, self.sources)
        self.assertFalse(report.ok)
        self.assertTrue(any("closed production population" in error for error in report.errors))

    def test_valid_forecast_series_and_many_issuances_share_one_outcome(self):
        self.assert_valid([self.outcome(status="RESOLVED", observed={"event_occurred": True})])

    def test_unknown_forecast_issuance_is_rejected(self):
        row = self.outcome()
        row["eligible_issuance_ids"] = ["UNKNOWN-ISSUANCE"]
        self.assert_invalid([row], "unknown eligible Forecast issuance")

    def test_substantively_different_series_requires_a_distinct_outcome(self):
        forecasts = self.forecasts(second_series=True)
        row = self.outcome(forecasts=forecasts)
        row["forecast_id"] = "FORECAST-SERIES-SYN-2"
        row["outcome_id"] = "FORECAST-SERIES-SYN-2"
        self.assert_invalid([row], "eligible issuance does not match")

    def test_administrative_correction_does_not_duplicate_reality(self):
        original = self.outcome(status="RESOLVED", observed={"event_occurred": True})
        correction = copy.deepcopy(original)
        correction.update({
            "revision_id": "OUTCOME-SERIES-SYN-1-R2",
            "revision_number": 2,
            "previous_revision_id": original["revision_id"],
            "revision_kind": "ADMINISTRATIVE_CORRECTION",
            "world_signals_reviewed_at_utc": "2026-02-01T04:00:00Z",
            "revision_reason": "Corrected a citation label without changing the outcome.",
        })
        self.assert_valid([original, correction])
        self.assertEqual(original["outcome_id"], correction["outcome_id"])

    def test_binary_true_and_false_at_deadline_are_resolvable(self):
        self.assert_valid([self.outcome(status="RESOLVED", observed={"event_occurred": True})])
        false = self.outcome(status="RESOLVED", observed={"event_occurred": False})
        self.assert_valid([false])

    def test_binary_event_after_deadline_is_rejected(self):
        row = self.outcome(status="RESOLVED", observed={"event_occurred": True})
        row["event_at_utc"] = "2026-02-02T00:00:00Z"
        self.assert_invalid([row], "within the Forecast resolution window")

    def test_categorical_outcome_uses_original_category_set(self):
        forecasts = self.forecasts(categorical=True)
        row = self.outcome(forecasts=forecasts, status="RESOLVED", observed={"outcome_id": "SYN-A"})
        self.assert_valid([row], forecasts)
        row["observed_outcome"] = {"outcome_id": "RETROSPECTIVE-NEW-CATEGORY"}
        self.assert_invalid([row], "outside the original category set", forecasts)

    def test_numeric_outcome_requires_matching_unit_and_vintage_rule(self):
        forecasts = self.forecasts(numeric=True)
        row = self.outcome(forecasts=forecasts, status="RESOLVED", observed={"value": 11.0, "unit": "synthetic units"})
        self.assert_valid([row], forecasts)
        row["observed_outcome"]["unit"] = "wrong units"
        self.assert_invalid([row], "unit must equal", forecasts)

    def test_primary_resolution_source_is_honoured(self):
        row = self.outcome(status="RESOLVED", observed={"event_occurred": True})
        row["resolution_source_id"] = "SRC-OUTCOME-FALLBACK"
        self.assert_invalid([row], "primary resolution source was not pre-authorised")

    def test_fallback_requires_pre_authorisation_and_is_recorded(self):
        row = self.outcome(status="RESOLVED", observed={"event_occurred": True})
        row["resolution_source_id"] = "SRC-OUTCOME-FALLBACK"
        row["fallback_source_used"] = True
        row["fallback_reason"] = "Primary source unavailable under the pre-declared fallback policy."
        self.assert_valid([row])

    def test_fallback_without_pre_authorisation_is_rejected(self):
        row = self.outcome(status="RESOLVED", observed={"event_occurred": True})
        row["resolution_source_id"] = "SRC-OUTCOME-FALLBACK"
        row["fallback_source_used"] = True
        row["fallback_reason"] = "Fallback selected after the fact."
        row["resolution_rule_reference"]["fallback_source_ids"] = []
        self.assert_invalid([row], "pre-declared Forecast rule")

    def test_event_and_publication_time_remain_distinct(self):
        row = self.outcome(status="RESOLVED", observed={"event_occurred": True})
        self.assertNotEqual(row["event_at_utc"], row["evidence_publication_at_utc"])
        row["world_signals_reviewed_at_utc"] = "2026-02-01T01:00:00Z"
        self.assert_invalid([row], "review cannot precede evidence publication")

    def test_outcome_correction_preserves_prior_revision(self):
        original = self.outcome(status="RESOLVED", observed={"event_occurred": True})
        corrected = copy.deepcopy(original)
        corrected.update({
            "revision_id": "OUTCOME-SERIES-SYN-1-R2",
            "revision_number": 2,
            "previous_revision_id": original["revision_id"],
            "revision_kind": "OUTCOME_CORRECTION",
            "observed_outcome": {"event_occurred": False},
            "evidence_refs": ["EVID-OUTCOME-CORRECTION"],
            "evidence_publication_at_utc": "2026-02-02T02:00:00Z",
            "resolution_at_utc": "2026-02-02T03:00:00Z",
            "world_signals_reviewed_at_utc": "2026-02-02T03:00:00Z",
            "review_provenance": {
                "created_by": "synthetic-reviewer",
                "created_at_utc": "2026-02-01T03:00:00Z",
                "reviewed_by": "synthetic-reviewer",
                "reviewed_at_utc": "2026-02-02T03:00:00Z",
                "decision_basis": "Synthetic source correction review.",
            },
            "revision_reason": "Authoritative source correction changed the recorded result.",
        })
        self.assert_valid([original, corrected])
        self.assertEqual(original["observed_outcome"], {"event_occurred": True})

    def test_original_resolution_rule_cannot_be_rewritten(self):
        original = self.outcome(status="RESOLVED", observed={"event_occurred": True})
        correction = copy.deepcopy(original)
        correction.update({
            "revision_id": "OUTCOME-SERIES-SYN-1-R2",
            "revision_number": 2,
            "previous_revision_id": original["revision_id"],
            "revision_kind": "OUTCOME_CORRECTION",
            "world_signals_reviewed_at_utc": "2026-02-02T03:00:00Z",
            "resolution_rule_reference": {**original["resolution_rule_reference"], "resolution_rule": "A different rule after observing the result."},
            "revision_reason": "Invalid retrospective rule change.",
        })
        self.assert_invalid([original, correction], "resolution rule was rewritten")

    def test_void_requires_reason_and_poor_performance_is_not_a_void_reason(self):
        row = self.outcome(status="VOID")
        self.assert_invalid([row], "VOID requires")
        row["void_reason"] = "The target event was cancelled under the pre-declared cancellation policy."
        row["resolution_at_utc"] = "2026-02-01T03:00:00Z"
        self.assert_valid([row])
        row["void_reason"] = "The forecast performed poorly."
        self.assert_invalid([row], "performance")

    def test_disputed_resolution_is_explicit(self):
        row = self.outcome(status="DISPUTED")
        self.assert_invalid([row], "DISPUTED requires")
        row["dispute_notes"] = "Two pre-authorised authoritative records conflict and require review."
        row["resolution_source_id"] = "SRC-OUTCOME-PRIMARY"
        row["source_locator"] = "https://synthetic.invalid/conflict"
        row["resolution_at_utc"] = "2026-02-01T03:00:00Z"
        self.assert_valid([row])

    def test_out_of_contract_category_uses_unresolvable_policy(self):
        forecasts = self.forecasts(categorical=True)
        row = self.outcome(forecasts=forecasts, status="UNRESOLVABLE")
        row["resolution_at_utc"] = "2026-02-01T03:00:00Z"
        row["resolution_rationale"] = "The authoritative result fell outside the original exhaustive category set."
        self.assert_valid([row], forecasts)

    def test_pending_cannot_masquerade_as_resolved(self):
        row = self.outcome()
        row["observed_outcome"] = {"event_occurred": True}
        self.assert_invalid([row], "PENDING Outcome cannot carry")

    def test_due_state_helper_is_deterministic(self):
        forecast = self.forecasts()["forecasts"][0]
        self.assertEqual(forecast_resolution_due_state(forecast, "2026-01-31T23:59:59Z"), "NOT_YET_DUE")
        self.assertEqual(forecast_resolution_due_state(forecast, "2026-02-01T00:00:00Z"), "DUE_AWAITING_AUTHORITATIVE_EVIDENCE")
        self.assertEqual(forecast_resolution_due_state(forecast, "2026-02-01T00:00:00Z", authoritative_evidence_available=True), "DUE_AWAITING_REVIEW")
        self.assertEqual(forecast_resolution_due_state(forecast, "2026-02-02T00:00:00Z"), "OVERDUE_FOR_RESOLUTION_REVIEW")
        resolved = self.outcome(status="RESOLVED", observed={"event_occurred": True})
        self.assertEqual(forecast_resolution_due_state(forecast, "2026-01-01T00:00:00Z", resolved), "RESOLVED")

    def test_as_of_state_excludes_future_outcome_revision(self):
        original = self.outcome()
        later = copy.deepcopy(original)
        later.update({
            "revision_id": "OUTCOME-SERIES-SYN-1-R2",
            "revision_number": 2,
            "previous_revision_id": original["revision_id"],
            "revision_kind": "RESOLUTION_UPDATE",
            "resolution_status": "RESOLVED",
            "observed_outcome": {"event_occurred": True},
            "resolution_source_id": "SRC-OUTCOME-PRIMARY",
            "resolution_at_utc": "2026-02-01T03:00:00Z",
            "event_at_utc": "2026-02-01T00:00:00Z",
            "evidence_publication_at_utc": "2026-02-01T02:00:00Z",
            "world_signals_reviewed_at_utc": "2026-02-01T04:00:00Z",
            "evidence_refs": ["EVID-OUTCOME-1"],
            "source_locator": "https://synthetic.invalid/result",
            "resolution_rationale": "Synthetic resolution.",
            "revision_reason": "Synthetic resolution update.",
        })
        historical = outcome_state_as_of(self.schema, [original, later], self.forecasts(), self.evidence, self.sources, "2026-02-01T03:30:00Z")
        self.assertEqual(historical[original["outcome_id"]]["resolution_status"], "PENDING")
        current = outcome_state_as_of(self.schema, [original, later], self.forecasts(), self.evidence, self.sources, "2026-02-01T05:00:00Z")
        self.assertEqual(current[original["outcome_id"]]["resolution_status"], "RESOLVED")

    def test_no_scoring_metric_is_generated(self):
        row = self.outcome(status="RESOLVED", observed={"event_occurred": True})
        self.assert_valid([row])
        self.assertFalse(any("score" in key or "accuracy" in key for key in row))

    def test_malformed_inputs_fail_closed_without_exceptions(self):
        for malformed in [None, "not-an-object", {"outcome_id": "missing-fields"}]:
            try:
                report = self.validate([malformed])
            except Exception as exc:  # pragma: no cover
                self.fail(f"malformed Outcome input raised {exc!r}")
            self.assertFalse(report.ok)

    def test_upstream_production_populations_and_ics_risk_inputs_are_unchanged(self):
        for path, key in (
            ("data/signals/signals.json", "signals"),
            ("data/relationships/relationships.json", "relationships"),
            ("data/risks/states.json", "states"),
            ("data/scenarios/scenarios.json", "scenarios"),
            ("data/forecasts/forecasts.json", "forecasts"),
            ("data/outcomes/outcomes.json", "outcomes"),
        ):
            self.assertEqual(json.loads((ROOT / path).read_text())[key], [])
        self.assertTrue((ROOT / "docs/world-signals.ics").exists())
        self.assertTrue((ROOT / "docs/data/risk_overlay.json").exists())


if __name__ == "__main__":
    unittest.main()
