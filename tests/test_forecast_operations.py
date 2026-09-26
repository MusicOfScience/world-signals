import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.forecast_operations import (
    build_watch_manifest,
    next_review_trigger,
    operational_state,
    validate_operations_policy,
)


class ForecastOperationsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.forecasts = json.loads((ROOT / "data/forecasts/forecasts.json").read_text())
        cls.outcomes = json.loads((ROOT / "data/outcomes/outcomes.json").read_text())
        cls.policy = json.loads((ROOT / "data/forecasts/operations_policy.json").read_text())

    def test_policy_is_explicitly_read_only(self):
        self.assertEqual(validate_operations_policy(self.policy), ())

    def test_all_four_production_issuances_appear(self):
        manifest = build_watch_manifest(self.forecasts, self.outcomes, "2026-09-27T00:00:00Z")
        self.assertEqual(manifest["forecast_count"], 4)
        self.assertEqual({item["issuance_id"] for item in manifest["items"]}, {
            "WS-FP-RBA-20261103-I1", "WS-FP-BOC-20261028-I1",
            "WS-FP-ECB-20261029-I1", "WS-FP-FED-20261028-I1",
        })
        self.assertTrue(all(item["operational_state"] == "OPEN_NOT_DUE" for item in manifest["items"]))

    def test_cutoffs_and_resolution_contract_are_projected_unchanged(self):
        manifest = build_watch_manifest(self.forecasts, self.outcomes, "2026-09-27T00:00:00Z")
        original = {row["issuance_id"]: row for row in self.forecasts["forecasts"]}
        for item in manifest["items"]:
            row = original[item["issuance_id"]]
            self.assertEqual(item["information_cutoff_at_utc"], row["information_cutoff_at_utc"])
            self.assertEqual(item["resolution_source_ids"], row["resolution"]["resolution_source_ids"])
            self.assertEqual(item["resolution_window_start_at_utc"], row["resolution"]["window_start_at_utc"])

    def test_review_window_due_and_overdue_states_are_deterministic(self):
        forecast = self.forecasts["forecasts"][0]
        start = forecast["resolution"]["window_start_at_utc"]
        self.assertEqual(operational_state(forecast, "2026-10-27T03:30:00Z"), "OPEN_REVIEW_WINDOW")
        self.assertEqual(operational_state(forecast, start), "RESOLUTION_DUE")
        self.assertEqual(operational_state(forecast, "2026-11-04T03:30:00Z"), "OVERDUE_REVIEW")
        self.assertEqual(next_review_trigger(forecast, "OPEN_NOT_DUE"), "2026-10-27T03:30:00Z")

    def test_terminal_outcomes_propagate_without_mutating_forecast(self):
        forecast = copy.deepcopy(self.forecasts["forecasts"][0])
        before = json.dumps(forecast, sort_keys=True)
        for status in ("RESOLVED", "VOID", "UNRESOLVABLE", "DISPUTED"):
            outcome = {"forecast_id": forecast["forecast_id"], "outcome_id": "OUT-1", "resolution_status": status, "revision_number": 1}
            self.assertEqual(operational_state(forecast, "2027-01-01T00:00:00Z", outcome), status)
        self.assertEqual(json.dumps(forecast, sort_keys=True), before)

    def test_future_outcome_revision_does_not_change_as_of_watch(self):
        outcomes = {"outcomes": [{
            "forecast_id": "WS-FP-RBA-20261103",
            "outcome_id": "WS-OUT-RBA-20261103",
            "resolution_status": "RESOLVED",
            "revision_number": 1,
            "world_signals_reviewed_at_utc": "2026-11-04T00:00:00Z",
        }]}
        manifest = build_watch_manifest(self.forecasts, outcomes, "2026-09-27T00:00:00Z")
        rba = next(item for item in manifest["items"] if item["forecast_id"] == "WS-FP-RBA-20261103")
        self.assertEqual(rba["operational_state"], "OPEN_NOT_DUE")
        self.assertIsNone(rba["outcome_id"])

    def test_authoritative_evidence_only_changes_operational_state(self):
        forecast = self.forecasts["forecasts"][0]
        self.assertEqual(operational_state(forecast, forecast["resolution"]["window_start_at_utc"], authoritative_evidence_available=True), "AWAITING_RESOLUTION")

    def test_later_issuance_does_not_replace_earlier_issuance(self):
        forecasts = copy.deepcopy(self.forecasts)
        later = copy.deepcopy(forecasts["forecasts"][0])
        later["issuance_id"] = "WS-FP-RBA-20261103-I2"
        later["issuance_number"] = 2
        forecasts["forecasts"].append(later)
        manifest = build_watch_manifest(forecasts, self.outcomes, "2026-09-27T00:00:00Z")
        items = [item for item in manifest["items"] if item["forecast_id"] == "WS-FP-RBA-20261103"]
        self.assertEqual({item["issuance_id"] for item in items}, {"WS-FP-RBA-20261103-I1", "WS-FP-RBA-20261103-I2"})
        self.assertEqual(items[0]["later_issuance_ids"], ["WS-FP-RBA-20261103-I2"])
        self.assertTrue(items[1]["is_latest_issuance"])

    def test_operations_helper_has_no_write_or_score_surface(self):
        manifest = build_watch_manifest(self.forecasts, self.outcomes, "2026-09-27T00:00:00Z")
        self.assertFalse(manifest["writes_allowed"])
        self.assertFalse(manifest["evaluation_allowed"])
        self.assertNotIn("score", manifest)

    def test_invalid_timestamp_fails_without_writes(self):
        with self.assertRaises(ValueError):
            build_watch_manifest(self.forecasts, self.outcomes, "not-a-time")


if __name__ == "__main__":
    unittest.main()
