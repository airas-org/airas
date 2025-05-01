import pytest
from unittest.mock import patch
from airas.publication.readme_subgraph.nodes.readme_upload import readme_upload


@pytest.fixture
def sample_inputs():
    return {
        "github_owner": "test-owner",
        "repository_name": "test-repo",
        "branch_name": "main",
        "title": "Test Title",
        "abstract": "Test Abstract",
        "devin_url": "https://example.com/devin",
    }


# 正常系: 全てのAPI呼び出しが成功した場合にTrueを返す
@patch(
    "airas.publication.readme_subgraph.nodes.readme_upload._request_github_file_upload",
    return_value=None,
)
@patch(
    "airas.publication.readme_subgraph.nodes.readme_upload._request_get_github_content",
    return_value={"sha": "dummy-sha"},
)
def test_readme_upload_success(mock_get_content, mock_file_upload, sample_inputs):
    result = readme_upload(**sample_inputs)
    assert result is True


# 異常系: READMEが存在しない場合（shaがNone）でもTrueを返す
@patch(
    "airas.publication.readme_subgraph.nodes.readme_upload._request_github_file_upload",
    return_value=None,
)
@patch(
    "airas.publication.readme_subgraph.nodes.readme_upload._request_get_github_content",
    return_value=None,
)
def test_readme_upload_no_readme(mock_get_content, mock_file_upload, sample_inputs):
    result = readme_upload(**sample_inputs)
    assert result is True
