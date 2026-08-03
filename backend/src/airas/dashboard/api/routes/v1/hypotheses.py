from typing import Annotated

from fastapi import APIRouter, Depends

from airas.dashboard.api.dependencies import get_litellm_client
from airas.dashboard.api.schemas.hypotheses import (
    GenerateHypothesisSubgraphV0RequestBody,
    GenerateHypothesisSubgraphV0ResponseBody,
)
from airas.infra.litellm_client import LiteLLMClient
from airas.usecases.generators.generate_hypothesis_subgraph.generate_hypothesis_subgraph_v0 import (
    GenerateHypothesisSubgraphV0,
)

router = APIRouter(prefix="/hypotheses", tags=["hypotheses"])


@router.post("/generations", response_model=GenerateHypothesisSubgraphV0ResponseBody)
async def generate_hypotheses(
    request: GenerateHypothesisSubgraphV0RequestBody,
    litellm_client: Annotated[LiteLLMClient, Depends(get_litellm_client)],
) -> GenerateHypothesisSubgraphV0ResponseBody:
    result = (
        await GenerateHypothesisSubgraphV0(
            litellm_client=litellm_client,
            refinement_rounds=request.refinement_rounds,
            llm_mapping=request.llm_mapping,
        )
        .build_graph()
        .ainvoke(request)
    )
    return GenerateHypothesisSubgraphV0ResponseBody(
        research_hypothesis=result["research_hypothesis"],
        execution_time=result["execution_time"],
    )
