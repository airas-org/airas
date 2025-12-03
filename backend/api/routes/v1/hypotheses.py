from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from api.schemas.hypotheses import (
    GenerateHypothesisSubgraphRequestBody,
    GenerateHypothesisSubgraphResponseBody,
)
from src.airas.core.container import Container
from src.airas.features.generators.generate_hypothesis_subgraph.generate_hypothesis_subgraph import (
    GenerateHypothesisSubgraph,
)
from src.airas.services.api_client.langchain_client import LangChainClient

router = APIRouter(prefix="/hypotheses", tags=["hypotheses"])


@router.post("/generations", response_model=GenerateHypothesisSubgraphResponseBody)
@inject
async def generate_hypotheses(
    request: GenerateHypothesisSubgraphRequestBody,
    langchain_client: Annotated[
        LangChainClient, Depends(Provide[Container.langchain_client])
    ],
) -> GenerateHypothesisSubgraphResponseBody:
    result = (
        await GenerateHypothesisSubgraph(
            langchain_client=langchain_client,
            refinement_rounds=request.refinement_rounds,
            num_retrieve_related_papers=0,  # Same behavior as v0 (no paper retrieval)
        )
        .build_graph()
        .ainvoke(request)
    )
    return GenerateHypothesisSubgraphResponseBody(
        research_hypothesis=result["research_hypothesis"],
        execution_time=result["execution_time"],
    )
