from jinja2 import Environment

from airas.features.create.create_experimental_design_subgraph.prompt.generate_experiment_details_prompt import (
    generate_experiment_details_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)


def generate_experiment_details(
    llm_name: LLM_MODEL,
    new_method: str,
    verification_policy: str,
) -> str:
    client = LLMFacadeClient(llm_name=llm_name)

    env = Environment()
    template = env.from_string(generate_experiment_details_prompt)
    data = {"new_method": new_method, "verification_policy": verification_policy}
    messages = template.render(data)
    output, cost = client.generate(
        message=messages,
    )
    if output is None:
        raise ValueError("No response from LLM in generate_experiment_details.")
    return output
