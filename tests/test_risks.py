from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from src.world_signals.risk_projection import public_risk_projection
from src.world_signals.risks import (
    public_risk_state_projection,
    risk_state_as_of,
    risk_state_is_stale,
    validate_risk_state_history,
    validate_risk_states,
)


ROOT = Path(__file__).resolve().parents[1]


class RiskRegimeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / "data/risks/schema.json").read_text())
        cls.canonical = {"records": []}
        cls.observations = {
            "observations": [
                {
                    "observation_id": "OBS-A",
                    "observed_at_utc": "2026-01-01T00:00:00Z",
                    "evidence_refs": ["E-A"],
                },
                {
                    "observation_id": "OBS-B",
                    "observed_at_utc": "2026-01-02T00:00:00Z",
                    "evidence_refs": ["E-B"],
                },
                {
                    "observation_id": "OBS-C",
                    "observed_at_utc": "2026-01-03T00:00:00Z",
                    "evidence_refs": ["E-C"],
                },
            ]
        }
        cls.evidence = {
            "evidence": [
                {
                    "evidence_id": "E-A",
                    "provider": "Provider One",
                    "publication_time": {"published_date": "2026-01-01"},
                },
                {
                    "evidence_id": "E-B",
                    "provider": "Provider One",
                    "publication_time": {"published_date": "2026-01-02"},
                },
                {
                    "evidence_id": "E-C",
                    "provider": "Provider Two",
                    "publication_time": {"published_date": "2026-01-03"},
                },
            ]
        }
        cls.signals = {
            "signals": [
                cls.signal("SIG-A", "SIG-A-R1", "OBS-A", "E-A", "SHIPPING_LOGISTICS"),
                cls.signal("SIG-B", "SIG-B-R1", "OBS-B", "E-B", "ENERGY"),
                cls.signal("SIG-C", "SIG-C-R1", "OBS-C", "E-C", "SHIPPING_LOGISTICS"),
            ]
        }
        cls.relationships = {
            "relationships": [cls.relationship("REL-A", "REL-A-R1", "OBS-B", "E-B")]
        }

    @staticmethod
    def signal(signal_id, revision_id, observation_id, evidence_id, domain, *, lifecycle="ACTIVE", review="ACCEPTED"):
        return {
            "signal_id": signal_id,
            "revision_id": revision_id,
            "revision_number": 1,
            "review_state": review,
            "lifecycle_state": lifecycle,
            "observation_ids": [observation_id],
            "evidence_refs": [evidence_id],
            "domains": [domain],
            "review_provenance": {
                "created_by": "synthetic-reviewer",
                "created_at_utc": "2026-01-04T00:00:00Z",
                "reviewed_by": "synthetic-reviewer" if review == "ACCEPTED" else None,
                "reviewed_at_utc": "2026-01-04T01:00:00Z" if review == "ACCEPTED" else None,
                "decision_basis": "synthetic contract fixture" if review == "ACCEPTED" else None,
            },
        }

    @staticmethod
    def relationship(relationship_id, revision_id, observation_id, evidence_id, *, lifecycle="ACTIVE", review="ACCEPTED"):
        return {
            "relationship_id": relationship_id,
            "revision_id": revision_id,
            "revision_number": 1,
            "review_state": review,
            "lifecycle_state": lifecycle,
            "supporting_observation_ids": [observation_id],
            "supporting_evidence_refs": [evidence_id],
            "domains": ["ENERGY"],
            "mechanism": "shipping disruption to energy exposure",
            "review_provenance": {
                "created_by": "synthetic-reviewer",
                "created_at_utc": "2026-01-04T00:00:00Z",
                "reviewed_by": "synthetic-reviewer" if review == "ACCEPTED" else None,
                "reviewed_at_utc": "2026-01-04T01:00:00Z" if review == "ACCEPTED" else None,
                "decision_basis": "synthetic contract fixture" if review == "ACCEPTED" else None,
            },
        }

    def _support_observations(self, signal_ids, relationship_ids):
        ids = set()
        for signal in self.signals["signals"]:
            if signal["signal_id"] in signal_ids:
                ids.update(signal["observation_ids"])
        for relationship in self.relationships["relationships"]:
            if relationship["relationship_id"] in relationship_ids:
                ids.update(relationship["supporting_observation_ids"])
        return sorted(ids)

    def state(self, *, state_id="RISK-1", revision_id="RISK-1-R1", revision_number=1,
              current="ELEVATED", previous=None, transition="INITIAL_ASSERTION",
              direction="UPWARD", signal_ids=("SIG-A",), relationship_ids=(),
              contradictory_signal_ids=(), contradictory_relationship_ids=(),
              created="2026-01-05T00:00:00Z", reviewed="2026-01-05T01:00:00Z",
              lifecycle="ACTIVE", review="ACCEPTED", previous_revision_id=None,
              supporting_observation_ids=None, expiry=None):
        signal_ids = list(signal_ids)
        relationship_ids = list(relationship_ids)
        contradictory_signal_ids = list(contradictory_signal_ids)
        contradictory_relationship_ids = list(contradictory_relationship_ids)
        support_obs = supporting_observation_ids or self._support_observations(signal_ids, relationship_ids)
        domains = set()
        mechanisms = set()
        providers = set()
        evidence_ids = set()
        for signal in self.signals["signals"]:
            if signal["signal_id"] in signal_ids:
                domains.update(signal["domains"])
                evidence_ids.update(signal["evidence_refs"])
        for relationship in self.relationships["relationships"]:
            if relationship["relationship_id"] in relationship_ids:
                domains.update(relationship["domains"])
                mechanisms.add(relationship["mechanism"])
                evidence_ids.update(relationship["supporting_evidence_refs"])
        for observation_id in support_obs:
            observation = next(item for item in self.observations["observations"] if item["observation_id"] == observation_id)
            evidence_ids.update(observation["evidence_refs"])
        for evidence_id in evidence_ids:
            item = next(item for item in self.evidence["evidence"] if item["evidence_id"] == evidence_id)
            providers.add(item["provider"].lower())
        if expiry is None:
            expiry = {
                "mode": "STALE_AFTER",
                "stale_after_days": 30,
                "expires_at_utc": None,
                "review_due_at_utc": None,
                "condition": "Review if linked evidence becomes stale",
            }
        return {
            "state_id": state_id,
            "revision_id": revision_id,
            "revision_number": revision_number,
            "previous_revision_id": previous_revision_id,
            "title": "Synthetic reviewed state",
            "state_class": "RISK_STATE",
            "system_domain": "shipping-energy exposure",
            "jurisdictions": ["Synthetic jurisdiction"],
            "current_state": current,
            "previous_state": previous,
            "transition_type": transition,
            "transition_direction": direction,
            "supporting_signal_revisions": [{"signal_id": x, "revision_id": f"{x}-R1"} for x in signal_ids],
            "supporting_relationship_revisions": [{"relationship_id": x, "revision_id": f"{x}-R1"} for x in relationship_ids],
            "contradictory_signal_revisions": [{"signal_id": x, "revision_id": f"{x}-R1"} for x in contradictory_signal_ids],
            "contradictory_relationship_revisions": [{"relationship_id": x, "revision_id": f"{x}-R1"} for x in contradictory_relationship_ids],
            "supporting_observation_ids": support_obs,
            "contributing_domains": sorted(domains),
            "convergence": {
                "state": "BROAD_CONVERGENCE" if len(providers) >= 2 and len(domains) >= 2 else "MULTI_DOMAIN" if len(domains) >= 2 else "LIMITED",
                "distinct_signal_count": len(signal_ids),
                "distinct_relationship_count": len(relationship_ids),
                "distinct_observation_count": len(support_obs),
                "distinct_provider_count": len(providers),
                "distinct_domain_count": len(domains),
                "distinct_mechanism_count": len(mechanisms),
                "rationale": "Synthetic lineage fixture; counts are derived, not a score.",
            },
            "persistence": "EMERGING",
            "trend_state": "ACCELERATING",
            "materiality": "MODERATE",
            "confidence": "MEDIUM",
            "first_detected_at_utc": "2026-01-01T00:00:00Z",
            "state_effective_at_utc": "2026-01-05T00:00:00Z",
            "review_state": review,
            "lifecycle_state": lifecycle,
            "expiry": expiry,
            "rationale": "Synthetic state assessment for contract testing.",
            "alternative_interpretation": "The observations may be correlated rather than a transition.",
            "falsification_conditions": ["Independent evidence ceases and the state is reviewed down."],
            "threshold_basis": {
                "threshold_type": "NONE",
                "description": "No numeric threshold is used.",
                "provenance": "Contract deliberately uses reviewed qualitative criteria.",
            },
            "review_provenance": {
                "created_by": "synthetic-reviewer",
                "created_at_utc": created,
                "reviewed_by": "synthetic-reviewer" if review == "ACCEPTED" else None,
                "reviewed_at_utc": reviewed if review == "ACCEPTED" else None,
                "decision_basis": "Synthetic reviewed fixture" if review == "ACCEPTED" else None,
            },
            "revision_reason": "Synthetic initial or revised assessment.",
        }

    def validate(self, rows, *, signals=None, relationships=None, observations=None, evidence=None):
        return validate_risk_state_history(
            self.schema, rows, signals or self.signals, relationships or self.relationships,
            observations or self.observations, evidence or self.evidence, self.canonical,
        )

    def test_valid_signal_and_relationship_references(self):
        report = self.validate([self.state(signal_ids=("SIG-A",), relationship_ids=("REL-A",))])
        self.assertTrue(report.ok, report.errors)

    def test_regime_state_uses_separate_state_vocabulary(self):
        row = self.state()
        row["state_class"] = "REGIME_STATE"
        row["current_state"] = "TRANSITIONING"
        row["title"] = "Synthetic regime transition"
        report = self.validate([row])
        self.assertTrue(report.ok, report.errors)

    def test_unknown_upstream_reference_is_rejected(self):
        report = self.validate([self.state(signal_ids=("SIG-NOT-FOUND",), supporting_observation_ids=["OBS-A"])])
        self.assertFalse(report.ok)
        self.assertTrue(any("unknown or mismatched Signal" in error for error in report.errors))

    def test_rejected_upstream_cannot_support_active_state(self):
        signals = deepcopy(self.signals)
        signals["signals"][0]["review_state"] = "REJECTED"
        signals["signals"][0]["lifecycle_state"] = "WITHDRAWN"
        report = self.validate([self.state()], signals=signals)
        self.assertFalse(report.ok)
        self.assertTrue(any("cannot support an active state" in error for error in report.errors))

    def test_duplicate_upstream_evidence_does_not_inflate_convergence(self):
        row = self.state(signal_ids=("SIG-A", "SIG-A"))
        report = self.validate([row])
        self.assertFalse(report.ok)
        self.assertTrue(any("duplicate Signal revision pins" in error for error in report.errors))

    def test_shared_provider_does_not_masquerade_as_independence(self):
        row = self.state(signal_ids=("SIG-A", "SIG-B"))
        row["convergence"]["distinct_provider_count"] = 2
        report = self.validate([row])
        self.assertFalse(report.ok)
        self.assertTrue(any("distinct_provider_count" in error for error in report.errors))

    def test_contradictory_evidence_is_preserved_and_not_counted_as_support(self):
        row = self.state(signal_ids=("SIG-A",), contradictory_signal_ids=("SIG-B",))
        report = self.validate([row])
        self.assertTrue(report.ok, report.errors)
        self.assertEqual(row["convergence"]["distinct_signal_count"], 1)

    def test_history_is_immutable_and_predecessor_is_required(self):
        first = self.state()
        second = self.state(
            revision_id="RISK-1-R2", revision_number=2, previous_revision_id="RISK-1-R1",
            previous="ELEVATED", current="EASING", transition="EASING", direction="DOWNWARD",
            created="2026-01-10T00:00:00Z", reviewed="2026-01-10T01:00:00Z",
        )
        report = self.validate([second],)
        self.assertFalse(report.ok)
        self.assertTrue(any("contiguous" in error or "predecessor" in error for error in report.errors))
        report = validate_risk_state_history(
            self.schema, [first, second], self.signals, self.relationships,
            self.observations, self.evidence, self.canonical, previous_revisions=[first],
        )
        self.assertTrue(report.ok, report.errors)
        altered = deepcopy(first)
        altered["rationale"] = "rewritten"
        report = validate_risk_state_history(
            self.schema, [altered, second], self.signals, self.relationships,
            self.observations, self.evidence, self.canonical, previous_revisions=[first],
        )
        self.assertFalse(report.ok)
        self.assertTrue(any("removed or rewritten" in error for error in report.errors))

    def test_invalid_transition_fails(self):
        row = self.state(transition="PERSISTENCE")
        report = self.validate([row])
        self.assertFalse(report.ok)
        self.assertTrue(any("first revision requires" in error for error in report.errors))

        first = self.state()
        invalid = self.state(
            revision_id="RISK-1-R2", revision_number=2, previous_revision_id="RISK-1-R1",
            previous="ELEVATED", current="BASELINE", transition="RETURN_TO_BASELINE",
            direction="DOWNWARD", created="2026-01-10T00:00:00Z", reviewed="2026-01-10T01:00:00Z",
        )
        report = self.validate([first, invalid])
        self.assertFalse(report.ok)
        self.assertTrue(any("invalid RISK_STATE transition" in error for error in report.errors))

    def test_as_of_excludes_future_revision(self):
        first = self.state()
        second = self.state(
            revision_id="RISK-1-R2", revision_number=2, previous_revision_id="RISK-1-R1",
            previous="ELEVATED", current="EASING", transition="EASING", direction="DOWNWARD",
            created="2026-01-10T00:00:00Z", reviewed="2026-01-10T01:00:00Z",
        )
        before = risk_state_as_of(self.schema, [first, second], self.signals, self.relationships, self.observations, self.evidence, self.canonical, "2026-01-06T00:00:00Z")
        after = risk_state_as_of(self.schema, [first, second], self.signals, self.relationships, self.observations, self.evidence, self.canonical, "2026-01-11T00:00:00Z")
        self.assertEqual(before["RISK-1"]["revision_id"], "RISK-1-R1")
        self.assertEqual(after["RISK-1"]["revision_id"], "RISK-1-R2")

    def test_later_observation_cannot_support_earlier_assessment(self):
        observations = deepcopy(self.observations)
        observations["observations"][0]["observed_at_utc"] = "2026-02-01T00:00:00Z"
        report = self.validate([self.state()], observations=observations)
        self.assertFalse(report.ok)
        self.assertTrue(any("later observation" in error for error in report.errors))

    def test_return_to_baseline_preserves_history(self):
        first = self.state()
        second = self.state(
            revision_id="RISK-1-R2", revision_number=2, previous_revision_id="RISK-1-R1",
            previous="ELEVATED", current="EASING", transition="EASING", direction="DOWNWARD",
            created="2026-01-10T00:00:00Z", reviewed="2026-01-10T01:00:00Z",
        )
        third = self.state(
            revision_id="RISK-1-R3", revision_number=3, previous_revision_id="RISK-1-R2",
            previous="EASING", current="BASELINE", transition="RETURN_TO_BASELINE", direction="DOWNWARD",
            created="2026-01-15T00:00:00Z", reviewed="2026-01-15T01:00:00Z",
        )
        report = self.validate([first, second, third])
        self.assertTrue(report.ok, report.errors)
        self.assertEqual(len({first["revision_id"], second["revision_id"], third["revision_id"]}), 3)

    def test_staleness_is_deterministic(self):
        row = self.state()
        self.assertFalse(risk_state_is_stale(row, {x["observation_id"]: x for x in self.observations["observations"]}, "2026-01-30T23:59:59Z"))
        self.assertTrue(risk_state_is_stale(row, {x["observation_id"]: x for x in self.observations["observations"]}, "2026-01-31T00:00:00Z"))

    def test_expiry_modes_are_validated(self):
        row = self.state(expiry={"mode": "EXPLICIT_DATE", "stale_after_days": None, "expires_at_utc": "2026-02-01T00:00:00Z", "review_due_at_utc": None, "condition": "Review by explicit date"})
        self.assertTrue(self.validate([row]).ok)
        row["expiry"]["expires_at_utc"] = None
        self.assertFalse(self.validate([row]).ok)

    def test_threshold_requires_provenance(self):
        row = self.state()
        row["threshold_basis"] = {"threshold_type": "ANALYST_HEURISTIC", "description": "", "provenance": ""}
        report = self.validate([row])
        self.assertFalse(report.ok)
        self.assertTrue(any("threshold_basis requires" in error for error in report.errors))

    def test_numeric_risk_scoring_is_rejected(self):
        row = self.state()
        row["risk_score"] = 72
        report = self.validate([row])
        self.assertFalse(report.ok)
        self.assertTrue(any("forecast/scenario fields" in error or "prohibited" in error for error in report.errors))

    def test_forecast_and_scenario_fields_are_rejected(self):
        row = self.state()
        row["probability"] = 0.65
        row["scenario_id"] = "SCENARIO-1"
        self.assertFalse(self.validate([row]).ok)

    def test_zero_production_population_is_valid(self):
        dataset = json.loads((ROOT / "data/risks/states.json").read_text())
        report = validate_risk_states(self.schema, dataset, self.signals, self.relationships, self.observations, self.evidence, self.canonical)
        self.assertTrue(report.ok, report.errors)

    def test_public_projection_remains_closed(self):
        dataset = json.loads((ROOT / "data/risks/states.json").read_text())
        projection = public_risk_state_projection(self.schema, dataset, self.signals, self.relationships, self.observations, self.evidence, self.canonical)
        self.assertEqual(projection["states"], [])
        self.assertFalse(projection["metadata"]["public_risk_projection_allowed"])

    def test_synthetic_fixture_cannot_leak_into_production(self):
        dataset = json.loads((ROOT / "data/risks/states.json").read_text())
        dataset["states"] = [self.state()]
        report = validate_risk_states(self.schema, dataset, self.signals, self.relationships, self.observations, self.evidence, self.canonical)
        self.assertFalse(report.ok)
        self.assertTrue(any("closed production population gate" in error for error in report.errors))

    def test_current_risk_overlay_remains_unchanged(self):
        registry = json.loads((ROOT / "data/canonical/registry.json").read_text())
        before = json.dumps(public_risk_projection(registry), sort_keys=True, separators=(",", ":"))
        dataset = json.loads((ROOT / "data/risks/states.json").read_text())
        public_risk_state_projection(self.schema, dataset, self.signals, self.relationships, self.observations, self.evidence, self.canonical)
        after = json.dumps(public_risk_projection(registry), sort_keys=True, separators=(",", ":"))
        self.assertEqual(hashlib.sha256(before.encode()).hexdigest(), hashlib.sha256(after.encode()).hexdigest())

    def test_malformed_input_fails_without_exception(self):
        report = validate_risk_state_history(self.schema, [{"state_id": "bad"}], self.signals, self.relationships, self.observations, self.evidence, self.canonical)
        self.assertFalse(report.ok)


if __name__ == "__main__":
    unittest.main()
