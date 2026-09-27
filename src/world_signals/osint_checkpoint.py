"""Validation and fail-closed migration for retained OSINT checkpoints."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import shutil
import uuid
from typing import Any


class CheckpointError(ValueError):
    """Raised when a retained checkpoint is incomplete or unsafe to migrate."""


REQUIRED_LATEST_KEYS = {
    "checkpoint", "completed_at", "metrics", "observation_candidates",
    "retrievals", "routes_attempted", "run_id", "run_mode",
    "signal_candidates", "started_at",
}
REQUIRED_CHECKPOINT_KEYS = {"document_states", "routes", "run_mode", "seen_document_keys"}
SUPPORTED_ADAPTER_VERSIONS = {"osint-engine-0.2-incremental"}


@dataclass(frozen=True)
class CheckpointInspection:
    path: Path
    run_id: str
    run_mode: str
    file_count: int
    total_bytes: int
    manifest_sha256: str
    latest_sha256: str
    semantic_sha256: str
    run_history_count: int
    route_count: int
    known_document_identity_count: int
    known_record_hash_count: int
    known_native_identity_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path), "run_id": self.run_id, "run_mode": self.run_mode,
            "file_count": self.file_count, "total_bytes": self.total_bytes,
            "manifest_sha256": self.manifest_sha256, "latest_sha256": self.latest_sha256,
            "semantic_sha256": self.semantic_sha256, "run_history_count": self.run_history_count,
            "route_count": self.route_count,
            "known_document_identity_count": self.known_document_identity_count,
            "known_record_hash_count": self.known_record_hash_count,
            "known_native_identity_count": self.known_native_identity_count,
        }


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _file_manifest(root: Path) -> tuple[list[dict[str, Any]], str]:
    entries: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if path.is_symlink():
            raise CheckpointError(f"checkpoint contains unsupported symlink: {relative}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise CheckpointError(f"checkpoint contains unsupported special file: {relative}")
        content = path.read_bytes()
        entries.append({"path": relative.as_posix(), "size": len(content), "sha256": _sha256_bytes(content)})
    return entries, _sha256_bytes(_canonical_json(entries))


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CheckpointError(f"cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CheckpointError(f"checkpoint JSON must be an object: {path}")
    return value


def _validate_latest(root: Path) -> dict[str, Any]:
    if not root.is_dir():
        raise CheckpointError(f"checkpoint directory does not exist: {root}")
    latest_path = root / "latest.json"
    if not latest_path.is_file():
        raise CheckpointError(f"checkpoint is missing latest.json: {root}")
    payload = _load_json(latest_path)
    missing = sorted(REQUIRED_LATEST_KEYS - payload.keys())
    if missing:
        raise CheckpointError(f"latest.json is missing required keys: {', '.join(missing)}")
    if payload["run_mode"] != "INCREMENTAL":
        raise CheckpointError(f"only an incremental checkpoint can be migrated; found {payload['run_mode']!r}")
    if not isinstance(payload["run_id"], str) or not payload["run_id"]:
        raise CheckpointError("latest.json has no valid run_id")
    if not isinstance(payload["retrievals"], list) or not payload["retrievals"]:
        raise CheckpointError("latest.json has no retained retrieval state")
    if not isinstance(payload["routes_attempted"], list) or not payload["routes_attempted"]:
        raise CheckpointError("latest.json has no retained route cohort")

    checkpoint = payload["checkpoint"]
    if not isinstance(checkpoint, dict):
        raise CheckpointError("latest.json checkpoint must be an object")
    missing = sorted(REQUIRED_CHECKPOINT_KEYS - checkpoint.keys())
    if missing:
        raise CheckpointError(f"checkpoint state is missing required keys: {', '.join(missing)}")
    if checkpoint["run_mode"] != "INCREMENTAL":
        raise CheckpointError(f"checkpoint run_mode is not incremental: {checkpoint['run_mode']!r}")
    if not isinstance(checkpoint["routes"], dict) or not checkpoint["routes"]:
        raise CheckpointError("checkpoint has no route state")
    if not isinstance(checkpoint["seen_document_keys"], list):
        raise CheckpointError("checkpoint seen_document_keys must be a list")
    if len(set(checkpoint["seen_document_keys"])) != len(checkpoint["seen_document_keys"]):
        raise CheckpointError("checkpoint seen_document_keys contains duplicates")
    if not isinstance(checkpoint["document_states"], dict) or not checkpoint["document_states"]:
        raise CheckpointError("checkpoint has no document state")
    for route_id, route_state in checkpoint["routes"].items():
        if not isinstance(route_state, dict):
            raise CheckpointError(f"route checkpoint is not an object: {route_id}")
        for key in ("source_id", "parser_version", "adapter_version", "checkpoint_state"):
            if key not in route_state:
                raise CheckpointError(f"route checkpoint {route_id} is missing {key}")
        if route_state["adapter_version"] not in SUPPORTED_ADAPTER_VERSIONS:
            raise CheckpointError(f"unsupported checkpoint adapter version: {route_state['adapter_version']!r}")
    for document_key, state in checkpoint["document_states"].items():
        if not isinstance(state, dict):
            raise CheckpointError(f"document state is not an object: {document_key}")
        for key in ("payload_sha256", "record_sha256", "source_native_id"):
            if key not in state:
                raise CheckpointError(f"document state {document_key} is missing {key}")

    runs = root / "runs"
    if not runs.is_dir():
        raise CheckpointError("checkpoint is missing its runs/ history directory")
    history = sorted(path for path in runs.iterdir() if path.is_file())
    if not history:
        raise CheckpointError("checkpoint has no run history")
    latest_run = runs / f"{payload['run_id']}.json"
    if not latest_run.is_file():
        raise CheckpointError(f"checkpoint latest run history is missing: {latest_run.name}")
    for run_path in history:
        _load_json(run_path)
    return payload


def inspect_checkpoint(root: Path) -> CheckpointInspection:
    """Validate and fingerprint a checkpoint without changing it."""
    root = root.resolve()
    payload = _validate_latest(root)
    entries, manifest_sha256 = _file_manifest(root)
    latest_bytes = (root / "latest.json").read_bytes()
    semantic = {
        "run_id": payload["run_id"], "run_mode": payload["run_mode"],
        "retrievals": payload["retrievals"], "checkpoint": payload["checkpoint"],
        "metrics": payload["metrics"], "observation_candidates": payload["observation_candidates"],
        "signal_candidates": payload["signal_candidates"],
    }
    checkpoint = payload["checkpoint"]
    states = checkpoint["document_states"].values()
    return CheckpointInspection(
        path=root, run_id=payload["run_id"], run_mode=payload["run_mode"],
        file_count=len(entries), total_bytes=sum(entry["size"] for entry in entries),
        manifest_sha256=manifest_sha256, latest_sha256=_sha256_bytes(latest_bytes),
        semantic_sha256=_sha256_bytes(_canonical_json(semantic)),
        run_history_count=len(list((root / "runs").iterdir())),
        route_count=len(checkpoint["routes"]),
        known_document_identity_count=len(checkpoint["seen_document_keys"]),
        known_record_hash_count=sum(bool(state.get("record_sha256")) for state in states),
        known_native_identity_count=sum(bool(state.get("source_native_id")) for state in checkpoint["document_states"].values()),
    )


def migrate_checkpoint(source: Path, target: Path) -> tuple[CheckpointInspection, CheckpointInspection]:
    """Copy a validated checkpoint into a new target and activate atomically."""
    source = source.resolve()
    target = target.resolve()
    source_inspection = inspect_checkpoint(source)
    if target.exists():
        raise CheckpointError(f"refusing to overwrite existing target: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = target.parent / f".{target.name}.staging-{uuid.uuid4().hex}"
    try:
        shutil.copytree(source, staging, copy_function=shutil.copy2)
        staged_inspection = inspect_checkpoint(staging)
        if staged_inspection.manifest_sha256 != source_inspection.manifest_sha256:
            raise CheckpointError("staged checkpoint file manifest differs from source")
        if staged_inspection.semantic_sha256 != source_inspection.semantic_sha256:
            raise CheckpointError("staged checkpoint semantic fingerprint differs from source")
        if staged_inspection.latest_sha256 != source_inspection.latest_sha256:
            raise CheckpointError("staged latest.json differs from source")
        staging.rename(target)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return source_inspection, inspect_checkpoint(target)
