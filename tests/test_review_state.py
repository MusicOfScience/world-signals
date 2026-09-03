import json
from pathlib import Path
import unittest

from src.world_signals.review_state import proposition_identity, reduce_review_state


ROOT=Path(__file__).resolve().parents[1]
CONTRACT=json.loads((ROOT/"data/monitor/review_candidate_state_contract.json").read_text(encoding="utf-8"))


class ReviewStateTests(unittest.TestCase):
    def setUp(self):
        self.canonical=[
            {
                "occurrence_id":"WSO-TEST-001",
                "start_local":"2026-09-10",
                "end_local":None,
                "certainty_status":"CONFIRMED",
                "lifecycle_status":"PLANNED",
            }
        ]
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
            "source_assertion":{"source_id":"WSSRC-TEST-001","source_url":"https://example.invalid/raw"},
            "review_state":"PENDING_REVIEW",
            "automatic_commit_allowed":False,
        }
        self.empty_decisions={"decisions":[]}
        self.empty_ledger={"changes":[]}

    def reduce(self,runs,decisions=None,ledger=None,canonical=None):
        return reduce_review_state(
            runs,
            canonical_records=self.canonical if canonical is None else canonical,
            decisions=self.empty_decisions if decisions is None else decisions,
            change_ledger=self.empty_ledger if ledger is None else ledger,
            contract=CONTRACT,
            generated_at="2026-09-04T00:00:00+00:00",
        )

    def test_identical_proposition_aggregates_across_candidate_ids(self):
        repeat=dict(self.candidate,candidate_id="WSRC-BBB")
        state=self.reduce([
            {"run_number":48,"run_id":"48","run_at":"2026-09-04T01:00:00+00:00","candidates":[self.candidate]},
            {"run_number":49,"run_id":"49","run_at":"2026-09-04T07:00:00+00:00","candidates":[repeat]},
        ])
        self.assertEqual(state["item_count"],1)
        item=state["items"][0]
        self.assertTrue(item["review_item_id"].startswith("WSRV-"))
        self.assertEqual(item["observation_count"],2)
        self.assertEqual(item["candidate_ids"],["WSRC-AAA","WSRC-BBB"])
        self.assertEqual(item["first_run_number"],48)
        self.assertEqual(item["last_run_number"],49)
        self.assertEqual(item["state"],"PENDING_REVIEW")
        self.assertFalse(item["automatic_commit_allowed"])

    def test_materially_different_proposition_becomes_sibling(self):
        revised=json.loads(json.dumps(self.candidate))
        revised["candidate_id"]="WSRC-CCC"
        revised["new_value"]["start_local"]="2026-09-12"
        state=self.reduce([
            {"run_number":48,"run_id":"48","run_at":"2026-09-04T01:00:00+00:00","candidates":[self.candidate]},
            {"run_number":49,"run_id":"49","run_at":"2026-09-04T07:00:00+00:00","candidates":[revised]},
        ])
        self.assertEqual(state["item_count"],2)
        self.assertEqual(len({item["review_item_id"] for item in state["items"]}),2)

    def test_absence_from_later_run_does_not_resolve_item(self):
        state=self.reduce([
            {"run_number":48,"run_id":"48","run_at":"2026-09-04T01:00:00+00:00","candidates":[self.candidate]},
            {"run_number":49,"run_id":"49","run_at":"2026-09-04T07:00:00+00:00","candidates":[]},
        ])
        self.assertEqual(state["run_count_considered"],2)
        self.assertEqual(state["item_count"],1)
        self.assertEqual(state["items"][0]["state"],"PENDING_REVIEW")
        self.assertEqual(state["items"][0]["last_run_number"],48)

    def test_rejected_item_does_not_reopen_when_reobserved(self):
        review_item_id=proposition_identity(self.candidate)["review_item_id"]
        decisions={"decisions":[{
            "review_item_id":review_item_id,
            "decision_state":"REJECTED",
            "decided_at":"2026-09-04T04:00:00+00:00",
        }]}
        state=self.reduce([
            {"run_number":48,"run_id":"48","run_at":"2026-09-04T01:00:00+00:00","candidates":[self.candidate]},
            {"run_number":49,"run_id":"49","run_at":"2026-09-04T07:00:00+00:00","candidates":[self.candidate]},
        ],decisions=decisions)
        item=state["items"][0]
        self.assertEqual(item["state"],"REJECTED")
        self.assertEqual(item["last_decision_state"],"REJECTED")
        self.assertTrue(item["reobserved_after_decision"])

    def test_canonical_alignment_without_review_ledger_link_requires_reconciliation(self):
        canonical=[dict(self.canonical[0],start_local="2026-09-11")]
        state=self.reduce([
            {"run_number":48,"run_id":"48","run_at":"2026-09-04T01:00:00+00:00","candidates":[self.candidate]},
        ],canonical=canonical)
        item=state["items"][0]
        self.assertEqual(item["state"],"CANONICAL_ALIGNMENT_REQUIRES_RECONCILIATION")
        self.assertEqual(item["canonical_alignment_state"],"ALIGNED_WITH_CANONICAL_NO_REVIEW_LEDGER_LINK")

    def test_review_ledger_link_marks_item_committed(self):
        review_item_id=proposition_identity(self.candidate)["review_item_id"]
        canonical=[dict(self.canonical[0],start_local="2026-09-11")]
        ledger={"changes":[{
            "change_id":"WSCHANGE-TEST",
            "origin_review_item_id":review_item_id,
            "origin_candidate_ids":["WSRC-AAA"],
        }]}
        state=self.reduce([
            {"run_number":48,"run_id":"48","run_at":"2026-09-04T01:00:00+00:00","candidates":[self.candidate]},
        ],ledger=ledger,canonical=canonical)
        item=state["items"][0]
        self.assertEqual(item["state"],"COMMITTED")
        self.assertEqual(item["canonical_alignment_state"],"COMMITTED_WITH_REVIEW_LEDGER_LINK")

    def test_opaque_legal_candidate_hashes_rule_state_without_public_payload(self):
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
        repeat=json.loads(json.dumps(legal))
        repeat["candidate_id"]="WSRC-LEGAL-B"
        state=self.reduce([
            {"run_number":48,"run_id":"48","run_at":"2026-09-04T01:00:00+00:00","candidates":[legal]},
            {"run_number":49,"run_id":"49","run_at":"2026-09-04T07:00:00+00:00","candidates":[repeat]},
        ])
        item=state["items"][0]
        self.assertEqual(item["identity_mode"],"OPAQUE_RULE_PROPOSITION")
        self.assertEqual(item["proposed_change_fields"],["OPAQUE_RULE_STATE"])
        serialized=json.dumps(item)
        self.assertNotIn("secret",serialized)
        self.assertNotIn('"old_value"',serialized)
        self.assertNotIn('"new_value"',serialized)
        self.assertEqual(item["observation_count"],2)

    def test_candidate_must_explicitly_prohibit_automatic_commit(self):
        bad=dict(self.candidate,automatic_commit_allowed=True)
        with self.assertRaises(ValueError):
            proposition_identity(bad)

    def test_pre_contract_run_is_excluded(self):
        state=self.reduce([
            {"run_number":47,"run_id":"47","run_at":"2026-09-03T12:00:00+00:00","candidates":[self.candidate]},
        ])
        self.assertEqual(state["run_count_considered"],0)
        self.assertEqual(state["item_count"],0)


if __name__=="__main__":
    unittest.main()
