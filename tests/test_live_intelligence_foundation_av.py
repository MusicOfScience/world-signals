from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.live_intelligence import (
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
        if "population_policy" in schema:
            schema["population_policy"]["production_population_allowed"] = True
            schema["population_policy"]["evidence_population_allowed"] = True
            schema["population_policy"]["maximum_observation_count"] = 999
            schema["population_policy"]["maximum_evidence_count"] = 999
        else:
            schema["foundation_population_policy"]["production_population_allowed"] = True
            schema["foundation_population_policy"]["evidence_population_allowed"] = True
        return schema

    def evidence_row(self, evidence_id="WSEV-LI-TEST-1", roles=None):
        return {
            "evidence_id": evidence_id,
            "evidence_class": "PRIMARY_OFFICIAL",
            "provider": "Test authority",
            "title": "Test factual observation",
            "url": "https://example.test/observation",
            "roles": roles or ["FACTUAL_OBSERVATION"],
            "publication_time": {"precision": "CIVIL_DATE", "published_date": "2026-09-06"},
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

    def test_av_foundation_checkpoint_is_preserved_while_live_descendants_may_grow(self):
        if self.schema["version"] == "0.1":
            self.assertEqual(self.observations["population_state"], "FOUNDATION_ONLY_NO_POPULATION")
            self.assertEqual(self.observations["observations"], [])
            self.assertEqual(self.evidence["evidence"], [])
        else:
            checkpoint = self.schema["foundation_checkpoint"]
            self.assertEqual(checkpoint["schema_version"], "0.1")
            self.assertEqual(checkpoint["population_state"], "FOUNDATION_ONLY_NO_POPULATION")
            self.assertEqual(checkpoint["observation_count"], 0)
            self.assertEqual(checkpoint["evidence_count"], 0)
        report = self.validate()
        self.assertTrue(report.ok, report.errors)

    def test_foundation_population_gate_rejects_convenience_population(self):
        schema = copy.deepcopy(self.schema)
        schema.pop("population_policy", None)
        schema["foundation_population_policy"] = {
            "production_population_allowed": False,
            "evidence_population_allowed": False,
            "existing_analysis_evidence_migration_allowed": False,
            "public_observation_projection_allowed": False,
        }
        evidence = copy.deepcopy(self.evidence)
        observations = copy.deepcopy(self.observations)
        evidence["evidence"].append(self.evidence_row("WSEV-LI-TEST-FOUNDATION"))
        observations["observations"].append(self.observation_row("WSLI-TEST-FOUNDATION", "WSEV-LI-TEST-FOUNDATION"))
        report = self.validate(schema=schema, evidence=evidence, observations=observations)
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

        row["canonical_links"][0]["occurrence_id"] = "WSO-DOES-NOT-EXIST"
        report = self.validate(schema=schema, evidence=evidence, observations=observations)
        self.assertIn("unknown canonical occurrence", " ".join(report.errors))

    def test_inferential_canonical_relationships_are_not_live_vocab(self):
        relationships = set(self.schema["controlled_vocabularies"]["canonical_relationship"])
        self.assertNotIn("AFFECTS_EXPECTATION_FOR", relationships)
        self.assertNotIn("RESPONSE_OBSERVATION_FOR", relationships)
        self.assertIn("COINCIDENT_WITH", relationships)

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

    def test_pre_analysis_semantics_keep_confidence_and_explanations_noncausal(self):
        semantics = self.schema["pre_analysis_semantics"]
        self.assertIn("verification_state", semantics["confidence"])
        self.assertIn("belongs in Analysis", semantics["competing_explanation"])
        self.assertIn("Attribution", semantics["market_reaction"])
        self.assertFalse(self.schema["story_grouping_policy"]["automatic_clustering_allowed"])

    def test_monitor_candidates_do_not_automatically_promote_to_live_intelligence(self):
        bridge = self.schema["monitor_bridge_policy"]
        self.assertFalse(bridge["automatic_promotion_from_monitor_candidate"])
        self.assertTrue(bridge["monitor_review_candidate_is_not_live_intelligence_observation"])
        self.assertTrue(bridge["positive_monitor_evidence_requires_separate_live_evidence_record"])

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

    def test_exact_event_time_may_preserve_matching_native_local_time_and_iana_zone(self):
        schema = self.opened_schema()
        evidence = copy.deepcopy(self.evidence)
        observations = copy.deepcopy(self.observations)
        evidence["evidence"].append(self.evidence_row())
        row = self.observation_row()
        row["event_time"] = {
            "precision": "EXACT_TIMESTAMP",
            "event_at_utc": "2026-09-04T23:30:00Z",
            "event_local": "2026-09-05T09:30:00",
            "event_timezone": "Australia/Melbourne",
        }
        observations["observations"].append(row)
        report = self.validate(schema=schema, evidence=evidence, observations=observations)
        self.assertTrue(report.ok, report.errors)

        row["event_time"]["event_timezone"] = "Asia/Tokyo"
        report = self.validate(schema=schema, evidence=evidence, observations=observations)
        self.assertIn("do not match event_at_utc", " ".join(report.errors))

    def test_external_data_revision_does_not_require_synthetic_prior_live_observation(self):
        schema = self.opened_schema()
        evidence = copy.deepcopy(self.evidence)
        observations = copy.deepcopy(self.observations)
        evidence["evidence"].append(
            self.evidence_row(roles=["FACTUAL_OBSERVATION", "CORRECTION_OR_REVISION"])
        )
        revision = self.observation_row()
        revision["observation_type"] = "DATA_REVISION"
        revision["revision_target_description"] = (
            "Previously published real-change values for April-June 2026."
        )
        observations["observations"].append(revision)
        report = self.validate(schema=schema, evidence=evidence, observations=observations)
        self.assertTrue(report.ok, report.errors)

        del revision["revision_target_description"]
        report = self.validate(schema=schema, evidence=evidence, observations=observations)
        self.assertIn("DATA_REVISION requires revision_target_description", " ".join(report.errors))

    def test_external_data_revision_requires_revision_evidence_role(self):
        schema = self.opened_schema()
        evidence = copy.deepcopy(self.evidence)
        observations = copy.deepcopy(self.observations)
        evidence["evidence"].append(self.evidence_row())
        revision = self.observation_row()
        revision["observation_type"] = "DATA_REVISION"
        revision["revision_target_description"] = "Previously published estimate."
        observations["observations"].append(revision)
        report = self.validate(schema=schema, evidence=evidence, observations=observations)
        self.assertIn("CORRECTION_OR_REVISION role", " ".join(report.errors))

    def test_correction_to_prior_live_observation_requires_explicit_reference(self):
        schema = self.opened_schema()
        evidence = copy.deepcopy(self.evidence)
        observations = copy.deepcopy(self.observations)
        evidence["evidence"].append(self.evidence_row())
        corrected = self.observation_row()
        corrected["verification_state"] = "CORRECTED"
        observations["observations"].append(corrected)
        report = self.validate(schema=schema, evidence=evidence, observations=observations)
        self.assertIn("corrected/retracted live observation requires revision reference", " ".join(report.errors))

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
        policy = self.schema.get("population_policy") or self.schema["foundation_population_policy"]
        self.assertFalse(policy["existing_analysis_evidence_migration_allowed"])
        analysis_evidence = json.loads((ROOT / "data/analysis/evidence_registry.json").read_text(encoding="utf-8"))
        self.assertGreater(len(analysis_evidence["evidence"]), 0)
        analysis_ids = {row.get("evidence_id") for row in analysis_evidence["evidence"]}
        live_ids = {row.get("evidence_id") for row in self.evidence.get("evidence", [])}
        self.assertTrue(analysis_ids.isdisjoint(live_ids))

    def test_public_projection_remains_metadata_only_not_a_fake_live_feed(self):
        projection = public_live_intelligence_projection(
            self.schema, self.evidence, self.observations, self.canonical
        )
        metadata = projection["metadata"]
        expected_type = (
            "LIVE_INTELLIGENCE_FOUNDATION_NOT_RUNTIME_FEED"
            if self.observations["population_state"] == "FOUNDATION_ONLY_NO_POPULATION"
            else "LIVE_INTELLIGENCE_CURATED_STORE_NOT_RUNTIME_FEED"
        )
        self.assertEqual(metadata["projection_type"], expected_type)
        self.assertEqual(metadata["schema_version"], self.schema["version"])
        self.assertEqual(metadata["internal_observation_count"], len(self.observations["observations"]))
        self.assertEqual(metadata["public_observation_count"], 0)
        self.assertEqual(metadata["canonical_registry_version_at_build"], self.canonical["version"])
        self.assertEqual(metadata["canonical_record_count_at_build"], self.canonical["record_count"])
        self.assertFalse(metadata["runtime_feed_claim"])
        self.assertEqual(projection["observations"], [])


if __name__ == "__main__":
    unittest.main()
