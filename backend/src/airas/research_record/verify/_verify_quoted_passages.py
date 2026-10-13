from __future__ import annotations

from pathlib import Path

from airas.core.hashing import file_sha256
from airas.core.research_paths import SOURCES_DIR
from airas.core.types.record_verification import RecordVerification
from airas.core.types.research_record import (
    LiteratureSource,
    ResearchRecord,
    Snapshot,
)
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


def _snapshot_text(
    root: Path,
    source: LiteratureSource,
    snapshot: Snapshot,
    verification: RecordVerification,
) -> str | None:
    field, relpath, ref = snapshot
    path = f"literature[{source.id}]/{field}"
    what = field.removesuffix("/snapshot")
    if ref is None or ref.path != relpath:
        problem = f"{what} snapshot must be {relpath} (preregister_record writes it)"
    elif not (root / relpath).resolve().is_relative_to(root.resolve()):
        problem = f"{relpath} resolves outside the repository"
    elif not (root / relpath).is_file():
        problem = f"{relpath} is missing (preregister_record writes it)"
    elif file_sha256(root / relpath) != ref.sha256:
        problem = f"{relpath} does not match the sha256 the record holds"
    else:
        verification.append_declaration_status(
            path, f"sha256 of {relpath}", "verified", evidence_path=relpath
        )
        return (root / relpath).read_text(encoding="utf-8")
    verification.append_declaration_status(
        path, f"source {source.id}: {problem}", "mismatch", evidence_path=relpath
    )
    return None


def verify_quoted_passages(
    root: Path, record: ResearchRecord, verification: RecordVerification
) -> None:
    """A source is confirmed by a registry and every passage quoted from it
    is verbatim in its paper's text or one of its repositories' snapshots."""
    # TODO: authors, year and venue are what the agent passed; only the
    # identifier's existence and the title in the PDF are checked.
    # TODO: the agent finds papers by unconstrained web search; the record
    # shows what it read, not whether it also found test data or answers.
    for source in record.latest_literature():
        source_path = f"literature[{source.id}]"
        verification.append_declaration_status(
            f"{source_path}/verified_by",
            "a registry consulted at preregistration"
            if source.verified_by
            else f"source {source.id}: no registry verified it (preregister_record does)",
            "verified" if source.verified_by else "mismatch",
        )
        texts = [
            _snapshot_text(root, source, snapshot, verification)
            for snapshot in source.snapshots()
        ]
        for passage in source.passages:
            quote_path = f"{source_path}/passages[{passage.id}]/quote"
            if None in texts:
                verification.append_declaration_status(
                    quote_path,
                    "a snapshot of the source is missing or altered",
                    "unverified",
                    evidence_path=f"{SOURCES_DIR}/{source.id}/",
                )
            elif any(passage_is_quoted(t, passage.quote) for t in texts if t):
                verification.append_declaration_status(
                    quote_path,
                    f"verbatim in {SOURCES_DIR}/{source.id}/",
                    "verified",
                    evidence_path=f"{SOURCES_DIR}/{source.id}/",
                )
            else:
                verification.append_declaration_status(
                    quote_path,
                    f"passage {passage.id}: quote is not found verbatim in {SOURCES_DIR}/{source.id}/",
                    "mismatch",
                    evidence_path=f"{SOURCES_DIR}/{source.id}/",
                )
