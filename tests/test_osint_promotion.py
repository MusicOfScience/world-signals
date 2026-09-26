from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.osint_promotion import (
    live_state_hash,
    validate_osint_promotion_transaction,
)


class OSINTPromotionTests(unittest.TestCase):
    def setUp(self):
        self.schema = {"version": "0.13"}
        self.evidence = {
            "version": "0.13",
            "evidence": [{
                "evidence_id": "WSEV-TEST-1",
                "provider": "Test authority",
            }],
        }
        self.observations = {
            "version": "0.13",
            "population_state": "CONTROLLED_OSINT_REVIEWED_OBSERVATION_SPECIMEN",
            "observations": [{
                "observation_id": "WSLI-TEST-1",
                "evidence_refs": ["WSEV-TEST-1"],
                "automatic_canonical_commit": False,
                "google_calendar_write": False,
            }],
        }
        self.sources = {
            "sources": [{
                "source_id": "WSSRC-TEST-1",
                "automated_monitoring_use": "CLEARED_BOUNDED_OFFICIAL_RSS",
            }],
        }

    def transaction(self):
        post_hash = live_state_hash(self.schema, self.evidence, self.observations)
        return {
            "transaction_id": "OSINT-PROMOTION-TEST-1",
            "transaction_type": "REVIEWED_OSINT_OBSERVATION_PROMOTION",
            "decision": "ACCEPTED",
            "decided_at_utc": "2026-09-27T00:00:00Z",
            "reviewer": {
                "reviewer_id": "test-reviewer",
                "reviewed_at_utc": "2026-09-27T00:00:00Z",
                "decision_basis": "The source fact was reviewed and separated from inference.",
            },
            "candidate_audit": [{
                "candidate_id": "WSC-TEST-1",
                "observation_id": "WSLI-TEST-1",
                "source_id": "WSSRC-TEST-1",
                "route_id": "osint-test-route",
                "retrieval_state": "SUCCESS",
                "payload_sha256": "a" * 64,
                "parser_version": "parser-test-1",
                "adapter_version": "adapter-test-1",
                "candidate_state": "NEW",
                "decision": "PROMOTE",
                "rationale": "Primary source and factual proposition are clear.",
            }],
            "evidence_ids": ["WSEV-TEST-1"],
            "observation_ids": ["WSLI-TEST-1"],
            "pre_state": {
                "schema_version": "0.12",
                "population_state": "CONTROLLED_PREVIOUS",
                "observation_count": 0,
                "evidence_count": 0,
                "sha256": "pre-state-recorded-separately",
            },
            "post_state": {
                "schema_version": "0.13",
                "population_state": "CONTROLLED_OSINT_REVIEWED_OBSERVATION_SPECIMEN",
                "observation_count": 1,
                "evidence_count": 1,
                "sha256": post_hash,
            },
            "validation": {
                "status": "PASS",
                "validator_version": "osint-promotion-test-1",
                "validated_at_utc": "2026-09-27T00:00:00Z",
            },
            "promotion_limit": {"maximum_new_observations": 4, "promoted_count": 1},
            "boundary": {
                "automatic_promotion": False,
                "automatic_signal_promotion": False,
                "automatic_canonical_commit": False,
                "public_observation_projection": "CLOSED",
            },
            "denominator_note": "The promoted observation remains in governed history and cannot be silently removed.",
        }

    def validate(self, transaction=None, *, source_registry=None):
        return validate_osint_promotion_transaction(
            self.schema,
            self.evidence,
            self.observations,
            source_registry or self.sources,
            transaction or self.transaction(),
            now_utc="2026-09-27T00:01:00Z",
        )

    def test_reviewed_promotion_with_provenance_passes(self):
        self.assertEqual(self.validate(), ())

    def test_failed_or_execution_environment_retrieval_cannot_promote(self):
        for state in ("HTTP_ERROR", "EXECUTION_ENVIRONMENT_DNS_FAILURE"):
            transaction = self.transaction()
            transaction["candidate_audit"][0]["retrieval_state"] = state
            self.assertIn("only a successful retrieval can be promoted", " ".join(self.validate(transaction)))

    def test_uncleared_source_cannot_promote(self):
        source_registry = copy.deepcopy(self.sources)
        source_registry["sources"][0]["automated_monitoring_use"] = "HELD_PENDING_REVIEW"
        self.assertIn("source automation permission is not cleared", " ".join(self.validate(source_registry=source_registry)))

    def test_automatic_signal_or_canonical_promotion_is_rejected(self):
        transaction = self.transaction()
        transaction["boundary"]["automatic_signal_promotion"] = True
        self.assertIn("boundary is not closed", " ".join(self.validate(transaction)))

    def test_duplicate_candidate_or_observation_is_rejected(self):
        transaction = self.transaction()
        transaction["candidate_audit"].append(copy.deepcopy(transaction["candidate_audit"][0]))
        self.assertIn("one reviewed entry per promoted observation", " ".join(self.validate(transaction)))

    def test_post_state_hash_detects_governed_data_drift(self):
        transaction = self.transaction()
        self.observations["observations"][0]["summary"] = "Changed after the transaction."
        self.assertIn("post-state sha256 does not match", " ".join(self.validate(transaction)))

    def test_four_observation_transaction_limit_is_enforced(self):
        transaction = self.transaction()
        transaction["observation_ids"] = ["WSLI-TEST-1"] * 5
        transaction["evidence_ids"] = ["WSEV-TEST-1"] * 5
        transaction["promotion_limit"]["promoted_count"] = 5
        self.assertIn("non-empty unique list", " ".join(self.validate(transaction)))


if __name__ == "__main__":
    unittest.main()
