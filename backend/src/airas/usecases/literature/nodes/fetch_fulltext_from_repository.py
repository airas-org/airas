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
    A directory in `files` stands for every text file under it (a package
    snapshotted whole, so the gate can hash its modules); binary files are
    left out. An `optional_files` entry absent at the commit is left out."""
    with tempfile.TemporaryDirectory() as tmp:

        def git(*args: str) -> bytes:
            done = subprocess.run(
                ["git", "-C", tmp, *args], capture_output=True, timeout=300
            )
            if done.returncode != 0:
                raise ValueError(
                    f"git {args[0]} failed for {url}@{commit}: "
                    f"{done.stderr.decode(errors='replace').strip()}"
                )
            return done.stdout

        def pages_under(path: str) -> list[str]:
            listed = git("ls-tree", "-r", "--name-only", "FETCH_HEAD", "--", path)
            if not listed:
                raise ValueError(f"'{path}' is not in {url}@{commit}")

            pages = []
            for file in listed.decode().splitlines():
                raw = git("show", f"FETCH_HEAD:{file}")
                if b"\0" in raw:  # binary, as git judges it
                    continue
                with contextlib.suppress(UnicodeDecodeError):
                    pages.append(f"==> {file} <==\n{raw.decode()}")
            return pages

        git("init", "-q")
        git("fetch", "-q", "--depth", "1", url, commit)
        pages = [page for path in files for page in pages_under(path)]
        for path in optional_files:
            with contextlib.suppress(ValueError):
                pages += pages_under(path)
        year = int(git("log", "-1", "--format=%cs", "FETCH_HEAD").decode()[:4])
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
