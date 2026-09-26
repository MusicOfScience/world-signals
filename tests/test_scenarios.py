import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.risk_projection import public_risk_projection
from world_signals.scenarios import (
    public_scenario_projection,
    scenario_state_as_of,
    validate_scenario_history,
    validate_scenarios,
)


class ScenarioContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / "data/scenarios/schema.json").read_text())
        cls.dataset = json.loads((ROOT / "data/scenarios/scenarios.json").read_text())
        cls.canonical = {"records": []}
        cls.observations = {
            "observations": [
                {"observation_id": "OBS-A", "observed_at_utc": "2026-01-01T00:00:00Z", "evidence_refs": ["E-A"]},
                {"observation_id": "OBS-B", "observed_at_utc": "2026-01-02T00:00:00Z", "evidence_refs": ["E-B"]},
            ]
        }
        cls.evidence = {
            "evidence": [
                {"evidence_id": "E-A", "provider": "Provider One", "publication_time": {"published_date": "2026-01-01"}},
                {"evidence_id": "E-B", "provider": "Provider Two", "publication_time": {"published_date": "2026-01-02"}},
            ]
        }
        cls.risks = {"states": [cls.upstream("RISK-1", "RISK-1-R1", "ACTIVE")]}
        cls.signals = {"signals": [cls.upstream("SIG-A", "SIG-A-R1", "ACTIVE")]}
        cls.relationships = {"relationships": [cls.upstream("REL-A", "REL-A-R1", "ACTIVE")]}

    @staticmethod
    def upstream(object_id, revision_id, lifecycle, *, review="ACCEPTED"):
        return {
            "state_id": object_id if object_id.startswith("RISK") else None,
            "signal_id": object_id if object_id.startswith("SIG") else None,
            "relationship_id": object_id if object_id.startswith("REL") else None,
            "revision_id": revision_id,
            "review_state": review,
            "lifecycle_state": lifecycle,
            "review_provenance": {
                "created_by": "synthetic-reviewer",
                "created_at_utc": "2026-01-04T00:00:00Z",
                "reviewed_by": "synthetic-reviewer" if review == "ACCEPTED" else None,
                "reviewed_at_utc": "2026-01-04T01:00:00Z" if review == "ACCEPTED" else None,
                "decision_basis": "synthetic reviewed upstream" if review == "ACCEPTED" else None,
            },
        }

    @staticmethod
    def scope():
        return {
            "system_domain": "shipping-energy exposure",
            "jurisdictions": ["Synthetic region"],
            "description": "Synthetic contract scope.",
        }

    @staticmethod
    def temporal_scope():
        return {
            "scope_type": "OPEN_ENDED",
            "start_at_utc": "2026-01-06T00:00:00Z",
            "end_at_utc": None,
            "description": "Conditional pathway scope begins at review time.",
        }

    @staticmethod
    def assumption(assumption_id, statement):
        return {
            "assumption_id": assumption_id,
            "category": "STRUCTURAL",
            "statement": statement,
            "rationale": "Synthetic assumption rationale.",
            "provenance": "Analyst review of the defined contract fixture.",
            "basis_observation_ids": ["OBS-A"],
            "basis_evidence_refs": ["E-A"],
        }

    @staticmethod
    def signpost(signpost_id, effect="DISCRIMINATING"):
        return {
            "signpost_id": signpost_id,
            "description": "A future observable development changes pathway compatibility.",
            "observable_evidence_class": "policy or operational change",
            "compatibility_effect": effect,
            "assessment_rule": "Review against a governed observation or signal; do not count headlines.",
            "resolution_notes": "Assessment remains a later reviewed action, not an automatic score.",
        }

    @classmethod
    def scenario_set(cls, *, revision_id="SET-1-R1", revision_number=1, previous_revision_id=None, scenario_ids=None, created="2026-01-05T00:00:00Z", first_created=None, effective="2026-01-05T00:00:00Z", reviewed_at=None, lifecycle="ACTIVE", review="ACCEPTED"):
        reviewed_at = reviewed_at or ("2026-01-05T01:00:00Z" if revision_number == 1 else "2026-01-10T01:00:00Z")
        return {
            "scenario_set_id": "SET-1",
            "revision_id": revision_id,
            "revision_number": revision_number,
            "previous_revision_id": previous_revision_id,
            "title": "Synthetic competing pathways",
            "scope": cls.scope(),
            "starting_risk_state_revisions": [{"state_id": "RISK-1", "revision_id": "RISK-1-R1"}],
            "shared_assumptions": [cls.assumption("SHARED-1", "The defined starting conditions remain the relevant context.")],
            "divergence_points": [{
                "divergence_point_id": "DIV-1",
                "description": "Operational continuity separates from disruption.",
                "observable_trigger": "A governed operational observation changes pathway compatibility.",
                "scenario_ids": scenario_ids or ["SCEN-A", "SCEN-B"],
            }],
            "scenario_ids": scenario_ids or ["SCEN-A", "SCEN-B"],
            "temporal_scope": cls.temporal_scope(),
            "review_state": review,
            "lifecycle_state": lifecycle,
            "first_created_at_utc": first_created or created,
            "effective_at_utc": effective,
            "latest_reviewed_at_utc": reviewed_at if review == "ACCEPTED" else None,
            "review_provenance": {
                "created_by": "synthetic-reviewer",
                "created_at_utc": created,
                "reviewed_by": "synthetic-reviewer" if review == "ACCEPTED" else None,
                "reviewed_at_utc": reviewed_at if review == "ACCEPTED" else None,
                "decision_basis": "Synthetic competing-set review" if review == "ACCEPTED" else None,
            },
            "revision_reason": "Synthetic initial or revised Scenario Set.",
        }

    @classmethod
    def scenario(cls, scenario_id="SCEN-A", *, revision_id=None, revision_number=1, previous_revision_id=None, set_revision_id="SET-1-R1", created="2026-01-06T00:00:00Z", first_created=None, effective="2026-01-06T00:00:00Z", reviewed_at=None, lifecycle="ACTIVE", review="ACCEPTED", competitor="SCEN-B"):
        reviewed_at = reviewed_at or ("2026-01-06T01:00:00Z" if revision_number == 1 else "2026-01-10T01:00:00Z")
        revision_id = revision_id or f"{scenario_id}-R{revision_number}"
        return {
            "scenario_id": scenario_id,
            "scenario_set_id": "SET-1",
            "scenario_set_revision_id": set_revision_id,
            "revision_id": revision_id,
            "revision_number": revision_number,
            "previous_revision_id": previous_revision_id,
            "title": "Continuity pathway" if scenario_id == "SCEN-A" else "Disruption pathway",
            "description": "A conditional pathway with explicit assumptions and branch conditions.",
            "scope": cls.scope(),
            "originating_risk_state_revisions": [{"state_id": "RISK-1", "revision_id": "RISK-1-R1"}],
            "relevant_signal_revisions": [{"signal_id": "SIG-A", "revision_id": "SIG-A-R1"}],
            "relevant_relationship_revisions": [{"relationship_id": "REL-A", "revision_id": "REL-A-R1"}],
            "supporting_observation_ids": ["OBS-A"],
            "supporting_evidence_refs": ["E-A"],
            "shared_assumption_ids": ["SHARED-1"],
            "assumptions": [cls.assumption(f"{scenario_id}-LOCAL-1", "The pathway-specific condition remains unresolved and must be watched.")],
            "enabling_conditions": ["The defined branch condition is observed and reviewed."],
            "inhibiting_conditions": ["The competing branch condition becomes more compatible."],
            "transmission_pathways": [{
                "pathway_id": f"{scenario_id}-PATH-1",
                "from_node": "shipping disruption",
                "to_node": "energy exposure",
                "relationship_revision_ids": ["REL-A-R1"],
                "epistemic_status": "HYPOTHESISED_TRANSMISSION",
                "rationale": "The pathway is carried as a reviewed hypothesis, not asserted causation.",
            }],
            "signposts": [cls.signpost(f"{scenario_id}-SP-1")],
            "disconfirming_signposts": [cls.signpost(f"{scenario_id}-DSP-1", "LESS_COMPATIBLE")],
            "falsification_conditions": ["A reviewed observation materially contradicts the pathway-specific condition."],
            "competing_scenario_ids": [competitor],
            "divergence_point_ids": ["DIV-1"],
            "uncertainty_notes": "The branch conditions and transmission remain conditional.",
            "temporal_scope": cls.temporal_scope(),
            "review_state": review,
            "lifecycle_state": lifecycle,
            "first_created_at_utc": first_created or created,
            "effective_at_utc": effective,
            "latest_reviewed_at_utc": reviewed_at if review == "ACCEPTED" else None,
            "review_provenance": {
                "created_by": "synthetic-reviewer",
                "created_at_utc": created,
                "reviewed_by": "synthetic-reviewer" if review == "ACCEPTED" else None,
                "reviewed_at_utc": reviewed_at if review == "ACCEPTED" else None,
                "decision_basis": "Synthetic scenario review" if review == "ACCEPTED" else None,
            },
            "rationale": "Synthetic scenario for contract testing only.",
            "revision_reason": "Synthetic initial or revised Scenario.",
        }

    def validate(self, sets, scenarios, *, risks=None, signals=None, relationships=None, observations=None, evidence=None, previous_set_revisions=None, previous_scenario_revisions=None):
        return validate_scenario_history(
            self.schema, sets, scenarios, risks or self.risks, signals or self.signals,
            relationships or self.relationships, observations or self.observations,
            evidence or self.evidence, self.canonical,
            previous_set_revisions=previous_set_revisions,
            previous_scenario_revisions=previous_scenario_revisions,
        )

    def test_valid_upstream_references(self):
        report = self.validate([self.scenario_set()], [self.scenario(), self.scenario("SCEN-B", competitor="SCEN-A")])
        self.assertTrue(report.ok, report.errors)

    def test_risk_signal_and_relationship_references_are_each_required_context(self):
        for field in ("originating_risk_state_revisions", "relevant_signal_revisions", "relevant_relationship_revisions"):
            row = self.scenario()
            row[field] = []
            if field == "relevant_relationship_revisions":
                row["transmission_pathways"] = []
            report = self.validate([self.scenario_set()], [row, self.scenario("SCEN-B", competitor="SCEN-A")])
            if field == "originating_risk_state_revisions":
                self.assertTrue(any("at least one Risk/Regime" in error for error in report.errors))
            else:
                self.assertTrue(report.ok, (field, report.errors))

    def test_rejected_signal_cannot_support_active_scenario(self):
        signals = copy.deepcopy(self.signals)
        signals["signals"][0]["review_state"] = "REJECTED"
        signals["signals"][0]["lifecycle_state"] = "WITHDRAWN"
        report = self.validate([self.scenario_set()], [self.scenario(), self.scenario("SCEN-B", competitor="SCEN-A")], signals=signals)
        self.assertFalse(report.ok)
        self.assertTrue(any("unaccepted upstream" in error or "withdrawn upstream" in error for error in report.errors))

    def test_duplicate_upstream_revision_does_not_inflate_support(self):
        row = self.scenario()
        row["relevant_signal_revisions"].append({"signal_id": "SIG-A", "revision_id": "SIG-A-R1"})
        report = self.validate([self.scenario_set()], [row, self.scenario("SCEN-B", competitor="SCEN-A")])
        self.assertFalse(report.ok)
        self.assertTrue(any("duplicate relevant_signal_revisions" in error for error in report.errors))

    def test_unknown_upstream_reference_rejected(self):
        row = self.scenario()
        row["originating_risk_state_revisions"][0]["revision_id"] = "RISK-NOT-FOUND"
        self.assertFalse(self.validate([self.scenario_set()], [row, self.scenario("SCEN-B", competitor="SCEN-A")]).ok)

    def test_withdrawn_upstream_cannot_support_active_scenario(self):
        risks = copy.deepcopy(self.risks)
        risks["states"][0]["lifecycle_state"] = "WITHDRAWN"
        report = self.validate([self.scenario_set()], [self.scenario(), self.scenario("SCEN-B", competitor="SCEN-A")], risks=risks)
        self.assertFalse(report.ok)
        self.assertTrue(any("withdrawn upstream" in error for error in report.errors))

    def test_assumptions_are_explicit_and_distinct_from_facts(self):
        row = self.scenario()
        row["assumptions"] = [{"statement": "hidden"}]
        report = self.validate([self.scenario_set()], [row, self.scenario("SCEN-B", competitor="SCEN-A")])
        self.assertFalse(report.ok)
        self.assertTrue(any("distinguish explicit assumptions" in error for error in report.errors))

    def test_competing_scenarios_share_starting_conditions(self):
        report = self.validate([self.scenario_set()], [self.scenario(), self.scenario("SCEN-B", competitor="SCEN-A")])
        self.assertTrue(report.ok, report.errors)

    def test_divergence_points_are_explicit(self):
        scenario_set = self.scenario_set()
        scenario_set["divergence_points"] = []
        self.assertFalse(self.validate([scenario_set], [self.scenario(), self.scenario("SCEN-B", competitor="SCEN-A")]).ok)

    def test_scenario_membership_and_shared_assumptions_are_checked(self):
        scenario_set = self.scenario_set()
        scenario_set["scenario_ids"] = ["SCEN-A", "SCEN-A"]
        report = self.validate([scenario_set], [self.scenario(), self.scenario("SCEN-B", competitor="SCEN-A")])
        self.assertFalse(report.ok)
        scenario_set = self.scenario_set(scenario_ids=["SCEN-A", "SCEN-B", "SCEN-C"])
        report = self.validate([scenario_set], [self.scenario(), self.scenario("SCEN-B", competitor="SCEN-A")])
        self.assertFalse(report.ok)
        row = self.scenario()
        row["shared_assumption_ids"] = ["SHARED-NOT-FOUND"]
        report = self.validate([self.scenario_set()], [row, self.scenario("SCEN-B", competitor="SCEN-A")])
        self.assertFalse(report.ok)

    def test_lifecycle_review_gate_is_explicit(self):
        row = self.scenario(review="CANDIDATE", lifecycle="ACTIVE")
        report = self.validate([self.scenario_set()], [row, self.scenario("SCEN-B", competitor="SCEN-A")])
        self.assertFalse(report.ok)
        rejected = self.scenario(review="REJECTED", lifecycle="ACTIVE")
        report = self.validate([self.scenario_set()], [rejected, self.scenario("SCEN-B", competitor="SCEN-A")])
        self.assertFalse(report.ok)

    def test_signposts_are_not_forecasts(self):
        report = self.validate([self.scenario_set()], [self.scenario(), self.scenario("SCEN-B", competitor="SCEN-A")])
        self.assertTrue(report.ok, report.errors)
        row = self.scenario()
        row["signposts"][0]["forecast_horizon"] = "14 days"
        self.assertFalse(self.validate([self.scenario_set()], [row, self.scenario("SCEN-B", competitor="SCEN-A")]).ok)

    def test_disconfirming_signposts_are_preserved(self):
        row = self.scenario()
        row["disconfirming_signposts"][0]["compatibility_effect"] = "MORE_COMPATIBLE"
        report = self.validate([self.scenario_set()], [row, self.scenario("SCEN-B", competitor="SCEN-A")])
        self.assertFalse(report.ok)
        self.assertTrue(any("disconfirming signposts" in error for error in report.errors))

    def test_history_is_immutable_and_revision_chain_contiguous(self):
        first = self.scenario()
        second = self.scenario(revision_id="SCEN-A-R3", revision_number=3, previous_revision_id="SCEN-A-R1", created="2026-01-10T00:00:00Z", first_created="2026-01-06T00:00:00Z", effective="2026-01-10T00:00:00Z")
        report = self.validate([self.scenario_set()], [first, second, self.scenario("SCEN-B", competitor="SCEN-A")])
        self.assertFalse(report.ok)
        self.assertTrue(any("contiguous" in error for error in report.errors))

    def test_history_accepts_valid_revision_and_retains_previous_snapshot(self):
        first = self.scenario()
        second = self.scenario(revision_id="SCEN-A-R2", revision_number=2, previous_revision_id="SCEN-A-R1", created="2026-01-10T00:00:00Z", first_created="2026-01-06T00:00:00Z", effective="2026-01-10T00:00:00Z")
        other = self.scenario("SCEN-B", competitor="SCEN-A")
        # A Scenario revision preserves its own history, while the member
        # snapshot pin may remain unchanged when the Set itself is unchanged.
        report = self.validate([self.scenario_set()], [first, second, other])
        self.assertTrue(report.ok, report.errors)
        set_second = self.scenario_set(revision_id="SET-1-R2", revision_number=2, previous_revision_id="SET-1-R1", created="2026-01-09T00:00:00Z", first_created="2026-01-05T00:00:00Z", effective="2026-01-09T00:00:00Z")
        second["scenario_set_revision_id"] = "SET-1-R2"
        report = self.validate([self.scenario_set(), set_second], [first, second, other])
        self.assertTrue(report.ok, report.errors)
        altered = copy.deepcopy(first)
        altered["rationale"] = "rewritten"
        report = self.validate([self.scenario_set(), set_second], [altered, second, other], previous_scenario_revisions=[first])
        self.assertFalse(report.ok)

    def test_as_of_excludes_future_revision_and_evidence(self):
        first = self.scenario()
        set_first = self.scenario_set()
        set_second = self.scenario_set(revision_id="SET-1-R2", revision_number=2, previous_revision_id="SET-1-R1", created="2026-01-10T00:00:00Z", first_created="2026-01-05T00:00:00Z", effective="2026-01-10T00:00:00Z")
        second = self.scenario(revision_id="SCEN-A-R2", revision_number=2, previous_revision_id="SCEN-A-R1", set_revision_id="SET-1-R2", created="2026-01-10T00:00:00Z", first_created="2026-01-06T00:00:00Z", effective="2026-01-10T00:00:00Z")
        other = self.scenario("SCEN-B", competitor="SCEN-A")
        before = scenario_state_as_of(self.schema, [set_first, set_second], [first, second, other], self.risks, self.signals, self.relationships, self.observations, self.evidence, self.canonical, "2026-01-07T00:00:00Z")
        after = scenario_state_as_of(self.schema, [set_first, set_second], [first, second, other], self.risks, self.signals, self.relationships, self.observations, self.evidence, self.canonical, "2026-01-11T00:00:00Z")
        self.assertEqual(before["SCEN-A"]["revision_id"], "SCEN-A-R1")
        self.assertEqual(after["SCEN-A"]["revision_id"], "SCEN-A-R2")
        late = copy.deepcopy(second)
        late["supporting_observation_ids"] = ["OBS-B"]
        late["supporting_evidence_refs"] = ["E-B"]
        late["first_created_at_utc"] = "2026-01-01T00:00:00Z"
        late["effective_at_utc"] = "2026-01-01T00:00:00Z"
        self.assertFalse(self.validate([set_first, set_second], [first, late, other]).ok)

    def test_later_upstream_revision_cannot_support_earlier_scenario(self):
        signals = copy.deepcopy(self.signals)
        signals["signals"][0]["review_provenance"]["created_at_utc"] = "2026-02-01T00:00:00Z"
        report = self.validate([self.scenario_set()], [self.scenario(), self.scenario("SCEN-B", competitor="SCEN-A")], signals=signals)
        self.assertFalse(report.ok)
        self.assertTrue(any("later upstream revision" in error for error in report.errors))

    def test_falsified_and_retired_remain_distinct(self):
        falsified = self.scenario(lifecycle="FALSIFIED")
        retired = self.scenario("SCEN-B", competitor="SCEN-A", lifecycle="RETIRED")
        report = self.validate([self.scenario_set()], [falsified, retired])
        self.assertTrue(report.ok, report.errors)
        self.assertNotEqual(falsified["lifecycle_state"], retired["lifecycle_state"])

    def test_probability_target_and_winner_fields_are_rejected(self):
        for field, value in (("probability", 0.6), ("target_value", 120), ("winner", "SCEN-A")):
            row = self.scenario()
            row[field] = value
            self.assertFalse(self.validate([self.scenario_set()], [row, self.scenario("SCEN-B", competitor="SCEN-A")]).ok, field)

    def test_competitors_do_not_create_an_implicit_ranking(self):
        row = self.scenario()
        row["competing_scenario_ids"] = ["SCEN-B"]
        report = self.validate([self.scenario_set()], [row, self.scenario("SCEN-B", competitor="SCEN-A")])
        self.assertTrue(report.ok, report.errors)
        row["competing_scenario_ids"] = ["SCEN-B", "SCEN-C"]
        self.assertFalse(self.validate([self.scenario_set()], [row, self.scenario("SCEN-B", competitor="SCEN-A")]).ok)

    def test_zero_production_population_is_valid(self):
        report = validate_scenarios(self.schema, self.dataset, self.risks, self.signals, self.relationships, self.observations, self.evidence, self.canonical)
        self.assertTrue(report.ok, report.errors)

    def test_synthetic_fixture_cannot_enter_production(self):
        dataset = copy.deepcopy(self.dataset)
        dataset["scenario_sets"] = [self.scenario_set()]
        dataset["scenarios"] = [self.scenario(), self.scenario("SCEN-B", competitor="SCEN-A")]
        report = validate_scenarios(self.schema, dataset, self.risks, self.signals, self.relationships, self.observations, self.evidence, self.canonical)
        self.assertFalse(report.ok)
        self.assertTrue(any("closed production population gate" in error for error in report.errors))

    def test_public_projection_remains_closed(self):
        projection = public_scenario_projection(self.schema, self.dataset, self.risks, self.signals, self.relationships, self.observations, self.evidence, self.canonical)
        self.assertEqual(projection["scenarios"], [])
        self.assertFalse(projection["metadata"]["public_scenario_projection_allowed"])

    def test_existing_risk_overlay_is_unchanged(self):
        registry = json.loads((ROOT / "data/canonical/registry.json").read_text())
        before = json.dumps(public_risk_projection(registry), sort_keys=True, separators=(",", ":"))
        public_scenario_projection(self.schema, self.dataset, self.risks, self.signals, self.relationships, self.observations, self.evidence, self.canonical)
        after = json.dumps(public_risk_projection(registry), sort_keys=True, separators=(",", ":"))
        self.assertEqual(hashlib.sha256(before.encode()).hexdigest(), hashlib.sha256(after.encode()).hexdigest())

    def test_malformed_input_fails_without_exception(self):
        report = validate_scenario_history(self.schema, [{"scenario_set_id": "bad"}], [{"scenario_id": "bad"}], self.risks, self.signals, self.relationships, self.observations, self.evidence, self.canonical)
        self.assertFalse(report.ok)


if __name__ == "__main__":
    unittest.main()
