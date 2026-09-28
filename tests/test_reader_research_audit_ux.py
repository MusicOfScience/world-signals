import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReaderResearchAuditUXTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "web/index.html").read_text(encoding="utf-8")
        cls.app = (ROOT / "web/app.js").read_text(encoding="utf-8")
        cls.styles = (ROOT / "web/styles.css").read_text(encoding="utf-8")

    def test_primary_navigation_remains_four_reader_surfaces(self):
        nav = re.search(r'<nav class="primary-nav".*?</nav>', self.html, re.S).group(0)
        self.assertEqual(
            re.findall(r'<a href="([^"]+)">([^<]+)</a>', nav),
            [
                ("#outlook", "OUTLOOK"),
                ("#horizon", "CALENDAR"),
                ("#analysisSection", "ANALYSIS"),
                ("#methods", "RESEARCH"),
            ],
        )

    def test_reader_order_and_calendar_continuity(self):
        self.assertLess(self.html.index('id="briefing"'), self.html.index('id="outlook"'))
        self.assertLess(self.html.index('id="horizon"'), self.html.index('id="filterDisclosure"'))
        self.assertLess(self.html.index('id="filterDisclosure"'), self.html.index('id="calendarView"'))
        self.assertLess(self.html.index('id="calendarView"'), self.html.index('id="methods"'))
        self.assertLess(self.html.index('id="methods"'), self.html.index('id="systemAuditDisclosure"'))

    def test_calendar_keeps_reader_metrics_and_moves_status_out(self):
        calendar = self.html[self.html.index('id="horizon"'):self.html.index('id="methods"')]
        self.assertIn("NEXT 24 HOURS", calendar)
        self.assertIn("NEXT 7 DAYS", calendar)
        self.assertIn("NEXT 30 DAYS", calendar)
        self.assertIn('id="calendarSubscribe"', calendar)
        self.assertNotIn('id="publicStatus"', calendar)
        self.assertNotIn("configured live monitor routes", calendar)
        self.assertNotIn("Outlook pilot is public", calendar)

    def test_research_owns_status_coverage_and_public_boundaries(self):
        research = self.html[self.html.index('id="methods"'):self.html.index('id="systemAuditDisclosure"')]
        self.assertIn('id="publicStatus"', research)
        self.assertIn('id="stats"', research)
        self.assertIn('id="worldStateCoverage"', research)
        self.assertIn('id="relationshipCoverage"', research)
        self.assertIn('id="publicationBoundaries"', research)
        self.assertIn("calendar corpus", self.app)
        self.assertNotIn("configured live monitor routes", self.app.split("function renderStats", 1)[1].split("function melbourneClock", 1)[0])

    def test_public_method_chain_is_compact_and_does_not_claim_population(self):
        chain = self.html[self.html.index('class="method-chain"'):self.html.index('</div>', self.html.index('class="method-chain"'))]
        for token in ("sources", "observations", "signals", "state + relationships", "scenarios", "forecasts", "outcomes"):
            self.assertIn(token, chain)
        self.assertIn("not a claim that every layer is populated or public", self.html)

    def test_analysis_has_primary_full_view_action_not_calendar_peer(self):
        analysis = self.html[self.html.index('id="analysisSection"'):self.html.index('id="horizon"')]
        self.assertIn('id="analysisTab"', analysis)
        self.assertNotIn('id="analysisTab"', self.html[self.html.index('id="systemAuditDisclosure"'):])

    def test_system_audit_is_collapsed_and_all_secondary_surfaces_remain(self):
        disclosure = self.html[self.html.index('<details id="systemAuditDisclosure"'):]
        self.assertIn('<details id="systemAuditDisclosure" class="system-audit-disclosure">', disclosure)
        self.assertNotIn('<details id="systemAuditDisclosure" class="system-audit-disclosure" open>', disclosure)
        for token in ("Event index", "Monitor routes", "Operations", "Change history"):
            self.assertIn(token, disclosure)
        self.assertIn("secondary-viewtabs", disclosure)
        self.assertIn("calendar-secondary-viewtabs", disclosure)

    def test_system_language_distinguishes_machinery_from_world_description(self):
        self.assertIn("These surfaces describe configuration, retained evidence, governance and review history.", self.html)
        self.assertIn("They do not describe the world directly.", self.html)

    def test_navigation_and_view_scripts_remain_read_only_and_deep_linkable(self):
        for token in ("#event=", "data-view=", "data/monitor_routes.json", "data/changes.json"):
            self.assertIn(token, self.html + self.app)
        for forbidden in ("method:'POST'", 'method:"POST"', "method:'PUT'", 'method:"PUT"', "method:'DELETE'", 'method:"DELETE"'):
            self.assertNotIn(forbidden, self.app)

    def test_palette_and_native_disclosure_semantics_remain(self):
        for token in ("--paper:#ebe6dc", "--panel:#f4f1eb", "--accent:#6b3437", "--focus:#8a5c14"):
            self.assertIn(token, self.styles)
        self.assertIn("system-audit-disclosure>summary", self.styles)
        self.assertIn("system-audit-disclosure[open]", self.styles)
        self.assertIn("prefers-reduced-motion:reduce", self.styles)


if __name__ == "__main__":
    unittest.main()
