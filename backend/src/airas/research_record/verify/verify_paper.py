"""The paper gate: every number, table, chart, claim and citation in the paper
is the record's. With a model, unjudged citations are judged on the way and
the judgments written into the record."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path

from pydantic import ValidationError

from airas.core.research_paths import RECORD_PATH
from airas.core.types.latex import LATEX_TEMPLATE_NAME, LatexBuildReport
from airas.core.types.paper_verification import PaperVerification
from airas.core.types.record_verification import RecordVerification
from airas.infra.litellm_client import LiteLLMClient
from airas.infra.local_git import commit_paths
from airas.infra.run_output_store import default_store
from airas.research_record.read.load_record import load_record
from airas.research_record.read.read_run_outputs import load_metrics_data
from airas.research_record.read.scan_main_tex import without_comments
from airas.research_record.render.render_claims_tex import write_claims_tex
from airas.research_record.render.render_paper_values import VALUES_TEX_FILENAME
from airas.research_record.verify._verify_citation_meaning import (
    verify_citation_meaning,
)
from airas.research_record.verify._verify_paper_files import verify_paper_files
from airas.research_record.verify._verify_results_against_store import StoreFactory
from airas.research_record.verify.verify_record import verify_record


async def verify_paper(
    local_path: str,
    template: LATEX_TEMPLATE_NAME,
    *,
    pdf_path: str | None = None,
    build: Callable[[str, LATEX_TEMPLATE_NAME, str], LatexBuildReport] | None = None,
    check_provenance: bool = True,
    require_record: bool = True,
    require_provenance: bool = True,
    require_history: bool = True,
    store_factory: StoreFactory = default_store,
    record: RecordVerification | None = None,
    model: str | None = None,
    litellm_client: LiteLLMClient | None = None,
) -> PaperVerification:
    """The paper's numbers are the record's, and the record holds; then, optionally, it builds."""
    if record is None:
        record = await verify_record(
            local_path,
            check_provenance=check_provenance,
            require_provenance=require_provenance,
            require_history=require_history,
            require_record=require_record,
            store_factory=store_factory,
        )
    root = Path(local_path).expanduser().resolve()
    latex_dir = root / ".research" / "latex" / template
    main_tex_path = latex_dir / "main.tex"
    main_tex = (
        main_tex_path.read_text(encoding="utf-8") if main_tex_path.is_file() else ""
    )
    required = [main_tex_path]
    if record.stage == "results":
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
    try:
        declared = load_record(str(root))
    except (ValidationError, ValueError):
        declared = None  # the record's own verification already reports this
    if declared is not None:
        try:
            metrics_data = load_metrics_data(str(root))
        except ValueError:
            metrics_data = {}
        if declared.active_literature():
            # Judged first, so claims.tex below is compared against the record
            # as it stands after the judgments.
            unjudged, unsupported, judged = await verify_citation_meaning(
                root,
                declared,
                without_comments(main_tex),
                model=model,
                litellm_client=litellm_client,
            )
            if judged:
                declared.save(local_path)
                claims_tex = write_claims_tex(local_path, template, declared)
                commit_paths(root, [RECORD_PATH, claims_tex], "record: judge citations")
            # Judged is required, supported is not: a citation nobody read as
            # it stands is the gap the judge exists to close.
            problems += [
                f"{label}: no judgment covers the citing text as it stands "
                "(verify with a model to write one)"
                for label in unjudged
            ]
        file_problems, unverified, uncited = await asyncio.to_thread(
            verify_paper_files,
            root,
            template,
            declared,
            metrics_data,
            main_tex,
            record.stage,
        )
        problems += file_problems
    if require_record and not (root / RECORD_PATH).is_file():
        problems.append(
            "record.json is missing: the paper does not use the canonical-record "
            "system, so its claims and numbers cannot be verified "
            "(preregister_record creates it)"
        )
    build_report: LatexBuildReport | None = None
    if pdf_path is not None:
        if build is None:
            raise ValueError("pdf_path needs a build function")
        build_report = await asyncio.to_thread(build, local_path, template, pdf_path)
        if not build_report.ok:
            problems.append("the LaTeX build failed (see build)")

    ok = record.ok and not problems
    pdf: str | None = None
    if pdf_path is not None:
        # A PDF handed out states verified numbers, so a failed run has none.
        if ok and Path(pdf_path).is_file():
            pdf = pdf_path
        else:
            Path(pdf_path).unlink(missing_ok=True)
            if build_report is not None:
                build_report = build_report.model_copy(update={"pdf_path": None})
    return PaperVerification(
        ok=ok,
        template=template,
        record=record,
        problems=problems,
        unverified=unverified,
        uncited_sources=uncited,
        unjudged_citations=unjudged,
        unsupported_citations=unsupported,
        build=build_report,
        pdf=pdf,
    )
