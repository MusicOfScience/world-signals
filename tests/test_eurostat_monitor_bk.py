from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import scripts.apply_eurostat_monitor_bk as tx
from world_signals.adapters.eurostat_ics import (
    AdapterError,
    EUROSTAT_ICS_ALL_RELEASES,
    EUROSTAT_ICS_SUBSCRIPTION_PAGE,
    EUROSTAT_TIMEZONE,
    parse_eurostat_release_calendar_ics,
)
from world_signals.eurostat_monitor import eurostat_release_calendar_review_candidates


ICS = """BEGIN:VCALENDAR\r
PRODID:-//Eurostat//Release calendar//EN\r
VERSION:2.0\r
BEGIN:VEVENT\r
UID:hicp-a@example\r
SUMMARY:Inflation (HICP)\r
DTSTART;VALUE=DATE:20260917\r
CATEGORIES:Purple Category\r
END:VEVENT\r
BEGIN:VEVENT\r
UID:trade-sep@example\r
SUMMARY:International trade in goods\r
DTSTART:20260915\r
END:VEVENT\r
BEGIN:VEVENT\r
UID:trade-oct@example\r
SUMMARY:International trade in goods\r
DTSTART:20261016\r
END:VEVENT\r
BEGIN:VEVENT\r
UID:folded@example\r
SUMMARY:GDP main aggregates and employ\r
 ment - update\r
DTSTART:20261020\r
END:VEVENT\r
END:VCALENDAR\r
"""


def record(occurrence_id: str, start_local: str, *, precision: str = "DAY", start_utc=None) -> dict:
    return {
        "occurrence_id": occurrence_id,
        "source_id": "WSSRC-MAC-005",
        "source_timezone": "Europe/Luxembourg",
        "start_local": start_local,
        "start_utc": start_utc,
        "time_precision": precision,
        "certainty_status": "PROVISIONAL",
        "lifecycle_status": "PLANNED",
    }


def config(rows: list[tuple[str, str]], *, max_days: int = 10) -> dict:
    return {
        "adapter_id": "EUROSTAT_RELEASE_CALENDAR_ICS",
        "source_id": "WSSRC-MAC-005",
        "canonical_occurrence_ids": [oid for oid, _ in rows],
        "tracked_items": [{"occurrence_id": oid, "feed_title": title} for oid, title in rows],
        "matching": {"nearest_exact_title_max_days": max_days},
        "automatic_commit_allowed": False,
    }


class EurostatMonitorBKTests(unittest.TestCase):
    def test_official_generator_and_all_category_route_are_frozen(self):
        self.assertEqual(EUROSTAT_ICS_SUBSCRIPTION_PAGE, "https://ec.europa.eu/eurostat/subscribe/ics.format")
        self.assertEqual(
            EUROSTAT_ICS_ALL_RELEASES,
            "https://ec.europa.eu/eurostat/o/calendars/eventsIcal?theme=0&category=0",
        )
        self.assertEqual(EUROSTAT_TIMEZONE, "Europe/Luxembourg")

    def test_parser_unfolds_lines_and_preserves_civil_date_only(self):
        items = parse_eurostat_release_calendar_ics(ICS)
        self.assertEqual(len(items), 4)
        self.assertEqual(items[0].summary, "Inflation (HICP)")
        self.assertEqual(items[0].start_date, "2026-09-17")
        self.assertEqual(items[-1].summary, "GDP main aggregates and employment - update")
        self.assertEqual(items[-1].start_date, "2026-10-20")

    def test_datetime_dtstart_fails_closed_instead_of_manufacturing_precision(self):
        broken = ICS.replace("DTSTART:20260915", "DTSTART:20260915T090000Z", 1)
        with self.assertRaises(AdapterError):
            parse_eurostat_release_calendar_ics(broken)

    def test_exact_title_and_date_yield_no_change_even_when_uid_changes(self):
        items = parse_eurostat_release_calendar_ics(ICS)
        records = [record("WSO-MAC-A-0030", "2026-09-17")]
        cfg = config([("WSO-MAC-A-0030", "Inflation (HICP)")])
        candidates, observations = eurostat_release_calendar_review_candidates(
            records, items, cfg, now_utc=datetime(2026, 9, 8, tzinfo=timezone.utc)
        )
        self.assertEqual(candidates, [])
        self.assertEqual(observations[0]["type"], "EUROSTAT_RELEASE_DATE_NO_CHANGE")
        changed_uid = [deepcopy(item) for item in items]
        object.__setattr__(changed_uid[0], "uid", "completely-different@example")
        candidates2, observations2 = eurostat_release_calendar_review_candidates(
            records, changed_uid, cfg, now_utc=datetime(2026, 9, 8, tzinfo=timezone.utc)
        )
        self.assertEqual(candidates2, [])
        self.assertEqual(observations2[0]["type"], "EUROSTAT_RELEASE_DATE_NO_CHANGE")

    def test_date_only_feed_never_downgrades_richer_canonical_trade_clock(self):
        items = parse_eurostat_release_calendar_ics(ICS)
        records = [record(
            "WSO-MAC-B-0054",
            "2026-09-15T11:00:00",
            precision="MINUTE",
            start_utc="2026-09-15T09:00:00Z",
        )]
        cfg = config([("WSO-MAC-B-0054", "International trade in goods")])
        candidates, observations = eurostat_release_calendar_review_candidates(
            records, items, cfg, now_utc=datetime(2026, 9, 8, tzinfo=timezone.utc)
        )
        self.assertEqual(candidates, [])
        obs = observations[0]
        self.assertEqual(obs["feed_time_precision"], "DAY")
        self.assertEqual(obs["canonical_time_precision"], "MINUTE")
        self.assertEqual(obs["canonical_civil_date"], "2026-09-15")

    def test_date_drift_is_review_only_and_preserves_clock_for_review(self):
        items = parse_eurostat_release_calendar_ics(ICS)
        records = [record(
            "WSO-MAC-B-0054",
            "2026-09-16T11:00:00",
            precision="MINUTE",
            start_utc="2026-09-16T09:00:00Z",
        )]
        cfg = config([("WSO-MAC-B-0054", "International trade in goods")])
        candidates, observations = eurostat_release_calendar_review_candidates(
            records, items, cfg, now_utc=datetime(2026, 9, 8, tzinfo=timezone.utc)
        )
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["candidate_type"], "EUROSTAT_RELEASE_DATE_DRIFT")
        self.assertFalse(candidate["automatic_commit_allowed"])
        self.assertEqual(candidate["event_state_inference"], "NONE")
        self.assertEqual(candidate["new_value"]["canonical_start_local_preserved_for_review"], "2026-09-16T11:00:00")
        self.assertEqual(candidate["new_value"]["canonical_start_utc_preserved_for_review"], "2026-09-16T09:00:00Z")
        self.assertEqual(observations[0]["type"], "EUROSTAT_RELEASE_DATE_DRIFT_REVIEW_REQUIRED")

    def test_absence_and_ambiguity_fail_to_review_not_event_state(self):
        items = parse_eurostat_release_calendar_ics(ICS)
        absent_records = [record("X", "2026-10-10")]
        absent_cfg = config([("X", "Not in feed")])
        candidates, _ = eurostat_release_calendar_review_candidates(
            absent_records, items, absent_cfg, now_utc=datetime(2026, 9, 8, tzinfo=timezone.utc)
        )
        self.assertEqual(candidates[0]["candidate_type"], "EUROSTAT_TRACKED_ITEM_ABSENT_OR_OUTSIDE_MATCH_WINDOW")
        self.assertEqual(candidates[0]["event_state_inference"], "NONE")

        duplicate = list(items) + [items[0]]
        ambig_records = [record("Y", "2026-09-17")]
        ambig_cfg = config([("Y", "Inflation (HICP)")])
        candidates2, _ = eurostat_release_calendar_review_candidates(
            ambig_records, duplicate, ambig_cfg, now_utc=datetime(2026, 9, 8, tzinfo=timezone.utc)
        )
        self.assertEqual(candidates2[0]["candidate_type"], "EUROSTAT_TRACKED_ITEM_IDENTITY_AMBIGUOUS")

    def test_elapsed_occurrence_is_not_presence_checked(self):
        records = [record("OLD", "2026-09-04")]
        cfg = config([("OLD", "Retail trade")])
        candidates, observations = eurostat_release_calendar_review_candidates(
            records, [], cfg, now_utc=datetime(2026, 9, 8, tzinfo=timezone.utc)
        )
        self.assertEqual(candidates, [])
        self.assertEqual(observations[0]["type"], "EUROSTAT_TRACKED_OCCURRENCE_ELAPSED_NOT_PRESENCE_CHECKED")

    def test_tracked_scope_must_exactly_equal_configured_occurrences(self):
        records = [record("A", "2026-09-17")]
        cfg = config([("A", "Inflation (HICP)")])
        cfg["canonical_occurrence_ids"].append("B")
        with self.assertRaises(ValueError):
            eurostat_release_calendar_review_candidates(records, [], cfg)

    def test_bk_pre_or_post_state_contract_and_mutation_boundary(self):
        sources = json.loads((ROOT / "data/sources/registry.json").read_text())
        expectations = json.loads((ROOT / "data/monitor/expectations.json").read_text())
        pre_transaction = sources["version"] == "1.83" and expectations["version"] == "0.10"

        if pre_transaction:
            post_sources, post_expectations, live, smoke, adapter_init = tx.build_post_state()
            pre_by_id = {row["source_id"]: row for row in sources["sources"]}
            post_by_id = {row["source_id"]: row for row in post_sources["sources"]}
            self.assertEqual(set(pre_by_id), set(post_by_id))
            for source_id in pre_by_id:
                if source_id != "WSSRC-MAC-005":
                    self.assertEqual(post_by_id[source_id], pre_by_id[source_id], source_id)
            self.assertEqual(post_expectations["adapters"][:8], expectations["adapters"])
        else:
            self.assertEqual(sources["version"], "1.84")
            self.assertEqual(expectations["version"], "0.11")
            post_sources, post_expectations = sources, expectations
            live = (ROOT / "scripts/run_live_monitor.py").read_text()
            smoke = (ROOT / "scripts/run_adapter_smoke.py").read_text()
            adapter_init = (ROOT / "src/world_signals/adapters/__init__.py").read_text()

        self.assertEqual(len(post_sources["sources"]), 246)
        self.assertEqual(len(post_expectations["adapters"]), 9)
        eurostat = next(row for row in post_sources["sources"] if row["source_id"] == "WSSRC-MAC-005")
        self.assertEqual(eurostat["automated_monitoring_use"], "CLEARED")
        self.assertEqual(eurostat["live_adapter_id"], "EUROSTAT_RELEASE_CALENDAR_ICS")
        self.assertEqual(eurostat["monitoring_activation_status"], "LIVE_READ_ONLY_REVIEW_MONITOR_NO_AUTO_COMMIT")
        endpoint = next(row for row in eurostat["monitor_endpoints"] if row.get("url") == tx.EUROSTAT_ENDPOINT)
        self.assertTrue(endpoint["preferred_for_monitoring"])
        self.assertEqual(endpoint["semantic_format"], "RFC5545_VCALENDAR")
        adapter = next(row for row in post_expectations["adapters"] if row["adapter_id"] == "EUROSTAT_RELEASE_CALENDAR_ICS")
        self.assertEqual(adapter["canonical_occurrence_ids"], [oid for oid, _ in tx.EUROSTAT_TRACKED])
        self.assertFalse(adapter["automatic_commit_allowed"])
        self.assertFalse(post_expectations["automatic_canonical_commit"])
        self.assertFalse(post_expectations["google_calendar_write"])
        self.assertIn("EUROSTAT_RELEASE_CALENDAR_ICS", live)
        self.assertIn("EUROSTAT_RELEASE_CALENDAR_ICS", smoke)
        self.assertIn("EUROSTAT_ICS_ALL_RELEASES", adapter_init)

        canonical = json.loads((ROOT / "data/canonical/registry.json").read_text())
        self.assertEqual(canonical["version"], "0.41")
        self.assertEqual(len(canonical["records"]), 689)
        live_data = json.loads((ROOT / "data/live_intelligence/observations.json").read_text())
        analysis = json.loads((ROOT / "data/analysis/event_reviews.json").read_text())
        self.assertEqual(live_data["version"], "0.6")
        self.assertEqual(len(live_data["observations"]), 6)
        self.assertEqual(analysis["version"], "0.17")
        self.assertEqual(len(analysis["reviews"]), 21)


if __name__ == "__main__":
    unittest.main()
