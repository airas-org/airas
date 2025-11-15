from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from airas.features.create.create_experimental_design_subgraph.create_experimental_design_subgraph import (
    CreateExperimentalDesignSubgraph,
)
from airas.features.create.create_hypothesis_subgraph.create_hypothesis_subgraph import (
    CreateHypothesisSubgraph,
)
from airas.features.create.create_method_subgraph.create_method_subgraph import (
    CreateMethodSubgraph,
)
from airas.services.api_client.arxiv_client import ArxivClient
from airas.services.api_client.llm_client.llm_facade_client import LLMFacadeClient
from airas.services.api_client.qdrant_client import QdrantClient
from airas.services.api_client.semantic_scholar_client import SemanticScholarClient
from api.schemas.create import (
    CreateExperimentalDesignRequestBody,
    CreateExperimentalDesignResponseBody,
    CreateHypothesisRequestBody,
    CreateHypothesisResponseBody,
    CreateMethodRequestBody,
    CreateMethodResponseBody,
)
from src.airas.core.container import Container

router = APIRouter(prefix="/create", tags=["papers"])


@router.get("/hypothesis", response_model=CreateHypothesisResponseBody)
@inject
async def create_hypothesis(
    request: CreateHypothesisRequestBody,
    qdrant_client: Annotated[QdrantClient, Depends(Provide[Container.qdrant_client])],
    arxiv_client: Annotated[ArxivClient, Depends(Provide[Container.arxiv_client])],
    ss_client: Annotated[
        SemanticScholarClient, Depends(Provide[Container.semantic_scholar_client])
    ],
    llm_client: Annotated[
        LLMFacadeClient, Depends(Provide[Container.llm_facade_client])
    ],
) -> CreateHypothesisResponseBody:
    result = await CreateHypothesisSubgraph(
        qdrant_client=qdrant_client,
        arxiv_client=arxiv_client,
        ss_client=ss_client,
        llm_client=llm_client,
        refinement_rounds=0,
    ).arun(request)
    return CreateHypothesisResponseBody(
        research_session=result["research_session"],
        evaluated_hypothesis_history=result["evaluated_hypothesis_history"],
    )


@router.get("/method", response_model=CreateMethodResponseBody)
@inject
async def create_method(
    request: CreateMethodRequestBody,
    llm_client: Annotated[
        LLMFacadeClient, Depends(Provide[Container.llm_facade_client])
    ],
) -> CreateMethodResponseBody:
    result = await CreateMethodSubgraph(
        llm_client=llm_client,
    ).arun(request)
    return CreateMethodResponseBody(
        research_session=result["research_session"],
    )


@router.get("/experimental_design", response_model=CreateExperimentalDesignResponseBody)
@inject
async def create_experimental_design(
    request: CreateExperimentalDesignRequestBody,
    llm_client: Annotated[
        LLMFacadeClient, Depends(Provide[Container.llm_facade_client])
    ],
) -> CreateExperimentalDesignResponseBody:
    result = await CreateExperimentalDesignSubgraph(
        llm_client=llm_client,
    ).arun(request)
    return CreateExperimentalDesignResponseBody(
        research_session=result["research_session"],
    )
