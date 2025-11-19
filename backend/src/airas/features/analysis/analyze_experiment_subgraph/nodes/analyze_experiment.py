from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.analysis.analyze_experiment_subgraph.prompts.analyze_experiment_prompt import (
    analyze_experiment_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_session import ResearchSession

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    analysis_report: str


async def analyze_experiment(
    llm_name: LLM_MODEL,
    llm_client: LLMFacadeClient,
    research_session: ResearchSession,
) -> str:
    if not research_session.current_iteration:
        logger.error("No current_iteration found in research_session")
        return ""

    env = Environment()
    template = env.from_string(analyze_experiment_prompt)

    messages = template.render({"research_session": research_session})
    output, cost = await llm_client.structured_outputs(
        message=messages, data_model=LLMOutput, llm_name=llm_name
    )
    if output is None:
        raise ValueError("No response from LLM in analyze_experimen.")

    return output["analysis_report"]
