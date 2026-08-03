from typing import Annotated

from fastapi import APIRouter, Depends

from airas.dashboard.api.dependencies import get_github_client
from airas.dashboard.api.schemas.github import (
    PushGitHubRequestBody,
    PushGitHubResponseBody,
)
from airas.infra.github_client import GithubClient
from airas.usecases.github.push_github_subgraph.push_github_subgraph import (
    PushGitHubSubgraph,
)

router = APIRouter(prefix="/github", tags=["github"])


@router.post("/push", response_model=PushGitHubResponseBody)
async def push_github(
    request: PushGitHubRequestBody,
    github_client: Annotated[GithubClient, Depends(get_github_client)],
) -> PushGitHubResponseBody:
    result = (
        await PushGitHubSubgraph(github_client=github_client)
        .build_graph()
        .ainvoke(request)
    )
    return PushGitHubResponseBody(
        is_file_pushed=result["is_file_pushed"], execution_time=result["execution_time"]
    )
