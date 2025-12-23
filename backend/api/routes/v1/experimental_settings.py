from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from langfuse import observe

from api.schemas.experimental_settings import (
    GenerateExperimentalDesignSubgraphRequestBody,
    GenerateExperimentalDesignSubgraphResponseBody,
)
from src.airas.core.container import Container
from src.airas.features.generators.generate_experimental_design_subgraph.generate_experimental_design_subgraph import (
    GenerateExperimentalDesignSubgraph,
)
from src.airas.services.api_client.langchain_client import LangChainClient
from src.airas.services.api_client.langfuse_client import LangfuseClient

router = APIRouter(prefix="/experimental_settings", tags=["experimental_settings"])


@router.post(
    "/generations", response_model=GenerateExperimentalDesignSubgraphResponseBody
)
@inject
@observe()
async def generate_experimental_design(
    request: GenerateExperimentalDesignSubgraphRequestBody,
    langchain_client: Annotated[
        LangChainClient, Depends(Provide[Container.langchain_client])
    ],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> GenerateExperimentalDesignSubgraphResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await GenerateExperimentalDesignSubgraph(
            langchain_client=langchain_client,
            runner_config=request.runner_config,
            num_models_to_use=request.num_models_to_use,
            num_datasets_to_use=request.num_datasets_to_use,
            num_comparative_methods=request.num_comparative_methods,
            llm_mapping=request.llm_mapping,
        )
        .build_graph()
        .ainvoke(request, config=config)
    )
    return GenerateExperimentalDesignSubgraphResponseBody(
        experimental_design=result["experimental_design"],
        execution_time=result["execution_time"],
    )
