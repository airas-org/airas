from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from langfuse import observe

from api.schemas.research_history import (
    GithubDownloadRequest,
    GithubDownloadResponse,
    GithubUploadRequest,
    GithubUploadResponse,
)
from src.airas.core.container import Container
from src.airas.features.github.github_download_subgraph import GithubDownloadSubgraph
from src.airas.features.github.github_upload_subgraph import GithubUploadSubgraph
from src.airas.services.api_client.github_client import GithubClient
from src.airas.services.api_client.langfuse_client import LangfuseClient

router = APIRouter(prefix="/research-history", tags=["research-history"])


@router.post("/download", response_model=GithubDownloadResponse)
@inject
@observe()
async def download_research_history(
    request: GithubDownloadRequest,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
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
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
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
