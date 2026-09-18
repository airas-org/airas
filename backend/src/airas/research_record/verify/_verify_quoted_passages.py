from __future__ import annotations

from pathlib import Path

from airas.core.research_paths import FULLTEXT_FILENAME, SOURCES_DIR
from airas.core.types.research_record import ResearchRecord
from airas.research_record.read.find_quote import find_quote
from airas.research_record.read.read_run_outputs import file_sha256


def passage_is_quoted(fulltext: str, quote: str) -> bool:
    return find_quote(fulltext, quote) is not None


def quote_context(fulltext: str, quote: str, margin: int = 600) -> str | None:
    """The quote with `margin` characters of its snapshot either side."""
    found = find_quote(fulltext, quote)
    if found is None:
        return None
    hay, start, end = found
    return hay[max(0, start - margin) : end + margin]


def verify_quoted_passages(root: Path, record: ResearchRecord) -> list[str]:
    """A source is confirmed by a registry and every passage quoted from it
    is verbatim in its snapshot — the same check whatever the source's
    origin."""
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
        expected = f"{SOURCES_DIR}/{source.id}/{FULLTEXT_FILENAME}"
        if source.fulltext is None or source.fulltext.path != expected:
            problems.append(
                f"source {source.id}: fulltext snapshot must be {expected} "
                "(preregister_record writes it)"
            )
            continue
        path = root / source.fulltext.path
        if not path.resolve().is_relative_to(root.resolve()):
            problems.append(
                f"source {source.id}: {expected} resolves outside the repository"
            )
            continue
        if not path.is_file():
            problems.append(
                f"source {source.id}: {source.fulltext.path} is missing "
                "(preregister_record writes it)"
            )
            continue
        if file_sha256(path) != source.fulltext.sha256:
            problems.append(
                f"source {source.id}: {source.fulltext.path} does not match the "
                "sha256 the record holds"
            )
            continue
        fulltext = path.read_text(encoding="utf-8")
        problems += [
            f"passage {p.id}: quote is not found verbatim in {source.fulltext.path}"
            for p in source.passages
            if not passage_is_quoted(fulltext, p.quote)
        ]
    return problems
