from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from world_signals.adapters.base import AdapterError, FetchSnapshot
from world_signals.adapters.fao_release_calendar import (
    FAO_CALENDAR_URL,
    FAO_ROBOTS_URL,
    fao_calendar_allowed,
    fetch_fao_release_calendar,
    fetch_fao_robots_policy,
    parse_fao_release_calendar,
)
from world_signals.fao_release_monitor import fao_release_calendar_review_candidates


MONTHS = ["October 2026", "November 2026", "December 2026"]


def calendar_html(*, omit: tuple[str, str] | None = None, duplicate: tuple[str, str] | None = None,
                  cross_month: tuple[str, str] | None = None) -> str:
    dates = {
        "October 2026": {"FFPI": "2 October", "AMIS": "2 October"},
        "November 2026": {"FFPI": "6 November", "AMIS": "6 November"},
        "December 2026": {"FFPI": "4 December", "AMIS": "4 December"},
    }
    labels = {
        "FFPI": "FAO Food Price Index and Commodity Price Indices",
        "AMIS": "AMIS Market Monitor",
    }
    parts = ["<!doctype html><html><body><h1>Statistics</h1><h2>2026 Calendar of Data Releases</h2>"]
    for month in MONTHS:
        parts.append(f"<h3>{month}</h3>")
        for product in ("FFPI", "AMIS"):
            if omit == (month, product):
                continue
            visible_date = dates[month][product]
            if cross_month == (month, product):
                visible_date = "30 September"
            row = f"<p>{labels[product]} ({visible_date})</p>"
            parts.append(row)
            if duplicate == (month, product):
                parts.append(row)
    parts.append("<div>" + ("background filler " * 1000) + "</div></body></html>")
    return "".join(parts)


def config() -> dict:
    identity = {}
    rows = [
        ("WSO-COM-A-0042", "WSER-COM-FAO-FFPI", "FFPI", "October 2026"),
        ("WSO-COM-A-0043", "WSER-COM-AMIS", "AMIS", "October 2026"),
        ("WSO-COM-A-0044", "WSER-COM-FAO-FFPI", "FFPI", "November 2026"),
        ("WSO-COM-A-0045", "WSER-COM-AMIS", "AMIS", "November 2026"),
        ("WSO-COM-A-0046", "WSER-COM-FAO-FFPI", "FFPI", "December 2026"),
        ("WSO-COM-A-0047", "WSER-COM-AMIS", "AMIS", "December 2026"),
    ]
    for oid, series, product, month in rows:
        identity[oid] = {"series_id": series, "product_key": product, "slot_month": month}
    return {
        "adapter_id": "FAO_RELEASE_CALENDAR",
        "source_id": "WSSRC-COM-010",
        "canonical_schedule_source_id": "WSSRC-COM-010",
        "canonical_occurrence_ids": [x[0] for x in rows],
        "identity_by_occurrence_id": identity,
        "configured_month_sections": MONTHS,
        "request_budget_per_run": 2,
        "robots_requests_per_run": 1,
        "calendar_requests_per_run": 1,
        "followup_requests_per_run": 0,
        "schedule_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "canonical_clock_mutation_allowed": False,
        "automatic_amis_followup_allowed": False,
        "automatic_faostat_followup_allowed": False,
        "automatic_pdf_fetch_allowed": False,
        "automatic_news_followup_allowed": False,
        "automatic_search_route_discovery_allowed": False,
        "automatic_commit_allowed": False,
    }


def canonical_records() -> list[dict]:
    rows = []
    dates = {
        "WSO-COM-A-0042": "2026-10-02",
        "WSO-COM-A-0043": "2026-10-02",
        "WSO-COM-A-0044": "2026-11-06",
        "WSO-COM-A-0045": "2026-11-06",
        "WSO-COM-A-0046": "2026-12-04",
        "WSO-COM-A-0047": "2026-12-04",
    }
    for oid, identity in config()["identity_by_occurrence_id"].items():
        rows.append({
            "occurrence_id": oid,
            "series_id": identity["series_id"],
            "source_id": "WSSRC-COM-010",
            "region": "Cross-regional / Global",
            "source_timezone": "Europe/Rome",
            "time_precision": "DAY",
            "timing_type": "CIVIL_DATE",
            "all_day_semantics": True,
            "start_local": dates[oid],
            "start_utc": None,
            "lifecycle_status": "PLANNED",
            "certainty_status": "CONFIRMED",
        })
    return rows


class FAOReleaseCalendarParserTests(unittest.TestCase):
    def test_parser_returns_exact_six_configured_rows(self) -> None:
        rows = parse_fao_release_calendar(calendar_html(), configured_month_sections=MONTHS)
        self.assertEqual(len(rows), 6)
        keyed = {(r.slot_month, r.product_key): r.release_date for r in rows}
        self.assertEqual(keyed[("October 2026", "FFPI")], "2026-10-02")
        self.assertEqual(keyed[("October 2026", "AMIS")], "2026-10-02")
        self.assertEqual(keyed[("November 2026", "FFPI")], "2026-11-06")
        self.assertEqual(keyed[("December 2026", "AMIS")], "2026-12-04")
        self.assertTrue(all(r.time_precision == "DAY" for r in rows))

    def test_missing_product_row_is_not_parser_failure(self) -> None:
        rows = parse_fao_release_calendar(
            calendar_html(omit=("November 2026", "AMIS")),
            configured_month_sections=MONTHS,
        )
        self.assertEqual(len(rows), 5)

    def test_duplicate_product_row_fails_closed(self) -> None:
        with self.assertRaises(AdapterError):
            parse_fao_release_calendar(
                calendar_html(duplicate=("October 2026", "FFPI")),
                configured_month_sections=MONTHS,
            )

    def test_cross_month_visible_date_fails_closed(self) -> None:
        with self.assertRaises(AdapterError):
            parse_fao_release_calendar(
                calendar_html(cross_month=("October 2026", "FFPI")),
                configured_month_sections=MONTHS,
            )

    def test_missing_month_section_is_structural_failure(self) -> None:
        html = calendar_html().replace("<h3>November 2026</h3>", "")
        with self.assertRaises(AdapterError):
            parse_fao_release_calendar(html, configured_month_sections=MONTHS)

    def test_rejection_body_is_not_accepted_as_calendar(self) -> None:
        with self.assertRaises(AdapterError):
            parse_fao_release_calendar(
                "<html><body><h1>Request Rejected</h1></body></html>",
                configured_month_sections=MONTHS,
            )

    def test_valid_robots_policy_allows_calendar(self) -> None:
        robots = "User-agent: *\nDisallow: /index.php\nDisallow: /typo3/\n"
        self.assertTrue(fao_calendar_allowed(robots))

    def test_html_masquerading_as_robots_fails_closed(self) -> None:
        with self.assertRaises(AdapterError):
            fao_calendar_allowed("<html><body>Request Rejected</body></html>")

    @patch("world_signals.adapters.fao_release_calendar.fetch_bytes")
    def test_fetch_robots_requires_plain_text(self, fetch_mock) -> None:
        fetch_mock.return_value = (
            b"User-agent: *\nDisallow:\n",
            FetchSnapshot(FAO_ROBOTS_URL, FAO_ROBOTS_URL, 200, "text/html", "x", 25),
        )
        with self.assertRaises(AdapterError):
            fetch_fao_robots_policy()

    @patch("world_signals.adapters.fao_release_calendar.fetch_bytes")
    def test_fetch_calendar_rejects_tiny_waf_body(self, fetch_mock) -> None:
        body = b"<html><body>Request Rejected</body></html>"
        fetch_mock.return_value = (
            body,
            FetchSnapshot(FAO_CALENDAR_URL, FAO_CALENDAR_URL, 200, "text/html", "x", len(body)),
        )
        with self.assertRaises(AdapterError):
            fetch_fao_release_calendar(MONTHS)


class FAOReleaseCalendarComparatorTests(unittest.TestCase):
    def test_exact_matches_generate_no_candidates(self) -> None:
        releases = parse_fao_release_calendar(calendar_html(), configured_month_sections=MONTHS)
        candidates, observations = fao_release_calendar_review_candidates(canonical_records(), releases, config())
        self.assertEqual(candidates, [])
        self.assertEqual(sum(o["type"] == "FAO_RELEASE_DATE_MATCH_OBSERVATION" for o in observations), 6)
        self.assertEqual(observations[-1]["type"], "FAO_RELEASE_CALENDAR_HAS_NO_COMPLETION_CERTAINTY_CLOCK_OR_DIRECT_WRITE_AUTHORITY")

    def test_date_change_targets_same_occurrence_identity(self) -> None:
        records = canonical_records()
        records[0]["start_local"] = "2026-10-01"
        releases = parse_fao_release_calendar(calendar_html(), configured_month_sections=MONTHS)
        candidates, _ = fao_release_calendar_review_candidates(records, releases, config())
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["candidate_type"], "FAO_RELEASE_DATE_CHANGE_REVIEW")
        self.assertEqual(candidate["occurrence_ids"], ["WSO-COM-A-0042"])
        self.assertEqual(candidate["new_value"]["observed_release_date"], "2026-10-02")
        self.assertFalse(candidate["automatic_commit_allowed"])
        self.assertFalse(candidate["lifecycle_mutation_allowed"])

    def test_missing_row_is_review_candidate_not_event_state(self) -> None:
        releases = parse_fao_release_calendar(
            calendar_html(omit=("November 2026", "AMIS")),
            configured_month_sections=MONTHS,
        )
        candidates, observations = fao_release_calendar_review_candidates(canonical_records(), releases, config())
        missing = [c for c in candidates if c["candidate_type"] == "FAO_RELEASE_SLOT_MISSING_REVIEW"]
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]["occurrence_ids"], ["WSO-COM-A-0045"])
        self.assertTrue(missing[0]["absence_is_not_cancellation_completion_or_certainty_change"])
        self.assertEqual(missing[0]["event_state_inference"], "NONE")
        self.assertTrue(any(o["type"] == "FAO_RELEASE_CONFIGURED_SLOT_ABSENT" for o in observations))

    def test_completed_occurrence_is_corroboration_only(self) -> None:
        records = canonical_records()
        records[0]["lifecycle_status"] = "COMPLETED"
        releases = parse_fao_release_calendar(calendar_html(), configured_month_sections=MONTHS)
        candidates, observations = fao_release_calendar_review_candidates(records, releases, config())
        self.assertFalse(any(c["occurrence_ids"] == ["WSO-COM-A-0042"] for c in candidates))
        self.assertTrue(any(o["type"] == "FAO_RELEASE_COMPLETED_OCCURRENCE_CALENDAR_CORROBORATION_ONLY" for o in observations))

    def test_gate_drift_fails_closed(self) -> None:
        cfg = config()
        cfg["automatic_commit_allowed"] = True
        releases = parse_fao_release_calendar(calendar_html(), configured_month_sections=MONTHS)
        with self.assertRaises(ValueError):
            fao_release_calendar_review_candidates(canonical_records(), releases, cfg)

    def test_route_source_identity_is_same_canonical_source(self) -> None:
        cfg = config()
        self.assertEqual(cfg["source_id"], cfg["canonical_schedule_source_id"])
        self.assertEqual(cfg["source_id"], "WSSRC-COM-010")


if __name__ == "__main__":
    unittest.main()
