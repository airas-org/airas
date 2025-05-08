import pytest

from airas.write.writer_subgraph.nodes.paper_writing import WritingNode


@pytest.fixture
def sample_llm_output() -> dict[str, str]:
    return {
        "Title": "A Novel Approach to Testing",
        "Abstract": "This abstract summarizes the novel testing approach.",
        "Introduction": "In this paper, we introduce our testing method.",
        "Related_Work": "Several works have explored testing paradigms.",
        "Background": "Background on testing frameworks is provided.",
        "Method": "We propose a templated test generation method.",
        "Experimental_Setup": "We ran tests on dummy data.",
        "Results": "Our tests passed with 100% success.",
        "Conclusions": "This method is effective for unit testing.",
    }


def test_replace_underscores_in_keys(dummy_llm_facade_client):
    client = dummy_llm_facade_client("dummy-model")
    node = WritingNode(llm_name="dummy-model", client=client)

    transformed = node._replace_underscores_in_keys({
        "Related_Work": "val1",
        "Experimental_Setup": "val2",
    })
    assert "Related Work" in transformed
    assert transformed["Related Work"] == "val1"
    assert "Experimental Setup" in transformed
    assert transformed["Experimental Setup"] == "val2"


def test_generate_write_and_refinement_prompts(dummy_llm_facade_client):
    client = dummy_llm_facade_client("dummy-model")
    node = WritingNode(llm_name="dummy-model", client=client)

    write_prompt = node._generate_write_prompt()
    assert "research paper" in write_prompt
    refine_prompt = node._generate_refinement_prompt({"Title": "Test"})
    assert "You are refining a research paper" in refine_prompt


def test_execute_refine_only_requires_content(dummy_llm_facade_client):
    client = dummy_llm_facade_client("dummy-model")
    node = WritingNode(llm_name="dummy-model", client=client, refine_only=True)

    with pytest.raises(ValueError) as excinfo:
        node.execute(note="dummy note", paper_content=None)
    assert "paper_content must be provided when refine_only is True" in str(excinfo.value)


def test_execute_refine_only_success(dummy_llm_facade_client, sample_llm_output):
    client = dummy_llm_facade_client("dummy-model")
    client._next_return = sample_llm_output
    node = WritingNode(llm_name="dummy-model", client=client, refine_only=True)

    result = node.execute(note="dummy note", paper_content=sample_llm_output)
    expected = {
        "Title": sample_llm_output["Title"],
        "Abstract": sample_llm_output["Abstract"],
        "Introduction": sample_llm_output["Introduction"],
        "Related Work": sample_llm_output["Related_Work"],
        "Background": sample_llm_output["Background"],
        "Method": sample_llm_output["Method"],
        "Experimental Setup": sample_llm_output["Experimental_Setup"],
        "Results": sample_llm_output["Results"],
        "Conclusions": sample_llm_output["Conclusions"],
    }
    assert result == expected
