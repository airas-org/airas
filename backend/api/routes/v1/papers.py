from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Request, status
from langfuse import observe

from airas.core.container import Container
from airas.features.retrieve.retrieve_paper_subgraph.retrieve_paper_subgraph import (
    RetrievePaperSubgraph,
)
from airas.features.retrieve.search_paper_titles_subgraph.search_paper_titles_from_airas_db_subgraph import (
    SearchPaperTitlesFromAirasDbSubgraph,
)
from airas.features.writers.write_subgraph.write_subgraph import WriteSubgraph
from airas.services.api_client.arxiv_client import ArxivClient
from airas.services.api_client.github_client import GithubClient
from airas.services.api_client.langchain_client import LangChainClient
from airas.services.api_client.langfuse_client import LangfuseClient
from api.schemas.papers import (
    RetrievePaperSubgraphRequestBody,
    RetrievePaperSubgraphResponseBody,
    SearchMethod,
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

    subgraph: SearchPaperTitlesFromAirasDbSubgraph
    match request.search_method:
        case SearchMethod.AIRAS_DB:
            search_index = container.airas_db_search_index()
            subgraph = SearchPaperTitlesFromAirasDbSubgraph(
                search_index=search_index,
                max_results_per_query=request.max_results_per_query,
            )

        case _:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported search method: {request.search_method}",
            )

    result = await subgraph.build_graph().ainvoke(
        {"queries": request.queries},
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
            writing_refinement_rounds=request.writing_refinement_rounds,
            llm_mapping=request.llm_mapping,
        )
        .build_graph()
        .ainvoke(request, config=config)
    )
    return WriteSubgraphResponseBody(
        paper_content=result["paper_content"],
        execution_time=result["execution_time"],
    )
