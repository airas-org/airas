"""Pinning a source's text: the snapshot its quoted passages are checked against."""

from __future__ import annotations

import contextlib
import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from airas.core.research_paths import FULLTEXT_FILENAME, PAGE_SEPARATOR, SOURCES_DIR
from airas.core.types.research_record import InputRef
from airas.research_record.read_run_outputs import file_sha256


def write_fulltext(root: Path, source_id: str, pages: list[str]) -> InputRef:
    relpath = f"{SOURCES_DIR}/{source_id}/{FULLTEXT_FILENAME}"
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    if any(p.is_symlink() for p in (path, *path.parents[:2])) or not (
        path.resolve().is_relative_to(root.resolve())
    ):
        raise ValueError(f"{relpath} is a symlink or leaves the repository")
    path.write_text(PAGE_SEPARATOR.join(pages), encoding="utf-8")
    return InputRef(path=relpath, sha256=file_sha256(path))


def snapshot_repository(
    url: str, commit: str, files: list[str], optional_files: Sequence[str] = ()
) -> tuple[dict[str, Any], list[str]]:
    """Metadata and one snapshot page per file, read from `commit` of the
    repository at `url`; the fetch succeeding is what confirms it exists.
    An `optional_files` entry absent at the commit is left out."""
    with tempfile.TemporaryDirectory() as tmp:

        def git(*args: str) -> str:
            done = subprocess.run(
                ["git", "-C", tmp, *args], capture_output=True, text=True, timeout=300
            )
            if done.returncode != 0:
                raise ValueError(
                    f"git {args[0]} failed for {url}@{commit}: {done.stderr.strip()}"
                )
            return done.stdout

        git("init", "-q")
        git("fetch", "-q", "--depth", "1", url, commit)
        pages = [
            f"==> {path} <==\n{git('show', f'FETCH_HEAD:{path}')}" for path in files
        ]
        for path in optional_files:
            with contextlib.suppress(ValueError):
                pages.append(f"==> {path} <==\n{git('show', f'FETCH_HEAD:{path}')}")
        year = int(git("log", "-1", "--format=%cs", "FETCH_HEAD")[:4])
    name = url.rstrip("/").removesuffix(".git").rsplit("/", 2)
    return (
        {
            "title": "/".join(name[-2:]),
            "authors": name[-2:-1],
            "year": year,
            "url": url,
            "commit": commit,
        },
        pages,
    )
