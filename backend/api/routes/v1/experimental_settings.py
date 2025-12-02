from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from api.schemas.experimental_settings import (
    GenerateExperimentalDesignSubgraphRequestBody,
    GenerateExperimentalDesignSubgraphResponseBody,
)
from src.airas.core.container import Container
from src.airas.features.generators.generate_experimental_design_subgraph.generate_experimental_design_subgraph import (
    GenerateExperimentalDesignSubgraph,
)
from src.airas.services.api_client.langchain_client import LangChainClient

router = APIRouter(prefix="/experimental_settings", tags=["hypotheses"])


@router.post(
    "/generations", response_model=GenerateExperimentalDesignSubgraphResponseBody
)
@inject
async def generate_hypotheses(
    request: GenerateExperimentalDesignSubgraphRequestBody,
    langchain_client: Annotated[
        LangChainClient, Depends(Provide[Container.langchain_client])
    ],
) -> GenerateExperimentalDesignSubgraphResponseBody:
    result = (
        await GenerateExperimentalDesignSubgraph(
            langchain_client=langchain_client,
            runner_config=request.runner_config,
            num_models_to_use=request.num_models_to_use,
            num_datasets_to_use=request.num_datasets_to_use,
            num_comparative_methods=request.num_comparative_methods,
        )
        .build_graph()
        .ainvoke(request)
    )
    return GenerateExperimentalDesignSubgraphResponseBody(
        experimental_design=result["experimental_design"],
        execution_time=result["execution_time"],
    )
