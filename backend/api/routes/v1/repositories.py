from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from api.schemas.repositories import (
    PrepareRepositorySubgraphRequestBody,
    PrepareRepositorySubgraphResponseBody,
)
from src.airas.core.container import Container
from src.airas.features.github.prepare_repository_subgraph.prepare_repository_subgraph import (
    PrepareRepositorySubgraph,
)
from src.airas.services.api_client.github_client import GithubClient

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
