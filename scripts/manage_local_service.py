#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.local_service import (
    DASHBOARD_LABEL,
    REFRESH_LABEL,
    LocalServiceConfig,
    launchd_manifests,
    manifest_bytes,
    manifest_filename,
    service_metadata,
)


INSTALL_GATE = "WORLD_SIGNALS_INSTALL_LOCAL_SERVICE"
UNINSTALL_GATE = "WORLD_SIGNALS_UNINSTALL_LOCAL_SERVICE"


def config_from_args(args: argparse.Namespace) -> LocalServiceConfig:
    return LocalServiceConfig(
        root=ROOT,
        python=Path(args.python),
        state_root=Path(args.state_dir),
        port=args.port,
    ).validated()


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)


def render(config: LocalServiceConfig, output_dir: Path) -> list[Path]:
    paths = []
    for label, payload in launchd_manifests(config).items():
        path = output_dir / manifest_filename(label)
        atomic_write(path, manifest_bytes(payload))
        paths.append(path)
    atomic_write(
        output_dir / "world-signals-service.json",
        (json.dumps(service_metadata(config), indent=2) + "\n").encode("utf-8"),
    )
    return paths


def git_value(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def require_clean_main() -> None:
    if git_value("status", "--porcelain", "--untracked-files=no"):
        raise RuntimeError("service installation requires a clean tracked worktree")
    if git_value("branch", "--show-current") != "main":
        raise RuntimeError("service installation requires the reviewed main branch")
    if git_value("rev-parse", "HEAD") != git_value("rev-parse", "@{upstream}"):
        raise RuntimeError("service installation requires local main to equal its reviewed upstream head")


def launch_domain() -> str:
    return f"gui/{os.getuid()}"


def is_loaded(label: str) -> bool:
    result = subprocess.run(
        ["launchctl", "print", f"{launch_domain()}/{label}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def require_macos() -> None:
    if sys.platform != "darwin":
        raise RuntimeError("the local service manager currently supports macOS launchd only")


def install(config: LocalServiceConfig, launch_agents: Path) -> None:
    require_macos()
    if os.environ.get(INSTALL_GATE) != "YES":
        raise RuntimeError(f"installation blocked: set {INSTALL_GATE}=YES after reviewed merge approval")
    require_clean_main()
    config.state_root.joinpath("logs").mkdir(parents=True, exist_ok=True)
    manifests = launchd_manifests(config)
    paths = {label: launch_agents / manifest_filename(label) for label in manifests}
    for label, path in paths.items():
        expected = manifest_bytes(manifests[label])
        if path.exists() and path.read_bytes() != expected:
            raise RuntimeError(f"refusing to overwrite a different service manifest: {path}")
    written: list[Path] = []
    loaded: list[str] = []
    try:
        for label, path in paths.items():
            if not path.exists():
                atomic_write(path, manifest_bytes(manifests[label]))
                written.append(path)
        for label, path in paths.items():
            if not is_loaded(label):
                subprocess.run(["launchctl", "bootstrap", launch_domain(), str(path)], check=True)
                loaded.append(label)
    except Exception:
        for label in reversed(loaded):
            subprocess.run(
                ["launchctl", "bootout", f"{launch_domain()}/{label}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        for path in written:
            path.unlink(missing_ok=True)
        raise


def uninstall(launch_agents: Path) -> None:
    require_macos()
    if os.environ.get(UNINSTALL_GATE) != "YES":
        raise RuntimeError(f"uninstallation blocked: set {UNINSTALL_GATE}=YES after explicit approval")
    paths = {
        label: launch_agents / manifest_filename(label)
        for label in (REFRESH_LABEL, DASHBOARD_LABEL)
    }
    for label, path in paths.items():
        if path.exists():
            payload = plistlib.loads(path.read_bytes())
            if payload.get("Label") != label:
                raise RuntimeError(f"refusing to remove an unrecognised manifest: {path}")
    for label, path in paths.items():
        if is_loaded(label):
            subprocess.run(["launchctl", "bootout", f"{launch_domain()}/{label}"], check=True)
        if path.exists():
            path.unlink()


def status(config: LocalServiceConfig, launch_agents: Path) -> dict:
    require_macos()
    manifests = launchd_manifests(config)
    jobs = []
    for label in (REFRESH_LABEL, DASHBOARD_LABEL):
        path = launch_agents / manifest_filename(label)
        present = path.is_file()
        jobs.append(
            {
                "label": label,
                "manifest_present": present,
                "manifest_matches_reviewed_config": present
                and path.read_bytes() == manifest_bytes(manifests[label]),
                "loaded": is_loaded(label),
            }
        )
    return {**service_metadata(config), "jobs": jobs}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Manage the guarded WORLD SIGNALS local macOS service")
    result.add_argument("command", choices=("render", "status", "install", "uninstall"))
    stable_python = Path("/opt/homebrew/bin/python3.13")
    result.add_argument("--python", default=str(stable_python if stable_python.is_file() else Path(sys.executable)))
    result.add_argument("--state-dir", default=str(ROOT / ".world-signals-runtime"))
    result.add_argument("--port", type=int, default=8765)
    result.add_argument("--output-dir", type=Path, default=ROOT / ".world-signals-runtime/service-preview")
    result.add_argument("--launch-agents", type=Path, default=Path.home() / "Library/LaunchAgents")
    return result


def main() -> int:
    args = parser().parse_args()
    config = config_from_args(args)
    if args.command == "render":
        paths = render(config, args.output_dir.resolve())
        print(json.dumps({"status": "RENDERED_NOT_INSTALLED", "files": [str(path) for path in paths]}, indent=2))
    elif args.command == "status":
        print(json.dumps(status(config, args.launch_agents.resolve()), indent=2))
    elif args.command == "install":
        install(config, args.launch_agents.resolve())
        print(json.dumps(status(config, args.launch_agents.resolve()), indent=2))
    else:
        uninstall(args.launch_agents.resolve())
        print(json.dumps({"status": "UNINSTALLED"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
