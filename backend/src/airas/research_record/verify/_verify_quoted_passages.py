from __future__ import annotations

from pathlib import Path

from airas.core.hashing import file_sha256
from airas.core.research_paths import (
    SOURCES_DIR,
    fulltext_relpath,
    repository_snapshot_relpath,
)
from airas.core.types.research_record import InputRef, ResearchRecord
from airas.research_record.read.find_quote import find_quote


def passage_is_quoted(fulltext: str, quote: str) -> bool:
    return find_quote(fulltext, quote) is not None


def quote_context(fulltext: str, quote: str, margin: int = 600) -> str | None:
    """The quote with `margin` characters of its snapshot either side."""
    found = find_quote(fulltext, quote)
    if found is None:
        return None
    hay, start, end = found
    return hay[max(0, start - margin) : end + margin]


def _read(
    root: Path,
    source_id: str,
    ref: InputRef | None,
    expected: str,
    what: str,
    problems: list[str],
) -> str | None:
    """The text a snapshot holds, if it is where the record says and unchanged."""
    if ref is None or ref.path != expected:
        problems.append(
            f"source {source_id}: {what} snapshot must be {expected} "
            "(preregister_record writes it)"
        )
        return None
    path = root / ref.path
    if not path.resolve().is_relative_to(root.resolve()):
        problems.append(
            f"source {source_id}: {expected} resolves outside the repository"
        )
        return None
    if not path.is_file():
        problems.append(
            f"source {source_id}: {ref.path} is missing (preregister_record writes it)"
        )
        return None
    if file_sha256(path) != ref.sha256:
        problems.append(
            f"source {source_id}: {ref.path} does not match the sha256 the record holds"
        )
        return None
    return path.read_text(encoding="utf-8")


def verify_quoted_passages(root: Path, record: ResearchRecord) -> list[str]:
    """A source is confirmed by a registry and every passage quoted from it
    is verbatim in its paper's text or one of its repositories' snapshots."""
    # TODO: authors, year and venue are what the agent passed; only the
    # identifier's existence and the title in the PDF are checked.
    # TODO: the agent finds papers by unconstrained web search; the record
    # shows what it read, not whether it also found test data or answers.
    problems: list[str] = []
    for source in record.active_literature():
        if not source.verified_by:
            problems.append(
                f"source {source.id}: no registry verified it (preregister_record does)"
            )
        texts = []
        if source.doi or source.arxiv_id or not source.repositories:
            texts.append(
                _read(
                    root,
                    source.id,
                    source.fulltext,
                    fulltext_relpath(source.id),
                    "fulltext",
                    problems,
                )
            )
        for repository in source.repositories:
            texts.append(
                _read(
                    root,
                    source.id,
                    repository.snapshot,
                    repository_snapshot_relpath(repository.id),
                    f"repository {repository.id}",
                    problems,
                )
            )
        found = [t for t in texts if t is not None]
        if len(found) < len(texts):
            continue
        problems += [
            f"passage {p.id}: quote is not found verbatim in {SOURCES_DIR}/{source.id}/"
            for p in source.passages
            if not any(passage_is_quoted(t, p.quote) for t in found)
        ]
    return problems
