from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from world_signals.adapters import AdapterError, parse_eia_wpsr_schedule_html


HTML=b'''<!doctype html><html><body>
<p>The wpsrsummary.pdf, overview.pdf, and Tables 1-14 in CSV and XLS formats,
are released to the web site after <strong>10:30 a.m.</strong> eastern time on Wednesday.
All other PDF and HTML files are released after 1:00 p.m.</p>
<table>
<tr><th>Data for the week ending</th><th>Alternate release date</th><th>Release day</th><th>Release time</th><th>Holiday</th></tr>
<tr><td>September 4, 2026</td><td>September 10, 2026</td><td>Thursday</td><td>12:00 p.m.</td><td>Labor Day</td></tr>
<tr><td>October 9, 2026</td><td>October 15, 2026</td><td>Thursday</td><td>12:00 p.m.</td><td>Columbus Day</td></tr>
</table></body></html>'''


class EIAWPSRScheduleAdapterTests(unittest.TestCase):
    def test_parses_standard_rule_and_holiday_exceptions(self):
        rule=parse_eia_wpsr_schedule_html(HTML)
        self.assertEqual(rule.standard_release_day,"Wednesday")
        self.assertEqual(rule.standard_release_time_local,"10:30")
        self.assertEqual(rule.standard_time_semantics,"AFTER")
        self.assertEqual(rule.source_timezone,"America/New_York")
        self.assertEqual(len(rule.holiday_exceptions),2)
        self.assertEqual(rule.holiday_exceptions[0]["week_ending"],"2026-09-04")
        self.assertEqual(rule.holiday_exceptions[0]["alternate_release_date"],"2026-09-10")
        self.assertEqual(rule.holiday_exceptions[0]["release_time_local"],"12:00")
        self.assertEqual(len(rule.schedule_sha256),64)

    def test_hash_is_semantic_not_markup_sensitive(self):
        variant=HTML.replace(b"<strong>10:30 a.m.</strong>",b"10:30 a.m.")
        self.assertEqual(
            parse_eia_wpsr_schedule_html(HTML).schedule_sha256,
            parse_eia_wpsr_schedule_html(variant).schedule_sha256,
        )

    def test_missing_standard_rule_fails_closed(self):
        broken=HTML.replace(b"after <strong>10:30 a.m.</strong> eastern time on Wednesday",b"at an unspecified time")
        with self.assertRaises(AdapterError):
            parse_eia_wpsr_schedule_html(broken)

    def test_missing_exception_table_fails_closed(self):
        broken=b'''<p>The wpsrsummary.pdf, overview.pdf, and Tables 1-14 in CSV and XLS formats, are released to the web site after 10:30 a.m. eastern time on Wednesday.</p>'''
        with self.assertRaises(AdapterError):
            parse_eia_wpsr_schedule_html(broken)


if __name__=="__main__":
    unittest.main()
