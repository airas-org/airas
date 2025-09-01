from jinja2 import Environment
from pydantic import BaseModel

from airas.config.runtime_prompt import RuntimeKeyType, runtime_prompt_dict
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


def generate_experiment_details(
    llm_name: LLM_MODEL,
    new_method: ResearchHypothesis,
    runtime_name: RuntimeKeyType,
    feedback_text: str | None = None,
    previous_method: ResearchHypothesis | None = None,
) -> ResearchHypothesis:
    client = LLMFacadeClient(llm_name=llm_name)
    env = Environment()

    template = env.from_string(generate_experiment_details_prompt)

    data = {
        "new_method": new_method.model_dump(),
        "runtime_prompt": runtime_prompt_dict[runtime_name],
        "consistency_feedback": feedback_text,
        "previous_method": previous_method.model_dump() if previous_method else None,
    }
    messages = template.render(data)
    output, cost = client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
    )
    if output is None:
        raise ValueError("No response from LLM in generate_experiment_specification.")

    new_method.experimental_design.experiment_details = output["experiment_details"]
    return new_method
