import json
from pathlib import Path
from typing import Any

from airas.core.research_paths import (
    FULLTEXT_FILENAME,
    PAGE_SEPARATOR,
    SOURCE_METADATA_FILENAME,
    SOURCES_DIR,
)
from airas.core.types.literature_material import (
    LiteratureMaterial,
    RepositoryMaterial,
)


def _pages(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").split(PAGE_SEPARATOR)


def load_imported_source(
    root: Path, source_id: str, passages: list[dict[str, Any]]
) -> LiteratureMaterial:
    """The source fetch_literature.yml put in .research/sources/<id>/, as the
    record pins it: the search row for its metadata, the fetched text (or,
    for an airas_records study, record.json at its commit) for its quotes."""
    source_dir = root / SOURCES_DIR / source_id
    metadata_path = source_dir / SOURCE_METADATA_FILENAME
    if not metadata_path.is_file():
        raise ValueError(
            f"{SOURCES_DIR}/{source_id} was not imported — dispatch_literature_fetch "
            "puts sources there; pull the branch once its run completes"
        )

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    published = metadata.get("published_date") or ""
    common: dict[str, Any] = {
        "title": metadata["title"],
        "authors": metadata.get("authors") or [],
        "year": int(published[:4]) if published[:4].isdigit() else None,
        "venue": metadata.get("venue") or "",
        "doi": metadata.get("doi"),
        "arxiv_id": metadata.get("arxiv_id"),
        "url": metadata.get("url"),
        "verified_by": metadata["source"],
        "verified_at": metadata["fetched_at"],
        "passages": passages,
    }

    if metadata["source"] == "airas_records":
        snapshot = metadata.get("snapshot") or {}
        if "error" in snapshot or not (source_dir / "r1.txt").is_file():
            raise ValueError(
                f"{source_id}: the study's record.json could not be fetched "
                f"({snapshot.get('error')}) — cite another source"
            )

        return LiteratureMaterial(
            **common,
            parser="git show",
            repositories=[
                RepositoryMaterial(
                    url=snapshot["url"],
                    commit=snapshot["commit"],
                    pages=_pages(source_dir / "r1.txt"),
                )
            ],
        )

    fulltext = metadata.get("fulltext") or {}
    # 本文が無いと passage の quote を照合する相手が無い
    if "error" in fulltext or not (source_dir / FULLTEXT_FILENAME).is_file():
        raise ValueError(
            f"{source_id}: no text was fetched ({fulltext.get('error')}) — "
            "cite another source"
        )

    return LiteratureMaterial(
        **common,
        parser=fulltext["parser"],
        pages=_pages(source_dir / FULLTEXT_FILENAME),
    )
