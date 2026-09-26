from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.icalendar import build_icalendar, validate_icalendar
from world_signals.io import load_json


class ICalendarProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_json(ROOT / "data/canonical/registry.json")
        cls.sources = load_json(ROOT / "data/sources/registry.json")
        cls.build = build_icalendar(cls.registry, cls.sources)
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

    def test_feed_is_structurally_valid_and_deterministic(self):
        self.assertEqual([], validate_icalendar(self.text))
        self.assertEqual(self.text, build_icalendar(self.registry, self.sources).text)
        self.assertGreater(len(self.build.included_occurrence_ids), 0)
        self.assertEqual(len(self.build.included_occurrence_ids), len(set(self.build.included_occurrence_ids)))
        self.assertTrue(all(len(line.encode("utf-8")) <= 75 for line in self.text.split("\r\n") if line))

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
        changed_event = next(
            line
            for line in build_icalendar(changed, self.sources).text.replace("\r\n", "\n").splitlines()
            if line.startswith("UID:WSO-ddb70f8ff05a58fb")
        )
        self.assertIn("UID:WSO-ddb70f8ff05a58fb@world-signals", original_event)
        self.assertEqual(changed_event, "UID:WSO-ddb70f8ff05a58fb@world-signals")

        changed_text = build_icalendar(changed, self.sources).text
        self.assertIn("DTSTART;TZID=America/Toronto:20260903T094500", changed_text)
        self.assertNotIn("DTSTART;TZID=America/Toronto:20260902T094500", changed_text)

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
