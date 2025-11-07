from fastapi import APIRouter

from api.schemas.paper import GetPaperTitleRequest, GetPaperTitleResponse
from src.airas.features.retrieve.get_paper_titles_subgraph.get_paper_titles_from_db_subgraph import (
    GetPaperTitlesFromDBSubgraph,
)

router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("/search/title", response_model=GetPaperTitleResponse)
async def get_paper_title(request: GetPaperTitleRequest) -> GetPaperTitleResponse:
    result = GetPaperTitlesFromDBSubgraph(
        max_results_per_query=3, semantic_search=True
    ).run(request)
    return GetPaperTitleResponse(research_study_list=result["research_study_list"])
