from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import unittest

from src.world_signals.projection import public_projection

ROOT = Path(__file__).resolve().parents[1]


class EventDetailUXTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "web/index.html").read_text(encoding="utf-8")
        cls.js = (ROOT / "web/app.js").read_text(encoding="utf-8")
        cls.css = (ROOT / "web/styles.css").read_text(encoding="utf-8")
        cls.projection = (ROOT / "src/world_signals/projection.py").read_text(encoding="utf-8")

    def test_detail_surface_is_semantic_and_progressive(self):
        self.assertIn('aria-labelledby="detailTitle"', self.html)
        self.assertIn('aria-describedby="detailSummary"', self.html)
        for label in ("Timing", "Source", "History", "Method / provenance", "Technical details"):
            self.assertIn(label, self.js)
        self.assertIn("<details", self.js)
        self.assertIn("#event=", self.js)
        self.assertIn("Copy public link", self.js)

    def test_detail_uses_public_projection_and_has_no_private_fetch_path(self):
        for field in ("time_precision", "time_status", "time_basis", "publication_datetime", "last_verified_at"):
            self.assertIn(f'"{field}"', self.projection)
        for forbidden in ("data/canonical/registry.json", "data/runtime.json", "data/review_state.json"):
            self.assertNotIn(forbidden, self.js)
        self.assertIn("data/events.json", self.js)
        self.assertIn("data/changes.json", self.js)

    def test_exact_timing_uses_iana_conversion_and_keeps_melbourne_secondary(self):
        self.assertIn("Intl.DateTimeFormat", self.js)
        self.assertIn("timeZone", self.js)
        self.assertIn("Australia/Melbourne", self.js)
        self.assertIn("Source-local time", self.js)
        self.assertIn("Melbourne reference", self.js)
        self.assertIn("Show UTC", self.js)
        self.assertNotIn("UTC+10", self.js)

    def test_non_exact_timing_has_explicit_precision_branches(self):
        for label in (
            "Date window",
            "Source-native date",
            "Time or date TBC",
            "Expected window",
            "Provisional",
            "Postponed",
            "Cancelled",
        ):
            self.assertIn(label, self.js)
        self.assertIn("no day boundary is asserted", self.js)
        self.assertIn("no reference-time conversion is asserted", self.js)

    def test_accessibility_and_mobile_detail_structure_are_present(self):
        self.assertIn("addEventListener('cancel'", self.js)
        self.assertIn("detailOpener", self.js)
        self.assertIn("preventScroll", self.js)
        self.assertIn("@media(max-width:620px)", self.css)
        self.assertIn(".detail-time-grid{grid-template-columns:1fr}", self.css)
        self.assertIn("prefers-reduced-motion:reduce", self.css)

    def test_projection_exposes_only_public_safe_timing_and_provenance_fields(self):
        record = {
            "occurrence_id": "WSO-DETAIL-0001",
            "series_id": "WSER-DETAIL",
            "canonical_name": "Test event",
            "short_calendar_title": "Test event",
            "category": "MACRO_MONETARY",
            "region": "North America",
            "jurisdiction": "United States",
            "institution": "Test Authority",
            "certainty_status": "PROVISIONAL",
            "lifecycle_status": "PLANNED",
            "event_type": "POLICY_DECISION",
            "record_class": "CANONICAL_EVENT",
            "timing_type": "EXACT_DATETIME",
            "start_local": "2026-10-14T08:30",
            "start_utc": "2026-10-14T12:30:00Z",
            "source_timezone": "America/New_York",
            "time_precision": "MINUTE",
            "time_status": "CONFIRMED",
            "time_basis": "SOURCE_SCHEDULE",
            "all_day_semantics": None,
            "reference_period": "September 2026",
            "publication_datetime": "2026-10-13T08:30",
            "last_verified_at": "2026-09-26T00:00:00Z",
            "visibility_tier": "PUBLIC",
            "render_policy": "PUBLIC_CALENDAR",
            "source_id": "SRC-TEST",
            "notes": "Public note",
        }
        row = public_projection({"version": "test", "records": [record]}, {"sources": []})["events"][0]
        self.assertEqual(row["time_precision"], "MINUTE")
        self.assertEqual(row["time_status"], "CONFIRMED")
        self.assertEqual(row["time_basis"], "SOURCE_SCHEDULE")
        self.assertEqual(row["publication_datetime"], "2026-10-13T08:30")
        self.assertEqual(row["last_verified_at"], "2026-09-26T00:00:00Z")
        self.assertNotIn("review_queue", row)
        self.assertNotIn("runtime", row)


class EventDetailTimeContractTests(unittest.TestCase):
    def test_new_york_to_melbourne_conversion_respects_dst(self):
        instant = datetime(2026, 10, 14, 12, 30, tzinfo=timezone.utc)
        self.assertEqual(instant.astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M %Z"), "2026-10-14 08:30 EDT")
        self.assertEqual(instant.astimezone(ZoneInfo("Australia/Melbourne")).strftime("%Y-%m-%d %H:%M %Z"), "2026-10-14 23:30 AEDT")

    def test_winter_conversion_changes_offsets_without_manual_constants(self):
        instant = datetime(2026, 1, 15, 14, 30, tzinfo=timezone.utc)
        self.assertEqual(instant.astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M %Z"), "2026-01-15 09:30 EST")
        self.assertEqual(instant.astimezone(ZoneInfo("Australia/Melbourne")).strftime("%Y-%m-%d %H:%M %Z"), "2026-01-16 01:30 AEDT")


if __name__ == "__main__":
    unittest.main()
