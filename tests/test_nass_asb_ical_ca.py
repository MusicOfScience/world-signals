from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from world_signals.adapters.base import AdapterError
from world_signals.adapters.nass_asb_ical import NASSASBRelease, parse_nass_asb_ical
from world_signals.nass_asb_monitor import (
    EXPECTED_UID_SUMMARIES,
    EXPECTED_UID_TO_OCCURRENCE,
    nass_asb_ical_review_candidates,
)

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = json.loads((ROOT / "data/canonical/registry.json").read_text(encoding="utf-8"))
PLAN = json.loads((ROOT / "data/monitor/USDA_NASS_ASB_ICAL_CA_PLAN_v0.1.json").read_text(encoding="utf-8"))


def ics_event(uid: str, summary: str, dtstart: str, *, dtstart_lhs: str = "DTSTART", extra: str = "") -> str:
    return (
        "BEGIN:VEVENT\r\n"
        f"UID:{uid}\r\n"
        f"SUMMARY:{summary}\r\n"
        f"{dtstart_lhs}:{dtstart}\r\n"
        "DTEND:20260911T120500\r\n"
        "DTSTAMP:20260101T000000Z\r\n"
        "SEQUENCE:0\r\n"
        f"{extra}"
        "DESCRIPTION:\r\n"
        "END:VEVENT\r\n"
    )


def calendar(*events: str) -> str:
    return "BEGIN:VCALENDAR\r\nVERSION:2.0\r\n" + "".join(events) + "END:VCALENDAR\r\n"


def route_config() -> dict:
    p = PLAN
    identity = p["configured_feed_identity_by_uid"]
    return {
        "adapter_id": "USDA_NASS_ASB_ICAL",
        "source_id": "WSSRC-COM-005",
        "canonical_schedule_source_id": "WSSRC-COM-005",
        "canonical_occurrence_ids": list(p["canonical_occurrence_ids"]),
        "request_budget_per_run": 1,
        "ical_request_count_per_run": 1,
        "robots_request_count_per_run": 0,
        "calendar_html_request_count_per_run": 0,
        "report_followup_request_count_per_run": 0,
        "search_route_discovery_request_count_per_run": 0,
        "machine_access_basis": "OFFICIAL_NASS_ICAL_PLUS_EXPLICIT_NONEXCESSIVE_ROBOT_POLICY_WITH_CONTACT_UA",
        "configured_uid_to_occurrence": {uid: row["occurrence_id"] for uid, row in identity.items()},
        "configured_uid_summaries": {uid: row["expected_summary"] for uid, row in identity.items()},
        "floating_datetime_timezone": "America/New_York",
        "floating_timezone_basis": "FIRST_PARTY_NASS_REPORTS_BY_DATE_PAGES_LABEL_TARGET_RELEASES_ET",
        "dtend_is_event_end": False,
        "dtstamp_is_event_time": False,
        "sequence_is_event_state": False,
        "description_is_event_time": False,
        "absence_semantics": "NONE",
        "unconfigured_item_review_floor_local": "2026-09-09T00:00:00",
        "schedule_authority": False,
        "clock_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "canonical_datetime_mutation_allowed": False,
        "automatic_calendar_html_fetch_allowed": False,
        "automatic_report_followup_allowed": False,
        "automatic_new_occurrence_creation_allowed": False,
        "automatic_search_route_discovery_allowed": False,
        "automatic_live_or_analysis_promotion_allowed": False,
        "automatic_commit_allowed": False,
    }


def configured_items() -> list[NASSASBRelease]:
    out = []
    for uid, row in PLAN["configured_feed_identity_by_uid"].items():
        out.append(
            NASSASBRelease(
                uid=uid,
                summary=row["expected_summary"],
                start_local=row["baseline_start_local"],
                dtstart_raw=row["baseline_start_local"].replace("-", "").replace(":", ""),
                dtend_raw="IGNORED",
                dtstamp_raw="IGNORED",
                sequence_raw="0",
                description="",
            )
        )
    return out


class NASSASBAdapterTests(unittest.TestCase):
    def test_parser_accepts_target_and_ignores_non_target(self):
        uid = "a763c1f5-aef0-435a-a183-2f8191f08d99"
        other = "11111111-1111-4111-8111-111111111111"
        parsed = parse_nass_asb_ical(
            calendar(
                ics_event(other, "Broiler Hatchery", "20260909T150000"),
                ics_event(uid, "Crop Production", "20260911T120000"),
            )
        )
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0].uid, uid)
        self.assertEqual(parsed[0].start_local, "2026-09-11T12:00:00")

    def test_parser_unfolds_rfc5545_lines(self):
        uid = "a763c1f5-aef0-435a-a183-2f8191f08d99"
        raw = calendar(ics_event(uid, "Crop Produc\r\n tion", "20260911T120000"))
        parsed = parse_nass_asb_ical(raw)
        self.assertEqual(parsed[0].summary, "Crop Production")

    def test_parser_rejects_html_rejection_body(self):
        with self.assertRaises(AdapterError):
            parse_nass_asb_ical("<html><body>Access denied</body></html>")

    def test_parser_rejects_missing_vcalendar_boundary(self):
        with self.assertRaises(AdapterError):
            parse_nass_asb_ical(ics_event("a763c1f5-aef0-435a-a183-2f8191f08d99", "Crop Production", "20260911T120000"))

    def test_parser_rejects_unclosed_vevent(self):
        raw = "BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nUID:a763c1f5-aef0-435a-a183-2f8191f08d99\r\nEND:VCALENDAR\r\n"
        with self.assertRaises(AdapterError):
            parse_nass_asb_ical(raw)

    def test_parser_rejects_duplicate_uid_even_across_non_target(self):
        uid = "a763c1f5-aef0-435a-a183-2f8191f08d99"
        with self.assertRaises(AdapterError):
            parse_nass_asb_ical(calendar(ics_event(uid, "Broiler Hatchery", "20260909T150000"), ics_event(uid, "Crop Production", "20260911T120000")))

    def test_parser_rejects_non_uuid_target_uid(self):
        with self.assertRaises(AdapterError):
            parse_nass_asb_ical(calendar(ics_event("not-a-uuid", "Crop Production", "20260911T120000")))

    def test_parser_rejects_missing_target_dtstart(self):
        raw = calendar("BEGIN:VEVENT\r\nUID:a763c1f5-aef0-435a-a183-2f8191f08d99\r\nSUMMARY:Crop Production\r\nEND:VEVENT\r\n")
        with self.assertRaises(AdapterError):
            parse_nass_asb_ical(raw)

    def test_parser_rejects_tzid_parameter_instead_of_guessing_contract_change(self):
        uid = "a763c1f5-aef0-435a-a183-2f8191f08d99"
        with self.assertRaises(AdapterError):
            parse_nass_asb_ical(calendar(ics_event(uid, "Crop Production", "20260911T120000", dtstart_lhs="DTSTART;TZID=America/New_York")))

    def test_parser_rejects_utc_dtstart_instead_of_silently_changing_semantics(self):
        uid = "a763c1f5-aef0-435a-a183-2f8191f08d99"
        with self.assertRaises(AdapterError):
            parse_nass_asb_ical(calendar(ics_event(uid, "Crop Production", "20260911T160000Z")))

    def test_parser_rejects_impossible_civil_datetime(self):
        uid = "a763c1f5-aef0-435a-a183-2f8191f08d99"
        with self.assertRaises(AdapterError):
            parse_nass_asb_ical(calendar(ics_event(uid, "Crop Production", "20260230T120000")))


class NASSASBComparatorTests(unittest.TestCase):
    def setUp(self):
        self.records = deepcopy(CANONICAL["records"])
        self.config = route_config()
        self.items = configured_items()

    def test_exact_current_datetimes_emit_five_matches_and_no_candidates(self):
        candidates, observations = nass_asb_ical_review_candidates(self.records, self.items, self.config)
        self.assertEqual(candidates, [])
        matches = [x for x in observations if x["type"] == "NASS_ASB_ICAL_DATETIME_MATCH_OBSERVATION"]
        self.assertEqual(len(matches), 5)

    def test_dst_conversion_uses_iana_timezone_not_fixed_offset(self):
        _, observations = nass_asb_ical_review_candidates(self.records, self.items, self.config)
        by_id = {x.get("occurrence_id"): x for x in observations if x["type"] == "NASS_ASB_ICAL_DATETIME_MATCH_OBSERVATION"}
        self.assertEqual(by_id["WSO-COM-A-0032"]["observed_start_utc"], "2026-10-09T16:00:00Z")
        self.assertEqual(by_id["WSO-COM-A-0034"]["observed_start_utc"], "2026-11-10T17:00:00Z")

    def test_same_uid_moved_datetime_generates_review_only(self):
        moved = deepcopy(self.items)
        target = next(x for x in moved if x.uid == "7172110f-8719-4672-9026-f708df320e71")
        moved[moved.index(target)] = NASSASBRelease(**{**target.as_dict(), "start_local": "2026-10-10T12:00:00", "dtstart_raw": "20261010T120000"})
        candidates, _ = nass_asb_ical_review_candidates(self.records, moved, self.config)
        self.assertEqual(len(candidates), 1)
        c = candidates[0]
        self.assertEqual(c["candidate_type"], "NASS_ASB_ICAL_DATETIME_CHANGE_REVIEW")
        self.assertEqual(c["occurrence_id"], "WSO-COM-A-0032")
        self.assertEqual(c["new_value"]["start_utc"], "2026-10-10T16:00:00Z")
        self.assertFalse(c["canonical_datetime_mutation_allowed"])
        self.assertEqual(c["event_state_inference"], "NONE")

    def test_missing_configured_uid_is_review_evidence_not_event_state(self):
        items = [x for x in self.items if x.uid != "4b58e729-3b3b-4f2a-a86e-2ee17637ad46"]
        candidates, _ = nass_asb_ical_review_candidates(self.records, items, self.config)
        self.assertEqual(len(candidates), 1)
        c = candidates[0]
        self.assertEqual(c["candidate_type"], "NASS_ASB_ICAL_CONFIGURED_UID_MISSING_REVIEW")
        self.assertTrue(c["absence_is_not_cancellation"])
        self.assertTrue(c["absence_is_not_completion"])
        self.assertTrue(c["absence_is_not_certainty_change"])

    def test_missing_completed_uid_does_not_reopen_event_state(self):
        for row in self.records:
            if row.get("occurrence_id") == "WSO-COM-A-0037":
                row["lifecycle_status"] = "COMPLETED"
        items = [x for x in self.items if x.uid != "4b58e729-3b3b-4f2a-a86e-2ee17637ad46"]
        candidates, observations = nass_asb_ical_review_candidates(self.records, items, self.config)
        self.assertEqual(candidates, [])
        self.assertTrue(any(x["type"] == "NASS_ASB_ICAL_COMPLETED_UID_ABSENCE_OBSERVATION" for x in observations))

    def test_present_completed_uid_is_corroboration_only_even_if_feed_datetime_differs(self):
        for row in self.records:
            if row.get("occurrence_id") == "WSO-COM-A-0037":
                row["lifecycle_status"] = "COMPLETED"
        moved = deepcopy(self.items)
        target = next(x for x in moved if x.uid == "4b58e729-3b3b-4f2a-a86e-2ee17637ad46")
        moved[moved.index(target)] = NASSASBRelease(**{**target.as_dict(), "start_local": "2026-10-01T12:00:00", "dtstart_raw": "20261001T120000"})
        candidates, observations = nass_asb_ical_review_candidates(self.records, moved, self.config)
        self.assertEqual(candidates, [])
        self.assertTrue(any(x["type"] == "NASS_ASB_ICAL_COMPLETED_UID_PRESENCE_OBSERVATION" for x in observations))

    def test_configured_uid_summary_drift_fails_closed(self):
        items = deepcopy(self.items)
        target = items[0]
        items[0] = NASSASBRelease(**{**target.as_dict(), "summary": "Crop Production Revised"})
        with self.assertRaises(ValueError):
            nass_asb_ical_review_candidates(self.records, items, self.config)

    def test_gate_drift_fails_closed(self):
        config = deepcopy(self.config)
        config["automatic_commit_allowed"] = True
        with self.assertRaises(ValueError):
            nass_asb_ical_review_candidates(self.records, self.items, config)

    def test_canonical_utc_drift_fails_closed(self):
        for row in self.records:
            if row.get("occurrence_id") == "WSO-COM-A-0034":
                row["start_utc"] = "2026-11-10T16:00:00Z"
        with self.assertRaises(ValueError):
            nass_asb_ical_review_candidates(self.records, self.items, self.config)

    def test_runtime_comparator_accepts_reviewed_descendant_datetime(self):
        for row in self.records:
            if row.get("occurrence_id") == "WSO-COM-A-0034":
                row["start_local"] = "2026-11-11T12:00:00"
                row["publication_datetime"] = "2026-11-11T12:00:00"
                row["start_utc"] = "2026-11-11T17:00:00Z"
        items = deepcopy(self.items)
        target = next(x for x in items if x.uid == "cf36624c-7ddb-4293-ad32-c52b78d0e299")
        items[items.index(target)] = NASSASBRelease(**{**target.as_dict(), "start_local": "2026-11-11T12:00:00", "dtstart_raw": "20261111T120000"})
        candidates, observations = nass_asb_ical_review_candidates(self.records, items, self.config)
        self.assertEqual(candidates, [])
        self.assertEqual(len([x for x in observations if x["type"] == "NASS_ASB_ICAL_DATETIME_MATCH_OBSERVATION"]), 5)

    def test_duplicate_uid_fails_closed_if_parser_is_bypassed(self):
        items = self.items + [deepcopy(self.items[0])]
        with self.assertRaises(ValueError):
            nass_asb_ical_review_candidates(self.records, items, self.config)

    def test_unconfigured_future_target_is_observation_only(self):
        extra = NASSASBRelease(
            uid="11111111-1111-4111-8111-111111111111",
            summary="Crop Production",
            start_local="2026-12-20T12:00:00",
            dtstart_raw="20261220T120000",
            dtend_raw=None,
            dtstamp_raw=None,
            sequence_raw="0",
            description="",
        )
        candidates, observations = nass_asb_ical_review_candidates(self.records, self.items + [extra], self.config)
        self.assertEqual(candidates, [])
        obs = next(x for x in observations if x["type"] == "NASS_ASB_ICAL_UNCONFIGURED_TARGET_RELEASE_OBSERVATION")
        self.assertEqual(obs["unconfigured_future_target_count"], 1)
        self.assertFalse(obs["automatic_new_occurrence_creation_allowed"])

    def test_unconfigured_historical_target_is_not_addition_signal(self):
        extra = NASSASBRelease(
            uid="11111111-1111-4111-8111-111111111111",
            summary="Grain Stocks",
            start_local="2026-06-30T12:00:00",
            dtstart_raw="20260630T120000",
            dtend_raw=None,
            dtstamp_raw=None,
            sequence_raw="0",
            description="",
        )
        _, observations = nass_asb_ical_review_candidates(self.records, self.items + [extra], self.config)
        obs = next(x for x in observations if x["type"] == "NASS_ASB_ICAL_UNCONFIGURED_TARGET_RELEASE_OBSERVATION")
        self.assertEqual(obs["unconfigured_future_target_count"], 0)

    def test_dtend_dtstamp_sequence_and_description_do_not_change_schedule_match(self):
        items = deepcopy(self.items)
        target = items[0]
        items[0] = NASSASBRelease(**{
            **target.as_dict(),
            "dtend_raw": "20991231T235959",
            "dtstamp_raw": "20991231T235959Z",
            "sequence_raw": "999",
            "description": "arbitrary metadata",
        })
        candidates, _ = nass_asb_ical_review_candidates(self.records, items, self.config)
        self.assertEqual(candidates, [])

    def test_comparator_does_not_mutate_inputs(self):
        records_before = deepcopy(self.records)
        items_before = deepcopy(self.items)
        config_before = deepcopy(self.config)
        nass_asb_ical_review_candidates(self.records, self.items, self.config)
        self.assertEqual(self.records, records_before)
        self.assertEqual(self.items, items_before)
        self.assertEqual(self.config, config_before)

    def test_plan_identity_maps_match_monitor_constants(self):
        self.assertEqual(
            {uid: row["occurrence_id"] for uid, row in PLAN["configured_feed_identity_by_uid"].items()},
            EXPECTED_UID_TO_OCCURRENCE,
        )
        self.assertEqual(
            {uid: row["expected_summary"] for uid, row in PLAN["configured_feed_identity_by_uid"].items()},
            EXPECTED_UID_SUMMARIES,
        )


if __name__ == "__main__":
    unittest.main()
