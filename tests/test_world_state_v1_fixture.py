"""Contract tests for the synthetic, test-only World State v1 fixture.

This module deliberately does not import a World State production reader.  The
small helpers below exercise the semantics in the design record without
opening, copying, or writing any governed production dataset.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "world_state_v1" / "fixture.json"
FORBIDDEN_PRODUCTION_PATHS = {
    "data/world_state/state.json",
    "data/canonical/registry.json",
    "data/live_intelligence/observations.json",
    "data/analysis/event_reviews.json",
    "data/signals/signals.json",
    "data/relationships/relationships.json",
    "data/risks/states.json",
    "data/scenarios/scenarios.json",
    "data/forecasts/forecasts.json",
    "data/outcomes/outcomes.json",
}
UNCERTAINTY_TYPES = {
    "PROVENANCE_SOURCE",
    "MEASUREMENT",
    "TEMPORAL",
    "INTERPRETIVE",
    "MODEL",
    "ACTOR_INTENT",
    "INSTITUTIONAL_AUTHORITY",
}


def load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def compact_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def manifest_by_id(fixture: dict) -> dict[str, dict]:
    return {item["object_id"]: item for item in fixture["source_manifest"]}


def source_objects_as_of(fixture: dict, as_of_utc: str) -> list[dict]:
    cutoff = parse_time(as_of_utc)
    return [
        item
        for item in fixture["source_manifest"]
        if parse_time(item["object"]["known_at_utc"]) <= cutoff
    ]


def implementation_claims_as_of(fixture: dict, as_of_utc: str) -> list[dict]:
    cutoff = parse_time(as_of_utc)
    return [
        claim
        for claim in fixture["implementation_claims"]
        if parse_time(claim["known_at_utc"]) <= cutoff
    ]


def explicit_states_as_of(fixture: dict, as_of_utc: str) -> set[str]:
    return {claim["state"] for claim in implementation_claims_as_of(fixture, as_of_utc)}


def outcome_references_as_of(fixture: dict, as_of_utc: str) -> list[dict]:
    cutoff = parse_time(as_of_utc)
    return [
        outcome
        for outcome in fixture["outcome_references"]
        if parse_time(outcome["known_at_utc"]) <= cutoff
    ]


def forecast_evidence_at_cutoff(fixture: dict, forecast: dict) -> list[str]:
    cutoff = parse_time(forecast["information_cutoff"])
    manifest = manifest_by_id(fixture)
    return [
        ref
        for ref in forecast["evidence_refs"]
        if ref in manifest and parse_time(manifest[ref]["object"]["known_at_utc"]) <= cutoff
    ]


def validate_source_manifest(fixture: dict) -> list[str]:
    errors = []
    seen: set[tuple[str, str]] = set()
    for item in fixture.get("source_manifest", []):
        key = (item.get("object_id", ""), item.get("revision_id", ""))
        if key in seen:
            errors.append(f"duplicate manifest pin {key}")
        seen.add(key)
        expected = compact_sha256(item.get("object"))
        if item.get("object_sha256") != expected:
            errors.append(f"manifest hash mismatch for {item.get('object_id')}")
        if not item.get("layer", "").startswith("TEST_ONLY_"):
            errors.append(f"non-test layer in manifest: {item.get('layer')}")
    return errors


def validate_negative_evidence(row: dict) -> list[str]:
    errors = []
    scope = row.get("search_scope", {})
    coverage = row.get("source_coverage", {})
    if row.get("type") != "NO_EVIDENCE_IN_SCOPED_SOURCES":
        errors.append("only bounded scoped absence is supported")
    if not scope.get("source_ids") or not coverage.get("queried_source_ids"):
        errors.append("negative evidence requires queried source coverage")
    if set(coverage.get("source_failures", [])):
        errors.append("source failure cannot become negative evidence")
    if not scope.get("query") or not scope.get("window_start") or not scope.get("window_end"):
        errors.append("negative evidence requires a query and time window")
    if not row.get("expected_action_or_measure"):
        errors.append("negative evidence requires an expected indicator")
    if not row.get("limitations"):
        errors.append("negative evidence requires limitations")
    return errors


def validate_fixture(fixture: dict) -> list[str]:
    errors = []
    if fixture.get("test_only") is not True:
        errors.append("fixture must be test-only")
    if fixture.get("production_population") is not False:
        errors.append("fixture must not be a production population")
    if fixture.get("production_write_targets") != []:
        errors.append("fixture must have no production write targets")
    errors.extend(validate_source_manifest(fixture))
    if set(fixture.get("review_transaction", {}).get("write_targets", [])):
        errors.append("review transaction has a write target")
    if fixture.get("review_transaction", {}).get("public_projection_permitted") is True:
        errors.append("public projection must remain closed")
    for row in fixture.get("negative_evidence", []):
        errors.extend(validate_negative_evidence(row))
    for collection in (
        "actors",
        "implementation_claims",
        "dimensions",
        "anomalies",
        "negative_evidence",
        "uncertainties",
        "hypotheses",
        "model_disagreement",
        "transmission_edges",
        "feedback_relationships",
        "market_sensors",
    ):
        for row in fixture.get(collection, []):
            support = set(row.get("support_refs", []))
            contradiction = set(row.get("contradiction_refs", []))
            if support & contradiction:
                errors.append(f"support/contradiction overlap in {collection}")
    for uncertainty in fixture.get("uncertainties", []):
        if uncertainty.get("type") not in UNCERTAINTY_TYPES:
            errors.append(f"unknown uncertainty type {uncertainty.get('type')}")
    if "confidence" in json.dumps(fixture, sort_keys=True):
        errors.append("universal confidence field is prohibited")
    return errors


class WorldStateV1FixtureContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load_fixture()
        cls.times = cls.fixture["times"]

    def test_fixture_is_unmistakably_test_only(self):
        self.assertEqual(validate_fixture(self.fixture), [])
        self.assertTrue(self.fixture["fixture_id"].startswith("TEST_ONLY_"))
        self.assertFalse((ROOT / "data/world_state/state.json").exists())

    def test_distinct_actor_identity_and_authority_scope(self):
        actors = {actor["actor_ref"]: actor for actor in self.fixture["actors"]}
        self.assertNotEqual(actors["actor:individual-alpha"]["actor_ref"], "actor:coordination-office")
        self.assertNotEqual(actors["actor:individual-alpha"]["actor_type"], actors["actor:coordination-office"]["actor_type"])
        self.assertIn("institutional_decision", actors["actor:individual-alpha"]["authority_scope"]["does_not_include"])
        self.assertIn("decide_coordination_protocol", actors["actor:coordination-office"]["authority_scope"]["may"])

    def test_actor_statement_cannot_become_institutional_decision(self):
        said = next(row for row in self.fixture["implementation_claims"] if row["state"] == "SAID")
        decided = next(row for row in self.fixture["implementation_claims"] if row["state"] == "DECIDED")
        self.assertEqual(said["actor_ref"], "actor:individual-alpha")
        self.assertEqual(decided["actor_ref"], "actor:coordination-office")
        self.assertNotEqual(said["claim_id"], decided["claim_id"])

    def test_authority_requires_competent_institution_evidence(self):
        claim = next(row for row in self.fixture["implementation_claims"] if row["state"] == "DECIDED")
        self.assertIn("E-DECIDED", claim["support_refs"])
        self.assertNotIn("E-SAID", claim["support_refs"])
        self.assertIn("U-INSTITUTIONAL-AUTHORITY", next(row for row in self.fixture["uncertainties"] if row["uncertainty_id"] == "U-INSTITUTIONAL-AUTHORITY")["uncertainty_id"])

    def test_actor_alias_similarity_does_not_auto_merge_identity(self):
        actors = self.fixture["actors"]
        exact = {
            alias: actor["actor_ref"]
            for actor in actors
            for alias in actor["aliases"]
        }
        self.assertEqual(exact["Transition Office"], "actor:coordination-office")
        self.assertEqual(exact["Transition Office Lead"], "actor:individual-alpha")
        self.assertNotEqual(exact["Transition Office"], exact["Transition Office Lead"])

    def test_said_does_not_imply_decided(self):
        states = explicit_states_as_of(self.fixture, self.times["t1"])
        self.assertIn("SAID", states)
        self.assertNotIn("DECIDED", states)

    def test_decided_does_not_imply_authorised(self):
        states = explicit_states_as_of(self.fixture, self.times["t2"])
        self.assertIn("DECIDED", states)
        self.assertNotIn("AUTHORISED", states)

    def test_authorised_does_not_imply_implemented(self):
        states = explicit_states_as_of(self.fixture, self.times["t3"])
        self.assertIn("AUTHORISED", states)
        self.assertNotIn("IMPLEMENTED", states)

    def test_implemented_does_not_imply_observed(self):
        claims = [row for row in self.fixture["implementation_claims"] if row["state"] == "IMPLEMENTED"]
        self.assertTrue(claims)
        self.assertFalse(any(row["state"] == "OBSERVED" for row in implementation_claims_as_of(self.fixture, self.times["t4"])))
        self.assertEqual(claims[0]["divergence"], "NARROWED_FROM_STATED_PROPOSITION")

    def test_later_evidence_is_excluded_from_earlier_as_of_read(self):
        ids = {row["object_id"] for row in source_objects_as_of(self.fixture, self.times["t1"])}
        self.assertIn("E-SAID", ids)
        self.assertNotIn("E-DECIDED", ids)
        self.assertNotIn("E-AUTHORISED", ids)

    def test_later_evidence_does_not_rewrite_earlier_state(self):
        before = deepcopy(next(row for row in self.fixture["implementation_claims"] if row["state"] == "SAID"))
        implementation_claims_as_of(self.fixture, self.times["t4"])
        after = next(row for row in self.fixture["implementation_claims"] if row["claim_id"] == before["claim_id"])
        self.assertEqual(after, before)

    def test_capability_and_constraint_claims_have_support_and_uncertainty(self):
        actors = self.fixture["actors"]
        capability = actors[0]["capabilities"][0]
        constraint = actors[1]["constraints"][0]
        self.assertTrue(capability["support_refs"])
        self.assertTrue(constraint["support_refs"])
        self.assertTrue(capability["uncertainty_refs"])
        self.assertTrue(constraint["uncertainty_refs"])
        self.assertTrue(capability["contradiction_refs"])

    def test_unknown_capability_remains_unknown(self):
        unknown = self.fixture["actors"][1]["unknown_claims"][0]
        self.assertEqual(unknown["status"], "UNKNOWN")
        self.assertEqual(unknown["support_refs"], [])
        self.assertEqual(unknown["contradiction_refs"], [])

    def test_baseline_is_explicit_and_inspectable(self):
        baseline = self.fixture["baselines"][0]
        self.assertEqual(baseline["basis"], "OBSERVATION_WINDOW")
        self.assertEqual(baseline["baseline_value_or_label"]["unit"], "handoffs_per_day")
        self.assertTrue(baseline["source_refs"])

    def test_anomaly_requires_compatible_baseline(self):
        anomaly = self.fixture["anomalies"][0]
        baseline_ids = {row["baseline_id"] for row in self.fixture["baselines"]}
        self.assertIn(anomaly["baseline_ref"], baseline_ids)
        invalid = deepcopy(anomaly)
        invalid["baseline_ref"] = None
        self.assertNotIn(invalid["baseline_ref"], baseline_ids)

    def test_anomaly_is_comparison_not_forecast(self):
        anomaly = self.fixture["anomalies"][0]
        forecast_ids = {row["forecast_id"] for row in self.fixture["forecast_references"]}
        self.assertNotIn(anomaly["anomaly_id"], forecast_ids)
        self.assertNotIn("probability", anomaly)

    def test_negative_evidence_is_bounded(self):
        row = self.fixture["negative_evidence"][0]
        self.assertEqual(validate_negative_evidence(row), [])
        self.assertEqual(row["source_coverage"]["coverage_assessment"], "PARTIAL")
        self.assertTrue(row["limitations"])

    def test_source_failure_cannot_be_negative_evidence(self):
        row = deepcopy(self.fixture["negative_evidence"][0])
        row["source_coverage"]["source_failures"] = ["synthetic-bulletin-a"]
        self.assertTrue(any("source failure" in error for error in validate_negative_evidence(row)))

    def test_unqueried_source_cannot_become_unbounded_negative_evidence(self):
        row = deepcopy(self.fixture["negative_evidence"][0])
        row["source_coverage"]["queried_source_ids"] = []
        self.assertTrue(any("queried source coverage" in error for error in validate_negative_evidence(row)))

    def test_unqueried_domain_does_not_become_negative_evidence(self):
        self.assertIn("HEALTH_BIOSECURITY", self.fixture["unqueried_domains"])
        self.assertFalse(any("HEALTH_BIOSECURITY" in json.dumps(row) for row in self.fixture["negative_evidence"]))

    def test_all_typed_uncertainty_types_are_retained_without_numeric_confidence(self):
        actual = {row["type"] for row in self.fixture["uncertainties"]}
        self.assertTrue(UNCERTAINTY_TYPES <= actual)
        self.assertNotIn("confidence", json.dumps(self.fixture, sort_keys=True))

    def test_unknown_is_supported_without_forcing_numeric_confidence(self):
        unknown = self.fixture["actors"][1]["unknown_claims"][0]
        self.assertEqual(unknown["status"], "UNKNOWN")
        self.assertNotIn("confidence", unknown)

    def test_competing_hypotheses_coexist(self):
        hypotheses = self.fixture["hypotheses"]
        self.assertEqual(len(hypotheses), 2)
        self.assertEqual({row["disposition"] for row in hypotheses}, {"UNRESOLVED"})
        self.assertEqual({row["subject_ref"] for row in hypotheses}, {"IMPLEMENTATION-DECIDED"})

    def test_hypothesis_support_contradiction_and_assumptions_are_preserved(self):
        for row in self.fixture["hypotheses"]:
            self.assertTrue(row["support_refs"])
            self.assertTrue(row["contradictory_refs"])
            self.assertTrue(row["assumptions"])
            self.assertTrue(row["falsifiers"])

    def test_model_disagreement_is_not_factual_corroboration(self):
        disagreement = self.fixture["model_disagreement"][0]
        self.assertEqual(disagreement["factual_source_refs"], [])
        self.assertEqual(len(disagreement["lenses"]), 2)
        self.assertTrue(disagreement["underlying_evidence_refs"])

    def test_reviewed_and_hypothesised_transmission_edges_are_distinct(self):
        edges = {row["edge_id"]: row for row in self.fixture["transmission_edges"]}
        self.assertEqual(edges["EDGE-SECURITY-TO-SHIPPING"]["class"], "DEPENDENCY")
        self.assertEqual(edges["EDGE-SHIPPING-TO-ENERGY"]["class"], "HYPOTHESISED_TRANSMISSION")
        self.assertEqual(edges["EDGE-SHIPPING-TO-ENERGY"]["review_status"], "UNDER_REVIEW")

    def test_graph_proximity_does_not_create_transitive_edge(self):
        pairs = {(row["source_ref"], row["target_ref"]) for row in self.fixture["transmission_edges"]}
        self.assertIn(("TEST-SECURITY-DISRUPTION", "TEST-SHIPPING-CONSTRAINT"), pairs)
        self.assertIn(("TEST-SHIPPING-CONSTRAINT", "TEST-ENERGY-IMPORT-COST"), pairs)
        self.assertNotIn(("TEST-SECURITY-DISRUPTION", "TEST-ENERGY-IMPORT-COST"), pairs)

    def test_lag_and_threshold_semantics_are_explicit(self):
        reviewed, hypothesised = self.fixture["transmission_edges"]
        self.assertEqual(reviewed["lag"]["unit"], "hours")
        self.assertTrue(reviewed["threshold"]["basis_refs"])
        self.assertIsNone(hypothesised["threshold"])
        self.assertEqual(hypothesised["threshold_status"], "NONE_DECLARED")

    def test_feedback_is_explicit_and_not_auto_inferred(self):
        feedback = self.fixture["feedback_relationships"][0]
        self.assertFalse(feedback["inferred_automatically"])
        self.assertEqual(feedback["class"], "REFLEXIVE_EFFECT")
        self.assertNotIn((feedback["source_ref"], feedback["target_ref"]), {
            (edge["source_ref"], edge["target_ref"]) for edge in self.fixture["transmission_edges"]
        })

    def test_market_sensor_retains_measurement_limits_and_alternatives(self):
        sensor = self.fixture["market_sensors"][0]
        for field in ("instrument_or_measure", "venue_or_measurement_source", "observed_at_utc", "baseline_or_counterfactual", "horizon", "measurement_method", "limitations", "alternative_explanations"):
            self.assertIn(field, sensor)
        self.assertEqual(sensor["causal_inference"], "NOT_ESTABLISHED")

    def test_market_movement_does_not_create_causality_or_edge(self):
        sensor = self.fixture["market_sensors"][0]
        edge_refs = {(row["source_ref"], row["target_ref"]) for row in self.fixture["transmission_edges"]}
        self.assertNotIn((sensor["market_sensor_id"], "TEST-ENERGY-IMPORT-COST"), edge_refs)
        self.assertNotEqual(sensor["causal_inference"], "CAUSAL_EVIDENCE")
        self.assertTrue(sensor["alternative_explanations"])

    def test_scenario_signposts_are_not_forecasts(self):
        signposts = self.fixture["scenario_signposts"][0]["signposts"]
        self.assertEqual(len(signposts), 2)
        for signpost in signposts:
            self.assertNotIn("probability", signpost)
            self.assertNotIn("rank", signpost)
            self.assertNotIn("forecast_outcome", signpost)
            self.assertIn(signpost["effect"], {"MORE_COMPATIBLE", "LESS_COMPATIBLE", "DISCRIMINATING"})

    def test_forecast_cutoff_excludes_late_evidence(self):
        forecast = self.fixture["forecast_references"][0]
        eligible = forecast_evidence_at_cutoff(self.fixture, forecast)
        self.assertIn("E-FORECAST-BASIS", eligible)
        self.assertNotIn("E-LATE-FORECAST", eligible)
        self.assertLess(parse_time(forecast["information_cutoff"]), parse_time(forecast["issue_time"]))

    def test_earlier_world_state_excludes_later_outcome(self):
        self.assertEqual(outcome_references_as_of(self.fixture, self.times["t3"]), [])
        self.assertEqual(len(outcome_references_as_of(self.fixture, self.times["t4"])), 1)

    def test_later_outcome_does_not_rewrite_forecast_issuance(self):
        forecast_before = deepcopy(self.fixture["forecast_references"][0])
        outcome = self.fixture["outcome_references"][0]
        self.assertEqual(outcome["forecast_id"], forecast_before["forecast_id"])
        self.assertEqual(self.fixture["forecast_references"][0], forecast_before)
        self.assertIn("information_cutoff", forecast_before["immutable_fields"])

    def test_source_manifest_pins_layer_object_revision_and_hash(self):
        self.assertEqual(validate_source_manifest(self.fixture), [])
        for item in self.fixture["source_manifest"]:
            self.assertTrue(item["layer"].startswith("TEST_ONLY_"))
            self.assertTrue(item["object_id"])
            self.assertTrue(item["revision_id"])
            self.assertEqual(len(item["object_sha256"]), 64)

    def test_source_manifest_hash_mismatch_fails_closed(self):
        mutated = deepcopy(self.fixture)
        mutated["source_manifest"][0]["object"]["kind"] = "rewritten_statement"
        self.assertTrue(any("hash mismatch" in error for error in validate_source_manifest(mutated)))

    def test_supporting_and_contradictory_references_are_disjoint(self):
        self.assertEqual(validate_fixture(self.fixture), [])
        claim = next(row for row in self.fixture["implementation_claims"] if row["claim_id"] == "IMPLEMENTATION-IMPLEMENTED-NARROWED")
        self.assertEqual(set(claim["support_refs"]) & set(claim["contradiction_refs"]), set())

    def test_repeated_same_origin_material_is_not_independent_corroboration(self):
        support_refs = self.fixture["hypotheses"][0]["support_refs"]
        sources = {
            manifest_by_id(self.fixture)[ref]["object"]["source_id"]
            for ref in support_refs
        }
        self.assertLessEqual(len(sources), len(support_refs))
        self.assertNotEqual(len(support_refs), 0)

    def test_empty_downstream_populations_are_valid_governed_results(self):
        populations = self.fixture["production_layer_populations"]
        self.assertEqual(populations["relationships"], [])
        self.assertEqual(populations["risks"], [])
        self.assertEqual(populations["scenarios"], [])
        self.assertEqual(populations["outcomes"], [])
        self.assertEqual(populations["evaluation"]["sample_state"], "NO_SAMPLE")

    def test_input_hashes_unchanged_after_validation(self):
        before = compact_sha256(self.fixture)
        operation_input = deepcopy(self.fixture)
        self.assertEqual(validate_fixture(operation_input), [])
        after = compact_sha256(operation_input)
        self.assertEqual(before, after)

    def test_validation_has_no_governed_or_public_write_target(self):
        self.assertEqual(self.fixture["review_transaction"]["write_targets"], [])
        self.assertFalse(self.fixture["public_projection_permitted"])
        self.assertTrue(FORBIDDEN_PRODUCTION_PATHS.isdisjoint(self.fixture["production_write_targets"]))
        self.assertFalse((ROOT / "docs" / "world-state.json").exists())


if __name__ == "__main__":
    unittest.main()
