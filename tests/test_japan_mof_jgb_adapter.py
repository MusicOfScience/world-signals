from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.adapters import (
    AdapterError,
    JAPAN_MOF_JGB_CALENDAR_INDEX,
    JAPAN_MOF_TIMEZONE,
    jgb_monthly_calendar_url,
    parse_jgb_monthly_auction_calendar_html,
)


HTML = b'''<!doctype html><html><body>
<h1>Auction Calendar September 2026</h1>
<h2>(1) Government Bonds and Treasury Discount Bills</h2>
<table>
<tr><th>Auction Date</th><th>Issue</th><th>Auction Announcement</th><th>Auction Result</th><th>Non-price-competitive Auction II</th></tr>
<tr><td>Sep. 1, 2026</td><td>10-year(383)</td><td>Detail</td><td>Detail</td><td>Detail</td></tr>
<tr><td>Sep. 3, 2026</td><td>30-year(91)</td><td>Detail</td><td>Detail</td><td>Detail</td></tr>
<tr><td>Sep. 8, 2026</td><td>5-year</td><td>Detail</td><td>Detail</td><td>Detail</td></tr>
<tr><td>Sep. 10, 2026</td><td>Liquidity Enhancement Auction (remaining maturities of 1-5 years)</td><td>Detail</td><td>Detail</td><td>-</td></tr>
<tr><td>Sep. 11, 2026</td><td>Treasury Discount Bills (3-month)(1406)</td><td>Detail</td><td>Detail</td><td>-</td></tr>
</table>
<h2>(2) Borrowing</h2>
<table>
<tr><th>Auction Date</th><th>Borrowing Date</th><th>Issue</th></tr>
<tr><td>Sep. 3, 2026</td><td>Sep. 11, 2026</td><td>Borrowing of Special Account</td></tr>
</table>
<p>The above calendar may be changed or added in light of changes in circumstances.</p>
</body></html>'''


class JapanMOFJGBAdapterTests(unittest.TestCase):
    def test_month_url_and_index_are_official_mof_routes(self):
        self.assertEqual(
            JAPAN_MOF_JGB_CALENDAR_INDEX,
            "https://www.mof.go.jp/english/policy/jgbs/auction/calendar/index.htm",
        )
        self.assertEqual(
            jgb_monthly_calendar_url(2026, 9),
            "https://www.mof.go.jp/english/policy/jgbs/auction/calendar/2609e.htm",
        )

    def test_parses_government_bond_table_without_borrowing_rows(self):
        schedule = parse_jgb_monthly_auction_calendar_html(HTML)
        self.assertEqual(schedule.year, 2026)
        self.assertEqual(schedule.month, 9)
        self.assertEqual(schedule.source_timezone, JAPAN_MOF_TIMEZONE)
        self.assertEqual(schedule.time_precision, "CIVIL_DATE")
        self.assertEqual(len(schedule.entries), 5)
        self.assertEqual(schedule.entries[0].auction_date, "2026-09-01")
        self.assertEqual(schedule.entries[1].issue, "30-year(91)")
        self.assertNotIn("Borrowing", " ".join(row.issue for row in schedule.entries))
        self.assertEqual(len(schedule.schedule_sha256), 64)

    def test_hash_ignores_result_and_link_markup_but_tracks_schedule_semantics(self):
        result_variant = HTML.replace(b"<td>Detail</td>", b"<td><a href='/result'>Result now</a></td>")
        baseline = parse_jgb_monthly_auction_calendar_html(HTML).schedule_sha256
        self.assertEqual(
            baseline,
            parse_jgb_monthly_auction_calendar_html(result_variant).schedule_sha256,
        )
        date_variant = HTML.replace(b"Sep. 8, 2026", b"Sep. 9, 2026", 1)
        self.assertNotEqual(
            baseline,
            parse_jgb_monthly_auction_calendar_html(date_variant).schedule_sha256,
        )

    def test_missing_government_bond_table_fails_closed(self):
        broken = HTML.replace(b"Auction Result", b"Outcome link")
        with self.assertRaises(AdapterError):
            parse_jgb_monthly_auction_calendar_html(broken)

    def test_row_outside_heading_month_fails_closed(self):
        broken = HTML.replace(b"Sep. 11, 2026", b"Oct. 11, 2026", 1)
        with self.assertRaises(AdapterError):
            parse_jgb_monthly_auction_calendar_html(broken)

    def test_bi_does_not_activate_a_production_monitor_route_or_rights(self):
        expectations = json.loads((ROOT / "data/monitor/expectations.json").read_text())
        self.assertNotIn(
            "JAPAN_MOF_JGB_AUCTION_CALENDAR",
            {row["adapter_id"] for row in expectations["adapters"]},
        )
        sources = json.loads((ROOT / "data/sources/registry.json").read_text())
        source = next(row for row in sources["sources"] if row["source_id"] == "WSSRC-FIS-007")
        self.assertEqual(source["automated_monitoring_use"], "ENDPOINT_REVIEW_REQUIRED")
        self.assertEqual(source["verification_mode"], "AUTOMATED_PILOT")
        self.assertFalse(expectations["automatic_canonical_commit"])
        self.assertFalse(expectations["google_calendar_write"])


if __name__ == "__main__":
    unittest.main()
