from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

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

router = APIRouter(prefix="/research-history", tags=["research-history"])


@router.post("/download", response_model=GithubDownloadResponse)
@inject
async def download_research_history(
    request: GithubDownloadRequest,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
) -> GithubDownloadResponse:
    result = await GithubDownloadSubgraph(github_client).build_graph().ainvoke(request)
    return GithubDownloadResponse(
        research_history=result["research_history"],
        execution_time=result["execution_time"],
    )


@router.post("/upload", response_model=GithubUploadResponse)
@inject
async def upload_research_history(
    request: GithubUploadRequest,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
) -> GithubUploadResponse:
    result = await GithubUploadSubgraph(github_client).build_graph().ainvoke(request)
    return GithubUploadResponse(
        is_github_upload=result["is_github_upload"],
        execution_time=result["execution_time"],
    )
