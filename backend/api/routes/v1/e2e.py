import asyncio
import logging
import traceback
import uuid
from datetime import datetime, timezone
from typing import Annotated, Any

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException

from api.schemas.e2e import (
    ExecuteE2ERequestBody,
    ExecuteE2EResponseBody,
)
from src.airas.core.container import Container
from src.airas.features.orchestrators.execute_e2e_subgraph.execute_e2e_subgraph import (
    ExecuteE2ESubgraph,
)
from src.airas.services.api_client.arxiv_client import ArxivClient
from src.airas.services.api_client.github_client import GithubClient
from src.airas.services.api_client.langchain_client import LangChainClient
from src.airas.services.api_client.llm_client.llm_facade_client import LLMFacadeClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/e2e", tags=["e2e"])

# In-memory task storage (temporary, will be replaced with Redis later)
# because if uvicorn worker > i, it breaks.

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
    github_client: GithubClient,
    arxiv_client: ArxivClient,
    langchain_client: LangChainClient,
    llm_client: LLMFacadeClient,
) -> None:
    try:
        logger.info(f"[Task {task_id}] Starting E2E execution")
        _tasks[task_id]["status"] = "running"
        _tasks[task_id]["updated_at"] = datetime.now(timezone.utc)

        graph = ExecuteE2ESubgraph(
            github_client=github_client,
            arxiv_client=arxiv_client,
            langchain_client=langchain_client,
            llm_client=llm_client,
        ).build_graph()

        logger.info(f"[Task {task_id}] Streaming graph execution")

        async for chunk in graph.astream(request, config={"recursion_limit": 100}):
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
async def execute_e2e(
    request: ExecuteE2ERequestBody,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
    arxiv_client: Annotated[ArxivClient, Depends(Provide[Container.arxiv_client])],
    langchain_client: Annotated[
        LangChainClient, Depends(Provide[Container.langchain_client])
    ],
    llm_client: Annotated[
        LLMFacadeClient, Depends(Provide[Container.llm_facade_client])
    ],
) -> ExecuteE2EResponseBody:
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
            github_client=github_client,
            arxiv_client=arxiv_client,
            langchain_client=langchain_client,
            llm_client=llm_client,
        )
    )

    return ExecuteE2EResponseBody(
        task_id=task_id,
        status="pending",
    )


@router.get("/status/{task_id}", response_model=ExecuteE2EResponseBody)
async def get_e2e_status(task_id: str) -> ExecuteE2EResponseBody:
    if not (task := _tasks.get(task_id)):
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return ExecuteE2EResponseBody(
        task_id=task["task_id"],
        status=task["status"],
        error=task.get("error"),
        research_history=task.get("research_history"),
    )
