from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException

from airas.core.container import Container
from airas.features.sessions.service import SessionService
from api.schemas.sessions import SessionCreateRequest, SessionResponse

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse)
@inject
def create_session(
    request: SessionCreateRequest,
    svc: Annotated[SessionService, Depends(Provide[Container.session_service])],
) -> SessionResponse:
    try:
        s = svc.create(title=request.title)
        return SessionResponse(id=s.id, title=s.title)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{session_id}", response_model=SessionResponse)
@inject
def get_session(
    session_id: UUID,
    svc: Annotated[SessionService, Depends(Provide[Container.session_service])],
) -> SessionResponse:
    try:
        s = svc.get(session_id)
        return SessionResponse(id=s.id, title=s.title)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
