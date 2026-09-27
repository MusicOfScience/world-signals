#!/usr/bin/env python3
"""Retain one non-governed, review-pending World State consistency proposal.

This is an audit/review evidence command, not a production World State writer.
It reads the existing governed layers through the Step 3 adapter, writes only
the explicitly named ``data/world_state_audit/`` package, and fails closed when
the requested knowledge cutoff is later than the selected repository snapshot.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.world_state_read import (  # noqa: E402
    CONTRACT_VERSION,
    WORLD_STATE_DIMENSIONS,
    WorldStateReadError,
    read_world_state,
    validate_read_request,
)


AUDIT_DIR = ROOT / "data/world_state_audit"
PACKAGE_VERSION = "0.1"
DEFAULT_REPOSITORY_REF = "main"
DEFAULT_AS_OF_UTC = "2026-09-27T04:39:04Z"
PROHIBITED_PRODUCTION_PATH = "data/world_state/state.json"


def _compact_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_compact_json(value).encode("utf-8")).hexdigest()


def _parse_utc(value: str, field: str) -> datetime:
    if not isinstance(value, str) or len(value) != 20 or not value.endswith("Z"):
        raise WorldStateReadError(f"{field} must be an exact UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise WorldStateReadError(f"{field} is not a valid UTC timestamp") from exc
    if parsed.tzinfo != timezone.utc:
        raise WorldStateReadError(f"{field} must be UTC")
    return parsed


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except subprocess.CalledProcessError as exc:
        raise WorldStateReadError(f"git command failed: git {' '.join(args)}: {exc.output.strip()}") from exc


def repository_provenance(repository_ref: str) -> dict[str, Any]:
    repository_sha = _git("rev-parse", "--verify", f"{repository_ref}^{{commit}}")
    commit_time = _git("show", "-s", "--format=%cI", repository_sha)
    commit_dt = datetime.fromisoformat(commit_time).astimezone(timezone.utc)
    knowledge_cutoff = commit_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    current_branch = _git("branch", "--show-current")
    return {
        "repository_ref": repository_ref,
        "repository_sha": repository_sha,
        "repository_commit_time": commit_time,
        "knowledge_cutoff_utc": knowledge_cutoff,
        "base_ref": "main",
        "branch": current_branch or "DETACHED_HEAD",
        "reader_contract_version": CONTRACT_VERSION,
        "reader_path": "src/world_signals/world_state_read.py",
    }


def validate_current_cutoff(as_of_utc: str, provenance: dict[str, Any]) -> None:
    requested = _parse_utc(as_of_utc, "as_of_utc")
    available = _parse_utc(provenance["knowledge_cutoff_utc"], "repository knowledge cutoff")
    if requested > available:
        raise WorldStateReadError(
            "future knowledge cutoff rejected: requested as_of_utc "
            f"{as_of_utc} is later than repository snapshot {provenance['repository_sha']} "
            f"at {provenance['knowledge_cutoff_utc']}"
        )


def _manifest_headers(manifest: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "layer": entry["layer"],
            "object_id": entry["object_id"],
            "revision_id": entry.get("revision_id"),
            "object_sha256": entry["object_sha256"],
        }
        for entry in manifest
    ]


def validate_retained_package(package: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    manifest = package.get("source_manifest")
    if not isinstance(manifest, list):
        return ["retained source_manifest must be a list"]
    for entry in manifest:
        if set(entry) != {"layer", "object_id", "revision_id", "object_sha256"}:
            errors.append(f"retained manifest entry has unexpected fields: {sorted(entry)}")
        if not isinstance(entry.get("object_sha256"), str) or len(entry["object_sha256"]) != 64:
            errors.append(f"invalid retained object hash for {entry.get('object_id')}")
    if package.get("retained_manifest_sha256") != _sha256(manifest):
        errors.append("retained manifest aggregate hash mismatch")
    if not isinstance(package.get("source_manifest_sha256"), str) or len(package["source_manifest_sha256"]) != 64:
        errors.append("source manifest fingerprint is missing or malformed")
    if package.get("status") != "REVIEW_PENDING":
        errors.append("retained package is not review pending")
    if package.get("production_world_state") is not False:
        errors.append("retained package cannot be production World State")
    if package.get("review_state", {}).get("write_targets") != []:
        errors.append("retained package has a write target")
    return errors


def _request(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "as_of_utc": args.as_of,
        "scope": {
            "jurisdictions": args.jurisdictions or ["*"],
            "dimensions": args.dimensions or sorted(WORLD_STATE_DIMENSIONS),
            "actor_ids": args.actor_ids,
        },
        "include_negative_evidence": not args.exclude_negative_evidence,
        "input_policy": "ACCEPTED_REVIEWED_HEADS_ONLY",
    }


def build_package(request: dict[str, Any], repository_ref: str = DEFAULT_REPOSITORY_REF) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build a deterministic package and review summary without writing files."""
    normalized = validate_read_request(request)
    provenance = repository_provenance(repository_ref)
    validate_current_cutoff(normalized["as_of_utc"], provenance)
    proposal = read_world_state(request)
    selected = proposal["selected_inputs"]
    manifest_headers = _manifest_headers(proposal["source_manifest"])
    proposal_body = deepcopy(proposal)
    proposal_body.pop("source_manifest", None)
    proposal_body.pop("source_manifest_sha256", None)
    proposal_body.pop("semantic_fingerprint", None)
    proposal_body.pop("proposal_id", None)
    package = {
        "package_type": "WORLD_STATE_CONSISTENCY_PROPOSAL",
        "package_version": PACKAGE_VERSION,
        "status": "REVIEW_PENDING",
        "production_world_state": False,
        "not_production_world_state": True,
        "no_write_targets": True,
        "public_projection_permitted": False,
        "read_request": proposal["read_request"],
        "proposal": proposal_body,
        "source_manifest": manifest_headers,
        "source_manifest_sha256": proposal["source_manifest_sha256"],
        "retained_manifest_sha256": _sha256(manifest_headers),
        "semantic_proposal_fingerprint": proposal["semantic_fingerprint"],
        "repository_provenance": provenance,
        "mutation_proof": proposal["mutation_check"],
        "review_state": {
            "decision": "REVIEW_PENDING",
            "write_targets": [],
            "public_projection_permitted": False,
        },
        "known_limitations": proposal["limitations"],
    }
    package["retained_package_validation"] = validate_retained_package(package)
    if package["retained_package_validation"]:
        raise WorldStateReadError("retained package consistency validation failed: " + "; ".join(package["retained_package_validation"]))
    summary = {
        "title": "WORLD STATE v1 CURRENT-REPOSITORY CONSISTENCY PROPOSAL",
        "status": "REVIEW_PENDING",
        "package_type": package["package_type"],
        "production_world_state": False,
        "as_of_utc": proposal["read_request"]["as_of_utc"],
        "repository_sha": provenance["repository_sha"],
        "repository_ref": repository_ref,
        "queried_jurisdictions": proposal["scope_coverage"]["queried_jurisdictions"],
        "queried_dimensions": proposal["scope_coverage"]["queried_dimensions"],
        "selected_counts": {key: len(value) for key, value in selected.items()},
        "empty_production_layers": [
            key for key, value in proposal["production_populations"].items() if value == 0
        ],
        "evaluation_state": proposal["evaluation"]["evaluation_state"],
        "analytical_object_counts": {
            key: len(proposal[key])
            for key in (
                "actors", "implementation_claims", "dimension_assessments", "hypotheses",
                "transmission_edges", "negative_evidence", "baselines", "anomalies",
            )
        },
        "unsupported_or_limited": [row["code"] for row in proposal["limitations"]],
        "source_manifest_sha256": proposal["source_manifest_sha256"],
        "retained_manifest_sha256": package["retained_manifest_sha256"],
        "semantic_proposal_fingerprint": proposal["semantic_fingerprint"],
        "mutation_check": proposal["mutation_check"],
        "review_state": "REVIEW_PENDING",
        "write_targets": [],
        "public_projection_permitted": False,
        "analytical_inference_made": False,
        "reproduction_command": (
            "python3 scripts/retain_world_state_consistency_proposal.py "
            f"--as-of {proposal['read_request']['as_of_utc']}"
        ),
    }
    return package, summary


def _summary_markdown(summary: dict[str, Any], package_path: str, summary_path: str) -> str:
    lines = [
        f"# {summary['title']}",
        "",
        "**Status:** `REVIEW_PENDING`",
        "**Package type:** `WORLD_STATE_CONSISTENCY_PROPOSAL`",
        "**Production World State:** `false`",
        "**Write targets:** `[]`",
        "**Public projection permitted:** `false`",
        "",
        "This is non-governed audit/review evidence. It is not a production World "
        "State record, admission transaction, analytical synthesis, briefing or public projection.",
        "",
        "## Repository and cutoff",
        "",
        f"- Repository ref: `{summary['repository_ref']}`",
        f"- Repository SHA: `{summary['repository_sha']}`",
        f"- Knowledge cutoff: `{summary['as_of_utc']}`",
        "- The cutoff is valid because it is no later than the selected repository snapshot commit time.",
        "- Future cutoffs are rejected by the retention command; a later repository ref may be supplied for historical replay.",
        "",
        "## Read result",
        "",
        f"- Queried jurisdictions: `{json.dumps(summary['queried_jurisdictions'], sort_keys=True)}`",
        f"- Queried dimensions: `{json.dumps(summary['queried_dimensions'], sort_keys=True)}`",
        f"- Selected counts: `{json.dumps(summary['selected_counts'], sort_keys=True)}`",
        f"- Explicitly empty production layers: `{json.dumps(summary['empty_production_layers'], sort_keys=True)}`",
        f"- Forecast Evaluation: `{summary['evaluation_state']}`",
        "",
        "## Analytical boundary",
        "",
        "No analytical inference was made. Actor assertions, implementation claims, "
        "dimension assessments, hypotheses, transmission edges, baselines, anomalies "
        "and production negative-evidence assertions remain empty.",
        "",
        f"- Analytical object counts: `{json.dumps(summary['analytical_object_counts'], sort_keys=True)}`",
        f"- Limitations: `{json.dumps(summary['unsupported_or_limited'], sort_keys=True)}`",
        "",
        "## Integrity and review",
        "",
        f"- Source manifest SHA-256: `{summary['source_manifest_sha256']}`",
        f"- Retained hash-only manifest SHA-256: `{summary['retained_manifest_sha256']}`",
        f"- Semantic proposal fingerprint: `{summary['semantic_proposal_fingerprint']}`",
        f"- Mutation check: `{summary['mutation_check']['status']}`",
        "- Review state: `REVIEW_PENDING`; Migration Step 5 has not been conducted.",
        "- Reproducibility requires the same repository source state, request and governed objects.",
        "",
        "## Retained files",
        "",
        f"- Machine-readable package: `{package_path}`",
        f"- This review summary: `{summary_path}`",
        "",
        f"Reproduce with: `{summary['reproduction_command']}`",
        "",
    ]
    return "\n".join(lines)


def write_package(package: dict[str, Any], summary: dict[str, Any]) -> tuple[Path, Path]:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = summary["as_of_utc"].replace("-", "").replace(":", "").replace("T", "T").replace("Z", "Z")
    package_path = AUDIT_DIR / f"CONSISTENCY_PROPOSAL_{stamp}_REVIEW_PENDING.json"
    summary_path = AUDIT_DIR / f"CONSISTENCY_PROPOSAL_{stamp}_REVIEW_SUMMARY.md"
    package_text = json.dumps(package, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    summary_text = _summary_markdown(
        summary,
        str(package_path.relative_to(ROOT)),
        str(summary_path.relative_to(ROOT)),
    )
    for path, text in ((package_path, package_text), (summary_path, summary_text)):
        if path.exists() and path.read_text(encoding="utf-8") != text:
            raise WorldStateReadError(f"retained evidence already exists with different content: {path.relative_to(ROOT)}")
        if not path.exists():
            path.write_text(text, encoding="utf-8")
    return package_path, summary_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", default=DEFAULT_AS_OF_UTC, help="exact UTC knowledge cutoff; defaults to the PR #156 merge timestamp")
    parser.add_argument("--repository-ref", default=DEFAULT_REPOSITORY_REF, help="repository snapshot ref whose commit time bounds the cutoff")
    parser.add_argument("--jurisdiction", action="append", dest="jurisdictions", default=None)
    parser.add_argument("--dimension", action="append", dest="dimensions", choices=sorted(WORLD_STATE_DIMENSIONS), default=None)
    parser.add_argument("--actor-id", action="append", dest="actor_ids", default=None)
    parser.add_argument("--exclude-negative-evidence", action="store_true")
    parser.add_argument("--check-only", action="store_true", help="build and validate without writing the retained package")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        request = _request(args)
        package, summary = build_package(request, args.repository_ref)
        if args.check_only:
            print(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True))
            return 0
        package_path, summary_path = write_package(package, summary)
        print(json.dumps({"status": "PASS", "package": str(package_path.relative_to(ROOT)), "summary": str(summary_path.relative_to(ROOT)), **summary}, indent=2, ensure_ascii=False, sort_keys=True))
        return 0
    except (WorldStateReadError, OSError, json.JSONDecodeError) as exc:
        print(f"World State consistency proposal FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
