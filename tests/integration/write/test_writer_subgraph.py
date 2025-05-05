from unittest.mock import patch

import pytest

from airas.write.writer_subgraph.writer_subgraph import WriterSubgraph


@pytest.fixture
def dummy_input():
    return {
        "base_method_text": "base",
        "new_method": "new",
        "verification_policy": "policy",
        "experiment_details": "details",
        "experiment_code": "code",
        "output_text_data": "output",
        "analysis_report": "report",
    }


@pytest.fixture
def expected_output():
    return {"paper_content": {"Title": "Test Paper", "Abstract": "Test Abstract"}}


@patch(
    "airas.write.writer_subgraph.nodes.generate_note.generate_note", return_value="note"
)
@patch(
    "airas.write.writer_subgraph.nodes.paper_writing.WritingNode.execute",
    return_value={"Title": "Test Paper", "Abstract": "Test Abstract"},
)
def test_writer_subgraph(mock_write, mock_note, dummy_input, expected_output):
    subgraph = WriterSubgraph(save_dir="/tmp", llm_name="dummy-llm", refine_round=1)
    graph = subgraph.build_graph()
    result = graph.invoke(dummy_input)
    assert result["paper_content"] == expected_output["paper_content"]
