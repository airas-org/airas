from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from airas.features.github.prepare_repository_subgraph.prepare_repository_subgraph import (
    PrepareRepositorySubgraph,
)
from airas.features.github.push_code_subgraph.push_code_subgraph import PushCodeSubgraph
from airas.services.api_client.github_client import GithubClient
from api.schemas.github import (
    PrepareRepositoryRequestBody,
    PrepareRepositoryResponseBody,
    PushCodeRequestBody,
    PushCodeResponseBody,
)
from src.airas.core.container import Container

router = APIRouter(prefix="/github", tags=["github"])


@router.post("/prepare", response_model=PrepareRepositoryResponseBody)
@inject
async def prepare_repository(
    request: PrepareRepositoryRequestBody,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
) -> PrepareRepositoryResponseBody:
    return await PrepareRepositorySubgraph(github_client=github_client).arun(request)


@router.post("/push/code", response_model=PushCodeResponseBody)
@inject
async def push_code(
    request: PushCodeRequestBody,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
) -> PushCodeResponseBody:
    return await PushCodeSubgraph(github_client=github_client).arun(request)
