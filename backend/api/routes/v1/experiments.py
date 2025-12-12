from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from api.schemas.experiments import (
    AnalyzeExperimentRequestBody,
    AnalyzeExperimentResponseBody,
    ExecuteEvaluationRequestBody,
    ExecuteEvaluationResponseBody,
    ExecuteFullRequestBody,
    ExecuteFullResponseBody,
    ExecuteTrialRequestBody,
    ExecuteTrialResponseBody,
    FetchExperimentalResultsRequestBody,
    FetchExperimentalResultsResponseBody,
    FetchRunIdsRequestBody,
    FetchRunIdsResponseBody,
)
from src.airas.core.container import Container
from src.airas.features.analyzers.analyze_experiment_subgraph.analyze_experiment_subgraph import (
    AnalyzeExperimentSubgraph,
)
from src.airas.features.executors.execute_evaluation_subgraph.execute_evaluation_subgraph import (
    ExecuteEvaluationSubgraph,
)
from src.airas.features.executors.execute_full_experiment_subgraph.execute_full_experiment_subgraph import (
    ExecuteFullExperimentSubgraph,
)
from src.airas.features.executors.execute_trial_experiment_subgraph.execute_trial_experiment_subgraph import (
    ExecuteTrialExperimentSubgraph,
)
from src.airas.features.executors.fetch_experiment_results_subgraph.fetch_experiment_results_subgraph import (
    FetchExperimentResultsSubgraph,
)
from src.airas.features.executors.fetch_run_ids_subgraph.fetch_run_ids_subgraph import (
    FetchRunIdsSubgraph,
)
from src.airas.services.api_client.github_client import GithubClient
from src.airas.services.api_client.langchain_client import LangChainClient

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("/run-ids", response_model=FetchRunIdsResponseBody)
@inject
async def fetch_run_ids(
    request: FetchRunIdsRequestBody,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
) -> FetchRunIdsResponseBody:
    result = (
        await FetchRunIdsSubgraph(github_client=github_client)
        .build_graph()
        .ainvoke(request)
    )
    return FetchRunIdsResponseBody(
        run_ids=result["run_ids"],
        execution_time=result["execution_time"],
    )


@router.post("/results", response_model=FetchExperimentalResultsResponseBody)
@inject
async def fetch_experimental_results(
    request: FetchExperimentalResultsRequestBody,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
) -> FetchExperimentalResultsResponseBody:
    result = (
        await FetchExperimentResultsSubgraph(github_client=github_client)
        .build_graph()
        .ainvoke(request)
    )
    return FetchExperimentalResultsResponseBody(
        experiment_results=result["experiment_results"],
        execution_time=result["execution_time"],
    )


@router.post("/test-runs", response_model=ExecuteTrialResponseBody)
@inject
async def execute_trial(
    request: ExecuteTrialRequestBody,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
) -> ExecuteTrialResponseBody:
    result = (
        await ExecuteTrialExperimentSubgraph(github_client=github_client)
        .build_graph()
        .ainvoke(request)
    )
    return ExecuteTrialResponseBody(
        dispatched=result["dispatched"],
        run_ids=result["run_ids"],
        execution_time=result["execution_time"],
    )


@router.post("/full-runs", response_model=ExecuteFullResponseBody)
@inject
async def execute_full(
    request: ExecuteFullRequestBody,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
) -> ExecuteFullResponseBody:
    result = (
        await ExecuteFullExperimentSubgraph(github_client=github_client)
        .build_graph()
        .ainvoke(request)
    )
    return ExecuteFullResponseBody(
        all_dispatched=result["all_dispatched"],
        branch_creation_results=result["branch_creation_results"],
        execution_time=result["execution_time"],
    )


@router.post("/evaluations", response_model=ExecuteEvaluationResponseBody)
@inject
async def execute_evaluation(
    request: ExecuteEvaluationRequestBody,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
) -> ExecuteEvaluationResponseBody:
    result = (
        await ExecuteEvaluationSubgraph(github_client=github_client)
        .build_graph()
        .ainvoke(request)
    )
    return ExecuteEvaluationResponseBody(
        dispatched=result["dispatched"],
        execution_time=result["execution_time"],
    )


@router.post("/analyses", response_model=AnalyzeExperimentResponseBody)
@inject
async def analyze_experiment(
    request: AnalyzeExperimentRequestBody,
    langchain_client: Annotated[
        LangChainClient, Depends(Provide[Container.langchain_client])
    ],
) -> AnalyzeExperimentResponseBody:
    result = (
        await AnalyzeExperimentSubgraph(langchain_client=langchain_client)
        .build_graph()
        .ainvoke(request)
    )
    return AnalyzeExperimentResponseBody(
        experimental_analysis=result["experimental_analysis"],
        execution_time=result["execution_time"],
    )
