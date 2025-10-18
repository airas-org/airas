import json
from logging import getLogger

from jinja2 import Environment

from airas.features.create.create_method_subgraph.nodes.idea_generator import (
    parse_research_study_list,
)
from airas.features.create.create_method_subgraph_v2.prompt.generate_idea_and_research_summary_prompt import (
    generate_idea_and_research_summary_prompt,  # noqa: F401
)
from airas.features.create.create_method_subgraph_v2.prompt.generate_simple_method_prompt import (
    generate_simple_method_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_idea import GenerateIdea, ResearchIdea
from airas.types.research_study import ResearchStudy
from airas.utils.save_prompt import save_io_on_github

logger = getLogger(__name__)


def generate_idea_and_research_summary(
    llm_name: LLM_MODEL,
    research_topic: str,
    research_study_list: list[ResearchStudy],
    github_repository_info: GitHubRepositoryInfo,
    client: LLMFacadeClient | None = None,
) -> ResearchIdea:
    client = client or LLMFacadeClient(llm_name=llm_name)
    env = Environment()

    # NOTE: Simplified the experiment's difficulty level.
    # template = env.from_string(generate_idea_and_research_summary_prompt)
    template = env.from_string(generate_simple_method_prompt)
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
    save_io_on_github(
        github_repository_info=github_repository_info,
        input=messages,
        output=json.dumps(output, ensure_ascii=False, indent=4),
        subgraph_name="create_method_subgraph_v2",
        node_name="generate_idea_and_research_summary",
        llm_name=llm_name,
    )
    new_idea_info = ResearchIdea(idea=GenerateIdea(**output))
    return new_idea_info
