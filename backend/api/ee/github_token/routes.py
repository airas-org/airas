from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from airas.container import Container
from airas.usecases.ee.github_token_service import GitHubTokenService
from api.ee.auth.dependencies import get_current_user_id

router = APIRouter(prefix="/github-token", tags=["ee-github-token"])


class SaveGitHubTokenRequest(BaseModel):
    github_token: str


@router.post("")
@inject
def save_github_token(
    request: SaveGitHubTokenRequest,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[
        GitHubTokenService, Depends(Provide[Container.github_token_service])
    ],
):
    service.save_token(current_user_id, request.github_token)
    return {"saved": True}


@router.get("/status")
@inject
def get_github_token_status(
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[
        GitHubTokenService, Depends(Provide[Container.github_token_service])
    ],
):
    token = service.get_token(current_user_id)
    return {"connected": token is not None}
