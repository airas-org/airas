from fastapi import APIRouter

from airas.features.retrieve.retrieve_datasets_subgraph.retrieve_datasets_subgraph import (
    RetrieveDatasetsSubgraph,
)
from api.schemas.datasets import (
    RetrieveDatasetsSubgraphRequestBody,
    RetrieveDatasetsSubgraphResponseBody,
)

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", response_model=RetrieveDatasetsSubgraphResponseBody)
async def retrieve_datasets(
    request: RetrieveDatasetsSubgraphRequestBody,
) -> RetrieveDatasetsSubgraphResponseBody:
    result = await RetrieveDatasetsSubgraph().build_graph().ainvoke(request)
    return RetrieveDatasetsSubgraphResponseBody(
        datasets_dict=result["datasets_dict"],
        execution_time=result["execution_time"],
    )
