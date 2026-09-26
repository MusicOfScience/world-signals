from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import re
import sys
import unittest
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.icalendar import build_icalendar, validate_icalendar
from world_signals.io import load_json


class ICalendarProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_json(ROOT / "data/canonical/registry.json")
        cls.sources = load_json(ROOT / "data/sources/registry.json")
        cls.changes = load_json(ROOT / "data/changes/ledger.json")
        cls.build = build_icalendar(cls.registry, cls.sources, cls.changes)
        cls.text = cls.build.text

    def _event(self, occurrence_id):
        lines = self.text.replace("\r\n", "\n").splitlines()
        start = next(i for i, line in enumerate(lines) if line == "BEGIN:VEVENT" and occurrence_id in "\n".join(lines[i : i + 4]))
        end = next(i for i in range(start, len(lines)) if lines[i] == "END:VEVENT")
        event = lines[start : end + 1]
        unfolded = []
        for line in event:
            if line.startswith(" "):
                unfolded[-1] += line[1:]
            else:
                unfolded.append(line)
        return unfolded

    @staticmethod
    def _property(event, name):
        return next(line for line in event if line.startswith(name + ":"))

    @staticmethod
    def _minimal_timed_registry(*records):
        return {"reference_date": "2026-09-26", "records": list(records)}

    def test_feed_is_structurally_valid_and_deterministic(self):
        self.assertEqual([], validate_icalendar(self.text))
        self.assertEqual(self.text, build_icalendar(self.registry, self.sources, self.changes).text)
        self.assertGreater(len(self.build.included_occurrence_ids), 0)
        self.assertEqual(len(self.build.included_occurrence_ids), len(set(self.build.included_occurrence_ids)))
        self.assertEqual(665, len(self.build.included_occurrence_ids))
        self.assertEqual(24, len(self.build.omitted))
        self.assertTrue(all(len(line.encode("utf-8")) <= 75 for line in self.text.split("\r\n") if line))

    def test_build_does_not_mutate_governed_inputs(self):
        registry = deepcopy(self.registry)
        sources = deepcopy(self.sources)
        changes = deepcopy(self.changes)
        build_icalendar(registry, sources, changes)
        self.assertEqual(self.registry, registry)
        self.assertEqual(self.sources, sources)
        self.assertEqual(self.changes, changes)

    def test_timed_event_preserves_source_timezone(self):
        event = self._event("WSO-ddb70f8ff05a58fb")
        self.assertIn("DTSTART;TZID=America/Toronto:20260902T094500", event)
        self.assertNotIn("DTSTART:20260902T134500Z", event)

    def test_civil_date_and_all_day_range_use_date_values(self):
        civil = self._event("WSO-a79e102ac5bb5091")
        self.assertIn("DTSTART;VALUE=DATE:20260918", civil)
        self.assertFalse(any("TZID=" in line for line in civil if line.startswith("DTSTART") or line.startswith("DTEND")))

        season = self._event("WSO-COM-A-0049")
        self.assertIn("DTSTART;VALUE=DATE:20260601", season)
        self.assertIn("DTEND;VALUE=DATE:20261201", season)

    def test_expected_window_is_a_window_not_a_synthetic_appointment(self):
        event = self._event("WSO-INT-A-0018")
        self.assertIn("SUMMARY:ASEAN leaders-level summit 1 — Singapore Chair 2027 [EXPECTED WINDOW]", event)
        self.assertIn("DTSTART;VALUE=DATE:20270501", event)
        self.assertIn("DTEND;VALUE=DATE:20270601", event)
        self.assertTrue(any("exact appointment date is not asserted" in line for line in event))
        self.assertFalse(any("20270515" in line for line in event))
        self.assertIn("TRANSP:TRANSPARENT", event)

    def test_every_tzid_reference_has_only_the_required_vtimezone(self):
        referenced = {
            match.group(1)
            for line in self.text.replace("\r\n", "\n").splitlines()
            if (match := re.search(r"(?:^|;)TZID=([^;:]+)(?:;|:)", line))
        }
        defined = {
            line[5:]
            for line in self.text.replace("\r\n", "\n").splitlines()
            if line.startswith("TZID:")
        }
        self.assertEqual(referenced, defined)
        self.assertGreater(len(defined), 0)
        self.assertEqual([], validate_icalendar(self.text))

    def test_dst_sensitive_vtimezone_uses_zoneinfo_for_standard_and_daylight(self):
        records = [
            {
                "occurrence_id": "winter",
                "canonical_name": "Toronto winter meeting",
                "render_policy": "INCLUDE",
                "timing_type": "TIMED_EVENT",
                "source_timezone": "America/Toronto",
                "start_local": "2026-01-15T09:00:00",
                "end_local": "2026-01-15T10:00:00",
                "start_utc": "2026-01-15T14:00:00Z",
                "end_utc": "2026-01-15T15:00:00Z",
                "certainty_status": "CONFIRMED",
                "lifecycle_status": "PLANNED",
                "first_discovered_at": "2026-01-01",
                "last_verified_at": "2026-01-01",
            },
            {
                "occurrence_id": "summer",
                "canonical_name": "Toronto summer meeting",
                "render_policy": "INCLUDE",
                "timing_type": "TIMED_EVENT",
                "source_timezone": "America/Toronto",
                "start_local": "2026-07-15T09:00:00",
                "end_local": "2026-07-15T10:00:00",
                "start_utc": "2026-07-15T13:00:00Z",
                "end_utc": "2026-07-15T14:00:00Z",
                "certainty_status": "CONFIRMED",
                "lifecycle_status": "PLANNED",
                "first_discovered_at": "2026-01-01",
                "last_verified_at": "2026-01-01",
            },
        ]
        text = build_icalendar(self._minimal_timed_registry(*records), {"sources": []}).text
        self.assertIn("BEGIN:STANDARD", text)
        self.assertIn("BEGIN:DAYLIGHT", text)
        self.assertIn("TZOFFSETFROM:-0500", text)
        self.assertIn("TZOFFSETTO:-0400", text)
        self.assertEqual([], validate_icalendar(text))
        for local, expected in (
            ("2026-01-15T09:00:00", "2026-01-15T14:00:00+00:00"),
            ("2026-07-15T09:00:00", "2026-07-15T13:00:00+00:00"),
        ):
            observed = datetime.fromisoformat(local).replace(tzinfo=ZoneInfo("America/Toronto")).astimezone(timezone.utc)
            self.assertEqual(observed.isoformat(), expected)

    def test_unresolved_and_monitor_only_records_are_omitted(self):
        for occurrence_id in ("WSO-FIS-NP-BUDGET-2084", "WSO-FIS-B-0004", "WSO-RISK-A-0001"):
            self.assertNotIn(occurrence_id, self.build.included_occurrence_ids)
        self.assertIn("WSO-FIS-NP-BUDGET-2084", self.build.omitted)
        self.assertIn("WSO-FIS-B-0004", self.build.omitted)
        self.assertIn("WSO-RISK-A-0001", self.build.omitted)

    def test_uid_is_stable_when_governed_date_changes(self):
        changed = deepcopy(self.registry)
        target = next(record for record in changed["records"] if record["occurrence_id"] == "WSO-ddb70f8ff05a58fb")
        target["start_local"] = "2026-09-03T09:45:00"
        target["start_utc"] = "2026-09-03T13:45:00Z"
        original_event = self._event("WSO-ddb70f8ff05a58fb")
        original_sequence = self._property(original_event, "SEQUENCE")
        changed_event = next(
            line
            for line in build_icalendar(changed, self.sources, self.changes).text.replace("\r\n", "\n").splitlines()
            if line.startswith("UID:WSO-ddb70f8ff05a58fb")
        )
        self.assertIn("UID:WSO-ddb70f8ff05a58fb@world-signals", original_event)
        self.assertEqual(changed_event, "UID:WSO-ddb70f8ff05a58fb@world-signals")

        changed_changes = deepcopy(self.changes)
        changed_changes["changes"].append(
            {
                "occurrence_id": "WSO-ddb70f8ff05a58fb",
                "change_type": "TIMING_REVISION",
                "review_state": "APPROVED_FOR_CANONICAL_COMMIT",
                "reviewed_at": "2026-09-12T12:00:00+10:00",
                "old_values": {"start_local": "2026-09-02T09:45:00"},
                "new_values": {"start_local": "2026-09-03T09:45:00"},
            }
        )
        changed_text = build_icalendar(changed, self.sources, changed_changes).text
        changed_event = self._event_from_text(changed_text, "WSO-ddb70f8ff05a58fb")
        self.assertIn("DTSTART;TZID=America/Toronto:20260903T094500", changed_text)
        self.assertNotIn("DTSTART;TZID=America/Toronto:20260902T094500", changed_text)
        self.assertGreater(int(self._property(changed_event, "SEQUENCE").split(":", 1)[1]), int(original_sequence.split(":", 1)[1]))

    def _event_from_text(self, text, occurrence_id):
        previous = self.text
        try:
            self.text = text
            return self._event(occurrence_id)
        finally:
            self.text = previous

    def test_unchanged_event_has_stable_uid_sequence_and_timestamps(self):
        first = self._event("WSO-ddb70f8ff05a58fb")
        rebuilt = build_icalendar(self.registry, self.sources, self.changes).text
        second = self._event_from_text(rebuilt, "WSO-ddb70f8ff05a58fb")
        for name in ("UID", "SEQUENCE", "DTSTAMP", "LAST-MODIFIED"):
            self.assertEqual(self._property(first, name), self._property(second, name))

    def test_lifecycle_revision_increases_sequence_without_status_history_change(self):
        changed = deepcopy(self.registry)
        target = next(record for record in changed["records"] if record["occurrence_id"] == "WSO-08f11832f0335c85")
        original = self._event("WSO-08f11832f0335c85")
        changed_changes = deepcopy(self.changes)
        changed_changes["changes"].append(
            {
                "occurrence_id": target["occurrence_id"],
                "change_type": "LIFECYCLE_REVISION",
                "review_state": "APPROVED_FOR_CANONICAL_COMMIT",
                "reviewed_at": "2026-09-12T12:00:00+10:00",
                "old_values": {"lifecycle_status": target["lifecycle_status"]},
                "new_values": {"lifecycle_status": "COMPLETED"},
            }
        )
        target["lifecycle_status"] = "COMPLETED"
        updated = self._event_from_text(build_icalendar(changed, self.sources, changed_changes).text, target["occurrence_id"])
        self.assertEqual(self._property(original, "UID"), self._property(updated, "UID"))
        self.assertGreater(int(self._property(updated, "SEQUENCE").split(":", 1)[1]), int(self._property(original, "SEQUENCE").split(":", 1)[1]))
        self.assertNotEqual(self._property(original, "LAST-MODIFIED"), self._property(updated, "LAST-MODIFIED"))

    def test_unrelated_registry_change_does_not_revise_other_event(self):
        changed = deepcopy(self.registry)
        target_id = "WSO-ddb70f8ff05a58fb"
        other = next(record for record in changed["records"] if record["occurrence_id"] != target_id)
        other["notes"] = str(other.get("notes") or "") + " unrelated test-only change"
        original = self._event(target_id)
        updated = self._event_from_text(build_icalendar(changed, self.sources, self.changes).text, target_id)
        self.assertEqual(self._property(original, "UID"), self._property(updated, "UID"))
        self.assertEqual(self._property(original, "SEQUENCE"), self._property(updated, "SEQUENCE"))
        self.assertEqual(self._property(original, "DTSTAMP"), self._property(updated, "DTSTAMP"))
        self.assertEqual(self._property(original, "LAST-MODIFIED"), self._property(updated, "LAST-MODIFIED"))

    def test_public_feed_contains_no_runtime_or_review_candidate_fields(self):
        for forbidden in ("review_candidates", "PENDING_REVIEW", "observations.json", "candidate_id"):
            self.assertNotIn(forbidden, self.text)

    def test_validator_rejects_malformed_calendar(self):
        malformed = self.text.replace("END:VCALENDAR\r\n", "", 1)
        self.assertTrue(validate_icalendar(malformed))

    def test_static_build_and_pages_workflow_publish_the_feed(self):
        build = (ROOT / "scripts/build_site.py").read_text(encoding="utf-8")
        pages = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
        self.assertIn('docs / "world-signals.ics"', build)
        self.assertIn("path: docs", pages)
        self.assertIn("scripts/build_site.py", pages)

    def test_live_monitor_workflow_is_not_a_recurring_runtime(self):
        workflow = (ROOT / ".github/workflows/live-monitor.yml").read_text(encoding="utf-8")
        self.assertNotIn("schedule:", workflow)
        self.assertNotIn("branches: [main]", workflow)
        self.assertIn("workflow_dispatch:", workflow)


if __name__ == "__main__":
    unittest.main()
