from logging import getLogger
from typing import Any

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.create.create_method_subgraph.nodes.idea_generator import (
    _parse_research_study_list,
)
from airas.features.create.create_method_subgraph.prompt.research_value_judgement_prompt import (
    research_value_judgement_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    reason: str
    judgement_result: bool


def research_value_judgement(
    llm_name: LLM_MODEL,
    research_topic: str,
    new_idea: str,
    research_study_list: list[dict[str, Any]],
) -> tuple[str, bool]:
    client = LLMFacadeClient(llm_name=llm_name)
    env = Environment()
    template = env.from_string(research_value_judgement_prompt)
    data = {
        "research_topic": research_topic,
        "new_idea": new_idea,
        "research_study_list": _parse_research_study_list(research_study_list),
    }
    messages = template.render(data)
    output, cost = client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
    )
    return (
        output["reason"],
        output["judgement_result"],
    )
