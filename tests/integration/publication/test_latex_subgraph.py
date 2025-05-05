import json
from unittest.mock import patch

import pytest

from airas.publication.latex_subgraph.latex_subgraph import LatexSubgraph


@pytest.fixture
def dummy_input():
    return {
        "paper_content": {"Title": "Test Paper", "Abstract": "This is a test abstract."}
    }


@pytest.fixture
def expected_output():
    return {"tex_text": "Generated LaTeX text"}


@patch(
    "airas.publication.latex_subgraph.nodes.compile_to_pdf.LatexNode.execute",
    return_value="Generated LaTeX text",
)
@patch(
    "airas.publication.latex_subgraph.nodes.convert_to_latex.openai_client",
    return_value=json.dumps(
        {
            "Title": "Dummy Title",
            "Abstract": "Dummy Abstract",
            "Introduction": "Dummy Introduction",
            "Related_Work": "Dummy Related Work",
            "Background": "Dummy Background",
            "Method": "Dummy Method",
            "Experimental_Setup": "Dummy Experimental Setup",
            "Results": "Dummy Results",
            "Conclusions": "Dummy Conclusions",
        }
    ),
)
def test_latex_subgraph(mock_openai_client, mock_execute, dummy_input, expected_output):
    subgraph = LatexSubgraph(save_dir="/tmp", llm_name="dummy-llm")
    graph = subgraph.build_graph()
    result = graph.invoke(dummy_input)
    assert result["tex_text"] == expected_output["tex_text"]
