"""Turn the agent's literature entries into materials the record can pin: a
source fetch_literature.yml imported, cited by its id, with the code the agent
chose snapshotted at a commit."""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from airas.core.types.literature_material import (
    LiteratureMaterial,
    RepositoryMaterial,
)
from airas.research_record.read.load_imported_source import load_imported_source
from airas.usecases.literature.nodes.fetch_fulltext_from_repository import (
    fetch_fulltext_from_repository,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


async def _repository(
    spec: dict[str, Any],
) -> tuple[dict[str, Any], RepositoryMaterial]:
    """`{"url", "commit", "files", "method_entry"?}`: the code at the commit,
    snapshotted whole; the fetch succeeding is what confirms it exists."""
    url, commit = (spec.get("url") or "").strip(), (spec.get("commit") or "").strip()
    if not (url and commit and spec.get("files")):
        raise ValueError("a repository needs url, commit and files")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError(
            f"'{url}': commit must be a full 40-hex sha, not '{commit}' — "
            "a branch or tag moves"
        )
    metadata, pages = await asyncio.to_thread(
        fetch_fulltext_from_repository, url, commit, list(spec["files"])
    )
    return metadata, RepositoryMaterial(
        url=url,
        commit=commit,
        pages=pages,
        method_entry=(spec.get("method_entry") or "").strip(),
    )


async def _code(entry: dict[str, Any]) -> LiteratureMaterial:
    """Repositories with no paper: the work is the code, named after the first."""
    fetched = [await _repository(spec) for spec in entry["repositories"]]
    metadata = fetched[0][0]
    return LiteratureMaterial(
        title=metadata["title"],
        authors=metadata["authors"],
        year=metadata["year"],
        url=metadata["url"],
        verified_by="git",
        verified_at=_now(),
        parser="git show",
        passages=entry.get("passages") or [],
        repositories=[repository for _, repository in fetched],
        bib_title=metadata["title"].rsplit("/", 1)[-1],
    )


async def resolve_literatures(
    root: Path, entries: list[dict[str, Any]]
) -> list[tuple[str | None, LiteratureMaterial]]:
    """`{"source_id", "passages"}` for an imported source,
    `{"repositories", "passages"}` for code with no paper (no id yet)."""
    materials: list[tuple[str | None, LiteratureMaterial]] = []
    for entry in entries:
        source_id = entry.get("source_id")
        if source_id:
            if entry.get("repositories"):
                raise ValueError(
                    f"{source_id}: cite the code a paper ships as a source of its "
                    "own (repositories alone), not inside the paper's entry"
                )
            materials.append(
                (
                    source_id,
                    load_imported_source(root, source_id, entry.get("passages") or []),
                )
            )
        elif entry.get("repositories"):
            materials.append((None, await _code(entry)))
        else:
            raise ValueError(
                f"{entry}: cite an imported source by source_id, or code by "
                "repositories"
            )
    return materials
