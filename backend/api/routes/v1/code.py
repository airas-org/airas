from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from langfuse import observe

from airas.container import Container
from airas.infra.github_client import GithubClient
from airas.infra.langchain_client import LangChainClient
from airas.infra.langfuse_client import LangfuseClient
from airas.usecases.generators.generate_code_subgraph.generate_code_subgraph import (
    GenerateCodeSubgraph,
)
from airas.usecases.github.push_code_subgraph.push_code_subgraph import (
    PushCodeSubgraph,
)
from api.schemas.code import (
    GenerateCodeSubgraphRequestBody,
    GenerateCodeSubgraphResponseBody,
    PushCodeSubgraphRequestBody,
    PushCodeSubgraphResponseBody,
)

router = APIRouter(prefix="/code", tags=["code"])


@router.post("/generations", response_model=GenerateCodeSubgraphResponseBody)
@inject
@observe()
async def generate_code(
    request: GenerateCodeSubgraphRequestBody,
    langchain_client: Annotated[
        LangChainClient, Depends(Provide[Container.langchain_client])
    ],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> GenerateCodeSubgraphResponseBody:
    config = {"recursion_limit": 100}
    if handler := langfuse_client.create_handler():
        config["callbacks"] = [handler]

    result = (
        await GenerateCodeSubgraph(
            wandb_config=request.wandb_config,
            langchain_client=langchain_client,
            max_code_validations=request.max_code_validations,
            llm_mapping=request.llm_mapping,
        )
        .build_graph()
        .ainvoke(request, config=config)
    )
    return GenerateCodeSubgraphResponseBody(
        experiment_code=result["experiment_code"],
        execution_time=result["execution_time"],
    )


@router.post("/push", response_model=PushCodeSubgraphResponseBody)
@inject
@observe()
async def push_code(
    request: PushCodeSubgraphRequestBody,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> PushCodeSubgraphResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await PushCodeSubgraph(
            github_client=github_client,
            secret_names=None,
        )
        .build_graph()
        .ainvoke(request, config=config)
    )
    return PushCodeSubgraphResponseBody(
        code_pushed=result["code_pushed"],
        execution_time=result["execution_time"],
    )
