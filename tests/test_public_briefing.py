import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from world_signals.public_briefing import (
    SELECTION_RULES,
    build_public_briefing,
    exact_public_calendar_events,
    select_next_calendar_occurrence,
    validate_public_briefing,
)


ROOT = Path(__file__).resolve().parents[1]


def synthetic_inputs():
    outlook = {
        "metadata": {"public_forecast_projection_allowed": True},
        "forecasts": [
            {
                "forecast_id": "F-B",
                "revision_id": "F-B-R1",
                "institution": "Bank B",
                "review_state": "ACCEPTED",
                "lifecycle_state": "OPEN",
                "forecast_type": "NUMERIC_POINT",
                "forecast_value": {"estimate": 2.25, "unit": "percent"},
                "resolution": {"window_start_at_utc": "2026-10-28T13:45:00Z"},
            },
            {
                "forecast_id": "F-A",
                "revision_id": "F-A-R1",
                "institution": "Bank A",
                "review_state": "ACCEPTED",
                "lifecycle_state": "OPEN",
                "forecast_type": "CATEGORICAL",
                "forecast_value": {"outcomes": [{"label": "Unchanged", "probability": 1}]},
                "resolution": {"window_start_at_utc": "2026-10-28T18:00:00Z"},
            },
            {
                "forecast_id": "DRAFT",
                "revision_id": "DRAFT-R1",
                "institution": "Draft Bank",
                "review_state": "DRAFT",
                "lifecycle_state": "OPEN",
                "resolution": {"window_start_at_utc": "2026-10-01T00:00:00Z"},
            },
        ],
    }
    events = {
        "events": [
            {
                "occurrence_id": "CANCELLED",
                "lifecycle": "CANCELLED",
                "render_policy": "INCLUDE",
                "timing_type": "LOCAL_DATETIME",
                "start_utc": "2026-09-29T00:00:00Z",
            },
            {
                "occurrence_id": "WINDOW",
                "lifecycle": "PLANNED",
                "render_policy": "INCLUDE",
                "timing_type": "EXPECTED_DATE_WINDOW",
                "date_earliest": "2026-09-29",
                "date_latest": "2026-10-01",
            },
            {
                "occurrence_id": "EXACT-LATER",
                "title": "Exact event",
                "institution": "Institution",
                "certainty": "CONFIRMED",
                "lifecycle": "PLANNED",
                "render_policy": "INCLUDE",
                "timing_type": "LOCAL_DATETIME",
                "start_utc": "2026-10-01T00:00:00Z",
            },
        ]
    }
    analysis = {
        "reviews": [
            {"analysis_id": "A-OLD", "review_state": "REVIEWED_SAMPLE", "analysis_as_of_utc": "2026-09-01T00:00:00Z"},
            {"analysis_id": "A-LATEST", "review_state": "REVIEWED_SAMPLE", "analysis_as_of_utc": "2026-09-03T00:00:00Z"},
            {"analysis_id": "A-DRAFT", "review_state": "DRAFT", "analysis_as_of_utc": "2026-09-04T00:00:00Z"},
        ]
    }
    return outlook, events, analysis


class PublicBriefingTests(unittest.TestCase):
    def test_contract_has_exactly_three_deterministic_lanes(self):
        outlook, events, analysis = synthetic_inputs()
        briefing = build_public_briefing(outlook, events, analysis)
        self.assertEqual(briefing["metadata"]["selection_rules"], SELECTION_RULES)
        self.assertEqual(set(SELECTION_RULES), {"forecast_resolution", "calendar", "analysis"})
        self.assertIsNone(briefing["metadata"]["importance_score"])

    def test_forecast_lane_selects_all_earliest_date_ties_and_pins_sources(self):
        briefing = build_public_briefing(*synthetic_inputs())
        self.assertEqual(briefing["forecast_resolution"]["forecast_ids"], ["F-A", "F-B"])
        self.assertEqual(briefing["forecast_resolution"]["resolution_date_utc"], "2026-10-28T13:45:00Z")
        self.assertEqual(
            {row["source_object_id"] for row in briefing["forecast_resolution"]["source_refs"]},
            {"F-A", "F-B"},
        )
        self.assertNotIn("DRAFT", briefing["forecast_resolution"]["forecast_ids"])

    def test_calendar_excludes_cancelled_and_uncertain_windows_and_is_explicit_time_selected(self):
        _, events, _ = synthetic_inputs()
        self.assertEqual([row["occurrence_id"] for row in exact_public_calendar_events(events["events"])], ["EXACT-LATER"])
        selected = select_next_calendar_occurrence(events["events"], "2026-09-28T00:00:00Z")
        self.assertEqual(selected["occurrence_id"], "EXACT-LATER")
        self.assertIsNone(select_next_calendar_occurrence(events["events"], "2026-10-02T00:00:00Z"))

    def test_latest_analysis_requires_reviewed_sample_and_is_deterministic(self):
        briefing = build_public_briefing(*synthetic_inputs())
        self.assertEqual(briefing["latest_reviewed_analysis"]["analysis_id"], "A-LATEST")
        self.assertEqual(briefing["latest_reviewed_analysis"]["source_ref"]["selection_rule"], SELECTION_RULES["analysis"])

    def test_tied_analysis_uses_analysis_id_as_neutral_tiebreak(self):
        outlook, events, analysis = synthetic_inputs()
        analysis["reviews"].append({"analysis_id": "A-ZED", "review_state": "REVIEWED_SAMPLE", "analysis_as_of_utc": "2026-09-03T00:00:00Z"})
        self.assertEqual(build_public_briefing(outlook, events, analysis)["latest_reviewed_analysis"]["analysis_id"], "A-ZED")

    def test_validation_and_build_are_deterministic_and_inputs_unchanged(self):
        outlook, events, analysis = synthetic_inputs()
        before = hashlib.sha256(json.dumps([outlook, events, analysis], sort_keys=True).encode()).hexdigest()
        first = build_public_briefing(outlook, events, analysis)
        second = build_public_briefing(outlook, events, analysis)
        self.assertEqual(first, second)
        self.assertEqual(validate_public_briefing(first, outlook, events, analysis), [])
        after = hashlib.sha256(json.dumps([outlook, events, analysis], sort_keys=True).encode()).hexdigest()
        self.assertEqual(before, after)

    def test_mutated_briefing_fails_closed(self):
        outlook, events, analysis = synthetic_inputs()
        briefing = build_public_briefing(outlook, events, analysis)
        tampered = copy.deepcopy(briefing)
        tampered["calendar"]["candidate_occurrence_ids"] = []
        self.assertTrue(validate_public_briefing(tampered, outlook, events, analysis))

    def test_public_contract_closes_world_state_relationship_and_ranking(self):
        briefing = build_public_briefing(*synthetic_inputs())
        self.assertEqual(briefing["metadata"]["world_state_projection"], "CLOSED")
        self.assertEqual(briefing["metadata"]["relationship_projection"], "CLOSED")
        self.assertNotIn("importance", json.dumps(briefing["metadata"]["selection_rules"]).lower())

    def test_public_surface_places_brief_before_outlook_and_keeps_three_lanes(self):
        html = (ROOT / "web/index.html").read_text(encoding="utf-8")
        js = (ROOT / "web/briefing.js").read_text(encoding="utf-8")
        self.assertLess(html.index('id="briefing"'), html.index('id="outlook"'))
        for label in ("NEXT TO RESOLVE", "NEXT ON THE CALENDAR", "LATEST REVIEWED"):
            self.assertIn(label, js)
        self.assertNotIn("MOST IMPORTANT", html + js)
        self.assertNotIn("TOP RISK", html + js)

    def test_public_brief_does_not_read_internal_forecast_store(self):
        js = (ROOT / "web/briefing.js").read_text(encoding="utf-8")
        self.assertIn("data/outlook.json", js)
        self.assertNotIn("data/forecasts/forecasts.json", js)

    def test_passed_unresolved_forecast_remains_visible_as_pending(self):
        js = (ROOT / "web/briefing.js").read_text(encoding="utf-8")
        self.assertIn("Resolution date passed · Outcome pending", js)
        self.assertIn("full distribution and cutoff in", js)

    def test_brief_has_no_political_or_importance_ranking_language(self):
        text = (ROOT / "web/briefing.js").read_text(encoding="utf-8") + (ROOT / "web/index.html").read_text(encoding="utf-8")
        self.assertNotIn("MOST IMPORTANT", text)
        self.assertNotIn("TOP RISK", text)
        self.assertNotIn("AI SELECTED", text)

    def test_empty_lanes_are_honest(self):
        outlook, events, analysis = synthetic_inputs()
        outlook["forecasts"] = []
        events["events"] = []
        analysis["reviews"] = []
        briefing = build_public_briefing(outlook, events, analysis)
        self.assertEqual(briefing["forecast_resolution"]["status"], "NO_OPEN_PUBLIC_FORECAST")
        self.assertEqual(briefing["calendar"]["candidate_occurrence_ids"], [])
        self.assertEqual(briefing["latest_reviewed_analysis"]["status"], "NO_REVIEWED_PUBLIC_ANALYSIS")


if __name__ == "__main__":
    unittest.main()
