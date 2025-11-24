from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from api.schemas.papers import (
    RetrievePaperSubgraphRequestBody,
    RetrievePaperSubgraphResponseBody,
)
from src.airas.core.container import Container
from src.airas.features.retrieve.retrieve_paper_subgraph.retrieve_paper_subgraph import (
    RetrievePaperSubgraph,
)
from src.airas.services.api_client.arxiv_client import ArxivClient
from src.airas.services.api_client.llm_client.llm_facade_client import LLMFacadeClient

router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("/search", response_model=RetrievePaperSubgraphResponseBody)
@inject
async def get_paper_title(
    request: RetrievePaperSubgraphRequestBody,
    llm_client: Annotated[
        LLMFacadeClient, Depends(Provide[Container.llm_facade_client])
    ],
    arxiv_client: Annotated[ArxivClient, Depends(Provide[Container.arxiv_client])],
) -> RetrievePaperSubgraphResponseBody:
    result = (
        await RetrievePaperSubgraph(
            llm_client=llm_client,
            arxiv_client=arxiv_client,
            max_results_per_query=request.max_results_per_query,
        )
        .build_graph()
        .ainvoke(request.model_dump())
    )
    return RetrievePaperSubgraphResponseBody(
        arxiv_info_list=result["arxiv_info_list"],
        execution_time=result["execution_time"],
    )
