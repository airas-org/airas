from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from langfuse import observe

from airas.container import Container
from airas.infra.langfuse_client import LangfuseClient
from airas.usecases.retrieve.retrieve_datasets_subgraph.retrieve_datasets_subgraph import (
    RetrieveDatasetsSubgraph,
)
from api.schemas.datasets import (
    RetrieveDatasetsSubgraphRequestBody,
    RetrieveDatasetsSubgraphResponseBody,
)

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=RetrieveDatasetsSubgraphResponseBody)
@inject
@observe()
async def retrieve_datasets(
    request: RetrieveDatasetsSubgraphRequestBody,
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> RetrieveDatasetsSubgraphResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await RetrieveDatasetsSubgraph().build_graph().ainvoke(request, config=config)
    )
    return RetrieveDatasetsSubgraphResponseBody(
        datasets_dict=result["datasets_dict"],
        execution_time=result["execution_time"],
    )
