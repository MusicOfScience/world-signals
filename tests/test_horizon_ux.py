from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class HorizonUXTests(unittest.TestCase):
    def test_horizon_surface_is_present_before_tool_views(self):
        html=(ROOT/"web/index.html").read_text(encoding="utf-8")
        self.assertIn('id="horizon"',html)
        self.assertIn('id="horizonNow"',html)
        self.assertIn('id="horizon7"',html)
        self.assertIn('id="horizon30"',html)
        self.assertIn('id="horizonWindows"',html)
        self.assertLess(html.index('id="horizon"'),html.index('class="viewbar"'))

    def test_horizon_uses_existing_read_only_projections(self):
        js=(ROOT/"web/horizon.js").read_text(encoding="utf-8")
        build=(ROOT/"scripts/build_site.py").read_text(encoding="utf-8")
        self.assertIn("fetch('data/events.json')",js)
        self.assertIn("fetch('data/changes.json')",js)
        self.assertIn("horizon.js",build)
        self.assertIn("horizon.css",build)
        self.assertNotIn("data/canonical/registry.json",js)
        self.assertNotIn("method:'POST'",js)
        self.assertNotIn('method:"POST"',js)
        self.assertNotIn("method:'PUT'",js)
        self.assertNotIn('method:"PUT"',js)
        self.assertNotIn("method:'DELETE'",js)
        self.assertNotIn('method:"DELETE"',js)

    def test_horizon_preserves_window_precision(self):
        js=(ROOT/"web/horizon.js").read_text(encoding="utf-8")
        self.assertIn("MONTH_BOUNDED_SEASON_WINDOW",js)
        self.assertIn("MULTI_PHASE_SEASON_WINDOW",js)
        self.assertIn("source-native month precision · no synthetic day",js)
        self.assertIn("seasonInView",js)
        self.assertIn("dateWindowInView",js)
        self.assertNotIn("new Date(event.season_phases",js)

    def test_horizon_exposes_user_facing_signal_groups(self):
        js=(ROOT/"web/horizon.js").read_text(encoding="utf-8")
        for label in (
            "Economics / central banks / fiscal / markets",
            "Elections / politics",
            "Geopolitics / institutions",
            "Trade / sanctions",
            "Commodities / energy / food",
            "Climate / physical risk",
            "Technology / infrastructure",
            "Health / biosecurity",
        ):
            self.assertIn(label,js)

    def test_horizon_exposes_local_native_certainty_importance_source_and_change(self):
        js=(ROOT/"web/horizon.js").read_text(encoding="utf-8")
        self.assertIn("source_timezone",js)
        self.assertIn("toLocaleString",js)
        self.assertIn("event.certainty",js)
        self.assertIn("intrinsic_importance",js)
        self.assertIn("expected_market_sensitivity",js)
        self.assertIn("authoritative source",js)
        self.assertIn("Changed recently",js)
        self.assertIn("change_type",js)

    def test_horizon_filter_controls_cover_region_and_jurisdiction(self):
        html=(ROOT/"web/index.html").read_text(encoding="utf-8")
        self.assertIn('id="horizonDomain"',html)
        self.assertIn('id="horizonRegion"',html)
        self.assertIn('id="horizonJurisdiction"',html)

    def test_horizon_event_cards_are_keyboard_openable(self):
        js=(ROOT/"web/horizon.js").read_text(encoding="utf-8")
        self.assertIn('role="button" tabindex="0"',js)
        self.assertIn("event.key==='Enter'",js)
        self.assertIn("event.key===' '",js)
        self.assertIn("window.showDetail",js)

if __name__=="__main__":
    unittest.main()
