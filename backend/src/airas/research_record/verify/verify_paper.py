"""The paper gate: every number, table, chart, claim and citation in the paper
is the record's. With a model, unjudged citations are judged on the way and
the judgments written into the record."""

from __future__ import annotations

import asyncio
from typing import Literal

from pydantic import ValidationError

from airas.core.research_paths import RECORD_PATH, repo_root
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.core.types.paper_verification import PaperVerification
from airas.core.types.research_record import ResearchRecord
from airas.infra.litellm_client import LiteLLMClient
from airas.infra.local_git import commit_paths
from airas.research_record.llm_as_a_judge.judge_citation_against_passage import (
    judge_citation_against_passage,
)
from airas.research_record.read.read_run_outputs import (
    load_metrics_data,
    run_ids_with_verifier_report,
)
from airas.research_record.read.scan_main_tex import without_comments
from airas.research_record.render.render_claims_tex import write_claims_tex
from airas.research_record.render.render_paper_values import VALUES_TEX_FILENAME
from airas.research_record.verify._verify_paper_files import verify_paper_files


async def verify_paper(
    local_path: str,
    template: LATEX_TEMPLATE_NAME,
    *,
    citation_verifier_model: str | None = None,
    litellm_client: LiteLLMClient | None = None,
) -> PaperVerification:
    root = repo_root(local_path)
    try:
        record = ResearchRecord.load(str(root))
    except (ValidationError, ValueError) as e:
        return PaperVerification(ok=False, template=template, problems=[str(e)])

    try:
        metrics_data = load_metrics_data(str(root))
    except ValueError:
        metrics_data = {}

    stage: Literal["prereg", "results"] = (
        "results"
        if metrics_data or run_ids_with_verifier_report(root, record)
        else "prereg"
    )

    latex_dir = root / ".research" / "latex" / template
    main_tex_path = latex_dir / "main.tex"
    main_tex = (
        main_tex_path.read_text(encoding="utf-8") if main_tex_path.is_file() else ""
    )
    required = [main_tex_path]

    if stage == "results":
        required.append(latex_dir / VALUES_TEX_FILENAME)
    problems = (
        [
            "missing: "
            + ", ".join(str(p.relative_to(root)) for p in required if not p.is_file())
        ]
        if any(not p.is_file() for p in required)
        else []
    )

    unverified: list[str] = []
    uncited: list[str] = []
    unjudged: list[str] = []
    unsupported: list[str] = []
    if record.latest_literature():
        unjudged, unsupported, judged = await judge_citation_against_passage(
            root,
            record,
            without_comments(main_tex),
            model=citation_verifier_model,
            litellm_client=litellm_client,
        )
        if judged:
            record.save(local_path)
            claims_tex = write_claims_tex(local_path, template, record)
            commit_paths(root, [RECORD_PATH, claims_tex], "record: judge citations")
        problems += [
            f"{label}: no judgment covers the citing text as it stands "
            "(verify with a model to write one)"
            for label in unjudged
        ]
    file_problems, unverified, uncited = await asyncio.to_thread(
        verify_paper_files,
        root,
        template,
        record,
        metrics_data,
        main_tex,
        stage,
    )
    problems += file_problems
    return PaperVerification(
        ok=not problems,
        template=template,
        stage=stage,
        problems=problems,
        unverified=unverified,
        uncited_sources=uncited,
        unjudged_citations=unjudged,
        unsupported_citations=unsupported,
    )
