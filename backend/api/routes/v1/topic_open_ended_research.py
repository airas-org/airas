import asyncio
import logging
import uuid
from typing import Annotated

from dependency_injector.wiring import Closing, Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Request
from langfuse import observe

from airas.container import Container
from airas.infra.arxiv_client import ArxivClient
from airas.infra.db.models.e2e import Status
from airas.infra.github_client import GithubClient
from airas.infra.langchain_client import LangChainClient
from airas.infra.langfuse_client import LangfuseClient
from airas.usecases.autonomous_research.topic_open_ended_research.topic_open_ended_research_service import (
    TopicOpenEndedResearchService,
)
from airas.usecases.autonomous_research.topic_open_ended_research.topic_open_ended_research_subgraph import (
    TopicOpenEndedResearchSubgraph,
)
from airas.usecases.retrieve.search_paper_titles_subgraph.nodes.search_paper_titles_from_airas_db import (
    AirasDbPaperSearchIndex,
)
from api.schemas.topic_open_ended_research import (
    TopicOpenEndedResearchListItemResponse,
    TopicOpenEndedResearchListResponseBody,
    TopicOpenEndedResearchRequestBody,
    TopicOpenEndedResearchResponseBody,
    TopicOpenEndedResearchStatusResponseBody,
    TopicOpenEndedResearchUpdateRequestBody,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/topic_open_ended_research", tags=["topic_open_ended_research"]
)
DEFAULT_CREATED_BY = uuid.UUID("00000000-0000-0000-0000-000000000001")

# TODO: [Polling/Redis] Implement asynchronous polling mechanism.
# Redis is required to persist task state (status, logs) across processes,
# allowing the client to poll progress via a separate GET /status endpoint.

# TODO: [Architecture/Celery] Introduce Celery for production hosting.
# Currently, this runs in the web server process. For long-running tasks,
# execution should be offloaded to a separate Worker process to prevent
# HTTP timeouts and ensure resilience against server restarts.


async def _execute_topic_open_ended_research(
    task_id: uuid.UUID,
    request: TopicOpenEndedResearchRequestBody,
    search_index: AirasDbPaperSearchIndex,
    github_client: GithubClient,
    arxiv_client: ArxivClient,
    langchain_client: LangChainClient,
    langfuse_client: LangfuseClient,
    e2e_service: TopicOpenEndedResearchService,
) -> None:
    try:
        logger.info(f"[Task {task_id}] Starting E2E execution")

        graph = TopicOpenEndedResearchSubgraph(
            search_index=search_index,
            github_client=github_client,
            arxiv_client=arxiv_client,
            langchain_client=langchain_client,
            e2e_service=e2e_service,
            runner_config=request.runner_config,
            wandb_config=request.wandb_config,
            task_id=task_id,
            is_github_repo_private=request.is_github_repo_private,
            num_paper_search_queries=request.num_paper_search_queries,
            papers_per_query=request.papers_per_query,
            hypothesis_refinement_iterations=request.hypothesis_refinement_iterations,
            num_experiment_models=request.num_experiment_models,
            num_experiment_datasets=request.num_experiment_datasets,
            num_comparison_methods=request.num_comparison_methods,
            experiment_code_validation_iterations=request.experiment_code_validation_iterations,
            paper_content_refinement_iterations=request.paper_content_refinement_iterations,
            latex_template_name=request.latex_template_name,
            github_actions_agent=request.github_actions_agent,
            llm_mapping=request.llm_mapping,
        ).build_graph()

        logger.info(f"[Task {task_id}] Streaming graph execution")

        config = {"recursion_limit": 100}
        if handler := langfuse_client.create_handler():
            config["callbacks"] = [handler]

        # NOTE:将来的にストリーミング UI に対応するためastreamで実装
        async for chunk in graph.astream(request, config=config):
            for node_name, node_output in chunk.items():
                if not isinstance(node_output, dict):
                    continue

                if "research_history" in node_output:
                    logger.info(
                        f"[Task {task_id}] Research history updated from node: {node_name}"
                    )

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.exception(f"[Task {task_id}] Execution failed")

        try:
            e2e_service.update(
                id=task_id, status=Status.FAILED, error_message=error_msg
            )
        except Exception:
            # If we fail to update status to FAILED, the task will remain in RUNNING state.
            # Since this runs in an async task (asyncio.create_task), exceptions won't
            # propagate to the caller, but at least we can log the error.
            logger.exception(
                f"[Task {task_id}] CRITICAL: Failed to update status to FAILED. "
                f"Task may remain in RUNNING state."
            )


@router.post("/run", response_model=TopicOpenEndedResearchResponseBody)
@inject
@observe()
async def execute_topic_open_ended_research(
    request: TopicOpenEndedResearchRequestBody,
    fastapi_request: Request,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
    arxiv_client: Annotated[ArxivClient, Depends(Provide[Container.arxiv_client])],
    langchain_client: Annotated[
        LangChainClient, Depends(Provide[Container.langchain_client])
    ],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
    e2e_service: Annotated[
        TopicOpenEndedResearchService,
        Depends(Provide[Container.topic_open_ended_research_service]),
    ],
) -> TopicOpenEndedResearchResponseBody:
    container: Container = fastapi_request.app.state.container
    task_id = uuid.uuid4()

    asyncio.create_task(
        _execute_topic_open_ended_research(
            task_id=task_id,
            request=request,
            search_index=container.airas_db_search_index(),
            github_client=github_client,
            arxiv_client=arxiv_client,
            langchain_client=langchain_client,
            langfuse_client=langfuse_client,
            e2e_service=e2e_service,
        )
    )

    return TopicOpenEndedResearchResponseBody(task_id=task_id)


@router.get(
    "/status/{task_id}", response_model=TopicOpenEndedResearchStatusResponseBody
)
@inject
@observe()
async def get_topic_open_ended_research_status(
    task_id: uuid.UUID,
    e2e_service: Annotated[
        TopicOpenEndedResearchService,
        Depends(Closing[Provide[Container.topic_open_ended_research_service]]),
    ],
) -> TopicOpenEndedResearchStatusResponseBody:
    try:
        result = e2e_service.get(task_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=404, detail=f"Task {task_id} not found"
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception(f"[Status {task_id}] Failed to get status")
        raise HTTPException(status_code=500, detail="Internal Server Error") from exc

    try:
        return TopicOpenEndedResearchStatusResponseBody.model_validate(result)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception(f"[Status {task_id}] Failed to validate response")
        raise HTTPException(
            status_code=500, detail="Failed to validate response"
        ) from exc


@router.get("", response_model=TopicOpenEndedResearchListResponseBody)
@inject
@observe()
async def list_topic_open_ended_research(
    e2e_service: Annotated[
        TopicOpenEndedResearchService,
        Depends(Closing[Provide[Container.topic_open_ended_research_service]]),
    ],
    offset: int = 0,
    limit: int | None = None,
) -> TopicOpenEndedResearchListResponseBody:
    records = e2e_service.list(offset=offset, limit=limit)
    sorted_records = sorted(records, key=lambda record: record.created_at, reverse=True)

    return TopicOpenEndedResearchListResponseBody(
        items=[
            TopicOpenEndedResearchListItemResponse.model_validate(record)
            for record in sorted_records
        ]
    )


@router.patch(
    "/{task_id}",
    response_model=TopicOpenEndedResearchStatusResponseBody,
    status_code=200,
)
@inject
@observe()
async def update_topic_open_ended_research(
    task_id: uuid.UUID,
    request: TopicOpenEndedResearchUpdateRequestBody,
    e2e_service: Annotated[
        TopicOpenEndedResearchService,
        Depends(Closing[Provide[Container.topic_open_ended_research_service]]),
    ],
) -> TopicOpenEndedResearchStatusResponseBody:
    updates = request.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    try:
        updated = e2e_service.update(id=task_id, **updates)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception(f"[Update {task_id}] Failed to update")
        raise HTTPException(status_code=500, detail="Internal Server Error") from exc

    try:
        return TopicOpenEndedResearchStatusResponseBody.model_validate(updated)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception(f"[Update {task_id}] Failed to validate response")
        raise HTTPException(
            status_code=500, detail="Failed to validate response"
        ) from exc
