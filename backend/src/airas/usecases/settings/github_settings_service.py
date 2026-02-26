from __future__ import annotations

from datetime import datetime
from uuid import UUID

from airas.infra.db.models.github_settings import GitHubSettingsModel
from airas.repository.github_settings_repository import GitHubSettingsRepository


class GitHubSettingsService:
    def __init__(self, repo: GitHubSettingsRepository):
        self.repo = repo

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

    def close(self) -> None:
        self.repo.db.close()
