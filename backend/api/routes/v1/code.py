from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from airas.features.generators.generate_code_subgraph.generate_code_subgraph import (
    GenerateCodeSubgraph,
)
from api.schemas.code import (
    GenerateCodeSubgraphRequestBody,
    GenerateCodeSubgraphResponseBody,
    PushCodeSubgraphRequestBody,
    PushCodeSubgraphResponseBody,
)
from src.airas.core.container import Container
from src.airas.features.github.push_code_subgraph.push_code_subgraph import (
    PushCodeSubgraph,
)
from src.airas.services.api_client.github_client import GithubClient
from src.airas.services.api_client.langchain_client import LangChainClient

router = APIRouter(prefix="/code", tags=["code"])

MAX_CODE_VALIDATIONS = 10


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
            max_code_validations=MAX_CODE_VALIDATIONS,
        )
        .build_graph()
        .ainvoke(request)
    )
    return GenerateCodeSubgraphResponseBody(
        experiment_code=result["experiment_code"],
        execution_time=result["execution_time"],
    )


@router.post("/push", response_model=PushCodeSubgraphResponseBody)
@inject
async def push_code(
    request: PushCodeSubgraphRequestBody,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
) -> PushCodeSubgraphResponseBody:
    result = (
        await PushCodeSubgraph(
            github_client=github_client,
            secret_names=None,
        )
        .build_graph()
        .ainvoke(request)
    )
    return PushCodeSubgraphResponseBody(
        files_pushed=result["files_pushed"],
        execution_time=result["execution_time"],
    )
