from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
POLICY=ROOT/"data/monitor/operations_policy.json"
WORKFLOW=ROOT/".github/workflows/live-monitor.yml"


class MonitorOperationsPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy=json.loads(POLICY.read_text(encoding="utf-8"))
        cls.workflow=WORKFLOW.read_text(encoding="utf-8")

    def test_architecture_boundary_is_read_only(self):
        boundary=self.policy["architecture_boundary"]
        self.assertTrue(boundary["canonical_registry_is_authoritative"])
        self.assertFalse(boundary["source_monitor_may_mutate_canonical"])
        self.assertFalse(boundary["browser_may_mutate_canonical"])
        self.assertFalse(boundary["google_calendar_write_allowed"])

    def test_auto_commit_gate_remains_closed(self):
        gate=self.policy["canonical_auto_commit_gate"]
        self.assertEqual(gate["state"],"CLOSED")
        self.assertEqual(len(gate["remaining_real_world_evidence"]),2)
        self.assertFalse(self.policy["review_candidate_lifecycle"]["automatic_commit_allowed"])

    def test_source_failure_cannot_be_event_state(self):
        rules=set(self.policy["source_health"]["rules"])
        self.assertIn("SOURCE_HEALTH_STATE_IS_INDEPENDENT_OF_EVENT_STATE",rules)
        self.assertIn("FETCH_FAILURE_DOES_NOT_IMPLY_CANCELLATION",rules)
        self.assertIn("ABSENCE_DOES_NOT_IMPLY_CANCELLATION_OR_COMPLETION",rules)
        invariants=set(self.policy["safety_invariants"])
        self.assertIn("SOURCE_FAILURE_CANNOT_CREATE_EVENT_CANCELLATION",invariants)
        self.assertIn("SOURCE_FAILURE_CANNOT_CREATE_EVENT_COMPLETION",invariants)
        self.assertIn("SOURCE_FAILURE_CANNOT_CREATE_EVENT_RESCHEDULE",invariants)

    def test_evidence_contract_requires_configuration_identity(self):
        fields=set(self.policy["evidence"]["required_run_identity_fields"])
        self.assertIn("canonical_sha256_before",fields)
        self.assertIn("canonical_sha256_after",fields)
        self.assertIn("monitor_operations_policy_version",fields)
        self.assertIn("monitor_operations_policy_sha256",fields)
        self.assertIn("configuration_fingerprint_sha256",fields)
        self.assertEqual(self.policy["evidence"]["artifact_retention_days"],90)

    def test_workflow_matches_policy_safety_controls(self):
        self.assertIn("contents: read",self.workflow)
        self.assertIn("group: world-signals-live-monitor",self.workflow)
        self.assertIn("cancel-in-progress: false",self.workflow)
        self.assertIn("timeout-minutes: 12",self.workflow)
        self.assertIn("retention-days: 90",self.workflow)

    def test_temporary_write_workflow_rule_is_explicit(self):
        promotion=self.policy["promotion_policy"]
        self.assertTrue(promotion["temporary_write_capable_promotion_workflows_must_be_removed_after_success"])
        self.assertTrue(promotion["pilot_validation_does_not_open_auto_commit"])


if __name__=="__main__":
    unittest.main()
