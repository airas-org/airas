from typing import Annotated

from fastapi import APIRouter, Depends

from airas.dashboard.api.dependencies import get_github_client
from airas.dashboard.api.schemas.github_actions import (
    DownloadGithubActionsArtifactsRequestBody,
    DownloadGithubActionsArtifactsResponseBody,
    PollGithubActionsRequestBody,
    PollGithubActionsResponseBody,
    SetGithubActionsSecretsRequestBody,
    SetGithubActionsSecretsResponseBody,
)
from airas.infra.github_client import GithubClient
from airas.usecases.github.download_github_actions_artifacts_subgraph.download_github_actions_artifacts_subgraph import (
    DownloadGithubActionsArtifactsSubgraph,
)
from airas.usecases.github.poll_github_actions_subgraph.poll_github_actions_subgraph import (
    PollGithubActionsSubgraph,
)
from airas.usecases.github.set_github_actions_secrets_subgraph.set_github_actions_secrets_subgraph import (
    SetGithubActionsSecretsSubgraph,
)

router = APIRouter(prefix="/github-actions", tags=["github-actions"])


@router.post("/polling", response_model=PollGithubActionsResponseBody)
async def poll_github_actions(
    request: PollGithubActionsRequestBody,
    github_client: Annotated[GithubClient, Depends(get_github_client)],
) -> PollGithubActionsResponseBody:
    config = {"recursion_limit": 1000}

    result = (
        await PollGithubActionsSubgraph(github_client=github_client)
        .build_graph()
        .ainvoke(request, config=config)
    )
    return PollGithubActionsResponseBody(
        workflow_run_id=result["workflow_run_id"],
        status=result["status"],
        conclusion=result["conclusion"],
        execution_time=result["execution_time"],
    )


@router.post("/secrets", response_model=SetGithubActionsSecretsResponseBody)
async def set_github_actions_secrets(
    request: SetGithubActionsSecretsRequestBody,
    github_client: Annotated[GithubClient, Depends(get_github_client)],
) -> SetGithubActionsSecretsResponseBody:
    result = (
        await SetGithubActionsSecretsSubgraph(
            github_client=github_client,
            secret_names=request.secret_names,
        )
        .build_graph()
        .ainvoke(request)
    )
    return SetGithubActionsSecretsResponseBody(
        secrets_set=result["secrets_set"],
        execution_time=result["execution_time"],
    )


@router.post(
    "/artifacts/download", response_model=DownloadGithubActionsArtifactsResponseBody
)
async def download_github_actions_artifacts(
    request: DownloadGithubActionsArtifactsRequestBody,
    github_client: Annotated[GithubClient, Depends(get_github_client)],
) -> DownloadGithubActionsArtifactsResponseBody:
    result = (
        await DownloadGithubActionsArtifactsSubgraph(github_client=github_client)
        .build_graph()
        .ainvoke(request)
    )
    return DownloadGithubActionsArtifactsResponseBody(
        artifact_data=result["artifact_data"],
        execution_time=result["execution_time"],
    )
