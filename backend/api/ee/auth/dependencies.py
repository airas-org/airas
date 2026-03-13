import os
from typing import Annotated
from uuid import UUID

import httpx
from anyio import to_thread
from dependency_injector.wiring import Provide, inject
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from airas.container import Container
from airas.infra.github_client import GithubClient
from airas.usecases.ee.github_oauth_service import GitHubOAuthService
from api.ee.auth.middleware import extract_user_id_from_request
from api.ee.settings import get_ee_settings

# FastAPI dependencies that absorb EE / non-EE branching and provide a unified interface to route handlers.
# Session lifecycle is managed by the Container; this module only resolves authentication credentials and assembles clients.

SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

_GITHUB_NOT_CONNECTED = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="GitHub account not connected. Please connect your GitHub account.",
)

# Show "Authorize" button in Swagger UI when EE is enabled
_bearer_scheme = HTTPBearer(auto_error=False)
_bearer_dependency = Depends(_bearer_scheme)


def get_current_user_id(
    request: Request,
    _credentials: HTTPAuthorizationCredentials | None = _bearer_dependency,
) -> UUID:
    """Return user ID from JWT if EE is enabled, otherwise return SYSTEM_USER_ID."""
    settings = get_ee_settings()
    if not settings.enabled:
        return SYSTEM_USER_ID
    return extract_user_id_from_request(request)


@inject
def get_github_owner(
    service: Annotated[
        GitHubOAuthService, Depends(Provide[Container.github_oauth_service])
    ],
    x_github_session: Annotated[str | None, Header()] = None,
) -> str:
    """Return the GitHub login of the connected account."""
    settings = get_ee_settings()
    if not settings.enabled:
        if not (owner := os.getenv("GITHUB_OWNER", "")):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GITHUB_OWNER environment variable is not set.",
            )
        return owner

    if not x_github_session:
        raise _GITHUB_NOT_CONNECTED

    github_status = service.get_status(x_github_session)
    if not (login := github_status.get("github_login") if github_status else None):
        raise _GITHUB_NOT_CONNECTED

    return login


def _resolve_github_token(
    service: GitHubOAuthService,
    x_github_session: str | None,
) -> str:
    """Resolve GitHub token from session (EE) or environment variable."""
    settings = get_ee_settings()
    if not settings.enabled:
        token = os.getenv("GH_PERSONAL_ACCESS_TOKEN", "")
        if not token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GH_PERSONAL_ACCESS_TOKEN is not configured.",
            )
        return token

    if not x_github_session:
        raise _GITHUB_NOT_CONNECTED

    token = service.get_token(x_github_session)
    if not token:
        raise _GITHUB_NOT_CONNECTED

    return token


@inject
async def get_github_client(
    service: Annotated[
        GitHubOAuthService, Depends(Provide[Container.github_oauth_service])
    ],
    github_sync_session: Annotated[
        httpx.Client, Depends(Provide[Container.github_sync_session])
    ],
    github_async_session: Annotated[
        httpx.AsyncClient, Depends(Provide[Container.github_async_session])
    ],
    x_github_session: Annotated[str | None, Header()] = None,
) -> GithubClient:
    token = await to_thread.run_sync(lambda: _resolve_github_token(service, x_github_session))
    return GithubClient(
        github_token=token,
        sync_session=github_sync_session,
        async_session=github_async_session,
    )
