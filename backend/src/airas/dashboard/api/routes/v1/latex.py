from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse

from airas.core.types.github import GitHubConfig
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.dashboard.api.dependencies import (
    get_github_client,
    get_github_client_or_none,
    get_litellm_client,
)
from airas.dashboard.api.schemas.latex import (
    CompileLatexSubgraphRequestBody,
    CompileLatexSubgraphResponseBody,
    GenerateLatexSubgraphRequestBody,
    GenerateLatexSubgraphResponseBody,
    PushLatexSubgraphRequestBody,
    PushLatexSubgraphResponseBody,
)
from airas.infra.github_client import GithubClient
from airas.infra.litellm_client import LiteLLMClient
from airas.usecases.publication.compile_latex_subgraph.compile_latex_subgraph import (
    CompileLatexSubgraph,
)
from airas.usecases.publication.generate_latex_subgraph.generate_latex_subgraph import (
    GenerateLatexSubgraph,
)
from airas.usecases.publication.open_in_overleaf_subgraph.open_in_overleaf_subgraph import (
    OpenInOverleafSubgraph,
)
from airas.usecases.publication.push_latex_subgraph.push_latex_subgraph import (
    PushLatexSubgraph,
)

router = APIRouter(prefix="/latex", tags=["latex"])


@router.post("/generations", response_model=GenerateLatexSubgraphResponseBody)
async def generate_latex(
    request: GenerateLatexSubgraphRequestBody,
    litellm_client: Annotated[LiteLLMClient, Depends(get_litellm_client)],
    github_client: Annotated[GithubClient, Depends(get_github_client)],
) -> GenerateLatexSubgraphResponseBody:
    result = (
        await GenerateLatexSubgraph(
            litellm_client=litellm_client,
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


# NOTE: In the local-agent flow main.tex is pushed with git; this endpoint
# remains for the dashboard UI and E2E and is a removal candidate in the next
# major release (see issue #913).
@router.post("/push", response_model=PushLatexSubgraphResponseBody)
async def push_latex(
    request: PushLatexSubgraphRequestBody,
    github_client: Annotated[GithubClient, Depends(get_github_client)],
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
        execution_time=result["execution_time"],
    )


@router.get(
    "/overleaf",
    response_class=HTMLResponse,
    responses={
        404: {
            "description": "LaTeX project not found in the repository "
            "(push_latex has not been run)",
        }
    },
)
async def open_in_overleaf(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    github_client: Annotated[GithubClient | None, Depends(get_github_client_or_none)],
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
    local_path: str | None = None,
) -> HTMLResponse:
    """Serve a page that forwards the paper's LaTeX project to Overleaf.

    Opened in a browser (not called as a JSON API): the page carries the
    zipped LaTeX sources inline and immediately POSTs them to Overleaf,
    which creates a new project in the user's Overleaf account.

    With `local_path` (path to a local clone of the experiment repository)
    the project is read from the working tree on disk instead of GitHub,
    so unpushed changes and locally rendered figures are included — and no
    GitHub token is required.
    """
    if local_path is None and github_client is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GH_PERSONAL_ACCESS_TOKEN is not configured (required "
            "unless local_path is provided).",
        )
    try:
        result = (
            await OpenInOverleafSubgraph(
                github_client=github_client,
                latex_template_name=latex_template_name,
                local_repo_path=local_path,
            )
            .build_graph()
            .ainvoke(
                {
                    "github_config": GitHubConfig(
                        github_owner=github_owner,
                        repository_name=repository_name,
                        branch_name=branch_name,
                    )
                }
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return HTMLResponse(result["overleaf_html"])


@router.post("/compile", response_model=CompileLatexSubgraphResponseBody)
async def compile_latex(
    request: CompileLatexSubgraphRequestBody,
    github_client: Annotated[GithubClient, Depends(get_github_client)],
) -> CompileLatexSubgraphResponseBody:
    result = (
        await CompileLatexSubgraph(
            github_client=github_client,
            latex_template_name=request.latex_template_name,
            github_actions_agent=request.github_actions_agent,
            llm_mapping=request.llm_mapping,
        )
        .build_graph()
        .ainvoke(request)
    )
    return CompileLatexSubgraphResponseBody(
        compile_latex_dispatched=result["compile_latex_dispatched"],
        paper_url=result["paper_url"],
        execution_time=result["execution_time"],
    )
