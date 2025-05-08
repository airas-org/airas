import pytest

from airas.publication.html_subgraph.nodes.convert_to_html import convert_to_html


@pytest.fixture
def sample_paper_content() -> dict[str, str]:
    return {
        "Section1": "Content of section 1",
        "Section2": "Content of section 2",
    }

@pytest.mark.parametrize(
    "dummy_return, expected, error_msg",
    [
        ({"generated_html_text": "<div>HTML</div>"}, "<div>HTML</div>", None),
        (None, None, "No response from the model in convert_to_html."),
        ({}, None, "Empty HTML content"),
        ({"other_key": "value"}, None, "Error: No response from the model in convert_to_html."),
        ({"generated_html_text": ""}, None, "Empty HTML content"),
    ],
)
def test_convert_to_html_with_dummy_client(
    sample_paper_content: dict[str, str],
    dummy_return,
    expected,
    error_msg,
    dummy_llm_facade_client,
):
    client = dummy_llm_facade_client("dummy-model")
    client._next_return = dummy_return

    if error_msg:
        with pytest.raises(ValueError) as excinfo:
            convert_to_html(
                llm_name="dummy-model",
                paper_content=sample_paper_content,
                client=client,
            )
        assert error_msg in str(excinfo.value)
    else:
        result = convert_to_html(
            llm_name="dummy-model",
            paper_content=sample_paper_content,
            client=client,
        )
        assert result == expected
