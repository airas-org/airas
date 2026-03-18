import secrets
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Header, HTTPException, Query

from airas.container import Container
from airas.usecases.ee.github_oauth_service import GitHubOAuthService
from api.schemas.ee import (
    GitHubAuthorizeResponse,
    GitHubCallbackRequest,
    GitHubCallbackResponse,
    GitHubConnectionStatus,
    GitHubDisconnectResponse,
)

router = APIRouter(prefix="/github", tags=["ee-github-oauth"])


@router.get("/authorize", response_model=GitHubAuthorizeResponse)
@inject
def authorize(
    redirect_uri: Annotated[str, Query()],
    service: Annotated[
        GitHubOAuthService, Depends(Provide[Container.github_oauth_service])
    ],
) -> GitHubAuthorizeResponse:
    authorize_url, state = service.get_authorize_url(redirect_uri)
    return GitHubAuthorizeResponse(authorize_url=authorize_url, state=state)


@router.post("/callback", response_model=GitHubCallbackResponse)
@inject
async def callback(
    request: GitHubCallbackRequest,
    service: Annotated[
        GitHubOAuthService, Depends(Provide[Container.github_oauth_service])
    ],
) -> GitHubCallbackResponse:
    try:
        result = await service.exchange_code(
            code=request.code, redirect_uri=request.redirect_uri
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    session_token = secrets.token_urlsafe(32)
    service.save_token(
        session_token=session_token,
        access_token=result["access_token"],
        github_login=result["github_login"],
    )
    return GitHubCallbackResponse(
        connected=True,
        github_login=result["github_login"],
        session_token=session_token,
    )


@router.get("/status", response_model=GitHubConnectionStatus)
@inject
def status(
    service: Annotated[
        GitHubOAuthService, Depends(Provide[Container.github_oauth_service])
    ],
    x_github_session: Annotated[str | None, Header()] = None,
) -> GitHubConnectionStatus:
    if not x_github_session:
        return GitHubConnectionStatus(connected=False)
    info = service.get_status(x_github_session)
    if info is None:
        return GitHubConnectionStatus(connected=False)
    return GitHubConnectionStatus(connected=True, **info)


@router.delete("/disconnect", response_model=GitHubDisconnectResponse)
@inject
def disconnect(
    service: Annotated[
        GitHubOAuthService, Depends(Provide[Container.github_oauth_service])
    ],
    x_github_session: Annotated[str | None, Header()] = None,
) -> GitHubDisconnectResponse:
    if not x_github_session:
        raise HTTPException(status_code=400, detail="X-GitHub-Session header required")
    deleted = service.disconnect(x_github_session)
    if not deleted:
        raise HTTPException(status_code=404, detail="GitHub connection not found")
    return GitHubDisconnectResponse(disconnected=True)
