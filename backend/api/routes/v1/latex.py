from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from langfuse import observe

from airas.container import Container
from airas.infra.github_client import GithubClient
from airas.infra.langchain_client import LangChainClient
from airas.infra.langfuse_client import LangfuseClient
from airas.usecases.publication.compile_latex_subgraph.compile_latex_subgraph import (
    CompileLatexSubgraph,
)
from airas.usecases.publication.generate_latex_subgraph.generate_latex_subgraph import (
    GenerateLatexSubgraph,
)
from airas.usecases.publication.push_latex_subgraph.push_latex_subgraph import (
    PushLatexSubgraph,
)
from api.dependencies.github import get_user_github_client
from api.schemas.latex import (
    CompileLatexSubgraphRequestBody,
    CompileLatexSubgraphResponseBody,
    GenerateLatexSubgraphRequestBody,
    GenerateLatexSubgraphResponseBody,
    PushLatexSubgraphRequestBody,
    PushLatexSubgraphResponseBody,
)

router = APIRouter(prefix="/latex", tags=["latex"])


@router.post("/generations", response_model=GenerateLatexSubgraphResponseBody)
@inject
@observe()
async def generate_latex(
    request: GenerateLatexSubgraphRequestBody,
    langchain_client: Annotated[
        LangChainClient, Depends(Provide[Container.langchain_client])
    ],
    github_client: Annotated[GithubClient, Depends(get_user_github_client)],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> GenerateLatexSubgraphResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await GenerateLatexSubgraph(
            langchain_client=langchain_client,
            github_client=github_client,
            latex_template_name=request.latex_template_name,
            llm_mapping=request.llm_mapping,
        )
        .build_graph()
        .ainvoke(request, config=config)
    )
    return GenerateLatexSubgraphResponseBody(
        latex_text=result["latex_text"],
        execution_time=result["execution_time"],
    )


@router.post("/push", response_model=PushLatexSubgraphResponseBody)
@inject
@observe()
async def push_latex(
    request: PushLatexSubgraphRequestBody,
    github_client: Annotated[GithubClient, Depends(get_user_github_client)],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> PushLatexSubgraphResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await PushLatexSubgraph(
            github_client=github_client,
            latex_template_name=request.latex_template_name,
        )
        .build_graph()
        .ainvoke(request, config=config)
    )
    return PushLatexSubgraphResponseBody(
        is_upload_successful=result["is_upload_successful"],
        is_images_prepared=result["is_images_prepared"],
        execution_time=result["execution_time"],
    )


@router.post("/compile", response_model=CompileLatexSubgraphResponseBody)
@inject
@observe()
async def compile_latex(
    request: CompileLatexSubgraphRequestBody,
    github_client: Annotated[GithubClient, Depends(get_user_github_client)],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> CompileLatexSubgraphResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = (
        await CompileLatexSubgraph(
            github_client=github_client,
            latex_template_name=request.latex_template_name,
            github_actions_agent=request.github_actions_agent,
            llm_mapping=request.llm_mapping,
        )
        .build_graph()
        .ainvoke(request, config=config)
    )
    return CompileLatexSubgraphResponseBody(
        compile_latex_dispatched=result["compile_latex_dispatched"],
        paper_url=result["paper_url"],
        execution_time=result["execution_time"],
    )
