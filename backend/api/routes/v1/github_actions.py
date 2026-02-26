from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from langfuse import observe

from airas.container import Container
from airas.infra.github_client import GithubClient
from airas.infra.langfuse_client import LangfuseClient
from airas.usecases.github.download_github_actions_artifacts_subgraph.download_github_actions_artifacts_subgraph import (
    DownloadGithubActionsArtifactsSubgraph,
)
from airas.usecases.github.poll_github_actions_subgraph.poll_github_actions_subgraph import (
    PollGithubActionsSubgraph,
)
from airas.usecases.github.set_github_actions_secrets_subgraph.set_github_actions_secrets_subgraph import (
    SetGithubActionsSecretsSubgraph,
)
from api.dependencies.github import get_user_github_client
from api.schemas.github_actions import (
    DownloadGithubActionsArtifactsRequestBody,
    DownloadGithubActionsArtifactsResponseBody,
    PollGithubActionsRequestBody,
    PollGithubActionsResponseBody,
    SetGithubActionsSecretsRequestBody,
    SetGithubActionsSecretsResponseBody,
)

router = APIRouter(prefix="/github-actions", tags=["github-actions"])


@router.post("/polling", response_model=PollGithubActionsResponseBody)
@inject
@observe()
async def poll_github_actions(
    request: PollGithubActionsRequestBody,
    github_client: Annotated[GithubClient, Depends(get_user_github_client)],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> PollGithubActionsResponseBody:
    config = {"recursion_limit": 1000}
    if handler := langfuse_client.create_handler():
        config["callbacks"] = [handler]

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
@inject
@observe()
async def set_github_actions_secrets(
    request: SetGithubActionsSecretsRequestBody,
    github_client: Annotated[GithubClient, Depends(get_user_github_client)],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> SetGithubActionsSecretsResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await SetGithubActionsSecretsSubgraph(github_client=github_client)
        .build_graph()
        .ainvoke(request, config=config)
    )
    return SetGithubActionsSecretsResponseBody(
        secrets_set=result["secrets_set"],
        execution_time=result["execution_time"],
    )


@router.post(
    "/artifacts/download", response_model=DownloadGithubActionsArtifactsResponseBody
)
@inject
@observe()
async def download_github_actions_artifacts(
    request: DownloadGithubActionsArtifactsRequestBody,
    github_client: Annotated[GithubClient, Depends(get_user_github_client)],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> DownloadGithubActionsArtifactsResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await DownloadGithubActionsArtifactsSubgraph(github_client=github_client)
        .build_graph()
        .ainvoke(request, config=config)
    )
    return DownloadGithubActionsArtifactsResponseBody(
        artifact_data=result["artifact_data"],
        execution_time=result["execution_time"],
    )
