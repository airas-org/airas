from typing import Annotated

from dependency_injector.wiring import Provide
from fastapi import APIRouter, Depends

from airas.features.create.create_hypothesis_subgraph.create_hypothesis_subgraph import (
    CreateHypothesisSubgraph,
)
from airas.services.api_client.arxiv_client import ArxivClient
from airas.services.api_client.llm_client.llm_facade_client import LLMFacadeClient
from airas.services.api_client.qdrant_client import QdrantClient
from airas.services.api_client.semantic_scholar_client import SemanticScholarClient
from api.schemas.create import CreateHypothesisRequestBody, CreateHypothesisResponseBody
from src.airas.services.api_client.api_clients_container import (
    AsyncContainer,
    SyncContainer,
)

router = APIRouter(prefix="/create", tags=["papers"])


@router.get("/hypothesis", response_model=CreateHypothesisResponseBody)
async def create_hypothesis(
    request: CreateHypothesisRequestBody,
    qdrant_client: Annotated[
        QdrantClient, Depends(Provide[SyncContainer.qdrant_client])
    ],
    arxiv_client: Annotated[ArxivClient, Depends(Provide[SyncContainer.arxiv_client])],
    ss_client: Annotated[
        SemanticScholarClient, Depends(Provide[SyncContainer.semantic_scholar_client])
    ],
    llm_client: Annotated[
        LLMFacadeClient, Depends(Provide[AsyncContainer.o3_2025_04_16])
    ],
    llm_embedding_client: Annotated[
        LLMFacadeClient, Depends(Provide[AsyncContainer.gemini_embedding_001])
    ],
) -> CreateHypothesisResponseBody:
    result = await CreateHypothesisSubgraph(
        qdrant_client=qdrant_client,
        arxiv_client=arxiv_client,
        ss_client=ss_client,
        llm_client=llm_client,
        llm_embedding_client=llm_embedding_client,
        refinement_rounds=0,
    ).arun(request)
    return CreateHypothesisResponseBody(
        research_session=result["research_session"],
        evaluated_hypothesis_history=result["evaluated_hypothesis_history"],
    )
