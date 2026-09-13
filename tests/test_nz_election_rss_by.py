from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.adapters.base import AdapterError, FetchSnapshot
from world_signals.adapters.nz_election_rss import (
    NZ_ELECTION_TIMETABLE_URL,
    NZElectionRSSItem,
    fetch_nz_election_rss,
    nz_election_rss_access_policy,
    parse_nz_election_rss,
)
from world_signals.nz_election_monitor import (
    nz_election_timetable_change_review_candidates,
)


def rss_item(index: int, *, target: bool = False, link: str | None = None, guid: str | None = None) -> str:
    url = NZ_ELECTION_TIMETABLE_URL if target else f"https://elections.nz/media-and-news/2026/example-{index}"
    link = url if link is None else link
    guid = url if guid is None else guid
    return f"""
    <item>
      <title>{'Key dates for 2026 General Election' if target else f'Example update {index}'}</title>
      <link>{link}</link>
      <description>{'Election timetable update page.' if target else f'General election news with date 7 November 2026 item {index}.'}</description>
      <pubDate>Mon, 07 Sep 2026 {13 + (index % 5):02d}:19:33 +1200</pubDate>
      <guid>{guid}</guid>
    </item>
    """


def rss_document(*, target_index: int | None = None, item_override: dict[int, str] | None = None) -> bytes:
    overrides = item_override or {}
    items = []
    for index in range(10):
        if index in overrides:
            items.append(overrides[index])
        else:
            items.append(rss_item(index, target=index == target_index))
    return (
        "<rss><channel>"
        "<title>10 Most Recently Updated Pages</title>"
        "<link>https://elections.nz/media-and-news/rss</link>"
        "<description>Shows a list of the 10 most recently updated pages.</description>"
        + "".join(items)
        + "</channel></rss>"
    ).encode("utf-8")


def config() -> dict:
    return {
        "adapter_id": "NZ_ELECTION_TIMETABLE_CHANGE_RSS",
        "source_id": "WSSRC-EL-NZ-002",
        "canonical_schedule_source_id": "WSSRC-EL-NZ-001",
        "canonical_occurrence_ids": [f"WSO-EL-A-{n:04d}" for n in range(5, 11)],
        "canonical_timetable_page_identity": NZ_ELECTION_TIMETABLE_URL,
        "request_budget_per_run": 2,
        "robots_request_count_per_run": 1,
        "rss_request_count_per_run": 1,
        "minimum_inter_request_delay_seconds": 2,
        "timetable_html_request_count_per_run": 0,
        "item_followup_request_count_per_run": 0,
        "results_data_request_count_per_run": 0,
        "search_route_discovery_request_count_per_run": 0,
        "rolling_feed_completeness": "FINITE_ROLLING_WINDOW_NOT_EXHAUSTIVE_CHANGE_LOG",
        "absence_semantics": "NONE",
        "schedule_authority": False,
        "clock_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "canonical_date_mutation_allowed": False,
        "automatic_timetable_html_fetch_allowed": False,
        "automatic_item_link_fetch_allowed": False,
        "automatic_results_data_fetch_allowed": False,
        "automatic_search_route_discovery_allowed": False,
        "automatic_commit_allowed": False,
        "automatic_live_or_analysis_promotion_allowed": False,
    }


def records() -> list[dict]:
    dates = ["2026-10-01", "2026-10-04", "2026-11-07", "2026-11-27", "2026-12-03", "2027-01-14"]
    milestones = [
        "DISSOLUTION",
        "WRIT_OR_FORMAL_CALL",
        "POLL_GENERAL",
        "OFFICIAL_RESULTS",
        "RETURN_OF_WRIT_DEADLINE",
        "PARLIAMENT_MEETING_DEADLINE",
    ]
    out = []
    for number, day, milestone in zip(range(5, 11), dates, milestones):
        out.append({
            "occurrence_id": f"WSO-EL-A-{number:04d}",
            "series_id": "WSER-EL-NZ-GEN",
            "source_id": "WSSRC-EL-NZ-001",
            "source_timezone": "Pacific/Auckland",
            "category": "ELECTIONS_GOVERNANCE",
            "region": "Oceania / Pacific",
            "event_type": "ELECTION_MILESTONE",
            "timing_type": "CIVIL_DATE",
            "time_precision": "DAY",
            "all_day_semantics": True,
            "start_local": day,
            "start_utc": None,
            "lifecycle_status": "PLANNED",
            "certainty_status": "CONFIRMED",
            "election_milestone_type": milestone,
        })
    return out


class NZElectionRSSAdapterTests(unittest.TestCase):
    def test_parser_accepts_exact_rolling_feed_and_exact_target_identity(self):
        items = parse_nz_election_rss(rss_document(target_index=3))
        self.assertEqual(len(items), 10)
        target = [item for item in items if item.guid == NZ_ELECTION_TIMETABLE_URL]
        self.assertEqual(len(target), 1)
        self.assertEqual(target[0].link, NZ_ELECTION_TIMETABLE_URL)
        self.assertEqual(target[0].pub_date_iso, "2026-09-07T16:19:33+12:00")

    def test_parser_rejects_malformed_xml(self):
        with self.assertRaises(AdapterError):
            parse_nz_election_rss(b"<rss><channel>")

    def test_parser_rejects_wrong_channel_identity(self):
        body = rss_document().replace(b"10 Most Recently Updated Pages", b"Election news")
        with self.assertRaises(AdapterError):
            parse_nz_election_rss(body)

    def test_parser_rejects_item_count_drift(self):
        body = rss_document().replace(rss_item(9).encode(), b"")
        with self.assertRaises(AdapterError):
            parse_nz_election_rss(body)

    def test_parser_rejects_off_host_item(self):
        override = rss_item(0, link="https://example.com/media-and-news/2026/bad", guid="https://example.com/media-and-news/2026/bad")
        with self.assertRaises(AdapterError):
            parse_nz_election_rss(rss_document(item_override={0: override}))

    def test_parser_rejects_link_guid_disagreement(self):
        override = rss_item(
            0,
            link="https://elections.nz/media-and-news/2026/a",
            guid="https://elections.nz/media-and-news/2026/b",
        )
        with self.assertRaises(AdapterError):
            parse_nz_election_rss(rss_document(item_override={0: override}))

    def test_parser_rejects_duplicate_identity(self):
        duplicate = rss_item(0)
        with self.assertRaises(AdapterError):
            parse_nz_election_rss(rss_document(item_override={1: duplicate}))

    def test_robots_policy_allows_rss_and_preserves_minimum_delay(self):
        allowed, delay = nz_election_rss_access_policy("User-agent: *\nCrawl-delay: 1\n")
        self.assertTrue(allowed)
        self.assertEqual(delay, 2.0)

    def test_robots_policy_respects_greater_live_delay(self):
        allowed, delay = nz_election_rss_access_policy("User-agent: *\nCrawl-delay: 7\n")
        self.assertTrue(allowed)
        self.assertEqual(delay, 7.0)

    def test_robots_policy_disallow_is_respected(self):
        allowed, _ = nz_election_rss_access_policy("User-agent: *\nDisallow: /media-and-news/rss\n")
        self.assertFalse(allowed)

    def test_robots_non_policy_body_fails_closed(self):
        with self.assertRaises(AdapterError):
            nz_election_rss_access_policy("<html>Request rejected</html>")

    @patch("world_signals.adapters.nz_election_rss.fetch_bytes")
    def test_perimeter_block_is_classified_as_access_failure(self, mock_fetch):
        body = b"<html><iframe>Request unsuccessful. Incapsula incident ID: fixture</iframe></html>"
        mock_fetch.return_value = (
            body,
            FetchSnapshot(
                url="https://elections.nz/media-and-news/rss",
                resolved_url="https://elections.nz/media-and-news/rss",
                status=200,
                content_type="text/html",
                body_sha256="fixture",
                body_bytes=len(body),
            ),
        )
        with self.assertRaisesRegex(AdapterError, "blocked by perimeter security"):
            fetch_nz_election_rss()


class NZElectionRSSComparatorTests(unittest.TestCase):
    def test_absent_timetable_page_generates_no_candidate_and_no_event_state(self):
        candidates, observations = nz_election_timetable_change_review_candidates(
            records(), parse_nz_election_rss(rss_document()), config()
        )
        self.assertEqual(candidates, [])
        healthy = [o for o in observations if o["type"] == "NZ_ELECTION_TIMETABLE_SENTINEL_HEALTHY_ROLLING_WINDOW_OBSERVATION"]
        self.assertEqual(len(healthy), 1)
        self.assertTrue(healthy[0]["absence_is_not_evidence_page_unchanged"])
        self.assertEqual(healthy[0]["event_state_inference"], "NONE")

    def test_exact_timetable_page_generates_one_six_occurrence_bundle_review(self):
        candidates, observations = nz_election_timetable_change_review_candidates(
            records(), parse_nz_election_rss(rss_document(target_index=2)), config()
        )
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["candidate_type"], "NZ_ELECTION_TIMETABLE_PAGE_UPDATED_REVIEW")
        self.assertEqual(candidate["occurrence_ids"], [f"WSO-EL-A-{n:04d}" for n in range(5, 11)])
        self.assertTrue(candidate["bundle_review_required"])
        self.assertIsNone(candidate["proposed_canonical_date_changes"])
        self.assertFalse(candidate["new_value"]["rss_pubdate_is_event_time"])
        self.assertFalse(candidate["new_value"]["timetable_html_fetched"])
        self.assertFalse(candidate["automatic_timetable_html_fetch_allowed"])
        self.assertFalse(candidate["automatic_commit_allowed"])
        self.assertEqual(candidate["event_state_inference"], "NONE")
        self.assertTrue(any(o["type"] == "NZ_ELECTION_TIMETABLE_PAGE_UPDATE_OBSERVED_REVIEW_REQUIRED" for o in observations))

    def test_general_election_news_dates_are_not_timetable_change_evidence(self):
        candidates, _ = nz_election_timetable_change_review_candidates(
            records(), parse_nz_election_rss(rss_document()), config()
        )
        self.assertEqual(candidates, [])

    def test_duplicate_target_items_fail_closed_at_comparator(self):
        target = NZElectionRSSItem(
            title="Key dates",
            link=NZ_ELECTION_TIMETABLE_URL,
            description="updated",
            pub_date_raw="Mon, 07 Sep 2026 13:19:33 +1200",
            pub_date_iso="2026-09-07T13:19:33+12:00",
            guid=NZ_ELECTION_TIMETABLE_URL,
        )
        with self.assertRaises(ValueError):
            nz_election_timetable_change_review_candidates(records(), [target, target], config())

    def test_runtime_comparator_accepts_reviewed_descendant_date_without_using_it_as_feed_identity(self):
        canonical = records()
        canonical[0]["start_local"] = "2026-10-02"
        candidates, _ = nz_election_timetable_change_review_candidates(
            canonical, parse_nz_election_rss(rss_document(target_index=1)), config()
        )
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["old_value"][0]["start_local"], "2026-10-02")

    def test_gate_drift_fails_closed(self):
        cfg = config()
        cfg["automatic_timetable_html_fetch_allowed"] = True
        with self.assertRaises(ValueError):
            nz_election_timetable_change_review_candidates(
                records(), parse_nz_election_rss(rss_document()), cfg
            )

    def test_canonical_shape_drift_fails_closed(self):
        canonical = records()
        canonical[0]["timing_type"] = "LOCAL_DATETIME"
        with self.assertRaises(ValueError):
            nz_election_timetable_change_review_candidates(
                canonical, parse_nz_election_rss(rss_document()), config()
            )

    def test_comparator_does_not_mutate_inputs(self):
        canonical = records()
        items = parse_nz_election_rss(rss_document(target_index=4))
        cfg = config()
        before = (copy.deepcopy(canonical), list(items), copy.deepcopy(cfg))
        nz_election_timetable_change_review_candidates(canonical, items, cfg)
        self.assertEqual(canonical, before[0])
        self.assertEqual(items, before[1])
        self.assertEqual(cfg, before[2])


if __name__ == "__main__":
    unittest.main()
