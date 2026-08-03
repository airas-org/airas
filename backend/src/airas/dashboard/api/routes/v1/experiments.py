from typing import Annotated

from fastapi import APIRouter, Depends

from airas.core.types.runner import EphemeralCloudRunnerConfig, StaticRunnerConfig
from airas.dashboard.api.dependencies import get_github_client, get_litellm_client
from airas.dashboard.api.schemas.experiments import (
    AnalyzeExperimentRequestBody,
    AnalyzeExperimentResponseBody,
    DispatchDiagramGenerationRequestBody,
    DispatchDiagramGenerationResponseBody,
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
from airas.infra.github_client import GithubClient
from airas.infra.litellm_client import LiteLLMClient
from airas.usecases.analyzers.analyze_experiment_subgraph.analyze_experiment_subgraph import (
    AnalyzeExperimentSubgraph,
)
from airas.usecases.executors.dispatch_experiment_on_ephemeral_cloud_subgraph.dispatch_experiment_on_ephemeral_cloud_subgraph import (
    DispatchExperimentOnEphemeralCloudSubgraph,
)
from airas.usecases.executors.dispatch_experiment_on_static_runner_subgraph.dispatch_experiment_on_static_runner_subgraph import (
    DispatchExperimentOnStaticRunnerSubgraph,
)
from airas.usecases.executors.dispatch_experiment_validation_subgraph.dispatch_experiment_validation_subgraph import (
    DispatchExperimentValidationSubgraph,
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
from airas.usecases.generators.dispatch_diagram_generation_subgraph.dispatch_diagram_generation_subgraph import (
    DispatchDiagramGenerationSubgraph,
)

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("/run-ids", response_model=FetchRunIdsResponseBody)
async def fetch_run_ids(
    request: FetchRunIdsRequestBody,
    github_client: Annotated[GithubClient, Depends(get_github_client)],
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
async def fetch_experimental_results(
    request: FetchExperimentalResultsRequestBody,
    github_client: Annotated[GithubClient, Depends(get_github_client)],
) -> FetchExperimentalResultsResponseBody:
    result = (
        await FetchExperimentResultsSubgraph(github_client=github_client)
        .build_graph()
        .ainvoke(request)
    )
    return FetchExperimentalResultsResponseBody(
        experimental_results=result["experimental_results"],
        execution_time=result["execution_time"],
    )


@router.post("/sanity-checks/dispatch", response_model=DispatchSanityCheckResponseBody)
async def dispatch_sanity_check(
    request: DispatchSanityCheckRequestBody,
    github_client: Annotated[GithubClient, Depends(get_github_client)],
) -> DispatchSanityCheckResponseBody:
    if isinstance(request.runner_config, StaticRunnerConfig):
        subgraph = DispatchExperimentOnStaticRunnerSubgraph(
            github_client=github_client,
            workflow_file="run_sanity_check.yml",
            runner_label=request.runner_config.runner_label,
        )
    elif isinstance(request.runner_config, EphemeralCloudRunnerConfig):
        subgraph = DispatchExperimentOnEphemeralCloudSubgraph(
            github_client=github_client,
            target_workflow="run_sanity_check.yml",
            cloud_provider=request.runner_config.cloud_provider,
            gpu_instance_type=request.runner_config.gpu_instance_type,
            max_instance_hours=request.runner_config.max_instance_hours,
        )
    else:
        raise TypeError(
            f"Unsupported runner config type: {type(request.runner_config)}"
        )

    result = await subgraph.build_graph().ainvoke(
        {"github_config": request.github_config, "run_id": request.run_id},
    )
    return DispatchSanityCheckResponseBody(
        dispatched=result["dispatched"],
        execution_time=result["execution_time"],
    )


@router.post(
    "/validations/dispatch", response_model=DispatchExperimentValidationResponseBody
)
async def dispatch_experiment_validation(
    request: DispatchExperimentValidationRequestBody,
    github_client: Annotated[GithubClient, Depends(get_github_client)],
) -> DispatchExperimentValidationResponseBody:
    result = (
        await DispatchExperimentValidationSubgraph(
            github_client=github_client,
            llm_mapping=request.llm_mapping,
        )
        .build_graph()
        .ainvoke(request)
    )
    return DispatchExperimentValidationResponseBody(
        dispatched=result["dispatched"],
        execution_time=result["execution_time"],
    )


@router.post("/main-runs/dispatch", response_model=DispatchMainExperimentResponseBody)
async def dispatch_main_experiment(
    request: DispatchMainExperimentRequestBody,
    github_client: Annotated[GithubClient, Depends(get_github_client)],
) -> DispatchMainExperimentResponseBody:
    if isinstance(request.runner_config, StaticRunnerConfig):
        subgraph = DispatchExperimentOnStaticRunnerSubgraph(
            github_client=github_client,
            workflow_file="run_main_experiment.yml",
            runner_label=request.runner_config.runner_label,
        )
    elif isinstance(request.runner_config, EphemeralCloudRunnerConfig):
        subgraph = DispatchExperimentOnEphemeralCloudSubgraph(
            github_client=github_client,
            target_workflow="run_main_experiment.yml",
            cloud_provider=request.runner_config.cloud_provider,
            gpu_instance_type=request.runner_config.gpu_instance_type,
            max_instance_hours=request.runner_config.max_instance_hours,
        )
    else:
        raise TypeError(
            f"Unsupported runner config type: {type(request.runner_config)}"
        )

    result = await subgraph.build_graph().ainvoke(
        {"github_config": request.github_config, "run_id": request.run_id},
    )
    return DispatchMainExperimentResponseBody(
        dispatched=result["dispatched"],
        execution_time=result["execution_time"],
    )


# NOTE: In the local-agent flow figures are rendered locally (render_chart /
# render_diagram); this GHA-dispatch endpoint remains for the dashboard UI and
# is scheduled for removal in the next major release (see issue #913).
@router.post(
    "/visualizations/dispatch", response_model=DispatchVisualizationResponseBody
)
async def dispatch_visualization(
    request: DispatchVisualizationRequestBody,
    github_client: Annotated[GithubClient, Depends(get_github_client)],
) -> DispatchVisualizationResponseBody:
    result = (
        await DispatchVisualizationSubgraph(
            github_client=github_client,
            runner_label=request.runner_label,
        )
        .build_graph()
        .ainvoke(request)
    )
    return DispatchVisualizationResponseBody(
        dispatched=result["dispatched"],
        execution_time=result["execution_time"],
    )


# NOTE: Scheduled for removal in the next major release together with the
# visualization dispatch above (see issue #913).
@router.post("/diagrams/dispatch", response_model=DispatchDiagramGenerationResponseBody)
async def dispatch_diagram_generation(
    request: DispatchDiagramGenerationRequestBody,
    github_client: Annotated[GithubClient, Depends(get_github_client)],
) -> DispatchDiagramGenerationResponseBody:
    result = (
        await DispatchDiagramGenerationSubgraph(
            github_client=github_client,
            diagram_description=request.diagram_description,
            prompt_path=request.prompt_path,
            llm_mapping=request.llm_mapping,
        )
        .build_graph()
        .ainvoke(request)
    )
    return DispatchDiagramGenerationResponseBody(
        dispatched=result["dispatched"],
        execution_time=result["execution_time"],
    )


@router.post("/analyses", response_model=AnalyzeExperimentResponseBody)
async def analyze_experiment(
    request: AnalyzeExperimentRequestBody,
    litellm_client: Annotated[LiteLLMClient, Depends(get_litellm_client)],
) -> AnalyzeExperimentResponseBody:
    result = (
        await AnalyzeExperimentSubgraph(
            litellm_client=litellm_client,
            llm_mapping=request.llm_mapping,
        )
        .build_graph()
        .ainvoke(request)
    )
    return AnalyzeExperimentResponseBody(
        experimental_analysis=result["experimental_analysis"],
        execution_time=result["execution_time"],
    )
