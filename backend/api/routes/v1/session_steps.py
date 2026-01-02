from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Closing, Provide, inject
from fastapi import APIRouter, Depends, HTTPException

from airas.container import Container
from airas.usecases.session_steps.service import SessionStepService
from api.schemas.session_steps import (
    SessionStepCreateRequest,
    SessionStepResponse,
)

router = APIRouter(prefix="/session-steps", tags=["session-steps"])


@router.post("", response_model=SessionStepResponse)
@inject
def create_session_step(
    request: SessionStepCreateRequest,
    svc: Annotated[
        SessionStepService, Depends(Closing[Provide[Container.session_step_service]])
    ],
) -> SessionStepResponse:
    step = svc.create(
        session_id=request.session_id,
        step_type=request.step_type,
        content=request.content,
        schema_version=request.schema_version,
        created_by=request.created_by,
        is_completed=request.is_completed,
    )
    return SessionStepResponse(
        id=step.id,
        session_id=step.session_id,
        step_type=step.step_type,
        content=step.content,
        schema_version=step.schema_version,
        created_by=step.created_by,
        created_at=step.created_at,
        is_completed=step.is_completed,
    )


@router.get("/{step_id}", response_model=SessionStepResponse)
@inject
def get_session_step(
    step_id: UUID,
    svc: Annotated[
        SessionStepService, Depends(Closing[Provide[Container.session_step_service]])
    ],
) -> SessionStepResponse:
    try:
        step = svc.get(step_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SessionStepResponse(
        id=step.id,
        session_id=step.session_id,
        step_type=step.step_type,
        content=step.content,
        schema_version=step.schema_version,
        created_by=step.created_by,
        created_at=step.created_at,
        is_completed=step.is_completed,
    )
