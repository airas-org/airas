import json
from unittest.mock import patch

import pytest
from requests.exceptions import HTTPError

from airas.execution.executor_subgraph.nodes.llm_decide import llm_decide


@pytest.fixture
def test_environment():
    return {
        "llm_name": "gpt-4o-mini-2024-07-18",
        "output_text_data": "No error",
        "error_text_data": "",
    }


@pytest.mark.parametrize(
    "mock_response_content, expected_result",
    [
        ({"judgment_result": True}, True),
        ({"judgment_result": False}, False),
    ],
)
@patch(
    "airas.execution.executor_subgraph.nodes.llm_decide.OpenAIClient.structured_outputs"
)
def test_llm_decide_success(
    mock_structured_outputs, test_environment, mock_response_content, expected_result
):
    mock_structured_outputs.return_value = (mock_response_content, 0.01)
    result = llm_decide(
        test_environment["llm_name"],
        test_environment["output_text_data"],
        test_environment["error_text_data"],
    )
    assert result == expected_result


@pytest.mark.parametrize(
    "exception",
    [
        ConnectionError("Mocked Connection Error"),
        TimeoutError("Mocked Timeout Error"),
        HTTPError("Mocked Internal Server Error (500)"),
        HTTPError("Mocked Rate Limit Error (429)"),
    ],
)
@patch(
    "airas.execution.executor_subgraph.nodes.llm_decide.OpenAIClient.structured_outputs"
)
def test_llm_decide_api_errors(mock_structured_outputs, test_environment, exception):
    mock_structured_outputs.side_effect = exception
    with pytest.raises((ConnectionError, TimeoutError, HTTPError)):
        llm_decide(
            test_environment["llm_name"],
            test_environment["output_text_data"],
            test_environment["error_text_data"],
        )


@pytest.mark.parametrize(
    "mock_response_content",
    [
        "Invalid response format",
        json.dumps({"wrong_key": True}),
        {"wrong_key": True},
    ],
)
@patch(
    "airas.execution.executor_subgraph.nodes.llm_decide.OpenAIClient.structured_outputs"
)
def test_llm_decide_invalid_response(
    mock_structured_outputs, test_environment, mock_response_content
):
    mock_structured_outputs.return_value = (mock_response_content, 0.01)
    with pytest.raises(ValueError):
        llm_decide(
            test_environment["llm_name"],
            test_environment["output_text_data"],
            test_environment["error_text_data"],
        )
