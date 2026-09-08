from __future__ import annotations

import json
from pathlib import Path
import unittest

from src.world_signals.adapters.base import AdapterError
from src.world_signals.adapters.fomc import (
    FOMC_MEETING_CALENDAR_URL,
    FOMC_OPERATIONAL_CALENDAR_TEMPLATE,
    FOMC_SERIES_BY_KIND,
    FOMC_TIMEZONE,
    fomc_operational_calendar_url,
    parse_fomc_meeting_calendar_html,
    parse_fomc_operational_calendar_html,
    validate_fomc_schedule_alignment,
)

ROOT = Path(__file__).resolve().parents[1]

MEETING_FIXTURE = """
<html><body>
<p>The minutes of regularly scheduled meetings are released three weeks after the date of the policy decision.</p>
<h4>2026 FOMC Meetings</h4>
<h5>January</h5><div>27-28</div><div>Statement:</div><div>Minutes:</div><div>(Released February 18, 2026)</div>
<h5>September</h5><div>15-16*</div>
<h5>October</h5><div>27-28</div>
<h5>December</h5><div>8-9*</div>
<h4>2025 FOMC Meetings</h4><h5>January</h5><div>28-29</div>
<h4>2027 FOMC Meetings</h4>
<h5>January</h5><div>26-27</div>
<h5>March</h5><div>16-17*</div>
<h5>April</h5><div>27-28</div>
<h5>June</h5><div>8-9*</div>
<h5>July</h5><div>27-28</div>
<h5>September</h5><div>14-15*</div>
<h5>October</h5><div>26-27</div>
<h5>December</h5><div>7-8*</div>
<p>Note: A two-day meeting is scheduled for January 25-26, 2028. Each meeting date is tentative until confirmed at the meeting immediately preceding it.</p>
</body></html>
"""

SEPTEMBER_FIXTURE = """
<html><body><h4>September 2026</h4>
<h4>FOMC Meetings</h4><div>Time:</div><div>Release Date(s):</div>
<div>2:30 p.m.</div><a>FOMC Press Conference</a><div>16</div>
<div>2:00 p.m.</div><div>FOMC Meeting</div><div>Two-day meeting, September 15 - 16</div><div>Press Conference</div><div>16</div>
<h4>Beige Book</h4><div>9:99 p.m.</div><div>irrelevant</div>
</body></html>
"""

OCTOBER_FIXTURE = """
<html><body><h4>October 2026</h4>
<h4>FOMC Meetings</h4><div>Time:</div><div>Release Date(s):</div>
<div>2:00 p.m.</div><div>FOMC Minutes</div><div>Meeting of September 15-16</div><div>7</div>
<div>2:30 p.m.</div><a>FOMC Press Conference</a><div>28</div>
<div>2:00 p.m.</div><div>FOMC Meeting</div><div>Two-day meeting, October 27 - 28</div><div>Press Conference</div><div>28</div>
<h4>Beige Book</h4>
</body></html>
"""

JANUARY_FIXTURE = """
<html><body><h4>January 2027</h4>
<h4>FOMC Meetings</h4><div>Time:</div><div>Release Date(s):</div>
<div>2:00 p.m.</div><div>FOMC Minutes</div><div>Meeting of December 8-9</div><div>6</div>
<h4>Beige Book</h4>
</body></html>
"""


class FOMCAdapterBMTests(unittest.TestCase):
    def test_official_routes_timezone_and_series_are_frozen(self):
        self.assertEqual(
            FOMC_MEETING_CALENDAR_URL,
            "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
        )
        self.assertEqual(
            FOMC_OPERATIONAL_CALENDAR_TEMPLATE,
            "https://www.federalreserve.gov/newsevents/{year}-{month}.htm",
        )
        self.assertEqual(fomc_operational_calendar_url(2026, 9), "https://www.federalreserve.gov/newsevents/2026-september.htm")
        self.assertEqual(FOMC_TIMEZONE, "America/New_York")
        self.assertEqual(
            set(FOMC_SERIES_BY_KIND.values()),
            {
                "WS.CB.FED.FOMC_MEETING_WINDOW",
                "WS.CB.FED.FOMC_POLICY_DECISION",
                "WS.CB.FED.FOMC_PRESS_CONFERENCE",
                "WS.CB.FED.FOMC_MINUTES",
            },
        )

    def test_meeting_calendar_preserves_windows_sep_marker_and_tentative_note(self):
        calendar = parse_fomc_meeting_calendar_html(MEETING_FIXTURE, years=(2026, 2027))
        rows = {(x.start_date, x.end_date): x for x in calendar.windows}
        self.assertEqual(len(rows), 12)
        self.assertIn(("2026-09-15", "2026-09-16"), rows)
        self.assertTrue(rows[("2026-09-15", "2026-09-16")].sep_associated)
        self.assertFalse(rows[("2026-10-27", "2026-10-28")].sep_associated)
        self.assertTrue(calendar.future_dates_tentative_note_present)
        self.assertIn("three weeks", calendar.minutes_release_rule.lower())
        self.assertTrue(all(row.source_timezone == "America/New_York" for row in calendar.windows))
        self.assertTrue(all(row.time_precision == "DATE_RANGE" for row in calendar.windows))

    def test_meeting_rule_does_not_manufacture_minutes_events_or_clocks(self):
        calendar = parse_fomc_meeting_calendar_html(MEETING_FIXTURE, years=(2027,))
        self.assertEqual(len(calendar.windows), 8)
        self.assertFalse(any(hasattr(row, "start_local") for row in calendar.windows))
        self.assertIsNotNone(calendar.minutes_release_rule)

    def test_monthly_calendar_keeps_decision_and_press_separate(self):
        calendar = parse_fomc_operational_calendar_html(SEPTEMBER_FIXTURE)
        by_kind = {row.event_kind: row for row in calendar.events}
        self.assertEqual(set(by_kind), {"DECISION", "PRESS_CONFERENCE"})
        self.assertEqual(by_kind["DECISION"].start_local, "2026-09-16T14:00:00")
        self.assertEqual(by_kind["PRESS_CONFERENCE"].start_local, "2026-09-16T14:30:00")
        self.assertEqual(by_kind["DECISION"].related_meeting_start_date, "2026-09-15")
        self.assertEqual(by_kind["DECISION"].related_meeting_end_date, "2026-09-16")
        self.assertNotEqual(by_kind["DECISION"].start_local, by_kind["PRESS_CONFERENCE"].start_local)

    def test_monthly_calendar_parses_minutes_as_a_separate_publication(self):
        calendar = parse_fomc_operational_calendar_html(OCTOBER_FIXTURE)
        by_kind = {row.event_kind: row for row in calendar.events}
        self.assertEqual(set(by_kind), {"DECISION", "PRESS_CONFERENCE", "MINUTES"})
        self.assertEqual(by_kind["MINUTES"].start_local, "2026-10-07T14:00:00")
        self.assertEqual(by_kind["MINUTES"].related_meeting_end_date, "2026-09-16")
        self.assertEqual(by_kind["DECISION"].start_local, "2026-10-28T14:00:00")
        self.assertEqual(by_kind["PRESS_CONFERENCE"].start_local, "2026-10-28T14:30:00")

    def test_january_minutes_roll_back_only_to_prior_december(self):
        calendar = parse_fomc_operational_calendar_html(JANUARY_FIXTURE)
        minute = next(row for row in calendar.events if row.event_kind == "MINUTES")
        self.assertEqual(minute.start_local, "2027-01-06T14:00:00")
        self.assertEqual(minute.related_meeting_start_date, "2026-12-08")
        self.assertEqual(minute.related_meeting_end_date, "2026-12-09")
        impossible = OCTOBER_FIXTURE.replace("Meeting of September 15-16", "Meeting of December 8-9")
        with self.assertRaises(AdapterError):
            parse_fomc_operational_calendar_html(impossible)

    def test_alignment_requires_distinct_decision_press_and_known_window(self):
        meetings = parse_fomc_meeting_calendar_html(MEETING_FIXTURE, years=(2026, 2027))
        september = parse_fomc_operational_calendar_html(SEPTEMBER_FIXTURE)
        october = parse_fomc_operational_calendar_html(OCTOBER_FIXTURE)
        validate_fomc_schedule_alignment(meetings, (september, october))
        broken = SEPTEMBER_FIXTURE.replace("2:30 p.m.", "2:00 p.m.")
        with self.assertRaises(AdapterError):
            validate_fomc_schedule_alignment(
                meetings,
                (parse_fomc_operational_calendar_html(broken),),
            )

    def test_missing_duplicate_or_ambiguous_fomc_rows_fail_closed(self):
        with self.assertRaises(AdapterError):
            parse_fomc_meeting_calendar_html("<h4>2026 FOMC Meetings</h4><h5>September</h5><div>15-16*</div><h5>September</h5><div>15-16*</div>", years=(2026,))
        with self.assertRaises(AdapterError):
            parse_fomc_operational_calendar_html(SEPTEMBER_FIXTURE.replace("FOMC Press Conference", "Press briefing"))
        duplicate = SEPTEMBER_FIXTURE.replace("<h4>Beige Book</h4>", "<div>2:00 p.m.</div><div>FOMC Meeting</div><div>Two-day meeting, September 15 - 16</div><h4>Beige Book</h4>")
        with self.assertRaises(AdapterError):
            parse_fomc_operational_calendar_html(duplicate)

    def test_semantic_hash_ignores_irrelevant_markup_but_tracks_schedule(self):
        a = parse_fomc_meeting_calendar_html(MEETING_FIXTURE, years=(2026, 2027))
        cosmetic = MEETING_FIXTURE.replace("<body>", "<body><div>decorative navigation only</div>")
        b = parse_fomc_meeting_calendar_html(cosmetic, years=(2026, 2027))
        changed = MEETING_FIXTURE.replace("15-16*", "16-17*", 1)
        c = parse_fomc_meeting_calendar_html(changed, years=(2026, 2027))
        self.assertEqual(a.schedule_sha256, b.schedule_sha256)
        self.assertNotEqual(a.schedule_sha256, c.schedule_sha256)

        op_a = parse_fomc_operational_calendar_html(SEPTEMBER_FIXTURE)
        op_b = parse_fomc_operational_calendar_html(SEPTEMBER_FIXTURE.replace("irrelevant", "different irrelevant prose"))
        op_c = parse_fomc_operational_calendar_html(SEPTEMBER_FIXTURE.replace("2:30 p.m.", "2:45 p.m."))
        self.assertEqual(op_a.schedule_sha256, op_b.schedule_sha256)
        self.assertNotEqual(op_a.schedule_sha256, op_c.schedule_sha256)

    def test_live_repository_preserves_readiness_only_boundary(self):
        canonical = json.loads((ROOT / "data/canonical/registry.json").read_text())
        sources = json.loads((ROOT / "data/sources/registry.json").read_text())
        expectations = json.loads((ROOT / "data/monitor/expectations.json").read_text())
        rows = [row for row in canonical["records"] if row.get("source_id") == "WSSRC-CB-001"]
        self.assertEqual(len(rows), 44)
        self.assertEqual(
            {row["series_id"] for row in rows},
            set(FOMC_SERIES_BY_KIND.values()),
        )
        self.assertEqual({row.get("source_timezone") for row in rows}, {"America/New_York"})
        self.assertEqual(sum(row.get("time_precision") == "DATE_RANGE" for row in rows), 11)
        self.assertEqual(sum(row.get("time_precision") == "MINUTE" for row in rows), 33)
        source = next(row for row in sources["sources"] if row["source_id"] == "WSSRC-CB-001")
        self.assertEqual(source["automated_monitoring_use"], "ENDPOINT_REVIEW_REQUIRED")
        self.assertEqual(source["verification_mode"], "AUTOMATED_PILOT")
        self.assertFalse(any(row.get("source_id") == "WSSRC-CB-001" for row in expectations["adapters"]))
        self.assertFalse(expectations["automatic_canonical_commit"])
        self.assertFalse(expectations["google_calendar_write"])
        if sources["version"] == "1.85":
            self.assertEqual(source["parser_version"], "fomc-calendar-rule-0.1")
        else:
            self.assertGreaterEqual(tuple(map(int, sources["version"].split("."))), (1, 86))
            self.assertEqual(source["parser_version"], "fomc-schedule-readiness-0.2")
            self.assertEqual(source["monitoring_activation_status"], "ENDPOINT_PERMISSION_HOLD_NO_PRODUCTION_ROUTE")


if __name__ == "__main__":
    unittest.main()
