from jinja2 import Environment
from pydantic import BaseModel

from airas.config.runner_type_info import RunnerType, runner_info_dict
from airas.features.create.create_code_subgraph.prompt.generate_experiment_code_prompt import (
    generate_experiment_code_prompt,
)
from airas.services.api_client.llm_client.anthropic_client import CLAUDE_MODEL

# from airas.services.api_client.llm_client.llm_facade_client import (
#     LLM_MODEL,
#     LLMFacadeClient,
# )
from airas.services.api_client.llm_client.openai_client import (
    OPENAI_MODEL,
    OpenAIClient,
)
from airas.types.research_hypothesis import ResearchHypothesis


class LLMOutput(BaseModel):
    experiment_code: str


def generate_experiment_code(
    llm_name: OPENAI_MODEL,
    new_method: ResearchHypothesis,
    runner_type: RunnerType,
    secret_names: list[str],
    full_experiment_validation: tuple[bool, str],
    feedback_text: str | None = None,
    use_structured_outputs: bool = True,
) -> str:
    # TODO: We will first verify openAI's reasoning.
    # client = LLMFacedeClient(llm_name=llm_name, reasoning_effort="high", thinking_budget=32768)
    client = OpenAIClient(reasoning_effort="high")
    env = Environment()

    template = env.from_string(generate_experiment_code_prompt)

    data = {
        "new_method": new_method.model_dump(),
        "runner_type_prompt": runner_info_dict[runner_type]["prompt"],
        "secret_names": secret_names,
        "consistency_feedback": feedback_text,
        "full_experiment_validation": full_experiment_validation,
    }
    messages = template.render(data)

    # NOTE: The Claude model does not support structured output.
    if llm_name in CLAUDE_MODEL.__args__ and use_structured_outputs:
        raise ValueError(
            f"Model '{llm_name}' does not support structured output. "
            "Please set use_structured_output=False when using this model."
        )

    if use_structured_outputs:
        output, cost = client.structured_outputs(
            model_name=llm_name,
            message=messages,
            data_model=LLMOutput,
        )
    else:
        raw_output, cost = client.generate(
            model_name=llm_name,
            message=messages,
        )
        output = {"experiment_code": raw_output} if raw_output is not None else None

    if output is None:
        raise ValueError("No response from LLM in generate_experiment_code.")

    return output["experiment_code"]
