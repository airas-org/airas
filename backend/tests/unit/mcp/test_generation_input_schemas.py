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
from airas.core.types.research_history import ResearchHistory
from airas.core.types.research_study import ResearchStudy
from airas.mcp.prompt_registry import (
    GENERATION_STEPS,
    build_generation_prompt,
    get_input_json_schema,
)
from airas.mcp.server import _reject_unknown_history_keys

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


def test_a_generation_step_error_does_not_offer_a_non_step():
    """research_history has a schema but is not something to generate.

    Listing it among the available steps would send the caller straight
    into a second error.
    """
    with pytest.raises(ValueError, match="Unknown step") as excinfo:
        build_generation_prompt("research_history", {})

    assert "research_history" not in str(excinfo.value).split("Available:")[1]


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


class TestResearchHistoryKeys:
    """The upload accepted eight top-level keys and kept two, reporting success.

    ResearchHistory leaves pydantic's default `extra="ignore"` in place, so
    the other six vanished during validation and `is_github_upload` came
    back true. A later session then restores a history with the experiment
    results, run ids and paper location simply absent.
    """

    # The exact call from the 2026-08-05 run.
    SUPPLIED = {
        "research_topic": "aggregate docking scores",
        "research_hypothesis": {},
        "results": {},
        "runs": [],
        "paper": {},
        "compute": {},
        "primary_metric": "lddt_pli",
        "known_infrastructure_constraint": "aarch64",
    }

    def test_keys_that_would_be_dropped_are_rejected(self):
        with pytest.raises(ValueError) as excinfo:
            _reject_unknown_history_keys(self.SUPPLIED)

        message = str(excinfo.value)
        for dropped in ("results", "runs", "paper", "compute", "primary_metric"):
            assert dropped in message
        # The escape hatch has to be named, or the caller just deletes data.
        assert "additional_data" in message

    def test_the_escape_hatch_is_accepted(self):
        _reject_unknown_history_keys(
            {
                "research_topic": "aggregate docking scores",
                "additional_data": {"runs": [], "primary_metric": "lddt_pli"},
            }
        )

    def test_a_declared_field_is_accepted(self):
        _reject_unknown_history_keys({"experiment_history": {"cycles": []}})

    def test_the_accepted_shape_is_published(self):
        schema = get_input_json_schema("research_history")

        assert "additional_data" in schema["properties"]
        assert "experiment_history" in schema["properties"]

    def test_the_parse_side_stays_lenient(self):
        """Downloading must not fail on a hand-written file with stray keys.

        The skills tell agents to write .research/research_history.json
        themselves, and github_download swallows a validation failure into
        an empty history — strictness there would lose everything.
        """
        history = ResearchHistory.model_validate(
            {"research_topic": "t", "something_a_human_added": 1}
        )

        assert history.research_topic == "t"

    @pytest.mark.asyncio
    async def test_the_shape_is_published_where_the_client_already_looks(self):
        """A `dict[str, Any]` parameter publishes nothing the caller can use.

        The tool listing said `additionalProperties: true` with no
        properties at all, so a client had no way to learn the shape
        without a second call it had no reason to make.
        """
        from airas.mcp.server import mcp

        tool = {t.name: t for t in await mcp.list_tools()}["upload_research_history"]
        published = tool.inputSchema["$defs"]["_ResearchHistoryInput"]

        assert published["additionalProperties"] is False
        assert "additional_data" in published["properties"]
        assert "experiment_history" in published["properties"]

    def test_a_non_object_is_named_rather_than_raising_a_type_error(self):
        with pytest.raises(ValueError, match="JSON object"):
            _reject_unknown_history_keys(["research_topic"])
