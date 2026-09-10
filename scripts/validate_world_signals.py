#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SAFE_RESEARCH_DOC_MARKERS = (
    "_RESEARCH_",
    "_AUDIT_",
    "_PRESSURE_",
    "_CLOSEOUT_",
    "_DIAGNOSTIC_",
)

PY_COMPILE_TARGETS = [
    "scripts/fetch_latest_monitor_snapshot.py",
    "scripts/fetch_retained_review_state.py",
    "scripts/validate_live_intelligence.py",
    "scripts/validate_analysis.py",
    "scripts/project_state_snapshot.py",
    "scripts/run_cross_layer_coverage_audit.py",
    "scripts/apply_analysis_revision_contract_ba.py",
    "scripts/validate_world_signals.py",
    "src/world_signals/live_intelligence.py",
    "src/world_signals/analysis.py",
    "src/world_signals/analysis_revision.py",
    "src/world_signals/analysis_revision_projection.py",
    "src/world_signals/live_analysis_bridge.py",
    "src/world_signals/cross_layer_coverage.py",
]

JS_CHECK_TARGETS = [
    "web/app.js",
    "web/horizon.js",
    "web/native-calendar.js",
    "web/history.js",
    "web/operations.js",
    "web/biosecurity.js",
    "web/analysis.js",
]


class ValidationError(RuntimeError):
    pass


def run_capture(args: list[str]) -> str:
    completed = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise ValidationError(
            f"command failed ({completed.returncode}): {' '.join(args)}\n"
            f"{completed.stdout}{completed.stderr}"
        )
    return completed.stdout.strip()


def run_checked(args: list[str]) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def changed_entries(base_ref: str, head_ref: str) -> list[tuple[str, list[str]]]:
    output = run_capture(
        ["git", "diff", "--name-status", "--find-renames", base_ref, head_ref]
    )
    entries: list[tuple[str, list[str]]] = []
    if not output:
        return entries
    for line in output.splitlines():
        parts = line.split("\t")
        status = parts[0]
        paths = parts[1:]
        if not paths:
            raise ValidationError(f"unparseable git diff entry: {line!r}")
        entries.append((status, paths))
    return entries


def is_safe_research_markdown(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if not normalized.startswith("data/") or not normalized.endswith(".md"):
        return False
    name = Path(normalized).name.upper()
    return any(marker in name for marker in SAFE_RESEARCH_DOC_MARKERS)


def verify_safe_research_surface(
    base_ref: str,
    head_ref: str,
    entries: list[tuple[str, list[str]]] | None = None,
) -> list[str]:
    rows = entries if entries is not None else changed_entries(base_ref, head_ref)
    if not rows:
        raise ValidationError("safe-research profile requires at least one changed file")

    safe_paths: list[str] = []
    for status, paths in rows:
        # Renames/copies/deletions deliberately escalate to FULL. A fast path
        # may add or edit research evidence, but it may not erase or move it.
        if status not in {"A", "M"} or len(paths) != 1:
            raise ValidationError(
                f"safe-research profile rejects change status {status!r}: {paths}"
            )
        path = paths[0]
        if not is_safe_research_markdown(path):
            raise ValidationError(
                f"safe-research profile rejects non-research path: {path}"
            )

        tree_row = run_capture(["git", "ls-tree", head_ref, "--", path])
        if not tree_row:
            raise ValidationError(f"safe-research file absent at head: {path}")
        mode = tree_row.split(None, 1)[0]
        if mode != "100644":
            raise ValidationError(
                f"safe-research file must be a regular non-executable blob: {path} ({mode})"
            )

        # Force UTF-8 decoding of the head blob.
        run_capture(["git", "show", f"{head_ref}:{path}"])
        safe_paths.append(path)

    run_capture(["git", "diff", "--check", base_ref, head_ref])
    return safe_paths


def classify_pull_request(base_ref: str, head_ref: str) -> str:
    rows = changed_entries(base_ref, head_ref)
    if not rows:
        return "FULL"
    try:
        verify_safe_research_surface(base_ref, head_ref, rows)
    except ValidationError:
        return "FULL"
    return "SAFE_RESEARCH_DOCS"


def merge_tree_equivalent(head_ref: str) -> bool:
    try:
        parents = run_capture(["git", "rev-list", "--parents", "-n", "1", head_ref]).split()
        # Output is HEAD PARENT1 PARENT2 for a conventional two-parent merge.
        if len(parents) != 3:
            return False
        second_parent = parents[2]
        head_tree = run_capture(["git", "rev-parse", f"{head_ref}^{{tree}}"])
        parent_tree = run_capture(["git", "rev-parse", f"{second_parent}^{{tree}}"])
        return head_tree == parent_tree
    except ValidationError:
        # Missing shallow-history objects or any other inability to prove tree
        # equivalence must escalate to FULL rather than fail open.
        return False


def classify(event: str, base_ref: str | None, head_ref: str) -> str:
    if event == "pull_request":
        if not base_ref:
            raise ValidationError("pull_request classification requires --base-ref")
        return classify_pull_request(base_ref, head_ref)
    if event == "push":
        return "POST_MERGE" if merge_tree_equivalent(head_ref) else "FULL"
    return "FULL"


def common_governed_checks() -> list[list[str]]:
    py = sys.executable
    return [
        [py, "scripts/validate_registry.py"],
        [py, "scripts/validate_live_intelligence.py"],
        [py, "scripts/validate_analysis.py"],
        [py, "scripts/project_state_snapshot.py", "--check"],
    ]


def coverage_checks() -> list[list[str]]:
    py = sys.executable
    return [
        [
            py,
            "-m",
            "unittest",
            "tests.test_coverage",
            "tests.test_cross_layer_coverage_cj",
            "-v",
        ],
        [py, "scripts/run_coverage_audit.py"],
        [py, "scripts/run_cross_layer_coverage_audit.py"],
    ]


def full_checks() -> list[list[str]]:
    py = sys.executable
    commands = common_governed_checks()
    commands.append([py, "-m", "unittest", "discover", "-s", "tests", "-v"])
    commands.append([py, "-m", "py_compile", *PY_COMPILE_TARGETS])
    commands.extend([["node", "--check", path] for path in JS_CHECK_TARGETS])
    commands.append([py, "scripts/build_site.py"])
    # Full unittest discovery already includes the coverage regression modules,
    # so only generate the read-only coverage/pressure artifacts here.
    commands.extend(
        [
            [py, "scripts/run_coverage_audit.py"],
            [py, "scripts/run_cross_layer_coverage_audit.py"],
        ]
    )
    return commands


def run_profile(profile: str, base_ref: str | None, head_ref: str) -> None:
    if profile == "SAFE_RESEARCH_DOCS":
        if not base_ref:
            raise ValidationError("SAFE_RESEARCH_DOCS requires --base-ref")
        verify_safe_research_surface(base_ref, head_ref)
        commands = common_governed_checks() + coverage_checks()
    elif profile == "POST_MERGE":
        if not merge_tree_equivalent(head_ref):
            raise ValidationError(
                "POST_MERGE requires a two-parent merge whose tree equals parent 2"
            )
        commands = common_governed_checks() + coverage_checks()
    elif profile == "FULL":
        if base_ref:
            run_checked(["git", "diff", "--check", base_ref, head_ref])
        commands = full_checks()
    else:
        raise ValidationError(f"unknown validation profile: {profile}")

    for command in commands:
        run_checked(command)


def write_summary(
    profile: str,
    event: str,
    base_ref: str | None,
    head_ref: str,
    status: str,
) -> None:
    path = ROOT / "artifacts" / "validation" / "summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "project": "WORLD SIGNALS",
                "dataset": "VALIDATION_RUN_SUMMARY",
                "version": "0.1",
                "profile": profile,
                "event": event,
                "base_ref": base_ref,
                "head_ref": head_ref,
                "status": status,
                "automatic_governed_write_authority": False,
                "google_calendar_write_authority": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Portable fail-closed validation entry point for WORLD SIGNALS."
    )
    parser.add_argument(
        "--event",
        choices=("pull_request", "push", "workflow_dispatch", "local"),
        default="local",
    )
    parser.add_argument("--base-ref")
    parser.add_argument("--head-ref", default="HEAD")
    parser.add_argument(
        "--profile",
        choices=("AUTO", "FULL", "SAFE_RESEARCH_DOCS", "POST_MERGE"),
        default="AUTO",
    )
    parser.add_argument("--classify-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        profile = (
            classify(args.event, args.base_ref, args.head_ref)
            if args.profile == "AUTO"
            else args.profile
        )
        if args.classify_only:
            print(profile)
            return 0

        print(f"WORLD_SIGNALS_VALIDATION_PROFILE={profile}", flush=True)
        run_profile(profile, args.base_ref, args.head_ref)
        write_summary(profile, args.event, args.base_ref, args.head_ref, "PASS")
        print("WORLD_SIGNALS_VALIDATION_PASS", flush=True)
        return 0
    except (ValidationError, subprocess.CalledProcessError, UnicodeDecodeError) as exc:
        try:
            profile = locals().get("profile", "UNRESOLVED")
            write_summary(str(profile), args.event, args.base_ref, args.head_ref, "FAIL")
        except Exception:
            pass
        print(f"WORLD_SIGNALS_VALIDATION_FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
