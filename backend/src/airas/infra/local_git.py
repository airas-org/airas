from __future__ import annotations

import re
import subprocess
from pathlib import Path


def _run(repo_root: Path, *args: str) -> subprocess.CompletedProcess[bytes] | None:
    try:
        return subprocess.run(
            ["git", "-C", str(repo_root), *args], capture_output=True, timeout=30
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _text(repo_root: Path, *args: str) -> str | None:
    result = _run(repo_root, *args)
    if result is None or result.returncode != 0:
        return None
    return result.stdout.decode("utf-8", errors="replace").strip()


def commit_is_ancestor(repo_root: Path, commit_hash: str) -> bool:
    # Ancestry, not mere existence: a commit on an unrelated local branch
    # "exists" but is not code this branch carries.
    result = _run(repo_root, "merge-base", "--is-ancestor", commit_hash, "HEAD")
    return result is not None and result.returncode == 0


def remote_origin_url(repo_root: Path) -> str | None:
    return _text(repo_root, "remote", "get-url", "origin")


def current_branch(repo_root: Path) -> str | None:
    branch = _text(repo_root, "rev-parse", "--abbrev-ref", "HEAD")
    return None if branch in (None, "HEAD") else branch  # HEAD = detached


def is_shallow(repo_root: Path) -> bool:
    return _text(repo_root, "rev-parse", "--is-shallow-repository") == "true"


def file_bytes_at_commit(
    repo_root: Path, commit_hash: str, repo_path: str
) -> bytes | None:
    result = _run(repo_root, "show", f"{commit_hash}:{repo_path}")
    if result is None or result.returncode != 0:
        return None

    return bytes(result.stdout)


def commits_touching(repo_root: Path, repo_path: str) -> list[str] | None:
    log = _text(repo_root, "log", "--format=%H", "--", repo_path)
    if log is None:
        return None

    return [line for line in log.splitlines() if line]


def commit_paths(repo_root: Path, paths: list[str], message: str) -> str | None:
    # Commits exactly `paths` (anything else staged is left alone); None on
    # failure. Unchanged paths return the current HEAD — already committed
    # is what callers care about.
    status = _run(repo_root, "status", "--porcelain", "--", *paths)
    if status is None or status.returncode != 0:
        return None
    if not status.stdout.strip():
        return _text(repo_root, "rev-parse", "HEAD")
    add = _run(repo_root, "add", "--", *paths)
    if add is None or add.returncode != 0:
        return None
    commit = _run(repo_root, "commit", "-m", message, "--", *paths)
    if commit is None or commit.returncode != 0:
        return None
    return _text(repo_root, "rev-parse", "HEAD")


def normalize_git_url(url: str) -> str:
    url = url.strip().removesuffix(".git")
    match = re.match(r"git@([^:]+):(.+)$", url) or re.match(
        r"ssh://(?:[^@/]+@)?([^/:]+)(?::\d+)?/(.+)$", url
    )
    if match:
        url = f"https://{match.group(1)}/{match.group(2)}"
    return url.lower().rstrip("/")
