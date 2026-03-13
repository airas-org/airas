from uuid import UUID

from sqlmodel import Session, select

from airas.infra.db.models.user_plan import UserPlanModel
from airas.repository.base_repository import BaseRepository


class UserPlanRepository(BaseRepository[UserPlanModel]):
    def __init__(self, db: Session):
        super().__init__(db, UserPlanModel)

    def get_by_user(self, user_id: UUID) -> UserPlanModel | None:
        stmt = select(UserPlanModel).where(UserPlanModel.user_id == user_id)
        return self.db.exec(stmt).first()
