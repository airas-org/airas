import pytest
from unittest.mock import patch
from airas.publication.html_subgraph.nodes.convert_to_html import convert_to_html


def test_convert_to_html_success():
    with patch(
        "airas.utils.api_client.llm_facade_client.LLMFacadeClient.structured_outputs",
        return_value=({"generated_html_text": "<p>OK</p>"}, 0.01),
    ):
        result = convert_to_html(
            llm_name="gpt-4o-mini-2024-07-18", paper_content={"sec1": "text"}
        )
        assert result == "<p>OK</p>"


@pytest.mark.parametrize(
    "raw_response, expected_msg",
    [
        (None, "No response"),
        ("", "Empty HTML content"),
        ("{}", "Empty HTML content"),
        ('{"generated_html_text": ""}', "Empty HTML content"),
    ],
)
def test_convert_to_html_errors(raw_response, expected_msg):
    def fake_structured_outputs(*args, **kwargs):
        if raw_response is None:
            return None, 0.01
        try:
            import json

            return json.loads(raw_response), 0.01
        except Exception:
            return raw_response, 0.01

    with patch(
        "airas.utils.api_client.llm_facade_client.LLMFacadeClient.structured_outputs",
        side_effect=fake_structured_outputs,
    ):
        with pytest.raises(ValueError) as exc:
            convert_to_html(
                llm_name="gpt-4o-mini-2024-07-18", paper_content={"sec1": "text"}
            )
        assert expected_msg in str(exc.value)
