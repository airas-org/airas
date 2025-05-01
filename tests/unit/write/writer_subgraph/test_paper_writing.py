import json
import pytest
from airas.write.writer_subgraph.nodes.paper_writing import WritingNode


@pytest.fixture
def fake_llm_response() -> dict[str, str]:
    return {
        "Title": "My Title",
        "Abstract": "My Abstract",
        "Introduction": "My Intro",
        "Related_Work": "My Related Work",
        "Background": "My Background",
        "Method": "My Method",
        "Experimental_Setup": "My Setup",
        "Results": "My Results",
        "Conclusions": "My Conclusions",
    }


@pytest.fixture
def node() -> WritingNode:
    node = WritingNode(llm_name="gpt-4o-mini-2024-07-18")
    return node


def test_replace_underscores_in_keys(node: WritingNode) -> None:
    inp = {"A_B": "x", "C": "y"}
    out = node._replace_underscores_in_keys(inp)
    assert out == {"A B": "x", "C": "y"}


def test_call_llm_success(
    node: WritingNode,
    monkeypatch: pytest.MonkeyPatch,
    fake_llm_response: dict[str, str],
) -> None:
    monkeypatch.setattr(
        "airas.utils.api_client.llm_facade_client.LLMFacadeClient.structured_outputs",
        lambda self, message, data_model: (fake_llm_response, 0.0),
    )
    result = node._call_llm(prompt="p", system_prompt="s")
    assert result["Related Work"] == fake_llm_response["Related_Work"]

    expected_keys = [
        "Title",
        "Abstract",
        "Introduction",
        "Related Work",
        "Background",
        "Method",
        "Experimental Setup",
        "Results",
        "Conclusions",
    ]
    for k in expected_keys:
        assert k in result


@pytest.mark.parametrize(
    "raw_response, expected_msg",
    [
        (None, "No response"),
        ("", "No response"),
        ("{}", "Missing or empty"),
        ('{"Title": ""}', "Missing or empty"),
    ],
)
def test_call_llm_errors(
    node: WritingNode,
    monkeypatch: pytest.MonkeyPatch,
    raw_response: str | None,
    expected_msg: str,
) -> None:
    def fake_structured_outputs(self, message, data_model):
        if raw_response is None or raw_response == "":
            return None, 0.0
        if isinstance(raw_response, str):
            return json.loads(raw_response), 0.0
        return raw_response, 0.0

    monkeypatch.setattr(
        "airas.utils.api_client.llm_facade_client.LLMFacadeClient.structured_outputs",
        fake_structured_outputs,
    )
    with pytest.raises(ValueError) as exc:
        node._call_llm(prompt="p", system_prompt="s")
    assert expected_msg in str(exc.value)


def test_generate_write_prompt(node: WritingNode) -> None:
    prompt = node._generate_write_prompt()
    assert "writing a research paper" in prompt


def test_generate_refinement_prompt(node: WritingNode) -> None:
    sample_content = {"Any": "Value"}
    prompt = node._generate_refinement_prompt(sample_content)
    assert "You are refining a research paper" in prompt
    assert "Here is the content that needs refinement" in prompt
    assert "Unenclosed math symbols" in prompt


def test_render_system_prompt(node: WritingNode) -> None:
    note = "This is context"
    sys_prompt = node._render_system_prompt(note)
    assert "This is context" in sys_prompt
    assert "## Title Tips" in sys_prompt
    assert "## Abstract Tips" in sys_prompt


def test_execute_full(
    node: WritingNode,
    monkeypatch: pytest.MonkeyPatch,
    fake_llm_response: dict[str, str],
) -> None:
    monkeypatch.setattr(
        "airas.utils.api_client.llm_facade_client.LLMFacadeClient.structured_outputs",
        lambda self, message, data_model: (fake_llm_response, 0.0),
    )
    result = node.execute(note="My paper context")
    assert result["Title"] == fake_llm_response["Title"]
    assert result["Related Work"] == fake_llm_response["Related_Work"]


def test_execute_refine_only(
    monkeypatch: pytest.MonkeyPatch, fake_llm_response: dict[str, str]
) -> None:
    node_refine = WritingNode(llm_name="gpt-4o-mini-2024-07-18", refine_only=True)
    initial_content = {
        "Title": "Init",
        "Abstract": "A",
        "Introduction": "I",
        "Related Work": "RW",
        "Background": "BG",
        "Method": "M",
        "Experimental Setup": "ES",
        "Results": "R",
        "Conclusions": "C",
    }
    monkeypatch.setattr(
        "airas.utils.api_client.llm_facade_client.LLMFacadeClient.structured_outputs",
        lambda self, message, data_model: (fake_llm_response, 0.0),
    )
    result = node_refine.execute(note="ctx", paper_content=initial_content)
    assert result["Title"] == fake_llm_response["Title"]
    assert result["Related Work"] == fake_llm_response["Related_Work"]


def test_execute_refine_only_without_content() -> None:
    node_refine = WritingNode(llm_name="gpt-4o-mini-2024-07-18", refine_only=True)
    with pytest.raises(ValueError) as exc:
        node_refine.execute(note="ctx")
    assert "paper_content must be provided" in str(exc.value)
