from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from langfuse import observe

from airas.container import Container
from airas.infra.github_client import GithubClient
from airas.infra.langfuse_client import LangfuseClient
from airas.usecases.github.push_github_subgraph.push_github_subgraph import (
    PushGitHubSubgraph,
)
from api.schemas.github import (
    PushGitHubRequestBody,
    PushGitHubResponseBody,
)

router = APIRouter(prefix="/github", tags=["github"])


@router.post("/push", response_model=PushGitHubResponseBody)
@inject
@observe()
async def push_github(
    request: PushGitHubRequestBody,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> PushGitHubResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await PushGitHubSubgraph(github_client=github_client)
        .build_graph()
        .ainvoke(request, config=config)
    )
    return PushGitHubResponseBody(
        is_file_pushed=result["is_file_pushed"], execution_time=result["execution_time"]
    )
