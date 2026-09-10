from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.canada_us_counter_tariff_co import (
    EVIDENCE_IDS,
    OBSERVATION_ID,
    TARGET_VERSION,
    target_evidence,
    target_live_schema,
    target_observations,
    validate_co_contract,
)
from world_signals.live_intelligence import public_live_intelligence_projection, validate_live_intelligence


PLAN_PATH = ROOT / "data/live_intelligence/CANADA_US_COUNTER_TARIFF_LIVE_CO_PLAN_v0.1.json"
PAYLOAD_PATH = ROOT / "data/live_intelligence/CANADA_US_COUNTER_TARIFF_LIVE_CO_PAYLOAD_v0.1.json"
SCHEMA_PATH = ROOT / "data/live_intelligence/schema.json"
OBSERVATIONS_PATH = ROOT / "data/live_intelligence/observations.json"
EVIDENCE_PATH = ROOT / "data/live_intelligence/evidence_registry.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
MONITOR_PATH = ROOT / "data/monitor/expectations.json"
ANALYSIS_REVIEWS_PATH = ROOT / "data/analysis/event_reviews.json"
ANALYSIS_EVIDENCE_PATH = ROOT / "data/analysis/evidence_registry.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class CanadaUSCounterTariffLiveCOTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load(PLAN_PATH)
        cls.payload = load(PAYLOAD_PATH)
        cls.schema = load(SCHEMA_PATH)
        cls.observations = load(OBSERVATIONS_PATH)
        cls.evidence = load(EVIDENCE_PATH)
        cls.canonical = load(CANONICAL_PATH)

    def simulate(self):
        return (
            target_live_schema(self.schema, self.plan),
            target_observations(self.observations, self.payload, self.plan),
            target_evidence(self.evidence, self.payload, self.plan),
        )

    def test_plan_freezes_exact_post_cn_base_and_bounded_target(self):
        self.assertEqual(self.plan["exact_base_main_sha"], "b2b9e85933dd1c5924af1228f47427d6b38bf967")
        self.assertEqual(self.plan["pre_state"]["live_schema_version"], "0.10")
        self.assertEqual(self.plan["pre_state"]["live_observation_count"], 9)
        self.assertEqual(self.plan["pre_state"]["live_evidence_count"], 12)
        self.assertEqual(self.plan["target_state"]["live_schema_version"], TARGET_VERSION)
        self.assertEqual(self.plan["target_state"]["live_observation_count"], 10)
        self.assertEqual(self.plan["target_state"]["live_evidence_count"], 14)
        self.assertEqual(self.plan["target_state"]["canonical_linked_live_observation_count"], 3)
        self.assertTrue(self.plan["gates"]["eleventh_live_observation_requires_new_pressure_audit"])
        self.assertFalse(self.plan["gates"]["us_response_collapsed_into_canada_observation"])

    def test_payload_is_one_canadian_policy_implementation_with_two_primary_sources(self):
        self.assertEqual(len(self.payload["live_evidence"]), 2)
        row = self.payload["live_observation"]
        self.assertEqual(row["observation_id"], OBSERVATION_ID)
        self.assertEqual(row["observation_type"], "POLICY_DEVELOPMENT")
        self.assertEqual(row["verification_state"], "PRIMARY_CONFIRMED")
        self.assertEqual(row["canonical_links"], [])
        self.assertIsNone(row["revision_of_observation_id"])
        self.assertEqual(row["jurisdictions"], ["Canada"])
        self.assertEqual(row["regions"], ["North America"])
        self.assertEqual(row["domain_tags"], ["TRADE", "ECONOMICS", "GEOPOLITICS"])
        self.assertEqual(tuple(item["evidence_id"] for item in self.payload["live_evidence"]), EVIDENCE_IDS)
        self.assertEqual({item["provider"] for item in self.payload["live_evidence"]}, {"Canada — Department of Finance", "Canada Border Services Agency"})
        for item in self.payload["live_evidence"]:
            self.assertEqual(item["evidence_class"], "PRIMARY_OFFICIAL")
            self.assertEqual(item["canonical_provenance_effect"], "NONE")

    def test_event_time_stays_civil_date_and_source_dates_remain_distinct(self):
        row = self.payload["live_observation"]
        evidence = {item["evidence_id"]: item for item in self.payload["live_evidence"]}
        self.assertEqual(row["event_time"], {"precision": "CIVIL_DATE", "event_date": "2026-09-08"})
        self.assertNotIn("event_at_utc", row["event_time"])
        self.assertNotIn("event_local", row["event_time"])
        self.assertEqual(evidence[EVIDENCE_IDS[0]]["publication_time"], {"precision": "CIVIL_DATE", "published_date": "2026-08-25"})
        self.assertEqual(evidence[EVIDENCE_IDS[1]]["publication_time"], {"precision": "CIVIL_DATE", "published_date": "2026-09-07"})
        for item in evidence.values():
            self.assertNotIn("published_at_utc", item["publication_time"])

    def test_payload_does_not_promote_timezone_unspecified_effective_clock(self):
        summary = self.payload["live_observation"]["summary"].lower()
        self.assertIn("timezone-unspecified 12:01 a.m.", summary)
        self.assertIn("does not promote", summary)
        exclusions = " ".join(self.payload["scope_exclusions"]).lower()
        self.assertIn("12:01 a.m.", exclusions)
        self.assertIn("not converted to utc", exclusions)

    def test_canadian_action_is_not_collapsed_with_us_response_or_story_identity(self):
        row = self.payload["live_observation"]
        summary = row["summary"].lower()
        self.assertNotIn("story_id", row)
        self.assertIn("does not fold", summary)
        self.assertIn("separate u.s. 8 september proclamations", summary)
        exclusions = " ".join(self.payload["scope_exclusions"]).lower()
        self.assertIn("separate u.s. presidential actions", exclusions)
        self.assertIn("no manual story identity", exclusions)

    def test_trade_scope_and_effects_are_not_overclaimed(self):
        summary = self.payload["live_observation"]["summary"].lower()
        self.assertIn("15%, 25% or 50%", summary)
        self.assertIn("$27.6 billion", summary)
        self.assertIn("does not imply", summary)
        self.assertIn("does not independently adjudicate", summary)
        self.assertIn("does not claim", summary)
        self.assertNotIn("c$27.6", summary)
        forbidden = {
            "what_was_expected", "what_surprised", "what_moved", "what_appears_connected",
            "what_may_be_noise", "alternative_explanations", "second_order_effects",
            "falsifiers", "causal_status", "confidence", "analytical_conclusion",
        }
        self.assertFalse(forbidden & set(row := self.payload["live_observation"]))

    def test_simulated_target_validates(self):
        schema, observations, evidence = self.simulate()
        if str(schema.get("version")) == TARGET_VERSION:
            co_errors = validate_co_contract(schema, observations, evidence, self.plan)
            self.assertEqual(co_errors, [])
        else:
            checkpoint = schema.get("co_checkpoint") or {}
            self.assertEqual(checkpoint.get("schema_version"), TARGET_VERSION)
            self.assertEqual(checkpoint.get("observation_count"), 10)
            self.assertEqual(checkpoint.get("evidence_count"), 14)
            self.assertEqual(checkpoint.get("canonical_linked_observation_count"), 3)
            current_row = next(
                row for row in observations["observations"]
                if row["observation_id"] == OBSERVATION_ID
            )
            self.assertEqual(current_row, self.payload["live_observation"])
            for expected in self.payload["live_evidence"]:
                current_evidence = next(
                    row for row in evidence["evidence"]
                    if row["evidence_id"] == expected["evidence_id"]
                )
                self.assertEqual(current_evidence, expected)
            self.assertEqual(current_row["canonical_links"], [])
        report = validate_live_intelligence(schema, evidence, observations, self.canonical)
        self.assertTrue(report.ok, report.errors)

    def test_co_preserves_cm_correction_conflict_contract_exactly(self):
        schema, _, _ = self.simulate()
        self.assertEqual(schema["correction_conflict_policy"], self.schema["correction_conflict_policy"])
        self.assertEqual(schema["correction_conflict_policy"]["minimum_unique_conflict_evidence_refs"], 2)
        self.assertEqual(schema["correction_conflict_policy"]["minimum_distinct_conflict_providers"], 2)
        self.assertTrue(schema["correction_conflict_policy"]["corrected_or_retracted_requires_correction_evidence"])

    def test_public_projection_and_automatic_ingestion_remain_closed(self):
        schema, observations, evidence = self.simulate()
        self.assertFalse(schema["population_policy"]["automatic_ingestion_allowed"])
        self.assertFalse(schema["population_policy"]["public_observation_projection_allowed"])
        self.assertFalse(schema["public_projection_policy"]["observation_projection_allowed"])
        public = public_live_intelligence_projection(schema, evidence, observations, self.canonical)
        self.assertEqual(public["observations"], [])

    def test_population_overflow_fails_closed(self):
        schema, observations, evidence = self.simulate()
        overflow = copy.deepcopy(observations)
        extra = copy.deepcopy(self.payload["live_observation"])
        extra["observation_id"] = "WSLI-TEST-CO-OVERFLOW"
        overflow["observations"].append(extra)
        report = validate_live_intelligence(schema, evidence, overflow, self.canonical)
        self.assertFalse(report.ok)
        self.assertTrue(any("exceeds reviewed policy maximum" in err for err in report.errors), report.errors)

    def test_upstream_and_analysis_populations_remain_descendant_safe(self):
        canonical = load(CANONICAL_PATH)
        sources = load(SOURCES_PATH)
        ledger = load(LEDGER_PATH)
        monitor = load(MONITOR_PATH)
        reviews = load(ANALYSIS_REVIEWS_PATH)
        analysis_evidence = load(ANALYSIS_EVIDENCE_PATH)
        pre = self.plan["pre_state"]
        self.assertGreaterEqual(len(canonical["records"]), pre["canonical_record_count"])
        self.assertGreaterEqual(len(sources["sources"]), pre["source_count"])
        self.assertGreaterEqual(len(ledger["changes"]), pre["change_ledger_count"])
        self.assertGreaterEqual(len(monitor["adapters"]), pre["monitor_adapter_count"])
        self.assertGreaterEqual(len(reviews["reviews"]), pre["analysis_review_count"])
        self.assertGreaterEqual(len(analysis_evidence["evidence"]), pre["analysis_evidence_count"])
        self.assertFalse(monitor["automatic_canonical_commit"])
        self.assertFalse(monitor["google_calendar_write"])

    def test_target_transform_is_idempotent(self):
        schema, observations, evidence = self.simulate()
        self.assertEqual(target_live_schema(schema, self.plan), schema)
        self.assertEqual(target_observations(observations, self.payload, self.plan), observations)
        self.assertEqual(target_evidence(evidence, self.payload, self.plan), evidence)

    def test_co_checkpoint_records_zero_canonical_growth(self):
        schema, observations, evidence = self.simulate()
        checkpoint = schema["co_checkpoint"]
        self.assertEqual(checkpoint["schema_version"], TARGET_VERSION)
        self.assertEqual(checkpoint["observation_count"], 10)
        self.assertEqual(checkpoint["evidence_count"], 14)
        self.assertEqual(checkpoint["canonical_linked_observation_count"], 3)
        row = next(row for row in observations["observations"] if row["observation_id"] == OBSERVATION_ID)
        self.assertEqual(row, self.payload["live_observation"])
        for expected in self.payload["live_evidence"]:
            evidence_row = next(row for row in evidence["evidence"] if row["evidence_id"] == expected["evidence_id"])
            self.assertEqual(evidence_row, expected)
        self.assertEqual(row["canonical_links"], [])
        self.assertGreaterEqual(len(evidence["evidence"]), checkpoint["evidence_count"])


if __name__ == "__main__":
    unittest.main()
