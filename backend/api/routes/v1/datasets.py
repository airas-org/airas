from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from langfuse import observe

from airas.features.retrieve.retrieve_datasets_subgraph.retrieve_datasets_subgraph import (
    RetrieveDatasetsSubgraph,
)
from api.schemas.datasets import (
    RetrieveDatasetsSubgraphRequestBody,
    RetrieveDatasetsSubgraphResponseBody,
)
from src.airas.core.container import Container
from src.airas.services.api_client.langfuse_client import LangfuseClient

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", response_model=RetrieveDatasetsSubgraphResponseBody)
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
