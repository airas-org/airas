from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.create.create_method_subgraph.prompt.idea_generator_prompt import (
    idea_generator_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_study import ResearchStudy

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    new_idea: str


def idea_generator(
    llm_name: LLM_MODEL,
    research_topic: str,
    research_study_list: list[ResearchStudy],
    idea_history: list[dict[str, str]],
    client: LLMFacadeClient | None = None,
) -> str:
    client = client or LLMFacadeClient(llm_name=llm_name)
    env = Environment()

    template = env.from_string(idea_generator_prompt)
    data = {
        "research_topic": research_topic,
        "research_study_list": parse_research_study_list(research_study_list),
        "idea_history": _parse_idea_history(idea_history),
    }
    messages = template.render(data)
    output, cost = client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
    )
    if output is None:
        raise ValueError("No response from LLM in idea_generator.")
    return output["new_idea"]


def parse_research_study_list(research_study_list: list[ResearchStudy]) -> str:
    data_str = ""
    for research_study in research_study_list:
        info = research_study.llm_extracted_info
        if not info:
            continue
        data_str += f"""\
Title:{research_study.title}
Main Contributions:{info.main_contributions}
Methodology:{info.methodology}
Experimental Setup:{info.experimental_setup}
Limitations:{info.limitations}
Future Research Directions:{info.future_research_directions}
Experiment:{info.experimental_code}
Experiment Result:{info.experimental_info}"""
    return data_str


def _parse_idea_history(idea_history: list[dict[str, str]]) -> str:
    if not idea_history:
        return "No previous ideas."

    lines = []
    for idea in idea_history:
        lines.append(f"- {idea['new_idea']} (Reason: {idea['reason']})")
    return "\n".join(lines)
