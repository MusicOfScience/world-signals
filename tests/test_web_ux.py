from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class WebUXTests(unittest.TestCase):
    def test_calendar_is_primary_view(self):
        html=(ROOT/"web/index.html").read_text(encoding="utf-8")
        self.assertIn('data-view="calendar" aria-pressed="true"', html)
        self.assertIn('id="calendarView"', html)
        self.assertIn('Windows and month-precision events', html)

    def test_browser_has_no_canonical_write_path(self):
        js=(ROOT/"web/app.js").read_text(encoding="utf-8")
        self.assertNotIn('data/canonical/registry.json', js)
        self.assertNotIn("method:'POST'", js)
        self.assertNotIn('method:"POST"', js)

if __name__=="__main__": unittest.main()
