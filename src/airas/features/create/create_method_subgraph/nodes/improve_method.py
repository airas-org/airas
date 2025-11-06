import json

from dependency_injector import providers
from dependency_injector.wiring import Provide, inject
from jinja2 import Environment
from pydantic import BaseModel

from airas.features.create.create_method_subgraph.prompts.improve_method_prompt import (
    improve_method_prompt,
)
from airas.services.api_client.api_clients_container import SyncContainer
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_session import ResearchSession
from airas.utils.save_prompt import save_io_on_github


class ImprovedMethod(BaseModel):
    improved_method: str


@inject
def improve_method(
    research_session: ResearchSession,
    llm_name: LLM_MODEL,
    github_repository_info: GitHubRepositoryInfo,
    llm_facade_provider: providers.Factory[LLMFacadeClient] = Provide[
        SyncContainer.llm_facade_provider
    ],
) -> str:
    client = llm_facade_provider(llm_name=llm_name)
    env = Environment()

    template = env.from_string(improve_method_prompt)
    data = {
        "research_session": research_session,
    }
    messages = template.render(data)

    output, cost = client.structured_outputs(
        message=messages,
        data_model=ImprovedMethod,
    )

    if output is None:
        raise ValueError("No response from LLM in improve_method.")

    save_io_on_github(
        github_repository_info=github_repository_info,
        input=messages,
        output=json.dumps(output, ensure_ascii=False, indent=4),
        subgraph_name="create_method_subgraph",
        node_name="improve_method",
        llm_name=llm_name,
    )

    return output["improved_method"]
