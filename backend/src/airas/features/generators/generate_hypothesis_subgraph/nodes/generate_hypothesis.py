from logging import getLogger

from jinja2 import Environment

from airas.features.generators.generate_hypothesis_subgraph.prompts.generate_hypothesis_prompt import (
    generate_hypothesis_prompt,  # noqa: F401
)
from airas.features.generators.generate_hypothesis_subgraph.prompts.generate_simple_hypothesis_prompt import (
    generate_simple_hypothesis_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_study import ResearchStudy

logger = getLogger(__name__)


async def generate_hypothesis(
    llm_name: LLM_MODEL,
    llm_client: LLMFacadeClient,
    research_objective: str,
    research_study_list: list[ResearchStudy],
) -> ResearchHypothesis:
    env = Environment()

    # NOTE: Simplified the experiment's difficulty level.
    # template = env.from_string(generate_hypothesis_prompt)
    template = env.from_string(generate_simple_hypothesis_prompt)
    data = {
        "research_objective": research_objective,
        "research_study_list": ResearchStudy.format_list(research_study_list),
    }
    messages = template.render(data)
    output, cost = await llm_client.structured_outputs(
        message=messages,
        data_model=ResearchHypothesis,
        llm_name=llm_name,
    )
    if output is None:
        raise ValueError("No response from LLM in generate_hypothesis.")

    return ResearchHypothesis(**output)
