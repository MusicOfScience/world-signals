from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import plistlib
from typing import Any


DAILY_INTERVAL_SECONDS = 86_400
REFRESH_LABEL = "io.worldsignals.refresh"
DASHBOARD_LABEL = "io.worldsignals.dashboard"
SERVICE_VERSION = "0.1"


@dataclass(frozen=True)
class LocalServiceConfig:
    root: Path
    python: Path
    state_root: Path
    service_working_directory: Path
    port: int = 8765
    interval_seconds: int = DAILY_INTERVAL_SECONDS

    def validated(self) -> "LocalServiceConfig":
        root = self.root.resolve()
        python = self.python.expanduser()
        state_root = self.state_root.resolve()
        working_directory = self.service_working_directory.expanduser().resolve()
        if not all(path.is_absolute() for path in (root, python, state_root, working_directory)):
            raise ValueError("local service paths must be absolute")
        if not python.is_file():
            raise ValueError("configured Python executable is missing")
        if not os.access(python, os.X_OK):
            raise ValueError("configured Python executable is not executable")
        if not (root / "scripts/run_local_operations.py").is_file():
            raise ValueError("WORLD SIGNALS runner is missing from the configured repository")
        if not (root / "docs").is_dir():
            raise ValueError("WORLD SIGNALS built dashboard directory is missing")
        try:
            relative = state_root.relative_to(root)
        except ValueError as exc:
            raise ValueError("local service state must stay inside the repository runtime root") from exc
        if not relative.parts or relative.parts[0] != ".world-signals-runtime":
            raise ValueError("local service state must stay under .world-signals-runtime/")
        if working_directory == root or root in working_directory.parents:
            raise ValueError("local service working directory must remain outside the repository")
        if self.interval_seconds != DAILY_INTERVAL_SECONDS:
            raise ValueError("local service cadence must match the governed daily monitor baseline")
        if not 1024 <= self.port <= 65535:
            raise ValueError("local dashboard port must be between 1024 and 65535")
        return LocalServiceConfig(
            root,
            python,
            state_root,
            working_directory,
            self.port,
            self.interval_seconds,
        )


def launchd_manifests(config: LocalServiceConfig) -> dict[str, dict[str, Any]]:
    cfg = config.validated()
    logs = cfg.state_root / "logs"
    refresh = {
        "Label": REFRESH_LABEL,
        "ProgramArguments": [
            str(cfg.python),
            str(cfg.root / "scripts/run_local_operations.py"),
            "--state-dir",
            str(cfg.state_root),
            "--python",
            str(cfg.python),
            "--require-main-upstream",
            "--execution-cwd",
            str(cfg.service_working_directory),
        ],
        "WorkingDirectory": str(cfg.service_working_directory),
        "RunAtLoad": True,
        "StartInterval": cfg.interval_seconds,
        "ProcessType": "Background",
        "LowPriorityIO": True,
        "StandardOutPath": str(logs / "refresh.stdout.log"),
        "StandardErrorPath": str(logs / "refresh.stderr.log"),
    }
    dashboard = {
        "Label": DASHBOARD_LABEL,
        "ProgramArguments": [
            str(cfg.python),
            "-m",
            "http.server",
            str(cfg.port),
            "--bind",
            "127.0.0.1",
            "--directory",
            str(cfg.root / "docs"),
        ],
        "WorkingDirectory": str(cfg.service_working_directory),
        "RunAtLoad": True,
        "KeepAlive": {"SuccessfulExit": False},
        "ThrottleInterval": 10,
        "StandardOutPath": str(logs / "dashboard.stdout.log"),
        "StandardErrorPath": str(logs / "dashboard.stderr.log"),
    }
    return {REFRESH_LABEL: refresh, DASHBOARD_LABEL: dashboard}


def manifest_bytes(payload: dict[str, Any]) -> bytes:
    return plistlib.dumps(payload, fmt=plistlib.FMT_XML, sort_keys=True)


def manifest_filename(label: str) -> str:
    if label not in {REFRESH_LABEL, DASHBOARD_LABEL}:
        raise ValueError(f"unknown WORLD SIGNALS service label: {label}")
    return f"{label}.plist"


def service_metadata(config: LocalServiceConfig) -> dict[str, Any]:
    cfg = config.validated()
    return {
        "service_contract_version": SERVICE_VERSION,
        "platform": "MACOS_USER_LAUNCH_AGENT",
        "refresh_label": REFRESH_LABEL,
        "dashboard_label": DASHBOARD_LABEL,
        "refresh_interval_seconds": cfg.interval_seconds,
        "dashboard_url": f"http://127.0.0.1:{cfg.port}/",
        "state_root": str(cfg.state_root),
        "service_working_directory": str(cfg.service_working_directory),
        "automatic_canonical_commit": False,
        "google_calendar_write": False,
        "automatic_live_or_analysis_promotion": False,
        "automatic_git_commit_or_merge": False,
        "requires_clean_reviewed_main_upstream": True,
    }
