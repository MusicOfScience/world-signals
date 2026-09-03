import json
from pathlib import Path
import unittest

from src.world_signals.review_checkpoint import (
    checkpoint_public_projection,
    checkpoint_sha256,
    propose_checkpoint,
    validate_checkpoint,
)
from src.world_signals.review_state import proposition_identity


ROOT=Path(__file__).resolve().parents[1]
REVIEW_CONTRACT=json.loads((ROOT/"data/monitor/review_candidate_state_contract.json").read_text(encoding="utf-8"))
CHECKPOINT_CONTRACT=json.loads((ROOT/"data/monitor/durable_review_checkpoint_contract.json").read_text(encoding="utf-8"))


class ReviewCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.checkpoint={
            "project":"WORLD SIGNALS",
            "dataset":"DURABLE_REVIEW_CHECKPOINT",
            "version":"0.1",
            "checkpoint_sequence":0,
            "generated_at":"2026-09-04T00:00:00+00:00",
            "covered_through_monitor_run_number":47,
            "covered_through_monitor_run_id":"33754900613",
            "covered_through_monitor_run_at":"2026-09-03T12:23:29+00:00",
            "previous_checkpoint_sha256":None,
            "item_count":0,
            "state_counts":{},
            "items":[],
            "automatic_canonical_commit":False,
            "google_calendar_write":False,
        }
        self.canonical=[{
            "occurrence_id":"WSO-TEST-001",
            "start_local":"2026-09-10",
            "end_local":None,
            "certainty_status":"CONFIRMED",
            "lifecycle_status":"PLANNED",
        }]
        self.candidate={
            "candidate_id":"WSRC-AAA",
            "diff_type":"DATE_OR_TIME_CHANGED",
            "occurrence_id":"WSO-TEST-001",
            "old_value":{
                "start_local":"2026-09-10",
                "end_local":None,
                "certainty_status":"CONFIRMED",
                "lifecycle_status":"PLANNED",
            },
            "new_value":{
                "start_local":"2026-09-11",
                "end_local":None,
                "certainty_status":"CONFIRMED",
                "lifecycle_status":"PLANNED",
            },
            "source_assertion":{"source_id":"WSSRC-TEST-001","raw":"must not persist"},
            "review_state":"PENDING_REVIEW",
            "automatic_commit_allowed":False,
        }
        self.decisions={"decisions":[]}
        self.ledger={"changes":[]}

    def proposal(self,checkpoint,runs,canonical=None,decisions=None,ledger=None,generated="2026-09-04T01:00:00+00:00"):
        return propose_checkpoint(
            checkpoint,
            runs,
            canonical_records=self.canonical if canonical is None else canonical,
            decisions=self.decisions if decisions is None else decisions,
            change_ledger=self.ledger if ledger is None else ledger,
            review_contract=REVIEW_CONTRACT,
            checkpoint_contract=CHECKPOINT_CONTRACT,
            generated_at=generated,
        )

    def test_new_proposition_is_persisted_with_minimum_private_canonical_state(self):
        proposal=self.proposal(self.checkpoint,[{
            "run_number":48,"run_id":"48","run_at":"2026-09-04T01:00:00+00:00","candidates":[self.candidate]
        }])
        self.assertEqual(proposal["checkpoint_sequence"],1)
        self.assertEqual(proposal["covered_through_monitor_run_number"],48)
        self.assertEqual(proposal["item_count"],1)
        item=proposal["items"][0]
        self.assertEqual(item["state"],"PENDING_REVIEW")
        self.assertEqual(item["canonical_proposed_values"],{"start_local":"2026-09-11"})
        self.assertEqual(item["observation_count"],1)
        self.assertEqual(proposal["previous_checkpoint_sha256"],checkpoint_sha256(self.checkpoint))

    def test_same_proposition_after_checkpoint_updates_not_duplicates(self):
        first=self.proposal(self.checkpoint,[{
            "run_number":48,"run_id":"48","run_at":"2026-09-04T01:00:00+00:00","candidates":[self.candidate]
        }])
        repeated=json.loads(json.dumps(self.candidate))
        repeated["candidate_id"]="WSRC-BBB"
        second=self.proposal(first,[{
            "run_number":49,"run_id":"49","run_at":"2026-09-04T07:00:00+00:00","candidates":[repeated]
        }],generated="2026-09-04T07:05:00+00:00")
        self.assertEqual(second["item_count"],1)
        item=second["items"][0]
        self.assertEqual(item["observation_count"],2)
        self.assertEqual(item["candidate_ids"],["WSRC-AAA","WSRC-BBB"])
        self.assertEqual(item["first_run_number"],48)
        self.assertEqual(item["last_run_number"],49)

    def test_absent_item_persists_while_checkpoint_advances(self):
        first=self.proposal(self.checkpoint,[{
            "run_number":48,"run_id":"48","run_at":"2026-09-04T01:00:00+00:00","candidates":[self.candidate]
        }])
        second=self.proposal(first,[{
            "run_number":49,"run_id":"49","run_at":"2026-09-04T07:00:00+00:00","candidates":[]
        }],generated="2026-09-04T07:05:00+00:00")
        self.assertEqual(second["covered_through_monitor_run_number"],49)
        self.assertEqual(second["item_count"],1)
        self.assertEqual(second["items"][0]["last_run_number"],48)
        self.assertEqual(second["items"][0]["state"],"PENDING_REVIEW")

    def test_manual_decision_applies_even_without_reobservation(self):
        first=self.proposal(self.checkpoint,[{
            "run_number":48,"run_id":"48","run_at":"2026-09-04T01:00:00+00:00","candidates":[self.candidate]
        }])
        review_item_id=first["items"][0]["review_item_id"]
        decisions={"decisions":[{
            "review_item_id":review_item_id,
            "decision_state":"REJECTED",
            "decided_at":"2026-09-04T04:00:00+00:00",
        }]}
        second=self.proposal(first,[{
            "run_number":49,"run_id":"49","run_at":"2026-09-04T07:00:00+00:00","candidates":[]
        }],decisions=decisions,generated="2026-09-04T07:05:00+00:00")
        self.assertEqual(second["items"][0]["state"],"REJECTED")
        self.assertEqual(second["items"][0]["last_decision_state"],"REJECTED")

    def test_canonical_alignment_after_original_artifact_can_be_reconciled_from_checkpoint_private_state(self):
        first=self.proposal(self.checkpoint,[{
            "run_number":48,"run_id":"48","run_at":"2026-09-04T01:00:00+00:00","candidates":[self.candidate]
        }])
        aligned=[dict(self.canonical[0],start_local="2026-09-11")]
        second=self.proposal(first,[],canonical=aligned,generated="2026-09-05T00:00:00+00:00")
        item=second["items"][0]
        self.assertEqual(item["state"],"CANONICAL_ALIGNMENT_REQUIRES_RECONCILIATION")
        self.assertEqual(item["canonical_alignment_state"],"ALIGNED_WITH_CANONICAL_NO_REVIEW_LEDGER_LINK")

    def test_reviewed_ledger_link_marks_checkpoint_item_committed(self):
        first=self.proposal(self.checkpoint,[{
            "run_number":48,"run_id":"48","run_at":"2026-09-04T01:00:00+00:00","candidates":[self.candidate]
        }])
        review_item_id=first["items"][0]["review_item_id"]
        ledger={"changes":[{"change_id":"WSCHANGE-TEST","origin_review_item_id":review_item_id,"origin_candidate_ids":["WSRC-AAA"]}]}
        committed=self.proposal(first,[],ledger=ledger,generated="2026-09-05T00:00:00+00:00")
        self.assertEqual(committed["items"][0]["state"],"COMMITTED")
        self.assertEqual(committed["items"][0]["canonical_alignment_state"],"COMMITTED_WITH_REVIEW_LEDGER_LINK")

    def test_opaque_rule_state_is_not_persisted_in_checkpoint(self):
        legal={
            "candidate_id":"WSRC-LEGAL-A",
            "candidate_type":"LEGAL_STATE_TOPOLOGY_CHANGED",
            "source_id":"WSSRC-LEGAL-001",
            "occurrence_ids":["WSO-TEST-001"],
            "old_value":{"topology":{"raw":"old"}},
            "new_value":{"topology":{"raw":"new"},"rows":[{"body":"secret"}]},
            "review_state":"PENDING_REVIEW",
            "automatic_commit_allowed":False,
        }
        proposal=self.proposal(self.checkpoint,[{
            "run_number":48,"run_id":"48","run_at":"2026-09-04T01:00:00+00:00","candidates":[legal]
        }])
        item=proposal["items"][0]
        self.assertEqual(item["identity_mode"],"OPAQUE_RULE_PROPOSITION")
        self.assertIsNone(item["canonical_proposed_values"])
        serialized=json.dumps(proposal)
        self.assertNotIn("secret",serialized)
        self.assertNotIn('"old_value"',serialized)
        self.assertNotIn('"new_value"',serialized)

    def test_public_projection_strips_checkpoint_private_values(self):
        proposal=self.proposal(self.checkpoint,[{
            "run_number":48,"run_id":"48","run_at":"2026-09-04T01:00:00+00:00","candidates":[self.candidate]
        }])
        public=checkpoint_public_projection(proposal,REVIEW_CONTRACT,CHECKPOINT_CONTRACT)
        serialized=json.dumps(public)
        self.assertNotIn("canonical_proposed_values",serialized)
        self.assertNotIn("2026-09-11",serialized)
        self.assertEqual(public["item_count"],1)

    def test_checkpoint_delta_cannot_reconsume_covered_run(self):
        with self.assertRaises(ValueError):
            self.proposal(self.checkpoint,[{
                "run_number":47,"run_id":"47","run_at":"2026-09-03T12:23:29+00:00","candidates":[self.candidate]
            }])

    def test_checkpoint_rejects_prohibited_or_unexpected_item_state(self):
        proposal=self.proposal(self.checkpoint,[{
            "run_number":48,"run_id":"48","run_at":"2026-09-04T01:00:00+00:00","candidates":[self.candidate]
        }])
        proposal["items"][0]["raw"]="forbidden"
        with self.assertRaises(ValueError):
            validate_checkpoint(proposal,CHECKPOINT_CONTRACT)

    def test_review_item_identity_is_unchanged_by_checkpoint_layer(self):
        expected=proposition_identity(self.candidate)["review_item_id"]
        proposal=self.proposal(self.checkpoint,[{
            "run_number":48,"run_id":"48","run_at":"2026-09-04T01:00:00+00:00","candidates":[self.candidate]
        }])
        self.assertEqual(proposal["items"][0]["review_item_id"],expected)


if __name__=="__main__":
    unittest.main()
