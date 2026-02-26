from __future__ import annotations

import secrets
from datetime import datetime
from uuid import UUID

from airas.infra.db.models.github_oauth_state import GitHubOAuthStateModel
from airas.infra.db.models.github_settings import GitHubSettingsModel
from airas.repository.github_oauth_state_repository import GitHubOAuthStateRepository
from airas.repository.github_settings_repository import GitHubSettingsRepository


class GitHubSettingsService:
    def __init__(
        self,
        repo: GitHubSettingsRepository,
        oauth_state_repo: GitHubOAuthStateRepository,
    ):
        self.repo = repo
        self.oauth_state_repo = oauth_state_repo

    def save_token(
        self, *, user_id: UUID, github_token: str, github_username: str | None = None
    ) -> GitHubSettingsModel:
        existing = self.repo.get_by_user_id(user_id)
        if existing:
            existing.github_token = github_token
            if github_username is not None:
                existing.github_username = github_username
            existing.updated_at = datetime.now().astimezone()
            self.repo.db.add(existing)
            self.repo.db.commit()
            self.repo.db.refresh(existing)
            return existing

        settings = GitHubSettingsModel(
            user_id=user_id,
            github_token=github_token,
            github_username=github_username,
        )
        return self.repo.create(settings)

    def get_by_user_id(self, user_id: UUID) -> GitHubSettingsModel | None:
        return self.repo.get_by_user_id(user_id)

    def get_token(self, user_id: UUID) -> str | None:
        settings = self.repo.get_by_user_id(user_id)
        return settings.github_token if settings else None

    def delete(self, user_id: UUID) -> bool:
        return self.repo.delete_by_user_id(user_id)

    # --- OAuth state management ---

    def create_oauth_state(self, user_id: UUID) -> str:
        """Create a new OAuth state for CSRF protection. Returns the state string."""
        # Clean up any existing states for this user
        self.oauth_state_repo.delete_by_user_id(user_id)
        # Clean up expired states from all users
        self.oauth_state_repo.delete_expired()

        state = secrets.token_urlsafe(32)
        oauth_state = GitHubOAuthStateModel(user_id=user_id, state=state)
        self.oauth_state_repo.create(oauth_state)
        return state

    def validate_oauth_state(self, state: str) -> UUID | None:
        """Validate an OAuth state and return the user_id. Deletes the state after use."""
        oauth_state = self.oauth_state_repo.get_by_state(state)
        if oauth_state is None:
            return None
        user_id = oauth_state.user_id
        self.oauth_state_repo.delete_by_state(state)
        return user_id

    def close(self) -> None:
        self.repo.db.close()
