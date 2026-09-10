from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_world_signals.py"

spec = importlib.util.spec_from_file_location("validate_world_signals", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ValidationProfileContractTests(unittest.TestCase):
    def test_only_named_data_research_markdown_is_fast_path_eligible(self):
        self.assertTrue(
            module.is_safe_research_markdown(
                "data/coverage/POST_CP_PRESSURE_CQ_v0.2.md"
            )
        )
        self.assertTrue(
            module.is_safe_research_markdown(
                "data/live_intelligence/FOO_TRANSACTION_AUDIT_v0.1.md"
            )
        )
        self.assertFalse(module.is_safe_research_markdown("data/coverage/notes.md"))
        self.assertFalse(module.is_safe_research_markdown("HANDOFF_PROTOCOL.md"))
        self.assertFalse(
            module.is_safe_research_markdown("data/coverage/biosecurity_overlay.json")
        )

    def test_safe_research_classifier_is_fail_closed(self):
        safe_rows = [
            ("A", ["data/coverage/FOO_RESEARCH_v0.1.md"]),
            ("A", ["data/analysis/BAR_PRESSURE_v0.2.md"]),
        ]
        with mock.patch.object(module, "changed_entries", return_value=safe_rows), mock.patch.object(
            module, "verify_safe_research_surface", return_value=[row[1][0] for row in safe_rows]
        ):
            self.assertEqual(
                module.classify_pull_request("BASE", "HEAD"),
                "SAFE_RESEARCH_DOCS",
            )

        with mock.patch.object(
            module,
            "changed_entries",
            return_value=[("M", ["scripts/build_site.py"])],
        ), mock.patch.object(
            module,
            "verify_safe_research_surface",
            side_effect=module.ValidationError("not safe"),
        ):
            self.assertEqual(module.classify_pull_request("BASE", "HEAD"), "FULL")

    def test_modification_deletion_rename_and_unknown_paths_cannot_use_fast_path(self):
        for rows in (
            [("M", ["data/coverage/FOO_RESEARCH_v0.1.md"])],
            [("D", ["data/coverage/FOO_RESEARCH_v0.1.md"])],
            [("R100", ["data/coverage/OLD_RESEARCH_v0.1.md", "data/coverage/NEW_RESEARCH_v0.1.md"])],
            [("A", ["data/coverage/ordinary-notes.md"])],
        ):
            with self.subTest(rows=rows), mock.patch.object(
                module, "changed_entries", return_value=rows
            ), mock.patch.object(
                module,
                "verify_safe_research_surface",
                side_effect=module.ValidationError("not safe"),
            ):
                self.assertEqual(module.classify_pull_request("BASE", "HEAD"), "FULL")

    def test_push_uses_post_merge_only_when_tree_equivalence_is_proven(self):
        with mock.patch.object(module, "merge_tree_equivalent", return_value=True):
            self.assertEqual(module.classify("push", None, "HEAD"), "POST_MERGE")
        with mock.patch.object(module, "merge_tree_equivalent", return_value=False):
            self.assertEqual(module.classify("push", None, "HEAD"), "FULL")

    def test_non_pr_non_push_events_default_to_full(self):
        self.assertEqual(module.classify("workflow_dispatch", None, "HEAD"), "FULL")
        self.assertEqual(module.classify("local", None, "HEAD"), "FULL")

    def test_full_profile_contains_historical_suite_build_and_coverage(self):
        commands = module.full_checks()
        flattened = [" ".join(command) for command in commands]
        self.assertTrue(any("unittest discover -s tests -v" in command for command in flattened))
        self.assertTrue(any("scripts/build_site.py" in command for command in flattened))
        self.assertTrue(any("scripts/run_coverage_audit.py" in command for command in flattened))
        self.assertTrue(any("scripts/run_cross_layer_coverage_audit.py" in command for command in flattened))

    def test_fast_and_post_merge_profiles_keep_all_governed_write_authority_closed(self):
        # The portable validator contains no write-mode flag and its summary
        # explicitly records that it has no governed or Calendar write authority.
        self.assertFalse(hasattr(module, "WRITE_ENV"))
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('"automatic_governed_write_authority": False', source)
        self.assertIn('"google_calendar_write_authority": False', source)

    def test_ci_self_hosted_route_has_hosted_fallback_and_fork_guard(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("WORLD_SIGNALS_VALIDATION_RUNNER", workflow)
        self.assertIn("github.event.pull_request.head.repo.full_name == github.repository", workflow)
        self.assertIn("'ubuntu-latest'", workflow)
        self.assertIn("Fetch merge second parent for post-merge proof", workflow)
        self.assertIn("actions/setup-python@v6", workflow)
        self.assertIn("actions/setup-node@v7", workflow)
        self.assertIn("node-version: '24'", workflow)

    def test_duplicate_coverage_trigger_and_scheduled_monitor_regressions_stay_off(self):
        coverage = (ROOT / ".github" / "workflows" / "coverage-audit.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", coverage)
        self.assertNotIn("\n  pull_request:", coverage)
        self.assertNotIn("\n  push:", coverage)

        monitor = (ROOT / ".github" / "workflows" / "live-monitor.yml").read_text(encoding="utf-8")
        self.assertIn("if: github.event_name != 'schedule'", monitor)


if __name__ == "__main__":
    unittest.main()
