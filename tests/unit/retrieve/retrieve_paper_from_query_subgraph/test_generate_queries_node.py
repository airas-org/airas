from unittest.mock import patch

from airas.retrieve.retrieve_paper_subgraph.nodes.generate_queries_node import (
    generate_queries_node,
)


# Normal case: openai_client returns valid queries
@patch(
    "airas.utils.api_client.llm_facade_client.LLMFacadeClient.structured_outputs",
    return_value=(
        {
            "generated_query_1": "q1",
            "generated_query_2": "q2",
            "generated_query_3": "q3",
            "generated_query_4": "q4",
            "generated_query_5": "q5",
        },
        0.0,
    ),
)
def test_generate_queries_node_success(mock_openai):
    llm_name = "gpt-4o-mini-2024-07-18"
    prompt_template = "template"
    selected_base_paper_info = "info"
    queries = ["query1"]
    result = generate_queries_node(
        llm_name, prompt_template, selected_base_paper_info, queries
    )
    assert result == ["q1", "q2", "q3", "q4", "q5"]
