from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.adapters.base import AdapterError
from world_signals.adapters.european_council_rss import (
    EuropeanCouncilRSSItem,
    parse_european_council_meeting_link,
    parse_european_council_meetings_rss,
)
from world_signals.european_council_monitor import european_council_rss_review_candidates


def item(guid: str, title: str, path: str, *, description: str = "", updated: str = "") -> str:
    return f"""
    <item>
      <guid>{guid}</guid>
      <link>https://www.consilium.europa.eu{path}</link>
      <title>{title}</title>
      <description>{description}</description>
      <updated>{updated}</updated>
    </item>
    """


def current_items(*, extra: list[str] | None = None, omit_guid: str | None = None) -> bytes:
    rows = [
        ("147805", "European Council", "/en/meetings/european-council/2026/10/15-16/"),
        ("147983", "Informal meeting of heads of state or government", "/en/meetings/european-council/2026/11/13/"),
        ("147844", "European Council", "/en/meetings/european-council/2026/12/17-18/"),
        ("140000", "European Council", "/en/meetings/european-council/2026/06/25-26/"),
    ]
    parts = [item(g, t, p) for g, t, p in rows if g != omit_guid]
    parts.extend(extra or [])
    return (
        "<rss><channel>"
        "<title>Council of the EU</title>"
        "<link>https://www.consilium.europa.eu/</link>"
        "<description></description><language>en</language>"
        + "".join(parts)
        + "</channel></rss>"
    ).encode("utf-8")


def config() -> dict:
    return {
        "adapter_id": "EUROPEAN_COUNCIL_MEETINGS_RSS",
        "source_id": "WSSRC-INT-035",
        "canonical_schedule_source_id": "WSSRC-INT-003",
        "canonical_occurrence_ids": ["WSO-INT-B-0102", "WSO-INT-B-0103", "WSO-INT-B-0104"],
        "configured_guid_to_occurrence": {
            "147805": "WSO-INT-B-0102",
            "147983": "WSO-INT-B-0103",
            "147844": "WSO-INT-B-0104",
        },
        "configured_guid_titles": {
            "147805": "European Council",
            "147983": "Informal meeting of heads of state or government",
            "147844": "European Council",
        },
        "request_budget_per_run": 1,
        "rss_request_count_per_run": 1,
        "robots_request_count_per_run": 0,
        "direct_calendar_html_request_count_per_run": 0,
        "item_followup_request_count_per_run": 0,
        "search_route_discovery_request_count_per_run": 0,
        "machine_access_basis": "OFFICIAL_CONSILIUM_RSS_AUTOMATIC_LOADING_INTERFACE",
        "absence_semantics": "NONE",
        "observed_date_source": "OFFICIAL_RSS_ITEM_LINK_PATH_ONLY",
        "updated_field_is_event_time": False,
        "description_field_is_event_time": False,
        "unconfigured_item_review_floor_local": "2026-09-09",
        "schedule_authority": False,
        "clock_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "canonical_date_mutation_allowed": False,
        "automatic_calendar_html_fetch_allowed": False,
        "automatic_item_link_fetch_allowed": False,
        "automatic_new_occurrence_creation_allowed": False,
        "automatic_search_route_discovery_allowed": False,
        "automatic_live_or_analysis_promotion_allowed": False,
        "automatic_commit_allowed": False,
    }


def records() -> list[dict]:
    rows = [
        ("WSO-INT-B-0102", "European Council", "2026-10-15", "2026-10-16"),
        ("WSO-INT-B-0103", "Informal meeting of EU heads of state or government", "2026-11-13", None),
        ("WSO-INT-B-0104", "European Council", "2026-12-17", "2026-12-18"),
    ]
    out = []
    for oid, name, start, end in rows:
        out.append({
            "occurrence_id": oid,
            "canonical_name": name,
            "series_id": "WSER-INT-EUCO",
            "source_id": "WSSRC-INT-003",
            "source_timezone": "Europe/Brussels",
            "category": "INTERNATIONAL_INSTITUTIONS",
            "region": "Europe",
            "event_type": "INSTITUTIONAL_MEETING",
            "time_precision": "DAY",
            "timing_type": "CIVIL_DATE" if end is None else "MULTI_DAY_LOCAL",
            "all_day_semantics": True,
            "start_local": start,
            "end_local": end,
            "start_utc": None,
            "end_utc": None,
            "lifecycle_status": "PLANNED",
            "certainty_status": "CONFIRMED",
        })
    return out


class EuropeanCouncilRSSAdapterTests(unittest.TestCase):
    def test_parser_accepts_current_contract_without_freezing_item_count(self):
        parsed = parse_european_council_meetings_rss(current_items())
        self.assertEqual(len(parsed), 4)
        configured = {x.guid: x for x in parsed}
        self.assertEqual(configured["147805"].start_local, "2026-10-15")
        self.assertEqual(configured["147805"].end_local, "2026-10-16")
        self.assertEqual(configured["147983"].start_local, "2026-11-13")
        self.assertIsNone(configured["147983"].end_local)
        self.assertEqual(configured["147844"].end_local, "2026-12-18")
        self.assertEqual(configured["147844"].updated, "")

    def test_parser_rejects_malformed_xml(self):
        with self.assertRaises(AdapterError):
            parse_european_council_meetings_rss(b"<rss><channel>")

    def test_parser_rejects_channel_identity_drift(self):
        body = current_items().replace(b"Council of the EU", b"European Commission", 1)
        with self.assertRaises(AdapterError):
            parse_european_council_meetings_rss(body)

    def test_parser_rejects_empty_feed(self):
        body = (
            b"<rss><channel><title>Council of the EU</title>"
            b"<link>https://www.consilium.europa.eu/</link><description></description>"
            b"</channel></rss>"
        )
        with self.assertRaises(AdapterError):
            parse_european_council_meetings_rss(body)

    def test_parser_rejects_off_host_item(self):
        bad = current_items().replace(
            b"https://www.consilium.europa.eu/en/meetings/european-council/2026/10/15-16/",
            b"https://example.com/en/meetings/european-council/2026/10/15-16/",
            1,
        )
        with self.assertRaises(AdapterError):
            parse_european_council_meetings_rss(bad)

    def test_parser_rejects_wrong_meeting_path(self):
        bad = current_items().replace(
            b"/en/meetings/european-council/2026/10/15-16/",
            b"/en/press/press-releases/2026/10/15-16/",
            1,
        )
        with self.assertRaises(AdapterError):
            parse_european_council_meetings_rss(bad)

    def test_parser_rejects_invalid_date(self):
        bad = current_items().replace(b"/2026/11/13/", b"/2026/02/31/", 1)
        with self.assertRaises(AdapterError):
            parse_european_council_meetings_rss(bad)

    def test_parser_rejects_backwards_range(self):
        with self.assertRaises(AdapterError):
            parse_european_council_meeting_link(
                "https://www.consilium.europa.eu/en/meetings/european-council/2026/10/18-17/"
            )

    def test_parser_rejects_duplicate_guid(self):
        duplicate = item("147805", "European Council", "/en/meetings/european-council/2026/10/15-16/")
        with self.assertRaises(AdapterError):
            parse_european_council_meetings_rss(current_items(extra=[duplicate]))

    def test_parser_rejects_non_numeric_guid(self):
        bad = current_items().replace(b"<guid>147805</guid>", b"<guid>euco-147805</guid>", 1)
        with self.assertRaises(AdapterError):
            parse_european_council_meetings_rss(bad)

    def test_parser_rejects_item_field_contract_drift(self):
        bad = current_items().replace(b"<updated></updated>", b"<pubDate></pubDate>", 1)
        with self.assertRaises(AdapterError):
            parse_european_council_meetings_rss(bad)


class EuropeanCouncilRSSComparatorTests(unittest.TestCase):
    def test_current_dates_emit_matches_and_no_candidates(self):
        candidates, observations = european_council_rss_review_candidates(
            records(), parse_european_council_meetings_rss(current_items()), config()
        )
        self.assertEqual(candidates, [])
        matches = [o for o in observations if o["type"] == "EUROPEAN_COUNCIL_RSS_DATE_MATCH_OBSERVATION"]
        self.assertEqual(len(matches), 3)

    def test_same_guid_moved_single_date_generates_review(self):
        body = current_items().replace(b"/2026/11/13/", b"/2026/11/14/", 1)
        candidates, _ = european_council_rss_review_candidates(
            records(), parse_european_council_meetings_rss(body), config()
        )
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["candidate_type"], "EUROPEAN_COUNCIL_RSS_DATE_CHANGE_REVIEW")
        self.assertEqual(candidate["occurrence_id"], "WSO-INT-B-0103")
        self.assertEqual(candidate["old_value"]["start_local"], "2026-11-13")
        self.assertEqual(candidate["new_value"]["start_local"], "2026-11-14")
        self.assertFalse(candidate["automatic_calendar_html_fetch_allowed"])
        self.assertFalse(candidate["canonical_date_mutation_allowed"])

    def test_same_guid_moved_range_generates_review(self):
        body = current_items().replace(b"/2026/10/15-16/", b"/2026/10/22-23/", 1)
        candidates, _ = european_council_rss_review_candidates(
            records(), parse_european_council_meetings_rss(body), config()
        )
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["new_value"]["end_local"], "2026-10-23")

    def test_missing_configured_guid_generates_review_without_event_state(self):
        candidates, _ = european_council_rss_review_candidates(
            records(), parse_european_council_meetings_rss(current_items(omit_guid="147983")), config()
        )
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["candidate_type"], "EUROPEAN_COUNCIL_RSS_CONFIGURED_GUID_MISSING_REVIEW")
        self.assertEqual(candidate["occurrence_id"], "WSO-INT-B-0103")
        self.assertTrue(candidate["absence_is_not_cancellation"])
        self.assertEqual(candidate["event_state_inference"], "NONE")

    def test_missing_completed_guid_does_not_reopen_event_state(self):
        canonical = records()
        canonical[1]["lifecycle_status"] = "COMPLETED"
        candidates, observations = european_council_rss_review_candidates(
            canonical, parse_european_council_meetings_rss(current_items(omit_guid="147983")), config()
        )
        self.assertEqual(candidates, [])
        completed = [o for o in observations if o["type"] == "EUROPEAN_COUNCIL_RSS_COMPLETED_GUID_ABSENCE_OBSERVATION"]
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0]["event_state_inference"], "NONE")

    def test_configured_guid_title_drift_fails_closed(self):
        body = current_items().replace(b"<title>European Council</title>", b"<title>Special summit</title>", 1)
        with self.assertRaises(ValueError):
            european_council_rss_review_candidates(
                records(), parse_european_council_meetings_rss(body), config()
            )

    def test_runtime_comparator_accepts_reviewed_descendant_date(self):
        canonical = records()
        canonical[1]["start_local"] = "2026-11-14"
        body = current_items().replace(b"/2026/11/13/", b"/2026/11/14/", 1)
        candidates, observations = european_council_rss_review_candidates(
            canonical, parse_european_council_meetings_rss(body), config()
        )
        self.assertEqual(candidates, [])
        match = [o for o in observations if o.get("occurrence_id") == "WSO-INT-B-0103" and o["type"] == "EUROPEAN_COUNCIL_RSS_DATE_MATCH_OBSERVATION"]
        self.assertEqual(len(match), 1)
        self.assertEqual(match[0]["current_start_local"], "2026-11-14")

    def test_descendant_range_to_single_day_is_shape_compatible_when_canonical_is_updated(self):
        canonical = records()
        canonical[0]["start_local"] = "2026-10-22"
        canonical[0]["end_local"] = None
        canonical[0]["timing_type"] = "CIVIL_DATE"
        body = current_items().replace(b"/2026/10/15-16/", b"/2026/10/22/", 1)
        candidates, _ = european_council_rss_review_candidates(
            canonical, parse_european_council_meetings_rss(body), config()
        )
        self.assertEqual(candidates, [])

    def test_unconfigured_future_item_is_observation_only(self):
        new_item = item("199999", "European Council", "/en/meetings/european-council/2026/11/30/")
        candidates, observations = european_council_rss_review_candidates(
            records(), parse_european_council_meetings_rss(current_items(extra=[new_item])), config()
        )
        self.assertEqual(candidates, [])
        obs = [o for o in observations if o["type"] == "EUROPEAN_COUNCIL_RSS_UNCONFIGURED_FUTURE_MEETING_OBSERVATION"]
        self.assertEqual(len(obs), 1)
        self.assertEqual(obs[0]["unconfigured_future_item_count"], 1)
        self.assertFalse(obs[0]["automatic_new_occurrence_creation_allowed"])

    def test_unconfigured_historical_item_is_not_future_addition_signal(self):
        candidates, observations = european_council_rss_review_candidates(
            records(), parse_european_council_meetings_rss(current_items()), config()
        )
        self.assertEqual(candidates, [])
        obs = [o for o in observations if o["type"] == "EUROPEAN_COUNCIL_RSS_UNCONFIGURED_FUTURE_MEETING_OBSERVATION"][0]
        self.assertEqual(obs["unconfigured_future_item_count"], 0)

    def test_gate_drift_fails_closed(self):
        cfg = config()
        cfg["automatic_item_link_fetch_allowed"] = True
        with self.assertRaises(ValueError):
            european_council_rss_review_candidates(
                records(), parse_european_council_meetings_rss(current_items()), cfg
            )

    def test_canonical_shape_drift_fails_closed(self):
        canonical = records()
        canonical[0]["source_timezone"] = "Australia/Melbourne"
        with self.assertRaises(ValueError):
            european_council_rss_review_candidates(
                canonical, parse_european_council_meetings_rss(current_items()), config()
            )

    def test_comparator_rejects_duplicate_guid_even_if_parser_is_bypassed(self):
        parsed = parse_european_council_meetings_rss(current_items())
        duplicate = EuropeanCouncilRSSItem(**parsed[0].as_dict())
        with self.assertRaises(ValueError):
            european_council_rss_review_candidates(records(), parsed + [duplicate], config())

    def test_comparator_does_not_mutate_inputs(self):
        canonical = records()
        parsed = parse_european_council_meetings_rss(current_items())
        cfg = config()
        before = (copy.deepcopy(canonical), list(parsed), copy.deepcopy(cfg))
        european_council_rss_review_candidates(canonical, parsed, cfg)
        self.assertEqual(canonical, before[0])
        self.assertEqual(parsed, before[1])
        self.assertEqual(cfg, before[2])


if __name__ == "__main__":
    unittest.main()
