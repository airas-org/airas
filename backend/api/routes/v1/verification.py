from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from langfuse import observe

from airas.container import Container
from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient
from airas.infra.langfuse_client import LangfuseClient
from airas.infra.litellm_client import LiteLLMClient
from airas.usecases.assisted_research.generate_experiment_code_subgraph.generate_experiment_code_subgraph import (
    GenerateExperimentCodeSubgraph,
)
from airas.usecases.assisted_research.generate_verification_method_subgraph.generate_verification_method_subgraph import (
    GenerateVerificationMethodSubgraph,
)
from airas.usecases.assisted_research.propose_verification_policy_subgraph.propose_verification_policy_subgraph import (
    ProposeVerificationPolicySubgraph,
)
from api.ee.auth.dependencies import get_github_client
from api.schemas.verification import (
    ExperimentCodeStatusResponseBody,
    GenerateExperimentCodeRequestBody,
    GenerateExperimentCodeResponseBody,
    GenerateMethodRequestBody,
    GenerateMethodResponseBody,
    ProposedMethodSchema,
    ProposePoliciesRequestBody,
    ProposePoliciesResponseBody,
)

router = APIRouter(prefix="/verification", tags=["verification"])


@router.post("/propose-policies", response_model=ProposePoliciesResponseBody)
@inject
@observe(capture_input=False)
async def propose_policies(
    request: ProposePoliciesRequestBody,
    litellm_client: Annotated[
        LiteLLMClient, Depends(Provide[Container.litellm_client])
    ],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> ProposePoliciesResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = await (
        ProposeVerificationPolicySubgraph(litellm_client=litellm_client)
        .build_graph()
        .ainvoke({"user_query": request.user_query}, config=config)
    )

    if not result.get("feasible", True):
        return ProposePoliciesResponseBody(
            feasible=False,
            infeasible_reason=result.get("feasibility_reason"),
            proposed_methods=[],
        )

    proposed_methods = [
        ProposedMethodSchema(
            id=m["id"],
            title=m["title"],
            what_to_verify=m["what_to_verify"],
            method=m["method"],
            pros=m["pros"],
            cons=m["cons"],
        )
        for m in result.get("proposed_methods", [])
    ]
    return ProposePoliciesResponseBody(
        feasible=True,
        infeasible_reason=None,
        proposed_methods=proposed_methods,
    )


@router.post("/generate-method", response_model=GenerateMethodResponseBody)
@inject
@observe(capture_input=False)
async def generate_method(
    request: GenerateMethodRequestBody,
    litellm_client: Annotated[
        LiteLLMClient, Depends(Provide[Container.litellm_client])
    ],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> GenerateMethodResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = await (
        GenerateVerificationMethodSubgraph(litellm_client=litellm_client)
        .build_graph()
        .ainvoke(
            {
                "user_query": request.user_query,
                "selected_policy_title": request.selected_policy.title,
                "selected_policy_what_to_verify": request.selected_policy.what_to_verify,
                "selected_policy_method": request.selected_policy.method,
            },
            config=config,
        )
    )

    return GenerateMethodResponseBody(
        what_to_verify=result["what_to_verify"],
        experiment_settings=result["experiment_settings"],
        steps=result["steps"],
    )


@router.post(
    "/generate-experiment-code", response_model=GenerateExperimentCodeResponseBody
)
@inject
@observe(capture_input=False)
async def generate_experiment_code(
    request: GenerateExperimentCodeRequestBody,
    github_client: Annotated[GithubClient, Depends(get_github_client)],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
) -> GenerateExperimentCodeResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    github_config = GitHubConfig(
        github_owner=request.github_owner,
        repository_name=request.repository_name,
        branch_name=request.branch_name,
    )

    result = await (
        GenerateExperimentCodeSubgraph(github_client=github_client)
        .build_graph()
        .ainvoke(
            {
                "user_query": request.user_query,
                "what_to_verify": request.what_to_verify,
                "experiment_settings": request.experiment_settings,
                "steps": request.steps,
                "modification_notes": request.modification_notes,
                "repository_name": request.repository_name,
                "github_config": github_config,
                "github_actions_agent": request.github_actions_agent,
            },
            config=config,
        )
    )

    github_url = (
        f"https://github.com/{request.github_owner}/{request.repository_name}"
        if result.get("dispatched")
        else None
    )

    return GenerateExperimentCodeResponseBody(
        dispatched=result.get("dispatched", False),
        workflow_run_id=result.get("workflow_run_id"),
        github_url=github_url,
        execution_time=result.get("execution_time", {}),
    )


@router.get(
    "/experiment-code-status/{github_owner}/{repository_name}/{workflow_run_id}",
    response_model=ExperimentCodeStatusResponseBody,
)
@inject
@observe()
async def get_experiment_code_status(
    github_owner: str,
    repository_name: str,
    workflow_run_id: int,
    github_client: Annotated[GithubClient, Depends(get_github_client)],
) -> ExperimentCodeStatusResponseBody:
    result = await github_client.aget_workflow_run(
        github_owner=github_owner,
        repository_name=repository_name,
        workflow_run_id=workflow_run_id,
    )
    if result is None:
        return ExperimentCodeStatusResponseBody(status="unknown", conclusion=None)
    return ExperimentCodeStatusResponseBody(
        status=result.get("status", "unknown"),
        conclusion=result.get("conclusion"),
    )
