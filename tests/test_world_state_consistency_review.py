from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import hashlib
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from review_world_state_consistency_proposal import (  # noqa: E402
    DEFAULT_PROPOSAL,
    DEFAULT_REVIEWED_AT_UTC,
    EXPECTED_PROPOSAL_FINGERPRINT,
    EXPECTED_RETAINED_MANIFEST_SHA256,
    EXPECTED_SOURCE_MANIFEST_SHA256,
    build_review_transaction,
    validate_review_candidate,
)


def package_copy() -> dict:
    return json.loads(DEFAULT_PROPOSAL.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class WorldStateConsistencyReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proposal_before = file_sha256(DEFAULT_PROPOSAL)
        cls.package = package_copy()

    def valid_record(self) -> dict:
        return build_review_transaction(
            package_copy(),
            decision="ACCEPTED",
            reviewed_at_utc=DEFAULT_REVIEWED_AT_UTC,
        )

    def test_valid_retained_proposal_can_be_reviewed(self):
        record = self.valid_record()
        self.assertEqual(record["decision"], "ACCEPTED")
        self.assertEqual(record["decision_scope"], "READ_BOUNDARY_CONSISTENCY_ONLY")
        self.assertEqual(record["write_targets"], [])

    def test_explicit_decision_is_required_and_no_default_acceptance_exists(self):
        with self.assertRaises(ValueError):
            build_review_transaction(
                package_copy(), decision="", reviewed_at_utc=DEFAULT_REVIEWED_AT_UTC
            )

    def test_only_read_boundary_acceptance_is_allowed(self):
        with self.assertRaises(ValueError):
            build_review_transaction(
                package_copy(), decision="PRODUCTION_ADMITTED", reviewed_at_utc=DEFAULT_REVIEWED_AT_UTC
            )

    def test_exact_fingerprints_are_required(self):
        for field, expected in (
            ("semantic_proposal_fingerprint", EXPECTED_PROPOSAL_FINGERPRINT),
            ("source_manifest_sha256", EXPECTED_SOURCE_MANIFEST_SHA256),
            ("retained_manifest_sha256", EXPECTED_RETAINED_MANIFEST_SHA256),
        ):
            candidate = package_copy()
            candidate[field] = "0" * 64
            errors = validate_review_candidate(candidate, verify_current_inputs=False)
            self.assertTrue(errors, field)
            self.assertNotIn(expected, errors)

    def test_changed_source_object_blocks_acceptance(self):
        candidate = package_copy()
        candidate["source_manifest"][0]["object_sha256"] = "0" * 64
        errors = validate_review_candidate(candidate, verify_current_inputs=False)
        self.assertTrue(any("aggregate hash mismatch" in error for error in errors))

    def test_mutation_check_failure_blocks_acceptance(self):
        candidate = package_copy()
        candidate["mutation_proof"]["status"] = "FAIL"
        errors = validate_review_candidate(candidate, verify_current_inputs=False)
        self.assertTrue(any("mutation proof" in error for error in errors))

    def test_future_evidence_contamination_blocks_acceptance(self):
        candidate = package_copy()
        candidate["proposal"]["selected_inputs"]["signals"].append({
            "object_id": "future-signal",
            "revision_id": "future-revision",
            "manifest_key": "future",
        })
        errors = validate_review_candidate(candidate)
        self.assertTrue(any("proposal body" in error for error in errors))
        with self.assertRaises(ValueError):
            build_review_transaction(
                candidate, decision="ACCEPTED", reviewed_at_utc=DEFAULT_REVIEWED_AT_UTC,
            )

    def test_forecast_cutoff_violation_blocks_acceptance(self):
        candidate = package_copy()
        candidate["proposal"]["forecast_outcome_references"][0]["information_cutoff_at_utc"] = "2026-09-28T00:00:00Z"
        errors = validate_review_candidate(candidate, verify_current_inputs=False)
        self.assertTrue(any("future information" in error for error in errors))

    def test_outcome_before_eligibility_blocks_acceptance(self):
        candidate = package_copy()
        candidate["proposal"]["forecast_outcome_references"][0]["outcome_revision_ids"] = ["future-outcome-revision"]
        errors = validate_review_candidate(candidate, verify_current_inputs=False)
        self.assertTrue(any("Outcome before eligibility" in error for error in errors))

    def test_nonempty_write_target_blocks_acceptance(self):
        candidate = package_copy()
        candidate["review_state"]["write_targets"] = ["data/world_state/state.json"]
        errors = validate_review_candidate(candidate, verify_current_inputs=False)
        self.assertTrue(any("write target" in error for error in errors))

    def test_public_projection_permission_blocks_acceptance(self):
        candidate = package_copy()
        candidate["public_projection_permitted"] = True
        errors = validate_review_candidate(candidate, verify_current_inputs=False)
        self.assertTrue(any("public projection" in error for error in errors))

    def test_production_admission_flag_blocks_acceptance(self):
        candidate = package_copy()
        candidate["production_world_state"] = True
        errors = validate_review_candidate(candidate, verify_current_inputs=False)
        self.assertTrue(any("production World State" in error for error in errors))

    def test_original_proposal_remains_unchanged(self):
        before = self.proposal_before
        self.valid_record()
        self.assertEqual(file_sha256(DEFAULT_PROPOSAL), before)

    def test_accepted_record_references_exact_proposal_and_fingerprints(self):
        record = self.valid_record()
        self.assertEqual(record["proposal_reference"], "data/world_state_audit/CONSISTENCY_PROPOSAL_20260927T043904Z_REVIEW_PENDING.json")
        self.assertEqual(record["proposal_semantic_fingerprint"], EXPECTED_PROPOSAL_FINGERPRINT)
        self.assertEqual(record["input_manifest_sha256"], EXPECTED_SOURCE_MANIFEST_SHA256)
        self.assertEqual(record["retained_manifest_sha256"], EXPECTED_RETAINED_MANIFEST_SHA256)

    def test_review_decision_is_reproducible(self):
        self.assertEqual(self.valid_record(), self.valid_record())

    def test_authority_empty_state_is_accepted(self):
        result = self.valid_record()["criterion_results"]["authority_interpretation"]
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["disposition"], "NO_CLAIMS_TO_REVIEW")

    def test_implementation_empty_state_is_accepted(self):
        result = self.valid_record()["criterion_results"]["implementation_state"]
        self.assertEqual(result["status"], "PASS")

    def test_negative_evidence_empty_state_is_accepted(self):
        result = self.valid_record()["criterion_results"]["negative_evidence"]
        self.assertEqual(result["disposition"], "EMPTY_RESULT_CORRECT")

    def test_graph_empty_state_is_accepted(self):
        result = self.valid_record()["criterion_results"]["graph_classes"]
        self.assertEqual(result["disposition"], "EMPTY_RESULT_CORRECT")

    def test_no_sample_is_accepted_without_calibration(self):
        result = self.valid_record()["criterion_results"]["evaluation"]
        self.assertEqual(result["disposition"], "NO_SAMPLE_ACCEPTED")

    def test_canonical_limitation_remains_explicit(self):
        result = self.valid_record()["criterion_results"]["canonical_limitation"]
        self.assertEqual(result["disposition"], "LIMITATION_RETAINED")

    def test_no_production_store_or_public_projection_is_created(self):
        record = self.valid_record()
        self.assertFalse((ROOT / "data/world_state").exists())
        self.assertFalse((ROOT / "docs/world_state.json").exists())
        self.assertFalse(record["public_projection_permitted"])
        self.assertFalse(record["production_world_state_admitted"])

    def test_review_record_has_no_write_targets(self):
        record = self.valid_record()
        self.assertEqual(record["write_targets"], [])
        self.assertTrue(record["reviewed_proposal_remains_non_governed"])

    def test_all_forecast_cutoffs_are_preserved(self):
        record = self.valid_record()
        result = record["criterion_results"]["forecast_cutoff_integrity"]
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["disposition"], "FOUR_ISSUANCES_PRESERVED")

    def test_review_does_not_change_the_loaded_candidate(self):
        candidate = package_copy()
        original = deepcopy(candidate)
        self.valid_record()
        self.assertEqual(candidate, original)


if __name__ == "__main__":
    unittest.main()
