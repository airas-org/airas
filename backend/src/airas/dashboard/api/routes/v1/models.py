from fastapi import APIRouter

from airas.dashboard.api.schemas.models import (
    RetrieveModelsSubgraphRequestBody,
    RetrieveModelsSubgraphResponseBody,
)
from airas.usecases.retrieve.retrieve_models_subgraph.retrieve_models_subgraph import (
    RetrieveModelsSubgraph,
)

router = APIRouter(prefix="/models", tags=["models"])


@router.post("", response_model=RetrieveModelsSubgraphResponseBody)
async def retrieve_models(
    request: RetrieveModelsSubgraphRequestBody,
) -> RetrieveModelsSubgraphResponseBody:
    result = await RetrieveModelsSubgraph().build_graph().ainvoke(request)
    return RetrieveModelsSubgraphResponseBody(
        models_dict=result["models_dict"],
        execution_time=result["execution_time"],
    )
