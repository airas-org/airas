from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from airas.container import Container
from airas.infra.github_client import GithubClient
from airas.usecases.settings.github_settings_service import GitHubSettingsService
from api.ee.auth.dependencies import get_current_user_id


@inject
async def get_user_github_client(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    github_client: Annotated[GithubClient, Depends(Provide[Container.github_client])],
    github_settings_service: Annotated[
        GitHubSettingsService, Depends(Provide[Container.github_settings_service])
    ],
) -> GithubClient:
    """Return a GithubClient configured with the user's token if available.

    Falls back to the default GithubClient (env var token) when no user token is stored.
    """
    token = github_settings_service.get_token(user_id)
    if token:
        return GithubClient(
            sync_session=github_client._sync_session,
            async_session=github_client._async_session,
            token=token,
        )
    return github_client
