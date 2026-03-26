from uuid import UUID

from sqlmodel import Session, select

from airas.infra.db.models.feedback import FeedbackModel
from airas.repository.base_repository import BaseRepository


class FeedbackRepository(BaseRepository[FeedbackModel]):
    def __init__(self, db: Session):
        super().__init__(db, FeedbackModel)

    def list_by_user(
        self,
        created_by: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FeedbackModel]:
        statement = (
            select(FeedbackModel)
            .where(FeedbackModel.created_by == created_by)
            .order_by(FeedbackModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return self.db.exec(statement).all()
