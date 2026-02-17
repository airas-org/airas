import asyncio
import logging
import uuid
from typing import Annotated, Any

from dependency_injector.wiring import Closing, Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Request
from langfuse import observe

from airas.container import Container
from airas.infra.arxiv_client import ArxivClient
from airas.infra.db.models.e2e import Status
from airas.infra.github_client import GithubClient
from airas.infra.langchain_client import LangChainClient
from airas.infra.langfuse_client import LangfuseClient
from airas.infra.litellm_client import LiteLLMClient
from airas.usecases.autonomous_research.topic_open_ended_research.topic_open_ended_research_service import (
    TopicOpenEndedResearchService,
)
from airas.usecases.autonomous_research.topic_open_ended_research.topic_open_ended_research_subgraph_v2 import (
    TopicOpenEndedResearchSubgraphV2,
)
from api.schemas.hypothesis_driven_research import (
    HypothesisDrivenResearchListItemResponse,
    HypothesisDrivenResearchListResponseBody,
    HypothesisDrivenResearchRequestBody,
    HypothesisDrivenResearchResponseBody,
    HypothesisDrivenResearchStatusResponseBody,
    HypothesisDrivenResearchUpdateRequestBody,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hypothesis_driven", tags=["hypothesis_driven"])
DEFAULT_CREATED_BY = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def _execute_hypothesis_driven_research(
    task_id: uuid.UUID,
    request: HypothesisDrivenResearchRequestBody,
    github_client: GithubClient,
    arxiv_client: ArxivClient,
    langchain_client: LangChainClient,
    litellm_client: LiteLLMClient,
    langfuse_client: LangfuseClient,
    e2e_service: TopicOpenEndedResearchService,
) -> None:
    try:
        logger.info(f"[Task {task_id}] Starting hypothesis-driven research execution")

        # Build the graph using the existing TopicOpenEndedResearchSubgraphV2
        # but we'll provide a pre-populated state with the hypothesis
        graph = TopicOpenEndedResearchSubgraphV2(
            github_client=github_client,
            arxiv_client=arxiv_client,
            langchain_client=langchain_client,
            litellm_client=litellm_client,
            qdrant_client=None,  # Not needed for hypothesis-driven
            e2e_service=e2e_service,
            runner_config=request.runner_config,
            wandb_config=request.wandb_config,
            task_id=task_id,
            is_github_repo_private=request.is_github_repo_private,
            search_method="airas_db",  # Not used since we skip search
            search_index=None,
            collection_name="",
            num_paper_search_queries=0,  # Not used
            papers_per_query=0,  # Not used
            hypothesis_refinement_iterations=0,  # Not used - hypothesis is provided
            num_experiment_models=request.num_experiment_models,
            num_experiment_datasets=request.num_experiment_datasets,
            num_comparison_methods=request.num_comparison_methods,
            paper_content_refinement_iterations=request.paper_content_refinement_iterations,
            latex_template_name=request.latex_template_name,
            github_actions_agent=request.github_actions_agent,
            llm_mapping=request.llm_mapping,
        ).build_graph()

        logger.info(f"[Task {task_id}] Streaming graph execution (hypothesis-driven)")

        config = {"recursion_limit": 100}
        if handler := langfuse_client.create_handler():
            config["callbacks"] = [handler]

        # Create initial state with hypothesis already populated
        # Use a dummy research_topic since it's required but not used
        initial_state = {
            "task_id": str(task_id),
            "github_config": request.github_config.model_dump(),
            "research_topic": f"[Hypothesis-Driven] {request.research_hypothesis.open_problems[:100]}...",
            "research_hypothesis": request.research_hypothesis.model_dump(),
            "research_study_list": [study.model_dump() for study in request.research_study_list],
        }

        async for chunk in graph.astream(initial_state, config=config):
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
    fastapi_request: Request,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
    arxiv_client: Annotated[ArxivClient, Depends(Provide[Container.arxiv_client])],
    langchain_client: Annotated[
        LangChainClient, Depends(Provide[Container.langchain_client])
    ],
    litellm_client: Annotated[
        LiteLLMClient, Depends(Provide[Container.litellm_client])
    ],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
    e2e_service: Annotated[
        TopicOpenEndedResearchService,
        Depends(Provide[Container.topic_open_ended_research_service]),
    ],
) -> HypothesisDrivenResearchResponseBody:
    task_id = uuid.uuid4()

    asyncio.create_task(
        _execute_hypothesis_driven_research(
            task_id=task_id,
            request=request,
            github_client=github_client,
            arxiv_client=arxiv_client,
            langchain_client=langchain_client,
            litellm_client=litellm_client,
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
        TopicOpenEndedResearchService,
        Depends(Closing[Provide[Container.topic_open_ended_research_service]]),
    ],
) -> HypothesisDrivenResearchStatusResponseBody:
    try:
        result = e2e_service.get(task_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=404, detail=f"Task {task_id} not found"
        ) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception(f"[Status {task_id}] Failed to get status")
        raise HTTPException(status_code=500, detail="Internal Server Error") from exc

    try:
        return HypothesisDrivenResearchStatusResponseBody.model_validate(result)
    except Exception as exc:  # pragma: no cover
        logger.exception(f"[Status {task_id}] Failed to validate response")
        raise HTTPException(
            status_code=500, detail="Failed to validate response"
        ) from exc


@router.get("", response_model=HypothesisDrivenResearchListResponseBody)
@inject
@observe()
async def list_hypothesis_driven_research(
    e2e_service: Annotated[
        TopicOpenEndedResearchService,
        Depends(Closing[Provide[Container.topic_open_ended_research_service]]),
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
        TopicOpenEndedResearchService,
        Depends(Closing[Provide[Container.topic_open_ended_research_service]]),
    ],
) -> HypothesisDrivenResearchStatusResponseBody:
    updates = request.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    try:
        updated = e2e_service.update(id=task_id, **updates)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception(f"[Update {task_id}] Failed to update")
        raise HTTPException(status_code=500, detail="Internal Server Error") from exc

    try:
        return HypothesisDrivenResearchStatusResponseBody.model_validate(updated)
    except Exception as exc:  # pragma: no cover
        logger.exception(f"[Update {task_id}] Failed to validate response")
        raise HTTPException(
            status_code=500, detail="Failed to validate response"
        ) from exc
