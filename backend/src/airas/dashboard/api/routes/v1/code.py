from typing import Annotated

from fastapi import APIRouter, Depends

from airas.dashboard.api.dependencies import get_github_client
from airas.dashboard.api.schemas.code import (
    DispatchCodeGenerationRequestBody,
    DispatchCodeGenerationResponseBody,
    FetchExperimentCodeRequestBody,
    FetchExperimentCodeResponseBody,
)
from airas.infra.github_client import GithubClient
from airas.usecases.executors.fetch_experiment_code_subgraph.fetch_experiment_code_subgraph import (
    FetchExperimentCodeSubgraph,
)
from airas.usecases.generators.dispatch_code_generation_subgraph.dispatch_code_generation_subgraph import (
    DispatchCodeGenerationSubgraph,
)

router = APIRouter(prefix="/code", tags=["code"])


@router.post("/generations/dispatch", response_model=DispatchCodeGenerationResponseBody)
async def dispatch_code_generation(
    request: DispatchCodeGenerationRequestBody,
    github_client: Annotated[GithubClient, Depends(get_github_client)],
) -> DispatchCodeGenerationResponseBody:
    result = (
        await DispatchCodeGenerationSubgraph(
            github_client=github_client,
            llm_mapping=request.llm_mapping,
        )
        .build_graph()
        .ainvoke(request)
    )
    return DispatchCodeGenerationResponseBody(
        dispatched=result["dispatched"],
        execution_time=result["execution_time"],
    )


@router.post("/fetch", response_model=FetchExperimentCodeResponseBody)
async def fetch_experiment_code(
    request: FetchExperimentCodeRequestBody,
    github_client: Annotated[GithubClient, Depends(get_github_client)],
) -> FetchExperimentCodeResponseBody:
    result = (
        await FetchExperimentCodeSubgraph(github_client=github_client)
        .build_graph()
        .ainvoke(request)
    )
    return FetchExperimentCodeResponseBody(
        experiment_code=result["experiment_code"],
        execution_time=result["execution_time"],
    )
