"""Compile a collected LaTeX project locally and report what is wrong with it.

This exists because dispatching `compile_latex.yml` only tells you the
workflow-dispatch request was accepted, and the Overleaf export only tells
you a link was produced. Neither answers the question that actually matters
when no human opens the PDF: did it build, are the citations resolved, are
the figures there.

The input is the same file map the Overleaf export sends, so a clean report
here means the exported project compiles as-is.
"""

import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from airas.core.types.latex import LatexBuildReport

logger = logging.getLogger(__name__)

# TeX wraps log lines at ~79 characters by default, which splits the very
# messages parsed below across lines. These are the documented knobs for
# turning that off; without them the regexes silently under-report.
_UNWRAPPED_LOG_ENV = {
    "max_print_line": "10000",
    "error_line": "254",
    "half_error_line": "238",
}

_PDFLATEX_TIMEOUT_SECONDS = 180.0
_BIBTEX_TIMEOUT_SECONDS = 60.0
_LOG_TAIL_CHARS = 4000

_UNDEFINED_CITATION = re.compile(r"Citation [`'\"]([^`'\"]+)['\"] on page")
_UNDEFINED_REFERENCE = re.compile(r"Reference [`'\"]([^`'\"]+)['\"] on page")
_MISSING_FILE = re.compile(r"File [`'\"]([^`'\"]+)['\"] not found")
_ERROR_LINE = re.compile(r"^! (.+)$", re.MULTILINE)


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
    env = {**os.environ, **_UNWRAPPED_LOG_ENV}
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
) -> LatexBuildReport:
    """Build `latex_files` in a scratch directory and report the result.

    Runs the same pdflatex/bibtex/pdflatex/pdflatex sequence the CI LaTeX
    agent uses, so the findings match what that agent would see.
    """
    if shutil.which("pdflatex") is None:
        raise LatexToolchainMissingError(
            "pdflatex was not found on PATH. Install a TeX distribution "
            "(e.g. `apt-get install texlive-latex-recommended "
            "texlive-latex-extra texlive-fonts-recommended texlive-science`) "
            "to verify the paper locally, or push and use compile_latex."
        )

    stem = Path(main_tex_name).stem

    with tempfile.TemporaryDirectory(prefix="airas-latex-") as tmp:
        build_dir = Path(tmp)
        _write_project(latex_files, build_dir)

        main_tex_path = build_dir / main_tex_name
        if not main_tex_path.is_file():
            raise ValueError(f"{main_tex_name} is not present in the collected project")

        pdflatex = [
            "pdflatex",
            "-interaction=nonstopmode",
            "-halt-on-error=0",
            main_tex_name,
        ]

        try:
            _run(pdflatex, build_dir, _PDFLATEX_TIMEOUT_SECONDS)
            if _needs_bibtex(main_tex_path.read_text(errors="replace")):
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
                f"LaTeX build exceeded {_PDFLATEX_TIMEOUT_SECONDS:.0f}s. The "
                "document may be stuck on an unclosed environment."
            ) from e

        log_path = build_dir / f"{stem}.log"
        log = log_path.read_text(errors="replace") if log_path.is_file() else ""
        citations, references, missing_files, errors = _parse_log(log)

        pdf_path = build_dir / f"{stem}.pdf"
        compiled = pdf_path.is_file()
        page_count = _page_count(pdf_path) if compiled else None

        # Two kinds of false positive to drop. graphicx probes for a graphic
        # under several extensions and names one probe with the unexpanded
        # macro `\Gin@base`, which is not a path anyone can supply. And a
        # "not found" for a file the project does ship is just that probing.
        project_paths = set(latex_files)
        missing_figures = [
            name
            for name in missing_files
            if "\\" not in name
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
        log_tail=log[-_LOG_TAIL_CHARS:],
    )
    logger.info(
        f"LaTeX build: compiled={report.compiled} pages={report.page_count} "
        f"undefined_citations={len(report.undefined_citations)} "
        f"missing_figures={len(report.missing_figures)} "
        f"errors={len(report.errors)}"
    )
    return report
