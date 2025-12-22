from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from airas.features.publication.compile_latex_subgraph.compile_latex_subgraph import (
    CompileLatexSubgraph,
)
from airas.features.publication.generate_latex_subgraph.generate_latex_subgraph import (
    GenerateLatexSubgraph,
)
from airas.features.publication.push_latex_subgraph.push_latex_subgraph import (
    PushLatexSubgraph,
)
from airas.services.api_client.github_client import GithubClient
from airas.services.api_client.langchain_client import LangChainClient
from api.schemas.latex import (
    CompileLatexSubgraphRequestBody,
    CompileLatexSubgraphResponseBody,
    GenerateLatexSubgraphRequestBody,
    GenerateLatexSubgraphResponseBody,
    PushLatexSubgraphRequestBody,
    PushLatexSubgraphResponseBody,
)
from src.airas.core.container import Container

router = APIRouter(prefix="/latex", tags=["latex"])


@router.post("/generations", response_model=GenerateLatexSubgraphResponseBody)
@inject
async def generate_latex(
    request: GenerateLatexSubgraphRequestBody,
    langchain_client: Annotated[
        LangChainClient, Depends(Provide[Container.langchain_client])
    ],
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
) -> GenerateLatexSubgraphResponseBody:
    result = (
        await GenerateLatexSubgraph(
            langchain_client=langchain_client,
            github_client=github_client,
            latex_template_name=request.latex_template_name,
            llm_mapping=request.llm_mapping,
        )
        .build_graph()
        .ainvoke(request)
    )
    return GenerateLatexSubgraphResponseBody(
        latex_text=result["latex_text"],
        execution_time=result["execution_time"],
    )


@router.post("/push", response_model=PushLatexSubgraphResponseBody)
@inject
async def push_latex(
    request: PushLatexSubgraphRequestBody,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
) -> PushLatexSubgraphResponseBody:
    result = (
        await PushLatexSubgraph(
            github_client=github_client,
            latex_template_name=request.latex_template_name,
        )
        .build_graph()
        .ainvoke(request)
    )
    return PushLatexSubgraphResponseBody(
        is_upload_successful=result["is_upload_successful"],
        is_images_prepared=result["is_images_prepared"],
        execution_time=result["execution_time"],
    )


@router.post("/compile", response_model=CompileLatexSubgraphResponseBody)
@inject
async def compile_latex(
    request: CompileLatexSubgraphRequestBody,
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
) -> CompileLatexSubgraphResponseBody:
    result = (
        await CompileLatexSubgraph(
            github_client=github_client,
            latex_template_name=request.latex_template_name,
        )
        .build_graph()
        .ainvoke(request)
    )
    return CompileLatexSubgraphResponseBody(
        compile_latex_dispatched=result["compile_latex_dispatched"],
        paper_url=result["paper_url"],
        execution_time=result["execution_time"],
    )
