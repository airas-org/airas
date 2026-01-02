from logging import getLogger

from jinja2 import Environment

from airas.features.generators.generate_hypothesis_subgraph.prompts.generate_hypothesis_prompt import (
    generate_hypothesis_prompt,  # noqa: F401
)
from airas.features.generators.generate_hypothesis_subgraph.prompts.generate_simple_hypothesis_prompt import (
    generate_simple_hypothesis_prompt,
)
from airas.services.api_client.langchain_client import LangChainClient
from airas.services.api_client.llm_specs import LLM_MODELS
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_study import ResearchStudy

logger = getLogger(__name__)


async def generate_hypothesis(
    llm_name: LLM_MODELS,
    llm_client: LangChainClient,
    research_topic: str,
    research_study_list: list[ResearchStudy],
) -> ResearchHypothesis:
    env = Environment()

    # NOTE: Simplified the experiment's difficulty level.
    # template = env.from_string(generate_hypothesis_prompt)
    template = env.from_string(generate_simple_hypothesis_prompt)
    data = {
        "research_topic": research_topic,
        "research_study_list": [
            ResearchStudy.to_formatted_json(research_study)
            for research_study in research_study_list
        ],
    }
    messages = template.render(data)
    output = await llm_client.structured_outputs(
        message=messages,
        data_model=ResearchHypothesis,
        llm_name=llm_name,
    )
    if output is None:
        raise ValueError("No response from LLM in generate_hypothesis.")

    return output
