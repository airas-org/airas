from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from api.schemas.workflows import PollWorkflowRequestBody, PollWorkflowResponseBody
from src.airas.core.container import Container
from src.airas.features.github.poll_workflow_subgraph.poll_workflow_subgraph import (
    PollWorkflowSubgraph,
)
from src.airas.services.api_client.github_client import GithubClient

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("/polling", response_model=PollWorkflowResponseBody)
@inject
async def poll_workflow(
    request: PollWorkflowRequestBody,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
) -> PollWorkflowResponseBody:
    result = (
        await PollWorkflowSubgraph(github_client=github_client)
        .build_graph()
        .ainvoke(request)
    )
    return PollWorkflowResponseBody(
        workflow_run_id=result["workflow_run_id"],
        status=result["status"],
        conclusion=result["conclusion"],
        execution_time=result["execution_time"],
    )
