from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from langfuse import observe

from api.schemas.hypotheses import (
    GenerateHypothesisSubgraphV0RequestBody,
    GenerateHypothesisSubgraphV0ResponseBody,
)
from src.airas.core.container import Container
from src.airas.features.generators.generate_hypothesis_subgraph.generate_hypothesis_subgraph_v0 import (
    GenerateHypothesisSubgraphV0,
)
from src.airas.services.api_client.langchain_client import LangChainClient
from src.airas.services.api_client.langfuse_client import LangfuseClient

router = APIRouter(prefix="/hypotheses", tags=["hypotheses"])


@router.post("/generations", response_model=GenerateHypothesisSubgraphV0ResponseBody)
@inject
@observe()
async def generate_hypotheses(
    request: GenerateHypothesisSubgraphV0RequestBody,
    langchain_client: Annotated[
        LangChainClient, Depends(Provide[Container.langchain_client])
    ],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> GenerateHypothesisSubgraphV0ResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await GenerateHypothesisSubgraphV0(
            langchain_client=langchain_client,
            refinement_rounds=request.refinement_rounds,
            llm_mapping=request.llm_mapping,
        )
        .build_graph()
        .ainvoke(request, config=config)
    )
    return GenerateHypothesisSubgraphV0ResponseBody(
        research_hypothesis=result["research_hypothesis"],
        execution_time=result["execution_time"],
    )
