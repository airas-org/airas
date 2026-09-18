from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from airas.core.types.latex import LUALATEX_ENGINE, LatexBuildReport, select_engine

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
    # The engines run without shell escape, so epstopdf cannot convert the
    # EPS a class includes (mdpi's logo) mid-build; convert up front under the
    # name epstopdf-pkg looks for, as the publish workflow does.
    if shutil.which("epstopdf"):
        for eps in build_dir.rglob("*.eps"):
            converted = eps.with_name(f"{eps.stem}-eps-converted-to.pdf")
            if not converted.exists():
                subprocess.run(
                    ["epstopdf", str(eps), f"--outfile={converted}"],
                    cwd=build_dir,
                    capture_output=True,
                    timeout=60,
                )


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


def build_latex_project(
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
    one build whose result has been inspected; the Publish Paper workflow
    builds the same way on CI.
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
                + " Or push and let the Publish Paper workflow build it."
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
