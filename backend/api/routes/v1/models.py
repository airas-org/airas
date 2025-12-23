from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from langfuse import observe

from airas.features.retrieve.retrieve_models_subgraph.retrieve_models_subgraph import (
    RetrieveModelsSubgraph,
)
from api.schemas.models import (
    RetrieveModelsSubgraphRequestBody,
    RetrieveModelsSubgraphResponseBody,
)
from src.airas.core.container import Container
from src.airas.services.api_client.langfuse_client import LangfuseClient

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=RetrieveModelsSubgraphResponseBody)
@inject
@observe()
async def retrieve_models(
    request: RetrieveModelsSubgraphRequestBody,
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> RetrieveModelsSubgraphResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await RetrieveModelsSubgraph().build_graph().ainvoke(request, config=config)
    )
    return RetrieveModelsSubgraphResponseBody(
        models_dict=result["models_dict"],
        execution_time=result["execution_time"],
    )
