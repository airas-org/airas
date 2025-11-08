from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from airas.services.api_client.llm_client.llm_facade_client import LLMFacadeClient
from airas.services.api_client.qdrant_client import QdrantClient
from api.schemas.papers import GetPaperTitleRequestBody, GetPaperTitleResponseBody
from src.airas.features.retrieve.get_paper_titles_subgraph.get_paper_titles_from_db_subgraph import (
    GetPaperTitlesFromDBSubgraph,
)
from src.airas.services.api_client.api_clients_container import (
    AsyncContainer,
    SyncContainer,
)

router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("/search/title", response_model=GetPaperTitleResponseBody)
@inject
async def get_paper_title(
    request: GetPaperTitleRequestBody,
    qdrant_client: Annotated[
        QdrantClient, Depends(Provide[SyncContainer.qdrant_client])
    ],
    llm_client: Annotated[
        LLMFacadeClient, Depends(Provide[AsyncContainer.gemini_embedding_001])
    ],
) -> GetPaperTitleResponseBody:
    result = await GetPaperTitlesFromDBSubgraph(
        qdrant_client=qdrant_client,
        llm_client=llm_client,
        max_results_per_query=3,
        semantic_search=True,
    ).arun(request.model_dump())
    return GetPaperTitleResponseBody(research_study_list=result["research_study_list"])
