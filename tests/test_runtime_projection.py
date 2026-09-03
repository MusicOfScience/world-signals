import unittest

from src.world_signals.runtime_projection import (
    prohibited_field_hits,
    public_runtime_projection,
    unavailable_runtime_projection,
)


class RuntimeProjectionTests(unittest.TestCase):
    def setUp(self):
        self.current={
            "canonical_registry_version":"0.20",
            "source_registry_version":"1.51",
            "monitor_expectations_version":"0.6",
            "monitor_operations_policy_version":"0.1",
        }
        self.report={
            "report_schema_version":"0.3",
            "run_at":"2026-09-03T18:00:00+00:00",
            "status":"REVIEW_REQUIRED",
            "workflow_context":{"github_run_id":"123","github_sha":"abc"},
            "canonical_registry_version":"0.19",
            "source_registry_version":"1.50",
            "monitor_expectations_version":"0.6",
            "monitor_operations_policy_version":"0.1",
            "configuration_fingerprint_sha256":"f"*64,
            "canonical_unchanged":True,
            "automatic_canonical_commit":False,
            "google_calendar_write":False,
            "candidate_count":1,
            "source_health_summary":{
                "healthy":5,
                "degraded":1,
                "all_expected_adapters_observed":True,
            },
            "source_health":[
                {
                    "adapter_id":"TEST_ADAPTER",
                    "source_id":"WSSRC-TEST-001",
                    "state":"DEGRADED",
                    "error":"sensitive parser detail must not leak",
                    "snapshot":{"body":"raw source content"},
                    "layers":{
                        "semantic":{"state":"HEALTHY","snapshot":{"raw":"x"}},
                        "topology":{"state":"DEGRADED","failure_stage":"PARSE","error":"raw"},
                    },
                }
            ],
            "observations":[{"raw":"must not leak"}],
        }
        self.manifest={
            "candidate_count":1,
            "automatic_canonical_commit":False,
            "files":["review_candidates/live/WSRC-1.json"],
        }
        self.candidate={
            "candidate_id":"WSRC-1",
            "candidate_type":"DATE_OR_TIME_CHANGED",
            "source_id":"WSSRC-TEST-001",
            "occurrence_ids":["WSO-TEST-001"],
            "old_value":{"start_local":"2026-09-10"},
            "new_value":{"start_local":"2026-09-11"},
            "source_assertion":{"source_url":"https://example.invalid/raw"},
            "review_state":"PENDING_REVIEW",
            "candidate_origin":"LIVE_READ_ONLY_MONITOR",
            "automatic_commit_allowed":False,
        }

    def test_sanitizer_removes_raw_evidence_payloads(self):
        projection=public_runtime_projection(self.report,self.manifest,[self.candidate],self.current)
        prohibited={"snapshot","error","old_value","new_value","source_assertion","observations","rule","topology","rows","body","raw"}
        self.assertEqual(prohibited_field_hits(projection,prohibited),[])
        self.assertEqual(projection["candidate_count"],1)
        self.assertEqual(projection["candidates"][0]["changed_fields"],["start_local"])
        self.assertEqual(projection["source_health"][0]["state"],"DEGRADED")
        self.assertEqual(projection["source_health"][0]["layer_states"][1]["failure_stage"],"PARSE")

    def test_stale_runtime_configuration_is_explicit(self):
        projection=public_runtime_projection(self.report,self.manifest,[self.candidate],self.current)
        alignment=projection["configuration_alignment"]
        self.assertEqual(alignment["state"],"STALE_RELATIVE_TO_CURRENT_SITE")
        self.assertFalse(alignment["fields"]["canonical_registry_version"]["matches"])
        self.assertFalse(alignment["fields"]["source_registry_version"]["matches"])
        self.assertTrue(alignment["fields"]["monitor_expectations_version"]["matches"])

    def test_canonical_guard_failure_cannot_be_published_as_runtime_snapshot(self):
        self.report["canonical_unchanged"]=False
        with self.assertRaises(ValueError):
            public_runtime_projection(self.report,self.manifest,[self.candidate],self.current)

    def test_candidate_must_explicitly_forbid_automatic_commit(self):
        self.candidate["automatic_commit_allowed"]=True
        with self.assertRaises(ValueError):
            public_runtime_projection(self.report,self.manifest,[self.candidate],self.current)

    def test_unavailable_projection_still_preserves_safety_boundary(self):
        projection=unavailable_runtime_projection("NO_ARTIFACT",self.current)
        self.assertEqual(projection["availability"],"UNAVAILABLE_AT_BUILD")
        self.assertFalse(projection["automatic_canonical_commit"])
        self.assertFalse(projection["google_calendar_write"])
        self.assertEqual(projection["source_health"],[])
        self.assertEqual(projection["candidates"],[])


if __name__=="__main__":
    unittest.main()
