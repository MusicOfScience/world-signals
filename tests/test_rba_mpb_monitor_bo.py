from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import scripts.apply_rba_mpb_monitor_bo as tx
from world_signals.adapters.rba_mpb import (
    RBAMeetingWindow,
    RBAMonetaryPolicyCalendar,
    RBAMonetaryPolicyEvent,
)
from world_signals.rba_mpb_monitor import (
    rba_mpb_schedule_review_candidates,
    rba_schedule_path_disallowed,
)


class RBAMPBMonitorBOTests(unittest.TestCase):
    def _fixture(self):
        records = [
            {
                "occurrence_id": "meeting",
                "series_id": "WS.CB.RBA.MPB_MEETING_WINDOW",
                "source_id": "WSSRC-CB-002",
                "source_timezone": "Australia/Sydney",
                "start_local": "2026-09-28",
                "end_local": "2026-09-29",
                "time_precision": "DATE_RANGE",
                "lifecycle_status": "PLANNED",
            },
            {
                "occurrence_id": "decision",
                "series_id": "WS.CB.RBA.MONETARY_POLICY_DECISION",
                "source_id": "WSSRC-CB-002",
                "source_timezone": "Australia/Sydney",
                "start_local": "2026-09-29T14:30:00",
                "end_local": None,
                "time_precision": "MINUTE",
                "lifecycle_status": "PLANNED",
            },
            {
                "occurrence_id": "conference",
                "series_id": "WS.CB.RBA.MPB_PRESS_CONFERENCE",
                "source_id": "WSSRC-CB-002",
                "source_timezone": "Australia/Sydney",
                "start_local": "2026-09-29T15:30:00",
                "end_local": None,
                "time_precision": "MINUTE",
                "lifecycle_status": "PLANNED",
            },
            {
                "occurrence_id": "minutes",
                "series_id": "WS.CB.RBA.MPB_MINUTES",
                "source_id": "WSSRC-CB-013",
                "source_timezone": "Australia/Sydney",
                "start_local": "2026-10-13T11:30:00",
                "end_local": None,
                "time_precision": "MINUTE",
                "lifecycle_status": "PLANNED",
            },
        ]
        config = {
            "source_id": "WSSRC-CB-002",
            "canonical_occurrence_ids": [r["occurrence_id"] for r in records],
            "canonical_source_role_contract": {
                "WS.CB.RBA.MPB_MEETING_WINDOW": "WSSRC-CB-002",
                "WS.CB.RBA.MONETARY_POLICY_DECISION": "WSSRC-CB-002",
                "WS.CB.RBA.MPB_PRESS_CONFERENCE": "WSSRC-CB-002",
                "WS.CB.RBA.MPB_MINUTES": "WSSRC-CB-013",
            },
            "matching": {"nearest_occurrence_max_days": 14},
        }
        events = (
            RBAMonetaryPolicyEvent(
                "MEETING_WINDOW", "WS.CB.RBA.MPB_MEETING_WINDOW",
                "2026-09-28", "2026-09-29", "Australia/Sydney", None, "CIVIL_DATE_RANGE"
            ),
            RBAMonetaryPolicyEvent(
                "DECISION_STATEMENT", "WS.CB.RBA.MONETARY_POLICY_DECISION",
                "2026-09-29T14:30:00", None, "Australia/Sydney", "AEST", "EXACT_LOCAL_TIME"
            ),
            RBAMonetaryPolicyEvent(
                "PRESS_CONFERENCE", "WS.CB.RBA.MPB_PRESS_CONFERENCE",
                "2026-09-29T15:30:00", None, "Australia/Sydney", "AEST", "EXACT_LOCAL_TIME"
            ),
            RBAMonetaryPolicyEvent(
                "MINUTES", "WS.CB.RBA.MPB_MINUTES",
                "2026-10-13T11:30:00", None, "Australia/Sydney", "AEDT", "EXACT_LOCAL_TIME"
            ),
        )
        calendar = RBAMonetaryPolicyCalendar(events=events)
        board = (RBAMeetingWindow("2026-09-28", "2026-09-29"),)
        return records, config, calendar, board

    def test_no_change_preserves_four_distinct_series_and_minutes_source(self):
        records, config, calendar, board = self._fixture()
        candidates, observations = rba_mpb_schedule_review_candidates(
            records, calendar, board, config,
            now_utc=datetime(2026, 9, 8, 6, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(candidates, [])
        no_change = [o for o in observations if o["type"].endswith("NO_CHANGE")]
        self.assertEqual(len(no_change), 4)
        minutes = next(o for o in no_change if o.get("occurrence_id") == "minutes")
        self.assertEqual(minutes["canonical_source_id"], "WSSRC-CB-013")
        self.assertEqual(minutes["monitor_source_id"], "WSSRC-CB-002")

    def test_observed_time_drift_is_review_only(self):
        records, config, calendar, board = self._fixture()
        changed = list(calendar.events)
        changed[1] = RBAMonetaryPolicyEvent(
            "DECISION_STATEMENT", "WS.CB.RBA.MONETARY_POLICY_DECISION",
            "2026-09-29T14:45:00", None, "Australia/Sydney", "AEST", "EXACT_LOCAL_TIME"
        )
        candidates, _ = rba_mpb_schedule_review_candidates(
            records, RBAMonetaryPolicyCalendar(events=tuple(changed)), board, config,
            now_utc=datetime(2026, 9, 8, 6, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["candidate_type"], "RBA_MPB_SCHEDULE_DRIFT")
        self.assertEqual(candidate["occurrence_ids"], ["decision"])
        self.assertEqual(candidate["event_state_inference"], "NONE")
        self.assertFalse(candidate["automatic_commit_allowed"])

    def test_absence_has_no_event_state_semantics(self):
        records, config, _, _ = self._fixture()
        calendar = RBAMonetaryPolicyCalendar(events=())
        candidates, observations = rba_mpb_schedule_review_candidates(
            records, calendar, (), config,
            now_utc=datetime(2026, 9, 8, 6, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(candidates, [])
        absent = [o for o in observations if "NOT_PRESENT" in o["type"]]
        self.assertEqual(len(absent), 4)
        self.assertTrue(all(o["event_state_inference"] == "NONE" for o in absent))
        self.assertTrue(all(o["absence_is_not_cancellation_delay_or_completion"] for o in absent))

    def test_robots_path_policy_fails_closed_on_schedule_prefix(self):
        self.assertFalse(rba_schedule_path_disallowed(("/assets/", "/search/", "/s/")))
        self.assertTrue(rba_schedule_path_disallowed(("/schedules-events/",)))
        self.assertTrue(rba_schedule_path_disallowed(("/",)))

    def test_plan_scope_is_exact_44_with_33_plus_11_source_roles(self):
        plan = json.loads((ROOT / "data/monitor/RBA_MPB_MONITOR_ACTIVATION_BO_PLAN_v0.1.json").read_text())
        canonical = json.loads((ROOT / "data/canonical/registry.json").read_text())
        ids = plan["canonical_occurrence_ids"]
        self.assertEqual(len(ids), 44)
        self.assertEqual(len(set(ids)), 44)
        rows = [r for r in canonical["records"] if r.get("occurrence_id") in set(ids)]
        self.assertEqual(len(rows), 44)
        self.assertEqual(sum(r.get("source_id") == "WSSRC-CB-002" for r in rows), 33)
        self.assertEqual(sum(r.get("source_id") == "WSSRC-CB-013" for r in rows), 11)
        for series, source_id in plan["canonical_source_role_contract"].items():
            self.assertEqual({r["source_id"] for r in rows if r["series_id"] == series}, {source_id})

    def test_transaction_simulation_changes_only_rba_schedule_source_and_appends_one_route(self):
        sources = json.loads((ROOT / "data/sources/registry.json").read_text())
        expectations = json.loads((ROOT / "data/monitor/expectations.json").read_text())
        if sources["version"] != "1.87" or expectations["version"] != "0.12":
            self.skipTest("exact BO transform comparison belongs to post-BN pre-state")
        new_sources, new_expectations, new_live, new_smoke = tx.build_post_state()
        self.assertEqual((new_sources["version"], len(new_sources["sources"])), ("1.88", 247))
        self.assertEqual((new_expectations["version"], len(new_expectations["adapters"])), ("0.13", 11))
        before = {r["source_id"]: r for r in sources["sources"]}
        after = {r["source_id"]: r for r in new_sources["sources"]}
        self.assertEqual([sid for sid in before if before[sid] != after[sid]], ["WSSRC-CB-002"])
        self.assertEqual(before["WSSRC-CB-013"], after["WSSRC-CB-013"])
        self.assertEqual(new_expectations["adapters"][:10], expectations["adapters"])
        route = new_expectations["adapters"][10]
        self.assertEqual(route["adapter_id"], "RBA_MPB_CALENDAR")
        self.assertFalse(route["automatic_commit_allowed"])
        self.assertIn('if "RBA_MPB_CALENDAR" in configs:', new_live)
        self.assertIn('"adapter":"RBA_MPB_CALENDAR"', new_smoke)


if __name__ == "__main__":
    unittest.main()
