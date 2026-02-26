import asyncio
import logging
import uuid
from typing import Annotated

from dependency_injector.wiring import Closing, Provide, inject
from fastapi import APIRouter, Depends, HTTPException
from langfuse import observe

from airas.container import Container
from airas.infra.db.models.e2e import Status
from airas.infra.github_client import GithubClient
from airas.infra.langchain_client import LangChainClient
from airas.infra.langfuse_client import LangfuseClient
from airas.usecases.autonomous_research.e2e_research_service_protocol import (
    E2EResearchServiceProtocol,
)
from airas.usecases.autonomous_research.hypothesis_driven_research.hypothesis_driven_research import (
    HypothesisDrivenResearch,
)
from api.dependencies.github import get_user_github_client
from api.ee.auth.dependencies import get_current_user_id
from api.schemas.hypothesis_driven_research import (
    HypothesisDrivenResearchListItemResponse,
    HypothesisDrivenResearchListResponseBody,
    HypothesisDrivenResearchRequestBody,
    HypothesisDrivenResearchResponseBody,
    HypothesisDrivenResearchStatusResponseBody,
    HypothesisDrivenResearchUpdateRequestBody,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/hypothesis_driven_research", tags=["hypothesis_driven_research"]
)


async def _execute_hypothesis_driven_research(
    task_id: uuid.UUID,
    created_by: uuid.UUID,
    request: HypothesisDrivenResearchRequestBody,
    github_client: GithubClient,
    langchain_client: LangChainClient,
    langfuse_client: LangfuseClient,
    e2e_service: E2EResearchServiceProtocol,
) -> None:
    try:
        logger.info(f"[Task {task_id}] Starting HypothesisDrivenResearch execution")

        graph = HypothesisDrivenResearch(
            github_client=github_client,
            langchain_client=langchain_client,
            e2e_service=e2e_service,
            runner_config=request.runner_config,
            wandb_config=request.wandb_config,
            task_id=task_id,
            created_by=created_by,
            is_github_repo_private=request.is_github_repo_private,
            num_experiment_models=request.num_experiment_models,
            num_experiment_datasets=request.num_experiment_datasets,
            num_comparison_methods=request.num_comparison_methods,
            paper_content_refinement_iterations=request.paper_content_refinement_iterations,
            github_actions_agent=request.github_actions_agent,
            latex_template_name=request.latex_template_name,
            llm_mapping=request.llm_mapping,
        ).build_graph()

        logger.info(f"[Task {task_id}] Streaming graph execution")

        config = {"recursion_limit": 100}
        if handler := langfuse_client.create_handler():
            config["callbacks"] = [handler]

        async for chunk in graph.astream(
            {
                "task_id": task_id,
                "github_config": request.github_config,
                "research_hypothesis": request.research_hypothesis,
                "research_topic": request.research_topic,
            },
            config=config,
        ):
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
            logger.exception(
                f"[Task {task_id}] CRITICAL: Failed to update status to FAILED. "
                f"Task may remain in RUNNING state."
            )


@router.post("/run", response_model=HypothesisDrivenResearchResponseBody)
@inject
@observe()
async def execute_hypothesis_driven_research(
    request: HypothesisDrivenResearchRequestBody,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    github_client: Annotated[GithubClient, Depends(get_user_github_client)],
    langchain_client: Annotated[
        LangChainClient, Depends(Provide[Container.langchain_client])
    ],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
    e2e_service: Annotated[
        E2EResearchServiceProtocol,
        Depends(Provide[Container.e2e_research_service]),
    ],
) -> HypothesisDrivenResearchResponseBody:
    task_id = uuid.uuid4()

    asyncio.create_task(
        _execute_hypothesis_driven_research(
            task_id=task_id,
            created_by=current_user_id,
            request=request,
            github_client=github_client,
            langchain_client=langchain_client,
            langfuse_client=langfuse_client,
            e2e_service=e2e_service,
        )
    )

    return HypothesisDrivenResearchResponseBody(task_id=task_id)


@router.get(
    "/status/{task_id}", response_model=HypothesisDrivenResearchStatusResponseBody
)
@inject
@observe()
async def get_hypothesis_driven_research_status(
    task_id: uuid.UUID,
    e2e_service: Annotated[
        E2EResearchServiceProtocol,
        Depends(Closing[Provide[Container.e2e_research_service]]),
    ],
) -> HypothesisDrivenResearchStatusResponseBody:
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
        return HypothesisDrivenResearchStatusResponseBody.model_validate(result)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception(f"[Status {task_id}] Failed to validate response")
        raise HTTPException(
            status_code=500, detail="Failed to validate response"
        ) from exc


@router.get("", response_model=HypothesisDrivenResearchListResponseBody)
@inject
@observe()
async def list_hypothesis_driven_research(
    e2e_service: Annotated[
        E2EResearchServiceProtocol,
        Depends(Closing[Provide[Container.e2e_research_service]]),
    ],
    offset: int = 0,
    limit: int | None = None,
) -> HypothesisDrivenResearchListResponseBody:
    records = e2e_service.list(offset=offset, limit=limit)
    sorted_records = sorted(records, key=lambda record: record.created_at, reverse=True)

    return HypothesisDrivenResearchListResponseBody(
        items=[
            HypothesisDrivenResearchListItemResponse.model_validate(record)
            for record in sorted_records
        ]
    )


@router.patch(
    "/{task_id}",
    response_model=HypothesisDrivenResearchStatusResponseBody,
    status_code=200,
)
@inject
@observe()
async def update_hypothesis_driven_research(
    task_id: uuid.UUID,
    request: HypothesisDrivenResearchUpdateRequestBody,
    e2e_service: Annotated[
        E2EResearchServiceProtocol,
        Depends(Closing[Provide[Container.e2e_research_service]]),
    ],
) -> HypothesisDrivenResearchStatusResponseBody:
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
        return HypothesisDrivenResearchStatusResponseBody.model_validate(updated)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception(f"[Update {task_id}] Failed to validate response")
        raise HTTPException(
            status_code=500, detail="Failed to validate response"
        ) from exc
