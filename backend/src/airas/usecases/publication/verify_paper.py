from __future__ import annotations

import asyncio
import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable, get_args

from pydantic import ValidationError

from airas.core.research_paths import RECORD_FILENAME, RECORD_PATH
from airas.core.types.latex import LATEX_TEMPLATE_NAME, LatexBuildReport
from airas.core.types.map_record_to_publication import TableSpec
from airas.core.types.paper_verification import PaperVerification
from airas.core.types.record_verification import RecordVerification
from airas.core.types.research_record import ResearchRecord
from airas.infra.local_git import (
    commits_touching,
    normalize_git_url,
    remote_origin_url,
)
from airas.infra.seyval_client import SeyvalClient, default_seyval_client
from airas.usecases.publication.map_record_to_publication import (
    CHART_DIR,
    CHART_SUFFIXES,
    TABLES_DIR_NAME,
    VALUES_TEX_FILENAME,
    render_chart_bytes,
    render_table_tex,
    render_values_tex,
    renderer_version,
    resolve_paper_values,
    substitute_chart_refs,
    table_tex_relpath,
)
from airas.usecases.publication.open_in_overleaf_subgraph.nodes.collect_latex_project_files import (
    LUALATEX_ENGINE,
    collect_latex_project_files_local,
    select_engine,
)
from airas.usecases.recording.update_or_load_record import (
    load_metrics_data,
    load_record,
)
from airas.usecases.recording.verify_record import verify_record

logger = logging.getLogger(__name__)


# ------------------------------------------------------- the LaTeX build
# TeX wraps log lines at ~79 characters by default, which splits the very
# messages parsed below across lines. These are the documented knobs for
# turning that off; without them the regexes silently under-report.
_UNWRAPPED_LOG_ENV = {
    "max_print_line": "10000",
    "error_line": "254",
    "half_error_line": "238",
}

# The .tex being compiled comes out of a repository, so it is not trusted
# input. TeX can read and write arbitrary paths, and this tool hands the log
# tail back to the caller — `\input{/etc/passwd}` would be enough. Paranoid
# mode confines reads and writes to the build directory and TEXMF, and shell
# escape is refused outright rather than left to the distribution's default.
_SANDBOX_ENV = {"openin_any": "p", "openout_any": "p"}

_PDFLATEX_TIMEOUT_SECONDS = 180.0

_BIBTEX_TIMEOUT_SECONDS = 60.0

_LOG_TAIL_CHARS = 4000

_UNDEFINED_CITATION = re.compile(r"Citation [`'\"]([^`'\"]+)['\"] on page")

_UNDEFINED_REFERENCE = re.compile(r"Reference [`'\"]([^`'\"]+)['\"] on page")

_MISSING_FILE = re.compile(r"File [`'\"]([^`'\"]+)['\"] not found")

_ERROR_LINE = re.compile(r"^! (.+)$", re.MULTILINE)

# Extensions that a "File ... not found" can carry without it being a figure.
# A missing figure is usually reported with no extension at all, so this has
# to be a denylist: an allowlist of image formats would discard the real ones.
_NON_FIGURE_SUFFIXES = {".sty", ".cls", ".bib", ".bst", ".tex", ".def", ".cfg"}


class LatexToolchainMissingError(RuntimeError):
    """Raised when pdflatex is not installed on this machine."""


def _write_project(latex_files: dict[str, bytes], build_dir: Path) -> None:
    for relative_path, content in latex_files.items():
        target = build_dir / relative_path
        # The collector already rejects escaping paths; re-check because this
        # writes to disk outside the repository.
        if not target.resolve().is_relative_to(build_dir.resolve()):
            logger.warning(
                f"Skipping path outside the build directory: {relative_path}"
            )
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def _run(command: list[str], cwd: Path, timeout: float) -> subprocess.CompletedProcess:
    env = {**os.environ, **_UNWRAPPED_LOG_ENV, **_SANDBOX_ENV}
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=timeout,
        check=False,
    )


def _needs_bibtex(main_tex: str) -> bool:
    return "\\bibliography{" in main_tex or "\\bibliographystyle{" in main_tex


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _parse_log(log: str) -> tuple[list[str], list[str], list[str], list[str]]:
    citations = _dedupe(_UNDEFINED_CITATION.findall(log))
    references = _dedupe(_UNDEFINED_REFERENCE.findall(log))
    # TeX reports a missing graphic by the name it was asked for, which may
    # omit the extension the driver would have appended.
    missing_files = _dedupe(_MISSING_FILE.findall(log))
    errors = _dedupe(match.strip() for match in _ERROR_LINE.findall(log))
    return citations, references, missing_files, errors


def _save_pdf(pdf_path: Path, output_path: str | Path | None) -> str | None:
    """Copy the built PDF out of the scratch directory, if asked."""
    if output_path is None:
        return None
    destination = Path(output_path).expanduser()
    # A directory is the natural thing to pass when checking several
    # templates, so accept it and keep the document's own name.
    if destination.is_dir() or not destination.suffix:
        destination = destination / pdf_path.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(pdf_path, destination)
    logger.info(f"Wrote the verified PDF to {destination}")
    return str(destination)


def _page_count(pdf_path: Path) -> int | None:
    try:
        from pypdf import PdfReader

        return len(PdfReader(str(pdf_path)).pages)
    except Exception as e:
        logger.warning(f"Could not read page count from {pdf_path.name}: {e}")
        return None


def verify_latex_build(
    latex_files: dict[str, bytes],
    main_tex_name: str = "main.tex",
    output_path: str | Path | None = None,
) -> LatexBuildReport:
    """Build `latex_files` in a scratch directory and report the result.

    Runs the same engine/bibtex/engine/engine sequence the CI LaTeX agent
    uses, so the findings match what that agent would see. The engine is
    lualatex for a document containing CJK and pdflatex otherwise.

    The build happens in a temporary directory that is deleted afterwards,
    so pass `output_path` to keep the PDF. It is worth keeping: this is the
    one build whose result has been inspected, and for a Japanese paper it
    is currently the only way to get a PDF at all — the GitHub Actions
    workflow runs pdflatex, which cannot typeset CJK.
    """
    stem = Path(main_tex_name).stem

    with tempfile.TemporaryDirectory(prefix="airas-latex-") as tmp:
        build_dir = Path(tmp)
        _write_project(latex_files, build_dir)

        main_tex_path = build_dir / main_tex_name
        if not main_tex_path.is_file():
            raise ValueError(f"{main_tex_name} is not present in the collected project")

        source = main_tex_path.read_text(errors="replace")
        engine = select_engine(source)
        if shutil.which(engine) is None:
            raise LatexToolchainMissingError(
                f"{engine} was not found on PATH. "
                + (
                    "This document contains Japanese, which needs LuaTeX: "
                    "`apt-get install texlive-luatex texlive-lang-japanese`."
                    if engine == LUALATEX_ENGINE
                    else "Install a TeX distribution (e.g. `apt-get install "
                    "texlive-latex-recommended texlive-latex-extra "
                    "texlive-fonts-recommended texlive-science`)."
                )
                + " Or push and use compile_latex."
            )

        pdflatex = [
            engine,
            "-interaction=nonstopmode",
            "-halt-on-error=0",
            "-no-shell-escape",
            main_tex_name,
        ]

        needs_bibtex = _needs_bibtex(source)
        if needs_bibtex and shutil.which("bibtex") is None:
            raise LatexToolchainMissingError(
                "The document has a bibliography but bibtex was not found on "
                "PATH. Install it (it ships with texlive-binaries) — without "
                "it every citation would be reported as undefined whether or "
                "not the bibliography is sound."
            )

        try:
            _run(pdflatex, build_dir, _PDFLATEX_TIMEOUT_SECONDS)
            if needs_bibtex:
                bibtex_result = _run(
                    ["bibtex", stem], build_dir, _BIBTEX_TIMEOUT_SECONDS
                )
                if bibtex_result.returncode != 0:
                    logger.info(
                        f"bibtex exited {bibtex_result.returncode}; "
                        "continuing so the undefined citations are reported"
                    )
            # Two more passes: the first resolves citations and references
            # from the freshly written .aux/.bbl, the second settles page
            # numbers those may have shifted.
            _run(pdflatex, build_dir, _PDFLATEX_TIMEOUT_SECONDS)
            _run(pdflatex, build_dir, _PDFLATEX_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired as e:
            raise TimeoutError(
                f"{Path(e.cmd[0]).name} timed out after {e.timeout:.0f}s. The "
                "document may be stuck on an unclosed environment."
            ) from e

        log_path = build_dir / f"{stem}.log"
        log = log_path.read_text(errors="replace") if log_path.is_file() else ""
        citations, references, missing_files, errors = _parse_log(log)

        pdf_path = build_dir / f"{stem}.pdf"
        compiled = pdf_path.is_file()
        page_count = _page_count(pdf_path) if compiled else None
        # Kept even when the report is not clean: a PDF with one unresolved
        # citation is still the fastest way to see what is wrong with it.
        saved_pdf = _save_pdf(pdf_path, output_path) if compiled else None

        # Three things to drop from the raw "File ... not found" list.
        # graphicx probes for a graphic under several extensions and names
        # one probe with the unexpanded macro `\Gin@base`, which is not a
        # path anyone can supply. A "not found" for a file the project does
        # ship is that same probing. And a missing package or class is not a
        # figure — it is already reported through `errors`, where LaTeX
        # raises it as `! LaTeX Error: File 'foo.sty' not found`.
        project_paths = set(latex_files)
        missing_figures = [
            name
            for name in missing_files
            if "\\" not in name
            and Path(name).suffix.lower() not in _NON_FIGURE_SUFFIXES
            and name not in project_paths
            and not any(path.startswith(f"{name}.") for path in project_paths)
        ]

    report = LatexBuildReport(
        ok=compiled
        and not citations
        and not references
        and not missing_figures
        and not errors,
        compiled=compiled,
        page_count=page_count,
        undefined_citations=citations,
        undefined_references=references,
        missing_figures=missing_figures,
        errors=errors,
        pdf_path=saved_pdf,
        log_tail=log[-_LOG_TAIL_CHARS:],
    )
    logger.info(
        f"LaTeX build: compiled={report.compiled} pages={report.page_count} "
        f"undefined_citations={len(report.undefined_citations)} "
        f"missing_figures={len(report.missing_figures)} "
        f"errors={len(report.errors)}"
    )
    return report


# ------------------------------------- the paper's numbers are the record's
_UNVERIFIED_RE = re.compile(r"\\unverified\{([^{}]*)\}")

_AIRASVAL_RE = re.compile(r"\\airasval\{([^{}]*)\}")


def _strip_comment(line: str) -> str:
    # A % starts a comment unless escaped by an odd number of preceding
    # backslashes: \% is a literal percent, \\% is a line break + comment.
    search_from = 0
    while True:
        at = line.find("%", search_from)
        if at == -1:
            return line
        backslashes = 0
        before = at - 1
        while before >= 0 and line[before] == "\\":
            backslashes += 1
            before -= 1
        if backslashes % 2 == 0:
            return line[:at]
        search_from = at + 1


def scan_main_tex(main_tex: str) -> tuple[list[str], list[str]]:
    unverified: list[str] = []
    used_keys: list[str] = []
    for raw_line in main_tex.splitlines():
        line = _strip_comment(raw_line)
        unverified.extend(m.group(1) for m in _UNVERIFIED_RE.finditer(line))
        used_keys.extend(
            m.group(1)
            for m in _AIRASVAL_RE.finditer(line)
            if m.group(1) not in used_keys
        )
    return unverified, used_keys


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
        relpath = table_tex_relpath(spec.key)
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


# -------------------------------------------------------- the paper's verdict


async def verify_paper(
    local_path: str,
    template: LATEX_TEMPLATE_NAME,
    *,
    pdf_path: str | None = None,
    check_provenance: bool = True,
    require_record: bool = True,
    require_provenance: bool = True,
    require_history: bool = True,
    seyval_client_factory: Callable[[], SeyvalClient] = default_seyval_client,
    record: RecordVerification | None = None,
) -> PaperVerification:
    """The paper's numbers are the record's, and the record holds; then, optionally, it builds."""
    if record is None:
        record = await verify_record(
            local_path,
            check_provenance=check_provenance,
            require_provenance=require_provenance,
            require_history=require_history,
            seyval_client_factory=seyval_client_factory,
        )
    root = Path(local_path).expanduser().resolve()

    problems, unverified = await asyncio.to_thread(
        _verify_mapping, root, template, record
    )
    if require_record and not (root / RECORD_PATH).is_file():
        problems.append(
            "record.json is missing: the paper does not use the canonical-record "
            "system, so its claims and numbers cannot be verified "
            "(preregister_record creates it)"
        )
    build: LatexBuildReport | None = None
    if pdf_path is not None:
        build = await asyncio.to_thread(_verify_build, local_path, template, pdf_path)
        if not build.ok:
            problems.append("the LaTeX build failed (see build)")

    ok = record.ok and not problems
    pdf: str | None = None
    if pdf_path is not None:
        # A PDF handed out states verified numbers, so a failed run has none.
        if ok and Path(pdf_path).is_file():
            pdf = pdf_path
        else:
            Path(pdf_path).unlink(missing_ok=True)
    return PaperVerification(
        ok=ok,
        template=template,
        record=record,
        problems=problems,
        unverified=unverified,
        build=build,
        pdf=pdf,
    )


def _verify_mapping(
    root: Path, template: str, record_result: RecordVerification
) -> tuple[list[str], list[str]]:
    """Every mapped artifact matches its regeneration from the record.

    Returns (problems, \\unverified claims for human review).
    """
    latex_dir = root / ".research" / "latex" / template
    values_tex_path = latex_dir / VALUES_TEX_FILENAME
    main_tex_path = latex_dir / "main.tex"
    problems: list[str] = []

    unverified: list[str] = []
    used_keys: list[str] = []
    if main_tex_path.is_file():
        unverified, used_keys = scan_main_tex(main_tex_path.read_text(encoding="utf-8"))
    required = [main_tex_path]
    if record_result.stage == "results":
        required.append(values_tex_path)
    missing = [str(p.relative_to(root)) for p in required if not p.is_file()]
    if missing:
        problems.append("missing: " + ", ".join(missing))

    try:
        record = load_record(str(root))
    except (ValidationError, ValueError):
        # The record's own verification already reports this.
        return problems, unverified
    if record_result.stage == "prereg":
        # A values.tex carried over without runs would put unverifiable
        # numbers in the PDF.
        if values_tex_path.is_file():
            problems.append(f"{VALUES_TEX_FILENAME} exists but no run outputs exist")
        if (latex_dir / TABLES_DIR_NAME).is_dir():
            problems.append(f"{TABLES_DIR_NAME}/ exists but no run outputs exist")
        return problems, unverified

    try:
        metrics_data = load_metrics_data(str(root))
    except ValueError:
        metrics_data = {}
    paper_values, undefined_keys = resolve_paper_values(record, metrics_data, used_keys)
    if undefined_keys:
        problems.append(
            "\\airasval keys main.tex references that record.json does not declare: "
            + ", ".join(undefined_keys)
        )
    if values_tex_path.is_file():
        origin = remote_origin_url(root)
        record_commits = commits_touching(root, RECORD_PATH)  # newest first
        expected = render_values_tex(
            paper_values,
            normalize_git_url(origin) if origin else None,
            record_commits[0] if record_commits else None,
        )
        if values_tex_path.read_text(encoding="utf-8") != expected:
            problems.append(
                f"{VALUES_TEX_FILENAME} differs from its regeneration (manual edit?)"
            )
    problems += _verify_tables(latex_dir, record.active_tables(), metrics_data)
    problems += _verify_charts(record, str(root), metrics_data)
    return problems, unverified


def _verify_build(
    local_path: str, template: LATEX_TEMPLATE_NAME, pdf_path: str
) -> LatexBuildReport:
    latex_files = collect_latex_project_files_local(local_path, template)
    return verify_latex_build(latex_files, "main.tex", pdf_path)


def detect_templates(local_path: str) -> list[str]:
    latex_root = Path(local_path).expanduser().resolve() / ".research" / "latex"
    if not latex_root.is_dir():
        return []
    known = set(get_args(LATEX_TEMPLATE_NAME))
    found = []
    for path in sorted(latex_root.iterdir()):
        if not (path / "main.tex").is_file():
            continue
        if path.name not in known:
            logger.warning(f"Skipping unknown LaTeX template directory: {path.name}")
            continue
        found.append(path.name)
    return found
