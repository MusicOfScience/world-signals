from __future__ import annotations

from copy import deepcopy
import unittest

from world_signals.world_state_actor import (
    ACTOR_IDENTITY_ADMISSION_TRANSACTION_TYPE,
    ActorIdentityAdmissionError,
    build_actor_identity_admission_transaction,
    build_actor_identity_candidate,
    simulate_actor_identity_admission,
    actor_identity_effective_as_of,
    actor_identity_known_as_of,
    validate_actor_identity_candidate,
)
from world_signals.world_state_history import fingerprint


def _ref(label: str) -> dict[str, str | None]:
    return {"layer": "SYNTHETIC", "object_id": label, "revision_id": None, "object_sha256": fingerprint({"id": label})}


class WorldStateActorIdentityTests(unittest.TestCase):
    def candidate(self, **overrides):
        values = {
            "actor_id": "WSACT-SYNTHETIC-CENTRAL-BANK",
            "canonical_label": "Synthetic Reserve",
            "actor_type": "CENTRAL_BANK",
            "aliases": ["Synthetic RB"],
            "jurisdiction": ["Synthetic Jurisdiction"],
            "effective_from": "2026-01-01T00:00:00Z",
            "provenance_refs": [_ref("synthetic-source")],
        }
        values.update(overrides)
        return build_actor_identity_candidate(**values)

    def test_identity_candidate_is_distinct_from_claims(self):
        candidate = self.candidate()
        self.assertEqual(validate_actor_identity_candidate(candidate), [])
        self.assertNotIn("capability", candidate)
        self.assertNotIn("intent", candidate)
        self.assertEqual(candidate["review_state"], "UNDER_REVIEW")

    def test_aliases_are_not_auto_merged(self):
        candidate = self.candidate()
        registry = {"actors": [self.candidate(actor_id="WSACT-OTHER", canonical_label="Other Institution", aliases=["Synthetic RB"])], "relationships": []}
        self.assertTrue(any("alias already belongs" in error for error in validate_actor_identity_candidate(candidate, existing_registry=registry)))

    def test_mutable_claims_and_fake_admission_metadata_are_rejected(self):
        candidate = self.candidate()
        candidate["capability"] = "injected"
        self.assertTrue(validate_actor_identity_candidate(candidate))
        clean = self.candidate()
        clean["admission_transaction_id"] = "NO-ADMISSION"
        self.assertTrue(validate_actor_identity_candidate(clean))

    def test_identity_admission_is_explicit_and_simulation_only(self):
        candidate = self.candidate()
        transaction = build_actor_identity_admission_transaction(
            candidate,
            reviewer_id="synthetic-reviewer",
            decided_at_utc="2026-01-02T00:00:00Z",
            admitted_at_utc="2026-01-02T00:00:01Z",
            pre_state_hashes={"actors": fingerprint({"actors": [], "relationships": []})},
            post_state_hashes={"actors": fingerprint({"actors": [candidate], "relationships": []})},
            write_targets=["SIMULATION_ONLY:actor_registry"],
        )
        self.assertEqual(transaction["transaction_type"], ACTOR_IDENTITY_ADMISSION_TRANSACTION_TYPE)
        result = simulate_actor_identity_admission(candidate, transaction)
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["production_write_performed"])
        self.assertEqual(candidate["review_state"], "UNDER_REVIEW")
        self.assertEqual(result["after"]["actors"][0]["review_state"], "ACCEPTED")

    def test_simulation_failure_leaves_input_unchanged(self):
        candidate = self.candidate()
        before = deepcopy(candidate)
        with self.assertRaises(ActorIdentityAdmissionError):
            simulate_actor_identity_admission(candidate, {"transaction_type": ACTOR_IDENTITY_ADMISSION_TRANSACTION_TYPE, "decision": "ACCEPTED", "candidate_fingerprint": "wrong"})
        self.assertEqual(candidate, before)

    def test_unknown_historical_start_is_explicit_and_fails_closed_for_effective_queries(self):
        candidate = self.candidate(
            effective_from=None,
            effective_from_precision="UNKNOWN",
            identity_known_at_utc="2026-09-05T14:40:00Z",
        )
        self.assertEqual(validate_actor_identity_candidate(candidate), [])
        self.assertTrue(actor_identity_known_as_of(candidate, "2026-09-06T00:00:00Z"))
        self.assertFalse(actor_identity_effective_as_of(candidate, "1900-01-01T00:00:00Z"))
        self.assertFalse(actor_identity_effective_as_of(candidate, "2026-09-06T00:00:00Z"))
