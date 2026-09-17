"""Each citation of a passage, read against the passage: does the citing
text say only what the passage supports? A model judges once and its
verdict is recorded on the passage; without a model, only recorded verdicts
count and an unjudged citation is reported."""

from __future__ import annotations

import asyncio
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field

from airas.core.research_paths import FULLTEXT_FILENAME, SOURCES_DIR
from airas.core.types.research_record import (
    PASSAGE_ID_PATTERN,
    CitationJudgment,
    QuotedPassage,
    ResearchRecord,
)
from airas.infra.litellm_client import LiteLLMClient
from airas.research_record.verify._verify_quoted_passages import quote_context

_CITE_WITH_LOCATOR = re.compile(r"\\cite[pt]?\*?\[([^\]]*)\]\{[^}]*\}")

# Enough of a paragraph to see the sentence the \cite sits in.
_WINDOW = 500


@dataclass(frozen=True)
class _Citation:
    where: str  # "main.tex \cite[s1.p2]{key}"
    text: str
    passage: QuotedPassage
    context: str  # the quote in its snapshot, with the text around it

    @property
    def text_sha256(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()


def _collect_citations(
    root: Path, record: ResearchRecord, main_tex: str
) -> list[_Citation]:
    """`main_tex` is comment-stripped. A passage no source declares is
    skipped: the gate reports that on its own. A hypothesis's `grounded_on`
    and a claim's `cites_passages` are not judged: they are conjectures that
    by design say more than the passages they build on, and the gate already
    checks that every passage they name exists."""
    passages = record.passage_index()
    fulltexts: dict[str, str] = {}
    citations: list[_Citation] = []

    def cite(where: str, text: str, passage_id: str) -> None:
        if (found := passages.get(passage_id)) is None:
            return
        source, passage = found
        if source.id not in fulltexts:
            # The canonical path the gate requires, not the record's own
            # `fulltext.path`: a crafted record must not choose what is read.
            path = root / SOURCES_DIR / source.id / FULLTEXT_FILENAME
            fulltexts[source.id] = (
                path.read_text(encoding="utf-8") if path.is_file() else ""
            )
        context = quote_context(fulltexts[source.id], passage.quote) or passage.quote
        citations.append(_Citation(where, text, passage, context))

    for paragraph in re.split(r"\n\s*\n", main_tex):
        for match in _CITE_WITH_LOCATOR.finditer(paragraph):
            locator = match.group(1).strip()
            if not re.fullmatch(PASSAGE_ID_PATTERN, locator):
                continue
            start, end = match.span()
            text = paragraph[max(0, start - _WINDOW) : end + _WINDOW].strip()
            cite(f"main.tex {match.group(0)}", text, locator)
    return citations


def _judgment_of(citation: _Citation) -> CitationJudgment | None:
    """The latest judgment of this citing text, as it stands."""
    return next(
        (
            j
            for j in reversed(citation.passage.judgments)
            if j.text_sha256 == citation.text_sha256
        ),
        None,
    )


class _CitationVerdict(BaseModel):
    supported: bool = Field(
        description="The citing text says only what the passage, read in its "
        "context, supports"
    )
    reason: str = Field(
        default="",
        description="One line: what the text adds, drops or reverses. Empty "
        "when supported",
    )


_PROMPT = """\
You are checking a citation in a research paper for fidelity.

The passage below is quoted verbatim from a cited source and shown inside \
the text that surrounds it there. The citing text claims to rest on that \
passage.

Decide whether the citing text says only what the passage, read in its \
context, supports. It is unsupported when it overstates, generalizes beyond \
the passage's conditions, reverses or drops a negation or a qualifier that \
the context carries, or attributes to the source something the passage does \
not say. A faithful paraphrase or summary is supported. Judge the fidelity of \
the citation, not whether the claim is true.

## Citing text ({where})
{text}

## Quoted passage {passage_id}
{quote}

## The passage in its source
…{context}…
"""


async def _judge(
    client: LiteLLMClient, model: str, citation: _Citation
) -> _CitationVerdict:
    verdict = await client.structured_output(
        llm_name=model,
        message=_PROMPT.format(
            where=citation.where,
            text=citation.text,
            passage_id=citation.passage.id,
            quote=citation.passage.quote,
            context=citation.context,
        ),
        data_model=_CitationVerdict,
    )
    if verdict is None:
        raise ValueError(f"no verdict from {model} for {citation.where}")
    return verdict


async def verify_citation_meaning(
    root: Path,
    record: ResearchRecord,
    main_tex: str,
    *,
    model: str | None = None,
    litellm_client: LiteLLMClient | None = None,
) -> tuple[list[str], list[str], int]:
    """(citations no judgment covers, citations judged unsupported, judgments
    written). `main_tex` is comment-stripped. With `model`, every unjudged
    citation is judged first and the verdict appended to its passage — the
    caller saves the record."""
    citations = _collect_citations(root, record, main_tex)
    judged = 0
    if model is not None:
        if litellm_client is None:
            raise ValueError("a model needs a litellm_client")
        pending = [c for c in citations if _judgment_of(c) is None]
        verdicts = await asyncio.gather(
            *(_judge(litellm_client, model, c) for c in pending)
        )
        for citation, verdict in zip(pending, verdicts, strict=True):
            citation.passage.judgments.append(
                CitationJudgment(
                    text_sha256=citation.text_sha256,
                    model=model,
                    supported=verdict.supported,
                    reason=verdict.reason,
                )
            )
        judged = len(pending)

    unjudged: list[str] = []
    unsupported: list[str] = []
    for citation in citations:
        label = f"{citation.where} cites {citation.passage.id}"
        judgment = _judgment_of(citation)
        if judgment is None:
            unjudged.append(label)
        elif not judgment.supported:
            reason = judgment.reason or "not supported by the passage"
            unsupported.append(f"{label}: {reason} ({judgment.model})")
    return unjudged, unsupported, judged
