import logging

from jinja2 import Environment

from airas.config.runner_type_info import RunnerType, runner_info_dict
from airas.features.create.create_experimental_design_subgraph.prompt.search_external_resources_prompt import (
    search_external_resources_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLMFacadeClient,
)
from airas.services.api_client.llm_client.openai_client import OPENAI_MODEL
from airas.types.research_hypothesis import ResearchHypothesis

logger = logging.getLogger(__name__)

OPENAI_MODEL_SET = set(OPENAI_MODEL.__args__)


def search_external_resources(
    llm_name: OPENAI_MODEL,
    new_method: ResearchHypothesis,
    runner_type: RunnerType,
    prompt_template: str = search_external_resources_prompt,
) -> ResearchHypothesis:
    if llm_name not in OPENAI_MODEL_SET:
        raise ValueError(
            f"It needs to be an OpenAI model. Invalid model name: {llm_name}"
        )

    client = LLMFacadeClient(llm_name=llm_name)
    env = Environment()

    template = env.from_string(prompt_template)
    messages = template.render(
        {
            "new_method": new_method.model_dump(),
            "runner_type_prompt": runner_info_dict[runner_type]["prompt"],
        }
    )

    output, cost = client.web_search(message=messages)

    if output is None:
        raise ValueError("No response from LLM in search_external_resources.")

    new_method.experimental_design.external_resources = output.get("external_resources")
    return new_method
