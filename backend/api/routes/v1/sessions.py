from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Closing, Provide, inject
from fastapi import APIRouter, Depends

from airas.container import Container
from airas.usecases.sessions.service import SessionService
from api.schemas.sessions import (
    SessionCreateRequest,
    SessionResponse,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse)
@inject
def create_session(
    request: SessionCreateRequest,
    svc: Annotated[
        SessionService, Depends(Closing[Provide[Container.session_service]])
    ],
) -> SessionResponse:
    s = svc.create(title=request.title, created_by=request.created_by)
    return SessionResponse(id=s.id, title=s.title, created_at=s.created_at)


@router.get("/{session_id}", response_model=SessionResponse)
@inject
def get_session(
    session_id: UUID,
    svc: Annotated[
        SessionService, Depends(Closing[Provide[Container.session_service]])
    ],
) -> SessionResponse:
    s = svc.get(session_id)
    return SessionResponse(id=s.id, title=s.title, created_at=s.created_at)
