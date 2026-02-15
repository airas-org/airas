from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Request, status
from langfuse import observe

from airas.container import Container
from airas.infra.arxiv_client import ArxivClient
from airas.infra.github_client import GithubClient
from airas.infra.langchain_client import LangChainClient
from airas.infra.langfuse_client import LangfuseClient
from airas.usecases.retrieve.retrieve_paper_subgraph.retrieve_paper_subgraph import (
    RetrievePaperSubgraph,
)
from airas.usecases.retrieve.search_paper_titles_subgraph.search_paper_titles_from_airas_db_subgraph import (
    SearchPaperTitlesFromAirasDbSubgraph,
)
from airas.usecases.retrieve.search_paper_titles_subgraph.search_paper_titles_from_qdrant_subgraph import (
    SearchPaperTitlesFromQdrantSubgraph,
)
from airas.usecases.writers.write_subgraph.write_subgraph import WriteSubgraph
from api.schemas.papers import (
    RetrievePaperSubgraphRequestBody,
    RetrievePaperSubgraphResponseBody,
    SearchPaperTitlesRequestBody,
    SearchPaperTitlesResponseBody,
    WriteSubgraphRequestBody,
    WriteSubgraphResponseBody,
)

router = APIRouter(prefix="/papers", tags=["papers"])


@router.post("/search", response_model=SearchPaperTitlesResponseBody)
@observe()
async def search_paper_titles(
    request: SearchPaperTitlesRequestBody,
    fastapi_request: Request,
) -> SearchPaperTitlesResponseBody:
    container: Container = fastapi_request.app.state.container

    if request.search_method == "qdrant":
        litellm_client = container.litellm_client()
        if hasattr(litellm_client, "__await__"):
            litellm_client = await litellm_client

        qdrant_client = container.qdrant_client()
        if hasattr(qdrant_client, "__await__"):
            qdrant_client = await qdrant_client

        result = (
            await SearchPaperTitlesFromQdrantSubgraph(
                litellm_client=litellm_client,
                qdrant_client=qdrant_client,
                collection_name=request.collection_name,
                papers_per_query=request.max_results_per_query,
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


@router.post("/retrieval", response_model=RetrievePaperSubgraphResponseBody)
@inject
@observe()
async def get_paper_title(
    request: RetrievePaperSubgraphRequestBody,
    langchain_client: Annotated[
        LangChainClient, Depends(Provide[Container.langchain_client])
    ],
    arxiv_client: Annotated[ArxivClient, Depends(Provide[Container.arxiv_client])],
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> RetrievePaperSubgraphResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await RetrievePaperSubgraph(
            langchain_client=langchain_client,
            arxiv_client=arxiv_client,
            github_client=github_client,
            llm_mapping=request.llm_mapping,
        )
        .build_graph()
        .ainvoke(request.model_dump(), config=config)
    )
    return RetrievePaperSubgraphResponseBody(
        research_study_list=[
            study.model_dump() for study in result["research_study_list"]
        ],
        execution_time=result["execution_time"],
    )


@router.post("/generations", response_model=WriteSubgraphResponseBody)
@inject
@observe()
async def generate_paper(
    request: WriteSubgraphRequestBody,
    langchain_client: Annotated[
        LangChainClient, Depends(Provide[Container.langchain_client])
    ],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> WriteSubgraphResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await WriteSubgraph(
            langchain_client=langchain_client,
            paper_content_refinement_iterations=request.writing_refinement_rounds,
            llm_mapping=request.llm_mapping,
        )
        .build_graph()
        .ainvoke(request, config=config)
    )
    return WriteSubgraphResponseBody(
        paper_content=result["paper_content"],
        execution_time=result["execution_time"],
    )
