from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Session, select

from airas.infra.db.models.user_github_token import UserGithubTokenModel
from airas.repository.base_repository import BaseRepository


class UserGithubTokenRepository(BaseRepository[UserGithubTokenModel]):
    def __init__(self, db: Session):
        super().__init__(db, UserGithubTokenModel)

    def get_by_user_id(self, user_id: UUID) -> UserGithubTokenModel | None:
        stmt = select(UserGithubTokenModel).where(
            UserGithubTokenModel.user_id == user_id,
        )
        return self.db.exec(stmt).first()

    def upsert(self, user_id: UUID, encrypted_token: str) -> UserGithubTokenModel:
        existing = self.get_by_user_id(user_id)
        if existing:
            existing.encrypted_token = encrypted_token
            existing.updated_at = datetime.now(timezone.utc)
            self.db.add(existing)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        model = UserGithubTokenModel(
            user_id=user_id,
            encrypted_token=encrypted_token,
        )
        return self.create(model)
