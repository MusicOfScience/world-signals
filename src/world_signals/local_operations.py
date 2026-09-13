from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import shutil
from typing import Any

from .io import load_json
from .review_state import reduce_review_state
from .runtime_projection import prohibited_field_hits, public_runtime_projection


LOCAL_RUN_NUMBER_OFFSET = 1_000_000_000
PROTECTED_PATHS = (
    "OPEC_QUARANTINE.md",
    "data/canonical",
    "data/sources",
    "data/changes",
    "data/monitor",
    "data/live_intelligence",
    "data/analysis",
)


def atomic_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def path_fingerprints(root: Path) -> dict[str, str]:
    fingerprints: dict[str, str] = {}
    for relative in PROTECTED_PATHS:
        target = root / relative
        paths = [target] if target.is_file() else sorted(path for path in target.rglob("*") if path.is_file())
        for path in paths:
            fingerprints[str(path.relative_to(root))] = sha256(path.read_bytes()).hexdigest()
    return fingerprints


def safe_candidate_path(raw: str) -> Path:
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe local candidate path: {raw}")
    if len(path.parts) != 3 or path.parts[:2] != ("review_candidates", "live") or path.suffix != ".json":
        raise ValueError(f"local candidate path outside review_candidates/live: {raw}")
    return Path(*path.parts)


def read_monitor_outputs(root: Path) -> tuple[dict, dict, list[dict]]:
    report = load_json(root / "artifacts/live-monitor.json")
    manifest = load_json(root / "review_candidates/live/manifest.json")
    candidates = [
        load_json(root / safe_candidate_path(raw))
        for raw in manifest.get("files") or []
    ]
    if int(manifest.get("candidate_count", -1)) != len(candidates):
        raise ValueError("local monitor manifest candidate count mismatch")
    return report, manifest, candidates


def current_configuration(root: Path) -> dict:
    return {
        "canonical_registry_version": load_json(root / "data/canonical/registry.json").get("version"),
        "source_registry_version": load_json(root / "data/sources/registry.json").get("version"),
        "monitor_expectations_version": load_json(root / "data/monitor/expectations.json").get("version"),
        "monitor_operations_policy_version": load_json(root / "data/monitor/operations_policy.json").get("version"),
    }


def archive_local_run(
    root: Path,
    state_root: Path,
    *,
    sequence: int,
    run_id: str,
    run_number: int,
    report: dict,
    manifest: dict,
    candidates: list[dict],
) -> Path:
    run_dir = state_root / "runs" / f"{sequence:08d}-{run_id}"
    if run_dir.exists():
        raise ValueError(f"local run archive already exists: {run_dir}")
    run_dir.mkdir(parents=True)
    shutil.copy2(root / "artifacts/live-monitor.json", run_dir / "live-monitor.json")
    shutil.copy2(root / "review_candidates/live/manifest.json", run_dir / "manifest.json")
    atomic_dump(run_dir / "candidates.json", candidates)
    atomic_dump(
        run_dir / "run.json",
        {
            "run_number": run_number,
            "run_id": run_id,
            "run_at": report.get("run_at"),
            "status": report.get("status"),
            "candidate_count": len(candidates),
            "candidates": candidates,
            "canonical_unchanged": report.get("canonical_unchanged"),
        },
    )
    return run_dir


def load_local_runs(state_root: Path) -> list[dict]:
    runs = []
    for path in sorted((state_root / "runs").glob("*/run.json")):
        runs.append(load_json(path))
    numbers = [int(run["run_number"]) for run in runs]
    if len(numbers) != len(set(numbers)) or numbers != sorted(numbers):
        raise ValueError("local monitor history has duplicate or unordered run numbers")
    return runs


def build_public_projections(
    root: Path,
    state_root: Path,
    *,
    report: dict,
    manifest: dict,
    candidates: list[dict],
) -> tuple[dict, dict]:
    runtime_contract = load_json(root / "data/monitor/public_runtime_projection_contract.json")
    runtime = public_runtime_projection(report, manifest, candidates, current_configuration(root))
    runtime["public_projection_contract_version"] = runtime_contract.get("version")
    hits = prohibited_field_hits(runtime, set(runtime_contract.get("prohibited_field_names") or []))
    if hits:
        raise ValueError("local public runtime projection contains prohibited fields: " + ", ".join(hits))

    review_contract = load_json(root / "data/monitor/review_candidate_state_contract.json")
    review = reduce_review_state(
        load_local_runs(state_root),
        canonical_records=load_json(root / "data/canonical/registry.json").get("records", []),
        decisions=load_json(root / "data/monitor/review_decisions.json"),
        change_ledger=load_json(root / "data/changes/ledger.json"),
        contract=review_contract,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
    review.update(
        {
            "availability": "AVAILABLE_LOCAL_HORIZON",
            "scope": "LOCAL_RUNTIME_HISTORY_NOT_CANONICAL_QUEUE",
            "run_number_namespace": f"LOCAL_OFFSET_{LOCAL_RUN_NUMBER_OFFSET}",
            "unsuccessful_run_count": 0,
            "evidence_horizon_complete": False,
            "evidence_gaps": ["PRE_LOCAL_MIGRATION_ACTIONS_EVIDENCE_NOT_IMPORTED"],
        }
    )

    atomic_dump(root / "artifacts/latest-monitor-public.json", runtime)
    atomic_dump(root / "artifacts/retained-review-public.json", review)
    return runtime, review
