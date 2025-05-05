import os
import subprocess
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from airas.publication.latex_subgraph.nodes.compile_to_pdf import LatexNode


@pytest.fixture
def tmp_env(tmp_path) -> dict[str, str]:
    template_dir = tmp_path / "templatex_dir"
    template_dir.mkdir()
    (template_dir / "template.tex").write_text(
        "TITLE HERE\nABSTRACT HERE\n\\cite{ref1}\n"
    )
    (template_dir / "references.bib").write_text(
        "@article{ref1, author={A}, title={T}, year={2025}}"
    )

    figures_dir = tmp_path / "figures"
    figures_dir.mkdir()

    pdf_file_path = tmp_path / "test.pdf"

    save_dir = tmp_path / "save"
    save_dir.mkdir()

    return {
        "template_dir": str(template_dir),
        "template_file": str(template_dir / "template.tex"),
        "save_dir": str(save_dir),
        "figures_dir": str(figures_dir),
        "pdf_file_path": str(pdf_file_path),
    }


@pytest.fixture(autouse=True)
def patch_openai():
    with patch(
        "airas.utils.api_client.openai_client.OpenAIClient.structured_outputs",
        return_value=({"latex_full_text": "DUMMY"}, 0.01),
    ):
        yield


@pytest.fixture
def node(tmp_env: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> LatexNode:
    """LatexNode のインスタンスを作成"""
    node = LatexNode(
        llm_name="test-model",
        figures_dir=tmp_env["figures_dir"],
        pdf_file_path=tmp_env["pdf_file_path"],
        save_dir=tmp_env["save_dir"],
        timeout=5,
        latex_template_file_path=tmp_env["template_file"],
    )
    monkeypatch.setattr(node, "template_dir", tmp_env["template_dir"])
    return node


def test_copy_template_creates_files(node: LatexNode, tmp_env: dict[str, str]) -> None:
    node._copy_template()
    copied = os.listdir(os.path.join(tmp_env["save_dir"], "latex"))
    assert "template.tex" in copied
    assert "references.bib" in copied


@pytest.mark.parametrize(
    "content, expected",
    [
        ({"title": "T1", "abstract": "A1"}, ("T1", "A1")),
        ({}, ("TITLE HERE", "ABSTRACT HERE")),
    ],
)
def test_fill_template(
    node: LatexNode, content: dict[str, str], expected: tuple[str, str]
) -> None:
    node._copy_template()
    text = node._fill_template(content)
    assert expected[0] in text
    assert expected[1] in text


def test_call_llm_success(node):
    res = node._call_llm("prompt")
    assert res == "DUMMY"


@pytest.mark.parametrize(
    "raw_response, expected_msg",
    [
        (None, "No response"),
        ("", "Empty LaTeX content"),
        ("{}", "Empty LaTeX content"),
        ('{"latex_full_text": ""}', "Empty LaTeX content"),
    ],
)
def test_call_llm_errors(
    node: LatexNode,
    raw_response: str | None,
    expected_msg: str,
) -> None:
    def fake_structured_outputs(*args, **kwargs):
        if raw_response is None:
            return None, 0.01
        try:
            import json

            return json.loads(raw_response), 0.01
        except Exception:
            return raw_response, 0.01

    with patch(
        "airas.utils.api_client.openai_client.OpenAIClient.structured_outputs",
        side_effect=fake_structured_outputs,
    ):
        with pytest.raises(ValueError, match=expected_msg):
            node._call_llm("prompt")


def test_check_references_success(node: LatexNode) -> None:
    node._copy_template()
    tex_valid = "\\documentclass{article}\\begin{document}\\cite{ref1}\\end{document}"
    assert node._check_references(tex_valid) == tex_valid


def test_check_refenrences_missing_entry(node: LatexNode) -> None:
    node._copy_template()
    tex_missing = (
        "\\documentclass{article}\\begin{document}\\cite{missing}\\end{document}"
    )
    assert node._check_references(tex_missing) == "DUMMY"


def test_check_references_error_missing_bib(
    node: LatexNode, tmp_env: dict[str, str]
) -> None:
    node._copy_template()
    os.remove(os.path.join(tmp_env["save_dir"], "latex", "references.bib"))
    with pytest.raises(FileNotFoundError):
        node._check_references("any text")


def test_check_figures_success(node: LatexNode, tmp_env: dict[str, str]) -> None:
    fig = os.path.join(tmp_env["figures_dir"], "fig1.pdf")
    open(fig, "w").close()
    node._copy_template()
    tex = "\\includegraphics{fig1.pdf}"
    assert node._check_figures(tex) == "DUMMY"


def test_check_figures_no_graphics(node: LatexNode) -> None:
    tex = "no graphics here"
    assert node._check_figures(tex) == tex


def test_check_figures_missing_files(node: LatexNode) -> None:
    node._copy_template()
    tex = "\\includegraphics{missing.pdf}"
    assert node._check_figures(tex) == tex


@pytest.mark.parametrize(
    "tex_input",
    [
        "A \\section{X} B",
    ],
)
def test_check_duplicates_no_dup(node: LatexNode, tex_input: str) -> None:
    assert (
        node._check_duplicates(tex_input, {"section": r"\\section{([^}]*)}"})
        == tex_input
    )


@pytest.mark.parametrize(
    "tex_input",
    [
        "\\section{A}\\section{A}",
        "\\includegraphics{fig1.pdf}\\includegraphics{fig1.pdf}",
    ],
)
def test_check_duplicates_with_dup(node: LatexNode, tex_input: str) -> None:
    result = node._check_duplicates(
        tex_input,
        {
            "section": r"\\section{([^}]*)}",
            "figure": r"\\includegraphics.*?{(.*?)}",
        },
    )
    assert result == "DUMMY"


def test_fix_latex_errors_no_errors(
    node: LatexNode, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "os.popen", lambda *args, **kwargs: SimpleNamespace(read=lambda: "")
    )
    original = "clean tex"
    assert node._fix_latex_errors(original) == original


def test_fix_latex_errors_with_errors(
    node: LatexNode, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "os.popen",
        lambda *args, **kwargs: SimpleNamespace(
            read=lambda: "1: Undefined control sequence."
        ),
    )
    assert node._fix_latex_errors("bad tex") == "DUMMY"


def test_compile_latex_no_exception(
    node: LatexNode, monkeypatch: pytest.MonkeyPatch, tmp_env: dict[str, str]
) -> None:
    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        ),
    )
    node._copy_template()
    node._compile_latex(cwd=os.path.join(tmp_env["save_dir"], "latex"))


def test_execute_replaces_and_returns(node: LatexNode) -> None:
    node._compile_latex = lambda cwd: None
    content = {"title": "MyT", "abstract": "MyA"}

    result = node.execute(content)
    assert "TITLE HERE" not in result
    assert "ABSTRACT HERE" not in result
    assert "MyT" in result
    assert "MyA" in result
