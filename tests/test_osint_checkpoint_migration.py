from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import world_signals.osint_checkpoint as checkpoint_module  # noqa: E402
from world_signals.osint_checkpoint import CheckpointError, inspect_checkpoint, migrate_checkpoint  # noqa: E402
from world_signals.osint_engine import run_once  # noqa: E402
from test_osint_engine import NOW, RSS, Response, route, source  # noqa: E402


class OSINTCheckpointMigrationTests(unittest.TestCase):
    def _incremental_checkpoint(self, root: Path) -> None:
        registry = {"sources": [source()]}
        cohort = {"routes": [route()]}
        run_once(registry, cohort, opener=lambda *a, **k: Response(), runtime_dir=root, now=NOW)
        run_once(registry, cohort, opener=lambda *a, **k: Response(), runtime_dir=root, now=NOW)

    def test_migration_preserves_fingerprint_and_replay_is_not_new(self):
        registry = {"sources": [source()]}
        cohort = {"routes": [route()]}
        with tempfile.TemporaryDirectory() as directory:
            source_dir = Path(directory) / "source"
            target_dir = Path(directory) / "durable"
            self._incremental_checkpoint(source_dir)
            before = inspect_checkpoint(source_dir)
            migrated_before, after = migrate_checkpoint(source_dir, target_dir)
            replay = run_once(registry, cohort, opener=lambda *a, **k: Response(), runtime_dir=target_dir, now=NOW)
            self.assertEqual(migrated_before.manifest_sha256, before.manifest_sha256)
            self.assertEqual(after.manifest_sha256, before.manifest_sha256)
            self.assertEqual(after.semantic_sha256, before.semantic_sha256)
            self.assertTrue(source_dir.exists())
            self.assertEqual(replay.observation_candidates, [])
            self.assertEqual(replay.signal_candidates, [])
            self.assertEqual(replay.metrics["genuinely_new_records"], 0)
            self.assertEqual(replay.retrievals[0].result_state, "NO_NEW_INFORMATION")

    def test_migration_preserves_same_identity_revision_detection(self):
        registry = {"sources": [source()]}
        cohort = {"routes": [route()]}
        revised = RSS.replace(b"Official statement.", b"Correction: official statement revised.")
        with tempfile.TemporaryDirectory() as directory:
            source_dir = Path(directory) / "source"
            target_dir = Path(directory) / "durable"
            self._incremental_checkpoint(source_dir)
            migrate_checkpoint(source_dir, target_dir)
            run = run_once(registry, cohort, opener=lambda *a, **k: Response(revised), runtime_dir=target_dir,
                           now=NOW.replace(day=28))
        self.assertEqual(len(run.observation_candidates), 1)
        self.assertEqual(run.observation_candidates[0].freshness_state, "INCREMENTAL_REVISION")
        self.assertEqual(run.observation_candidates[0].novelty_state, "REVISION_TO_CHECKPOINT")
        self.assertEqual(run.observation_candidates[0].change_kind, "CORRECTION")

    def test_invalid_sources_fail_closed_without_creating_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing = root / "missing"
            missing.mkdir()
            (missing / "runs").mkdir()
            target = root / "target"
            with self.assertRaises(CheckpointError):
                migrate_checkpoint(missing, target)
            self.assertFalse(target.exists())

    def test_missing_required_document_state_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_dir = root / "source"
            self._incremental_checkpoint(source_dir)
            latest = source_dir / "latest.json"
            payload = json.loads(latest.read_text(encoding="utf-8"))
            payload["checkpoint"]["document_states"] = {}
            latest.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(CheckpointError):
                inspect_checkpoint(source_dir)

    def test_unsupported_adapter_version_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            source_dir = Path(directory) / "source"
            self._incremental_checkpoint(source_dir)
            latest = source_dir / "latest.json"
            payload = json.loads(latest.read_text(encoding="utf-8"))
            next(iter(payload["checkpoint"]["routes"].values()))["adapter_version"] = "osint-engine-unknown"
            latest.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(CheckpointError):
                inspect_checkpoint(source_dir)

    def test_partial_staging_failure_leaves_source_and_no_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_dir = root / "source"
            target = root / "target"
            self._incremental_checkpoint(source_dir)
            with patch.object(checkpoint_module.shutil, "copytree", side_effect=OSError("simulated copy failure")):
                with self.assertRaises(OSError):
                    migrate_checkpoint(source_dir, target)
            self.assertTrue(source_dir.exists())
            self.assertFalse(target.exists())

    def test_default_runtime_is_ignored_and_durable(self):
        runner = Path(__file__).resolve().parents[1] / "scripts" / "run_osint_engine.py"
        ignore = Path(__file__).resolve().parents[1] / ".gitignore"
        self.assertIn('ROOT / ".world-signals-runtime/osint"', runner.read_text(encoding="utf-8"))
        self.assertIn("/.world-signals-runtime/", ignore.read_text(encoding="utf-8"))

    def test_unsupported_bootstrap_and_conflicting_target_fail_safely(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_dir = root / "source"
            self._incremental_checkpoint(source_dir)
            latest = source_dir / "latest.json"
            content = latest.read_text(encoding="utf-8").replace('"run_mode": "INCREMENTAL"', '"run_mode": "BOOTSTRAP"', 1)
            latest.write_text(content, encoding="utf-8")
            target = root / "target"
            target.mkdir()
            (target / "keep.txt").write_text("good state", encoding="utf-8")
            with self.assertRaises(CheckpointError):
                migrate_checkpoint(source_dir, target)
            self.assertEqual((target / "keep.txt").read_text(encoding="utf-8"), "good state")


if __name__ == "__main__":
    unittest.main()
