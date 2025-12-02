from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from airas.features.generators.generate_code_subgraph.generate_code_subgraph import (
    GenerateCodeSubgraph,
)
from api.schemas.code import (
    GenerateCodeSubgraphRequestBody,
    GenerateCodeSubgraphResponseBody,
)
from src.airas.core.container import Container
from src.airas.services.api_client.langchain_client import LangChainClient

router = APIRouter(prefix="/code", tags=["code"])


@router.post("/generations", response_model=GenerateCodeSubgraphResponseBody)
@inject
async def generate_code(
    request: GenerateCodeSubgraphRequestBody,
    langchain_client: Annotated[
        LangChainClient, Depends(Provide[Container.langchain_client])
    ],
) -> GenerateCodeSubgraphResponseBody:
    result = (
        await GenerateCodeSubgraph(
            wandb_config=request.wandb_config,
            langchain_client=langchain_client,
            max_code_validations=request.max_code_validations,
        )
        .build_graph()
        .ainvoke(request)
    )
    return GenerateCodeSubgraphResponseBody(
        experiment_code=result["experiment_code"],
        execution_time=result["execution_time"],
    )
