from __future__ import annotations

import json
from pathlib import Path
import unittest

from src.world_signals.adapters.base import AdapterError
from src.world_signals.adapters.fed_monetary_rss import (
    FedMonetaryRSSItem,
    parse_fed_monetary_policy_rss,
)
from src.world_signals.fed_monetary_monitor import (
    DECISION_SERIES,
    MINUTES_SERIES,
    classify_fed_monetary_item,
    fed_monetary_rss_review_candidates,
)

ROOT = Path(__file__).resolve().parents[1]
PLAN = json.loads((ROOT / "data/monitor/FED_MONETARY_RSS_MONITOR_BP_PLAN_v0.1.json").read_text())
CANONICAL = json.loads((ROOT / "data/canonical/registry.json").read_text())


def _config() -> dict:
    return {
        "adapter_id": "FED_MONETARY_POLICY_RSS",
        "source_id": "WSSRC-CB-015",
        "canonical_occurrence_ids": [row["occurrence_id"] for row in PLAN["tracked_publications"]],
        "matching": {"timestamp_tolerance_minutes": 180},
        "automatic_commit_allowed": False,
    }


def _item(title: str, pub_date_utc: str, suffix: str = "x") -> FedMonetaryRSSItem:
    url = f"https://www.federalreserve.gov/newsevents/pressreleases/monetary{suffix}.htm"
    return FedMonetaryRSSItem(
        title=title,
        description=title,
        link=url,
        guid=url,
        pub_date_utc=pub_date_utc,
    )


RSS_FIXTURE = b'''<?xml version="1.0"?>
<rss version="2.0"><channel><title>Federal Reserve: Monetary Policy</title>
<item><title>Federal Reserve issues FOMC statement</title>
<link>https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm</link>
<guid>https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm</guid>
<description>Federal Reserve issues FOMC statement</description>
<pubDate>Wed, 16 Sep 2026 18:00:00 GMT</pubDate></item>
<item><title>Minutes of the Federal Open Market Committee, September 15-16, 2026</title>
<link>https://www.federalreserve.gov/newsevents/pressreleases/monetary20261007a.htm</link>
<guid>https://www.federalreserve.gov/newsevents/pressreleases/monetary20261007a.htm</guid>
<description>Minutes of the Federal Open Market Committee, September 15-16, 2026</description>
<pubDate>Wed, 7 Oct 2026 18:00:00 GMT</pubDate></item>
</channel></rss>'''


class FedMonetaryRSSBPTests(unittest.TestCase):
    def test_rss_parser_normalises_timezone_aware_publication_times(self):
        items = parse_fed_monetary_policy_rss(RSS_FIXTURE)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].pub_date_utc, "2026-09-16T18:00:00Z")
        self.assertEqual(items[1].pub_date_utc, "2026-10-07T18:00:00Z")
        self.assertEqual(classify_fed_monetary_item(items[0]), DECISION_SERIES)
        self.assertEqual(classify_fed_monetary_item(items[1]), MINUTES_SERIES)

    def test_rss_parser_fails_closed_on_malformed_root_external_host_and_conflicting_guid(self):
        with self.assertRaises(AdapterError):
            parse_fed_monetary_policy_rss(b"<feed></feed>")
        external = RSS_FIXTURE.replace(
            b"https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm",
            b"https://example.com/not-fed",
            1,
        )
        with self.assertRaises(AdapterError):
            parse_fed_monetary_policy_rss(external)
        duplicate = RSS_FIXTURE.replace(
            b"</channel>",
            b'''<item><title>Different payload</title><link>https://www.federalreserve.gov/other.htm</link><guid>https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm</guid><description>Different payload</description><pubDate>Wed, 16 Sep 2026 18:01:00 GMT</pubDate></item></channel>''',
        )
        with self.assertRaises(AdapterError):
            parse_fed_monetary_policy_rss(duplicate)

    def test_exact_summer_statement_and_minutes_publications_create_review_candidates_only(self):
        items = [
            _item("Federal Reserve issues FOMC statement", "2026-09-16T18:00:00Z", "20260916a"),
            _item("Minutes of the Federal Open Market Committee, September 15-16, 2026", "2026-10-07T18:00:00Z", "20261007a"),
        ]
        candidates, observations = fed_monetary_rss_review_candidates(CANONICAL["records"], items, _config())
        self.assertEqual(len(candidates), 2)
        self.assertEqual({c["occurrence_ids"][0] for c in candidates}, {"WSO-08f11832f0335c85", "WSO-9eba0c2ef8365a9f"})
        self.assertTrue(all(c["candidate_type"] == "FED_FOMC_PUBLICATION_EVIDENCE_AVAILABLE" for c in candidates))
        self.assertTrue(all(c["review_state"] == "PENDING_AUTHORITATIVE_FOMC_PUBLICATION_REVIEW" for c in candidates))
        self.assertTrue(all(c["event_state_inference"] == "NONE" for c in candidates))
        self.assertTrue(all(c["automatic_commit_allowed"] is False for c in candidates))
        matched = [o for o in observations if o["type"] == "FED_FOMC_RSS_PUBLICATION_MATCHED_REVIEW_REQUIRED"]
        self.assertEqual({o["timestamp_delta_seconds"] for o in matched}, {0})

    def test_winter_timezone_mapping_uses_est_not_fixed_utc_offset(self):
        item = _item("Federal Reserve issues FOMC statement", "2026-12-09T19:00:00Z", "20261209a")
        candidates, _ = fed_monetary_rss_review_candidates(CANONICAL["records"], [item], _config())
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["occurrence_ids"], ["WSO-723fbab6b29755d8"])

    def test_historical_publication_is_observation_only_and_feed_absence_is_nonsemantic(self):
        item = _item("Federal Reserve issues FOMC statement", "2026-07-29T18:00:00Z", "20260729a")
        candidates, observations = fed_monetary_rss_review_candidates(CANONICAL["records"], [item], _config())
        self.assertEqual(candidates, [])
        self.assertTrue(any(o["type"] == "FED_FOMC_RSS_PUBLICATION_OUTSIDE_CONFIGURED_SCOPE" for o in observations))
        absence = next(o for o in observations if o["type"] == "FED_FOMC_RSS_ABSENCE_HAS_NO_SCHEDULE_OR_LIFECYCLE_SEMANTICS")
        self.assertEqual(absence["event_state_inference"], "NONE")
        self.assertFalse(absence["automatic_commit_allowed"])

    def test_unclassified_fomc_item_is_nonsemantic(self):
        item = _item("FOMC announces a technical note", "2026-09-16T18:00:00Z", "technical")
        candidates, observations = fed_monetary_rss_review_candidates(CANONICAL["records"], [item], _config())
        self.assertEqual(candidates, [])
        unclassified = next(o for o in observations if o["type"] == "FED_FOMC_RSS_ITEM_UNCLASSIFIED_NO_EVENT_INFERENCE")
        self.assertEqual(unclassified["event_state_inference"], "NONE")

    def test_duplicate_feed_publications_mapping_to_one_occurrence_fail_closed(self):
        items = [
            _item("Federal Reserve issues FOMC statement", "2026-09-16T18:00:00Z", "a"),
            _item("Federal Reserve issues FOMC statement", "2026-09-16T18:01:00Z", "b"),
        ]
        with self.assertRaises(ValueError):
            fed_monetary_rss_review_candidates(CANONICAL["records"], items, _config())

    def test_plan_scope_is_exact_and_preserves_html_schedule_authority(self):
        rows = [r for r in CANONICAL["records"] if r.get("occurrence_id") in {x["occurrence_id"] for x in PLAN["tracked_publications"]}]
        self.assertEqual(len(rows), 22)
        self.assertEqual(sum(r["series_id"] == DECISION_SERIES for r in rows), 11)
        self.assertEqual(sum(r["series_id"] == MINUTES_SERIES for r in rows), 11)
        self.assertEqual({r["source_id"] for r in rows}, {"WSSRC-CB-001"})
        self.assertEqual({r["source_timezone"] for r in rows}, {"America/New_York"})
        self.assertEqual({r["time_precision"] for r in rows}, {"MINUTE"})
        self.assertEqual(PLAN["source_role_contract"]["machine_source_canonical_dependency_count"], 0)
        self.assertTrue(PLAN["source_role_contract"]["html_schedule_endpoint_permission_hold_preserved"])


if __name__ == "__main__":
    unittest.main()
