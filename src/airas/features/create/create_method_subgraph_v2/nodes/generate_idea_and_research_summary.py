from logging import getLogger

from jinja2 import Environment

from airas.features.create.create_method_subgraph.nodes.idea_generator import (
    parse_research_study_list,
)
from airas.features.create.create_method_subgraph_v2.prompt.generate_ide_and_research_summary_prompt import (
    generate_ide_and_research_summary_prompt,
)
from airas.features.create.create_method_subgraph_v2.types import GenerateIdea
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_study import ResearchStudy

logger = getLogger(__name__)


def generate_idea_and_research_summary(
    llm_name: LLM_MODEL,
    research_topic: str,
    research_study_list: list[ResearchStudy],
    client: LLMFacadeClient | None = None,
) -> dict[str, str]:
    client = client or LLMFacadeClient(llm_name=llm_name)
    env = Environment()

    template = env.from_string(generate_ide_and_research_summary_prompt)
    data = {
        "research_topic": research_topic,
        "research_study_list": parse_research_study_list(research_study_list),
    }
    messages = template.render(data)
    output, cost = client.structured_outputs(
        message=messages,
        data_model=GenerateIdea,
    )
    if output is None:
        raise ValueError("No response from LLM in idea_generator.")
    return output
