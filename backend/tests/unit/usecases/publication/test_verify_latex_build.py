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

from airas.usecases.publication.open_in_overleaf_subgraph.nodes.collect_latex_project_files import (
    select_engine,
)
from airas.usecases.publication.verify_paper import verify_latex_build

# Most documents here end in \bibliography{references}, so bibtex runs too.
requires_tex = pytest.mark.skipif(
    shutil.which("pdflatex") is None or shutil.which("bibtex") is None,
    reason="requires a local TeX distribution (pdflatex and bibtex)",
)
pytestmark = requires_tex

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


class TestEngineSelection:
    """pdflatex cannot typeset Japanese, so the engine follows the document.

    A paper drafted in Japanese is checked in Japanese — asking the author
    to declare the engine would just move the mistake somewhere easier to
    forget, and getting it wrong is not a preference but a silent loss:
    pdflatex raises `LaTeX Error: Unicode character` per character and
    leaves the text out of the PDF.
    """

    def test_japanese_selects_lualatex(self):
        assert select_engine("\\section{はじめに}") == "lualatex"

    def test_latin_stays_on_pdflatex(self):
        # Curly quotes and dashes are not CJK; they must not switch engines.
        assert select_engine("A “quoted” em—dash paper.") == "pdflatex"

    @pytest.mark.skipif(
        shutil.which("lualatex") is None
        or subprocess.run(["kpsewhich", "luatexja.sty"], capture_output=True).returncode
        != 0,
        reason="requires texlive-luatex and texlive-lang-japanese",
    )
    def test_a_japanese_paper_compiles_and_is_reported_sound(self):
        report = verify_latex_build(
            {
                "main.tex": (
                    "\\documentclass[11pt]{article}\n"
                    "\\usepackage{luatexja-fontspec}\n"
                    "\\setmainjfont{IPAexMincho}\n"
                    "\\title{集約スコアは系ごとの失敗を隠蔽する}\n"
                    "\\begin{document}\\maketitle\n"
                    "\\section{はじめに}本研究では、集約指標の妥当性を検証する。\n"
                    "\\end{document}\n"
                ).encode()
            }
        )

        assert report.ok
        assert report.page_count == 1
        assert report.errors == []


class TestKeepingThePdf:
    """The build directory is temporary, so the PDF has to be asked for.

    For a Japanese paper this is the only way to get one: compile_latex
    runs pdflatex on GitHub Actions, which cannot typeset CJK.
    """

    def test_the_pdf_is_discarded_unless_a_path_is_given(self):
        report = verify_latex_build({"main.tex": _document("Text.")})

        assert report.compiled
        assert report.pdf_path is None

    def test_an_explicit_path_receives_the_verified_build(self, tmp_path):
        destination = tmp_path / "out" / "paper.pdf"

        report = verify_latex_build(
            {"main.tex": _document("Text.")}, output_path=destination
        )

        assert report.pdf_path == str(destination)
        assert destination.is_file() and destination.stat().st_size > 0

    def test_a_directory_keeps_the_document_name(self, tmp_path):
        report = verify_latex_build(
            {"main.tex": _document("Text.")}, output_path=tmp_path
        )

        assert report.pdf_path == str(tmp_path / "main.pdf")

    def test_a_flawed_paper_still_yields_its_pdf(self, tmp_path):
        """Seeing the '?' in place is faster than reading about it."""
        report = verify_latex_build(
            {
                "main.tex": _document("Cited \\cite{never_added}."),
                "references.bib": BIB,
            },
            output_path=tmp_path / "paper.pdf",
        )

        assert not report.ok
        assert report.pdf_path is not None
