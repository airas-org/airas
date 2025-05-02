from unittest.mock import patch
from airas.retrieve.retrieve_paper_subgraph.nodes.summarize_paper_node import (
    summarize_paper_node,
)


# Normal case: vertexai_client returns all required fields
@patch(
    "airas.utils.api_client.llm_facade_client.LLMFacadeClient.structured_outputs",
    return_value=(
        {
            "main_contributions": "contrib",
            "methodology": "method",
            "experimental_setup": "setup",
            "limitations": "limits",
            "future_research_directions": "future",
        },
        0.0,
    ),
)
def test_summarize_paper_node_success(mock_structured_outputs):
    llm_name = "gpt-4o-mini-2024-07-18"
    prompt_template = "template"
    paper_text = "text"
    result = summarize_paper_node(llm_name, prompt_template, paper_text)
    assert result == ("contrib", "method", "setup", "limits", "future")
