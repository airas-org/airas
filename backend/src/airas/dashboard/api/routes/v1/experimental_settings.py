from typing import Annotated

from fastapi import APIRouter, Depends

from airas.dashboard.api.dependencies import get_litellm_client
from airas.dashboard.api.schemas.experimental_settings import (
    GenerateExperimentalDesignSubgraphRequestBody,
    GenerateExperimentalDesignSubgraphResponseBody,
    RefineExperimentalDesignSubgraphRequestBody,
    RefineExperimentalDesignSubgraphResponseBody,
)
from airas.infra.litellm_client import LiteLLMClient
from airas.usecases.generators.generate_experimental_design_subgraph.generate_experimental_design_subgraph import (
    GenerateExperimentalDesignSubgraph,
)
from airas.usecases.generators.refine_experimental_design_subgraph.refine_experimental_design_subgraph import (
    RefineExperimentalDesignSubgraph,
)

router = APIRouter(prefix="/experimental_settings", tags=["experimental_settings"])


@router.post(
    "/generations", response_model=GenerateExperimentalDesignSubgraphResponseBody
)
async def generate_experimental_design(
    request: GenerateExperimentalDesignSubgraphRequestBody,
    litellm_client: Annotated[LiteLLMClient, Depends(get_litellm_client)],
) -> GenerateExperimentalDesignSubgraphResponseBody:
    result = (
        await GenerateExperimentalDesignSubgraph(
            litellm_client=litellm_client,
            compute_environment=request.compute_environment,
            num_models_to_use=request.num_models_to_use,
            num_datasets_to_use=request.num_datasets_to_use,
            num_comparative_methods=request.num_comparative_methods,
            llm_mapping=request.llm_mapping,
        )
        .build_graph()
        .ainvoke(request)
    )
    return GenerateExperimentalDesignSubgraphResponseBody(
        experimental_design=result["experimental_design"],
        execution_time=result["execution_time"],
    )


@router.post(
    "/refinements", response_model=RefineExperimentalDesignSubgraphResponseBody
)
async def refine_experimental_design(
    request: RefineExperimentalDesignSubgraphRequestBody,
    litellm_client: Annotated[LiteLLMClient, Depends(get_litellm_client)],
) -> RefineExperimentalDesignSubgraphResponseBody:
    result = (
        await RefineExperimentalDesignSubgraph(
            litellm_client=litellm_client,
            compute_environment=request.compute_environment,
            num_models_to_use=request.num_models_to_use,
            num_datasets_to_use=request.num_datasets_to_use,
            num_comparative_methods=request.num_comparative_methods,
            llm_mapping=request.llm_mapping,
        )
        .build_graph()
        .ainvoke(request)
    )
    return RefineExperimentalDesignSubgraphResponseBody(
        experimental_design=result["experimental_design"],
        execution_time=result["execution_time"],
    )
