from pathlib import Path
import unittest
from urllib.parse import urljoin


ROOT = Path(__file__).resolve().parents[1]


class SubscriptionShareUXTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "web/index.html").read_text(encoding="utf-8")
        cls.js = (ROOT / "web/app.js").read_text(encoding="utf-8")
        cls.css = (ROOT / "web/styles.css").read_text(encoding="utf-8")

    def test_calendar_subscription_is_discoverable_and_scoped(self):
        for text in (
            'id="calendarSubscribe"',
            "Subscribe to the public calendar",
            "Subscribe to calendar",
            "world-signals.ics",
            "Copy calendar URL",
            "How to subscribe",
            "Apple Calendar",
            "Google Calendar",
            "Outlook",
            "private analysis, Signals and Forecasts are not included",
        ):
            self.assertIn(text, self.html)

    def test_calendar_url_is_pages_subpath_safe_and_hash_free(self):
        self.assertEqual(
            urljoin("https://musicofscience.github.io/world-signals/", "world-signals.ics"),
            "https://musicofscience.github.io/world-signals/world-signals.ics",
        )
        self.assertIn("new URL('world-signals.ics',window.location.href)", self.js)
        self.assertIn("url.hash=''", self.js)

    def test_platform_guidance_distinguishes_subscription_from_import(self):
        self.assertIn("New Calendar Subscription", self.html)
        self.assertIn("From URL", self.html)
        self.assertIn("does not keep it updated", self.html)
        self.assertIn("Subscribe from web", self.html)
        self.assertIn("one-time file import", self.html)

    def test_event_sharing_preserves_public_deep_link_and_summary_actions(self):
        for text in (
            "Copy public link",
            "Copy event summary",
            "navigator.share",
            "AbortError",
            "eventShareUrl",
            "eventSummaryText",
            "Source-local:",
            "Melbourne reference:",
        ):
            self.assertIn(text, self.js)
        self.assertIn("url.hash=detailHash(e.occurrence_id)", self.js)
        self.assertIn("This public event is included in the", self.js)

    def test_summary_has_no_private_fetch_or_internal_id_fallback(self):
        self.assertNotIn("data/canonical/registry.json", self.js)
        self.assertNotIn("data/runtime.json", self.js)
        self.assertNotIn("data/review_state.json", self.js)
        summary = self.js[self.js.index("function eventSummaryText"):self.js.index("function copyDetailLink")]
        self.assertIn("e.institution||e.source_name||''", summary)
        self.assertNotIn("e.source_id", summary)

    def test_copy_fallback_and_accessible_feedback_are_present(self):
        self.assertIn("document.execCommand('copy')", self.js)
        self.assertIn('aria-live="polite"', self.html)
        self.assertIn('type="button"', self.html)
        self.assertIn("calendar-subscribe", self.css)
        self.assertIn("platform-guidance{grid-template-columns:1fr", self.css)

    def test_shared_text_keeps_non_exact_precision(self):
        self.assertIn("timingLabel(timing.kind)", self.js)
        self.assertIn("timing.nativeCalendar", self.js)
        self.assertIn("TBC", self.js)
        self.assertIn("Expected window", self.js)
        self.assertIn("Date window", self.js)


if __name__ == "__main__":
    unittest.main()
