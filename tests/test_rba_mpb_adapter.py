from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.adapters import (
    AdapterError,
    RBA_BOARD_SCHEDULE_URL,
    RBA_MPB_CALENDAR_URL,
    RBA_SERIES_BY_KIND,
    RBA_TIMEZONE,
    parse_rba_board_schedule_html,
    parse_rba_monetary_policy_calendar_html,
    validate_rba_calendar_alignment,
)


CALENDAR_HTML = b'''<!doctype html><html><body>
<h2>September 2026</h2>
<h4>Monetary Policy Board Meeting</h4>
<p>Monetary Policy Decision</p>
<p>28 September 2026&ndash;29 September 2026</p>
<h4>Monetary Policy Decision Statement</h4>
<p>Media Release</p>
<p>29 September 2026 2.30 pm AEST</p>
<h4>Monetary Policy Decision</h4>
<p>Media conference</p><p>Audio 40MB</p>
<p>29 September 2026 3.30 pm AEST</p>
<h2>October 2026</h2>
<h4>Minutes of the September 2026 Monetary Policy Board Meeting</h4>
<p>13 October 2026 11.30 am AEDT</p>
<h2>November 2026</h2>
<h4>Monetary Policy Board Meeting</h4>
<p>Monetary Policy Decision</p>
<p>2&ndash;3 November 2026</p>
<h4>Monetary Policy Decision Statement</h4>
<p>Media Release</p><p>3 November 2026 2.30 pm AEDT</p>
<h4>Statement on Monetary Policy</h4><p>3 November 2026 2.30 pm AEDT</p>
<h4>Monetary Policy Decision</h4><p>Media conference</p><p>3 November 2026 3.30 pm AEDT</p>
</body></html>'''

BOARD_HTML = b'''<!doctype html><html><body>
<table>
<caption>Board meeting schedules 2026</caption>
<tr><th>Month</th><th>Monetary Policy Board</th><th>Payments System Board</th></tr>
<tr><td>August</td><td>10&ndash;11 August</td><td>27 August</td></tr>
<tr><td>September</td><td>28&ndash;29 September</td><td></td></tr>
<tr><td>November</td><td>2&ndash;3 November</td><td>19 November</td></tr>
<tr><td>December</td><td>7&ndash;8 December</td><td></td></tr>
</table>
<table>
<caption>Board meeting schedules 2027</caption>
<tr><th>Month</th><th>Monetary Policy Board</th><th>Payments System Board</th></tr>
<tr><td>February</td><td>8&ndash;9 February</td><td>24 February</td></tr>
</table>
</body></html>'''


def _version_tuple(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in str(value).split("."))


class RBAMPBAdapterTests(unittest.TestCase):
    def test_official_routes_and_source_native_timezone_are_frozen(self):
        self.assertEqual(
            RBA_MPB_CALENDAR_URL,
            "https://www.rba.gov.au/schedules-events/calendar/?topics=monetary-policy-board",
        )
        self.assertEqual(
            RBA_BOARD_SCHEDULE_URL,
            "https://www.rba.gov.au/schedules-events/board-meeting-schedules.html",
        )
        self.assertEqual(RBA_TIMEZONE, "Australia/Sydney")
        self.assertEqual(
            RBA_SERIES_BY_KIND,
            {
                "MEETING_WINDOW": "WS.CB.RBA.MPB_MEETING_WINDOW",
                "DECISION_STATEMENT": "WS.CB.RBA.MONETARY_POLICY_DECISION",
                "PRESS_CONFERENCE": "WS.CB.RBA.MPB_PRESS_CONFERENCE",
                "MINUTES": "WS.CB.RBA.MPB_MINUTES",
            },
        )

    def test_meeting_window_decision_and_press_conference_remain_distinct(self):
        calendar = parse_rba_monetary_policy_calendar_html(CALENDAR_HTML)
        sep = [event for event in calendar.events if event.start_local.startswith("2026-09")]
        self.assertEqual({event.event_kind for event in sep}, {"MEETING_WINDOW", "DECISION_STATEMENT", "PRESS_CONFERENCE"})
        meeting = next(event for event in sep if event.event_kind == "MEETING_WINDOW")
        decision = next(event for event in sep if event.event_kind == "DECISION_STATEMENT")
        conference = next(event for event in sep if event.event_kind == "PRESS_CONFERENCE")
        self.assertEqual(meeting.start_local, "2026-09-28")
        self.assertEqual(meeting.end_local, "2026-09-29")
        self.assertEqual(meeting.time_precision, "CIVIL_DATE_RANGE")
        self.assertEqual(decision.start_local, "2026-09-29T14:30:00")
        self.assertEqual(decision.published_timezone_label, "AEST")
        self.assertEqual(conference.start_local, "2026-09-29T15:30:00")
        self.assertEqual(conference.published_timezone_label, "AEST")
        self.assertNotEqual(meeting.start_local, decision.start_local)
        self.assertNotEqual(decision.start_local, conference.start_local)

    def test_minutes_and_daylight_label_are_preserved_separately(self):
        calendar = parse_rba_monetary_policy_calendar_html(CALENDAR_HTML)
        minutes = next(event for event in calendar.events if event.event_kind == "MINUTES")
        november_decision = next(
            event for event in calendar.events
            if event.event_kind == "DECISION_STATEMENT" and event.start_local.startswith("2026-11")
        )
        self.assertEqual(minutes.start_local, "2026-10-13T11:30:00")
        self.assertEqual(minutes.published_timezone_label, "AEDT")
        self.assertEqual(november_decision.start_local, "2026-11-03T14:30:00")
        self.assertEqual(november_decision.published_timezone_label, "AEDT")
        self.assertTrue(all(event.source_timezone == "Australia/Sydney" for event in calendar.events))

    def test_board_schedule_cross_checks_topic_calendar_without_collapsing_events(self):
        calendar = parse_rba_monetary_policy_calendar_html(CALENDAR_HTML)
        windows = parse_rba_board_schedule_html(BOARD_HTML)
        self.assertIn(("2026-09-28", "2026-09-29"), {(row.start_local, row.end_local) for row in windows})
        validate_rba_calendar_alignment(calendar, windows)

    def test_semantic_hash_ignores_audio_metadata_but_tracks_decision_time(self):
        baseline = parse_rba_monetary_policy_calendar_html(CALENDAR_HTML).schedule_sha256
        audio_variant = CALENDAR_HTML.replace(b"Audio 40MB", b"Audio 43.7MB")
        self.assertEqual(baseline, parse_rba_monetary_policy_calendar_html(audio_variant).schedule_sha256)
        time_variant = CALENDAR_HTML.replace(b"29 September 2026 2.30 pm AEST", b"29 September 2026 2.45 pm AEST", 1)
        self.assertNotEqual(baseline, parse_rba_monetary_policy_calendar_html(time_variant).schedule_sha256)

    def test_missing_separate_press_conference_fails_alignment(self):
        broken = CALENDAR_HTML.replace(
            b"<h4>Monetary Policy Decision</h4>\n<p>Media conference</p><p>Audio 40MB</p>\n<p>29 September 2026 3.30 pm AEST</p>",
            b"",
            1,
        )
        calendar = parse_rba_monetary_policy_calendar_html(broken)
        windows = parse_rba_board_schedule_html(BOARD_HTML)
        with self.assertRaises(AdapterError):
            validate_rba_calendar_alignment(calendar, windows)

    def test_bj_checkpoint_or_later_reviewed_activation_is_safe(self):
        expectations = json.loads((ROOT / "data/monitor/expectations.json").read_text())
        sources = json.loads((ROOT / "data/sources/registry.json").read_text())
        adapter_ids = {row["adapter_id"] for row in expectations["adapters"]}
        source = next(row for row in sources["sources"] if row["source_id"] == "WSSRC-CB-002")

        # BJ's exact reviewed checkpoint was Monitor v0.10 / 8 with no RBA MPB
        # production route and endpoint review still required. That state must
        # remain provable, but it is not a permanent ceiling on a later tranche.
        self.assertGreaterEqual(_version_tuple(expectations["version"]), (0, 10))
        self.assertGreaterEqual(len(expectations["adapters"]), 8)
        self.assertEqual(source["canonical_provenance_use"], "CLEARED_CURATED_FACTUAL_METADATA")
        self.assertEqual(source["verification_mode"], "AUTOMATED_PILOT")

        if expectations["version"] == "0.10":
            self.assertEqual(len(expectations["adapters"]), 8)
            self.assertNotIn("RBA_MPB_CALENDAR", adapter_ids)
            self.assertEqual(source["automated_monitoring_use"], "ENDPOINT_REVIEW_REQUIRED")
        elif "RBA_MPB_CALENDAR" not in adapter_ids:
            self.assertEqual(source["automated_monitoring_use"], "ENDPOINT_REVIEW_REQUIRED")
        else:
            route = next(row for row in expectations["adapters"] if row["adapter_id"] == "RBA_MPB_CALENDAR")
            self.assertGreaterEqual(_version_tuple(expectations["version"]), (0, 13))
            self.assertEqual(source["automated_monitoring_use"], "CLEARED")
            self.assertEqual(
                source["automated_retrieval_permission"],
                "CLEARED_BOUNDED_ROBOTS_CONFORMANT_LOW_RATE_SCHEDULE_PATHS",
            )
            self.assertEqual(route["cadence"], "DAILY")
            self.assertEqual(route["request_budget_per_run"], 3)
            self.assertEqual(route["robots_policy"], "FETCH_FIRST_FAIL_CLOSED_IF_SCHEDULE_PATH_DISALLOWED")
            self.assertEqual(len(route["canonical_occurrence_ids"]), 44)
            self.assertEqual(
                route["canonical_source_role_contract"]["WS.CB.RBA.MPB_MINUTES"],
                "WSSRC-CB-013",
            )
            self.assertFalse(route["automatic_commit_allowed"])

        self.assertFalse(expectations["automatic_canonical_commit"])
        self.assertFalse(expectations["google_calendar_write"])
        self.assertTrue(all(not row.get("automatic_commit_allowed", False) for row in expectations["adapters"]))


if __name__ == "__main__":
    unittest.main()
