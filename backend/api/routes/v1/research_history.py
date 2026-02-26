from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from langfuse import observe

from airas.container import Container
from airas.infra.github_client import GithubClient
from airas.infra.langfuse_client import LangfuseClient
from airas.usecases.github.github_download_subgraph import GithubDownloadSubgraph
from airas.usecases.github.github_upload_subgraph import GithubUploadSubgraph
from api.dependencies.github import get_user_github_client
from api.schemas.research_history import (
    GithubDownloadRequest,
    GithubDownloadResponse,
    GithubUploadRequest,
    GithubUploadResponse,
)

router = APIRouter(prefix="/research-history", tags=["research-history"])


@router.post("/download", response_model=GithubDownloadResponse)
@inject
@observe()
async def download_research_history(
    request: GithubDownloadRequest,
    github_client: Annotated[GithubClient, Depends(get_user_github_client)],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> GithubDownloadResponse:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await GithubDownloadSubgraph(github_client)
        .build_graph()
        .ainvoke(request, config=config)
    )
    return GithubDownloadResponse(
        research_history=result["research_history"],
        execution_time=result["execution_time"],
    )


@router.post("/upload", response_model=GithubUploadResponse)
@inject
@observe()
async def upload_research_history(
    request: GithubUploadRequest,
    github_client: Annotated[GithubClient, Depends(get_user_github_client)],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> GithubUploadResponse:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await GithubUploadSubgraph(github_client)
        .build_graph()
        .ainvoke(request, config=config)
    )
    return GithubUploadResponse(
        is_github_upload=result["is_github_upload"],
        execution_time=result["execution_time"],
    )
