from unittest.mock import MagicMock, patch

import pytest

from airas.retrieve.retrieve_code_subgraph.node.extract_experimental_info import (
    extract_experimental_info,
)


def test_extract_experimental_info_success():
    fake_client = MagicMock()
    fake_client.structured_outputs.return_value = (
        {"extract_code": "print('code')", "extract_info": "info text"},
        0.01,
    )
    with patch(
        "airas.retrieve.retrieve_code_subgraph.node.extract_experimental_info.GoogelGenAIClient",
        return_value=fake_client,
    ):
        code, info = extract_experimental_info(
            model_name="gemini-2.0-flash-001",
            method_text="test method",
            repository_content_str="test repo content",
        )
        assert code == "print('code')"
        assert info == "info text"


@pytest.mark.parametrize(
    "vertexai_return, expected_exception, expected_msg",
    [
        (None, RuntimeError, "Failed to get response from Vertex AI."),
    ],
)
def test_extract_experimental_info_error(
    vertexai_return, expected_exception, expected_msg
):
    fake_client = MagicMock()
    fake_client.structured_outputs.return_value = (vertexai_return, 0.01)
    with patch(
        "airas.retrieve.retrieve_code_subgraph.node.extract_experimental_info.GoogelGenAIClient",
        return_value=fake_client,
    ):
        with pytest.raises(expected_exception) as exc:
            extract_experimental_info(
                model_name="gemini-2.0-flash-001",
                method_text="test method",
                repository_content_str="test repo content",
            )
        assert expected_msg in str(exc.value)
