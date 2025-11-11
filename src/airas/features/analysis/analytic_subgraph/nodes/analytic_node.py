from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.analysis.analytic_subgraph.prompt.analytic_node_prompt import (
    analytic_node_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_session import ResearchSession

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    analysis_report: str


async def analytic_node(
    llm_name: LLM_MODEL,
    llm_client: LLMFacadeClient,
    research_session: ResearchSession,
) -> str:
    if not research_session.current_iteration:
        logger.error("No current_iteration found in research_session")
        return ""

    env = Environment()
    template = env.from_string(analytic_node_prompt)

    messages = template.render({"research_session": research_session})
    output, cost = await llm_client.structured_outputs(
        message=messages, data_model=LLMOutput, llm_name=llm_name
    )
    if output is None:
        raise ValueError("No response from LLM in analytic_node.")

    return output["analysis_report"]
