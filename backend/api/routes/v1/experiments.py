from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from langfuse import observe

from airas.container import Container
from airas.infra.github_client import GithubClient
from airas.infra.langchain_client import LangChainClient
from airas.infra.langfuse_client import LangfuseClient
from airas.usecases.analyzers.analyze_experiment_subgraph.analyze_experiment_subgraph import (
    AnalyzeExperimentSubgraph,
)
from airas.usecases.executors.dispatch_experiment_validation_subgraph.dispatch_experiment_validation_subgraph import (
    DispatchExperimentValidationSubgraph,
)
from airas.usecases.executors.dispatch_main_experiment_subgraph.dispatch_main_experiment_subgraph import (
    DispatchMainExperimentSubgraph,
)
from airas.usecases.executors.dispatch_sanity_check_subgraph.dispatch_sanity_check_subgraph import (
    DispatchSanityCheckSubgraph,
)
from airas.usecases.executors.dispatch_visualization_subgraph.dispatch_visualization_subgraph import (
    DispatchVisualizationSubgraph,
)
from airas.usecases.executors.fetch_experiment_results_subgraph.fetch_experiment_results_subgraph import (
    FetchExperimentResultsSubgraph,
)
from airas.usecases.executors.fetch_run_ids_subgraph.fetch_run_ids_subgraph import (
    FetchRunIdsSubgraph,
)
from api.schemas.experiments import (
    AnalyzeExperimentRequestBody,
    AnalyzeExperimentResponseBody,
    DispatchExperimentValidationRequestBody,
    DispatchExperimentValidationResponseBody,
    DispatchMainExperimentRequestBody,
    DispatchMainExperimentResponseBody,
    DispatchSanityCheckRequestBody,
    DispatchSanityCheckResponseBody,
    DispatchVisualizationRequestBody,
    DispatchVisualizationResponseBody,
    FetchExperimentalResultsRequestBody,
    FetchExperimentalResultsResponseBody,
    FetchRunIdsRequestBody,
    FetchRunIdsResponseBody,
)

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("/run-ids", response_model=FetchRunIdsResponseBody)
@inject
@observe()
async def fetch_run_ids(
    request: FetchRunIdsRequestBody,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> FetchRunIdsResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await FetchRunIdsSubgraph(github_client=github_client)
        .build_graph()
        .ainvoke(request, config=config)
    )
    return FetchRunIdsResponseBody(
        run_ids=result["run_ids"],
        execution_time=result["execution_time"],
    )


@router.post("/results", response_model=FetchExperimentalResultsResponseBody)
@inject
@observe()
async def fetch_experimental_results(
    request: FetchExperimentalResultsRequestBody,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> FetchExperimentalResultsResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await FetchExperimentResultsSubgraph(github_client=github_client)
        .build_graph()
        .ainvoke(request, config=config)
    )
    return FetchExperimentalResultsResponseBody(
        experimental_results=result["experimental_results"],
        execution_time=result["execution_time"],
    )


@router.post("/sanity-checks/dispatch", response_model=DispatchSanityCheckResponseBody)
@inject
@observe()
async def dispatch_sanity_check(
    request: DispatchSanityCheckRequestBody,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> DispatchSanityCheckResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await DispatchSanityCheckSubgraph(
            github_client=github_client,
        )
        .build_graph()
        .ainvoke(request, config=config)
    )
    return DispatchSanityCheckResponseBody(
        dispatched=result["dispatched"],
        execution_time=result["execution_time"],
    )


@router.post(
    "/validations/dispatch", response_model=DispatchExperimentValidationResponseBody
)
@inject
@observe()
async def dispatch_experiment_validation(
    request: DispatchExperimentValidationRequestBody,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> DispatchExperimentValidationResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await DispatchExperimentValidationSubgraph(
            github_client=github_client,
            llm_mapping=request.llm_mapping,
        )
        .build_graph()
        .ainvoke(request, config=config)
    )
    return DispatchExperimentValidationResponseBody(
        dispatched=result["dispatched"],
        execution_time=result["execution_time"],
    )


@router.post("/main-runs/dispatch", response_model=DispatchMainExperimentResponseBody)
@inject
@observe()
async def dispatch_main_experiment(
    request: DispatchMainExperimentRequestBody,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> DispatchMainExperimentResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await DispatchMainExperimentSubgraph(
            github_client=github_client,
        )
        .build_graph()
        .ainvoke(request, config=config)
    )
    return DispatchMainExperimentResponseBody(
        dispatched=result["dispatched"],
        execution_time=result["execution_time"],
    )


@router.post(
    "/visualizations/dispatch", response_model=DispatchVisualizationResponseBody
)
@inject
@observe()
async def dispatch_visualization(
    request: DispatchVisualizationRequestBody,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> DispatchVisualizationResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await DispatchVisualizationSubgraph(
            github_client=github_client,
        )
        .build_graph()
        .ainvoke(request, config=config)
    )
    return DispatchVisualizationResponseBody(
        dispatched=result["dispatched"],
        execution_time=result["execution_time"],
    )


@router.post("/analyses", response_model=AnalyzeExperimentResponseBody)
@inject
@observe()
async def analyze_experiment(
    request: AnalyzeExperimentRequestBody,
    langchain_client: Annotated[
        LangChainClient, Depends(Provide[Container.langchain_client])
    ],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> AnalyzeExperimentResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await AnalyzeExperimentSubgraph(
            langchain_client=langchain_client,
            llm_mapping=request.llm_mapping,
        )
        .build_graph()
        .ainvoke(request, config=config)
    )
    return AnalyzeExperimentResponseBody(
        experimental_analysis=result["experimental_analysis"],
        execution_time=result["execution_time"],
    )
