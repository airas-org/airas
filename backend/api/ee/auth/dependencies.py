import os
from typing import Annotated
from uuid import UUID

import httpx
from dependency_injector.wiring import Provide, inject
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from airas.container import Container
from airas.infra.github_client import GithubClient
from airas.usecases.ee.github_oauth_service import GitHubOAuthService
from api.ee.auth.middleware import extract_user_id_from_request
from api.ee.settings import get_ee_settings

SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

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
    if settings.enabled:
        if not x_github_session:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="GitHub account not connected. Please connect your GitHub account.",
            )
        github_status = service.get_status(x_github_session)
        if not github_status or not github_status.get("github_login"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="GitHub account not connected. Please connect your GitHub account.",
            )
        return github_status["github_login"]
    else:
        owner = os.getenv("GITHUB_OWNER", "")
        if not owner:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GITHUB_OWNER environment variable is not set.",
            )
        return owner


@inject
async def get_github_client(
    service: Annotated[
        GitHubOAuthService, Depends(Provide[Container.github_oauth_service])
    ],
    x_github_session: Annotated[str | None, Header()] = None,
) -> GithubClient:
    settings = get_ee_settings()
    if settings.enabled:
        if not x_github_session:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="GitHub account not connected. Please connect your GitHub account.",
            )
        token = service.get_token(x_github_session)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="GitHub account not connected. Please connect your GitHub account.",
            )
    else:
        token = os.getenv("GH_PERSONAL_ACCESS_TOKEN", "")
        if not token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GH_PERSONAL_ACCESS_TOKEN is not configured.",
            )
    timeout = httpx.Timeout(connect=10.0, read=60.0, write=120.0, pool=5.0)
    sync_session = httpx.Client(follow_redirects=True, timeout=timeout)
    async_session = httpx.AsyncClient(follow_redirects=True, timeout=timeout)
    try:
        yield GithubClient(
            github_token=token,
            sync_session=sync_session,
            async_session=async_session,
        )
    finally:
        sync_session.close()
        await async_session.aclose()
