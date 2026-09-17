"""The shape of `inputs` has to be discoverable before the call.

In host-authoring mode the caller assembles these by hand — a
`research_study_list` built from `search_papers` rows, a
`compute_environment` that is an object rather than a string — and the
shape was written down nowhere. The only way to learn it was to send
something wrong and read the validation error.

The same models both validate the call and are published as
`input_json_schema`, so the documented shape cannot drift from the
accepted one.
"""

import pytest
from pydantic import ValidationError

from airas.core.types.experimental_design import ComputeEnvironment
from airas.core.types.research_study import ResearchStudy
from airas.mcp.prompt_registry import (
    GENERATION_STEPS,
    build_generation_prompt,
    get_input_json_schema,
)

HYPOTHESIS_INPUTS = {
    "research_topic": "Whether aggregate docking scores hide per-system failure",
    "research_study_list": [{"title": "PLINDER", "abstract": "A benchmark."}],
}


@pytest.mark.parametrize("step", GENERATION_STEPS)
def test_every_step_publishes_a_schema(step):
    schema = get_input_json_schema(step)

    assert schema["properties"], f"{step} publishes no input fields"


def test_an_unknown_step_names_the_ones_that_exist():
    with pytest.raises(ValueError, match="hypothesis"):
        get_input_json_schema("hypotheses")


def test_the_published_schema_is_the_one_that_validates():
    """Publishing a second, hand-written schema would let the two drift."""
    schema = get_input_json_schema("hypothesis")
    result = build_generation_prompt("hypothesis", HYPOTHESIS_INPUTS)

    assert result["input_json_schema"] == schema


def test_the_prompt_call_reports_the_shape_it_wanted():
    result = build_generation_prompt("hypothesis", HYPOTHESIS_INPUTS)

    assert set(result) == {
        "step",
        "input_json_schema",
        "output_json_schema",
        "prompt",
        "flow",
    }


def test_a_missing_input_is_a_validation_error_not_a_key_error():
    with pytest.raises(ValidationError) as excinfo:
        build_generation_prompt("hypothesis", {"research_topic": "x"})

    assert excinfo.value.errors()[0]["loc"] == ("research_study_list",)


def test_a_study_needs_only_a_title():
    """A paper that was found but not read still has to be expressible.

    Requiring full_text/references/llm_extracted_info left the caller
    inventing content for papers it had only seen the abstract of.
    """
    study = ResearchStudy(title="PLINDER", abstract="A benchmark.")

    assert study.title == "PLINDER"
    # The abstract has somewhere to go, and reaches the prompt.
    assert "A benchmark." in study.to_formatted_json()


def test_a_study_list_of_bare_titles_and_abstracts_is_accepted():
    result = build_generation_prompt("hypothesis", HYPOTHESIS_INPUTS)

    assert "PLINDER" in result["prompt"]


def test_compute_environment_carries_the_architecture():
    """arch decides whether a dependency has an installable wheel at all.

    Without the field it could only be described in free text, where
    nothing downstream could act on it.
    """
    assert "arch" in ComputeEnvironment.model_fields

    schema = get_input_json_schema("experimental_design")
    compute = schema["$defs"]["ComputeEnvironment"]["properties"]
    assert "arch" in compute
