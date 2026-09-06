from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

from src.world_signals.live_intelligence import (
    public_live_intelligence_projection,
    validate_live_intelligence,
)


class LiveIntelligenceFoundationAVTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / "data/live_intelligence/schema.json").read_text(encoding="utf-8"))
        cls.evidence = json.loads((ROOT / "data/live_intelligence/evidence_registry.json").read_text(encoding="utf-8"))
        cls.observations = json.loads((ROOT / "data/live_intelligence/observations.json").read_text(encoding="utf-8"))
        cls.canonical = json.loads((ROOT / "data/canonical/registry.json").read_text(encoding="utf-8"))

    def opened_schema(self):
        schema = copy.deepcopy(self.schema)
        schema["foundation_population_policy"]["production_population_allowed"] = True
        schema["foundation_population_policy"]["evidence_population_allowed"] = True
        return schema

    def evidence_row(self, evidence_id="WSEV-LI-TEST-1"):
        return {
            "evidence_id": evidence_id,
            "evidence_class": "PRIMARY_OFFICIAL",
            "provider": "Test authority",
            "title": "Test factual observation",
            "url": "https://example.test/observation",
            "roles": ["FACTUAL_OBSERVATION"],
            "canonical_provenance_effect": "NONE",
        }

    def observation_row(self, observation_id="WSLI-TEST-1", evidence_id="WSEV-LI-TEST-1"):
        return {
            "observation_id": observation_id,
            "observed_at_utc": "2026-09-06T00:00:00Z",
            "observation_type": "OFFICIAL_ANNOUNCEMENT",
            "verification_state": "PRIMARY_CONFIRMED",
            "headline": "Test observation",
            "summary": "A factual observation used only to exercise the Live Intelligence contract.",
            "domain_tags": ["INSTITUTIONS"],
            "jurisdictions": ["Test jurisdiction"],
            "regions": ["Cross-regional / Global"],
            "evidence_refs": [evidence_id],
            "canonical_links": [],
            "revision_of_observation_id": None,
            "automatic_canonical_commit": False,
            "google_calendar_write": False,
        }

    def validate(self, schema=None, evidence=None, observations=None):
        return validate_live_intelligence(
            schema or self.schema,
            evidence or self.evidence,
            observations or self.observations,
            self.canonical,
        )

    def test_exact_post_76_foundation_is_empty_and_valid(self):
        self.assertEqual(self.schema["version"], "0.1")
        self.assertEqual(self.observations["population_state"], "FOUNDATION_ONLY_NO_POPULATION")
        self.assertEqual(self.observations["observations"], [])
        self.assertEqual(self.evidence["evidence"], [])
        report = self.validate()
        self.assertTrue(report.ok, report.errors)

    def test_foundation_population_gate_rejects_convenience_population(self):
        evidence = copy.deepcopy(self.evidence)
        observations = copy.deepcopy(self.observations)
        evidence["evidence"].append(self.evidence_row())
        observations["observations"].append(self.observation_row())
        report = self.validate(evidence=evidence, observations=observations)
        joined = " ".join(report.errors)
        self.assertIn("prohibits production observation population", joined)
        self.assertIn("prohibits evidence population", joined)

    def test_unscheduled_observation_can_exist_without_canonical_identity_when_gate_later_opens(self):
        schema = self.opened_schema()
        evidence = copy.deepcopy(self.evidence)
        observations = copy.deepcopy(self.observations)
        evidence["evidence"].append(self.evidence_row())
        observations["observations"].append(self.observation_row())
        report = self.validate(schema=schema, evidence=evidence, observations=observations)
        self.assertTrue(report.ok, report.errors)

    def test_canonical_link_must_resolve_but_is_optional(self):
        schema = self.opened_schema()
        evidence = copy.deepcopy(self.evidence)
        observations = copy.deepcopy(self.observations)
        evidence["evidence"].append(self.evidence_row())
        row = self.observation_row()
        row["canonical_links"] = [
            {"occurrence_id": "WSO-MAC-A-0025", "relationship": "CONTEXT_FOR"}
        ]
        observations["observations"].append(row)
        self.assertTrue(self.validate(schema=schema, evidence=evidence, observations=observations).ok)

        observations["observations"][0]["canonical_links"][0]["occurrence_id"] = "WSO-DOES-NOT-EXIST"
        report = self.validate(schema=schema, evidence=evidence, observations=observations)
        self.assertIn("unknown canonical occurrence", " ".join(report.errors))

    def test_analysis_only_interpretation_fields_are_rejected(self):
        schema = self.opened_schema()
        evidence = copy.deepcopy(self.evidence)
        observations = copy.deepcopy(self.observations)
        evidence["evidence"].append(self.evidence_row())
        row = self.observation_row()
        row["what_appears_connected"] = {"causal_status": "OBSERVED_ASSOCIATION"}
        observations["observations"].append(row)
        report = self.validate(schema=schema, evidence=evidence, observations=observations)
        joined = " ".join(report.errors)
        self.assertIn("Analysis-only fields prohibited", joined)
        self.assertIn("causal_status", joined)

    def test_evidence_refs_and_live_provenance_fail_closed(self):
        schema = self.opened_schema()
        evidence = copy.deepcopy(self.evidence)
        observations = copy.deepcopy(self.observations)
        bad_evidence = self.evidence_row()
        bad_evidence["canonical_provenance_effect"] = "REASSIGN_SOURCE"
        evidence["evidence"].append(bad_evidence)
        row = self.observation_row()
        row["evidence_refs"] = ["WSEV-LI-MISSING"]
        observations["observations"].append(row)
        report = self.validate(schema=schema, evidence=evidence, observations=observations)
        joined = " ".join(report.errors)
        self.assertIn("cannot alter canonical provenance", joined)
        self.assertIn("unknown evidence_ref", joined)

    def test_observation_time_is_exact_utc_and_separate_from_event_time(self):
        schema = self.opened_schema()
        evidence = copy.deepcopy(self.evidence)
        observations = copy.deepcopy(self.observations)
        evidence["evidence"].append(self.evidence_row())
        row = self.observation_row()
        row["observed_at_utc"] = "2026-09-06T10:00:00+10:00"
        row["event_time"] = {
            "precision": "CIVIL_DATE",
            "event_date": "2026-09-06",
            "event_at_utc": "2026-09-06T00:00:00Z",
        }
        observations["observations"].append(row)
        report = self.validate(schema=schema, evidence=evidence, observations=observations)
        joined = " ".join(report.errors)
        self.assertIn("observed_at_utc must be an exact UTC timestamp", joined)
        self.assertIn("civil date must not be upgraded", joined)

    def test_data_revision_requires_explicit_prior_observation(self):
        schema = self.opened_schema()
        evidence = copy.deepcopy(self.evidence)
        observations = copy.deepcopy(self.observations)
        evidence["evidence"].append(self.evidence_row())
        revision = self.observation_row()
        revision["observation_type"] = "DATA_REVISION"
        observations["observations"].append(revision)
        report = self.validate(schema=schema, evidence=evidence, observations=observations)
        self.assertIn("DATA_REVISION requires revision_of_observation_id", " ".join(report.errors))

    def test_revision_history_is_append_only_and_acyclic(self):
        schema = self.opened_schema()
        evidence = copy.deepcopy(self.evidence)
        observations = copy.deepcopy(self.observations)
        evidence["evidence"].append(self.evidence_row())
        first = self.observation_row("WSLI-TEST-1")
        second = self.observation_row("WSLI-TEST-2")
        first["revision_of_observation_id"] = "WSLI-TEST-2"
        second["revision_of_observation_id"] = "WSLI-TEST-1"
        observations["observations"].extend([first, second])
        report = self.validate(schema=schema, evidence=evidence, observations=observations)
        self.assertIn("revision graph contains a cycle", " ".join(report.errors))

    def test_source_failure_is_not_live_fact_and_write_gates_are_closed(self):
        boundary = self.schema["layer_boundary"]
        self.assertFalse(boundary["source_failure_or_absence_may_create_live_fact"])
        self.assertFalse(boundary["canonical_mutation_allowed"])
        self.assertFalse(boundary["calendar_mutation_allowed"])
        self.assertFalse(boundary["analysis_mutation_allowed"])
        self.assertFalse(boundary["causal_interpretation_allowed"])
        self.assertFalse(boundary["market_move_attribution_allowed"])

    def test_existing_analysis_evidence_is_not_migration_seed(self):
        policy = self.schema["foundation_population_policy"]
        self.assertFalse(policy["existing_analysis_evidence_migration_allowed"])
        analysis_evidence = json.loads((ROOT / "data/analysis/evidence_registry.json").read_text(encoding="utf-8"))
        self.assertGreater(len(analysis_evidence["evidence"]), 0)
        self.assertEqual(self.evidence["evidence"], [])

    def test_public_projection_is_metadata_only_not_a_fake_live_feed(self):
        projection = public_live_intelligence_projection(
            self.schema, self.evidence, self.observations, self.canonical
        )
        metadata = projection["metadata"]
        self.assertEqual(metadata["projection_type"], "LIVE_INTELLIGENCE_FOUNDATION_NOT_RUNTIME_FEED")
        self.assertEqual(metadata["schema_version"], "0.1")
        self.assertEqual(metadata["internal_observation_count"], 0)
        self.assertEqual(metadata["public_observation_count"], 0)
        self.assertEqual(metadata["canonical_registry_version_at_build"], "0.38")
        self.assertEqual(metadata["canonical_record_count_at_build"], 688)
        self.assertFalse(metadata["runtime_feed_claim"])
        self.assertEqual(projection["observations"], [])


if __name__ == "__main__":
    unittest.main()
