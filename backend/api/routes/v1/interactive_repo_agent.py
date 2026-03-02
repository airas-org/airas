from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from langfuse import observe

from airas.container import Container
from airas.infra.github_client import GithubClient
from airas.infra.langfuse_client import LangfuseClient
from airas.usecases.assisted_research.cancel_interactive_repo_agent_subgraph.cancel_interactive_repo_agent_subgraph import (
    CancelInteractiveRepoAgentSubgraph,
)
from airas.usecases.assisted_research.dispatch_interactive_repo_agent_subgraph.dispatch_interactive_repo_agent_subgraph import (
    DispatchInteractiveRepoAgentSubgraph,
)
from api.schemas.interactive_repo_agent import (
    CancelInteractiveRepoAgentRequestBody,
    CancelInteractiveRepoAgentResponseBody,
    DispatchInteractiveRepoAgentRequestBody,
    DispatchInteractiveRepoAgentResponseBody,
)

router = APIRouter(prefix="/interactive-repo-agent", tags=["interactive-repo-agent"])


@router.post("/dispatch", response_model=DispatchInteractiveRepoAgentResponseBody)
@inject
@observe()
async def dispatch_interactive_repo_agent(
    request: DispatchInteractiveRepoAgentRequestBody,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> DispatchInteractiveRepoAgentResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await DispatchInteractiveRepoAgentSubgraph(
            github_client=github_client,
            session_username=request.session_username,
            session_password=request.session_password,
        )
        .build_graph()
        .ainvoke(
            {
                "github_config": request.github_config,
                "github_actions_agent": request.github_actions_agent,
            },
            config=config,
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
@inject
@observe()
async def cancel_interactive_repo_agent(
    workflow_run_id: int,
    request: CancelInteractiveRepoAgentRequestBody,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> CancelInteractiveRepoAgentResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await CancelInteractiveRepoAgentSubgraph(github_client=github_client)
        .build_graph()
        .ainvoke(
            {
                "github_config": request.github_config,
                "workflow_run_id": workflow_run_id,
            },
            config=config,
        )
    )
    return CancelInteractiveRepoAgentResponseBody(
        cancelled=result["cancelled"],
        execution_time=result["execution_time"],
    )
