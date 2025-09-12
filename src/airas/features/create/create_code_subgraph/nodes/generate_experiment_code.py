from jinja2 import Environment
from pydantic import BaseModel

from airas.config.runner_type_info import RunnerType, runner_info_dict
from airas.features.create.create_code_subgraph.prompt.generate_experiment_code_prompt import (
    generate_experiment_code_prompt,
)
from airas.services.api_client.llm_client.anthropic_client import CLAUDE_MODEL
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_hypothesis import ResearchHypothesis


class LLMOutput(BaseModel):
    experiment_code: str


def generate_experiment_code(
    llm_name: LLM_MODEL,
    new_method: ResearchHypothesis,
    runner_type: RunnerType,
    secret_names: list[str],
    generated_file_contents: dict[str, str] | None = None,
    feedback_text: str | None = None,
) -> ResearchHypothesis:
    client = LLMFacadeClient(llm_name=llm_name)
    env = Environment()

    template = env.from_string(generate_experiment_code_prompt)

    data = {
        "new_method": new_method.model_dump(),
        "runner_type_prompt": runner_info_dict[runner_type]["prompt"],
        "secret_names": secret_names,
        "consistency_feedback": feedback_text,
        "generated_file_contents": generated_file_contents,
    }
    messages = template.render(data)

    # NOTE: The Claude model does not support structured output.
    if llm_name in CLAUDE_MODEL.__args__:
        output, cost = client.generate(message=messages)
        output = {"experiment_code": output} if output is not None else None
    else:
        output, cost = client.structured_outputs(
            message=messages,
            data_model=LLMOutput,
        )

    if output is None:
        raise ValueError("No response from LLM in generate_experiment_code.")

    new_method.experimental_design.experiment_code = output["experiment_code"]
    return new_method
