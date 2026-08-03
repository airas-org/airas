from fastapi import APIRouter

from airas.dashboard.api.schemas.datasets import (
    RetrieveDatasetsSubgraphRequestBody,
    RetrieveDatasetsSubgraphResponseBody,
)
from airas.usecases.retrieve.retrieve_datasets_subgraph.retrieve_datasets_subgraph import (
    RetrieveDatasetsSubgraph,
)

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=RetrieveDatasetsSubgraphResponseBody)
async def retrieve_datasets(
    request: RetrieveDatasetsSubgraphRequestBody,
) -> RetrieveDatasetsSubgraphResponseBody:
    result = await RetrieveDatasetsSubgraph().build_graph().ainvoke(request)
    return RetrieveDatasetsSubgraphResponseBody(
        datasets_dict=result["datasets_dict"],
        execution_time=result["execution_time"],
    )
