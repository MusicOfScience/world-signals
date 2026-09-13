import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import scripts.run_local_operations as local_runner
import scripts.run_live_monitor as live_monitor

from src.world_signals.local_operations import (
    LOCAL_RUN_NUMBER_OFFSET,
    archive_local_run,
    build_public_projections,
    path_fingerprints,
    safe_candidate_path,
)


ROOT = Path(__file__).resolve().parents[1]


class LocalOperationsCSTests(unittest.TestCase):
    def candidate(self):
        return {
            "candidate_id": "WSRC-LOCAL-TEST",
            "candidate_type": "DATE_OR_TIME_CHANGED",
            "source_id": "WSSRC-TEST-001",
            "occurrence_ids": ["WSO-MAC-A-0001"],
            "old_value": {"start_local": "2026-09-01"},
            "new_value": {"start_local": "2026-09-02"},
            "review_state": "PENDING_REVIEW",
            "candidate_origin": "LIVE_READ_ONLY_MONITOR",
            "automatic_commit_allowed": False,
        }

    def report(self):
        return {
            "report_schema_version": "0.3",
            "run_at": "2026-09-13T07:00:00+00:00",
            "status": "REVIEW_REQUIRED",
            "workflow_context": {
                "execution_mode": "LOCAL",
                "run_id": "LOCAL-00000001-20260913T070000Z",
                "run_number": str(LOCAL_RUN_NUMBER_OFFSET + 1),
                "head_sha": "abc123",
                "github_run_id": None,
                "github_sha": None,
            },
            "canonical_registry_version": "0.43",
            "source_registry_version": "2.04",
            "monitor_expectations_version": "0.28",
            "monitor_operations_policy_version": "0.1",
            "configuration_fingerprint_sha256": "f" * 64,
            "canonical_unchanged": True,
            "automatic_canonical_commit": False,
            "google_calendar_write": False,
            "candidate_count": 1,
            "source_health_summary": {
                "healthy": 1,
                "degraded": 0,
                "all_expected_adapters_observed": True,
            },
            "source_health": [
                {"adapter_id": "TEST", "source_id": "WSSRC-TEST-001", "state": "HEALTHY"}
            ],
        }

    def test_candidate_paths_are_bounded(self):
        self.assertEqual(
            safe_candidate_path("review_candidates/live/WSRC-1.json"),
            Path("review_candidates/live/WSRC-1.json"),
        )
        for unsafe in ("../secret.json", "/tmp/secret.json", "review_candidates/other/x.json"):
            with self.assertRaises(ValueError):
                safe_candidate_path(unsafe)

    def test_local_archive_and_public_projections_are_read_only_and_sanitized(self):
        with TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            state_root = Path(temporary) / "state"
            workspace.mkdir()
            for relative in ("data/canonical", "data/sources", "data/changes", "data/monitor"):
                (workspace / relative).mkdir(parents=True, exist_ok=True)
            for source, target in (
                (ROOT / "data/canonical/registry.json", workspace / "data/canonical/registry.json"),
                (ROOT / "data/sources/registry.json", workspace / "data/sources/registry.json"),
                (ROOT / "data/changes/ledger.json", workspace / "data/changes/ledger.json"),
                (ROOT / "data/monitor/expectations.json", workspace / "data/monitor/expectations.json"),
                (ROOT / "data/monitor/operations_policy.json", workspace / "data/monitor/operations_policy.json"),
                (ROOT / "data/monitor/review_candidate_state_contract.json", workspace / "data/monitor/review_candidate_state_contract.json"),
                (ROOT / "data/monitor/review_decisions.json", workspace / "data/monitor/review_decisions.json"),
                (ROOT / "data/monitor/public_runtime_projection_contract.json", workspace / "data/monitor/public_runtime_projection_contract.json"),
            ):
                target.write_bytes(source.read_bytes())
            (workspace / "artifacts").mkdir()
            (workspace / "review_candidates/live").mkdir(parents=True)
            candidate = self.candidate()
            report = self.report()
            manifest = {
                "candidate_count": 1,
                "files": ["review_candidates/live/WSRC-LOCAL-TEST.json"],
                "automatic_canonical_commit": False,
            }
            (workspace / "artifacts/live-monitor.json").write_text(json.dumps(report))
            (workspace / "review_candidates/live/manifest.json").write_text(json.dumps(manifest))
            (workspace / "review_candidates/live/WSRC-LOCAL-TEST.json").write_text(json.dumps(candidate))

            archive_local_run(
                workspace,
                state_root,
                sequence=1,
                run_id="LOCAL-00000001-20260913T070000Z",
                run_number=LOCAL_RUN_NUMBER_OFFSET + 1,
                report=report,
                manifest=manifest,
                candidates=[candidate],
            )
            runtime, review = build_public_projections(
                workspace,
                state_root,
                report=report,
                manifest=manifest,
                candidates=[candidate],
            )
            self.assertEqual(runtime["execution_mode"], "LOCAL")
            self.assertEqual(runtime["run_id"], "LOCAL-00000001-20260913T070000Z")
            self.assertEqual(runtime["head_sha"], "abc123")
            self.assertEqual(review["availability"], "AVAILABLE_LOCAL_HORIZON")
            self.assertEqual(review["item_count"], 1)
            serialized = json.dumps({"runtime": runtime, "review": review})
            self.assertNotIn('"old_value"', serialized)
            self.assertNotIn('"new_value"', serialized)

    def test_protected_fingerprints_cover_governed_layers_and_opec(self):
        fingerprints = path_fingerprints(ROOT)
        self.assertIn("OPEC_QUARANTINE.md", fingerprints)
        self.assertIn("data/canonical/registry.json", fingerprints)
        self.assertIn("data/sources/registry.json", fingerprints)
        self.assertIn("data/monitor/expectations.json", fingerprints)
        self.assertIn("data/live_intelligence/observations.json", fingerprints)
        self.assertIn("data/analysis/event_reviews.json", fingerprints)
        self.assertIn("data/coverage/biosecurity_overlay.json", fingerprints)

    def test_repository_local_state_is_confined_to_ignored_runtime_root(self):
        local_runner.validate_state_root(ROOT / ".world-signals-runtime" / "custom")
        with self.assertRaises(ValueError):
            local_runner.validate_state_root(ROOT / "data" / "monitor" / "unsafe-state")

    def test_live_monitor_uses_generic_local_execution_identity(self):
        local_environment = {
            "WORLD_SIGNALS_EXECUTION_MODE": "LOCAL",
            "WORLD_SIGNALS_RUN_ID": "LOCAL-00000001-20260913T070000Z",
            "WORLD_SIGNALS_RUN_NUMBER": str(LOCAL_RUN_NUMBER_OFFSET + 1),
            "WORLD_SIGNALS_GIT_SHA": "abc123",
        }
        with patch.dict(os.environ, local_environment, clear=True):
            context = live_monitor.workflow_context()
        self.assertEqual(context["execution_mode"], "LOCAL")
        self.assertEqual(context["run_id"], local_environment["WORLD_SIGNALS_RUN_ID"])
        self.assertEqual(context["run_number"], local_environment["WORLD_SIGNALS_RUN_NUMBER"])
        self.assertEqual(context["head_sha"], "abc123")
        self.assertIsNone(context["github_run_id"])

    def test_public_contract_and_browser_support_generic_local_identity(self):
        contract = json.loads(
            (ROOT / "data/monitor/public_runtime_projection_contract.json").read_text(encoding="utf-8")
        )
        self.assertEqual(contract["version"], "0.2")
        allowed = set(contract["allowed_runtime_fields"])
        self.assertTrue({"execution_mode", "run_id", "head_sha"}.issubset(allowed))
        browser = (ROOT / "web/operations.js").read_text(encoding="utf-8")
        self.assertIn("Local run", browser)
        self.assertIn("AVAILABLE_LOCAL_HORIZON", browser)


if __name__ == "__main__":
    unittest.main()
