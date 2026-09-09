import json
import unittest

from world_signals.adapters.base import AdapterError
from world_signals.adapters.hmt_t1_content_api import (
    HMT_T1_BASE_PATH,
    HMT_T1_CONTENT_ID,
    HMT_T1_TITLE,
    parse_hmt_t1_content_api,
)


def payload(*, updated="2025-11-20T09:30:10+00:00", body_suffix="", withdrawn=None):
    body = " ".join([
        "This is a draft SI and should not be treated as final",
        "HM Treasury intends to lay the final SI",
        "subject to the affirmative procedure",
        "approved by both Houses of Parliament",
        "11 October 2027",
        body_suffix,
    ])
    return json.dumps({
        "content_id": HMT_T1_CONTENT_ID,
        "base_path": HMT_T1_BASE_PATH,
        "title": HMT_T1_TITLE,
        "document_type": "html_publication",
        "schema_name": "html_publication",
        "first_published_at": "2025-11-20T09:30:10+00:00",
        "public_updated_at": updated,
        "withdrawn_notice": withdrawn,
        "details": {"body": body},
    })


class HMTT1ContentAPICC(unittest.TestCase):
    def test_baseline_contract(self):
        state = parse_hmt_t1_content_api(payload())
        self.assertEqual(state.content_id, HMT_T1_CONTENT_ID)
        self.assertFalse(state.withdrawn)
        self.assertTrue(all(state.pending_markers.values()))
        self.assertEqual(len(state.semantic_sha256), 64)

    def test_nonsemantic_body_edit_does_not_change_semantic_hash(self):
        left = parse_hmt_t1_content_api(payload(body_suffix="Editorial A"))
        right = parse_hmt_t1_content_api(payload(body_suffix="Editorial B"))
        self.assertEqual(left.semantic_sha256, right.semantic_sha256)

    def test_public_revision_is_retained(self):
        state = parse_hmt_t1_content_api(payload(updated="2026-09-09T08:00:00+00:00"))
        self.assertEqual(state.public_updated_at, "2026-09-09T08:00:00+00:00")

    def test_identity_drift_fails_closed(self):
        doc = json.loads(payload())
        doc["content_id"] = "different"
        with self.assertRaises(AdapterError):
            parse_hmt_t1_content_api(json.dumps(doc))

    def test_missing_pending_marker_is_observable_not_parser_failure(self):
        doc = json.loads(payload())
        doc["details"]["body"] = doc["details"]["body"].replace(
            "This is a draft SI and should not be treated as final", ""
        )
        state = parse_hmt_t1_content_api(json.dumps(doc))
        self.assertFalse(state.pending_markers["draft_not_final"])

    def test_bad_timestamp_fails_closed(self):
        doc = json.loads(payload())
        doc["public_updated_at"] = "not-a-time"
        with self.assertRaises(AdapterError):
            parse_hmt_t1_content_api(json.dumps(doc))


if __name__ == "__main__":
    unittest.main()
