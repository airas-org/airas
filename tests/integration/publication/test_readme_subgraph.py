import pytest
from unittest.mock import patch
from airas.publication.readme_subgraph.readme_subgraph import ReadmeSubgraph


@pytest.fixture
def dummy_input():
    return {
        "github_owner": "test-owner",
        "repository_name": "test-repo",
        "branch_name": "test-branch",
        "paper_content": {"Title": "Test Paper", "Abstract": "Test Abstract"},
        "output_text_data": "output",
        "experiment_devin_url": "https://devin.ai/mock",
    }


@pytest.fixture
def expected_output():
    return {"readme_upload_result": True}


@patch(
    "airas.publication.readme_subgraph.nodes.readme_upload.readme_upload",
    return_value=True,
)
def test_readme_subgraph(mock_readme_upload, dummy_input, expected_output):
    subgraph = ReadmeSubgraph()
    graph = subgraph.build_graph()
    result = graph.invoke(dummy_input)
    assert result["readme_upload_result"] == expected_output["readme_upload_result"]
