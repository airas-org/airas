import pytest
import airas.retrieve.retrieve_code_subgraph.node.retrieve_repository_contents as mod
from airas.retrieve.retrieve_code_subgraph.node.retrieve_repository_contents import (
    retrieve_repository_contents,
)


# Normal case: Only .py and .ipynb files are extracted and their contents are concatenated
def test_retrieve_repository_contents_success(monkeypatch):
    monkeypatch.setattr(
        mod,
        "_retrieve_repository_tree",
        lambda *a, **kw: {
            "tree": [
                {"path": "main.py"},
                {"path": "README.md"},
                {"path": "notebook.ipynb"},
            ]
        },
    )
    monkeypatch.setattr(
        mod,
        "_retrieve_file_contents",
        lambda *a, **kw: f"print('This is {kw['file_path']}')",
    )
    url = "https://github.com/testuser/testrepo"
    result = retrieve_repository_contents(url)
    assert "File Path: main.py" in result
    assert "File Path: notebook.ipynb" in result
    assert "README.md" not in result
    assert "print('This is main.py')" in result
    assert "print('This is notebook.ipynb')" in result


@pytest.mark.parametrize(
    "tree, file_content, url, expected_exception, expected_msg",
    [
        # Error case: Failed to retrieve tree
        (
            None,
            None,
            "https://github.com/testuser/testrepo",
            RuntimeError,
            "Failed to retrieve the tree",
        ),
        # Error case: Invalid URL
        (
            "dummy",
            "dummy",
            "https://invalid-url.com/testuser/testrepo",
            ValueError,
            "Invalid GitHub URL",
        ),
    ],
)
def test_retrieve_repository_contents_error_cases(
    monkeypatch, tree, file_content, url, expected_exception, expected_msg
):
    if tree != "dummy":
        monkeypatch.setattr(mod, "_retrieve_repository_tree", lambda *a, **kw: tree)
    if file_content != "dummy":
        monkeypatch.setattr(
            mod, "_retrieve_file_contents", lambda *a, **kw: file_content
        )
    with pytest.raises(expected_exception) as exc:
        retrieve_repository_contents(url)
    assert expected_msg in str(exc.value)


# Error case: Failed to retrieve file content
def test_retrieve_repository_contents_file_content_none(monkeypatch, caplog):
    monkeypatch.setattr(
        mod,
        "_retrieve_repository_tree",
        lambda *a, **kw: {"tree": [{"path": "main.py"}, {"path": "notebook.ipynb"}]},
    )
    monkeypatch.setattr(mod, "_retrieve_file_contents", lambda *a, **kw: None)
    url = "https://github.com/testuser/testrepo"
    with caplog.at_level("WARNING"):
        result = retrieve_repository_contents(url)
    assert "File Path: main.py" not in result
    assert "File Path: notebook.ipynb" not in result
    assert "Failed to retrieve file data: main.py" in caplog.text
    assert "Failed to retrieve file data: notebook.ipynb" in caplog.text
