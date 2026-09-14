from pathlib import Path
from tempfile import TemporaryDirectory
import plistlib
import sys
import unittest
from unittest.mock import patch

import scripts.manage_local_service as manager
from src.world_signals.local_service import (
    DAILY_INTERVAL_SECONDS,
    DASHBOARD_LABEL,
    REFRESH_LABEL,
    LocalServiceConfig,
    launchd_manifests,
    manifest_bytes,
    service_metadata,
)


ROOT = Path(__file__).resolve().parents[1]
STABLE_PYTHON = Path("/opt/homebrew/bin/python3.13")
TEST_PYTHON = STABLE_PYTHON if STABLE_PYTHON.is_file() else Path(sys.executable)


class LocalServiceCWTests(unittest.TestCase):
    def config(self, **overrides):
        values = {
            "root": ROOT,
            "python": TEST_PYTHON,
            "state_root": ROOT / ".world-signals-runtime",
            "port": 8765,
            "interval_seconds": DAILY_INTERVAL_SECONDS,
        }
        values.update(overrides)
        return LocalServiceConfig(**values)

    def test_manifests_preserve_daily_governed_runner_and_loopback_only_dashboard(self):
        manifests = launchd_manifests(self.config())
        refresh = manifests[REFRESH_LABEL]
        dashboard = manifests[DASHBOARD_LABEL]
        self.assertEqual(refresh["StartInterval"], 86_400)
        self.assertTrue(refresh["RunAtLoad"])
        self.assertIn(str(ROOT / "scripts/run_local_operations.py"), refresh["ProgramArguments"])
        self.assertIn("--require-main-upstream", refresh["ProgramArguments"])
        self.assertNotIn("git", " ".join(refresh["ProgramArguments"]).lower())
        self.assertEqual(dashboard["ProgramArguments"][-4:-2], ["--bind", "127.0.0.1"])
        self.assertEqual(dashboard["ProgramArguments"][-2], "--directory")
        self.assertTrue(dashboard["KeepAlive"])

    def test_service_metadata_keeps_every_automatic_write_gate_closed(self):
        metadata = service_metadata(self.config())
        self.assertFalse(metadata["automatic_canonical_commit"])
        self.assertFalse(metadata["google_calendar_write"])
        self.assertFalse(metadata["automatic_live_or_analysis_promotion"])
        self.assertFalse(metadata["automatic_git_commit_or_merge"])
        self.assertTrue(metadata["requires_clean_reviewed_main_upstream"])
        self.assertEqual(metadata["dashboard_url"], "http://127.0.0.1:8765/")

    def test_non_daily_cadence_and_unbounded_state_paths_fail_closed(self):
        with self.assertRaises(ValueError):
            self.config(interval_seconds=3600).validated()
        with self.assertRaises(ValueError):
            self.config(state_root=Path("/tmp/world-signals-runtime")).validated()
        with self.assertRaises(ValueError):
            self.config(port=80).validated()

    def test_render_emits_parseable_reviewable_plists_without_installing(self):
        self.assertEqual(Path(manager.parser().parse_args(["render"]).python), TEST_PYTHON)
        with TemporaryDirectory() as temporary:
            output = Path(temporary)
            with patch.object(manager, "is_loaded") as loaded:
                paths = manager.render(self.config().validated(), output)
            self.assertEqual(len(paths), 2)
            self.assertFalse(loaded.called)
            labels = {plistlib.loads(path.read_bytes())["Label"] for path in paths}
            self.assertEqual(labels, {REFRESH_LABEL, DASHBOARD_LABEL})
            for path in paths:
                self.assertEqual(
                    plistlib.loads(path.read_bytes())["ProgramArguments"][0],
                    str(TEST_PYTHON),
                )
            self.assertTrue((output / "world-signals-service.json").is_file())

    def test_install_and_uninstall_require_separate_explicit_gates(self):
        with patch.object(manager, "require_macos"):
            with patch.dict(manager.os.environ, {}, clear=True):
                with self.assertRaisesRegex(RuntimeError, manager.INSTALL_GATE):
                    manager.install(self.config().validated(), Path("/tmp/launch-agents"))
                with self.assertRaisesRegex(RuntimeError, manager.UNINSTALL_GATE):
                    manager.uninstall(Path("/tmp/launch-agents"))

    def test_install_rolls_back_new_manifests_and_jobs_on_partial_failure(self):
        with TemporaryDirectory() as temporary:
            launch_agents = Path(temporary)
            calls = []

            def run(command, **kwargs):
                calls.append(command)
                if command[:2] == ["launchctl", "bootstrap"] and command[-1].endswith(
                    f"{DASHBOARD_LABEL}.plist"
                ):
                    raise manager.subprocess.CalledProcessError(5, command)
                return manager.subprocess.CompletedProcess(command, 0)

            with (
                patch.object(manager, "require_macos"),
                patch.object(manager, "require_clean_main"),
                patch.object(manager, "is_loaded", return_value=False),
                patch.object(manager.subprocess, "run", side_effect=run),
                patch.dict(manager.os.environ, {manager.INSTALL_GATE: "YES"}, clear=True),
            ):
                with self.assertRaises(manager.subprocess.CalledProcessError):
                    manager.install(self.config().validated(), launch_agents)

            self.assertEqual(list(launch_agents.glob("*.plist")), [])
            self.assertTrue(
                any(command[:2] == ["launchctl", "bootout"] for command in calls),
                "the successfully bootstrapped refresh job must be rolled back",
            )

    def test_uninstall_preflights_both_manifests_before_removing_either(self):
        with TemporaryDirectory() as temporary:
            launch_agents = Path(temporary)
            manifests = launchd_manifests(self.config())
            refresh_path = launch_agents / f"{REFRESH_LABEL}.plist"
            dashboard_path = launch_agents / f"{DASHBOARD_LABEL}.plist"
            refresh_path.write_bytes(manifest_bytes(manifests[REFRESH_LABEL]))
            bad_dashboard = dict(manifests[DASHBOARD_LABEL], Label="io.not-world-signals.dashboard")
            dashboard_path.write_bytes(manifest_bytes(bad_dashboard))
            with (
                patch.object(manager, "require_macos"),
                patch.object(manager, "is_loaded") as loaded,
                patch.dict(manager.os.environ, {manager.UNINSTALL_GATE: "YES"}, clear=True),
            ):
                with self.assertRaisesRegex(RuntimeError, "unrecognised manifest"):
                    manager.uninstall(launch_agents)
            self.assertTrue(refresh_path.exists())
            self.assertTrue(dashboard_path.exists())
            self.assertFalse(loaded.called)

    def test_status_distinguishes_present_matching_and_loaded_state(self):
        with TemporaryDirectory() as temporary:
            launch_agents = Path(temporary)
            manifests = launchd_manifests(self.config())
            refresh_path = launch_agents / f"{REFRESH_LABEL}.plist"
            refresh_path.write_bytes(manifest_bytes(manifests[REFRESH_LABEL]))
            with (
                patch.object(manager, "require_macos"),
                patch.object(manager, "is_loaded", side_effect=lambda label: label == REFRESH_LABEL),
            ):
                result = manager.status(self.config().validated(), launch_agents)
            by_label = {job["label"]: job for job in result["jobs"]}
            self.assertTrue(by_label[REFRESH_LABEL]["manifest_present"])
            self.assertTrue(by_label[REFRESH_LABEL]["manifest_matches_reviewed_config"])
            self.assertTrue(by_label[REFRESH_LABEL]["loaded"])
            self.assertFalse(by_label[DASHBOARD_LABEL]["manifest_present"])
            self.assertFalse(by_label[DASHBOARD_LABEL]["manifest_matches_reviewed_config"])
            self.assertFalse(by_label[DASHBOARD_LABEL]["loaded"])


if __name__ == "__main__":
    unittest.main()
