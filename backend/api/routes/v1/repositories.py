from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from langfuse import observe

from airas.container import Container
from airas.infra.github_client import GithubClient
from airas.infra.langfuse_client import LangfuseClient
from airas.usecases.github.prepare_repository_subgraph.prepare_repository_subgraph import (
    PrepareRepositorySubgraph,
)
from api.dependencies.github import get_user_github_client
from api.schemas.repositories import (
    PrepareRepositorySubgraphRequestBody,
    PrepareRepositorySubgraphResponseBody,
)

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.post("", response_model=PrepareRepositorySubgraphResponseBody)
@inject
@observe()
async def prepare_repository(
    request: PrepareRepositorySubgraphRequestBody,
    github_client: Annotated[GithubClient, Depends(get_user_github_client)],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> PrepareRepositorySubgraphResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await PrepareRepositorySubgraph(
            github_client=github_client, is_github_repo_private=request.is_private
        )
        .build_graph()
        .ainvoke(request, config=config)
    )
    return PrepareRepositorySubgraphResponseBody(
        is_repository_ready=result["is_repository_ready"],
        is_branch_ready=result["is_branch_ready"],
        execution_time=result["execution_time"],
    )
