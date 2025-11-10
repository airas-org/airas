from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.analysis.analytic_subgraph.prompt.evaluate_method_prompt import (
    evaluate_method_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_session import ResearchSession

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    method_feedback: str


def evaluate_method(
    llm_name: LLM_MODEL,
    research_session: ResearchSession,
    llm_client: LLMFacadeClient,
) -> str:
    env = Environment()
    template = env.from_string(evaluate_method_prompt)

    messages = template.render({"research_session": research_session})
    output, cost = llm_client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
        llm_name=llm_name,
    )
    if output is None:
        raise ValueError("No response from LLM in evaluate_method.")

    return output["method_feedback"]
