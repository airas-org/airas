from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Query

from airas.container import Container
from airas.usecases.ee.github_oauth_service import GitHubOAuthService
from api.ee.auth.dependencies import get_current_user_id
from api.schemas.ee import (
    GitHubAuthorizeResponse,
    GitHubCallbackRequest,
    GitHubConnectionStatus,
)

router = APIRouter(prefix="/github", tags=["ee-github-oauth"])


@router.get("/authorize", response_model=GitHubAuthorizeResponse)
@inject
def authorize(
    redirect_uri: Annotated[str, Query()],
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[
        GitHubOAuthService, Depends(Provide[Container.github_oauth_service])
    ],
) -> GitHubAuthorizeResponse:
    authorize_url, state = service.get_authorize_url(redirect_uri)
    return GitHubAuthorizeResponse(authorize_url=authorize_url, state=state)


@router.post("/callback")
@inject
async def callback(
    request: GitHubCallbackRequest,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[
        GitHubOAuthService, Depends(Provide[Container.github_oauth_service])
    ],
):
    try:
        result = await service.exchange_code(
            code=request.code, redirect_uri=request.redirect_uri
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    service.save_token(
        user_id=current_user_id,
        access_token=result["access_token"],
        github_login=result["github_login"],
    )
    return {"connected": True, "github_login": result["github_login"]}


@router.get("/status", response_model=GitHubConnectionStatus)
@inject
def status(
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[
        GitHubOAuthService, Depends(Provide[Container.github_oauth_service])
    ],
) -> GitHubConnectionStatus:
    info = service.get_status(current_user_id)
    if info is None:
        return GitHubConnectionStatus(connected=False)
    return GitHubConnectionStatus(connected=True, **info)


@router.delete("/disconnect")
@inject
def disconnect(
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[
        GitHubOAuthService, Depends(Provide[Container.github_oauth_service])
    ],
):
    deleted = service.disconnect(current_user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="GitHub connection not found")
    return {"disconnected": True}
