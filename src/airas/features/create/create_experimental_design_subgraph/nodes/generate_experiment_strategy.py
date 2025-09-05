from jinja2 import Environment
from pydantic import BaseModel

from airas.config.runner_type_prompt import RunnerTypeKey, runner_type_prompt_dict
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
    runner_type: RunnerTypeKey,
    feedback_text: str | None = None,
    previous_method: ResearchHypothesis | None = None,
    generated_file_contents: dict[str, str] | None = None,
) -> ResearchHypothesis:
    client = LLMFacadeClient(llm_name=llm_name)
    env = Environment()

    template = env.from_string(generate_experiment_strategy_prompt)

    data = {
        "new_method": new_method.model_dump(),
        "runner_type_prompt": runner_type_prompt_dict[runner_type],
        "consistency_feedback": feedback_text,
        "previous_method": previous_method.model_dump() if previous_method else None,
        "generated_file_contents": generated_file_contents,
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
