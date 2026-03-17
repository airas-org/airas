from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Closing, Provide, inject
from fastapi import APIRouter, Depends, HTTPException
from langfuse import observe

from airas.container import Container
from airas.core.types.github import GitHubConfig
from airas.infra.db.models.verification import VerificationModel
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
from airas.usecases.verification.verification_service import VerificationService
from api.ee.auth.dependencies import (
    get_current_user_id,
    get_github_client,
    get_litellm_client,
)
from api.schemas.verification import (
    ExperimentCodeStatusResponseBody,
    GenerateExperimentCodeRequestBody,
    GenerateExperimentCodeResponseBody,
    GenerateMethodRequestBody,
    GenerateMethodResponseBody,
    ProposedMethodSchema,
    ProposePoliciesRequestBody,
    ProposePoliciesResponseBody,
    VerificationSessionCreateRequest,
    VerificationSessionListResponse,
    VerificationSessionResponse,
    VerificationSessionUpdateRequest,
)

router = APIRouter(prefix="/verification", tags=["verification"])


def _model_to_response(m: VerificationModel) -> VerificationSessionResponse:
    return VerificationSessionResponse(
        id=str(m.id),
        title=m.title,
        query=m.query,
        created_by=str(m.created_by),
        created_at=m.created_at.isoformat(),
        updated_at=m.updated_at.isoformat(),
        phase=m.phase,
        proposed_methods=m.proposed_methods,
        selected_method_id=m.selected_method_id,
        verification_method=m.verification_method,
        plan=m.plan,
        repository_name=m.repository_name,
        github_owner=m.github_owner,
        github_url=m.github_url,
        workflow_run_id=m.workflow_run_id,
        modification_notes=m.modification_notes,
        code_generation_status=m.code_generation_status,
        code_generation_conclusion=m.code_generation_conclusion,
        implementation=m.implementation,
        paper_draft=m.paper_draft,
    )


# --- Session CRUD endpoints ---


@router.post("/sessions", response_model=VerificationSessionResponse)
@inject
def create_session(
    request: VerificationSessionCreateRequest,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    verification_service: Annotated[
        VerificationService,
        Depends(Closing[Provide[Container.verification_service]]),
    ],
) -> VerificationSessionResponse:
    verification = verification_service.create(
        created_by=current_user_id, title=request.title
    )
    return _model_to_response(verification)


@router.get("/sessions", response_model=VerificationSessionListResponse)
@inject
def list_sessions(
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    verification_service: Annotated[
        VerificationService,
        Depends(Closing[Provide[Container.verification_service]]),
    ],
) -> VerificationSessionListResponse:
    verifications = verification_service.list_by_user(current_user_id)
    return VerificationSessionListResponse(
        sessions=[_model_to_response(v) for v in verifications]
    )


@router.get("/sessions/{verification_id}", response_model=VerificationSessionResponse)
@inject
def get_session(
    verification_id: UUID,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    verification_service: Annotated[
        VerificationService,
        Depends(Closing[Provide[Container.verification_service]]),
    ],
) -> VerificationSessionResponse:
    verification = verification_service.get(verification_id)
    if verification is None or verification.created_by != current_user_id:
        raise HTTPException(status_code=404, detail="Verification not found")
    return _model_to_response(verification)


@router.patch("/sessions/{verification_id}", response_model=VerificationSessionResponse)
@inject
def update_session(
    verification_id: UUID,
    request: VerificationSessionUpdateRequest,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    verification_service: Annotated[
        VerificationService,
        Depends(Closing[Provide[Container.verification_service]]),
    ],
) -> VerificationSessionResponse:
    existing = verification_service.get(verification_id)
    if existing is None or existing.created_by != current_user_id:
        raise HTTPException(status_code=404, detail="Verification not found")
    update_data = request.model_dump(exclude_unset=True)
    verification = verification_service.update(verification_id, **update_data)
    if verification is None:
        raise HTTPException(status_code=404, detail="Verification not found")
    return _model_to_response(verification)


@router.delete("/sessions/{verification_id}", status_code=204)
@inject
def delete_session(
    verification_id: UUID,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    verification_service: Annotated[
        VerificationService,
        Depends(Closing[Provide[Container.verification_service]]),
    ],
) -> None:
    verification = verification_service.get(verification_id)
    if verification is None or verification.created_by != current_user_id:
        raise HTTPException(status_code=404, detail="Verification not found")
    verification_service.delete(verification_id)


# --- Existing AI endpoints ---


@router.post("/propose-policies", response_model=ProposePoliciesResponseBody)
@inject
@observe(capture_input=False)
async def propose_policies(
    request: ProposePoliciesRequestBody,
    litellm_client: Annotated[LiteLLMClient, Depends(get_litellm_client)],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
    verification_service: Annotated[
        VerificationService,
        Depends(Closing[Provide[Container.verification_service]]),
    ],
) -> ProposePoliciesResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = await (
        ProposeVerificationPolicySubgraph(
            litellm_client=litellm_client, llm_mapping=request.llm_mapping
        )
        .build_graph()
        .ainvoke({"user_query": request.user_query}, config=config)
    )

    if not result.get("feasible", True):
        return ProposePoliciesResponseBody(
            feasible=False,
            infeasible_reason=result.get("infeasible_reason"),
            proposed_methods=[],
            execution_time=result.get("execution_time", {}),
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

    if request.verification_id is not None:
        verification_service.update(
            request.verification_id,
            query=request.user_query,
            phase="methods-proposed",
            proposed_methods=[m.model_dump() for m in proposed_methods],
        )

    return ProposePoliciesResponseBody(
        feasible=True,
        infeasible_reason=None,
        proposed_methods=proposed_methods,
        execution_time=result.get("execution_time", {}),
    )


@router.post("/generate-method", response_model=GenerateMethodResponseBody)
@inject
@observe(capture_input=False)
async def generate_method(
    request: GenerateMethodRequestBody,
    litellm_client: Annotated[LiteLLMClient, Depends(get_litellm_client)],
    langfuse_client: Annotated[
        LangfuseClient, Depends(Provide[Container.langfuse_client])
    ],
    verification_service: Annotated[
        VerificationService,
        Depends(Closing[Provide[Container.verification_service]]),
    ],
) -> GenerateMethodResponseBody:
    handler = langfuse_client.create_handler()
    config = {"callbacks": [handler]} if handler else {}

    result = await (
        GenerateVerificationMethodSubgraph(
            litellm_client=litellm_client, llm_mapping=request.llm_mapping
        )
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

    if request.verification_id is not None:
        verification_service.update(
            request.verification_id,
            selected_method_id=request.selected_policy.id,
            phase="method-generated",
            verification_method={
                "what_to_verify": result["what_to_verify"],
                "experiment_settings": result["experiment_settings"],
                "steps": result["steps"],
            },
        )

    return GenerateMethodResponseBody(
        what_to_verify=result["what_to_verify"],
        experiment_settings=result["experiment_settings"],
        steps=result["steps"],
        execution_time=result.get("execution_time", {}),
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
    verification_service: Annotated[
        VerificationService,
        Depends(Closing[Provide[Container.verification_service]]),
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
        GenerateExperimentCodeSubgraph(
            github_client=github_client, llm_mapping=request.llm_mapping
        )
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

    if request.verification_id is not None:
        update_kwargs: dict[str, object] = {
            "phase": "code-generated",
            "repository_name": request.repository_name,
            "github_owner": request.github_owner,
            "modification_notes": request.modification_notes,
        }
        if result.get("dispatched"):
            update_kwargs["github_url"] = github_url
            update_kwargs["workflow_run_id"] = result.get("workflow_run_id")
            update_kwargs["code_generation_status"] = "pending"
        verification_service.update(request.verification_id, **update_kwargs)

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
