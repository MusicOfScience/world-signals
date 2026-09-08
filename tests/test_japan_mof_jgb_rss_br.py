from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.adapters.base import AdapterError
from world_signals.adapters.japan_mof_rss import JapanMOFRSSItem, parse_japan_mof_news_rss
from world_signals.japan_mof_jgb_monitor import japan_mof_jgb_rss_review_candidates

PLAN = json.loads((ROOT / "data/monitor/JGB_RSS_MONITOR_BR_PLAN_v0.1.json").read_text())
CANONICAL = json.loads((ROOT / "data/canonical/registry.json").read_text())


def item(title: str, *, link: str = "https://www.mof.go.jp/english/policy/jgbs/auction/calendar/eresul/example.htm", pub: str = "2026-09-08T03:35:00Z") -> JapanMOFRSSItem:
    return JapanMOFRSSItem(
        title=title,
        link=link,
        guid=link + "#guid",
        pub_date_utc=pub,
        pub_date_original="Tue, 08 Sep 2026 12:35:00 +0900",
        description="",
    )


def config() -> dict:
    return {
        "adapter_id": "JAPAN_MOF_JGB_RSS",
        "source_id": "WSSRC-FIS-029",
        "canonical_occurrence_ids": list(PLAN["canonical_occurrence_ids"]),
    }


class JapanMOFRSSAdapterTests(unittest.TestCase):
    def test_parser_preserves_publication_time_and_official_identity(self):
        xml = b'''<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0"><channel><title>MOF</title><item>
          <title>Auction Result of 5-Year JGBs on September 8, 2026</title>
          <link>https://www.mof.go.jp/english/policy/jgbs/auction/calendar/eresul/eresul20260908.htm</link>
          <guid>https://www.mof.go.jp/english/policy/jgbs/auction/calendar/eresul/eresul20260908.htm</guid>
          <pubDate>Tue, 08 Sep 2026 12:35:00 +0900</pubDate>
          <description>Official result</description>
        </item></channel></rss>'''
        rows = parse_japan_mof_news_rss(xml)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].pub_date_utc, "2026-09-08T03:35:00Z")
        self.assertEqual(rows[0].pub_date_original, "Tue, 08 Sep 2026 12:35:00 +0900")
        self.assertIn("5-Year JGBs", rows[0].title)

    def test_parser_accepts_missing_guid_by_using_official_link_identity(self):
        xml = b'''<rss version="2.0"><channel><item>
          <title>Announcement of 20-year JGBs to Be Issued in September 2026</title>
          <link>https://www.mof.go.jp/english/policy/jgbs/auction/calendar/announcement/auct20260908e.htm</link>
          <pubDate>Tue, 08 Sep 2026 10:30:00 +0900</pubDate>
        </item></channel></rss>'''
        rows = parse_japan_mof_news_rss(xml)
        self.assertEqual(rows[0].guid, rows[0].link)

    def test_parser_rejects_external_item_link(self):
        xml = b'''<rss version="2.0"><channel><item>
          <title>Bad item</title><link>https://example.com/x</link>
          <pubDate>Tue, 08 Sep 2026 10:30:00 +0900</pubDate>
        </item></channel></rss>'''
        with self.assertRaises(AdapterError):
            parse_japan_mof_news_rss(xml)

    def test_parser_rejects_empty_feed(self):
        with self.assertRaises(AdapterError):
            parse_japan_mof_news_rss(b"<rss version='2.0'><channel/></rss>")


class JapanMOFJGBMonitorTests(unittest.TestCase):
    def test_standard_result_for_current_planned_auction_creates_review_candidate_not_completion(self):
        rows = [item("Auction Result of 5-Year JGBs on September 8, 2026")]
        candidates, observations = japan_mof_jgb_rss_review_candidates(CANONICAL["records"], rows, config())
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["candidate_type"], "JAPAN_MOF_JGB_AUCTION_RESULT_PUBLICATION_EVIDENCE")
        self.assertEqual(candidate["occurrence_ids"], ["WSO-FIS-A-0016"])
        self.assertEqual(candidate["event_state_inference"], "NONE")
        self.assertFalse(candidate["automatic_commit_allowed"])
        self.assertTrue(candidate["completion_requires_review"])
        self.assertFalse(candidate["canonical_clock_mutation_allowed"])
        self.assertTrue(candidate["new_value"]["rss_publication_time_is_not_auction_time"])
        matched = [x for x in observations if x["type"] == "JAPAN_MOF_JGB_STANDARD_RESULT_MATCHED_REVIEW_REQUIRED"]
        self.assertEqual(len(matched), 1)

    def test_completed_sep3_result_is_corroboration_only(self):
        rows = [item("Auction Result of 30-Year JGBs on September 3, 2026", pub="2026-09-03T03:35:00Z")]
        candidates, observations = japan_mof_jgb_rss_review_candidates(CANONICAL["records"], rows, config())
        self.assertEqual(candidates, [])
        matching = [x for x in observations if x["type"] == "JAPAN_MOF_JGB_COMPLETED_OCCURRENCE_RESULT_PRESENT_NO_LIFECYCLE_ACTION"]
        self.assertEqual(matching[0]["occurrence_id"], "WSO-FIS-A-0015")

    def test_special_participant_result_never_creates_duplicate_candidate(self):
        rows = [
            item("Auction Result of 5-Year JGBs on September 8, 2026"),
            item(
                "Auction Result of 5-Year JGBs on September 8, 2026 (For JGB Market Special Participants)",
                link="https://www.mof.go.jp/english/policy/jgbs/auction/calendar/eresul/eresul20260908a.htm",
                pub="2026-09-08T06:15:00Z",
            ),
        ]
        candidates, observations = japan_mof_jgb_rss_review_candidates(CANONICAL["records"], rows, config())
        self.assertEqual(len(candidates), 1)
        special = [x for x in observations if x["type"] == "JAPAN_MOF_JGB_SPECIAL_PARTICIPANT_RESULT_CORROBORATION_ONLY"]
        self.assertEqual(len(special), 1)
        self.assertEqual(special[0]["occurrence_id"], "WSO-FIS-A-0016")

    def test_issuance_announcement_is_observation_only_and_does_not_establish_date(self):
        rows = [item(
            "Announcement of 20-year JGBs to Be Issued in September 2026",
            link="https://www.mof.go.jp/english/policy/jgbs/auction/calendar/announcement/auct20260908e.htm",
            pub="2026-09-08T01:30:00Z",
        )]
        candidates, observations = japan_mof_jgb_rss_review_candidates(CANONICAL["records"], rows, config())
        self.assertEqual(candidates, [])
        announcement = [x for x in observations if x["type"] == "JAPAN_MOF_JGB_ISSUANCE_ANNOUNCEMENT_OBSERVED_NO_SCHEDULE_MUTATION"][0]
        self.assertEqual(announcement["occurrence_id"], "WSO-FIS-A-0017")
        self.assertTrue(announcement["announcement_title_does_not_establish_auction_date"])

    def test_calendar_change_notice_requires_manual_schedule_recheck_and_never_fetches_html(self):
        rows = [item(
            "Alteration of the JGB Auction Calendar for September 2026",
            link="https://www.mof.go.jp/english/policy/jgbs/auction/calendar/change/example.htm",
        )]
        candidates, observations = japan_mof_jgb_rss_review_candidates(CANONICAL["records"], rows, config())
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["candidate_type"], "JAPAN_MOF_JGB_CALENDAR_CHANGE_NOTICE_REQUIRES_MANUAL_SCHEDULE_REVIEW")
        self.assertTrue(candidates[0]["date_change_requires_manual_authoritative_calendar_review"])
        self.assertFalse(candidates[0]["new_value"]["automatic_calendar_html_fetch_allowed"])
        self.assertTrue([x for x in observations if x["type"] == "JAPAN_MOF_JGB_CALENDAR_CHANGE_NOTICE_REVIEW_REQUIRED"])

    def test_feed_absence_always_has_no_schedule_lifecycle_or_certainty_semantics(self):
        candidates, observations = japan_mof_jgb_rss_review_candidates(CANONICAL["records"], [], config())
        self.assertEqual(candidates, [])
        tail = observations[-1]
        self.assertEqual(tail["type"], "JAPAN_MOF_JGB_RSS_ABSENCE_HAS_NO_SCHEDULE_LIFECYCLE_OR_CERTAINTY_SEMANTICS")
        self.assertEqual(tail["event_state_inference"], "NONE")
        self.assertFalse(tail["automatic_commit_allowed"])

    def test_current_repository_preserves_html_hold_or_complete_br_descendant_contract(self):
        sources = json.loads((ROOT / "data/sources/registry.json").read_text())
        monitor = json.loads((ROOT / "data/monitor/expectations.json").read_text())
        by_source = {x["source_id"]: x for x in sources["sources"]}
        schedule = by_source["WSSRC-FIS-007"]
        self.assertEqual(schedule["automated_monitoring_use"], "ENDPOINT_REVIEW_REQUIRED")
        self.assertEqual(schedule["automated_retrieval_permission"], "PENDING_ENDPOINT_OPERATIONAL_REVIEW")
        self.assertEqual(schedule["canonical_dependency_count"], 10)
        machine = by_source.get("WSSRC-FIS-029")
        routes = {x["adapter_id"]: x for x in monitor["adapters"]}
        if machine is None:
            self.assertNotIn("JAPAN_MOF_JGB_RSS", routes)
        else:
            self.assertEqual(machine["canonical_dependency_count"], 0)
            self.assertEqual(machine["automated_monitoring_use"], "CLEARED")
            self.assertEqual(machine["canonical_provenance_use"], "MONITOR_ONLY_PUBLICATION_CHANGE_SENTINEL_NO_CANONICAL_SCHEDULE_AUTHORITY")
            route = routes["JAPAN_MOF_JGB_RSS"]
            self.assertEqual(set(route["canonical_occurrence_ids"]), set(PLAN["canonical_occurrence_ids"]))
            self.assertEqual(route["request_budget_per_run"], 1)
            self.assertFalse(route["schedule_authority"])
            self.assertFalse(route["lifecycle_authority"])
            self.assertFalse(route["certainty_authority"])
            self.assertFalse(route["automatic_calendar_html_fetch_allowed"])
            self.assertFalse(route["automatic_commit_allowed"])


if __name__ == "__main__":
    unittest.main()
