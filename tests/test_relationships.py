from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.relationships import (
    public_relationship_projection,
    relationship_graph_edges_as_of,
    relationship_state_as_of,
    validate_relationship_history,
    validate_relationships,
)


class RelationshipContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / "data/relationships/schema.json").read_text())
        cls.signals_schema = json.loads((ROOT / "data/signals/schema.json").read_text())
        cls.production_signals = json.loads((ROOT / "data/signals/signals.json").read_text())
        cls.canonical = {"records": [{"occurrence_id": "CANON-1"}]}

    def upstream(self, *, include_c=False):
        signals = {
            "version": "0.1",
            "population_state": "CLOSED_NO_PRODUCTION_SIGNALS",
            "signals": [
                self.signal("SIG-A", "OBS-A", "E-A"),
                self.signal("SIG-B", "OBS-B", "E-B"),
            ],
        }
        observations = {
            "observations": [
                {"observation_id": "OBS-A", "observed_at_utc": "2026-09-01T00:00:00Z", "verification_state": "PRIMARY_CONFIRMED", "evidence_refs": ["E-A"]},
                {"observation_id": "OBS-B", "observed_at_utc": "2026-09-02T00:00:00Z", "verification_state": "PRIMARY_CONFIRMED", "evidence_refs": ["E-B"]},
            ]
        }
        evidence = {
            "evidence": [
                {"evidence_id": "E-A", "evidence_class": "PRIMARY_OFFICIAL", "provider": "Authority A", "publication_time": {"precision": "CIVIL_DATE", "published_date": "2026-09-01"}},
                {"evidence_id": "E-B", "evidence_class": "ACADEMIC_OR_INSTITUTIONAL", "provider": "Institution B", "publication_time": {"precision": "CIVIL_DATE", "published_date": "2026-09-02"}},
            ]
        }
        if include_c:
            signals["signals"].append(self.signal("SIG-C", "OBS-C", "E-C"))
            observations["observations"].append({"observation_id": "OBS-C", "observed_at_utc": "2026-09-03T00:00:00Z", "verification_state": "PRIMARY_CONFIRMED", "evidence_refs": ["E-C"]})
            evidence["evidence"].append({"evidence_id": "E-C", "evidence_class": "REPUTABLE_NEWSWIRE", "provider": "Authority C", "publication_time": {"precision": "CIVIL_DATE", "published_date": "2026-09-03"}})
        return signals, observations, evidence

    @staticmethod
    def signal(signal_id, observation_id, evidence_id, *, review_state="ACCEPTED", lifecycle_state="ACTIVE"):
        return {
            "signal_id": signal_id,
            "revision_id": f"{signal_id}-R1",
            "revision_number": 1,
            "review_state": review_state,
            "lifecycle_state": lifecycle_state,
            "observation_ids": [observation_id],
            "evidence_refs": [evidence_id],
            "review_provenance": {
                "created_by": "synthetic-signal-review",
                "created_at_utc": "2026-09-03T00:00:00Z",
                "reviewed_by": "synthetic-signal-reviewer" if review_state == "ACCEPTED" else None,
                "reviewed_at_utc": "2026-09-03T01:00:00Z" if review_state == "ACCEPTED" else None,
                "decision_basis": "Synthetic reviewed Signal fixture." if review_state == "ACCEPTED" else None,
            },
        }

    def relationship(self, **overrides):
        row = {
            "relationship_id": "REL-1",
            "revision_id": "REL-1-R1",
            "revision_number": 1,
            "previous_revision_id": None,
            "title": "Synthetic transmission relationship",
            "source_nodes": [{"node_id": "SIG-A", "node_type": "SIGNAL"}],
            "target_nodes": [{"node_id": "SIG-B", "node_type": "SIGNAL"}],
            "supporting_signal_revisions": [
                {"signal_id": "SIG-A", "revision_id": "SIG-A-R1"},
                {"signal_id": "SIG-B", "revision_id": "SIG-B-R1"},
            ],
            "supporting_observation_ids": ["OBS-A", "OBS-B"],
            "supporting_evidence_refs": ["E-A", "E-B"],
            "contradictory_evidence_refs": [],
            "contextual_canonical_occurrence_ids": ["CANON-1"],
            "relationship_class": "HYPOTHESISED_TRANSMISSION",
            "directionality": "DIRECTED",
            "directionality_rationale": "The proposed pathway is directional but not established as causal.",
            "domains": ["ENERGY", "LOGISTICS"],
            "jurisdictions": ["Synthetic jurisdiction"],
            "rationale": "Synthetic contract rationale preserves the analytical distinction between pathway and proof.",
            "mechanism": "",
            "alternative_explanations": ["A common external driver could explain both Signals."],
            "confounders": ["Synthetic global conditions may affect both nodes."],
            "common_driver_signal_ids": [],
            "causal_basis": [],
            "confidence": "MEDIUM",
            "temporal_scope": {
                "scope_type": "OBSERVED_PERIOD",
                "start_at_utc": "2026-09-01T00:00:00Z",
                "end_at_utc": "2026-09-03T00:00:00Z",
                "notes": "Observed synthetic period; not a forecast horizon.",
            },
            "first_asserted_at_utc": "2026-09-04T00:00:00Z",
            "review_state": "UNDER_REVIEW",
            "lifecycle_state": "UNRESOLVED",
            "falsification_conditions": ["Independent evidence attributes the change to another mechanism."],
            "review_provenance": {
                "created_by": "synthetic-relationship-review",
                "created_at_utc": "2026-09-04T00:00:00Z",
                "reviewed_by": None,
                "reviewed_at_utc": None,
                "decision_basis": None,
            },
            "revision_reason": "Initial synthetic relationship fixture.",
        }
        row.update(overrides)
        return row

    @staticmethod
    def dataset(rows):
        return {"version": "0.1", "population_state": "CLOSED_NO_PRODUCTION_RELATIONSHIPS", "relationships": rows}

    def validate(self, rows, *, signals=None, observations=None, evidence=None, canonical=None, previous=None):
        defaults = self.upstream()
        signals = defaults[0] if signals is None else signals
        observations = defaults[1] if observations is None else observations
        evidence = defaults[2] if evidence is None else evidence
        canonical = canonical or self.canonical
        return validate_relationship_history(self.schema, rows, signals, observations, evidence, canonical, previous_revisions=previous)

    def accepted(self, **overrides):
        row = self.relationship(
            review_state="ACCEPTED",
            lifecycle_state="ACTIVE",
            review_provenance={
                "created_by": "synthetic-relationship-review",
                "created_at_utc": "2026-09-04T00:00:00Z",
                "reviewed_by": "synthetic-relationship-reviewer",
                "reviewed_at_utc": "2026-09-04T01:00:00Z",
                "decision_basis": "Reviewed synthetic alternatives and evidence.",
            },
        )
        row.update(overrides)
        return row

    def test_zero_production_relationships_is_valid(self):
        signals, observations, evidence = self.upstream()
        report = validate_relationships(self.schema, self.dataset([]), signals, observations, evidence, self.canonical)
        self.assertTrue(report.ok, report.errors)
        projection = public_relationship_projection(self.schema, self.dataset([]), signals, observations, evidence, self.canonical)
        self.assertEqual(projection["metadata"]["public_relationship_count"], 0)
        self.assertEqual(projection["relationships"], [])

    def test_valid_signal_references_are_accepted(self):
        self.assertTrue(self.validate([self.relationship()]).ok)

    def test_unknown_signal_reference_is_rejected(self):
        row = self.relationship(source_nodes=[{"node_id": "SIG-NOT-REAL", "node_type": "SIGNAL"}])
        self.assertIn("unknown Signal reference", " ".join(self.validate([row]).errors))

    def test_rejected_signal_cannot_masquerade_as_active_node(self):
        signals, observations, evidence = self.upstream()
        signals["signals"][1] = self.signal("SIG-B", "OBS-B", "E-B", review_state="REJECTED", lifecycle_state="WITHDRAWN")
        self.assertIn("cannot masquerade", " ".join(self.validate([self.accepted()], signals=signals, observations=observations, evidence=evidence).errors))

    def test_duplicate_signal_refs_do_not_inflate_support(self):
        row = self.relationship(supporting_signal_revisions=[
            {"signal_id": "SIG-A", "revision_id": "SIG-A-R1"},
            {"signal_id": "SIG-A", "revision_id": "SIG-A-R1"},
            {"signal_id": "SIG-B", "revision_id": "SIG-B-R1"},
        ])
        self.assertIn("duplicate Signal revision pins", " ".join(self.validate([row]).errors))

    def test_association_does_not_masquerade_as_causal(self):
        row = self.relationship(relationship_class="ASSOCIATION", mechanism="", causal_basis=[])
        self.assertTrue(self.validate([row]).ok)
        causal = self.relationship(relationship_class="CAUSAL_EVIDENCE", mechanism="", causal_basis=[])
        self.assertFalse(self.validate([causal]).ok)

    def test_strong_class_requires_explicit_reviewed_evidentiary_basis(self):
        row = self.accepted(relationship_class="MECHANISTICALLY_SUPPORTED", mechanism="", causal_basis=[])
        self.assertFalse(self.validate([row]).ok)
        row = self.accepted(
            relationship_class="MECHANISTICALLY_SUPPORTED",
            mechanism="A reviewed physical mechanism is described here.",
            causal_basis=["ESTABLISHED_PHYSICAL_MECHANISM"],
        )
        self.assertTrue(self.validate([row]).ok, self.validate([row]).errors)

    def test_contradictory_evidence_is_preserved(self):
        signals, observations, evidence = self.upstream(include_c=True)
        row = self.relationship(
            supporting_observation_ids=["OBS-A", "OBS-B", "OBS-C"],
            supporting_evidence_refs=["E-A", "E-B"],
            contradictory_evidence_refs=["E-C"],
        )
        self.assertTrue(self.validate([row], signals=signals, observations=observations, evidence=evidence).ok)

    def test_alternatives_are_required_for_inference_but_representable(self):
        row = self.relationship(alternative_explanations=[])
        self.assertIn("alternative explanations", " ".join(self.validate([row]).errors))
        row["alternative_explanations"] = ["Independent common driver remains plausible."]
        self.assertTrue(self.validate([row]).ok)

    def test_common_driver_and_confounder_semantics_are_explicit(self):
        row = self.relationship(
            relationship_class="COMMON_DRIVER",
            directionality="UNDIRECTED",
            directionality_rationale="No direction is established.",
            common_driver_signal_ids=["SIG-A"],
            confounders=["A shared policy environment may drive both nodes."],
        )
        self.assertTrue(self.validate([row]).ok, self.validate([row]).errors)

    def test_revisions_preserve_historical_states(self):
        first = self.accepted()
        second = deepcopy(first)
        second.update(revision_id="REL-1-R2", revision_number=2, previous_revision_id="REL-1-R1", lifecycle_state="WEAKENING", revision_reason="Contradictory evidence weakens the relationship.")
        second["review_provenance"] = {
            "created_by": "synthetic-relationship-review",
            "created_at_utc": "2026-09-05T00:00:00Z",
            "reviewed_by": "synthetic-relationship-reviewer",
            "reviewed_at_utc": "2026-09-05T01:00:00Z",
            "decision_basis": "Reviewed weakening evidence.",
        }
        report = self.validate([first, second], previous=[first])
        self.assertTrue(report.ok, report.errors)
        self.assertEqual(relationship_state_as_of(self.schema, [first, second], *self.upstream(), self.canonical, "2026-09-04T12:00:00Z")["REL-1"]["revision_id"], "REL-1-R1")
        self.assertEqual(relationship_state_as_of(self.schema, [first, second], *self.upstream(), self.canonical, "2026-09-06T00:00:00Z")["REL-1"]["revision_id"], "REL-1-R2")

    def test_directionality_is_explicit(self):
        row = self.relationship(directionality_rationale="")
        self.assertFalse(self.validate([row]).ok)
        row = self.relationship(relationship_class="HYPOTHESISED_TRANSMISSION", directionality="UNDIRECTED")
        self.assertFalse(self.validate([row]).ok)

    def test_non_directional_relationship_remains_non_directional(self):
        row = self.relationship(relationship_class="CO_OCCURRENCE", directionality="UNDIRECTED", directionality_rationale="Co-occurrence only; no direction is asserted.", alternative_explanations=[])
        self.assertTrue(self.validate([row]).ok, self.validate([row]).errors)
        row["directionality"] = "DIRECTED"
        self.assertIn("CO_OCCURRENCE must remain", " ".join(self.validate([row]).errors))

    def test_direction_reversal_requires_a_new_reviewed_revision(self):
        first = self.accepted()
        altered = deepcopy(first)
        altered["directionality"] = "UNDIRECTED"
        altered["revision_reason"] = "Illicit in-place reversal."
        self.assertIn("retained Relationship revision was removed or rewritten", " ".join(self.validate([altered], previous=[first]).errors))

    def test_graph_does_not_create_transitive_edges(self):
        signals, observations, evidence = self.upstream(include_c=True)
        first = self.accepted()
        second = self.accepted(
            relationship_id="REL-2", revision_id="REL-2-R1", title="B to C",
            source_nodes=[{"node_id": "SIG-B", "node_type": "SIGNAL"}],
            target_nodes=[{"node_id": "SIG-C", "node_type": "SIGNAL"}],
            supporting_signal_revisions=[
                {"signal_id": "SIG-B", "revision_id": "SIG-B-R1"},
                {"signal_id": "SIG-C", "revision_id": "SIG-C-R1"},
            ],
            supporting_observation_ids=["OBS-B", "OBS-C"], supporting_evidence_refs=["E-B", "E-C"],
        )
        edges = relationship_graph_edges_as_of(self.schema, [first, second], signals, observations, evidence, self.canonical, "2026-09-06T00:00:00Z")
        self.assertEqual({edge["relationship_id"] for edge in edges}, {"REL-1", "REL-2"})
        self.assertFalse(any({node["node_id"] for node in edge["source_nodes"]} == {"SIG-A"} and {node["node_id"] for node in edge["target_nodes"]} == {"SIG-C"} for edge in edges))

    def test_explicit_feedback_cycle_is_valid(self):
        signals, observations, evidence = self.upstream()
        first = self.accepted(relationship_class="FEEDBACK_LOOP", directionality="RECIPROCAL", directionality_rationale="Both directions are explicitly reviewed.")
        self.assertTrue(self.validate([first], signals=signals, observations=observations, evidence=evidence).ok)

    def test_forecast_or_scenario_fields_are_rejected(self):
        row = self.relationship()
        row["probability"] = 0.7
        self.assertIn("forecast/scenario fields", " ".join(self.validate([row]).errors))

    def test_synthetic_fixture_cannot_open_production_gate(self):
        signals, observations, evidence = self.upstream()
        row = self.relationship()
        self.assertTrue(self.validate([row]).ok)
        report = validate_relationships(self.schema, self.dataset([row]), signals, observations, evidence, self.canonical)
        self.assertIn("closed production population gate", " ".join(report.errors))
        with self.assertRaises(ValueError):
            public_relationship_projection(self.schema, self.dataset([row]), signals, observations, evidence, self.canonical)

    def test_as_of_history_does_not_use_later_evidence_retroactively(self):
        signals, observations, evidence = self.upstream()
        observations["observations"][1]["observed_at_utc"] = "2026-09-10T00:00:00Z"
        row = self.relationship()
        self.assertIn("later observation", " ".join(self.validate([row], signals=signals, observations=observations, evidence=evidence).errors))

    def test_malformed_inputs_fail_without_exceptions(self):
        row = self.relationship(source_nodes=[None], temporal_scope=None)
        report = self.validate([row])
        self.assertIsInstance(report.ok, bool)

    def test_public_projection_is_closed_even_with_policy_fixture_flag(self):
        schema = deepcopy(self.schema)
        schema["population_policy"]["production_population_allowed"] = True
        signals, observations, evidence = self.upstream()
        with self.assertRaises(ValueError):
            public_relationship_projection(schema, self.dataset([]), signals, observations, evidence, self.canonical)


if __name__ == "__main__":
    unittest.main()
