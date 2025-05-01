import pytest
from pathlib import Path
from airas.publication.html_subgraph.nodes.render_html import (
    _wrap_in_html_template,
    _save_index_html,
)


def test_wrap_in_html_template() -> None:
    test_content = "<p>Hello, world!</p>"
    result = _wrap_in_html_template(test_content)
    assert test_content in result


@pytest.mark.parametrize("subpath", ["", "missing_dir"])
def test_save_index_html_creates_file(tmp_path: Path, subpath: str) -> None:
    test_full_html = "<html><body>Test</body></html>"
    save_dir = tmp_path / subpath
    _save_index_html(test_full_html, str(save_dir))

    index_file = save_dir / "index.html"
    assert index_file.exists()
    assert index_file.read_text(encoding="utf-8") == test_full_html
