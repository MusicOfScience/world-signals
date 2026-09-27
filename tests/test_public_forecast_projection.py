import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.public_forecast_projection import (
    PUBLIC_FORECAST_ALLOWLIST,
    PublicForecastProjectionError,
    build_public_forecast_projection,
    validate_public_forecast_projection,
)

class PublicForecastProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / "data/forecasts/forecasts.json"
        cls.dataset = json.loads(cls.path.read_text(encoding="utf-8"))

    def test_exact_reviewed_open_allowlist_projects(self):
        projection = build_public_forecast_projection(self.dataset)
        self.assertEqual(
            {row["forecast_id"] for row in projection["forecasts"]},
            set(PUBLIC_FORECAST_ALLOWLIST),
        )
        self.assertEqual(projection["metadata"]["public_forecast_count"], 4)
        self.assertEqual(validate_public_forecast_projection(projection), [])

    def test_values_cutoffs_and_resolution_contracts_are_preserved(self):
        projection = build_public_forecast_projection(self.dataset)
        rows = {row["forecast_id"]: row for row in projection["forecasts"]}
        self.assertEqual(rows["WS-FP-RBA-20261103"]["forecast_value"]["estimate"], 4.35)
        self.assertEqual(rows["WS-FP-BOC-20261028"]["forecast_value"]["estimate"], 2.25)
        self.assertEqual(rows["WS-FP-FED-20261028"]["forecast_value"]["outcomes"][1]["probability"], 0.65)
        self.assertEqual(rows["WS-FP-ECB-20261029"]["forecast_value"]["outcomes"][1]["probability"], 0.55)
        for row in rows.values():
            self.assertEqual(row["information_cutoff_at_utc"], "2026-09-26T17:00:00Z")
            self.assertEqual(row["resolution"]["window_start_at_utc"], row["resolution"]["window_end_at_utc"])
            self.assertTrue(row["resolution"]["resolution_rule"])

    def test_categorical_probabilities_sum_and_numeric_units_remain_typed(self):
        projection = build_public_forecast_projection(self.dataset)
        for row in projection["forecasts"]:
            if row["forecast_type"] == "CATEGORICAL":
                self.assertAlmostEqual(
                    sum(item["probability"] for item in row["forecast_value"]["outcomes"]), 1.0
                )
            else:
                self.assertIsInstance(row["forecast_value"]["estimate"], (int, float))
                self.assertTrue(row["forecast_value"]["unit"])

    def test_private_review_and_model_fields_are_not_projected(self):
        projection = build_public_forecast_projection(self.dataset)
        text = json.dumps(projection)
        for field in ("forecast_provenance", "review_provenance", "supporting_evidence_refs", "assumptions"):
            self.assertNotIn(field, text)
        self.assertEqual(projection["metadata"]["evaluation_state"], "NO_SAMPLE")
        self.assertEqual(projection["metadata"]["outcome_projection"], "NONE_AVAILABLE")
        self.assertTrue(all(row["resolution_status"] == "UNRESOLVED" for row in projection["forecasts"]))

    def test_political_or_electoral_forecast_fails_closed(self):
        dataset = copy.deepcopy(self.dataset)
        dataset["forecasts"][0]["question"] = "Which party wins the election?"
        with self.assertRaises(PublicForecastProjectionError):
            build_public_forecast_projection(dataset)

    def test_draft_or_non_allowlisted_forecast_is_not_public(self):
        dataset = copy.deepcopy(self.dataset)
        extra = copy.deepcopy(dataset["forecasts"][0])
        extra["forecast_id"] = "WS-FP-SYN-DRAFT-ELECTION"
        extra["review_state"] = "DRAFT"
        extra["question"] = "Which party wins the election?"
        dataset["forecasts"].append(extra)
        projection = build_public_forecast_projection(dataset)
        self.assertNotIn("WS-FP-SYN-DRAFT-ELECTION", {row["forecast_id"] for row in projection["forecasts"]})

    def test_projection_is_deterministic_and_input_is_unchanged(self):
        before = hashlib.sha256(self.path.read_bytes()).hexdigest()
        first = build_public_forecast_projection(self.dataset)
        second = build_public_forecast_projection(self.dataset)
        self.assertEqual(first, second)
        self.assertEqual(
            json.dumps(first, sort_keys=True, separators=(",", ":")),
            json.dumps(second, sort_keys=True, separators=(",", ":")),
        )
        self.assertEqual(before, hashlib.sha256(self.path.read_bytes()).hexdigest())

    def test_duplicate_allowlist_row_cannot_silently_replace_reviewed_issuance(self):
        dataset = copy.deepcopy(self.dataset)
        duplicate = copy.deepcopy(dataset["forecasts"][0])
        duplicate["revision_id"] = "DUPLICATE"
        dataset["forecasts"].append(duplicate)
        with self.assertRaises(PublicForecastProjectionError):
            build_public_forecast_projection(dataset)


if __name__ == "__main__":
    unittest.main()
