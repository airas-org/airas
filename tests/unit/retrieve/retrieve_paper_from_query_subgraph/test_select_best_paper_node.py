from unittest.mock import patch

from airas.retrieve.retrieve_paper_subgraph.nodes.select_best_paper_node import (
    select_best_paper_node,
)


# Normal case: LLMFacadeClient.structured_outputs returns a valid arxiv_id string
@patch(
    "airas.utils.api_client.llm_facade_client.LLMFacadeClient.structured_outputs",
    return_value=({"selected_arxiv_id": "1234.5678v1\n2345.6789v2"}, 0),
)
def test_select_best_paper_node_success(mock_structured_outputs):
    llm_name = "gpt-4o-mini-2024-07-18"
    prompt_template = "template"
    candidate_papers = ["paper1", "paper2"]
    result = select_best_paper_node(llm_name, prompt_template, candidate_papers)
    assert result == ["1234.5678v1", "2345.6789v2"]


# Abnormal case: LLMFacadeClient.structured_outputs returns dict without selected_arxiv_id
@patch(
    "airas.utils.api_client.llm_facade_client.LLMFacadeClient.structured_outputs",
    return_value=({}, 0),
)
def test_select_best_paper_node_no_selected_id(mock_structured_outputs):
    llm_name = "gpt-4o-mini-2024-07-18"
    prompt_template = "template"
    candidate_papers = ["paper1", "paper2"]
    result = select_best_paper_node(llm_name, prompt_template, candidate_papers)
    assert result == []
