from uuid import UUID

from sqlmodel import Session, select

from airas.infra.db.models.github_settings import GitHubSettingsModel
from airas.repository.base_repository import BaseRepository


class GitHubSettingsRepository(BaseRepository[GitHubSettingsModel]):
    def __init__(self, db: Session):
        super().__init__(db, GitHubSettingsModel)

    def get_by_user_id(self, user_id: UUID) -> GitHubSettingsModel | None:
        statement = select(GitHubSettingsModel).where(
            GitHubSettingsModel.user_id == user_id
        )
        return self.db.exec(statement).first()

    def delete_by_user_id(self, user_id: UUID) -> bool:
        obj = self.get_by_user_id(user_id)
        if obj is None:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True
