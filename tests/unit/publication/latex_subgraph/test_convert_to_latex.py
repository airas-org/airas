from unittest.mock import patch

import pytest

from airas.publication.latex_subgraph.nodes.convert_to_latex import convert_to_latex


@pytest.fixture
def fake_llm_response() -> dict[str, str]:
    return {
        "Title": "LaTeX Title",
        "Abstract": "This is abstract.",
        "Introduction": "Intro text",
        "Related_Work": "Related work",
        "Background": "Background",
        "Method": "Method",
        "Experimental_Setup": "Setup",
        "Results": "Results",
        "Conclusions": "Conclusion",
    }


def test_convert_to_latex_success(fake_llm_response: dict[str, str]) -> None:
    def fake_structured_outputs(*args, **kwargs):
        return fake_llm_response, 0.01

    with patch(
        "airas.utils.api_client.openai_client.OpenAIClient.structured_outputs",
        side_effect=fake_structured_outputs,
    ):
        result = convert_to_latex(
            llm_name="o3-mini-2025-01-31",
            prompt_template="",
            paper_content={key: "dummy" for key in fake_llm_response.keys()},
        )
        assert result["Title"] == "LaTeX Title"


@pytest.mark.parametrize(
    "raw_response, expected_msg",
    [
        (None, "No response"),
        ("", "Missing or empty fields in model response"),
        ("{}", "Missing or empty fields in model response"),
        ('{"Title": ""}', "Missing or empty fields in model response"),
    ],
)
def test_convert_to_latex_errors(
    fake_llm_response: dict[str, str],
    raw_response: str | None,
    expected_msg: str,
):
    def fake_structured_outputs(*args, **kwargs):
        if raw_response is None:
            return None, 0.01
        try:
            import json

            return json.loads(raw_response), 0.01
        except Exception:
            return raw_response, 0.01

    with patch(
        "airas.utils.api_client.openai_client.OpenAIClient.structured_outputs",
        side_effect=fake_structured_outputs,
    ):
        with pytest.raises(ValueError) as exc:
            convert_to_latex(
                llm_name="o3-mini-2025-01-31",
                prompt_template="",
                paper_content={key: "dummy" for key in fake_llm_response.keys()},
            )
        assert expected_msg in str(exc.value)
