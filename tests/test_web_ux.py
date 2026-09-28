from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class WebUXTests(unittest.TestCase):
    def test_public_surface_tokens_reduce_luminance_without_removing_contrast(self):
        css=(ROOT/"web/styles.css").read_text(encoding="utf-8")
        for token in (
            "--paper:#efede7",
            "--panel:#f4f1eb",
            "--panel-raised:#f1eee8",
            "--line:#cfc8bd",
            "--accent:#6b3437",
            "--focus:#8a5c14",
        ):
            self.assertIn(token,css)
        self.assertIn("prefers-reduced-motion:reduce",css)

    def test_public_first_view_leads_with_outlook_and_keeps_world_state_closed(self):
        html=(ROOT/"web/index.html").read_text(encoding="utf-8")
        self.assertIn("A PUBLIC INTELLIGENCE BRIEF",html)
        self.assertIn("What we expect next.",html)
        self.assertIn('href="#outlook">OUTLOOK</a>',html)
        self.assertIn('id="outlook"',html)
        self.assertIn('id="worldStateCoverage"',html)
        self.assertIn("Public World State synthesis is not yet open.",html)
        self.assertNotIn("VALUES NOT PUBLISHED",html)
        self.assertIn('id="horizonDomain"><option value="">All domains</option>',html)

    def test_public_intelligence_spine_demotes_registry_dashboard_material(self):
        html=(ROOT/"web/index.html").read_text(encoding="utf-8")
        self.assertLess(html.index('id="outlook"'), html.index('id="nextClock"'))
        self.assertLess(html.index('id="nextClock"'), html.index('id="analysisSection"'))
        self.assertLess(html.index('id="analysisSection"'), html.index('id="horizon"'))
        self.assertLess(html.index('id="horizon"'), html.index('id="methods"'))
        self.assertNotIn('id="now"', html)
        self.assertNotIn('id="themes"', html)
        self.assertNotIn('id="changeView"', html)
        self.assertIn('id="calendar-brief-meta"', html)
        self.assertIn('class="theme-section calendar-context"', html)
        self.assertIn('id="themeList"', html)

    def test_hero_uses_quiet_public_boundary(self):
        html=(ROOT/"web/index.html").read_text(encoding="utf-8")
        self.assertIn('class="safety hero-boundary"', html)
        self.assertIn("PUBLIC NOW", html)
        self.assertIn("Boundaries and method", html)
        self.assertNotIn("Publication boundary", html)

    def test_forecast_lifecycle_and_object_specific_resolution_are_rendered(self):
        html=(ROOT/"web/index.html").read_text(encoding="utf-8")
        js=(ROOT/"web/app.js").read_text(encoding="utf-8")
        self.assertIn('id="forecastChronology"', html)
        self.assertIn("forecast-lifecycle", js)
        self.assertIn("WHAT SETTLES THIS?", js)
        self.assertIn("Outcome pending", js)
        self.assertIn("forecast_id", js)

    def test_no_fake_resolution_link_affordance_and_explicit_calendar_mapping(self):
        js=(ROOT/"web/app.js").read_text(encoding="utf-8")
        projection=(ROOT/"src/world_signals/public_forecast_projection.py").read_text(encoding="utf-8")
        self.assertNotIn("Official resolution source ↗", js)
        self.assertIn("calendar_event", js)
        self.assertIn("PUBLIC_FORECAST_CALENDAR_LINKS", projection)
        self.assertIn("EXPLICIT_REVIEWED_OCCURRENCE_IDS", projection)

    def test_analysis_preview_is_time_ordered_and_world_state_is_research_boundary(self):
        js=(ROOT/"web/app.js").read_text(encoding="utf-8")
        html=(ROOT/"web/index.html").read_text(encoding="utf-8")
        self.assertIn("analysis_as_of_utc", js)
        self.assertIn("REVIEWED ANALYSIS", html)
        self.assertLess(html.index('id="analysisSection"'), html.index('id="horizon"'))
        self.assertLess(html.index('id="methods"'), html.index('id="worldStateCoverage"'))

    def test_outlook_projection_is_built_separately_from_governed_forecasts(self):
        build=(ROOT/"scripts/build_site.py").read_text(encoding="utf-8")
        app=(ROOT/"web/app.js").read_text(encoding="utf-8")
        self.assertIn("public_forecast_projection", build)
        self.assertIn('data/outlook.json', app)
        self.assertNotIn('data/forecasts/forecasts.json', app)
        self.assertIn('forecast_value', app)
        self.assertIn('probability-track', app)

    def test_primary_navigation_is_reader_oriented(self):
        html=(ROOT/"web/index.html").read_text(encoding="utf-8")
        self.assertIn('href="#outlook">OUTLOOK</a>',html)
        self.assertIn('href="#horizon">CALENDAR</a>',html)
        self.assertIn('href="#analysisSection">ANALYSIS</a>',html)
        self.assertIn('href="#methods">RESEARCH</a>',html)
        self.assertNotIn('href="#signals">SIGNALS</a>',html)

    def test_public_mobile_structure_has_viewport_and_non_wrapping_navigation(self):
        html=(ROOT/"web/index.html").read_text(encoding="utf-8")
        css=(ROOT/"web/styles.css").read_text(encoding="utf-8")
        self.assertIn('name="viewport"',html)
        self.assertIn("overflow:auto",css)
        self.assertIn("@media(max-width:620px)",css)

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
        self.assertIn('id="opsReviewSearch"', html)
        self.assertIn('id="opsReviewAttentionFilter"', html)
        self.assertIn('Operator routing only', html)
        self.assertIn('bounded by retained execution evidence', html)
        self.assertIn('stable <code>WSRV-*</code> review item', html)
        self.assertIn("fetch('data/review_state.json')", js)
        self.assertIn('AVAILABLE_RETAINED_HORIZON', js)
        self.assertIn('A later run with no matching candidate does not resolve an earlier item', js)
        self.assertIn('operator_attention_class', js)
        self.assertIn('operator_next_action', js)
        self.assertIn('Evidence objects', js)
        self.assertIn('renderReviewItems', js)
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

    def test_cross_domain_risk_overlay_is_a_separate_read_only_view(self):
        js=(ROOT/"web/risk.js").read_text(encoding="utf-8")
        build=(ROOT/"scripts/build_site.py").read_text(encoding="utf-8")
        self.assertIn('id="riskTab"', js)
        self.assertIn('id="riskView"', js)
        self.assertIn('Single danger score: absent', js)
        self.assertIn('Private Live Intelligence: not consumed', js)
        self.assertIn("fetch('data/risk_overlay.json')", js)
        self.assertIn('risk_overlay.json', build)
        self.assertNotIn('data/canonical/registry.json', js)
        self.assertNotIn("method:'POST'", js)
        self.assertNotIn('method:"POST"', js)

if __name__=="__main__": unittest.main()
