"""Safely publish a deterministic public build to a dedicated Pages branch.

The command is intentionally operator-invoked. It never commits to ``main``
and it refuses to publish from an unclean or unsynchronised source checkout.
Use ``--check-only`` to exercise all build and privacy checks without a push.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_public_site import validate_public_site


def git(*args: str, cwd: Path = ROOT, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=False)
    if check and result.returncode:
        raise SystemExit(result.stderr.strip() or result.stdout.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def require_clean_source(source_branch: str) -> str:
    if git("branch", "--show-current") != source_branch:
        raise SystemExit(f"Refusing publication: current branch is not {source_branch!r}")
    if git("status", "--porcelain"):
        raise SystemExit("Refusing publication: source worktree is not clean")
    git("fetch", "origin", "--prune")
    head = git("rev-parse", "HEAD")
    remote = git("rev-parse", f"origin/{source_branch}")
    if head != remote:
        raise SystemExit(f"Refusing publication: HEAD {head} does not equal origin/{source_branch} {remote}")
    return head


def build_and_validate() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts/build_site.py")], cwd=ROOT, check=True)
    problems = validate_public_site(ROOT / "docs")
    if problems:
        raise SystemExit("Refusing publication:\n- " + "\n- ".join(problems))


def publication_worktree(branch: str, source_head: str) -> Path:
    temp = Path(tempfile.mkdtemp(prefix="world-signals-pages-", dir=tempfile.gettempdir()))
    remote_exists = subprocess.run(
        ["git", "ls-remote", "--exit-code", "--heads", "origin", branch], cwd=ROOT, capture_output=True
    ).returncode == 0
    if remote_exists:
        git("worktree", "add", "--detach", str(temp), f"origin/{branch}")
    else:
        git("worktree", "add", "--detach", str(temp), source_head)
        git("switch", "--orphan", branch, cwd=temp)
    return temp


def publish(branch: str, source_head: str) -> str:
    temp = publication_worktree(branch, source_head)
    try:
        for child in temp.iterdir():
            if child.name == ".git":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        shutil.copytree(ROOT / "docs", temp, dirs_exist_ok=True)
        git("add", "-A", cwd=temp)
        staged = git("diff", "--cached", "--stat", cwd=temp)
        if not staged:
            return git("rev-parse", "HEAD", cwd=temp)
        git("-c", "user.name=WORLD SIGNALS publisher", "-c", "user.email=world-signals-pages@users.noreply.github.com", "commit", "-m", "Publish WORLD SIGNALS static site", cwd=temp)
        git("push", "origin", f"HEAD:refs/heads/{branch}", cwd=temp)
        return git("rev-parse", "HEAD", cwd=temp)
    finally:
        git("worktree", "remove", "--force", str(temp), check=False)
        if temp.exists():
            shutil.rmtree(temp)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-branch", default="main")
    parser.add_argument("--publication-branch", default="gh-pages")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    source_head = require_clean_source(args.source_branch)
    build_and_validate()
    if args.check_only:
        print(f"Pages publication checks PASS for {args.source_branch}@{source_head}; no branch was changed")
        return
    publication_head = publish(args.publication_branch, source_head)
    print(f"Published {args.source_branch}@{source_head} to {args.publication_branch}@{publication_head}")


if __name__ == "__main__":
    main()
