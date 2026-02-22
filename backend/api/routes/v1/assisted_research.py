from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Closing, Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Request

from airas.container import Container
from airas.usecases.assisted_research.assisted_research_link_service import (
    AssistedResearchLinkService,
    DuplicateAssistedResearchLinkError,
)
from airas.usecases.assisted_research.assisted_research_session_service import (
    AssistedResearchSessionService,
)
from airas.usecases.assisted_research.assisted_research_step_service import (
    AssistedResearchStepService,
)
from api.ee.auth.dependencies import get_current_user_id
from api.schemas.assisted_research import (
    AssistedResearchLinkCreateRequest,
    AssistedResearchLinkListResponse,
    AssistedResearchLinkResponse,
    AssistedResearchSessionCreateRequest,
    AssistedResearchSessionResponse,
    AssistedResearchStepCreateRequest,
    AssistedResearchStepResponse,
)

router = APIRouter(prefix="/assisted_research", tags=["assisted_research"])


# session endpoints
@router.post("/session", response_model=AssistedResearchSessionResponse)
@inject
def create_session(
    request: AssistedResearchSessionCreateRequest,
    fastapi_request: Request,
    session_service: Annotated[
        AssistedResearchSessionService,
        Depends(Closing[Provide[Container.assisted_research_session_service]]),
    ],
) -> AssistedResearchSessionResponse:
    current_user_id = get_current_user_id(fastapi_request)
    session = session_service.create(title=request.title, created_by=current_user_id)
    return AssistedResearchSessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        created_by=session.created_by,
        active_head_step_id=session.active_head_step_id,
    )


@router.get("/session/{session_id}", response_model=AssistedResearchSessionResponse)
@inject
def get_session(
    session_id: UUID,
    session_service: Annotated[
        AssistedResearchSessionService,
        Depends(Closing[Provide[Container.assisted_research_session_service]]),
    ],
) -> AssistedResearchSessionResponse:
    session = session_service.get(session_id)
    return AssistedResearchSessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        created_by=session.created_by,
        active_head_step_id=session.active_head_step_id,
    )


# step endpoints
@router.post("/step", response_model=AssistedResearchStepResponse)
@inject
def create_step(
    request: AssistedResearchStepCreateRequest,
    fastapi_request: Request,
    step_service: Annotated[
        AssistedResearchStepService,
        Depends(Closing[Provide[Container.assisted_research_step_service]]),
    ],
) -> AssistedResearchStepResponse:
    current_user_id = get_current_user_id(fastapi_request)
    step = step_service.create(
        session_id=request.session_id,
        created_by=current_user_id,
        status=request.status,
        step_type=request.step_type,
        error_message=request.error_message,
        result=request.result,
        schema_version=request.schema_version,
    )
    return AssistedResearchStepResponse(
        id=step.id,
        session_id=step.session_id,
        created_by=step.created_by,
        created_at=step.created_at,
        status=step.status,
        step_type=step.step_type,
        error_message=step.error_message,
        result=step.result,
        schema_version=step.schema_version,
    )


@router.get("/step/{step_id}", response_model=AssistedResearchStepResponse)
@inject
def get_step(
    step_id: UUID,
    step_service: Annotated[
        AssistedResearchStepService,
        Depends(Closing[Provide[Container.assisted_research_step_service]]),
    ],
) -> AssistedResearchStepResponse:
    try:
        step = step_service.get(step_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AssistedResearchStepResponse(
        id=step.id,
        session_id=step.session_id,
        created_by=step.created_by,
        created_at=step.created_at,
        status=step.status,
        step_type=step.step_type,
        error_message=step.error_message,
        result=step.result,
        schema_version=step.schema_version,
    )


# link endpoints
@router.post("/link", response_model=AssistedResearchLinkResponse)
@inject
def create_link(
    request: AssistedResearchLinkCreateRequest,
    link_service: Annotated[
        AssistedResearchLinkService,
        Depends(Closing[Provide[Container.assisted_research_link_service]]),
    ],
) -> AssistedResearchLinkResponse:
    try:
        link = link_service.create(
            from_step_id=request.from_step_id,
            to_step_id=request.to_step_id,
        )
    except DuplicateAssistedResearchLinkError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return AssistedResearchLinkResponse(
        from_step_id=link.from_step_id,
        to_step_id=link.to_step_id,
    )


@router.get("/link/{from_step_id}", response_model=AssistedResearchLinkListResponse)
@inject
def get_link(
    from_step_id: UUID,
    link_service: Annotated[
        AssistedResearchLinkService,
        Depends(Closing[Provide[Container.assisted_research_link_service]]),
    ],
) -> AssistedResearchLinkListResponse:
    links = link_service.get_list(from_step_id)
    return AssistedResearchLinkListResponse(
        links=[
            AssistedResearchLinkResponse(
                from_step_id=link.from_step_id,
                to_step_id=link.to_step_id,
            )
            for link in links
        ]
    )
