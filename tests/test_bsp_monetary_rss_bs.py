from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.adapters.base import AdapterError
from world_signals.adapters.bsp_rss import BSPMediaReleaseItem, parse_bsp_media_releases_rss
from world_signals.bsp_monetary_monitor import (
    bsp_monetary_rss_review_candidates,
    is_bsp_monetary_policy_stance_item,
)

PLAN = json.loads((ROOT / "data/monitor/BSP_MONETARY_RSS_BS_PLAN_v0.1.json").read_text())
CANONICAL = json.loads((ROOT / "data/canonical/registry.json").read_text())


def config() -> dict:
    return {
        "adapter_id": "BSP_MONETARY_POLICY_RSS",
        "source_id": "WSSRC-REGJ-006",
        "canonical_occurrence_ids": list(PLAN["canonical_occurrence_ids"]),
        "schedule_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
    }


def item(title: str, *, published: str, body: str) -> BSPMediaReleaseItem:
    return BSPMediaReleaseItem(
        title=title,
        link="https://www.bsp.gov.ph/Lists/Media%20Releases%20and%20Advisories/cDispForm.aspx?ID=9000",
        guid="https://www.bsp.gov.ph/Lists/Media%20Releases%20and%20Advisories/cDispForm.aspx?ID=9000",
        pub_date_utc=published,
        pub_date_original="fixture",
        description_text=body,
    )


STANCE_BODY = (
    "At its monetary policy meeting today, the Monetary Board decided to maintain "
    "the BSP’s Target Reverse Repurchase Rate."
)


class BSPRSSAdapterTests(unittest.TestCase):
    def test_parser_preserves_publication_timestamp_and_normalizes_description(self):
        xml = b'''<rss version="2.0"><channel><item>
        <title>Monetary Board raises target RRP Rate by 25 basis points</title>
        <link>https://www.bsp.gov.ph/Lists/Media%20Releases%20and%20Advisories/cDispForm.aspx?ID=8047</link>
        <guid>https://www.bsp.gov.ph/Lists/Media%20Releases%20and%20Advisories/cDispForm.aspx?ID=8047</guid>
        <pubDate>Thu, 27 Aug 2026 06:23:15 GMT</pubDate>
        <description>&lt;div&gt;&lt;p&gt;At its monetary policy meeting today, the Monetary Board decided to raise the BSP's Target Reverse Repurchase Rate.&lt;/p&gt;&lt;/div&gt;</description>
        </item></channel></rss>'''
        rows = parse_bsp_media_releases_rss(xml)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].pub_date_utc, "2026-08-27T06:23:15Z")
        self.assertIn("At its monetary policy meeting today", rows[0].description_text)
        self.assertTrue(is_bsp_monetary_policy_stance_item(rows[0]))

    def test_parser_rejects_external_item_link(self):
        xml = b'''<rss version="2.0"><channel><item>
        <title>Monetary Board example</title><link>https://example.com/x</link>
        <pubDate>Thu, 22 Oct 2026 06:23:15 GMT</pubDate>
        </item></channel></rss>'''
        with self.assertRaises(AdapterError):
            parse_bsp_media_releases_rss(xml)

    def test_generic_monetary_policy_mentions_do_not_classify_as_stance(self):
        generic = item(
            "Moody's cites PH monetary policy, banking system, external position",
            published="2026-10-22T06:00:00Z",
            body="The BSP continues to pursue sound monetary policy.",
        )
        self.assertFalse(is_bsp_monetary_policy_stance_item(generic))


class BSPMonetaryMonitorTests(unittest.TestCase):
    def test_october_stance_publication_creates_review_candidate_not_completion_or_clock(self):
        stance = item(
            "Monetary Board maintains target RRP Rate",
            published="2026-10-22T06:23:15Z",
            body=STANCE_BODY,
        )
        candidates, observations = bsp_monetary_rss_review_candidates(CANONICAL["records"], [stance], config())
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["candidate_type"], "BSP_MONETARY_POLICY_STANCE_PUBLICATION_EVIDENCE")
        self.assertEqual(candidate["occurrence_ids"], ["WSO-REG-J-0008"])
        self.assertEqual(candidate["event_state_inference"], "NONE")
        self.assertTrue(candidate["completion_requires_review"])
        self.assertFalse(candidate["automatic_commit_allowed"])
        self.assertFalse(candidate["canonical_clock_mutation_allowed"])
        self.assertFalse(candidate["new_value"]["rss_publication_time_is_event_time"])
        self.assertTrue(any(x["type"] == "BSP_MONETARY_POLICY_STANCE_PUBLICATION_MATCHED_REVIEW_REQUIRED" for x in observations))

    def test_manila_civil_date_not_raw_utc_date_controls_identity(self):
        # 16:30 UTC on 21 October is 00:30 on 22 October in Manila.
        stance = item(
            "Monetary Board maintains target RRP Rate",
            published="2026-10-21T16:30:00Z",
            body=STANCE_BODY,
        )
        candidates, _ = bsp_monetary_rss_review_candidates(CANONICAL["records"], [stance], config())
        self.assertEqual(candidates[0]["occurrence_ids"], ["WSO-REG-J-0008"])
        self.assertEqual(candidates[0]["new_value"]["publication_local_date"], "2026-10-22")

    def test_historical_august_stance_release_is_outside_scope_observation_only(self):
        historical = item(
            "Monetary Board raises target RRP Rate by 25 basis points",
            published="2026-08-27T06:23:15Z",
            body=STANCE_BODY,
        )
        candidates, observations = bsp_monetary_rss_review_candidates(CANONICAL["records"], [historical], config())
        self.assertEqual(candidates, [])
        outside = [x for x in observations if x["type"] == "BSP_MONETARY_POLICY_STANCE_PUBLICATION_OUTSIDE_CONFIGURED_SCOPE"]
        self.assertEqual(len(outside), 1)
        self.assertTrue(outside[0]["historical_or_untracked_publication_only"])

    def test_completed_occurrence_is_corroboration_only(self):
        registry = deepcopy(CANONICAL["records"])
        row = next(x for x in registry if x["occurrence_id"] == "WSO-REG-J-0008")
        row["lifecycle_status"] = "COMPLETED"
        stance = item(
            "Monetary Board maintains target RRP Rate",
            published="2026-10-22T06:23:15Z",
            body=STANCE_BODY,
        )
        candidates, observations = bsp_monetary_rss_review_candidates(registry, [stance], config())
        self.assertEqual(candidates, [])
        self.assertTrue(any(x["type"] == "BSP_COMPLETED_OCCURRENCE_STANCE_PUBLICATION_PRESENT_NO_LIFECYCLE_ACTION" for x in observations))

    def test_feed_absence_has_no_event_state_semantics(self):
        candidates, observations = bsp_monetary_rss_review_candidates(CANONICAL["records"], [], config())
        self.assertEqual(candidates, [])
        tail = observations[-1]
        self.assertEqual(tail["type"], "BSP_RSS_ABSENCE_HAS_NO_SCHEDULE_LIFECYCLE_OR_CERTAINTY_SEMANTICS")
        self.assertEqual(tail["event_state_inference"], "NONE")
        self.assertFalse(tail["automatic_commit_allowed"])

    def test_multiple_stance_publications_for_same_occurrence_fail_closed(self):
        a = item("Monetary Board maintains target RRP Rate", published="2026-10-22T06:00:00Z", body=STANCE_BODY)
        b = BSPMediaReleaseItem(
            title="Monetary Board maintains target RRP Rate - update",
            link="https://www.bsp.gov.ph/Lists/Media%20Releases%20and%20Advisories/cDispForm.aspx?ID=9001",
            guid="https://www.bsp.gov.ph/Lists/Media%20Releases%20and%20Advisories/cDispForm.aspx?ID=9001",
            pub_date_utc="2026-10-22T07:00:00Z",
            pub_date_original="fixture",
            description_text=STANCE_BODY,
        )
        with self.assertRaises(ValueError):
            bsp_monetary_rss_review_candidates(CANONICAL["records"], [a, b], config())


if __name__ == "__main__":
    unittest.main()
