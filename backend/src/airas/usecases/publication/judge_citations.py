"""Reading each citation against its passage, by a model that writes what it
found into the record."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from airas.core.research_paths import RECORD_PATH
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.core.types.research_record import CitationJudgment
from airas.infra.litellm_client import LiteLLMClient
from airas.research_record.citations import (
    Citation,
    collect_citations,
    judgment_of,
)
from airas.research_record.store import (
    commit_record_paths,
    load_record,
    record_path,
    save_record,
)
from airas.usecases.publication.verify_paper import without_comments
from airas.usecases.publication.write_tex_files import write_claims_tex


class CitationVerdict(BaseModel):
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
    client: LiteLLMClient, model: str, citation: Citation
) -> CitationVerdict:
    verdict = await client.structured_output(
        llm_name=model,
        message=_PROMPT.format(
            where=citation.where,
            text=citation.text,
            passage_id=citation.passage.id,
            quote=citation.passage.quote,
            context=citation.context,
        ),
        data_model=CitationVerdict,
    )
    if verdict is None:
        raise ValueError(f"no verdict from {model} for {citation.where}")
    return verdict


async def judge_citations(
    local_path: str,
    model: str,
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
    *,
    litellm_client: LiteLLMClient,
) -> dict[str, Any]:
    """Judge every citation not yet judged as it stands, and commit the
    judgments with the record."""
    root = Path(local_path).expanduser().resolve()
    record = load_record(local_path)
    main_tex_path = root / ".research" / "latex" / latex_template_name / "main.tex"
    main_tex = (
        without_comments(main_tex_path.read_text(encoding="utf-8"))
        if main_tex_path.is_file()
        else ""
    )
    pending = [
        c for c in collect_citations(root, record, main_tex) if judgment_of(c) is None
    ]
    verdicts = await asyncio.gather(
        *(_judge(litellm_client, model, c) for c in pending)
    )
    unsupported: list[str] = []
    for citation, verdict in zip(pending, verdicts, strict=True):
        citation.passage.judgments.append(
            CitationJudgment(
                text_sha256=citation.text_sha256,
                model=model,
                supported=verdict.supported,
                reason=verdict.reason,
            )
        )
        if not verdict.supported:
            unsupported.append(
                f"{citation.where} cites {citation.passage.id}: {verdict.reason}"
            )

    def _write() -> dict[str, Any]:
        commit = None
        if pending:
            save_record(local_path, record)
            claims_tex = write_claims_tex(local_path, latex_template_name, record)
            commit = commit_record_paths(
                local_path, [RECORD_PATH, claims_tex], "record: judge citations"
            )
        return {
            "record_path": str(record_path(local_path)),
            "judged": len(pending),
            "unsupported": unsupported,
            "commit": commit,
        }

    return await asyncio.to_thread(_write)
