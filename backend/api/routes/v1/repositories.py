from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from airas.core.container import Container
from airas.features.github.prepare_repository_subgraph.prepare_repository_subgraph import (
    PrepareRepositorySubgraph,
)
from airas.services.api_client.github_client import GithubClient
from api.schemas.repositories import (
    PrepareRepositorySubgraphRequestBody,
    PrepareRepositorySubgraphResponseBody,
)

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.post("", response_model=PrepareRepositorySubgraphResponseBody)
@inject
async def prepare_repository(
    request: PrepareRepositorySubgraphRequestBody,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
) -> PrepareRepositorySubgraphResponseBody:
    result = (
        await PrepareRepositorySubgraph(
            github_client=github_client, is_private=request.is_private
        )
        .build_graph()
        .ainvoke(request)
    )
    return PrepareRepositorySubgraphResponseBody(
        is_repository_ready=result["is_repository_ready"],
        is_branch_ready=result["is_branch_ready"],
        execution_time=result["execution_time"],
    )
