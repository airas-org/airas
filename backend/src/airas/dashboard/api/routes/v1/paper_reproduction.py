from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from langfuse import observe

from airas.container import Container
from airas.core.types.github import GitHubConfig
from airas.dashboard.api.dependencies import (
    get_github_client,
    get_github_owner,
    get_langchain_client,
)
from airas.dashboard.api.schemas.github import GitHubConfigRequest
from airas.dashboard.api.schemas.paper_reproduction import (
    DispatchPaperReproductionGenerateRequestBody,
    DispatchPaperReproductionGenerateResponseBody,
    DispatchPaperReproductionRunRequestBody,
    DispatchPaperReproductionRunResponseBody,
    DispatchParameterTuningRunRequestBody,
    DispatchParameterTuningRunResponseBody,
    FetchPaperReproductionResultsRequestBody,
    FetchPaperReproductionResultsResponseBody,
    FetchParameterTuningResultsRequestBody,
    FetchParameterTuningResultsResponseBody,
)
from airas.infra.github_client import GithubClient
from airas.infra.langchain_client import LangChainClient
from airas.infra.langfuse_client import LangfuseClient
from airas.usecases.executors.dispatch_paper_reproduction_run_subgraph.dispatch_paper_reproduction_run_subgraph import (
    DispatchPaperReproductionRunSubgraph,
)
from airas.usecases.executors.dispatch_parameter_tuning_run_subgraph.dispatch_parameter_tuning_run_subgraph import (
    DispatchParameterTuningRunSubgraph,
)
from airas.usecases.executors.fetch_paper_reproduction_results_subgraph.fetch_paper_reproduction_results_subgraph import (
    FetchPaperReproductionResultsSubgraph,
)
from airas.usecases.executors.fetch_parameter_tuning_results_subgraph.fetch_parameter_tuning_results_subgraph import (
    FetchParameterTuningResultsSubgraph,
)
from airas.usecases.generators.dispatch_paper_reproduction_generate_subgraph.dispatch_paper_reproduction_generate_subgraph import (
    DispatchPaperReproductionGenerateSubgraph,
)

router = APIRouter(prefix="/paper-reproduction", tags=["paper-reproduction"])


def _build_github_config(
    github_owner: str,
    request_github_config: GitHubConfigRequest,
) -> GitHubConfig:
    return GitHubConfig(
        github_owner=github_owner,
        repository_name=request_github_config.repository_name,
        branch_name=request_github_config.branch_name,
    )


@router.post(
    "/generate/dispatch",
    response_model=DispatchPaperReproductionGenerateResponseBody,
)
@inject
@observe()
async def dispatch_paper_reproduction_generate(
    request: DispatchPaperReproductionGenerateRequestBody,
    github_owner: Annotated[str, Depends(get_github_owner)],
    github_client: Annotated[GithubClient, Depends(get_github_client)],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> DispatchPaperReproductionGenerateResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await DispatchPaperReproductionGenerateSubgraph(
            github_client=github_client,
            runner_label=request.runner_label,
            llm_mapping=request.llm_mapping,
        )
        .build_graph()
        .ainvoke(
            {
                "github_config": _build_github_config(
                    github_owner, request.github_config
                ),
                "paper_url": request.paper_url,
                "instruction": request.instruction,
                "repo_url": request.repo_url,
                "github_actions_agent": request.github_actions_agent,
            },
            config=config,
        )
    )
    return DispatchPaperReproductionGenerateResponseBody(
        dispatched=result["dispatched"],
        repro_id=result["repro_id"],
        execution_time=result["execution_time"],
    )


@router.post(
    "/run/dispatch",
    response_model=DispatchPaperReproductionRunResponseBody,
)
@inject
@observe()
async def dispatch_paper_reproduction_run(
    request: DispatchPaperReproductionRunRequestBody,
    github_owner: Annotated[str, Depends(get_github_owner)],
    github_client: Annotated[GithubClient, Depends(get_github_client)],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> DispatchPaperReproductionRunResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await DispatchPaperReproductionRunSubgraph(
            github_client=github_client,
            runner_label=request.runner_label,
        )
        .build_graph()
        .ainvoke(
            {
                "github_config": _build_github_config(
                    github_owner, request.github_config
                ),
                "repro_id": request.repro_id,
                "repo_url": request.repo_url,
            },
            config=config,
        )
    )
    return DispatchPaperReproductionRunResponseBody(
        dispatched=result["dispatched"],
        execution_time=result["execution_time"],
    )


@router.post(
    "/results",
    response_model=FetchPaperReproductionResultsResponseBody,
)
@inject
@observe()
async def fetch_paper_reproduction_results(
    request: FetchPaperReproductionResultsRequestBody,
    github_owner: Annotated[str, Depends(get_github_owner)],
    github_client: Annotated[GithubClient, Depends(get_github_client)],
    langchain_client: Annotated[LangChainClient, Depends(get_langchain_client)],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> FetchPaperReproductionResultsResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await FetchPaperReproductionResultsSubgraph(
            github_client=github_client,
            langchain_client=langchain_client,
            llm_mapping=request.llm_mapping,
        )
        .build_graph()
        .ainvoke(
            {
                "github_config": _build_github_config(
                    github_owner, request.github_config
                ),
                "repro_id": request.repro_id,
            },
            config=config,
        )
    )
    return FetchPaperReproductionResultsResponseBody(
        result=result.get("result"),
        validation=result.get("validation"),
        final_status=result.get("final_status"),
        repro_md=result.get("repro_md"),
        repro_png_base64=result.get("repro_png_base64"),
        execution_time=result["execution_time"],
    )


@router.post(
    "/parameter-tuning/dispatch",
    response_model=DispatchParameterTuningRunResponseBody,
)
@inject
@observe()
async def dispatch_parameter_tuning_run(
    request: DispatchParameterTuningRunRequestBody,
    github_owner: Annotated[str, Depends(get_github_owner)],
    github_client: Annotated[GithubClient, Depends(get_github_client)],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> DispatchParameterTuningRunResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await DispatchParameterTuningRunSubgraph(
            github_client=github_client,
            runner_label=request.runner_label,
        )
        .build_graph()
        .ainvoke(
            {
                "github_config": _build_github_config(
                    github_owner, request.github_config
                ),
                "repro_id": request.repro_id,
                "repo_url": request.repo_url,
            },
            config=config,
        )
    )
    return DispatchParameterTuningRunResponseBody(
        dispatched=result["dispatched"],
        execution_time=result["execution_time"],
    )


@router.post(
    "/parameter-tuning/results",
    response_model=FetchParameterTuningResultsResponseBody,
)
@inject
@observe()
async def fetch_parameter_tuning_results(
    request: FetchParameterTuningResultsRequestBody,
    github_owner: Annotated[str, Depends(get_github_owner)],
    github_client: Annotated[GithubClient, Depends(get_github_client)],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> FetchParameterTuningResultsResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await FetchParameterTuningResultsSubgraph(github_client=github_client)
        .build_graph()
        .ainvoke(
            {
                "github_config": _build_github_config(
                    github_owner, request.github_config
                ),
                "repro_id": request.repro_id,
            },
            config=config,
        )
    )
    return FetchParameterTuningResultsResponseBody(
        result=result.get("result"),
        tuning_figure_png_base64=result.get("tuning_figure_png_base64"),
        final_status=result.get("final_status"),
        execution_time=result["execution_time"],
    )
