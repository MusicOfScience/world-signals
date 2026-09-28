"""Static contract tests for the Step 13A mobile editorial surface.

These tests exercise the public shell and its projection boundaries only.  They
do not treat CSS tokens as a substitute for visual QA; the rendered page is
checked separately at the requested viewport sizes.
"""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class MobileEditorialProductTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "web/index.html").read_text(encoding="utf-8")
        cls.app = (ROOT / "web/app.js").read_text(encoding="utf-8")
        cls.outlook = (ROOT / "web/outlook.css").read_text(encoding="utf-8")
        cls.styles = (ROOT / "web/styles.css").read_text(encoding="utf-8")
        cls.analysis = (ROOT / "web/analysis.js").read_text(encoding="utf-8")
        cls.risk = (ROOT / "web/risk.js").read_text(encoding="utf-8")

    def test_primary_navigation_is_exactly_reader_oriented(self):
        nav = re.search(r'<nav class="primary-nav".*?</nav>', self.html, re.S).group(0)
        self.assertEqual(re.findall(r'<a href="([^"]+)">([^<]+)</a>', nav), [
            ("#outlook", "OUTLOOK"),
            ("#horizon", "CALENDAR"),
            ("#analysisSection", "ANALYSIS"),
            ("#methods", "RESEARCH"),
        ])

    def test_forecast_precedes_calendar_and_has_scan_to_audit_contract(self):
        self.assertLess(self.html.index('id="outlook"'), self.html.index('id="horizon"'))
        for token in (
            "forecast-card-head", "forecast-target", "forecast-state",
            "Understand this forecast", "Question", "Information cutoff",
            "Resolution rule", "Rationale", "Outcome / evaluation",
        ):
            self.assertIn(token, self.app)
        self.assertIn("forecast-lifecycle", self.app)
        self.assertIn("display:none", self.outlook[self.outlook.index("@media(max-width:680px)"):])

    def test_mobile_chronology_is_a_ledger_not_a_horizontal_dependency(self):
        mobile = self.outlook[self.outlook.index("@media(max-width:680px)"):]
        self.assertIn(".forecast-chronology{overflow:visible", mobile)
        self.assertIn(".forecast-chronology .chronology-line{display:none}", mobile)
        self.assertIn("grid-template-columns:repeat(2,minmax(0,1fr))", mobile)

    def test_calendar_offers_mobile_agenda_and_secondary_month_views(self):
        self.assertIn('id="calendarAgendaToggle"', self.html)
        self.assertIn('id="calendarMonthToggle"', self.html)
        self.assertIn("calendarViewMode", self.app)
        self.assertIn("matchMedia?.('(max-width: 680px)').matches ? 'agenda' : 'month'", self.app)
        self.assertIn("calendarViewMode==='agenda'", self.app)
        self.assertIn("calendarGrid[hidden]", self.styles)

    def test_calendar_rows_retain_operational_fields_and_subscription(self):
        for token in (
            "dayAgendaTitle", "dayAgendaBody", "e.title", "e.institution",
            "e.certainty", 'id="calendarSubscribe"', "Subscribe to calendar",
            "Source-native uncertainty", 'id="nativeCalendarDates"',
        ):
            self.assertIn(token, self.html + self.app)

    def test_filters_have_one_shared_search_and_region_state(self):
        self.assertIn('data-shared-filter="search"', self.html)
        self.assertIn('data-shared-filter="region"', self.html)
        self.assertIn("bindSharedFilterState", self.app)
        self.assertIn("['#search','#horizonSearch']", self.app)
        self.assertIn("['#region','#horizonRegion']", self.app)
        self.assertIn('id="filterDisclosure"', self.html)
        self.assertIn('id="horizonFilterDisclosure"', self.html)

    def test_system_and_audit_views_are_secondary(self):
        self.assertIn("System / audit", self.html)
        secondary = self.html[self.html.index('class="secondary-views"'):self.html.index('</details>', self.html.index('class="secondary-views"'))]
        for label in ("Monitor routes", "Operations", "Change history"):
            self.assertIn(label, secondary)
        self.assertIn('id="analysisTab"', self.html)
        self.assertIn("document.querySelector('.secondary-viewtabs')||document.querySelector('.viewtabs')", self.risk)
        self.assertIn(".secondary-viewtabs button:not(#riskTab)", self.risk)

    def test_analysis_full_view_remains_disclosable_and_filter_is_not_a_surface(self):
        self.assertIn("Read the caution", self.app)
        self.assertIn("Alternative explanations", self.analysis)
        self.assertIn("Falsifiers", self.analysis)
        self.assertIn("#filterDisclosure", self.analysis)

    def test_mobile_layout_has_no_body_overflow_and_preserves_touch_sizing(self):
        self.assertIn("body{overflow-x:hidden}", self.styles)
        mobile = self.styles[self.styles.index("@media(max-width:680px)"):]
        for token in ("min-height:2.75rem", "height:100dvh", "safe-area-inset-bottom"):
            self.assertIn(token, mobile)
        self.assertIn("@media(max-width:380px)", self.styles)

    def test_mobile_detail_is_a_full_height_accessible_sheet(self):
        mobile = self.styles[self.styles.index("@media(max-width:680px)"):]
        for token in ("dialog#detail", "width:100vw", "height:100dvh", "safe-area-inset-top"):
            self.assertIn(token, mobile)
        for token in ('aria-labelledby="detailTitle"', 'aria-describedby="detailSummary"', "addEventListener('cancel'"):
            self.assertIn(token, self.html + self.app)

    def test_warm_palette_and_reduced_motion_remain_explicit(self):
        for token in ("--paper:#ebe6dc", "--panel:#f4f1eb", "--accent:#6b3437", "--focus:#8a5c14"):
            self.assertIn(token, self.styles)
        self.assertIn("prefers-reduced-motion:reduce", self.styles + self.outlook)

    def test_world_state_and_relationships_remain_closed_in_public_shell(self):
        self.assertIn("Public World State synthesis is not yet open.", self.html)
        self.assertNotIn("data/world_state", self.app)
        self.assertNotIn("data/relationships", self.app)
        self.assertNotIn("world_state", " ".join(re.findall(r'fetch\([^)]*\)', self.app)))

    def test_public_projection_is_bounded_and_current_values_are_unchanged(self):
        outlook = json.loads((ROOT / "docs/data/outlook.json").read_text(encoding="utf-8"))
        self.assertEqual(outlook["metadata"]["public_forecast_count"], 4)
        self.assertEqual(
            {row["forecast_id"] for row in outlook["forecasts"]},
            {"WS-FP-RBA-20261103", "WS-FP-BOC-20261028", "WS-FP-FED-20261028", "WS-FP-ECB-20261029"},
        )
        self.assertTrue(all(row["resolution_status"] == "UNRESOLVED" for row in outlook["forecasts"]))


if __name__ == "__main__":
    unittest.main()
