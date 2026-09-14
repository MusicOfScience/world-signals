#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.io import load_json
from world_signals.local_operations import (
    LOCAL_RUN_NUMBER_OFFSET,
    archive_local_run,
    atomic_dump,
    build_public_projections,
    path_fingerprints,
    read_monitor_outputs,
)


def command(args: list[str], *, env: dict[str, str] | None = None) -> None:
    print("+ " + " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, env=env, check=True)


def git_value(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def assert_clean_tracked_worktree() -> None:
    status = git_value("status", "--porcelain", "--untracked-files=no")
    if status:
        raise RuntimeError("local operations require a clean tracked worktree")


def assert_reviewed_main_upstream() -> None:
    if git_value("branch", "--show-current") != "main":
        raise RuntimeError("scheduled local operations require the reviewed main branch")
    if git_value("rev-parse", "HEAD") != git_value("rev-parse", "@{upstream}"):
        raise RuntimeError("scheduled local operations require local main to equal its tracked upstream head")


def next_sequence(state_root: Path) -> int:
    state_path = state_root / "sequence.json"
    if not state_path.exists():
        return 1
    state = load_json(state_path)
    return int(state.get("last_sequence", 0)) + 1


def validate_state_root(state_root: Path) -> None:
    try:
        relative = state_root.relative_to(ROOT)
    except ValueError:
        return
    if not relative.parts or relative.parts[0] != ".world-signals-runtime":
        raise ValueError("state directory inside the repository must remain under .world-signals-runtime/")


def validate(python: str) -> None:
    for script in (
        "scripts/validate_registry.py",
        "scripts/validate_live_intelligence.py",
        "scripts/validate_analysis.py",
    ):
        command([python, script])
    command([python, "scripts/project_state_snapshot.py", "--check"])
    command(
        [
            python,
            "-m",
            "unittest",
            "tests.test_adapters",
            "tests.test_live_monitor",
            "tests.test_legal_monitor",
            "tests.test_monitor_operations_policy",
            "-v",
        ]
    )


def serve(port: int) -> None:
    command(
        [
            sys.executable,
            "-m",
            "http.server",
            str(port),
            "--bind",
            "127.0.0.1",
            "--directory",
            str(ROOT / "docs"),
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the read-only WORLD SIGNALS stack locally")
    parser.add_argument("--state-dir", type=Path, default=ROOT / ".world-signals-runtime")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--require-main-upstream", action="store_true")
    args = parser.parse_args()

    state_root = args.state_dir.resolve()
    validate_state_root(state_root)
    state_root.mkdir(parents=True, exist_ok=True)
    lock_path = state_root / "operations.lock"
    with lock_path.open("w", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise SystemExit("another WORLD SIGNALS local operations run is active") from exc

        assert_clean_tracked_worktree()
        if args.require_main_upstream:
            assert_reviewed_main_upstream()
        protected_before = path_fingerprints(ROOT)
        validate(args.python)

        sequence = next_sequence(state_root)
        run_number = LOCAL_RUN_NUMBER_OFFSET + sequence
        started = datetime.now(timezone.utc)
        run_id = f"LOCAL-{sequence:08d}-{started.strftime('%Y%m%dT%H%M%SZ')}"
        git_sha = git_value("rev-parse", "HEAD")

        shutil.rmtree(ROOT / "artifacts", ignore_errors=True)
        shutil.rmtree(ROOT / "review_candidates", ignore_errors=True)
        environment = os.environ.copy()
        environment.update(
            {
                "WORLD_SIGNALS_EXECUTION_MODE": "LOCAL",
                "WORLD_SIGNALS_RUN_ID": run_id,
                "WORLD_SIGNALS_RUN_NUMBER": str(run_number),
                "WORLD_SIGNALS_GIT_SHA": git_sha,
                "WORLD_SIGNALS_MONITOR_OUTPUT": "SUMMARY",
            }
        )
        command([args.python, "scripts/run_live_monitor.py"], env=environment)

        report, manifest, candidates = read_monitor_outputs(ROOT)
        if report.get("canonical_unchanged") is not True:
            raise RuntimeError("local monitor failed the Canonical byte guard")
        run_dir = archive_local_run(
            ROOT,
            state_root,
            sequence=sequence,
            run_id=run_id,
            run_number=run_number,
            report=report,
            manifest=manifest,
            candidates=candidates,
        )
        try:
            runtime, review = build_public_projections(
                ROOT,
                state_root,
                report=report,
                manifest=manifest,
                candidates=candidates,
            )
            command([args.python, "scripts/build_site.py"])

            protected_after = path_fingerprints(ROOT)
            if protected_after != protected_before:
                raise RuntimeError("local operations changed protected governed files")
            assert_clean_tracked_worktree()
            atomic_dump(
                state_root / "sequence.json",
                {
                    "last_sequence": sequence,
                    "last_run_number": run_number,
                    "last_run_id": run_id,
                    "last_run_at": report.get("run_at"),
                    "last_git_sha": git_sha,
                },
            )
        except Exception:
            shutil.rmtree(run_dir, ignore_errors=True)
            raise

        summary = {
            "status": runtime.get("status"),
            "run_id": runtime.get("run_id"),
            "run_at": runtime.get("run_at"),
            "healthy_adapters": runtime.get("healthy_adapter_count"),
            "degraded_adapters": runtime.get("degraded_adapter_count"),
            "review_candidates_this_run": runtime.get("candidate_count"),
            "locally_retained_review_items": review.get("item_count"),
            "canonical_unchanged": runtime.get("canonical_unchanged"),
            "dashboard": f"http://127.0.0.1:{args.port}/",
        }
        print(json.dumps(summary, indent=2), flush=True)

    if args.serve:
        serve(args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
