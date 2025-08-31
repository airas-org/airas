from jinja2 import Environment
from pydantic import BaseModel

from airas.config.runtime_prompt import RuntimeKeyType, runtime_prompt_dict
from airas.features.create.create_experimental_design_subgraph.prompt.generate_experiment_strategy_prompt import (
    generate_experiment_strategy_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_hypothesis import ExperimentalDesign, ResearchHypothesis


class LLMOutput(BaseModel):
    experiment_strategy: str


def generate_experiment_strategy(
    llm_name: LLM_MODEL,
    new_method: ResearchHypothesis,
    runtime_prompt_name: RuntimeKeyType,
    consistency_feedback: list[str] | None = None,
) -> ResearchHypothesis:
    client = LLMFacadeClient(llm_name=llm_name)
    env = Environment()

    template = env.from_string(generate_experiment_strategy_prompt)

    method_text = new_method.method

    feedback_text = None
    if consistency_feedback and len(consistency_feedback) > 0:
        feedback_text = consistency_feedback[-1]

    data = {
        "new_method": method_text,
        "runtime_prompt": runtime_prompt_dict[runtime_prompt_name],
        "consistency_feedback": feedback_text,
    }
    messages = template.render(data)
    output, cost = client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
    )
    if output is None:
        raise ValueError("No response from LLM in generate_experiment_strategy.")

    if new_method.experimental_design is None:
        new_method.experimental_design = ExperimentalDesign()
    new_method.experimental_design.experiment_strategy = output["experiment_strategy"]

    return new_method
