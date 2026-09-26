from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.signals import public_signal_projection, validate_signals


class SignalContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def load(relative):
            return json.loads((ROOT / relative).read_text(encoding="utf-8"))

        cls.schema = load("data/signals/schema.json")
        cls.live_observations = load("data/live_intelligence/observations.json")
        cls.live_evidence = load("data/live_intelligence/evidence_registry.json")

    def upstream_fixture(self, contradictory=False):
        observations = deepcopy(self.live_observations)
        evidence = deepcopy(self.live_evidence)
        evidence_rows = [
            {
                "evidence_id": "WSEV-SIG-TEST-1",
                "provider": "Synthetic authority one",
            },
            {
                "evidence_id": "WSEV-SIG-TEST-2",
                "provider": "Synthetic authority two",
            },
        ]
        observation_rows = [
            {
                "observation_id": "WSLI-SIG-TEST-1",
                "observed_at_utc": "2026-09-01T00:00:00Z",
                "verification_state": "PRIMARY_CONFIRMED",
                "evidence_refs": ["WSEV-SIG-TEST-1"],
            },
            {
                "observation_id": "WSLI-SIG-TEST-2",
                "observed_at_utc": "2026-09-02T00:00:00Z",
                "verification_state": "PRIMARY_CONFIRMED",
                "evidence_refs": ["WSEV-SIG-TEST-2"],
            },
        ]
        if contradictory:
            evidence_rows.append(
                {
                    "evidence_id": "WSEV-SIG-TEST-3",
                    "provider": "Synthetic authority three",
                }
            )
            observation_rows.append(
                {
                    "observation_id": "WSLI-SIG-TEST-3",
                    "observed_at_utc": "2026-09-03T00:00:00Z",
                    "verification_state": "PRIMARY_CONFIRMED",
                    "evidence_refs": ["WSEV-SIG-TEST-3"],
                }
            )
        evidence["evidence"].extend(evidence_rows)
        observations["observations"].extend(observation_rows)
        return observations, evidence

    def signal_row(self, **overrides):
        row = {
            "signal_id": "WSSIG-TEST-001",
            "revision_id": "WSSIG-TEST-001-R1",
            "revision_number": 1,
            "previous_revision_id": None,
            "title": "Synthetic persistent pressure",
            "signal_type": "PERSISTENT_CHANGE",
            "observation_ids": ["WSLI-SIG-TEST-1", "WSLI-SIG-TEST-2"],
            "evidence_refs": ["WSEV-SIG-TEST-1", "WSEV-SIG-TEST-2"],
            "entities": ["Synthetic entity"],
            "jurisdictions": ["Synthetic jurisdiction"],
            "regions": ["Cross-regional / Global"],
            "domains": ["ECONOMICS", "MARKETS"],
            "direction": "UPWARD",
            "magnitude": "MODERATE",
            "novelty": "NEW",
            "persistence": "PERSISTENT",
            "trend_state": "ACCELERATING",
            "corroboration": {
                "state": "INDEPENDENT",
                "independent_observation_count": 2,
                "distinct_provider_count": 2,
            },
            "confidence": "MEDIUM",
            "transmission_relevance": [
                {
                    "channel": "repricing exposure",
                    "affected_domains": ["MARKETS"],
                    "relationship_status": "HYPOTHESISED_TRANSMISSION",
                    "rationale": "Synthetic test rationale only.",
                }
            ],
            "first_detected_at_utc": "2026-09-01T00:00:00Z",
            "latest_supporting_observation_id": "WSLI-SIG-TEST-2",
            "review_state": "UNDER_REVIEW",
            "lifecycle_state": "UNRESOLVED",
            "expiry": {
                "mode": "REVIEW_REQUIRED",
                "condition": "Review if supporting observations go stale.",
            },
            "supporting_rationale": "Synthetic review rationale only.",
            "contradictory_evidence_refs": [],
            "falsification_conditions": ["The observed change is corrected or withdrawn."],
            "review_provenance": {
                "created_by": "synthetic-test",
                "created_at_utc": "2026-09-03T00:00:00Z",
                "reviewed_by": None,
                "reviewed_at_utc": None,
                "decision_basis": None,
            },
        }
        row.update(overrides)
        return row

    def dataset(self, rows):
        return {
            "version": self.schema["version"],
            "population_state": "CLOSED_NO_PRODUCTION_SIGNALS",
            "signals": rows,
        }

    def validate(self, rows, observations=None, evidence=None):
        observations, evidence = observations or self.upstream_fixture()[0], evidence or self.upstream_fixture()[1]
        return validate_signals(self.schema, self.dataset(rows), observations, evidence)

    def test_closed_production_dataset_is_valid_and_empty(self):
        report = validate_signals(
            self.schema,
            self.dataset([]),
            self.live_observations,
            self.live_evidence,
        )
        self.assertTrue(report.ok, report.errors)
        projection = public_signal_projection(
            self.schema,
            self.dataset([]),
            self.live_observations,
            self.live_evidence,
        )
        self.assertEqual(projection["metadata"]["public_signal_count"], 0)
        self.assertEqual(projection["signals"], [])

    def test_signal_references_existing_immutable_observations(self):
        observations, evidence = self.upstream_fixture()
        report = self.validate([self.signal_row()], observations, evidence)
        self.assertTrue(report.ok, report.errors)

    def test_nonexistent_observation_reference_fails(self):
        observations, evidence = self.upstream_fixture()
        row = self.signal_row(observation_ids=["WSLI-SIG-DOES-NOT-EXIST", "WSLI-SIG-TEST-2"])
        report = self.validate([row], observations, evidence)
        self.assertIn("unknown observation_id WSLI-SIG-DOES-NOT-EXIST", " ".join(report.errors))

    def test_duplicate_observation_ids_cannot_increase_corroboration(self):
        observations, evidence = self.upstream_fixture()
        row = self.signal_row(observation_ids=["WSLI-SIG-TEST-1", "WSLI-SIG-TEST-1"])
        report = self.validate([row], observations, evidence)
        self.assertIn("duplicate observation_ids", " ".join(report.errors))

    def test_contradictory_evidence_remains_explicit(self):
        observations, evidence = self.upstream_fixture(contradictory=True)
        row = self.signal_row(
            observation_ids=["WSLI-SIG-TEST-1", "WSLI-SIG-TEST-2", "WSLI-SIG-TEST-3"],
            evidence_refs=["WSEV-SIG-TEST-1", "WSEV-SIG-TEST-2"],
            contradictory_evidence_refs=["WSEV-SIG-TEST-3"],
            corroboration={
                "state": "CONFLICTED",
                "independent_observation_count": 2,
                "distinct_provider_count": 3,
            },
        )
        report = self.validate([row], observations, evidence)
        self.assertTrue(report.ok, report.errors)

    def test_revision_history_preserves_prior_assessment(self):
        observations, evidence = self.upstream_fixture()
        first = self.signal_row(
            review_state="ACCEPTED",
            lifecycle_state="ACTIVE",
            review_provenance={
                "created_by": "synthetic-test",
                "created_at_utc": "2026-09-03T00:00:00Z",
                "reviewed_by": "synthetic-reviewer",
                "reviewed_at_utc": "2026-09-03T01:00:00Z",
                "decision_basis": "Synthetic contract test only.",
            },
        )
        second = deepcopy(first)
        second.update(
            {
                "revision_id": "WSSIG-TEST-001-R2",
                "revision_number": 2,
                "previous_revision_id": "WSSIG-TEST-001-R1",
                "lifecycle_state": "WEAKENING",
                "trend_state": "DECELERATING",
                "supporting_rationale": "Synthetic revised assessment only.",
            }
        )
        report = self.validate([first, second], observations, evidence)
        self.assertTrue(report.ok, report.errors)

    def test_rejected_signal_cannot_project_as_active(self):
        observations, evidence = self.upstream_fixture()
        row = self.signal_row(review_state="REJECTED", lifecycle_state="WITHDRAWN")
        report = self.validate([row], observations, evidence)
        self.assertTrue(report.ok, report.errors)
        projection = public_signal_projection(
            self.schema,
            self.dataset([row]),
            observations,
            evidence,
        )
        self.assertEqual(projection["signals"], [])

    def test_forecast_fields_are_rejected(self):
        observations, evidence = self.upstream_fixture()
        row = self.signal_row(probability=0.7)
        report = self.validate([row], observations, evidence)
        self.assertIn("forecast/scenario fields are prohibited", " ".join(report.errors))

    def test_malformed_signal_fails_closed_without_validator_exception(self):
        observations, evidence = self.upstream_fixture()
        row = self.signal_row(
            corroboration=[],
            observation_ids=[{"not": "an observation id"}, "WSLI-SIG-TEST-2"],
        )
        report = self.validate([row], observations, evidence)
        self.assertFalse(report.ok)
        self.assertIn("corroboration must be an object", " ".join(report.errors))

    def test_synthetic_fixture_does_not_change_closed_production_population(self):
        observations, evidence = self.upstream_fixture()
        row = self.signal_row()
        projection = public_signal_projection(
            self.schema,
            self.dataset([row]),
            observations,
            evidence,
        )
        self.assertEqual(projection["metadata"]["internal_signal_count"], 1)
        self.assertEqual(projection["metadata"]["public_signal_count"], 0)
        self.assertEqual(projection["signals"], [])


if __name__ == "__main__":
    unittest.main()
