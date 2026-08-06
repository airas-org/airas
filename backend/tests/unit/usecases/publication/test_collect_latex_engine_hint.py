"""Overleaf builds with latexmk and defaults it to pdfLaTeX.

A Japanese paper exported without a hint arrives there and compiles with
its text missing — the reader has to find the compiler setting to see
anything. latexmk reads `latexmkrc` from the project, so the export
carries the answer with it.
"""

from airas.usecases.publication.open_in_overleaf_subgraph.nodes.collect_latex_project_files import (
    _add_engine_hint,
)


def test_a_japanese_project_gets_a_lualatex_latexmkrc():
    files = {"main.tex": "\\section{はじめに}".encode()}

    _add_engine_hint(files)

    assert files["latexmkrc"] == b"$pdf_mode = 4;\n"


def test_an_english_project_is_left_alone():
    files = {"main.tex": b"\\section{Introduction}"}

    _add_engine_hint(files)

    assert "latexmkrc" not in files


def test_a_project_that_ships_its_own_latexmkrc_keeps_it():
    own = b"$pdf_mode = 1;\n"
    files = {"main.tex": "\\section{はじめに}".encode(), "latexmkrc": own}

    _add_engine_hint(files)

    assert files["latexmkrc"] == own
