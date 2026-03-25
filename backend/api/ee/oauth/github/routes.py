import secrets
from typing import Annotated
from urllib.parse import quote

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import RedirectResponse

from airas.container import Container
from api.ee.oauth.github.service import GitHubOAuthService
from api.schemas.ee import (
    GitHubAuthorizeResponse,
    GitHubCallbackRequest,
    GitHubCallbackResponse,
    GitHubConnectionStatus,
    GitHubDisconnectResponse,
    GitHubProxyCompleteRequest,
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


# ---- OAuth Proxy endpoints ----


@router.get("/proxy-authorize", response_model=GitHubAuthorizeResponse)
@inject
def proxy_authorize(
    origin: Annotated[str, Query()],
    service: Annotated[
        GitHubOAuthService, Depends(Provide[Container.github_oauth_service])
    ],
) -> GitHubAuthorizeResponse:
    """Return a GitHub authorize URL for the OAuth Proxy flow.

    Called by preview frontends.  The ``origin`` is embedded in the state
    so that the proxy-callback can redirect back to the correct frontend.
    """
    try:
        authorize_url, state = service.get_proxy_authorize_url(origin)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return GitHubAuthorizeResponse(authorize_url=authorize_url, state=state)


@router.get("/proxy-callback")
@inject
async def proxy_callback(
    code: Annotated[str, Query()],
    state: Annotated[str, Query()],
    service: Annotated[
        GitHubOAuthService, Depends(Provide[Container.github_oauth_service])
    ],
) -> RedirectResponse:
    """Receive the OAuth callback from GitHub and redirect to the preview frontend.

    This endpoint runs on the production/develop backend (the fixed callback URL
    registered with the GitHub App).  It exchanges the code for credentials,
    wraps them in a short-lived JWT, and 302-redirects to the preview frontend.
    """
    try:
        origin = service.proxy.decode_state(state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    proxy_callback_url = (
        f"{service.proxy.get_develop_public_url()}/airas/ee/github/proxy-callback"
    )
    try:
        result = await service.exchange_code(code=code, redirect_uri=proxy_callback_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    proxy_token = service.proxy.create_proxy_token(
        {"access_token": result["access_token"], "github_login": result["github_login"]}
    )
    redirect_url = (
        f"{origin}/auth/github/callback?proxy_token={quote(proxy_token, safe='')}"
    )
    return RedirectResponse(url=redirect_url, status_code=302)


@router.post("/proxy-complete", response_model=GitHubCallbackResponse)
@inject
def proxy_complete(
    request: GitHubProxyCompleteRequest,
    service: Annotated[
        GitHubOAuthService, Depends(Provide[Container.github_oauth_service])
    ],
) -> GitHubCallbackResponse:
    """Complete the OAuth Proxy flow on the preview backend.

    The preview frontend sends the proxy JWT it received via redirect.
    This endpoint validates the JWT, creates a local session, and stores
    the GitHub token in this environment's own database.
    """
    try:
        claims = service.proxy.validate_proxy_token(request.proxy_token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    session_token = secrets.token_urlsafe(32)
    service.save_token(
        session_token=session_token,
        access_token=claims["access_token"],
        github_login=claims["github_login"],
    )
    return GitHubCallbackResponse(
        connected=True,
        github_login=claims["github_login"],
        session_token=session_token,
    )
