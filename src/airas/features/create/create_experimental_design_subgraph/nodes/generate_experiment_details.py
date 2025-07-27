from jinja2 import Environment
from pydantic import BaseModel

from airas.features.create.create_experimental_design_subgraph.prompt.generate_experiment_specification_prompt import (
    generate_experiment_specification_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)


class LLMOutput(BaseModel):
    experiment_specification: str


def generate_experiment_specification(
    llm_name: LLM_MODEL,
    new_method: str,
    experiment_strategy: str,
) -> str:
    client = LLMFacadeClient(llm_name=llm_name)
    env = Environment()

    template = env.from_string(generate_experiment_specification_prompt)
    data = {"new_method": new_method, "experiment_strategy": experiment_strategy}
    messages = template.render(data)
    output, cost = client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
    )
    if output is None:
        raise ValueError("No response from LLM in generate_experiment_specification.")
    return output["experiment_specification"]
