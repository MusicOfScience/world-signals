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

    def test_reviewed_change_history_is_a_separate_read_only_view(self):
        html=(ROOT/"web/index.html").read_text(encoding="utf-8")
        js=(ROOT/"web/history.js").read_text(encoding="utf-8")
        build=(ROOT/"scripts/build_site.py").read_text(encoding="utf-8")
        self.assertIn('id="historyTab"', html)
        self.assertIn('id="historyView"', html)
        self.assertIn('Reviewed history: visible here', html)
        self.assertIn('Run-generated candidates: Operations snapshot', html)
        self.assertIn('Retained review state: Operations horizon', html)
        self.assertIn('Permanent review queue: not yet claimed', html)
        self.assertIn("fetch('data/changes.json')", js)
        self.assertIn('old_values', js)
        self.assertIn('new_values', js)
        self.assertIn('review_basis', js)
        self.assertIn('history.js', build)
        self.assertIn('history.css', build)

    def test_operations_view_exposes_dated_runtime_without_claiming_now(self):
        html=(ROOT/"web/index.html").read_text(encoding="utf-8")
        js=(ROOT/"web/operations.js").read_text(encoding="utf-8")
        build=(ROOT/"scripts/build_site.py").read_text(encoding="utf-8")
        self.assertIn('id="operationsTab"', html)
        self.assertIn('id="operationsView"', html)
        self.assertIn('Latest retained run: dated snapshot only', html)
        self.assertIn('Current source health: not inferred', html)
        self.assertIn('Retained review state: visible inside evidence horizon', html)
        self.assertIn('Permanent review queue: not yet claimed', html)
        self.assertIn("fetch('data/runtime.json')", js)
        self.assertIn('A recorded run is not current health', html)
        self.assertIn('runtime.json', build)

    def test_retained_review_state_is_visible_but_not_claimed_permanent(self):
        html=(ROOT/"web/index.html").read_text(encoding="utf-8")
        js=(ROOT/"web/operations.js").read_text(encoding="utf-8")
        build=(ROOT/"scripts/build_site.py").read_text(encoding="utf-8")
        pages=(ROOT/".github/workflows/pages.yml").read_text(encoding="utf-8")
        self.assertIn('id="opsReviewSummary"', html)
        self.assertIn('id="opsReviewItems"', html)
        self.assertIn('bounded by retained Actions evidence', html)
        self.assertIn('stable <code>WSRV-*</code> review item', html)
        self.assertIn("fetch('data/review_state.json')", js)
        self.assertIn('AVAILABLE_RETAINED_HORIZON', js)
        self.assertIn('A later run with no matching candidate does not resolve an earlier item', js)
        self.assertIn('review_state.json', build)
        self.assertIn('fetch_retained_review_state.py', pages)
        self.assertNotIn('permanent pending-review database', js.lower())

    def test_operations_module_has_no_write_path(self):
        js=(ROOT/"web/operations.js").read_text(encoding="utf-8")
        self.assertNotIn('data/canonical/registry.json', js)
        self.assertNotIn("method:'POST'", js)
        self.assertNotIn('method:"POST"', js)
        self.assertNotIn('PUT', js)
        self.assertNotIn('DELETE', js)
        self.assertNotIn('automatic_commit_allowed:true', js.replace(' ',''))

    def test_history_module_has_no_write_path(self):
        js=(ROOT/"web/history.js").read_text(encoding="utf-8")
        self.assertNotIn('data/canonical/registry.json', js)
        self.assertNotIn("method:'POST'", js)
        self.assertNotIn('method:"POST"', js)
        self.assertNotIn('PUT', js)
        self.assertNotIn('DELETE', js)

    def test_browser_has_no_canonical_write_path(self):
        js=(ROOT/"web/app.js").read_text(encoding="utf-8")
        self.assertNotIn('data/canonical/registry.json', js)
        self.assertNotIn("method:'POST'", js)
        self.assertNotIn('method:"POST"', js)
        self.assertNotIn('automatic_commit_allowed:true', js.replace(' ',''))

    def test_seasonal_windows_use_source_native_month_semantics(self):
        js=(ROOT/"web/app.js").read_text(encoding="utf-8")
        self.assertIn('MONTH_BOUNDED_SEASON_WINDOW', js)
        self.assertIn('MULTI_PHASE_SEASON_WINDOW', js)
        self.assertIn('source_native_window_label', js)
        self.assertIn('season_phases', js)
        self.assertIn('month-bounded seasonal window · no day boundary asserted', js)
        self.assertIn('seasonOverlapsMonth', js)
        self.assertIn('if(isSeasonWindow(e)) return null;', js)

    def test_seasonal_sort_proxy_is_not_a_rendered_event_date(self):
        js=(ROOT/"web/app.js").read_text(encoding="utf-8")
        self.assertIn('parseMonthSortProxy', js)
        self.assertIn('eventSortDate', js)
        self.assertIn('windowLabel(e)', js)
        self.assertNotIn('seasonSortDate(e).toLocale', js)
        self.assertNotIn('seasonSortDate(e).toISOString', js)
        self.assertNotIn('seasonSortDate(e).toLocaleDateString', js)

if __name__=="__main__": unittest.main()
