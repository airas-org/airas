from sqlmodel import Session, select

from airas.infra.db.models.user_github_token import UserGitHubTokenModel
from airas.repository.base_repository import BaseRepository


class UserGitHubTokenRepository(BaseRepository[UserGitHubTokenModel]):
    def __init__(self, db: Session):
        super().__init__(db, UserGitHubTokenModel)

    def get_by_session_token(self, session_token: str) -> UserGitHubTokenModel | None:
        stmt = select(UserGitHubTokenModel).where(
            UserGitHubTokenModel.session_token == session_token
        )
        return self.db.exec(stmt).first()

    def delete_by_session_token(self, session_token: str) -> bool:
        obj = self.get_by_session_token(session_token)
        if obj is None:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True
