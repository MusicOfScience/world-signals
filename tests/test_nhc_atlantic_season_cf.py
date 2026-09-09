import unittest

from world_signals.adapters.base import AdapterError
from world_signals.adapters.nhc_atlantic_season import (
    NHCAtlanticSeasonDefinition,
    parse_nhc_atlantic_climatology_html,
    validate_nhc_rss_xml,
)
from world_signals.nhc_atlantic_season_monitor import nhc_atlantic_season_review_candidates


class NHCAtlanticSeasonAdapterTests(unittest.TestCase):
    def test_parses_current_primary_semantics(self):
        definition = parse_nhc_atlantic_climatology_html(
            "<html><p>The Atlantic hurricane season runs from June 1 to November 30.</p></html>"
        )
        self.assertEqual(definition.start_month_day, "06-01")
        self.assertEqual(definition.end_month_day, "11-30")
        self.assertTrue(definition.semantic_sha256)

    def test_parses_official_season_wording(self):
        definition = parse_nhc_atlantic_climatology_html(
            "<p>The official hurricane season for the Atlantic basin is from June 1 to November 30, but storms can occur outside it.</p>"
        )
        self.assertEqual((definition.start_month_day, definition.end_month_day), ("06-01", "11-30"))

    def test_rejects_missing_semantic_definition(self):
        with self.assertRaises(AdapterError):
            parse_nhc_atlantic_climatology_html("<p>Atlantic tropical cyclone climatology.</p>")

    def test_rejects_conflicting_semantic_definitions(self):
        with self.assertRaises(AdapterError):
            parse_nhc_atlantic_climatology_html(
                "<p>Atlantic hurricane season runs from June 1 to November 30.</p>"
                "<p>The official hurricane season for the Atlantic basin is from May 30 to December 1.</p>"
            )

    def test_rss_health_validation_is_structure_only(self):
        validate_nhc_rss_xml("<rss version='2.0'><channel><title>NHC</title></channel></rss>")
        with self.assertRaises(AdapterError):
            validate_nhc_rss_xml("<html><body>not a feed</body></html>")


class NHCAtlanticSeasonMonitorTests(unittest.TestCase):
    def setUp(self):
        self.records = [
            {
                "occurrence_id": "WSO-COM-A-0049",
                "series_id": "WSER-RISK-ATL-HURR",
                "source_id": "WSSRC-RISK-002",
                "category": "PHYSICAL_CLIMATE_RISK",
                "event_type": "PHYSICAL_RISK_WINDOW",
                "region": "Cross-regional / Global",
                "jurisdiction": "Atlantic basin",
                "timing_type": "ALL_DAY_RANGE",
                "time_precision": "DAY",
                "time_status": "CONFIRMED",
                "certainty_status": "CONFIRMED",
                "start_local": "2026-06-01",
                "end_local": "2026-11-30",
            },
            {
                "occurrence_id": "WSO-COM-A-0050",
                "series_id": "WSER-RISK-ATL-HURR",
                "source_id": "WSSRC-RISK-002",
                "category": "PHYSICAL_CLIMATE_RISK",
                "event_type": "PHYSICAL_RISK_WINDOW",
                "region": "Cross-regional / Global",
                "jurisdiction": "Atlantic basin",
                "timing_type": "ALL_DAY_RANGE",
                "time_precision": "DAY",
                "time_status": "CONFIRMED",
                "certainty_status": "CONFIRMED",
                "start_local": "2027-06-01",
                "end_local": "2027-11-30",
            },
        ]
        self.config = {
            "source_id": "WSSRC-RISK-002",
            "canonical_occurrence_ids": ["WSO-COM-A-0049", "WSO-COM-A-0050"],
            "schedule_authority": False,
            "lifecycle_authority": False,
            "certainty_authority": False,
            "automatic_new_occurrence_creation_allowed": False,
            "automatic_live_or_analysis_promotion_allowed": False,
            "automatic_commit_allowed": False,
        }

    def test_matching_definition_is_observation_only(self):
        definition = NHCAtlanticSeasonDefinition("06-01", "11-30", "abc")
        candidates, observations = nhc_atlantic_season_review_candidates(self.records, definition, self.config)
        self.assertEqual(candidates, [])
        self.assertEqual(len([x for x in observations if x.get("semantic_match") is True]), 2)
        self.assertTrue(all(x.get("automatic_commit_allowed") is False for x in observations))

    def test_definition_drift_creates_review_only_candidate(self):
        definition = NHCAtlanticSeasonDefinition("05-30", "12-01", "drift")
        candidates, observations = nhc_atlantic_season_review_candidates(self.records, definition, self.config)
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["candidate_type"], "NHC_ATLANTIC_SEASON_DEFINITION_DRIFT_REVIEW")
        self.assertEqual(candidate["occurrence_ids"], ["WSO-COM-A-0049", "WSO-COM-A-0050"])
        self.assertFalse(candidate["automatic_commit_allowed"])
        self.assertFalse(candidate["canonical_date_mutation_allowed"])
        self.assertFalse(candidate["rss_activity_is_date_authority"])
        self.assertEqual(len(observations), 3)

    def test_wrong_source_configuration_is_rejected(self):
        config = dict(self.config)
        config["source_id"] = "WRONG"
        with self.assertRaises(ValueError):
            nhc_atlantic_season_review_candidates(
                self.records, NHCAtlanticSeasonDefinition("06-01", "11-30", "abc"), config
            )


if __name__ == "__main__":
    unittest.main()
