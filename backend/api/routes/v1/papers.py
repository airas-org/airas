from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from airas.features.retrieve.retrieve_code_subgraph.retrieve_code_subgraph import (
    RetrieveCodeSubgraph,
)
from airas.features.retrieve.retrieve_paper_content_subgraph.retrieve_paper_content_subgraph import (
    RetrievePaperContentSubgraph,
)
from airas.features.retrieve.summarize_paper_subgraph.summarize_paper_subgraph import (
    SummarizePaperSubgraph,
)
from airas.services.api_client.arxiv_client import ArxivClient
from airas.services.api_client.github_client import GithubClient
from airas.services.api_client.llm_client.llm_facade_client import LLMFacadeClient
from airas.services.api_client.qdrant_client import QdrantClient
from airas.services.api_client.semantic_scholar_client import SemanticScholarClient
from api.schemas.papers import (
    GetPaperTitleRequestBody,
    GetPaperTitleResponseBody,
    RetrieveCodeRequestBody,
    RetrieveCodeResponseBody,
    RetrievePaperContentRequestBody,
    RetrievePaperContentResponseBody,
    SummarizePaperRequestBody,
    SummarizePaperResponseBody,
)
from src.airas.core.container import Container
from src.airas.features.retrieve.get_paper_titles_subgraph.get_paper_titles_from_db_subgraph import (
    GetPaperTitlesFromDBSubgraph,
)

router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("/search/title", response_model=GetPaperTitleResponseBody)
@inject
async def get_paper_title(
    request: GetPaperTitleRequestBody,
    qdrant_client: Annotated[QdrantClient, Depends(Provide[Container.qdrant_client])],
    llm_client: Annotated[
        LLMFacadeClient, Depends(Provide[Container.llm_facade_client])
    ],
) -> GetPaperTitleResponseBody:
    result = await GetPaperTitlesFromDBSubgraph(
        qdrant_client=qdrant_client,
        llm_client=llm_client,
        max_results_per_query=10,
        semantic_search=True,
    ).arun(request)
    return GetPaperTitleResponseBody(research_study_list=result["research_study_list"])


@router.get("/content", response_model=RetrievePaperContentResponseBody)
@inject
async def retrieve_paper_content(
    request: RetrievePaperContentRequestBody,
    arxiv_client: Annotated[ArxivClient, Depends(Provide[Container.arxiv_client])],
    ss_client: Annotated[
        SemanticScholarClient, Depends(Provide[Container.semantic_scholar_client])
    ],
    llm_client: Annotated[
        LLMFacadeClient, Depends(Provide[Container.llm_facade_client])
    ],
) -> RetrievePaperContentResponseBody:
    result = await RetrievePaperContentSubgraph(
        target_study_list_source="research_study_list",
        llm_client=llm_client,
        arxiv_client=arxiv_client,
        ss_client=ss_client,
        paper_provider="arxiv",
    ).arun(request)
    return RetrievePaperContentResponseBody(
        research_study_list=result["research_study_list"]
    )


@router.get("/summarize", response_model=SummarizePaperResponseBody)
@inject
async def summarize_paper_content(
    request: SummarizePaperRequestBody,
    llm_client: Annotated[
        LLMFacadeClient, Depends(Provide[Container.llm_facade_client])
    ],
) -> SummarizePaperResponseBody:
    result = await SummarizePaperSubgraph(
        llm_client=llm_client,
    ).arun(request)
    return SummarizePaperResponseBody(research_study_list=result["research_study_list"])


@router.get("/code", response_model=RetrieveCodeResponseBody)
@inject
async def retrieve_code(
    request: RetrieveCodeRequestBody,
    llm_client: Annotated[
        LLMFacadeClient, Depends(Provide[Container.llm_facade_client])
    ],
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
) -> RetrieveCodeResponseBody:
    result = await RetrieveCodeSubgraph(
        llm_client=llm_client,
        github_client=github_client,
    ).arun(request)
    return RetrieveCodeResponseBody(research_study_list=result["research_study_list"])
