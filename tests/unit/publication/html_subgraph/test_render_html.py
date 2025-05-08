import pytest

from airas.publication.html_subgraph.nodes.render_html import (
    _wrap_in_html_template,
    _save_index_html,
    render_html,
)


@pytest.fixture
def sample_content() -> str:
    return "<h1>Hello, World!</h1>"

def test_wrap_in_html_template_contains_structure_and_content(sample_content):
    wrapped = _wrap_in_html_template(sample_content)

    assert wrapped.lstrip().startswith("<!DOCTYPE html>")
    assert "<html" in wrapped and "</html>" in wrapped
    assert "<head>" in wrapped and "</head>" in wrapped
    assert "<body>" in wrapped and "</body>" in wrapped
    assert sample_content in wrapped

def test_save_index_html_creates_file_and_writes_content(tmp_path, sample_content):
    save_dir = tmp_path / "output"
    _save_index_html(sample_content, str(save_dir))

    index_path = save_dir / "index.html"
    assert index_path.exists()

    written = index_path.read_text(encoding="utf-8")
    assert written == sample_content

def test_render_html_returns_full_html_and_saves_file(tmp_path, sample_content):
    full_html = render_html(sample_content, str(tmp_path))
    assert full_html.lstrip().startswith("<!DOCTYPE html>")
    assert sample_content in full_html

    index_file = tmp_path / "index.html"
    assert index_file.exists()

    file_text = index_file.read_text(encoding="utf-8")
    assert file_text == full_html
