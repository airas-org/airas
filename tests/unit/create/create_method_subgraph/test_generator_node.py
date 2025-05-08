import pytest

from typing import Any

from airas.create.create_method_subgraph.nodes.generator_node import generator_node
from airas.typing.paper import CandidatePaperInfo

@pytest.fixture
def sample_inputs() -> dict[str, Any]:
    base: CandidatePaperInfo = {
        "arxiv_id": "2001.00001",
        "arxiv_url": "https://arxiv.org/abs/2001.00001",
        "title": "Base Paper Title",
        "authors": ["Alice", "Bob"],
        "published_date": "2020-01-01",
        "journal": "Journal of Testing",
        "doi": "10.1000/j.jt.2020.01",
        "summary": "This is a summary of the base paper.",
        "github_url": "https://github.com/example/base-paper",
        "main_contributions": "Contribution A, Contribution B",
        "methodology": "We used method X.",
        "experimental_setup": "Setup details here.",
        "limitations": "Some limitations.",
        "future_research_directions": "Future work here.",
    }

    add1: CandidatePaperInfo = {
        "arxiv_id": "2001.00002",
        "arxiv_url": "https://arxiv.org/abs/2001.00002",
        "title": "Additional Paper 1",
        "authors": ["Carol"],
        "published_date": "2021-02-02",
        "journal": "Journal of Extras",
        "doi": "10.1000/j.je.2021.02",
        "summary": "Summary of additional paper 1.",
        "github_url": "https://github.com/example/additional-1",
        "main_contributions": "Contribution C",
        "methodology": "Method Y.",
        "experimental_setup": "Experimental setup details.",
        "limitations": "Limitations here.",
        "future_research_directions": "Next steps.",
    }

    add2: CandidatePaperInfo = {
        "arxiv_id": "2001.00003",
        "arxiv_url": "https://arxiv.org/abs/2001.00003",
        "title": "Additional Paper 2",
        "authors": ["Dave", "Eve"],
        "published_date": "2022-03-03",
        "journal": "Journal of More Extras",
        "doi": "10.1000/j.jme.2022.03",
        "summary": "Summary of additional paper 2.",
        "github_url": "https://github.com/example/additional-2",
        "main_contributions": "Contribution D, Contribution E",
        "methodology": "Method Z.",
        "experimental_setup": "Setup details here.",
        "limitations": "Known limitations.",
        "future_research_directions": "Future directions.",
    }

    return {
        "llm_name": "dummy-llm",
        "base_method_text": base,
        "add_method_texts": [add1, add2],
    }


@pytest.mark.parametrize(
    "dummy_return, expected, mode",
    [
        (("output result", 0.1), "output result", "success"),
        ((None, 0.1), None, "ValueError"),
    ],
)
def test_generator_node_success_and_failure(
    sample_inputs,
    dummy_return,
    expected,
    mode,
    dummy_llm_facade_client,
):
    client = dummy_llm_facade_client(sample_inputs["llm_name"])
    client._next_return = dummy_return

    match mode:
        case "success":
            result = generator_node(**sample_inputs, client=client)
            assert result == expected
        case "ValueError":
            with pytest.raises(ValueError):
                generator_node(**sample_inputs, client=client)
        case _:
            raise NotImplementedError(f"Unsupported mode: {mode}")
