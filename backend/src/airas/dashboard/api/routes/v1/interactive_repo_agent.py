from typing import Annotated

from fastapi import APIRouter, Depends

from airas.dashboard.api.dependencies import get_github_client
from airas.dashboard.api.schemas.interactive_repo_agent import (
    CancelInteractiveRepoAgentRequestBody,
    CancelInteractiveRepoAgentResponseBody,
    DispatchInteractiveRepoAgentRequestBody,
    DispatchInteractiveRepoAgentResponseBody,
)
from airas.infra.github_client import GithubClient
from airas.usecases.assisted_research.cancel_interactive_repo_agent_subgraph.cancel_interactive_repo_agent_subgraph import (
    CancelInteractiveRepoAgentSubgraph,
)
from airas.usecases.assisted_research.dispatch_interactive_repo_agent_subgraph.dispatch_interactive_repo_agent_subgraph import (
    DispatchInteractiveRepoAgentSubgraph,
)

router = APIRouter(prefix="/interactive-repo-agent", tags=["interactive-repo-agent"])


@router.post("/dispatch", response_model=DispatchInteractiveRepoAgentResponseBody)
async def dispatch_interactive_repo_agent(
    request: DispatchInteractiveRepoAgentRequestBody,
    github_client: Annotated[GithubClient, Depends(get_github_client)],
) -> DispatchInteractiveRepoAgentResponseBody:
    result = (
        await DispatchInteractiveRepoAgentSubgraph(
            github_client=github_client,
            session_username=request.session_username,
            session_password=request.session_password.get_secret_value(),
        )
        .build_graph()
        .ainvoke(
            {
                "github_config": request.github_config,
                "github_actions_agent": request.github_actions_agent,
            },
        )
    )
    return DispatchInteractiveRepoAgentResponseBody(
        dispatched=result["dispatched"],
        workflow_run_id=result["workflow_run_id"],
        tunnel_url=result.get("artifact_data", {}).get("tunnel_url"),
        execution_time=result["execution_time"],
    )


@router.post(
    "/{workflow_run_id}/cancel",
    response_model=CancelInteractiveRepoAgentResponseBody,
)
async def cancel_interactive_repo_agent(
    workflow_run_id: int,
    request: CancelInteractiveRepoAgentRequestBody,
    github_client: Annotated[GithubClient, Depends(get_github_client)],
) -> CancelInteractiveRepoAgentResponseBody:
    result = (
        await CancelInteractiveRepoAgentSubgraph(github_client=github_client)
        .build_graph()
        .ainvoke(
            {
                "github_config": request.github_config,
                "workflow_run_id": workflow_run_id,
            },
        )
    )
    return CancelInteractiveRepoAgentResponseBody(
        cancelled=result["cancelled"],
        execution_time=result["execution_time"],
    )
