import os
from typing import Annotated
from urllib.parse import urlencode
from uuid import UUID

import httpx
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse

from airas.container import Container
from airas.usecases.settings.github_settings_service import GitHubSettingsService
from api.ee.auth.dependencies import get_current_user_id
from api.schemas.settings import (
    GitHubConnectionStatusResponse,
    GitHubOAuthAuthorizeResponse,
    GitHubSettingsResponse,
)

router = APIRouter(prefix="/settings", tags=["settings"])

# Separate router for OAuth callback (no auth required)
oauth_callback_router = APIRouter(prefix="/settings", tags=["settings"])

GITHUB_OAUTH_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_OAUTH_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_OAUTH_SCOPES = "repo,workflow"


def _get_frontend_url() -> str:
    return os.getenv("FRONTEND_URL", "http://localhost:5173")


def _get_client_id() -> str:
    return os.getenv("GITHUB_OAUTH_CLIENT_ID", "")


def _get_client_secret() -> str:
    return os.getenv("GITHUB_OAUTH_CLIENT_SECRET", "")


@router.get("/github", response_model=GitHubSettingsResponse)
@inject
async def get_github_settings(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    github_settings_service: Annotated[
        GitHubSettingsService, Depends(Provide[Container.github_settings_service])
    ],
) -> GitHubSettingsResponse:
    settings = github_settings_service.get_by_user_id(user_id)
    if not settings:
        return GitHubSettingsResponse(is_connected=False)

    token = settings.github_token
    last4 = token[-4:] if len(token) >= 4 else "****"
    return GitHubSettingsResponse(
        is_connected=True,
        github_username=settings.github_username,
        token_last4=last4,
    )


@router.delete("/github")
@inject
async def delete_github_settings(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    github_settings_service: Annotated[
        GitHubSettingsService, Depends(Provide[Container.github_settings_service])
    ],
) -> GitHubSettingsResponse:
    github_settings_service.delete(user_id)
    return GitHubSettingsResponse(is_connected=False)


@router.get("/github/status", response_model=GitHubConnectionStatusResponse)
@inject
async def check_github_connection(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    github_settings_service: Annotated[
        GitHubSettingsService, Depends(Provide[Container.github_settings_service])
    ],
) -> GitHubConnectionStatusResponse:
    token = github_settings_service.get_token(user_id)
    if not token:
        return GitHubConnectionStatusResponse(
            is_valid=False, error="GitHub token is not configured"
        )

    try:
        username = await _verify_github_token(token)
        return GitHubConnectionStatusResponse(is_valid=True, github_username=username)
    except Exception as e:
        return GitHubConnectionStatusResponse(is_valid=False, error=str(e))


@router.get("/github/oauth/authorize", response_model=GitHubOAuthAuthorizeResponse)
@inject
async def github_oauth_authorize(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    github_settings_service: Annotated[
        GitHubSettingsService, Depends(Provide[Container.github_settings_service])
    ],
) -> GitHubOAuthAuthorizeResponse:
    """Generate a GitHub OAuth authorization URL with CSRF state."""
    client_id = _get_client_id()
    if not client_id:
        raise ValueError("GITHUB_OAUTH_CLIENT_ID is not configured")

    state = github_settings_service.create_oauth_state(user_id)

    backend_base = os.getenv("BACKEND_URL", "http://localhost:8000")
    callback_url = f"{backend_base}/airas/v1/settings/github/oauth/callback"

    params = urlencode(
        {
            "client_id": client_id,
            "redirect_uri": callback_url,
            "scope": GITHUB_OAUTH_SCOPES,
            "state": state,
        }
    )
    authorize_url = f"{GITHUB_OAUTH_AUTHORIZE_URL}?{params}"

    return GitHubOAuthAuthorizeResponse(authorize_url=authorize_url)


@oauth_callback_router.get("/github/oauth/callback")
@inject
async def github_oauth_callback(
    code: Annotated[str, Query()],
    state: Annotated[str, Query()],
    github_settings_service: Annotated[
        GitHubSettingsService, Depends(Provide[Container.github_settings_service])
    ],
) -> RedirectResponse:
    """Handle GitHub OAuth callback. Exchange code for token, save, redirect to frontend."""
    frontend_url = _get_frontend_url()

    # Validate state (CSRF protection)
    user_id = github_settings_service.validate_oauth_state(state)
    if user_id is None:
        return RedirectResponse(
            url=f"{frontend_url}?github=error&message=invalid_state"
        )

    # Exchange code for access token
    client_id = _get_client_id()
    client_secret = _get_client_secret()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GITHUB_OAUTH_TOKEN_URL,
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                },
                headers={"Accept": "application/json"},
            )

            if response.status_code != 200:
                return RedirectResponse(
                    url=f"{frontend_url}?github=error&message=token_exchange_failed"
                )

            token_data = response.json()
            access_token = token_data.get("access_token")

            if not access_token:
                error = token_data.get("error", "unknown_error")
                return RedirectResponse(
                    url=f"{frontend_url}?github=error&message={error}"
                )

        # Verify token and get username
        username = await _verify_github_token(access_token)

        # Save token to database
        github_settings_service.save_token(
            user_id=user_id,
            github_token=access_token,
            github_username=username,
        )

        return RedirectResponse(url=f"{frontend_url}?github=connected")

    except Exception:
        return RedirectResponse(
            url=f"{frontend_url}?github=error&message=unexpected_error"
        )


async def _verify_github_token(token: str) -> str | None:
    """Verify a GitHub token by calling the /user endpoint. Returns username."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("login")
        if response.status_code == 401:
            raise ValueError("Invalid GitHub token")
        raise ValueError(f"GitHub API error: {response.status_code}")
