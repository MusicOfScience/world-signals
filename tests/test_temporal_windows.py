from __future__ import annotations

import copy
import unittest

from src.world_signals.projection import public_projection
from src.world_signals.validation import validate_registry


def base_record() -> dict:
    return {
        "occurrence_id": "WSO-TEST-RISK-0001",
        "series_id": "WSER-TEST-RISK",
        "canonical_name": "Test seasonal risk window",
        "category": "PHYSICAL_CLIMATE_RISK",
        "region": "Oceania / Pacific",
        "institution": "Test Authority",
        "certainty_status": "CONFIRMED",
        "lifecycle_status": "PLANNED",
        "timing_type": "MONTH_BOUNDED_SEASON_WINDOW",
        "season_window_model": "MONTH_BOUNDED_SINGLE_PHASE",
        "start_local": None,
        "end_local": None,
        "start_utc": None,
        "end_utc": None,
        "date_earliest": None,
        "date_latest": None,
        "publication_datetime": None,
        "time_precision": "MONTH",
        "time_status": "NOT_APPLICABLE",
        "time_basis": "NOT_APPLICABLE",
        "source_native_window_label": "November–April",
        "season_phases": [
            {
                "phase_id": "PHASE_1",
                "start_month": "2026-11",
                "end_month": "2027-04",
                "boundary_precision": "MONTH",
                "source_label": "November–April",
            }
        ],
    }


def validate(record: dict):
    return validate_registry({"record_count": 1, "records": [record]})


class SeasonalWindowValidationTests(unittest.TestCase):
    def test_single_month_bounded_cross_year_phase_is_valid(self):
        report = validate(base_record())
        self.assertTrue(report.ok, report.errors)

    def test_month_bounded_window_rejects_wrong_window_model(self):
        record = base_record()
        record["season_window_model"] = "MONTH_BOUNDED_MULTI_PHASE"
        report = validate(record)
        self.assertFalse(report.ok)
        self.assertTrue(any("season_window_model" in error for error in report.errors))

    def test_month_bounded_window_rejects_synthetic_day_boundary(self):
        record = base_record()
        record["date_earliest"] = "2026-11-01"
        report = validate(record)
        self.assertFalse(report.ok)
        self.assertTrue(any("date_earliest" in error for error in report.errors))

    def test_month_bounded_window_rejects_clock_time_semantics(self):
        record = base_record()
        record["time_status"] = "CONFIRMED"
        record["time_basis"] = "EXPLICIT_SCHEDULE_TIME"
        report = validate(record)
        self.assertFalse(report.ok)
        self.assertTrue(any("time_status=NOT_APPLICABLE" in error for error in report.errors))
        self.assertTrue(any("time_basis=NOT_APPLICABLE" in error for error in report.errors))

    def test_month_bounded_window_rejects_malformed_month_token(self):
        record = base_record()
        record["season_phases"][0]["start_month"] = "2026-11-01"
        report = validate(record)
        self.assertFalse(report.ok)
        self.assertTrue(any("YYYY-MM" in error for error in report.errors))

    def test_multi_phase_window_preserves_noncontiguous_phases(self):
        record = base_record()
        record["timing_type"] = "MULTI_PHASE_SEASON_WINDOW"
        record["season_window_model"] = "MONTH_BOUNDED_MULTI_PHASE"
        record["region"] = "South Asia"
        record["source_native_window_label"] = "April–June and October–December"
        record["season_phases"] = [
            {
                "phase_id": "PHASE_1",
                "start_month": "2027-04",
                "end_month": "2027-06",
                "boundary_precision": "MONTH",
                "source_label": "April–June",
            },
            {
                "phase_id": "PHASE_2",
                "start_month": "2027-10",
                "end_month": "2027-12",
                "boundary_precision": "MONTH",
                "source_label": "October–December",
            },
        ]
        report = validate(record)
        self.assertTrue(report.ok, report.errors)

    def test_multi_phase_window_rejects_overlap(self):
        record = base_record()
        record["timing_type"] = "MULTI_PHASE_SEASON_WINDOW"
        record["season_window_model"] = "MONTH_BOUNDED_MULTI_PHASE"
        record["season_phases"] = [
            {
                "phase_id": "PHASE_1",
                "start_month": "2027-04",
                "end_month": "2027-06",
                "boundary_precision": "MONTH",
                "source_label": "April–June",
            },
            {
                "phase_id": "PHASE_2",
                "start_month": "2027-06",
                "end_month": "2027-12",
                "boundary_precision": "MONTH",
                "source_label": "June–December",
            },
        ]
        report = validate(record)
        self.assertFalse(report.ok)
        self.assertTrue(any("overlap" in error for error in report.errors))

    def test_multi_phase_window_rejects_adjacent_phases(self):
        record = base_record()
        record["timing_type"] = "MULTI_PHASE_SEASON_WINDOW"
        record["season_window_model"] = "MONTH_BOUNDED_MULTI_PHASE"
        record["season_phases"] = [
            {
                "phase_id": "PHASE_1",
                "start_month": "2027-04",
                "end_month": "2027-06",
                "boundary_precision": "MONTH",
                "source_label": "April–June",
            },
            {
                "phase_id": "PHASE_2",
                "start_month": "2027-07",
                "end_month": "2027-12",
                "boundary_precision": "MONTH",
                "source_label": "July–December",
            },
        ]
        report = validate(record)
        self.assertFalse(report.ok)
        self.assertTrue(any("adjacent phases" in error for error in report.errors))

    def test_projection_preserves_month_semantics_without_fabricating_dates(self):
        record = base_record()
        registry = {"version": "test", "reference_date": "2026-09-04", "records": [copy.deepcopy(record)]}
        projected = public_projection(registry, {"sources": []})["events"][0]
        self.assertEqual(projected["season_phases"], record["season_phases"])
        self.assertEqual(projected["season_window_model"], "MONTH_BOUNDED_SINGLE_PHASE")
        self.assertEqual(projected["source_native_window_label"], "November–April")
        self.assertIsNone(projected["date_earliest"])
        self.assertIsNone(projected["start_local"])


if __name__ == "__main__":
    unittest.main()
