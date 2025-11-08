import json
from logging import getLogger

from dependency_injector import providers
from dependency_injector.wiring import Provide, inject
from jinja2 import Environment

from airas.features.create.create_hypothesis_subgraph.prompt.generate_hypothesis_prompt import (
    generate_hypothesis_prompt,  # noqa: F401
)
from airas.features.create.create_hypothesis_subgraph.prompt.generate_simple_hypothesis_prompt import (
    generate_simple_hypothesis_prompt,
)
from airas.services.api_client.api_clients_container import SyncContainer
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_study import ResearchStudy
from airas.utils.save_prompt import save_io_on_github

logger = getLogger(__name__)


@inject
def generate_hypothesis(
    llm_name: LLM_MODEL,
    research_topic: str,
    research_study_list: list[ResearchStudy],
    github_repository_info: GitHubRepositoryInfo,
    llm_facade_provider: providers.Factory[LLMFacadeClient] = Provide[
        SyncContainer.llm_facade_provider
    ],
) -> ResearchHypothesis:
    client = llm_facade_provider(llm_name=llm_name)
    env = Environment()

    # NOTE: Simplified the experiment's difficulty level.
    # template = env.from_string(generate_hypothesis_prompt)
    template = env.from_string(generate_simple_hypothesis_prompt)
    data = {
        "research_topic": research_topic,
        "research_study_list": ResearchStudy.format_list(research_study_list),
    }
    messages = template.render(data)
    output, cost = client.structured_outputs(
        message=messages,
        data_model=ResearchHypothesis,
    )
    if output is None:
        raise ValueError("No response from LLM in generate_hypothesis.")
    save_io_on_github(
        github_repository_info=github_repository_info,
        input=messages,
        output=json.dumps(output, ensure_ascii=False, indent=4),
        subgraph_name="create_hypothesis_subgraph",
        node_name="generate_hypothesis",
        llm_name=llm_name,
    )
    return ResearchHypothesis(**output)
