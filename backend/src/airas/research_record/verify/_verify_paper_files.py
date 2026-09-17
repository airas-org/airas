"""Every generated file under .research/latex/<template>/ — references.bib, claims.tex, values.tex, tables/, and the charts — equals its regeneration from the record, and every \\cite names a registered source and passage."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

from airas.core.research_paths import RECORD_FILENAME, REFERENCES_BIB_FILENAME
from airas.core.types.map_record_to_publication import TableSpec
from airas.core.types.research_record import PASSAGE_ID_PATTERN, ResearchRecord
from airas.infra.local_git import normalize_git_url, remote_origin_url
from airas.research_record.read.scan_main_tex import scan_citations, scan_main_tex
from airas.research_record.render.render_charts import (
    CHART_DIR,
    CHART_SUFFIXES,
    render_chart_bytes,
    renderer_version,
    substitute_chart_refs,
)
from airas.research_record.render.render_claims_tex import (
    CLAIMS_TEX_FILENAME,
    render_claims_tex,
)
from airas.research_record.render.render_paper_values import (
    VALUES_TEX_FILENAME,
    record_link_commit,
    render_values_tex,
    resolve_paper_values,
)
from airas.research_record.render.render_references_bib import render_references_bib
from airas.research_record.render.render_tables import TABLES_DIR_NAME, render_table_tex


def _verify_paper_citations(
    record: ResearchRecord, main_tex: str
) -> tuple[list[str], list[str]]:
    """Every cited key is a registered source and every passage locator one
    of that source's passages. Returns (problems, bibkeys never cited)."""
    by_key = {source.bibkey: source for source in record.active_literature()}
    passages = record.passage_index()
    problems: dict[str, None] = {}
    cited: set[str] = set()
    for locator, keys in scan_citations(main_tex):
        for key in keys:
            if key in by_key:
                cited.add(key)
            else:
                problems[
                    f"main.tex cites '{key}', which no source in record.json "
                    "declares (preregister_record adds one)"
                ] = None
        if not (locator and re.fullmatch(PASSAGE_ID_PATTERN, locator)):
            continue
        if len(keys) != 1:
            problems[
                f"main.tex cites passage '{locator}' against several keys "
                f"({', '.join(keys)}) — a passage belongs to one source"
            ] = None
        elif locator not in passages or passages[locator][0].bibkey != keys[0]:
            problems[
                f"main.tex cites '{keys[0]}' at '{locator}', which is not a "
                "passage of that source"
            ] = None
    return list(problems), [key for key in by_key if key not in cited]


def _verify_references_bib(latex_dir: Path, record: ResearchRecord) -> list[str]:
    path = latex_dir / REFERENCES_BIB_FILENAME
    if not path.is_file():
        return [f"{REFERENCES_BIB_FILENAME} is missing (preregister_record writes it)"]
    if path.read_text(encoding="utf-8") != render_references_bib(
        record.active_literature()
    ):
        return [
            f"{REFERENCES_BIB_FILENAME} differs from its regeneration from the "
            "record's literature (preregister_record writes it)"
        ]
    return []


def _verify_claims_tex(
    latex_dir: Path, record: ResearchRecord, metrics_data: dict[str, Any]
) -> list[str]:
    # The list in the PDF is the record's, at the prereg stage (pending) as
    # after results.
    claims_path = latex_dir / CLAIMS_TEX_FILENAME
    if not claims_path.is_file():
        return [f"{CLAIMS_TEX_FILENAME} is missing (preregister_record writes it)"]
    if claims_path.read_text(encoding="utf-8") != render_claims_tex(
        record, metrics_data
    ):
        return [f"{CLAIMS_TEX_FILENAME} differs from its regeneration (manual edit?)"]
    return []


def _verify_values_tex(
    root: Path,
    latex_dir: Path,
    record: ResearchRecord,
    metrics_data: dict[str, Any],
    used_keys: list[str],
) -> list[str]:
    values_tex_path = latex_dir / VALUES_TEX_FILENAME
    problems: list[str] = []
    paper_values, undefined_keys = resolve_paper_values(record, metrics_data, used_keys)
    if undefined_keys:
        problems.append(
            "\\airasval keys main.tex references that record.json does not declare: "
            + ", ".join(undefined_keys)
        )
    if values_tex_path.is_file():
        origin = remote_origin_url(root)
        expected = render_values_tex(
            paper_values,
            normalize_git_url(origin) if origin else None,
            record_link_commit(root),
        )
        if values_tex_path.read_text(encoding="utf-8") != expected:
            problems.append(
                f"{VALUES_TEX_FILENAME} differs from its regeneration (manual edit?)"
            )
    return problems


def _verify_tables(
    latex_dir: Path, specs: list[TableSpec], metrics_data: dict[str, Any]
) -> list[str]:
    # The undeclared-file check matters as much as the diff: without it a
    # hand-written tables/<name>.tex could be \input alongside the
    # generated ones and carry any numbers at all.
    problems: list[str] = []
    registered: set[str] = set()
    for spec in specs:
        registered.add(f"{spec.key}.tex")
        relpath = f"{TABLES_DIR_NAME}/{spec.key}.tex"
        table_path = latex_dir / relpath
        if not table_path.is_file():
            problems.append(f"{relpath} is missing (update_record writes it)")
            continue
        try:
            expected = render_table_tex(spec, metrics_data)
        except ValueError as e:
            problems.append(f"{relpath}: {e}")
            continue
        if table_path.read_text(encoding="utf-8") != expected:
            problems.append(f"{relpath} differs from its regeneration (manual edit?)")
    tables_dir = latex_dir / TABLES_DIR_NAME
    if tables_dir.is_dir():
        for table_path in sorted(tables_dir.rglob("*.tex")):
            relative = table_path.relative_to(tables_dir).as_posix()
            if relative not in registered:
                problems.append(
                    f"{TABLES_DIR_NAME}/{relative} is not declared in "
                    f"{RECORD_FILENAME} — table files here must come from "
                    "update_record"
                )
    return problems


def _verify_charts(
    record: ResearchRecord, local_repo_path: str, metrics_data: dict[str, Any]
) -> list[str]:
    """Re-render every declared chart; reject undeclared chart files."""

    chart_dir = Path(local_repo_path).expanduser().resolve() / CHART_DIR
    charts = record.active_charts()
    declared = {c.path: c for c in charts}
    renderers = {c.path: c.renders[-1].renderer for c in charts if c.renders}

    problems: list[str] = []
    if chart_dir.is_dir():
        # Recursive: the LaTeX export collects figures from any depth under
        # .research/results/, so a chart hidden in a subdirectory must not
        # escape the declaration requirement.
        for chart_path in sorted(chart_dir.rglob("*")):
            if not chart_path.is_file():
                continue
            if chart_path.suffix.lower() not in CHART_SUFFIXES:
                continue
            relative = chart_path.relative_to(chart_dir).as_posix()
            if relative not in declared:
                problems.append(
                    f"{CHART_DIR}/{relative} is not declared in record.json — "
                    "its data has no declared source (render_chart declares "
                    "and renders in one step)"
                )

    for relative, declaration in declared.items():
        chart_path = chart_dir / relative
        if not chart_path.is_file():
            problems.append(
                f"{CHART_DIR}/{relative} is declared but missing "
                "(render_chart writes it)"
            )
            continue
        try:
            resolved, _ = substitute_chart_refs(declaration.spec, metrics_data)
            expected = render_chart_bytes(resolved, declaration.format)
        except Exception as e:
            problems.append(
                f"{CHART_DIR}/{relative}: spec could not be re-rendered: {e}"
            )
            continue
        if chart_path.read_bytes() != expected:
            recorded = renderers.get(relative, "unknown renderer")
            hint = (
                ""
                if recorded == renderer_version()
                else (
                    f" (rendered with {recorded}, verifying with "
                    f"{renderer_version()} — re-render to rule out a "
                    "renderer version difference)"
                )
            )
            problems.append(
                f"{CHART_DIR}/{relative}: file differs from a re-render of "
                f"its declared spec{hint}"
            )
    return problems


def verify_paper_files(
    root: Path,
    template: str,
    record: ResearchRecord,
    metrics_data: dict[str, Any],
    main_tex: str,
    stage: Literal["prereg", "results"],
) -> tuple[list[str], list[str], list[str]]:
    """(problems, \\unverified marks for human review, registered sources the
    paper never cites). Every generated file matches its regeneration."""
    latex_dir = root / ".research" / "latex" / template
    values_tex_path = latex_dir / VALUES_TEX_FILENAME
    unverified, used_keys = scan_main_tex(main_tex) if main_tex else ([], [])
    problems = _verify_claims_tex(latex_dir, record, metrics_data)
    uncited: list[str] = []
    if record.active_literature():
        cited_problems, uncited = _verify_paper_citations(record, main_tex)
        problems += cited_problems + _verify_references_bib(latex_dir, record)
    if stage == "prereg":
        # A values.tex carried over without runs would put unverifiable
        # numbers in the PDF.
        if values_tex_path.is_file():
            problems.append(f"{VALUES_TEX_FILENAME} exists but no run outputs exist")
        if (latex_dir / TABLES_DIR_NAME).is_dir():
            problems.append(f"{TABLES_DIR_NAME}/ exists but no run outputs exist")
        return problems, unverified, uncited
    problems += _verify_values_tex(root, latex_dir, record, metrics_data, used_keys)
    problems += _verify_tables(latex_dir, record.active_tables(), metrics_data)
    problems += _verify_charts(record, str(root), metrics_data)
    return problems, unverified, uncited
