import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.forecast_admission import validate_admission_transaction
from world_signals.forecasts import validate_forecast_history


class ForecastAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / "data/forecasts/schema.json").read_text())
        cls.dataset = json.loads((ROOT / "data/forecasts/forecasts.json").read_text())
        cls.transaction = json.loads((ROOT / "data/forecasts/admission_transaction.json").read_text())
        cls.scenarios = json.loads((ROOT / "data/scenarios/scenarios.json").read_text())
        cls.risks = json.loads((ROOT / "data/risks/states.json").read_text())
        cls.signals = json.loads((ROOT / "data/signals/signals.json").read_text())
        cls.relationships = json.loads((ROOT / "data/relationships/relationships.json").read_text())
        cls.observations = json.loads((ROOT / "data/live_intelligence/observations.json").read_text())
        cls.evidence = json.loads((ROOT / "data/live_intelligence/evidence_registry.json").read_text())
        cls.canonical = json.loads((ROOT / "data/canonical/registry.json").read_text())
        cls.sources = json.loads((ROOT / "data/sources/registry.json").read_text())

    def valid_errors(self, dataset=None, transaction=None):
        return validate_admission_transaction(
            self.schema,
            dataset or self.dataset,
            self.transaction if transaction is None else transaction,
            now_utc="2026-09-26T17:01:00Z",
        )

    def test_reviewed_transaction_admits_exact_prospective_population(self):
        self.assertEqual(self.valid_errors(), ())

    def test_production_rows_require_explicit_transaction(self):
        errors = self.valid_errors(transaction=None)
        # Passing None uses the class transaction by default; make the absence explicit.
        errors = validate_admission_transaction(self.schema, self.dataset, None)
        self.assertTrue(any("transaction is required" in error for error in errors))

    def test_target_already_resolved_is_rejected(self):
        dataset = copy.deepcopy(self.dataset)
        dataset["forecasts"][0]["resolution"]["window_end_at_utc"] = "2026-09-26T16:59:00Z"
        errors = self.valid_errors(dataset)
        self.assertTrue(any("not prospective" in error for error in errors))

    def test_missing_authoritative_source_is_rejected(self):
        rows = copy.deepcopy(self.dataset["forecasts"])
        rows[0]["resolution"]["resolution_source_ids"] = []
        report = validate_forecast_history(
            self.schema, rows, self.scenarios, self.risks, self.signals,
            self.relationships, self.observations, self.evidence, self.canonical, self.sources,
        )
        self.assertFalse(report.ok)
        self.assertTrue(any("authoritative resolution source" in error for error in report.errors))

    def test_ambiguous_resolution_rule_is_rejected(self):
        rows = copy.deepcopy(self.dataset["forecasts"])
        rows[0]["resolution"]["resolution_rule"] = "Decide later from the most convenient official publication."
        rows[0]["resolution"]["resolution_source_basis"] = ""
        report = validate_forecast_history(
            self.schema, rows, self.scenarios, self.risks, self.signals,
            self.relationships, self.observations, self.evidence, self.canonical, self.sources,
        )
        self.assertFalse(report.ok)
        self.assertTrue(any("resolution resolution_source_basis is required" in error for error in report.errors))

    def test_reviewer_provenance_is_required(self):
        transaction = copy.deepcopy(self.transaction)
        transaction["reviewer"]["reviewer_id"] = ""
        errors = self.valid_errors(transaction=transaction)
        self.assertTrue(any("reviewer provenance" in error for error in errors))

    def test_pre_and_post_hashes_are_binding(self):
        transaction = copy.deepcopy(self.transaction)
        transaction["post_state"]["sha256_dataset"] = "tampered"
        errors = self.valid_errors(transaction=transaction)
        self.assertTrue(any("dataset hash" in error for error in errors))

    def test_duplicate_issuance_is_rejected(self):
        transaction = copy.deepcopy(self.transaction)
        transaction["issuance_ids"].append(transaction["issuance_ids"][0])
        errors = self.valid_errors(transaction=transaction)
        self.assertTrue(any("issuance_ids must be" in error for error in errors))

    def test_admitted_issuance_cannot_be_deleted_from_the_post_state(self):
        dataset = copy.deepcopy(self.dataset)
        dataset["forecasts"].pop()
        errors = self.valid_errors(dataset)
        self.assertTrue(any("do not exactly match the production dataset" in error for error in errors))

    def test_substantive_update_is_not_an_administrative_admission(self):
        transaction = copy.deepcopy(self.transaction)
        transaction["transaction_type"] = "ADMINISTRATIVE_CORRECTION"
        errors = self.valid_errors(transaction=transaction)
        self.assertTrue(any("initial prospective Forecast pilot" in error for error in errors))

    def test_denominator_obligation_is_retained(self):
        self.assertIn("evaluation denominator", self.transaction["denominator_obligation"])
        self.assertEqual(len(self.dataset["forecasts"]), len(self.transaction["issuance_ids"]))


if __name__ == "__main__":
    unittest.main()
