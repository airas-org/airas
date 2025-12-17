from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from airas.core.container import Container
from airas.features.github.poll_github_actions_subgraph.poll_github_actions_subgraph import (
    PollGithubActionsSubgraph,
)
from airas.services.api_client.github_client import GithubClient
from api.schemas.github_actions import (
    PollGithubActionsRequestBody,
    PollGithubActionsResponseBody,
)

router = APIRouter(prefix="/github-actions", tags=["github-actions"])


@router.post("/polling", response_model=PollGithubActionsResponseBody)
@inject
async def poll_github_actions(
    request: PollGithubActionsRequestBody,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
) -> PollGithubActionsResponseBody:
    result = (
        await PollGithubActionsSubgraph(github_client=github_client)
        .build_graph()
        .ainvoke(request)
    )
    return PollGithubActionsResponseBody(
        workflow_run_id=result["workflow_run_id"],
        status=result["status"],
        conclusion=result["conclusion"],
        execution_time=result["execution_time"],
    )
