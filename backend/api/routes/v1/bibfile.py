from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from langfuse import observe

from airas.core.container import Container
from airas.features.writers.generate_bibfile_subgraph.generate_bibfile_subgraph import (
    GenerateBibfileSubgraph,
)
from airas.services.api_client.langfuse_client import LangfuseClient
from api.schemas.bibfile import (
    GenerateBibfileSubgraphRequestBody,
    GenerateBibfileSubgraphResponseBody,
)

router = APIRouter(prefix="/bibfile", tags=["bibfile"])


@router.post("/generations", response_model=GenerateBibfileSubgraphResponseBody)
@inject
@observe()
async def generate_bibfile(
    request: GenerateBibfileSubgraphRequestBody,
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> GenerateBibfileSubgraphResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await GenerateBibfileSubgraph().build_graph().ainvoke(request, config=config)
    )
    return GenerateBibfileSubgraphResponseBody(
        references_bib=result["references_bib"],
        execution_time=result["execution_time"],
    )
