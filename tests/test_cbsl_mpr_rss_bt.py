from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from world_signals.adapters.base import AdapterError
from world_signals.adapters.cbsl_rss import parse_cbsl_mpr_rss
from world_signals.cbsl_monetary_monitor import cbsl_mpr_rss_review_candidates

ROOT = Path(__file__).resolve().parents[1]
PLAN = json.loads((ROOT / "data/monitor/CBSL_MPR_RSS_BT_PLAN_v0.1.json").read_text())
CANONICAL = json.loads((ROOT / "data/canonical/registry.json").read_text())


def item_xml(title: str, filename: str, *, host: str = "www.cbsl.gov.lk", extra: str = "") -> str:
    return (
        "<item>"
        f"<title>{title}</title>"
        f"<link>https://{host}/sites/default/files/cbslweb_documents/press/pr/{filename}</link>"
        "<source>Central Bank of Sri Lanka</source>"
        f"{extra}"
        "</item>"
    )


def feed(*items: str) -> str:
    return "<?xml version='1.0'?><rss><channel>" + "".join(items) + "</channel></rss>"


def config() -> dict:
    return {
        "adapter_id": "CBSL_MONETARY_POLICY_RSS",
        "source_id": "WSSRC-REGJ-007",
        "canonical_occurrence_ids": list(PLAN["canonical_occurrence_ids"]),
        "review_identity_by_occurrence_id": {
            row["occurrence_id"]: {
                "review_number": row["review_number"],
                "year": row["year"],
                "announcement_date": row["announcement_date"],
            }
            for row in PLAN["canonical_occurrences"]
        },
        "schedule_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "rss_has_publication_clock": False,
        "official_link_filename_date_is_clock_time": False,
        "canonical_clock_mutation_allowed": False,
        "automatic_item_link_fetch_allowed": False,
        "automatic_schedule_html_fetch_allowed": False,
        "automatic_commit_allowed": False,
    }


class CBSLRSSParserTests(unittest.TestCase):
    def test_parses_title_and_official_pdf_filename_identity_without_publication_clock(self) -> None:
        items = parse_cbsl_mpr_rss(feed(
            item_xml(
                "Monetary Policy Review - No. 4 of 2026",
                "press_20260722_Monetary_Policy_Review_No_4_2026_e_jKlAA7.pdf",
            ),
            item_xml(
                "Monetary Policy Review - No. 5 of 2026",
                "press_20260930_Monetary_Policy_Review_No_5_2026_e_Ab12Cd.pdf",
            ),
        ))
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].review_number, 4)
        self.assertEqual(items[0].review_year, 2026)
        self.assertEqual(items[0].link_date, "2026-07-22")
        self.assertEqual(items[1].link_date, "2026-09-30")
        self.assertFalse(hasattr(items[0], "pub_date_utc"))

    def test_rejects_title_filename_review_identity_mismatch(self) -> None:
        body = feed(item_xml(
            "Monetary Policy Review - No. 5 of 2026",
            "press_20260930_Monetary_Policy_Review_No_6_2026_e_Ab12Cd.pdf",
        ))
        with self.assertRaises(AdapterError):
            parse_cbsl_mpr_rss(body)

    def test_rejects_official_identity_on_non_cbsl_host(self) -> None:
        body = feed(item_xml(
            "Monetary Policy Review - No. 5 of 2026",
            "press_20260930_Monetary_Policy_Review_No_5_2026_e_Ab12Cd.pdf",
            host="example.com",
        ))
        with self.assertRaises(AdapterError):
            parse_cbsl_mpr_rss(body)

    def test_rejects_item_field_contract_drift(self) -> None:
        body = feed(item_xml(
            "Monetary Policy Review - No. 5 of 2026",
            "press_20260930_Monetary_Policy_Review_No_5_2026_e_Ab12Cd.pdf",
            extra="<pubDate>Wed, 30 Sep 2026 00:00:00 +0530</pubDate>",
        ))
        with self.assertRaises(AdapterError):
            parse_cbsl_mpr_rss(body)

    def test_rejects_filename_without_strict_date_review_contract(self) -> None:
        body = feed(item_xml(
            "Monetary Policy Review - No. 5 of 2026",
            "Monetary_Policy_Review_No_5_2026.pdf",
        ))
        with self.assertRaises(AdapterError):
            parse_cbsl_mpr_rss(body)


class CBSLComparatorTests(unittest.TestCase):
    def parsed_items(self):
        return parse_cbsl_mpr_rss(feed(
            item_xml(
                "Monetary Policy Review - No. 4 of 2026",
                "press_20260722_Monetary_Policy_Review_No_4_2026_e_jKlAA7.pdf",
            ),
            item_xml(
                "Monetary Policy Review - No. 5 of 2026",
                "press_20260930_Monetary_Policy_Review_No_5_2026_e_Ab12Cd.pdf",
            ),
        ))

    def test_exact_review_number_year_and_filename_date_match_generates_review_only_candidate(self) -> None:
        candidates, observations = cbsl_mpr_rss_review_candidates(
            CANONICAL["records"], self.parsed_items(), config()
        )
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["occurrence_ids"], ["WSO-REG-J-0006"])
        self.assertEqual(candidate["candidate_type"], "CBSL_MONETARY_POLICY_REVIEW_PUBLICATION_EVIDENCE")
        self.assertEqual(candidate["event_state_inference"], "NONE")
        self.assertFalse(candidate["automatic_commit_allowed"])
        self.assertTrue(candidate["completion_requires_review"])
        self.assertFalse(candidate["canonical_clock_mutation_allowed"])
        self.assertEqual(candidate["new_value"]["official_link_filename_date"], "2026-09-30")
        self.assertFalse(candidate["new_value"]["official_link_filename_date_is_clock_time"])
        self.assertFalse(candidate["new_value"]["rss_has_publication_clock"])
        self.assertTrue(any(
            row["type"] == "CBSL_MONETARY_POLICY_REVIEW_PUBLICATION_OUTSIDE_CONFIGURED_SCOPE"
            and row["review_number"] == 4
            for row in observations
        ))
        absence = next(row for row in observations if row["type"].startswith("CBSL_RSS_ABSENCE"))
        self.assertEqual(absence["configured_occurrence_count"], 2)
        self.assertEqual(absence["matched_occurrence_count"], 1)

    def test_feed_absence_has_no_event_state_semantics(self) -> None:
        candidates, observations = cbsl_mpr_rss_review_candidates(
            CANONICAL["records"], [], config()
        )
        self.assertEqual(candidates, [])
        self.assertEqual(observations[-1]["matched_occurrence_count"], 0)
        self.assertEqual(observations[-1]["event_state_inference"], "NONE")
        self.assertFalse(observations[-1]["automatic_commit_allowed"])

    def test_multiple_items_mapping_to_one_occurrence_fail_closed(self) -> None:
        item = self.parsed_items()[1]
        with self.assertRaises(ValueError):
            cbsl_mpr_rss_review_candidates(CANONICAL["records"], [item, item], config())

    def test_completed_occurrence_does_not_generate_completion_action(self) -> None:
        records = deepcopy(CANONICAL["records"])
        target = next(row for row in records if row.get("occurrence_id") == "WSO-REG-J-0006")
        target["lifecycle_status"] = "COMPLETED"
        candidates, observations = cbsl_mpr_rss_review_candidates(
            records, [self.parsed_items()[1]], config()
        )
        self.assertEqual(candidates, [])
        self.assertTrue(any(
            row["type"] == "CBSL_COMPLETED_OCCURRENCE_MPR_PUBLICATION_PRESENT_NO_LIFECYCLE_ACTION"
            for row in observations
        ))

    def test_any_authority_gate_drift_fails_closed(self) -> None:
        for key in (
            "schedule_authority",
            "lifecycle_authority",
            "certainty_authority",
            "rss_has_publication_clock",
            "official_link_filename_date_is_clock_time",
            "canonical_clock_mutation_allowed",
            "automatic_item_link_fetch_allowed",
            "automatic_schedule_html_fetch_allowed",
            "automatic_commit_allowed",
        ):
            bad = config()
            bad[key] = True
            with self.subTest(key=key), self.assertRaises(ValueError):
                cbsl_mpr_rss_review_candidates(CANONICAL["records"], [], bad)


if __name__ == "__main__":
    unittest.main()
