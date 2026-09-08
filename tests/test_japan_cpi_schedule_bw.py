from __future__ import annotations

import copy
import unittest

from world_signals.adapters.base import AdapterError
from world_signals.adapters.japan_cpi_schedule import (
    JapanCPIReleaseRow,
    japan_cpi_schedule_allowed,
    parse_japan_cpi_schedule,
)
from world_signals.japan_cpi_monitor import japan_cpi_schedule_review_candidates


SAMPLE = b"""
<html><body><h1>Schedule of Release</h1><table>
<tr><th>Survey month</th><th>Date of release</th><th>Survey month</th><th>Date of release</th></tr>
<tr><td>December, 2025</td><td>January 23, 2026</td><td>January, 2026</td><td>January 30, 2026</td></tr>
<tr><td>January, 2026</td><td>February 20</td><td>February</td><td>February 27</td></tr>
<tr><td>February</td><td>March 24</td><td>March</td><td>March 31</td></tr>
<tr><td>March</td><td>April 24</td><td>April</td><td>May 1</td></tr>
<tr><td>April</td><td>May 22</td><td>May</td><td>May 29</td></tr>
<tr><td>May</td><td>June 19</td><td>June</td><td>June 26</td></tr>
<tr><td>June</td><td>July 24</td><td>July</td><td>July 31</td></tr>
<tr><td>July</td><td>August 21</td><td>August</td><td>August 28</td></tr>
<tr><td>August</td><td>September 18</td><td>September</td><td>October 2</td></tr>
<tr><td>September</td><td>October 23</td><td>October</td><td>October 30</td></tr>
<tr><td>October</td><td>November 20</td><td>November</td><td>November 27</td></tr>
<tr><td>November</td><td>December 18</td><td>December</td><td>December 25</td></tr>
<tr><td>December</td><td>January 22, 2027</td><td>January, 2027</td><td>January 29, 2027</td></tr>
<tr><td>January, 2027</td><td>February 19</td><td>February</td><td>February 26</td></tr>
<tr><td>February</td><td>March 19</td><td>March</td><td>March 26</td></tr>
</table></body></html>
"""


def config() -> dict:
    ids = [f"WSO-MAC-A-{n:04d}" for n in range(50, 57)]
    periods = [
        "August 2026",
        "September 2026",
        "October 2026",
        "November 2026",
        "December 2026",
        "January 2027",
        "February 2027",
    ]
    return {
        "adapter_id": "JAPAN_CPI_RELEASE_SCHEDULE",
        "source_id": "WSSRC-MAC-014",
        "canonical_schedule_source_id": "WSSRC-MAC-014",
        "same_source_identity_for_canonical_and_monitor": True,
        "canonical_occurrence_ids": ids,
        "identity_by_occurrence_id": {
            oid: {"series_id": "WSER-MAC-JP-CPI", "reference_period": period}
            for oid, period in zip(ids, periods)
        },
        "request_budget_per_run": 2,
        "robots_requests_per_run": 1,
        "schedule_requests_per_run": 1,
        "followup_requests_per_run": 0,
        "schedule_mutation_authority": False,
        "clock_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "canonical_clock_mutation_allowed": False,
        "automatic_tokyo_cpi_followup_allowed": False,
        "automatic_estat_api_followup_allowed": False,
        "automatic_data_release_followup_allowed": False,
        "automatic_pdf_fetch_allowed": False,
        "automatic_news_followup_allowed": False,
        "automatic_search_route_discovery_allowed": False,
        "automatic_commit_allowed": False,
    }


def records() -> list[dict]:
    dates = [
        ("August 2026", "2026-09-18T08:30:00", "2026-09-17T23:30:00Z"),
        ("September 2026", "2026-10-23T08:30:00", "2026-10-22T23:30:00Z"),
        ("October 2026", "2026-11-20T08:30:00", "2026-11-19T23:30:00Z"),
        ("November 2026", "2026-12-18T08:30:00", "2026-12-17T23:30:00Z"),
        ("December 2026", "2027-01-22T08:30:00", "2027-01-21T23:30:00Z"),
        ("January 2027", "2027-02-19T08:30:00", "2027-02-18T23:30:00Z"),
        ("February 2027", "2027-03-19T08:30:00", "2027-03-18T23:30:00Z"),
    ]
    out = []
    for number, (period, start_local, start_utc) in enumerate(dates, 50):
        out.append({
            "occurrence_id": f"WSO-MAC-A-{number:04d}",
            "series_id": "WSER-MAC-JP-CPI",
            "source_id": "WSSRC-MAC-014",
            "region": "East Asia",
            "source_timezone": "Asia/Tokyo",
            "reference_period": period,
            "start_local": start_local,
            "start_utc": start_utc,
            "time_precision": "MINUTE",
            "time_basis": "EXPLICIT_OCCURRENCE_TIME",
            "timing_type": "LOCAL_DATETIME",
            "all_day_semantics": False,
            "lifecycle_status": "PLANNED",
            "certainty_status": "CONFIRMED",
        })
    return out


class JapanCPIScheduleAdapterTests(unittest.TestCase):
    def test_parser_uses_national_columns_and_carries_year_anchors(self):
        rows = parse_japan_cpi_schedule(SAMPLE)
        by_period = {row.reference_period: row for row in rows}
        self.assertEqual(by_period["August 2026"].release_date, "2026-09-18")
        self.assertEqual(by_period["December 2026"].release_date, "2027-01-22")
        self.assertEqual(by_period["January 2027"].release_date, "2027-02-19")
        self.assertEqual(by_period["February 2027"].release_date, "2027-03-19")
        self.assertNotIn("September 2026 -> Tokyo", by_period)
        self.assertTrue(all(row.clock_exposed_by_schedule is False for row in rows))

    def test_parser_fails_on_bare_month_before_year_anchor(self):
        body = b"<h1>Schedule of Release</h1><table><tr><td>August</td><td>September 18</td></tr></table>"
        with self.assertRaises(AdapterError):
            parse_japan_cpi_schedule(body)

    def test_parser_fails_on_duplicate_national_reference_period(self):
        body = SAMPLE.replace(
            b"</table>",
            b"<tr><td>February</td><td>March 20</td><td>March</td><td>March 27</td></tr></table>",
        )
        with self.assertRaises(AdapterError):
            parse_japan_cpi_schedule(body)

    def test_parser_fails_on_malformed_release_date_for_valid_survey_row(self):
        body = SAMPLE.replace(b"<td>September 18</td>", b"<td>18 September</td>", 1)
        with self.assertRaises(AdapterError):
            parse_japan_cpi_schedule(body)

    def test_robots_policy_allows_registered_cpi_schedule(self):
        robots = "User-agent: *\nDisallow: /library/opac/\n"
        self.assertTrue(japan_cpi_schedule_allowed(robots))

    def test_robots_policy_disallow_is_respected(self):
        robots = "User-agent: *\nDisallow: /english/data/cpi/\n"
        self.assertFalse(japan_cpi_schedule_allowed(robots))

    def test_robots_non_policy_body_fails_closed(self):
        with self.assertRaises(AdapterError):
            japan_cpi_schedule_allowed("<html>request rejected</html>")


class JapanCPIMonitorTests(unittest.TestCase):
    def test_exact_schedule_matches_generate_no_review_candidates(self):
        candidates, observations = japan_cpi_schedule_review_candidates(
            records(), parse_japan_cpi_schedule(SAMPLE), config()
        )
        self.assertEqual(candidates, [])
        matches = [o for o in observations if o["type"] == "JAPAN_CPI_RELEASE_DATE_MATCH_OBSERVATION"]
        self.assertEqual(len(matches), 7)
        self.assertTrue(all(o["canonical_start_local_preserved"].endswith("T08:30:00") for o in matches))
        authority = observations[-1]
        self.assertFalse(authority["canonical_clock_mutation_allowed"])
        self.assertFalse(authority["lifecycle_mutation_allowed"])
        self.assertFalse(authority["certainty_mutation_allowed"])

    def test_date_change_generates_review_only_candidate_and_preserves_clock_fields(self):
        releases = parse_japan_cpi_schedule(SAMPLE)
        changed = [
            JapanCPIReleaseRow(
                reference_period=row.reference_period,
                survey_month_label=row.survey_month_label,
                release_date="2026-09-21" if row.reference_period == "August 2026" else row.release_date,
            )
            for row in releases
        ]
        candidates, _ = japan_cpi_schedule_review_candidates(records(), changed, config())
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["candidate_type"], "JAPAN_CPI_RELEASE_DATE_CHANGE_REVIEW")
        self.assertEqual(candidate["old_value"]["start_local"], "2026-09-18T08:30:00")
        self.assertEqual(candidate["new_value"]["observed_release_date"], "2026-09-21")
        self.assertFalse(candidate["canonical_clock_mutation_allowed"])
        self.assertFalse(candidate["schedule_mutation_authority"])
        self.assertFalse(candidate["automatic_commit_allowed"])

    def test_missing_row_is_review_evidence_not_event_state(self):
        releases = [row for row in parse_japan_cpi_schedule(SAMPLE) if row.reference_period != "October 2026"]
        candidates, observations = japan_cpi_schedule_review_candidates(records(), releases, config())
        missing = [c for c in candidates if c["candidate_type"] == "JAPAN_CPI_RELEASE_ROW_MISSING_REVIEW"]
        self.assertEqual(len(missing), 1)
        self.assertTrue(missing[0]["absence_is_not_cancellation_completion_delay_or_certainty_change"])
        self.assertEqual(missing[0]["event_state_inference"], "NONE")
        absent_obs = [o for o in observations if o["type"] == "JAPAN_CPI_RELEASE_CONFIGURED_ROW_ABSENT"]
        self.assertEqual(len(absent_obs), 1)

    def test_completed_missing_row_does_not_generate_candidate(self):
        canonical = records()
        canonical[2]["lifecycle_status"] = "COMPLETED"
        releases = [row for row in parse_japan_cpi_schedule(SAMPLE) if row.reference_period != "October 2026"]
        candidates, _ = japan_cpi_schedule_review_candidates(canonical, releases, config())
        self.assertEqual(candidates, [])

    def test_completed_matching_row_is_corroboration_only(self):
        canonical = records()
        canonical[0]["lifecycle_status"] = "COMPLETED"
        candidates, observations = japan_cpi_schedule_review_candidates(
            canonical, parse_japan_cpi_schedule(SAMPLE), config()
        )
        self.assertEqual(candidates, [])
        corroboration = [
            o for o in observations
            if o["type"] == "JAPAN_CPI_COMPLETED_OCCURRENCE_SCHEDULE_CORROBORATION_ONLY"
        ]
        self.assertEqual(len(corroboration), 1)

    def test_outside_scope_rows_are_observed_not_added(self):
        candidates, observations = japan_cpi_schedule_review_candidates(
            records(), parse_japan_cpi_schedule(SAMPLE), config()
        )
        self.assertEqual(candidates, [])
        outside = [
            o for o in observations
            if o["type"] == "JAPAN_CPI_OUTSIDE_CONFIGURED_REFERENCE_PERIOD_OBSERVATION"
        ][0]
        self.assertGreater(outside["outside_configured_reference_period_count"], 0)
        self.assertFalse(outside["automatic_canonical_addition_allowed"])

    def test_duplicate_observed_identity_fails_closed(self):
        releases = parse_japan_cpi_schedule(SAMPLE)
        with self.assertRaises(ValueError):
            japan_cpi_schedule_review_candidates(records(), releases + [releases[-1]], config())

    def test_gate_drift_fails_closed(self):
        cfg = config()
        cfg["clock_authority"] = True
        with self.assertRaises(ValueError):
            japan_cpi_schedule_review_candidates(records(), parse_japan_cpi_schedule(SAMPLE), cfg)

    def test_canonical_clock_shape_drift_fails_closed_without_deriving_replacement(self):
        canonical = records()
        canonical[0]["start_local"] = "2026-09-18"
        with self.assertRaises(ValueError):
            japan_cpi_schedule_review_candidates(canonical, parse_japan_cpi_schedule(SAMPLE), config())

    def test_comparator_does_not_mutate_inputs(self):
        canonical = records()
        releases = parse_japan_cpi_schedule(SAMPLE)
        cfg = config()
        before = (copy.deepcopy(canonical), copy.deepcopy(releases), copy.deepcopy(cfg))
        japan_cpi_schedule_review_candidates(canonical, releases, cfg)
        self.assertEqual(canonical, before[0])
        self.assertEqual(releases, before[1])
        self.assertEqual(cfg, before[2])


if __name__ == "__main__":
    unittest.main()
