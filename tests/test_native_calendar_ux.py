from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class NativeCalendarUXTests(unittest.TestCase):
    def test_native_date_surface_is_outside_gregorian_lanes(self):
        html=(ROOT/"web/index.html").read_text(encoding="utf-8")
        self.assertIn('id="nativeCalendarDates"',html)
        self.assertIn('SOURCE-NATIVE DATES',html)
        self.assertIn('not yet Gregorian here',html)
        self.assertLess(html.index('id="horizonWindows"'),html.index('id="nativeCalendarDates"'))

    def test_native_date_browser_is_read_only_projection(self):
        js=(ROOT/"web/native-calendar.js").read_text(encoding="utf-8")
        self.assertIn("fetch('data/events.json')",js)
        self.assertIn("SOURCE_NATIVE_CALENDAR_DATE",js)
        self.assertIn("UNRESOLVED_AUTHORITATIVE_CONVERSION",js)
        for token in ("method:'POST'",'method:"POST"',"method:'PUT'",'method:"PUT"',"method:'DELETE'",'method:"DELETE"'):
            self.assertNotIn(token,js)
        self.assertNotIn('data/canonical/',js)

    def test_native_date_surface_says_no_synthetic_civil_date(self):
        js=(ROOT/"web/native-calendar.js").read_text(encoding="utf-8")
        self.assertIn('No synthetic civil date',js)
        self.assertIn('Gregorian resolution pending',js)
        self.assertIn('authoritative mapping',js)

    def test_projection_carries_native_fields(self):
        projection=(ROOT/"src/world_signals/projection.py").read_text(encoding="utf-8")
        for field in (
            'native_calendar_system','native_calendar_year','native_calendar_month',
            'native_calendar_day','source_native_date_label','gregorian_resolution_status'
        ):
            self.assertIn(field,projection)

    def test_static_build_bundles_native_assets(self):
        build=(ROOT/"scripts/build_site.py").read_text(encoding="utf-8")
        self.assertIn('native-calendar.js',build)
        self.assertIn('native-calendar.css',build)
        ci=(ROOT/".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn('node --check web/native-calendar.js',ci)


if __name__=="__main__":
    unittest.main()
