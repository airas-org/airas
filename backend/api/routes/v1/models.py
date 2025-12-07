from fastapi import APIRouter

from airas.features.retrieve.retrieve_models_subgraph.retrieve_models_subgraph import (
    RetrieveModelsSubgraph,
)
from api.schemas.models import (
    RetrieveModelsSubgraphRequestBody,
    RetrieveModelsSubgraphResponseBody,
)

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=RetrieveModelsSubgraphResponseBody)
async def retrieve_models(
    request: RetrieveModelsSubgraphRequestBody,
) -> RetrieveModelsSubgraphResponseBody:
    result = await RetrieveModelsSubgraph().build_graph().ainvoke(request)
    return RetrieveModelsSubgraphResponseBody(
        models_dict=result["models_dict"],
        execution_time=result["execution_time"],
    )
