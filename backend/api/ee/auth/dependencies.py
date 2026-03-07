import os
from typing import Annotated
from uuid import UUID

import httpx
from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from airas.container import Container
from airas.infra.github_client import GithubClient
from airas.usecases.ee.github_token_service import GitHubTokenService
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
def get_github_client(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[
        GitHubTokenService, Depends(Provide[Container.github_token_service])
    ],
) -> GithubClient:
    settings = get_ee_settings()
    if settings.enabled:
        token = service.get_token(user_id)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="GitHub account not connected. Please sign in with GitHub.",
            )
    else:
        token = os.getenv("GH_PERSONAL_ACCESS_TOKEN", "")
    timeout = httpx.Timeout(connect=10.0, read=60.0, write=120.0, pool=5.0)
    return GithubClient(
        github_token=token,
        sync_session=httpx.Client(follow_redirects=True, timeout=timeout),
        async_session=httpx.AsyncClient(follow_redirects=True, timeout=timeout),
    )
