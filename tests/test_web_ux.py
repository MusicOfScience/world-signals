from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class WebUXTests(unittest.TestCase):
    def test_calendar_is_primary_view(self):
        html=(ROOT/"web/index.html").read_text(encoding="utf-8")
        self.assertIn('data-view="calendar" aria-pressed="true"', html)
        self.assertIn('id="calendarView"', html)
        self.assertIn('Windows and month-precision events', html)

    def test_monitor_routes_are_present_but_not_claimed_as_runtime_status(self):
        html=(ROOT/"web/index.html").read_text(encoding="utf-8")
        js=(ROOT/"web/app.js").read_text(encoding="utf-8")
        self.assertIn('data-view="monitors"', html)
        self.assertIn('id="monitorsView"', html)
        self.assertIn('Runtime health is intentionally not claimed here', js)
        self.assertIn('data/monitor_routes.json', js)

    def test_browser_has_no_canonical_write_path(self):
        js=(ROOT/"web/app.js").read_text(encoding="utf-8")
        self.assertNotIn('data/canonical/registry.json', js)
        self.assertNotIn("method:'POST'", js)
        self.assertNotIn('method:"POST"', js)
        self.assertNotIn('automatic_commit_allowed:true', js.replace(' ',''))

if __name__=="__main__": unittest.main()
