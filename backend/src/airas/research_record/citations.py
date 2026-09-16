from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from airas.core.types.research_record import (
    PASSAGE_ID_PATTERN,
    CitationJudgment,
    QuotedPassage,
    ResearchRecord,
)
from airas.research_record.passages import quote_context

_CITE_WITH_LOCATOR = re.compile(r"\\cite[pt]?\*?\[([^\]]*)\]\{[^}]*\}")

# Enough of a paragraph to see the sentence the \cite sits in.
_WINDOW = 500


@dataclass(frozen=True)
class Citation:
    where: str  # "main.tex \cite[s1.p2]{key}", "hypothesis h1", "claim c1"
    text: str
    passage: QuotedPassage
    context: str  # the quote in its snapshot, with the text around it

    @property
    def text_sha256(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()


def collect_citations(
    root: Path, record: ResearchRecord, main_tex: str
) -> list[Citation]:
    """`main_tex` is comment-stripped. A passage no source declares is
    skipped: the gate reports that on its own."""
    passages = record.passage_index()
    fulltexts: dict[str, str] = {}
    citations: list[Citation] = []

    def cite(where: str, text: str, passage_id: str) -> None:
        if (found := passages.get(passage_id)) is None:
            return
        source, passage = found
        if source.id not in fulltexts:
            path = root / source.fulltext.path if source.fulltext else None
            fulltexts[source.id] = (
                path.read_text(encoding="utf-8") if path and path.is_file() else ""
            )
        context = quote_context(fulltexts[source.id], passage.quote) or passage.quote
        citations.append(Citation(where, text, passage, context))

    for paragraph in re.split(r"\n\s*\n", main_tex):
        for match in _CITE_WITH_LOCATOR.finditer(paragraph):
            locator = match.group(1).strip()
            if not re.fullmatch(PASSAGE_ID_PATTERN, locator):
                continue
            start, end = match.span()
            text = paragraph[max(0, start - _WINDOW) : end + _WINDOW].strip()
            cite(f"main.tex {match.group(0)}", text, locator)

    for hypothesis in record.active_hypotheses():
        for pid in hypothesis.grounded_on:
            cite(f"hypothesis {hypothesis.id}", hypothesis.statement, pid)
    for _, claim in record.active_claims():
        for pid in claim.cites_passages:
            text = f"{claim.statement} Rationale: {claim.rationale}"
            cite(f"claim {claim.id}", text, pid)
    return citations


def judgment_of(citation: Citation) -> CitationJudgment | None:
    """The latest judgment of this citing text, as it stands."""
    return next(
        (
            j
            for j in reversed(citation.passage.judgments)
            if j.text_sha256 == citation.text_sha256
        ),
        None,
    )


def review_citations(
    root: Path, record: ResearchRecord, main_tex: str
) -> tuple[list[str], list[str]]:
    """(citations no judgment covers, citations judged unsupported)."""
    # A record with no judgment at all is not using the judge.
    if not any(p.judgments for s in record.active_literature() for p in s.passages):
        return [], []
    unjudged: list[str] = []
    unsupported: list[str] = []
    for citation in collect_citations(root, record, main_tex):
        label = f"{citation.where} cites {citation.passage.id}"
        judgment = judgment_of(citation)
        if judgment is None:
            unjudged.append(label)
        elif not judgment.supported:
            reason = judgment.reason or "not supported by the passage"
            unsupported.append(f"{label}: {reason} ({judgment.model})")
    return unjudged, unsupported
