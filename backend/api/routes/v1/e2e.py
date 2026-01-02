import asyncio
import logging
import traceback
import uuid
from datetime import datetime, timezone
from typing import Annotated, Any

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Request
from langfuse import observe

from airas.container import Container
from airas.infra.arxiv_client import ArxivClient
from airas.infra.github_client import GithubClient
from airas.infra.langchain_client import LangChainClient
from airas.infra.langfuse_client import LangfuseClient
from airas.usecases.orchestrators.execute_e2e_subgraph.execute_e2e_subgraph import (
    ExecuteE2ESubgraph,
)
from airas.usecases.retrieve.search_paper_titles_subgraph.nodes.search_paper_titles_from_airas_db import (
    AirasDbPaperSearchIndex,
)
from api.schemas.e2e import (
    ExecuteE2ERequestBody,
    ExecuteE2EResponseBody,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/e2e", tags=["e2e"])

# In-memory task storage (temporary, will be replaced with Redis later)
# because if uvicorn worker count > 1, it breaks.

_tasks: dict[str, dict[str, Any]] = {}


# TODO: [Polling/Redis] Implement asynchronous polling mechanism.
# Redis is required to persist task state (status, logs) across processes,
# allowing the client to poll progress via a separate GET /status endpoint.

# TODO: [Architecture/Celery] Introduce Celery for production hosting.
# Currently, this runs in the web server process. For long-running tasks,
# execution should be offloaded to a separate Worker process to prevent
# HTTP timeouts and ensure resilience against server restarts.


async def _execute_e2e(
    task_id: str,
    request: ExecuteE2ERequestBody,
    search_index: AirasDbPaperSearchIndex,
    github_client: GithubClient,
    arxiv_client: ArxivClient,
    langchain_client: LangChainClient,
    langfuse_client: LangfuseClient,
) -> None:
    try:
        logger.info(f"[Task {task_id}] Starting E2E execution")
        _tasks[task_id]["status"] = "running"
        _tasks[task_id]["updated_at"] = datetime.now(timezone.utc)

        graph = ExecuteE2ESubgraph(
            search_index=search_index,
            github_client=github_client,
            arxiv_client=arxiv_client,
            langchain_client=langchain_client,
            runner_config=request.runner_config,
            wandb_config=request.wandb_config,
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
        ).build_graph()

        logger.info(f"[Task {task_id}] Streaming graph execution")

        config = {"recursion_limit": 100}
        if handler := langfuse_client.create_handler():
            config["callbacks"] = [handler]

        async for chunk in graph.astream(request, config=config):
            for node_name, node_output in chunk.items():
                if not isinstance(node_output, dict):
                    continue

                if "research_history" in node_output:
                    _tasks[task_id]["research_history"] = node_output[
                        "research_history"
                    ]
                    _tasks[task_id]["updated_at"] = datetime.now(timezone.utc)
                    logger.info(
                        f"[Task {task_id}] Research history updated from node: {node_name}"
                    )

                if "status" in node_output:
                    _tasks[task_id]["status"] = node_output["status"]
                    _tasks[task_id]["updated_at"] = datetime.now(timezone.utc)

        logger.info(f"[Task {task_id}] Execution completed successfully")
        _tasks[task_id]["status"] = "completed"
        _tasks[task_id]["updated_at"] = datetime.now(timezone.utc)

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"[Task {task_id}] Execution failed: {error_msg}")
        logger.error(f"[Task {task_id}] Traceback:\n{traceback.format_exc()}")

        _tasks[task_id]["status"] = "failed"
        _tasks[task_id]["error"] = error_msg
        _tasks[task_id]["updated_at"] = datetime.now(timezone.utc)


@router.post("/run", response_model=ExecuteE2EResponseBody)
@inject
@observe()
async def execute_e2e(
    request: ExecuteE2ERequestBody,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
    arxiv_client: Annotated[ArxivClient, Depends(Provide[Container.arxiv_client])],
    langchain_client: Annotated[
        LangChainClient, Depends(Provide[Container.langchain_client])
    ],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
    fastapi_request: Request,
) -> ExecuteE2EResponseBody:
    container: Container = fastapi_request.app.state.container
    task_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    _tasks[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "created_at": now,
        "updated_at": now,
        "result": None,
        "error": None,
        "research_history": None,
    }

    asyncio.create_task(
        _execute_e2e(
            task_id=task_id,
            request=request,
            search_index=container.airas_db_search_index(),
            github_client=github_client,
            arxiv_client=arxiv_client,
            langchain_client=langchain_client,
            langfuse_client=langfuse_client,
        )
    )

    return ExecuteE2EResponseBody(
        task_id=task_id,
        status="pending",
    )


@router.get("/status/{task_id}", response_model=ExecuteE2EResponseBody)
@observe()
async def get_e2e_status(task_id: str) -> ExecuteE2EResponseBody:
    if not (task := _tasks.get(task_id)):
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return ExecuteE2EResponseBody(
        task_id=task["task_id"],
        status=task["status"],
        error=task.get("error"),
        research_history=task.get("research_history"),
    )
