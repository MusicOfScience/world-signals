import unittest

from world_signals.adapters.hmt_t1_content_api import HMTT1ContentState
from world_signals.hmt_t1_monitor import hmt_t1_dependency_review_candidate


def canonical():
    return [{
        "occurrence_id": "WSO-MKT-A-0016",
        "series_id": "WSER-MKT-UK-T1",
        "source_id": "WSSRC-MKT-012",
        "category": "CORPORATE_FINANCIAL_MARKET_STRUCTURE",
        "activation_mode": "CONDITIONAL",
        "certainty_status": "PROVISIONAL",
        "condition_state": "PENDING_DEPENDENCY",
        "start_local": "2027-10-11",
        "time_status": "PROVISIONAL",
        "timing_type": "JURISDICTIONAL_CIVIL_DATE",
    }]


def config():
    return {
        "adapter_id": "HMT_T1_CONTENT_API",
        "source_id": "WSSRC-MKT-014",
        "canonical_occurrence_ids": ["WSO-MKT-A-0016"],
        "baseline_public_updated_at": "2025-11-20T09:30:10+00:00",
        "schedule_authority": False,
        "clock_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "condition_state_authority": False,
        "canonical_datetime_mutation_allowed": False,
        "automatic_attachment_fetch_allowed": False,
        "automatic_parent_page_fetch_allowed": False,
        "automatic_legislation_followup_allowed": False,
        "automatic_new_occurrence_creation_allowed": False,
        "automatic_live_or_analysis_promotion_allowed": False,
        "automatic_commit_allowed": False,
    }


def state(*, updated="2025-11-20T09:30:10+00:00", withdrawn=False, markers=None):
    if markers is None:
        markers = {
            "draft_not_final": True,
            "intends_lay_final": True,
            "affirmative_procedure": True,
            "both_houses": True,
            "implementation_date": True,
        }
    return HMTT1ContentState(
        content_id="b6b2d2f2-eae6-4564-9ed1-338abb8ca2f2",
        base_path="/government/publications/accelerated-settlement-t1/policy-note-mandating-t1-settlement-in-the-uk",
        title="Policy note – Mandating T+1 settlement in the UK",
        document_type="html_publication",
        schema_name="html_publication",
        first_published_at="2025-11-20T09:30:10+00:00",
        public_updated_at=updated,
        withdrawn=withdrawn,
        pending_markers=markers,
        semantic_sha256="a" * 64,
    )


class HMTT1MonitorCC(unittest.TestCase):
    def test_unchanged_pending_state_is_observation_only(self):
        candidate, observation = hmt_t1_dependency_review_candidate(canonical(), state(), config())
        self.assertIsNone(candidate)
        self.assertEqual(observation["event_state_inference"], "NONE")
        self.assertEqual(observation["condition_state_inference"], "NONE")
        self.assertFalse(observation["automatic_commit_allowed"])

    def test_public_revision_generates_manual_review_only(self):
        candidate, observation = hmt_t1_dependency_review_candidate(
            canonical(), state(updated="2026-09-09T08:00:00+00:00"), config()
        )
        self.assertEqual(candidate["candidate_type"], "HMT_T1_LEGISLATIVE_DEPENDENCY_REVIEW")
        self.assertEqual(candidate["review_state"], "PENDING_AUTHORITATIVE_UK_LEGISLATION_VERIFICATION")
        self.assertEqual(candidate["event_state_inference"], "NONE")
        self.assertEqual(candidate["condition_state_inference"], "NONE")
        self.assertFalse(candidate["canonical_datetime_mutation_allowed"])
        self.assertFalse(candidate["automatic_commit_allowed"])
        self.assertEqual(observation["legal_completion_inference"], "NONE")

    def test_withdrawal_generates_review_not_cancellation(self):
        candidate, _ = hmt_t1_dependency_review_candidate(canonical(), state(withdrawn=True), config())
        self.assertTrue(candidate["new_value"]["withdrawn"])
        self.assertEqual(candidate["event_state_inference"], "NONE")

    def test_missing_pending_marker_generates_review(self):
        markers = state().pending_markers.copy()
        markers["draft_not_final"] = False
        candidate, _ = hmt_t1_dependency_review_candidate(canonical(), state(markers=markers), config())
        self.assertIsNotNone(candidate)
        self.assertFalse(candidate["new_value"]["pending_markers"]["draft_not_final"])

    def test_authority_gate_true_fails_closed(self):
        bad = config()
        bad["condition_state_authority"] = True
        with self.assertRaises(ValueError):
            hmt_t1_dependency_review_candidate(canonical(), state(), bad)

    def test_canonical_scope_drift_fails_closed(self):
        rows = canonical()
        rows[0]["certainty_status"] = "CONFIRMED"
        with self.assertRaises(ValueError):
            hmt_t1_dependency_review_candidate(rows, state(), config())


if __name__ == "__main__":
    unittest.main()
