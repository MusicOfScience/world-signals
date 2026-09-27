from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.world_state_read import (  # noqa: E402
    DATA_PATHS,
    WORLD_STATE_DIMENSIONS,
    WorldStateReadError,
    object_sha256,
    proposal_summary,
    read_world_state,
    semantic_fingerprint,
    validate_proposal_manifest,
)


def request(as_of: str = "2026-09-27T23:59:59Z", *, dimensions: list[str] | None = None) -> dict:
    return {
        "contract_version": "0.1",
        "as_of_utc": as_of,
        "scope": {
            "jurisdictions": ["*"],
            "dimensions": dimensions or sorted(WORLD_STATE_DIMENSIONS),
            "actor_ids": None,
        },
        "include_negative_evidence": True,
        "input_policy": "ACCEPTED_REVIEWED_HEADS_ONLY",
    }


def file_hashes() -> dict[str, str]:
    return {
        key: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        for key, path in sorted(DATA_PATHS.items())
    }


class WorldStateReadAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proposal = read_world_state(request(), generated_at_utc="2026-09-27T12:00:00Z")

    def test_valid_explicit_read_request_is_accepted(self):
        self.assertEqual(self.proposal["read_request"]["as_of_utc"], "2026-09-27T23:59:59Z")
        self.assertEqual(self.proposal["read_request"]["input_policy"], "ACCEPTED_REVIEWED_HEADS_ONLY")
        self.assertEqual(self.proposal["review_transaction"]["write_targets"], [])

    def test_invalid_contract_version_is_rejected(self):
        bad = request()
        bad["contract_version"] = "0.2"
        with self.assertRaises(WorldStateReadError):
            read_world_state(bad)

    def test_malformed_or_naive_timestamp_is_rejected(self):
        for value in ("2026-09-27T23:59:59", "2026-09-27T23:59:59+00:00", "not-a-time"):
            bad = request(value)
            with self.subTest(value=value), self.assertRaises(WorldStateReadError):
                read_world_state(bad)

    def test_unknown_dimension_is_rejected_and_known_unsupported_dimension_is_explicit(self):
        bad = request(dimensions=["NOT_A_WORLD_STATE_DIMENSION"])
        with self.assertRaises(WorldStateReadError):
            read_world_state(bad)
        supported_vocab_but_unimplemented = read_world_state(request(dimensions=["HEALTH_BIOSECURITY"]))
        codes = {row["code"] for row in supported_vocab_but_unimplemented["limitations"]}
        self.assertIn("DIMENSION_ASSESSMENT_NOT_SUPPORTED", codes)

    def test_unqueried_scope_is_distinct_from_empty_selected_layers(self):
        proposal = read_world_state(request(dimensions=["CONFLICT_MILITARY_ACTIVITY"]))
        self.assertIn("HEALTH_BIOSECURITY", proposal["scope_coverage"]["unqueried_dimensions"])
        self.assertEqual(proposal["scope_coverage"]["queried_domain_with_no_eligible_evidence"], [])
        self.assertEqual(proposal["production_populations"]["relationships"], 0)

    def test_existing_upstream_validation_is_orchestrated(self):
        with patch("world_signals.world_state_read.validate_governed_inputs", wraps=__import__(
            "world_signals.world_state_read", fromlist=["validate_governed_inputs"]
        ).validate_governed_inputs) as validator:
            read_world_state(request())
        validator.assert_called_once()

    def test_signal_as_of_selection_excludes_future_review_revision(self):
        early = read_world_state(request("2026-09-26T23:59:59Z"))
        late = read_world_state(request("2026-09-27T23:59:59Z"))
        self.assertEqual(early["selected_inputs"]["signals"], [])
        self.assertEqual(len(late["selected_inputs"]["signals"]), 1)

    def test_all_upstream_as_of_helpers_receive_explicit_cutoff(self):
        with patch("world_signals.world_state_read.signal_state_as_of", wraps=__import__(
            "world_signals.world_state_read", fromlist=["signal_state_as_of"]
        ).signal_state_as_of) as signal, patch(
            "world_signals.world_state_read.relationship_state_as_of", wraps=__import__(
                "world_signals.world_state_read", fromlist=["relationship_state_as_of"]
            ).relationship_state_as_of
        ) as relationship, patch(
            "world_signals.world_state_read.risk_state_as_of", wraps=__import__(
                "world_signals.world_state_read", fromlist=["risk_state_as_of"]
            ).risk_state_as_of
        ) as risk, patch(
            "world_signals.world_state_read.scenario_state_as_of", wraps=__import__(
                "world_signals.world_state_read", fromlist=["scenario_state_as_of"]
            ).scenario_state_as_of
        ) as scenario, patch(
            "world_signals.world_state_read.forecast_state_as_of", wraps=__import__(
                "world_signals.world_state_read", fromlist=["forecast_state_as_of"]
            ).forecast_state_as_of
        ) as forecast, patch(
            "world_signals.world_state_read.outcome_state_as_of", wraps=__import__(
                "world_signals.world_state_read", fromlist=["outcome_state_as_of"]
            ).outcome_state_as_of
        ) as outcome:
            read_world_state(request("2026-09-27T12:34:56Z"))
        for helper in (signal, relationship, risk, scenario, forecast, outcome):
            self.assertTrue(helper.call_args.args or helper.call_args.kwargs)
            self.assertIn("2026-09-27T12:34:56Z", helper.call_args.args)

    def test_live_intelligence_is_selected_only_when_known_by_cutoff(self):
        early = read_world_state(request("2026-09-06T00:00:00Z"))
        late = read_world_state(request("2026-09-27T23:59:59Z"))
        self.assertEqual(len(early["selected_inputs"]["live_observations"]), 0)
        self.assertEqual(len(late["selected_inputs"]["live_observations"]), 12)
        self.assertEqual(len(late["selected_inputs"]["live_evidence"]), 16)

    def test_analysis_review_identity_and_semantics_are_preserved(self):
        analysis = self.proposal["selected_inputs"]["analysis_reviews"]
        self.assertEqual(len(analysis), 22)
        self.assertEqual(len(self.proposal["selected_inputs"]["analysis_evidence"]), 97)
        self.assertTrue(self.proposal["source_manifest_sha256"])

    def test_empty_relationships_risks_and_scenarios_remain_empty(self):
        self.assertEqual(self.proposal["selected_inputs"]["relationships"], [])
        self.assertEqual(self.proposal["selected_inputs"]["risks_regimes"], [])
        self.assertEqual(self.proposal["selected_inputs"]["scenarios"], [])
        self.assertEqual(self.proposal["relationships"], [])

    def test_forecast_issuance_cutoff_and_revision_identity_are_preserved(self):
        refs = self.proposal["forecast_outcome_references"]
        self.assertEqual(len(refs), 4)
        for row in refs:
            self.assertIn("issuance_id", row)
            self.assertIn("revision_id", row)
            self.assertIn("information_cutoff_at_utc", row)
            self.assertIn("resolution", row)
            self.assertLessEqual(row["information_cutoff_at_utc"], row["issued_at_utc"])

    def test_forecasts_are_not_selected_before_their_revision_is_known(self):
        early = read_world_state(request("2026-09-26T16:59:59Z"))
        self.assertEqual(early["forecast_outcome_references"], [])

    def test_future_outcomes_are_excluded_and_current_evaluation_is_no_sample(self):
        self.assertEqual(self.proposal["selected_inputs"]["outcomes"], [])
        self.assertEqual(self.proposal["evaluation"]["evaluation_state"], "NO_SAMPLE")
        self.assertEqual(self.proposal["evaluation"]["evaluations"], [])

    def test_canonical_historical_limitation_is_visible(self):
        codes = {row["code"] for row in self.proposal["limitations"]}
        self.assertIn("CANONICAL_HISTORICAL_AS_OF_UNSUPPORTED", codes)
        self.assertTrue(self.proposal["selected_inputs"]["canonical_context"])

    def test_actor_and_implementation_state_are_not_invented(self):
        self.assertEqual(self.proposal["actors"], [])
        self.assertEqual(self.proposal["implementation_claims"], [])
        codes = {row["code"] for row in self.proposal["limitations"]}
        self.assertIn("ACTOR_REGISTRY_UNAVAILABLE", codes)
        self.assertIn("WORLD_STATE_ASSESSMENT_NOT_SYNTHESISED", codes)

    def test_no_new_dimensions_baselines_hypotheses_or_transmission_are_invented(self):
        for field in ("dimension_assessments", "baselines", "anomalies", "hypotheses", "model_disagreement", "transmission_edges"):
            self.assertEqual(self.proposal[field], [])

    def test_negative_evidence_is_not_inferred_from_absence(self):
        self.assertEqual(self.proposal["negative_evidence"], [])
        self.assertEqual(self.proposal["scope_coverage"]["negative_evidence_status"], "NO_EXPLICIT_GOVERNED_NEGATIVE_EVIDENCE")
        self.assertIn("NO_EXPLICIT_GOVERNED_NEGATIVE_EVIDENCE", {row["code"] for row in self.proposal["limitations"]})

    def test_excluded_negative_evidence_domain_is_marked_not_requested(self):
        excluded = request()
        excluded["include_negative_evidence"] = False
        proposal = read_world_state(excluded)
        self.assertEqual(proposal["scope_coverage"]["negative_evidence_status"], "NOT_REQUESTED")
        self.assertNotIn("NO_EXPLICIT_GOVERNED_NEGATIVE_EVIDENCE", {row["code"] for row in proposal["limitations"]})

    def test_market_feed_is_not_introduced_and_causality_is_not_created(self):
        self.assertEqual(self.proposal["transmission_edges"], [])
        self.assertIn("MARKET_FEED_NOT_INTRODUCED", {row["code"] for row in self.proposal["limitations"]})

    def test_manifest_hashes_are_deterministic_and_validate(self):
        self.assertEqual(validate_proposal_manifest(self.proposal), [])
        first = self.proposal["source_manifest"][0]
        self.assertEqual(first["object_sha256"], object_sha256(first["object"]))
        self.assertEqual(self.proposal["source_manifest_sha256"], object_sha256(self.proposal["source_manifest"]))

    def test_mutated_object_causes_manifest_failure(self):
        mutated = deepcopy(self.proposal)
        mutated["source_manifest"][0]["object"]["__mutation__"] = True
        self.assertTrue(any("hash mismatch" in error for error in validate_proposal_manifest(mutated)))

    def test_wrong_revision_pin_causes_manifest_failure(self):
        mutated = deepcopy(self.proposal)
        mutated["source_manifest"][0]["revision_id"] = "UNAVAILABLE-FUTURE-REVISION"
        self.assertTrue(any("aggregate hash mismatch" in error for error in validate_proposal_manifest(mutated)))

    def test_semantic_fingerprint_excludes_incidental_generated_time(self):
        first = read_world_state(request(), generated_at_utc="2026-09-27T12:00:00Z")
        second = read_world_state(request(), generated_at_utc="2026-09-27T12:01:00Z")
        self.assertNotEqual(first["generated_at_utc"], second["generated_at_utc"])
        self.assertEqual(first["semantic_fingerprint"], second["semantic_fingerprint"])
        self.assertEqual(semantic_fingerprint(first), semantic_fingerprint(second))

    def test_repeated_identical_read_is_deterministic(self):
        first = read_world_state(request())
        second = read_world_state(request())
        self.assertEqual(first["semantic_fingerprint"], second["semantic_fingerprint"])
        self.assertEqual(first["source_manifest"], second["source_manifest"])

    def test_proposal_is_serialisable_and_inspectable(self):
        encoded = json.dumps(self.proposal, ensure_ascii=False, sort_keys=True)
        decoded = json.loads(encoded)
        self.assertEqual(decoded["proposal_id"], self.proposal["proposal_id"])
        self.assertEqual(proposal_summary(self.proposal)["proposal_status"], "EPHEMERAL_READ_ONLY")

    def test_mutation_protection_reports_all_governed_inputs_unchanged(self):
        before = file_hashes()
        proposal = read_world_state(request())
        after = file_hashes()
        self.assertEqual(before, after)
        self.assertEqual(proposal["mutation_check"]["status"], "PASS")
        self.assertEqual(proposal["mutation_check"]["before"], proposal["mutation_check"]["after"])

    def test_no_production_world_state_dataset_or_public_projection_exists(self):
        self.assertFalse((ROOT / "data/world_state/state.json").exists())
        self.assertFalse(self.proposal["review_transaction"]["public_projection_permitted"])
        self.assertNotIn("docs", {Path(path).parts[0] for path in DATA_PATHS.values()})

    def test_step_2_fixture_remains_isolated(self):
        fixture = ROOT / "tests/fixtures/world_state_v1/fixture.json"
        self.assertTrue(fixture.exists())
        self.assertEqual(fixture.parts[-4:-1], ("tests", "fixtures", "world_state_v1"))
        self.assertFalse((ROOT / "data/world_state").exists())


if __name__ == "__main__":
    unittest.main()
