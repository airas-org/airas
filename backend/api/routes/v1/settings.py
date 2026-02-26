from typing import Annotated
from uuid import UUID

import httpx
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from airas.container import Container
from airas.usecases.settings.github_settings_service import GitHubSettingsService
from api.ee.auth.dependencies import get_current_user_id
from api.schemas.settings import (
    GitHubConnectionStatusResponse,
    GitHubSettingsResponse,
    SaveGitHubTokenRequest,
)

router = APIRouter(prefix="/settings", tags=["settings"])


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


@router.post("/github", response_model=GitHubSettingsResponse)
@inject
async def save_github_settings(
    request: SaveGitHubTokenRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    github_settings_service: Annotated[
        GitHubSettingsService, Depends(Provide[Container.github_settings_service])
    ],
) -> GitHubSettingsResponse:
    # Verify the token by calling GitHub API
    username = await _verify_github_token(request.github_token)

    settings = github_settings_service.save_token(
        user_id=user_id,
        github_token=request.github_token,
        github_username=username,
    )

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
