from unittest.mock import patch

import pytest

from airas.execution.executor_subgraph.nodes.fix_code_with_devin import (
    fix_code_with_devin,
)


# Normal case: _request_revision_to_devin is called and fix_iteration_count is incremented
@patch(
    "airas.execution.executor_subgraph.nodes.fix_code_with_devin._request_revision_to_devin"
)
def test_fix_code_with_devin_success(mock_request):
    headers = {"Authorization": "Bearer token"}
    session_id = "session"
    output_text_data = "output"
    error_text_data = "error"
    fix_iteration_count = 2
    result = fix_code_with_devin(
        headers, session_id, output_text_data, error_text_data, fix_iteration_count
    )
    assert result == 3
    mock_request.assert_called_once_with(
        headers, session_id, output_text_data, error_text_data
    )


# Abnormal case: _request_revision_to_devin raises an exception
@patch(
    "airas.execution.executor_subgraph.nodes.fix_code_with_devin._request_revision_to_devin",
    side_effect=Exception("API error"),
)
def test_fix_code_with_devin_api_error(mock_request):
    headers = {"Authorization": "Bearer token"}
    session_id = "session"
    output_text_data = "output"
    error_text_data = "error"
    fix_iteration_count = 2
    with pytest.raises(Exception):
        fix_code_with_devin(
            headers, session_id, output_text_data, error_text_data, fix_iteration_count
        )
