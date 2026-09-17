from __future__ import annotations

import contextlib
import subprocess
import tempfile
from collections.abc import Sequence
from typing import Any


def fetch_fulltext_from_repository(
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
