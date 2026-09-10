import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data" / "canonical" / "registry.json"
SOURCES = ROOT / "data" / "sources" / "registry.json"
LIVE = ROOT / "data" / "live_intelligence" / "observations.json"
PLAN = ROOT / "data" / "live_intelligence" / "ECB_MONETARY_OUTCOME_CP_PLAN_v0.1.json"

OCCURRENCE_ID = "WSO-ad4d0618a65059f2"
SERIES_ID = "WS.CB.ECB.MONETARY_POLICY_DECISION"
SCHEDULE_SOURCE_ID = "WSSRC-CB-003"
OUTCOME_SOURCE_ID = "WSSRC-CB-004"


def load(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


class EcbMonetaryOutcomeCPReadinessTests(unittest.TestCase):
    def setUp(self):
        self.canonical = load(CANONICAL)
        self.sources = load(SOURCES)
        self.live = load(LIVE)
        self.plan = load(PLAN)

    def occurrence(self):
        rows = [
            row for row in self.canonical["records"]
            if row["occurrence_id"] == OCCURRENCE_ID
        ]
        self.assertEqual(len(rows), 1)
        return rows[0]

    def test_stable_ecb_identity_and_clock_are_preserved(self):
        row = self.occurrence()
        self.assertEqual(row["series_id"], SERIES_ID)
        self.assertEqual(row["canonical_name"], "ECB Governing Council monetary policy decision — 2026-09-10")
        self.assertEqual(row["source_id"], SCHEDULE_SOURCE_ID)
        self.assertEqual(row["timing_type"], "LOCAL_DATETIME")
        self.assertEqual(row["start_local"], "2026-09-10T14:15:00")
        self.assertEqual(row["source_timezone"], "Europe/Berlin")
        self.assertEqual(row["start_utc"], "2026-09-10T12:15:00Z")
        self.assertEqual(row["time_precision"], "MINUTE")
        self.assertEqual(row["time_status"], "CONFIRMED")
        self.assertEqual(row["time_basis"], "AUTHORITATIVE_STANDARD_PUBLICATION_RULE")
        self.assertEqual(row["certainty_status"], "CONFIRMED")
        self.assertIn(row["lifecycle_status"], {"PLANNED", "COMPLETED"})

    def test_no_duplicate_same_series_decision_identity(self):
        rows = [
            row for row in self.canonical["records"]
            if row["series_id"] == SERIES_ID and row.get("start_local") == "2026-09-10T14:15:00"
        ]
        self.assertEqual([row["occurrence_id"] for row in rows], [OCCURRENCE_ID])

    def test_schedule_and_outcome_sources_remain_distinct(self):
        by_id = {row["source_id"]: row for row in self.sources["sources"]}
        self.assertIn(SCHEDULE_SOURCE_ID, by_id)
        self.assertIn(OUTCOME_SOURCE_ID, by_id)
        self.assertNotEqual(SCHEDULE_SOURCE_ID, OUTCOME_SOURCE_ID)
        self.assertEqual(by_id[SCHEDULE_SOURCE_ID]["institution"], "European Central Bank")
        self.assertEqual(by_id[OUTCOME_SOURCE_ID]["institution"], "European Central Bank")
        self.assertNotEqual(by_id[OUTCOME_SOURCE_ID].get("automated_monitoring_use"), "CLEARED")

    def test_planned_anchor_cannot_have_outcome_live_row(self):
        lifecycle = self.occurrence()["lifecycle_status"]
        links = []
        for observation in self.live["observations"]:
            for link in observation.get("canonical_links", []):
                if link.get("occurrence_id") == OCCURRENCE_ID and link.get("relationship") == "OUTCOME_OF":
                    links.append(observation["observation_id"])
        if lifecycle == "PLANNED":
            self.assertEqual(links, [])
        elif links:
            self.assertEqual(lifecycle, "COMPLETED")

    def test_initial_preflight_remains_frozen(self):
        initial = self.plan["initial_preflight"]
        self.assertEqual(initial["as_of_utc"], "2026-09-10T11:30:00Z")
        self.assertFalse(initial["official_outcome_available"])
        self.assertFalse(initial["scheduled_release_time_is_completion_evidence"])
        self.assertTrue(initial["identity_resolved"])
        self.assertFalse(initial["duplicate_canonical_identity_allowed"])

    def test_post_release_recheck_remains_fail_closed(self):
        self.assertEqual(
            self.plan["status"],
            "READ_ONLY_POST_RELEASE_PRIMARY_EVIDENCE_BLOCKED_NO_OUTCOME_POPULATION_AUTHORISED",
        )
        recheck = self.plan["post_release_recheck"]
        self.assertTrue(recheck["scheduled_release_time_passed"])
        self.assertFalse(recheck["official_ecb_outcome_retrievable_on_reviewed_primary_surfaces"])
        self.assertTrue(recheck["secondary_reporting_indicates_decision_occurred"])
        self.assertFalse(recheck["secondary_reporting_admitted_as_canonical_completion_evidence"])
        self.assertFalse(recheck["secondary_reporting_admitted_as_live_outcome_evidence"])
        self.assertFalse(recheck["governed_write_authorised"])
        self.assertEqual(
            recheck["status_interpretation"],
            "PRIMARY_SOURCE_RETRIEVAL_OR_INDEXING_GAP_NOT_EVIDENCE_OF_NO_DECISION",
        )

    def test_latest_primary_recheck_freezes_new_routes_without_opening_authority(self):
        latest = self.plan["latest_primary_recheck"]
        self.assertEqual(latest["as_of_utc"], "2026-09-10T14:28:00Z")
        self.assertEqual(latest["official_decision_index_latest_visible_decision_date"], "2026-07-23")
        self.assertTrue(latest["official_press_conference_surface_still_rendered_pre_release_state"])
        self.assertTrue(latest["official_weekly_schedule_still_records_2026_09_10_decision_and_press_conference"])
        self.assertTrue(latest["official_tv_downlink_surface_records_2026_09_10_press_conference_transmission_schedule"])
        self.assertEqual(latest["official_press_rss_route_discovered"], "https://www.ecb.europa.eu/rss/press.html")
        self.assertFalse(latest["official_press_rss_payload_retrievable_in_current_research_toolchain"])
        self.assertFalse(latest["eurosystem_member_surfaces_exposed_current_decision_outcome"])
        self.assertFalse(latest["official_ecb_outcome_retrievable_on_reviewed_primary_surfaces"])
        self.assertFalse(latest["secondary_reporting_admitted_as_substitute"])
        self.assertFalse(latest["governed_write_authorised"])
        self.assertEqual(latest["repeat_search_without_new_primary_surface_value"], "LOW")

    def test_readiness_does_not_pre_assume_production_payload(self):
        design = self.plan["transaction_design_state"]
        self.assertFalse(design["final_transaction_shape_frozen"])
        self.assertFalse(design["atomic_lifecycle_plus_live_selected"])
        self.assertFalse(design["two_step_lifecycle_then_live_selected"])
        self.assertFalse(design["canonical_target_version_assumed"])
        self.assertFalse(design["change_ledger_target_version_assumed"])
        self.assertFalse(design["live_target_version_assumed"])
        self.assertFalse(design["live_evidence_row_count_assumed"])
        self.assertFalse(design["live_observation_id_assumed"])
        self.assertFalse(design["rate_decision_assumed_from_secondary_reporting"])
        self.assertFalse(design["source_registry_new_identity_expected"])
        self.assertEqual(
            design["source_registry_existing_outcome_source_must_be_reused_if_competent"],
            OUTCOME_SOURCE_ID,
        )

    def test_readiness_safety_gates_remain_closed(self):
        prohibited = self.plan["prohibited_in_cp_readiness"]
        self.assertTrue(prohibited["canonical_mutation_before_primary_outcome"])
        self.assertTrue(prohibited["live_population_before_primary_outcome"])
        self.assertTrue(prohibited["duplicate_canonical_occurrence"])
        self.assertTrue(prohibited["elapsed_time_completion_inference"])
        self.assertTrue(prohibited["secondary_news_as_substitute_for_registered_primary_outcome_source"])
        self.assertTrue(prohibited["new_ecb_monitor_route"])
        self.assertTrue(prohibited["automatic_monitor_to_live"])
        self.assertTrue(prohibited["automatic_live_to_analysis"])
        self.assertTrue(prohibited["market_causality_claim"])
        self.assertTrue(prohibited["public_projection"])
        self.assertTrue(prohibited["opec_quarantine_mutation"])
        self.assertEqual(self.plan["candidate"]["canonical_occurrence_id"], OCCURRENCE_ID)
        self.assertEqual(self.plan["candidate"]["outcome_source_id"], OUTCOME_SOURCE_ID)


if __name__ == "__main__":
    unittest.main()
