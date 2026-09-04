from pathlib import Path

from airas.usecases.publication.verify_paper import detect_templates


def test_detects_only_written_known_templates(tmp_path: Path) -> None:
    latex = tmp_path / ".research" / "latex"
    (latex / "mdpi").mkdir(parents=True)
    (latex / "mdpi" / "main.tex").write_text("x")
    (latex / "iclr2024").mkdir()  # template present but no paper written
    (latex / "homebrew").mkdir()  # unknown template directory
    (latex / "homebrew" / "main.tex").write_text("x")

    assert detect_templates(str(tmp_path)) == ["mdpi"]


def test_detects_nothing_without_latex_dir(tmp_path: Path) -> None:
    assert detect_templates(str(tmp_path)) == []
