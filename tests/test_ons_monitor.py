from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.adapters import (
    AdapterError,
    ONSReleaseItem,
    ons_release_calendar_rss_url,
    parse_ons_release_calendar_rss,
)
from world_signals.ons_monitor import ons_release_calendar_review_candidates


SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Release calendar</title>
    <link>https://www.ons.gov.uk/releasecalendar</link>
    <description>Upcoming releases</description>
    <item>
      <title>GDP monthly estimate, UK: July 2026</title>
      <link>https://www.ons.gov.uk/releases/gdpmonthlyestimateukjuly2026</link>
      <guid>https://www.ons.gov.uk/releases/gdpmonthlyestimateukjuly2026</guid>
      <pubDate>Fri, 11 Sep 2026 06:00:00 +0000</pubDate>
      <description>Monthly GDP publication.</description>
    </item>
  </channel>
</rss>
"""


def record(start_local: str = "2026-09-11T07:00:00") -> dict:
    return {
        "occurrence_id": "WSO-MAC-B-0035",
        "series_id": "WSER-MAC-UK-MGDP",
        "canonical_name": "UK Monthly GDP — July 2026",
        "category": "MACROECONOMIC_RELEASE",
        "jurisdiction": "United Kingdom",
        "institution": "Office for National Statistics",
        "source_id": "WSSRC-MAC-006",
        "start_local": start_local,
        "end_local": None,
        "start_utc": "2026-09-11T06:00:00Z",
        "certainty_status": "CONFIRMED",
        "lifecycle_status": "PLANNED",
    }


def config() -> dict:
    return {
        "adapter_id": "ONS_RELEASE_CALENDAR_RSS",
        "source_id": "WSSRC-MAC-006",
        "canonical_occurrence_ids": ["WSO-MAC-B-0035"],
        "tracked_items": [
            {
                "occurrence_id": "WSO-MAC-B-0035",
                "feed_title": "GDP monthly estimate, UK: July 2026",
            }
        ],
        "automatic_commit_allowed": False,
    }


class ONSReleaseCalendarAdapterTests(unittest.TestCase):
    def test_url_is_official_upcoming_rss_route(self):
        url = ons_release_calendar_rss_url(page=2, limit=100)
        self.assertTrue(url.startswith("https://www.ons.gov.uk/releasecalendar?"))
        self.assertIn("release-type=type-upcoming", url)
        self.assertIn("rss=", url)
        self.assertIn("page=2", url)
        self.assertIn("limit=100", url)

    def test_rss_parser_preserves_identity_and_normalizes_utc(self):
        items = parse_ons_release_calendar_rss(SAMPLE_RSS)
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item.title, "GDP monthly estimate, UK: July 2026")
        self.assertEqual(item.pub_date_iso, "2026-09-11T06:00:00Z")
        self.assertEqual(item.guid, item.link)

    def test_rss_parser_fails_closed_on_missing_timezone(self):
        broken = SAMPLE_RSS.replace(
            "Fri, 11 Sep 2026 06:00:00 +0000",
            "Fri, 11 Sep 2026 06:00:00",
        )
        with self.assertRaises(AdapterError):
            parse_ons_release_calendar_rss(broken)


class ONSReleaseCalendarMonitorTests(unittest.TestCase):
    NOW = datetime(2026, 9, 5, 0, 0, tzinfo=timezone.utc)

    def test_exact_live_datetime_is_no_change(self):
        item = ONSReleaseItem(
            title="GDP monthly estimate, UK: July 2026",
            link="https://www.ons.gov.uk/releases/gdpmonthlyestimateukjuly2026",
            guid="https://www.ons.gov.uk/releases/gdpmonthlyestimateukjuly2026",
            pub_date_iso="2026-09-11T06:00:00Z",
            description="Monthly GDP publication.",
        )
        candidates, observations = ons_release_calendar_review_candidates(
            [record()], [item], config(), now_utc=self.NOW
        )
        self.assertEqual(candidates, [])
        self.assertEqual(observations[0]["type"], "ONS_RELEASE_DATETIME_NO_CHANGE")

    def test_datetime_drift_is_review_only_and_requires_html_verification(self):
        item = ONSReleaseItem(
            title="GDP monthly estimate, UK: July 2026",
            link="https://www.ons.gov.uk/releases/gdpmonthlyestimateukjuly2026",
            guid="https://www.ons.gov.uk/releases/gdpmonthlyestimateukjuly2026",
            pub_date_iso="2026-09-11T07:00:00Z",
            description="Monthly GDP publication.",
        )
        candidates, observations = ons_release_calendar_review_candidates(
            [record()], [item], config(), now_utc=self.NOW
        )
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["diff_type"], "DATE_OR_TIME_CHANGED")
        self.assertEqual(candidate["review_state"], "PENDING_ONS_RELEASE_CALENDAR_HTML_VERIFICATION")
        self.assertFalse(candidate["automatic_commit_allowed"])
        self.assertEqual(candidate["source_assertion"]["rss_carries_certainty_status"], False)
        self.assertEqual(observations[0]["type"], "ONS_RELEASE_DATETIME_DRIFT_REVIEW_REQUIRED")

    def test_absence_generates_source_match_review_not_cancellation(self):
        candidates, observations = ons_release_calendar_review_candidates(
            [record()], [], config(), now_utc=self.NOW
        )
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["candidate_type"], "ONS_TRACKED_ITEM_ABSENT_OR_RENAMED")
        self.assertEqual(candidate["event_state_inference"], "NONE")
        self.assertFalse(candidate["automatic_commit_allowed"])
        self.assertEqual(observations[0]["type"], "ONS_TRACKED_ITEM_ABSENT_NO_EVENT_STATE_INFERENCE")

    def test_elapsed_occurrence_is_not_presence_checked_against_upcoming_feed(self):
        candidates, observations = ons_release_calendar_review_candidates(
            [record()], [], config(), now_utc=datetime(2026, 9, 12, 0, 0, tzinfo=timezone.utc)
        )
        self.assertEqual(candidates, [])
        self.assertEqual(observations[0]["type"], "ONS_TRACKED_OCCURRENCE_ELAPSED_NOT_PRESENCE_CHECKED")
        self.assertEqual(observations[0]["event_state_inference"], "NONE")

    def test_duplicate_exact_title_is_ambiguous_not_arbitrarily_selected(self):
        item = ONSReleaseItem(
            title="GDP monthly estimate, UK: July 2026",
            link="https://www.ons.gov.uk/releases/a",
            guid="https://www.ons.gov.uk/releases/a",
            pub_date_iso="2026-09-11T06:00:00Z",
            description="A",
        )
        other = ONSReleaseItem(
            title=item.title,
            link="https://www.ons.gov.uk/releases/b",
            guid="https://www.ons.gov.uk/releases/b",
            pub_date_iso="2026-09-11T06:00:00Z",
            description="B",
        )
        candidates, _ = ons_release_calendar_review_candidates(
            [record()], [item, other], config(), now_utc=self.NOW
        )
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["candidate_type"], "ONS_TRACKED_ITEM_IDENTITY_AMBIGUOUS")

    def test_config_scope_must_exactly_match_tracked_items(self):
        bad = config()
        bad["canonical_occurrence_ids"] = ["WSO-MAC-B-0035", "WSO-OTHER"]
        with self.assertRaises(ValueError):
            ons_release_calendar_review_candidates([record()], [], bad, now_utc=self.NOW)


if __name__ == "__main__":
    unittest.main()
