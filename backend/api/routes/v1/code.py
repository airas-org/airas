from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from langfuse import observe

from airas.container import Container
from airas.infra.github_client import GithubClient
from airas.infra.langfuse_client import LangfuseClient
from airas.usecases.executors.fetch_experiment_code_subgraph.fetch_experiment_code_subgraph import (
    FetchExperimentCodeSubgraph,
)
from airas.usecases.generators.dispatch_code_generation_subgraph.dispatch_code_generation_subgraph import (
    DispatchCodeGenerationSubgraph,
)
from api.dependencies.github import get_user_github_client
from api.schemas.code import (
    DispatchCodeGenerationRequestBody,
    DispatchCodeGenerationResponseBody,
    FetchExperimentCodeRequestBody,
    FetchExperimentCodeResponseBody,
)

router = APIRouter(prefix="/code", tags=["code"])


@router.post("/generations/dispatch", response_model=DispatchCodeGenerationResponseBody)
@inject
@observe()
async def dispatch_code_generation(
    request: DispatchCodeGenerationRequestBody,
    github_client: Annotated[GithubClient, Depends(get_user_github_client)],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> DispatchCodeGenerationResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await DispatchCodeGenerationSubgraph(
            github_client=github_client,
            llm_mapping=request.llm_mapping,
        )
        .build_graph()
        .ainvoke(request, config=config)
    )
    return DispatchCodeGenerationResponseBody(
        dispatched=result["dispatched"],
        execution_time=result["execution_time"],
    )


@router.post("/fetch", response_model=FetchExperimentCodeResponseBody)
@inject
@observe()
async def fetch_experiment_code(
    request: FetchExperimentCodeRequestBody,
    github_client: Annotated[GithubClient, Depends(get_user_github_client)],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> FetchExperimentCodeResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await FetchExperimentCodeSubgraph(github_client=github_client)
        .build_graph()
        .ainvoke(request, config=config)
    )
    return FetchExperimentCodeResponseBody(
        experiment_code=result["experiment_code"],
        execution_time=result["execution_time"],
    )
