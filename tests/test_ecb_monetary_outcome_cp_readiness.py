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

    def test_frozen_preflight_records_no_outcome_authorisation(self):
        self.assertEqual(self.plan["status"], "READ_ONLY_READINESS_NO_OUTCOME_POPULATION_AUTHORISED")
        self.assertFalse(self.plan["preflight"]["official_outcome_available"])
        self.assertFalse(self.plan["preflight"]["scheduled_release_time_is_completion_evidence"])
        self.assertEqual(self.plan["candidate"]["canonical_occurrence_id"], OCCURRENCE_ID)
        self.assertEqual(self.plan["candidate"]["outcome_source_id"], OUTCOME_SOURCE_ID)
        self.assertTrue(self.plan["prohibited_in_cp_readiness"]["elapsed_time_completion_inference"])
        self.assertTrue(self.plan["prohibited_in_cp_readiness"]["live_population_before_outcome"])


if __name__ == "__main__":
    unittest.main()
