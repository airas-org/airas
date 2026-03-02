from uuid import UUID

from sqlmodel import Session, select

from airas.infra.db.models.user_api_key import ApiProvider, UserApiKeyModel
from airas.repository.base_repository import BaseRepository


class UserApiKeyRepository(BaseRepository[UserApiKeyModel]):
    def __init__(self, db: Session):
        super().__init__(db, UserApiKeyModel)

    def get_by_user_and_provider(
        self, user_id: UUID, provider: ApiProvider
    ) -> UserApiKeyModel | None:
        stmt = select(UserApiKeyModel).where(
            UserApiKeyModel.user_id == user_id,
            UserApiKeyModel.provider == provider,
        )
        return self.db.exec(stmt).first()

    def list_by_user(self, user_id: UUID) -> list[UserApiKeyModel]:
        stmt = select(UserApiKeyModel).where(UserApiKeyModel.user_id == user_id)
        return self.db.exec(stmt).all()

    def delete_by_user_and_provider(self, user_id: UUID, provider: ApiProvider) -> bool:
        obj = self.get_by_user_and_provider(user_id, provider)
        if obj is None:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True
