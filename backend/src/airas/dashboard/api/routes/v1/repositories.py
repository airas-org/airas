from typing import Annotated

from fastapi import APIRouter, Depends

from airas.dashboard.api.dependencies import get_github_client
from airas.dashboard.api.schemas.repositories import (
    PrepareRepositorySubgraphRequestBody,
    PrepareRepositorySubgraphResponseBody,
)
from airas.infra.github_client import GithubClient
from airas.usecases.github.prepare_repository_subgraph.prepare_repository_subgraph import (
    PrepareRepositorySubgraph,
)

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.post("", response_model=PrepareRepositorySubgraphResponseBody)
async def prepare_repository(
    request: PrepareRepositorySubgraphRequestBody,
    github_client: Annotated[GithubClient, Depends(get_github_client)],
) -> PrepareRepositorySubgraphResponseBody:
    result = (
        await PrepareRepositorySubgraph(
            github_client=github_client, is_github_repo_private=request.is_private
        )
        .build_graph()
        .ainvoke(request)
    )
    return PrepareRepositorySubgraphResponseBody(
        is_repository_ready=result["is_repository_ready"],
        is_branch_ready=result["is_branch_ready"],
        execution_time=result["execution_time"],
    )
