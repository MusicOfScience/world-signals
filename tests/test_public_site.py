import json
import re
import unittest
from pathlib import Path

from scripts.validate_public_site import validate_public_site


ROOT = Path(__file__).resolve().parents[1]


class PublicSiteTests(unittest.TestCase):
    def test_public_build_has_pages_root_and_subscription_feed(self):
        self.assertEqual(validate_public_site(ROOT / "docs"), [])
        self.assertTrue((ROOT / "docs/index.html").exists())
        self.assertTrue((ROOT / "docs/.nojekyll").exists())
        self.assertTrue((ROOT / "docs/world-signals.ics").exists())

    def test_public_status_opens_only_the_bounded_forecast_pilot(self):
        status = json.loads((ROOT / "docs/data/public_status.json").read_text())
        self.assertEqual(status["canonical"]["count"], 689)
        self.assertEqual(status["sources"]["count"], 258)
        self.assertEqual(status["monitor_routes"]["count"], 26)
        self.assertEqual(status["live_intelligence"]["public_count"], 0)
        for layer in ("signals", "relationships", "risks", "scenarios", "outcomes"):
            self.assertFalse(status[layer]["public_projection"])
        self.assertEqual(status["relationships"]["count"], 0)
        self.assertEqual(status["risks"]["count"], 0)
        self.assertEqual(status["scenarios"]["count"], 0)
        self.assertTrue(status["forecasts"]["public_projection"])
        self.assertEqual(status["forecasts"]["internal_count"], 4)
        self.assertEqual(status["forecasts"]["public_count"], 4)
        self.assertEqual(status["forecasts"]["state"], "PILOT_PUBLIC_PROJECTION")
        self.assertEqual(status["evaluation"]["state"], "NO_SAMPLE")

    def test_public_output_never_contains_private_runtime_files_or_fields(self):
        files = {path.name for path in (ROOT / "docs").rglob("*") if path.is_file()}
        self.assertNotIn("runtime.json", files)
        self.assertNotIn("review_state.json", files)
        for path in (ROOT / "docs/data").glob("*.json"):
            if path.name != "outlook.json":
                self.assertNotIn("forecast_value", path.read_text())
            self.assertNotIn("observation_candidates", path.read_text())
            self.assertNotIn("signal_candidates", path.read_text())
        for path in (ROOT / "docs").rglob("*"):
            if path.is_file():
                self.assertNotIn("WSDIM-HEALTH-COD-BVD-REPORTED-BURDEN", path.read_text(errors="ignore"))

    def test_outlook_is_the_allowlisted_forecast_projection(self):
        outlook = json.loads((ROOT / "docs/data/outlook.json").read_text())
        self.assertEqual(outlook["metadata"]["public_forecast_count"], 4)
        self.assertEqual(outlook["metadata"]["evaluation_state"], "NO_SAMPLE")
        self.assertEqual(len(outlook["forecasts"]), 4)
        self.assertNotIn("WSDIM-HEALTH-COD-BVD-REPORTED-BURDEN", json.dumps(outlook))

    def test_briefing_is_a_three_lane_projection_with_source_refs(self):
        briefing = json.loads((ROOT / "docs/data/briefing.json").read_text())
        self.assertEqual(briefing["metadata"]["projection_type"], "PUBLIC_BRIEFING_LEAD")
        self.assertEqual(
            set(briefing["metadata"]["selection_rules"]),
            {"forecast_resolution", "calendar", "analysis"},
        )
        self.assertTrue(briefing["forecast_resolution"]["source_refs"])
        self.assertTrue(briefing["calendar"]["source_refs"])
        self.assertTrue(briefing["latest_reviewed_analysis"]["source_ref"])
        self.assertIsNone(briefing["metadata"]["importance_score"])
        self.assertEqual(briefing["metadata"]["world_state_projection"], "CLOSED")
        self.assertEqual(briefing["metadata"]["relationship_projection"], "CLOSED")

    def test_public_html_uses_relative_assets_for_project_pages_base_path(self):
        html = (ROOT / "docs/index.html").read_text()
        self.assertIsNone(re.search(r"(?:href|src)=['\"]/(?!/)", html))
        self.assertIn('href="world-signals.ics"', html)

    def test_pages_workflow_does_not_fetch_private_runtime_or_review_state(self):
        workflow = (ROOT / ".github/workflows/pages.yml").read_text()
        executable_lines = [line for line in workflow.splitlines() if line.lstrip().startswith("- run:")]
        self.assertFalse(any("fetch_latest_monitor_snapshot" in line for line in executable_lines))
        self.assertFalse(any("fetch_retained_review_state" in line for line in executable_lines))
        self.assertIn("scripts/build_site.py", workflow)

    def test_operator_cockpit_is_separate_from_public_output(self):
        self.assertTrue((ROOT / "operator/operator.html").exists())
        self.assertTrue((ROOT / "operator/data/operator.json").exists())
        self.assertNotIn("operator/", {path.name for path in (ROOT / "docs").glob("*")})


if __name__ == "__main__":
    unittest.main()
