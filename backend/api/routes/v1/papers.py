from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from airas.core.container import Container
from airas.features.retrieve.retrieve_paper_subgraph.retrieve_paper_subgraph import (
    RetrievePaperSubgraph,
)
from airas.features.writers.write_subgraph.write_subgraph import WriteSubgraph
from airas.services.api_client.arxiv_client import ArxivClient
from airas.services.api_client.github_client import GithubClient
from airas.services.api_client.langchain_client import LangChainClient
from airas.services.api_client.llm_client.llm_facade_client import LLMFacadeClient
from api.schemas.papers import (
    RetrievePaperSubgraphRequestBody,
    RetrievePaperSubgraphResponseBody,
    WriteSubgraphRequestBody,
    WriteSubgraphResponseBody,
)

router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("", response_model=RetrievePaperSubgraphResponseBody)
@inject
async def get_paper_title(
    request: RetrievePaperSubgraphRequestBody,
    llm_client: Annotated[
        LLMFacadeClient, Depends(Provide[Container.llm_facade_client])
    ],
    langchain_client: Annotated[
        LangChainClient, Depends(Provide[Container.langchain_client])
    ],
    arxiv_client: Annotated[ArxivClient, Depends(Provide[Container.arxiv_client])],
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
) -> RetrievePaperSubgraphResponseBody:
    result = (
        await RetrievePaperSubgraph(
            llm_client=llm_client,
            langchain_client=langchain_client,
            arxiv_client=arxiv_client,
            github_client=github_client,
            max_results_per_query=request.max_results_per_query,
        )
        .build_graph()
        .ainvoke(request.model_dump())
    )
    return RetrievePaperSubgraphResponseBody(
        research_study_list=[
            [study.model_dump() for study in chunk]
            for chunk in result["research_study_list"]
        ],
        execution_time=result["execution_time"],
    )


@router.post("/generations", response_model=WriteSubgraphResponseBody)
@inject
async def generate_paper(
    request: WriteSubgraphRequestBody,
    langchain_client: Annotated[
        LangChainClient, Depends(Provide[Container.langchain_client])
    ],
) -> WriteSubgraphResponseBody:
    result = (
        await WriteSubgraph(
            langchain_client=langchain_client,
            writing_refinement_rounds=request.writing_refinement_rounds,
            llm_mapping=request.llm_mapping,
        )
        .build_graph()
        .ainvoke(request)
    )
    return WriteSubgraphResponseBody(
        paper_content=result["paper_content"],
        execution_time=result["execution_time"],
    )
