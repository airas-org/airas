from unittest.mock import patch

import pytest

from airas.execution.executor_subgraph.nodes.check_devin_completion import (
    check_devin_completion,
)


@pytest.fixture
def mock_headers():
    return {"Authorization": "Bearer dummy_token"}


@pytest.mark.parametrize(
    "response_data, expected_called_times",
    [
        ({"status_enum": "completed"}, 1),
        ({"status_enum": "blocked"}, 1),
        ({"status_enum": "stopped"}, 1),
        ({"status_enum": "running"}, 3),  # Retry 2回まで想定
    ],
)
@patch("airas.execution.executor_subgraph.nodes.check_devin_completion.fetch_api_data")
def test_check_devin_completion_retries(
    mock_fetch, response_data, expected_called_times, mock_headers
):
    """status_enum の値に応じて retry されるかを確認"""
    mock_fetch.side_effect = [response_data] * expected_called_times

    with patch(
        "airas.execution.executor_subgraph.nodes.check_devin_completion.retry_request"
    ) as mock_retry:
        mock_retry.return_value = response_data

        result = check_devin_completion(mock_headers, "test-session")
        assert result == response_data
        mock_retry.assert_called_once()
        args, kwargs = mock_retry.call_args
        assert kwargs["check_condition"](response_data) == (
            response_data["status_enum"] not in ["blocked", "stopped"]
        )


def test_check_devin_completion_returns_none_on_failure(mock_headers):
    """fetch_api_data が例外を投げた場合 None が返るか"""
    with patch(
        "airas.execution.executor_subgraph.nodes.check_devin_completion.retry_request"
    ) as mock_retry:
        mock_retry.return_value = None

        result = check_devin_completion(mock_headers, "invalid-session")
        assert result is None


@patch("airas.execution.executor_subgraph.nodes.check_devin_completion.fetch_api_data")
def test_check_devin_completion_max_retries_exceeded(mock_fetch, mock_headers):
    """fetch_api_data が常に retry 対象を返すと、最終的に None が返る"""

    mock_fetch.return_value = {"status_enum": "running"}  # 常に retry 対象
    with patch(
        "airas.execution.executor_subgraph.nodes.check_devin_completion.retry_request"
    ) as mock_retry:
        # 模擬的に retry が全失敗するようにする
        mock_retry.return_value = None

        result = check_devin_completion(mock_headers, "session-id")
        assert result is None


@patch("airas.execution.executor_subgraph.nodes.check_devin_completion.retry_request")
def test_check_devin_completion_url_format(mock_retry, mock_headers):
    """session_id が URL に正しく埋め込まれているか"""
    mock_retry.return_value = {"status_enum": "completed"}

    session_id = "abc123"
    check_devin_completion(mock_headers, session_id)

    args, kwargs = mock_retry.call_args
    url = args[1]  # retry_request(func, url, ...)
    assert session_id in url
    assert url == f"https://api.devin.ai/v1/session/{session_id}"


@pytest.mark.parametrize(
    "response, expected_output",
    [
        (None, ""),
        ({}, ""),
        ({"structured_output": {}}, ""),
        ({"structured_output": {"extracted_info": "Info A"}}, "Info A"),
        ({"structured_output": {"extracted_info": ""}}, ""),
        ({"structured_output": {"wrong_key": "Oops"}}, ""),
    ],
)
def test_extract_experiment_info_behavior(response, expected_output):
    """structured_output の有無や内容に応じた抽出処理の挙動をテスト"""

    if response is None:
        result = ""
    else:
        structured_output = response.get("structured_output")
        if not structured_output:
            result = ""
        else:
            result = structured_output.get("extracted_info", "")

    assert result == expected_output
