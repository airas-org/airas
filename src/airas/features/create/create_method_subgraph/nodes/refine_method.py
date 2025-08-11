from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.create.create_method_subgraph.nodes.idea_generator import (
    _parse_idea_history,
    _parse_research_study_list,
)
from airas.features.create.create_method_subgraph.prompt.refine_method_prompt import (
    refine_method_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_study import ResearchStudy

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    refine_idea: str


def refine_idea(
    llm_name: LLM_MODEL,
    research_topic: str,
    new_idea: str,
    research_study_list: list[ResearchStudy],
    idea_history: list[dict[str, str]],
    refine_iterations: int,
    client: LLMFacadeClient | None = None,
) -> str:
    client = client or LLMFacadeClient(llm_name=llm_name)
    env = Environment()

    for iteration in range(refine_iterations):
        logger.info(f"Refining idea iteration {iteration + 1}/{refine_iterations}")
        template = env.from_string(refine_method_prompt)
        data = {
            "research_topic": research_topic,
            "new_idea": new_idea,
            "research_study_list": _parse_research_study_list(research_study_list),
            "idea_history": _parse_idea_history(idea_history),
        }
        messages = template.render(data)
        output, cost = client.structured_outputs(
            message=messages,
            data_model=LLMOutput,
        )
        if output is None:
            raise ValueError("No response from LLM in refine_idea.")
        new_idea = output["refine_idea"]
    return new_idea
