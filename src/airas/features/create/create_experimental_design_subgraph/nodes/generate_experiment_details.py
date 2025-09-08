from jinja2 import Environment
from pydantic import BaseModel

from airas.config.runner_type_info import RunnerType, runner_info_dict
from airas.features.create.create_experimental_design_subgraph.prompt.generate_experiment_details_prompt import (
    generate_experiment_details_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_hypothesis import ResearchHypothesis


class LLMOutput(BaseModel):
    experiment_details: str
    expected_models: list[str]
    expected_datasets: list[str]


def generate_experiment_details(
    llm_name: LLM_MODEL,
    new_method: ResearchHypothesis,
    runner_type: RunnerType,
    feedback_text: str | None = None,
    generated_file_contents: dict[str, str] | None = None,
) -> ResearchHypothesis:
    client = LLMFacadeClient(llm_name=llm_name)
    env = Environment()

    template = env.from_string(generate_experiment_details_prompt)

    data = {
        "new_method": new_method.model_dump(),
        "runner_type_prompt": runner_info_dict[runner_type]["prompt"],
        "consistency_feedback": feedback_text,
        "generated_file_contents": generated_file_contents,
    }
    messages = template.render(data)
    output, cost = client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
    )
    if output is None:
        raise ValueError("No response from LLM in generate_experiment_details.")

    new_method.experimental_design.experiment_details = output["experiment_details"]
    new_method.experimental_design.expected_models = output["expected_models"]
    new_method.experimental_design.expected_datasets = output["expected_datasets"]
    return new_method
