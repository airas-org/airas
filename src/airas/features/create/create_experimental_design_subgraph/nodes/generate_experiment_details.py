from jinja2 import Environment
from pydantic import BaseModel

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
    consistency_feedback: list[str] | None = None,
) -> ResearchHypothesis:
    client = LLMFacadeClient(llm_name=llm_name)
    env = Environment()

    template = env.from_string(generate_experiment_details_prompt)

    method_text = new_method.method
    experiment_strategy = new_method.experimental_design.experiment_strategy

    feedback_text = None
    if consistency_feedback and len(consistency_feedback) > 0:
        feedback_text = consistency_feedback[-1]

    data = {
        "new_method": method_text,
        "experiment_strategy": experiment_strategy,
        "consistency_feedback": feedback_text,
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
