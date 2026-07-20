import os
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Request, status

from airas.container import Container
from airas.core.llm_config import uniform_llm_mapping
from airas.dashboard.api.dependencies import get_github_client, get_litellm_client
from airas.dashboard.api.schemas.papers import (
    FetchPaperFulltextRequestBody,
    FetchPaperFulltextResponseBody,
    RetrievePaperSubgraphRequestBody,
    RetrievePaperSubgraphResponseBody,
    SearchPapersRequestBody,
    SearchPapersResponseBody,
    SearchPaperTitlesRequestBody,
    SearchPaperTitlesResponseBody,
    WriteSubgraphRequestBody,
    WriteSubgraphResponseBody,
)
from airas.infra.arxiv_client import ArxivClient
from airas.infra.github_client import GithubClient
from airas.infra.litellm_client import LiteLLMClient
from airas.infra.openalex_client import OpenAlexClient
from airas.infra.semantic_scholar_client import SemanticScholarClient
from airas.usecases.retrieve.fetch_paper_fulltext_subgraph.fetch_paper_fulltext_subgraph import (
    FetchPaperFulltextSubgraph,
)
from airas.usecases.retrieve.retrieve_paper_subgraph.retrieve_paper_subgraph import (
    RetrievePaperSubgraph,
)
from airas.usecases.retrieve.search_paper_titles_subgraph.search_paper_titles_from_airas_db_subgraph import (
    SearchPaperTitlesFromAirasDbSubgraph,
)
from airas.usecases.retrieve.search_paper_titles_subgraph.search_paper_titles_from_qdrant_subgraph import (
    SearchPaperTitlesFromQdrantLLMMapping,
    SearchPaperTitlesFromQdrantSubgraph,
)
from airas.usecases.retrieve.search_papers_subgraph.search_papers_subgraph import (
    SearchPapersSubgraph,
)
from airas.usecases.writers.write_subgraph.write_subgraph import WriteSubgraph

router = APIRouter(prefix="/papers", tags=["papers"])

# The Qdrant paper-title index is a platform resource: its embeddings must be
# produced with the same model the collection was built with, so this is
# infrastructure config (env-overridable), not a user-selectable model.
_QDRANT_EMBEDDING_MODEL = os.getenv(
    "QDRANT_EMBEDDING_MODEL", "gemini/gemini-embedding-001"
)


@router.post("/search", response_model=SearchPaperTitlesResponseBody)
async def search_paper_titles(
    request: SearchPaperTitlesRequestBody,
    fastapi_request: Request,
) -> SearchPaperTitlesResponseBody:
    container: Container = fastapi_request.app.state.container

    if request.search_method == "qdrant":
        # NOTE: Qdrant embedding uses platform keys (env vars), not per-user keys.
        # LiteLLMClient() with no args falls back to os.environ.
        litellm_client = LiteLLMClient()

        qdrant_client = container.qdrant_client()
        if hasattr(qdrant_client, "__await__"):
            qdrant_client = await qdrant_client

        result = (
            await SearchPaperTitlesFromQdrantSubgraph(
                litellm_client=litellm_client,
                qdrant_client=qdrant_client,
                collection_name=request.collection_name,
                papers_per_query=request.max_results_per_query,
                llm_mapping=uniform_llm_mapping(
                    SearchPaperTitlesFromQdrantLLMMapping, _QDRANT_EMBEDDING_MODEL
                ),
            )
            .build_graph()
            .ainvoke({"queries": request.queries})
        )
    else:
        search_index = container.airas_db_search_index()
        if search_index is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="search_index is not available for airas_db search method",
            )

        result = (
            await SearchPaperTitlesFromAirasDbSubgraph(
                search_index=search_index,
                papers_per_query=request.max_results_per_query,
            )
            .build_graph()
            .ainvoke({"queries": request.queries})
        )

    return SearchPaperTitlesResponseBody(
        paper_titles=result["paper_titles"],
        execution_time=result["execution_time"],
    )


@router.post("/source-search", response_model=SearchPapersResponseBody)
@inject
async def search_papers(
    request: SearchPapersRequestBody,
    fastapi_request: Request,
    openalex_client: Annotated[
        OpenAlexClient, Depends(Provide[Container.openalex_client])
    ],
    semantic_scholar_client: Annotated[
        SemanticScholarClient, Depends(Provide[Container.semantic_scholar_client])
    ],
    arxiv_client: Annotated[ArxivClient, Depends(Provide[Container.arxiv_client])],
) -> SearchPapersResponseBody:
    container: Container = fastapi_request.app.state.container
    search_index = container.airas_db_search_index()

    result = (
        await SearchPapersSubgraph(
            openalex_client=openalex_client,
            semantic_scholar_client=semantic_scholar_client,
            arxiv_client=arxiv_client,
            airas_db_search_index=search_index,
        )
        .build_graph()
        .ainvoke(
            {
                "query": request.query,
                "sources": request.sources,
                "max_results_per_source": request.max_results_per_source,
                "year": request.year,
                "search_mode": request.search_mode,
            }
        )
    )
    return SearchPapersResponseBody(
        papers=result["papers"],
        source_results=result["source_results"],
        search_errors=result["search_errors"],
        execution_time=result["execution_time"],
    )


@router.post("/fulltext", response_model=FetchPaperFulltextResponseBody)
@inject
async def fetch_paper_fulltext(
    request: FetchPaperFulltextRequestBody,
    semantic_scholar_client: Annotated[
        SemanticScholarClient, Depends(Provide[Container.semantic_scholar_client])
    ],
) -> FetchPaperFulltextResponseBody:
    if not (request.arxiv_id or request.doi or request.pdf_url):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="One of arxiv_id, doi, or pdf_url must be provided.",
        )

    result = (
        await FetchPaperFulltextSubgraph(
            semantic_scholar_client=semantic_scholar_client,
        )
        .build_graph()
        .ainvoke(
            {
                "arxiv_id": request.arxiv_id,
                "doi": request.doi,
                "pdf_url": request.pdf_url,
            }
        )
    )
    return FetchPaperFulltextResponseBody(
        text=result["text"],
        status=result["status"],
        resolved_from=result["resolved_from"],
        execution_time=result["execution_time"],
    )


@router.post("/retrieval", response_model=RetrievePaperSubgraphResponseBody)
@inject
async def get_paper_title(
    request: RetrievePaperSubgraphRequestBody,
    litellm_client: Annotated[LiteLLMClient, Depends(get_litellm_client)],
    arxiv_client: Annotated[ArxivClient, Depends(Provide[Container.arxiv_client])],
    github_client: Annotated[GithubClient, Depends(get_github_client)],
) -> RetrievePaperSubgraphResponseBody:
    result = (
        await RetrievePaperSubgraph(
            litellm_client=litellm_client,
            arxiv_client=arxiv_client,
            github_client=github_client,
            llm_mapping=request.llm_mapping,
        )
        .build_graph()
        .ainvoke(request.model_dump())
    )
    return RetrievePaperSubgraphResponseBody(
        research_study_list=[
            study.model_dump() for study in result["research_study_list"]
        ],
        execution_time=result["execution_time"],
    )


@router.post("/generations", response_model=WriteSubgraphResponseBody)
async def generate_paper(
    request: WriteSubgraphRequestBody,
    litellm_client: Annotated[LiteLLMClient, Depends(get_litellm_client)],
) -> WriteSubgraphResponseBody:
    result = (
        await WriteSubgraph(
            litellm_client=litellm_client,
            paper_content_refinement_iterations=request.writing_refinement_rounds,
            llm_mapping=request.llm_mapping,
        )
        .build_graph()
        .ainvoke(request)
    )
    return WriteSubgraphResponseBody(
        paper_content=result["paper_content"],
        execution_time=result["execution_time"],
    )
