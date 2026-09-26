from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.signals import (
    public_signal_projection, validate_signals, validate_signal_history,
    observation_digest, signal_state_as_of, observation_signal_dependencies,
)
from world_signals.live_intelligence import validate_live_intelligence


class SignalContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def load(relative):
            return json.loads((ROOT / relative).read_text(encoding="utf-8"))

        cls.schema = load("data/signals/schema.json")
        cls.live_observations = load("data/live_intelligence/observations.json")
        cls.live_evidence = load("data/live_intelligence/evidence_registry.json")
        cls.live_schema = load("data/live_intelligence/schema.json")
        cls.canonical = load("data/canonical/registry.json")

    def upstream_fixture(self, contradictory=False):
        observations = deepcopy(self.live_observations)
        evidence = deepcopy(self.live_evidence)
        evidence_rows = [
            {
                "evidence_id": "WSEV-SIG-TEST-1",
                "provider": "Synthetic authority one",
                "evidence_class": "PRIMARY_OFFICIAL",
                "url": "https://one.example.test/report",
                "roles": ["FACTUAL_OBSERVATION"],
            },
            {
                "evidence_id": "WSEV-SIG-TEST-2",
                "provider": "Synthetic authority two",
                "evidence_class": "PRIMARY_OFFICIAL",
                "url": "https://two.example.test/report",
                "roles": ["FACTUAL_OBSERVATION"],
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
                    "evidence_class": "PRIMARY_OFFICIAL",
                    "url": "https://three.example.test/report",
                    "roles": ["FACTUAL_OBSERVATION"],
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
            "revision_reason": "Initial synthetic assessment for contract testing.",
            "baseline": {"description": "First observation is the qualitative baseline.", "observation_ids": ["WSLI-SIG-TEST-1"]},
            "assessment_basis": {
                "materiality": "The test change affects a specified exposure, not article volume.",
                "novelty": "New relative to the first snapshot.",
                "persistence": "Two distinct dated snapshots across the interval.",
                "trend": "Qualitative reinforcement, not a measured rate.",
                "confidence": "Moderate because competing explanations remain.",
                "source_quality": "Primary collection, reviewed lineage.",
                "coverage_bias": "Synthetic regional sample is not global coverage.",
                "alternatives": "Seasonality could account for the pattern.",
            },
            "evidence_lineage": [
                {"evidence_ref": "WSEV-SIG-TEST-1", "origin_ids": ["synthetic-collection-one"], "basis": "Independent primary collection."},
                {"evidence_ref": "WSEV-SIG-TEST-2", "origin_ids": ["synthetic-collection-two"], "basis": "Separate primary collection."},
            ],
            "observation_hashes": {r["observation_id"]: observation_digest(r) for r in self.upstream_fixture()[0]["observations"] if r["observation_id"].startswith("WSLI-SIG-TEST-")},
            "correction_review_observation_ids": [],
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
                "rationale": "Two separate collection origins, subject to human lineage review.",
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
                "review_due_at_utc": "2026-09-10T00:00:00Z",
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
        return validate_signal_history(self.schema, rows, observations, evidence)

    def test_closed_production_dataset_is_valid_and_empty(self):
        report = validate_signals(
            self.schema,
            json.loads((ROOT / "data/signals/signals.json").read_text()),
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
        self.assertIn("unknown observation_id", " ".join(report.errors))

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
                "distinct_provider_count": 2,
                "rationale": "Contrary evidence does not add supporting corroboration.",
            },
        )
        row["evidence_lineage"].append({"evidence_ref": "WSEV-SIG-TEST-3", "origin_ids": ["contrary-origin"], "basis": "Independent contrary collection."})
        row["observation_hashes"].update({r["observation_id"]: observation_digest(r) for r in observations["observations"] if r["observation_id"] == "WSLI-SIG-TEST-3"})
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
        second["review_provenance"]["created_at_utc"] = "2026-09-04T00:00:00Z"
        second["review_provenance"]["reviewed_at_utc"] = "2026-09-04T01:00:00Z"
        report = self.validate([first, second], observations, evidence)
        self.assertTrue(report.ok, report.errors)

    def test_rejected_signal_cannot_project_as_active(self):
        observations, evidence = self.upstream_fixture()
        row = self.signal_row(review_state="REJECTED", lifecycle_state="WITHDRAWN")
        row["review_provenance"].update(reviewed_by="reviewer", reviewed_at_utc="2026-09-03T01:00:00Z", decision_basis="Insufficient materiality.")
        report = self.validate([row], observations, evidence)
        self.assertTrue(report.ok, report.errors)
        with self.assertRaises(ValueError):
            public_signal_projection(self.schema, self.dataset([row]), observations, evidence)

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

    def accepted(self):
        row = self.signal_row(review_state="ACCEPTED", lifecycle_state="ACTIVE")
        row["review_provenance"].update(reviewed_by="reviewer", reviewed_at_utc="2026-09-03T01:00:00Z", decision_basis="Reviewed test evidence and alternatives.")
        return row

    def child(self, row):
        child = deepcopy(row)
        child.update(revision_number=row["revision_number"]+1,
                     revision_id=f"{row['signal_id']}-R{row['revision_number']+1}",
                     previous_revision_id=row["revision_id"], revision_reason="New evidence requires reassessment.")
        child["review_provenance"].update(created_at_utc="2026-09-05T00:00:00Z", reviewed_at_utc="2026-09-05T01:00:00Z")
        return child

    def test_baseline_and_qualitative_justifications_are_required(self):
        for field in ("materiality", "persistence", "confidence", "coverage_bias", "source_quality", "alternatives"):
            with self.subTest(field=field):
                row = self.signal_row()
                row["assessment_basis"][field] = ""
                self.assertFalse(self.validate([row]).ok)
        row = self.signal_row()
        row["baseline"]["observation_ids"] = ["missing"]
        self.assertFalse(self.validate([row]).ok)

    def test_shared_origin_syndication_cannot_inflate_corroboration(self):
        row = self.signal_row()
        row["evidence_lineage"][1]["origin_ids"] = ["synthetic-collection-one"]
        self.assertIn("origin components", " ".join(self.validate([row]).errors))
        row["corroboration"].update(state="PARTIAL", independent_observation_count=1)
        self.assertTrue(self.validate([row]).ok)

    def test_same_provider_or_document_is_not_independent(self):
        for field in ("provider", "url"):
            with self.subTest(field=field):
                observations, evidence = self.upstream_fixture()
                evidence["evidence"][-1][field] = evidence["evidence"][-2][field]
                self.assertFalse(self.validate([self.signal_row()], observations, evidence).ok)

    def test_circular_lineage_and_model_text_are_rejected(self):
        row = self.signal_row()
        row["evidence_lineage"][0]["origin_ids"] = ["WSEV-SIG-TEST-2"]
        self.assertIn("circular", " ".join(self.validate([row]).errors))
        observations, evidence = self.upstream_fixture()
        evidence["evidence"][-1]["evidence_class"] = "MODEL_GENERATED"
        self.assertIn("model-generated", " ".join(self.validate([self.signal_row()], observations, evidence).errors))

    def test_context_only_cannot_be_counted_as_support(self):
        observations, evidence = self.upstream_fixture()
        evidence["evidence"][-1]["roles"] = ["CONTEXT_ONLY"]
        self.assertIn("context-only", " ".join(self.validate([self.signal_row()], observations, evidence).errors))

    def test_future_publication_cannot_inflate_prior_assessment(self):
        observations, evidence = self.upstream_fixture()
        evidence["evidence"][-1]["publication_time"] = {"precision": "CIVIL_DATE", "published_date": "2026-09-10"}
        self.assertIn("future publication", " ".join(self.validate([self.signal_row()], observations, evidence).errors))

    def test_causal_mechanism_is_not_granted_by_signal_contract(self):
        row = self.signal_row()
        row["transmission_relevance"][0]["relationship_status"] = "REVIEWED_MECHANISM"
        self.assertFalse(self.validate([row]).ok)

    def test_one_headline_cannot_be_persistent(self):
        observations, evidence = self.upstream_fixture()
        observations["observations"][-1]["observed_at_utc"] = observations["observations"][-2]["observed_at_utc"]
        row = self.signal_row()
        row["observation_hashes"]["WSLI-SIG-TEST-2"] = observation_digest(observations["observations"][-1])
        self.assertIn("multiple observation times", " ".join(self.validate([row], observations, evidence).errors))

    def test_all_linked_evidence_must_be_classified(self):
        observations, evidence = self.upstream_fixture(contradictory=True)
        row = self.signal_row()
        row["observation_ids"].append("WSLI-SIG-TEST-3")
        row["observation_hashes"]["WSLI-SIG-TEST-3"] = observation_digest(observations["observations"][-1])
        self.assertIn("every linked evidence", " ".join(self.validate([row], observations, evidence).errors))

    def test_decisions_require_reviewer_time_and_reason(self):
        for state, lifecycle in (("ACCEPTED", "ACTIVE"), ("REJECTED", "WITHDRAWN")):
            for field in ("reviewed_by", "reviewed_at_utc", "decision_basis"):
                with self.subTest(state=state, field=field):
                    row = self.accepted()
                    row.update(review_state=state, lifecycle_state=lifecycle)
                    row["review_provenance"][field] = None
                    self.assertFalse(self.validate([row]).ok)

    def test_retained_history_cannot_be_rewritten_or_removed(self):
        observations, evidence = self.upstream_fixture()
        first = self.accepted()
        child = self.child(first)
        self.assertTrue(validate_signal_history(self.schema, [first, child], observations, evidence, previous_revisions=[first]).ok)
        altered = deepcopy(first)
        altered["confidence"] = "HIGH"
        for revisions in ([altered, child], [child]):
            report = validate_signal_history(self.schema, revisions, observations, evidence, previous_revisions=[first])
            self.assertFalse(report.ok)

    def test_revision_cannot_backdate_decision_or_use_future_evidence(self):
        first = self.accepted()
        child = self.child(first)
        child["review_provenance"]["created_at_utc"] = first["review_provenance"]["created_at_utc"]
        self.assertIn("strictly advance", " ".join(self.validate([first, child]).errors))
        row = self.signal_row()
        row["review_provenance"]["created_at_utc"] = "2026-09-01T00:00:00Z"
        self.assertIn("future evidence", " ".join(self.validate([row]).errors))

    def test_observation_mutation_breaks_snapshot_pin(self):
        observations, evidence = self.upstream_fixture()
        observations["observations"][-1]["headline"] = "Retrospectively rewritten"
        self.assertIn("hash mismatch", " ".join(self.validate([self.signal_row()], observations, evidence).errors))

    def test_terminal_states_do_not_masquerade_as_active(self):
        observations, evidence = self.upstream_fixture()
        for state in ("EXPIRED", "WITHDRAWN", "SUPERSEDED"):
            with self.subTest(state=state):
                row = self.accepted()
                row["lifecycle_state"] = state
                child = self.child(row)
                child["lifecycle_state"] = "ACTIVE"
                self.assertFalse(self.validate([row, child]).ok)
                result = signal_state_as_of(self.schema, [row], observations, evidence, "2026-09-04T00:00:00Z")
                self.assertEqual(state, result[row["signal_id"]]["effective_state"])

    def test_candidate_requires_explicit_review_transition(self):
        row = self.signal_row(review_state="CANDIDATE")
        child = self.child(row)
        child.update(review_state="ACCEPTED", lifecycle_state="ACTIVE")
        child["review_provenance"].update(reviewed_by="reviewer", decision_basis="Decision")
        self.assertIn("invalid review transition", " ".join(self.validate([row, child]).errors))

    def test_expiry_is_deterministic_and_does_not_rewrite_history(self):
        observations, evidence = self.upstream_fixture()
        row = self.accepted()
        row["expiry"] = {"mode": "STALE_AFTER", "stale_after_days": 4, "condition": "Reassess without new supporting evidence."}
        before = deepcopy(row)
        for at, state in (("2026-09-04T00:00:00Z", "ACTIVE"), ("2026-09-06T00:00:00Z", "STALE")):
            result = signal_state_as_of(self.schema, [row], observations, evidence, at)
            self.assertEqual(state, result[row["signal_id"]]["effective_state"])
        self.assertEqual(before, row)
        row["expiry"] = {"mode": "EXPLICIT_DATE", "expires_at_utc": "2026-09-02T00:00:00Z", "condition": "Expired"}
        self.assertFalse(self.validate([row]).ok)

    def correction_fixture(self, state="CORRECTED"):
        observations, evidence = self.upstream_fixture()
        evidence["evidence"].append({"evidence_id": "correction-evidence", "provider": "Correction authority", "evidence_class": "PRIMARY_OFFICIAL", "roles": ["CORRECTION_OR_REVISION"]})
        correction = {"observation_id": "correction", "observed_at_utc": "2026-09-04T00:00:00Z", "verification_state": state,
                      "revision_of_observation_id": "WSLI-SIG-TEST-2", "evidence_refs": ["correction-evidence"]}
        observations["observations"].append(correction)
        return observations, evidence

    def test_new_cm_correction_triggers_review_without_rewriting_old_assessment(self):
        for state in ("CORRECTED", "RETRACTED"):
            with self.subTest(state=state):
                observations, evidence = self.correction_fixture(state)
                row = self.accepted()
                before = deepcopy((row, observations, evidence))
                for at, expected in (("2026-09-03T02:00:00Z", "ACTIVE"), ("2026-09-04T00:00:00Z", "REVIEW_REQUIRED")):
                    result = signal_state_as_of(self.schema, [row], observations, evidence, at)
                    self.assertEqual(expected, result[row["signal_id"]]["effective_state"])
                self.assertEqual(before, (row, observations, evidence))
                child = self.child(row)
                self.assertIn("explicit Signal review", " ".join(self.validate([row, child], observations, evidence).errors))

    def test_correction_fixture_uses_the_existing_live_cm_contract(self):
        schema = deepcopy(self.live_schema)
        schema["population_policy"]["maximum_observation_count"] = 999
        schema["population_policy"]["maximum_evidence_count"] = 999
        evidence = deepcopy(self.live_evidence)
        observations = deepcopy(self.live_observations)
        evidence["evidence"].append({
            "evidence_id": "WSEV-SIG-CM-CORRECTION",
            "evidence_class": "PRIMARY_OFFICIAL",
            "provider": "Synthetic correction authority",
            "title": "Synthetic correction evidence",
            "url": "https://example.test/signal-correction",
            "roles": ["CORRECTION_OR_REVISION"],
            "publication_time": {"precision": "CIVIL_DATE", "published_date": "2026-09-10"},
            "canonical_provenance_effect": "NONE",
        })
        original = deepcopy(observations["observations"][0])
        original["observation_id"] = "WSLI-SIG-CM-ORIGINAL"
        original["observed_at_utc"] = "2026-09-10T01:00:00Z"
        original["evidence_refs"] = ["WSEV-SIG-CM-CORRECTION"]
        original["revision_of_observation_id"] = None
        corrected = deepcopy(original)
        corrected.update({
            "observation_id": "WSLI-SIG-CM-CORRECTED",
            "observed_at_utc": "2026-09-10T02:00:00Z",
            "verification_state": "CORRECTED",
            "revision_of_observation_id": original["observation_id"],
        })
        observations["observations"].extend([original, corrected])
        report = validate_live_intelligence(schema, evidence, observations, self.canonical)
        self.assertTrue(report.ok, report.errors)

    def test_reviewed_correction_revision_preserves_prior_snapshot(self):
        observations, evidence = self.correction_fixture()
        first = self.accepted()
        child = self.child(first)
        child.update(observation_ids=["WSLI-SIG-TEST-1", "correction"], evidence_refs=["WSEV-SIG-TEST-1", "correction-evidence"],
                     latest_supporting_observation_id="correction", correction_review_observation_ids=["correction"])
        child["observation_hashes"] = {r["observation_id"]: observation_digest(r) for r in observations["observations"] if r["observation_id"] in child["observation_ids"]}
        child["evidence_lineage"][1].update(evidence_ref="correction-evidence", origin_ids=["corrected-collection"])
        report = self.validate([first, child], observations, evidence)
        self.assertTrue(report.ok, report.errors)
        reverse = observation_signal_dependencies([first, child])
        self.assertEqual([first["signal_id"]], reverse["WSLI-SIG-TEST-2"])
        self.assertEqual([first["signal_id"]], reverse["correction"])

    def test_nested_malformed_values_fail_without_exceptions(self):
        bad_values = (None, [], {}, True, 1.5, "", "bogus")
        template = self.signal_row()
        for field in template:
            for value in bad_values:
                with self.subTest(field=field, value=value):
                    row = deepcopy(template)
                    row[field] = value
                    report = self.validate([row])
                    self.assertIsInstance(report.ok, bool)
        for obj in ("corroboration", "review_provenance", "expiry", "baseline"):
            for field in template[obj]:
                for value in bad_values:
                    with self.subTest(obj=obj, field=field, value=value):
                        row = deepcopy(template)
                        row[obj][field] = value
                        self.assertIsInstance(self.validate([row]).ok, bool)

    def test_missing_or_unknown_fields_fail_without_exceptions(self):
        row = self.signal_row()
        row.pop("baseline")
        self.assertFalse(self.validate([row]).ok)
        row = self.signal_row()
        row["unapproved_internal_note"] = "private"
        self.assertFalse(self.validate([row]).ok)

    def test_public_gate_cannot_be_opened_by_fixture_flag(self):
        observations, evidence = self.upstream_fixture()
        schema = deepcopy(self.schema)
        schema["population_policy"]["production_population_allowed"] = True
        with self.assertRaises(ValueError):
            public_signal_projection(schema, self.dataset([]), observations, evidence)

    def test_synthetic_fixture_does_not_change_closed_production_population(self):
        observations, evidence = self.upstream_fixture()
        row = self.signal_row()
        self.assertTrue(self.validate([row], observations, evidence).ok)
        report = validate_signals(self.schema, self.dataset([row]), observations, evidence)
        self.assertIn("closed production population gate", " ".join(report.errors))
        with self.assertRaises(ValueError):
            public_signal_projection(self.schema, self.dataset([row]), observations, evidence)


if __name__ == "__main__":
    unittest.main()
