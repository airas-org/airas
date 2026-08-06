"""The failures that still produce a PDF have to be reported as failures.

An undefined citation prints as `?`, an absent figure prints as a box, and
pdflatex exits happily in both cases. Without these checks a fully
automated run ships either one without noticing.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from airas.usecases.publication.nodes.verify_latex_build import verify_latex_build

# Every document here ends in \bibliography{references}, so bibtex runs too.
pytestmark = pytest.mark.skipif(
    shutil.which("pdflatex") is None or shutil.which("bibtex") is None,
    reason="requires a local TeX distribution (pdflatex and bibtex)",
)

BIB = b"""
@article{known2020,
  author  = {A. Author},
  title   = {A Known Title},
  journal = {Journal},
  year    = {2020}
}
"""


def _document(body: str) -> bytes:
    return (
        "\\documentclass{article}\n"
        "\\usepackage{graphicx}\n"
        "\\begin{document}\n"
        f"{body}\n"
        "\\bibliographystyle{plain}\n"
        "\\bibliography{references}\n"
        "\\end{document}\n"
    ).encode()


@pytest.fixture(scope="module")
def figure_pdf() -> bytes:
    """A real one-page PDF, standing in for a rendered chart."""
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        (directory / "f.tex").write_bytes(
            b"\\documentclass{article}\\begin{document}figure\\end{document}"
        )
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "f.tex"],
            cwd=directory,
            capture_output=True,
            check=False,
        )
        return (directory / "f.pdf").read_bytes()


def test_sound_document_is_ok(figure_pdf):
    report = verify_latex_build(
        {
            "main.tex": _document(
                "Cited \\cite{known2020}.\n"
                "\\begin{figure}\\includegraphics[width=0.4\\linewidth]"
                "{images/chart/loss.pdf}\\caption{Loss}\\end{figure}"
            ),
            "references.bib": BIB,
            "images/chart/loss.pdf": figure_pdf,
        }
    )

    assert report.ok
    assert report.compiled
    assert report.page_count == 1
    assert report.undefined_citations == []
    assert report.missing_figures == []


def test_citation_absent_from_the_bibliography_is_reported():
    report = verify_latex_build(
        {
            "main.tex": _document("Cited \\cite{never_added}."),
            "references.bib": BIB,
        }
    )

    # This is what shipping the template's placeholder references.bib looks
    # like: a PDF is produced, and every citation in it reads '?'.
    assert report.compiled
    assert not report.ok
    assert report.undefined_citations == ["never_added"]


def test_figure_referenced_but_not_shipped_is_reported():
    report = verify_latex_build(
        {
            "main.tex": _document(
                "\\begin{figure}\\includegraphics[width=0.4\\linewidth]"
                "{images/chart/absent.pdf}\\caption{Absent}\\end{figure}"
            ),
            "references.bib": BIB,
        }
    )

    assert not report.ok
    assert report.missing_figures == ["images/chart/absent.pdf"]


def test_graphicx_extension_probing_is_not_a_missing_figure(figure_pdf):
    """graphicx names one probe with the raw macro `\\Gin@base`."""
    report = verify_latex_build(
        {
            "main.tex": _document(
                "\\begin{figure}\\includegraphics[width=0.4\\linewidth]"
                "{images/chart/absent.pdf}\\caption{Absent}\\end{figure}"
            ),
            "references.bib": BIB,
        }
    )

    assert all("\\" not in name for name in report.missing_figures)


def test_dangling_reference_is_reported():
    report = verify_latex_build(
        {
            "main.tex": _document("See section~\\ref{sec:nowhere}."),
            "references.bib": BIB,
        }
    )

    assert not report.ok
    assert report.undefined_references == ["sec:nowhere"]


def test_missing_main_tex_is_rejected():
    with pytest.raises(ValueError, match="main.tex"):
        verify_latex_build({"references.bib": BIB})


def test_the_document_cannot_read_files_outside_the_build_directory(tmp_path):
    """The .tex comes out of a repository, so it is not trusted input.

    TeX can open any path the process can, and `log_tail` is handed back to
    the caller — so a document that reads a file and echoes it to the log is
    an exfiltration primitive. (Reading it into the *page* is not, since the
    PDF never leaves the build directory; the log is the channel that does.)
    """
    secret = tmp_path / "secret.txt"
    secret.write_text("SUPERSECRETVALUE")

    report = verify_latex_build(
        {
            "main.tex": (
                "\\documentclass{article}\n"
                "\\newread\\leak\n"
                f"\\openin\\leak={secret}\n"
                "\\read\\leak to \\stolen\n"
                "\\closein\\leak\n"
                "\\begin{document}\n"
                "\\typeout{LEAKED: \\stolen}\n"
                "text\n"
                "\\end{document}\n"
            ).encode(),
        }
    )

    assert "SUPERSECRETVALUE" not in report.log_tail
    # The read is refused outright rather than silently returning nothing.
    assert not report.compiled
    assert not report.ok


def test_a_missing_package_is_an_error_not_a_missing_figure():
    report = verify_latex_build(
        {
            "main.tex": (
                "\\documentclass{article}\n"
                "\\usepackage{a-package-that-does-not-exist}\n"
                "\\begin{document}text\\end{document}\n"
            ).encode(),
        }
    )

    assert report.missing_figures == []
    assert any("not found" in error for error in report.errors)
    assert not report.ok
