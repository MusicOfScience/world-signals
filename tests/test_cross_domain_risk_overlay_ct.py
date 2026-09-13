from copy import deepcopy
import json
from pathlib import Path
import subprocess
import unittest

from src.world_signals.risk_projection import (
    DATASET,
    LAYER,
    public_risk_projection,
    validate_risk_projection,
)


ROOT = Path(__file__).resolve().parents[1]


class CrossDomainRiskOverlayCTTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads(
            (ROOT / "data/canonical/registry.json").read_text(encoding="utf-8")
        )
        cls.projection = public_risk_projection(cls.registry)

    def test_projection_validates_at_current_canonical_checkpoint(self):
        self.assertEqual(self.projection["dataset"], DATASET)
        self.assertEqual(self.projection["layer"], LAYER)
        self.assertEqual(validate_risk_projection(self.registry, self.projection), [])
        metadata = self.projection["metadata"]
        self.assertEqual(metadata["canonical_registry_version"], self.registry["version"])
        self.assertEqual(metadata["canonical_record_count"], len(self.registry["records"]))
        self.assertFalse(metadata["canonical_mutation_authorized"])
        self.assertFalse(metadata["event_population_authorized"])
        self.assertFalse(metadata["live_intelligence_inferred"])
        self.assertFalse(metadata["analysis_conclusions_inferred"])

    def test_projection_is_read_only_and_preserves_canonical_risk_fields(self):
        before = json.dumps(self.registry, sort_keys=True, separators=(",", ":"))
        projection = public_risk_projection(self.registry)
        after = json.dumps(self.registry, sort_keys=True, separators=(",", ":"))
        self.assertEqual(after, before)

        canonical = {row["occurrence_id"]: row for row in self.registry["records"]}
        self.assertEqual(len(projection["events"]), len(canonical))
        for event in projection["events"]:
            source = canonical[event["occurrence_id"]]
            for field in (
                "series_id", "intrinsic_importance", "expected_market_sensitivity",
                "geopolitical_sensitivity", "transmission_channels", "lifecycle_status",
                "date_earliest", "date_latest", "source_native_window_label",
            ):
                self.assertEqual(event[field], source.get(field))
            self.assertEqual(event["season_phases"], source.get("season_phases", []))

    def test_uncertain_and_source_native_windows_keep_their_supported_precision(self):
        expected_window = next(
            event for event in self.projection["events"]
            if event["date_earliest"] and event["date_latest"]
            and event["date_earliest"] != event["date_latest"]
        )
        self.assertIsNone(expected_window["timing_anchor"])
        self.assertEqual(expected_window["timing_anchor_basis"], "NO_EXACT_GREGORIAN_ANCHOR")
        season = next(event for event in self.projection["events"] if event["season_phases"])
        self.assertIsNone(season["timing_anchor"])
        self.assertTrue(season["source_native_window_label"])

    def test_domain_mapping_is_nonexclusive_and_covers_all_nine_lenses(self):
        domains = self.projection["domains"]
        self.assertEqual(len(domains), 9)
        self.assertTrue(all(row["canonical_event_count"] > 0 for row in domains))
        self.assertTrue(any(len(event["risk_domain_ids"]) > 1 for event in self.projection["events"]))
        self.assertTrue(all(event["risk_domain_ids"] for event in self.projection["events"]))

    def test_convergence_is_exact_timing_density_not_causal_inference(self):
        event_map = {event["occurrence_id"]: event for event in self.projection["events"]}
        self.assertGreater(len(self.projection["convergence_windows"]), 0)
        for window in self.projection["convergence_windows"]:
            self.assertEqual(window["timing_basis"], "CALENDAR_WEEK_BUCKET_FROM_EXACT_CANONICAL_START")
            self.assertEqual(window["interpretation"], "DENSITY_ONLY_NOT_CAUSAL_OR_PROBABILISTIC")
            self.assertGreaterEqual(window["event_count"], 2)
            self.assertGreaterEqual(len(window["canonical_categories"]), 2)
            self.assertGreaterEqual(len(window["risk_domain_ids"]), 2)
            for occurrence_id in window["occurrence_ids"]:
                event = event_map[occurrence_id]
                self.assertIsNotNone(event["timing_anchor"])
                self.assertIn(event["lifecycle_status"], {"ACTIVE", "PLANNED"})

    def test_scalar_probability_forecast_and_causal_fields_fail_closed(self):
        for field in (
            "risk_score", "composite_score", "severity_score", "probability",
            "likelihood", "forecast", "causal_status", "causal_claim",
        ):
            projection = deepcopy(self.projection)
            projection["events"][0][field] = 1
            errors = validate_risk_projection(self.registry, projection)
            self.assertTrue(any("prohibited" in error for error in errors), field)

    def test_unknown_or_rewritten_canonical_identity_fails_closed(self):
        projection = deepcopy(self.projection)
        projection["events"][0]["occurrence_id"] = "WSO-NOT-CANONICAL"
        errors = validate_risk_projection(self.registry, projection)
        self.assertTrue(any("unknown canonical occurrence" in error for error in errors))

        projection = deepcopy(self.projection)
        projection["events"][0]["geopolitical_sensitivity"] = "HIGH"
        source = next(
            row for row in self.registry["records"]
            if row["occurrence_id"] == projection["events"][0]["occurrence_id"]
        )
        if source["geopolitical_sensitivity"] == "HIGH":
            projection["events"][0]["geopolitical_sensitivity"] = "LOW"
        errors = validate_risk_projection(self.registry, projection)
        self.assertTrue(any("geopolitical_sensitivity diverges" in error for error in errors))

    def test_opec_quarantine_is_not_reactivated(self):
        quarantine = (ROOT / "OPEC_QUARANTINE.md").read_text(encoding="utf-8")
        self.assertIn("OPEC CE work must remain dormant", quarantine)
        self.assertIn("OPEC is excluded from candidate selection", quarantine)
        opec_events = [event for event in self.projection["events"] if event["institution"] == "OPEC"]
        self.assertEqual(
            {event["occurrence_id"] for event in opec_events},
            {"WSO-COM-A-0001", "WSO-COM-A-0002", "WSO-COM-A-0003"},
        )
        for event in opec_events:
            self.assertNotIn("candidate_node_id", event)
            self.assertNotIn("provenance_repair", event)

    def test_browser_surface_is_read_only_responsive_and_built(self):
        browser = (ROOT / "web/risk.js").read_text(encoding="utf-8")
        css = (ROOT / "web/risk.css").read_text(encoding="utf-8")
        build = (ROOT / "scripts/build_site.py").read_text(encoding="utf-8")
        self.assertIn("Risk overlay", browser)
        self.assertIn("fetch('data/risk_overlay.json')", browser)
        self.assertIn("Single danger score: absent", browser)
        self.assertIn("Coincidence ≠ causality", browser)
        self.assertIn('aria-label="Risk horizon"', browser)
        self.assertIn("event.date_earliest", browser)
        self.assertIn("event.season_phases", browser)
        self.assertIn("@media(max-width:620px)", css)
        self.assertIn('web/risk.js', build)
        self.assertIn('risk_overlay.json', build)
        self.assertNotIn('data/canonical/registry.json', browser)
        self.assertNotIn("method:'POST'", browser)
        self.assertNotIn('method:"POST"', browser)
        self.assertNotIn("method:'PUT'", browser)
        self.assertNotIn("method:'DELETE'", browser)

    def test_browser_module_has_valid_javascript_syntax(self):
        subprocess.run(
            ["node", "--check", str(ROOT / "web/risk.js")],
            check=True,
            capture_output=True,
            text=True,
        )


if __name__ == "__main__":
    unittest.main()
