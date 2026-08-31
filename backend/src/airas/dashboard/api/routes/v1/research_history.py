from typing import Annotated

from fastapi import APIRouter, Depends

from airas.dashboard.api.dependencies import get_github_client
from airas.dashboard.api.schemas.research_history import (
    GithubDownloadRequest,
    GithubDownloadResponse,
    GithubUploadRequest,
    GithubUploadResponse,
)
from airas.infra.github_client import GithubClient
from airas.usecases.github.github_download_subgraph import GithubDownloadSubgraph
from airas.usecases.github.github_upload_subgraph import GithubUploadSubgraph

router = APIRouter(prefix="/research-history", tags=["research-history"])


@router.post("/download", response_model=GithubDownloadResponse)
async def download_research_history(
    request: GithubDownloadRequest,
    github_client: Annotated[GithubClient, Depends(get_github_client)],
) -> GithubDownloadResponse:
    result = await GithubDownloadSubgraph(github_client).build_graph().ainvoke(request)
    return GithubDownloadResponse(
        research_history=result["research_history"],
        execution_time=result["execution_time"],
    )


@router.post("/upload", response_model=GithubUploadResponse)
async def upload_research_history(
    request: GithubUploadRequest,
    github_client: Annotated[GithubClient, Depends(get_github_client)],
) -> GithubUploadResponse:
    result = await GithubUploadSubgraph(github_client).build_graph().ainvoke(request)
    return GithubUploadResponse(
        is_github_upload=result["is_github_upload"],
        execution_time=result["execution_time"],
    )
