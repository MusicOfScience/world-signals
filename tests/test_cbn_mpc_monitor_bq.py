from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import scripts.apply_cbn_mpc_monitor_bq as tx
from world_signals.adapters.base import AdapterError
from world_signals.adapters.cbn_mpc import CBNMPCCalendar, CBNMPCMeeting, parse_cbn_mpc_calendar_html
from world_signals.cbn_mpc_monitor import cbn_calendar_path_allowed, cbn_mpc_schedule_review_candidates

FIXTURE = '''<!doctype html><html><body>
<h2>MPC Meeting Calendar for 2026</h2>
<table>
<tr><th>Months</th><th>Meeting No.</th><th>Day 1</th><th>Day 2</th></tr>
<tr><td>February</td><td>304</td><td>Feb. 23, 2026</td><td>Feb. 24, 2026</td></tr>
<tr><td>May</td><td>305</td><td>May 19, 2026</td><td>May 20, 2026</td></tr>
<tr><td>July</td><td>306</td><td>Jul. 20, 2026</td><td>Jul. 21, 2026</td></tr>
<tr><td>September</td><td>307</td><td>Sep. 21, 2026</td><td>Sep. 22, 2026</td></tr>
<tr><td>November</td><td>308</td><td>Nov. 23, 2026</td><td>Nov. 24, 2026</td></tr>
</table></body></html>'''


class CBNMPCMonitorBQTests(unittest.TestCase):
    def _scope(self):
        canonical = json.loads((ROOT / "data/canonical/registry.json").read_text())
        plan = json.loads((ROOT / "data/monitor/CBN_MPC_MONITOR_BQ_PLAN_v0.1.json").read_text())
        config = {
            "source_id": "WSSRC-CB-014",
            "canonical_occurrence_ids": [row["occurrence_id"] for row in plan["tracked_occurrences"]],
            "meeting_number_by_occurrence_id": {
                row["occurrence_id"]: row["meeting_number"] for row in plan["tracked_occurrences"]
            },
        }
        return canonical["records"], config

    def test_parser_preserves_numbered_two_day_windows_only(self):
        calendar = parse_cbn_mpc_calendar_html(FIXTURE)
        self.assertEqual([row.meeting_number for row in calendar.meetings], [304, 305, 306, 307, 308])
        target = calendar.meetings[-2:]
        self.assertEqual((target[0].start_local, target[0].end_local), ("2026-09-21", "2026-09-22"))
        self.assertEqual((target[1].start_local, target[1].end_local), ("2026-11-23", "2026-11-24"))
        self.assertTrue(all(row.source_timezone == "Africa/Lagos" for row in calendar.meetings))
        self.assertTrue(all(row.time_precision == "DAY_RANGE" for row in calendar.meetings))

    def test_parser_hash_is_semantic_and_duplicate_meeting_fails_closed(self):
        base = parse_cbn_mpc_calendar_html(FIXTURE).schedule_sha256
        marked = FIXTURE.replace("<table>", "<table class='calendar'>", 1).replace("September", "  September  ")
        self.assertEqual(base, parse_cbn_mpc_calendar_html(marked).schedule_sha256)
        duplicate = FIXTURE.replace("<tr><td>November</td>", "<tr><td>November</td>").replace("<td>308</td>", "<td>307</td>", 1)
        with self.assertRaises(AdapterError):
            parse_cbn_mpc_calendar_html(duplicate)

    def test_robots_policy_is_operational_gate_not_blanket_permission(self):
        allowed = "User-agent: *\nAllow: /\nDisallow: /museum/\n"
        blocked = "User-agent: *\nDisallow: /MonetaryPolicy/\n"
        self.assertTrue(cbn_calendar_path_allowed(allowed))
        self.assertFalse(cbn_calendar_path_allowed(blocked))

    def test_exact_future_windows_are_no_change_with_no_event_state(self):
        records, config = self._scope()
        calendar = parse_cbn_mpc_calendar_html(FIXTURE)
        candidates, observations = cbn_mpc_schedule_review_candidates(
            records, calendar, config,
            now_utc=datetime(2026, 9, 8, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(candidates, [])
        no_change = [row for row in observations if row["type"] == "CBN_MPC_MEETING_WINDOW_NO_CHANGE"]
        self.assertEqual({row["meeting_number"] for row in no_change}, {307, 308})
        self.assertTrue(all(row["event_state_inference"] == "NONE" for row in no_change))
        self.assertTrue(all(row["decision_publication_time_inference"] == "PROHIBITED" for row in no_change))

    def test_date_drift_is_review_only(self):
        records, config = self._scope()
        calendar = CBNMPCCalendar(meetings=(
            CBNMPCMeeting(307, "2026-09-22", "2026-09-23"),
            CBNMPCMeeting(308, "2026-11-23", "2026-11-24"),
        ))
        candidates, _ = cbn_mpc_schedule_review_candidates(
            records, calendar, config,
            now_utc=datetime(2026, 9, 8, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["candidate_type"], "CBN_MPC_MEETING_WINDOW_DRIFT")
        self.assertEqual(candidate["occurrence_ids"], ["WSO-CBN-MPC-307"])
        self.assertEqual(candidate["event_state_inference"], "NONE")
        self.assertEqual(candidate["decision_publication_time_inference"], "PROHIBITED")
        self.assertFalse(candidate["automatic_commit_allowed"])

    def test_future_absence_is_review_evidence_not_cancellation_or_delay(self):
        records, config = self._scope()
        calendar = CBNMPCCalendar(meetings=(CBNMPCMeeting(308, "2026-11-23", "2026-11-24"),))
        candidates, _ = cbn_mpc_schedule_review_candidates(
            records, calendar, config,
            now_utc=datetime(2026, 9, 8, 0, 0, tzinfo=timezone.utc),
        )
        absent = next(row for row in candidates if row["candidate_type"].endswith("ABSENT_FROM_CURRENT_CALENDAR"))
        self.assertEqual(absent["occurrence_ids"], ["WSO-CBN-MPC-307"])
        self.assertTrue(absent["absence_is_not_cancellation_delay_completion_or_certainty_change"])
        self.assertEqual(absent["event_state_inference"], "NONE")

    def test_untracked_future_meeting_does_not_expand_scope(self):
        records, config = self._scope()
        calendar = CBNMPCCalendar(meetings=(
            CBNMPCMeeting(307, "2026-09-21", "2026-09-22"),
            CBNMPCMeeting(308, "2026-11-23", "2026-11-24"),
            CBNMPCMeeting(309, "2026-12-14", "2026-12-15"),
        ))
        candidates, observations = cbn_mpc_schedule_review_candidates(
            records, calendar, config,
            now_utc=datetime(2026, 9, 8, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(candidates, [])
        untracked = next(row for row in observations if row["type"] == "CBN_MPC_UNTRACKED_FUTURE_MEETING")
        self.assertEqual(untracked["meeting_number"], 309)
        self.assertTrue(untracked["scope_extension_requires_review"])
        self.assertFalse(untracked["automatic_commit_allowed"])

    def test_transaction_is_one_source_row_plus_one_appended_route(self):
        sources = json.loads((ROOT / "data/sources/registry.json").read_text())
        expectations = json.loads((ROOT / "data/monitor/expectations.json").read_text())
        if sources["version"] != "1.89" or expectations["version"] != "0.14":
            self.skipTest("exact BQ transform comparison belongs to post-BP pre-state")
        post_sources, post_monitor, live, smoke, adapter_init = tx.build_post_state()
        self.assertEqual((post_sources["version"], len(post_sources["sources"])), ("1.90", 248))
        self.assertEqual((post_monitor["version"], len(post_monitor["adapters"])), ("0.15", 13))
        before = {row["source_id"]: row for row in sources["sources"]}
        after = {row["source_id"]: row for row in post_sources["sources"]}
        self.assertEqual([sid for sid in before if before[sid] != after[sid]], ["WSSRC-CB-014"])
        cbn = after["WSSRC-CB-014"]
        self.assertEqual(cbn["canonical_provenance_use"], "CLEARED_CURATED_FACTUAL_METADATA")
        self.assertEqual(cbn["canonical_dependency_count"], 2)
        self.assertEqual(cbn["automated_monitoring_use"], "CLEARED")
        self.assertEqual(cbn["verification_mode"], "AUTOMATED_PILOT")
        self.assertEqual(post_monitor["adapters"][:12], expectations["adapters"])
        route = post_monitor["adapters"][12]
        self.assertEqual(route["adapter_id"], "CBN_MPC_CALENDAR")
        self.assertEqual(route["request_budget_per_run"], 2)
        self.assertEqual(len(route["canonical_occurrence_ids"]), 2)
        self.assertFalse(route["decision_publication_time_authority"])
        self.assertFalse(route["lifecycle_authority"])
        self.assertFalse(route["automatic_commit_allowed"])
        self.assertIn('if "CBN_MPC_CALENDAR" in configs:', live)
        self.assertIn('"adapter":"CBN_MPC_CALENDAR"', smoke)
        self.assertIn("CBN_MPC_CALENDAR_URL", adapter_init)


if __name__ == "__main__":
    unittest.main()
