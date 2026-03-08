from uuid import UUID

from sqlmodel import Session, select

from airas.infra.db.models.user_github_token import UserGitHubTokenModel
from airas.repository.base_repository import BaseRepository


class UserGitHubTokenRepository(BaseRepository[UserGitHubTokenModel]):
    def __init__(self, db: Session):
        super().__init__(db, UserGitHubTokenModel)

    def get_by_user(self, user_id: UUID) -> UserGitHubTokenModel | None:
        stmt = select(UserGitHubTokenModel).where(
            UserGitHubTokenModel.user_id == user_id
        )
        return self.db.exec(stmt).first()

    def delete_by_user(self, user_id: UUID) -> bool:
        obj = self.get_by_user(user_id)
        if obj is None:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True
